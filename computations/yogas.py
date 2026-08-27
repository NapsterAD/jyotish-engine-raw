"""
yogas.py — Yoga detection: Pancha Mahapurusha, Viparita Raja, Dhana,
Raj Yogas, Kemadruma, Manglik, Kaal Sarp, and more.
100% offline — rule-based detection from chart data.
"""

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_7, PLANETS_9,
    EXALTATION, DEBILITATION, OWN_SIGNS, NATURAL_FRIENDS,
    SIGN_ELEMENT,
)
from ..core.mapping import houses_from


# ═══════════════════════════════════════════
# PANCHA MAHAPURUSHA YOGAS
# ═══════════════════════════════════════════

def check_pancha_mahapurusha(chart):
    """
    Check all 5 Pancha Mahapurusha Yogas.
    Formed when Mars/Mercury/Jupiter/Venus/Saturn is in:
      - Own sign or exalted sign
      - AND in a Kendra house (1, 4, 7, 10)
      
    Returns:
        list of formed yoga dicts
    """
    yogas = []
    kendra = {1, 4, 7, 10}

    yoga_names = {
        "Mars": "Ruchaka",
        "Mercury": "Bhadra",
        "Jupiter": "Hamsa",
        "Venus": "Malavya",
        "Saturn": "Sasa",
    }

    for planet, yoga_name in yoga_names.items():
        rc = chart.rashi_chart.get(planet, {})
        if not rc:
            continue

        house = rc.get("house_rashi", 0)
        dignity = rc.get("dignity", "")

        in_kendra = house in kendra
        in_own_or_exalted = dignity in ["Own Sign", "Exalted", "Moolatrikona"]

        if in_kendra and in_own_or_exalted:
            status = "FORMED"
            weaken = []
            try:
                comb = chart.combustion.get(planet, {})
                if comb.get("is_combust"):
                    status = "WEAKENED"
                    weaken.append("combust")
            except Exception:
                pass
            try:
                if planet in (chart.yuddha or {}).get("losers", []):
                    status = "WEAKENED"
                    weaken.append("yuddha_loser")
            except Exception:
                pass
            deg = chart.positions.get(planet, {}).get("degree_in_sign", 0)
            if deg > 29.0 or deg < 1.0:
                status = "WEAKENED"
                weaken.append("rashi_sandhi")
            for dust_h in (6, 8, 12):
                dl = chart.lordships.get(dust_h)
                if dl and dl in ("Saturn", "Mars", "Sun", "Rahu", "Ketu"):
                    if house in chart.aspects.get(dl, []):
                        status = "WEAKENED"
                        weaken.append(f"aspected_by_{dl}_dusthana")
            yogas.append({
                "name": f"{yoga_name} Yoga",
                "planet": planet,
                "house": house,
                "dignity": dignity,
                "formed": True,
                "status": status,
                "weakenings": weaken,
                "description": f"{planet} in {dignity} in Kendra H{house}"
                + (f" ({status}: {', '.join(weaken)})" if weaken else ""),
            })

    return yogas


def check_malavya(chart):
    """Check specifically for Malavya Yoga (Venus in own/exalted in Kendra)."""
    for y in check_pancha_mahapurusha(chart):
        if y["planet"] == "Venus":
            return y
    return {"name": "Malavya Yoga", "formed": False}


# ═══════════════════════════════════════════
# VIPARITA RAJA YOGA (VRY)
# ═══════════════════════════════════════════

def check_viparita_raja(chart):
    """
    Check Viparita Raja Yoga (VRY).
    Formed when dusthana lords (6L, 8L, 12L) are placed in dusthana houses (6, 8, 12).
    
    Three types:
    - Harsha: 6L in 6H, 8H, or 12H
    - Sarala: 8L in 6H, 8H, or 12H
    - Vimala: 12L in 6H, 8H, or 12H
    
    Returns:
        list of formed VRY dicts
    """
    yogas = []
    dusthana = {6, 8, 12}
    lordships = chart.lordships

    vry_types = {
        6: "Harsha",
        8: "Sarala",
        12: "Vimala",
    }

    for house, vry_name in vry_types.items():
        lord = lordships.get(house, "")
        if not lord:
            continue

        rc = chart.rashi_chart.get(lord, {})
        if not rc:
            continue

        placed_house = rc.get("house_rashi", 0)

        if placed_house in dusthana:
            yogas.append({
                "name": f"{vry_name} Viparita Raja Yoga",
                "lord": lord,
                "lord_of": f"{house}L",
                "placed_in": f"H{placed_house}",
                "formed": True,
                "description": f"{lord} ({house}L) in dusthana H{placed_house}",
            })

    return yogas


# ═══════════════════════════════════════════
# DHANA YOGAS (Wealth)
# ═══════════════════════════════════════════

def check_dhana_yogas(chart):
    """
    Check Dhana Yogas based on 1-2-5-9-11 framework.
    Lords of wealth houses connected with each other.
    
    Returns:
        list of dhana yoga dicts
    """
    yogas = []
    wealth_houses = [1, 2, 5, 9, 11]
    lordships = chart.lordships

    # Get placement of wealth house lords
    wealth_lords = {}
    for h in wealth_houses:
        lord = lordships.get(h, "")
        if lord:
            rc = chart.rashi_chart.get(lord, {})
            if rc:
                wealth_lords[h] = {
                    "lord": lord,
                    "placed_in": rc.get("house_rashi", 0)
                }

    # Check if any two wealth lords are conjunct (same house) or in mutual houses
    checked = set()
    for h1, info1 in wealth_lords.items():
        for h2, info2 in wealth_lords.items():
            if h1 >= h2:
                continue
            pair = (h1, h2)
            if pair in checked:
                continue
            checked.add(pair)

            # Conjunction
            if info1["placed_in"] == info2["placed_in"]:
                yogas.append({
                    "name": f"Dhana Yoga ({h1}L-{h2}L conjunction)",
                    "lords": [info1["lord"], info2["lord"]],
                    "house": info1["placed_in"],
                    "formed": True,
                    "description": f"{info1['lord']} ({h1}L) conjunct {info2['lord']} ({h2}L) in H{info1['placed_in']}",
                })

            # Exchange (parivartana)
            if info1["placed_in"] == h2 and info2["placed_in"] == h1:
                yogas.append({
                    "name": f"Dhana Yoga ({h1}L-{h2}L exchange)",
                    "lords": [info1["lord"], info2["lord"]],
                    "formed": True,
                    "description": f"{info1['lord']} ({h1}L) and {info2['lord']} ({h2}L) in mutual exchange",
                })

    return yogas


# ═══════════════════════════════════════════
# KALATRAMOOLADDHANA YOGA
# ═══════════════════════════════════════════

def check_kalatramooladdhana(chart):
    """
    Check Kalatramooladdhana Yoga — wealth through spouse.
    Formed when 7L is in 2H, 11H, or other wealth houses,
    or 2L/11L is in 7H.
    
    Returns:
        yoga dict
    """
    lordships = chart.lordships
    l7 = lordships.get(7, "")
    rc_7l = chart.rashi_chart.get(l7, {})
    h_7l = rc_7l.get("house_rashi", 0) if rc_7l else 0

    # 7L in 2H, 11H
    if h_7l in [2, 11]:
        return {
            "name": "Kalatramooladdhana Yoga",
            "formed": True,
            "description": f"7L {l7} in H{h_7l} — wealth through spouse/partnership",
        }

    return {"name": "Kalatramooladdhana Yoga", "formed": False}


# ═══════════════════════════════════════════
# GAJA KESARI YOGA
# ═══════════════════════════════════════════

def check_gaja_kesari(chart):
    """
    Check Gaja Kesari Yoga.
    Formed when Jupiter is in Kendra from Moon (1, 4, 7, 10 houses from Moon).
    
    Returns:
        yoga dict
    """
    moon_house = chart.rashi_chart.get("Moon", {}).get("house_rashi", 0)
    jup_house = chart.rashi_chart.get("Jupiter", {}).get("house_rashi", 0)

    if not moon_house or not jup_house:
        return {"name": "Gaja Kesari Yoga", "formed": False}

    distance = ((jup_house - moon_house) % 12) + 1
    # Kendra from Moon = 1, 4, 7, 10 houses distance
    if distance in [1, 4, 7, 10]:
        return {
            "name": "Gaja Kesari Yoga",
            "formed": True,
            "description": f"Jupiter (H{jup_house}) is {distance}th from Moon (H{moon_house})",
        }

    return {"name": "Gaja Kesari Yoga", "formed": False}


# ═══════════════════════════════════════════
# KEMADRUMA YOGA
# ═══════════════════════════════════════════

def check_kemadruma(chart):
    """
    Check Kemadruma Yoga on Moon.
    Formed when there are NO planets in 2nd and 12th from Moon.
    (Rahu/Ketu are excluded from this check.)
    
    Cancellation conditions:
    - Planet in Kendra from Lagna (some traditions)
    - Moon in Kendra
    
    Returns:
        yoga dict with cancellation info
    """
    moon_house = chart.rashi_chart.get("Moon", {}).get("house_rashi", 0)
    if not moon_house:
        return {"name": "Kemadruma Yoga", "formed": False}

    h2_from_moon = ((moon_house) % 12) + 1  # 2nd from Moon
    h12_from_moon = ((moon_house - 2) % 12) + 1  # 12th from Moon

    # Check for planets in 2nd and 12th from Moon (exclude Rahu, Ketu)
    check_planets = ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

    planets_in_2 = [p for p in check_planets
                    if chart.rashi_chart.get(p, {}).get("house_rashi") == h2_from_moon]
    planets_in_12 = [p for p in check_planets
                     if chart.rashi_chart.get(p, {}).get("house_rashi") == h12_from_moon]

    formed = len(planets_in_2) == 0 and len(planets_in_12) == 0

    # Check cancellation: planet in Kendra from Lagna
    cancellations = []
    kendra = {1, 4, 7, 10}
    for p in check_planets:
        h = chart.rashi_chart.get(p, {}).get("house_rashi", 0)
        if h in kendra:
            cancellations.append(f"{p} in Kendra H{h}")

    # Moon in Kendra cancels too
    if moon_house in kendra:
        cancellations.append(f"Moon itself in Kendra H{moon_house}")

    return {
        "name": "Kemadruma Yoga",
        "formed": formed,
        "moon_house": moon_house,
        "2nd_from_moon": f"H{h2_from_moon} — {', '.join(planets_in_2) if planets_in_2 else 'EMPTY'}",
        "12th_from_moon": f"H{h12_from_moon} — {', '.join(planets_in_12) if planets_in_12 else 'EMPTY'}",
        "cancellations": cancellations if formed else [],
        "effectively_cancelled": formed and len(cancellations) > 0,
    }


# ═══════════════════════════════════════════
# MANGLIK DOSHA (Kuja Dosha)
# ═══════════════════════════════════════════

def _house_of(chart, planet):
    return chart.rashi_chart.get(planet, {}).get("house_rashi", 0)


def _house_from(planet_house, ref_house):
    if not planet_house or not ref_house:
        return 0
    return houses_from(planet_house, ref_house)


def _sign_of(chart, planet):
    return chart.positions.get(planet, {}).get("sign", "")


def _same_sign(chart, a, b):
    sa = _sign_of(chart, a)
    sb = _sign_of(chart, b)
    return bool(sa) and sa == sb


def check_manglik(chart):
    """
    Manglik / Kuja Dosha from Lagna, Moon, and Venus with weighted score
    and 8 cancellation conditions. rules.md §17.
    """
    manglik_houses = {1, 2, 4, 7, 8, 12}
    mars_h = _house_of(chart, "Mars")
    moon_h = _house_of(chart, "Moon")
    venus_h = _house_of(chart, "Venus")

    from_lagna = mars_h in manglik_houses
    from_moon = _house_from(mars_h, moon_h) in manglik_houses if moon_h else False
    from_venus = _house_from(mars_h, venus_h) in manglik_houses if venus_h else False
    score = (2 if from_lagna else 0) + (1 if from_moon else 0) + (1 if from_venus else 0)

    mars_sign = _sign_of(chart, "Mars")
    jup_h = _house_of(chart, "Jupiter")
    lord7 = chart.lordships.get(7)
    lord7_h = _house_of(chart, lord7) if lord7 else 0
    moon_elong = (
        (chart.positions.get("Moon", {}).get("longitude", 0)
         - chart.positions.get("Sun", {}).get("longitude", 0)) % 360
    )
    shukla = moon_elong < 180.0

    cancellations = []
    if mars_sign in ("Aries", "Scorpio"):
        cancellations.append("Mars in own sign")
    if mars_sign == "Capricorn":
        cancellations.append("Mars exalted")
    if _same_sign(chart, "Mars", "Jupiter") or (
        jup_h and mars_h in chart.aspects.get("Jupiter", [])
    ):
        cancellations.append("Jupiter conjunct/aspects Mars")
    if _same_sign(chart, "Mars", "Moon") and shukla:
        cancellations.append("Waxing Moon conjunct Mars")
    if mars_sign in ("Leo", "Aquarius"):
        cancellations.append("Mars in Leo or Aquarius")
    if lord7_h in {1, 4, 5, 7, 9, 10}:
        cancellations.append("7th lord in Kendra/Trikona")
    if venus_h == 7:
        cancellations.append("Venus in 7th")
    sat_h = _house_of(chart, "Saturn")
    if sat_h in {1, 4, 7, 8, 12}:
        cancellations.append("Saturn in 1/4/7/8/12 (comparative cancel)")

    formed = score > 0
    cancelled = formed and len(cancellations) > 0
    return {
        "name": "Manglik Dosha (Kuja Dosha)",
        "formed": formed and not cancelled,
        "raw_formed": formed,
        "cancelled": cancelled,
        "score": score,
        "from_lagna": from_lagna,
        "from_moon": from_moon,
        "from_venus": from_venus,
        "mars_house": mars_h,
        "cancellations": cancellations,
        "description": (
            f"Mars H{mars_h} score={score}"
            + (f" cancelled by {cancellations}" if cancelled else
               (" — Manglik" if formed else " — NOT Manglik"))
        ),
    }


# ═══════════════════════════════════════════
# KAAL SARP YOGA
# ═══════════════════════════════════════════

def check_kaal_sarp(chart):
    """
    Check Kaal Sarp Yoga.
    Formed when ALL 7 planets are between Rahu and Ketu axis
    (hemmed between the nodes).
    
    Returns:
        yoga dict
    """
    rahu_long = chart.positions.get("Rahu", {}).get("longitude", 0)
    ketu_long = chart.positions.get("Ketu", {}).get("longitude", 0)

    # Planets between Rahu and Ketu (going forward from Rahu to Ketu)
    inside = []
    outside = []

    for planet in PLANETS_7:
        p_long = chart.positions.get(planet, {}).get("longitude", 0)

        # Check if planet is between Rahu and Ketu (shorter arc)
        if rahu_long < ketu_long:
            between = rahu_long < p_long < ketu_long
        else:
            between = p_long > rahu_long or p_long < ketu_long

        if between:
            inside.append(planet)
        else:
            outside.append(planet)

    formed = len(outside) == 0  # All 7 planets between nodes

    rahu_h = _house_of(chart, "Rahu")
    ketu_h = _house_of(chart, "Ketu")
    ksy_names = {
        1: "Ananta", 2: "Kulika", 3: "Vasuki", 4: "Shankhapala",
        5: "Padma", 6: "Mahapadma", 7: "Takshaka", 8: "Karkotaka",
        9: "Shankhachuda", 10: "Ghataka", 11: "Vishadhara", 12: "Sheshanaga",
    }
    ksy_type = ksy_names.get(rahu_h)

    # Kala Sarpa: planets sit on the arc from Rahu toward Ketu (forward).
    # Kala Amrita: planets sit on the arc from Ketu toward Rahu (toward Ketu).
    toward_rahu = []
    toward_ketu = []
    for planet in PLANETS_7:
        p_long = chart.positions.get(planet, {}).get("longitude", 0)
        d_to_rahu = (rahu_long - p_long) % 360.0
        d_to_ketu = (ketu_long - p_long) % 360.0
        if d_to_rahu <= d_to_ketu:
            toward_rahu.append(planet)
        else:
            toward_ketu.append(planet)
    flavour = None
    if formed:
        flavour = "Kala Sarpa" if len(toward_rahu) >= len(toward_ketu) else "Kala Amrita"

    return {
        "name": "Kaal Sarp Yoga" if flavour != "Kala Amrita" else "Kala Amrita Yoga",
        "formed": formed,
        "type": ksy_type if formed else None,
        "rahu_house": rahu_h,
        "ketu_house": ketu_h,
        "flavour": flavour,
        "inside": inside,
        "outside": outside,
        "toward_rahu": toward_rahu,
        "toward_ketu": toward_ketu,
        "description": (
            f"{flavour or 'Kaal Sarp'} {ksy_type or ''} "
            f"{'ALL' if formed else f'{len(inside)}/7'} planets between Rahu-Ketu"
        ).strip(),
    }


# ═══════════════════════════════════════════
# RAJ YOGAS (Kendra-Trikona connection)
# ═══════════════════════════════════════════

def check_raj_yogas(chart):
    """
    Check for Raj Yogas (Kendra-Trikona connections).
    A Raj Yoga is formed when a Kendra lord (1,4,7,10) and a
    Trikona lord (1,5,9) are connected by:
    - Conjunction
    - Mutual aspect
    - Exchange (parivartana)
    
    Returns:
        list of raj yoga dicts
    """
    yogas = []
    lordships = chart.lordships
    kendra_houses = {1, 4, 7, 10}
    trikona_houses = {1, 5, 9}

    # Build planet -> houses mapping
    planet_houses = {}
    for h, lord in lordships.items():
        planet_houses.setdefault(lord, []).append(h)

    # Find kendra lords and trikona lords
    kendra_lords = set()
    trikona_lords = set()
    for planet, houses in planet_houses.items():
        if any(h in kendra_houses for h in houses):
            kendra_lords.add(planet)
        if any(h in trikona_houses for h in houses):
            trikona_lords.add(planet)

    # Check connections between kendra and trikona lords
    for k_lord in kendra_lords:
        for t_lord in trikona_lords:
            if k_lord == t_lord:
                continue  # Same planet ruling both — implicit yoga

            k_house = chart.rashi_chart.get(k_lord, {}).get("house_rashi", 0)
            t_house = chart.rashi_chart.get(t_lord, {}).get("house_rashi", 0)

            connected = False
            connection_type = ""

            # Conjunction
            if k_house == t_house and k_house > 0:
                connected = True
                connection_type = f"Conjunction in H{k_house}"

            # Mutual aspect (via chart.aspects)
            if not connected:
                k_aspects = chart.aspects.get(k_lord, [])
                t_aspects = chart.aspects.get(t_lord, [])
                if t_house in k_aspects or k_house in t_aspects:
                    connected = True
                    connection_type = "Mutual aspect"

            if connected:
                k_houses_str = "+".join(f"{h}L" for h in sorted(planet_houses.get(k_lord, [])))
                t_houses_str = "+".join(f"{h}L" for h in sorted(planet_houses.get(t_lord, [])))
                yogas.append({
                    "name": "Raj Yoga",
                    "kendra_lord": f"{k_lord} ({k_houses_str})",
                    "trikona_lord": f"{t_lord} ({t_houses_str})",
                    "connection": connection_type,
                    "formed": True,
                })

    return yogas


# ═══════════════════════════════════════════
# SAKATA YOGA
# ═══════════════════════════════════════════

def check_sakata(chart):
    """
    Check Sakata Yoga — Moon in 6th, 8th, or 12th from Jupiter.
    Indicates fluctuating fortune.
    
    Returns:
        yoga dict
    """
    moon_h = chart.rashi_chart.get("Moon", {}).get("house_rashi", 0)
    jup_h = chart.rashi_chart.get("Jupiter", {}).get("house_rashi", 0)

    if not moon_h or not jup_h:
        return {"name": "Sakata Yoga", "formed": False}

    distance = ((moon_h - jup_h) % 12) + 1
    formed = distance in [6, 8, 12]

    return {
        "name": "Sakata Yoga",
        "formed": formed,
        "moon_house": moon_h,
        "jupiter_house": jup_h,
        "distance": distance,
    }


# ═══════════════════════════════════════════
# UBHAYACHARI YOGA
# ═══════════════════════════════════════════

def check_ubhayachari(chart):
    """
    Check Ubhayachari Yoga — planets on both sides of the Sun
    (in 2nd and 12th from Sun). Rahu/Ketu excluded.
    
    Vasi Yoga = planet in 12th from Sun only
    Vesi Yoga = planet in 2nd from Sun only
    Ubhayachari = both sides
    
    Returns:
        yoga dict
    """
    sun_house = chart.rashi_chart.get("Sun", {}).get("house_rashi", 0)
    if not sun_house:
        return {"name": "Ubhayachari Yoga", "formed": False}

    h2 = (sun_house % 12) + 1      # 2nd from Sun
    h12 = ((sun_house - 2) % 12) + 1  # 12th from Sun

    check = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

    in_2 = [p for p in check if chart.rashi_chart.get(p, {}).get("house_rashi") == h2]
    in_12 = [p for p in check if chart.rashi_chart.get(p, {}).get("house_rashi") == h12]

    if in_2 and in_12:
        yoga_type = "Ubhayachari"
    elif in_12:
        yoga_type = "Vasi"
    elif in_2:
        yoga_type = "Vesi"
    else:
        return {"name": "Ubhayachari Yoga", "formed": False}

    return {
        "name": f"{yoga_type} Yoga",
        "formed": True,
        "planets_before_sun": in_12,
        "planets_after_sun": in_2,
    }


# ═══════════════════════════════════════════
# NEECHA BHANGA RAJA YOGA
# ═══════════════════════════════════════════

def check_neecha_bhanga(chart):
    """8-condition Neecha Bhanga. rules.md §9.5."""
    kendra = {1, 4, 7, 10}
    moon_h = _house_of(chart, "Moon")
    results = []

    def in_kendra_lm(planet):
        h = _house_of(chart, planet)
        if h in kendra:
            return True
        if moon_h and _house_from(h, moon_h) in kendra:
            return True
        return False

    for planet in PLANETS_7:
        rc = chart.rashi_chart.get(planet, {})
        if rc.get("dignity") != "Debilitated":
            continue
        deb_sign = DEBILITATION[planet][0]
        exalt_sign = EXALTATION[planet][0]
        deb_lord = SIGN_LORDS[deb_sign]
        exalt_lord = SIGN_LORDS[exalt_sign]
        hits = []
        if in_kendra_lm(deb_lord):
            hits.append(1)
        if in_kendra_lm(exalt_lord):
            hits.append(2)
        if rc.get("house_rashi") in chart.aspects.get(deb_lord, []):
            hits.append(3)
        if _same_sign(chart, planet, exalt_lord):
            hits.append(4)
        for q in PLANETS_7:
            if q == planet:
                continue
            qd = chart.rashi_chart.get(q, {}).get("dignity")
            if qd == "Exalted" and _same_sign(chart, q, planet):
                hits.append(5)
                break
        # planet exalted in P's debilitation sign
        for q, (ex_sign, _) in EXALTATION.items():
            if q in PLANETS_7 and ex_sign == deb_sign and in_kendra_lm(q):
                hits.append(6)
                break
        if chart.positions.get(planet, {}).get("retrograde"):
            hits.append(7)
        # parivartana with the planet that owns this sign / is exalted here
        p_sign = _sign_of(chart, planet)
        other = SIGN_LORDS.get(p_sign)
        if other and other != planet:
            if SIGN_LORDS.get(_sign_of(chart, other)) == planet:
                if chart.rashi_chart.get(other, {}).get("dignity") == "Exalted":
                    hits.append(8)
        hits = sorted(set(hits))
        dusthana = rc.get("house_rashi") in {6, 8, 12}
        results.append({
            "name": "Neecha Bhanga Raja Yoga",
            "planet": planet,
            "formed": len(hits) > 0,
            "conditions_met": hits,
            "strength": (
                "FULL" if len(hits) >= 2 else ("PARTIAL" if hits else "NONE")
            ),
            "dusthana_weakened": dusthana,
            "description": f"{planet} debilitated in {p_sign}; conditions {hits}",
        })
    if not results:
        return [{"name": "Neecha Bhanga Raja Yoga", "formed": False}]
    return results


def check_parivartana(chart):
    """Classify mutual sign exchanges. rules.md §9.6."""
    kendra, trikona, dusthana = {1, 4, 7, 10}, {1, 5, 9}, {6, 8, 12}
    seen = set()
    yogas = []
    for p in PLANETS_7:
        p_sign = _sign_of(chart, p)
        q = SIGN_LORDS.get(p_sign)
        if not q or q == p or q not in PLANETS_7:
            continue
        q_sign = _sign_of(chart, q)
        if SIGN_LORDS.get(q_sign) != p:
            continue
        pair = tuple(sorted((p, q)))
        if pair in seen:
            continue
        seen.add(pair)
        hp, hq = _house_of(chart, p), _house_of(chart, q)
        houses = {hp, hq}
        if houses <= dusthana:
            kind = "VIPARITA_PARIVARTANA"
        elif houses & dusthana:
            kind = "DAINYA_PARIVARTANA"
        elif houses <= (kendra | trikona):
            kind = "MAHA_PARIVARTANA"
        elif (houses & (kendra | trikona)) and (houses & {2, 3, 11}):
            kind = "KAHALA_PARIVARTANA"
        else:
            kind = "KAHALA_PARIVARTANA"
        yogas.append({
            "name": f"Parivartana Yoga ({kind})",
            "formed": True,
            "planets": [p, q],
            "houses": [hp, hq],
            "classification": kind,
            "description": f"{p} in {p_sign} ↔ {q} in {q_sign} ({kind})",
        })
    if not yogas:
        yogas.append({"name": "Parivartana Yoga", "formed": False})
    return yogas


def check_extended_yogas(chart):
    """§9.7 catalogue: Budhaditya, lunar, wealth, dosha yogas."""
    out = []
    sun_h, moon_h, mer_h = _house_of(chart, "Sun"), _house_of(chart, "Moon"), _house_of(chart, "Mercury")
    mer_comb = False
    try:
        mer_comb = bool(chart.combustion.get("Mercury", {}).get("is_combust"))
    except Exception:
        pass
    mer_own = chart.rashi_chart.get("Mercury", {}).get("dignity") in (
        "Own Sign", "Exalted", "Moolatrikona"
    )
    budha = _same_sign(chart, "Sun", "Mercury") and (not mer_comb or mer_own)
    out.append({
        "name": "Budhaditya Yoga",
        "formed": budha,
        "description": "Sun-Mercury conjunction" + (" (Mercury protected)" if mer_own else ""),
    })

    # Sunapha / Anapha / Durudhara — 2nd/12th from Moon, exclude Sun/Rahu/Ketu
    lunar_check = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    in2_m = [p for p in lunar_check if _house_from(_house_of(chart, p), moon_h) == 2]
    in12_m = [p for p in lunar_check if _house_from(_house_of(chart, p), moon_h) == 12]
    out.append({"name": "Sunapha Yoga", "formed": bool(in2_m), "planets": in2_m})
    out.append({"name": "Anapha Yoga", "formed": bool(in12_m), "planets": in12_m})
    out.append({"name": "Durudhara Yoga", "formed": bool(in2_m) and bool(in12_m),
                "planets_2": in2_m, "planets_12": in12_m})
    out.append({
        "name": "Chandra-Mangal Yoga",
        "formed": _same_sign(chart, "Moon", "Mars"),
        "description": "Moon conjunct Mars",
    })

    natural_benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
    amala = any(
        _house_of(chart, p) == 10 or _house_from(_house_of(chart, p), moon_h) == 10
        for p in natural_benefics
    )
    out.append({"name": "Amala Yoga", "formed": amala})

    # Classical Lakshmi (Phaladeepika): 9th or 5th lord own/exalt in a Kendra,
    # and Lagna lord powerfully placed (own/exalt/MT or in Kendra).
    # 9L merely occupying Lagna with 1L is Raja/Dhana, not Lakshmi.
    kendra = {1, 4, 7, 10}
    strong_dig = ("Own Sign", "Exalted", "Moolatrikona")

    def _dig(p):
        return chart.rashi_chart.get(p, {}).get("dignity", "")

    lord9 = chart.lordships.get(9)
    lord5 = chart.lordships.get(5)
    lord1 = chart.lordships.get(1)
    nine_or_five = False
    for lord in (lord9, lord5):
        if lord and _dig(lord) in strong_dig and _house_of(chart, lord) in kendra:
            nine_or_five = True
            break
    lagna_strong = bool(
        lord1 and (_dig(lord1) in strong_dig or _house_of(chart, lord1) in kendra)
    )
    lakshmi = nine_or_five and lagna_strong
    out.append({
        "name": "Lakshmi Yoga",
        "formed": lakshmi,
        "description": (
            "9th or 5th lord own/exalt in Kendra, Lagna lord strong"
            if lakshmi else
            "9L/5L not own-or-exalt in Kendra (1L+9L in Lagna is Raja/Dhana)"
        ),
    })

    adhi_n = sum(
        1 for p in natural_benefics
        if _house_from(_house_of(chart, p), moon_h) in {6, 7, 8}
    )
    out.append({"name": "Adhi Yoga", "formed": adhi_n >= 2, "benefics_count": adhi_n})

    out.append({
        "name": "Guru-Chandal Yoga",
        "formed": _same_sign(chart, "Jupiter", "Rahu"),
        "description": "Jupiter conjunct Rahu",
    })

    occupied = []
    for p in PLANETS_9:
        sidx = chart.positions.get(p, {}).get("sign_index")
        if sidx is not None:
            occupied.append(sidx)
    occupied = sorted(set(occupied))
    longest = 1
    run = 1
    if occupied:
        circ = occupied + [s + 12 for s in occupied]
        for i in range(1, len(circ)):
            if circ[i] == circ[i - 1] + 1:
                run += 1
                longest = max(longest, run)
            else:
                run = 1
        longest = min(longest, 12)
    out.append({
        "name": "Graha Malika Yoga",
        "formed": longest >= 3,
        "consecutive_signs": longest,
    })

    lord9p = chart.lordships.get(9)
    pitra = (
        _same_sign(chart, "Sun", "Rahu")
        or (lord9p and _same_sign(chart, lord9p, "Rahu"))
        or _house_of(chart, "Rahu") == 9
    )
    out.append({"name": "Pitra Dosha", "formed": pitra})

    kendradhipati = []
    for h in (4, 7, 10):
        lord = chart.lordships.get(h)
        if lord in ("Jupiter", "Venus", "Mercury", "Moon"):
            kendradhipati.append(f"{lord}={h}L")
    out.append({
        "name": "Kendradhipati Dosha",
        "formed": bool(kendradhipati),
        "lords": kendradhipati,
    })
    return out


# ═══════════════════════════════════════════
# MASTER YOGA SCANNER
# ═══════════════════════════════════════════

def check_all_yogas(chart):
    """
    Run all yoga checks and return a complete tally.
    
    Args:
        chart: BirthChart object
        
    Returns:
        dict with:
            formed: list of formed yogas
            not_formed: list of checked but not formed
            total_formed: count
            total_checked: count
    """
    all_checks = []

    # Pancha Mahapurusha (5 yogas)
    pmp = check_pancha_mahapurusha(chart)
    all_checks.extend(pmp)
    # Add non-formed PMP
    formed_pmp = {y["planet"] for y in pmp}
    for planet, name in [("Mars", "Ruchaka"), ("Mercury", "Bhadra"),
                         ("Jupiter", "Hamsa"), ("Venus", "Malavya"), ("Saturn", "Sasa")]:
        if planet not in formed_pmp:
            all_checks.append({"name": f"{name} Yoga", "formed": False, "planet": planet})

    # VRY
    vry = check_viparita_raja(chart)
    all_checks.extend(vry)

    # Individual yogas
    all_checks.append(check_gaja_kesari(chart))
    all_checks.append(check_kemadruma(chart))
    all_checks.append(check_manglik(chart))
    all_checks.append(check_kaal_sarp(chart))
    all_checks.append(check_sakata(chart))
    all_checks.append(check_ubhayachari(chart))
    all_checks.append(check_kalatramooladdhana(chart))

    # Raj Yogas
    raj = check_raj_yogas(chart)
    all_checks.extend(raj)

    # Dhana Yogas
    dhana = check_dhana_yogas(chart)
    all_checks.extend(dhana)

    all_checks.extend(check_neecha_bhanga(chart))
    all_checks.extend(check_parivartana(chart))
    all_checks.extend(check_extended_yogas(chart))

    # ── Nabhasa Yogas (32) ──────────────────────────────
    try:
        from .yogas_nabhasa import check_all_nabhasa_yogas
        all_checks.extend(check_all_nabhasa_yogas(chart))
    except Exception:
        pass  # Module not available — degrade gracefully

    # ── Extended Raja/Dhana/Aristha/Sannyasa Yogas ──────
    try:
        from .yogas_raja import check_all_raja_yogas
        all_checks.extend(check_all_raja_yogas(chart))
    except Exception:
        pass  # Module not available — degrade gracefully

    # Separate formed vs not formed
    formed = [y for y in all_checks if y.get("formed", False)]
    not_formed = [y for y in all_checks if not y.get("formed", False)]

    return {
        "formed": formed,
        "not_formed": not_formed,
        "total_formed": len(formed),
        "total_checked": len(all_checks),
    }


# ═══════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════

def format_yoga_tally(yoga_data):
    """Format yoga results as readable text."""
    lines = []
    lines.append(f"=== Yoga Tally: {yoga_data['total_formed']} formed / {yoga_data['total_checked']} checked ===\n")

    lines.append("FORMED YOGAS:")
    for y in yoga_data["formed"]:
        desc = y.get("description", y.get("connection", ""))
        lines.append(f"  + {y['name']} — {desc}")

    lines.append("\nNOT FORMED:")
    for y in yoga_data["not_formed"]:
        lines.append(f"  - {y['name']}")

    return "\n".join(lines)
