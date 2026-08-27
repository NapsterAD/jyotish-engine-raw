"""
sudarshana.py — Sudarshana Chakra Dasha Engine (rules.md §27).
Overlays three concurrent house progressions:
1. Physical / Body (Lagna)
2. Mind / Perception (Chandra / Moon)
3. Soul / Authority (Surya / Sun)
Each advances one house/sign per completed year of life (0-indexed age).
Also supports monthly sub-cycles (1 month per sign inside the yearly sign).
"""

from typing import Dict, Any, List
from ..core.constants import SIGNS, SIGN_INDEX, SIGN_LORDS
from ..core.mapping import house_to_sign_index, sign_to_house


def calc_sudarshana_chakra_dasha(chart, max_years: int = 100) -> Dict[str, Any]:
    """
    Calculate Sudarshana Chakra Dasha progression for years 1 to max_years.
    
    Returns:
        Dict with:
        - lagna_sign, moon_sign, sun_sign
        - progressions: list of yearly entries (age, active signs, lords, occupants, cross_aspects)
        - current_year_analysis: detailed breakdown for native's current age
    """
    positions = chart.positions or {}
    rashi_chart = chart.rashi_chart or {}
    
    lagna_sign = chart.lagna_sign or "Aries"
    lagna_idx = SIGN_INDEX.get(lagna_sign, 0)
    
    moon_sign = positions.get("Moon", {}).get("sign", "Aries")
    moon_idx = SIGN_INDEX.get(moon_sign, 0)
    
    sun_sign = positions.get("Sun", {}).get("sign", "Aries")
    sun_idx = SIGN_INDEX.get(sun_sign, 0)
    
    # Map planets in each sign
    planets_in_sign = {s: [] for s in SIGNS}
    for p, pos in positions.items():
        if p == "Lagna" or not isinstance(pos, dict):
            continue
        psign = pos.get("sign")
        if psign in planets_in_sign:
            planets_in_sign[psign].append(p)
            
    progressions = []
    
    for age in range(0, max_years):
        # Shift count for this age cycle
        cycle_shift = age % 12
        
        # 1. Lagna progression
        l_sign_idx = (lagna_idx + cycle_shift) % 12
        l_sign = SIGNS[l_sign_idx]
        l_house = cycle_shift + 1
        l_lord = SIGN_LORDS[l_sign]
        l_planets = planets_in_sign[l_sign]
        
        # 2. Moon progression
        m_sign_idx = (moon_idx + cycle_shift) % 12
        m_sign = SIGNS[m_sign_idx]
        m_house = cycle_shift + 1
        m_lord = SIGN_LORDS[m_sign]
        m_planets = planets_in_sign[m_sign]
        
        # 3. Sun progression
        s_sign_idx = (sun_idx + cycle_shift) % 12
        s_sign = SIGNS[s_sign_idx]
        s_house = cycle_shift + 1
        s_lord = SIGN_LORDS[s_sign]
        s_planets = planets_in_sign[s_sign]
        
        # Cross-layer activations
        all_activated_planets = list(set(l_planets + m_planets + s_planets))
        double_activated = [p for p in all_activated_planets if (p in l_planets) + (p in m_planets) + (p in s_planets) >= 2]
        triple_activated = [p for p in all_activated_planets if (p in l_planets) and (p in m_planets) and (p in s_planets)]
        
        # Benefic / malefic balance
        benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
        malefics = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}
        
        benefic_score = sum(1 for p in all_activated_planets if p in benefics)
        malefic_score = sum(1 for p in all_activated_planets if p in malefics)
        
        entry = {
            "age": age,
            "year_of_life": age + 1,
            "lagna_layer": {
                "house": l_house,
                "sign": l_sign,
                "lord": l_lord,
                "occupants": l_planets,
            },
            "moon_layer": {
                "house": m_house,
                "sign": m_sign,
                "lord": m_lord,
                "occupants": m_planets,
            },
            "sun_layer": {
                "house": s_house,
                "sign": s_sign,
                "lord": s_lord,
                "occupants": s_planets,
            },
            "all_occupants": all_activated_planets,
            "double_activated": double_activated,
            "triple_activated": triple_activated,
            "benefic_score": benefic_score,
            "malefic_score": malefic_score,
            "intensity": "HIGH" if (double_activated or len(all_activated_planets) >= 3) else "MODERATE"
        }
        progressions.append(entry)
        
    return {
        "lagna_reference": lagna_sign,
        "moon_reference": moon_sign,
        "sun_reference": sun_sign,
        "total_years_computed": max_years,
        "progressions": progressions,
    }


def get_sudarshana_for_age(chart, age: int) -> Dict[str, Any]:
    """Get detailed Sudarshana Chakra analysis for a specific completed age."""
    sc = calc_sudarshana_chakra_dasha(chart, max_years=max(age + 2, 120))
    progs = sc.get("progressions", [])
    if 0 <= age < len(progs):
        return progs[age]
    return {}
