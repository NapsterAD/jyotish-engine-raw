"""
lal_kitab.py — Pakka Ghar, Masnui grahas, Soya Hua, Andha Teva, Pitru Rin.
rules.md §23. Chart-agnostic.
"""

from ..core.constants import PLANETS_9, SIGN_LORDS

PAKKA_GHAR = {
    1: {"lords": ["Mars", "Sun"], "exalted": ["Sun"], "debilitated": ["Saturn"]},
    2: {"lords": ["Jupiter"], "exalted": ["Moon"], "debilitated": []},
    3: {"lords": ["Mars"], "exalted": ["Rahu"], "debilitated": ["Ketu"]},
    4: {"lords": ["Moon"], "exalted": ["Jupiter"], "debilitated": ["Mars"]},
    5: {"lords": ["Jupiter"], "exalted": ["Sun"], "debilitated": []},
    6: {"lords": ["Mercury", "Ketu"], "exalted": ["Mercury", "Rahu"],
        "debilitated": ["Venus", "Ketu"]},
    7: {"lords": ["Venus", "Mercury"], "exalted": ["Saturn"], "debilitated": ["Sun"]},
    8: {"lords": ["Saturn", "Mars"], "exalted": [], "debilitated": ["Moon"]},
    9: {"lords": ["Jupiter"], "exalted": ["Ketu"], "debilitated": ["Rahu"]},
    10: {"lords": ["Saturn"], "exalted": ["Mars"], "debilitated": ["Jupiter"]},
    11: {"lords": ["Jupiter"], "exalted": [], "debilitated": []},
    12: {"lords": ["Jupiter", "Rahu"], "exalted": ["Venus", "Ketu"],
         "debilitated": ["Mercury", "Rahu"]},
}

MASNUI = {
    "Sun": [("Jupiter", "Ketu")],
    "Moon": [("Jupiter", "Venus")],
    "Mars_benefic": [("Sun", "Mercury")],
    "Mars_malefic": [("Sun", "Saturn")],
    "Mercury": [("Jupiter", "Rahu")],
    "Jupiter": [("Sun", "Moon")],
    "Venus": [("Rahu", "Ketu")],
    "Saturn": [("Venus", "Mars")],
    "Rahu": [("Mars", "Saturn")],
    "Ketu": [("Venus", "Saturn")],
}


def _house(chart, planet):
    return chart.rashi_chart.get(planet, {}).get("house_rashi", 0)


def _conjunct(chart, a, b):
    return _house(chart, a) and _house(chart, a) == _house(chart, b)


def calc_lal_kitab(chart):
    sleeping_houses = []
    for h in range(1, 13):
        occ = chart.get_planets_in_house(h, "rashi")
        aspected = chart.get_aspects_to_house(h)
        if not occ and not aspected:
            sleeping_houses.append(h)

    masnui_active = {}
    for name, pairs in MASNUI.items():
        hits = []
        for a, b in pairs:
            if _conjunct(chart, a, b):
                hits.append((a, b))
        if hits:
            masnui_active[name] = hits

    sun1 = _house(chart, "Sun") == 1
    sat7 = _house(chart, "Saturn") == 7
    andha = sun1 and sat7

    def afflicted(planet, by_list, houses):
        h = _house(chart, planet)
        if h not in houses:
            return False
        for other in by_list:
            if _conjunct(chart, planet, other):
                return True
            if h in chart.aspects.get(other, []):
                return True
        return False

    rin = {
        "Pitru": afflicted("Jupiter", ["Venus", "Mercury", "Rahu"], {2, 5, 9, 12}),
        "Matru": afflicted("Moon", ["Ketu"], {2, 4, 8}),
        "Stri": afflicted("Venus", ["Sun", "Moon", "Rahu"], {2, 7}),
        "Bhratri": afflicted("Mars", ["Mercury", "Ketu"], {1, 3, 8}),
        "Svajan": afflicted("Sun", ["Venus", "Saturn", "Rahu"], {1, 5}),
        "Kanya": afflicted("Mercury", ["Moon"], {3, 6}),
        "Nirmamta": afflicted("Saturn", ["Sun", "Moon", "Mars"], {8, 10, 11}),
        "Rahu": afflicted("Rahu", ["Sun", "Venus", "Mars"], {12}),
        "Ketu": afflicted("Ketu", ["Moon", "Mars"], {6}),
    }
    return {
        "pakka_ghar": PAKKA_GHAR,
        "sleeping_houses": sleeping_houses,
        "masnui_active": masnui_active,
        "andha_teva": andha,
        "pitru_rin": {k: v for k, v in rin.items() if v},
        "pitru_rin_all": rin,
    }
