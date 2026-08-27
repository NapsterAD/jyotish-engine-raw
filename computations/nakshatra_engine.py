"""
nakshatra_engine.py — Nakshatra-level predictive algorithms.

Sources:
  Brhat Nakshatra (Sanjay Rath) — 257KB mined
  Deepanshu Giri (Predict Using Nakshatra Pada) — 76KB mined
  Sunil John (Predicting Through Nakshatras) — 18KB + 10KB
  Nakshatra Chintamani (R. Bhatt) — 12KB mined

Implements:
  1. Activation Ages (Vimshottari-based nakshatra lord activation)
  2. Nava-Tara (9 Star Groups) for transit analysis
  3. Nakshatra Career/Health/Marriage profiles
  4. Pushkara Bhaga (specific lucky degrees)
  5. Mrityu Bhaga (death degrees)
"""

from ..core.constants import (
    NAKSHATRAS, NAKSHATRA_SPAN, PADA_SPAN,
    VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS,
    PLANETS_9, SIGNS,
)


# ═══════════════════════════════════════════
# ACTIVATION AGES
# ═══════════════════════════════════════════

# Vimshottari-based activation cycle:
# Ketu=1,10,19,28,37,46,55  Venus=2,11,20,29,38,47,56  Sun=3,12,21,30,39,48,57
# Moon=4,13,22,31,40,49,58  Mars=5,14,23,32,41,50,59   Rahu=6,15,24,33,42,51,60
# Jupiter=7,16,25,34,43,52,61  Saturn=8,17,26,35,44,53,62  Mercury=9,18,27,36,45,54,63

ACTIVATION_AGES = {}
for i, lord in enumerate(VIMSHOTTARI_ORDER):
    ages = [i + 1 + 9 * k for k in range(8)]  # up to ~72
    ACTIVATION_AGES[lord] = ages

# Alternative: Pada-specific ages (Deepanshu Giri system)
# Pada 1 adds +0, Pada 2 adds +1, Pada 3 adds +2, Pada 4 adds +3
# to the base activation year of the nakshatra lord


def calc_activation_ages(chart):
    """
    Calculate nakshatra activation ages for all planets.

    For each planet, returns:
      - Nakshatra lord activation ages (Vimshottari cycle)
      - Pada-modified activation ages (Deepanshu Giri method)
      - Sub-lord activation ages

    Returns:
        dict keyed by planet name
    """
    results = {}
    for p in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(p, {})
        if not isinstance(pos, dict) or "nakshatra_lord" not in pos:
            continue
        nak_lord = pos["nakshatra_lord"]
        pada = pos.get("pada", 1)
        sub_lord = pos.get("sub_lord", "")

        # Base activation ages from nakshatra lord
        base_ages = ACTIVATION_AGES.get(nak_lord, [])

        # Pada-modified: add (pada-1) to each base age for more specific timing
        pada_ages = [a + (pada - 1) for a in base_ages]

        # Sub-lord activation (if available)
        sub_ages = ACTIVATION_AGES.get(sub_lord, []) if sub_lord else []

        results[p] = {
            "nakshatra": pos.get("nakshatra", ""),
            "pada": pada,
            "nakshatra_lord": nak_lord,
            "base_activation_ages": base_ages,
            "pada_activation_ages": pada_ages,
            "sub_lord": sub_lord,
            "sub_lord_ages": sub_ages,
        }
    return results


# ═══════════════════════════════════════════
# NAVA-TARA (9 Star Groups)
# ═══════════════════════════════════════════

TARA_NAMES = [
    "Janma",    # 1 — Birth star (mixed, caution)
    "Sampat",   # 2 — Wealth (excellent)
    "Vipat",    # 3 — Danger (avoid)
    "Kshema",   # 4 — Prosperity (good)
    "Pratyari", # 5 — Obstacle (bad)
    "Sadhaka",  # 6 — Achievement (good)
    "Vadha",    # 7 — Death (worst, avoid)
    "Mitra",    # 8 — Friend (good)
    "Parama Mitra",  # 9 — Best Friend (excellent)
]

TARA_QUALITY = {
    "Janma": "MIXED",
    "Sampat": "EXCELLENT",
    "Vipat": "BAD",
    "Kshema": "GOOD",
    "Pratyari": "BAD",
    "Sadhaka": "GOOD",
    "Vadha": "WORST",
    "Mitra": "GOOD",
    "Parama Mitra": "EXCELLENT",
}


def calc_nava_tara(birth_nak_num, transit_nak_num):
    """
    Calculate Tara (Star Group) for a transit nakshatra relative to birth nakshatra.

    Args:
        birth_nak_num: 1-27 (birth Moon's nakshatra number)
        transit_nak_num: 1-27 (transiting body's nakshatra number)

    Returns:
        dict with tara_number (1-9), tara_name, quality, cycle
    """
    diff = (transit_nak_num - birth_nak_num) % 27
    tara_pos = diff + 1  # 1 to 27
    cycle = (tara_pos - 1) // 9 + 1  # 1, 2, or 3
    tara_num = ((tara_pos - 1) % 9) + 1  # 1 to 9
    tara_name = TARA_NAMES[tara_num - 1]
    return {
        "tara_number": tara_num,
        "tara_name": tara_name,
        "quality": TARA_QUALITY[tara_name],
        "cycle": cycle,
        "raw_distance": diff,
    }


def calc_full_nava_tara(chart):
    """
    Build the full Nava-Tara table for all 27 nakshatras
    relative to birth Moon's nakshatra.

    Returns:
        dict with birth_nakshatra, table (list of 27 entries)
    """
    moon_pos = chart.positions.get("Moon", {})
    if not isinstance(moon_pos, dict):
        return {"birth_nakshatra": "Unknown", "table": []}

    moon_nak = moon_pos.get("nakshatra", "")
    moon_nak_num = 0
    for n in NAKSHATRAS:
        if n["name"] == moon_nak:
            moon_nak_num = n["num"]
            break

    if not moon_nak_num:
        return {"birth_nakshatra": moon_nak, "table": []}

    table = []
    for n in NAKSHATRAS:
        tara = calc_nava_tara(moon_nak_num, n["num"])
        tara["nakshatra"] = n["name"]
        tara["nakshatra_num"] = n["num"]
        tara["lord"] = n["lord"]
        table.append(tara)

    return {
        "birth_nakshatra": moon_nak,
        "birth_nakshatra_num": moon_nak_num,
        "table": table,
    }


# ═══════════════════════════════════════════
# PUSHKARA BHAGA (Lucky Degrees)
# ═══════════════════════════════════════════

# Pushkara Bhaga = specific degrees within each sign that grant
# exceptional auspiciousness. From BPHS / CS Patel.
PUSHKARA_BHAGA = {
    "Aries":       [21],
    "Taurus":      [14],
    "Gemini":      [18],
    "Cancer":      [8],
    "Leo":         [19],
    "Virgo":       [9],
    "Libra":       [24],
    "Scorpio":     [11],
    "Sagittarius": [23],
    "Capricorn":   [14],
    "Aquarius":    [19],
    "Pisces":      [9],
}

# Mrityu Bhaga = degrees of death/danger within each sign.
# From Prasna Marga / BPHS.
MRITYU_BHAGA = {
    "Sun":     {"Aries": 20, "Taurus": 9, "Gemini": 12, "Cancer": 6, "Leo": 8,
                "Virgo": 24, "Libra": 16, "Scorpio": 17, "Sagittarius": 22,
                "Capricorn": 2, "Aquarius": 3, "Pisces": 23},
    "Moon":    {"Aries": 26, "Taurus": 12, "Gemini": 13, "Cancer": 25, "Leo": 24,
                "Virgo": 11, "Libra": 26, "Scorpio": 14, "Sagittarius": 13,
                "Capricorn": 25, "Aquarius": 5, "Pisces": 12},
    "Mars":    {"Aries": 19, "Taurus": 28, "Gemini": 25, "Cancer": 23, "Leo": 29,
                "Virgo": 28, "Libra": 14, "Scorpio": 21, "Sagittarius": 2,
                "Capricorn": 15, "Aquarius": 11, "Pisces": 16},
    "Mercury": {"Aries": 15, "Taurus": 14, "Gemini": 13, "Cancer": 12, "Leo": 8,
                "Virgo": 18, "Libra": 20, "Scorpio": 10, "Sagittarius": 21,
                "Capricorn": 22, "Aquarius": 7, "Pisces": 5},
    "Jupiter": {"Aries": 19, "Taurus": 29, "Gemini": 12, "Cancer": 27, "Leo": 6,
                "Virgo": 4, "Libra": 13, "Scorpio": 10, "Sagittarius": 17,
                "Capricorn": 11, "Aquarius": 15, "Pisces": 28},
    "Venus":   {"Aries": 28, "Taurus": 15, "Gemini": 11, "Cancer": 17, "Leo": 10,
                "Virgo": 13, "Libra": 4, "Scorpio": 18, "Sagittarius": 20,
                "Capricorn": 16, "Aquarius": 14, "Pisces": 25},
    "Saturn":  {"Aries": 10, "Taurus": 4, "Gemini": 7, "Cancer": 9, "Leo": 12,
                "Virgo": 17, "Libra": 22, "Scorpio": 23, "Sagittarius": 24,
                "Capricorn": 29, "Aquarius": 4, "Pisces": 19},
}

# Orb for Mrityu Bhaga = ±1°
MRITYU_ORB = 1.0


def calc_pushkara_mrityu(chart):
    """
    Check all planets for Pushkara Bhaga and Mrityu Bhaga.

    Returns:
        dict keyed by planet with pushkara/mrityu status
    """
    results = {}
    for p in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(p, {})
        if not isinstance(pos, dict):
            continue
        sign = pos.get("sign", "")
        deg = pos.get("degree_in_sign", 0.0)
        if not sign:
            continue

        # Pushkara Bhaga check
        pb_list = PUSHKARA_BHAGA.get(sign, [])
        is_pushkara = any(abs(deg - pb) < 1.0 for pb in pb_list)

        # Mrityu Bhaga check (only for 7 planets, not Lagna/Rahu/Ketu)
        is_mrityu = False
        mrityu_deg = None
        if p in MRITYU_BHAGA:
            mrityu_deg = MRITYU_BHAGA[p].get(sign)
            if mrityu_deg is not None:
                is_mrityu = abs(deg - mrityu_deg) <= MRITYU_ORB

        results[p] = {
            "sign": sign,
            "degree": round(deg, 2),
            "is_pushkara_bhaga": is_pushkara,
            "pushkara_degrees": pb_list,
            "is_mrityu_bhaga": is_mrityu,
            "mrityu_degree": mrityu_deg,
        }
    return results


# ═══════════════════════════════════════════
# NAKSHATRA PROFILES
# ═══════════════════════════════════════════

# Career, health, and relationship tendencies per nakshatra
# Source: Sunil John Parts 1+2, Deepanshu Giri
NAKSHATRA_PROFILES = {
    "Ashwini":       {"career": ["Doctors", "Healers", "Emergency services", "Racing"],
                      "health": ["Head injuries", "Brain disorders", "Migraine"],
                      "spouse": "Active, athletic, healer type"},
    "Bharani":       {"career": ["Legal", "Finance", "Entertainment", "Taboo fields"],
                      "health": ["Reproductive issues", "Urinary"],
                      "spouse": "Intense, passionate, possessive"},
    "Krittika":      {"career": ["Military", "Cooking", "Authority", "Critics"],
                      "health": ["Fevers", "Inflammations", "Acidity"],
                      "spouse": "Sharp-tongued, warm heart, protective"},
    "Rohini":        {"career": ["Arts", "Agriculture", "Fashion", "Music"],
                      "health": ["Throat", "Cold", "Tonsils"],
                      "spouse": "Beautiful, materialistic, sensual"},
    "Mrigashira":    {"career": ["Research", "Travel", "Real estate", "Writing"],
                      "health": ["Sinuses", "Allergies", "Nasal"],
                      "spouse": "Curious, seeking, always searching"},
    "Ardra":         {"career": ["Technology", "Destruction/Renovation", "Surgery"],
                      "health": ["Mental stress", "Nervous disorders"],
                      "spouse": "Intense, transformative, storms"},
    "Punarvasu":     {"career": ["Teaching", "Counseling", "Archery", "Religion"],
                      "health": ["Lungs", "Chest"],
                      "spouse": "Caring, returns home, mother-like"},
    "Pushya":        {"career": ["Government", "Banking", "Counseling", "Priesthood"],
                      "health": ["Chest", "Stomach acids"],
                      "spouse": "Nurturing, older soul, steady"},
    "Ashlesha":      {"career": ["Psychology", "Occult", "Poisons", "Research"],
                      "health": ["Nervous system", "Joints", "Mental health"],
                      "spouse": "Cunning, perceptive, magnetic"},
    "Magha":         {"career": ["Administration", "Government", "Ancestral work"],
                      "health": ["Heart", "Spine"],
                      "spouse": "Royal bearing, status-conscious"},
    "Purva Phalguni":{"career": ["Entertainment", "Arts", "Luxury goods", "Hospitality"],
                      "health": ["Heart", "Lips", "Circulation"],
                      "spouse": "Creative, romantic, luxury-loving"},
    "Uttara Phalguni":{"career": ["Social work", "Management", "Government", "Contracts"],
                       "health": ["Back pain", "Intestines", "Skin"],
                       "spouse": "Reliable, supportive, good manager"},
    "Hasta":         {"career": ["Crafts", "Surgery", "Magic", "Commerce"],
                      "health": ["Hands", "Arms", "Allergies"],
                      "spouse": "Skillful, dexterous, helpful"},
    "Chitra":        {"career": ["Architecture", "Design", "Jewelry", "Engineering"],
                      "health": ["Abdomen", "Kidneys"],
                      "spouse": "Attractive, creative, proud"},
    "Swati":         {"career": ["Trade", "Import/Export", "Diplomacy", "Wind energy"],
                      "health": ["Bladder", "Kidneys", "Skin"],
                      "spouse": "Independent, balanced, business-minded"},
    "Vishakha":      {"career": ["Goal-driven work", "Sales", "Occult", "Research"],
                      "health": ["Liver", "Pancreas"],
                      "spouse": "Ambitious, competitive, victory-oriented"},
    "Anuradha":      {"career": ["Organization", "Math", "Mysticism", "International"],
                      "health": ["Hips", "Bladder"],
                      "spouse": "Loyal, devoted, friendship-based love"},
    "Jyeshtha":      {"career": ["Police", "Military", "Investigation", "Leadership"],
                      "health": ["Neck", "Stomach"],
                      "spouse": "Senior type, protective, chief-like"},
    "Moola":         {"career": ["Research", "Roots", "Medicine", "Destruction"],
                      "health": ["Sciatica", "Hip pain", "Nervous system"],
                      "spouse": "Transformative, uproots old patterns"},
    "Purva Ashadha": {"career": ["Water-related", "Media", "Motivation", "Purification"],
                      "health": ["Thighs", "Blood"],
                      "spouse": "Proud, invincible, declares victory"},
    "Uttara Ashadha":{"career": ["Government", "Law", "Military command"],
                      "health": ["Thighs", "Knees"],
                      "spouse": "Virtuous, principled, ultimate victory"},
    "Shravana":      {"career": ["Media", "Counseling", "Education", "Music"],
                      "health": ["Ears", "Skin"],
                      "spouse": "Good listener, learned, connects"},
    "Dhanishtha":    {"career": ["Music", "Real estate", "Charity", "Sports"],
                      "health": ["Bones", "Joints"],
                      "spouse": "Wealthy, musical, group-oriented"},
    "Shatabhisha":   {"career": ["Technology", "Medicine", "Astrology", "Electronics"],
                      "health": ["Calves", "Circulation"],
                      "spouse": "Secretive, healer, 100 doctors"},
    "Purva Bhadrapada":{"career": ["Fire work", "Occult", "Intense research"],
                        "health": ["Ankles", "Liver"],
                        "spouse": "Intense, fiery, transformative"},
    "Uttara Bhadrapada":{"career": ["Spiritual teaching", "Counseling", "Charity"],
                         "health": ["Feet", "Sleep disorders"],
                         "spouse": "Wise, controlled, deep waters"},
    "Revati":        {"career": ["Travel", "Wealth management", "Nurturing", "Roads"],
                      "health": ["Feet", "Ankles"],
                      "spouse": "Wealthy, nurturing, journey companion"},
}


def calc_nakshatra_profile(chart):
    """
    Return nakshatra-based career, health, and spouse profiles
    for key points: Lagna, Moon, 7th lord.
    """
    results = {}
    for key in ["Lagna", "Moon", "Sun"]:
        pos = chart.positions.get(key, {})
        if not isinstance(pos, dict):
            continue
        nak = pos.get("nakshatra", "")
        profile = NAKSHATRA_PROFILES.get(nak, {})
        results[key] = {
            "nakshatra": nak,
            "pada": pos.get("pada"),
            "career_tendencies": profile.get("career", []),
            "health_vulnerabilities": profile.get("health", []),
            "spouse_description": profile.get("spouse", ""),
        }
    return results


# ═══════════════════════════════════════════
# MASTER BUNDLE
# ═══════════════════════════════════════════

def calc_nakshatra_bundle(chart):
    """
    Compute the full nakshatra predictive bundle.

    Returns:
        dict with activation_ages, nava_tara, pushkara_mrityu, profiles
    """
    return {
        "activation_ages": calc_activation_ages(chart),
        "nava_tara": calc_full_nava_tara(chart),
        "pushkara_mrityu": calc_pushkara_mrityu(chart),
        "profiles": calc_nakshatra_profile(chart),
    }
