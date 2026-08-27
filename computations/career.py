"""
career.py — Career & Profession Determination Engine (rules.md §29).
Pure data extraction & objective algorithmic scoring for vocational analysis:
- Primary 10th House & 10th Lord Analysis
- D10 (Dashamsha) Career Chart Mapping
- Amatyakaraka (AmK) Integration (D1, D9, D10)
- Planetary Karakatwas & House-Profession Axis
- Government Authority / Executive Indicator Score
"""

from typing import Dict, Any, List
from ..core.constants import SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_7, PLANETS_9
from ..core.mapping import house_to_sign, sign_to_house

PLANET_CAREER_DOMAINS = {
    "Sun": ["Government", "Administration", "Leadership", "Medicine", "Politics", "Executive Power"],
    "Moon": ["Hospitality", "Public Relations", "Liquids/Beverages", "Psychology", "Healthcare", "Travel"],
    "Mars": ["Engineering", "Defense/Military", "Real Estate", "Surgery", "Sports", "Technology"],
    "Mercury": ["Commerce", "Software/IT", "Finance/Accounting", "Media/Writing", "Analytics", "Trading"],
    "Jupiter": ["Law/Judiciary", "Advisory/Consulting", "Higher Education", "Banking", "Philosophy", "Mentorship"],
    "Venus": ["Creative Arts", "Entertainment", "Luxury Goods", "Design/Aesthetics", "Hospitality", "Finance"],
    "Saturn": ["Heavy Industry", "Law/Judiciary", "Mining", "Infrastructure", "Public Administration", "Research"],
    "Rahu": ["Foreign Enterprise", "Aviation", "High-Tech/AI", "Diplomacy", "Media/Broadcasting", "Unconventional"],
    "Ketu": ["Software Engineering", "Data Analytics", "Spiritual/Occult", "Precision Research", "Investigation"],
}

HOUSE_AXIS_DOMAINS = {
    1: "Independent Practice / Entrepreneurship / Self-Employed",
    2: "Finance / Banking / Family Enterprise / Asset Management",
    3: "Media / Digital Communications / Writing / Sales / Logistics",
    4: "Real Estate / Infrastructure / Institutional Leadership / Agriculture",
    5: "Advisory / Strategic Consulting / Creative Direction / Speculation",
    6: "Service / Problem Resolution / Healthcare / Legal Defense / Operations",
    7: "Partnership / International Trade / Client Advisory / Public Relations",
    8: "Deep Research / Data Mining / Risk Analytics / Occult / Crisis Management",
    9: "Higher Learning / Corporate Strategy / Publishing / International Law",
    10: "High Executive Authority / Government / Institutional Headship",
    11: "Large Enterprise Networks / Tech Platforms / Organizational Scaling",
    12: "Multinational Corporations / Foreign Lands / Offshore Ventures / R&D",
}


def calc_career_profile(chart) -> Dict[str, Any]:
    """
    Extract all classical career parameters and compute objective scoring.
    """
    positions = chart.positions or {}
    rashi = chart.rashi_chart or {}
    lordships = getattr(chart, "lordships", {}) or {}
    
    # 1. 10th House & Lord (D1)
    h10_lord = lordships.get(10, "Mars")
    h10_lord_pos = positions.get(h10_lord, {})
    h10_lord_house = rashi.get(h10_lord, {}).get("house_rashi", 10)
    h10_lord_sign = h10_lord_pos.get("sign", "Aries")
    h10_lord_nak = h10_lord_pos.get("nakshatra", "")
    h10_lord_dignity = rashi.get(h10_lord, {}).get("dignity", "Neutral")
    
    # Occupants of 10H
    h10_occupants = [p for p, rc in rashi.items() if rc.get("house_rashi") == 10 and p != "Lagna"]
    
    # 2. D10 Dashamsha Analysis
    vargas = getattr(chart, "vargas", {}) or {}
    d10 = vargas.get("D10", {})
    d10_lagna_sign = d10.get("Lagna", "Aries")
    d10_lagna_idx = SIGN_INDEX.get(d10_lagna_sign, 0)
    d10_h10_sign = SIGNS[(d10_lagna_idx + 9) % 12]
    d10_h10_lord = SIGN_LORDS[d10_h10_sign]
    d10_h10_occupants = [p for p, s in d10.items() if s == d10_h10_sign and p != "Lagna"]
    
    # 3. Amatyakaraka (AmK)
    karakas = getattr(chart, "karakas", {}) or {}
    amk_7 = karakas.get("karakas", {}).get("AmK", "Sun")
    amk_pos = positions.get(amk_7, {})
    amk_sign = amk_pos.get("sign", "Aries")
    amk_house = rashi.get(amk_7, {}).get("house_rashi", 1)
    
    # 4. Sun & Saturn (Authority & Work Karakas)
    sun_house = rashi.get("Sun", {}).get("house_rashi", 1)
    saturn_house = rashi.get("Saturn", {}).get("house_rashi", 1)
    
    # 5. Government Authority Score (rules.md §29.4)
    gov_checks = [
        ("Sun in Kendra or Trikona", sun_house in (1, 4, 7, 10, 5, 9)),
        ("Sun connected with 10L", (sun_house == h10_lord_house) or ("Sun" == h10_lord)),
        ("10L connected to 1L or 9L", h10_lord_house in (1, 9) or h10_lord in (lordships.get(1), lordships.get(9))),
        ("Saturn in or aspecting 10H", saturn_house == 10 or (10 in chart.aspects.get("Saturn", []))),
        ("D10 Lagna in Royal/Executive sign", d10_lagna_sign in ("Leo", "Capricorn", "Aries", "Sagittarius")),
        ("AmK is Sun or Jupiter", amk_7 in ("Sun", "Jupiter")),
    ]
    gov_score = sum(1 for _, ok in gov_checks if ok)
    
    # 6. Primary Vocational Domains
    top_planets = [h10_lord, amk_7]
    if h10_occupants:
        top_planets.extend(h10_occupants)
    suggested_domains = []
    for p in set(top_planets):
        suggested_domains.extend(PLANET_CAREER_DOMAINS.get(p, []))
        
    return {
        "tenth_lord": h10_lord,
        "tenth_lord_house": h10_lord_house,
        "tenth_lord_sign": h10_lord_sign,
        "tenth_lord_nakshatra": h10_lord_nak,
        "tenth_lord_dignity": h10_lord_dignity,
        "tenth_house_occupants": h10_occupants,
        "tenth_house_axis_nature": HOUSE_AXIS_DOMAINS.get(h10_lord_house, "General Professional Focus"),
        "d10_lagna": d10_lagna_sign,
        "d10_tenth_sign": d10_h10_sign,
        "d10_tenth_lord": d10_h10_lord,
        "d10_tenth_occupants": d10_h10_occupants,
        "amatyakaraka": amk_7,
        "amatyakaraka_sign": amk_sign,
        "amatyakaraka_house": amk_house,
        "saturn_placement": {"house": saturn_house, "sign": positions.get("Saturn", {}).get("sign")},
        "sun_placement": {"house": sun_house, "sign": positions.get("Sun", {}).get("sign")},
        "government_authority_score": gov_score,
        "government_indicators": dict(gov_checks),
        "primary_vocational_fields": list(dict.fromkeys(suggested_domains))[:10],
    }
