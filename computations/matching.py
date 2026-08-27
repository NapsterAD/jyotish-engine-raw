"""
matching.py — Ashtakoota Guna Milan (Kundali Matching / Compatibility).
North Indian 8-koota system with 36 maximum points.
100% offline — pure arithmetic from Moon nakshatra and sign positions.

The 8 Kootas:
1. Varna (spiritual compatibility)      — 1 point
2. Vashya (dominance/mutual attraction) — 2 points
3. Tara (destiny compatibility)         — 3 points
4. Yoni (sexual/physical compatibility) — 4 points
5. Graha Maitri (mental compatibility)  — 5 points
6. Gana (temperament compatibility)     — 6 points
7. Bhakoot (health/wealth compatibility)— 7 points
8. Nadi (health/progeny compatibility)  — 8 points
                                Total = 36 points
"""

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, SIGN_ELEMENT,
    NAKSHATRAS, NATURAL_FRIENDS, NATURAL_ENEMIES,
)


# ═══════════════════════════════════════════
# NAKSHATRA → ATTRIBUTES TABLES
# ═══════════════════════════════════════════

# Varna (caste) of each nakshatra (1-indexed)
# Brahmin=1, Kshatriya=2, Vaishya=3, Shudra=4
VARNA_TABLE = {
    1: 3, 2: 4, 3: 2, 4: 4, 5: 3, 6: 4, 7: 1, 8: 2, 9: 4,      # Ashwini-Ashlesha
    10: 4, 11: 1, 12: 2, 13: 3, 14: 4, 15: 1, 16: 1, 17: 4, 18: 3,  # Magha-Jyeshtha
    19: 4, 20: 1, 21: 2, 22: 4, 23: 3, 24: 4, 25: 1, 26: 2, 27: 3,  # Moola-Revati
}

# Gana: Deva=1, Manushya=2, Rakshasa=3
GANA_TABLE = {
    1: 1, 2: 2, 3: 3, 4: 2, 5: 1, 6: 2, 7: 1, 8: 1, 9: 3,
    10: 3, 11: 2, 12: 2, 13: 1, 14: 3, 15: 1, 16: 3, 17: 1, 18: 3,
    19: 3, 20: 2, 21: 2, 22: 1, 23: 3, 24: 3, 25: 2, 26: 2, 27: 1,
}

# Yoni animals (1-indexed nakshatra -> animal code)
# Each animal has a pair (male/female)
YONI_TABLE = {
    1: "Horse",    2: "Elephant",  3: "Sheep",     4: "Serpent",
    5: "Serpent",  6: "Dog",       7: "Cat",       8: "Sheep",
    9: "Cat",      10: "Rat",      11: "Rat",      12: "Cow",
    13: "Buffalo", 14: "Tiger",    15: "Buffalo",  16: "Tiger",
    17: "Deer",    18: "Deer",     19: "Dog",      20: "Monkey",
    21: "Mongoose", 22: "Monkey",  23: "Lion",     24: "Horse",
    25: "Lion",    26: "Cow",      27: "Elephant",
}

# Yoni compatibility scores (animal pair -> score out of 4)
# Same animal = 4, Friendly = 3, Neutral = 2, Enemy = 1, Sworn enemy = 0
YONI_ENEMIES = {
    frozenset({"Horse", "Buffalo"}): 0,
    frozenset({"Elephant", "Lion"}): 0,
    frozenset({"Sheep", "Monkey"}): 0,
    frozenset({"Serpent", "Mongoose"}): 0,
    frozenset({"Dog", "Deer"}): 0,
    frozenset({"Cat", "Rat"}): 0,
    frozenset({"Cow", "Tiger"}): 0,
}

YONI_FRIENDLY = {
    frozenset({"Horse", "Monkey"}): 3,
    frozenset({"Elephant", "Sheep"}): 3,
    frozenset({"Serpent", "Cat"}): 3,
    frozenset({"Dog", "Cat"}): 3,
    frozenset({"Cow", "Elephant"}): 3,
    frozenset({"Lion", "Dog"}): 3,
}

# Nadi: Aadi=1 (Vata), Madhya=2 (Pitta), Antya=3 (Kapha)
NADI_TABLE = {
    1: 1, 2: 2, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 2, 9: 3,
    10: 1, 11: 2, 12: 3, 13: 3, 14: 2, 15: 1, 16: 1, 17: 2, 18: 3,
    19: 1, 20: 2, 21: 3, 22: 3, 23: 2, 24: 1, 25: 1, 26: 2, 27: 3,
}

# Vashya categories per sign
# Chatushpada (quadruped), Manushya (human), Jalachara (aquatic),
# Vanachara (wild), Keeta (insect)
VASHYA_CATEGORY = {
    "Aries": "Chatushpada",    "Taurus": "Chatushpada",
    "Gemini": "Manushya",      "Cancer": "Jalachara",
    "Leo": "Vanachara",        "Virgo": "Manushya",
    "Libra": "Manushya",       "Scorpio": "Keeta",
    "Sagittarius": "Chatushpada",  "Capricorn": "Jalachara",
    "Aquarius": "Manushya",    "Pisces": "Jalachara",
}


# ═══════════════════════════════════════════
# 1. VARNA KOOTA (1 point)
# ═══════════════════════════════════════════

def check_varna(nak_boy, nak_girl):
    """
    Check Varna Koota (spiritual/ego compatibility).

    Rule: Boy's varna should be >= Girl's varna.
    Brahmin(1) > Kshatriya(2) > Vaishya(3) > Shudra(4)
    If boy's varna >= girl's: 1 point
    Otherwise: 0 points

    Args:
        nak_boy: boy's Moon nakshatra number (1-27)
        nak_girl: girl's Moon nakshatra number (1-27)

    Returns:
        dict with score, max_score, details
    """
    v_boy = VARNA_TABLE.get(nak_boy, 4)
    v_girl = VARNA_TABLE.get(nak_girl, 4)

    varna_names = {1: "Brahmin", 2: "Kshatriya", 3: "Vaishya", 4: "Shudra"}

    # Lower number = higher varna
    score = 1 if v_boy <= v_girl else 0

    return {
        "koota": "Varna",
        "score": score,
        "max_score": 1,
        "boy_varna": varna_names.get(v_boy, "Unknown"),
        "girl_varna": varna_names.get(v_girl, "Unknown"),
        "description": f"Boy: {varna_names.get(v_boy)}, Girl: {varna_names.get(v_girl)}",
    }


# ═══════════════════════════════════════════
# 2. VASHYA KOOTA (2 points)
# ═══════════════════════════════════════════

def check_vashya(sign_boy, sign_girl):
    """
    Check Vashya Koota (dominance/mutual attraction).

    Points:
    - Same category: 2 points
    - One is Vashya to the other: 1 point (partial compatibility)
    - Otherwise: 0 points

    Vashya relationships:
    - Manushya is vashya to Chatushpada
    - Chatushpada is vashya to Manushya
    - Jalachara mutual vashya with Jalachara
    - Vanachara has dominance
    - Keeta is generally vashya to all

    Args:
        sign_boy: boy's Moon sign name
        sign_girl: girl's Moon sign name

    Returns:
        dict with score, max_score, details
    """
    cat_boy = VASHYA_CATEGORY.get(sign_boy, "Manushya")
    cat_girl = VASHYA_CATEGORY.get(sign_girl, "Manushya")

    if cat_boy == cat_girl:
        score = 2
    elif {cat_boy, cat_girl} == {"Manushya", "Chatushpada"}:
        score = 1
    elif "Jalachara" in {cat_boy, cat_girl}:
        score = 1
    elif "Keeta" in {cat_boy, cat_girl}:
        score = 0
    else:
        score = 0

    return {
        "koota": "Vashya",
        "score": score,
        "max_score": 2,
        "boy_category": cat_boy,
        "girl_category": cat_girl,
    }


# ═══════════════════════════════════════════
# 3. TARA KOOTA (3 points)
# ═══════════════════════════════════════════

def check_tara(nak_boy, nak_girl):
    """
    Check Tara Koota (destiny/health compatibility).

    Count from boy's nakshatra to girl's nakshatra and vice versa.
    Take remainder when divided by 9.
    If remainder is 3 (Vipat), 5 (Pratyak), 7 (Naidhana) = inauspicious.

    Points:
    - Both favorable (not 3, 5, 7): 3 points
    - One favorable: 1.5 points
    - Both unfavorable: 0 points

    Args:
        nak_boy: boy's Moon nakshatra number (1-27)
        nak_girl: girl's Moon nakshatra number (1-27)

    Returns:
        dict with score, max_score, details
    """
    tara_names = {
        1: "Janma", 2: "Sampat", 3: "Vipat", 4: "Kshema",
        5: "Pratyak", 6: "Sadhana", 7: "Naidhana", 8: "Mitra", 0: "Parama Mitra"
    }
    bad_taras = {3, 5, 7}

    # Boy to Girl
    diff_bg = ((nak_girl - nak_boy) % 27) + 1
    tara_bg = diff_bg % 9

    # Girl to Boy
    diff_gb = ((nak_boy - nak_girl) % 27) + 1
    tara_gb = diff_gb % 9

    bg_good = tara_bg not in bad_taras
    gb_good = tara_gb not in bad_taras

    if bg_good and gb_good:
        score = 3
    elif bg_good or gb_good:
        score = 1.5
    else:
        score = 0

    return {
        "koota": "Tara",
        "score": score,
        "max_score": 3,
        "boy_to_girl_tara": tara_names.get(tara_bg, str(tara_bg)),
        "girl_to_boy_tara": tara_names.get(tara_gb, str(tara_gb)),
        "boy_to_girl_favorable": bg_good,
        "girl_to_boy_favorable": gb_good,
    }


# ═══════════════════════════════════════════
# 4. YONI KOOTA (4 points)
# ═══════════════════════════════════════════

def check_yoni(nak_boy, nak_girl):
    """
    Check Yoni Koota (sexual/physical compatibility).

    Each nakshatra has an associated animal (yoni).
    Scoring:
    - Same animal: 4 points
    - Friendly animals: 3 points
    - Neutral: 2 points
    - Unfriendly: 1 point
    - Sworn enemies: 0 points

    Args:
        nak_boy: boy's Moon nakshatra number (1-27)
        nak_girl: girl's Moon nakshatra number (1-27)

    Returns:
        dict with score, max_score, details
    """
    animal_boy = YONI_TABLE.get(nak_boy, "Unknown")
    animal_girl = YONI_TABLE.get(nak_girl, "Unknown")

    if animal_boy == animal_girl:
        score = 4
    else:
        pair = frozenset({animal_boy, animal_girl})
        if pair in YONI_ENEMIES:
            score = YONI_ENEMIES[pair]
        elif pair in YONI_FRIENDLY:
            score = YONI_FRIENDLY[pair]
        else:
            score = 2  # Neutral

    return {
        "koota": "Yoni",
        "score": score,
        "max_score": 4,
        "boy_yoni": animal_boy,
        "girl_yoni": animal_girl,
    }


# ═══════════════════════════════════════════
# 5. GRAHA MAITRI KOOTA (5 points)
# ═══════════════════════════════════════════

def check_graha_maitri(sign_boy, sign_girl):
    """
    Check Graha Maitri Koota (mental/intellectual compatibility).

    Based on the relationship between the Moon sign lords.
    - Both friends: 5 points
    - One friend, one neutral: 4 points
    - Both neutral: 3 points
    - One friend, one enemy: 1 point
    - One neutral, one enemy: 0.5 points
    - Both enemies: 0 points

    Args:
        sign_boy: boy's Moon sign name
        sign_girl: girl's Moon sign name

    Returns:
        dict with score, max_score, details
    """
    lord_boy = SIGN_LORDS.get(sign_boy, "")
    lord_girl = SIGN_LORDS.get(sign_girl, "")

    if lord_boy == lord_girl:
        score = 5  # Same lord = perfect compatibility
        relationship = "Same lord"
    else:
        # Check mutual friendship
        boy_friends = NATURAL_FRIENDS.get(lord_boy, [])
        boy_enemies = NATURAL_ENEMIES.get(lord_boy, [])
        girl_friends = NATURAL_FRIENDS.get(lord_girl, [])
        girl_enemies = NATURAL_ENEMIES.get(lord_girl, [])

        boy_to_girl = "friend" if lord_girl in boy_friends else (
            "enemy" if lord_girl in boy_enemies else "neutral"
        )
        girl_to_boy = "friend" if lord_boy in girl_friends else (
            "enemy" if lord_boy in girl_enemies else "neutral"
        )

        relationship = f"{lord_boy}->{lord_girl}: {boy_to_girl}, {lord_girl}->{lord_boy}: {girl_to_boy}"

        combo = {boy_to_girl, girl_to_boy}
        if combo == {"friend"}:
            score = 5
        elif combo == {"friend", "neutral"}:
            score = 4
        elif combo == {"neutral"}:
            score = 3
        elif combo == {"friend", "enemy"}:
            score = 1
        elif combo == {"neutral", "enemy"}:
            score = 0.5
        else:
            score = 0

    return {
        "koota": "Graha Maitri",
        "score": score,
        "max_score": 5,
        "boy_lord": lord_boy,
        "girl_lord": lord_girl,
        "relationship": relationship,
    }


# ═══════════════════════════════════════════
# 6. GANA KOOTA (6 points)
# ═══════════════════════════════════════════

def check_gana(nak_boy, nak_girl):
    """
    Check Gana Koota (temperament compatibility).

    Gana types: Deva (divine), Manushya (human), Rakshasa (demon).
    - Same Gana: 6 points
    - Deva-Manushya: 6 points (compatible)
    - Deva-Rakshasa: 0 points (incompatible)
    - Manushya-Rakshasa: 0 points (incompatible)

    Some systems give partial points (1) for Manushya-Rakshasa.

    Args:
        nak_boy: boy's Moon nakshatra number (1-27)
        nak_girl: girl's Moon nakshatra number (1-27)

    Returns:
        dict with score, max_score, details
    """
    gana_names = {1: "Deva", 2: "Manushya", 3: "Rakshasa"}

    g_boy = GANA_TABLE.get(nak_boy, 2)
    g_girl = GANA_TABLE.get(nak_girl, 2)

    if g_boy == g_girl:
        score = 6
    elif {g_boy, g_girl} == {1, 2}:  # Deva-Manushya
        score = 6
    elif {g_boy, g_girl} == {2, 3}:  # Manushya-Rakshasa
        score = 1
    else:  # Deva-Rakshasa
        score = 0

    return {
        "koota": "Gana",
        "score": score,
        "max_score": 6,
        "boy_gana": gana_names.get(g_boy, "Unknown"),
        "girl_gana": gana_names.get(g_girl, "Unknown"),
    }


# ═══════════════════════════════════════════
# 7. BHAKOOT KOOTA (7 points)
# ═══════════════════════════════════════════

def check_bhakoot(sign_boy, sign_girl):
    """
    Check Bhakoot Koota (health and wealth compatibility).

    Based on the relationship between Moon signs (house distance).
    Inauspicious combinations (Bhakoot Dosha):
    - 2/12 (Dhan-Vyay): financial problems
    - 6/8 (Rog-Mrityu): health issues
    - 5/9 (some traditions consider this inauspicious; others don't)

    If Bhakoot Dosha present: 0 points
    Otherwise: 7 points

    Args:
        sign_boy: boy's Moon sign name
        sign_girl: girl's Moon sign name

    Returns:
        dict with score, max_score, details
    """
    idx_boy = SIGN_INDEX.get(sign_boy, 0)
    idx_girl = SIGN_INDEX.get(sign_girl, 0)

    distance_bg = ((idx_girl - idx_boy) % 12) + 1
    distance_gb = ((idx_boy - idx_girl) % 12) + 1

    # Check for inauspicious Bhakoot
    dosha_pairs = [{2, 12}, {6, 8}]
    distances = {distance_bg, distance_gb}

    bhakoot_dosha = False
    dosha_type = ""
    for bad_pair in dosha_pairs:
        if distances == bad_pair:
            bhakoot_dosha = True
            if bad_pair == {2, 12}:
                dosha_type = "Dhan-Vyay (2/12)"
            else:
                dosha_type = "Rog-Mrityu (6/8)"
            break

    # Check Bhakoot Dosha cancellation
    cancellation = None
    if bhakoot_dosha:
        lord_boy = SIGN_LORDS.get(sign_boy, "")
        lord_girl = SIGN_LORDS.get(sign_girl, "")

        # Cancellation 1: If both sign lords are the same
        if lord_boy == lord_girl:
            cancellation = "Same lord cancellation"
            bhakoot_dosha = False

        # Cancellation 2: If lords are mutual friends
        elif lord_girl in NATURAL_FRIENDS.get(lord_boy, []) and \
             lord_boy in NATURAL_FRIENDS.get(lord_girl, []):
            cancellation = "Mutual friendship cancellation"
            bhakoot_dosha = False

    score = 0 if bhakoot_dosha else 7

    return {
        "koota": "Bhakoot",
        "score": score,
        "max_score": 7,
        "distance": f"{distance_bg}/{distance_gb}",
        "dosha": bhakoot_dosha,
        "dosha_type": dosha_type,
        "cancellation": cancellation,
    }


# ═══════════════════════════════════════════
# 8. NADI KOOTA (8 points)
# ═══════════════════════════════════════════

def check_nadi(nak_boy, nak_girl, sign_boy=None, sign_girl=None,
               pada_boy=None, pada_girl=None):
    """
    Check Nadi Koota (health and progeny compatibility). rules.md §12.

    Nadi types: Aadi (Vata), Madhya (Pitta), Antya (Kapha)
    - Different Nadi: 8 points
    - Same Nadi: 0 points (Nadi Dosha)

    Cancellation (restores 8 points):
    - Same nakshatra with different padas (same pada does not cancel)
    - Same Moon sign
    """
    nadi_names = {1: "Aadi (Vata)", 2: "Madhya (Pitta)", 3: "Antya (Kapha)"}

    n_boy = NADI_TABLE.get(nak_boy, 1)
    n_girl = NADI_TABLE.get(nak_girl, 1)

    nadi_dosha = (n_boy == n_girl)

    cancellation = None
    if nadi_dosha:
        if nak_boy == nak_girl:
            same_pada = (
                pada_boy is not None and pada_girl is not None
                and int(pada_boy) == int(pada_girl)
            )
            if not same_pada:
                cancellation = "Same nakshatra, different padas"
                nadi_dosha = False
        if nadi_dosha and sign_boy and sign_girl and sign_boy == sign_girl:
            cancellation = "Same Moon sign"
            nadi_dosha = False

    score = 0 if nadi_dosha else 8

    return {
        "koota": "Nadi",
        "score": score,
        "max_score": 8,
        "boy_nadi": nadi_names.get(n_boy, "Unknown"),
        "girl_nadi": nadi_names.get(n_girl, "Unknown"),
        "dosha": nadi_dosha,
        "cancellation": cancellation,
    }


# ═══════════════════════════════════════════
# MASTER: ASHTAKOOTA GUNA MILAN
# ═══════════════════════════════════════════

def calc_ashtakoota(nak_boy, sign_boy, nak_girl, sign_girl,
                    pada_boy=None, pada_girl=None):
    """
    Calculate complete Ashtakoota Guna Milan (36-point matching).

    Args:
        nak_boy: boy's Moon nakshatra number (1-27)
        sign_boy: boy's Moon sign name
        nak_girl: girl's Moon nakshatra number (1-27)
        sign_girl: girl's Moon sign name

    Returns:
        dict with all 8 koota results, total score, and assessment
    """
    kootas = [
        check_varna(nak_boy, nak_girl),
        check_vashya(sign_boy, sign_girl),
        check_tara(nak_boy, nak_girl),
        check_yoni(nak_boy, nak_girl),
        check_graha_maitri(sign_boy, sign_girl),
        check_gana(nak_boy, nak_girl),
        check_bhakoot(sign_boy, sign_girl),
        check_nadi(nak_boy, nak_girl, sign_boy, sign_girl, pada_boy, pada_girl),
    ]

    total = sum(k["score"] for k in kootas)
    max_total = 36

    # Assessment
    if total >= 28:
        assessment = "Excellent — highly recommended"
        recommendation = "Very Good Match"
    elif total >= 21:
        assessment = "Good — recommended with some adjustments"
        recommendation = "Good Match"
    elif total >= 18:
        assessment = "Average — acceptable with remedies"
        recommendation = "Average Match"
    elif total >= 14:
        assessment = "Below average — significant concerns"
        recommendation = "Below Average"
    else:
        assessment = "Poor — not recommended without strong remedial measures"
        recommendation = "Not Recommended"

    # Check for critical doshas
    critical_doshas = []
    for k in kootas:
        if k.get("dosha"):
            critical_doshas.append(f"{k['koota']} Dosha")

    return {
        "kootas": kootas,
        "total_score": total,
        "max_score": max_total,
        "percentage": round(total / max_total * 100, 1),
        "assessment": assessment,
        "recommendation": recommendation,
        "critical_doshas": critical_doshas,
    }


# ═══════════════════════════════════════════
# CHART-BASED MATCHING
# ═══════════════════════════════════════════

def calc_matching_score(chart_boy, chart_girl):
    """
    Calculate full matching score from two BirthChart objects.

    Extracts Moon nakshatra and sign from each chart automatically.

    Args:
        chart_boy: BirthChart object for boy
        chart_girl: BirthChart object for girl

    Returns:
        dict with ashtakoota results + manglik comparison
    """
    # Extract Moon data
    moon_boy = chart_boy.positions.get("Moon", {})
    moon_girl = chart_girl.positions.get("Moon", {})

    sign_boy = moon_boy.get("sign", "Aries")
    sign_girl = moon_girl.get("sign", "Aries")

    # Get nakshatra number (1-indexed)
    nak_name_boy = moon_boy.get("nakshatra", "Ashwini")
    nak_name_girl = moon_girl.get("nakshatra", "Ashwini")

    # Find nakshatra number from name
    nak_boy = 1
    nak_girl = 1
    for n in NAKSHATRAS:
        if n["name"] == nak_name_boy:
            nak_boy = n["num"]
        if n["name"] == nak_name_girl:
            nak_girl = n["num"]

    # Calculate Ashtakoota
    ashtakoota = calc_ashtakoota(
        nak_boy, sign_boy, nak_girl, sign_girl,
        moon_boy.get("pada"), moon_girl.get("pada"),
    )

    # Manglik comparison
    from .yogas import check_manglik
    manglik_boy = check_manglik(chart_boy)
    manglik_girl = check_manglik(chart_girl)

    manglik_status = "Balanced"
    if manglik_boy["formed"] and not manglik_girl["formed"]:
        manglik_status = "Boy is Manglik, Girl is not — CONCERN"
    elif not manglik_boy["formed"] and manglik_girl["formed"]:
        manglik_status = "Girl is Manglik, Boy is not — CONCERN"
    elif manglik_boy["formed"] and manglik_girl["formed"]:
        manglik_status = "Both Manglik — cancellation applies"

    return {
        "boy_name": chart_boy.birth_data.get("name", "Boy"),
        "girl_name": chart_girl.birth_data.get("name", "Girl"),
        "boy_moon": {"sign": sign_boy, "nakshatra": nak_name_boy},
        "girl_moon": {"sign": sign_girl, "nakshatra": nak_name_girl},
        "ashtakoota": ashtakoota,
        "manglik_boy": manglik_boy,
        "manglik_girl": manglik_girl,
        "manglik_status": manglik_status,
    }


# ═══════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════

def format_ashtakoota(result):
    """Format Ashtakoota results as readable text."""
    lines = []
    lines.append("=== Ashtakoota Guna Milan ===\n")

    for k in result["kootas"]:
        score_str = f"{k['score']}/{k['max_score']}"
        dosha_flag = " ⚠️ DOSHA" if k.get("dosha") else ""
        cancel_flag = f" [Cancelled: {k['cancellation']}]" if k.get("cancellation") else ""
        lines.append(f"  {k['koota']:<15} {score_str:<8}{dosha_flag}{cancel_flag}")

    lines.append(f"\n  TOTAL: {result['total_score']}/{result['max_score']} ({result['percentage']}%)")
    lines.append(f"  Assessment: {result['assessment']}")
    lines.append(f"  Recommendation: {result['recommendation']}")

    if result.get("critical_doshas"):
        lines.append(f"\n  ⚠️ Critical Doshas: {', '.join(result['critical_doshas'])}")

    return "\n".join(lines)


def format_matching_report(match_result):
    """Format full matching report as readable text."""
    lines = []
    lines.append(f"=== Kundali Matching: {match_result['boy_name']} ↔ {match_result['girl_name']} ===\n")

    bm = match_result["boy_moon"]
    gm = match_result["girl_moon"]
    lines.append(f"  Boy Moon:  {bm['sign']} — {bm['nakshatra']}")
    lines.append(f"  Girl Moon: {gm['sign']} — {gm['nakshatra']}")
    lines.append("")

    lines.append(format_ashtakoota(match_result["ashtakoota"]))
    lines.append(f"\n  Manglik: {match_result['manglik_status']}")

    return "\n".join(lines)
