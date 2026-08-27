"""
transits.py — Transit engine: current positions for any date, transit-to-natal overlay,
sign ingress finder, double transit (Jupiter+Saturn), SAV transit scoring, BB transit.
100% offline — uses Swiss Ephemeris via Ephemeris wrapper.
"""

from datetime import datetime, timedelta

import swisseph as swe

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_7, PLANETS_9,
    SPECIAL_ASPECTS, NAKSHATRAS, NAKSHATRA_SPAN, PLANET_SWE_IDS,
)
from ..core.ephemeris import Ephemeris
from ..core.mapping import sign_to_house, house_counted_from, house_to_sign

_SWE_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH | swe.FLG_MOSEPH


def sidereal_lon_speed(planet, jd):
    """Single-body sidereal longitude + daily speed. Ketu = Rahu + 180°."""
    if planet == "Ketu":
        r = swe.calc_ut(jd, PLANET_SWE_IDS["Rahu"], _SWE_FLAGS)[0]
        return (r[0] + 180.0) % 360.0, r[3]
    sid = PLANET_SWE_IDS.get(planet)
    if sid is None:
        raise ValueError(planet)
    r = swe.calc_ut(jd, sid, _SWE_FLAGS)[0]
    return r[0] % 360.0, r[3]


def slim_from_lon_speed(lon, speed):
    """Sign / nakshatra / motion from a single-body Swiss result. No houses."""
    lon = lon % 360.0
    sign_idx = int(lon / 30.0) % 12
    nak_idx = min(int(lon / NAKSHATRA_SPAN), 26)
    nak = NAKSHATRAS[nak_idx]
    return {
        "longitude": lon,
        "sign": SIGNS[sign_idx],
        "sign_index": sign_idx,
        "degree_in_sign": lon % 30.0,
        "nakshatra": nak["name"],
        "nakshatra_num": nak["num"],
        "nakshatra_lord": nak["lord"],
        "retrograde": bool(speed < 0),
        "speed": speed,
    }


def sav_bav_at_sign(chart, planet, sign_idx):
    """SAV / BAV bindus for a sign index. SAV and BAV are lists, not dicts."""
    sav_score = None
    bav_score = None
    try:
        sav_block = chart.ashtakavarga.get("sav", {})
        sav_list = sav_block.get("sav") if isinstance(sav_block, dict) else sav_block
        if isinstance(sav_list, list) and 0 <= sign_idx < 12:
            sav_score = sav_list[sign_idx]
    except Exception:
        pass
    if planet in PLANETS_7:
        try:
            row = chart.ashtakavarga.get("bav", {}).get(planet)
            if isinstance(row, list) and 0 <= sign_idx < 12:
                bav_score = row[sign_idx]
        except Exception:
            pass
    return sav_score, bav_score


def _sign_of_lon(lon):
    return SIGNS[int((lon % 360.0) / 30.0) % 12]


# ═══════════════════════════════════════════
# TRANSIT POSITIONS (any arbitrary date)
# ═══════════════════════════════════════════

def calc_transit_positions(date, time="12:00:00", tz="+00:00",
                           lat=None, lon=None,
                           ephe_path=None, ayanamsha="lahiri"):
    """
    Calculate planetary positions for any date (transit snapshot).

    Args:
        date: "YYYY-MM-DD"
        time: "HH:MM:SS" (default noon)
        tz: timezone string
        lat, lon: location (for Lagna). Required for a real native; 0,0 if omitted
                  (planet longitudes do not depend on geography).
        ephe_path: Swiss Ephemeris data path
        ayanamsha: sidereal system

    Returns:
        dict of planet -> {longitude, sign, sign_index, degree_in_sign, nakshatra, retrograde, ...}
    """
    if lat is None:
        lat = 0.0
    if lon is None:
        lon = 0.0
    ephe = Ephemeris(ephe_path=ephe_path, ayanamsha=ayanamsha)
    return ephe.get_planet_positions(date, time, tz, lat, lon)


# ═══════════════════════════════════════════
# TRANSIT-TO-NATAL OVERLAY
# ═══════════════════════════════════════════

def calc_transit_to_natal(transit_positions, natal_chart):
    """
    Overlay transit positions onto natal chart.
    For each transiting planet, determine:
      - Which natal house it's transiting
      - Which natal planets it conjuncts (same sign)
      - Which natal houses/planets it aspects
      - SAV score in that sign (if ashtakavarga available)

    Args:
        transit_positions: dict from calc_transit_positions()
        natal_chart: BirthChart object

    Returns:
        dict of planet -> {transit_sign, natal_house, conjuncts, aspects, sav_score, ...}
    """
    lagna_idx = natal_chart.lagna_index
    result = {}

    for planet in PLANETS_9:
        t_pos = transit_positions.get(planet, {})
        if not t_pos or isinstance(t_pos, (float, int)):
            continue

        t_sign = t_pos.get("sign", "")
        t_sign_idx = t_pos.get("sign_index", 0)
        t_long = t_pos.get("longitude", 0)
        t_retro = t_pos.get("retrograde", False)

        # Which natal house is this transit in?
        natal_house = sign_to_house(t_sign_idx, lagna_idx)

        # Which natal planets does it conjunct? (same sign)
        conjuncts = []
        for n_planet in PLANETS_9:
            n_pos = natal_chart.positions.get(n_planet, {})
            if isinstance(n_pos, dict) and n_pos.get("sign") == t_sign:
                conjuncts.append(n_planet)

        # Which houses does this transit aspect?
        aspected_houses = [house_counted_from(natal_house, 7)]
        if planet in SPECIAL_ASPECTS:
            for offset in SPECIAL_ASPECTS[planet]:
                aspected_houses.append(house_counted_from(natal_house, offset))
        aspected_houses = sorted(set(aspected_houses))

        # Which natal planets are aspected?
        aspected_planets = []
        for a_house in aspected_houses:
            aspected_planets.extend(natal_chart.get_planets_in_house(a_house))

        sav_score, bav_score = sav_bav_at_sign(natal_chart, planet, t_sign_idx)

        result[planet] = {
            "transit_sign": t_sign,
            "transit_degree": round(t_pos.get("degree_in_sign", 0), 2),
            "transit_longitude": round(t_long, 4),
            "transit_nakshatra": t_pos.get("nakshatra", ""),
            "retrograde": t_retro,
            "natal_house": natal_house,
            "conjuncts_natal": conjuncts,
            "aspects_houses": aspected_houses,
            "aspects_planets": aspected_planets,
            "sav_score": sav_score,
            "bav_score": bav_score,
        }

    return result


# ═══════════════════════════════════════════
# SIGN INGRESS FINDER
# ═══════════════════════════════════════════

def find_sign_ingress(planet, start_date, end_date, ephe_path=None,
                      ayanamsha="lahiri", step_days=1, chart=None):
    """
    Sign ingresses via single-body Swiss calls + adaptive step to the next
    sign boundary (no full 9-planet + houses dump per day).
    """
    if chart is not None:
        _ = chart._ephe  # sidereal mode already applied at chart init
    else:
        Ephemeris(ephe_path=ephe_path, ayanamsha=ayanamsha)

    y, m, d = (int(x) for x in start_date.split("-"))
    ey, em, ed = (int(x) for x in end_date.split("-"))
    jd = swe.julday(y, m, d, 12.0)
    end_jd = swe.julday(ey, em, ed, 12.0)
    lon, spd = sidereal_lon_speed(planet, jd)
    prev_sign = int((lon % 360.0) / 30.0) % 12
    ingresses = []
    max_step = max(float(step_days), 1.0) * 8.0

    while jd < end_jd:
        if abs(spd) < 1e-5:
            jd += max(float(step_days), 1.0)
        else:
            if spd > 0:
                boundary = (prev_sign + 1) * 30.0
                dist = (boundary - lon) % 360.0
            else:
                boundary = prev_sign * 30.0
                dist = (lon - boundary) % 360.0
            if dist < 1e-4:
                dist = 30.0
            jd += max(0.25, min(max_step, 0.85 * dist / abs(spd)))
        if jd > end_jd:
            jd = end_jd
        lon, spd = sidereal_lon_speed(planet, jd)
        sign = int((lon % 360.0) / 30.0) % 12
        if sign != prev_sign:
            lo, hi = jd - max_step, jd
            from_sign = SIGNS[prev_sign]
            for _ in range(24):
                if hi - lo < 0.02:
                    break
                mid = (lo + hi) / 2.0
                mlon, _ = sidereal_lon_speed(planet, mid)
                if int((mlon % 360.0) / 30.0) % 12 == prev_sign:
                    lo = mid
                else:
                    hi = mid
            yy, mm, dd, _ = swe.revjul(hi)
            ingresses.append({
                "date": f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}",
                "from_sign": from_sign,
                "to_sign": SIGNS[sign],
                "longitude": round(lon, 6),
            })
            prev_sign = sign
        if jd >= end_jd:
            break

    return ingresses


# ═══════════════════════════════════════════
# DOUBLE TRANSIT (Jupiter + Saturn)
# ═══════════════════════════════════════════

def calc_double_transit(transit_positions, natal_chart):
    """
    Calculate Double Transit — houses aspected by BOTH Jupiter AND Saturn
    simultaneously. This is the primary Parashara timing technique.

    The houses where both Jupiter and Saturn have influence (occupation + aspect)
    are activated for major events.

    Args:
        transit_positions: dict from calc_transit_positions()
        natal_chart: BirthChart object

    Returns:
        dict with:
            jupiter_influences: set of houses Jupiter occupies or aspects
            saturn_influences: set of houses Saturn occupies or aspects
            double_transit_houses: set of houses influenced by BOTH
            activated_signs: signs of the double-transit houses
    """
    lagna_idx = natal_chart.lagna_index

    def get_influence_houses(planet):
        """Get all houses a transiting planet influences (occupation + aspects)."""
        t_pos = transit_positions.get(planet, {})
        if not t_pos or isinstance(t_pos, (float, int)):
            return set()

        t_sign_idx = t_pos.get("sign_index", 0)
        natal_house = sign_to_house(t_sign_idx, lagna_idx)

        houses = {natal_house}  # Occupation

        # 7th aspect (all planets)
        houses.add(house_counted_from(natal_house, 7))
        if planet in SPECIAL_ASPECTS:
            for offset in SPECIAL_ASPECTS[planet]:
                houses.add(house_counted_from(natal_house, offset))

        return houses

    jup_houses = get_influence_houses("Jupiter")
    sat_houses = get_influence_houses("Saturn")
    double_houses = jup_houses & sat_houses

    activated_signs = []
    for h in sorted(double_houses):
        activated_signs.append(house_to_sign(h, lagna_idx))

    return {
        "jupiter_influences": sorted(jup_houses),
        "saturn_influences": sorted(sat_houses),
        "double_transit_houses": sorted(double_houses),
        "activated_signs": activated_signs,
    }


# ═══════════════════════════════════════════
# BHRIGU BINDU TRANSIT CHECK
# ═══════════════════════════════════════════

def _bb_orb(planet, orb=None):
    """§10.4: Jupiter/Saturn 5°, others 2°. Explicit `orb` overrides both."""
    if orb is not None:
        return float(orb)
    return 5.0 if planet in ("Jupiter", "Saturn") else 2.0


def check_bb_transit(transit_positions, natal_bb_longitude, orb=None):
    """
    Check if any transiting planet is near the natal Bhrigu Bindu.

    BB transit activation: when a transiting planet crosses BB,
    major events related to BB's house/nakshatra are triggered.

    Args:
        transit_positions: dict from calc_transit_positions()
        natal_bb_longitude: BB longitude from natal chart
        orb: conjunction orb in degrees. None = §10.4 split (5° Ju/Sa, 2° rest).

    Returns:
        list of {planet, transit_long, separation, applying/separating}
    """
    activations = []

    for planet in PLANETS_9:
        t_pos = transit_positions.get(planet, {})
        if not t_pos or isinstance(t_pos, (float, int)):
            continue

        t_long = t_pos.get("longitude", 0)

        # Angular separation
        sep = abs(t_long - natal_bb_longitude)
        if sep > 180:
            sep = 360 - sep

        used_orb = _bb_orb(planet, orb)
        t_sign_idx = t_pos.get("sign_index")
        if t_sign_idx is None:
            t_sign_idx = int((t_long % 360.0) / 30.0) % 12
        bb_sign_idx = int((natal_bb_longitude % 360.0) / 30.0) % 12
        house_from = sign_to_house(bb_sign_idx, t_sign_idx)
        aspect_houses = [7] + list(SPECIAL_ASPECTS.get(planet, []))

        kind = None
        if sep <= used_orb:
            kind = "conjunction"
        elif house_from in aspect_houses:
            kind = f"aspect_{house_from}"

        if kind:
            spd = t_pos.get("speed")
            if spd is None:
                spd = 0.0
            signed = (natal_bb_longitude - t_long) % 360.0
            if signed > 180.0:
                signed -= 360.0
            if abs(spd) < 1e-6:
                status = "Stationary"
            elif (spd * signed) > 0:
                status = "Applying"
            else:
                status = "Separating"
            activations.append({
                "planet": planet,
                "kind": kind,
                "transit_longitude": round(t_long, 4),
                "bb_longitude": round(natal_bb_longitude, 4),
                "separation": round(sep, 4),
                "orb": used_orb,
                "status": status,
                "retrograde": t_pos.get("retrograde", False),
            })

    return activations


# ═══════════════════════════════════════════
# SAV TRANSIT SCORING
# ═══════════════════════════════════════════

def score_transit_ashtakavarga(transit_sign, planet, natal_chart):
    """
    Score a transit using Ashtakavarga.

    - SAV score of the transit sign: overall favorability
    - BAV score of the planet in that sign: planet-specific favorability

    Convention:
    - SAV >= 28 = favorable sign for transit
    - BAV >= 4 = favorable for that specific planet
    - SAV < 25 = unfavorable
    - BAV < 3 = planet struggles in that sign

    Args:
        transit_sign: sign name ("Aries", etc.)
        planet: transiting planet name
        natal_chart: BirthChart object

    Returns:
        dict with sav_score, bav_score, assessment
    """
    sign_idx = SIGN_INDEX.get(transit_sign, 0) if isinstance(transit_sign, str) else int(transit_sign)
    sav_score, bav_score = sav_bav_at_sign(natal_chart, planet, sign_idx)
    sav_score = sav_score or 0
    bav_score = bav_score or 0

    # Assessment
    if sav_score >= 28 and bav_score >= 4:
        assessment = "Highly Favorable"
    elif sav_score >= 28 or bav_score >= 4:
        assessment = "Favorable"
    elif sav_score < 25 and bav_score < 3:
        assessment = "Unfavorable"
    else:
        assessment = "Neutral"

    return {
        "transit_sign": transit_sign,
        "planet": planet,
        "sav_score": sav_score,
        "bav_score": bav_score,
        "assessment": assessment,
    }


# ═══════════════════════════════════════════
# GOCHARA (VEDHA) — Transit from Moon
# ═══════════════════════════════════════════

# Per-planet Vedha: favorable house -> obstructing house. rules.md §10.2
GOCHARA_VEDHA = {
    "Sun":     {3: 9, 6: 12, 10: 4, 11: 5},
    "Moon":    {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "Mars":    {3: 12, 6: 9, 11: 5},
    "Mercury": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    "Jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    "Venus":   {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 6, 12: 3},
    "Saturn":  {3: 12, 6: 9, 11: 5},
    "Rahu":    {3: 12, 6: 9, 11: 5},
    "Ketu":    {3: 12, 6: 9, 11: 5},
}

# Father-son pairs never obstruct each other. rules.md §10.2
VEDHA_EXEMPT_PAIRS = {
    ("Sun", "Saturn"), ("Saturn", "Sun"),
    ("Moon", "Mercury"), ("Mercury", "Moon"),
}

# Favorable transit houses from Moon (per planet). Rahu/Ketu = 3, 6, 11.
GOCHARA_FAVORABLE = {
    "Sun":     [3, 6, 10, 11],
    "Moon":    [1, 3, 6, 7, 10, 11],
    "Mars":    [3, 6, 11],
    "Mercury": [2, 4, 6, 8, 10, 11],
    "Jupiter": [2, 5, 7, 9, 11],
    "Venus":   [1, 2, 3, 4, 5, 8, 9, 11, 12],
    "Saturn":  [3, 6, 11],
    "Rahu":    [3, 6, 11],
    "Ketu":    [3, 6, 11],
}


def calc_gochara(transit_positions, natal_chart):
    """
    Calculate Gochara (transit results from Moon sign).

    For each transiting planet:
    1. Find which house it transits from natal Moon
    2. Check if that house is favorable or unfavorable
    3. Check for Vedha (obstruction by another planet)

    Args:
        transit_positions: dict from calc_transit_positions()
        natal_chart: BirthChart object

    Returns:
        dict of planet -> {house_from_moon, favorable, vedha, vedha_by}
    """
    moon_sign_idx = natal_chart.positions.get("Moon", {}).get("sign_index", 0)
    result = {}

    # First pass: find all transit houses from Moon
    transit_houses = {}
    for planet in PLANETS_9:
        t_pos = transit_positions.get(planet, {})
        if not t_pos or isinstance(t_pos, (float, int)):
            continue
        t_sign_idx = t_pos.get("sign_index", 0)
        house_from_moon = sign_to_house(t_sign_idx, moon_sign_idx)
        transit_houses[planet] = house_from_moon

    # Second pass: evaluate each transit
    for planet in PLANETS_9:
        if planet not in transit_houses:
            continue

        h = transit_houses[planet]
        favorable_houses = GOCHARA_FAVORABLE.get(planet, [])
        is_favorable = h in favorable_houses

        vedha_house = GOCHARA_VEDHA.get(planet, {}).get(h)
        vedha_by = []
        if vedha_house and is_favorable:
            for other_planet, other_h in transit_houses.items():
                if other_planet == planet or other_h != vedha_house:
                    continue
                if (planet, other_planet) in VEDHA_EXEMPT_PAIRS:
                    continue
                vedha_by.append(other_planet)

        result[planet] = {
            "house_from_moon": h,
            "favorable": is_favorable,
            "vedha_house": vedha_house,
            "vedha_by": vedha_by,
            "vedha_active": len(vedha_by) > 0,
            "net_effect": "Obstructed" if vedha_by else (
                "Favorable" if is_favorable else "Unfavorable"
            ),
        }

    return result


# ═══════════════════════════════════════════
# TRANSIT SNAPSHOT (convenience)
# ═══════════════════════════════════════════

def calc_full_transit_report(date, natal_chart, time="12:00:00", tz=None):
    """
    Transit report vs this natal. tz defaults to the native's birth timezone.
    """
    tz = tz or natal_chart.birth_data.get("tz") or "+00:00"
    bd = natal_chart.birth_data
    t_pos = natal_chart._ephe.get_planet_positions(
        date, time, tz, bd["lat"], bd["lon"]
    )

    t2n = calc_transit_to_natal(t_pos, natal_chart)
    dt = calc_double_transit(t_pos, natal_chart)
    gochara = calc_gochara(t_pos, natal_chart)

    # BB transit check
    bb_transit = []
    try:
        bb_long = natal_chart.special_points.get("bhrigu_bindu", {}).get("longitude", 0)
        if bb_long:
            bb_transit = check_bb_transit(t_pos, bb_long)
    except Exception:
        pass

    sat_long = t_pos.get("Saturn", {}).get("longitude", 0.0)
    moon_long = natal_chart.positions.get("Moon", {}).get("longitude", 0.0)
    sade = calc_sade_sati(moon_long, sat_long)

    return {
        "date": date,
        "transit_positions": t_pos,
        "transit_to_natal": t2n,
        "double_transit": dt,
        "gochara": gochara,
        "bb_transit": bb_transit,
        "sade_sati": sade,
    }


# ═══════════════════════════════════════════
# SADE-SATI / ASHTAMA SHANI / KANTAKA SHANI
# ═══════════════════════════════════════════

def calc_sade_sati(natal_moon_longitude, transit_saturn_longitude):
    """
    Sade-Sati: transiting Saturn within ±1 sign of natal Moon. rules.md §10.3.
    Chart-agnostic — pass this native's Moon and the query-date Saturn.
    """
    moon_idx = int((natal_moon_longitude % 360.0) / 30.0) % 12
    sat_idx = int((transit_saturn_longitude % 360.0) / 30.0) % 12
    from_moon = (sat_idx - moon_idx) % 12  # 0 = Moon sign, 11 = 12th from Moon

    rising = (moon_idx - 1) % 12
    peak = moon_idx
    setting = (moon_idx + 1) % 12

    if sat_idx == rising:
        active, phase = True, "RISING"
    elif sat_idx == peak:
        active, phase = True, "PEAK"
    elif sat_idx == setting:
        active, phase = True, "SETTING"
    else:
        active, phase = False, None

    return {
        "sade_sati": active,
        "phase": phase,
        "natal_moon_sign": SIGNS[moon_idx],
        "transit_saturn_sign": SIGNS[sat_idx],
        "houses_from_moon": from_moon + 1,
        "ashtama_shani": sat_idx == (moon_idx + 7) % 12,
        "kantaka_shani": sat_idx == (moon_idx + 3) % 12,
    }


# ═══════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════

def format_transit_to_natal(t2n):
    """Format transit-to-natal overlay as readable text."""
    lines = []
    lines.append("=== Transit to Natal ===\n")

    for planet in PLANETS_9:
        t = t2n.get(planet, {})
        if not t:
            continue
        retro = " (R)" if t.get("retrograde") else ""
        conj = ", ".join(t.get("conjuncts_natal", [])) or "—"
        asp = ", ".join(t.get("aspects_planets", [])) or "—"
        sav = t.get("sav_score", "?")
        bav = t.get("bav_score", "?")

        lines.append(
            f"  {planet:<10} {t['transit_sign']:<13} H{t['natal_house']:<3}{retro}"
            f"  Conj: {conj:<20} Asp: {asp:<20} SAV:{sav} BAV:{bav}"
        )

    return "\n".join(lines)


def format_gochara(gochara):
    """Format Gochara results as readable text."""
    lines = []
    lines.append("=== Gochara (from Moon) ===\n")

    for planet in PLANETS_9:
        g = gochara.get(planet, {})
        if not g:
            continue
        vedha_str = f" [VEDHA by {', '.join(g['vedha_by'])}]" if g.get("vedha_by") else ""
        lines.append(
            f"  {planet:<10} H{g['house_from_moon']:<3} "
            f"{g['net_effect']:<12}{vedha_str}"
        )

    return "\n".join(lines)
