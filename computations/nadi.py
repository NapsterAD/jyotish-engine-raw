"""
nadi.py — Bhrigu Nandi Nadi directional conjunctions. rules.md §22.
"""

from ..core.constants import SIGNS, SIGN_INDEX, SIGN_ELEMENT, PLANETS_9

DIRECTION = {
    "Fire": "East", "Earth": "South", "Air": "West", "Water": "North",
}


def same_direction(sign_a, sign_b):
    return SIGN_INDEX[sign_a] % 4 == SIGN_INDEX[sign_b] % 4


def nadi_weight(from_sign, to_sign):
    """Positional weight from P's sign to Q's sign. §22.2."""
    a, b = SIGN_INDEX[from_sign], SIGN_INDEX[to_sign]
    dist = (b - a) % 12  # 0 = same
    house = dist + 1
    if house in (1, 5, 9):
        return 1.0, "trinal"
    if house == 7:
        return 1.0, "opposition"
    if house == 2:
        return 0.75, "front"
    if house == 12:
        return 0.50, "rear"
    if house in (3, 11):
        return 0.25, "supportive"
    return 0.0, "none"


def calc_nadi(chart):
    planets = {}
    for p in PLANETS_9:
        pos = chart.positions.get(p, {})
        if not isinstance(pos, dict):
            continue
        sign = pos.get("sign")
        sidx = pos.get("sign_index", SIGN_INDEX.get(sign, 0))
        retro = bool(pos.get("retrograde"))
        acts_from = [sign]
        if retro:
            acts_from.append(SIGNS[(sidx - 1) % 12])
        links = []
        for q in PLANETS_9:
            if q == p:
                continue
            qsign = chart.positions.get(q, {}).get("sign")
            if not qsign:
                continue
            w, kind = nadi_weight(sign, qsign)
            if w > 0:
                links.append({
                    "planet": q, "sign": qsign, "weight": w, "kind": kind,
                    "same_direction": same_direction(sign, qsign),
                })
        planets[p] = {
            "sign": sign,
            "direction": DIRECTION[SIGN_ELEMENT[sign]],
            "retrograde_dual": retro,
            "acts_from_signs": acts_from,
            "links": links,
        }
    return {
        "planets": planets,
        "karakatwa": {
            "Jupiter": "Jeeva", "Saturn": "Karma", "Venus": "Kalatra/Dhana",
            "Mars": "Bhratri/Pati", "Mercury": "Buddhi/Vidya",
            "Sun": "Pitru/Atma", "Moon": "Matru/Manas",
            "Rahu": "Maya/Pitamaha", "Ketu": "Moksha/Matamaha",
        },
    }
