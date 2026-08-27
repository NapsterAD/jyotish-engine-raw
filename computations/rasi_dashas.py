"""
rasi_dashas.py — Remaining dasha systems from rules.md §4.
All take this native's chart (or moon/lagna longitudes). Chart-agnostic.
"""

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, SIGN_MODALITY,
    NAKSHATRAS, NAKSHATRA_SPAN,
    VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS, VIMSHOTTARI_TOTAL,
    PLANETS_7, PLANETS_9,
)
from .dashas import (
    SIDEREAL_YEAR_DAYS, _jd_to_date_str, calc_vimshottari, _vimshottari_balance,
)
from ..core.mapping import house_to_sign_index, sign_to_house


def _nak_num(moon_long):
    return min(int((moon_long % 360.0) / NAKSHATRA_SPAN), 26) + 1


def _sign_dasha_lord(sign_idx, positions):
    sign = SIGNS[sign_idx]
    lord = SIGN_LORDS[sign]
    if sign == "Scorpio" and positions.get("Mars", {}).get("sign") == "Scorpio":
        return "Ketu"
    if sign == "Aquarius" and positions.get("Saturn", {}).get("sign") == "Aquarius":
        return "Rahu"
    return lord


def jaimini_sign_years(sign_idx, positions):
    """Years for a rasi dasha sign. rules.md §4.3. Own sign = 12."""
    lord = _sign_dasha_lord(sign_idx, positions)
    lord_pos = positions.get(lord, {})
    if not isinstance(lord_pos, dict):
        return 1
    lord_idx = lord_pos.get("sign_index", 0)
    odd = (sign_idx % 2 == 0)  # Aries=0 odd
    if odd:
        house_count = sign_to_house(lord_idx, sign_idx)
    else:
        house_count = sign_to_house(sign_idx, lord_idx)
    raw = house_count - 1
    return 12 if raw == 0 else raw


def _rasi_periods(start_idx, sequence, positions, birth_jd, years_fn=None):
    years_fn = years_fn or (lambda i: jaimini_sign_years(i, positions))
    periods = []
    current = birth_jd
    for sign_idx in sequence:
        years = years_fn(sign_idx)
        end = current + years * SIDEREAL_YEAR_DAYS
        periods.append({
            "lord": SIGNS[sign_idx],
            "sign_index": sign_idx,
            "level": "MD",
            "start_jd": current,
            "end_jd": end,
            "start_date": _jd_to_date_str(current),
            "end_date": _jd_to_date_str(end),
            "duration_years": years,
        })
        current = end
    return periods


def _fwd_back_sequence(start_idx, forward, n=12):
    step = 1 if forward else -1
    return [(start_idx + step * i) % 12 for i in range(n)]


def calc_chara_dasha(chart):
    """Jaimini Chara Dasha. Start = Lagna. rules.md §4.3."""
    start = chart.lagna_index
    forward = (start % 2 == 0)
    seq = _fwd_back_sequence(start, forward)
    return {
        "system": "Chara",
        "start_sign": SIGNS[start],
        "direction": "forward" if forward else "backward",
        "periods": _rasi_periods(start, seq, chart.positions, chart.positions["_jd"]),
    }


def _kendra_strength(chart, house):
    planets = chart.get_planets_in_house(house, "rashi")
    score = len(planets)
    for p in planets:
        if chart.rashi_chart.get(p, {}).get("dignity") == "Exalted":
            score += 2
    return score


def calc_narayana_dasha(chart):
    """Narayana Dasha: start from strongest kendra (D-1 = Lagna fallback). §4.4."""
    best_h, best_s = 1, -1
    for h in (1, 4, 7, 10):
        s = _kendra_strength(chart, h)
        if s > best_s:
            best_s, best_h = s, h
    start = house_to_sign_index(best_h, chart.lagna_index)
    if best_s == 0:
        start = chart.lagna_index
    forward = (start % 2 == 0)
    seq = _fwd_back_sequence(start, forward)
    return {
        "system": "Narayana",
        "start_sign": SIGNS[start],
        "periods": _rasi_periods(start, seq, chart.positions, chart.positions["_jd"]),
    }


def calc_mandook_dasha(chart):
    """Mandook (frog-jump) dasha. §4.5."""
    s1, s7 = _kendra_strength(chart, 1), _kendra_strength(chart, 7)
    start_h = 1 if s1 >= s7 else 7
    start = house_to_sign_index(start_h, chart.lagna_index)
    odd = start % 2 == 0
    if odd:
        hops = [1, 4, 7, 10, 2, 5, 8, 11, 3, 6, 9, 12]
    else:
        hops = [1, 10, 7, 4, 12, 9, 6, 3, 11, 8, 5, 2]
    seq = [((start + h - 1) % 12) for h in hops]
    return {
        "system": "Mandook",
        "start_sign": SIGNS[start],
        "periods": _rasi_periods(start, seq, chart.positions, chart.positions["_jd"]),
    }


def calc_sudasa(chart):
    """Sudasa from Sree Lagna. §4.7."""
    sl = chart.special_lagnas.get("sree_lagna") or chart.special_lagnas.get("Sree")
    if isinstance(sl, dict):
        sl_long = sl.get("longitude", chart.positions["Lagna"]["longitude"])
    elif isinstance(sl, (int, float)):
        sl_long = float(sl)
    else:
        moon = chart.positions["Moon"]["longitude"]
        asc = chart.positions["Lagna"]["longitude"]
        frac = (moon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
        sl_long = (asc + frac * 360.0) % 360.0
    start = int(sl_long / 30) % 12
    forward = (start % 2 == 0)
    seq = _fwd_back_sequence(start, forward)
    return {
        "system": "Sudasa",
        "start_sign": SIGNS[start],
        "sree_longitude": round(sl_long, 4),
        "periods": _rasi_periods(start, seq, chart.positions, chart.positions["_jd"]),
    }


def calc_lagna_kendradi(chart):
    """Lagna Kendradi Rasi Dasa. §4.12."""
    start = chart.lagna_index
    odd = start % 2 == 0
    if odd:
        groups = [[1, 4, 7, 10], [2, 5, 8, 11], [3, 6, 9, 12]]
    else:
        groups = [[1, 10, 7, 4], [12, 9, 6, 3], [11, 8, 5, 2]]
    seq = [((start + h - 1) % 12) for g in groups for h in g]
    return {
        "system": "Lagna Kendradi",
        "start_sign": SIGNS[start],
        "periods": _rasi_periods(start, seq, chart.positions, chart.positions["_jd"]),
    }


def calc_drigdasa(chart):
    """Drigdasa from 9th, then signs that Jaimini-aspect it. §4.13."""
    from .graha_state import jaimini_aspect_signs
    seq = []
    seen = set()
    for house in range(9, 21):  # 9..12 then 1..8
        h = ((house - 1) % 12) + 1
        sidx = house_to_sign_index(h, chart.lagna_index)
        block = [sidx] + [SIGN_INDEX[s] for s in jaimini_aspect_signs(SIGNS[sidx])]
        if sidx % 2 == 1:
            block = [block[0]] + list(reversed(block[1:]))
        for i in block:
            if i not in seen:
                seen.add(i)
                seq.append(i)
    return {
        "system": "Drigdasa",
        "start_sign": SIGNS[seq[0]] if seq else SIGNS[chart.lagna_index],
        "periods": _rasi_periods(seq[0] if seq else chart.lagna_index, seq,
                                 chart.positions, chart.positions["_jd"]),
    }


def calc_shoola_dasha(chart):
    """Shoola Dasa: 9 years per sign. §4.14."""
    s1, s7 = _kendra_strength(chart, 1), _kendra_strength(chart, 7)
    start_h = 1 if s1 >= s7 else 7
    start = house_to_sign_index(start_h, chart.lagna_index)
    forward = (start % 2 == 0)
    seq = _fwd_back_sequence(start, forward)
    return {
        "system": "Shoola",
        "start_sign": SIGNS[start],
        "periods": _rasi_periods(
            start, seq, chart.positions, chart.positions["_jd"],
            years_fn=lambda i: 9,
        ),
    }


def calc_niryana_shoola(chart):
    """Niryana Shoola: 7/8/9 years by modality; start strongest of 2nd/7th/8th. §4.15."""
    scores = {h: _kendra_strength(chart, h) for h in (2, 7, 8)}
    start_h = max((2, 7, 8), key=lambda h: (scores[h], -h))
    start = house_to_sign_index(start_h, chart.lagna_index)
    forward = (start % 2 == 0)
    seq = _fwd_back_sequence(start, forward)
    years_map = {"Movable": 7, "Fixed": 8, "Dual": 9}
    return {
        "system": "Niryana Shoola",
        "start_sign": SIGNS[start],
        "start_house": start_h,
        "house_scores": scores,
        "direction": "forward" if forward else "backward",
        "periods": _rasi_periods(
            start, seq, chart.positions, chart.positions["_jd"],
            years_fn=lambda i: years_map[SIGN_MODALITY[SIGNS[i]]],
        ),
    }


# ── Nakshatra-conditional ──────────────────────────────────────

_SHASHTI_GROUPS = [
    ((1, 2, 3), "Jupiter", 10),
    ((4, 5, 6), "Sun", 10),
    ((7, 8, 9), "Mars", 10),
    ((10, 11, 12), "Moon", 6),
    ((13, 14, 15), "Mercury", 6),
    ((16, 17, 18), "Venus", 6),
    ((19, 20, 21), "Saturn", 6),
    ((22, 23, 24, 25, 26, 27), "Rahu", 6),
]

_ASHTOTTARI_GROUPS = [
    ((6, 7, 8, 9), "Sun", 6),
    ((10, 11, 12), "Moon", 15),
    ((13, 14, 15, 16), "Mars", 8),
    ((17, 18, 19), "Mercury", 17),
    ((20, 21, 22), "Saturn", 10),
    ((23, 24, 25), "Jupiter", 19),
    ((26, 27, 1, 2), "Rahu", 12),
    ((3, 4, 5), "Venus", 21),
]


def _group_balance(moon_long, groups):
    n = _nak_num(moon_long)
    degree_in = (moon_long % 360.0) % NAKSHATRA_SPAN
    for members, lord, years in groups:
        if n in members:
            idx = members.index(n)
            total_arc = len(members) * NAKSHATRA_SPAN
            elapsed = idx * NAKSHATRA_SPAN + degree_in
            remaining = 1.0 - elapsed / total_arc
            return lord, years * remaining, groups
    # fallback first group
    members, lord, years = groups[0]
    return lord, years, groups


def _planet_cycle_periods(start_lord, order_years, birth_jd, balance_years, cycle_name):
    lords = [ow[0] for ow in order_years]
    years_map = dict(order_years)
    idx = lords.index(start_lord)
    periods = []
    current = birth_jd
    for i in range(len(lords)):
        lord = lords[(idx + i) % len(lords)]
        full = years_map[lord]
        years = balance_years if i == 0 else full
        end = current + years * SIDEREAL_YEAR_DAYS
        periods.append({
            "lord": lord,
            "level": "MD",
            "start_jd": current,
            "end_jd": end,
            "start_date": _jd_to_date_str(current),
            "end_date": _jd_to_date_str(end),
            "duration_years": round(years, 4),
            "full_years": full,
        })
        current = end
    return periods


def calc_shashti_hayani(chart):
    """60-year dasha; applicable when Sun is in Lagna. §4.6."""
    applicable = _house_of_safe(chart, "Sun") == 1
    moon = chart.positions["Moon"]["longitude"]
    lord, bal, groups = _group_balance(moon, _SHASHTI_GROUPS)
    order = [(g[1], g[2]) for g in groups]
    return {
        "system": "Shashti-Hayani",
        "applicable": applicable,
        "periods": _planet_cycle_periods(lord, order, chart.positions["_jd"], bal, "SH"),
    }


def calc_ashtottari(chart):
    """108-year Ashtottari. §4.9."""
    rahu_h = _house_of_safe(chart, "Rahu")
    lagna_lord = chart.lordships.get(1)
    ll_h = _house_of_safe(chart, lagna_lord) if lagna_lord else 0
    from_ll = ((rahu_h - ll_h) % 12) + 1 if ll_h else rahu_h
    ss = chart.sunrise_sunset or {}
    is_day = bool(ss.get("is_day_birth"))
    elong = (chart.positions["Moon"]["longitude"] - chart.positions["Sun"]["longitude"]) % 360
    krishna = elong >= 180.0
    applicable = (
        from_ll in {1, 4, 5, 7, 9, 10}
        or (krishna and is_day)
        or ((not krishna) and (not is_day))
    )
    moon = chart.positions["Moon"]["longitude"]
    lord, bal, groups = _group_balance(moon, _ASHTOTTARI_GROUPS)
    order = [(g[1], g[2]) for g in groups]
    return {
        "system": "Ashtottari",
        "applicable": applicable,
        "periods": _planet_cycle_periods(lord, order, chart.positions["_jd"], bal, "AS"),
    }


def calc_tribhagi(chart):
    """Vimshottari compressed to 40-year cycle. §4.8."""
    moon = chart.positions["Moon"]["longitude"]
    birth_jd = chart.positions["_jd"]
    lord, bal, _, _ = _vimshottari_balance(moon)
    # reuse vimshottari then scale displayed years: actual JD span is 1/3
    # Implement as own cycle with years/3
    order = [(p, VIMSHOTTARI_YEARS[p] / 3.0) for p in VIMSHOTTARI_ORDER]
    idx = VIMSHOTTARI_ORDER.index(lord)
    remaining_frac = bal / VIMSHOTTARI_YEARS[lord]
    tri_bal = remaining_frac * (VIMSHOTTARI_YEARS[lord] / 3.0)
    return {
        "system": "Tribhagi",
        "periods": _planet_cycle_periods(lord, order, birth_jd, tri_bal, "TRI"),
    }


# Kalachakra — savya/apasavya 9-sign wheels + paramayus years. §4.10
KCD_YEARS = {
    0: 7, 1: 16, 2: 9, 3: 21, 4: 5, 5: 9,
    6: 16, 7: 7, 8: 10, 9: 4, 10: 4, 11: 10,
}
# §4.10.1 Savya (direct): Ashwini–Ashlesha, Chitra–Mula, Purva Bhadrapada–Revati.
# Apasavya (reverse): Magha–Hasta, Purva Ashadha–Shatabhisha, plus Abhijit.
# Shravana (22) and Abhijit are Apasavya — they are not in SAVYA_NAK.
SAVYA_NAK = {1, 2, 3, 4, 5, 6, 7, 8, 9, 14, 15, 16, 17, 18, 19, 25, 26, 27}
APASAVYA_NAK = {10, 11, 12, 13, 20, 21, 22, 23, 24}
# Abhijit intercalary: 6°40′ Capricorn → 10°53′20″ Capricorn (Apasavya).
ABHIJIT_START = 276.0 + 40.0 / 60.0
ABHIJIT_END = 280.0 + 53.0 / 60.0 + 20.0 / 3600.0
SAVYA_WHEELS = {
    1: [0, 1, 2, 3, 4, 5, 6, 7, 8],
    2: [9, 10, 11, 7, 6, 5, 3, 4, 2],
    3: [1, 0, 11, 10, 9, 8, 7, 6, 5],
    4: [4, 3, 2, 1, 0, 11, 10, 9, 8],
}


def _in_abhijit(moon_long):
    lam = moon_long % 360.0
    return ABHIJIT_START <= lam < ABHIJIT_END


def _kalachakra_gati(prev_idx, next_idx):
    """
    Classify the sign-to-sign jump. rules.md §4.10.4:
    Manduki (frog), Markati (monkey / backward adjacent), Simhavalokana (lion's glance).
    """
    pair = (prev_idx, next_idx)
    # Spec examples: Sg→Ar, Pi→Sc
    if pair in {(8, 0), (0, 8), (11, 7), (7, 11)}:
        return "Simhavalokana"
    # Spec examples: Cancer→Leo, Virgo→Cancer
    if pair in {(3, 4), (4, 3), (5, 3), (3, 5)}:
        return "Manduki"
    step = (next_idx - prev_idx) % 12
    back = (prev_idx - next_idx) % 12
    if step == 1:
        return "normal"
    if back == 1:
        return "Markati"
    if step == 4 or back == 4:
        return "Simhavalokana"
    if step in (2, 3) or back in (2, 3):
        return "Manduki"
    if back > 1:
        return "Markati"
    return "Manduki"


def calc_kalachakra(chart):
    moon = chart.positions["Moon"]["longitude"]
    n = _nak_num(moon)
    abhijit = _in_abhijit(moon)
    degree_in = (moon % 360.0) % NAKSHATRA_SPAN
    pada = min(int(degree_in / (NAKSHATRA_SPAN / 4.0)) + 1, 4)
    # Abhijit is Apasavya (§4.10.1); otherwise the 27-nakshatra Savya set.
    savya = (n in SAVYA_NAK) and not abhijit
    wheel = list(SAVYA_WHEELS[pada])
    if not savya:
        wheel = list(reversed(wheel))
    deha, jiva = wheel[0], wheel[-1]
    pada_frac_remaining = 1.0 - (degree_in % (NAKSHATRA_SPAN / 4.0)) / (NAKSHATRA_SPAN / 4.0)
    birth_jd = chart.positions["_jd"]
    periods = []
    current = birth_jd
    special_gatis = []
    for i, sidx in enumerate(wheel):
        full = KCD_YEARS[sidx]
        years = full * pada_frac_remaining if i == 0 else full
        end = current + years * SIDEREAL_YEAR_DAYS
        gati = None
        if i > 0:
            gati = _kalachakra_gati(wheel[i - 1], sidx)
            if gati != "normal":
                special_gatis.append({
                    "from": SIGNS[wheel[i - 1]],
                    "to": SIGNS[sidx],
                    "gati": gati,
                    "at": _jd_to_date_str(current),
                })
        periods.append({
            "lord": SIGNS[sidx],
            "sign_index": sidx,
            "level": "MD",
            "start_jd": current,
            "end_jd": end,
            "start_date": _jd_to_date_str(current),
            "end_date": _jd_to_date_str(end),
            "duration_years": round(years, 4),
            "full_years": full,
            "gati": gati,
        })
        current = end
    return {
        "system": "Kalachakra",
        "savya": savya,
        "group": "Savya" if savya else "Apasavya",
        "abhijit": abhijit,
        "nakshatra_num": n,
        "pada": pada,
        "deha": SIGNS[deha],
        "jiva": SIGNS[jiva],
        "special_gatis": special_gatis,
        "periods": periods,
    }


def calc_moola_dasa(chart):
    """Moola / D-60 karma dasha: kendra occupants by strength. §4.11."""
    moon_h = chart.rashi_chart.get("Moon", {}).get("house_rashi", 0)
    start_from_moon = moon_h in {1, 4, 7, 10}
    origin = moon_h if start_from_moon else 1

    def group(houses):
        found = []
        for h in houses:
            actual = ((origin + h - 2) % 12) + 1 if start_from_moon else h
            for p in chart.get_planets_in_house(actual, "rashi"):
                if p not in found:
                    found.append(p)
        return found

    order = group([1, 4, 7, 10]) + group([2, 5, 8, 11]) + group([3, 6, 9, 12])
    for p in PLANETS_9:
        if p not in order:
            order.append(p)
    # dignity coefficient
    coef = {
        "Exalted": 1.0, "Moolatrikona": 0.9, "Own Sign": 0.85,
        "Friendly": 0.7, "Neutral": 0.5, "Enemy": 0.35, "Debilitated": 0.25,
    }
    birth_jd = chart.positions["_jd"]
    periods = []
    current = birth_jd
    for p in order:
        base = VIMSHOTTARI_YEARS.get(p, 7)
        dig = chart.rashi_chart.get(p, {}).get("dignity", "Neutral")
        years = base * coef.get(dig, 0.5)
        end = current + years * SIDEREAL_YEAR_DAYS
        periods.append({
            "lord": p,
            "level": "MD",
            "start_jd": current,
            "end_jd": end,
            "start_date": _jd_to_date_str(current),
            "end_date": _jd_to_date_str(end),
            "duration_years": round(years, 4),
            "dignity": dig,
        })
        current = end
    return {"system": "Moola", "periods": periods}


def dasha_lord_strength(chart, lord):
    """§4.16 checklist for a dasha lord (planet or skip for rasi)."""
    if lord not in chart.rashi_chart:
        # rasi dasha: use sign lord
        if lord in SIGN_INDEX:
            planet = SIGN_LORDS[lord]
        else:
            return {"lord": lord, "flag": "NEUTRAL"}
    else:
        planet = lord
    rc = chart.rashi_chart.get(planet, {})
    dignity = rc.get("dignity", "Neutral")
    flag = {
        "Own Sign": "STRONG", "Exalted": "VERY_STRONG", "Moolatrikona": "STRONG",
        "Friendly": "MODERATE", "Neutral": "NEUTRAL", "Enemy": "WEAK",
        "Debilitated": "VERY_WEAK",
    }.get(dignity, "NEUTRAL")
    notes = []
    try:
        if chart.combustion.get(planet, {}).get("is_combust"):
            flag = "WEAKENED"
            notes.append("combust")
    except Exception:
        pass
    if chart.positions.get(planet, {}).get("retrograde"):
        notes.append("retrograde")
        if flag not in ("VERY_WEAK", "WEAKENED"):
            flag = "MODIFIED_STRENGTH"
    return {"lord": planet, "dignity": dignity, "flag": flag, "notes": notes}


def _house_of_safe(chart, planet):
    return chart.rashi_chart.get(planet, {}).get("house_rashi", 0)


def calc_all_dasha_systems(chart):
    """Every §4 system for this native."""
    return {
        "vimshottari": chart.dashas,
        "yogini": chart.yogini_dasha,
        "tribhagi": calc_tribhagi(chart),
        "chara": calc_chara_dasha(chart),
        "narayana": calc_narayana_dasha(chart),
        "mandook": calc_mandook_dasha(chart),
        "shashti_hayani": calc_shashti_hayani(chart),
        "sudasa": calc_sudasa(chart),
        "ashtottari": calc_ashtottari(chart),
        "kalachakra": calc_kalachakra(chart),
        "moola": calc_moola_dasa(chart),
        "lagna_kendradi": calc_lagna_kendradi(chart),
        "drigdasa": calc_drigdasa(chart),
        "shoola": calc_shoola_dasha(chart),
        "niryana_shoola": calc_niryana_shoola(chart),
    }
