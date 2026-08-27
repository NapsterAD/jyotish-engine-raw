"""
raw_layers.py — Extra raw-number layers for AI (no interpretation).
Vargas with degrees, nakshatra depth, 10y ingresses, PD trees, drik matrix.
"""

from datetime import datetime

import swisseph as swe

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, NAKSHATRAS, NAKSHATRA_SPAN, PADA_SPAN,
    PLANETS_7, PLANETS_9, SPECIAL_ASPECTS,
    YOGINI_NAMES, YOGINI_PLANETS, YOGINI_YEARS, YOGINI_TOTAL,
)
from .vargas import VARGA_FUNCTIONS
from .kp import kp_chain
from .shadbala import _drishti_pinda
from .transits import find_sign_ingress
from .dashas import _jd_to_date_str
from .matching import NADI_TABLE, YONI_TABLE, GANA_TABLE
from ..core.mapping import sign_to_house, house_to_sign, house_counted_from


VARGA_PARTS = {
    "D1": 1, "D2": 2, "D3": 3, "D4": 4, "D7": 7, "D9": 9, "D10": 10,
    "D12": 12, "D16": 16, "D20": 20, "D24": 24, "D27": 27,
    "D40": 40, "D45": 45, "D60": 60,
}

HOUSE_KARAKA = {
    1: "Sun", 2: "Jupiter", 3: "Mars", 4: "Moon", 5: "Jupiter",
    6: "Mars", 7: "Venus", 8: "Saturn", 9: "Jupiter", 10: "Sun",
    11: "Jupiter", 12: "Saturn",
}


def _nak_pack(lam):
    lam = lam % 360.0
    nak_idx = min(int(lam / NAKSHATRA_SPAN), 26)
    nak = NAKSHATRAS[nak_idx]
    into = lam - nak_idx * NAKSHATRA_SPAN
    pada = min(int(into / PADA_SPAN) + 1, 4)
    return {
        "nakshatra": nak["name"],
        "nakshatra_num": nak["num"],
        "lord": nak["lord"],
        "deity": nak.get("deity"),
        "pada": pada,
        "degree_into": round(into, 6),
        "span": NAKSHATRA_SPAN,
        "elapsed_pct": round(into / NAKSHATRA_SPAN * 100.0, 4),
        "remaining_pct": round((1.0 - into / NAKSHATRA_SPAN) * 100.0, 4),
        "start_long": round(nak_idx * NAKSHATRA_SPAN, 6),
        "end_long": round((nak_idx + 1) * NAKSHATRA_SPAN, 6),
        "nadi": {1: "Aadi", 2: "Madhya", 3: "Antya"}.get(NADI_TABLE.get(nak["num"])),
        "yoni": YONI_TABLE.get(nak["num"]),
        "gana": {1: "Deva", 2: "Manushya", 3: "Rakshasa"}.get(GANA_TABLE.get(nak["num"])),
    }


def _body_brief(chart, planet):
    pos = chart.positions.get(planet) or {}
    if not isinstance(pos, dict):
        return None
    rc = chart.rashi_chart.get(planet) or {}
    return {
        "sign": pos.get("sign"),
        "dms": pos.get("dms"),
        "house": rc.get("house_rashi"),
        "dignity": rc.get("dignity"),
        "retrograde": pos.get("retrograde"),
        "speed": pos.get("speed"),
    }


def calc_tropical_sidereal(chart):
    aya = chart.positions.get("_ayanamsha") or 0.0
    out = {"ayanamsha": aya, "jd": chart.positions.get("_jd"), "bodies": {}}
    for name in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(name)
        if not pos or not isinstance(pos, dict):
            continue
        sid = pos["longitude"]
        trop = (sid + aya) % 360.0
        out["bodies"][name] = {
            "sidereal": round(sid, 6),
            "tropical": round(trop, 6),
            "sign": pos.get("sign"),
            "degree_in_sign": pos.get("degree_in_sign"),
            "latitude": pos.get("latitude"),
            "speed": pos.get("speed"),
        }
    return out


def calc_nakshatra_layers(chart):
    janma = chart.positions["Moon"].get("nakshatra_num") or (
        min(int(chart.positions["Moon"]["longitude"] / NAKSHATRA_SPAN), 26) + 1
    )
    out = {}
    for name in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(name)
        if not pos or not isinstance(pos, dict):
            continue
        lam = pos["longitude"]
        nak = _nak_pack(lam)
        ch = kp_chain(lam)
        lords = {}
        for key, lord in (
            ("star", ch["star_lord"]),
            ("sub", ch["sub_lord"]),
            ("ssl", ch["sub_sub_lord"]),
            ("sssl", ch["sssl_lord"]),
        ):
            lords[key] = {"planet": lord, "placement": _body_brief(chart, lord)}
        from .sensitive import nava_tara
        tara = nava_tara(janma, nak["nakshatra_num"])
        out[name] = {
            **nak,
            "kp": ch,
            "lords": lords,
            "tara_from_moon": tara,
        }
    return out


def calc_varga_sphutas(chart):
    """Sign + degree-in-varga + nakshatra of varga-sphuta for each body."""
    bodies = ["Lagna"] + list(PLANETS_9)
    result = {}
    for vname, fn in VARGA_FUNCTIONS.items():
        parts = VARGA_PARTS.get(vname, 12)
        block = {}
        for name in bodies:
            pos = chart.positions.get(name)
            if not pos or not isinstance(pos, dict):
                continue
            lon = pos["longitude"]
            sign = fn(lon)
            deg_in = (lon % 30.0)
            span = 30.0 / parts if parts else 30.0
            frac = (deg_in % span) / span if span else 0.0
            vdeg = frac * 30.0
            vsphuta = SIGN_INDEX[sign] * 30.0 + vdeg
            nak = _nak_pack(vsphuta)
            block[name] = {
                "sign": sign,
                "degree_in_sign": round(vdeg, 6),
                "sphuta": round(vsphuta % 360.0, 6),
                "nakshatra": nak["nakshatra"],
                "pada": nak["pada"],
                "nak_lord": nak["lord"],
            }
        result[vname] = block
    return result


def calc_drik_house_matrix(chart):
    """Graha drishti pinda from each planet onto each house."""
    rashi = chart.rashi_chart
    grid = {}
    for planet in PLANETS_7:
        src = rashi.get(planet, {}).get("house_rashi")
        if not src:
            continue
        row = {}
        for h in range(1, 13):
            row[str(h)] = _drishti_pinda(planet, src, h)
        grid[planet] = row
    return grid


def calc_bhava_raw(chart):
    """House karaka shadbala + graha/rashi drishti lists + lord vargas."""
    from .graha_state import jaimini_aspect_signs
    sb = chart.shadbala
    vargas = chart.vargas
    vkeys = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]
    out = {}
    for h in range(1, 13):
        lord = chart.lordships.get(h)
        sign = house_to_sign(h, chart.lagna_index)
        karaka = HOUSE_KARAKA[h]
        graha_asp = [p for p, houses in (chart.aspects or {}).items() if h in (houses or [])]
        rashi_asp = []
        for p in PLANETS_9:
            psign = chart.positions.get(p, {}).get("sign")
            if psign and sign in jaimini_aspect_signs(psign):
                rashi_asp.append(p)
        lord_v = {vk: (vargas.get(vk) or {}).get(lord) for vk in vkeys} if lord else {}
        bb = (chart.bhava_bala or {}).get(h) or {}
        out[str(h)] = {
            "sign": sign,
            "lord": lord,
            "karaka": karaka,
            "karaka_shadbala_rupas": (sb.get(karaka) or {}).get("rupas"),
            "lord_shadbala_rupas": (sb.get(lord) or {}).get("rupas") if lord else None,
            "graha_drishti": graha_asp,
            "rashi_drishti": rashi_asp,
            "lord_vargas": lord_v,
            "bhava_bala": {
                "rupas": bb.get("rupas"),
                "adhipati": bb.get("adhipati"),
                "dig": bb.get("dig"),
                "drishti": bb.get("drishti"),
            },
        }
    return out


def _natal_house_of_sign(chart, sign):
    return sign_to_house(sign, chart.lagna_index)


def _aspect_houses(planet, occ_house):
    hs = {house_counted_from(occ_house, 7)}
    for off in SPECIAL_ASPECTS.get(planet, []):
        hs.add(house_counted_from(occ_house, off))
    return sorted(hs)


def calc_ingress_calendar(chart, start="2025-01-01", end="2043-12-31"):
    planets = ["Jupiter", "Saturn", "Rahu", "Ketu", "Mars"]
    out = {}
    natal_by_sign = {}
    for p in PLANETS_9:
        s = chart.positions.get(p, {}).get("sign")
        if s:
            natal_by_sign.setdefault(s, []).append(p)
    for planet in planets:
        step = 20 if planet in ("Jupiter", "Saturn", "Rahu", "Ketu") else 5
        try:
            ing = find_sign_ingress(
                planet, start, end,
                ephe_path=getattr(chart._ephe, "_ephe_path", None),
                ayanamsha=chart.birth_data.get("ayanamsha", "lahiri"),
                step_days=step,
                chart=chart,
            )
        except Exception as exc:
            out[planet] = {"error": str(exc)}
            continue
        rows = []
        for i, ev in enumerate(ing):
            to_sign = ev.get("to_sign")
            entry = ev.get("date")
            exit_ = ing[i + 1]["date"] if i + 1 < len(ing) else end
            house = _natal_house_of_sign(chart, to_sign) if to_sign else None
            rows.append({
                "sign": to_sign,
                "entry": entry,
                "exit": exit_,
                "natal_house": house,
                "aspects_houses": _aspect_houses(planet, house) if house else [],
                "conjunct_natal": natal_by_sign.get(to_sign, []),
            })
        out[planet] = rows
    return {"start": start, "end": end, "planets": out}


def calc_transit_over_natal(chart, start="2025-01-01", end="2035-12-31", orb=1.5):
    """Slow-body conjunction windows to natal longitudes (monthly scan)."""
    natal = {
        n: chart.positions[n]["longitude"]
        for n in PLANETS_9
        if isinstance(chart.positions.get(n), dict)
    }
    bb = (chart.special_points.get("bhrigu_bindu") or {}).get("longitude")
    if bb is not None:
        natal["BhriguBindu"] = bb
    transitors = ["Jupiter", "Saturn", "Rahu", "Ketu", "Mars"]
    from .transits import sidereal_lon_speed
    y, m, d = (int(x) for x in start.split("-"))
    ey, em, ed = (int(x) for x in end.split("-"))
    jd = swe.julday(y, m, d, 12.0)
    end_jd = swe.julday(ey, em, ed, 12.0)
    hits = {t: {n: [] for n in natal} for t in transitors}
    while jd <= end_jd:
        yy, mm, dd, _ = swe.revjul(jd)
        date = f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}"
        for t in transitors:
            tlong, _ = sidereal_lon_speed(t, jd)
            for n, nlong in natal.items():
                delta = abs((tlong - nlong) % 360.0)
                if delta > 180:
                    delta = 360 - delta
                if delta <= orb:
                    hits[t][n].append({"date": date, "orb": round(delta, 3)})
        jd += 12.0

    def collapse(lst):
        if not lst:
            return []
        wins = []
        a = b = lst[0]["date"]
        best = lst[0]["orb"]
        prevd = datetime.strptime(a, "%Y-%m-%d")
        for row in lst[1:]:
            d = datetime.strptime(row["date"], "%Y-%m-%d")
            if (d - prevd).days <= 20:
                b = row["date"]
                best = min(best, row["orb"])
            else:
                wins.append({"start": a, "end": b, "min_orb": best})
                a = b = row["date"]
                best = row["orb"]
            prevd = d
        wins.append({"start": a, "end": b, "min_orb": best})
        return wins

    out = {}
    for t in transitors:
        out[t] = {n: collapse(hits[t][n]) for n in natal if hits[t][n]}
    return {"start": start, "end": end, "orb": orb, "hits": out}


def calc_vimshottari_pd_tree(chart, md_lord=None):
    """MD → AD → PD rows for one mahadasha (current MD if omitted)."""
    now = datetime.now().strftime("%Y-%m-%d")
    if md_lord is None:
        cur = chart.get_current_dasha(now) or {}
        md = cur.get("MD") or {}
        md_lord = md.get("lord") if isinstance(md, dict) else md
    rows = []
    for md in chart.dashas or []:
        if md.get("lord") != md_lord:
            continue
        for ad in md.get("sub_periods") or []:
            pds = []
            for pd in ad.get("sub_periods") or []:
                pds.append({
                    "lord": pd.get("lord"),
                    "start": pd.get("start_date"),
                    "end": pd.get("end_date"),
                })
            rows.append({
                "ad": ad.get("lord"),
                "start": ad.get("start_date"),
                "end": ad.get("end_date"),
                "pd": pds,
            })
        break
    return {"md": md_lord, "antardashas": rows}


def calc_yogini_pd_tree(chart):
    """Current Yogini MD → AD → synthetic PD (8-fold of each AD)."""
    now = datetime.now().strftime("%Y-%m-%d")
    tree = []
    for md in chart.yogini_dasha or []:
        if md.get("level") == "AD":
            continue
        end = md.get("end_date") or ""
        if end and end < now:
            continue
        ads = []
        for ad in md.get("sub_periods") or []:
            a0 = ad.get("start_jd")
            a1 = ad.get("end_jd")
            pds = []
            if a0 and a1:
                span = a1 - a0
                cur = a0
                start_idx = YOGINI_NAMES.index(ad.get("yogini")) if ad.get("yogini") in YOGINI_NAMES else 0
                for j in range(8):
                    yi = (start_idx + j) % 8
                    prop = YOGINI_YEARS[yi] / YOGINI_TOTAL
                    nxt = cur + span * prop
                    pds.append({
                        "yogini": YOGINI_NAMES[yi],
                        "planet": YOGINI_PLANETS[yi],
                        "start": _jd_to_date_str(cur),
                        "end": _jd_to_date_str(nxt),
                    })
                    cur = nxt
            ads.append({
                "yogini": ad.get("yogini"),
                "planet": ad.get("planet"),
                "start": ad.get("start_date"),
                "end": ad.get("end_date"),
                "pd": pds,
            })
        tree.append({
            "yogini": md.get("yogini"),
            "planet": md.get("planet"),
            "start": md.get("start_date"),
            "end": md.get("end_date"),
            "antardashas": ads,
        })
        break
    return tree


def calc_sthana_speed_drik(chart):
    """Sthana sub-scores already on shadbala; add speed + yuddha + drik matrix."""
    sb = chart.shadbala
    out = {}
    for p in PLANETS_7:
        pos = chart.positions.get(p) or {}
        kd = (sb.get(p) or {}).get("components", {})
        out[p] = {
            "sthana_detail": kd.get("sthana_detail"),
            "kala_detail": kd.get("kala_detail"),
            "dig": kd.get("dig"),
            "cheshta": kd.get("cheshta"),
            "drik": kd.get("drik"),
            "speed_deg_day": pos.get("speed"),
            "retrograde": pos.get("retrograde"),
            "sign": pos.get("sign"),
        }
    out["drik_house_matrix"] = calc_drik_house_matrix(chart)
    return out


def calc_raw_layers(chart):
    return {
        "tropical_sidereal": calc_tropical_sidereal(chart),
        "nakshatra_layers": calc_nakshatra_layers(chart),
        "varga_sphutas": calc_varga_sphutas(chart),
        "bhava_raw": calc_bhava_raw(chart),
        "sthana_speed_drik": calc_sthana_speed_drik(chart),
        "ingress_2025_2043": calc_ingress_calendar(chart),
        "transit_over_natal": calc_transit_over_natal(chart),
        "vimshottari_pd_tree": calc_vimshottari_pd_tree(chart),
        "yogini_pd_tree": calc_yogini_pd_tree(chart),
        "dhoomadi_upagrahas": chart.dhoomadi_upagrahas,
        "fertility_longevity_sphutas": chart.fertility_and_longevity_sphutas,
        "vaiseshikamsa": chart.vaiseshikamsa,
        "sayanadi_avasthas": chart.sayanadi_avasthas,
        "pindayu_ayurdaya": chart.pindayu_ayurdaya,
    }
