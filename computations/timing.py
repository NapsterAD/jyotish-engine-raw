"""
timing.py — Marriage-timing convergence. rules.md §19.
"""

from ..core.constants import SIGN_LORDS
from ..core.mapping import house_to_sign, sign_to_house, DUSTHANA_HOUSES


def calc_marriage_timing(chart, date=None):
    """
    Check whether current (or birth) dasha lords and natal factors
    converge on marriage significators. Transit double-check is optional
    via date.
    """
    lord7 = chart.lordships.get(7)
    in7 = chart.get_planets_in_house(7, "rashi")
    venus = "Venus"
    d9 = chart.vargas.get("D9") or {}
    d9_lagna = d9.get("Lagna") if isinstance(d9, dict) else None
    if isinstance(d9_lagna, dict):
        d9_lagna = d9_lagna.get("sign")
    d9_lagna_lord = SIGN_LORDS.get(d9_lagna) if d9_lagna else None
    ul = None
    try:
        ul = chart.arudhas.get("A12") or chart.arudhas.get("UL")
    except Exception:
        pass
    ul_lord = None
    if isinstance(ul, dict):
        ul_sign = ul.get("sign")
        ul_lord = SIGN_LORDS.get(ul_sign) if ul_sign else None
    dk = None
    try:
        kar = chart.karakas_8 or {}
        if isinstance(kar, dict):
            inner = kar.get("karakas") if isinstance(kar.get("karakas"), dict) else kar
            dk = inner.get("DK")
            if isinstance(dk, dict):
                dk = dk.get("planet")
    except Exception:
        pass

    significators = [x for x in [lord7, venus, d9_lagna_lord, ul_lord, dk] if x]
    significators.extend(in7)

    current = chart.get_current_dasha(date) or {}
    md = ad = pd = None
    if isinstance(current, dict):
        md = current.get("MD", {})
        ad = current.get("AD", {})
        pd = current.get("PD", {})
        md = md.get("lord") if isinstance(md, dict) else md
        ad = ad.get("lord") if isinstance(ad, dict) else ad
        pd = pd.get("lord") if isinstance(pd, dict) else pd

    dasha_hit = [x for x in (md, ad, pd) if x and x in significators]

    d9_7_dusthana = None
    if d9_lagna:
        sign7 = house_to_sign(7, d9_lagna)
        d9_7_lord = SIGN_LORDS[sign7]
        d9_7_sign = d9.get(d9_7_lord) if isinstance(d9, dict) else None
        if isinstance(d9_7_sign, dict):
            d9_7_sign = d9_7_sign.get("sign")
        if d9_7_sign:
            h = sign_to_house(d9_7_sign, d9_lagna)
            d9_7_dusthana = h in DUSTHANA_HOUSES

    return {
        "significators": list(dict.fromkeys(significators)),
        "dasha": {"md": md, "ad": ad, "pd": pd, "hits": dasha_hit},
        "dasha_supports": bool(dasha_hit),
        "navamsa_7l_dusthana": d9_7_dusthana,
        "ul_lord": ul_lord,
        "darakaraka": dk,
    }
