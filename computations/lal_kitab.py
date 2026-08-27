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
        "nek_manda_grahas": calc_nek_manda_planets(chart),
        "dhaat_metals": LAL_KITAB_METALS,
        "remedies": calc_lal_kitab_remedies(chart),
    }


# ═══════════════════════════════════════════
# LAL KITAB METALS, ARTICLES & REMEDIES
# ═══════════════════════════════════════════
# Sources: Lal Kitab 1952, Arun Sanhita, BM Gosvami

LAL_KITAB_METALS = {
    "Sun": {"metal": "Gold / Copper", "article": "Wheat, Jaggery, Ruby", "direction": "East"},
    "Moon": {"metal": "Silver", "article": "Milk, Water, Rice, Pearl", "direction": "North-West"},
    "Mars": {"metal": "Copper / Brass", "article": "Red Lentils, Honey, Red Coral", "direction": "South"},
    "Mercury": {"metal": "Bronze / Bell-metal", "article": "Green Gram (Moong), Emerald", "direction": "North"},
    "Jupiter": {"metal": "Gold / Brass", "article": "Gram Dal, Turmeric, Yellow Sapphire", "direction": "North-East"},
    "Venus": {"metal": "Silver / Platinum", "article": "Curd, Camphor, Diamond, White Silk", "direction": "South-East"},
    "Saturn": {"metal": "Iron", "article": "Mustard Oil, Black Sesame, Blue Sapphire", "direction": "West"},
    "Rahu": {"metal": "Lead", "article": "Barley, Coconut, Hessonite (Gomed)", "direction": "South-West"},
    "Ketu": {"metal": "Two-metal (Gold+Silver alloy)", "article": "Black & White Sesame, Cat's Eye", "direction": "Center"},
}

LAL_KITAB_CLASSICAL_UPAYAS = {
    ("Sun", 1): "Keep pure water at home; avoid taking free gifts.",
    ("Sun", 12): "Do not tell lies; keep religious books in home.",
    ("Moon", 3): "Serve girls; avoid donating milk/water.",
    ("Moon", 4): "Respect mother; worship Lord Shiva with milk.",
    ("Mars", 1): "Wear silver ring; avoid eating sweets on Tuesday.",
    ("Mars", 11): "Keep gold at home; care for elder brother.",
    ("Mercury", 1): "Feed green fodder to cows; wear green sparingly.",
    ("Mercury", 12): "Wear steel ring without joints; keep pure intentions.",
    ("Jupiter", 8): "Wear gold chain; respect spiritual mentors and gurus.",
    ("Jupiter", 9): "Visit temple regularly; apply saffron (kesar) tilak on forehead.",
    ("Venus", 1): "Feed cows curd/ghee; respect women; maintain clean clothes.",
    ("Venus", 7): "Serve white cows; donate milk and silver.",
    ("Saturn", 8): "Do not consume alcohol or non-vegetarian food; serve the underprivileged.",
    ("Saturn", 10): "Feed stray black dogs with mustard-oil smeared rotis.",
    ("Rahu", 9): "Wear silver; maintain cordial relations with grandfather.",
    ("Ketu", 3): "Serve stray dogs with bread/roti; maintain spiritual discipline.",
}


def calc_nek_manda_planets(chart):
    """
    Classify planets as Nek (Benefic/Favorable) or Manda (Malefic/Depressed)
    per Lal Kitab house placement and Pakka Ghar rules.
    """
    status = {}
    for p in PLANETS_9:
        h = _house(chart, p)
        if not h:
            continue
        pakka = PAKKA_GHAR.get(h, {})
        is_pakka_lord = p in pakka.get("lords", [])
        is_exalted_house = p in pakka.get("exalted", [])
        is_debilitated_house = p in pakka.get("debilitated", [])
        
        if is_debilitated_house:
            cat = "MANDA"
            reason = f"Placed in Pakka Debilitation house H{h}"
        elif is_exalted_house or is_pakka_lord:
            cat = "NEK"
            reason = f"Placed in Pakka Own/Exaltation house H{h}"
        elif h in {6, 8, 12}:
            cat = "MANDA"
            reason = f"Placed in Lal Kitab boundary house H{h}"
        else:
            cat = "NEK"
            reason = f"Favorable house placement H{h}"
            
        status[p] = {"house": h, "status": cat, "reason": reason}
    return status


def calc_lal_kitab_remedies(chart):
    """
    Generate applicable classical Lal Kitab remedies based on planetary house placements.
    """
    remedies = []
    for p in PLANETS_9:
        h = _house(chart, p)
        if (p, h) in LAL_KITAB_CLASSICAL_UPAYAS:
            remedies.append({
                "planet": p,
                "house": h,
                "metal": LAL_KITAB_METALS.get(p, {}).get("metal", ""),
                "upaya": LAL_KITAB_CLASSICAL_UPAYAS[(p, h)],
            })
    return remedies

