"""
special_points.py — Yogi/Avayogi/SahaYogi, Bhrigu Bindu, Sahams (Vivaha/Parashara/Fortuna),
Maandi/Gulika calculations.
100% offline — pure arithmetic from planetary longitudes.
"""

import math
from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS,
    NAKSHATRAS, NAKSHATRA_SPAN,
    VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS, VIMSHOTTARI_TOTAL,
)


# ═══════════════════════════════════════════
# YOGI POINT / YOGI / AVAYOGI / SAHAYOGI
# ═══════════════════════════════════════════

# Relationship between nakshatra lords and planets for Yogi/Avayogi
AVAYOGI_FROM_YOGI = {
    "Sun": "Saturn",
    "Moon": "Mercury",
    "Mars": "Jupiter",
    "Mercury": "Moon",
    "Jupiter": "Mars",
    "Venus": "Ketu",
    "Saturn": "Sun",
    "Rahu": "Venus",
    "Ketu": "Rahu",
}

SAHAYOGI_FROM_YOGI = {
    "Sun": "Moon",
    "Moon": "Venus",
    "Mars": "Sun",
    "Mercury": "Venus",
    "Jupiter": "Sun",
    "Venus": "Mercury",
    "Saturn": "Venus",
    "Rahu": "Saturn",
    "Ketu": "Mars",
}


def calc_yogi_point(sun_long, moon_long):
    """
    Calculate Yogi Point, Yogi planet, Avayogi, and SahaYogi.
    
    Yogi Point = Sun longitude + Moon longitude + 93°20'
    The nakshatra lord of the Yogi Point = Yogi planet.
    
    Args:
        sun_long: sidereal longitude of Sun
        moon_long: sidereal longitude of Moon
        
    Returns:
        dict with yogi_point, yogi, avayogi, sahayogi, yogi_nakshatra
    """
    # rules.md §8: Yogi = Sun+Moon+93°20′; SahaYogi +186°40′; Avayogi +280°.
    yogi_point = (sun_long + moon_long + 93.0 + 20.0 / 60.0) % 360.0
    sahayogi_point = (sun_long + moon_long + 186.0 + 40.0 / 60.0) % 360.0
    avayogi_point = (sun_long + moon_long + 280.0) % 360.0

    def _nak_lord(longitude):
        idx = min(int((longitude % 360.0) / NAKSHATRA_SPAN), 26)
        return NAKSHATRAS[idx]

    yogi_nak = _nak_lord(yogi_point)
    yogi_planet = yogi_nak["lord"]
    sahayogi = _nak_lord(sahayogi_point)["lord"]
    avayogi = _nak_lord(avayogi_point)["lord"]

    sign_idx = int(yogi_point / 30)
    degree_in_sign = yogi_point - (sign_idx * 30)
    yogi_sign = SIGNS[sign_idx]

    # Duplicate Yogi check: if the nakshatra lord of the AVAYOGI's nakshatra
    # is the same as the Yogi planet, there's a "duplicate" paradox
    duplicate_yogi = None
    # This is chart-specific — check if avayogi's nakshatra lord = yogi planet
    # (handled at chart level, not here)

    return {
        "yogi_point": round(yogi_point, 4),
        "yogi_point_sign": yogi_sign,
        "yogi_point_degree": round(degree_in_sign, 4),
        "yogi_point_dms": f"{int(degree_in_sign)}d{int((degree_in_sign % 1) * 60)}m",
        "yogi_nakshatra": yogi_nak["name"],
        "yogi": yogi_planet,
        "avayogi": avayogi,
        "sahayogi": sahayogi,
    }


# ═══════════════════════════════════════════
# BHRIGU BINDU (BB)
# ═══════════════════════════════════════════

def calc_bhrigu_bindu(rahu_long, moon_long):
    """
    Calculate Bhrigu Bindu (BB).
    
    BB = midpoint of Rahu and Moon.
    Formula: (Rahu_long + Moon_long) / 2
    If the result > 360, subtract 360.
    
    Some traditions: BB = (Rahu + Moon) / 2 if < 180 apart,
    otherwise add 180 and divide by 2.
    
    Args:
        rahu_long: sidereal longitude of Rahu
        moon_long: sidereal longitude of Moon
        
    Returns:
        dict with bb_longitude, sign, degree, nakshatra
    """
    # Standard midpoint
    bb = (rahu_long + moon_long) / 2.0

    # Ensure we take the shorter arc
    diff = abs(rahu_long - moon_long)
    if diff > 180:
        bb = (bb + 180.0) % 360.0

    bb = bb % 360.0

    sign_idx = int(bb / 30)
    degree_in_sign = bb - (sign_idx * 30)

    # Nakshatra
    nak_idx = int(bb / NAKSHATRA_SPAN)
    nak_idx = min(nak_idx, 26)
    bb_nak = NAKSHATRAS[nak_idx]

    return {
        "longitude": round(bb, 4),
        "sign": SIGNS[sign_idx],
        "degree_in_sign": round(degree_in_sign, 4),
        "dms": f"{int(degree_in_sign)}d{int((degree_in_sign % 1) * 60):02d}m",
        "nakshatra": bb_nak["name"],
        "nakshatra_lord": bb_nak["lord"],
        "house_significance": "BB transit activation triggers major events",
    }


# ═══════════════════════════════════════════
# VIVAHA SAHAM (Marriage Saham — Tajika)
# ═══════════════════════════════════════════

def calc_vivaha_saham(moon_long, venus_long, asc_long, is_day=True):
    """
    Calculate Tajika Vivaha Saham (Marriage Sensitive Point).
    
    Classical Tajika Neelakanthi Formula:
      Day Birth  : Lagna + Moon - Venus
      Night Birth: Lagna + Venus - Moon
      (If target is not within 30° of Lagna, some schools add 30°, but standard is exact subtraction)
    
    Args:
        moon_long: Moon's sidereal longitude
        venus_long: Venus's sidereal longitude
        asc_long: Ascendant's sidereal longitude
        is_day: True for day birth, False for night birth
        
    Returns:
        dict with longitude, sign, degree, nakshatra
    """
    if is_day:
        vs = (asc_long + moon_long - venus_long) % 360.0
        formula = "ASC + Moon - Venus (day)"
    else:
        vs = (asc_long + venus_long - moon_long) % 360.0
        formula = "ASC + Venus - Moon (night)"

    sign_idx = int(vs / 30)
    degree_in_sign = vs - (sign_idx * 30)

    nak_idx = int(vs / NAKSHATRA_SPAN)
    nak_idx = min(nak_idx, 26)

    return {
        "longitude": round(vs, 4),
        "sign": SIGNS[sign_idx],
        "degree_in_sign": round(degree_in_sign, 4),
        "dms": f"{int(degree_in_sign)}d{int((degree_in_sign % 1) * 60):02d}m",
        "nakshatra": NAKSHATRAS[nak_idx]["name"],
        "formula": formula,
    }


# ═══════════════════════════════════════════
# PARASHARA VIVAHA SAHAM
# ═══════════════════════════════════════════

def calc_parashara_vivaha_saham(asc_long, venus_long, jupiter_long):
    """
    Calculate Parashara Vivaha Saham.
    
    Formula: ASC + Venus - Jupiter
    
    Args:
        asc_long: Ascendant's sidereal longitude
        venus_long: Venus's sidereal longitude
        jupiter_long: Jupiter's sidereal longitude
        
    Returns:
        dict with longitude, sign, degree, nakshatra
    """
    pvs = (asc_long + venus_long - jupiter_long) % 360.0

    sign_idx = int(pvs / 30)
    degree_in_sign = pvs - (sign_idx * 30)

    nak_idx = int(pvs / NAKSHATRA_SPAN)
    nak_idx = min(nak_idx, 26)

    return {
        "longitude": round(pvs, 4),
        "sign": SIGNS[sign_idx],
        "degree_in_sign": round(degree_in_sign, 4),
        "dms": f"{int(degree_in_sign)}d{int((degree_in_sign % 1) * 60):02d}m",
        "nakshatra": NAKSHATRAS[nak_idx]["name"],
        "formula": "ASC + Venus - Jupiter",
    }


# ═══════════════════════════════════════════
# PART OF FORTUNE (Fortuna)
# ═══════════════════════════════════════════

def calc_part_of_fortune(asc_long, sun_long, moon_long, is_day=True):
    """
    Calculate the Part of Fortune (Pars Fortunae / Fortuna).
    
    Day formula: ASC + Moon - Sun
    Night formula: ASC + Sun - Moon
    
    Args:
        asc_long, sun_long, moon_long: sidereal longitudes
        is_day: True for day birth, False for night birth
        
    Returns:
        dict with longitude, sign, degree
    """
    if is_day:
        pof = (asc_long + moon_long - sun_long) % 360.0
        formula = "ASC + Moon - Sun (day)"
    else:
        pof = (asc_long + sun_long - moon_long) % 360.0
        formula = "ASC + Sun - Moon (night)"

    sign_idx = int(pof / 30)
    degree_in_sign = pof - (sign_idx * 30)

    nak_idx = int(pof / NAKSHATRA_SPAN)
    nak_idx = min(nak_idx, 26)

    return {
        "longitude": round(pof, 4),
        "sign": SIGNS[sign_idx],
        "degree_in_sign": round(degree_in_sign, 4),
        "dms": f"{int(degree_in_sign)}d{int((degree_in_sign % 1) * 60):02d}m",
        "nakshatra": NAKSHATRAS[nak_idx]["name"],
        "formula": formula,
    }


# ═══════════════════════════════════════════
# MAANDI / GULIKA
# ═══════════════════════════════════════════

# Maandi risings per weekday (hours after sunrise, in 1/8 of day length)
# Day = Sunday(0) through Saturday(6)
# Maandi rise segment: Saturn's portion of the day
MAANDI_SEGMENTS = {
    0: 6,  # Sunday: Saturn's segment is 7th (index 6)
    1: 5,  # Monday
    2: 4,  # Tuesday
    3: 3,  # Wednesday
    4: 2,  # Thursday
    5: 1,  # Friday
    6: 0,  # Saturday
}


def calc_maandi_gulika(birth_jd, sunrise_jd, sunset_jd, lat, lon, weekday):
    """
    Calculate Maandi and Gulika positions.
    
    Maandi = the longitude of the ascending point at Saturn's
    portion of the day/night.
    
    Simplified: Returns the approximate longitude based on
    the time segment and rising sign at that moment.
    
    Args:
        birth_jd: Julian Day of birth
        sunrise_jd: JD of sunrise
        sunset_jd: JD of sunset
        lat, lon: birth coordinates
        weekday: 0=Sunday through 6=Saturday
        
    Returns:
        dict with maandi and gulika positions (approximate)
    """
    # Day duration in JD units
    day_duration = sunset_jd - sunrise_jd
    segment_duration = day_duration / 8.0

    # Maandi = ascendant at the start of Saturn's segment
    segment = MAANDI_SEGMENTS.get(weekday, 6)
    maandi_jd = sunrise_jd + segment * segment_duration

    # Calculate ascending sign at Maandi time
    # This would require swe.houses_ex() call; simplified here
    # Approximate: use birth ascendant + rotation
    time_offset = maandi_jd - birth_jd
    # Sidereal rotation: ~361° per day
    asc_rotation = time_offset * 361.0
    # This is an approximation — full implementation needs swe

    return {
        "maandi_jd": round(maandi_jd, 6),
        "gulika_jd": round(maandi_jd, 6),
        "segment": segment,
        "note": "Approximate — full calculation requires swe.houses_ex at Maandi time",
    }


# ═══════════════════════════════════════════
# ALL SPECIAL POINTS (convenience)
# ═══════════════════════════════════════════

def calc_all_special_points(chart):
    """
    Calculate all special points for a birth chart.
    
    Args:
        chart: BirthChart object
        
    Returns:
        dict with yogi, bb, vivaha_saham, parashara_saham, part_of_fortune
    """
    positions = chart.positions
    sun = positions.get("Sun", {}).get("longitude", 0)
    moon = positions.get("Moon", {}).get("longitude", 0)
    asc = positions.get("Lagna", {}).get("longitude", 0)
    venus = positions.get("Venus", {}).get("longitude", 0)
    jupiter = positions.get("Jupiter", {}).get("longitude", 0)
    rahu = positions.get("Rahu", {}).get("longitude", 0)

    yogi = calc_yogi_point(sun, moon)
    bb = calc_bhrigu_bindu(rahu, moon)

    is_day = True
    ss = getattr(chart, "sunrise_sunset", None) or {}
    if ss.get("is_day_birth") is not None:
        is_day = bool(ss["is_day_birth"])
    vs = calc_vivaha_saham(moon, venus, asc, is_day)
    pvs = calc_parashara_vivaha_saham(asc, venus, jupiter)
    pof = calc_part_of_fortune(asc, sun, moon, is_day)

    sahams = calc_extended_sahams(chart, is_day)

    return {
        "yogi": yogi,
        "bhrigu_bindu": bb,
        "vivaha_saham_tajika": vs,
        "vivaha_saham_parashara": pvs,
        "part_of_fortune": pof,
        "sahams": sahams,
    }


def _pack_long(lam, formula=""):
    lam = lam % 360.0
    sidx = int(lam / 30) % 12
    deg = lam - sidx * 30
    nak_idx = min(int(lam / NAKSHATRA_SPAN), 26)
    return {
        "longitude": round(lam, 4),
        "sign": SIGNS[sidx],
        "degree_in_sign": round(deg, 4),
        "nakshatra": NAKSHATRAS[nak_idx]["name"],
        "formula": formula,
    }


def calc_extended_sahams(chart, is_day=True):
    """16 Tajika sahams. Day formula ASC+A-B; night swaps A and B. §16."""
    p = chart.positions
    asc = p["Lagna"]["longitude"]
    sun, moon = p["Sun"]["longitude"], p["Moon"]["longitude"]
    ven = p["Venus"]["longitude"]
    jup = p["Jupiter"]["longitude"]
    sat = p["Saturn"]["longitude"]
    mar = p["Mars"]["longitude"]
    mer = p["Mercury"]["longitude"]
    cusp8 = (asc + 210.0) % 360.0
    lord9 = chart.lordships.get(9)
    long9 = p.get(lord9, {}).get("longitude", 0.0) if lord9 else 0.0
    cancer_15 = 90.0 + 15.0  # 15° Cancer

    specs = {
        "Punya": (moon, sun),
        "Vidya": (sun, moon),
        "Vivaha": (ven, moon),
        "Putra": (jup, moon),
        "Pitri": (sat, sun),
        "Matri": (moon, ven),
        "Bhratri": (jup, sat),
        "Roga": (sat, mar),
        "Mrityu": (moon, cusp8),
        "Karma": (mar, mer),
        "Paradesa": (sat, long9),
        "Bandhu": (mer, moon),
        "Jalapatna": (cancer_15, sat),
        "Mangal": (jup, mar),
        "Sastra": (sat, mar),
        "Gaurava": (jup, sun),
    }
    out = {}
    for name, (a, b) in specs.items():
        if is_day:
            lam = (asc + a - b) % 360.0
            formula = "ASC + A - B (day)"
        else:
            lam = (asc + b - a) % 360.0
            formula = "ASC + B - A (night)"
        out[name] = _pack_long(lam, formula)
    return out
