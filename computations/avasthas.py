"""
avasthas.py — Complete Parashara Avasthas Engine (BPHS Ch. 45).
Computes all 4 classical Avastha dimensions for all 9 Grahas:
1. Baladi Avasthas (5 states: Bala, Kumara, Yuva, Vriddha, Mrita)
2. Jagradadi Avasthas (3 alertness states: Jaagrita [Awake], Swapna [Dreaming], Sushupta [Deep Sleep])
3. Deeptadi Avasthas (9 moods: Deepta, Swastha, Mudita, Saanta, Deena, Duhkhita, Vikala, Khala, Kopa)
4. Shayanadi Avasthas (12 activities: Sayana, Upaveshana, Netrapani, Prakasana, Gamana, Agamana, Sabha, Agama, Bhojana, Nrityalipsa, Kautuka, Nidra)
"""

from typing import Dict, Any
from ..core.constants import (
    SIGNS, SIGN_INDEX, NAKSHATRAS, PLANETS_7, PLANETS_9,
    EXALTATION, DEBILITATION, OWN_SIGNS, NATURAL_FRIENDS, NATURAL_ENEMIES
)

BALADI_ODD = ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"]
BALADI_EVEN = ["Mrita", "Vriddha", "Yuva", "Kumara", "Bala"]

BALADI_FRUITS = {
    "Bala": {"name": "Bala (Infant)", "strength_pct": 25, "desc": "1/4 fruit — nascent, emerging potential"},
    "Kumara": {"name": "Kumara (Youthful)", "strength_pct": 50, "desc": "1/2 fruit — energetic, growing capacity"},
    "Yuva": {"name": "Yuva (Adult/Prime)", "strength_pct": 100, "desc": "Full fruit — peak vitality and executive manifestation"},
    "Vriddha": {"name": "Vriddha (Aged/Mature)", "strength_pct": 12.5, "desc": "Minimal direct fruit — experienced, reflective"},
    "Mrita": {"name": "Mrita (Deceased/Dormant)", "strength_pct": 0, "desc": "Zero direct fruit — dormant, requiring external activation"},
}

JAGRADADI_STATES = {
    "Jaagrita": {"name": "Jaagrita (Awake)", "power": 1.0, "desc": "100% conscious, alert, and actively manifesting"},
    "Swapna": {"name": "Swapna (Dreaming)", "power": 0.5, "desc": "50% conscious, semi-alert, subjective expression"},
    "Sushupta": {"name": "Sushupta (Deep Sleep)", "power": 0.0, "desc": "0% conscious, dormant, subconscious/passive only"},
}

DEEPTADI_MOODS = {
    "Deepta": {"name": "Deepta (Exalted/Radiant)", "desc": "Highest glory, regal status, triumphant results"},
    "Swastha": {"name": "Swastha (Own Sign/Comfortable)", "desc": "Self-contained, content, enduring security"},
    "Mudita": {"name": "Mudita (Delighted/Friendly)", "desc": "Joyful, collaborative, harmonious expansion"},
    "Saanta": {"name": "Saanta (Peaceful/Neutral)", "desc": "Tranquil, balanced, moderate steady results"},
    "Deena": {"name": "Deena (Depressed/Inimical)", "desc": "Strained, anxious, uphill struggle"},
    "Duhkhita": {"name": "Duhkhita (Agonized/Debilitated)", "desc": "Frustrated, compromised, acute distress"},
    "Vikala": {"name": "Vikala (Mutilated/Combust)", "desc": "Impaired by solar proximity, hidden vulnerability"},
    "Khala": {"name": "Khala (Defeated in War)", "desc": "Subjugated by planetary opponent, lost authority"},
    "Kopa": {"name": "Kopa (Enraged/Malefic Influence)", "desc": "Agitated by harsh malefic aspects/conjunctions"},
}

SAYANADI_NAMES = [
    "Nidra", "Sayana", "Upaveshana", "Netrapani", "Prakasha",
    "Gamana", "Agamana", "Sabha", "Agama", "Bhojana",
    "Nrityalipsa", "Kautuka"
]

SAYANADI_DESC = {
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


def calc_baladi_avastha(sign: str, degree_in_sign: float) -> Dict[str, Any]:
    """Calculate Baladi Avastha based on odd/even sign and degree."""
    sign_idx = SIGN_INDEX.get(sign, 0)
    is_odd = (sign_idx % 2 == 0) # Aries=0 is Odd sign
    
    div = int(degree_in_sign / 6.0)
    div = min(max(div, 0), 4)
    
    state = BALADI_ODD[div] if is_odd else BALADI_EVEN[div]
    fruit_info = BALADI_FRUITS[state]
    
    return {
        "state": state,
        "sign_type": "Odd" if is_odd else "Even",
        "division": div + 1,
        "strength_percentage": fruit_info["strength_pct"],
        "description": fruit_info["desc"]
    }


def calc_jagradadi_avastha(planet: str, sign: str, dignity: str) -> Dict[str, Any]:
    """
    Calculate Jagradadi (Alertness) Avastha:
    - Exalted or Own Sign -> Jaagrita (Awake)
    - Friendly or Neutral Sign -> Swapna (Dreaming)
    - Enemy or Debilitated Sign -> Sushupta (Deep Sleep)
    """
    if planet in ("Rahu", "Ketu"):
        # Nodes: exalted in Tau/Sco or own in Vir/Pis/Gem/Sag
        if dignity in ("Exalted", "Own Sign", "Moolatrikona"):
            state = "Jaagrita"
        elif "Enemy" in dignity or "Debilitated" in dignity:
            state = "Sushupta"
        else:
            state = "Swapna"
    else:
        if dignity in ("Exalted", "Own Sign", "Moolatrikona") or sign in OWN_SIGNS.get(planet, []):
            state = "Jaagrita"
        elif "Enemy" in dignity or dignity == "Debilitated":
            state = "Sushupta"
        else:
            state = "Swapna"
            
    info = JAGRADADI_STATES[state]
    return {
        "state": state,
        "power": info["power"],
        "description": info["desc"]
    }


def calc_deeptadi_avastha(planet: str, dignity: str, is_combust: bool = False, is_war_loser: bool = False) -> Dict[str, Any]:
    """Calculate Deeptadi (Psychological Mood) Avastha."""
    if is_war_loser:
        state = "Khala"
    elif is_combust and planet not in ("Sun", "Rahu", "Ketu"):
        state = "Vikala"
    elif dignity == "Exalted":
        state = "Deepta"
    elif dignity in ("Own Sign", "Moolatrikona"):
        state = "Swastha"
    elif "Great Friend" in dignity or "Friendly" in dignity or dignity == "Friend":
        state = "Mudita"
    elif "Neutral" in dignity:
        state = "Saanta"
    elif "Enemy" in dignity:
        state = "Deena"
    elif dignity == "Debilitated":
        state = "Duhkhita"
    else:
        state = "Saanta"
        
    info = DEEPTADI_MOODS.get(state, DEEPTADI_MOODS["Saanta"])
    return {
        "state": state,
        "description": info["desc"]
    }


def calc_complete_avasthas(chart) -> Dict[str, Dict[str, Any]]:
    """Compute the 4-tier classical Avastha matrix for all planets."""
    positions = chart.positions or {}
    rashi = chart.rashi_chart or {}
    combustion = getattr(chart, "combustion", {}) or {}
    yuddha = getattr(chart, "yuddha", {}) or {}
    losers = yuddha.get("losers", []) if isinstance(yuddha, dict) else []
    
    # Calculate Sayanadi avasthas
    sayanadi_dict = {}
    try:
        from .classical_extensions import calc_sayanadi_avasthas
        sayanadi_dict = calc_sayanadi_avasthas(chart)
    except Exception:
        pass
        
    result = {}
    for p in PLANETS_9:
        pos = positions.get(p, {})
        rc = rashi.get(p, {})
        if not pos or not isinstance(pos, dict):
            continue
            
        sign = pos.get("sign", "Aries")
        deg_in_sign = pos.get("degree_in_sign", 0.0)
        dignity = rc.get("dignity", pos.get("dignity", "Neutral"))
        
        is_comb = combustion.get(p, {}).get("is_combust", False) if isinstance(combustion, dict) else False
        is_loser = p in losers
        
        baladi = calc_baladi_avastha(sign, deg_in_sign)
        jagradadi = calc_jagradadi_avastha(p, sign, dignity)
        deeptadi = calc_deeptadi_avastha(p, dignity, is_comb, is_loser)
        sayanadi = sayanadi_dict.get(p, {})
        
        result[p] = {
            "planet": p,
            "sign": sign,
            "degree_in_sign": deg_in_sign,
            "dignity": dignity,
            "baladi": baladi,
            "jagradadi": jagradadi,
            "deeptadi": deeptadi,
            "sayanadi": sayanadi.get("avastha", "Sayana"),
            "sayanadi_detail": sayanadi,
            "composite_summary": f"{baladi['state']} | {jagradadi['state']} | {deeptadi['state']} | {sayanadi.get('avastha', 'Sayana')}"
        }
        
    return result
