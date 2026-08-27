"""
arudhas.py — Arudha Padas (A1-A12), Upapada (UL), Darapada (A7),
Graha Arudhas, and all related Jaimini special lagnas.
100% offline — pure arithmetic from sign positions.

Arudha rule:
    Count from sign lord to lord's position = N houses.
    Count N houses from that sign = Arudha sign.
    
    Exception: If Arudha falls in same sign as source or 7th from it,
    take 10th from it instead (or 4th, per some schools).
"""

from ..core.constants import SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_7
from ..core.mapping import sign_to_house, house_to_sign_index


# ═══════════════════════════════════════════
# ARUDHA CALCULATION (Core formula)
# ═══════════════════════════════════════════

def _calc_arudha_sign(house_sign_idx, lord, positions, apply_exception=True):
    """
    Calculate arudha pada for a house sign.
    
    Rule: 
    1. Find the lord of the house sign
    2. Count how many signs the lord is from the house sign
    3. Count that many signs from the lord's position
    4. That's the arudha
    
    Exception: If arudha = house sign or 7th from it, use 10th from house instead.
    
    Args:
        house_sign_idx: 0-based sign index of the house
        lord: planet name that lords the sign
        positions: dict from ephemeris
        apply_exception: whether to apply the 1/7 exception rule
        
    Returns:
        int: 0-based sign index of the arudha
    """
    # Get lord's sign position
    lord_pos = positions.get(lord, {})
    if not lord_pos or isinstance(lord_pos, (float, int)):
        return house_sign_idx  # Fallback

    lord_sign_idx = lord_pos.get("sign_index", 0)

    # Count from house sign to lord's sign (1-indexed offset)
    offset = (lord_sign_idx - house_sign_idx) % 12
    if offset == 0:
        offset = 12  # Same sign counts as 12

    # Count same offset from lord's position
    arudha_idx = (lord_sign_idx + offset) % 12

    # Exception rule: if arudha = source sign or 7th from it
    if apply_exception:
        seventh = (house_sign_idx + 6) % 12
        if arudha_idx == house_sign_idx or arudha_idx == seventh:
            # Use 10th from the source house
            arudha_idx = (house_sign_idx + 9) % 12

    return arudha_idx


# ═══════════════════════════════════════════
# ARUDHA LAGNA (AL / A1)
# ═══════════════════════════════════════════

def calc_arudha_lagna(chart):
    """
    Calculate Arudha Lagna (AL / A1) — the image of the 1st house.
    
    Args:
        chart: BirthChart object
        
    Returns:
        dict with sign, sign_index, house_from_lagna
    """
    lagna_idx = chart.lagna_index
    lagna_lord = SIGN_LORDS[SIGNS[lagna_idx]]

    al_idx = _calc_arudha_sign(lagna_idx, lagna_lord, chart.positions)
    house_from_lagna = sign_to_house(al_idx, lagna_idx)

    return {
        "sign": SIGNS[al_idx],
        "sign_index": al_idx,
        "house_from_lagna": house_from_lagna,
        "lord": SIGN_LORDS[SIGNS[al_idx]],
    }


# ═══════════════════════════════════════════
# UPAPADA (UL / A12)
# ═══════════════════════════════════════════

def calc_upapada(chart, school="parashara"):
    """
    Calculate Upapada Lagna (UL) — arudha of the 12th house.
    
    Args:
        chart: BirthChart object
        school: "parashara" (standard) or "rath" (Sanjay Rath variant)
        
    Returns:
        dict with sign, sign_index, house_from_lagna
    """
    lagna_idx = chart.lagna_index
    # 12th house sign
    h12_idx = house_to_sign_index(12, lagna_idx)
    h12_lord = SIGN_LORDS[SIGNS[h12_idx]]

    ul_idx = _calc_arudha_sign(h12_idx, h12_lord, chart.positions)
    house_from_lagna = sign_to_house(ul_idx, lagna_idx)

    return {
        "sign": SIGNS[ul_idx],
        "sign_index": ul_idx,
        "house_from_lagna": house_from_lagna,
        "lord": SIGN_LORDS[SIGNS[ul_idx]],
        "school": school,
    }


# ═══════════════════════════════════════════
# DARAPADA (A7)
# ═══════════════════════════════════════════

def calc_darapada(chart):
    """
    Calculate Darapada (A7) — arudha of the 7th house.
    Important for marriage and partnership.
    
    Args:
        chart: BirthChart object
        
    Returns:
        dict with sign, sign_index, house_from_lagna
    """
    lagna_idx = chart.lagna_index
    h7_idx = house_to_sign_index(7, lagna_idx)
    h7_lord = SIGN_LORDS[SIGNS[h7_idx]]

    a7_idx = _calc_arudha_sign(h7_idx, h7_lord, chart.positions)
    house_from_lagna = sign_to_house(a7_idx, lagna_idx)

    return {
        "sign": SIGNS[a7_idx],
        "sign_index": a7_idx,
        "house_from_lagna": house_from_lagna,
        "lord": SIGN_LORDS[SIGNS[a7_idx]],
    }


# ═══════════════════════════════════════════
# ALL 12 ARUDHA PADAS (A1-A12)
# ═══════════════════════════════════════════

def calc_all_arudhas(chart):
    """
    Calculate all 12 Arudha Padas (A1 through A12).
    
    A1 = Arudha Lagna (AL)
    A2 = Dhana Pada
    A3 = Vikrama Pada
    A4 = Sukha Pada
    A5 = Mantra Pada
    A6 = Roga Pada / Shatru Pada
    A7 = Dara Pada
    A8 = Mrityu Pada
    A9 = Dharma Pada / Pitri Pada
    A10 = Rajya Pada / Karma Pada
    A11 = Labha Pada
    A12 = Upapada (UL)
    
    Args:
        chart: BirthChart object
        
    Returns:
        dict of "A1" through "A12" -> {sign, sign_index, house_from_lagna, ...}
    """
    ARUDHA_NAMES = {
        1: "Arudha Lagna (AL)",
        2: "Dhana Pada",
        3: "Vikrama Pada",
        4: "Sukha Pada",
        5: "Mantra Pada",
        6: "Shatru Pada",
        7: "Dara Pada",
        8: "Mrityu Pada",
        9: "Pitri Pada",
        10: "Rajya Pada",
        11: "Labha Pada",
        12: "Upapada (UL)",
    }

    lagna_idx = chart.lagna_index
    arudhas = {}

    for house in range(1, 13):
        house_sign_idx = house_to_sign_index(house, lagna_idx)
        house_sign = SIGNS[house_sign_idx]
        lord = SIGN_LORDS[house_sign]

        arudha_sign_idx = _calc_arudha_sign(house_sign_idx, lord, chart.positions)
        house_from_lagna = sign_to_house(arudha_sign_idx, lagna_idx)

        key = f"A{house}"
        arudhas[key] = {
            "sign": SIGNS[arudha_sign_idx],
            "sign_index": arudha_sign_idx,
            "house_from_lagna": house_from_lagna,
            "house_sign": house_sign,
            "lord": lord,
            "name": ARUDHA_NAMES[house],
        }

    return arudhas


# ═══════════════════════════════════════════
# GRAHA ARUDHAS (per-planet arudhas)
# ═══════════════════════════════════════════

def calc_graha_arudhas(chart):
    """
    Calculate Graha Arudhas (arudha pada for each planet).
    
    Graha Arudha = arudha of the sign the planet occupies.
    
    Args:
        chart: BirthChart object
        
    Returns:
        dict of planet -> {sign, sign_index, ...}
    """
    result = {}

    for planet in PLANETS_7:
        pos = chart.positions.get(planet, {})
        if not pos or isinstance(pos, (float, int)):
            continue

        planet_sign_idx = pos.get("sign_index", 0)
        planet_sign = SIGNS[planet_sign_idx]
        sign_lord = SIGN_LORDS[planet_sign]

        # The arudha of the planet's own sign
        arudha_idx = _calc_arudha_sign(planet_sign_idx, sign_lord, chart.positions)
        house_from_lagna = sign_to_house(arudha_idx, chart.lagna_index)

        result[planet] = {
            "sign": SIGNS[arudha_idx],
            "sign_index": arudha_idx,
            "house_from_lagna": house_from_lagna,
            "planet_in": planet_sign,
        }

    return result


# ═══════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════

def format_arudhas(arudhas):
    """Format all 12 arudha padas as readable text."""
    lines = []
    lines.append("=== Arudha Padas (A1-A12) ===\n")

    for key in [f"A{i}" for i in range(1, 13)]:
        a = arudhas.get(key, {})
        lines.append(
            f"  {key:<4} {a.get('name', ''):<22} "
            f"{a.get('sign', '?'):<14} (H{a.get('house_from_lagna', '?')})"
        )

    return "\n".join(lines)
