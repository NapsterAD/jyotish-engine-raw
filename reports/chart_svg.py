"""
chart_svg.py — Pure Python vector SVG Kundali diagram generator.
Renders high-resolution, print-ready North Indian and South Indian Vedic birth charts.
Zero external dependencies — pure SVG generation.
"""

from typing import Dict, List, Any, Optional

PLANET_SHORT = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
    "Rahu": "Ra", "Ketu": "Ke", "Lagna": "Asc", "Ascendant": "Asc",
    "Gulika": "Gu", "Maandi": "Md", "Uranus": "Ur", "Neptune": "Ne", "Pluto": "Pl"
}

SIGN_NUMBERS = {
    "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4,
    "Leo": 5, "Virgo": 6, "Libra": 7, "Scorpio": 8,
    "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12
}

SIGN_NAMES_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


def _planet_label(p):
    """Short print label: Su, Su(R), Ve↑, Ma↓ plus optional degree."""
    name = p.get("short_name") or PLANET_SHORT.get(p.get("name", ""), (p.get("name") or "")[:2])
    dignity = p.get("dignity") or ""
    if p.get("retro"):
        name += "(R)"
    if dignity == "Exalted":
        name += "↑"
    elif dignity == "Debilitated":
        name += "↓"
    elif dignity in ("Own Sign", "Moolatrikona"):
        name += "*"
    extra_cls = ""
    if p.get("retro") or dignity == "Debilitated":
        extra_cls = " k-retro"
    elif dignity == "Exalted":
        extra_cls = " k-exalt"
    elif dignity in ("Own Sign", "Moolatrikona"):
        extra_cls = " k-own"
    return name, extra_cls, p.get("deg_str") or ""


def _house_data_by_sign(house_data):
    """Accept house-number dicts from extract_chart_house_data()."""
    if not house_data:
        return {}
    sample = next(iter(house_data))
    if isinstance(sample, int) or (isinstance(sample, str) and str(sample).isdigit()):
        out = {}
        for info in house_data.values():
            if not isinstance(info, dict):
                continue
            sign = info.get("sign")
            if sign:
                out[sign] = info
        return out
    return house_data


def render_north_indian_svg(
    house_data: Dict[int, Dict[str, Any]],
    title: str = "Rashi Chart (D-1)",
    width: int = 380,
    height: int = 380,
    theme: str = "gold"
) -> str:
    """
    Generate North Indian Diamond Kundali SVG.
    
    Args:
        house_data: dict[1..12] -> {
            "sign": "Libra",
            "sign_num": 7,
            "planets": [{"name": "Sun", "retro": False, "deg": 19.26, "dignity": "Debilitated"}, ...]
        }
        title: Chart title shown in center or top
        width, height: dimensions in px
        theme: "gold", "navy", or "monochrome"
    """
    W = width
    H = height
    
    # Theme color palettes
    if theme == "gold":
        bg = "#ffffff"
        border_color = "#92400e" # warm deep amber/bronze
        line_color = "#b45309"
        kendra_bg = "#fffbeb" # subtle warm tint for kendras (1, 4, 7, 10)
        trikona_bg = "#fefce8"
        text_color = "#1e293b"
        sign_num_color = "#b45309"
        planet_color = "#0f172a"
        retro_color = "#b91c1c"
        exalt_color = "#15803d"
    elif theme == "navy":
        bg = "#0f172a"
        border_color = "#f59e0b"
        line_color = "#d97706"
        kendra_bg = "#1e293b"
        trikona_bg = "#1e293b"
        text_color = "#f8fafc"
        sign_num_color = "#fbbf24"
        planet_color = "#f8fafc"
        retro_color = "#f87171"
        exalt_color = "#4ade80"
    else: # monochrome for black-and-white printing
        bg = "#ffffff"
        border_color = "#111827"
        line_color = "#374151"
        kendra_bg = "#f9fafb"
        trikona_bg = "#ffffff"
        text_color = "#111827"
        sign_num_color = "#4b5563"
        planet_color = "#000000"
        retro_color = "#000000"
        exalt_color = "#000000"

    # Define polygon coordinate points for all 12 houses
    # Base points
    p_tl = "0,0"
    p_tr = f"{W},0"
    p_br = f"{W},{H}"
    p_bl = f"0,{H}"
    
    p_tm = f"{W/2},0"
    p_rm = f"{W},{H/2}"
    p_bm = f"{W/2},{H}"
    p_lm = f"0,{H/2}"
    p_c = f"{W/2},{H/2}"

    # House Polygons
    # 1H (Top Diamond): p_tm -> p_c -> (W/4, H/4) -> wait, standard diamond:
    # Inner diamond vertices: p_tm, p_rm, p_bm, p_lm
    # Diagonals: (0,0)-(W,H) and (W,0)-(0,H)
    # The diagonals intersect the diamond edges at midpoints of quarter-squares:
    # Top-center diamond is House 1: vertices (W/2, 0), (3W/4, H/4), (W/2, H/2), (W/4, H/4)
    # Left-center diamond is House 4: vertices (0, H/2), (W/4, H/4), (W/2, H/2), (W/4, 3H/4)
    # Bottom-center diamond is House 7: vertices (W/2, H), (W/4, 3H/4), (W/2, H/2), (3W/4, 3H/4)
    # Right-center diamond is House 10: vertices (W, H/2), (3W/4, H/4), (W/2, H/2), (3W/4, 3H/4)
    
    # 2H (Top Left, upper): (0,0), (W/2, 0), (W/4, H/4)
    # 3H (Top Left, lower): (0,0), (0, H/2), (W/4, H/4)
    # 5H (Bottom Left, upper): (0, H/2), (0, H), (W/4, 3H/4)
    # 6H (Bottom Left, lower): (0, H), (W/2, H), (W/4, 3H/4)
    # 8H (Bottom Right, lower): (W/2, H), (W, H), (3W/4, 3H/4)
    # 9H (Bottom Right, upper): (W, H/2), (W, H), (3W/4, 3H/4)
    # 11H (Top Right, lower): (W, 0), (W, H/2), (3W/4, H/4)
    # 12H (Top Right, upper): (0+W/2, 0), (W, 0), (3W/4, H/4)

    house_polygons = {
        1: f"{W/2},0 {3*W/4},{H/4} {W/2},{H/2} {W/4},{H/4}",
        2: f"0,0 {W/2},0 {W/4},{H/4}",
        3: f"0,0 0,{H/2} {W/4},{H/4}",
        4: f"0,{H/2} {W/4},{H/4} {W/2},{H/2} {W/4},{3*H/4}",
        5: f"0,{H/2} 0,{H} {W/4},{3*H/4}",
        6: f"0,{H} {W/2},{H} {W/4},{3*H/4}",
        7: f"{W/2},{H} {W/4},{3*H/4} {W/2},{H/2} {3*W/4},{3*H/4}",
        8: f"{W/2},{H} {W},{H} {3*W/4},{3*H/4}",
        9: f"{W},{H/2} {W},{H} {3*W/4},{3*H/4}",
        10: f"{W},{H/2} {3*W/4},{H/4} {W/2},{H/2} {3*W/4},{3*H/4}",
        11: f"{W},0 {W},{H/2} {3*W/4},{H/4}",
        12: f"{W/2},0 {W},0 {3*W/4},{H/4}",
    }

    # Center positions for text placement (sign numbers & planets)
    house_centers = {
        1:  (W * 0.50, H * 0.25, W * 0.50, H * 0.12),
        2:  (W * 0.26, H * 0.14, W * 0.38, H * 0.08),
        3:  (W * 0.14, H * 0.26, W * 0.08, H * 0.38),
        4:  (W * 0.25, H * 0.50, W * 0.12, H * 0.50),
        5:  (W * 0.14, H * 0.74, W * 0.08, H * 0.62),
        6:  (W * 0.26, H * 0.86, W * 0.38, H * 0.92),
        7:  (W * 0.50, H * 0.75, W * 0.50, H * 0.88),
        8:  (W * 0.74, H * 0.86, W * 0.62, H * 0.92),
        9:  (W * 0.86, H * 0.74, W * 0.92, H * 0.62),
        10: (W * 0.75, H * 0.50, W * 0.88, H * 0.50),
        11: (W * 0.86, H * 0.26, W * 0.92, H * 0.38),
        12: (W * 0.74, H * 0.14, W * 0.62, H * 0.08),
    }

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" class="kundali-svg">')
    svg.append(f'  <defs>')
    svg.append(f'    <style>')
    svg.append(f'      .k-bg {{ fill: {bg}; }}')
    svg.append(f'      .k-kendra {{ fill: {kendra_bg}; fill-opacity: 0.7; }}')
    svg.append(f'      .k-lagna-poly {{ fill: {kendra_bg}; fill-opacity: 0.95; }}')
    svg.append(f'      .k-line {{ stroke: {line_color}; stroke-width: 1.65; stroke-linejoin: round; }}')
    svg.append(f'      .k-border {{ stroke: {border_color}; stroke-width: 2.8; fill: none; }}')
    svg.append(f'      .k-sign-num {{ font-family: "Cinzel", "Marcellus", serif; font-size: 10px; font-weight: 700; fill: {sign_num_color}; text-anchor: middle; }}')
    svg.append(f'      .k-planet {{ font-family: "Inter", -apple-system, sans-serif; font-size: 10px; font-weight: 650; fill: {planet_color}; text-anchor: middle; }}')
    svg.append(f'      .k-retro {{ fill: {retro_color}; font-weight: 700; }}')
    svg.append(f'      .k-exalt {{ fill: {exalt_color}; font-weight: 700; }}')
    svg.append(f'      .k-own {{ fill: {sign_num_color}; font-weight: 700; }}')
    svg.append(f'      .k-deg {{ font-size: 7.5px; font-weight: 400; opacity: 0.78; fill: {text_color}; }}')
    svg.append(f'    </style>')
    svg.append(f'  </defs>')

    # Background
    svg.append(f'  <rect width="{W}" height="{H}" class="k-bg"/>')

    # Draw house polygon backgrounds
    for h, poly in house_polygons.items():
        if h == 1:
            cls = "k-lagna-poly"
        elif h in (1, 4, 7, 10):
            cls = "k-kendra"
        else:
            cls = "k-bg"
        svg.append(f'  <polygon points="{poly}" class="{cls}"/>')

    # Draw geometric structure lines
    # Outer box
    svg.append(f'  <rect x="0" y="0" width="{W}" height="{H}" class="k-border"/>')
    # Diagonals
    svg.append(f'  <line x1="0" y1="0" x2="{W}" y2="{H}" class="k-line"/>')
    svg.append(f'  <line x1="{W}" y1="0" x2="0" y2="{H}" class="k-line"/>')
    # Inner diamond
    svg.append(f'  <polygon points="{W/2},0 {W},{H/2} {W/2},{H} 0,{H/2}" class="k-line" fill="none"/>')

    # Render Sign numbers and Planet labels
    for h in range(1, 13):
        h_info = house_data.get(h, {})
        sign_num = h_info.get("sign_num", "")
        planets = h_info.get("planets", [])

        cx, cy, sx, sy = house_centers[h]

        # Sign number
        if sign_num:
            svg.append(f'  <text x="{sx:.1f}" y="{sy:.1f}" class="k-sign-num" dominant-baseline="central">{sign_num}</text>')

        # Planet listing inside house
        if planets:
            count = len(planets)
            line_height = 11.5 if count > 3 else 13.0
            start_y = cy - ((count - 1) * line_height / 2.0)
            for i, p in enumerate(planets):
                py = start_y + (i * line_height)
                label, extra_cls, deg_str = _planet_label(p)
                if deg_str:
                    svg.append(
                        f'  <text x="{cx:.1f}" y="{py:.1f}" class="k-planet{extra_cls}" dominant-baseline="central">'
                        f'{label} <tspan class="k-deg">{deg_str}</tspan></text>'
                    )
                else:
                    svg.append(
                        f'  <text x="{cx:.1f}" y="{py:.1f}" class="k-planet{extra_cls}" dominant-baseline="central">{label}</text>'
                    )

    svg.append('</svg>')
    return '\n'.join(svg)


def render_south_indian_svg(
    sign_data: Dict[str, Dict[str, Any]],
    lagna_sign: str = "Aries",
    title: str = "Rashi Chart (D-1)",
    width: int = 380,
    height: int = 380,
    theme: str = "gold"
) -> str:
    """
    Generate South Indian (Fixed-Sign) Kundali SVG.
    In South Indian charts, signs occupy fixed squares in clockwise order starting from Pisces (top-left).
    Accepts either sign-keyed dicts or house-number dicts from extract_chart_house_data().
    """
    sign_data = _house_data_by_sign(sign_data)
    W = width
    H = height
    cell_w = W / 4.0
    cell_h = H / 4.0

    # Grid mapping for 12 signs in South Indian format: (row, col) from top-left (0,0)
    south_grid = {
        "Pisces":      (0, 0),
        "Aries":       (0, 1),
        "Taurus":      (0, 2),
        "Gemini":      (0, 3),
        "Cancer":      (1, 3),
        "Leo":         (2, 3),
        "Virgo":       (3, 3),
        "Libra":       (3, 2),
        "Scorpio":     (3, 1),
        "Sagittarius": (3, 0),
        "Capricorn":   (2, 0),
        "Aquarius":    (1, 0),
    }

    border_color = "#92400e" if theme == "gold" else ("#f59e0b" if theme == "navy" else "#111827")
    line_color = "#b45309" if theme == "gold" else ("#d97706" if theme == "navy" else "#374151")
    bg = "#ffffff" if theme != "navy" else "#0f172a"
    cell_bg = "#fffbeb" if theme == "gold" else ("#1e293b" if theme == "navy" else "#ffffff")
    lagna_bg = "#fef3c7" if theme == "gold" else ("#334155" if theme == "navy" else "#f3f4f6")
    text_color = "#0f172a" if theme != "navy" else "#f8fafc"

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" class="kundali-svg south-indian">')
    svg.append(f'  <defs>')
    svg.append(f'    <style>')
    svg.append(f'      .si-bg {{ fill: {bg}; }}')
    svg.append(f'      .si-cell {{ fill: {cell_bg}; stroke: {line_color}; stroke-width: 1.2; }}')
    svg.append(f'      .si-lagna {{ fill: {lagna_bg}; }}')
    svg.append(f'      .si-border {{ stroke: {border_color}; stroke-width: 2.2; fill: none; }}')
    svg.append(f'      .si-sign-name {{ font-family: "Inter", sans-serif; font-size: 9px; font-weight: 700; fill: #6b7280; text-anchor: start; }}')
    svg.append(f'      .si-planet {{ font-family: "Inter", sans-serif; font-size: 10px; font-weight: 650; fill: {text_color}; text-anchor: middle; }}')
    svg.append(f'      .si-planet.k-retro {{ fill: #b91c1c; }}')
    svg.append(f'      .si-planet.k-exalt {{ fill: #15803d; }}')
    svg.append(f'      .si-planet.k-own {{ fill: {border_color}; }}')
    svg.append(f'      .si-asc {{ font-family: "Cinzel", serif; font-size: 10px; font-weight: 800; fill: #b45309; text-anchor: end; }}')
    svg.append(f'      .si-center-title {{ font-family: "Cinzel", "Marcellus", serif; font-size: 14px; font-weight: 700; fill: {border_color}; text-anchor: middle; }}')
    svg.append(f'    </style>')
    svg.append(f'  </defs>')

    svg.append(f'  <rect width="{W}" height="{H}" class="si-bg"/>')
    svg.append(f'  <rect x="0" y="0" width="{W}" height="{H}" class="si-border"/>')

    # Draw cells for 12 signs
    for sign, (r, c) in south_grid.items():
        x = c * cell_w
        y = r * cell_h
        is_lagna = (sign == lagna_sign)
        cls = "si-cell si-lagna" if is_lagna else "si-cell"
        svg.append(f'  <rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" class="{cls}"/>')

        # Sign label
        svg.append(f'  <text x="{x + 4}" y="{y + 11}" class="si-sign-name">{sign[:3].upper()}</text>')

        # Lagna marker
        if is_lagna:
            svg.append(f'  <text x="{x + cell_w - 4}" y="{y + 11}" class="si-asc">ASC</text>')
            # Diagonal slash across top corner for Lagna
            svg.append(f'  <line x1="{x}" y1="{y + cell_h * 0.35}" x2="{x + cell_w * 0.35}" y2="{y}" stroke="{border_color}" stroke-width="1.5" stroke-dasharray="2,2"/>')

        # Planets in this sign
        s_info = sign_data.get(sign, {})
        planets = s_info.get("planets", [])
        if planets:
            count = len(planets)
            cx = x + (cell_w / 2.0)
            cy = y + (cell_h / 2.0) + 4
            lh = 12.5
            start_y = cy - ((count - 1) * lh / 2.0)
            for i, p in enumerate(planets):
                py = start_y + (i * lh)
                label, extra_cls, deg_str = _planet_label(p)
                bit = f'{label} <tspan font-size="7.5px" opacity="0.78">{deg_str}</tspan>' if deg_str else label
                svg.append(
                    f'  <text x="{cx}" y="{py}" class="si-planet{extra_cls}" dominant-baseline="central">{bit}</text>'
                )

    # Center box title
    cx_center = W / 2.0
    cy_center = H / 2.0
    svg.append(f'  <rect x="{cell_w}" y="{cell_h}" width="{cell_w * 2}" height="{cell_h * 2}" fill="{bg}" stroke="{line_color}" stroke-width="1.2"/>')
    svg.append(f'  <text x="{cx_center}" y="{cy_center - 8}" class="si-center-title" dominant-baseline="central">{title}</text>')
    svg.append(f'  <text x="{cx_center}" y="{cy_center + 12}" font-family="Inter" font-size="10px" fill="#6b7280" text-anchor="middle">Lagna: {lagna_sign}</text>')

    svg.append('</svg>')
    return '\n'.join(svg)


def extract_chart_house_data(chart, varga_name: str = "D1") -> Dict[int, Dict[str, Any]]:
    """
    Extract structured house data from BirthChart for SVG rendering.
    Supports D1 (Rashi) and all divisional vargas (D9 Navamsa, D10 Dasamsa, etc.).
    """
    from ..core.constants import SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_9

    if varga_name == "D1":
        lagna_sign = chart.lagna_sign
        lagna_idx = chart.lagna_index
        house_map = {}
        for h in range(1, 13):
            sign_idx = (lagna_idx + h - 1) % 12
            sign_name = SIGNS[sign_idx]
            planets_in_h = []
            
            for planet in PLANETS_9:
                rc = chart.rashi_chart.get(planet, {})
                if rc.get("house_rashi") == h:
                    pos = chart.positions.get(planet, {})
                    planets_in_h.append({
                        "name": planet,
                        "short_name": PLANET_SHORT.get(planet, planet[:2]),
                        "retro": pos.get("retrograde", False),
                        "dignity": rc.get("dignity", ""),
                        "deg": pos.get("degree_in_sign", 0.0),
                        "deg_str": f"{int(pos.get('degree_in_sign', 0))}°"
                    })

            # Check if Lagna itself should be shown
            if h == 1:
                lagna_pos = chart.positions.get("Lagna", {})
                planets_in_h.insert(0, {
                    "name": "Ascendant",
                    "short_name": "Asc",
                    "retro": False,
                    "dignity": "",
                    "deg": lagna_pos.get("degree_in_sign", 0.0),
                    "deg_str": f"{int(lagna_pos.get('degree_in_sign', 0))}°"
                })

            house_map[h] = {
                "sign": sign_name,
                "sign_num": sign_idx + 1,
                "lord": SIGN_LORDS[sign_name],
                "planets": planets_in_h,
            }
        return house_map
    else:
        # Varga chart (e.g. D9, D10)
        vargas = chart.vargas
        varga_data = vargas.get(varga_name, {})
        v_lagna_sign = varga_data.get("Lagna", chart.lagna_sign)
        if isinstance(v_lagna_sign, dict):
            v_lagna_sign = v_lagna_sign.get("sign", chart.lagna_sign)
        v_lagna_idx = SIGN_INDEX.get(v_lagna_sign, 0)
        
        house_map = {}
        for h in range(1, 13):
            sign_idx = (v_lagna_idx + h - 1) % 12
            sign_name = SIGNS[sign_idx]
            planets_in_h = []
            
            for planet in PLANETS_9:
                p_varga_sign = varga_data.get(planet)
                if isinstance(p_varga_sign, dict):
                    p_varga_sign = p_varga_sign.get("sign")
                if p_varga_sign == sign_name:
                    pos = chart.positions.get(planet, {})
                    planets_in_h.append({
                        "name": planet,
                        "short_name": PLANET_SHORT.get(planet, planet[:2]),
                        "retro": pos.get("retrograde", False),
                        "dignity": "",
                        "deg": 0.0,
                        "deg_str": ""
                    })

            if h == 1:
                planets_in_h.insert(0, {
                    "name": "Ascendant",
                    "short_name": "Asc",
                    "retro": False,
                    "dignity": "",
                    "deg": 0.0,
                    "deg_str": ""
                })

            house_map[h] = {
                "sign": sign_name,
                "sign_num": sign_idx + 1,
                "lord": SIGN_LORDS[sign_name],
                "planets": planets_in_h,
            }
        return house_map
