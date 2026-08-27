"""
generator.py — A4 Print Report Generator for Jyotish Calculation Engine.
Generates comprehensive, multi-page, publication-grade A4 PDF/HTML reports
directly from BirthChart instances.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..core.constants import SIGNS, SIGN_INDEX, SIGN_LORDS, PLANETS_9, PLANETS_7
from ..core.mapping import bhavat_bhavam
from .chart_svg import (
    render_north_indian_svg,
    render_south_indian_svg,
    extract_chart_house_data
)


def _embedded_font_css():
    """Base64 @font-face so Chromium print does not need Google Fonts."""
    import base64
    font_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", "fonts"
    )
    faces = (
        ("Cinzel", 700, "Cinzel-700.woff2"),
        ("Cinzel", 800, "Cinzel-800.woff2"),
        ("Inter", 400, "Inter-400.woff2"),
        ("Inter", 600, "Inter-600.woff2"),
        ("Inter", 700, "Inter-700.woff2"),
    )
    chunks = []
    for family, weight, fname in faces:
        path = os.path.join(font_dir, fname)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        chunks.append(
            f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};"
            f"font-display:swap;src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
        )
    return "\n".join(chunks)


class ReportGenerator:
    """
    Generates standalone, print-ready A4 HTML reports with embedded vector SVG charts,
    high-precision astrological tables, and interactive preview controls.
    """

    def __init__(self, css_path: Optional[str] = None):
        if css_path is None:
            css_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "templates", "styles", "report_a4.css"
            )
        self.css_path = css_path
        self._css_content = None

    def _get_css(self) -> str:
        """Load CSS with local Cinzel/Inter embedded so PDF print works offline."""
        if self._css_content is None:
            if os.path.exists(self.css_path):
                with open(self.css_path, "r", encoding="utf-8") as f:
                    raw = f.read()
            else:
                raw = "/* CSS file not found */"
            import re
            raw = re.sub(r"@import url\([^)]+\);\s*", "", raw, count=1)
            self._css_content = _embedded_font_css() + "\n" + raw
        return self._css_content

    def generate_html(
        self,
        chart,
        chart_style: str = "north",
        theme: str = "gold",
        selected_pages: Optional[List[int]] = None,
        custom_css: Optional[str] = None,
        header_title: Optional[str] = None,
        subtitle: Optional[str] = None,
        custom_notes: Optional[str] = None,
        include_toolbar: bool = True,
        watermark: Optional[str] = None,
        include_front_matter: bool = True,
    ) -> str:
        """
        Build the publication-grade A4 HTML document from a BirthChart instance.

        Args:
            chart: BirthChart instance
            chart_style: "north" or "south"
            theme: "gold", "navy", "monochrome", "ruby", "emerald", or "sapphire"
            selected_pages: List of page numbers (1..14) to render. Defaults to all 14.
            custom_css: Optional CSS string to prepend/override styles.
            header_title: Optional title override (e.g. "JYOTISH KUNDALI MASTER REPORT")
            subtitle: Optional subtitle override
            custom_notes: Optional custom consultation notes to display
            include_toolbar: Whether to render the on-screen preview toolbar
            watermark: Optional watermark text across pages (e.g. "CONFIDENTIAL")
            include_front_matter: Cover + contents sheets before the 14 body pages.

        Returns:
            Complete HTML string
        """
        base_css = self._get_css()
        css = f"{base_css}\n{custom_css}" if custom_css else base_css
        aya = chart.birth_data.get("ayanamsha", "lahiri")
        self._ayanamsha_label = (
            "True Chitrapaksha" if aya in ("lahiri", "true_chitrapaksha") else aya
        )
        self._custom_notes = custom_notes
        self._header_title_override = header_title
        self._subtitle_override = subtitle

        # Extract SVG charts
        d1_data = extract_chart_house_data(chart, "D1")
        d9_data = extract_chart_house_data(chart, "D9")
        d10_data = extract_chart_house_data(chart, "D10")

        svg_theme = theme if theme in ("gold", "navy", "monochrome") else "gold"
        if chart_style == "south":
            d1_svg = render_south_indian_svg(d1_data, chart.lagna_sign, "Rashi (D-1)", 240, 240, svg_theme)
            d9_svg = render_south_indian_svg(d9_data, d9_data[1]["sign"], "Navamsa (D-9)", 240, 240, svg_theme)
            d10_svg = render_south_indian_svg(d10_data, d10_data[1]["sign"], "Dasamsa (D-10)", 240, 240, svg_theme)
            cover_svg = render_south_indian_svg(d1_data, chart.lagna_sign, "Rashi (D-1)", 320, 320, svg_theme)
        else:
            d1_svg = render_north_indian_svg(d1_data, "Rashi (D-1)", 250, 250, svg_theme)
            d9_svg = render_north_indian_svg(d9_data, "Navamsa (D-9)", 250, 250, svg_theme)
            d10_svg = render_north_indian_svg(d10_data, "Dasamsa (D-10)", 250, 250, svg_theme)
            cover_svg = render_north_indian_svg(d1_data, "Rashi (D-1)", 320, 320, svg_theme)

        # Page Builders Dictionary
        from .pages_extended import (
            _page6_kp,
            _page7_rasi_dashas,
            _page8_transits,
            _page9_lal_nadi_marriage,
            _page10_sensitive,
        )
        from .pages_raw import (
            _page11_sthana_bav_drik,
            _page12_nak_varga,
            _page13_ingress,
            _page14_dasha_trees,
        )

        try:
            raw = chart.raw_layers or {}
        except Exception:
            raw = {}

        page_builders = {
            1: lambda: self._build_page1_core(chart, d1_svg, d9_svg),
            2: lambda: self._build_page2_bhavas(chart),
            3: lambda: self._build_page3_strengths(chart),
            4: lambda: self._build_page4_dashas(chart),
            5: lambda: self._build_page5_yogas_vargas(chart, d10_svg),
            6: lambda: _page6_kp(self, chart),
            7: lambda: _page7_rasi_dashas(self, chart),
            8: lambda: _page8_transits(self, chart),
            9: lambda: _page9_lal_nadi_marriage(self, chart),
            10: lambda: _page10_sensitive(self, chart),
            11: lambda: _page11_sthana_bav_drik(self, chart, raw),
            12: lambda: _page12_nak_varga(self, chart, raw),
            13: lambda: _page13_ingress(self, chart, raw),
            14: lambda: _page14_dasha_trees(self, chart, raw),
        }

        # Normalize selected pages
        if not selected_pages:
            selected_pages = list(range(1, 15))
        valid_pages = [p for p in selected_pages if p in page_builders]
        if not valid_pages:
            valid_pages = [1]

        front_offset = 2 if include_front_matter else 0
        self._total_pages = front_offset + len(valid_pages)
        self._page_num_map = {
            orig_p: front_offset + idx + 1 for idx, orig_p in enumerate(valid_pages)
        }

        pages_html = []
        if include_front_matter:
            pages_html.append(self._build_cover(chart, cover_svg))
            pages_html.append(self._build_toc(valid_pages))
        for pnum in valid_pages:
            page_content = page_builders[pnum]()
            if watermark:
                # Inject watermark inside section
                wm_html = f'<div class="page-watermark">{watermark}</div>'
                page_content = page_content.replace('<section class="a4-page">', f'<section class="a4-page">\n    {wm_html}')
            pages_html.append(page_content)

        rendered_pages_str = "\n".join(pages_html)

        theme_class = f"theme-{theme}" if theme in ("gold", "navy", "monochrome", "ruby", "emerald", "sapphire") else "theme-gold"

        toolbar_markup = ""
        if include_toolbar:
            toolbar_markup = f"""
  <!-- Screen Toolbar for Interactive Preview & PDF Print -->
  <header class="report-toolbar">
    <div class="toolbar-brand">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="m4.93 4.93 4.24 4.24m5.66 5.66 4.24 4.24M4.93 19.07l4.24-4.24m5.66-5.66 4.24-4.24"/>
        <circle cx="12" cy="12" r="4"/>
      </svg>
      JYOTISH ENGINE <span>· Kundali A4 Studio</span>
    </div>
    <div class="toolbar-actions">
      <div class="view-controls">
        <label for="chartStyleSelect">Chart:</label>
        <select id="chartStyleSelect" onchange="changeChartStyle(this.value)">
          <option value="north" {'selected' if chart_style == 'north' else ''}>North Indian (Diamond)</option>
          <option value="south" {'selected' if chart_style == 'south' else ''}>South Indian (Square)</option>
        </select>
        <label for="themeSelect" style="margin-left: 8px;">Theme:</label>
        <select id="themeSelect" onchange="changeTheme(this.value)">
          <option value="gold" {'selected' if theme == 'gold' else ''}>Vedic Gold</option>
          <option value="navy" {'selected' if theme == 'navy' else ''}>Midnight Navy</option>
          <option value="monochrome" {'selected' if theme == 'monochrome' else ''}>Monochrome</option>
          <option value="ruby" {'selected' if theme == 'ruby' else ''}>Ruby Crimson</option>
          <option value="emerald" {'selected' if theme == 'emerald' else ''}>Forest Emerald</option>
          <option value="sapphire" {'selected' if theme == 'sapphire' else ''}>Royal Sapphire</option>
        </select>
        <label for="zoomSlider" style="margin-left: 8px;">Zoom:</label>
        <input type="range" id="zoomSlider" min="50" max="150" value="100" oninput="adjustZoom(this.value)" style="width: 70px; accent-color: #d97706;">
      </div>
      <button class="btn btn-secondary" onclick="toggleEditMode()" id="editModeBtn" title="Click anywhere on page to edit text directly">
        ✏️ In-Place Edit
      </button>
      <button class="btn btn-primary" onclick="window.print()">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <polyline points="6 9 6 2 18 2 18 9"/>
          <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
          <rect x="6" y="14" width="12" height="8"/>
        </svg>
        Print / Save A4 PDF
      </button>
    </div>
  </header>
"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Jyotish Kundali Report — {chart.birth_data.get('name', 'Native')}</title>
  <style>
{css}
  </style>
</head>
<body class="{theme_class}">

{toolbar_markup}

  <!-- Multi-Page Document Container -->
  <main class="report-container" id="reportPages">
{rendered_pages_str}
  </main>

  <script>
    function adjustZoom(val) {{
      const container = document.getElementById('reportPages');
      if (container) {{
        container.style.transform = `scale(${{val / 100}})`;
        container.style.transformOrigin = 'top center';
      }}
    }}
    function changeChartStyle(style) {{
      const url = new URL(window.location);
      url.searchParams.set('style', style);
      window.location = url.toString();
    }}
    function changeTheme(theme) {{
      const url = new URL(window.location);
      url.searchParams.set('theme', theme);
      window.location = url.toString();
    }}
    let isEditing = false;
    function toggleEditMode() {{
      isEditing = !isEditing;
      const container = document.getElementById('reportPages');
      const btn = document.getElementById('editModeBtn');
      if (container) {{
        container.setAttribute('contenteditable', isEditing ? 'true' : 'false');
        if (btn) {{
          btn.style.background = isEditing ? '#15803d' : '';
          btn.style.color = isEditing ? '#ffffff' : '';
          btn.innerText = isEditing ? '✅ Editing Active' : '✏️ In-Place Edit';
        }}
      }}
    }}
  </script>
</body>
</html>
"""
        return html

    @staticmethod
    def _fmt_date(s):
        """ISO date → '10 Jan 2025' so years do not wrap or OCR as 2029."""
        if not s:
            return "—"
        text = str(s)[:10]
        try:
            return datetime.strptime(text, "%Y-%m-%d").strftime("%d %b %Y")
        except Exception:
            return str(s)

    @staticmethod
    def _fmt_date_short(s):
        """Compact print date '10 Jan 25' for dense portrait tables."""
        if not s:
            return "—"
        text = str(s)[:10]
        try:
            return datetime.strptime(text, "%Y-%m-%d").strftime("%d %b %y")
        except Exception:
            return str(s)[:8]

    @staticmethod
    def _fmt_lon(lon):
        """Sidereal longitude → 'Sign Dd°Mm''."""
        if lon is None:
            return "—"
        try:
            lon = float(lon) % 360.0
        except (TypeError, ValueError):
            return "—"
        sign = SIGNS[int(lon / 30.0) % 12]
        deg = lon % 30.0
        d = int(deg)
        m = int((deg - d) * 60)
        return f"{sign} {d}°{m:02d}'"

    def _build_header(self, chart, title: str, subtitle: str) -> str:
        name = chart.birth_data.get("name", "Native")
        date = chart.birth_data.get("date", "")
        time = chart.birth_data.get("time", "")
        tz = chart.birth_data.get("tz", "")
        place = chart.birth_data.get("place") or ""
        place_bit = f" · {place}" if place else ""
        
        display_title = getattr(self, "_header_title_override", None) or title
        display_sub = getattr(self, "_subtitle_override", None) or subtitle

        return f"""
    <div class="page-header">
      <div class="page-header-title">
        <h1>{display_title}</h1>
        <span class="tag">{display_sub}</span>
      </div>
      <div class="page-header-meta">
        <strong>{name}</strong>{place_bit} · {date} {time} ({tz})
      </div>
    </div>
"""

    def _build_footer(self, page_num: int, total_pages: int = None) -> str:
        mapping = getattr(self, "_page_num_map", {})
        display_num = mapping.get(page_num, page_num)
        total = total_pages or getattr(self, "_total_pages", 14)
        return f"""
    <div class="page-footer">
      <span class="f-right" style="margin-left:auto;">Page {display_num} of {total}</span>
    </div>
"""

    BODY_TITLES = {
        1: ("Birth Chart & Panchanga", "Identity, grahas, D-1 / D-9"),
        2: ("Bhavas, Karakas & Sahams", "Houses, Jaimini, sensitive points"),
        3: ("Ashtakavarga & Shadbala", "SAV, six-fold strength, Ishta-Kashta"),
        4: ("Vimshottari & Yogini", "Dasha timelines, Sade-Sati"),
        5: ("Yogas & Vargas", "Named yogas, D-10"),
        6: ("KP Significators", "ABCD, SSL chains, fold grid"),
        7: ("Rasi Dashas", "Narayana, Chara, Kalachakra, Niryana"),
        8: ("Transits & Time Pack", "Gochara, Varshaphala, eclipses"),
        9: ("Lal Kitab, Nadi, Marriage", "Pakka ghar, BNN, significators"),
        10: ("Sensitive Points", "Pushkara, Ayurdaya, extra lagnas"),
        11: ("Raw Strength", "Sthana, BAV, Drik Pinda"),
        12: ("Nakshatra & Varga Sphuta", "Chains, degrees in every varga"),
        13: ("Ingress Calendar", "Sign changes 2025–2043"),
        14: ("Dasha PD Trees", "Vimshottari and Yogini PD"),
    }

    def _build_cover(self, chart, d1_svg: str) -> str:
        b = chart.birth_data
        name = b.get("name") or "Native"
        place = b.get("place") or ""
        lat, lon = b.get("lat"), b.get("lon")
        try:
            coord = (
                f"{abs(float(lat)):.4f}°{'N' if float(lat) >= 0 else 'S'}, "
                f"{abs(float(lon)):.4f}°{'E' if float(lon) >= 0 else 'W'}"
            )
        except (TypeError, ValueError):
            coord = "—"
        lag = chart.positions.get("Lagna") or {}
        moon = chart.positions.get("Moon") or {}
        cur = {}
        try:
            cur = chart.get_current_dasha() or {}
        except Exception:
            cur = {}
        md = (cur.get("MD") or {}) if isinstance(cur.get("MD"), dict) else {}
        ad = (cur.get("AD") or {}) if isinstance(cur.get("AD"), dict) else {}
        dasha = f"{md.get('lord') or '—'} MD · {ad.get('lord') or '—'} AD"
        aya = getattr(self, "_ayanamsha_label", "True Chitrapaksha")
        total = getattr(self, "_total_pages", 16)
        return f"""
  <section class="a4-page cover-page" id="cover">
    <div class="cover-band">
      <div class="cover-kicker">Janma Kundali · Professional A4 Report</div>
      <h1 class="cover-name">{name}</h1>
      <div class="cover-place">{place or '—'}</div>
    </div>
    <div class="cover-grid">
      <div class="cover-facts">
        <table class="cover-table">
          <tr><th>Date of birth</th><td>{self._fmt_date(b.get('date'))}</td></tr>
          <tr><th>Time</th><td>{b.get('time', '—')} ({b.get('tz', '—')})</td></tr>
          <tr><th>Coordinates</th><td>{coord}</td></tr>
          <tr><th>Ayanamsha</th><td>{aya}</td></tr>
          <tr><th>Lagna</th><td>{lag.get('sign', '—')} {lag.get('dms', '')}</td></tr>
          <tr><th>Moon</th><td>{moon.get('sign', '—')} {moon.get('nakshatra', '')} p{moon.get('pada', '')}</td></tr>
          <tr><th>Current dasha</th><td>{dasha}</td></tr>
        </table>
        <p class="cover-note">Calculated offline from civil birth data. Formulas: rules.md. This booklet is a calculation report, not a prediction.</p>
      </div>
      <div class="cover-chart">
        {d1_svg}
        <div class="cover-chart-cap">Rashi (D-1)</div>
      </div>
    </div>
    <div class="page-footer cover-footer">
      <span class="f-left">JYOTISH ENGINE · {total} A4 sheets</span>
      <span class="f-right">Cover</span>
    </div>
  </section>
"""

    def _build_toc(self, valid_pages) -> str:
        mapping = getattr(self, "_page_num_map", {})
        total = getattr(self, "_total_pages", 16)
        rows = [
            "<tr><td>Cover</td><td>Identity &amp; D-1 kundli</td><td class='right'>Cover</td></tr>",
            "<tr><td>Contents</td><td>This sheet</td><td class='right'>2</td></tr>",
        ]
        for p in valid_pages:
            title, sub = self.BODY_TITLES.get(p, (f"Page {p}", ""))
            disp = mapping.get(p, p)
            rows.append(
                f"<tr><td>{title}</td><td>{sub}</td>"
                f"<td class='right'>{disp}</td></tr>"
            )
        return f"""
  <section class="a4-page toc-page" id="contents">
    <div>
      <div class="page-header">
        <div class="page-header-title">
          <h1>Contents</h1>
          <span class="tag">A4 Kundali</span>
        </div>
      </div>
      <p class="toc-lead">Body sheets keep their original section titles. Page numbers below include this front matter.</p>
      <table class="data-table toc-table">
        <thead>
          <tr><th>Section</th><th>What is on the sheet</th><th class="right">Page</th></tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
    <div class="page-footer">
      <span class="f-right" style="margin-left:auto;">Page 2 of {total}</span>
    </div>
  </section>
"""


    # ═══════════════════════════════════════════════════════════════════
    # PAGE 1: CORE CHART & PANCHANGA
    # ═══════════════════════════════════════════════════════════════════
    def _build_page1_core(self, chart, d1_svg: str, d9_svg: str) -> str:
        b = chart.birth_data
        p = chart.panchang
        t = p.get("tithi", {})
        v = p.get("vara", {})
        n = p.get("nakshatra", {})
        y = p.get("yoga", {})
        k = p.get("karana", {})
        h = p.get("hora", {})
        sr = chart.sunrise_sunset

        # Planetary table rows
        rows = []
        for planet in ["Lagna"] + list(PLANETS_9):
            pos = chart.positions.get(planet, {})
            if not pos or planet.startswith("_"):
                continue

            sign = pos.get("sign", "")
            deg_dms = pos.get("dms", "")
            nak = pos.get("nakshatra", "")
            pada = pos.get("pada", "")
            nak_lord = pos.get("nakshatra_lord", "")
            
            # KP Sub lord if available
            kp_info = chart.kp.get("planets", {}).get(planet, {}) if hasattr(chart, "kp") and chart.kp else {}
            sub_lord = kp_info.get("sub_lord") or pos.get("sub_lord", "")
            ssl = kp_info.get("sub_sub_lord") or pos.get("sub_sub_lord", "")
            sssl = kp_info.get("sssl_lord") or pos.get("sssl_lord", "")
            if ssl:
                sub_lord = f"{sub_lord}/{ssl}" + (f"/{sssl}" if sssl else "")
            kp249 = kp_info.get("kp_249") or pos.get("kp_249", "—")
            rem = pos.get("nakshatra_remaining_pct")
            rem_s = f"{rem:.0f}%" if isinstance(rem, (int, float)) else "—"

            if planet == "Lagna":
                house_rashi = 1
                house_chalit = 1
                dignity = "—"
                retro_str = "—"
                badge_cls = ""
            else:
                rc = chart.rashi_chart.get(planet, {})
                cc = chart.chalit_chart.get(planet, {})
                house_rashi = rc.get("house_rashi", "—")
                house_chalit = cc.get("house_chalit", house_rashi)
                dignity = rc.get("dignity", "Neutral")
                is_retro = pos.get("retrograde", False)
                retro_str = '<span class="badge badge-retro">R</span>' if is_retro else "Dir"

                if dignity == "Exalted":
                    badge_cls = "badge badge-exalt"
                elif dignity == "Debilitated":
                    badge_cls = "badge badge-deb"
                elif dignity in ("Own Sign", "Moolatrikona"):
                    badge_cls = "badge badge-own"
                elif dignity == "Friendly":
                    badge_cls = "badge badge-friend"
                else:
                    badge_cls = "badge badge-enemy"

            chalit_display = f"{house_chalit}"
            if house_chalit != house_rashi:
                chalit_display = f"<strong>{house_chalit}</strong>*"

            rows.append(f"""
          <tr>
            <td class="bold">{planet}</td>
            <td>{sign}</td>
            <td>{deg_dms}</td>
            <td>{nak} (P{pada})</td>
            <td>{nak_lord}</td>
            <td>{sub_lord}</td>
            <td class="center">{kp249}</td>
            <td class="center">{rem_s}</td>
            <td class="center">{retro_str}</td>
            <td><span class="{badge_cls}">{dignity}</span></td>
            <td class="center">{house_rashi}H</td>
            <td class="center">{chalit_display}</td>
          </tr>""")

        table_rows_html = "\n".join(rows)

        comb = {}
        try:
            comb = chart.combustion or {}
        except Exception:
            comb = {}
        comb_bits = []
        for p in PLANETS_7:
            c = comb.get(p) or {}
            if not isinstance(c, dict):
                continue
            st = c.get("state") or "NONE"
            if st in ("NONE", "EXEMPT"):
                continue
            comb_bits.append(f"{p} {st} sep {c.get('separation')}° (orb {c.get('orb')})")
        yuddha = {}
        try:
            yuddha = chart.yuddha or {}
        except Exception:
            yuddha = {}
        wars = yuddha.get("wars") or []
        war_s = "; ".join(
            f"{w.get('winner')} beats {w.get('loser')} ({w.get('separation')}°)"
            for w in wars
        ) or "none"
        fn = chart.functional_nature or {}
        fn_s = " · ".join(
            f"{g}: {', '.join(x[0] if isinstance(x, (list, tuple)) else str(x) for x in (fn.get(g) or []))}"
            for g in ("benefic", "malefic", "neutral")
        )

        return f"""
  <section class="a4-page" id="page1">
    <div>
      {self._build_header(chart, "Janma Kundali & Astro Identity", "Natal Horoscope")}

      <!-- Native Meta & Panchanga Grid -->
      <div class="native-meta-grid">
        <div class="info-card gold-border">
          <table class="info-table">
            <tr><td class="label">Native Name:</td><td class="val">{b.get('name', 'N/A')}</td><td class="label">Ayanamsha:</td><td class="val">{self._ayanamsha_label} ({chart.positions.get('_ayanamsha', '')}°)</td></tr>
            <tr><td class="label">Date of Birth:</td><td class="val">{b.get('date')}</td><td class="label">Place:</td><td class="val">{b.get('place') or f"{b.get('lat')}°, {b.get('lon')}°"}</td></tr>
            <tr><td class="label">Time of Birth:</td><td class="val">{b.get('time')} ({b.get('tz')})</td><td class="label">Coordinates:</td><td class="val">{b.get('lat')}° N, {b.get('lon')}° E</td></tr>
            <tr><td class="label">Ascendant (Lagna):</td><td class="val"><strong>{chart.lagna_sign}</strong> ({chart.positions.get('Lagna', {}).get('dms', '')})</td><td class="label">Birth Period:</td><td class="val">{'Day' if sr.get('is_day_birth') else 'Night'} Birth · {sr.get('sunrise', '—')} / {sr.get('sunset', '—')} (Hora: {h.get('hora_lord', '—')})</td></tr>
          </table>
        </div>

        <div class="info-card">
          <div class="panchang-grid">
            <div class="panchang-item">
              <div class="p-label">Tithi</div>
              <div class="p-value">{t.get('name', '—')}</div>
              <div class="p-sub">{t.get('paksha', '')} ({t.get('lord', '')})</div>
            </div>
            <div class="panchang-item">
              <div class="p-label">Vara (Day)</div>
              <div class="p-value">{v.get('weekday', '—')}</div>
              <div class="p-sub">Lord: {v.get('lord', '')}</div>
            </div>
            <div class="panchang-item">
              <div class="p-label">Nakshatra</div>
              <div class="p-value">{n.get('name', '—')}</div>
              <div class="p-sub">Lord: {n.get('lord', '')}</div>
            </div>
            <div class="panchang-item">
              <div class="p-label">Yoga</div>
              <div class="p-value">{y.get('name', '—')}</div>
              <div class="p-sub">#{y.get('number', '')} Nithya</div>
            </div>
            <div class="panchang-item">
              <div class="p-label">Karana</div>
              <div class="p-value">{k.get('name', '—')}</div>
              <div class="p-sub">#{k.get('number', '')} Half-Tithi</div>
            </div>
            <div class="panchang-item">
              <div class="p-label">Planetary Hora</div>
              <div class="p-value">{h.get('hora_lord', '—')}</div>
              <div class="p-sub">{'Day' if h.get('is_day_hora') else 'Night'} Segment</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row (D1 & D9) -->
      <div class="charts-row">
        <div class="chart-card">
          <h3>D-1 Rashi Kundali (Birth Chart)</h3>
          {d1_svg}
        </div>
        <div class="chart-card">
          <h3>D-9 Navamsa Kundali (Dharma & Destiny)</h3>
          {d9_svg}
        </div>
      </div>

      <!-- Planetary Positions Table -->
      <div class="section-title">
        <span class="icon-sym">✦</span> Planetary Longitudes & Dignities
        <span class="sub">True Chitrapaksha Sidereal Coordinates</span>
      </div>
      <table class="data-table" style="font-size:7.5pt;">
        <thead>
          <tr>
            <th>Graha</th>
            <th>Rashi (Sign)</th>
            <th>Longitude</th>
            <th>Nakshatra (Pada)</th>
            <th>Star Lord</th>
            <th>Sub Lord (KP)</th>
            <th class="center">249</th>
            <th class="center">Nak%</th>
            <th class="center">Motion</th>
            <th>Dignity</th>
            <th class="center">Rashi H.</th>
            <th class="center">Chalit H.</th>
          </tr>
        </thead>
        <tbody>
          {table_rows_html}
        </tbody>
      </table>
      <div style="font-size:7.5pt;line-height:1.4;margin-top:5px;color:#1e293b;">
        <strong>Combustion:</strong> {'; '.join(comb_bits) or 'none'} ·
        <strong>Graha Yuddha:</strong> {war_s}<br>
        <strong>Functional nature:</strong> {fn_s}
      </div>
    </div>
    {self._build_footer(1)}
  </section>
"""

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 2: BHAVAS, CHALIT, ARUDHAS & SPECIAL POINTS
    # ═══════════════════════════════════════════════════════════════════
    def _build_page2_bhavas(self, chart) -> str:
        # House Details Table
        h_rows = []
        house_map = chart.get_house_map("rashi")
        
        for h in range(1, 13):
            info = house_map[h]
            sign = info["sign"]
            lord = info["lord"]
            planets_rashi = info["planets"]
            planets_chalit = chart.get_planets_in_house(h, "chalit")
            aspects_in = chart.get_aspects_to_house(h)
            
            # Bhavat bhavam
            bb_house = bhavat_bhavam(h)
            
            p_r_str = ", ".join(planets_rashi) if planets_rashi else "—"
            p_c_str = ", ".join(planets_chalit) if planets_chalit else "—"
            asp_str = ", ".join(aspects_in) if aspects_in else "—"

            h_rows.append(f"""
          <tr>
            <td class="bold center">{h}</td>
            <td>{sign}</td>
            <td class="bold">{lord}</td>
            <td>{p_r_str}</td>
            <td>{p_c_str}</td>
            <td>{asp_str}</td>
            <td class="center">{bb_house}H</td>
          </tr>""")

        # Jaimini Karakas rows
        k_data = chart.karakas.get("details", {})
        k_rows = []
        karaka_names = {
            "AK": "Atmakaraka (Soul)", "AmK": "Amatyakaraka (Career)",
            "BK": "Bhratrikaraka (Siblings/Guru)", "MK": "Matrikaraka (Mother)",
            "PK": "Putrakaraka (Intellect/Progeny)", "GK": "Gnati Karaka (Obstacles)",
            "DK": "Darakaraka (Spouse/Partner)"
        }
        for planet, k_info in k_data.items():
            k_tag = k_info.get("karaka", "")
            k_name = karaka_names.get(k_tag, k_tag)
            k_deg = f"{k_info.get('degree_in_sign', 0):.2f}°"
            k_rows.append(f"""
          <tr>
            <td class="bold">{k_tag}</td>
            <td>{k_name}</td>
            <td class="bold">{planet}</td>
            <td>{k_deg}</td>
          </tr>""")

        # Arudha Padas
        arudhas = chart.arudhas
        a_padas_list = []
        for i in range(1, 13):
            key = f"A{i}"
            a_info = arudhas.get(key, {})
            a_name = a_info.get("name", key)
            a_sign = a_info.get("sign", "")
            a_padas_list.append(f"<strong>{key}</strong> ({a_name[:12]}): {a_sign}")

        # Special sensitive points
        sp = chart.special_points
        yogi = sp.get("yogi", {})
        bb = sp.get("bhrigu_bindu", {})
        vs_tajika = sp.get("vivaha_saham_tajika", {})
        vs_parashara = sp.get("vivaha_saham_parashara", {})
        fortuna = sp.get("part_of_fortune", {})
        sl = chart.special_lagnas

        return f"""
  <section class="a4-page" id="page2">
    <div>
      {self._build_header(chart, "Bhavas, Chalit, Arudhas & Special Points", "House Dynamics")}

      <div class="section-title">
        <span class="icon-sym">✦</span> Twelve Bhavas (Houses) & Chalit Displacement
        <span class="sub">Rashi vs Bhava Chalit Occupancy Comparison</span>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th class="center">Bhava</th>
            <th>Sign (Rashi)</th>
            <th>Lord</th>
            <th>Rashi Occupants</th>
            <th>Chalit Occupants</th>
            <th>Drishti (Aspects In)</th>
            <th class="center">Bhavat Bhavam</th>
          </tr>
        </thead>
        <tbody>
          {''.join(h_rows)}
        </tbody>
      </table>

      <!-- Two column grid: Jaimini Karakas + Arudha Padas -->
      <div class="two-col-grid">
        <div class="info-card">
          <div class="section-title" style="margin-top:0;">
            <span class="icon-sym">✦</span> Jaimini Chara Karakas (7-Graha)
          </div>
          <table class="data-table">
            <thead>
              <tr><th>Tag</th><th>Signification</th><th>Planet</th><th>Deg in Sign</th></tr>
            </thead>
            <tbody>
              {''.join(k_rows)}
            </tbody>
          </table>
          <div style="font-size:7.5pt; color: #64748b; margin-top: 2px;">
            <strong>Karakamsa:</strong> {chart.karakamsa.get('karakamsa') if isinstance(chart.karakamsa, dict) else chart.karakamsa}
            (AK {chart.karakas.get('karakas', {}).get('AK')} in D9)
            · 7th: {chart.karakamsa.get('karakamsa_7h') if isinstance(chart.karakamsa, dict) else ''}
            · Lord: {chart.karakamsa.get('karakamsa_lord') if isinstance(chart.karakamsa, dict) else ''}
          </div>
        </div>

        <div class="info-card">
          <div class="section-title" style="margin-top:0;">
            <span class="icon-sym">✦</span> 12 Arudha Padas (A1 to A12)
          </div>
          <table class="info-table" style="margin-top: 4px;">
            <tr>
              <td><strong>AL (A1):</strong> {arudhas.get('A1', {}).get('sign')} ({arudhas.get('A1', {}).get('house_from_lagna')}H)</td>
              <td><strong>A2:</strong> {arudhas.get('A2', {}).get('sign')}</td>
              <td><strong>A3:</strong> {arudhas.get('A3', {}).get('sign')}</td>
            </tr>
            <tr>
              <td><strong>A4:</strong> {arudhas.get('A4', {}).get('sign')}</td>
              <td><strong>A5:</strong> {arudhas.get('A5', {}).get('sign')}</td>
              <td><strong>A6:</strong> {arudhas.get('A6', {}).get('sign')}</td>
            </tr>
            <tr>
              <td><strong>A7 (Dara):</strong> {arudhas.get('A7', {}).get('sign')} ({arudhas.get('A7', {}).get('house_from_lagna')}H)</td>
              <td><strong>A8:</strong> {arudhas.get('A8', {}).get('sign')}</td>
              <td><strong>A9:</strong> {arudhas.get('A9', {}).get('sign')}</td>
            </tr>
            <tr>
              <td><strong>A10:</strong> {arudhas.get('A10', {}).get('sign')}</td>
              <td><strong>A11:</strong> {arudhas.get('A11', {}).get('sign')}</td>
              <td><strong>UL (A12):</strong> {arudhas.get('A12', {}).get('sign')} ({arudhas.get('A12', {}).get('house_from_lagna')}H)</td>
            </tr>
          </table>

          <div class="section-title" style="margin-top: 6px;">
            <span class="icon-sym">✦</span> Special Lagnas
          </div>
          <table class="info-table">
            <tr>
              <td><strong>Hora Lagna (HL):</strong> {self._fmt_lon(sl.get('hora_lagna'))}</td>
              <td><strong>Ghati Lagna (GL):</strong> {self._fmt_lon(sl.get('ghati_lagna'))}</td>
            </tr>
            <tr>
              <td><strong>Sree Lagna (SL):</strong> {self._fmt_lon(sl.get('sree_lagna'))}</td>
              <td><strong>Varnada:</strong> {self._fmt_lon(sl.get('varnada_lagna'))}</td>
            </tr>
            <tr>
              <td><strong>Bhava Lagna:</strong> {self._fmt_lon(sl.get('bhava_lagna'))}</td>
              <td><strong>Maandi / Gulika:</strong> {self._fmt_lon(sl.get('maandi'))} / {self._fmt_lon(sl.get('gulika'))}</td>
            </tr>
          </table>
        </div>
      </div>

      <!-- Special Sensitive Points & Sahams -->
      <div class="section-title">
        <span class="icon-sym">✦</span> Special Sensitive Points & Sahams
      </div>
      <div class="three-col-grid">
        <div class="stat-tile">
          <div class="st-label">Yogi / Avayogi Axis</div>
          <div class="st-value" style="font-size:9.5pt;">Yogi: {yogi.get('yogi', '—')} · Avayogi: {yogi.get('avayogi', '—')}</div>
          <div class="st-sub">Point: {yogi.get('yogi_point_sign', '')} {yogi.get('yogi_point_dms', '')} ({yogi.get('yogi_nakshatra', '')}) · SahaYogi: {yogi.get('sahayogi', '—')}</div>
        </div>
        <div class="stat-tile">
          <div class="st-label">Bhrigu Bindu (BB)</div>
          <div class="st-value" style="font-size:9.5pt;">{bb.get('sign', '')} {bb.get('dms', '')}</div>
          <div class="st-sub">Nakshatra: {bb.get('nakshatra', '')} ({bb.get('nakshatra_lord', '')}) · Transits activate destiny</div>
        </div>
        <div class="stat-tile">
          <div class="st-label">Vivaha Saham & Pars Fortuna</div>
          <div class="st-value" style="font-size:9.5pt;">Fortuna: {fortuna.get('sign', '')} {fortuna.get('dms', '')}</div>
          <div class="st-sub">Vivaha Saham (Tajika): {vs_tajika.get('sign', '')} {vs_tajika.get('dms', '')}</div>
        </div>
      </div>
    </div>
    {self._build_footer(2)}
  </section>
"""

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 3: ASHTAKAVARGA & SHADBALA
    # ═══════════════════════════════════════════════════════════════════
    def _build_page3_strengths(self, chart) -> str:
        # Ashtakavarga SAV Table
        sav_data = chart.ashtakavarga.get("sav", {})
        sav_counts = sav_data.get("sav", [0]*12)
        sav_ranking = sav_data.get("ranking", [])

        sav_head = "".join(f"<th class='center'>{s[:3]}</th>" for s in SIGNS)
        sav_pts = "".join(
            f"<td class='center bold'>{sav_counts[i] if i < len(sav_counts) else 0}</td>"
            for i in range(12)
        )
        sav_bars = []
        for i in range(12):
            pts = sav_counts[i] if i < len(sav_counts) else 0
            cls = "sav-bar-fill low" if pts < 25 else ("sav-bar-fill" if pts >= 28 else "sav-bar-fill mid")
            pct = min(100, int((pts / 40.0) * 100))
            sav_bars.append(
                f"<td><div class='sav-bar'><div class='{cls}' style='width:{pct}%;'></div></div></td>"
            )

        # Shadbala Breakdown Table
        shadbala = chart.shadbala
        sb_rows = []
        
        for planet in PLANETS_7:
            p_sb = shadbala.get(planet, {})
            comps = p_sb.get("components", {})
            sthana = comps.get("sthana", 0)
            dig = comps.get("dig", 0)
            kala = comps.get("kala", 0)
            cheshta = comps.get("cheshta", 0)
            naisargika = comps.get("naisargika", 0)
            drik = comps.get("drik", 0)
            total_shashtiamsas = p_sb.get("shashtiamsas", 0)
            rupas = p_sb.get("rupas", 0)
            req = p_sb.get("minimum", 0)
            passes = p_sb.get("passes", False)
            status_badge = '<span class="badge badge-exalt">Pass</span>' if passes else '<span class="badge badge-deb">Deficit</span>'

            sb_rows.append(f"""
          <tr>
            <td class="bold">{planet}</td>
            <td class="right">{sthana:.1f}</td>
            <td class="right">{dig:.1f}</td>
            <td class="right">{kala:.1f}</td>
            <td class="right">{cheshta:.1f}</td>
            <td class="right">{naisargika:.1f}</td>
            <td class="right">{drik:.1f}</td>
            <td class="right bold">{rupas:.2f}</td>
            <td class="right">{req:.1f}</td>
            <td class="center">{status_badge}</td>
          </tr>""")

        # Ishta / Kashta and Avasthas
        ik_data = chart.ishta_kashta
        avasthas = chart.avasthas
        ik_rows = []
        for planet in PLANETS_7:
            ik = ik_data.get(planet, {}) or {}
            av = avasthas.get(planet, {})
            av_name = av.get("avastha", av) if isinstance(av, dict) else av
            ishta = ik.get("ishta", ik.get("ishta_phala"))
            kashta = ik.get("kashta", ik.get("kashta_phala"))
            ishta = 0 if ishta is None else ishta
            kashta = 0 if kashta is None else kashta
            net = ik.get("net")
            if net is None:
                net = float(ishta) - float(kashta)
            dom = ik.get("dominant") or ("Ishta" if float(ishta) >= float(kashta) else "Kashta")
            ik_rows.append(f"""
          <tr>
            <td class="bold">{planet}</td>
            <td class="center">{av_name}</td>
            <td class="right bold" style="color: #15803d;">{float(ishta):.2f}</td>
            <td class="right bold" style="color: #b91c1c;">{float(kashta):.2f}</td>
            <td class="right">{float(net):.2f}</td>
            <td class="center">{dom}</td>
          </tr>""")

        # Bhava Bala
        bb = chart.bhava_bala
        bb_list = []
        if isinstance(bb, dict):
            for h in range(1, 13):
                val = bb.get(h, {})
                if isinstance(val, dict):
                    rup = val.get("rupas", 0)
                    lord = val.get("lord", "")
                    bb_list.append(f"H{h} ({lord[:2]}): <strong>{rup:.2f}R</strong>")
                else:
                    bb_list.append(f"H{h}: <strong>{float(val):.2f}R</strong>")
        bb_str = " · ".join(bb_list[:6]) + "<br>" + " · ".join(bb_list[6:])
        bb_detail_rows = []
        if isinstance(bb, dict):
            for h in range(1, 13):
                val = bb.get(h, {})
                if not isinstance(val, dict):
                    continue
                bb_detail_rows.append(
                    f"<tr><td class='center bold'>{h}</td><td>{val.get('lord','')}</td>"
                    f"<td class='right'>{val.get('rupas',0):.2f}</td>"
                    f"<td class='right'>{val.get('adhipati', val.get('lord_shadbala',0))}</td>"
                    f"<td class='right'>{val.get('dig',0)}</td>"
                    f"<td class='right'>{val.get('drishti',0)}</td></tr>"
                )

        kala_rows = []
        for planet in PLANETS_7:
            kd = (shadbala.get(planet, {}) or {}).get("components", {}).get("kala_detail") or {}
            kala_rows.append(
                f"<tr><td class='bold'>{planet}</td>"
                f"<td class='right'>{kd.get('natonnatha', kd.get('divaratri','—'))}</td>"
                f"<td class='right'>{kd.get('paksha','—')}</td>"
                f"<td class='right'>{kd.get('tribhaga','—')}</td>"
                f"<td class='right'>{kd.get('abda','—')}</td>"
                f"<td class='right'>{kd.get('masa','—')}</td>"
                f"<td class='right'>{kd.get('vara','—')}</td>"
                f"<td class='right'>{kd.get('hora','—')}</td>"
                f"<td class='right'>{kd.get('ayana','—')}</td></tr>"
            )

        vim = {}
        try:
            vim = chart.vimsopaka or {}
        except Exception:
            vim = {}
        vim_s = " · ".join(f"{p} {vim.get(p)}" for p in PLANETS_7 if p in vim) or "—"

        bav = chart.ashtakavarga.get("bav") or {}
        bav_head = "".join(f"<th class='center'>{s[:3]}</th>" for s in SIGNS)
        bav_rows = []
        for p in PLANETS_7 + ["Lagna"]:
            row = bav.get(p)
            if not isinstance(row, list):
                continue
            cells = "".join(f"<td class='center'>{int(x)}</td>" for x in row[:12])
            bav_rows.append(f"<tr><td class='bold'>{p}</td>{cells}</tr>")

        sodhya = chart.ashtakavarga.get("sodhya") or {}
        sod_s = " · ".join(
            f"{p} {d.get('sodhya')}" for p, d in sodhya.items() if isinstance(d, dict)
        )

        return f"""
  <section class="a4-page" id="page3">
    <div>
      {self._build_header(chart, "Ashtakavarga & Shadbala Strengths", "Potency Metrics")}

      <div class="two-col-grid">
        <!-- Sarvashtakavarga -->
        <div class="info-card">
          <div class="section-title" style="margin-top:0;">
            <span class="icon-sym">✦</span> Sarvashtakavarga (SAV Points)
            <span class="sub">Total: {sav_data.get('total', '—')} (Parashara identity 337)</span>
          </div>
          <table class="data-table compact">
            <thead><tr>{sav_head}</tr></thead>
            <tbody>
              <tr>{sav_pts}</tr>
              <tr>{''.join(sav_bars)}</tr>
            </tbody>
          </table>
          <div style="font-size:7.5pt; color: #475569;">
            <strong>Strongest Sign:</strong> {sav_data.get('strongest', ('—','—'))[0]} ({sav_data.get('strongest', ('—','—'))[1]} pts) · 
            <strong>Weakest:</strong> {sav_data.get('weakest', ('—','—'))[0]} ({sav_data.get('weakest', ('—','—'))[1]} pts)
          </div>
        </div>

        <!-- Ishta / Kashta & Baladi Avasthas -->
        <div class="info-card">
          <div class="section-title" style="margin-top:0;">
            <span class="icon-sym">✦</span> Ishta-Kashta Phala & Avasthas
          </div>
          <table class="data-table">
            <thead>
              <tr><th>Graha</th><th class="center">Baladi Avastha</th><th class="right">Ishta</th><th class="right">Kashta</th><th class="right">Net</th><th class="center">Dom</th></tr>
            </thead>
            <tbody>
              {''.join(ik_rows)}
            </tbody>
          </table>

          <div class="section-title" style="margin-top: 8px;">
            <span class="icon-sym">✦</span> Bhava Bala (lord / dig / drishti)
          </div>
          <table class="data-table compact">
            <thead><tr><th>H</th><th>Lord</th><th class="right">Rupas</th><th class="right">Adhipati</th><th class="right">Dig</th><th class="right">Drishti</th></tr></thead>
            <tbody>{''.join(bb_detail_rows)}</tbody>
          </table>
        </div>
      </div>

      <!-- 6-Fold Shadbala Breakdown Table -->
      <div class="section-title">
        <span class="icon-sym">✦</span> Comprehensive Shadbala (Six-Fold Strength Breakdown)
        <span class="sub">All values in Shashtiamsas · Rupas = Shashtiamsas / 60</span>
      </div>
      <table class="data-table compact">
        <thead>
          <tr>
            <th>Graha</th>
            <th class="right">Sthana</th>
            <th class="right">Dig</th>
            <th class="right">Kala</th>
            <th class="right">Cheshta</th>
            <th class="right">Nais</th>
            <th class="right">Drik</th>
            <th class="right gold-th">Rupas</th>
            <th class="right">Min</th>
            <th class="center">Status</th>
          </tr>
        </thead>
        <tbody>
          {''.join(sb_rows)}
        </tbody>
      </table>
      <div class="section-title"><span class="icon-sym">✦</span> Kala Bala components · Vimsopaka {vim_s}</div>
      <table class="data-table compact">
        <thead>
          <tr><th>Graha</th><th class="right">Nato</th><th class="right">Paksha</th><th class="right">Tri</th>
              <th class="right">Abda</th><th class="right">Masa</th><th class="right">Vara</th>
              <th class="right">Hora</th><th class="right">Ayana</th></tr>
        </thead>
        <tbody>{''.join(kala_rows)}</tbody>
      </table>
      <div style="font-size:7.5pt;margin-top:4px;color:#475569;">BAV 8×12 and Sodhya pinda are on sheet 11 (full matrix). Sodhya: {sod_s}</div>
    </div>
    {self._build_footer(3)}
  </section>
"""

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 4: DASHAS & TIMING
    # ═══════════════════════════════════════════════════════════════════
    def _build_page4_dashas(self, chart) -> str:
        # Vimshottari Mahadasha Table
        dashas = chart.dashas
        d_rows = []
        
        for md in dashas:
            lord = md.get("lord", "")
            start = md.get("start_date", "")
            end = md.get("end_date", "")
            dur = md.get("duration_years", 0)
            d_rows.append(f"""
          <tr>
            <td class="bold">{lord} Mahadasha</td>
            <td class="date-cell">{self._fmt_date(start)}</td>
            <td class="date-cell">{self._fmt_date(end)}</td>
            <td class="right">{dur:.2f} yrs</td>
          </tr>""")

        # Yogini Dasha Table
        yogini = chart.yogini_dasha
        y_rows = []
        majors = [yd for yd in yogini if yd.get("level") in ("Major", "MD", None) or "yogini" in yd]
        shown = 0
        for yd in majors:
            if yd.get("level") == "AD":
                continue
            name = yd.get("yogini") or yd.get("name") or ""
            lord = yd.get("planet") or yd.get("lord") or ""
            start = yd.get("start_date", "")
            end = yd.get("end_date", "")
            y_rows.append(f"""
          <tr>
            <td class="bold">{name} ({lord})</td>
            <td class="date-cell">{self._fmt_date(start)}</td>
            <td class="date-cell">{self._fmt_date(end)}</td>
          </tr>""")
            shown += 1
            if shown >= 8:
                break

        now_str = datetime.now().strftime("%Y-%m-%d")
        yogini_ad_rows = []
        current_yogini_ad = None
        current_yogini_md = None
        for yd in yogini or []:
            if yd.get("level") not in ("Major", "MD", None):
                continue
            start = yd.get("start_date") or ""
            end = yd.get("end_date") or ""
            if end and end < now_str:
                continue
            current_yogini_md = yd.get("yogini") or yd.get("name") or "Yogini"
            current_yogini_ad = None
            for sub in (yd.get("sub_periods") or [])[:8]:
                s0 = sub.get("start_date") or ""
                s1 = sub.get("end_date") or ""
                active = bool(s0 and s1 and s0 <= now_str < s1)
                if active:
                    current_yogini_ad = sub.get("yogini") or sub.get("name")
                mark = " ← now" if active else ""
                cls = " class='bold'" if active else ""
                yogini_ad_rows.append(
                    f"<tr{cls}><td>{yd.get('yogini')}</td>"
                    f"<td>{sub.get('yogini') or sub.get('name')}{mark}</td>"
                    f"<td class='date-cell'>{self._fmt_date(sub.get('start_date'))}</td>"
                    f"<td class='date-cell'>{self._fmt_date(sub.get('end_date'))}</td></tr>"
                )
            break

        # Current dasha info (engine keys: MD / AD / PD / SD / PAD)
        curr_dasha = chart.get_current_dasha(now_str, levels=5) or {}
        def _lord(block):
            if isinstance(block, dict):
                return block.get("lord", "—")
            return block or "—"
        curr_md = _lord(curr_dasha.get("MD") or curr_dasha.get("mahadasha"))
        curr_ad = _lord(curr_dasha.get("AD") or curr_dasha.get("antardasha"))
        curr_pd = _lord(curr_dasha.get("PD") or curr_dasha.get("pratyantardasha"))
        curr_sd = _lord(curr_dasha.get("SD"))
        curr_pad = _lord(curr_dasha.get("PAD"))
        ad_block = curr_dasha.get("AD") or curr_dasha.get("antardasha") or {}
        ad_span = ""
        if isinstance(ad_block, dict):
            ad_span = (
                f"{self._fmt_date(ad_block.get('start', ad_block.get('start_date', '')))}"
                f" to {self._fmt_date(ad_block.get('end', ad_block.get('end_date', '')))}"
            )

        # Sade-sati calculation
        ss_info = chart.sade_sati_for(now_str)
        ss_active = bool(ss_info.get("sade_sati") or ss_info.get("is_sade_sati"))
        ss_status = "Active" if ss_active else "Inactive"
        ss_phase = ss_info.get("phase") or "None"

        return f"""
  <section class="a4-page" id="page4">
    <div>
      {self._build_header(chart, "Vimshottari & Yogini Dasha Timelines", "Dasha Timing")}

      <!-- Active Dasha Banner -->
      <div class="dasha-banner">
        <div>
          <div class="d-level">Active Vimshottari Dasha ({self._fmt_date(now_str)})</div>
          <div class="d-val">{curr_md} MD · {curr_ad} AD · {curr_pd} PD · {curr_sd} SD · {curr_pad} PAD</div>
        </div>
        <div class="d-dates">
          {ad_span}
        </div>
      </div>

      <div class="two-col-grid">
        <!-- Vimshottari Mahadashas -->
        <div class="info-card">
          <div class="section-title" style="margin-top:0;">
            <span class="icon-sym">✦</span> Vimshottari 120-Year Cycle
          </div>
          <table class="data-table">
            <thead>
              <tr><th>Mahadasha</th><th>Start Date</th><th>End Date</th><th class="right">Duration</th></tr>
            </thead>
            <tbody>
              {''.join(d_rows)}
            </tbody>
          </table>
        </div>

        <!-- Yogini Dashas -->
        <div class="info-card">
          <div class="section-title" style="margin-top:0;">
            <span class="icon-sym">✦</span> Yogini 36-Year Cycle
          </div>
          <table class="data-table">
            <thead>
              <tr><th>Yogini Period</th><th>Start Date</th><th>End Date</th></tr>
            </thead>
            <tbody>
              {''.join(y_rows)}
            </tbody>
          </table>
          <div class="section-title" style="margin-top:6px;font-size:8pt;">{current_yogini_md or 'Yogini'} antardashas{(' · now ' + current_yogini_ad) if current_yogini_ad else ''}</div>
          <table class="data-table" style="font-size:7.5pt;">
            <thead><tr><th>MD</th><th>AD</th><th>Start</th><th>End</th></tr></thead>
            <tbody>{''.join(yogini_ad_rows) or '<tr><td colspan="4">—</td></tr>'}</tbody>
          </table>
        </div>
      </div>

      <!-- Sade-Sati & Gochara Transits -->
      <div class="section-title">
        <span class="icon-sym">✦</span> Saturn Transit (Sade-Sati) & Gochara Health
      </div>
      <div class="three-col-grid">
        <div class="stat-tile {'stat-active' if ss_active else 'stat-inactive'}">
          <div class="st-label">Sade-Sati Status</div>
          <div class="st-value" style="font-size:10pt;">{ss_status} ({ss_phase})</div>
          <div class="st-sub">Saturn within ±1 sign of Natal Moon ({chart.positions.get('Moon', {}).get('sign')})</div>
        </div>
        <div class="stat-tile {'stat-active' if (ss_info.get('ashtama_shani') or ss_info.get('kantaka_shani') or ss_info.get('is_ashtama_shani')) else 'stat-inactive'}">
          <div class="st-label">Kantaka / Ashtama Shani</div>
          <div class="st-value" style="font-size:10pt;">{'Active' if ss_info.get('ashtama_shani') or ss_info.get('kantaka_shani') or ss_info.get('is_ashtama_shani') else 'Inactive'}</div>
          <div class="st-sub">Saturn 8th or 4th from Moon check</div>
        </div>
        <div class="stat-tile">
          <div class="st-label">Badhaka Sthana & Lord</div>
          <div class="st-value" style="font-size:10pt;">H{chart.badhaka.get('house')} ({chart.badhaka.get('sign')}) · {chart.badhaka.get('lord')}</div>
          <div class="st-sub">Obstruction house based on {chart.badhaka.get('modality')} Lagna</div>
        </div>
      </div>
    </div>
    {self._build_footer(4)}
  </section>
"""

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 5: YOGAS, DOSHAS & DIVISIONAL VARGAS
    # ═══════════════════════════════════════════════════════════════════
    def _build_page5_yogas_vargas(self, chart, d10_svg: str) -> str:
        # Formed Yogas
        yogas = chart.yogas
        formed_yogas = yogas.get("formed", [])
        
        y_items = []
        for y in formed_yogas[:10]:
            name = y.get("name", "")
            desc = y.get("description", y.get("connection", ""))
            y_items.append(f"""
          <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 3px solid #b45309; border-radius: 3px; padding: 2px 5px; margin-bottom: 2px;">
            <div style="font-weight: 700; font-size: 7.2pt; color: #0f172a;">{name}</div>
            <div style="font-size:6.8pt; color: #475569;">{desc}</div>
          </div>""")

        # Shodashavarga Grid Summary
        vargas = chart.vargas
        v_keys_a = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20"]
        v_keys_b = ["D24", "D27", "D30", "D40", "D45", "D60"]
        v_bodies = ["Lagna"] + list(PLANETS_9)

        def _varga_rows(keys):
            rows = []
            for p in v_bodies:
                cells = []
                for vk in keys:
                    v_chart = vargas.get(vk, {})
                    p_sign = v_chart.get(p, "—")
                    if isinstance(p_sign, dict):
                        p_sign = p_sign.get("sign", "—")
                    cells.append(f"<td class='center'>{str(p_sign)[:3]}</td>")
                rows.append(f"<tr><td class='bold'>{p}</td>{''.join(cells)}</tr>")
            heads = "".join(f"<th class='center'>{vk}</th>" for vk in keys)
            return heads, "".join(rows)

        v_heads_a, v_rows_a = _varga_rows(v_keys_a)
        v_heads_b, v_rows_b = _varga_rows(v_keys_b)

        # Placidus CSL from Swiss P cusp λ (not equal-bhava, which is Ra/Ke alternate
        # at this lagna degree). Show sign + star so repeated Rahu CSLs are not dummy.
        kp_bits = []
        placidus_cusps = (getattr(chart, "house_cusps", None) or {}).get("cusps") or {}
        for h in range(1, 13):
            csp = placidus_cusps.get(h) or {}
            sign3 = str(csp.get("sign") or "—")[:3]
            deg = csp.get("degree")
            deg_s = f"{float(deg):.1f}°" if isinstance(deg, (int, float)) else ""
            nak = str(csp.get("nakshatra") or "—")[:4]
            star = csp.get("nak_lord") or "—"
            sub = csp.get("sub_lord") or "—"
            kp_bits.append(f"H{h} {sign3} {deg_s} {nak} {star}/{sub}")
        kp_line = " · ".join(kp_bits)

        from ..computations.karakas import KARAKA_NAMES_8
        k8 = chart.karakas_8.get("karakas", {}) if hasattr(chart, "karakas_8") else {}
        k8_line = " · ".join(
            f"{tag}={k8[tag]}" for tag in KARAKA_NAMES_8 if tag in k8
        ) if k8 else "—"

        comb = {}
        try:
            comb = chart.combustion
        except Exception:
            pass
        comb_list = [p for p, v in comb.items() if isinstance(v, dict) and v.get("is_combust")]
        comb_str = ", ".join(comb_list) if comb_list else "None"

        not_formed = yogas.get("not_formed") or []
        nf_names = []
        for y in not_formed:
            if isinstance(y, dict):
                nf_names.append(y.get("name", ""))
            else:
                nf_names.append(str(y))
        nf_s = " · ".join(n for n in nf_names if n) or "—"
        vt = (chart.vargas or {}).get("_vargottama") or {}
        vt_s = ", ".join(p for p, v in vt.items() if v) if isinstance(vt, dict) else "—"

        return f"""
  <section class="a4-page" id="page5">
    <div>
      {self._build_header(chart, "Auspicious Yogas & Divisional Vargas", "Synthesis & Vargas")}

      <div class="two-col-grid">
        <!-- Formed Yogas Column -->
        <div>
          <div class="section-title" style="margin-top:0;">
            <span class="icon-sym">✦</span> Major Yogas Formed ({len(formed_yogas)})
          </div>
          {''.join(y_items)}
        </div>

        <!-- D-10 Dasamsa Chart Card -->
        <div class="chart-card">
          <h3>D-10 Dasamsa (Career Zenith)</h3>
          {d10_svg}
        </div>
      </div>

      <!-- Shodashavarga Sign Placements -->
      <div class="section-title">
        <span class="icon-sym">✦</span> Shodashavarga (D1–D60 — all 16 divisions)
      </div>
      <table class="data-table compact">
        <thead><tr><th>Graha</th>{v_heads_a}</tr></thead>
        <tbody>{v_rows_a}</tbody>
      </table>
      <table class="data-table compact">
        <thead><tr><th>Graha</th>{v_heads_b}</tr></thead>
        <tbody>{v_rows_b}</tbody>
      </table>

      <!-- Verification and Summary Note -->
      <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 5px; padding: 6px 9px; font-size:7.5pt; line-height: 1.4; color: #1e293b; margin-top: 6px;">
        <strong>KP Placidus CSL</strong> (Swiss P cusp λ · star/sub — not equal-bhava): {kp_line}<br>
        Equal-bhava CSL at this lagna degree is the Ra/Ke alternate; that table is on the KP sheet, not here.<br>
        <strong>8-planet Karakas:</strong> {k8_line}<br>
        <strong>Combust:</strong> {comb_str}
        · <strong>Vargottama:</strong> {vt_s}<br>
        <strong>Lakshmi Yoga:</strong> not formed (9L/5L not own-or-exalt in Kendra). 1L+9L in Lagna is Dhana/Raja.<br>
        <strong>Checked not formed:</strong> {nf_s}<br>
        Full packs: <code>*_synthesis.json</code> + <code>*_advanced.json</code>.
      </div>
    </div>
    {self._build_footer(5)}
  </section>
"""

    def save_html(self, chart, output_path: str, chart_style: str = "north", theme: str = "gold") -> str:
        """
        Generate and save the A4 report HTML file to disk.

        Args:
            chart: BirthChart instance
            output_path: Target destination file path
            chart_style: "north" or "south"
            theme: "gold", "navy", or "monochrome"

        Returns:
            Absolute path to the saved HTML file
        """
        parent = os.path.dirname(os.path.abspath(output_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        html = self.generate_html(chart, chart_style=chart_style, theme=theme)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return os.path.abspath(output_path)

    def save_pdf(self, chart, output_path: str, chart_style: str = "north", theme: str = "gold") -> str:
        """Generate the A4 HTML report, print to PDF, and write a synthesis JSON beside it."""
        from .pdf import html_to_pdf
        from .synthesis import save_synthesis_json
        html = self.generate_html(chart, chart_style=chart_style, theme=theme)
        pdf_path = html_to_pdf(html, output_path)
        json_path = pdf_path[:-4] + "_synthesis.json" if pdf_path.lower().endswith(".pdf") else pdf_path + "_synthesis.json"
        save_synthesis_json(chart, json_path)
        from .synthesis import save_advanced_json
        adv_path = (
            pdf_path[:-4] + "_advanced.json"
            if pdf_path.lower().endswith(".pdf")
            else pdf_path + "_advanced.json"
        )
        save_advanced_json(chart, adv_path)
        return pdf_path


def generate_chart_report(chart, output_path: Optional[str] = None, chart_style: str = "north",
                         theme: str = "gold") -> str:
    """Save HTML or PDF (if output_path ends with .pdf). Defaults to HTML."""
    generator = ReportGenerator()
    if output_path is None:
        name_clean = chart.birth_data.get("name", "Kundali").replace(" ", "_")
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        output_path = os.path.join(output_dir, f"{name_clean}_A4_Report.html")
    if output_path.lower().endswith(".pdf"):
        return generator.save_pdf(chart, output_path, chart_style=chart_style, theme=theme)
    return generator.save_html(chart, output_path, chart_style=chart_style, theme=theme)
