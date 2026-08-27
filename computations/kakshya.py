"""
kakshya.py — Kakshya (sub-divisions of Ashtakavarga signs).
Each sign is divided into 8 Kakshyas of 3°45' each.
The kakshya lords follow the order: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna.

When a planet transits a sign, the kakshya it occupies determines the
sub-period effect. The BAV contribution from that kakshya's lord determines
whether the transit is benefic (1) or malefic (0) in that sub-sector.

100% offline — pure arithmetic from planetary longitudes.
"""

from ..core.constants import SIGNS, SIGN_INDEX, PLANETS_7


# ═══════════════════════════════════════════
# KAKSHYA LORDS (fixed order per Parashara)
# ═══════════════════════════════════════════

# The 8 kakshya lords in order within each sign.
# Each kakshya = 3°45' = 3.75° (30° / 8)
KAKSHYA_LORDS = [
    "Saturn", "Jupiter", "Mars", "Sun",
    "Venus", "Mercury", "Moon", "Lagna"
]

KAKSHYA_SPAN = 30.0 / 8  # 3.75° per kakshya


# ═══════════════════════════════════════════
# KAKSHYA CALCULATION
# ═══════════════════════════════════════════

def get_kakshya(longitude):
    """
    Determine which kakshya a planet is in, based on its sidereal longitude.

    Args:
        longitude: sidereal longitude (0-360)

    Returns:
        dict with:
            sign: sign name
            kakshya_num: 1-8
            kakshya_lord: lord of the kakshya
            degree_in_kakshya: position within the kakshya (0-3.75)
            kakshya_start: starting degree of this kakshya in sign
            kakshya_end: ending degree of this kakshya in sign
    """
    longitude = longitude % 360.0
    sign_idx = int(longitude / 30)
    degree_in_sign = longitude - (sign_idx * 30)

    kakshya_num = int(degree_in_sign / KAKSHYA_SPAN)
    if kakshya_num >= 8:
        kakshya_num = 7  # Edge case at exactly 30°

    kakshya_lord = KAKSHYA_LORDS[kakshya_num]
    degree_in_kakshya = degree_in_sign - (kakshya_num * KAKSHYA_SPAN)
    kakshya_start = kakshya_num * KAKSHYA_SPAN
    kakshya_end = kakshya_start + KAKSHYA_SPAN

    return {
        "sign": SIGNS[sign_idx],
        "sign_index": sign_idx,
        "kakshya_num": kakshya_num + 1,  # 1-indexed
        "kakshya_lord": kakshya_lord,
        "degree_in_sign": round(degree_in_sign, 4),
        "degree_in_kakshya": round(degree_in_kakshya, 4),
        "kakshya_start": round(kakshya_start, 4),
        "kakshya_end": round(kakshya_end, 4),
    }


# ═══════════════════════════════════════════
# KAKSHYA MAP FOR A SIGN
# ═══════════════════════════════════════════

def calc_kakshya_map(sign_idx):
    """
    Generate the complete kakshya map for a sign.
    Shows all 8 kakshya divisions with their lords and degree ranges.

    Args:
        sign_idx: 0-based sign index (0=Aries, 11=Pisces)

    Returns:
        list of 8 kakshya dicts with:
            kakshya_num (1-8), lord, start_deg, end_deg
    """
    kakshya_map = []
    for i in range(8):
        start_deg = round(i * KAKSHYA_SPAN, 4)
        end_deg = round((i + 1) * KAKSHYA_SPAN, 4)
        kakshya_map.append({
            "kakshya_num": i + 1,
            "lord": KAKSHYA_LORDS[i],
            "start_deg": start_deg,
            "end_deg": end_deg,
            "sign": SIGNS[sign_idx],
        })
    return kakshya_map


# ═══════════════════════════════════════════
# KAKSHYA TRANSIT SCORING
# ═══════════════════════════════════════════

def score_kakshya_transit(planet, transit_longitude, natal_bav):
    """
    Score a transit using the Kakshya system.

    The kakshya lord of the transit position is checked against the BAV.
    If the BAV contribution from that kakshya lord is 1 (benefic dot),
    the transit gives good results in that sub-period.
    If 0, the results are unfavorable.

    Args:
        planet: transiting planet name (must be in PLANETS_7)
        transit_longitude: current sidereal longitude of the planet
        natal_bav: BAV data from natal chart (dict of planet -> sign -> score)

    Returns:
        dict with kakshya info, bav_contribution, and assessment
    """
    kakshya = get_kakshya(transit_longitude)
    kakshya_lord = kakshya["kakshya_lord"]
    transit_sign = kakshya["sign"]

    # BAV contribution lookup
    # In the BAV system, each planet has contributions from 7 planets + Lagna
    # The kakshya lord's contribution tells us if this sub-sector is benefic
    bav_contribution = None
    if planet in natal_bav:
        # BAV is stored as sign -> total, but we need individual contributions
        # For now, use the sign total / 8 as approximation
        # A proper implementation would store individual BAV contributions
        planet_bav_sign = natal_bav.get(planet, {}).get(transit_sign, 0)
        bav_contribution = planet_bav_sign  # Total BAV in this sign

    # Assessment based on kakshya lord nature
    assessment = "Neutral"
    if kakshya_lord == "Lagna":
        assessment = "Self-referential — depends on Lagna lord strength"
    elif kakshya_lord in ["Jupiter", "Venus"]:
        assessment = "Natural benefic kakshya — generally favorable"
    elif kakshya_lord in ["Saturn", "Mars"]:
        assessment = "Natural malefic kakshya — challenging"
    elif kakshya_lord in ["Sun", "Moon", "Mercury"]:
        assessment = "Conditional — depends on functional nature"

    return {
        "planet": planet,
        "transit_longitude": round(transit_longitude, 4),
        "sign": transit_sign,
        "kakshya_num": kakshya["kakshya_num"],
        "kakshya_lord": kakshya_lord,
        "degree_in_kakshya": kakshya["degree_in_kakshya"],
        "bav_sign_score": bav_contribution,
        "assessment": assessment,
    }


# ═══════════════════════════════════════════
# ALL KAKSHYAS FOR A CHART
# ═══════════════════════════════════════════

def calc_natal_kakshyas(chart):
    """
    Calculate the kakshya position of every planet in the natal chart.

    Args:
        chart: BirthChart object

    Returns:
        dict of planet -> kakshya data
    """
    result = {}
    for planet in PLANETS_7 + ["Rahu", "Ketu"]:
        pos = chart.positions.get(planet, {})
        if not pos or isinstance(pos, (float, int)):
            continue

        longitude = pos.get("longitude", 0)
        kakshya = get_kakshya(longitude)
        result[planet] = kakshya

    # Also calculate for Lagna
    lagna_pos = chart.positions.get("Lagna", {})
    if lagna_pos and isinstance(lagna_pos, dict):
        lagna_long = lagna_pos.get("longitude", 0)
        result["Lagna"] = get_kakshya(lagna_long)

    return result


# ═══════════════════════════════════════════
# KAKSHYA TIMING (sub-period within transit)
# ═══════════════════════════════════════════

def calc_kakshya_timing(planet, sign_idx, transit_speed_deg_per_day=None):
    """
    Calculate approximate timing for each kakshya within a sign transit.

    Each kakshya = 3°45'. If we know the planet's average daily motion,
    we can estimate how many days each kakshya takes.

    Args:
        planet: planet name
        sign_idx: sign being transited
        transit_speed_deg_per_day: average daily motion (default: use typical speeds)

    Returns:
        list of 8 dicts with kakshya_num, lord, approx_days
    """
    # Average daily motions (degrees per day, approximate)
    AVG_SPEED = {
        "Sun": 0.9856, "Moon": 13.176, "Mars": 0.524,
        "Mercury": 1.383, "Jupiter": 0.0831, "Venus": 1.20,
        "Saturn": 0.0335, "Rahu": 0.0529, "Ketu": 0.0529,
    }

    speed = transit_speed_deg_per_day or AVG_SPEED.get(planet, 1.0)
    days_per_kakshya = KAKSHYA_SPAN / speed if speed > 0 else 0

    timing = []
    for i in range(8):
        timing.append({
            "kakshya_num": i + 1,
            "lord": KAKSHYA_LORDS[i],
            "approx_days": round(days_per_kakshya, 2),
            "sign": SIGNS[sign_idx],
        })

    return timing


# ═══════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════

def format_kakshya_map(sign_idx):
    """Format kakshya map for a sign as readable text."""
    kakshya_map = calc_kakshya_map(sign_idx)
    lines = [f"=== Kakshya Map: {SIGNS[sign_idx]} ===\n"]

    for k in kakshya_map:
        lines.append(
            f"  K{k['kakshya_num']}: {k['lord']:<10} "
            f"{k['start_deg']:>6.2f}° — {k['end_deg']:>6.2f}°"
        )

    return "\n".join(lines)


def format_natal_kakshyas(kakshyas):
    """Format natal kakshya positions as readable text."""
    lines = ["=== Natal Kakshya Positions ===\n"]

    for planet, k in kakshyas.items():
        lines.append(
            f"  {planet:<10} {k['sign']:<13} K{k['kakshya_num']} "
            f"({k['kakshya_lord']:<10}) "
            f"at {k['degree_in_sign']:.2f}°"
        )

    return "\n".join(lines)
