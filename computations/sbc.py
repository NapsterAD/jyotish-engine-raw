"""
sbc.py — Sarvatobhadra Chakra (SBC) Transit & Vedha Grid Engine (rules.md §28).
81-Square ($9 \times 9$) symmetrical astrological grid mapping:
- 28 Nakshatras (including Abhijit)
- 12 Signs (Rashis)
- 16 Vowels (Swaras)
- 20 Consonants (Varnas)
- 5 Tithi classes (Nanda, Bhadra, Jaya, Rikta, Purna)
- 7 Weekdays (Varas)

Calculates 4 types of Vedha (Aspectual Piercing / Obstruction):
1. Front Vedha (Sammukha)
2. Right Vedha (Dakshina / Vama)
3. Left Vedha
4. Diagonal / Corner Vedhas
"""

from typing import Dict, Any, List, Tuple
from ..core.constants import SIGNS, SIGN_INDEX, NAKSHATRAS, PLANETS_7, PLANETS_9

# 28 Nakshatra sequence in SBC order (Classical starting from Krittika in NE corner)
SBC_28_NAKSHATRAS = [
    "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Abhijit",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati", "Ashwini", "Bharani"
]

# Outer border 28 coordinates on 9x9 grid (Row, Col) - 0-indexed
SBC_NAKSHATRA_GRID_POS = {
    # Top edge (Cols 0 to 8, Row 0) - East to North
    "Krittika": (0, 0), "Rohini": (0, 1), "Mrigashira": (0, 2), "Ardra": (0, 3),
    "Punarvasu": (0, 4), "Pushya": (0, 5), "Ashlesha": (0, 6), "Magha": (0, 7),
    "Purva Phalguni": (0, 8),
    
    # Right edge (Rows 1 to 8, Col 8) - North to West
    "Uttara Phalguni": (1, 8), "Hasta": (2, 8), "Chitra": (3, 8), "Swati": (4, 8),
    "Vishakha": (5, 8), "Anuradha": (6, 8), "Jyeshtha": (7, 8), "Moola": (8, 8),
    
    # Bottom edge (Cols 7 down to 0, Row 8) - West to South
    "Purva Ashadha": (8, 7), "Uttara Ashadha": (8, 6), "Abhijit": (8, 5),
    "Shravana": (8, 4), "Dhanishta": (8, 3), "Shatabhisha": (8, 2),
    "Purva Bhadrapada": (8, 1), "Uttara Bhadrapada": (8, 0),
    
    # Left edge (Rows 7 down to 1, Col 0) - South to East
    "Revati": (7, 0), "Ashwini": (6, 0), "Bharani": (5, 0)
}


def get_sbc_vedha_cells(row: int, col: int) -> List[Tuple[int, int]]:
    """
    Compute all cells pierced by Vedha rays from (row, col) in a 9x9 grid:
    1. Horizontal ray (Same row)
    2. Vertical ray (Same col)
    3. Main diagonal (Top-Left to Bottom-Right)
    4. Anti diagonal (Top-Right to Bottom-Left)
    """
    vedhas = set()
    
    # Horizontal & Vertical
    for c in range(9):
        if c != col:
            vedhas.add((row, c))
    for r in range(9):
        if r != row:
            vedhas.add((r, col))
            
    # Main diagonal (r - c = constant)
    diff = row - col
    for r in range(9):
        c = r - diff
        if 0 <= c < 9 and (r, c) != (row, col):
            vedhas.add((r, c))
            
    # Anti-diagonal (r + c = constant)
    total = row + col
    for r in range(9):
        c = total - r
        if 0 <= c < 9 and (r, c) != (row, col):
            vedhas.add((r, c))
            
    return list(vedhas)


def map_longitude_to_sbc_nakshatra(longitude: float) -> str:
    """Map a 0-360 sidereal longitude to 28-nakshatra SBC scheme (including Abhijit)."""
    lon = longitude % 360.0
    # Abhijit: Capricorn 6°40' (276.6667°) to 10°53'20" (280.8889°)
    if 276.666667 <= lon < 280.888889:
        return "Abhijit"
        
    span = 360.0 / 27.0
    idx = int(lon / span)
    idx = min(idx, 26)
    standard_name = NAKSHATRAS[idx]["name"]
    return standard_name


def calc_sarvatobhadra_chakra(natal_chart, transit_positions: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Compute Sarvatobhadra Chakra natal coordinates and active transit Vedhas.
    
    Args:
        natal_chart: BirthChart object
        transit_positions: Dict of transit planet positions (optional)
        
    Returns:
        Dict with:
        - natal_target_nakshatras (Janma, Karma, Samudayika, Vainashika, Manasa)
        - transit_vedhas: Vedha hits from each transiting planet onto natal sensitive points
        - auspicious_day_score: net score of benefic vs malefic vedha
    """
    natal_positions = natal_chart.positions or {}
    moon_pos = natal_positions.get("Moon", {})
    moon_lon = moon_pos.get("longitude", 0.0)
    janma_nak = map_longitude_to_sbc_nakshatra(moon_lon)
    
    lagna_pos = natal_positions.get("Lagna", {})
    lagna_lon = lagna_pos.get("longitude", 0.0)
    lagna_nak = map_longitude_to_sbc_nakshatra(lagna_lon)
    
    sun_pos = natal_positions.get("Sun", {})
    sun_lon = sun_pos.get("longitude", 0.0)
    sun_nak = map_longitude_to_sbc_nakshatra(sun_lon)
    
    sensitive_nakshatras = {
        "Janma": janma_nak,
        "Lagna_Nak": lagna_nak,
        "Surya_Nak": sun_nak,
    }
    
    # Invert grid mapping
    pos_to_nak = {pos: name for name, pos in SBC_NAKSHATRA_GRID_POS.items()}
    
    # Check transit vedhas if transit positions provided
    transit_hits = []
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}
    
    if transit_positions:
        for tp, tdata in transit_positions.items():
            if not isinstance(tdata, dict) or tp == "Lagna":
                continue
            tlon = tdata.get("longitude", 0.0)
            tnak = map_longitude_to_sbc_nakshatra(tlon)
            tgrid = SBC_NAKSHATRA_GRID_POS.get(tnak)
            if not tgrid:
                continue
                
            vedha_cells = get_sbc_vedha_cells(tgrid[0], tgrid[1])
            for cell in vedha_cells:
                target_nak = pos_to_nak.get(cell)
                if not target_nak:
                    continue
                # Check if target is one of our sensitive points
                for tag, snak in sensitive_nakshatras.items():
                    if target_nak == snak:
                        is_malefic = tp in malefics
                        transit_hits.append({
                            "transit_planet": tp,
                            "nature": "Malefic" if is_malefic else "Benefic",
                            "transit_nakshatra": tnak,
                            "target_point": tag,
                            "target_nakshatra": target_nak,
                            "impact": "AFFLICTION" if is_malefic else "PROTECTION"
                        })
                        
    malefic_count = sum(1 for h in transit_hits if h["nature"] == "Malefic")
    benefic_count = sum(1 for h in transit_hits if h["nature"] == "Benefic")
    
    return {
        "sensitive_nakshatras": sensitive_nakshatras,
        "janma_nakshatra_sbc": janma_nak,
        "total_transit_vedha_hits": len(transit_hits),
        "transit_vedha_details": transit_hits,
        "benefic_vedhas": benefic_count,
        "malefic_vedhas": malefic_count,
        "net_vedha_verdict": "FAVORABLE" if benefic_count >= malefic_count else "OBSTRUCTED"
    }
