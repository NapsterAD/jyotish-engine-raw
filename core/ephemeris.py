"""
ephemeris.py — Swiss Ephemeris wrapper for sidereal planetary positions.
100% offline — uses local .se1 files or built-in Moshier approximation.
"""

import os
import math
from datetime import datetime, timezone, timedelta
import swisseph as swe

from .constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, PLANET_SWE_IDS, NAKSHATRAS,
    NAKSHATRA_SPAN, PADA_SPAN, get_navamsa_sign
)


class Ephemeris:
    """Swiss Ephemeris wrapper configured for Vedic (sidereal) calculations."""

    def __init__(self, ephe_path=None, ayanamsha="lahiri"):
        """
        Initialize ephemeris engine.
        
        Args:
            ephe_path: Path to Swiss Ephemeris .se1 data files.
                       If None, uses built-in Moshier (slightly less precise).
            ayanamsha: Ayanamsha system. Default "lahiri" (Chitrapaksha).
        """
        self._ephe_path = ephe_path
        if ephe_path and os.path.isdir(ephe_path):
            swe.set_ephe_path(ephe_path)

        # Set sidereal mode
        from .inputs import AYANAMSHA_ALIASES
        ayanamsha_map = {
            # Engine "lahiri" = True Chitrapaksha (Spica at 180°). Official IAU
            # Lahiri is ayanamsha="lahiri_official".
            "lahiri": swe.SIDM_TRUE_CITRA,
            "lahiri_official": swe.SIDM_LAHIRI,
            "raman": swe.SIDM_RAMAN,
            "krishnamurti": swe.SIDM_KRISHNAMURTI,
            "yukteshwar": swe.SIDM_YUKTESHWAR,
            "true_chitrapaksha": swe.SIDM_TRUE_CITRA,
        }
        key = AYANAMSHA_ALIASES.get(str(ayanamsha).strip().lower(), "lahiri")
        sid_mode = ayanamsha_map[key]
        swe.set_sid_mode(sid_mode)
        self._ayanamsha = key

    @staticmethod
    def _parse_timezone(tz_str, date_str=None, time_str=None):
        """Parse +HH:MM, UTC, IST, or IANA. Never silently substitutes IST."""
        from .inputs import parse_timezone
        return parse_timezone(tz_str, date_str, time_str)

    @staticmethod
    def _to_julian_day(date_str, time_str, tz_offset_hours):
        """
        Convert date/time/timezone to Julian Day (UT).
        
        Args:
            date_str: "YYYY-MM-DD"
            time_str: "HH:MM:SS" or "HH:MM"
            tz_offset_hours: float, e.g. 5.5 for IST
        """
        parts = date_str.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

        time_parts = time_str.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0

        # Convert to UT
        ut_hour = hour + minute / 60.0 + second / 3600.0 - tz_offset_hours
        jd = swe.julday(year, month, day, ut_hour)
        return jd

    def get_ayanamsha_value(self, jd):
        """Get the ayanamsha value in degrees for a given Julian Day."""
        return swe.get_ayanamsa_ut(jd)

    def get_planet_positions(self, date, time, tz, lat, lon):
        """
        Calculate sidereal positions for all 9 grahas + Lagna.
        
        Args:
            date: "YYYY-MM-DD"
            time: "HH:MM:SS"
            tz: timezone string ("+05:30" or "IST (+5:30)")
            lat: latitude (float)
            lon: longitude (float)
            
        Returns:
            dict with planet names as keys, each containing:
                longitude, sign, sign_index, degree_in_sign, 
                nakshatra, pada, nakshatra_lord, retrograde
        """
        tz_offset = self._parse_timezone(tz, date, time)
        jd = self._to_julian_day(date, time, tz_offset)

        positions = {}

        # Calculate Lagna (Ascendant). Placidus is undefined in polar regions.
        _cusps, ascmc, _hsys = self._houses_ex_safe(jd, lat, lon, "P")
        asc_sid = ascmc[0]
        positions["Lagna"] = self._build_position(asc_sid, retrograde=False)

        # Calculate planet positions
        for planet_name, swe_id in PLANET_SWE_IDS.items():
            flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
            result, ret_flags = swe.calc_ut(jd, swe_id, flags)
            longitude = result[0]
            speed = result[3]  # Negative speed = retrograde

            latitude = result[1]
            if planet_name == "Rahu":
                # Mean node always retrogrades (rules.md §2.9). Same dλ/dt for Ketu.
                pos = self._build_position(
                    longitude, retrograde=True, latitude=latitude, speed=speed
                )
                positions["Rahu"] = pos

                ketu_long = (longitude + 180.0) % 360.0
                positions["Ketu"] = self._build_position(
                    ketu_long, retrograde=True, latitude=-latitude, speed=speed
                )
            else:
                is_retro = speed < 0
                positions[planet_name] = self._build_position(
                    longitude, retrograde=is_retro, latitude=latitude, speed=speed
                )

        # Store Julian Day and raw data for other calculations
        positions["_jd"] = jd
        positions["_lat"] = lat
        positions["_lon"] = lon
        positions["_tz_offset"] = tz_offset
        positions["_ayanamsha"] = self.get_ayanamsha_value(jd)

        return positions

    def _build_position(self, longitude, retrograde=False, latitude=0.0, speed=0.0):
        """Build position dict from a sidereal longitude."""
        longitude = longitude % 360.0

        # Sign
        sign_idx = int(longitude / 30.0) % 12
        sign = SIGNS[sign_idx]
        degree_in_sign = longitude - (sign_idx * 30)

        # Degree, minute, second
        deg = int(degree_in_sign)
        min_float = (degree_in_sign - deg) * 60
        minutes = int(min_float)
        seconds = (min_float - minutes) * 60

        # Nakshatra and pada
        nak_info = self._get_nakshatra(longitude)

        # Navamsa
        navamsa = get_navamsa_sign(longitude)
        from ..computations.kp import kp_chain
        ch = kp_chain(longitude)

        return {
            "longitude": round(longitude, 6),
            "sign": sign,
            "sign_index": sign_idx,
            "degree_in_sign": round(degree_in_sign, 6),
            "deg": deg,
            "min": minutes,
            "sec": round(seconds, 2),
            "dms": f"{deg}°{minutes:02d}'{seconds:05.2f}\"",
            "nakshatra": nak_info["name"],
            "nakshatra_num": nak_info["num"],
            "pada": nak_info["pada"],
            "nakshatra_lord": nak_info["lord"],
            "nakshatra_remaining_pct": round(nak_info["remaining_pct"], 4),
            "sign_lord": SIGN_LORDS[sign],
            "sub_lord": ch["sub_lord"],
            "sub_sub_lord": ch["sub_sub_lord"],
            "sssl_lord": ch["sssl_lord"],
            "kp_249": ch["kp_249"],
            "navamsa": navamsa,
            "retrograde": retrograde,
            "latitude": round(latitude, 6),
            "speed": round(speed, 6),
        }

    @staticmethod
    def _get_nakshatra(longitude):
        """Calculate nakshatra, pada, and remaining % from sidereal longitude."""
        longitude = longitude % 360.0
        nak_idx = int(longitude / NAKSHATRA_SPAN)
        nak_idx = min(nak_idx, 26)  # Clamp to 0-26

        nak = NAKSHATRAS[nak_idx]
        degree_in_nak = longitude - (nak_idx * NAKSHATRA_SPAN)
        pada = int(degree_in_nak / PADA_SPAN) + 1
        pada = min(pada, 4)

        # Remaining % of nakshatra
        remaining = 1.0 - (degree_in_nak / NAKSHATRA_SPAN)
        remaining_pct = remaining * 100.0

        return {
            "name": nak["name"],
            "num": nak["num"],
            "lord": nak["lord"],
            "pada": pada,
            "remaining_pct": remaining_pct,
        }

    @staticmethod
    def _houses_ex_safe(jd, lat, lon, system="P"):
        """
        Placidus is undefined above the arctic/antarctic circle.
        Fall back to Equal so any latitude still yields 12 cusps + ASC.
        """
        wanted = (system or "P").upper()[:1]
        if abs(float(lat)) >= 66.0 and wanted == "P":
            wanted = "E"
        try:
            cusps, ascmc = swe.houses_ex(jd, float(lat), float(lon), wanted.encode(), swe.FLG_SIDEREAL)
            return cusps, ascmc, wanted
        except Exception:
            cusps, ascmc = swe.houses_ex(jd, float(lat), float(lon), b"E", swe.FLG_SIDEREAL)
            return cusps, ascmc, "E"

    def get_house_cusps(self, date, time, tz, lat, lon, system="P"):
        """
        Calculate house cusps.
        
        Args:
            system: "P" = Placidus, "E" = Equal, "W" = Whole Sign
            
        Returns:
            dict with cusps (1-12) and special points (ASC, MC, etc.)
        """
        tz_offset = self._parse_timezone(tz, date, time)
        jd = self._to_julian_day(date, time, tz_offset)

        cusps, ascmc, used = self._houses_ex_safe(jd, lat, lon, system)

        result = {
            "cusps": {},
            "asc": ascmc[0],
            "mc": ascmc[1],
            "armc": ascmc[2],
            "vertex": ascmc[3],
            "house_system": used,
            "polar_fallback": used != (system or "P").upper()[:1] and abs(float(lat)) >= 66.0,
        }

        from ..computations.kp import kp_chain
        for i, cusp_long in enumerate(cusps):
            house_num = i + 1
            if house_num > 12:
                break
            nak = self._get_nakshatra(cusp_long)
            ch = kp_chain(cusp_long)
            result["cusps"][house_num] = {
                "longitude": round(cusp_long, 6),
                "sign": SIGNS[int(cusp_long / 30) % 12],
                "degree": round(cusp_long % 30, 4),
                "nakshatra": nak["name"],
                "nak_lord": nak["lord"],
                "sub_lord": ch["sub_lord"],
                "sub_sub_lord": ch["sub_sub_lord"],
                "sssl_lord": ch["sssl_lord"],
                "kp_249": ch["kp_249"],
            }

        return result

    @staticmethod
    def _get_kp_sublord(longitude):
        from ..computations.kp import kp_sub_lord
        return kp_sub_lord(longitude)

    @staticmethod
    def _get_kp_sub_sub_lord(longitude):
        from ..computations.kp import kp_sub_sub_lord
        return kp_sub_sub_lord(longitude)

    @staticmethod
    def _sun_altitude_deg(jd, lat, lon, flags):
        """Geometric altitude of the Sun's disc center (degrees). + = above horizon."""
        try:
            xx, _ = swe.calc_ut(jd, swe.SUN, flags)
            hor = swe.azalt(jd, swe.ECL2HOR, (float(lon), float(lat), 0.0), 0.0, 0.0, xx[:3])
            return float(hor[1])
        except Exception:
            return None

    def get_sunrise_sunset(self, date, lat, lon, tz):
        """
        Calculate sunrise and sunset times for a given date and location.

        Uses pyswisseph 2.10 rise_trans(tjdut, body, rsmi, geopos, ...).
        Polar regions: search adjacent days for the last/next real event
        instead of inventing noon±6h. Flag polar_estimated when the civil
        date itself has no rise or set.
        """
        tz_offset = self._parse_timezone(tz, date, "12:00:00")
        jd = self._to_julian_day(date, "12:00:00", tz_offset)
        geopos = (float(lon), float(lat), 0.0)
        flags = swe.FLG_SWIEPH | swe.FLG_MOSEPH
        max_days = 366

        def _event_at(tjd, rsmi):
            try:
                res, tret = swe.rise_trans(
                    tjd - 0.5, swe.SUN, rsmi, geopos, 0.0, 0.0, flags
                )
                if res == 0 and tret and tret[0] > 0:
                    return tret[0]
            except Exception:
                pass
            return None

        def _next_event(start_jd, rsmi):
            for i in range(max_days + 1):
                found = _event_at(start_jd + i, rsmi)
                if found is not None:
                    return found
            return None

        def _prev_event(start_jd, rsmi):
            for i in range(1, max_days + 1):
                found = _event_at(start_jd - i, rsmi)
                if found is not None and found <= start_jd:
                    return found
            return None

        # JHora special-lagna sunrise = true geometric disc center, no refraction.
        rise_flag = swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
        set_flag = swe.CALC_SET | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
        rise_jd = _event_at(jd, rise_flag)
        set_jd = _event_at(jd, set_flag)
        polar = rise_jd is None or set_jd is None
        polar_mode = None
        if polar:
            alt = self._sun_altitude_deg(jd, lat, lon, flags)
            if alt is not None:
                sun_up = alt > 0.0
            else:
                month = int(str(date).split("-")[1])
                sun_up = (4 <= month <= 9) if float(lat) >= 0 else (month <= 3 or month >= 10)
            polar_mode = "day" if sun_up else "night"
            if rise_jd is None:
                rise_jd = _prev_event(jd, rise_flag) if sun_up else _next_event(jd, rise_flag)
            if set_jd is None:
                set_jd = _next_event(jd, set_flag) if sun_up else _prev_event(jd, set_flag)
            # Last resort if Swiss finds nothing within a year.
            if rise_jd is None:
                rise_jd = jd - 0.25
            if set_jd is None:
                set_jd = jd + 0.25

        def jd_to_local(jd_val):
            year, month, day, hour_frac = swe.revjul(jd_val)
            hour_frac += tz_offset
            # Carry overflow into hours (can be 24+ or negative)
            extra_days = int(math.floor(hour_frac / 24.0))
            hour_frac -= extra_days * 24.0
            hours = int(hour_frac)
            mins = int((hour_frac - hours) * 60)
            secs = int(((hour_frac - hours) * 60 - mins) * 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d}"

        return {
            "sunrise": jd_to_local(rise_jd),
            "sunset": jd_to_local(set_jd),
            "sunrise_jd": rise_jd,
            "sunset_jd": set_jd,
            "is_day_birth": None,
            "polar_estimated": polar,
            "polar_mode": polar_mode,
        }

    def get_special_lagnas(self, date, time, tz, lat, lon):
        """
        Bhava / Hora / Ghati / Vighati / Sree / Varnada lagnas, plus Maandi/Gulika.

        BL/HL/GL start from the Sun at sunrise (Parashara / JHora):
          BL  +15° per hour from sunrise  (1 sign / 2 hours)
          HL  +30° per hour               (1 sign / hora)
          GL  +75° per hour               (1 sign / ghati)
        Sree Lagna = Lagna + (Moon elapsed in nakshatra / 13°20′) × 360°.
        Varnada = (lagna sign index + hora sign index + 1) % 12 at lagna degree.
        """
        tz_offset = self._parse_timezone(tz, date, time)
        jd = self._to_julian_day(date, time, tz_offset)
        flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_MOSEPH

        _cusps, ascmc, _hsys = self._houses_ex_safe(jd, lat, lon, "P")
        asc = ascmc[0]
        moon_pos = swe.calc_ut(jd, swe.MOON, flags)[0][0]

        ss = self.get_sunrise_sunset(date, lat, lon, tz)
        rise_jd = ss["sunrise_jd"]
        set_jd = ss["sunset_jd"]
        sun_at_rise = swe.calc_ut(rise_jd, swe.SUN, flags)[0][0]

        hours_from_rise = (jd - rise_jd) * 24.0
        if hours_from_rise < 0:
            hours_from_rise += 24.0

        bhava_lagna = (sun_at_rise + hours_from_rise * 15.0) % 360.0
        hora_lagna = (sun_at_rise + hours_from_rise * 30.0) % 360.0
        ghati_lagna = (sun_at_rise + hours_from_rise * 75.0) % 360.0
        # 1 vighati = 24 seconds; 1 sign per vighati = 4500°/hour
        vighati_lagna = (sun_at_rise + hours_from_rise * 4500.0) % 360.0

        # Sree Lagna
        degree_in_nak = moon_pos % NAKSHATRA_SPAN
        sree_lagna = (asc + (degree_in_nak / NAKSHATRA_SPAN) * 360.0) % 360.0

        # Varnada: odd/odd signs add 1-based counts
        lagna_idx = int(asc / 30) % 12
        hl_idx = int(hora_lagna / 30) % 12
        varnada_idx = (lagna_idx + hl_idx + 1) % 12
        varnada_lagna = varnada_idx * 30.0 + (asc % 30)

        # Maandi / Gulika — Saturn's 1/8 portion of day (weekday from local date)
        parts = date.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        # 0=Sunday ... 6=Saturday. datetime: 0=Monday, so convert.
        from datetime import datetime as _dt
        weekday_sun = (_dt(year, month, day).weekday() + 1) % 7
        day_len = set_jd - rise_jd
        if day_len <= 0:
            day_len = 0.5
        # Saturn portion: Sunday=7th (idx 6) ... Saturday=1st (idx 0)
        segment = (6 - weekday_sun) % 7
        # Day birth uses day duration; night birth uses night duration.
        # Maandi is taken at the START of Saturn's segment.
        maandi_jd = rise_jd + segment * (day_len / 8.0)
        try:
            _mc, m_ascmc, _ = self._houses_ex_safe(maandi_jd, lat, lon, "P")
            maandi = m_ascmc[0]
        except Exception:
            maandi = (asc + (maandi_jd - jd) * 361.0) % 360.0
        # Gulika is often the same Saturn-portion rising; JHora splits them
        # slightly (Gulika earlier). Use start of portion for Gulika and
        # midpoint for Maandi to separate the two longitudes.
        gulika_jd = rise_jd + segment * (day_len / 8.0)
        maandi_jd = gulika_jd + (day_len / 16.0)
        try:
            _gc, g_ascmc, _ = self._houses_ex_safe(gulika_jd, lat, lon, "P")
            gulika = g_ascmc[0]
            _mc, m_ascmc, _ = self._houses_ex_safe(maandi_jd, lat, lon, "P")
            maandi = m_ascmc[0]
        except Exception:
            gulika = maandi

        return {
            "bhava_lagna": round(bhava_lagna, 6),
            "hora_lagna": round(hora_lagna, 6),
            "ghati_lagna": round(ghati_lagna, 6),
            "vighati_lagna": round(vighati_lagna, 6),
            "sree_lagna": round(sree_lagna, 6),
            "varnada_lagna": round(varnada_lagna, 6),
            "maandi": round(maandi, 6),
            "gulika": round(gulika, 6),
        }
