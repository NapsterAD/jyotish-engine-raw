"""
yogas_nabhasa.py — 32 Nabhasa Yogas (Celestial Yogas).

BPHS Ch. 22-24 / Saravali Ch. 12-13 / BV Raman 300 Combinations.

Categories:
  Ashraya (3): Based on how planets occupy Movable/Fixed/Dual signs.
  Dala   (2): Planets occupy only Kendras or only Panapharas/Apoklimas.
  Akriti (20): Shape-based patterns formed by planetary placement.
  Sankhya (7): Number of signs occupied by planets.

Total: 32 Nabhasa Yogas.
"""

from ..core.constants import (
    SIGNS, SIGN_INDEX, PLANETS_7, PLANETS_9,
)


def _sign_idx_of(chart, planet):
    """Return 0-based sign index of planet."""
    pos = chart.positions.get(planet, {})
    if isinstance(pos, dict):
        return pos.get("sign_index", SIGN_INDEX.get(pos.get("sign", ""), 0))
    return 0


def _house_of(chart, planet):
    return chart.rashi_chart.get(planet, {}).get("house_rashi", 0)


def _occupied_houses(chart, planets=None):
    """Return set of rashi houses occupied by given planets."""
    ps = planets or PLANETS_7
    return {_house_of(chart, p) for p in ps if _house_of(chart, p)}


def _occupied_signs(chart, planets=None):
    """Return set of 0-based sign indices occupied by given planets."""
    ps = planets or PLANETS_7
    return {_sign_idx_of(chart, p) for p in ps}


def _house_set(chart, planets=None):
    """Return {house: [planets]} mapping."""
    ps = planets or PLANETS_7
    hmap = {}
    for p in ps:
        h = _house_of(chart, p)
        if h:
            hmap.setdefault(h, []).append(p)
    return hmap


# ═══════════════════════════════════════════
# ASHRAYA YOGAS (3) — Movable/Fixed/Dual
# ═══════════════════════════════════════════

def check_rajju(chart):
    """
    Rajju Yoga: ALL 7 planets in Movable (Chara) signs.
    Result: Fond of travel, active, restless.
    """
    movable = {"Aries", "Cancer", "Libra", "Capricorn"}
    all_in = all(
        chart.positions.get(p, {}).get("sign", "") in movable
        for p in PLANETS_7
    )
    return {
        "name": "Rajju Yoga (Nabhasa-Ashraya)",
        "formed": all_in,
        "category": "Ashraya",
        "description": "All 7 planets in Movable signs — fond of travel, restless",
    }


def check_musala(chart):
    """
    Musala Yoga: ALL 7 planets in Fixed (Sthira) signs.
    Result: Proud, wealthy, learned, firm resolve.
    """
    fixed = {"Taurus", "Leo", "Scorpio", "Aquarius"}
    all_in = all(
        chart.positions.get(p, {}).get("sign", "") in fixed
        for p in PLANETS_7
    )
    return {
        "name": "Musala Yoga (Nabhasa-Ashraya)",
        "formed": all_in,
        "category": "Ashraya",
        "description": "All 7 planets in Fixed signs — proud, wealthy, firm resolve",
    }


def check_nala(chart):
    """
    Nala Yoga: ALL 7 planets in Dual (Dvisvabhava) signs.
    Result: Skilled artisan, defective limbs, clever.
    """
    dual = {"Gemini", "Virgo", "Sagittarius", "Pisces"}
    all_in = all(
        chart.positions.get(p, {}).get("sign", "") in dual
        for p in PLANETS_7
    )
    return {
        "name": "Nala Yoga (Nabhasa-Ashraya)",
        "formed": all_in,
        "category": "Ashraya",
        "description": "All 7 planets in Dual signs — skilled, clever, adaptable",
    }


# ═══════════════════════════════════════════
# DALA YOGAS (2) — Kendra / Panaphara-Apoklima
# ═══════════════════════════════════════════

def check_maala(chart):
    """
    Maala (Srak) Yoga: ALL planets in Kendras (1,4,7,10) +
    Trikonas (5,9) + 2nd house.
    Variant: All 7 planets in Kendra only. (Strict form)
    General: Benefics in 3 consecutive kendras from Lagna.
    """
    kendra = {1, 4, 7, 10}
    trikona = {5, 9}
    occ = _occupied_houses(chart)
    # Strict: all 7 in kendra only
    strict = occ.issubset(kendra)
    # Relaxed: all 7 in kendra + trikona + 2nd
    relaxed = occ.issubset(kendra | trikona | {2})
    # Benefic pattern: benefics in 3 consecutive kendras
    benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
    ben_houses = {_house_of(chart, p) for p in benefics if _house_of(chart, p)}
    ben_in_kendras = ben_houses & kendra
    return {
        "name": "Maala (Srak) Yoga (Nabhasa-Dala)",
        "formed": strict or (relaxed and len(ben_in_kendras) >= 3),
        "category": "Dala",
        "strict_kendra_only": strict,
        "relaxed": relaxed,
        "benefics_in_kendras": len(ben_in_kendras),
        "description": "Planets in Kendra/Trikona pattern — fortunate, famous",
    }


def check_sarpa(chart):
    """
    Sarpa Yoga: ALL 7 planets in Panapharas (2,5,8,11) only,
    OR all in Apoklimas (3,6,9,12) only.
    Result: Miserable, cruel, dependent.
    """
    panaphara = {2, 5, 8, 11}
    apoklima = {3, 6, 9, 12}
    occ = _occupied_houses(chart)
    in_pan = occ.issubset(panaphara)
    in_apo = occ.issubset(apoklima)
    return {
        "name": "Sarpa Yoga (Nabhasa-Dala)",
        "formed": in_pan or in_apo,
        "category": "Dala",
        "in_panapharas": in_pan,
        "in_apoklimas": in_apo,
        "description": "All planets in Panapharas or Apoklimas — difficulties, dependency",
    }


# ═══════════════════════════════════════════
# AKRITI YOGAS (20) — Shape Patterns
# ═══════════════════════════════════════════

def _consecutive_occupied(chart, houses, planets=None):
    """Check if given houses are all occupied by at least one planet each."""
    ps = planets or PLANETS_7
    hmap = _house_set(chart, ps)
    return all(h in hmap for h in houses)


def check_gada(chart):
    """
    Gada Yoga: Planets only in 2 adjacent Kendras (e.g. 1+4 or 4+7).
    Result: Wealthy through ceremonies/rituals.
    """
    kendra_pairs = [(1, 4), (4, 7), (7, 10), (10, 1)]
    occ = _occupied_houses(chart)
    for a, b in kendra_pairs:
        if occ.issubset({a, b}):
            return {
                "name": "Gada Yoga (Nabhasa-Akriti)",
                "formed": True, "category": "Akriti",
                "pair": (a, b),
                "description": f"All planets in H{a}+H{b} (adjacent Kendras)",
            }
    return {"name": "Gada Yoga (Nabhasa-Akriti)", "formed": False, "category": "Akriti"}


def check_shakata(chart):
    """
    Shakata Yoga (Nabhasa): Planets only in H1+H7 (opposite Kendras).
    (Not the Moon-Jupiter Sakata.)
    Result: Poverty, illness, earns by carrying loads.
    """
    occ = _occupied_houses(chart)
    formed = occ.issubset({1, 7})
    return {
        "name": "Shakata Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "All planets in H1+H7 — poverty pattern" if formed else "",
    }


def check_shringataka(chart):
    """
    Shringataka Yoga: Planets in all 4 Trikonas from any start.
    E.g. H1, H5, H9 (fire trikonas), or all trinal houses occupied.
    Result: Quarrelsome, fond of fighting, happy.
    """
    trikona_groups = [
        {1, 5, 9},   # Fire trikonas (from Lagna)
        {2, 6, 10},  # From 2nd
        {3, 7, 11},  # From 3rd
        {4, 8, 12},  # From 4th
    ]
    occ = _occupied_houses(chart)
    for tri in trikona_groups:
        if tri.issubset(occ):
            return {
                "name": "Shringataka Yoga (Nabhasa-Akriti)",
                "formed": True, "category": "Akriti",
                "trikona_set": sorted(tri),
                "description": f"Planets in all trikonas {sorted(tri)}",
            }
    return {"name": "Shringataka Yoga (Nabhasa-Akriti)", "formed": False, "category": "Akriti"}


def check_hala(chart):
    """
    Hala Yoga: All planets in 3 consecutive houses OTHER than Kendras.
    E.g. H2,H3,H4 or H5,H6,H7.
    Result: Agriculture, farming background.
    """
    occ = sorted(_occupied_houses(chart))
    kendra = {1, 4, 7, 10}
    for start in range(1, 13):
        triple = {((start - 1 + i) % 12) + 1 for i in range(3)}
        if triple & kendra:
            continue
        if set(occ).issubset(triple):
            return {
                "name": "Hala Yoga (Nabhasa-Akriti)",
                "formed": True, "category": "Akriti",
                "houses": sorted(triple),
                "description": f"All planets in consecutive non-kendra {sorted(triple)}",
            }
    return {"name": "Hala Yoga (Nabhasa-Akriti)", "formed": False, "category": "Akriti"}


def check_vajra(chart):
    """
    Vajra Yoga: Benefics in H1+H7, malefics in H4+H10.
    Result: Brave, handsome, happy beginning and end of life.
    """
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    h1 = set(chart.get_planets_in_house(1))
    h7 = set(chart.get_planets_in_house(7))
    h4 = set(chart.get_planets_in_house(4))
    h10 = set(chart.get_planets_in_house(10))
    ben_17 = (h1 | h7) & benefics
    mal_410 = (h4 | h10) & malefics
    formed = len(ben_17) >= 2 and len(mal_410) >= 2
    return {
        "name": "Vajra Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "benefics_in_1_7": sorted(ben_17),
        "malefics_in_4_10": sorted(mal_410),
        "description": "Benefics in 1/7, Malefics in 4/10 — brave, handsome",
    }


def check_yava(chart):
    """
    Yava Yoga: Benefics in H4+H10, malefics in H1+H7 (reverse of Vajra).
    Result: Charitable, happy in middle of life.
    """
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    h1 = set(chart.get_planets_in_house(1))
    h7 = set(chart.get_planets_in_house(7))
    h4 = set(chart.get_planets_in_house(4))
    h10 = set(chart.get_planets_in_house(10))
    ben_410 = (h4 | h10) & benefics
    mal_17 = (h1 | h7) & malefics
    formed = len(ben_410) >= 2 and len(mal_17) >= 2
    return {
        "name": "Yava Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "benefics_in_4_10": sorted(ben_410),
        "malefics_in_1_7": sorted(mal_17),
        "description": "Benefics in 4/10, Malefics in 1/7 — charitable, happy mid-life",
    }


def check_kamala(chart):
    """
    Kamala (Padma) Yoga: All 7 planets in all 4 Kendras (1,4,7,10).
    Result: Virtuous, famous, performs many noble deeds.
    """
    kendra = {1, 4, 7, 10}
    occ = _occupied_houses(chart)
    formed = occ.issubset(kendra) and len(occ & kendra) >= 3
    return {
        "name": "Kamala Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "Planets in Kendras only — virtuous, famous",
    }


def check_vapi(chart):
    """
    Vapi Yoga: All 7 planets in Panapharas only (2,5,8,11) or
    Apoklimas only (3,6,9,12). When both together, NOT Vapi.
    Result: Capable of hoarding wealth.
    """
    pan = {2, 5, 8, 11}
    apo = {3, 6, 9, 12}
    occ = _occupied_houses(chart)
    in_pan = occ.issubset(pan) and len(occ) >= 2
    in_apo = occ.issubset(apo) and len(occ) >= 2
    formed = in_pan or in_apo
    return {
        "name": "Vapi Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "in_panapharas": in_pan,
        "in_apoklimas": in_apo,
        "description": "All planets in Panapharas or Apoklimas — hoards wealth",
    }


def check_yupa(chart):
    """
    Yupa Yoga: All 7 planets in H1,H2,H3,H4 (first quadrant).
    Result: Charitable, performer of sacrifices.
    """
    occ = _occupied_houses(chart)
    formed = occ.issubset({1, 2, 3, 4})
    return {
        "name": "Yupa Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "All planets in H1-H4 — charitable, sacrificial",
    }


def check_ishu(chart):
    """
    Ishu (Shara) Yoga: All planets in H4,H5,H6,H7 (second quadrant).
    Result: Jailer, liar, connected to prison/confinement.
    """
    occ = _occupied_houses(chart)
    formed = occ.issubset({4, 5, 6, 7})
    return {
        "name": "Ishu Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "All planets in H4-H7",
    }


def check_shakti(chart):
    """
    Shakti Yoga: All planets in H7,H8,H9,H10 (third quadrant).
    Result: Lazy, without wealth, miserable.
    """
    occ = _occupied_houses(chart)
    formed = occ.issubset({7, 8, 9, 10})
    return {
        "name": "Shakti Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "All planets in H7-H10 — lazy, poverty",
    }


def check_danda(chart):
    """
    Danda Yoga: All planets in H10,H11,H12,H1 (fourth quadrant).
    Result: Loss of wife/children, miserable.
    """
    occ = _occupied_houses(chart)
    formed = occ.issubset({10, 11, 12, 1})
    return {
        "name": "Danda Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "All planets in H10-H1 — loss, misery",
    }


def check_nauka(chart):
    """
    Nauka (Nau) Yoga: All 7 planets in H1 through H7 (one hemisphere).
    Result: Fond of water, livelihood through navigation/shipping.
    """
    occ = _occupied_houses(chart)
    formed = occ.issubset(set(range(1, 8)))
    return {
        "name": "Nauka Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "All planets in H1-H7 — shipping, navigation",
    }


def check_kuta(chart):
    """
    Kuta Yoga: All 7 planets in H4 through H10.
    Result: Liar, jailer, dwells in forts.
    """
    occ = _occupied_houses(chart)
    formed = occ.issubset(set(range(4, 11)))
    return {
        "name": "Kuta Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "All planets in H4-H10 — fort-dweller",
    }


def check_chhatra(chart):
    """
    Chhatra Yoga: All 7 planets in H7 through H1 (upper hemisphere).
    Result: Helps relatives, protects others.
    """
    upper = {7, 8, 9, 10, 11, 12, 1}
    occ = _occupied_houses(chart)
    formed = occ.issubset(upper)
    return {
        "name": "Chhatra Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "All planets in upper hemisphere — protects others",
    }


def check_chapa(chart):
    """
    Chapa (Dhanush) Yoga: All 7 planets in H10 through H4.
    Result: Brave, truthful, happy beginning/end.
    """
    houses = {10, 11, 12, 1, 2, 3, 4}
    occ = _occupied_houses(chart)
    formed = occ.issubset(houses)
    return {
        "name": "Chapa Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "description": "All planets H10-H4 — brave, truthful",
    }


def check_ardha_chandra(chart):
    """
    Ardha Chandra Yoga: All 7 planets in 7 consecutive houses.
    Result: Handsome, brave, leader.
    """
    occ = sorted(_occupied_houses(chart))
    if not occ:
        return {"name": "Ardha Chandra Yoga (Nabhasa-Akriti)", "formed": False, "category": "Akriti"}
    for start in range(1, 13):
        block = {((start - 1 + i) % 12) + 1 for i in range(7)}
        if set(occ).issubset(block) and len(occ) == 7:
            return {
                "name": "Ardha Chandra Yoga (Nabhasa-Akriti)",
                "formed": True, "category": "Akriti",
                "start_house": start,
                "description": f"All 7 planets in 7 consecutive houses from H{start}",
            }
    return {"name": "Ardha Chandra Yoga (Nabhasa-Akriti)", "formed": False, "category": "Akriti"}


def check_chakra(chart):
    """
    Chakra Yoga: Planets fill 6 ODD houses (1,3,5,7,9,11).
    Result: King or emperor.
    """
    odd = {1, 3, 5, 7, 9, 11}
    occ = _occupied_houses(chart)
    formed = occ.issubset(odd) and len(occ & odd) >= 4
    return {
        "name": "Chakra Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "odd_houses_filled": len(occ & odd),
        "description": "Planets in odd houses — king/emperor pattern",
    }


def check_samudra(chart):
    """
    Samudra Yoga: Planets fill 6 EVEN houses (2,4,6,8,10,12).
    Result: Equal to a king, many pleasures.
    """
    even = {2, 4, 6, 8, 10, 12}
    occ = _occupied_houses(chart)
    formed = occ.issubset(even) and len(occ & even) >= 4
    return {
        "name": "Samudra Yoga (Nabhasa-Akriti)",
        "formed": formed, "category": "Akriti",
        "even_houses_filled": len(occ & even),
        "description": "Planets in even houses — king-like, many pleasures",
    }


# ═══════════════════════════════════════════
# SANKHYA YOGAS (7) — Count of Signs Occupied
# ═══════════════════════════════════════════

def _count_occupied_signs(chart):
    """Count how many distinct signs are occupied by the 7 planets."""
    signs = set()
    for p in PLANETS_7:
        si = _sign_idx_of(chart, p)
        signs.add(si)
    return len(signs)


def check_sankhya_yogas(chart):
    """
    7 Sankhya Yogas based on how many signs the 7 planets occupy.
    
    1 sign  = Gola     (all conjunct) — poor, unhappy
    2 signs = Yuga     — heretic, poor
    3 signs = Shoola   — sharp, cruel, lazy
    4 signs = Kedara   — farmer, charitable
    5 signs = Paasha   — skilled, large family
    6 signs = Daama    — liberal, wealthy
    7 signs = Veena/Vallaki — fond of music, happy
    """
    count = _count_occupied_signs(chart)
    names = {
        1: ("Gola", "All 7 planets in 1 sign — extreme concentration"),
        2: ("Yuga", "7 planets in 2 signs — heretic tendencies"),
        3: ("Shoola", "7 planets in 3 signs — sharp, cruel"),
        4: ("Kedara", "7 planets in 4 signs — farmer, charitable"),
        5: ("Paasha", "7 planets in 5 signs — skilled artisan"),
        6: ("Daama", "7 planets in 6 signs — liberal, wealthy"),
        7: ("Veena (Vallaki)", "7 planets in 7 signs — musical, happy"),
    }
    results = []
    for n, (name, desc) in names.items():
        formed = count == n
        results.append({
            "name": f"{name} Yoga (Nabhasa-Sankhya)",
            "formed": formed,
            "category": "Sankhya",
            "signs_occupied": count,
            "description": desc if formed else "",
        })
    return results


# ═══════════════════════════════════════════
# MASTER SCANNER
# ═══════════════════════════════════════════

def check_all_nabhasa_yogas(chart):
    """
    Run all 32 Nabhasa yoga checks.
    
    Returns:
        list of yoga result dicts
    """
    results = []

    # Ashraya (3)
    results.append(check_rajju(chart))
    results.append(check_musala(chart))
    results.append(check_nale(chart))

    # Dala (2)
    results.append(check_maala(chart))
    results.append(check_sarpa(chart))

    # Akriti (20)
    results.append(check_gada(chart))
    results.append(check_shakata(chart))
    results.append(check_shringataka(chart))
    results.append(check_hala(chart))
    results.append(check_vajra(chart))
    results.append(check_yava(chart))
    results.append(check_kamala(chart))
    results.append(check_vapi(chart))
    results.append(check_yupa(chart))
    results.append(check_ishu(chart))
    results.append(check_shakti(chart))
    results.append(check_danda(chart))
    results.append(check_nauka(chart))
    results.append(check_kuta(chart))
    results.append(check_chhatra(chart))
    results.append(check_chapa(chart))
    results.append(check_ardha_chandra(chart))
    results.append(check_chakra(chart))
    results.append(check_samudra(chart))

    # Sankhya (7)
    results.extend(check_sankhya_yogas(chart))

    return results


# Alias for the Nala function (typo-safe)
check_nale = check_nala
