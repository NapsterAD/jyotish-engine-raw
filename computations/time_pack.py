"""
time_pack.py — Dated raw calendars for AI timing: Varshaphala years,
monthly Gochara, transit-to-natal orbs, eclipses, Tara Bala years, BB hits.
Chart-agnostic. No named predictions.
"""

from datetime import datetime

import swisseph as swe

from ..core.constants import (
    SIGNS, PLANETS_9, NAKSHATRA_SPAN,
)
from .sensitive import nava_tara
from ..core.mapping import sign_to_house


def _slim_pos(pos):
    if not pos or not isinstance(pos, dict):
        return None
    return {
        "longitude": pos.get("longitude"),
        "sign": pos.get("sign"),
        "degree_in_sign": round(pos.get("degree_in_sign") or 0, 4),
        "nakshatra": pos.get("nakshatra"),
        "nakshatra_lord": pos.get("nakshatra_lord"),
        "pada": pos.get("pada"),
        "retrograde": pos.get("retrograde"),
        "speed": pos.get("speed"),
    }


def _natal_moon_nak_num(chart):
    return chart.positions["Moon"].get("nakshatra_num") or (
        min(int(chart.positions["Moon"]["longitude"] / NAKSHATRA_SPAN), 26) + 1
    )


def _orb(a, b):
    d = abs((a - b) % 360.0)
    return d if d <= 180.0 else 360.0 - d


def calc_varsha_years(chart, years):
    """Varshaphala facts for each year: lagna, muntha, varshesha, slim positions."""
    out = []
    for year in years:
        try:
            raw = chart.varshaphala(year)
        except Exception as exc:
            out.append({"year": year, "error": str(exc)})
            continue
        vc = raw.get("varsha_chart") or {}
        pos = vc.get("positions") or {}
        slim = {}
        for name in ["Lagna"] + list(PLANETS_9):
            slim[name] = _slim_pos(pos.get(name))
        yogas = []
        for y in raw.get("tajika_yogas") or []:
            yogas.append({
                "kind": y.get("yoga"),
                "faster": y.get("faster_planet"),
                "slower": y.get("slower_planet"),
                "aspect": y.get("aspect_type"),
                "separation": y.get("separation"),
            })
        out.append({
            "year": year,
            "age": vc.get("age"),
            "solar_return_date": vc.get("solar_return_date"),
            "solar_return_time_ut": vc.get("solar_return_time_ut"),
            "varsha_lagna": vc.get("varsha_lagna"),
            "muntha": vc.get("muntha"),
            "varshesha": raw.get("varshesha"),
            "positions": slim,
            "tajika_aspects": yogas,
        })
    return out


def calc_monthly_gochara(chart, start_date, months=36):
    """First-of-month noon (natal tz) transit overlay for `months` months.

    Single-body Swiss longitudes — no houses_ex / 9-planet dump per month.
    """
    from .transits import sidereal_lon_speed, slim_from_lon_speed, sav_bav_at_sign
    tz_hours = chart._ephe._parse_timezone(chart.birth_data["tz"])
    start = datetime.strptime(start_date, "%Y-%m-%d").replace(day=1)
    lagna_idx = chart.lagna_index
    natal_points = {
        n: chart.positions[n]["longitude"]
        for n in ["Lagna"] + list(PLANETS_9)
        if isinstance(chart.positions.get(n), dict)
    }
    natal_sign_of = {
        n: chart.positions[n]["sign"]
        for n in PLANETS_9
        if isinstance(chart.positions.get(n), dict)
    }
    bb = (chart.special_points.get("bhrigu_bindu") or {}).get("longitude")
    if bb is not None:
        natal_points["BhriguBindu"] = bb
    rows = []
    for i in range(months):
        month = (start.month - 1 + i) % 12 + 1
        year = start.year + (start.month - 1 + i) // 12
        date = f"{year:04d}-{month:02d}-01"
        jd = swe.julday(year, month, 1, 12.0 - float(tz_hours))
        slim_overlay = {}
        hits = []
        for planet in PLANETS_9:
            tlong, spd = sidereal_lon_speed(planet, jd)
            slim = slim_from_lon_speed(tlong, spd)
            t_sign_idx = slim["sign_index"]
            sav_score, bav_score = sav_bav_at_sign(chart, planet, t_sign_idx)
            conjuncts = [n for n, s in natal_sign_of.items() if s == slim["sign"]]
            for nname, nlong in natal_points.items():
                sep = _orb(tlong, nlong)
                if sep <= 5.0:
                    hits.append({
                        "transit": planet,
                        "natal": nname,
                        "orb": round(sep, 3),
                        "transit_long": round(tlong, 4),
                        "natal_long": round(nlong, 4),
                    })
            slim_overlay[planet] = {
                "sign": slim["sign"],
                "degree": round(slim["degree_in_sign"], 2),
                "nakshatra": slim["nakshatra"],
                "natal_house": sign_to_house(t_sign_idx, lagna_idx),
                "retrograde": slim["retrograde"],
                "conjuncts_natal": conjuncts,
                "sav_score": sav_score,
                "bav_score": bav_score,
            }
        rows.append({
            "date": date,
            "planets": slim_overlay,
            "degree_hits_orb5": hits,
        })
    return rows


def calc_eclipse_map(chart, start_year, years=5, natal_orb=5.0):
    """Upcoming solar/lunar eclipses and natal points within natal_orb."""
    natal = {
        n: chart.positions[n]["longitude"]
        for n in ["Lagna"] + list(PLANETS_9)
        if isinstance(chart.positions.get(n), dict)
    }
    bb = (chart.special_points.get("bhrigu_bindu") or {}).get("longitude")
    if bb is not None:
        natal["BhriguBindu"] = bb
    ul = (chart.arudhas.get("A12") or chart.arudhas.get("UL") or {})
    if isinstance(ul, dict) and ul.get("longitude") is not None:
        natal["UL"] = ul["longitude"]
    elif isinstance(ul, dict) and ul.get("sign"):
        natal["UL_sign"] = ul["sign"]

    tjd = swe.julday(start_year, 1, 1, 0)
    end = swe.julday(start_year + years, 12, 31, 0)
    events = []

    def _add(kind, jd):
        y, m, d, ut = swe.revjul(jd)
        flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_MOSEPH
        sun = swe.calc_ut(jd, swe.SUN, flags)[0][0]
        moon = swe.calc_ut(jd, swe.MOON, flags)[0][0]
        body = sun if kind.startswith("solar") else moon
        hits = []
        for nname, nlong in natal.items():
            if not isinstance(nlong, (int, float)):
                continue
            sep = _orb(body, nlong)
            if sep <= natal_orb:
                hits.append({"natal": nname, "orb": round(sep, 3)})
        events.append({
            "kind": kind,
            "date": f" {int(y):04d}-{int(m):02d}-{int(d):02d}".strip(),
            "jd": round(jd, 6),
            "sun_long": round(sun % 360.0, 4),
            "moon_long": round(moon % 360.0, 4),
            "natal_hits_orb5": hits,
        })

    jd = tjd
    for _ in range(40):
        try:
            ret, tret = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH, 0, False)
        except TypeError:
            try:
                ret, tret = swe.sol_eclipse_when_glob(jd)
            except Exception:
                break
        except Exception:
            break
        if not tret:
            break
        maxjd = tret[0] if isinstance(tret, (list, tuple)) else tret
        if maxjd <= 0 or maxjd > end:
            break
        _add("solar", maxjd)
        jd = maxjd + 10
        if jd > end:
            break

    jd = tjd
    for _ in range(40):
        try:
            ret, tret = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, False)
        except TypeError:
            try:
                ret, tret = swe.lun_eclipse_when(jd)
            except Exception:
                break
        except Exception:
            break
        if not tret:
            break
        maxjd = tret[0] if isinstance(tret, (list, tuple)) else tret
        if maxjd <= 0 or maxjd > end:
            break
        _add("lunar", maxjd)
        jd = maxjd + 10
        if jd > end:
            break

    events.sort(key=lambda e: e["jd"])
    return events


def calc_tara_year_grid(chart, start_year, end_year):
    """Each Jan-1, tara of transiting grahas vs natal Moon nakshatra."""
    from .transits import sidereal_lon_speed, slim_from_lon_speed
    tz_hours = chart._ephe._parse_timezone(chart.birth_data["tz"])
    janma = _natal_moon_nak_num(chart)
    rows = []
    for year in range(start_year, end_year + 1):
        date = f"{year:04d}-01-01"
        jd = swe.julday(year, 1, 1, 12.0 - float(tz_hours))
        planets = {}
        for p in PLANETS_9:
            tlong, spd = sidereal_lon_speed(p, jd)
            slim = slim_from_lon_speed(tlong, spd)
            nnum = slim["nakshatra_num"]
            tara = nava_tara(janma, nnum)
            planets[p] = {
                "sign": slim["sign"],
                "nakshatra": slim["nakshatra"],
                "nakshatra_num": nnum,
                "tara": tara["name"],
                "tara_index": tara["index"],
                "tara_weight": tara["weight"],
                "damage": tara["name"] in ("Vipat", "Pratyak", "Naidhana"),
            }
        rows.append({"date": date, "planets": planets})
    return {"janma_nakshatra_num": janma, "years": rows}


def calc_bb_hit_windows(chart, start_date, days=365 * 3, orb=1.0):
    """
    Days when Sun/Moon/Jupiter/Saturn are within `orb` of natal Bhrigu Bindu.
    Moon scanned daily; slow bodies every 3 days.
    """
    bb = (chart.special_points.get("bhrigu_bindu") or {}).get("longitude")
    if bb is None:
        return {"error": "no Bhrigu Bindu"}
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_MOSEPH
    start = datetime.strptime(start_date, "%Y-%m-%d")
    tz = chart.positions.get("_tz_offset") or 0.0
    # JD at noon UT approx from civil date in natal tz
    y, m, d = start.year, start.month, start.day
    jd0 = swe.julday(y, m, d, 12.0 - float(tz))
    bodies = {"Sun": swe.SUN, "Moon": swe.MOON, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN}
    hits = {name: [] for name in bodies}
    prev_moon = None
    for i in range(int(days)):
        jd = jd0 + i
        moon = swe.calc_ut(jd, swe.MOON, flags)[0][0]
        sep = _orb(moon, bb)
        crossed = False
        if prev_moon is not None:
            motion = (moon - prev_moon) % 360.0
            if motion < 20.0:
                from_bb = (bb - prev_moon) % 360.0
                crossed = 0.0 <= from_bb <= motion
        if sep <= orb or crossed:
            y2, m2, d2, _ = swe.revjul(jd)
            hits["Moon"].append({
                "date": f"{int(y2):04d}-{int(m2):02d}-{int(d2):02d}",
                "orb": round(min(sep, 0.0 if crossed else sep), 3),
            })
        prev_moon = moon
        if i % 3 == 0:
            for name, sid in bodies.items():
                if name == "Moon":
                    continue
                long = swe.calc_ut(jd, sid, flags)[0][0]
                sep = _orb(long, bb)
                if sep <= orb:
                    y2, m2, d2, _ = swe.revjul(jd)
                    hits[name].append({
                        "date": f"{int(y2):04d}-{int(m2):02d}-{int(d2):02d}",
                        "orb": round(sep, 3),
                    })
    # Collapse consecutive Moon dates to windows
    def collapse(lst):
        if not lst:
            return []
        windows = []
        run_start = lst[0]["date"]
        run_end = lst[0]["date"]
        best = lst[0]["orb"]
        prev = datetime.strptime(lst[0]["date"], "%Y-%m-%d")
        for row in lst[1:]:
            cur = datetime.strptime(row["date"], "%Y-%m-%d")
            if (cur - prev).days <= 2:
                run_end = row["date"]
                best = min(best, row["orb"])
            else:
                windows.append({"start": run_start, "end": run_end, "min_orb": best})
                run_start = run_end = row["date"]
                best = row["orb"]
            prev = cur
        windows.append({"start": run_start, "end": run_end, "min_orb": best})
        return windows

    return {
        "bhrigu_bindu_longitude": round(bb, 6),
        "orb": orb,
        "windows": {k: collapse(v) for k, v in hits.items()},
        "hit_counts": {k: len(v) for k, v in hits.items()},
    }


def calc_bav_peak_signs(chart):
    """Top-3 BAV signs per graha (BAV is per-sign, not per-degree)."""
    bav = (chart.ashtakavarga or {}).get("bav") or {}
    out = {}
    for planet, row in bav.items():
        if not isinstance(row, list) or len(row) < 12:
            continue
        ranked = sorted(
            ((SIGNS[i], int(row[i])) for i in range(12)),
            key=lambda x: -x[1],
        )
        out[planet] = {
            "by_sign": {SIGNS[i]: int(row[i]) for i in range(12)},
            "top3": [{"sign": s, "bindus": n} for s, n in ranked[:3]],
            "bottom3": [{"sign": s, "bindus": n} for s, n in ranked[-3:]],
        }
    return out


def calc_time_pack(chart, from_date=None, months=36, tara_years=20, eclipse_years=5):
    if from_date is None:
        from_date = datetime.now().strftime("%Y-%m-%d")
    start = datetime.strptime(from_date, "%Y-%m-%d")
    year0 = start.year
    varsha_years = list(range(year0, year0 + 5))
    return {
        "from_date": from_date,
        "varshaphala": calc_varsha_years(chart, varsha_years),
        "monthly_gochara": calc_monthly_gochara(chart, from_date, months=months),
        "eclipses": calc_eclipse_map(chart, year0, years=eclipse_years),
        "tara_bala_years": calc_tara_year_grid(chart, year0, year0 + tara_years - 1),
        "bhrigu_bindu_windows": calc_bb_hit_windows(chart, from_date, days=months * 31),
        "bav_peak_signs": calc_bav_peak_signs(chart),
    }
