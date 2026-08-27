"""Extra A4 pages: KP, rashi dashas, transits/time-pack, Lal Kitab/Nadi, sensitive points."""

from datetime import datetime

from ..core.constants import SIGNS, PLANETS_7, PLANETS_9


def _s(v, default="—"):
    if v is None or v == "":
        return default
    return str(v)


def _try(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def build_extra_pages(gen, chart):
    """Pages 6–10 HTML fragments."""
    return (
        _page6_kp(gen, chart),
        _page7_rasi_dashas(gen, chart),
        _page8_transits(gen, chart),
        _page9_lal_nadi_marriage(gen, chart),
        _page10_sensitive(gen, chart),
    )


def _page6_kp(gen, chart):
    now = datetime.now().strftime("%Y-%m-%d")
    rp = _try(lambda: chart.kp_ruling_planets(), {}) or {}
    rp_list = rp.get("list") or rp.get("planets") or []
    if isinstance(rp_list, dict):
        rp_list = list(rp_list.values())

    abcd_rows = []
    for h in range(1, 13):
        b = _try(lambda h=h: chart.kp_significators(h, "placidus"), {}) or {}
        a = ", ".join(b.get("A") or []) or "—"
        bb = ", ".join(b.get("B") or []) or "—"
        c = ", ".join(b.get("C") or []) or "—"
        d = ", ".join(b.get("D") or []) or "—"
        ag = ", ".join(b.get("agents") or []) or "—"
        csl = b.get("cusp_sub_lord", "—")
        abcd_rows.append(
            f"<tr><td class='center bold'>{h}</td><td>{csl}</td>"
            f"<td>{a}</td><td>{bb}</td><td>{c}</td><td>{d}</td><td>{ag}</td></tr>"
        )

    fr_m = _try(lambda: chart.kp_fruitful([2, 7, 11], [1, 6, 10]), {}) or {}
    fr_c = _try(lambda: chart.kp_fruitful([2, 6, 10, 11], [5, 8, 12]), {}) or {}
    fr_w = _try(lambda: chart.kp_fruitful([2, 11], [8, 12]), {}) or {}

    def _fr_line(block, label):
        sigs = ", ".join(block.get("significators") or []) or "—"
        deny = ", ".join(block.get("denying") or []) or "—"
        csl = block.get("csl") or {}
        bits = []
        for h, info in csl.items():
            if isinstance(info, dict):
                mark = "Y" if info.get("fruitful") else "N"
                bits.append(f"H{h} {info.get('csl','?')}={mark}")
        return (
            f"<tr><td class='bold'>{label}</td><td>{sigs}</td>"
            f"<td>{deny}</td><td>{' · '.join(bits) or '—'}</td></tr>"
        )

    adv = _try(lambda: chart.kp_advanced, {}) or {}
    ssl = adv.get("ssl_tables") or {}
    bodies = ssl.get("bodies") or {}
    ssl_rows = []
    for p in ["Lagna"] + list(PLANETS_9):
        ch = bodies.get(p) or {}
        ssl_rows.append(
            f"<tr><td class='bold'>{p}</td><td>{_s(ch.get('sign_lord'))}</td>"
            f"<td>{_s(ch.get('star_lord'))}</td><td>{_s(ch.get('sub_lord'))}</td>"
            f"<td>{_s(ch.get('sub_sub_lord'))}</td><td>{_s(ch.get('sssl_lord'))}</td>"
            f"<td class='center'>{_s(ch.get('kp_249'))}</td></tr>"
        )

    mx = (adv.get("significator_matrix_placidus") or {}).get("grid") or {}
    fold_rows = []
    for p in PLANETS_9:
        cells = []
        row = mx.get(p) or {}
        for h in range(1, 13):
            cell = row.get(str(h)) or {}
            n = cell.get("fold", 0)
            cells.append(f"<td class='center'>{n if n else '·'}</td>")
        fold_rows.append(f"<tr><td class='bold'>{p}</td>{''.join(cells)}</tr>")

    return f"""
  <section class="a4-page" id="page6">
    <div>
      {gen._build_header(chart, "KP Significators & SSL Chains", "Krishnamurti Paddhati")}
      <div class="section-title" style="margin-top:0;">
        <span class="icon-sym">✦</span> Ruling Planets ({now})
        <span class="sub">{', '.join(str(x) for x in rp_list) or '—'}</span>
      </div>
      <div class="section-title">
        <span class="icon-sym">✦</span> ABCD Significators (Placidus)
      </div>
      <table class="data-table compact">
        <thead>
          <tr><th>H</th><th>CSL</th><th>A star-of-occ</th><th>B occupant</th>
              <th>C star-of-lord</th><th>D lord</th><th>Agents</th></tr>
        </thead>
        <tbody>{''.join(abcd_rows)}</tbody>
      </table>
      <div class="section-title">
        <span class="icon-sym">✦</span> Fruitful Significators
      </div>
      <table class="data-table compact">
        <thead><tr><th>Event houses</th><th>Significators</th><th>Denying</th><th>CSL fruitful</th></tr></thead>
        <tbody>
          {_fr_line(fr_m, "Marriage 2-7-11 deny 1-6-10")}
          {_fr_line(fr_c, "Career 2-6-10-11 deny 5-8-12")}
          {_fr_line(fr_w, "Wealth 2-11 deny 8-12")}
        </tbody>
      </table>
      <div class="two-col-grid">
        <div>
          <div class="section-title"><span class="icon-sym">✦</span> Body SSL / SSSL</div>
          <table class="data-table compact">
            <thead><tr><th>Body</th><th>Sign</th><th>Star</th><th>Sub</th><th>SSL</th><th>SSSL</th><th>249</th></tr></thead>
            <tbody>{''.join(ssl_rows)}</tbody>
          </table>
        </div>
        <div>
          <div class="section-title"><span class="icon-sym">✦</span> Fold count 9×12 (Placidus)</div>
          <table class="data-table compact">
            <thead><tr><th>P</th>{''.join(f'<th class="center">{h}</th>' for h in range(1,13))}</tr></thead>
            <tbody>{''.join(fold_rows)}</tbody>
          </table>
        </div>
      </div>
    </div>
    {gen._build_footer(6)}
  </section>
"""


def _page7_rasi_dashas(gen, chart):
    ds = _try(lambda: chart.dasha_systems, {}) or {}
    now = datetime.now().strftime("%Y-%m-%d")

    def current_and_next(block, n=4):
        periods = []
        if isinstance(block, dict):
            periods = block.get("periods") or []
        elif isinstance(block, list):
            periods = block
        rows = []
        shown = 0
        started = False
        for p in periods:
            if not isinstance(p, dict):
                continue
            end = p.get("end_date") or ""
            start = p.get("start_date") or ""
            if end and end < now and not started:
                continue
            started = True
            lord = p.get("lord") or p.get("yogini") or p.get("sign") or ""
            gati = p.get("gati") or ""
            extra = f" {gati}" if gati and gati != "normal" else ""
            rows.append(
                f"<tr><td class='bold'>{lord}{extra}</td>"
                f"<td class='date-cell'>{gen._fmt_date(start)}</td>"
                f"<td class='date-cell'>{gen._fmt_date(end)}</td>"
                f"<td class='right'>{p.get('duration_years') or p.get('years') or '—'}</td></tr>"
            )
            shown += 1
            if shown >= n:
                break
        return rows or ["<tr><td colspan='4'>—</td></tr>"]

    systems = [
        ("chara", "Chara"),
        ("narayana", "Narayana"),
        ("mandook", "Mandook"),
        ("sudasa", "Sudasa"),
        ("ashtottari", "Ashtottari"),
        ("kalachakra", "Kalachakra"),
        ("drigdasa", "Drigdasa"),
        ("lagna_kendradi", "Lagna Kendradi"),
        ("shoola", "Shoola"),
        ("niryana_shoola", "Niryana Shoola"),
        ("moola", "Moola"),
        ("shashti_hayani", "Shashti-Hayani"),
        ("tribhagi", "Tribhagi"),
    ]
    sys_rows = []
    for key, label in systems:
        block = ds.get(key) or {}
        meta_bits = []
        if isinstance(block, dict):
            for k in ("start_sign", "deha", "jiva", "group", "savya"):
                if k in block and block[k] not in (None, "", False):
                    meta_bits.append(f"{k}={block[k]}")
        plist = []
        src = block.get("periods") if isinstance(block, dict) else block
        if isinstance(src, list):
            now = datetime.now().strftime("%Y-%m-%d")
            started = False
            for p in src:
                if not isinstance(p, dict):
                    continue
                end = p.get("end_date") or ""
                if end and end < now and not started:
                    continue
                started = True
                lord = p.get("lord") or p.get("yogini") or p.get("sign") or ""
                plist.append(
                    f"{lord} {gen._fmt_date(p.get('start_date'))}–{gen._fmt_date(p.get('end_date'))}"
                )
                if len(plist) >= 2:
                    break
        sys_rows.append(
            f"<tr><td class='bold'>{label}</td>"
            f"<td style='font-size:7pt'>{' · '.join(meta_bits) or '—'}</td>"
            f"<td>{plist[0] if plist else '—'}</td>"
            f"<td>{plist[1] if len(plist) > 1 else '—'}</td></tr>"
        )

    # Current MD antardashas
    ad_rows = []
    curr = _try(lambda: chart.get_current_dasha(now, levels=5), {}) or {}
    md_lord = ""
    if isinstance(curr.get("MD"), dict):
        md_lord = curr["MD"].get("lord", "")
    for md in chart.dashas or []:
        if md.get("lord") == md_lord:
            for ad in (md.get("sub_periods") or [])[:12]:
                ad_rows.append(
                    f"<tr><td class='bold'>{ad.get('lord')}</td>"
                    f"<td class='date-cell'>{gen._fmt_date(ad.get('start_date'))}</td>"
                    f"<td class='date-cell'>{gen._fmt_date(ad.get('end_date'))}</td></tr>"
                )
            break

    str_rows = []
    for p in PLANETS_7:
        st = _try(lambda p=p: chart.dasha_lord_strength(p), {}) or {}
        notes = ", ".join(st.get("notes") or []) or "—"
        str_rows.append(
            f"<tr><td class='bold'>{p}</td><td>{st.get('dignity','—')}</td>"
            f"<td>{st.get('flag','—')}</td><td>{notes}</td></tr>"
        )

    return f"""
  <section class="a4-page" id="page7">
    <div>
      {gen._build_header(chart, "Rashi Dashas & Lord Strength", "Jaimini / Nakshatra Systems")}
      <div class="section-title" style="margin-top:0;">
        <span class="icon-sym">✦</span> Current Vimshottari {md_lord or '—'} AD tree
      </div>
      <table class="data-table compact">
        <thead><tr><th>Antardasha</th><th>Start</th><th>End</th></tr></thead>
        <tbody>{''.join(ad_rows) or '<tr><td colspan="3">—</td></tr>'}</tbody>
      </table>
      <div class="section-title"><span class="icon-sym">✦</span> Other dasha systems (current + next)</div>
      <table class="data-table compact">
        <thead><tr><th>System</th><th>Meta</th><th>Current</th><th>Next</th></tr></thead>
        <tbody>{''.join(sys_rows)}</tbody>
      </table>
      <div class="section-title"><span class="icon-sym">✦</span> Dasha-lord strength flags</div>
      <table class="data-table compact">
        <thead><tr><th>Graha</th><th>Dignity</th><th>Flag</th><th>Notes</th></tr></thead>
        <tbody>{''.join(str_rows)}</tbody>
      </table>
    </div>
    {gen._build_footer(7)}
  </section>
"""


def _page8_transits(gen, chart):
    now = datetime.now().strftime("%Y-%m-%d")
    tr = _try(lambda: chart.transits_for(now), {}) or {}
    go = tr.get("gochara") or {}
    t2n = tr.get("transit_to_natal") or {}
    dt = tr.get("double_transit") or {}
    bb = tr.get("bb_transit") or []

    go_rows = []
    for p in PLANETS_9:
        g = go.get(p) or {}
        t = t2n.get(p) or {}
        go_rows.append(
            f"<tr><td class='bold'>{p}</td>"
            f"<td>{t.get('transit_sign') or g.get('sign') or '—'}</td>"
            f"<td class='right'>{t.get('transit_degree', '—')}</td>"
            f"<td class='center'>{t.get('natal_house') or g.get('house_from_moon') or '—'}</td>"
            f"<td>{', '.join(t.get('conjuncts_natal') or []) or '—'}</td>"
            f"<td>{g.get('net_effect') or g.get('effect') or '—'}</td>"
            f"<td class='center'>{t.get('sav_score') if t.get('sav_score') is not None else '—'}</td>"
            f"</tr>"
        )

    tp = _try(lambda: chart.get_time_pack(from_date=now), {}) or {}

    vrows = []
    for v in (tp.get("varshaphala") or [])[:5]:
        if not isinstance(v, dict) or v.get("error"):
            continue
        mun = v.get("muntha") or {}
        vs = v.get("varshesha") or {}
        if isinstance(vs, dict):
            vs = vs.get("year_lord") or vs.get("varshesha") or vs.get("lord") or "—"
        mun_s = "—"
        if isinstance(mun, dict):
            mun_s = f"{mun.get('muntha_sign', '—')} H{mun.get('house_from_lagna', '—')}"
        vrows.append(
            f"<tr><td class='bold'>{v.get('year')}</td><td>{v.get('varsha_lagna')}</td>"
            f"<td>{mun_s}</td><td>{vs}</td>"
            f"<td class='date-cell'>{gen._fmt_date(v.get('solar_return_date'))}</td></tr>"
        )

    ecl_rows = []
    for e in tp.get("eclipses") or []:
        hits = e.get("natal_hits_orb5") or []
        if not hits:
            continue
        hit_s = ", ".join(f"{h.get('natal')} {h.get('orb')}" for h in hits[:4])
        ecl_rows.append(
            f"<tr><td>{e.get('kind')}</td><td class='date-cell'>{gen._fmt_date(e.get('date'))}</td><td>{hit_s}</td></tr>"
        )

    tara_bad = []
    for yr in (tp.get("tara_bala_years") or {}).get("years") or []:
        damaged = [p for p, d in (yr.get("planets") or {}).items()
                   if isinstance(d, dict) and d.get("damage")]
        if damaged:
            tara_bad.append(f"{yr.get('date','')[:4]}: {', '.join(damaged)}")

    bbw = (tp.get("bhrigu_bindu_windows") or {}).get("windows") or {}
    bb_bits = []
    for body, wins in bbw.items():
        if wins:
            w0 = wins[0]
            bb_bits.append(f"{body} {w0.get('start')} (orb {w0.get('min_orb')})")

    ing_cal = ((_try(lambda: chart.raw_layers, {}) or {}).get("ingress_2025_2043") or {}).get("planets") or {}
    ing_bits = []
    for planet in ("Jupiter", "Saturn"):
        for row in (ing_cal.get(planet) or [])[:4]:
            if not isinstance(row, dict):
                continue
            entry = row.get("entry") or row.get("date") or ""
            if entry and entry < now:
                continue
            ing_bits.append(f"{entry} →{row.get('sign')}")
            if len(ing_bits) >= 8:
                break

    dt_h = ", ".join(str(h) for h in (dt.get("double_transit_houses") or [])) or "—"

    return f"""
  <section class="a4-page" id="page8">
    <div>
      {gen._build_header(chart, "Transits, Varshaphala & Time Pack", "Gochara Calendars")}
      <div class="section-title" style="margin-top:0;">
        <span class="icon-sym">✦</span> Transit overlay {now}
        <span class="sub">Double transit houses: {dt_h}</span>
      </div>
      <table class="data-table compact">
        <thead>
          <tr><th>Graha</th><th>Sign</th><th class="right">Deg</th><th class="center">Natal H</th>
              <th>Conjunct natal</th><th>Gochara</th><th class="center">SAV</th></tr>
        </thead>
        <tbody>{''.join(go_rows)}</tbody>
      </table>
      <div class="two-col-grid">
        <div>
          <div class="section-title"><span class="icon-sym">✦</span> Varshaphala 5 years</div>
          <table class="data-table compact">
            <thead><tr><th>Year</th><th>V-Lagna</th><th>Muntha</th><th>Varshesha</th><th>SR date</th></tr></thead>
            <tbody>{''.join(vrows) or '<tr><td colspan="5">—</td></tr>'}</tbody>
          </table>
        </div>
        <div>
          <div class="section-title"><span class="icon-sym">✦</span> Eclipses hitting natal (5°)</div>
          <table class="data-table compact">
            <thead><tr><th>Kind</th><th>Date</th><th>Natal hits</th></tr></thead>
            <tbody>{''.join(ecl_rows[:10]) or '<tr><td colspan="3">None within 5°</td></tr>'}</tbody>
          </table>
        </div>
      </div>
      <div style="font-size:7.5pt;line-height:1.45;margin-top:6px;color:#1e293b;">
        <strong>Jupiter/Saturn ingresses:</strong> {(' · '.join(ing_bits)) or '—'}<br>
        <strong>Tara damage years (Sa/Ju/Ra/Ke):</strong> {(' · '.join(tara_bad[:8])) or 'none'}<br>
        <strong>Next BB windows:</strong> {(' · '.join(bb_bits[:6])) or '—'}<br>
        <strong>BB now:</strong> {(', '.join(str(x.get('planet')) for x in bb) if bb else 'no planet on BB')}
      </div>
    </div>
    {gen._build_footer(8)}
  </section>
"""


def _page9_lal_nadi_marriage(gen, chart):
    lk = _try(lambda: chart.lal_kitab, {}) or {}
    nadi = _try(lambda: chart.nadi, {}) or {}
    mt = _try(lambda: chart.marriage_timing(), {}) or {}

    sleep = ", ".join(f"H{h}" for h in (lk.get("sleeping_houses") or [])) or "none"
    masnui = lk.get("masnui_active") or {}
    mas_s = ", ".join(
        f"{k}={'/'.join('+'.join(p) for p in v)}" for k, v in masnui.items()
    ) or "none"
    rin = lk.get("pitru_rin") or {}
    rin_s = ", ".join(rin.keys()) or "none"

    pakka_rows = []
    pg = lk.get("pakka_ghar") or {}
    for h in range(1, 13):
        info = pg.get(h) or pg.get(str(h)) or {}
        occ = chart.get_planets_in_house(h, "rashi")
        pakka_rows.append(
            f"<tr><td class='center bold'>{h}</td>"
            f"<td>{', '.join(info.get('lords') or [])}</td>"
            f"<td>{', '.join(occ) or '—'}</td>"
            f"<td>{', '.join(info.get('exalted') or []) or '—'}</td>"
            f"<td>{', '.join(info.get('debilitated') or []) or '—'}</td></tr>"
        )

    nadi_rows = []
    planets = nadi.get("planets") or {}
    for p in PLANETS_9:
        d = planets.get(p) or {}
        links = d.get("links") or []
        top = ", ".join(
            f"{x['planet']} {x['kind']} {x['weight']}"
            for x in sorted(links, key=lambda z: -z.get("weight", 0))[:4]
        )
        nadi_rows.append(
            f"<tr><td class='bold'>{p}</td><td>{d.get('sign')}</td>"
            f"<td>{d.get('direction')}</td>"
            f"<td>{', '.join(d.get('acts_from_signs') or [])}</td>"
            f"<td>{top or '—'}</td></tr>"
        )

    dasha = mt.get("dasha") or {}
    hits = ", ".join(dasha.get("hits") or []) or "none"

    return f"""
  <section class="a4-page" id="page9">
    <div>
      {gen._build_header(chart, "Lal Kitab, Nadi & Marriage Timing", "Alternate Systems")}
      <div class="section-title" style="margin-top:0;">
        <span class="icon-sym">✦</span> Lal Kitab
        <span class="sub">Sleeping: {sleep} · Andha Teva: {lk.get('andha_teva')} · Rin: {rin_s} · Masnui: {mas_s}</span>
      </div>
      <table class="data-table compact">
        <thead><tr><th>H</th><th>Pakka lords</th><th>Occupants</th><th>Exalted here</th><th>Debilitated here</th></tr></thead>
        <tbody>{''.join(pakka_rows)}</tbody>
      </table>
      <div class="section-title"><span class="icon-sym">✦</span> Bhrigu Nandi Nadi links</div>
      <table class="data-table compact">
        <thead><tr><th>Graha</th><th>Sign</th><th>Dir</th><th>Acts from</th><th>Top links</th></tr></thead>
        <tbody>{''.join(nadi_rows)}</tbody>
      </table>
      <div class="section-title"><span class="icon-sym">✦</span> Marriage significator convergence</div>
      <div style="font-size:7.5pt;line-height:1.45;">
        Significators: <strong>{', '.join(mt.get('significators') or []) or '—'}</strong><br>
        Current MD/AD/PD: {dasha.get('md')} / {dasha.get('ad')} / {dasha.get('pd')}
        · Hits: <strong>{hits}</strong> · Supports: {mt.get('dasha_supports')}<br>
        UL lord: {mt.get('ul_lord')} · DK: {mt.get('darakaraka')}
        · D9 7L in dusthana: {mt.get('navamsa_7l_dusthana')}
      </div>
    </div>
    {gen._build_footer(9)}
  </section>
"""


def _page10_sensitive(gen, chart):
    push = _try(lambda: chart.pushkara, {}) or {}
    n64 = _try(lambda: chart.sensitive.get("navamsa_64"), {}) or {}
    d22 = _try(lambda: chart.sensitive.get("drekkana_22"), {}) or {}
    tara = _try(lambda: chart.nava_tara, {}) or {}
    ayu = _try(lambda: chart.ayurdaya, {}) or {}
    gh = _try(lambda: chart.grahan, {}) or {}
    kak = _try(lambda: chart.kakshyas, {}) or {}
    jdri = _try(lambda: chart.jaimini_drishti, {}) or {}
    fn = _try(lambda: chart.functional_nature, {}) or {}
    vt = _try(lambda: chart.vargas.get("_vargottama"), {}) or {}

    push_rows = []
    for p in ["Lagna"] + list(PLANETS_9):
        d = push.get(p) or {}
        flags = []
        if d.get("pushkara_navamsa"):
            flags.append("PN")
        if d.get("pushkara_bhaga"):
            flags.append("PB")
        if d.get("vargottama"):
            flags.append("VG")
        k = kak.get(p) or {}
        push_rows.append(
            f"<tr><td class='bold'>{p}</td><td>{' '.join(flags) or '—'}</td>"
            f"<td class='center'>K{k.get('kakshya_num','—')}</td>"
            f"<td>{k.get('kakshya_lord','—')}</td></tr>"
        )

    vt_list = []
    if isinstance(vt, dict):
        vt_list = [p for p, v in vt.items() if v]
    elif isinstance(vt, list):
        vt_list = vt

    fn_rows = []
    for group in ("benefic", "malefic", "neutral"):
        items = fn.get(group) or []
        bits = []
        for it in items:
            if isinstance(it, (list, tuple)) and it:
                bits.append(f"{it[0]} ({it[-1] if len(it)>1 else ''})")
            else:
                bits.append(str(it))
        fn_rows.append(f"<tr><td class='bold'>{group}</td><td>{', '.join(bits) or '—'}</td></tr>")

    jd_rows = []
    for p in ["Lagna"] + list(PLANETS_7):
        d = (jdri.get("planets") or {}).get(p) or {}
        jd_rows.append(
            f"<tr><td class='bold'>{p}</td><td>{d.get('sign')}</td>"
            f"<td>{', '.join(d.get('aspected_signs') or [])}</td>"
            f"<td>{', '.join(d.get('aspected_planets') or []) or '—'}</td></tr>"
        )

    sens = tara.get("sensitive") or {}
    ages = tara.get("activation_ages") or {}
    m64 = n64.get("from_moon") or {}
    l64 = n64.get("from_lagna") or {}

    extra = _try(lambda: chart.extra_points, {}) or {}
    indu = extra.get("indu_lagna") or {}
    tl = extra.get("tithi_lagna") or {}
    vl = extra.get("viparita_lagna") or {}
    ml = extra.get("mrityu_lagna") or {}
    pp = _try(lambda: chart.pranapada, {}) or {}
    bphs_pp = pp.get("bphs") if isinstance(pp, dict) else {}
    para_pp = pp.get("parashara") if isinstance(pp, dict) else {}
    if not isinstance(bphs_pp, dict):
        bphs_pp = {}
    if not isinstance(para_pp, dict):
        para_pp = {}
    sahams = _try(lambda: chart.special_points.get("sahams"), {}) or {}
    saham_bits = []
    for name, block in (sahams.items() if isinstance(sahams, dict) else []):
        if isinstance(block, dict):
            saham_bits.append(f"{name} {block.get('sign')} {block.get('degree_in_sign', 0):.1f}°")

    nq = extra.get("nakshatra_qualities") or {}
    nq_rows = []
    for p in ["Lagna"] + list(PLANETS_9):
        d = nq.get(p) or {}
        nq_rows.append(
            f"<tr><td class='bold'>{p}</td><td>{d.get('gana')}</td><td>{d.get('nadi')}</td>"
            f"<td>{d.get('yoni')}</td><td>{d.get('rajju')}</td><td>{d.get('tatva')}</td></tr>"
        )

    ga = _try(lambda: chart.graha_arudhas, {}) or {}
    ga_bits = [f"{p} {d.get('sign')} H{d.get('house_from_lagna')}"
               for p, d in ga.items() if isinstance(d, dict)]

    return f"""
  <section class="a4-page" id="page10">
    <div>
      {gen._build_header(chart, "Sensitive Points & Classifications", "Crisis / Longevity / Qualities")}
      <div class="three-col-grid">
        <div class="stat-tile">
          <div class="st-label">Ayurdaya</div>
          <div class="st-value" style="font-size:10pt;">{ayu.get('verdict','—')}</div>
          <div class="st-sub">{ayu.get('age_range')} · L/8L {ayu.get('pair1_lagna_8l')} · 1L/MoonL {ayu.get('pair2_1l_moonlord')}</div>
        </div>
        <div class="stat-tile">
          <div class="st-label">Grahan natal</div>
          <div class="st-value" style="font-size:9pt;">Sun {gh.get('sun_eclipsed')} / Moon {gh.get('moon_eclipsed')}</div>
          <div class="st-sub">Full {gh.get('full_moon_eclipse')} · New {gh.get('new_moon_eclipse')}</div>
        </div>
        <div class="stat-tile">
          <div class="st-label">Vargottama</div>
          <div class="st-value" style="font-size:9pt;">{', '.join(vt_list) or 'none'}</div>
          <div class="st-sub">Same sign D1=D9</div>
        </div>
      </div>
      <div style="font-size:7.5pt;line-height:1.45;margin:6px 0;color:#1e293b;">
        <strong>64th Navamsa</strong> Moon: {m64.get('sign')} {m64.get('degree_in_sign')}° ({m64.get('lord')})
        · Lagna: {l64.get('sign')} {l64.get('degree_in_sign')}° ({l64.get('lord')})
        · <strong>22nd Drekkana</strong> {d22.get('sign')} Kharadhipati {d22.get('kharadhipati')}<br>
        <strong>Nava-Tara</strong> Janma {tara.get('janma_nakshatra')} · Karma {sens.get('Karma')}
        · Vainashika {sens.get('Vainashika')} · ages {ages.get('primary')}/{ages.get('secondary')}<br>
        <strong>Indu</strong> {indu.get('sign')} H{indu.get('house_from_lagna')}
        · <strong>Tithi Lagna</strong> {tl.get('sign')}
        · <strong>Viparita</strong> {vl.get('sign')}
        · <strong>Mrityu 8H</strong> {(ml.get('eighth_cusp') or {}).get('sign')}<br>
        <strong>Pranapada</strong> BPHS {bphs_pp.get('sign')} {bphs_pp.get('degree_in_sign')}° / Parashara {para_pp.get('sign')} {para_pp.get('degree_in_sign')}°
        · <strong>Graha Arudhas</strong> {' · '.join(ga_bits)}
      </div>
      <div class="two-col-grid">
        <div>
          <div class="section-title"><span class="icon-sym">✦</span> Pushkara / Kakshya</div>
          <table class="data-table" style="font-size:7.5pt;">
            <thead><tr><th>Body</th><th>PN/PB/VG</th><th>Kak</th><th>Lord</th></tr></thead>
            <tbody>{''.join(push_rows)}</tbody>
          </table>
        </div>
        <div>
          <div class="section-title"><span class="icon-sym">✦</span> Nakshatra qualities</div>
          <table class="data-table" style="font-size:7.5pt;">
            <thead><tr><th>Body</th><th>Gana</th><th>Nadi</th><th>Yoni</th><th>Rajju</th><th>Tatva</th></tr></thead>
            <tbody>{''.join(nq_rows)}</tbody>
          </table>
        </div>
      </div>
      <div class="two-col-grid">
        <div>
          <div class="section-title"><span class="icon-sym">✦</span> Functional nature</div>
          <table class="data-table" style="font-size:7.5pt;">
            <thead><tr><th>Class</th><th>Planets</th></tr></thead>
            <tbody>{''.join(fn_rows)}</tbody>
          </table>
        </div>
        <div>
          <div class="section-title"><span class="icon-sym">✦</span> Jaimini rashi-drishti</div>
          <table class="data-table" style="font-size:7.5pt;">
            <thead><tr><th>P</th><th>Sign</th><th>Aspects signs</th><th>Planets</th></tr></thead>
            <tbody>{''.join(jd_rows)}</tbody>
          </table>
        </div>
      </div>
      <div style="font-size:7.5pt;margin-top:4px;color:#334155;">
        <strong>Sahams:</strong> {' · '.join(saham_bits[:16])}
      </div>
    </div>
    {gen._build_footer(10)}
  </section>
"""
