"""
constants.py — Core astrological constants: signs, nakshatras, lords, dignities.
All data is static and offline — no external dependencies.
"""

# ═══════════════════════════════════════════
# SIGNS (Rashis)
# ═══════════════════════════════════════════

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_INDEX = {s: i for i, s in enumerate(SIGNS)}  # "Aries" -> 0

SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}

SIGN_ELEMENT = {
    "Aries": "Fire", "Taurus": "Earth", "Gemini": "Air",
    "Cancer": "Water", "Leo": "Fire", "Virgo": "Earth",
    "Libra": "Air", "Scorpio": "Water", "Sagittarius": "Fire",
    "Capricorn": "Earth", "Aquarius": "Air", "Pisces": "Water"
}

SIGN_MODALITY = {
    "Aries": "Movable", "Taurus": "Fixed", "Gemini": "Dual",
    "Cancer": "Movable", "Leo": "Fixed", "Virgo": "Dual",
    "Libra": "Movable", "Scorpio": "Fixed", "Sagittarius": "Dual",
    "Capricorn": "Movable", "Aquarius": "Fixed", "Pisces": "Dual"
}

# ═══════════════════════════════════════════
# PLANETS (Grahas)
# ═══════════════════════════════════════════

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
PLANETS_7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]  # For Jaimini 7-planet
PLANETS_9 = PLANETS  # All 9 including nodes

# Swiss Ephemeris planet IDs
import swisseph as swe
PLANET_SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,  # Mean Rahu (True node = swe.TRUE_NODE)
    # Ketu = Rahu + 180°
}

# ═══════════════════════════════════════════
# NAKSHATRAS (27 lunar mansions)
# ═══════════════════════════════════════════

NAKSHATRAS = [
    {"num": 1,  "name": "Ashwini",        "lord": "Ketu",    "deity": "Ashwini Kumaras"},
    {"num": 2,  "name": "Bharani",         "lord": "Venus",   "deity": "Yama"},
    {"num": 3,  "name": "Krittika",        "lord": "Sun",     "deity": "Agni"},
    {"num": 4,  "name": "Rohini",          "lord": "Moon",    "deity": "Brahma"},
    {"num": 5,  "name": "Mrigashira",      "lord": "Mars",    "deity": "Soma"},
    {"num": 6,  "name": "Ardra",           "lord": "Rahu",    "deity": "Rudra"},
    {"num": 7,  "name": "Punarvasu",       "lord": "Jupiter", "deity": "Aditi"},
    {"num": 8,  "name": "Pushya",          "lord": "Saturn",  "deity": "Brihaspati"},
    {"num": 9,  "name": "Ashlesha",        "lord": "Mercury", "deity": "Nagas"},
    {"num": 10, "name": "Magha",           "lord": "Ketu",    "deity": "Pitris"},
    {"num": 11, "name": "Purva Phalguni",  "lord": "Venus",   "deity": "Bhaga"},
    {"num": 12, "name": "Uttara Phalguni", "lord": "Sun",     "deity": "Aryaman"},
    {"num": 13, "name": "Hasta",           "lord": "Moon",    "deity": "Savitr"},
    {"num": 14, "name": "Chitra",          "lord": "Mars",    "deity": "Tvashtr"},
    {"num": 15, "name": "Swati",           "lord": "Rahu",    "deity": "Vayu"},
    {"num": 16, "name": "Vishakha",        "lord": "Jupiter", "deity": "Indra-Agni"},
    {"num": 17, "name": "Anuradha",        "lord": "Saturn",  "deity": "Mitra"},
    {"num": 18, "name": "Jyeshtha",        "lord": "Mercury", "deity": "Indra"},
    {"num": 19, "name": "Moola",           "lord": "Ketu",    "deity": "Nirrti"},
    {"num": 20, "name": "Purva Ashadha",   "lord": "Venus",   "deity": "Apas"},
    {"num": 21, "name": "Uttara Ashadha",  "lord": "Sun",     "deity": "Vishvedevas"},
    {"num": 22, "name": "Shravana",        "lord": "Moon",    "deity": "Vishnu"},
    {"num": 23, "name": "Dhanishtha",      "lord": "Mars",    "deity": "Vasus"},
    {"num": 24, "name": "Shatabhisha",     "lord": "Rahu",    "deity": "Varuna"},
    {"num": 25, "name": "Purva Bhadrapada","lord": "Jupiter", "deity": "Aja Ekapada"},
    {"num": 26, "name": "Uttara Bhadrapada","lord": "Saturn", "deity": "Ahir Budhnya"},
    {"num": 27, "name": "Revati",          "lord": "Mercury", "deity": "Pushan"},
]

NAKSHATRA_SPAN = 360.0 / 27  # 13°20' per nakshatra
PADA_SPAN = NAKSHATRA_SPAN / 4  # 3°20' per pada

# Vimshottari dasha order and durations (years)
VIMSHOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}
VIMSHOTTARI_TOTAL = 120  # Total cycle in years

# Yogini dasha order and durations
YOGINI_NAMES = ["Mangala", "Pingala", "Dhanya", "Bhramari", "Bhadrika", "Ulka", "Siddha", "Sankata"]
YOGINI_PLANETS = ["Moon", "Sun", "Jupiter", "Mars", "Mercury", "Saturn", "Venus", "Rahu"]
YOGINI_YEARS = [1, 2, 3, 4, 5, 6, 7, 8]
YOGINI_TOTAL = 36

# ═══════════════════════════════════════════
# DIGNITY TABLE (friendship / enmity)
# ═══════════════════════════════════════════

# Exaltation signs and degrees
EXALTATION = {
    "Sun": ("Aries", 10), "Moon": ("Taurus", 3), "Mars": ("Capricorn", 28),
    "Mercury": ("Virgo", 15), "Jupiter": ("Cancer", 5),
    "Venus": ("Pisces", 27), "Saturn": ("Libra", 20),
    "Rahu": ("Taurus", 20), "Ketu": ("Scorpio", 20)
}

# Debilitation signs (opposite of exaltation)
DEBILITATION = {
    "Sun": ("Libra", 10), "Moon": ("Scorpio", 3), "Mars": ("Cancer", 28),
    "Mercury": ("Pisces", 15), "Jupiter": ("Capricorn", 5),
    "Venus": ("Virgo", 27), "Saturn": ("Aries", 20),
    "Rahu": ("Scorpio", 20), "Ketu": ("Taurus", 20)
}

# Moolatrikona signs and degree ranges
MOOLATRIKONA = {
    "Sun": ("Leo", 0, 20), "Moon": ("Taurus", 3, 30),
    "Mars": ("Aries", 0, 12), "Mercury": ("Virgo", 15, 20),
    "Jupiter": ("Sagittarius", 0, 10), "Venus": ("Libra", 0, 15),
    "Saturn": ("Aquarius", 0, 20)
}

# Own signs (Swakshetra)
OWN_SIGNS = {
    "Sun": ["Leo"], "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"], "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"], "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
    "Rahu": ["Aquarius"], "Ketu": ["Scorpio"]  # per some traditions
}

# Natural friendships (Naisargika Maitri)
NATURAL_FRIENDS = {
    "Sun":     ["Moon", "Mars", "Jupiter"],
    "Moon":    ["Sun", "Mercury"],
    "Mars":    ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus":   ["Mercury", "Saturn"],
    "Saturn":  ["Mercury", "Venus"],
}

NATURAL_ENEMIES = {
    "Sun":     ["Venus", "Saturn"],
    "Moon":    [],  # No natural enemies
    "Mars":    ["Mercury"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus"],
    "Venus":   ["Sun", "Moon"],
    "Saturn":  ["Sun", "Moon", "Mars"],
}

# ═══════════════════════════════════════════
# ASPECTS (Graha Drishti — Parashari)
# ═══════════════════════════════════════════

# All planets aspect the 7th house from them.
# Special aspects: Mars (4th, 8th), Jupiter (5th, 9th), Saturn (3rd, 10th)
# Rahu/Ketu: same as Jupiter per some schools (5th, 9th)
SPECIAL_ASPECTS = {
    "Mars": [4, 8],
    "Jupiter": [5, 9],
    "Saturn": [3, 10],
    "Rahu": [5, 9],   # Per Parashara
    "Ketu": [5, 9],
}

# ═══════════════════════════════════════════
# HOUSE LORDSHIPS BY LAGNA
# ═══════════════════════════════════════════

def get_house_lordships(lagna_sign):
    """Return dict of house_number -> lord planet for given lagna sign."""
    lagna_idx = SIGN_INDEX[lagna_sign]
    lordships = {}
    for h in range(1, 13):
        sign_idx = (lagna_idx + h - 1) % 12
        sign = SIGNS[sign_idx]
        lordships[h] = SIGN_LORDS[sign]
    return lordships


def get_functional_nature(lagna_sign):
    """
    Classify planets as benefic/malefic/neutral for a given lagna.
    Returns dict with keys: 'benefic', 'malefic', 'neutral'
    Follows Parashara rules:
    - Trikona lords (1, 5, 9) = benefic
    - Kendra lords (1, 4, 7, 10) = depends on natural nature
    - Trishadaya lords (3, 6, 11) = malefic
    - Dusthana lords (6, 8, 12) = malefic
    - 2L/7L = maraka
    """
    lordships = get_house_lordships(lagna_sign)

    # Build reverse: planet -> list of houses
    planet_houses = {}
    for h, p in lordships.items():
        planet_houses.setdefault(p, []).append(h)

    benefics = []
    malefics = []
    neutrals = []

    trikona = {1, 5, 9}
    kendra = {1, 4, 7, 10}
    dusthana = {6, 8, 12}
    trishadaya = {3, 6, 11}
    maraka = {2, 7}

    for planet, houses in planet_houses.items():
        house_set = set(houses)
        is_trikona = bool(house_set & trikona)
        is_kendra = bool(house_set & kendra)
        is_dusthana = bool(house_set & dusthana)
        is_trishadaya = bool(house_set & trishadaya)
        is_maraka = bool(house_set & maraka)

        # Yogakaraka: lords of both a trikona and a kendra (excluding 1st)
        non_first_trikona = house_set & {5, 9}
        non_first_kendra = house_set & {4, 7, 10}
        if non_first_trikona and non_first_kendra:
            benefics.append((planet, houses, "Yogakaraka"))
        elif is_trikona:
            benefics.append((planet, houses, "Trikona lord"))
        elif is_maraka and not is_trikona:
            malefics.append((planet, houses, "Maraka"))
        elif is_trishadaya and not is_trikona:
            malefics.append((planet, houses, "Trishadaya lord"))
        elif is_kendra:
            neutrals.append((planet, houses, "Kendra lord"))
        else:
            malefics.append((planet, houses, "Dusthana/other"))

    return {"benefic": benefics, "malefic": malefics, "neutral": neutrals}


# ═══════════════════════════════════════════
# NAVAMSA DIVISION RULE
# ═══════════════════════════════════════════

NAVAMSA_START = {
    # Fire signs start from Aries, Earth from Capricorn,
    # Air from Libra, Water from Cancer
    "Fire": 0,   # Aries index
    "Earth": 9,  # Capricorn index
    "Air": 6,    # Libra index
    "Water": 3,  # Cancer index
}

def get_navamsa_sign(longitude):
    """
    Calculate navamsa (D9) sign from sidereal longitude.
    Each navamsa = 3°20' (400 minutes).
    """
    sign_idx = int(longitude / 30)
    degree_in_sign = longitude - (sign_idx * 30)
    navamsa_num = int(degree_in_sign / (30.0 / 9))  # 0-8 within sign

    element = SIGN_ELEMENT[SIGNS[sign_idx]]
    start = NAVAMSA_START[element]
    result_idx = (start + navamsa_num) % 12
    return SIGNS[result_idx]


# ═══════════════════════════════════════════
# VARGA DIVISION RULES (D1-D60)
# ═══════════════════════════════════════════

def calc_varga_sign(longitude, divisor, varga_type="standard"):
    """
    Generic varga division. Returns the sign index (0-11) for a given longitude
    and division factor.
    
    For D2 (Hora): special Sun/Moon rule.
    For D3 (Drekkana): based on element.
    For most others: standard cyclic division.
    """
    sign_idx = int(longitude / 30)
    degree_in_sign = longitude - (sign_idx * 30)
    division = int(degree_in_sign / (30.0 / divisor))

    if varga_type == "standard":
        return (sign_idx * divisor + division) % 12
    else:
        return division  # Return raw division index for special handling


# Varga divisors
VARGA_DIVISORS = {
    "D1": 1, "D2": 2, "D3": 3, "D4": 4, "D5": 5, "D6": 6,
    "D7": 7, "D8": 8, "D9": 9, "D10": 10, "D11": 11, "D12": 12,
    "D16": 16, "D20": 20, "D24": 24, "D27": 27, "D30": 30,
    "D40": 40, "D45": 45, "D60": 60
}
