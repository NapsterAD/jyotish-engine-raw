"""
vargas.py — All 16 divisional charts (D1 through D60).
Uses classical Parashara mapping rules for each varga.
100% offline — pure arithmetic from sidereal longitudes.
"""

from ..core.constants import SIGNS, SIGN_INDEX, SIGN_ELEMENT, SIGN_LORDS, get_navamsa_sign


# ═══════════════════════════════════════════
# HELPER: sign from index
# ═══════════════════════════════════════════

def _sign_at(idx):
    """Return sign name for 0-based index (wraps around)."""
    return SIGNS[idx % 12]


def _sign_idx(longitude):
    """Return 0-based sign index from longitude."""
    return int(longitude / 30) % 12


def _degree_in_sign(longitude):
    """Return degree within sign (0-30)."""
    return longitude % 30


# ═══════════════════════════════════════════
# D1 — RASHI (identity, included for completeness)
# ═══════════════════════════════════════════

def calc_d1(longitude):
    """D1 Rashi — the sign itself."""
    return _sign_at(_sign_idx(longitude))


# ═══════════════════════════════════════════
# D2 — HORA (wealth)
# ═══════════════════════════════════════════

def calc_d2_hora(longitude):
    """
    D2 Hora chart.
    Parashara rule:
      - Odd sign: 0-15° = Sun (Leo), 15-30° = Moon (Cancer)
      - Even sign: 0-15° = Moon (Cancer), 15-30° = Sun (Leo)
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    is_odd = (sign_idx % 2 == 0)  # 0-indexed: Aries=0 (odd sign)

    if is_odd:
        return "Leo" if deg < 15 else "Cancer"
    else:
        return "Cancer" if deg < 15 else "Leo"


# ═══════════════════════════════════════════
# D3 — DREKKANA (siblings / courage)
# ═══════════════════════════════════════════

def calc_d3_drekkana(longitude):
    """
    D3 Drekkana chart (Parashara method).
    Divide sign into 3 parts of 10° each:
      - 0-10°: same sign (1st drekkana)
      - 10-20°: 5th from sign
      - 20-30°: 9th from sign
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)

    if deg < 10:
        return _sign_at(sign_idx)
    elif deg < 20:
        return _sign_at(sign_idx + 4)  # 5th from
    else:
        return _sign_at(sign_idx + 8)  # 9th from


# ═══════════════════════════════════════════
# D4 — CHATURTHAMSA (fortune / property)
# ═══════════════════════════════════════════

def calc_d4(longitude):
    """
    D4 Chaturthamsa.
    Divide sign into 4 parts of 7°30' each:
      - Part 1 (0-7.5°): same sign
      - Part 2 (7.5-15°): 4th from sign
      - Part 3 (15-22.5°): 7th from sign
      - Part 4 (22.5-30°): 10th from sign
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    part = int(deg / 7.5)
    part = min(part, 3)

    offsets = [0, 3, 6, 9]  # same, 4th, 7th, 10th
    return _sign_at(sign_idx + offsets[part])


# ═══════════════════════════════════════════
# D5 — PANCHAMSA (spiritual merit)
# ═══════════════════════════════════════════

def calc_d5(longitude):
    """
    D5 Panchamsa.
    6° per division. Start from same sign for odd, 
    from the sign itself for even signs.
    Standard cyclic: (sign_idx * 5 + division) % 12
    Note: Some traditions use a different mapping.
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / 6)
    division = min(division, 4)

    # Parashara: Odd signs start from same sign, count 5 signs per division
    # Even signs start from opposite (7th) and count backward
    # Simplified standard cyclic mapping:
    return _sign_at(sign_idx * 5 + division)


# ═══════════════════════════════════════════
# D6 — SHASHTHAMSA (health / disease)
# ═══════════════════════════════════════════

def calc_d6(longitude):
    """
    D6 Shashthamsa.
    5° per division (6 divisions per sign).
    Standard cyclic: (sign_idx * 6 + division) % 12
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / 5)
    division = min(division, 5)
    return _sign_at(sign_idx * 6 + division)


# ═══════════════════════════════════════════
# D7 — SAPTAMSA (children / progeny)
# ═══════════════════════════════════════════

def calc_d7(longitude):
    """
    D7 Saptamsa (Parashara).
    4°17'8.57" per division (30/7).
    - Odd sign: count from same sign
    - Even sign: count from 7th from sign
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / (30.0 / 7))
    division = min(division, 6)

    is_odd = (sign_idx % 2 == 0)  # 0-indexed
    if is_odd:
        return _sign_at(sign_idx + division)
    else:
        return _sign_at(sign_idx + 6 + division)  # 7th from sign + division


# ═══════════════════════════════════════════
# D8 — ASHTAMSA (unexpected trouble)
# ═══════════════════════════════════════════

def calc_d8(longitude):
    """
    D8 Ashtamsa.
    3°45' per division (8 divisions).
    Standard cyclic: (sign_idx * 8 + division) % 12
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / 3.75)
    division = min(division, 7)
    return _sign_at(sign_idx * 8 + division)


# ═══════════════════════════════════════════
# D9 — NAVAMSA (dharma / spouse / inner self)
# ═══════════════════════════════════════════

def calc_d9_navamsa(longitude):
    """
    D9 Navamsa — uses the classical element-based starting point.
    Delegates to the authoritative implementation in constants.py.
    """
    return get_navamsa_sign(longitude)


def calc_d10(longitude):
    """
    D10 Dasamsa — Classical Phaladeepika / BPHS Chara-Sthira-Dwiswabhava mapping.
    3° per division (10 divisions per sign).
      Chara (Movable - Ar/Cn/Li/Cp): start from the sign itself (sign_idx)
      Sthira (Fixed - Ta/Le/Sc/Aq): start from the 9th from the sign (sign_idx + 8)
      Dwiswabhava (Dual - Ge/Vi/Sg/Pi): start from the 5th from the sign (sign_idx + 4)
    """
    from ..core.constants import SIGN_MODALITY
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / 3.0)
    division = min(division, 9)
    modality = SIGN_MODALITY[SIGNS[sign_idx]]
    if modality == "Movable":
        start = sign_idx
    elif modality == "Fixed":
        start = sign_idx + 8  # 9th
    else:
        start = sign_idx + 4  # 5th
    return _sign_at(start + division)



# ═══════════════════════════════════════════
# D11 — EKADASAMSA / RUDRAMSA (death / danger)
# ═══════════════════════════════════════════

def calc_d11(longitude):
    """
    D11 Ekadasamsa / Rudramsa.
    Standard cyclic: (sign_idx * 11 + division) % 12
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / (30.0 / 11))
    division = min(division, 10)
    return _sign_at(sign_idx * 11 + division)


# ═══════════════════════════════════════════
# D12 — DWADASAMSA (parents)
# ═══════════════════════════════════════════

def calc_d12(longitude):
    """
    D12 Dwadasamsa (Parashara).
    2°30' per division (12 divisions per sign).
    Counting starts from same sign, each division = next sign.
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / 2.5)
    division = min(division, 11)
    return _sign_at(sign_idx + division)


# ═══════════════════════════════════════════
# D16 — SHODASAMSA (vehicles / comforts / accidents)
# ═══════════════════════════════════════════

def calc_d16(longitude):
    """
    D16 Shodasamsa (Parashara).
    1°52'30" per division (16 divisions per sign).
    - Movable sign: start from Aries
    - Fixed sign: start from Leo
    - Dual sign: start from Sagittarius
    """
    from ..core.constants import SIGN_MODALITY

    sign_idx = _sign_idx(longitude)
    sign = SIGNS[sign_idx]
    deg = _degree_in_sign(longitude)
    division = int(deg / (30.0 / 16))
    division = min(division, 15)

    modality = SIGN_MODALITY[sign]
    start_map = {"Movable": 0, "Fixed": 4, "Dual": 8}  # Aries, Leo, Sagittarius
    start = start_map[modality]
    return _sign_at(start + division)


# ═══════════════════════════════════════════
# D20 — VIMSAMSA (spiritual progress / upasana)
# ═══════════════════════════════════════════

def calc_d20(longitude):
    """
    D20 Vimsamsa (Parashara).
    1°30' per division (20 divisions per sign).
    - Movable sign: start from Aries
    - Fixed sign: start from Sagittarius
    - Dual sign: start from Leo
    """
    from ..core.constants import SIGN_MODALITY

    sign_idx = _sign_idx(longitude)
    sign = SIGNS[sign_idx]
    deg = _degree_in_sign(longitude)
    division = int(deg / (30.0 / 20))
    division = min(division, 19)

    modality = SIGN_MODALITY[sign]
    start_map = {"Movable": 0, "Fixed": 8, "Dual": 4}  # Aries, Sagittarius, Leo
    start = start_map[modality]
    return _sign_at(start + division)


# ═══════════════════════════════════════════
# D24 — CHATURVIMSAMSA (learning / education)
# ═══════════════════════════════════════════

def calc_d24(longitude):
    """
    D24 Chaturvimsamsa (Siddhamsa — Parashara).
    1°15' per division (24 divisions per sign).
    - Odd sign: start from Leo
    - Even sign: start from Cancer
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / (30.0 / 24))
    division = min(division, 23)

    is_odd = (sign_idx % 2 == 0)  # 0-indexed
    if is_odd:
        return _sign_at(4 + division)   # Leo
    else:
        return _sign_at(3 + division)   # Cancer


# ═══════════════════════════════════════════
# D27 — SAPTAVIMSAMSA (strength / weakness)
# ═══════════════════════════════════════════

def calc_d27(longitude):
    """
    D27 Saptavimsamsa (Bhamsa — Parashara).
    1°6'40" per division (27 divisions per sign).
    - Fire sign: start from Aries
    - Earth sign: start from Cancer
    - Air sign: start from Libra
    - Water sign: start from Capricorn
    """
    sign_idx = _sign_idx(longitude)
    sign = SIGNS[sign_idx]
    element = SIGN_ELEMENT[sign]
    deg = _degree_in_sign(longitude)
    division = int(deg / (30.0 / 27))
    division = min(division, 26)

    start_map = {"Fire": 0, "Earth": 3, "Air": 6, "Water": 9}
    start = start_map[element]
    return _sign_at(start + division)


# ═══════════════════════════════════════════
# D30 — TRIMSAMSA (evil / misfortune / character)
# ═══════════════════════════════════════════

def calc_d30(longitude):
    """
    D30 Trimsamsa (Parashara).
    Unequal divisions — different for odd vs even signs.
    
    Odd signs: Mars(5°) Sat(5°) Jup(8°) Mer(7°) Ven(5°)
    Even signs: Ven(5°) Mer(7°) Jup(8°) Sat(5°) Mars(5°)
    
    The sign = the sign ruled by that planet.
    Mars→Aries, Saturn→Aquarius, Jupiter→Sagittarius, 
    Mercury→Gemini, Venus→Libra
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    is_odd = (sign_idx % 2 == 0)  # 0-indexed

    # Planet-to-sign mapping for trimsamsa
    planet_sign = {
        "Mars": "Aries", "Saturn": "Aquarius", "Jupiter": "Sagittarius",
        "Mercury": "Gemini", "Venus": "Libra"
    }

    if is_odd:
        boundaries = [(5, "Mars"), (10, "Saturn"), (18, "Jupiter"),
                      (25, "Mercury"), (30, "Venus")]
    else:
        boundaries = [(5, "Venus"), (12, "Mercury"), (20, "Jupiter"),
                      (25, "Saturn"), (30, "Mars")]

    for bound, planet in boundaries:
        if deg < bound:
            return planet_sign[planet]

    return planet_sign[boundaries[-1][1]]


# ═══════════════════════════════════════════
# D40 — KHAVEDAMSA (auspicious/inauspicious effects)
# ═══════════════════════════════════════════

def calc_d40(longitude):
    """
    D40 Khavedamsa (Parashara).
    0°45' per division (40 divisions per sign).
    - Odd sign: start from Aries
    - Even sign: start from Libra
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / (30.0 / 40))
    division = min(division, 39)

    is_odd = (sign_idx % 2 == 0)  # 0-indexed
    if is_odd:
        return _sign_at(division)       # from Aries
    else:
        return _sign_at(6 + division)   # from Libra


# ═══════════════════════════════════════════
# D45 — AKSHAVEDAMSA (general well-being)
# ═══════════════════════════════════════════

def calc_d45(longitude):
    """
    D45 Akshavedamsa (Parashara).
    0°40' per division (45 divisions per sign).
    - Movable sign: start from Aries
    - Fixed sign: start from Leo
    - Dual sign: start from Sagittarius
    """
    from ..core.constants import SIGN_MODALITY

    sign_idx = _sign_idx(longitude)
    sign = SIGNS[sign_idx]
    deg = _degree_in_sign(longitude)
    division = int(deg / (30.0 / 45))
    division = min(division, 44)

    modality = SIGN_MODALITY[sign]
    start_map = {"Movable": 0, "Fixed": 4, "Dual": 8}
    start = start_map[modality]
    return _sign_at(start + division)


# ═══════════════════════════════════════════
# D60 — SHASHTIAMSA (past karma / everything)
# ═══════════════════════════════════════════

def calc_d60(longitude):
    """
    D60 Shashtiamsa (Parashara).
    0°30' per division (60 divisions per sign).
    Cyclic: starts from same sign.
    """
    sign_idx = _sign_idx(longitude)
    deg = _degree_in_sign(longitude)
    division = int(deg / 0.5)
    division = min(division, 59)
    return _sign_at(sign_idx + division)


# ═══════════════════════════════════════════
# VARGOTTAMA CHECK
# ═══════════════════════════════════════════

def check_vargottama(positions):
    """
    Check which planets are vargottama (same sign in D1 and D9).
    
    Args:
        positions: dict from ephemeris — planet -> {longitude, sign, navamsa, ...}
        
    Returns:
        dict of planet -> bool (True if vargottama)
    """
    result = {}
    from ..core.constants import PLANETS_9
    
    for planet in ["Lagna"] + list(PLANETS_9):
        pos = positions.get(planet)
        if not pos or isinstance(pos, (float, int)):
            continue
        d1_sign = pos.get("sign")
        d9_sign = pos.get("navamsa")
        result[planet] = (d1_sign == d9_sign) if (d1_sign and d9_sign) else False

    return result


# ═══════════════════════════════════════════
# ALL VARGAS AT ONCE
# ═══════════════════════════════════════════

# Master dispatch table
VARGA_FUNCTIONS = {
    "D1": calc_d1, "D2": calc_d2_hora, "D3": calc_d3_drekkana,
    "D4": calc_d4, "D5": calc_d5, "D6": calc_d6,
    "D7": calc_d7, "D8": calc_d8, "D9": calc_d9_navamsa,
    "D10": calc_d10, "D11": calc_d11, "D12": calc_d12,
    "D16": calc_d16, "D20": calc_d20, "D24": calc_d24,
    "D27": calc_d27, "D30": calc_d30, "D40": calc_d40,
    "D45": calc_d45, "D60": calc_d60,
}


def calc_all_vargas(positions):
    """
    Calculate all 20 varga charts for all planets.
    
    Args:
        positions: dict from ephemeris — planet -> {longitude, ...}
        
    Returns:
        dict of varga_name -> {planet_name: sign, ...}
    """
    from ..core.constants import PLANETS_9

    all_vargas = {}

    for varga_name, func in VARGA_FUNCTIONS.items():
        varga_chart = {}
        for planet in ["Lagna"] + list(PLANETS_9):
            pos = positions.get(planet)
            if not pos or isinstance(pos, (float, int)):
                continue
            longitude = pos.get("longitude", 0)
            varga_chart[planet] = func(longitude)
        all_vargas[varga_name] = varga_chart

    # Add vargottama info
    all_vargas["_vargottama"] = check_vargottama(positions)

    return all_vargas


def calc_single_varga(positions, varga_name):
    """
    Calculate a single varga chart for all planets.
    
    Args:
        positions: dict from ephemeris
        varga_name: "D9", "D10", etc.
        
    Returns:
        dict of planet_name -> sign
    """
    from ..core.constants import PLANETS_9

    func = VARGA_FUNCTIONS.get(varga_name.upper())
    if not func:
        raise ValueError(f"Unknown varga: {varga_name}. Valid: {list(VARGA_FUNCTIONS.keys())}")

    chart = {}
    for planet in ["Lagna"] + list(PLANETS_9):
        pos = positions.get(planet)
        if not pos or isinstance(pos, (float, int)):
            continue
        chart[planet] = func(pos["longitude"])

    return chart
