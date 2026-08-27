"""
nadi.py — Bhrigu Nandi Nadi directional conjunctions. rules.md §22.
"""

from ..core.constants import SIGNS, SIGN_INDEX, SIGN_ELEMENT, PLANETS_9

DIRECTION = {
    "Fire": "East", "Earth": "South", "Air": "West", "Water": "North",
}


def same_direction(sign_a, sign_b):
    return SIGN_INDEX[sign_a] % 4 == SIGN_INDEX[sign_b] % 4


def nadi_weight(from_sign, to_sign):
    """Positional weight from P's sign to Q's sign. §22.2."""
    a, b = SIGN_INDEX[from_sign], SIGN_INDEX[to_sign]
    dist = (b - a) % 12  # 0 = same
    house = dist + 1
    if house in (1, 5, 9):
        return 1.0, "trinal"
    if house == 7:
        return 1.0, "opposition"
    if house == 2:
        return 0.75, "front"
    if house == 12:
        return 0.50, "rear"
    if house in (3, 11):
        return 0.25, "supportive"
    return 0.0, "none"


def calc_nadi(chart):
    planets = {}
    for p in PLANETS_9:
        pos = chart.positions.get(p, {})
        if not isinstance(pos, dict):
            continue
        sign = pos.get("sign")
        sidx = pos.get("sign_index", SIGN_INDEX.get(sign, 0))
        retro = bool(pos.get("retrograde"))
        acts_from = [sign]
        if retro:
            acts_from.append(SIGNS[(sidx - 1) % 12])
        links = []
        for q in PLANETS_9:
            if q == p:
                continue
            qsign = chart.positions.get(q, {}).get("sign")
            if not qsign:
                continue
            w, kind = nadi_weight(sign, qsign)
            if w > 0:
                links.append({
                    "planet": q, "sign": qsign, "weight": w, "kind": kind,
                    "same_direction": same_direction(sign, qsign),
                })
        planets[p] = {
            "sign": sign,
            "direction": DIRECTION[SIGN_ELEMENT[sign]],
            "retrograde_dual": retro,
            "acts_from_signs": acts_from,
            "links": links,
        }
    return {
        "planets": planets,
        "karakatwa": {
            "Jupiter": "Jeeva (Self/Soul)", "Saturn": "Karma (Profession/Action)",
            "Venus": "Kalatra/Dhana (Spouse/Wealth)", "Mars": "Bhratri/Pati (Brother/Husband/Energy)",
            "Mercury": "Buddhi/Vidya (Intellect/Business)", "Sun": "Pitru/Atma (Father/Soul/Authority)",
            "Moon": "Matru/Manas (Mother/Mind/Travel)", "Rahu": "Maya/Foreign (Illusion/Grandfather)",
            "Ketu": "Moksha/De-linking (Spirituality/Liberation)",
        },
        "pair_readings": calc_bnn_pair_readings(planets),
        "profession_profile": calc_nadi_profession(planets),
        "marriage_profile": calc_nadi_marriage(planets),
    }


# ═══════════════════════════════════════════
# BNN CLASSICAL PLANET-PAIR INTERPRETATIONS
# ═══════════════════════════════════════════
# Sources: RG Rao (Bhrigu Nandi Nadi), Core of Nadi Astrology

BNN_PAIR_MEANINGS = {
    ("Jupiter", "Saturn"): "Dharma Karmadhipati Yoga — Highly respected, righteous professional, teacher, advisor, leadership in career.",
    ("Jupiter", "Venus"): "Sanjeevani Yoga / Mahalakshmi — Blessed with luxury, wealth, beautiful spouse, spiritual grace, prosperity.",
    ("Jupiter", "Mars"): "Guru-Mangala Yoga — Courageous, authoritative, high self-esteem, engineering, property ownership, executive.",
    ("Jupiter", "Mercury"): "Saraswati / Buddhi Yoga — Sharp intellect, communication mastery, commercial acumen, academic success, writer.",
    ("Jupiter", "Sun"): "Suryo-Guru Yoga — Government favor, administrative authority, high status, father blessing, noble soul.",
    ("Jupiter", "Moon"): "Gaja-Kesari Nadi Yoga — Fluctuating emotions balanced by wisdom, fond of travel, popular, artistic flair.",
    ("Jupiter", "Rahu"): "Guru-Chandal Nadi — Unconventional wisdom, foreign connections, tech acumen, breaking traditional boundaries.",
    ("Jupiter", "Ketu"): "Ganesha / Moksha Yoga — Deep spiritual insight, occult wisdom, detachment from materialism, intuitive healer.",
    ("Saturn", "Venus"): "Dhana Karma Yoga — Wealth through business, real estate, finance, arts, luxury industries, steady accumulation.",
    ("Saturn", "Mars"): "Agni-Marut / High Effort — Physical vigor, technical/engineering skills, surgical, industrial, work with metals.",
    ("Saturn", "Mercury"): "Vyapara Karma Yoga — Commerce, trading, programming, accounting, publishing, multi-tasking career.",
    ("Saturn", "Sun"): "Pitri Karma — Government service, political career, challenges with seniors/father, high ambition.",
    ("Saturn", "Moon"): "Pravasa Karma — Career involving travel, hospitality, public dealing, liquid assets, changeable work.",
    ("Saturn", "Rahu"): "Foreign / Tech Karma — Information technology, automation, foreign MNC, unconventional career, massive scale.",
    ("Saturn", "Ketu"): "Moksha Karma — Advisory, research, audit, occult, renunciation, service without personal attachment.",
    ("Venus", "Mars"): "Passion / Bhrigu Yoga — Strong romantic magnetism, dynamic relationship, attractive partner, property acquisition.",
    ("Venus", "Mercury"): "Artistic & Commercial — Creative talents, humor, business in luxury/communication, charming demeanor.",
    ("Venus", "Rahu"): "Grand Luxuries / Unconventional — Foreign spouse, extraordinary wealth aspirations, glamour, cinematic.",
    ("Venus", "Ketu"): "Spiritual Intimacy — Detachment in relationships, traditional/spiritual partner, spiritual aesthetics.",
}


def calc_bnn_pair_readings(planets_data):
    """
    Evaluate directional conjunctions and trinal links between key BNN pairs.
    """
    readings = []
    seen = set()
    
    for p1, info in planets_data.items():
        for link in info.get("links", []):
            p2 = link["planet"]
            weight = link["weight"]
            if weight >= 0.75: # Trinal (1.0), Opposition (1.0), or Front (0.75)
                pair = tuple(sorted([p1, p2]))
                if pair not in seen and pair in BNN_PAIR_MEANINGS:
                    seen.add(pair)
                    readings.append({
                        "planets": list(pair),
                        "relationship": link["kind"],
                        "weight": weight,
                        "meaning": BNN_PAIR_MEANINGS[pair],
                    })
    return readings


def calc_nadi_profession(planets_data):
    """
    RG Rao Profession Determination from Saturn (Karma Karaka).
    Inspects Saturn's primary trinal and front directional connections.
    """
    sat_info = planets_data.get("Saturn", {})
    if not sat_info:
        return {"primary_fields": [], "supporting_fields": []}
    
    fields = []
    for link in sat_info.get("links", []):
        p = link["planet"]
        w = link["weight"]
        kind = link["kind"]
        if w >= 0.5:
            if p == "Jupiter":
                fields.append("Teaching, Advisory, Management, Judiciary, Finance")
            elif p == "Mercury":
                fields.append("Trading, IT/Software, Commerce, Data Analysis, Journalism")
            elif p == "Venus":
                fields.append("Finance, Luxury Goods, Entertainment, Architecture, Real Estate")
            elif p == "Mars":
                fields.append("Engineering, Real Estate, Defense, Surgery, Heavy Industries")
            elif p == "Sun":
                fields.append("Government, Public Administration, Leadership, Politics")
            elif p == "Moon":
                fields.append("Travel, Logistics, Hospitality, Liquids/Chemicals, Arts")
            elif p == "Rahu":
                fields.append("Cutting-edge Tech, Foreign MNCs, Aviation, Media, AI")
            elif p == "Ketu":
                fields.append("Research, Software Architecture, Law, Spiritual Consultancy")
                
    return {
        "saturn_sign": sat_info.get("sign"),
        "saturn_direction": sat_info.get("direction"),
        "vocational_indicators": fields,
    }


def calc_nadi_marriage(planets_data):
    """
    Nadi marriage analysis:
    - For male: Venus (Kalatra Karaka) + Jupiter (Self)
    - Directional links connecting Venus/Mars/Jupiter
    """
    ven_info = planets_data.get("Venus", {})
    links = ven_info.get("links", []) if ven_info else []
    
    spouse_traits = []
    for link in links:
        p = link["planet"]
        w = link["weight"]
        if w >= 0.75:
            if p == "Jupiter":
                spouse_traits.append("Spouse is noble, philosophical, respected, brings good fortune")
            elif p == "Mars":
                spouse_traits.append("Spouse is active, athletic, courageous, strong-willed")
            elif p == "Mercury":
                spouse_traits.append("Spouse is intelligent, witty, youthful, working/career-oriented")
            elif p == "Saturn":
                spouse_traits.append("Spouse is mature, disciplined, structured, long-lasting commitment")
            elif p == "Sun":
                spouse_traits.append("Spouse comes from a respectable family, authoritative")
            elif p == "Rahu":
                spouse_traits.append("Spouse has foreign or unconventional background, distinctive beauty")
            elif p == "Ketu":
                spouse_traits.append("Spouse is spiritually minded, simple, deeply loyal")
                
    return {
        "venus_sign": ven_info.get("sign") if ven_info else "",
        "spouse_profile_traits": spouse_traits,
    }

