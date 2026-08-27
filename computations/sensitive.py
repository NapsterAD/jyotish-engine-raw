"""
sensitive.py — Pranapada, Pushkara, 64th Navamsa, 22nd Drekkana,
Nava-Tara, Bhavat Bhavam, Ayurdaya, Grahan. rules.md §15, §18, §20, §24–26.
"""

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, SIGN_ELEMENT, SIGN_MODALITY,
    NAKSHATRAS, NAKSHATRA_SPAN, PLANETS_7, PLANETS_9,
)
from ..core.mapping import bhavat_bhavam as _bb, house_to_sign

# Pushkara Navamsa spans by element. rules.md §24.1
PUSHKARA_NAVAMSA = {
    "Fire":  [(20.0, 23.0 + 20.0 / 60.0), (26.0 + 40.0 / 60.0, 30.0)],
    "Earth": [(6.0 + 40.0 / 60.0, 10.0), (13.0 + 20.0 / 60.0, 16.0 + 40.0 / 60.0)],
    "Air":   [(16.0 + 40.0 / 60.0, 20.0), (23.0 + 20.0 / 60.0, 26.0 + 40.0 / 60.0)],
    "Water": [(0.0, 3.0 + 20.0 / 60.0), (6.0 + 40.0 / 60.0, 10.0)],
}

# Pushkara Bhaga exact degree (end of 1° arc). §24.2
PUSHKARA_BHAGA = {
    "Aries": 21, "Taurus": 14, "Gemini": 18, "Cancer": 8,
    "Leo": 19, "Virgo": 9, "Libra": 24, "Scorpio": 11,
    "Sagittarius": 23, "Capricorn": 14, "Aquarius": 19, "Pisces": 9,
}

TARA_NAMES = [
    ("Janma", 0.0), ("Sampat", 1.0), ("Vipat", -1.0), ("Kshema", 0.8),
    ("Pratyak", -0.8), ("Sadhana", 1.0), ("Naidhana", -1.0),
    ("Mitra", 0.8), ("Parama Mitra", 1.0),
]

NAK_ACTIVATION_AGES = {
    "Ashwini": (20, 28), "Bharani": (24, 33), "Krittika": (21, 30),
    "Rohini": (24, 32), "Mrigashira": (28, 35), "Ardra": (25, 34),
    "Punarvasu": (24, 32), "Pushya": (28, 36), "Ashlesha": (30, 39),
    "Magha": (25, 34), "Purva Phalguni": (28, 38), "Uttara Phalguni": (30, 36),
    "Hasta": (25, 35), "Chitra": (32, 38), "Swati": (30, 37),
    "Vishakha": (28, 34), "Anuradha": (32, 39), "Jyeshtha": (27, 36),
    "Moola": (28, 36), "Purva Ashadha": (28, 35), "Uttara Ashadha": (31, 38),
    "Shravana": (25, 33), "Dhanishtha": (24, 32), "Shatabhisha": (28, 36),
    "Purva Bhadrapada": (24, 33), "Uttara Bhadrapada": (27, 35), "Revati": (23, 32),
}


def _ang_sep(a, b):
    d = abs((a - b) % 360.0)
    return d if d <= 180.0 else 360.0 - d


def calc_pranapada(chart):
    """BPHS + Parashari Pranapada. rules.md §15."""
    ss = chart.sunrise_sunset or {}
    rise = ss.get("sunrise_jd")
    birth_jd = chart.positions.get("_jd")
    asc = chart.positions["Lagna"]["longitude"]
    sun = chart.positions["Sun"]["longitude"]
    ishta_ghati = 0.0
    if rise and birth_jd:
        hours = (birth_jd - rise) * 24.0
        if hours < 0:
            hours += 24.0
        ishta_ghati = hours * 2.5  # 1 hour = 2.5 ghatis
    bphs = (asc + ishta_ghati * 0.24) % 360.0

    sun_mod = SIGN_MODALITY[chart.positions["Sun"]["sign"]]
    add = {"Movable": 0.0, "Fixed": 240.0, "Dual": 120.0}[sun_mod]
    day_frac = 0.0
    if rise and birth_jd:
        day_frac = ((birth_jd - rise) % 1.0)
    parashara = (day_frac * 360.0 * 2.0 + sun + add) % 360.0

    def pack(lam, formula):
        sidx = int(lam / 30) % 12
        deg = lam - sidx * 30
        return {
            "longitude": round(lam, 4),
            "sign": SIGNS[sidx],
            "degree_in_sign": round(deg, 4),
            "formula": formula,
        }

    return {
        "bphs": pack(bphs, "Lagna + IshtaGhati×0.24"),
        "parashara": pack(parashara, "day-fraction×720 + Sun + modality"),
        "ishta_ghati": round(ishta_ghati, 4),
    }


def is_pushkara_navamsa(longitude):
    sign = SIGNS[int((longitude % 360.0) / 30) % 12]
    deg = (longitude % 360.0) % 30.0
    element = SIGN_ELEMENT[sign]
    for lo, hi in PUSHKARA_NAVAMSA[element]:
        if lo <= deg < hi:
            return True
    return False


def is_pushkara_bhaga(longitude, orb=0.5):
    sign = SIGNS[int((longitude % 360.0) / 30) % 12]
    deg = (longitude % 360.0) % 30.0
    target = PUSHKARA_BHAGA[sign]
    # arc is (target-1) to target
    return (target - 1.0) <= deg <= target + orb


def calc_pushkara(chart):
    planets = {}
    for name in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(name, {})
        if not isinstance(pos, dict):
            continue
        lam = pos.get("longitude", 0.0)
        planets[name] = {
            "pushkara_navamsa": is_pushkara_navamsa(lam),
            "pushkara_bhaga": is_pushkara_bhaga(lam),
            "vargottama": pos.get("sign") == pos.get("navamsa"),
        }
    return planets


def calc_64th_navamsa(chart):
    moon = chart.positions["Moon"]["longitude"]
    asc = chart.positions["Lagna"]["longitude"]
    from_moon = (moon + 210.0) % 360.0
    from_lagna = (asc + 210.0) % 360.0

    def pack(lam):
        sidx = int(lam / 30) % 12
        return {
            "longitude": round(lam, 4),
            "sign": SIGNS[sidx],
            "degree_in_sign": round(lam - sidx * 30, 4),
            "lord": SIGN_LORDS[SIGNS[sidx]],
        }

    return {"from_moon": pack(from_moon), "from_lagna": pack(from_lagna)}


def calc_22nd_drekkana(chart):
    asc = chart.positions["Lagna"]["longitude"]
    lam = (asc + 70.0) % 360.0
    sidx = int(lam / 30) % 12
    sign = SIGNS[sidx]
    return {
        "longitude": round(lam, 4),
        "sign": sign,
        "degree_in_sign": round(lam - sidx * 30, 4),
        "kharadhipati": SIGN_LORDS[sign],
    }


def nava_tara(janma_num, target_num):
    """Tara index 1-9 from janma nakshatra. §25.2."""
    idx = ((target_num - janma_num) % 9) + 1
    name, weight = TARA_NAMES[idx - 1]
    return {"index": idx, "name": name, "weight": weight}


def calc_nava_tara(chart):
    janma = chart.positions["Moon"].get("nakshatra_num") or (
        min(int(chart.positions["Moon"]["longitude"] / NAKSHATRA_SPAN), 26) + 1
    )
    taras = {}
    for nak in NAKSHATRAS:
        taras[nak["name"]] = nava_tara(janma, nak["num"])
    sensitive = {
        "Janma": NAKSHATRAS[(janma - 1) % 27]["name"],
        "Karma": NAKSHATRAS[(janma - 1 + 9) % 27]["name"],
        "Samudayika": NAKSHATRAS[(janma - 1 + 17) % 27]["name"],
        "Vainashika": NAKSHATRAS[(janma - 1 + 22) % 27]["name"],
        "Kula": NAKSHATRAS[(janma - 1 + 23) % 27]["name"],
        "Manasa": NAKSHATRAS[(janma - 1 + 24) % 27]["name"],
        "Jati": NAKSHATRAS[(janma - 1 + 25) % 27]["name"],
        "Desha": NAKSHATRAS[(janma - 1 + 26) % 27]["name"],
    }
    janma_name = NAKSHATRAS[janma - 1]["name"]
    ages = NAK_ACTIVATION_AGES.get(janma_name)
    abhijit = {
        "span": "Capricorn 6°40' – 10°53'20\"",
        "moon_in_abhijit": (
            270.0 + 6.0 + 40.0 / 60.0
            <= (chart.positions["Moon"]["longitude"] % 360.0)
            < 270.0 + 10.0 + 53.0 / 60.0 + 20.0 / 3600.0
        ),
    }
    return {
        "janma_nakshatra": janma_name,
        "janma_number": janma,
        "taras": taras,
        "sensitive": sensitive,
        "activation_ages": {"primary": ages[0] if ages else None,
                            "secondary": ages[1] if ages else None},
        "abhijit": abhijit,
    }


def bhavat_bhavam(house):
    """BhB(H) = count H houses from H. §18."""
    return _bb(house)


def calc_bhavat_bhavam(chart):
    result = {}
    for h in range(1, 13):
        bb = bhavat_bhavam(h)
        result[h] = {
            "bhavat_bhavam": bb,
            "sign": house_to_sign(bb, chart.lagna_index),
            "lord": chart.lordships.get(bb),
            "occupants": chart.get_planets_in_house(bb, "rashi"),
        }
    return result


def _modality_class(mod_a, mod_b):
    if mod_a == mod_b:
        return {"Movable": "Alpaayu", "Fixed": "Purnaayu", "Dual": "Madhyaayu"}[mod_a]
    return "MIXED"


def calc_ayurdaya(chart):
    """Three-pair longevity classification. rules.md §20."""
    lagna_mod = SIGN_MODALITY[chart.lagna_sign]
    lord8 = chart.lordships.get(8)
    lord8_sign = chart.rashi_chart.get(lord8, {}).get("sign") or chart.positions.get(lord8, {}).get("sign")
    pair1 = _modality_class(lagna_mod, SIGN_MODALITY.get(lord8_sign, lagna_mod))

    lord1 = chart.lordships.get(1)
    l1_sign = chart.rashi_chart.get(lord1, {}).get("sign")
    moon_sign = chart.positions["Moon"]["sign"]
    moon_lord = SIGN_LORDS[moon_sign]
    ml_sign = chart.rashi_chart.get(moon_lord, {}).get("sign")
    pair2 = _modality_class(
        SIGN_MODALITY.get(l1_sign, lagna_mod),
        SIGN_MODALITY.get(ml_sign, lagna_mod),
    )

    hl = chart.special_lagnas.get("hora_lagna") or chart.special_lagnas.get("HL")
    if isinstance(hl, dict):
        hl_sign = hl.get("sign")
    elif isinstance(hl, (int, float)):
        hl_sign = SIGNS[int((hl % 360.0) / 30.0) % 12]
    else:
        hl_sign = None
    if not hl_sign:
        pair3 = "MIXED"
    else:
        pair3 = _modality_class(lagna_mod, SIGN_MODALITY[hl_sign])

    votes = [p for p in (pair1, pair2, pair3) if p != "MIXED"]
    if not votes:
        verdict = "Madhyaayu"
    else:
        verdict = max(set(votes), key=votes.count)
    ranges = {"Alpaayu": "0-32", "Madhyaayu": "33-66", "Purnaayu": "67-100"}
    return {
        "pair1_lagna_8l": pair1,
        "pair2_1l_moonlord": pair2,
        "pair3_lagna_hora": pair3,
        "verdict": verdict,
        "age_range": ranges.get(verdict),
    }


def calc_grahan(chart, orb=12.0):
    """Solar/lunar eclipse yoga. §26.4."""
    sun = chart.positions["Sun"]["longitude"]
    moon = chart.positions["Moon"]["longitude"]
    rahu = chart.positions["Rahu"]["longitude"]
    ketu = chart.positions["Ketu"]["longitude"]
    sun_e = _ang_sep(sun, rahu) <= orb or _ang_sep(sun, ketu) <= orb
    moon_e = _ang_sep(moon, rahu) <= orb or _ang_sep(moon, ketu) <= orb
    full_moon = _ang_sep(sun, moon) >= (180.0 - 12.0)
    return {
        "sun_eclipsed": sun_e,
        "moon_eclipsed": moon_e,
        "full_moon_eclipse": bool(moon_e and full_moon),
        "new_moon_eclipse": bool(sun_e and _ang_sep(sun, moon) <= 12.0),
    }


def calc_gandanta(longitude: float) -> dict:
    """
    Gandanta detection and 3-tier severity scoring. rules.md §33.
    Fire-Water junctions: Pisces-Aries, Cancer-Leo, Scorpio-Sagittarius.
    """
    lam = longitude % 360.0
    deg_in_sign = lam % 30.0
    sidx = int(lam / 30.0) % 12
    sign = SIGNS[sidx]
    element = SIGN_ELEMENT[sign]
    
    is_gand = False
    gand_type = None
    severity = "NONE"
    proximity = 0.0
    zone_name = None
    
    # 1. Pisces -> Aries
    if sidx == 11 and deg_in_sign >= (30.0 - 3.333333):
        is_gand = True
        gand_type = "END_OF_WATER"
        proximity = 30.0 - deg_in_sign
        zone_name = "Pisces-Aries (Revati-Ashwini)"
    elif sidx == 0 and deg_in_sign <= 3.333333:
        is_gand = True
        gand_type = "START_OF_FIRE"
        proximity = deg_in_sign
        zone_name = "Pisces-Aries (Revati-Ashwini)"
    # 2. Cancer -> Leo
    elif sidx == 3 and deg_in_sign >= (30.0 - 3.333333):
        is_gand = True
        gand_type = "END_OF_WATER"
        proximity = 30.0 - deg_in_sign
        zone_name = "Cancer-Leo (Ashlesha-Magha)"
    elif sidx == 4 and deg_in_sign <= 3.333333:
        is_gand = True
        gand_type = "START_OF_FIRE"
        proximity = deg_in_sign
        zone_name = "Cancer-Leo (Ashlesha-Magha)"
    # 3. Scorpio -> Sagittarius
    elif sidx == 7 and deg_in_sign >= (30.0 - 3.333333):
        is_gand = True
        gand_type = "END_OF_WATER"
        proximity = 30.0 - deg_in_sign
        zone_name = "Scorpio-Sagittarius (Jyeshtha-Moola)"
    elif sidx == 8 and deg_in_sign <= 3.333333:
        is_gand = True
        gand_type = "START_OF_FIRE"
        proximity = deg_in_sign
        zone_name = "Scorpio-Sagittarius (Jyeshtha-Moola)"
        
    if is_gand:
        if proximity <= 0.8: # 0°48'
            severity = "SEVERE_ABHUKTA_MOOLA"
        elif proximity <= 1.6: # 1°36'
            severity = "HIGH"
        else:
            severity = "MODERATE"
            
    return {
        "is_gandanta": is_gand,
        "zone": zone_name,
        "type": gand_type,
        "severity": severity,
        "proximity_degrees": round(proximity, 4) if is_gand else 0.0,
    }


def is_nakshatra_sandhi(longitude: float, orb: float = 0.5) -> bool:
    """Check if longitude is within orb (default 0°30') of any nakshatra boundary."""
    rem = (longitude % 360.0) % NAKSHATRA_SPAN
    return rem <= orb or rem >= (NAKSHATRA_SPAN - orb)


def is_rashi_sandhi(longitude: float, orb: float = 1.0) -> bool:
    """Check if longitude is within orb (default 1°00') of any sign boundary."""
    rem = (longitude % 360.0) % 30.0
    return rem <= orb or rem >= (30.0 - orb)


def calc_gandanta_and_sandhis(chart) -> dict:
    """Calculate Gandanta, Nakshatra Sandhi, and Rashi Sandhi for all points in chart."""
    positions = chart.positions or {}
    results = {}
    for p, pos in positions.items():
        if not isinstance(pos, dict):
            continue
        lon = pos.get("longitude", 0.0)
        gand = calc_gandanta(lon)
        nak_s = is_nakshatra_sandhi(lon)
        ras_s = is_rashi_sandhi(lon)
        results[p] = {
            "gandanta": gand,
            "is_nakshatra_sandhi": nak_s,
            "is_rashi_sandhi": ras_s,
            "has_junction_affliction": gand["is_gandanta"] or nak_s or ras_s
        }
    return results


def calc_sensitive_bundle(chart):
    return {
        "pranapada": calc_pranapada(chart),
        "pushkara": calc_pushkara(chart),
        "navamsa_64": calc_64th_navamsa(chart),
        "drekkana_22": calc_22nd_drekkana(chart),
        "nava_tara": calc_nava_tara(chart),
        "bhavat_bhavam": calc_bhavat_bhavam(chart),
        "ayurdaya": calc_ayurdaya(chart),
        "grahan": calc_grahan(chart),
        "gandanta_and_sandhis": calc_gandanta_and_sandhis(chart),
    }
