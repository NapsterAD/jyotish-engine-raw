"""Raw-calculation A4 pages (11–14) for AI feed. Numbers only."""

from datetime import datetime

from ..core.constants import SIGNS, PLANETS_7, PLANETS_9

_P2 = {
    "Jupiter": "Ju",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
    "Mars": "Ma",
    "Sun": "Su",
    "Moon": "Mo",
    "Mercury": "Me",
    "Venus": "Ve",
    "Lagna": "Lg",
}

# Special-aspect offsets from occupied house (7th is always included).
_ASPECT_RULE = "Ju 5,7,9 · Sa 3,7,10 · Ma 4,8,7 · Ra/Ke 7"


def _split_cols(rows, n):
    """Evenly split HTML <tr> strings across n column tables."""
    if not rows:
        return [""] * n
    q, r = divmod(len(rows), n)
    out = []
    i = 0
    for c in range(n):
        take = q + (1 if c < r else 0)
        out.append("".join(rows[i:i + take]))
        i += take
    return out


def _try(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def build_raw_pages(gen, chart):
    raw = _try(lambda: chart.raw_layers, {}) or {}
    return (
        _page11_sthana_bav_drik(gen, chart, raw),
        _page12_nak_varga(gen, chart, raw),
        _page13_ingress(gen, chart, raw),
        _page14_dasha_trees(gen, chart, raw),
    )


def _page11_sthana_bav_drik(gen, chart, raw):
    sb = chart.shadbala or {}
    sth_rows = []
    for p in PLANETS_7:
        d = ((sb.get(p) or {}).get("components") or {}).get("sthana_detail") or {}
        kd = ((sb.get(p) or {}).get("components") or {}).get("kala_detail") or {}
        pos = chart.positions.get(p) or {}
        sth_rows.append(
            f"<tr><td class='bold'>{p}</td>"
            f"<td class='right'>{d.get('uchcha','—')}</td>"
            f"<td class='right'>{d.get('saptavargaja','—')}</td>"
            f"<td class='right'>{d.get('ojha_yugma','—')}</td>"
            f"<td class='right'>{d.get('kendra','—')}</td>"
            f"<td class='right'>{d.get('drekkana','—')}</td>"
            f"<td class='right'>{kd.get('yuddha','—')}</td>"
            f"<td class='right'>{pos.get('speed','—')}</td>"
            f"<td>{'R' if pos.get('retrograde') else 'D'}</td></tr>"
        )
    bav = (chart.ashtakavarga or {}).get("bav") or {}
    sodhya = (chart.ashtakavarga or {}).get("sodhya") or {}
    bav_rows = []
    head = "".join(f"<th class='center'>{s[:3]}</th>" for s in SIGNS)
    for p in PLANETS_7 + ["Lagna"]:
        row = bav.get(p)
        if not isinstance(row, list):
            continue
        cells = "".join(f"<td class='center'>{int(x)}</td>" for x in row[:12])
        sod = sodhya.get(p) or {}
        red = sod.get("reduced") or []
        red_s = " ".join(str(int(x)) for x in red[:12]) if red else "—"
        bav_rows.append(
            f"<tr><td class='bold'>{p}</td>{cells}"
            f"<td class='right'>{sod.get('sodhya','—')}"
            f"<div style='font-size:6pt;color:#64748b;font-weight:400'>{red_s}</div></td></tr>"
        )
    drik = (raw.get("sthana_speed_drik") or {}).get("drik_house_matrix") or {}
    drik_rows = []
    for p in PLANETS_7:
        row = drik.get(p) or {}
        cells = "".join(f"<td class='center'>{row.get(str(h), 0)}</td>" for h in range(1, 13))
        drik_rows.append(f"<tr><td class='bold'>{p}</td>{cells}</tr>")

    return f"""
  <section class="a4-page" id="page11">
    <div>
      {gen._build_header(chart, "Raw Strength: Sthana / BAV / Drik Pinda", "Numbers only")}
      <div class="section-title" style="margin-top:0;">
        <span class="icon-sym">✦</span> Sthana sub-scores + speed (shashtiamsas, deg/day)
      </div>
      <table class="data-table compact">
        <thead>
          <tr><th>P</th><th class="right">Uccha</th><th class="right">Saptavargaja</th>
              <th class="right">Ojha</th><th class="right">Kendra</th><th class="right">Drekkana</th>
              <th class="right">Yuddha</th><th class="right">Speed</th><th>Mot</th></tr>
        </thead>
        <tbody>{''.join(sth_rows)}</tbody>
      </table>
      <div class="section-title"><span class="icon-sym">✦</span> BAV bindus + Sodhya (reduced bindus under Sodhya)</div>
      <table class="data-table compact">
        <thead><tr><th>P</th>{head}<th class="right">Sodhya</th></tr></thead>
        <tbody>{''.join(bav_rows)}</tbody>
      </table>
      <div class="section-title"><span class="icon-sym">✦</span> Drishti pinda onto houses (virupa)</div>
      <table class="data-table compact">
        <thead><tr><th>P</th>{''.join(f'<th class="center">{h}</th>' for h in range(1,13))}</tr></thead>
        <tbody>{''.join(drik_rows)}</tbody>
      </table>
    </div>
    {gen._build_footer(11)}
  </section>
"""


def _page12_nak_varga(gen, chart, raw):
    nak = raw.get("nakshatra_layers") or {}
    nak_rows = []
    for p in ["Lagna"] + list(PLANETS_9):
        d = nak.get(p) or {}
        lords = d.get("lords") or {}
        star = (lords.get("star") or {}).get("placement") or {}
        sub = (lords.get("sub") or {}).get("placement") or {}
        ssl = (lords.get("ssl") or {}).get("placement") or {}
        nak_rows.append(
            f"<tr><td class='bold'>{p}</td>"
            f"<td>{d.get('nakshatra')} P{d.get('pada')}</td>"
            f"<td class='right'>{d.get('degree_into')}</td>"
            f"<td class='right'>{d.get('elapsed_pct')}%</td>"
            f"<td>{d.get('deity')}</td>"
            f"<td>{d.get('nadi')}</td>"
            f"<td>{(lords.get('star') or {}).get('planet')} "
            f"{star.get('sign')} H{star.get('house')}</td>"
            f"<td>{(lords.get('sub') or {}).get('planet')} "
            f"{sub.get('sign')} H{sub.get('house')}</td>"
            f"<td>{(lords.get('ssl') or {}).get('planet')} "
            f"{ssl.get('sign')} H{ssl.get('house')}</td></tr>"
        )

    vs = raw.get("varga_sphutas") or {}
    vkeys = ["D1", "D9", "D10", "D24", "D27", "D40", "D45", "D60"]
    v_rows = []
    for p in ["Lagna"] + list(PLANETS_7):
        cells = []
        for vk in vkeys:
            b = (vs.get(vk) or {}).get(p) or {}
            if not b:
                cells.append("<td>—</td>")
            else:
                cells.append(
                    f"<td>{str(b.get('sign',''))[:3]} {b.get('degree_in_sign',0):.1f}°</td>"
                )
        v_rows.append(f"<tr><td class='bold'>{p}</td>{''.join(cells)}</tr>")

    bh = raw.get("bhava_raw") or {}
    bh_rows = []
    for h in range(1, 13):
        d = bh.get(str(h)) or {}
        bh_rows.append(
            f"<tr><td class='center bold'>{h}</td><td>{d.get('sign')}</td>"
            f"<td>{d.get('lord')}</td><td>{d.get('karaka')} {d.get('karaka_shadbala_rupas')}</td>"
            f"<td>{', '.join(d.get('graha_drishti') or []) or '—'}</td>"
            f"<td>{', '.join(d.get('rashi_drishti') or []) or '—'}</td></tr>"
        )

    trop = (raw.get("tropical_sidereal") or {}).get("bodies") or {}
    trop_s = " · ".join(
        f"{p} sid {d.get('sidereal')} trop {d.get('tropical')}"
        for p, d in trop.items() if p in ("Lagna", "Sun", "Moon")
    )

    return f"""
  <section class="a4-page" id="page12">
    <div>
      {gen._build_header(chart, "Nakshatra Chains & Varga Sphutas", "Degrees into nak / D24 D60")}
      <div style="font-size:7.5pt;margin-bottom:4px;">{trop_s} · JD {(raw.get('tropical_sidereal') or {}).get('jd')} · aya {(raw.get('tropical_sidereal') or {}).get('ayanamsha')}</div>
      <div class="section-title" style="margin-top:0;"><span class="icon-sym">✦</span> Nakshatra depth + star/sub/SSL placement</div>
      <table class="data-table compact">
        <thead>
          <tr><th>P</th><th>Nak P</th><th class="right">Into°</th><th class="right">%</th>
              <th>Deity</th><th>Nadi</th><th>Star lord</th><th>Sub lord</th><th>SSL</th></tr>
        </thead>
        <tbody>{''.join(nak_rows)}</tbody>
      </table>
      <div class="section-title"><span class="icon-sym">✦</span> Varga sphuta (sign + deg-in-varga)</div>
      <table class="data-table compact">
        <thead><tr><th>P</th>{''.join(f'<th>{k}</th>' for k in vkeys)}</tr></thead>
        <tbody>{''.join(v_rows)}</tbody>
      </table>
      <div class="section-title"><span class="icon-sym">✦</span> Bhava karaka + drishti lists</div>
      <table class="data-table compact">
        <thead><tr><th>H</th><th>Sign</th><th>Lord</th><th>Karaka SB</th><th>Graha drishti</th><th>Rashi drishti</th></tr></thead>
        <tbody>{''.join(bh_rows)}</tbody>
      </table>
    </div>
    {gen._build_footer(12)}
  </section>
"""


def _page13_ingress(gen, chart, raw):
    cal = raw.get("ingress_2025_2043") or {}
    planets = cal.get("planets") or {}
    rows = []
    natal_occ = []
    seen_sign = set()
    for name in ("Jupiter", "Saturn", "Rahu", "Ketu", "Mars"):
        abbr = _P2.get(name, name[:2])
        for ev in (planets.get(name) or []):
            if not isinstance(ev, dict):
                continue
            sign = ev.get("sign") or "—"
            h = ev.get("natal_house") or "—"
            sign3 = str(sign)[:3]
            cj = ",".join(_P2.get(x, x[:2]) for x in (ev.get("conjunct_natal") or []))
            rows.append(
                f"<tr><td class='bold'>{abbr}</td>"
                f"<td>{sign3}</td><td class='center'>{h}</td>"
                f"<td class='date-cell'>{gen._fmt_date_short(ev.get('entry'))}</td>"
                f"<td class='date-cell'>{gen._fmt_date_short(ev.get('exit'))}</td>"
                f"<td>{cj or '—'}</td></tr>"
            )
            if sign not in seen_sign:
                seen_sign.add(sign)
                occ = ev.get("conjunct_natal") or []
                if occ:
                    natal_occ.append(
                        f"{sign3} {','.join(_P2.get(x, x[:2]) for x in occ)}"
                    )
    n = len(rows)
    ncols = 4 if n > 64 else 3
    cols = _split_cols(rows, ncols)
    grid_cls = "four-col-grid" if ncols == 4 else "three-col-grid"
    empty = "<tr><td colspan='6'>—</td></tr>"
    head = (
        "<thead><tr><th>P</th><th>Sign</th><th>H</th>"
        "<th>In</th><th>Out</th><th>cj</th></tr></thead>"
    )
    tables = "".join(
        f"<table class='data-table compact'>{head}<tbody>{c or empty}</tbody></table>"
        for c in cols
    )

    over = (raw.get("transit_over_natal") or {}).get("hits") or {}
    over_bits = []
    for t, targets in over.items():
        ta = _P2.get(t, (t or "")[:2])
        for body, wins in (targets or {}).items():
            if not wins:
                continue
            w = wins[0]
            nb = _P2.get(body, (body or "")[:2])
            over_bits.append(
                f"{ta}→{nb} {gen._fmt_date_short(w.get('start'))}"
                f"–{gen._fmt_date_short(w.get('end'))} {w.get('min_orb')}"
            )

    return f"""
  <section class="a4-page" id="page13">
    <div>
      {gen._build_header(chart, "Ingress Calendar (raw)", f"Ju Sa Ra Ke Mars 2025–2043 — {n} sign changes")}
      <div class="{grid_cls}">
        {tables}
      </div>
      <div style="font-size:6.4pt;line-height:1.25;margin-top:3px;">
        <strong>Aspects from occupied house:</strong> {_ASPECT_RULE}
        · <strong>Natal occupants:</strong> {' · '.join(natal_occ) or '—'}
        · cj column = natal grahas in that sign (same facts as aspects/conjunctions on each row)
      </div>
      <div class="section-title"><span class="icon-sym">✦</span> Transit over natal (orb 1.5°, first windows)</div>
      <div style="font-size:6.4pt;line-height:1.25;">{' · '.join(over_bits) or '—'}</div>
    </div>
    {gen._build_footer(13)}
  </section>
"""


def _page14_dasha_trees(gen, chart, raw):
    tree = raw.get("vimshottari_pd_tree") or {}
    md = tree.get("md") or "—"
    md2 = _P2.get(md, (md or "—")[:2])
    pd_all = []
    for ad in (tree.get("antardashas") or []):
        ad_lord = ad.get("ad") or ""
        ad2 = _P2.get(ad_lord, ad_lord[:2] if ad_lord else "—")
        for pd in (ad.get("pd") or []):
            lord = pd.get("lord") or ""
            p2 = _P2.get(lord, lord[:2] if lord else "—")
            pd_all.append(
                f"<tr><td>{md2}-{ad2}-{p2}</td>"
                f"<td class='date-cell'>{gen._fmt_date_short(pd.get('start'))}</td>"
                f"<td class='date-cell'>{gen._fmt_date_short(pd.get('end'))}</td></tr>"
            )
    n = len(pd_all)
    ncols = 4 if n > 72 else 3
    cols = _split_cols(pd_all, ncols)
    grid_cls = "four-col-grid" if ncols == 4 else "three-col-grid"
    empty = "<tr><td colspan='3'>—</td></tr>"
    pd_head = "<thead><tr><th>PD</th><th>Start</th><th>End</th></tr></thead>"
    pd_tables = "".join(
        f"<table class='data-table compact'>{pd_head}<tbody>{c or empty}</tbody></table>"
        for c in cols
    )

    yog = raw.get("yogini_pd_tree") or []
    yb = yog[0] if yog else {}
    y_ad = []
    for ad in (yb.get("antardashas") or []):
        y_ad.append(
            f"<tr><td>{yb.get('yogini')}-{ad.get('yogini')}</td>"
            f"<td class='date-cell'>{gen._fmt_date_short(ad.get('start'))}</td>"
            f"<td class='date-cell'>{gen._fmt_date_short(ad.get('end'))}</td></tr>"
        )
    y_n = len(y_ad)
    y_cols = _split_cols(y_ad, 2) if y_n > 6 else ["".join(y_ad), ""]
    y_empty = "<tr><td colspan='3'>—</td></tr>"
    y_head = "<thead><tr><th>Yogini AD</th><th>Start</th><th>End</th></tr></thead>"

    d10 = {}
    try:
        from ..computations.extra_lagnas import calc_d10_facts
        d10 = calc_d10_facts(chart)
    except Exception:
        d10 = {}
    bodies = d10.get("bodies") or {}
    d10_s = " · ".join(
        f"{_P2.get(p, p[:2])} {str(b.get('sign') or '')[:3]} H{b.get('house_from_d10_lagna')}"
        for p, b in bodies.items()
    )

    return f"""
  <section class="a4-page" id="page14">
    <div>
      {gen._build_header(chart, "Vimshottari PD tree (current MD) + Yogini AD", "Raw date windows")}
      <div class="section-title" style="margin-top:0;">
        <span class="icon-sym">✦</span> {md} MD — every AD → PD window ({n})
      </div>
      <div class="{grid_cls}">
        {pd_tables}
      </div>
      <div class="section-title"><span class="icon-sym">✦</span> Yogini {yb.get('yogini')} ({yb.get('planet')}) — all antardashas</div>
      <div class="two-col-grid">
        <table class="data-table compact">{y_head}<tbody>{y_cols[0] or y_empty}</tbody></table>
        <table class="data-table compact">{y_head}<tbody>{y_cols[1] or y_empty}</tbody></table>
      </div>
      <div style="font-size:6.5pt;margin-top:3px;line-height:1.25;">
        <strong>D10 facts:</strong> Lagna {d10.get('d10_lagna')} · 10th-from {d10.get('tenth_from_d10_lagna')}
        · MD {d10.get('current_md_lord')} in D10 {d10.get('current_md_in_d10')}
        · {d10_s}
      </div>
    </div>
    {gen._build_footer(14)}
  </section>
"""
