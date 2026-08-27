"""
wealth.py — Wealth & Dhana Determination Engine (rules.md §30).
Algorithmic data extraction and composite Dhana Scoring:
- 2nd, 11th, 5th, 9th Lordship Interlinks
- Indu Lagna & Sree Lagna Fortitude
- Ashtakavarga Wealth Metrics (SAV 11H vs 10H/12H, Jupiter BAV)
- Classical Dhana Yoga Weighted Score (0 to 25+)
"""

from typing import Dict, Any, List
from ..core.constants import SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_7
from ..core.mapping import house_to_sign, sign_to_house


def calc_wealth_profile(chart) -> Dict[str, Any]:
    """
    Calculate full wealth profile and composite Dhana Yoga score.
    """
    positions = chart.positions or {}
    rashi = chart.rashi_chart or {}
    lordships = getattr(chart, "lordships", {}) or {}
    ashtakavarga = getattr(chart, "ashtakavarga", {}) or {}
    sav_by_house = ashtakavarga.get("by_house", {})
    bav = ashtakavarga.get("bav", {})
    
    # Lords
    l1 = lordships.get(1)
    l2 = lordships.get(2)
    l5 = lordships.get(5)
    l9 = lordships.get(9)
    l11 = lordships.get(11)
    
    h1_house = rashi.get(l1, {}).get("house_rashi", 1)
    h2_house = rashi.get(l2, {}).get("house_rashi", 2)
    h5_house = rashi.get(l5, {}).get("house_rashi", 5)
    h9_house = rashi.get(l9, {}).get("house_rashi", 9)
    h11_house = rashi.get(l11, {}).get("house_rashi", 11)
    
    l2_dignity = rashi.get(l2, {}).get("dignity", "Neutral")
    l11_dignity = rashi.get(l11, {}).get("dignity", "Neutral")
    
    jup_house = rashi.get("Jupiter", {}).get("house_rashi", 0)
    ven_house = rashi.get("Venus", {}).get("house_rashi", 0)
    
    # Indu Lagna
    extra = getattr(chart, "extra_lagnas", {}) or {}
    indu_data = extra.get("indu_lagna", {})
    indu_sign = indu_data.get("sign", "Aries")
    indu_lord = SIGN_LORDS.get(indu_sign, "Mars")
    indu_lord_house = rashi.get(indu_lord, {}).get("house_rashi", 1)
    indu_lord_in_kendra_trikona = indu_lord_house in (1, 4, 7, 10, 5, 9)
    
    # SAV metrics
    sav_11 = sav_by_house.get(11, 28)
    sav_10 = sav_by_house.get(10, 28)
    sav_12 = sav_by_house.get(12, 28)
    sav_2 = sav_by_house.get(2, 28)
    
    # Jupiter BAV in 11H
    jup_bav = bav.get("Jupiter", [])
    h11_sign_idx = SIGN_INDEX.get(house_to_sign(11, chart.lagna_index), 0)
    jup_bav_11 = jup_bav[h11_sign_idx] if len(jup_bav) > h11_sign_idx else 0
    
    # Yoga check helpers
    aspects = getattr(chart, "aspects", {}) or {}
    def are_connected(p1, p2):
        if not p1 or not p2: return False
        h_p1 = rashi.get(p1, {}).get("house_rashi")
        h_p2 = rashi.get(p2, {}).get("house_rashi")
        if h_p1 == h_p2: return True
        return (h_p2 in aspects.get(p1, [])) or (h_p1 in aspects.get(p2, []))
        
    # Weighted scoring criteria (rules.md §30.2)
    score_items = []
    
    # 1. 2L-11L connection (w=3)
    if are_connected(l2, l11):
        score_items.append(("2L-11L conjunction/mutual aspect", 3))
    # 2. 5L-9L connection (w=3)
    if are_connected(l5, l9):
        score_items.append(("5L-9L conjunction/mutual aspect", 3))
    # 3. 1L-2L connection (w=2)
    if are_connected(l1, l2):
        score_items.append(("1L-2L conjunction/mutual aspect", 2))
    # 4. 1L-9L connection (w=3)
    if are_connected(l1, l9):
        score_items.append(("1L-9L Dhana connection", 3))
    # 5. Jupiter in Dhana/Trikona (2, 11, 5, 9) (w=2)
    if jup_house in (2, 11, 5, 9):
        score_items.append(("Jupiter in Dhana/Trikona house", 2))
    # 6. Venus in 2, 4, 7 (w=1)
    if ven_house in (2, 4, 7):
        score_items.append(("Venus in 2H/4H/7H wealth/comfort axis", 1))
    # 7. 11L own sign or exalted (w=2)
    if l11_dignity in ("Own Sign", "Exalted", "Moolatrikona"):
        score_items.append(("11th Lord exalted or in own sign", 2))
    # 8. 2L own sign or exalted (w=2)
    if l2_dignity in ("Own Sign", "Exalted", "Moolatrikona"):
        score_items.append(("2nd Lord exalted or in own sign", 2))
    # 9. Indu Lagna Lord in Kendra/Trikona (w=2)
    if indu_lord_in_kendra_trikona:
        score_items.append(("Indu Lagna Lord in Kendra/Trikona", 2))
    # 10. SAV 11H >= 30 (w=1)
    if sav_11 >= 30:
        score_items.append(("11th House SAV >= 30 (High Gains Capacity)", 1))
        
    total_dhana_score = sum(w for _, w in score_items)
    
    # AV Wealth Flags (rules.md §30.4)
    av_flags = {
        "11H_gt_10H": sav_11 > sav_10,  # Gains exceed effort (KN Rao rule)
        "11H_gt_12H": sav_11 > sav_12,  # Income exceeds expenditure
        "2H_gt_avg": sav_2 > (337.0 / 12.0), # Wealth accumulation above average
        "jupiter_BAV_11H_bindus": jup_bav_11,
    }
    
    return {
        "dhana_score": total_dhana_score,
        "dhana_score_breakdown": score_items,
        "wealth_category": "EXTRAORDINARY" if total_dhana_score >= 10 else ("HIGH" if total_dhana_score >= 6 else "MODERATE"),
        "key_lords": {
            "1L": {"lord": l1, "house": h1_house},
            "2L": {"lord": l2, "house": h2_house, "dignity": l2_dignity},
            "5L": {"lord": l5, "house": h5_house},
            "9L": {"lord": l9, "house": h9_house},
            "11L": {"lord": l11, "house": h11_house, "dignity": l11_dignity},
        },
        "indu_lagna": {
            "sign": indu_sign,
            "lord": indu_lord,
            "lord_house": indu_lord_house,
            "is_kendra_trikona": indu_lord_in_kendra_trikona
        },
        "ashtakavarga_wealth_flags": av_flags,
        "sav_wealth_houses": {
            "2H_SAV": sav_2,
            "10H_SAV": sav_10,
            "11H_SAV": sav_11,
            "12H_SAV": sav_12
        },
        "wealth_manifestation_triggers": [l2, l11, l5, l9, l1, "Jupiter", "Venus", indu_lord]
    }
