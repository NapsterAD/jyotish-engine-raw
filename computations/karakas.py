"""
karakas.py — Chara Karakas (7-planet and 8-planet schemes) + Karakamsa.
100% offline — pure arithmetic from sidereal longitudes.

Chara Karakas are determined by ranking planets by their degree traversed
in their respective signs (longitude % 30), from highest to lowest.
"""

from ..core.constants import PLANETS_7, PLANETS_9, SIGNS, SIGN_INDEX, SIGN_LORDS, get_navamsa_sign


# ═══════════════════════════════════════════
# KARAKA NAMES
# ═══════════════════════════════════════════

# 8-planet rank order (highest degree-in-sign → lowest). DK is whoever ranks last.
# PK is rank 5 (same slot as 7-planet PK); PiK is inserted as rank 6.
KARAKA_NAMES_8 = ["AK", "AmK", "BK", "MK", "PK", "PiK", "GK", "DK"]
KARAKA_NAMES_7 = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]


# ═══════════════════════════════════════════
# 7-PLANET CHARA KARAKAS (KN Rao / classical)
# ═══════════════════════════════════════════

def calc_chara_karakas_7(positions):
    """
    Calculate 7-planet Chara Karakas (no Rahu, no Ketu).
    Ranks 7 planets by degree-in-sign (longitude % 30), highest = AK, lowest = DK.
    
    This is the KN Rao / classical scheme used in most Jaimini analysis.
    
    Args:
        positions: dict from ephemeris — planet -> {longitude, degree_in_sign, ...}
        
    Returns:
        dict with:
            karakas: {AK: planet, AmK: planet, ...}
            ranking: [(planet, degree_in_sign), ...] sorted descending
            details: {planet: {karaka, degree_in_sign}}
    """
    planet_degrees = []

    for planet in PLANETS_7:
        pos = positions.get(planet, {})
        if not pos or isinstance(pos, (float, int)):
            continue
        deg = pos.get("degree_in_sign", 0)
        planet_degrees.append((planet, deg))

    # Sort by degree descending — highest degree = Atmakaraka
    planet_degrees.sort(key=lambda x: x[1], reverse=True)

    karakas = {}
    details = {}
    for i, (planet, deg) in enumerate(planet_degrees):
        if i < len(KARAKA_NAMES_7):
            karaka_name = KARAKA_NAMES_7[i]
            karakas[karaka_name] = planet
            details[planet] = {
                "karaka": karaka_name,
                "degree_in_sign": round(deg, 4),
                "rank": i + 1,
            }

    return {
        "karakas": karakas,
        "ranking": [(p, round(d, 4)) for p, d in planet_degrees],
        "details": details,
        "scheme": "7-planet (KN Rao, no Rahu/Ketu)",
    }


# ═══════════════════════════════════════════
# 8-PLANET CHARA KARAKAS (incl. Rahu)
# ═══════════════════════════════════════════

def calc_chara_karakas_8(positions):
    """
    Calculate 8-planet Chara Karakas (7 planets + Rahu).
    Rahu's degree is measured from the END of the sign (30 - degree).
    Ketu is excluded.
    
    PK stays rank 5 (same planet as 7-planet PK). PiK is rank 6.
    DK is the lowest degree (often Rahu after the 30°−λ rule).
    
    Args:
        positions: dict from ephemeris
        
    Returns:
        dict with karakas, ranking, details (same structure as 7-planet)
    """
    planet_degrees = []

    for planet in PLANETS_7:
        pos = positions.get(planet, {})
        if not pos or isinstance(pos, (float, int)):
            continue
        deg = pos.get("degree_in_sign", 0)
        planet_degrees.append((planet, deg))

    # Rahu: use (30 - degree) as per Jaimini convention
    rahu_pos = positions.get("Rahu", {})
    if rahu_pos and isinstance(rahu_pos, dict):
        rahu_deg = 30 - rahu_pos.get("degree_in_sign", 0)
        planet_degrees.append(("Rahu", rahu_deg))

    # Sort by degree descending
    planet_degrees.sort(key=lambda x: x[1], reverse=True)

    karakas = {}
    details = {}
    for i, (planet, deg) in enumerate(planet_degrees):
        if i < len(KARAKA_NAMES_8):
            karaka_name = KARAKA_NAMES_8[i]
            karakas[karaka_name] = planet
            details[planet] = {
                "karaka": karaka_name,
                "degree_in_sign": round(deg, 4),
                "rank": i + 1,
                "note": "(30 - degree used)" if planet == "Rahu" else "",
            }

    return {
        "karakas": karakas,
        "ranking": [(p, round(d, 4)) for p, d in planet_degrees],
        "details": details,
        "scheme": "8-planet (incl. Rahu with 30-degree rule)",
    }


# ═══════════════════════════════════════════
# KARAKAMSA
# ═══════════════════════════════════════════

def get_karakamsa(positions, karakas_7=None):
    """
    Calculate Karakamsa — the Navamsa sign of the Atmakaraka.
    
    Args:
        positions: dict from ephemeris
        karakas_7: output from calc_chara_karakas_7() (optional, computed if None)
        
    Returns:
        dict with:
            karakamsa: sign name
            ak: Atmakaraka planet name
            ak_navamsa: same as karakamsa
            karakamsa_7h: sign of 7th from Karakamsa
    """
    if karakas_7 is None:
        karakas_7 = calc_chara_karakas_7(positions)

    ak = karakas_7["karakas"].get("AK", "Moon")
    ak_pos = positions.get(ak, {})
    ak_long = ak_pos.get("longitude", 0) if isinstance(ak_pos, dict) else 0

    karakamsa = get_navamsa_sign(ak_long)
    karakamsa_idx = SIGN_INDEX[karakamsa]
    karakamsa_7h = SIGNS[(karakamsa_idx + 6) % 12]

    return {
        "karakamsa": karakamsa,
        "ak": ak,
        "ak_navamsa": karakamsa,
        "karakamsa_7h": karakamsa_7h,
        "karakamsa_lord": SIGN_LORDS.get(karakamsa, ""),
    }


# ═══════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════

def format_karakas(karakas_data):
    """Format karakas as readable text."""
    lines = []
    scheme = karakas_data.get("scheme", "Unknown")
    lines.append(f"=== Chara Karakas ({scheme}) ===\n")

    for planet, deg in karakas_data["ranking"]:
        detail = karakas_data["details"].get(planet, {})
        karaka = detail.get("karaka", "—")
        note = detail.get("note", "")
        lines.append(f"  {karaka:<5} = {planet:<10} {deg:>7.2f}°  {note}")

    return "\n".join(lines)
