"""
extra_lagnas.py — Indu, Tithi, Viparita, Mrityu lagnas; D10/D2/D30 fact
blocks; per-graha nakshatra qualities. Pure arithmetic. Chart-agnostic.
"""

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, SIGN_ELEMENT, SIGN_MODALITY,
    NAKSHATRAS, NAKSHATRA_SPAN, PLANETS_7, PLANETS_9, get_navamsa_sign,
)
from .matching import VARNA_TABLE, GANA_TABLE, YONI_TABLE, NADI_TABLE, VASHYA_CATEGORY
from .kp import kp_chain
from .vargas import calc_d2_hora, calc_d10, calc_d30, calc_d20, calc_d24, calc_d40, calc_d45
from ..core.mapping import sign_to_house, house_to_sign_index


# BPHS Indu kalas (rays) of the 7 grahas.
INDU_KALAS = {
    "Sun": 30, "Moon": 16, "Mars": 6, "Mercury": 8,
    "Jupiter": 10, "Venus": 12, "Saturn": 1,
}

GANA_NAME = {1: "Deva", 2: "Manushya", 3: "Rakshasa"}
NADI_NAME = {1: "Aadi", 2: "Madhya", 3: "Antya"}
VARNA_NAME = {1: "Brahmin", 2: "Kshatriya", 3: "Vaishya", 4: "Shudra"}

# Rajju (matching rope) by nakshatra number 1-27.
RAJJU = {
    1: "Pada", 2: "Kati", 3: "Nabhi", 4: "Kanta", 5: "Siro",
    6: "Kanta", 7: "Nabhi", 8: "Kati", 9: "Pada",
    10: "Pada", 11: "Kati", 12: "Nabhi", 13: "Kanta", 14: "Siro",
    15: "Kanta", 16: "Nabhi", 17: "Kati", 18: "Pada",
    19: "Pada", 20: "Kati", 21: "Nabhi", 22: "Kanta", 23: "Siro",
    24: "Kanta", 25: "Nabhi", 26: "Kati", 27: "Pada",
}

# D30 lord → classical flavour (Parashara trimsamsa).
D30_FLAVOUR = {
    "Aries": "Mars — wounds, heat, acute",
    "Aquarius": "Saturn — chronic, delay, cold",
    "Sagittarius": "Jupiter — dharma, liver, counsel",
    "Gemini": "Mercury — nerves, speech, skin",
    "Libra": "Venus — pleasure, reproductive, kidney",
}


def _pack(lam, formula=""):
    lam = lam % 360.0
    sidx = int(lam / 30) % 12
    deg = lam - sidx * 30
    nak_idx = min(int(lam / NAKSHATRA_SPAN), 26)
    nak = NAKSHATRAS[nak_idx]
    return {
        "longitude": round(lam, 6),
        "sign": SIGNS[sidx],
        "sign_index": sidx,
        "degree_in_sign": round(deg, 4),
        "nakshatra": nak["name"],
        "nakshatra_lord": nak["lord"],
        "pada": min(int((lam % NAKSHATRA_SPAN) / (NAKSHATRA_SPAN / 4.0)) + 1, 4),
        "sign_lord": SIGN_LORDS[SIGNS[sidx]],
        "kp": kp_chain(lam),
        "formula": formula,
    }


def calc_indu_lagna(chart):
    """
    Indu (wealth) Lagna. BPHS: kalas of 9th-lord from Lagna + kalas of
    9th-lord from Moon; remainder from 12 counted from the Moon's sign.
    """
    lagna_idx = chart.lagna_index
    moon_idx = chart.positions["Moon"]["sign_index"]
    lord9_lagna = chart.lordships.get(9)
    sign9_from_moon = SIGNS[house_to_sign_index(9, moon_idx)]
    lord9_moon = SIGN_LORDS[sign9_from_moon]
    k1 = INDU_KALAS.get(lord9_lagna, 0)
    k2 = INDU_KALAS.get(lord9_moon, 0)
    total = k1 + k2
    rem = total % 12
    if rem == 0:
        rem = 12
    indu_idx = (moon_idx + rem - 1) % 12
    # Place at Moon's degree in that sign (sphuta convention).
    moon_deg = chart.positions["Moon"]["degree_in_sign"]
    lam = indu_idx * 30.0 + moon_deg
    packed = _pack(lam, "Moon_sign + ((kalas_9L_Lagna + kalas_9L_Moon) mod 12) at Moon degree")
    packed["kalas_9l_lagna"] = k1
    packed["kalas_9l_moon"] = k2
    packed["lords"] = {"from_lagna": lord9_lagna, "from_moon": lord9_moon}
    packed["house_from_lagna"] = sign_to_house(indu_idx, lagna_idx)
    return packed


def calc_tithi_lagna(chart):
    """Tithi Lagna sphuta = ASC + (Moon − Sun)."""
    asc = chart.positions["Lagna"]["longitude"]
    moon = chart.positions["Moon"]["longitude"]
    sun = chart.positions["Sun"]["longitude"]
    lam = (asc + (moon - sun)) % 360.0
    packed = _pack(lam, "ASC + (Moon - Sun)")
    packed["tithi_elongation"] = round((moon - sun) % 360.0, 4)
    packed["house_from_lagna"] = int(((lam - asc) % 360.0) / 30.0) + 1
    return packed


def calc_viparita_lagna(chart):
    """Viparita Lagna = ASC + 180° (equal 7th cusp)."""
    asc = chart.positions["Lagna"]["longitude"]
    return _pack((asc + 180.0) % 360.0, "ASC + 180")


def calc_mrityu_lagna(chart):
    """Mrityu-related sphutas: Placidus 8th cusp + Gulika if present."""
    c8 = chart.house_cusps["cusps"][8]["longitude"]
    gulika = chart.special_lagnas.get("gulika")
    if isinstance(gulika, dict):
        g_long = gulika.get("longitude")
    elif isinstance(gulika, (int, float)):
        g_long = float(gulika)
    else:
        g_long = None
    out = {"eighth_cusp": _pack(c8, "Placidus 8th cusp")}
    if g_long is not None:
        out["gulika"] = _pack(g_long, "Gulika")
    return out


def calc_house_pranapadas(chart):
    """D9 (navamsa) of each Placidus and equal cusp — 'soul of the house'."""
    asc = chart.positions["Lagna"]["longitude"]
    out = {"placidus": {}, "equal": {}}
    for h in range(1, 13):
        p_long = chart.house_cusps["cusps"][h]["longitude"]
        e_long = (asc + 30.0 * (h - 1)) % 360.0
        out["placidus"][str(h)] = {
            "cusp": round(p_long, 6),
            "navamsa": get_navamsa_sign(p_long),
            "navamsa_lord": SIGN_LORDS[get_navamsa_sign(p_long)],
        }
        out["equal"][str(h)] = {
            "cusp": round(e_long, 6),
            "navamsa": get_navamsa_sign(e_long),
            "navamsa_lord": SIGN_LORDS[get_navamsa_sign(e_long)],
        }
    return out


def calc_d10_facts(chart):
    """D10 lagna, 10th-from-D10-lagna, each graha's D10 house, current MD in D10."""
    v = chart.vargas.get("D10") or {}
    d10_lagna = v.get("Lagna")
    if not d10_lagna:
        d10_lagna = calc_d10(chart.positions["Lagna"]["longitude"])
    d10_l_idx = SIGN_INDEX[d10_lagna]
    tenth_sign = SIGNS[house_to_sign_index(10, d10_l_idx)]
    bodies = {}
    for p in ["Lagna"] + list(PLANETS_9):
        sign = v.get(p) or (calc_d10(chart.positions[p]["longitude"]) if p in chart.positions else None)
        if not sign:
            continue
        house = sign_to_house(sign, d10_l_idx)
        bodies[p] = {"sign": sign, "house_from_d10_lagna": house, "sign_lord": SIGN_LORDS[sign]}
    md = None
    try:
        cur = chart.get_current_dasha(levels=5) or {}
        md = cur.get("MD") or cur.get("mahadasha") or cur.get("lord")
        if isinstance(md, dict):
            md = md.get("lord")
    except Exception:
        md = None
    md_block = bodies.get(md) if md else None
    return {
        "d10_lagna": d10_lagna,
        "d10_lagna_lord": SIGN_LORDS[d10_lagna],
        "tenth_from_d10_lagna": tenth_sign,
        "tenth_from_d10_lord": SIGN_LORDS[tenth_sign],
        "bodies": bodies,
        "current_md_lord": md,
        "current_md_in_d10": md_block,
    }


def calc_d2_hora_facts(chart):
    """Sun-Hora vs Moon-Hora for each graha (wealth vehicle)."""
    out = {}
    for p in ["Lagna"] + list(PLANETS_7):
        pos = chart.positions.get(p)
        if not pos or not isinstance(pos, dict):
            continue
        hora_sign = calc_d2_hora(pos["longitude"])
        out[p] = {
            "hora_sign": hora_sign,
            "hora_lord": "Sun" if hora_sign == "Leo" else "Moon",
            "wealth_via": "self" if hora_sign == "Leo" else "others",
        }
    return out


def calc_d30_facts(chart):
    """Trimsamsa sign + flavour for each graha (health/evil varga)."""
    out = {}
    for p in PLANETS_7:
        pos = chart.positions.get(p)
        if not pos or not isinstance(pos, dict):
            continue
        sign = calc_d30(pos["longitude"])
        out[p] = {
            "trimsamsa_sign": sign,
            "trimsamsa_lord": SIGN_LORDS[sign],
            "flavour": D30_FLAVOUR.get(sign, ""),
        }
    return out


def calc_other_varga_lagna(chart):
    """Lagna of D20/D24/D40/D45 plus each graha's sign (raw, no interpretation)."""
    keys = {
        "D20": calc_d20, "D24": calc_d24, "D40": calc_d40, "D45": calc_d45,
    }
    out = {}
    for name, fn in keys.items():
        block = {"lagna": fn(chart.positions["Lagna"]["longitude"]), "bodies": {}}
        block["lagna_lord"] = SIGN_LORDS[block["lagna"]]
        for p in PLANETS_9:
            pos = chart.positions.get(p)
            if pos and isinstance(pos, dict):
                block["bodies"][p] = fn(pos["longitude"])
        out[name] = block
    return out


def nakshatra_quality(nak_num, sign):
    return {
        "nakshatra_num": nak_num,
        "varna": VARNA_NAME.get(VARNA_TABLE.get(nak_num)),
        "gana": GANA_NAME.get(GANA_TABLE.get(nak_num)),
        "nadi": NADI_NAME.get(NADI_TABLE.get(nak_num)),
        "yoni": YONI_TABLE.get(nak_num),
        "rajju": RAJJU.get(nak_num),
        "vasya": VASHYA_CATEGORY.get(sign),
        "tatva": SIGN_ELEMENT.get(sign),
        "modality": SIGN_MODALITY.get(sign),
    }


def calc_nakshatra_qualities(chart):
    """Gana/yoni/nadi/varna/rajju/vasya/tatva for Lagna + 9 grahas."""
    out = {}
    for name in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(name)
        if not pos or not isinstance(pos, dict):
            continue
        num = pos.get("nakshatra_num") or (
            min(int(pos["longitude"] / NAKSHATRA_SPAN), 26) + 1
        )
        out[name] = nakshatra_quality(num, pos.get("sign"))
        out[name]["nakshatra"] = pos.get("nakshatra")
        out[name]["sign"] = pos.get("sign")
    return out


def calc_extra_points_bundle(chart):
    return {
        "indu_lagna": calc_indu_lagna(chart),
        "tithi_lagna": calc_tithi_lagna(chart),
        "viparita_lagna": calc_viparita_lagna(chart),
        "mrityu_lagna": calc_mrityu_lagna(chart),
        "house_pranapadas": calc_house_pranapadas(chart),
        "d10_facts": calc_d10_facts(chart),
        "d2_hora": calc_d2_hora_facts(chart),
        "d30_trimsamsa": calc_d30_facts(chart),
        "varga_lagnas_d20_d45": calc_other_varga_lagna(chart),
        "nakshatra_qualities": calc_nakshatra_qualities(chart),
    }
