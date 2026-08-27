"""
tajika.py — Tajika Varshaphala (Annual Chart / Solar Return) computations.
Solar return finder, Varsha Kundali, Muntha, Tajika aspects & yogas.
100% offline — uses Swiss Ephemeris via Ephemeris wrapper.

Tajika is the annual horoscopy system (Varshaphala) adapted from
Arabic/Tajik sources into the Vedic framework. It uses the exact moment
the Sun returns to its natal longitude each year to build an annual chart.
"""

import math
from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_7, PLANETS_9,
    NAKSHATRAS, NAKSHATRA_SPAN,
)
from ..core.ephemeris import Ephemeris
from ..core.mapping import sign_to_house, TRIKONA_HOUSES, KENDRA_HOUSES, DUSTHANA_HOUSES


# ═══════════════════════════════════════════
# SOLAR RETURN (Varsha Pravesh)
# ═══════════════════════════════════════════

def find_solar_return_jd(birth_sun_long, year, ephe):
    """
    Find the exact Julian Day when the Sun returns to its birth longitude
    in a given year. This is the Varsha Pravesh (annual chart) moment.

    Uses iterative Newton-Raphson-like refinement:
    1. Start from approximate date (birthday)
    2. Calculate Sun's position
    3. Adjust JD by the angular difference / Sun's daily speed

    Args:
        birth_sun_long: natal Sun's sidereal longitude
        year: year for which to find solar return
        ephe: Ephemeris instance

    Returns:
        float: Julian Day of the solar return
    """
    import swisseph as swe

    # Start from approximate date: same month/day as birth in target year
    # Use Jan 1 of the year as a safe starting point, then search forward
    jd_start = swe.julday(year, 1, 1, 12.0)

    # Sun takes ~365.25 days to complete a cycle
    # Start searching from about 30 days before expected return
    jd = jd_start

    # Find approximate position first
    for _ in range(400):  # Search day by day through the year
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        result, _ = swe.calc_ut(jd, swe.SUN, flags)
        sun_long = result[0] % 360.0
        sun_speed = result[3]  # degrees per day

        diff = (birth_sun_long - sun_long + 360) % 360
        if diff > 180:
            diff -= 360

        # If within 1 degree, start refining
        if abs(diff) < 1.0:
            break

        # Advance by estimated days
        if sun_speed > 0:
            jd += diff / sun_speed
        else:
            jd += 1  # Fallback

    # Refine to high precision
    for _ in range(50):
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        result, _ = swe.calc_ut(jd, swe.SUN, flags)
        sun_long = result[0] % 360.0
        sun_speed = result[3]

        diff = (birth_sun_long - sun_long + 360) % 360
        if diff > 180:
            diff -= 360

        if abs(diff) < 0.00001:  # ~0.036 arc-seconds precision
            break

        if sun_speed != 0:
            jd += diff / sun_speed
        else:
            break

    return jd


def _jd_to_date_time(jd):
    """Convert Julian Day to date and time strings."""
    import swisseph as swe
    year, month, day, ut_hours = swe.revjul(jd)
    hour = int(ut_hours)
    minute = int((ut_hours - hour) * 60)
    second = int(((ut_hours - hour) * 60 - minute) * 60)
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
    return date_str, time_str


# ═══════════════════════════════════════════
# VARSHA KUNDALI (Annual Chart)
# ═══════════════════════════════════════════

def build_varsha_chart(birth_data, year, ephe_path=None, ayanamsha="lahiri",
                       natal_sun_long=None, natal_lagna_idx=None, ephe=None):
    """
    Build a Varsha Kundali (annual chart) for a given year.

    This calculates the planetary positions at the exact moment the Sun
    returns to its natal longitude. The chart for that moment is the
    annual horoscope.

    Args:
        birth_data: dict with date, time, tz, lat, lon, name
        year: year for the annual chart
        ephe_path: Swiss Ephemeris data path
        ayanamsha: sidereal system

    Returns:
        dict with:
            solar_return_jd: Julian Day of solar return
            solar_return_date: date string
            solar_return_time: time string (UT)
            positions: planetary positions at solar return
            muntha: Muntha sign and details
            varsha_lagna: Ascendant of the annual chart
    """
    if ephe is None:
        ephe = Ephemeris(ephe_path=ephe_path, ayanamsha=ayanamsha)

    if natal_sun_long is None or natal_lagna_idx is None:
        natal_pos = ephe.get_planet_positions(
            birth_data["date"], birth_data["time"], birth_data["tz"],
            birth_data["lat"], birth_data["lon"]
        )
        birth_sun_long = natal_pos.get("Sun", {}).get("longitude", 0)
        birth_lagna_idx = SIGN_INDEX[natal_pos.get("Lagna", {}).get("sign", "Aries")]
    else:
        birth_sun_long = natal_sun_long
        birth_lagna_idx = natal_lagna_idx

    # Find solar return moment
    sr_jd = find_solar_return_jd(birth_sun_long, year, ephe)
    sr_date, sr_time = _jd_to_date_time(sr_jd)

    # Calculate positions at solar return moment
    sr_positions = ephe.get_planet_positions(
        sr_date, sr_time, "+00:00",  # JD is already in UT
        birth_data["lat"], birth_data["lon"]
    )

    # Calculate age (for Muntha)
    birth_year = int(birth_data["date"].split("-")[0])
    age = year - birth_year

    # Muntha
    muntha = calc_muntha(birth_lagna_idx, age)

    # Varsha Lagna
    varsha_lagna = sr_positions.get("Lagna", {}).get("sign", "Unknown")

    return {
        "year": year,
        "age": age,
        "solar_return_jd": round(sr_jd, 6),
        "solar_return_date": sr_date,
        "solar_return_time_ut": sr_time,
        "birth_sun_longitude": round(birth_sun_long, 4),
        "positions": sr_positions,
        "varsha_lagna": varsha_lagna,
        "muntha": muntha,
    }


# ═══════════════════════════════════════════
# MUNTHA (Progressed Sign)
# ═══════════════════════════════════════════

def calc_muntha(birth_lagna_idx, age):
    """
    Calculate Muntha — the progressed sign.

    Muntha starts from the birth Lagna and advances 1 sign per year.
    It indicates the focus area for the year.

    Formula: Muntha sign = (Lagna index + age) % 12

    Args:
        birth_lagna_idx: 0-based index of birth Lagna sign
        age: current age (years since birth)

    Returns:
        dict with muntha_sign, sign_index, house_from_lagna
    """
    muntha_idx = (birth_lagna_idx + age) % 12
    house_from_lagna = sign_to_house(muntha_idx, birth_lagna_idx)

    muntha_lord = SIGN_LORDS[SIGNS[muntha_idx]]

    # Muntha in Kendra/Trikona = good year
    good_houses = set(KENDRA_HOUSES) | set(TRIKONA_HOUSES)
    bad_houses = set(DUSTHANA_HOUSES)

    if house_from_lagna in good_houses:
        effect = "Favorable — Muntha in auspicious house"
    elif house_from_lagna in bad_houses:
        effect = "Challenging — Muntha in difficult house"
    else:
        effect = "Neutral — moderate year"

    return {
        "muntha_sign": SIGNS[muntha_idx],
        "sign_index": muntha_idx,
        "house_from_lagna": house_from_lagna,
        "muntha_lord": muntha_lord,
        "effect": effect,
    }


# ═══════════════════════════════════════════
# TAJIKA ASPECTS (degree-based, not sign-based)
# ═══════════════════════════════════════════

# Tajika aspects use orbs and exact degree separations (like Western)
# rather than sign-based aspects (like Parashari)
TAJIKA_ASPECTS = {
    "conjunction": {"angle": 0, "orb": 8},
    "sextile":     {"angle": 60, "orb": 5},
    "square":      {"angle": 90, "orb": 7},
    "trine":       {"angle": 120, "orb": 7},
    "opposition":  {"angle": 180, "orb": 8},
}


def check_tajika_aspect(long1, long2, speed1=1.0, speed2=0.5):
    """
    Check for Tajika aspects between two planets using degree-based orbs.

    Args:
        long1: longitude of faster planet
        long2: longitude of slower planet
        speed1: daily speed of planet 1 (deg/day)
        speed2: daily speed of planet 2 (deg/day)

    Returns:
        dict with aspect_type, separation, applying/separating, or None if no aspect
    """
    diff = abs(long1 - long2)
    if diff > 180:
        diff = 360 - diff

    for aspect_name, aspect_data in TAJIKA_ASPECTS.items():
        angle = aspect_data["angle"]
        orb = aspect_data["orb"]

        separation = abs(diff - angle)
        if separation <= orb:
            # Determine if applying or separating
            # Applying = faster planet moving toward exact aspect
            applying = speed1 > speed2

            return {
                "aspect": aspect_name,
                "angle": angle,
                "separation": round(separation, 4),
                "orb": orb,
                "applying": applying,
                "status": "Applying" if applying else "Separating",
            }

    return None


# ═══════════════════════════════════════════
# TAJIKA YOGAS (Itthasala, Ishrafa, etc.)
# ═══════════════════════════════════════════

def check_itthasala(long_faster, long_slower, speed_faster, speed_slower):
    """
    Check for Itthasala Yoga (application).

    Itthasala occurs when:
    1. The faster planet is behind the slower planet (in longitude)
    2. The faster planet is applying (moving toward) the slower
    3. Both are within orb of an aspect
    4. Neither planet is combust

    This is the most important Tajika yoga — indicates fulfillment
    of the house signification.

    Args:
        long_faster: longitude of faster planet
        long_slower: longitude of slower planet
        speed_faster: daily speed of faster planet
        speed_slower: daily speed of slower planet

    Returns:
        dict with yoga details, or None
    """
    aspect = check_tajika_aspect(long_faster, long_slower, speed_faster, speed_slower)
    if not aspect:
        return None

    if aspect["applying"]:
        return {
            "yoga": "Itthasala",
            "meaning": "Application — event will materialize",
            "aspect_type": aspect["aspect"],
            "separation": aspect["separation"],
            "strength": "Strong" if aspect["separation"] < 3 else "Moderate",
        }

    return None


def check_ishrafa(long_faster, long_slower, speed_faster, speed_slower):
    """
    Check for Ishrafa Yoga (separation).

    Ishrafa is the opposite of Itthasala — the faster planet has
    already passed the exact aspect and is separating.
    This indicates the matter is past or denied.

    Returns:
        dict with yoga details, or None
    """
    aspect = check_tajika_aspect(long_faster, long_slower, speed_faster, speed_slower)
    if not aspect:
        return None

    if not aspect["applying"]:
        return {
            "yoga": "Ishrafa",
            "meaning": "Separation — event has passed or is denied",
            "aspect_type": aspect["aspect"],
            "separation": aspect["separation"],
        }

    return None


def check_nakta(long1, long2, speed1, speed2, long3, speed3):
    """
    Check for Nakta Yoga (translation of light).

    Nakta occurs when two significators are not in aspect,
    but a third (faster) planet separates from one and applies to the other,
    carrying the "light" between them.

    Args:
        long1, long2: longitudes of the two main significators
        speed1, speed2: speeds of the main significators
        long3, speed3: longitude and speed of the potential translator

    Returns:
        dict with yoga details, or None
    """
    # Check if planet3 is separating from planet1
    asp_31 = check_tajika_aspect(long3, long1, speed3, speed1)
    # Check if planet3 is applying to planet2
    asp_32 = check_tajika_aspect(long3, long2, speed3, speed2)

    if asp_31 and asp_32:
        if not asp_31["applying"] and asp_32["applying"]:
            return {
                "yoga": "Nakta",
                "meaning": "Translation of light — mediator connects the two",
                "separating_from": asp_31["aspect"],
                "applying_to": asp_32["aspect"],
            }

    return None


def check_yamaya(long1, long2, speed1, speed2):
    """
    Check for Yamaya Yoga (prohibition/refusal).

    Yamaya occurs when two planets are applying to aspect,
    but a third planet perfects an aspect with the slower planet
    BEFORE the faster planet can reach it.

    Simplified version: checks if the aspect is very wide (almost out of orb)
    and the applying planet is slow — indicating the matter won't materialize.

    Returns:
        dict with yoga details, or None
    """
    aspect = check_tajika_aspect(long1, long2, speed1, speed2)
    if not aspect:
        return None

    if aspect["applying"] and aspect["separation"] > aspect["orb"] * 0.75:
        return {
            "yoga": "Yamaya",
            "meaning": "Prohibition — matter is blocked or delayed",
            "aspect_type": aspect["aspect"],
            "separation": aspect["separation"],
            "orb_remaining": round(aspect["orb"] - aspect["separation"], 2),
        }

    return None


# ═══════════════════════════════════════════
# ANNUAL YEAR LORD (Varshesha)
# ═══════════════════════════════════════════

# The 7 weekday lords rule years in a specific cycle
YEAR_LORDS_CYCLE = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]


def calc_varshesha(birth_weekday, age):
    """
    Calculate the Varshesha (Year Lord) for a given year.

    The year lord cycles through the weekday lords starting from
    the birth weekday lord.

    Args:
        birth_weekday: 0=Sunday through 6=Saturday
        age: current age

    Returns:
        dict with varshesha (year lord), strength notes
    """
    # Weekday -> starting lord index
    weekday_lord_idx = {
        0: 0,  # Sunday -> Sun
        1: 3,  # Monday -> Moon
        2: 6,  # Tuesday -> Mars
        3: 2,  # Wednesday -> Mercury
        4: 5,  # Thursday -> Jupiter
        5: 1,  # Friday -> Venus
        6: 4,  # Saturday -> Saturn
    }

    start_idx = weekday_lord_idx.get(birth_weekday, 0)
    lord_idx = (start_idx + age) % 7
    varshesha = YEAR_LORDS_CYCLE[lord_idx]

    return {
        "varshesha": varshesha,
        "year_lord": varshesha,
        "age": age,
        "note": f"{varshesha} rules this year — check its strength in Varsha Kundali",
    }


# ═══════════════════════════════════════════
# MASTER TAJIKA ANALYSIS
# ═══════════════════════════════════════════

def calc_tajika_analysis(birth_data, year, ephe_path=None, ayanamsha="lahiri",
                         natal_sun_long=None, natal_lagna_idx=None, ephe=None):
    """
    Complete Tajika analysis for a given year.

    Args:
        birth_data: dict with date, time, tz, lat, lon
        year: target year
        ephe_path: Swiss Ephemeris data path
        ayanamsha: sidereal system

    Returns:
        dict with varsha_chart, muntha, tajika_yogas, year_lord
    """
    varsha = build_varsha_chart(
        birth_data, year, ephe_path, ayanamsha,
        natal_sun_long=natal_sun_long,
        natal_lagna_idx=natal_lagna_idx,
        ephe=ephe,
    )

    # Calculate weekday of birth for Varshesha
    from datetime import datetime
    birth_dt = datetime.strptime(birth_data["date"], "%Y-%m-%d")
    birth_weekday = birth_dt.weekday()
    # Python weekday: 0=Mon, 6=Sun -> convert to 0=Sun
    birth_weekday_sun = (birth_weekday + 1) % 7

    varshesha = calc_varshesha(birth_weekday_sun, varsha["age"])

    # Check Tajika yogas between key planet pairs in the Varsha chart
    tajika_yogas = []
    sr_pos = varsha["positions"]

    # Average daily speeds for reference
    SPEEDS = {
        "Sun": 0.9856, "Moon": 13.176, "Mars": 0.524,
        "Mercury": 1.383, "Jupiter": 0.0831, "Venus": 1.20,
        "Saturn": 0.0335,
    }

    # Check Itthasala/Ishrafa between all planet pairs
    checked_pairs = set()
    for p1 in PLANETS_7:
        for p2 in PLANETS_7:
            if p1 >= p2:
                continue
            pair = (p1, p2)
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            pos1 = sr_pos.get(p1, {})
            pos2 = sr_pos.get(p2, {})
            if not isinstance(pos1, dict) or not isinstance(pos2, dict):
                continue

            l1 = pos1.get("longitude", 0)
            l2 = pos2.get("longitude", 0)
            s1 = SPEEDS.get(p1, 1.0)
            s2 = SPEEDS.get(p2, 1.0)

            # Ensure faster planet is planet with higher speed
            if s1 > s2:
                faster, slower = p1, p2
                lf, ls, sf, ss = l1, l2, s1, s2
            else:
                faster, slower = p2, p1
                lf, ls, sf, ss = l2, l1, s2, s1

            itthasala = check_itthasala(lf, ls, sf, ss)
            if itthasala:
                itthasala["faster_planet"] = faster
                itthasala["slower_planet"] = slower
                tajika_yogas.append(itthasala)

            ishrafa = check_ishrafa(lf, ls, sf, ss)
            if ishrafa:
                ishrafa["faster_planet"] = faster
                ishrafa["slower_planet"] = slower
                tajika_yogas.append(ishrafa)

    return {
        "varsha_chart": varsha,
        "varshesha": varshesha,
        "tajika_yogas": tajika_yogas,
        "tajika_yogas_count": len(tajika_yogas),
    }


# ═══════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════

def format_varsha_chart(varsha):
    """Format Varsha Kundali as readable text."""
    lines = []
    lines.append(f"=== Varsha Kundali (Year {varsha['year']}, Age {varsha['age']}) ===\n")
    lines.append(f"  Solar Return: {varsha['solar_return_date']} {varsha['solar_return_time_ut']} UT")
    lines.append(f"  Varsha Lagna: {varsha['varsha_lagna']}")

    muntha = varsha["muntha"]
    lines.append(f"  Muntha: {muntha['muntha_sign']} (H{muntha['house_from_lagna']}) — {muntha['effect']}")

    lines.append("\n  Positions:")
    sr_pos = varsha["positions"]
    for planet in ["Lagna"] + list(PLANETS_9):
        pos = sr_pos.get(planet, {})
        if not pos or not isinstance(pos, dict):
            continue
        retro = " (R)" if pos.get("retrograde") else ""
        lines.append(
            f"    {planet:<10} {pos.get('sign', '?'):<13} "
            f"{pos.get('dms', '?'):<10} {pos.get('nakshatra', '?'):<18}{retro}"
        )

    return "\n".join(lines)


def format_tajika_yogas(yogas):
    """Format Tajika yogas as readable text."""
    lines = ["=== Tajika Yogas ===\n"]

    if not yogas:
        lines.append("  No Tajika yogas detected.")
        return "\n".join(lines)

    for y in yogas:
        yoga_name = y.get("yoga", "Unknown")
        meaning = y.get("meaning", "")
        faster = y.get("faster_planet", "?")
        slower = y.get("slower_planet", "?")
        aspect = y.get("aspect_type", "?")
        sep = y.get("separation", 0)

        lines.append(
            f"  {yoga_name}: {faster}-{slower} ({aspect}, {sep:.1f}° sep) — {meaning}"
        )

    return "\n".join(lines)
