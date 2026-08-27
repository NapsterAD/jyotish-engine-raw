"""
kp.py — Krishnamurti Paddhati calculations.
Sign / star / sub / sub-sub for any longitude; equal-bhava cusps;
Placidus occupancy; ruling planets; ABCD significators.
"""

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS,
    NAKSHATRAS, NAKSHATRA_SPAN,
    VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS, VIMSHOTTARI_TOTAL,
    PLANETS_9,
)
from ..core.mapping import house_to_sign

DAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
# Sunday=0 ... Saturday=6


def _degree_in_nakshatra(longitude):
    longitude = longitude % 360.0
    nak_idx = min(int(longitude / NAKSHATRA_SPAN), 26)
    return nak_idx, longitude - nak_idx * NAKSHATRA_SPAN


def kp_star_lord(longitude):
    nak_idx, _ = _degree_in_nakshatra(longitude)
    return NAKSHATRAS[nak_idx]["lord"]


def kp_sign_lord(longitude):
    return SIGN_LORDS[SIGNS[int((longitude % 360.0) / 30) % 12]]


def _walk_vimshottari(start_lord, remainder, total_span):
    """Return (lord, start_in_span, span) for the sub-arc containing remainder."""
    lord_idx = VIMSHOTTARI_ORDER.index(start_lord)
    accumulated = 0.0
    for i in range(9):
        lord = VIMSHOTTARI_ORDER[(lord_idx + i) % 9]
        span = total_span * (VIMSHOTTARI_YEARS[lord] / VIMSHOTTARI_TOTAL)
        if accumulated + span > remainder:
            return lord, accumulated, span
        accumulated += span
    lord = start_lord
    return lord, accumulated, total_span * (VIMSHOTTARI_YEARS[lord] / VIMSHOTTARI_TOTAL)


def kp_sub_lord(longitude):
    """Sub-lord of λ. Sequence starts from the star lord (rules.md §21.2)."""
    nak_idx, degree_in_nak = _degree_in_nakshatra(longitude)
    star = NAKSHATRAS[nak_idx]["lord"]
    sub, _, _ = _walk_vimshottari(star, degree_in_nak, NAKSHATRA_SPAN)
    return sub


def kp_sub_sub_lord(longitude):
    """Sub-sub lord of λ. Sequence starts from the sub-lord."""
    nak_idx, degree_in_nak = _degree_in_nakshatra(longitude)
    star = NAKSHATRAS[nak_idx]["lord"]
    sub, sub_start, sub_span = _walk_vimshottari(star, degree_in_nak, NAKSHATRA_SPAN)
    remainder = degree_in_nak - sub_start
    ssl, _, _ = _walk_vimshottari(sub, remainder, sub_span)
    return ssl


def kp_sssl_lord(longitude):
    """Sub-sub-sub lord of λ (4th KP level)."""
    nak_idx, degree_in_nak = _degree_in_nakshatra(longitude)
    star = NAKSHATRAS[nak_idx]["lord"]
    sub, sub_start, sub_span = _walk_vimshottari(star, degree_in_nak, NAKSHATRA_SPAN)
    remainder = degree_in_nak - sub_start
    ssl, ssl_start, ssl_span = _walk_vimshottari(sub, remainder, sub_span)
    rem2 = remainder - ssl_start
    sssl, _, _ = _walk_vimshottari(ssl, rem2, ssl_span)
    return sssl


def kp_chain(longitude):
    """Sign / star / sub / SSL / SSSL of any longitude."""
    return {
        "sign_lord": kp_sign_lord(longitude),
        "star_lord": kp_star_lord(longitude),
        "sub_lord": kp_sub_lord(longitude),
        "sub_sub_lord": kp_sub_sub_lord(longitude),
        "sssl_lord": kp_sssl_lord(longitude),
        "kp_249": kp_249_index(longitude),
    }


def _build_kp249_table():
    """
    Sequential KP 1-249 zones. 27 nak × 9 subs; a sub that straddles a 30°
    sign boundary is split into two numbered pieces (rules.md §21.6).
    Each row: (start, end, number, star_lord, sub_lord).
    """
    table = []
    num = 1
    for nak in range(27):
        star = NAKSHATRAS[nak]["lord"]
        star_idx = VIMSHOTTARI_ORDER.index(star)
        nak_start = nak * NAKSHATRA_SPAN
        accumulated = 0.0
        for k in range(9):
            sub = VIMSHOTTARI_ORDER[(star_idx + k) % 9]
            span = NAKSHATRA_SPAN * (VIMSHOTTARI_YEARS[sub] / VIMSHOTTARI_TOTAL)
            sub_start = nak_start + accumulated
            sub_end = sub_start + span
            start_sign = int((sub_start + 1e-12) / 30.0)
            end_sign = int((sub_end - 1e-12) / 30.0)
            if end_sign != start_sign:
                boundary = (start_sign + 1) * 30.0
                table.append((sub_start, boundary, num, star, sub))
                num += 1
                table.append((boundary, sub_end, num, star, sub))
                num += 1
            else:
                table.append((sub_start, sub_end, num, star, sub))
                num += 1
            accumulated += span
    return table


_KP249_TABLE = _build_kp249_table()


def kp_249_index(longitude):
    """KP-249 zone number (1-249) of λ. KP-1 = Aries 0° Ashwini-Ketu-Ketu."""
    lam = longitude % 360.0
    if abs(lam) < 1e-12:
        return 1
    for start, end, num, _star, _sub in _KP249_TABLE:
        if start <= lam < end:
            return num
    return _KP249_TABLE[-1][2]


def kp_249_info(longitude):
    """KP-249 zone plus star/sub of that piece."""
    num = kp_249_index(longitude)
    for start, end, n, star, sub in _KP249_TABLE:
        if n == num:
            return {
                "kp_249": n,
                "start": round(start, 6),
                "end": round(end, 6),
                "star_lord": star,
                "sub_lord": sub,
            }
    return {"kp_249": num}


def kp_coords(longitude):
    """Sign / star / sub / SSL / SSSL of a longitude, plus KP-249. rules.md §21.2."""
    longitude = longitude % 360.0
    sign = SIGNS[int(longitude / 30) % 12]
    nak_idx, _ = _degree_in_nakshatra(longitude)
    nak = NAKSHATRAS[nak_idx]
    ch = kp_chain(longitude)
    return {
        "longitude": round(longitude, 6),
        "sign": sign,
        "sign_lord": SIGN_LORDS[sign],
        "nakshatra": nak["name"],
        "star_lord": nak["lord"],
        "sub_lord": ch["sub_lord"],
        "sub_sub_lord": ch["sub_sub_lord"],
        "sssl_lord": ch["sssl_lord"],
        "kp_249": ch["kp_249"],
    }


def equal_bhava_cusps(asc_longitude):
    """
    Equal-bhava cusps: same degree as Lagna in each successive sign.
    λ_C(H) = ASC + 30°(H-1).
    """
    result = {}
    for h in range(1, 13):
        cusp_long = (asc_longitude + 30.0 * (h - 1)) % 360.0
        coords = kp_coords(cusp_long)
        coords["house"] = h
        result[h] = coords
    return result


def equal_bhava_occupancy(planet_longitude, asc_longitude):
    offset = (planet_longitude - asc_longitude + 360.0) % 360.0
    house = int(offset / 30) + 1
    return 12 if house > 12 else house


def placidus_occupancy(planet_longitude, cusp_longitudes):
    """
    House H if cusp[H] ≤ λ < cusp[H+1] (wrap at 360).
    cusp_longitudes: dict house -> longitude (1-12).
    """
    lam = planet_longitude % 360.0
    for h in range(1, 13):
        start = cusp_longitudes[h] % 360.0
        end = cusp_longitudes[h % 12 + 1] % 360.0
        if start <= end:
            if start <= lam < end:
                return h
        else:
            if lam >= start or lam < end:
                return h
    return 1


def _day_lord_from_date(date_str):
    """Vara lord. date_str YYYY-MM-DD, local civil date (Sunday=Sun)."""
    from datetime import datetime
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    sunday0 = (dt.weekday() + 1) % 7
    return DAY_LORDS[sunday0]


def ruling_planets(chart, date=None):
    """
    Natal (or query-date) ruling planets: Lagna star/sign, Moon star/sign, day lord.
    Nodes join the set when they share a sign with an RP or their star lord is an RP.
    """
    positions = chart.positions
    lagna = positions["Lagna"]
    moon = positions["Moon"]
    date_str = date or chart.birth_data["date"]

    rps = {
        "lagna_star_lord": lagna.get("nakshatra_lord") or kp_star_lord(lagna["longitude"]),
        "lagna_sign_lord": SIGN_LORDS[lagna["sign"]],
        "lagna_sub_lord": lagna.get("sub_lord") or kp_sub_lord(lagna["longitude"]),
        "moon_star_lord": moon.get("nakshatra_lord") or kp_star_lord(moon["longitude"]),
        "moon_sign_lord": SIGN_LORDS[moon["sign"]],
        "day_lord": _day_lord_from_date(date_str),
    }
    core = [
        rps["lagna_star_lord"], rps["lagna_sign_lord"], rps["lagna_sub_lord"],
        rps["moon_star_lord"], rps["moon_sign_lord"], rps["day_lord"],
    ]
    unique = []
    for p in core:
        if p not in unique:
            unique.append(p)

    nodes_added = []
    for node in ("Rahu", "Ketu"):
        npos = positions.get(node, {})
        if not isinstance(npos, dict):
            continue
        n_sign = npos.get("sign")
        n_star = npos.get("nakshatra_lord") or kp_star_lord(npos.get("longitude", 0))
        shares_sign = any(
            positions.get(rp, {}).get("sign") == n_sign
            for rp in unique
            if isinstance(positions.get(rp), dict)
        )
        if n_star in unique or shares_sign or SIGN_LORDS.get(n_sign) in unique:
            if node not in unique:
                unique.append(node)
                nodes_added.append(node)

    rps["list"] = unique
    rps["nodes_added"] = nodes_added
    return rps


def _occupants(chart, house_num, system="placidus"):
    occupants = []
    if system == "placidus":
        cusp_longs = {
            h: chart.house_cusps["cusps"][h]["longitude"]
            for h in range(1, 13)
        }
        for planet in PLANETS_9:
            pos = chart.positions.get(planet)
            if not pos or not isinstance(pos, dict):
                continue
            h = placidus_occupancy(pos["longitude"], cusp_longs)
            if h == house_num:
                occupants.append(planet)
    else:
        asc = chart.positions["Lagna"]["longitude"]
        for planet in PLANETS_9:
            pos = chart.positions.get(planet)
            if not pos or not isinstance(pos, dict):
                continue
            h = equal_bhava_occupancy(pos["longitude"], asc)
            if h == house_num:
                occupants.append(planet)
    return occupants


def _house_sign_lord(chart, house_num, system="placidus"):
    if system == "placidus":
        sign = chart.house_cusps["cusps"][house_num]["sign"]
        return SIGN_LORDS[sign]
    return SIGN_LORDS[house_to_sign(house_num, chart.lagna_index)]


def abcd_significators(chart, house_num, system="placidus"):
    """
    KP ABCD significators of house H.
    A: planets in the nakshatra of an occupant of H
    B: occupants of H
    C: planets in the nakshatra of the sign-lord of H
    D: sign-lord of H
    """
    cache = getattr(chart, "_abcd_cache", None)
    if cache is None:
        chart._abcd_cache = {}
        cache = chart._abcd_cache
    key = (system, int(house_num))
    hit = cache.get(key)
    if hit is not None:
        return hit
    occupants = _occupants(chart, house_num, system)
    lord = _house_sign_lord(chart, house_num, system)
    occupant_set = set(occupants)

    level_a = []
    level_c = []
    for planet in PLANETS_9:
        pos = chart.positions.get(planet)
        if not pos or not isinstance(pos, dict):
            continue
        star = pos.get("nakshatra_lord") or kp_star_lord(pos["longitude"])
        # A: planet sits in the nakshatra of an occupant (star lord ∈ occupants)
        if star in occupant_set and planet not in level_a:
            level_a.append(planet)
        # C: planet sits in the nakshatra of the house sign-lord
        if star == lord and planet not in level_c:
            level_c.append(planet)

    # Rahu/Ketu as agents of the sign they occupy
    agents = []
    for node in ("Rahu", "Ketu"):
        npos = chart.positions.get(node, {})
        if not isinstance(npos, dict):
            continue
        agent_of = SIGN_LORDS.get(npos.get("sign"))
        if agent_of == lord or agent_of in occupants:
            agents.append(node)

    result = {
        "house": house_num,
        "system": system,
        "A": level_a,
        "B": occupants,
        "C": level_c,
        "D": [lord],
        "agents": agents,
        "cusp_sub_lord": (
            chart.house_cusps["cusps"][house_num].get("sub_lord")
            if system == "placidus"
            else kp_sub_lord(
                (chart.positions["Lagna"]["longitude"] + 30.0 * (house_num - 1)) % 360.0
            )
        ),
    }
    cache[key] = result
    return result


def fruitful_significators(chart, houses, deny_houses=None, system="placidus"):
    """CSL of each house must appear among A/B/C/D of the house set."""
    deny_houses = deny_houses or []
    sig_set = []
    details = {}
    for h in houses:
        block = abcd_significators(chart, h, system)
        details[h] = block
        for key in ("A", "B", "C", "D"):
            for p in block[key]:
                if p not in sig_set:
                    sig_set.append(p)
        for p in block["agents"]:
            if p not in sig_set:
                sig_set.append(p)

    deny_set = []
    for h in deny_houses:
        block = abcd_significators(chart, h, system)
        for key in ("A", "B", "C", "D"):
            for p in block[key]:
                if p not in deny_set:
                    deny_set.append(p)

    csl_hits = {}
    for h in houses:
        csl = details[h]["cusp_sub_lord"]
        csl_hits[h] = {
            "csl": csl,
            "is_significator": csl in sig_set,
            "is_denying": csl in deny_set,
            "fruitful": csl in sig_set and csl not in deny_set,
        }

    return {
        "houses": houses,
        "significators": sig_set,
        "denying": deny_set,
        "csl": csl_hits,
        "details": details,
    }


def calc_kp_bundle(chart):
    """Full natal KP dump: planet triples, equal cusps, Placidus already on chart."""
    planets = {}
    for name in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(name)
        if not pos or not isinstance(pos, dict):
            continue
        planets[name] = {
            "sign_lord": pos.get("sign_lord") or kp_sign_lord(pos["longitude"]),
            "star_lord": pos.get("nakshatra_lord") or kp_star_lord(pos["longitude"]),
            "sub_lord": pos.get("sub_lord") or kp_sub_lord(pos["longitude"]),
            "sub_sub_lord": pos.get("sub_sub_lord") or kp_sub_sub_lord(pos["longitude"]),
            "sssl_lord": pos.get("sssl_lord") or kp_sssl_lord(pos["longitude"]),
            "kp_249": pos.get("kp_249") or kp_249_index(pos["longitude"]),
            "sign": pos["sign"],
            "nakshatra": pos.get("nakshatra"),
        }

    asc = chart.positions["Lagna"]["longitude"]
    equal = equal_bhava_cusps(asc)
    occupancy = {}
    cusp_longs = {
        h: chart.house_cusps["cusps"][h]["longitude"] for h in range(1, 13)
    }
    for planet in PLANETS_9:
        pos = chart.positions.get(planet)
        if not pos or not isinstance(pos, dict):
            continue
        occupancy[planet] = {
            "placidus": placidus_occupancy(pos["longitude"], cusp_longs),
            "equal": equal_bhava_occupancy(pos["longitude"], asc),
            "rashi": chart.rashi_chart[planet]["house_rashi"],
        }

    return {
        "planets": planets,
        "equal_cusps": equal,
        "occupancy": occupancy,
        "ruling_planets": ruling_planets(chart),
    }


def _cusp_longitudes(chart, system="placidus"):
    if system == "equal":
        asc = chart.positions["Lagna"]["longitude"]
        return {h: (asc + 30.0 * (h - 1)) % 360.0 for h in range(1, 13)}
    return {h: chart.house_cusps["cusps"][h]["longitude"] for h in range(1, 13)}


def _houses_occupied_by(chart, planet, system="placidus"):
    occ = (chart.kp.get("occupancy") or {}).get(planet, {})
    if system == "equal":
        return occ.get("equal")
    if system == "placidus":
        return occ.get("placidus")
    return chart.rashi_chart.get(planet, {}).get("house_rashi")


def _houses_lorded(chart, planet):
    return [h for h, lord in chart.lordships.items() if lord == planet]


def _houses_signified_abcd(chart, planet, system="placidus"):
    """Houses for which planet appears in A/B/C/D."""
    hits = []
    for h in range(1, 13):
        block = abcd_significators(chart, h, system)
        roles = []
        for key in ("A", "B", "C", "D"):
            if planet in block.get(key, []):
                roles.append(key)
        if planet in block.get("agents", []):
            roles.append("agent")
        if block.get("cusp_sub_lord") == planet:
            roles.append("CSL")
        if roles:
            hits.append({"house": h, "roles": roles, "fold": len(set(roles))})
    return hits


def ssl_tables(chart):
    """SSL (+ SSSL) for 9 grahas + Lagna and 12 cusps, Placidus and equal."""
    bodies = {}
    for name in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(name)
        if not pos or not isinstance(pos, dict):
            continue
        ch = kp_chain(pos["longitude"])
        ch["longitude"] = round(pos["longitude"], 6)
        ch["sign"] = pos.get("sign")
        ch["nakshatra"] = pos.get("nakshatra")
        bodies[name] = ch

    placidus = {}
    equal = {}
    p_longs = _cusp_longitudes(chart, "placidus")
    e_longs = _cusp_longitudes(chart, "equal")
    for h in range(1, 13):
        pc = kp_chain(p_longs[h])
        pc["longitude"] = round(p_longs[h], 6)
        placidus[str(h)] = pc
        ec = kp_chain(e_longs[h])
        ec["longitude"] = round(e_longs[h], 6)
        equal[str(h)] = ec
    return {"bodies": bodies, "cusps_placidus": placidus, "cusps_equal": equal}


def significator_matrix(chart, system="placidus"):
    """
    9-planet × 12-house fold-count grid.
    Fold bits: A star-of-occupant, B occupant, C star-of-lord, D lord,
    E CSL or sub-lord of occupant/lord.
    """
    matrix = {}
    for planet in PLANETS_9:
        row = {}
        pos = chart.positions.get(planet)
        if not pos or not isinstance(pos, dict):
            continue
        star = pos.get("nakshatra_lord") or kp_star_lord(pos["longitude"])
        sub = pos.get("sub_lord") or kp_sub_lord(pos["longitude"])
        for h in range(1, 13):
            block = abcd_significators(chart, h, system)
            roles = []
            if planet in block["A"]:
                roles.append("A")
            if planet in block["B"]:
                roles.append("B")
            if planet in block["C"]:
                roles.append("C")
            if planet in block["D"]:
                roles.append("D")
            occupants = block["B"]
            lord = block["D"][0] if block["D"] else None
            if block.get("cusp_sub_lord") == planet:
                roles.append("E_CSL")
            elif sub in occupants or sub == lord:
                roles.append("E_sub")
            row[str(h)] = {
                "fold": len(roles),
                "roles": roles,
                "star": star,
                "sub": sub,
            }
        matrix[planet] = row
    return {"system": system, "grid": matrix}


def cuspal_interlinks(chart, system="placidus"):
    """
    CRL: for each cusp, planets in the star/sub of its CSL, houses that CSL
    occupies/lords, and house-to-house links (CSL of A sits in star of CSL of B).
    """
    longs = _cusp_longitudes(chart, system)
    csl = {h: kp_sub_lord(longs[h]) for h in range(1, 13)}
    ssl = {h: kp_sub_sub_lord(longs[h]) for h in range(1, 13)}
    star_of = {}
    sub_of = {}
    for planet in PLANETS_9:
        pos = chart.positions.get(planet)
        if not pos or not isinstance(pos, dict):
            continue
        star_of[planet] = pos.get("nakshatra_lord") or kp_star_lord(pos["longitude"])
        sub_of[planet] = pos.get("sub_lord") or kp_sub_lord(pos["longitude"])

    houses = {}
    for h in range(1, 13):
        lord = csl[h]
        in_star = [p for p, s in star_of.items() if s == lord]
        in_sub = [p for p, s in sub_of.items() if s == lord]
        occupied = _houses_occupied_by(chart, lord, system)
        lorded = _houses_lorded(chart, lord)
        houses[str(h)] = {
            "csl": lord,
            "ssl": ssl[h],
            "planets_in_star_of_csl": in_star,
            "planets_in_sub_of_csl": in_sub,
            "csl_occupies_house": occupied,
            "csl_lords_houses": lorded,
        }

    links = []
    for a in range(1, 13):
        for b in range(1, 13):
            if a == b:
                continue
            # CSL(A) is in the nakshatra of CSL(B)
            if star_of.get(csl[a]) == csl[b]:
                links.append({"from_cusp": a, "to_cusp": b, "via": "CSL_in_star_of_CSL"})
            if csl[a] == csl[b] and a < b:
                links.append({"from_cusp": a, "to_cusp": b, "via": "same_CSL"})
    return {"system": system, "cusps": houses, "interlinks": links}


def planet_star_chains(chart, system="placidus"):
    """4-level KP chain per graha, with houses each level signifies."""
    out = {}
    for planet in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(planet)
        if not pos or not isinstance(pos, dict):
            continue
        ch = kp_chain(pos["longitude"])
        levels = []
        for key in ("sign_lord", "star_lord", "sub_lord", "sub_sub_lord", "sssl_lord"):
            lord = ch[key]
            levels.append({
                "level": key,
                "planet": lord,
                "occupies": _houses_occupied_by(chart, lord, system),
                "lords": _houses_lorded(chart, lord),
                "significator_of": _houses_signified_abcd(chart, lord, system),
            })
        out[planet] = {
            "longitude": round(pos["longitude"], 6),
            "chain": [
                ch["sign_lord"], ch["star_lord"], ch["sub_lord"],
                ch["sub_sub_lord"], ch["sssl_lord"],
            ],
            "levels": levels,
        }
    return {"system": system, "bodies": out}


def calc_kp_advanced(chart):
    """All KP raw layers an AI timing stage needs."""
    return {
        "ssl_tables": ssl_tables(chart),
        "significator_matrix_placidus": significator_matrix(chart, "placidus"),
        "significator_matrix_equal": significator_matrix(chart, "equal"),
        "cuspal_interlinks_placidus": cuspal_interlinks(chart, "placidus"),
        "cuspal_interlinks_equal": cuspal_interlinks(chart, "equal"),
        "planet_star_chains": planet_star_chains(chart, "placidus"),
        "abcd_all_houses": {
            str(h): abcd_significators(chart, h, "placidus") for h in range(1, 13)
        },
        "fruitful_marriage_2_7_11": fruitful_significators(chart, [2, 7, 11], [1, 6, 10]),
        "fruitful_career_2_6_10_11": fruitful_significators(chart, [2, 6, 10, 11], [5, 8, 12]),
        "fruitful_wealth_2_11": fruitful_significators(chart, [2, 11], [8, 12]),
    }


# ═══════════════════════════════════════════
# KP HORARY (PRASHNA) & 4-STEP THEORY
# ═══════════════════════════════════════════
# Sources: KP Reader 6 (Horary), Advanced Stellar KP, 4-Step Theory

def get_kp249_longitude(horary_number):
    """
    Given a KP Horary number (1 to 249), return the starting longitude of that sub-arc.
    """
    if horary_number < 1 or horary_number > 249:
        raise ValueError(f"Horary number must be 1..249, got {horary_number}")
    
    table = _build_kp249_table()
    row = table[horary_number - 1]
    return {
        "number": horary_number,
        "start_longitude": row[0],
        "end_longitude": row[1],
        "star_lord": row[3],
        "sub_lord": row[4],
        "sign_lord": kp_sign_lord(row[0]),
    }


def kp_four_step_theory(chart, planet, target_houses, detrimental_houses=None, system="placidus"):
    """
    Evaluate a planet using KP 4-Step Theory (Sunil Gondhalekar system):
      Step 1: Planet itself (occupies & lords)
      Step 2: Star Lord of the Planet (occupies & lords) - SOURCE
      Step 3: Sub Lord of the Planet (occupies & lords) - DECIDING / END RESULT
      Step 4: Star Lord of the Sub Lord (occupies & lords) - CONFIRMATION
    
    If Step 3 / Step 4 strongly signify detrimental houses, the event is negated.
    
    Returns:
        dict with 4 steps, favorable score, negation flag, and judgment.
    """
    pos = chart.positions.get(planet)
    if not pos or not isinstance(pos, dict):
        return {"error": f"Planet {planet} not found"}
    
    p_lon = pos["longitude"]
    star = pos.get("nakshatra_lord") or kp_star_lord(p_lon)
    sub = pos.get("sub_lord") or kp_sub_lord(p_lon)
    
    # Sub lord's position in chart to find its star lord
    sub_pos = chart.positions.get(sub, {})
    sub_star = sub_pos.get("nakshatra_lord") if isinstance(sub_pos, dict) else kp_star_lord(p_lon)
    
    steps = [
        {"step": 1, "entity": planet, "role": "Offer / Planet",
         "occupies": _houses_occupied_by(chart, planet, system), "lords": _houses_lorded(chart, planet)},
        {"step": 2, "entity": star, "role": "Source / Star Lord",
         "occupies": _houses_occupied_by(chart, star, system), "lords": _houses_lorded(chart, star)},
        {"step": 3, "entity": sub, "role": "Decider / Sub Lord",
         "occupies": _houses_occupied_by(chart, sub, system), "lords": _houses_lorded(chart, sub)},
        {"step": 4, "entity": sub_star, "role": "Confirm / Star of Sub",
         "occupies": _houses_occupied_by(chart, sub_star, system), "lords": _houses_lorded(chart, sub_star)},
    ]
    
    for s in steps:
        occ_list = [s["occupies"]] if isinstance(s["occupies"], int) else (s["occupies"] or [])
        all_h = set(occ_list + s["lords"])
        s["signifies_target"] = list(all_h & set(target_houses))
        s["signifies_detrimental"] = list(all_h & set(detrimental_houses or []))
    
    # Decider check: Step 3 & 4
    step3_favorable = bool(steps[2]["signifies_target"])
    step3_detrimental = bool(steps[2]["signifies_detrimental"])
    step4_favorable = bool(steps[3]["signifies_target"])
    
    is_promising = step3_favorable and not step3_detrimental
    
    return {
        "planet": planet,
        "steps": steps,
        "target_houses": target_houses,
        "detrimental_houses": detrimental_houses,
        "is_promising": is_promising,
        "status": "FRUITFUL" if is_promising else ("NEGATED" if step3_detrimental else "NEUTRAL"),
    }


def verify_rp_agreement(chart, query_rp_list=None):
    """
    Check consistency of natal ruling planets against current query RP or verify strength.
    """
    natal_rp = kp_ruling_planets(chart)
    rp_planets = natal_rp.get("list", [])
    
    return {
        "natal_ruling_planets": rp_planets,
        "details": natal_rp,
        "is_verified": len(rp_planets) >= 3,
    }

