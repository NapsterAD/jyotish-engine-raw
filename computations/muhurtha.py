"""
muhurtha.py — Muhurtha Essentials & Panchanga Shuddhi Engine (rules.md §32).
Provides electional purity scoring for any query moment:
1. Panchanga Shuddhi (Tithi, Nakshatra, Yoga, Karana, Vara)
2. Chandrabala (Lunar placement from natal Moon)
3. Tarabala (9 Nava-Tara strength matrix)
4. Lagna Shuddhi (Ascendant purity & 8H/7H verification)
5. Event-Specific Weekday Suitability Lookup
"""

from typing import Dict, Any, List
from ..core.constants import SIGNS, SIGN_INDEX, NAKSHATRAS, NAKSHATRA_SPAN

INAUSPICIOUS_TITHIS = {4, 9, 14, 19, 24, 29, 30} # Rikta tithis (4, 9, 14 in both pakshas) + Amavasya (30)
INAUSPICIOUS_YOGAS = {1, 6, 9, 10, 13, 15, 17, 19, 27} # Vishkambha, Atiganda, Shoola, Ganda, Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti
INAUSPICIOUS_NAKSHATRAS = {"Bharani", "Ashlesha", "Jyeshtha"}

EVENT_WEEKDAYS = {
    "Marriage": {"favorable": ["Monday", "Wednesday", "Thursday", "Friday"], "avoid": ["Tuesday", "Saturday", "Sunday"]},
    "Business_Start": {"favorable": ["Wednesday", "Thursday", "Friday"], "avoid": ["Tuesday", "Saturday"]},
    "Travel": {"favorable": ["Monday", "Wednesday", "Friday"], "avoid": ["Tuesday", "Sunday"]},
    "Surgery": {"favorable": ["Tuesday", "Saturday"], "avoid": ["Monday", "Friday"]},
    "Property_Purchase": {"favorable": ["Thursday", "Friday"], "avoid": ["Tuesday"]},
    "Education_Commencement": {"favorable": ["Wednesday", "Thursday"], "avoid": ["Tuesday", "Saturday"]},
}

TARA_NAMES = [
    "Janma", "Sampat", "Vipat", "Kshema", "Pratyak",
    "Sadhana", "Naidhana (Vadh)", "Mitra", "Parama Mitra"
]

TARA_CLASSIFICATION = {
    "Janma": {"auspicious": True, "score": 0.0, "status": "Neutral/Self"},
    "Sampat": {"auspicious": True, "score": 1.0, "status": "Highly Auspicious (Wealth/Gains)"},
    "Vipat": {"auspicious": False, "score": -1.0, "status": "Inauspicious (Danger/Loss - Avoid)"},
    "Kshema": {"auspicious": True, "score": 0.8, "status": "Auspicious (Protection/Well-being)"},
    "Pratyak": {"auspicious": False, "score": -0.8, "status": "Inauspicious (Obstacles/Conflict - Avoid)"},
    "Sadhana": {"auspicious": True, "score": 1.0, "status": "Highly Auspicious (Achievement/Success)"},
    "Naidhana (Vadh)": {"auspicious": False, "score": -1.0, "status": "Severely Inauspicious (Fatal/Destructive - Strictly Avoid)"},
    "Mitra": {"auspicious": True, "score": 0.8, "status": "Auspicious (Friendly/Alliance)"},
    "Parama Mitra": {"auspicious": True, "score": 1.0, "status": "Supreme Auspicious (Highest Gain)"},
}


def calc_panchanga_shuddhi(tithi_num: int, nakshatra_name: str, yoga_num: int, karana_name: str, weekday_name: str, event_type: str = "General") -> Dict[str, Any]:
    """Validate the 5 limbs of Panchanga for electional purity."""
    tithi_ok = tithi_num not in INAUSPICIOUS_TITHIS
    nak_ok = nakshatra_name not in INAUSPICIOUS_NAKSHATRAS
    yoga_ok = yoga_num not in INAUSPICIOUS_YOGAS
    karana_ok = "Vishti" not in karana_name and "Bhadra" not in karana_name
    
    event_rules = EVENT_WEEKDAYS.get(event_type, {"favorable": [], "avoid": ["Tuesday"]})
    vara_ok = weekday_name not in event_rules.get("avoid", [])
    
    shuddhi_flags = {
        "tithi_purity": tithi_ok,
        "nakshatra_purity": nak_ok,
        "yoga_purity": yoga_ok,
        "karana_purity": karana_ok,
        "vara_purity": vara_ok,
    }
    
    is_pure = all(shuddhi_flags.values())
    purity_score = sum(1 for v in shuddhi_flags.values() if v) / 5.0 * 100.0
    
    return {
        "is_panchanga_shuddha": is_pure,
        "purity_percentage": purity_score,
        "limb_checks": shuddhi_flags,
        "flaws_detected": [k for k, v in shuddhi_flags.items() if not v]
    }


def calc_chandrabala(transit_moon_sign: str, natal_moon_sign: str, event_type: str = "General") -> Dict[str, Any]:
    """Calculate Chandrabala (Lunar Transit Strength relative to Natal Moon)."""
    t_idx = SIGN_INDEX.get(transit_moon_sign, 0)
    n_idx = SIGN_INDEX.get(natal_moon_sign, 0)
    
    house_from_moon = ((t_idx - n_idx) % 12) + 1
    
    # Favorable: 1, 3, 6, 7, 10, 11
    # Unfavorable: 2, 5, 8, 9, 12
    # 4H is OK for fixed properties/agriculture
    if house_from_moon in (1, 3, 6, 7, 10, 11):
        favorable = True
        status = "EXCELLENT"
    elif house_from_moon == 4 and event_type in ("Property_Purchase", "Real_Estate", "Home_Entry"):
        favorable = True
        status = "FAVORABLE_FOR_PROPERTY"
    else:
        favorable = False
        status = "UNFAVORABLE"
        
    return {
        "house_from_natal_moon": house_from_moon,
        "is_favorable": favorable,
        "status": status,
        "description": f"Transit Moon is in House {house_from_moon} from Natal Moon"
    }


def calc_tarabala(transit_moon_longitude: float, natal_moon_longitude: float) -> Dict[str, Any]:
    """Calculate Tarabala (9 Nava-Tara strength)."""
    t_nak = int((transit_moon_longitude % 360.0) / NAKSHATRA_SPAN) % 27
    n_nak = int((natal_moon_longitude % 360.0) / NAKSHATRA_SPAN) % 27
    
    tara_idx = ((t_nak - n_nak) % 9)
    tara_num = tara_idx + 1
    tara_name = TARA_NAMES[tara_idx]
    info = TARA_CLASSIFICATION[tara_name]
    
    return {
        "tara_number": tara_num,
        "tara_name": tara_name,
        "is_auspicious": info["auspicious"],
        "scoring_weight": info["score"],
        "status": info["status"],
        "transit_nakshatra": NAKSHATRAS[t_nak]["name"],
        "natal_nakshatra": NAKSHATRAS[n_nak]["name"]
    }


def evaluate_muhurtha(chart, muhurtha_chart, event_type: str = "General") -> Dict[str, Any]:
    """Comprehensive Muhurtha Evaluation of a proposed chart against native's birth chart."""
    m_panchang = muhurtha_chart.panchang or {}
    tithi_num = m_panchang.get("tithi", {}).get("number", 1)
    nak_name = m_panchang.get("nakshatra", {}).get("name", "Ashwini")
    yoga_num = m_panchang.get("yoga", {}).get("number", 1)
    karana_name = m_panchang.get("karana", {}).get("name", "Bava")
    weekday_name = m_panchang.get("vara", {}).get("day", "Wednesday")
    
    p_shuddhi = calc_panchanga_shuddhi(tithi_num, nak_name, yoga_num, karana_name, weekday_name, event_type)
    
    t_moon_sign = muhurtha_chart.positions.get("Moon", {}).get("sign", "Aries")
    n_moon_sign = chart.positions.get("Moon", {}).get("sign", "Aries")
    c_bala = calc_chandrabala(t_moon_sign, n_moon_sign, event_type)
    
    t_moon_lon = muhurtha_chart.positions.get("Moon", {}).get("longitude", 0.0)
    n_moon_lon = chart.positions.get("Moon", {}).get("longitude", 0.0)
    t_bala = calc_tarabala(t_moon_lon, n_moon_lon)
    
    # Lagna Shuddhi
    m_lagna_sign = muhurtha_chart.lagna_sign
    n_lagna_sign = chart.lagna_sign
    m_lagna_idx = SIGN_INDEX.get(m_lagna_sign, 0)
    n_lagna_idx = SIGN_INDEX.get(n_lagna_sign, 0)
    
    is_8th_from_natal = ((m_lagna_idx - n_lagna_idx) % 12) + 1 == 8
    
    lagna_shuddhi = {
        "is_not_8th_from_natal": not is_8th_from_natal,
        "muhurtha_lagna": m_lagna_sign,
        "natal_lagna": n_lagna_sign
    }
    
    overall_approved = (p_shuddhi["is_panchanga_shuddha"] and c_bala["is_favorable"] and t_bala["is_auspicious"] and not is_8th_from_natal)
    
    return {
        "event_type": event_type,
        "is_approved_muhurtha": overall_approved,
        "panchanga_shuddhi": p_shuddhi,
        "chandrabala": c_bala,
        "tarabala": t_bala,
        "lagna_shuddhi": lagna_shuddhi,
    }
