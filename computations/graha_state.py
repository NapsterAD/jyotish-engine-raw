"""
graha_state.py — Universal natal flags that depend only on this chart's
longitudes / Lagna: combustion, Graha Yuddha, Badhaka, Jaimini rashi drishti.
Formulas: rules.md §2.7, §2.8, §2.11, §7.2.
"""

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, SIGN_MODALITY,
    PLANETS_9,
)
from ..core.mapping import house_to_sign, badhaka_house as _badhaka_house

# Direct / retrograde orbs (degrees). Moon has no retro. rules.md §2.7.
COMBUSTION_ORBS = {
    "Moon": (12.0, None),
    "Mars": (17.0, 17.0),
    "Mercury": (14.0, 12.0),
    "Jupiter": (11.0, 11.0),
    "Venus": (10.0, 8.0),
    "Saturn": (15.0, 15.0),
}

YUDDHA_PLANETS = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
YUDDHA_ORB = 1.0
ECLIPSE_ORB = 15.0

# Badhaka house offset from Lagna (0-based house index add). rules.md §2.11.
BADHAKA_HOUSE = {
    "Movable": 11,  # 11th
    "Fixed": 9,     # 9th
    "Dual": 7,      # 7th
}


def angular_sep(a, b):
    """Shortest arc between two longitudes, 0..180."""
    d = abs((a - b) % 360.0)
    return d if d <= 180.0 else 360.0 - d


def calc_combustion(chart):
    """
    Combustion (Asta) for every graha of this native.
    Sun is never combust; Rahu/Ketu never combust.
    Sun eclipsed if |Sun − Rahu| ≤ 15°.
    """
    sun = chart.positions.get("Sun", {}).get("longitude", 0.0)
    rahu = chart.positions.get("Rahu", {}).get("longitude", 0.0)
    result = {}
    for planet in PLANETS_9:
        pos = chart.positions.get(planet, {})
        if not isinstance(pos, dict):
            continue
        if planet in ("Rahu", "Ketu"):
            result[planet] = {
                "is_combust": False, "state": "EXEMPT",
                "separation": None, "orb": None,
            }
            continue
        if planet == "Sun":
            sep = angular_sep(sun, rahu)
            result[planet] = {
                "is_combust": False,
                "is_eclipsed": sep <= ECLIPSE_ORB,
                "state": "ECLIPSED" if sep <= ECLIPSE_ORB else "NONE",
                "separation": round(sep, 4),
                "orb": ECLIPSE_ORB,
            }
            continue
        direct_orb, retro_orb = COMBUSTION_ORBS[planet]
        is_retro = bool(pos.get("retrograde"))
        orb = retro_orb if (is_retro and retro_orb is not None) else direct_orb
        sep = angular_sep(pos.get("longitude", 0.0), sun)
        is_combust = sep <= orb
        if not is_combust:
            state = "NONE"
        elif sep <= 3.0:
            state = "FULLY_COMBUST"
        elif sep <= 6.0:
            state = "SEVERELY_COMBUST"
        else:
            state = "MODERATELY_COMBUST"
        result[planet] = {
            "is_combust": is_combust,
            "state": state,
            "separation": round(sep, 4),
            "orb": orb,
            "retrograde": is_retro,
        }
    return result


def calc_graha_yuddha(chart):
    """
    Planetary war among Mars, Mercury, Jupiter, Venus, Saturn.
    Pair is at war if shortest arc ≤ 1°.
    Winner = higher |latitude|; fallback = lesser longitude (Phaladeepika).
    """
    wars = []
    bodies = []
    for planet in YUDDHA_PLANETS:
        pos = chart.positions.get(planet, {})
        if not isinstance(pos, dict):
            continue
        bodies.append(planet)

    for i, p1 in enumerate(bodies):
        for p2 in bodies[i + 1:]:
            long1 = chart.positions[p1]["longitude"]
            long2 = chart.positions[p2]["longitude"]
            sep = angular_sep(long1, long2)
            if sep > YUDDHA_ORB:
                continue
            lat1 = abs(chart.positions[p1].get("latitude") or 0.0)
            lat2 = abs(chart.positions[p2].get("latitude") or 0.0)
            if lat1 != lat2:
                winner = p1 if lat1 > lat2 else p2
                rule = "higher_latitude"
            else:
                winner = p1 if long1 < long2 else p2
                rule = "lesser_longitude"
            loser = p2 if winner == p1 else p1
            wars.append({
                "planets": [p1, p2],
                "separation": round(sep, 4),
                "winner": winner,
                "loser": loser,
                "rule": rule,
            })
    return {
        "wars": wars,
        "in_war": sorted({p for w in wars for p in w["planets"]}),
        "winners": [w["winner"] for w in wars],
        "losers": [w["loser"] for w in wars],
    }


def calc_badhaka(chart):
    """
    Badhaka house and Badhakesh from this Lagna's modality. rules.md §2.11.
    """
    lagna = chart.lagna_sign
    modality = SIGN_MODALITY[lagna]
    house = _badhaka_house(lagna)
    sign = house_to_sign(house, chart.lagna_index)
    lord = SIGN_LORDS[sign]

    yogakarakas = []
    for group in ("benefic",):
        for item in chart.functional_nature.get(group, []):
            planet, houses, tag = item[0], item[1], item[2] if len(item) > 2 else ""
            if tag == "Yogakaraka":
                yogakarakas.append(planet)

    occupants = []
    for planet in PLANETS_9:
        rc = chart.rashi_chart.get(planet, {})
        if rc.get("house_rashi") == house:
            occupants.append(planet)

    return {
        "lagna": lagna,
        "modality": modality,
        "house": house,
        "sign": sign,
        "lord": lord,
        "occupants": occupants,
        "yogakarakas": yogakarakas,
        "has_badhaka_yogakaraka_conflict": lord in yogakarakas,
    }


def jaimini_aspect_signs(sign_name):
    """
    Signs aspected by `sign_name` via Jaimini rashi drishti. rules.md §7.2.
    Movable → all Fixed except the next (2nd).
    Fixed → all Movable except the previous (12th).
    Dual → the other three Duals (4th, 7th, 10th).
    """
    idx = SIGN_INDEX[sign_name]
    modality = SIGN_MODALITY[sign_name]
    if modality == "Movable":
        skip = (idx + 1) % 12  # adjacent fixed
        targets = [i for i, s in enumerate(SIGNS)
                   if SIGN_MODALITY[s] == "Fixed" and i != skip]
    elif modality == "Fixed":
        skip = (idx - 1) % 12  # adjacent movable
        targets = [i for i, s in enumerate(SIGNS)
                   if SIGN_MODALITY[s] == "Movable" and i != skip]
    else:
        targets = [i for i, s in enumerate(SIGNS)
                   if SIGN_MODALITY[s] == "Dual" and i != idx]
    return [SIGNS[i] for i in targets]


def calc_jaimini_drishti(chart):
    """
    For each planet (and Lagna), the signs and planets it aspects by rashi drishti.
    """
    by_sign = {s: jaimini_aspect_signs(s) for s in SIGNS}

    planets_in_sign = {s: [] for s in SIGNS}
    for planet in PLANETS_9:
        pos = chart.positions.get(planet, {})
        if isinstance(pos, dict) and pos.get("sign"):
            planets_in_sign[pos["sign"]].append(planet)

    result = {"by_sign": by_sign, "planets": {}}
    for name in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(name, {})
        if not isinstance(pos, dict):
            continue
        sign = pos.get("sign")
        aspected_signs = by_sign.get(sign, [])
        aspected_planets = []
        for s in aspected_signs:
            aspected_planets.extend(planets_in_sign[s])
        result["planets"][name] = {
            "sign": sign,
            "aspected_signs": aspected_signs,
            "aspected_planets": aspected_planets,
        }
    return result
