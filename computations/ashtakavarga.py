"""
ashtakavarga.py — Bhinnashtakavarga (BAV), Sarvashtakavarga (SAV), and Sodhya Pinda.
100% offline — classical Parashara contribution rules.

Each planet's BAV is an 8×12 matrix showing benefic points (bindus) contributed
by each of the 8 contributors (7 planets + Lagna) across all 12 signs.
SAV is the column-wise sum of all 8 planets' BAV matrices.
"""

from ..core.constants import SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_7
from ..core.mapping import house_to_sign_index


# ═══════════════════════════════════════════
# PARASHARA BAV CONTRIBUTION RULES
# ═══════════════════════════════════════════
#
# For each planet (beneficiary), each contributor gives a bindu (1)
# when the contributor is placed in specific houses from the planet's position.
# These rules come from BPHS chapters 66-72.
#
# Format: BAV_RULES[beneficiary][contributor] = list of houses where bindu = 1
# Houses are 1-indexed offsets from the contributor's position.

BAV_RULES = {
    "Sun": {
        "Sun":     [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":    [3, 6, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus":   [6, 7, 12],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna":   [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        # PyJHora / JHora Parashara: Moon +9 from Moon, −9 from Mars,
        # +2 / −12 from Jupiter. These four cells are what made SAV 339.
        "Sun":     [3, 6, 7, 8, 10, 11],
        "Moon":    [1, 3, 6, 7, 9, 10, 11],
        "Mars":    [2, 3, 5, 6, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 2, 4, 7, 8, 10, 11],
        "Venus":   [3, 4, 5, 7, 9, 10, 11],
        "Saturn":  [3, 5, 6, 11],
        "Lagna":   [3, 6, 10, 11],
    },
    "Mars": {
        "Sun":     [3, 5, 6, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus":   [6, 8, 11, 12],
        "Saturn":  [1, 4, 7, 8, 9, 10, 11],
        "Lagna":   [1, 3, 6, 10, 11],
    },
    "Mercury": {
        "Sun":     [5, 6, 9, 11, 12],
        "Moon":    [2, 4, 6, 8, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna":   [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sun":     [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon":    [2, 5, 7, 9, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus":   [2, 5, 6, 9, 10, 11],
        "Saturn":  [3, 5, 6, 12],
        "Lagna":   [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venus": {
        "Sun":     [8, 11, 12],
        "Moon":    [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars":    [3, 4, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn":  [3, 4, 5, 8, 9, 10, 11],
        "Lagna":   [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sun":     [1, 2, 4, 7, 8, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [3, 5, 6, 10, 11, 12],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus":   [6, 11, 12],
        "Saturn":  [3, 5, 6, 11],
        "Lagna":   [1, 3, 4, 6, 10, 11],
    },
}

# Lagna BAV: Lagna is also treated as a "planet" for SAV calculation
BAV_RULES["Lagna"] = {
    "Sun":     [3, 4, 6, 10, 11, 12],
    "Moon":    [3, 6, 10, 11, 12],
    "Mars":    [1, 3, 6, 10, 11],
    "Mercury": [1, 2, 4, 6, 8, 10, 11],
    "Jupiter": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    "Venus":   [1, 2, 3, 4, 5, 8, 9],
    "Saturn":  [1, 3, 4, 6, 10, 11],
    "Lagna":   [3, 6, 10, 11],
}


# ═══════════════════════════════════════════
# BAV CALCULATION
# ═══════════════════════════════════════════

def calc_bav(positions):
    """
    Calculate Bhinnashtakavarga (BAV) for all 8 entities (7 planets + Lagna).
    
    Args:
        positions: dict from ephemeris — planet/Lagna -> {sign_index, ...}
        
    Returns:
        dict of planet -> [12 values], where each value is the bindu count
        for that sign (Aries=index 0 ... Pisces=index 11).
        Also includes row_totals per planet.
    """
    # Get sign index for each contributor
    contributor_signs = {}
    for name in PLANETS_7 + ["Lagna"]:
        pos = positions.get(name)
        if pos and isinstance(pos, dict):
            contributor_signs[name] = pos["sign_index"]

    bav = {}

    for beneficiary in PLANETS_7 + ["Lagna"]:
        rules = BAV_RULES.get(beneficiary, {})
        bindu_counts = [0] * 12  # One per sign (Aries=0 ... Pisces=11)

        for contributor, houses in rules.items():
            cont_sign_idx = contributor_signs.get(contributor)
            if cont_sign_idx is None:
                continue

            for house_offset in houses:
                # House offset is 1-indexed from contributor's sign
                target_sign = (cont_sign_idx + house_offset - 1) % 12
                bindu_counts[target_sign] += 1

        bav[beneficiary] = bindu_counts

    return bav


# ═══════════════════════════════════════════
# SAV CALCULATION
# ═══════════════════════════════════════════

def calc_sav(bav):
    """
    Calculate Sarvashtakavarga (SAV) from BAV.
    SAV = column-wise sum of 7 planetary BAV rows ONLY (Lagna excluded).
    Classical standard: SAV total = 337 for any chart.
    
    Args:
        bav: dict from calc_bav()
        
    Returns:
        dict with:
            sav: [12 values] (one per sign)
            total: sum of all 12 values (should be 337)
            strongest: (sign_name, value)
            weakest: (sign_name, value)
            ranking: sorted list of (sign, value)
    """
    sav = [0] * 12

    # SAV sums only the 7 planets — NOT Lagna
    for planet in PLANETS_7:
        if planet in bav:
            for i in range(12):
                sav[i] += bav[planet][i]

    total = sum(sav)

    # Find strongest and weakest
    sign_values = [(SIGNS[i], sav[i]) for i in range(12)]
    strongest = max(sign_values, key=lambda x: x[1])
    weakest = min(sign_values, key=lambda x: x[1])
    ranking = sorted(sign_values, key=lambda x: x[1], reverse=True)

    return {
        "sav": sav,
        "total": total,
        "strongest": strongest,
        "weakest": weakest,
        "ranking": ranking,
        "average": round(total / 12, 2),
    }


def calc_sav_by_house(bav, lagna_sign_index):
    """
    SAV by whole-sign house from Lagna (H1 = Lagna sign, Aries-first sav[i]
    rotated). Aditya lock (Libra lagna): H1=30 H2=21 H3=28 H12=25 — this is
    the JHora/ad2/PyJHora vector. The "Virgo–Sag reversed / H1↔H2 swap" reading
    is a retracted PDF digit-split error, not an engine bug.
    """
    sav = [0] * 12
    # SAV sums only the 7 planets — NOT Lagna
    for planet in PLANETS_7:
        if planet in bav:
            for i in range(12):
                sav[i] += bav[planet][i]

    house_sav = {}
    for house in range(1, 13):
        sign_idx = house_to_sign_index(house, lagna_sign_index)
        house_sav[house] = sav[sign_idx]

    return house_sav


# ═══════════════════════════════════════════
# ROW TOTALS
# ═══════════════════════════════════════════

def calc_row_totals(bav):
    """
    Calculate total bindus per planet (row sums).
    
    Returns:
        dict of planet -> total bindus
    """
    return {planet: sum(values) for planet, values in bav.items()}


# ═══════════════════════════════════════════
# SODHYA PINDA
# ═══════════════════════════════════════════

# Sign multipliers for Rasi Pinda (Aries=0 to Pisces=11)
RASI_GUNAKARA = {
    0: 7,   # Aries
    1: 10,  # Taurus
    2: 8,   # Gemini
    3: 4,   # Cancer
    4: 10,  # Leo
    5: 5,   # Virgo
    6: 7,   # Libra
    7: 8,   # Scorpio
    8: 9,   # Sagittarius
    9: 5,   # Capricorn
    10: 11, # Aquarius
    11: 12, # Pisces
}

# Planet multipliers for Graha Pinda
GRAHA_GUNAKARA = {
    "Sun": 5,
    "Moon": 5,
    "Mars": 8,
    "Mercury": 5,
    "Jupiter": 10,
    "Venus": 7,
    "Saturn": 5,
}


def _trikona_shodhana(bindus):
    """
    Trikona reduction on a 12-length bindu row (Aries=0).
    For each elemental trikona, if all three signs have bindus, subtract min.
    """
    reduced = list(bindus)
    for group in ((0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)):
        vals = [reduced[i] for i in group]
        if min(vals) > 0:
            m = min(vals)
            for i in group:
                reduced[i] -= m
    return reduced


def _occupied_signs(positions):
    occupied = set()
    for p in PLANETS_7:
        pos = positions.get(p, {})
        if isinstance(pos, dict) and "sign_index" in pos:
            occupied.add(pos["sign_index"])
    return occupied


def _ekadhipatya_shodhana(bindus, occupied):
    """
    Dual-lordship reduction after Trikona. Pairs: Mars, Venus, Mercury,
    Jupiter, Saturn. Sun/Moon single signs are skipped.
    """
    reduced = list(bindus)
    pairs = ((0, 7), (1, 6), (2, 5), (8, 11), (9, 10))
    for s1, s2 in pairs:
        v1, v2 = reduced[s1], reduced[s2]
        # Parashara: if either sign is already 0 after Trikona, skip the pair.
        if v1 == 0 or v2 == 0:
            continue
        occ1, occ2 = s1 in occupied, s2 in occupied
        if occ1 and occ2:
            continue
        if occ1 and not occ2:
            reduced[s2] = v1 if v2 > v1 else 0
        elif occ2 and not occ1:
            reduced[s1] = v2 if v1 > v2 else 0
        else:
            if v1 == v2:
                reduced[s1] = 0
                reduced[s2] = 0
            else:
                m = min(v1, v2)
                reduced[s1] = m
                reduced[s2] = m
    return reduced


def calc_sodhya_pinda(bav, positions):
    """
    Sodhya Pinda after Trikona + Ekadhipatya shodhana (Parashara / JHora).
    Rasi Pinda = remaining bindus × rasi gunakara.
    Graha Pinda = remaining bindus in an occupied sign × gunakara of occupant(s).
    """
    occupied = _occupied_signs(positions)
    result = {}

    for planet in PLANETS_7 + ["Lagna"]:
        if planet not in bav:
            continue
        row = list(bav[planet])
        reduced = _ekadhipatya_shodhana(_trikona_shodhana(row), occupied)

        rasi_pinda = 0
        graha_pinda = 0
        for sign_idx in range(12):
            pts = reduced[sign_idx]
            if pts <= 0:
                continue
            rasi_pinda += pts * RASI_GUNAKARA[sign_idx]
            occ_mult = 0
            for p in PLANETS_7:
                pos = positions.get(p, {})
                if isinstance(pos, dict) and pos.get("sign_index") == sign_idx:
                    occ_mult += GRAHA_GUNAKARA.get(p, 5)
            graha_pinda += pts * occ_mult

        result[planet] = {
            "sodhya": rasi_pinda + graha_pinda,
            "rasi": rasi_pinda,
            "graha": graha_pinda,
            "reduced": reduced,
        }

    return result


# ═══════════════════════════════════════════
# HOUSE BINDU ANALYSIS
# ═══════════════════════════════════════════

def get_house_bindus(bav, sign_index):
    """
    Get per-planet bindus for a specific sign.
    
    Args:
        bav: dict from calc_bav()
        sign_index: 0-11 (Aries=0)
        
    Returns:
        dict of planet -> bindu count at that sign
    """
    result = {}
    total = 0
    for planet in PLANETS_7 + ["Lagna"]:
        if planet in bav:
            val = bav[planet][sign_index]
            result[planet] = val
            total += val
    result["total"] = total
    return result


# ═══════════════════════════════════════════
# SAV PATTERN CHECKS
# ═══════════════════════════════════════════

def check_sav_patterns(sav_data, lagna_sign_index):
    """
    Check notable SAV patterns per KN Rao and other authorities.
    
    Args:
        sav_data: dict from calc_sav()
        lagna_sign_index: 0-based sign index of lagna
        
    Returns:
        list of pattern descriptions
    """
    sav = sav_data["sav"]
    patterns = []

    def house_sav(house_num):
        return sav[house_to_sign_index(house_num, lagna_sign_index)]

    # KN Rao: 11H > 10H pattern (presidents / royals)
    h11 = house_sav(11)
    h10 = house_sav(10)
    if h11 > h10:
        patterns.append(f"11H({h11}) > 10H({h10}): KN Rao pattern (presidents/royals)")
    else:
        patterns.append(f"11H({h11}) ≤ 10H({h10}): 11H > 10H pattern NOT present")

    # Strong houses (> average)
    avg = sav_data["average"]
    strong_houses = []
    weak_houses = []
    for h in range(1, 13):
        val = house_sav(h)
        if val > avg:
            strong_houses.append(f"H{h}({val})")
        elif val < avg - 3:
            weak_houses.append(f"H{h}({val})")

    if strong_houses:
        patterns.append(f"Above-average houses: {', '.join(strong_houses)}")
    if weak_houses:
        patterns.append(f"Notably weak houses: {', '.join(weak_houses)}")

    # 7H weakness check (marriage difficulty if < 25)
    h7 = house_sav(7)
    if h7 < 25:
        patterns.append(f"7H SAV = {h7} (below 25): marriage timing delays possible")

    # 6H strength (service / enemies)
    h6 = house_sav(6)
    if h6 > 30:
        patterns.append(f"6H SAV = {h6} (strong): victory over enemies, good health endurance")

    return patterns


# ═══════════════════════════════════════════
# RANKING HELPERS
# ═══════════════════════════════════════════

def rank_houses_by_sav(sav_data, lagna_sign_index):
    """
    Rank all 12 houses by SAV value (descending).
    
    Returns:
        list of (house_num, sign_name, sav_value) sorted by value descending
    """
    sav = sav_data["sav"]
    house_list = []
    for h in range(1, 13):
        sign_idx = house_to_sign_index(h, lagna_sign_index)
        house_list.append((h, SIGNS[sign_idx], sav[sign_idx]))

    return sorted(house_list, key=lambda x: x[2], reverse=True)


# ═══════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════

def format_bav_matrix(bav):
    """Format BAV as a readable text matrix."""
    lines = []
    lines.append("═══ Bhinnashtakavarga (BAV) Matrix ═══\n")

    # Header
    header = f"{'Planet':<10}" + "".join(f"{s[:3]:>5}" for s in SIGNS) + "  Total"
    lines.append(header)
    lines.append("─" * len(header))

    for planet in PLANETS_7 + ["Lagna"]:
        if planet not in bav:
            continue
        row = bav[planet]
        total = sum(row)
        line = f"{planet:<10}" + "".join(f"{v:>5}" for v in row) + f"  {total:>5}"
        lines.append(line)

    # SAV row
    sav_row = [0] * 12
    for planet in PLANETS_7 + ["Lagna"]:
        if planet in bav:
            for i in range(12):
                sav_row[i] += bav[planet][i]
    lines.append("─" * len(header))
    line = f"{'SAV':<10}" + "".join(f"{v:>5}" for v in sav_row) + f"  {sum(sav_row):>5}"
    lines.append(line)

    return "\n".join(lines)


# ═══════════════════════════════════════════
# CS PATEL ASHTAKAVARGA ADVANCED ALGORITHMS
# ═══════════════════════════════════════════
# Source: CS Patel's "Ashtakavarga" & "Practical Ashtakavarga"

from ..core.constants import NAKSHATRAS


def calc_patel_sensitive_points(bav, sodhya_pindas, positions):
    """
    Calculate CS Patel's classical Ashtakavarga sensitive degrees/nakshatras.
    Formula: (Sodhya Pinda of Planet * Bindus in Hth from Planet) % 27
    Resulting nakshatra and its trines (1, 10, 19) become sensitive points for transits.
    
    Returns:
        dict with sensitive nakshatras and rasis for father, mother, siblings, children, spouse, longevity.
    """
    results = {}
    
    relations = [
        ("Father", "Sun", 9, "Saturn/Rahu transit brings distress/event to father"),
        ("Mother", "Moon", 4, "Saturn/Mars transit brings distress/event to mother"),
        ("Siblings", "Mars", 3, "Saturn transit brings events to brothers/sisters"),
        ("Progeny", "Jupiter", 5, "Jupiter transit triggers childbirth; Saturn transit brings events"),
        ("Spouse", "Venus", 7, "Jupiter transit triggers marriage; Saturn brings testing"),
        ("Longevity", "Saturn", 8, "Saturn/Jupiter transit indicates critical life transitions"),
    ]
    
    for rel_name, planet, offset_house, effect in relations:
        p_pos = positions.get(planet, {})
        if not isinstance(p_pos, dict) or "sign_index" not in p_pos:
            continue
        
        p_sign_idx = p_pos["sign_index"]
        target_sign_idx = (p_sign_idx + offset_house - 1) % 12
        
        planet_bav = bav.get(planet, [0]*12)
        bindus_in_target = planet_bav[target_sign_idx]
        
        pinda_info = sodhya_pindas.get(planet, {})
        sodhya_val = pinda_info.get("sodhya", 0)
        
        product = sodhya_val * bindus_in_target
        nak_num = (product % 27) or 27  # 1 to 27
        rasi_num = (product % 12) or 12 # 1 to 12
        
        nak_name = NAKSHATRAS[nak_num - 1]["name"] if nak_num <= 27 else "Unknown"
        rasi_name = SIGNS[rasi_num - 1]
        
        # Trinal nakshatras (Nakshatras at distance 9 and 18)
        trine1_num = ((nak_num - 1 + 9) % 27) + 1
        trine2_num = ((nak_num - 1 + 18) % 27) + 1
        trine_naks = [
            nak_name,
            NAKSHATRAS[trine1_num - 1]["name"],
            NAKSHATRAS[trine2_num - 1]["name"]
        ]
        
        results[rel_name] = {
            "planet": planet,
            "karaka_house": offset_house,
            "bindus_in_house": bindus_in_target,
            "sodhya_pinda": sodhya_val,
            "product": product,
            "sensitive_nakshatra": nak_name,
            "sensitive_nakshatra_num": nak_num,
            "trinal_nakshatras": trine_naks,
            "sensitive_rasi": rasi_name,
            "sensitive_rasi_num": rasi_num,
            "classical_significance": effect,
        }
        
    return results


def get_bav_transit_quality(planet, bindu_count):
    """
    CS Patel standard interpretation for transit over a house containing N bindus in BAV.
    """
    scale = {
        8: ("EXCELLENT", "Highest royal/official favor, supreme success, acquisition of great wealth"),
        7: ("VERY_GOOD", "Success through enterprise, happiness, fine gains, respect"),
        6: ("GOOD", "Acquisition of wealth, fame, support from virtuous associates"),
        5: ("FAVORABLE", "Moderate gains, steady progress, general happiness"),
        4: ("NEUTRAL", "Mixed results, status quo, expenditure matches income"),
        3: ("UNFAVORABLE", "Fatigue, delays, friction with friends, financial pressure"),
        2: ("BAD", "Loss of money, anxiety, opposition from rivals, health stress"),
        1: ("VERY_BAD", "Severe difficulties, distress, unexpected setbacks"),
        0: ("EXTREME_CAUTION", "Critical obstacle, acute distress, vulnerability — avoid key beginnings"),
    }
    return scale.get(bindu_count, ("NEUTRAL", "Status quo"))

