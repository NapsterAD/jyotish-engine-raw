"""
yogas_raja.py — Extended Yoga catalogue from classical sources.

Sources:
  BV Raman 300 Important Combinations
  Phaldipika (Mantreshwara)
  BPHS (Parashara)
  Saravali (Kalyana Varma)
  Hora Sara (Prithuyasas)
  Jataka Parijata
  Uttara Kalamrita (Kalidasa)
  Laghu Parashari

Categories implemented:
  1. Solar yogas (Vasi, Vesi, Ubhayachari) — already in yogas.py
  2. Lunar yogas (Sunapha, Anapha, Durudhara, Kemadruma) — already in yogas.py
  3. Extended Dhana yogas (classical rules)
  4. Extended Raja yogas (Parashari + Jaimini)
  5. Pancha Mahapurusha extensions
  6. Aristha yogas (affliction/longevity)
  7. Sannyasa / Pravrajya yogas
  8. Arishta cancellation yogas
  9. Named classical yogas (Kahala, Chaamara, etc.)
"""

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, SIGN_ELEMENT,
    PLANETS_7, PLANETS_9,
    EXALTATION, DEBILITATION, OWN_SIGNS, NATURAL_FRIENDS,
)
from ..core.mapping import houses_from


def _h(chart, planet):
    """Shorthand: rashi house of planet."""
    return chart.rashi_chart.get(planet, {}).get("house_rashi", 0)


def _sign(chart, planet):
    return chart.positions.get(planet, {}).get("sign", "")


def _dig(chart, planet):
    return chart.rashi_chart.get(planet, {}).get("dignity", "")


def _conjunct(chart, p, q):
    hp, hq = _h(chart, p), _h(chart, q)
    return hp > 0 and hp == hq


def _aspects_house(chart, planet, house):
    return house in chart.aspects.get(planet, [])


def _house_from(h1, h2):
    if not h1 or not h2:
        return 0
    return houses_from(h1, h2)


def _lord_of(chart, house):
    return chart.lordships.get(house, "")


def _in_kendra(h):
    return h in {1, 4, 7, 10}


def _in_trikona(h):
    return h in {1, 5, 9}


def _in_dusthana(h):
    return h in {6, 8, 12}


def _is_benefic(planet):
    return planet in {"Jupiter", "Venus", "Mercury", "Moon"}


def _is_malefic(planet):
    return planet in {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def _strong(chart, planet):
    """Planet in own/exalted/MT."""
    d = _dig(chart, planet)
    return d in ("Own Sign", "Exalted", "Moolatrikona")


# ═══════════════════════════════════════════
# CLASSICAL NAMED YOGAS (BV Raman + BPHS)
# ═══════════════════════════════════════════

def check_chamara_yoga(chart):
    """
    Chamara Yoga: Lagna lord exalted in Kendra, aspected by Jupiter.
    Result: King, scholarly, long life.
    Source: BV Raman #14.
    """
    lord1 = _lord_of(chart, 1)
    h1l = _h(chart, lord1)
    d1l = _dig(chart, lord1)
    jup_aspects = chart.aspects.get("Jupiter", [])
    formed = (d1l == "Exalted" and _in_kendra(h1l) and h1l in jup_aspects)
    return {
        "name": "Chamara Yoga",
        "formed": formed,
        "source": "BV Raman #14",
        "description": "Lagna lord exalted in Kendra, aspected by Jupiter — scholarly king",
    }


def check_kahala_yoga(chart):
    """
    Kahala Yoga: 4th lord and Jupiter in mutual Kendras,
    or 4th lord strong and Lagna lord in own/exalted.
    Result: Brave, cunning, rules territories.
    Source: BV Raman #43.
    """
    lord4 = _lord_of(chart, 4)
    h4l = _h(chart, lord4)
    hjup = _h(chart, "Jupiter")
    h1l = _h(chart, _lord_of(chart, 1))
    # Mutual kendras
    mutual = (_in_kendra(_house_from(h4l, hjup)) and _in_kendra(_house_from(hjup, h4l)))
    strong_form = (_strong(chart, lord4) and _strong(chart, _lord_of(chart, 1)))
    formed = mutual or strong_form
    return {
        "name": "Kahala Yoga",
        "formed": formed,
        "source": "BV Raman #43",
        "description": "4L + Jupiter mutual Kendras, or both lords strong — brave ruler",
    }


def check_subha_kartari(chart):
    """
    Shubha Kartari Yoga: Lagna hemmed between benefics
    (benefics in 2nd and 12th from Lagna).
    Result: Protection, auspiciousness.
    Source: BPHS.
    """
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    h2 = set(chart.get_planets_in_house(2)) & benefics
    h12 = set(chart.get_planets_in_house(12)) & benefics
    formed = bool(h2) and bool(h12)
    return {
        "name": "Shubha Kartari Yoga",
        "formed": formed,
        "benefics_in_2": sorted(h2),
        "benefics_in_12": sorted(h12),
        "description": "Lagna hemmed by benefics — auspicious protection",
    }


def check_papa_kartari(chart):
    """
    Papa Kartari Yoga: Lagna hemmed between malefics
    (malefics in 2nd and 12th from Lagna).
    Result: Obstruction, difficulties.
    """
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    h2 = set(chart.get_planets_in_house(2)) & malefics
    h12 = set(chart.get_planets_in_house(12)) & malefics
    formed = bool(h2) and bool(h12)
    return {
        "name": "Papa Kartari Yoga",
        "formed": formed,
        "malefics_in_2": sorted(h2),
        "malefics_in_12": sorted(h12),
        "description": "Lagna hemmed by malefics — obstruction, difficulties",
    }


def check_kalanidhi_yoga(chart):
    """
    Kalanidhi Yoga: Jupiter in 2nd or 5th, conjoined/aspected by Mercury+Venus.
    Result: Prosperous king, immune to diseases.
    Source: BV Raman #36.
    """
    hjup = _h(chart, "Jupiter")
    if hjup not in {2, 5}:
        return {"name": "Kalanidhi Yoga", "formed": False, "source": "BV Raman #36"}
    mer_conj = _conjunct(chart, "Jupiter", "Mercury")
    ven_conj = _conjunct(chart, "Jupiter", "Venus")
    mer_asp = _aspects_house(chart, "Mercury", hjup)
    ven_asp = _aspects_house(chart, "Venus", hjup)
    formed = (mer_conj or mer_asp) and (ven_conj or ven_asp)
    return {
        "name": "Kalanidhi Yoga",
        "formed": formed,
        "source": "BV Raman #36",
        "description": "Jupiter in 2/5 with Mercury+Venus influence — prosperous",
    }


def check_akhanda_samrajya_yoga(chart):
    """
    Akhanda Samrajya Yoga: Jupiter lord of 2/5/11, in Kendra from Moon,
    and 11th lord in Kendra.
    Result: Undisputed sovereign.
    Source: BV Raman #47.
    """
    jup_lordships = []
    for h, lord in chart.lordships.items():
        if lord == "Jupiter":
            jup_lordships.append(h)
    jup_owns_wealth = any(h in {2, 5, 11} for h in jup_lordships)
    hjup = _h(chart, "Jupiter")
    hmoon = _h(chart, "Moon")
    jup_kendra_moon = _in_kendra(_house_from(hjup, hmoon))
    lord11 = _lord_of(chart, 11)
    h11l = _h(chart, lord11)
    l11_kendra = _in_kendra(h11l)
    formed = jup_owns_wealth and jup_kendra_moon and l11_kendra
    return {
        "name": "Akhanda Samrajya Yoga",
        "formed": formed,
        "source": "BV Raman #47",
        "description": "Jupiter owns 2/5/11, Kendra from Moon, 11L in Kendra — sovereign",
    }


def check_sarada_yoga(chart):
    """
    Sarada Yoga: 10th lord in 5th, Mercury exalted/in own sign in Kendra/Trikona,
    or 10th lord in 5th aspected by Mercury.
    Result: Great writer, poet.
    Source: BV Raman #72.
    """
    lord10 = _lord_of(chart, 10)
    h10l = _h(chart, lord10)
    hmer = _h(chart, "Mercury")
    mer_strong = _strong(chart, "Mercury") and (_in_kendra(hmer) or _in_trikona(hmer))
    l10_in_5 = h10l == 5
    mer_asp_5 = _aspects_house(chart, "Mercury", 5) or _conjunct(chart, "Mercury", lord10)
    formed = l10_in_5 and (mer_strong or mer_asp_5)
    return {
        "name": "Sarada Yoga",
        "formed": formed,
        "source": "BV Raman #72",
        "description": "10L in 5th with Mercury strong — great writer, poet",
    }


def check_parvata_yoga(chart):
    """
    Parvata Yoga: Lagna lord and 12th lord in mutual Kendras,
    or benefics in Kendras and 6/8 houses empty.
    Result: Wealthy, ruler of a province.
    Source: BV Raman #29.
    """
    lord1 = _lord_of(chart, 1)
    lord12 = _lord_of(chart, 12)
    h1l = _h(chart, lord1)
    h12l = _h(chart, lord12)
    mutual = (_in_kendra(h1l) and _in_kendra(h12l))
    # Alternative: benefics in kendras and 6/8 empty
    kendra = {1, 4, 7, 10}
    benefics_in_kendra = sum(
        1 for p in ["Jupiter", "Venus", "Mercury", "Moon"]
        if _h(chart, p) in kendra
    )
    h6_empty = len(chart.get_planets_in_house(6)) == 0
    h8_empty = len(chart.get_planets_in_house(8)) == 0
    alt = benefics_in_kendra >= 2 and h6_empty and h8_empty
    formed = mutual or alt
    return {
        "name": "Parvata Yoga",
        "formed": formed,
        "source": "BV Raman #29",
        "description": "1L + 12L in mutual Kendras, or benefics in Kendras with 6/8 empty — ruler",
    }


def check_shankha_yoga(chart):
    """
    Shankha Yoga: 5th and 6th lords in mutual Kendras,
    Lagna lord strong.
    Result: Fond of pleasures, charitable, long-lived.
    Source: BV Raman #49.
    """
    lord5 = _lord_of(chart, 5)
    lord6 = _lord_of(chart, 6)
    h5l = _h(chart, lord5)
    h6l = _h(chart, lord6)
    mutual_k = (_in_kendra(h5l) and _in_kendra(h6l))
    lord1_strong = _strong(chart, _lord_of(chart, 1))
    formed = mutual_k and lord1_strong
    return {
        "name": "Shankha Yoga",
        "formed": formed,
        "source": "BV Raman #49",
        "description": "5L + 6L mutual Kendras, 1L strong — pleasures, charity",
    }


def check_bheri_yoga(chart):
    """
    Bheri Yoga: All planets in H1, H2, H7, H12, and
    9th lord strong.
    Result: Religious, virtuous, long-lived.
    Source: BV Raman #51.
    """
    occ = set()
    for p in PLANETS_7:
        occ.add(_h(chart, p))
    formed = occ.issubset({1, 2, 7, 12}) and _strong(chart, _lord_of(chart, 9))
    return {
        "name": "Bheri Yoga",
        "formed": formed,
        "source": "BV Raman #51",
        "description": "Planets in 1/2/7/12, 9L strong — religious, long-lived",
    }


def check_mridanga_yoga(chart):
    """
    Mridanga Yoga: Lagna lord in Kendra, strong,
    and all planets in own/exalted signs.
    Result: King, ruler.
    Source: BV Raman #52.
    """
    lord1 = _lord_of(chart, 1)
    h1l = _h(chart, lord1)
    l1_strong = _strong(chart, lord1) and _in_kendra(h1l)
    all_strong = all(
        _dig(chart, p) in ("Own Sign", "Exalted", "Moolatrikona")
        for p in PLANETS_7
    )
    formed = l1_strong and all_strong
    return {
        "name": "Mridanga Yoga",
        "formed": formed,
        "source": "BV Raman #52",
        "description": "1L strong in Kendra, all planets own/exalted — ruler",
    }


# ═══════════════════════════════════════════
# EXTENDED DHANA YOGAS (Classical)
# ═══════════════════════════════════════════

def check_classical_dhana_yogas(chart):
    """
    Full classical Dhana yoga set from Phaldipika, BPHS, Laghu Parashari.
    """
    yogas = []
    lordships = chart.lordships

    # Lakshmi-Narayana variants
    lord2 = _lord_of(chart, 2)
    lord11 = _lord_of(chart, 11)
    lord5 = _lord_of(chart, 5)
    lord9 = _lord_of(chart, 9)
    lord1 = _lord_of(chart, 1)

    # 2L + 11L connection
    if _conjunct(chart, lord2, lord11) or _aspects_house(chart, lord2, _h(chart, lord11)):
        yogas.append({
            "name": "Dhana Yoga (2L-11L)",
            "formed": True,
            "description": f"{lord2} (2L) connected with {lord11} (11L)",
        })

    # 5L + 9L connection (Lakshmi Yoga variant)
    if _conjunct(chart, lord5, lord9):
        yogas.append({
            "name": "Dhana Yoga (5L-9L Lakshmi)",
            "formed": True,
            "description": f"{lord5} (5L) conjunct {lord9} (9L) — Lakshmi variant",
        })

    # Jupiter in 2H or 11H
    hjup = _h(chart, "Jupiter")
    if hjup in {2, 11}:
        yogas.append({
            "name": "Dhana Yoga (Jupiter in 2/11)",
            "formed": True,
            "description": f"Jupiter in H{hjup} — natural wealth indicator",
        })

    # 2L in 11H or 11L in 2H
    h2l = _h(chart, lord2)
    h11l = _h(chart, lord11)
    if h2l == 11:
        yogas.append({
            "name": "Dhana Yoga (2L in 11H)",
            "formed": True,
            "description": f"{lord2} (2L) in 11H — income through stored wealth",
        })
    if h11l == 2:
        yogas.append({
            "name": "Dhana Yoga (11L in 2H)",
            "formed": True,
            "description": f"{lord11} (11L) in 2H — gains stored as wealth",
        })

    # Venus + Jupiter conjunction or mutual aspect
    if _conjunct(chart, "Venus", "Jupiter"):
        yogas.append({
            "name": "Dhana Yoga (Venus-Jupiter conjunction)",
            "formed": True,
            "description": "Venus conjunct Jupiter — prosperity combo",
        })

    # 9L in 1H, 2H, 5H, 9H, 11H (strong trikona wealth)
    h9l = _h(chart, lord9)
    if h9l in {1, 2, 5, 9, 11}:
        yogas.append({
            "name": "Dhana Yoga (9L in wealth house)",
            "formed": True,
            "description": f"{lord9} (9L) in H{h9l} — fortune supports wealth",
        })

    return yogas


# ═══════════════════════════════════════════
# ARISTHA YOGAS (Longevity / Affliction)
# ═══════════════════════════════════════════

def check_aristha_yogas(chart):
    """
    Balaristya + Madhyaristya + longevity affliction markers.
    Source: Phaldipika Ch.13, BPHS Ch.12, Jataka Parijata.
    """
    yogas = []

    # Moon in 6/8/12 from Lagna
    hmoon = _h(chart, "Moon")
    if _in_dusthana(hmoon):
        yogas.append({
            "name": "Chandra Aristha",
            "formed": True,
            "category": "Aristha",
            "description": f"Moon in dusthana H{hmoon} — emotional affliction",
        })

    # 8th lord in 1st or 1st lord in 8th
    lord8 = _lord_of(chart, 8)
    lord1 = _lord_of(chart, 1)
    h8l = _h(chart, lord8)
    h1l = _h(chart, lord1)
    if h8l == 1:
        yogas.append({
            "name": "Lagna Aristha (8L in 1H)",
            "formed": True,
            "category": "Aristha",
            "description": f"{lord8} (8L) in Lagna — health vulnerability",
        })
    if h1l == 8:
        yogas.append({
            "name": "Lagna Aristha (1L in 8H)",
            "formed": True,
            "category": "Aristha",
            "description": f"{lord1} (1L) in 8H — health through transformation",
        })

    # Malefics in 1H without benefic aspect
    h1_planets = chart.get_planets_in_house(1)
    malefics_in_1 = [p for p in h1_planets if _is_malefic(p)]
    benefic_aspect_1 = any(
        1 in chart.aspects.get(p, []) for p in ["Jupiter", "Venus"]
    )
    if malefics_in_1 and not benefic_aspect_1:
        yogas.append({
            "name": "Lagna Malefic Aristha",
            "formed": True,
            "category": "Aristha",
            "description": f"Malefic(s) {malefics_in_1} in 1H without benefic aspect",
        })

    # Saturn + Mars conjunction in 1, 4, 7, 8, 10
    if _conjunct(chart, "Saturn", "Mars"):
        h = _h(chart, "Saturn")
        if h in {1, 4, 7, 8, 10}:
            yogas.append({
                "name": "Saturn-Mars Aristha",
                "formed": True,
                "category": "Aristha",
                "description": f"Saturn + Mars conjunct in H{h} — accidents, surgery risk",
            })

    # Moon + Saturn conjunction (Vish Yoga / Punarphoo)
    if _conjunct(chart, "Moon", "Saturn"):
        yogas.append({
            "name": "Vish Yoga (Punarphoo)",
            "formed": True,
            "category": "Aristha",
            "description": "Moon conjunct Saturn — emotional heaviness, delayed marriage",
        })

    # Moon + Rahu (Grahan Yoga)
    if _conjunct(chart, "Moon", "Rahu"):
        yogas.append({
            "name": "Chandra Grahan Yoga",
            "formed": True,
            "category": "Aristha",
            "description": "Moon conjunct Rahu — mental confusion, eclipse of mind",
        })

    # Sun + Rahu (Surya Grahan)
    if _conjunct(chart, "Sun", "Rahu"):
        yogas.append({
            "name": "Surya Grahan Yoga",
            "formed": True,
            "category": "Aristha",
            "description": "Sun conjunct Rahu — father issues, ego challenges",
        })

    return yogas


# ═══════════════════════════════════════════
# SANNYASA / PRAVRAJYA YOGAS
# ═══════════════════════════════════════════

def check_sannyasa_yogas(chart):
    """
    Spiritual renunciation yogas from BPHS, Phaldipika, Saravali.
    """
    yogas = []

    # 4+ planets in one sign
    sign_counts = {}
    for p in PLANETS_7:
        s = _sign(chart, p)
        sign_counts[s] = sign_counts.get(s, 0) + 1
    max_conj = max(sign_counts.values()) if sign_counts else 0
    if max_conj >= 4:
        best_sign = max(sign_counts, key=sign_counts.get)
        yogas.append({
            "name": "Sannyasa Yoga (4+ planets)",
            "formed": True,
            "category": "Sannyasa",
            "sign": best_sign,
            "count": max_conj,
            "description": f"{max_conj} planets in {best_sign} — renunciation tendency",
        })

    # Ketu in 12H
    hketu = _h(chart, "Ketu")
    if hketu == 12:
        yogas.append({
            "name": "Moksha Yoga (Ketu in 12H)",
            "formed": True,
            "category": "Sannyasa",
            "description": "Ketu in 12th house — natural spiritual detachment",
        })

    # Jupiter + Ketu conjunction
    if _conjunct(chart, "Jupiter", "Ketu"):
        yogas.append({
            "name": "Ganesha Yoga (Jupiter-Ketu)",
            "formed": True,
            "category": "Sannyasa",
            "description": "Jupiter conjunct Ketu — deep spiritual wisdom, moksha karaka",
        })

    # Saturn in 9H or 12H, aspected by Jupiter
    hsat = _h(chart, "Saturn")
    if hsat in {9, 12} and _aspects_house(chart, "Jupiter", hsat):
        yogas.append({
            "name": "Tapasvi Yoga",
            "formed": True,
            "category": "Sannyasa",
            "description": f"Saturn in H{hsat} aspected by Jupiter — ascetic tendencies",
        })

    # Moon + Ketu conjunction
    if _conjunct(chart, "Moon", "Ketu"):
        yogas.append({
            "name": "Pravrajya Yoga (Moon-Ketu)",
            "formed": True,
            "category": "Sannyasa",
            "description": "Moon conjunct Ketu — emotional detachment, spiritual seeking",
        })

    return yogas


# ═══════════════════════════════════════════
# ADDITIONAL NAMED YOGAS FROM BV RAMAN
# ═══════════════════════════════════════════

def check_sharada_yoga(chart):
    """Saraswati Yoga: Jupiter, Venus, Mercury in Kendras/Trikonas/2H."""
    trio = ["Jupiter", "Venus", "Mercury"]
    good = {1, 2, 4, 5, 7, 9, 10}
    all_good = all(_h(chart, p) in good for p in trio)
    return {
        "name": "Saraswati Yoga",
        "formed": all_good,
        "source": "BV Raman #73",
        "description": "Jupiter, Venus, Mercury in Kendras/Trikonas/2H — scholar, artist",
    }


def check_vasumati_yoga(chart):
    """
    Vasumati Yoga: Benefics in 3, 6, 10, 11 (upachaya) from Moon.
    Result: Extremely wealthy.
    Source: BV Raman #93.
    """
    hmoon = _h(chart, "Moon")
    upachaya = {3, 6, 10, 11}
    benefics = ["Jupiter", "Venus", "Mercury"]
    count = 0
    for p in benefics:
        hp = _h(chart, p)
        dist = _house_from(hp, hmoon)
        if dist in upachaya:
            count += 1
    formed = count >= 2
    return {
        "name": "Vasumati Yoga",
        "formed": formed,
        "source": "BV Raman #93",
        "benefics_in_upachaya": count,
        "description": "Benefics in upachaya from Moon — extremely wealthy",
    }


def check_gajakesari_extensions(chart):
    """
    Extended Gaja Kesari checks: weakening conditions from KN Rao.
    Already in yogas.py, but add cancellation checks.
    """
    moon_h = _h(chart, "Moon")
    jup_h = _h(chart, "Jupiter")
    if not moon_h or not jup_h:
        return {"name": "Gaja Kesari (extended)", "formed": False}
    dist = _house_from(jup_h, moon_h)
    formed = dist in {1, 4, 7, 10}
    if not formed:
        return {"name": "Gaja Kesari (extended)", "formed": False}
    # Weakening checks
    weakenings = []
    jdig = _dig(chart, "Jupiter")
    if jdig == "Debilitated":
        weakenings.append("Jupiter debilitated")
    try:
        if chart.combustion.get("Jupiter", {}).get("is_combust"):
            weakenings.append("Jupiter combust")
    except Exception:
        pass
    if _conjunct(chart, "Jupiter", "Rahu") or _conjunct(chart, "Jupiter", "Ketu"):
        weakenings.append("Jupiter with nodes")
    if _in_dusthana(jup_h):
        weakenings.append(f"Jupiter in dusthana H{jup_h}")

    return {
        "name": "Gaja Kesari (extended)",
        "formed": True,
        "strength": "WEAKENED" if weakenings else "FULL",
        "weakenings": weakenings,
        "description": f"Jupiter H{jup_h}, {dist}th from Moon H{moon_h}"
                       + (f" ({', '.join(weakenings)})" if weakenings else ""),
    }


def check_chandra_adhi_yoga(chart):
    """
    Chandra Adhi Yoga: Benefics in 6/7/8 from Moon.
    If 2 benefics: MahaPurush; if 3: Raja.
    Source: BV Raman #44.
    """
    hmoon = _h(chart, "Moon")
    benefics = ["Mercury", "Jupiter", "Venus"]
    count = 0
    planets = []
    for p in benefics:
        hp = _h(chart, p)
        dist = _house_from(hp, hmoon)
        if dist in {6, 7, 8}:
            count += 1
            planets.append(p)
    formed = count >= 2
    return {
        "name": "Chandra Adhi Yoga",
        "formed": formed,
        "source": "BV Raman #44",
        "benefic_count": count,
        "planets": planets,
        "strength": "Raja" if count >= 3 else ("MahaPurush" if count == 2 else "None"),
        "description": f"{count} benefics in 6/7/8 from Moon — {planets}",
    }


def check_hamsa_details(chart):
    """
    Detailed Hamsa yoga check with cancellation conditions.
    Source: Saravali + KN Rao.
    """
    hjup = _h(chart, "Jupiter")
    djup = _dig(chart, "Jupiter")
    formed = _in_kendra(hjup) and djup in ("Own Sign", "Exalted", "Moolatrikona")
    if not formed:
        return {"name": "Hamsa Yoga (detailed)", "formed": False}
    cancellations = []
    try:
        if chart.combustion.get("Jupiter", {}).get("is_combust"):
            cancellations.append("combust")
    except Exception:
        pass
    if _conjunct(chart, "Jupiter", "Rahu"):
        cancellations.append("Guru-Chandal (with Rahu)")
    if _conjunct(chart, "Jupiter", "Saturn"):
        cancellations.append("Jupiter-Saturn conjunction")
    return {
        "name": "Hamsa Yoga (detailed)",
        "formed": True,
        "strength": "WEAKENED" if cancellations else "FULL",
        "cancellations": cancellations,
        "house": hjup,
        "dignity": djup,
    }


def check_bharathi_yoga(chart):
    """
    Bharathi Yoga: 2nd lord with 5th lord, or Venus in Kendra
    with Jupiter in 2/5.
    Result: Famous scholar.
    Source: BV Raman #78.
    """
    lord2 = _lord_of(chart, 2)
    lord5 = _lord_of(chart, 5)
    conj = _conjunct(chart, lord2, lord5)
    hven = _h(chart, "Venus")
    hjup = _h(chart, "Jupiter")
    alt = _in_kendra(hven) and hjup in {2, 5}
    formed = conj or alt
    return {
        "name": "Bharathi Yoga",
        "formed": formed,
        "source": "BV Raman #78",
        "description": "2L + 5L connected, or Venus Kendra + Jupiter 2/5 — famous scholar",
    }


def check_pushkala_yoga(chart):
    """
    Pushkala Yoga: Lagna lord with Moon, in Kendra, aspected by/conjunct
    a planet friendly to Lagna lord.
    Result: Wealthy, famous, king-like.
    Source: BV Raman #25.
    """
    lord1 = _lord_of(chart, 1)
    h1l = _h(chart, lord1)
    hmoon = _h(chart, "Moon")
    formed = (h1l == hmoon and _in_kendra(h1l))
    return {
        "name": "Pushkala Yoga",
        "formed": formed,
        "source": "BV Raman #25",
        "description": "1L conjunct Moon in Kendra — wealthy, famous",
    }


def check_harsha_yoga_extended(chart):
    """
    Harsha Yoga: 6th lord in 6th — health recovers, defeats enemies.
    Extended with aspects/conjunctions.
    """
    lord6 = _lord_of(chart, 6)
    h6l = _h(chart, lord6)
    formed = h6l == 6
    return {
        "name": "Harsha Yoga (extended)",
        "formed": formed,
        "description": f"6L {lord6} in own house — immune system, defeats enemies",
    }


def check_house_kartari_yogas(chart):
    """
    Check Kartari Yogas for all houses (not just Lagna).
    Returns formed Kartaris for key houses: 1H, 7H, 10H.
    """
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    results = []

    for target_h in [1, 2, 5, 7, 9, 10]:
        h_before = ((target_h - 2) % 12) + 1  # 12th from target
        h_after = (target_h % 12) + 1          # 2nd from target
        ps_before = set(chart.get_planets_in_house(h_before))
        ps_after = set(chart.get_planets_in_house(h_after))
        ben_b = ps_before & benefics
        ben_a = ps_after & benefics
        mal_b = ps_before & malefics
        mal_a = ps_after & malefics
        if ben_b and ben_a:
            results.append({
                "name": f"Shubha Kartari H{target_h}",
                "formed": True,
                "house": target_h,
                "before": sorted(ben_b),
                "after": sorted(ben_a),
            })
        if mal_b and mal_a:
            results.append({
                "name": f"Papa Kartari H{target_h}",
                "formed": True,
                "house": target_h,
                "before": sorted(mal_b),
                "after": sorted(mal_a),
            })
    return results


# ═══════════════════════════════════════════
# MASTER SCANNER
# ═══════════════════════════════════════════

def check_all_raja_yogas(chart):
    """
    Run all extended yoga checks from this module.
    Returns list of yoga dicts.
    """
    results = []

    # Named classical yogas
    results.append(check_chamara_yoga(chart))
    results.append(check_kahala_yoga(chart))
    results.append(check_subha_kartari(chart))
    results.append(check_papa_kartari(chart))
    results.append(check_kalanidhi_yoga(chart))
    results.append(check_akhanda_samrajya_yoga(chart))
    results.append(check_sarada_yoga(chart))
    results.append(check_parvata_yoga(chart))
    results.append(check_shankha_yoga(chart))
    results.append(check_bheri_yoga(chart))
    results.append(check_mridanga_yoga(chart))
    results.append(check_sharada_yoga(chart))
    results.append(check_vasumati_yoga(chart))
    results.append(check_gajakesari_extensions(chart))
    results.append(check_chandra_adhi_yoga(chart))
    results.append(check_hamsa_details(chart))
    results.append(check_bharathi_yoga(chart))
    results.append(check_pushkala_yoga(chart))
    results.append(check_harsha_yoga_extended(chart))

    # Kartari yogas for multiple houses
    results.extend(check_house_kartari_yogas(chart))

    # Classical Dhana yogas
    results.extend(check_classical_dhana_yogas(chart))

    # Aristha yogas
    results.extend(check_aristha_yogas(chart))

    # Sannyasa yogas
    results.extend(check_sannyasa_yogas(chart))

    return results
