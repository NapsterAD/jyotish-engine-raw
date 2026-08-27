"""
classical_extensions.py — High-precision classical Jyotish extensions:
1. Sayanadi 12 Avasthas (BPHS Chapter 45)
2. Vaiseshikamsa Dignity Scales (BPHS Chapter 6 / JHora)
3. 5 Dhoomadi Upagrahas / Apranash Grahas (BPHS Chapter 3)
4. Fertility & Longevity Sphutas (Phaladeepika Ch. 12 & Prasna Marga)
5. Detailed Classical Pindayu Ayurdaya Reductions (BPHS Chapter 43)

100% pure astronomical arithmetic with zero external runtime dependencies.
"""

from __future__ import annotations
import math
from typing import Dict, Any, List, Optional

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_9, PLANETS_7,
    OWN_SIGNS, MOOLATRIKONA, EXALTATION, DEBILITATION,
    NAKSHATRAS, NAKSHATRA_SPAN,
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. 5 DHOOMADI UPAGRAHAS / APRANASH GRAHAS (BPHS Chapter 3)
# ══════════════════════════════════════════════════════════════════════════════

def calc_dhoomadi_upagrahas(sun_long: float) -> Dict[str, Dict[str, Any]]:
    """
    Calculate the 5 non-luminous Dhoomadi Upagrahas based on Sun's sidereal longitude:
    1. Dhuma (धूम)        = Sun + 133°20'
    2. Vyatipata (व्यतीपात)   = 360° - Dhuma
    3. Parivesha (परिवेश)    = Vyatipata + 180°
    4. Indrachapa (इन्द्रचाप) = 360° - Parivesha
    5. Upaketu (उपकेतु)      = Indrachapa + 16°40'
    
    Invariant: (Upaketu + 30°) % 360 == Sun % 360
    """
    dhuma = (sun_long + 133.0 + 20.0 / 60.0) % 360.0
    vyatipata = (360.0 - dhuma) % 360.0
    parivesha = (vyatipata + 180.0) % 360.0
    indrachapa = (360.0 - parivesha) % 360.0
    upaketu = (indrachapa + 16.0 + 40.0 / 60.0) % 360.0

    upagrahas = {
        "Dhuma": dhuma,
        "Vyatipata": vyatipata,
        "Parivesha": parivesha,
        "Indrachapa": indrachapa,
        "Upaketu": upaketu,
    }

    result = {}
    nak_names = [n["name"] for n in NAKSHATRAS]

    for name, lon in upagrahas.items():
        s_idx = int(lon / 30.0)
        deg_in_sign = lon % 30.0
        nak_idx = int(lon / NAKSHATRA_SPAN)
        deg_in_nak = lon % NAKSHATRA_SPAN
        pada = int(deg_in_nak / (NAKSHATRA_SPAN / 4.0)) + 1
        
        # Navamsha sign calculation
        nav_sign_idx = (int(lon / (30.0 / 9.0))) % 12

        result[name] = {
            "longitude": round(lon, 6),
            "sign": SIGNS[s_idx],
            "sign_index": s_idx,
            "degree_in_sign": round(deg_in_sign, 4),
            "nakshatra": nak_names[nak_idx % 27],
            "pada": pada,
            "navamsha_sign": SIGNS[nav_sign_idx],
        }

    return result


# ══════════════════════════════════════════════════════════════════════════════
# 2. FERTILITY & LONGEVITY SPHUTAS (Phaladeepika Ch. 12 & Prasna Marga)
# ══════════════════════════════════════════════════════════════════════════════

def calc_fertility_and_longevity_sphutas(chart) -> Dict[str, Any]:
    """
    Calculate essential Classical Sphutas:
    - Beeja Sphuta (Male progeny capacity)   = (Sun + Venus + Jupiter) % 360
    - Kshetra Sphuta (Female progeny capacity)= (Moon + Mars + Jupiter) % 360
    - Santhana Tithi                         = ((Moon - Sun) % 360) * 5 % 360
    - Tri-Sphuta                             = (Lagna + Moon + Gulika) % 360
    - Chatur-Sphuta                          = (Tri-Sphuta + Sun) % 360
    - Pancha-Sphuta                          = (Chatur-Sphuta + Rahu) % 360
    - Prana Sphuta                           = (Lagna * 5 + Gulika) % 360
    - Deha Sphuta                            = (Moon * 8 + Gulika) % 360
    - Mrityu Sphuta                          = (Gulika * 7 + Sun) % 360
    """
    pos = chart.positions
    sun_lon = pos.get("Sun", {}).get("longitude", 0.0)
    moon_lon = pos.get("Moon", {}).get("longitude", 0.0)
    mars_lon = pos.get("Mars", {}).get("longitude", 0.0)
    jup_lon = pos.get("Jupiter", {}).get("longitude", 0.0)
    ven_lon = pos.get("Venus", {}).get("longitude", 0.0)
    rahu_lon = pos.get("Rahu", {}).get("longitude", 0.0)
    asc_lon = pos.get("Lagna", {}).get("longitude", 0.0)

    # Gulika from special_lagnas or default
    gulika_lon = 0.0
    if hasattr(chart, "special_lagnas") and isinstance(chart.special_lagnas, dict):
        gulika_lon = chart.special_lagnas.get("gulika") or chart.special_lagnas.get("maandi") or 0.0

    # 1. Progeny Sphutas
    beeja = (sun_lon + ven_lon + jup_lon) % 360.0
    kshetra = (moon_lon + mars_lon + jup_lon) % 360.0
    santhana_deg = (((moon_lon - sun_lon + 360.0) % 360.0) * 5.0) % 360.0

    # 2. Longevity / Prasna Sphutas
    tri_sphuta = (asc_lon + moon_lon + gulika_lon) % 360.0
    chatur_sphuta = (tri_sphuta + sun_lon) % 360.0
    pancha_sphuta = (chatur_sphuta + rahu_lon) % 360.0
    prana_sphuta = (asc_lon * 5.0 + gulika_lon) % 360.0
    deha_sphuta = (moon_lon * 8.0 + gulika_lon) % 360.0
    mrityu_sphuta = (gulika_lon * 7.0 + sun_lon) % 360.0

    def _sphuta_details(lon: float) -> Dict[str, Any]:
        s_idx = int(lon / 30.0)
        deg = lon % 30.0
        nak_names = [n["name"] for n in NAKSHATRAS]
        nak_idx = int(lon / NAKSHATRA_SPAN)
        pada = int((lon % NAKSHATRA_SPAN) / (NAKSHATRA_SPAN / 4.0)) + 1
        nav_sign_idx = (int(lon / (30.0 / 9.0))) % 12
        is_odd_rashi = (s_idx % 2 == 0)
        is_odd_navamsha = (nav_sign_idx % 2 == 0)

        return {
            "longitude": round(lon, 4),
            "sign": SIGNS[s_idx],
            "degree_in_sign": round(deg, 4),
            "nakshatra": nak_names[nak_idx % 27],
            "pada": pada,
            "navamsha_sign": SIGNS[nav_sign_idx],
            "is_odd_rashi": is_odd_rashi,
            "is_odd_navamsha": is_odd_navamsha,
        }

    beeja_info = _sphuta_details(beeja)
    beeja_info["favorable"] = beeja_info["is_odd_rashi"] and beeja_info["is_odd_navamsha"]

    kshetra_info = _sphuta_details(kshetra)
    kshetra_info["favorable"] = (not kshetra_info["is_odd_rashi"]) and (not kshetra_info["is_odd_navamsha"])

    santhana_tithi_num = int(santhana_deg / 12.0) + 1
    tithi_names = [
        "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
        "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
        "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima",
        "Pratipada (K)", "Dvitiya (K)", "Tritiya (K)", "Chaturthi (K)", "Panchami (K)",
        "Shashthi (K)", "Saptami (K)", "Ashtami (K)", "Navami (K)", "Dashami (K)",
        "Ekadashi (K)", "Dvadashi (K)", "Trayodashi (K)", "Chaturdashi (K)", "Amavasya"
    ]

    return {
        "progeny": {
            "beeja_sphuta": beeja_info,
            "kshetra_sphuta": kshetra_info,
            "santhana_tithi": {
                "degree": round(santhana_deg, 4),
                "tithi_number": santhana_tithi_num,
                "tithi_name": tithi_names[(santhana_tithi_num - 1) % 30],
                "favorable": santhana_tithi_num not in [4, 6, 8, 9, 14, 15, 19, 21, 23, 24, 29, 30],
            },
        },
        "longevity_sphutas": {
            "tri_sphuta": _sphuta_details(tri_sphuta),
            "chatur_sphuta": _sphuta_details(chatur_sphuta),
            "pancha_sphuta": _sphuta_details(pancha_sphuta),
            "prana_sphuta": _sphuta_details(prana_sphuta),
            "deha_sphuta": _sphuta_details(deha_sphuta),
            "mrityu_sphuta": _sphuta_details(mrityu_sphuta),
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. VAISESHIKAMSA DIGNITY SCALES (BPHS Chapter 6 / JHora)
# ══════════════════════════════════════════════════════════════════════════════

def calc_vaiseshikamsa(chart) -> Dict[str, Dict[str, Any]]:
    """
    Calculate Vaiseshikamsa dignity count in Dasa Varga (10) and Shodasa Varga (16).
    
    Titles in Dasa Varga (10 harmonic charts):
    - 2: Parijata (2-Paarijaata)
    - 3: Uttama (3-Uttama)
    - 4: Gopura (4-Gopura)
    - 5: Simhasana (5-Simhasana)
    - 6: Paravata (6-Paravata)
    - 7: Devaloka (7-Devaloka)
    - 8: Airavata (8-Airavata)
    - 9: Vaishnavamsha (9-Vaishnavamsha)
    - 10: Saubhagyamsha (10-Saubhagyamsha)
    
    Titles in Shodasa Varga (16 harmonic charts):
    - 2: Parijata (2-Paarijaata)
    - 3: Kusuma (3-Kusuma)
    - 4: Nagapurusha (4-Nagapurusha)
    - 5: Kanduka (5-Kanduka)
    - 6: Kerala (6-Kerala)
    - 7: Kalpavriksha (7-Kalpavriksha)
    - 8: Chandanavana (8-Chandanavana)
    - 9: Poornachandra (9-Poornachandra)
    - 10: Uchchaisrava (10-Uchchaisrava)
    - 11: Dhanvantari (11-Dhanvantari)
    - 12: Suryakanta (12-Suryakanta)
    - 13: Vidruma (13-Vidruma)
    - 14: Shakra (14-Shakra)
    - 15: Goloka (15-Goloka)
    - 16: Shreedhamamsha (16-Shreedhamamsha)
    """
    dasa_vargas = ["D1", "D2", "D3", "D7", "D9", "D10", "D12", "D16", "D30", "D60"]
    shodasa_vargas = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]

    dasa_names = {
        2: "2-Paarijaata", 3: "3-Uttama", 4: "4-Gopura", 5: "5-Simhasana",
        6: "6-Paravata", 7: "7-Devaloka", 8: "8-Airavata", 9: "9-Vaishnavamsha",
        10: "10-Saubhagyamsha"
    }
    shodasa_names = {
        2: "2-Paarijaata", 3: "3-Kusuma", 4: "4-Nagapurusha", 5: "5-Kanduka",
        6: "6-Kerala", 7: "7-Kalpavriksha", 8: "8-Chandanavana", 9: "9-Poornachandra",
        10: "10-Uchchaisrava", 11: "11-Dhanvantari", 12: "12-Suryakanta",
        13: "13-Vidruma", 14: "14-Shakra", 15: "15-Goloka", 16: "16-Shreedhamamsha"
    }

    def _is_dignified(planet: str, sign_name: str) -> bool:
        if planet in OWN_SIGNS and sign_name in OWN_SIGNS[planet]:
            return True
        if planet in EXALTATION and EXALTATION[planet][0] == sign_name:
            return True
        if planet in MOOLATRIKONA and MOOLATRIKONA[planet][0] == sign_name:
            return True
        return False

    result = {}
    vargas_dict = chart.vargas if hasattr(chart, "vargas") else {}

    for p in PLANETS_9:
        dv_count = 0
        sv_count = 0
        dv_vargas_list = []
        sv_vargas_list = []

        for v in dasa_vargas:
            v_dict = vargas_dict.get(v, {})
            v_data = v_dict.get(p, {}) if isinstance(v_dict, dict) else {}
            v_sign = v_data.get("sign") if isinstance(v_data, dict) else (v_data if isinstance(v_data, str) else None)
            if v_sign and _is_dignified(p, v_sign):
                dv_count += 1
                dv_vargas_list.append(f"{v}:{v_sign}")

        for v in shodasa_vargas:
            v_dict = vargas_dict.get(v, {})
            v_data = v_dict.get(p, {}) if isinstance(v_dict, dict) else {}
            v_sign = v_data.get("sign") if isinstance(v_data, dict) else (v_data if isinstance(v_data, str) else None)
            if v_sign and _is_dignified(p, v_sign):
                sv_count += 1
                sv_vargas_list.append(f"{v}:{v_sign}")

        result[p] = {
            "dasa_varga_count": dv_count,
            "dasa_varga_title": dasa_names.get(dv_count, f"{dv_count}-Swavarga" if dv_count else "None"),
            "dasa_varga_charts": dv_vargas_list,
            "shodasa_varga_count": sv_count,
            "shodasa_varga_title": shodasa_names.get(sv_count, f"{sv_count}-Swavarga" if sv_count else "None"),
            "shodasa_varga_charts": sv_vargas_list,
        }

    return result


# ══════════════════════════════════════════════════════════════════════════════
# 4. SAYANADI 12 AVASTHAS (BPHS Chapter 45)
# ══════════════════════════════════════════════════════════════════════════════

def calc_sayanadi_avasthas(chart) -> Dict[str, Dict[str, Any]]:
    """
    Calculate the 12 Sayanadi Avasthas (activities / states) for all 9 planets:
    1. Sayana (Lying down / Resting)
    2. Upaveshana (Sitting)
    3. Netrapani (Eyes on hands / Weeping)
    4. Prakasha (Radiant / Shining)
    5. Gamana (Moving / Going)
    6. Agamana (Coming / Returning)
    7. Sabha (In assembly / Council)
    8. Agama (Acquisition / Arrival)
    9. Bhojana (Eating / Feasting)
    10. Nrityalipsa (Desiring to dance / Energetic)
    11. Kautuka (Playful / Eager / Joyful)
    12. Nidra (Sleeping)

    BPHS Formula:
      Product = (Np * P * Nv) + M + G + L
      Avastha = Product % 12
    """
    sayanadi_names = [
        "Nidra", "Sayana", "Upaveshana", "Netrapani", "Prakasha",
        "Gamana", "Agamana", "Sabha", "Agama", "Bhojana",
        "Nrityalipsa", "Kautuka"
    ]
    sayanadi_desc = {
        "Sayana": "Lying down / resting — tranquil, passive contemplation",
        "Upaveshana": "Sitting — settled, firm, administrative focus",
        "Netrapani": "Eyes on hands — emotional, anxious, cautious vigilance",
        "Prakasha": "Radiant / shining — exalted glory, renown, high manifestation",
        "Gamana": "Moving / going away — itinerant, ambitious, changing horizons",
        "Agamana": "Coming / returning — reunion, acquisition, domestic blessings",
        "Sabha": "In assembly / court — honored among peers, leadership, eloquence",
        "Agama": "Arrival / acquisition — gain of knowledge, wealth, prosperity",
        "Bhojana": "Eating / feasting — enjoyment of comforts, culinary pleasures, indulgence",
        "Nrityalipsa": "Desiring to dance — highly active, spirited, artistic exuberance",
        "Kautuka": "Eager / joyful — curiosity, celebration, romantic delights",
        "Nidra": "Sleeping / slumber — dormant potential, introversion, slow fructification",
    }

    nak_names = [n["name"] for n in NAKSHATRAS]
    planet_num_map = {
        "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
        "Jupiter": 5, "Venus": 6, "Saturn": 7, "Rahu": 8, "Ketu": 9
    }

    # Ghati of birth calculation
    ss = chart.sunrise_sunset or {}
    sunrise_str = ss.get("sunrise", "06:00:00")
    try:
        sh, sm, ss_sec = [float(x) for x in sunrise_str.split(":")]
        sunrise_hours = sh + sm / 60.0 + ss_sec / 3600.0
    except Exception:
        sunrise_hours = 6.0

    tob_str = chart.birth_data.get("time", "12:00:00")
    try:
        th, tm, ts_sec = [float(x) for x in tob_str.split(":")]
        birth_hours = th + tm / 60.0 + ts_sec / 3600.0
    except Exception:
        birth_hours = 12.0

    hours_from_rise = (birth_hours - sunrise_hours) % 24.0
    ghati_of_birth = int(hours_from_rise * 2.5)

    moon_pos = chart.positions.get("Moon", {})
    m_nak_name = moon_pos.get("nakshatra", "Ashwini")
    m_nak = (nak_names.index(m_nak_name) if m_nak_name in nak_names else 0) + 1

    lagna_pos = chart.positions.get("Lagna", {})
    l_rashi = SIGN_INDEX.get(lagna_pos.get("sign", "Aries"), 0) + 1

    result = {}

    for p in PLANETS_9:
        pos = chart.positions.get(p)
        if not pos or not isinstance(pos, dict):
            continue

        p_nak_name = pos.get("nakshatra", "Ashwini")
        np_nak = (nak_names.index(p_nak_name) if p_nak_name in nak_names else 0) + 1
        p_num = planet_num_map.get(p, 1)
        deg_in_sign = pos.get("degree_in_sign", 0.0)
        nv_navamsa = int(deg_in_sign / (30.0 / 9.0)) + 1

        # BPHS Product = (Np * P * Nv) + M + G + L
        product = int((np_nak * p_num * nv_navamsa) + m_nak + ghati_of_birth + l_rashi)
        avastha_idx = product % 12
        avastha_name = sayanadi_names[avastha_idx]

        result[p] = {
            "avastha": avastha_name,
            "avastha_index": avastha_idx,
            "product": product,
            "description": sayanadi_desc.get(avastha_name, ""),
        }

    return result


# ══════════════════════════════════════════════════════════════════════════════
# 5. DETAILED CLASSICAL PINDAYU AYURDAYA (BPHS Chapter 43)
# ══════════════════════════════════════════════════════════════════════════════

def calc_pindayu_detailed(chart) -> Dict[str, Any]:
    """
    Calculate Classical Pindayu Longevity (Ayurdaya) with all 3 BPHS reductions:
    - Base years at exaltation: Sun=19, Moon=25, Mars=15, Mercury=12, Jupiter=15, Venus=21, Saturn=20
    - Base years at debilitation: Half of exaltation
    - Linear interpolation for intermediate positions.
    - Chakrapatha Harana (12H..7H malefic reduction)
    - Astangata Harana (Combustion 1/2 reduction, Venus & Saturn exempt)
    - Shatrukshetra Harana (Enemy sign 1/3 reduction, Retrograde exempt)
    - Bharana (Exaltation / Retrograde enhancement)
    """
    max_years = {
        "Sun": 19.0, "Moon": 25.0, "Mars": 15.0,
        "Mercury": 12.0, "Jupiter": 15.0, "Venus": 21.0, "Saturn": 20.0
    }
    exalt_points = {
        "Sun": 10.0, "Moon": 33.0, "Mars": 298.0,
        "Mercury": 165.0, "Jupiter": 95.0, "Venus": 357.0, "Saturn": 200.0
    }

    raw_contributions = {}
    reductions = {}

    sun_lon = chart.positions.get("Sun", {}).get("longitude", 0.0)

    for p in PLANETS_7:
        pos = chart.positions.get(p, {})
        lon = pos.get("longitude", 0.0)
        ex = exalt_points[p]
        deb = (ex + 180.0) % 360.0

        # Arc distance from debilitation
        arc = (lon - deb + 360.0) % 360.0
        if arc > 180.0:
            arc = 360.0 - arc

        # Base contribution = (max_years / 2) + (max_years / 2) * (arc / 180)
        base = (max_years[p] / 2.0) + (max_years[p] / 2.0) * (arc / 180.0)
        curr = base

        # 1. Shatrukshetra Harana (1/3 reduction if in enemy sign and not retrograde)
        dignity = pos.get("dignity", "Neutral")
        is_retro = pos.get("is_retrograde", False)
        shatru_red = 0.0
        if "Enemy" in dignity and not is_retro:
            shatru_red = curr * (1.0 / 3.0)
            curr -= shatru_red

        # 2. Astangata Harana (1/2 reduction if combust, Venus and Saturn exempt)
        astangata_red = 0.0
        if p not in ("Venus", "Saturn"):
            sep = abs((lon - sun_lon + 180.0) % 360.0 - 180.0)
            orb = 14.0 if p == "Mercury" else (17.0 if p == "Mars" else 11.0)
            if sep <= orb:
                astangata_red = curr * 0.5
                curr -= astangata_red

        # 3. Chakrapatha Harana (12H..7H reduction based on house)
        house = pos.get("house_rashi", 1)
        chakra_red = 0.0
        if house in [7, 8, 9, 10, 11, 12]:
            fractions_malefic = {12: 1.0, 11: 0.5, 10: 1/3, 9: 1/4, 8: 1/5, 7: 1/6}
            fractions_benefic = {12: 0.5, 11: 0.25, 10: 1/6, 9: 1/8, 8: 1/10, 7: 1/12}
            is_mal = p in ["Sun", "Mars", "Saturn"]
            frac = fractions_malefic[house] if is_mal else fractions_benefic[house]
            chakra_red = curr * frac
            curr -= chakra_red

        # 4. Bharana (Enhancement for Retrograde / Exaltation)
        bharana_add = 0.0
        if is_retro or "Exalted" in dignity:
            bharana_add = curr * 0.5  # up to 50% enhancement in classical Parashara
            curr += bharana_add

        raw_contributions[p] = round(base, 2)
        reductions[p] = {
            "base_years": round(base, 2),
            "shatru_reduction": round(shatru_red, 2),
            "astangata_reduction": round(astangata_red, 2),
            "chakrapatha_reduction": round(chakra_red, 2),
            "bharana_addition": round(bharana_add, 2),
            "final_years": round(curr, 2),
        }

    # Lagna Contribution (Lagna deg / 30 * 12 years if lord strong, else base)
    asc_deg = chart.positions.get("Lagna", {}).get("degree_in_sign", 0.0)
    lagna_contrib = (asc_deg / 30.0) * (max_years.get(chart.lordships.get(1), 12.0) / 2.0)

    total_years = sum(r["final_years"] for r in reductions.values()) + lagna_contrib
    years_int = int(total_years)
    months_int = int((total_years - years_int) * 12.0)
    days_int = int((((total_years - years_int) * 12.0) - months_int) * 30.0)

    return {
        "system": "Pindayu (BPHS Chapter 43)",
        "total_years_decimal": round(total_years, 2),
        "formatted_longevity": f"{years_int} Years, {months_int} Months, {days_int} Days",
        "category": "Poornayu (Long Life >70 yrs)" if total_years >= 70 else ("Madhyayu (Middle Life 36-70 yrs)" if total_years >= 36 else "Alpayu (Short Life <36 yrs)"),
        "lagna_contribution": round(lagna_contrib, 2),
        "graha_breakdown": reductions,
    }
