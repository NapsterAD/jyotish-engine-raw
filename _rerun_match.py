"""Recompute Aditya natal into a second PDF and match it to the current report."""
import os
import re
import sys
import hashlib
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.core.constants import PLANETS_9
from jyotish_engine.reports.generator import ReportGenerator
from jyotish_engine.reports.pdf import html_to_pdf
from pypdf import PdfReader

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
BASE = os.path.join(OUT, "Aditya_Prasad_A4_Report")
RERUN = os.path.join(OUT, "Aditya_Prasad_A4_Report_rerun")

BIRTH = dict(
    date="2000-10-06",
    time="07:02:21",
    tz="+05:30",
    lat=23.797487,
    lon=86.305251,
    name="Aditya Prasad",
)

PASS = FAIL = 0


def check(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {label}" + (f"  {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL  {label}" + (f"  {detail}" if detail else ""))


def norm_ws(text):
    return re.sub(r"\s+", " ", (text or "").replace("\x00", "")).strip()


def pdf_pages(path):
    r = PdfReader(path)
    pages = []
    for i, pg in enumerate(r.pages):
        box = pg.mediabox
        pages.append({
            "i": i + 1,
            "w": float(box.width),
            "h": float(box.height),
            "text": norm_ws(pg.extract_text() or ""),
        })
    return pages


def facts(chart):
    lag = chart.positions["Lagna"]
    moon = chart.positions["Moon"]
    sav = (chart.ashtakavarga or {}).get("sav") or {}
    k8 = (chart.karakas_8 or {}).get("karakas") or {}
    cur = chart.get_current_dasha("2026-08-20") or {}
    md = cur.get("MD") or {}
    ad = cur.get("AD") or {}
    pd = cur.get("PD") or {}
    indu = (chart.extra_points.get("indu_lagna") or {})
    moon_kp = ((chart.kp_advanced.get("ssl_tables") or {}).get("bodies") or {}).get("Moon") or {}
    grahas = {}
    for p in ["Lagna"] + list(PLANETS_9):
        pos = chart.positions.get(p) or {}
        grahas[p] = (
            pos.get("sign"),
            round(float(pos.get("degree_in_sign") or 0), 6),
            pos.get("nakshatra"),
            pos.get("pada"),
            bool(pos.get("retrograde")),
        )
    return {
        "aya": round(float(chart.positions.get("_ayanamsha") or 0), 8),
        "lagna": (lag.get("sign"), lag.get("dms"), lag.get("nakshatra"), lag.get("pada")),
        "moon": (moon.get("sign"), moon.get("dms"), moon.get("nakshatra"), moon.get("pada")),
        "sav_total": sav.get("total"),
        "sav_vec": sav.get("sav") or sav.get("points"),
        "k8": {k: k8.get(k) for k in ("AK", "AmK", "BK", "MK", "PK", "PiK", "GK", "DK")},
        "md": (md.get("lord"), md.get("start") or md.get("start_date"), md.get("end") or md.get("end_date")),
        "ad": (ad.get("lord"), ad.get("start") or ad.get("start_date"), ad.get("end") or ad.get("end_date")),
        "pd": (pd.get("lord"), pd.get("start") or pd.get("start_date"), pd.get("end") or pd.get("end_date")),
        "indu": (indu.get("sign"), indu.get("house_from_lagna")),
        "moon_kp": (
            moon_kp.get("sign_lord"), moon_kp.get("star_lord"), moon_kp.get("sub_lord"),
            moon_kp.get("sub_sub_lord"), moon_kp.get("sssl_lord"), moon_kp.get("kp_249"),
        ),
        "grahas": grahas,
    }


def print_facts(label, f):
    print(f"\n=== {label} ===")
    print("AYANAMSHA", f["aya"])
    print("LAGNA", *f["lagna"])
    print("MOON", *f["moon"])
    print("SAV", f["sav_total"], f["sav_vec"])
    print("K8", f["k8"])
    print("MD", f["md"])
    print("AD", f["ad"])
    print("PD", f["pd"])
    print("INDU", f["indu"])
    print("MOON KP", f["moon_kp"])
    for p, row in f["grahas"].items():
        print(f"  {p:8s} {row}")


print("BASE PDF exists", os.path.exists(BASE + ".pdf"), "bytes",
      os.path.getsize(BASE + ".pdf") if os.path.exists(BASE + ".pdf") else 0)
print("BASE HTML exists", os.path.exists(BASE + ".html"), "bytes",
      os.path.getsize(BASE + ".html") if os.path.exists(BASE + ".html") else 0)

engine = JyotishEngine()
chart_a = engine.compute(**BIRTH)
chart_a.birth_data["place"] = "Katrasgarh, Jharkhand"
chart_b = engine.compute(**BIRTH)
chart_b.birth_data["place"] = "Katrasgarh, Jharkhand"

fa, fb = facts(chart_a), facts(chart_b)
print_facts("COMPUTE A", fa)
print_facts("COMPUTE B (second call)", fb)

print("\n=== ENGINE A vs B (two compute calls) ===")
for key in fa:
    check(f"compute {key}", fa[key] == fb[key], "" if fa[key] == fb[key] else f"{fa[key]} != {fb[key]}")

print("\n=== LOCKS vs known Aditya values ===")
check("Lagna Libra Swati p1", fa["lagna"][0] == "Libra" and fa["lagna"][2] == "Swati" and fa["lagna"][3] == 1)
check("Moon Sag Purva Ashadha p4", fa["moon"][0] == "Sagittarius" and fa["moon"][2] == "Purva Ashadha" and fa["moon"][3] == 4)
check("SAV 337", fa["sav_total"] == 337)
check("Rahu/Ketu retrograde", fa["grahas"]["Rahu"][4] is True and fa["grahas"]["Ketu"][4] is True)
check("8p PK Jupiter", fa["k8"].get("PK") == "Jupiter")
check("8p PiK Mercury", fa["k8"].get("PiK") == "Mercury")
check("Indu Capricorn H4", fa["indu"] == ("Capricorn", 4))
check("Moon KP Ju Ve Me Sa Rahu 183", fa["moon_kp"][:5] == ("Jupiter", "Venus", "Mercury", "Saturn", "Rahu") and fa["moon_kp"][5] == 183)
check("MD Rahu", fa["md"][0] == "Rahu")
check("AD Rahu", fa["ad"][0] == "Rahu")
check("PD Ketu", fa["pd"][0] == "Ketu")

print("\n=== WRITE RERUN HTML + PDF ===")
gen = ReportGenerator()
html_rerun = gen.generate_html(chart_a, chart_style="north", theme="gold")
html_rerun_path = RERUN + ".html"
with open(html_rerun_path, "w", encoding="utf-8") as fh:
    fh.write(html_rerun)
print("HTML rerun", html_rerun_path, os.path.getsize(html_rerun_path))
pdf_rerun_path = html_to_pdf(html_rerun, RERUN + ".pdf")
print("PDF rerun", pdf_rerun_path, os.path.getsize(pdf_rerun_path))

from pathlib import Path
html_base_path = BASE + ".html"
pdf_base_path = BASE + ".pdf"
html_base = Path(html_base_path).read_text(encoding="utf-8")

print("\n=== HTML current vs rerun ===")
check("html byte-identical", html_base == html_rerun,
      f"base={len(html_base)} rerun={len(html_rerun)}")
if html_base != html_rerun:
    # Ignore nothing — show first mismatch region
    n = min(len(html_base), len(html_rerun))
    i = next((k for k in range(n) if html_base[k] != html_rerun[k]), n)
    print("  first html mismatch at", i)
    print("  BASE ", repr(html_base[max(0, i - 40):i + 80]))
    print("  RERUN", repr(html_rerun[max(0, i - 40):i + 80]))
    # token-level: strip possible live dates already equal; count a4 pages
check("html a4-page 16", html_rerun.count('class="a4-page') == 16, str(html_rerun.count('class="a4-page')))
check("html Page 16 of 16", "Page 16 of 16" in html_rerun)
check("html no landscape", "landscape-sheet" not in html_rerun and "a4-page landscape" not in html_rerun)
check("html D24", "D24" in html_rerun)
check("html D60", "D60" in html_rerun)
check("html SSSL", "SSSL" in html_rerun)
check("html name", "Aditya Prasad" in html_rerun)
check("html place", "Katrasgarh" in html_rerun)
check("html birth date", "2000-10-06" in html_rerun)
check("html birth time", "07:02:21" in html_rerun)

print("\n=== PDF current vs rerun ===")
base_pages = pdf_pages(pdf_base_path)
rerun_pages = pdf_pages(pdf_rerun_path)
check("pdf page count", len(base_pages) == len(rerun_pages) == 16,
      f"base={len(base_pages)} rerun={len(rerun_pages)}")
wides_b = sum(1 for p in base_pages if p["w"] > p["h"])
wides_r = sum(1 for p in rerun_pages if p["w"] > p["h"])
check("both portrait", wides_b == 0 and wides_r == 0, f"base_wide={wides_b} rerun_wide={wides_r}")
check("page0 size match",
      abs(base_pages[0]["w"] - rerun_pages[0]["w"]) < 0.2 and abs(base_pages[0]["h"] - rerun_pages[0]["h"]) < 0.2,
      f"base={base_pages[0]['w']:.2f}x{base_pages[0]['h']:.2f} rerun={rerun_pages[0]['w']:.2f}x{rerun_pages[0]['h']:.2f}")

text_mismatch = 0
for b, r in zip(base_pages, rerun_pages):
    same = b["text"] == r["text"]
    if not same:
        text_mismatch += 1
        # show a short window
        bn, rn = b["text"], r["text"]
        n = min(len(bn), len(rn))
        i = next((k for k in range(n) if bn[k] != rn[k]), n)
        print(f"  DIFF page {b['i']} at char {i}")
        print("    BASE ", repr(bn[max(0, i - 30):i + 60]))
        print("    RERUN", repr(rn[max(0, i - 30):i + 60]))
    check(f"pdf text page {b['i']}", same, f"base_len={len(b['text'])} rerun_len={len(r['text'])}")

base_all = " ".join(p["text"] for p in base_pages)
rerun_all = " ".join(p["text"] for p in rerun_pages)
check("pdf full text match", base_all == rerun_all)
print("base pdf sha256", hashlib.sha256(open(pdf_base_path, "rb").read()).hexdigest()[:16])
print("rerun pdf sha256", hashlib.sha256(open(pdf_rerun_path, "rb").read()).hexdigest()[:16])
print("base html sha256", hashlib.sha256(html_base.encode("utf-8")).hexdigest()[:16])
print("rerun html sha256", hashlib.sha256(html_rerun.encode("utf-8")).hexdigest()[:16])

# Presence of lock strings in BOTH pdfs
needles = [
    "Aditya Prasad", "Katrasgarh", "Libra", "Swati", "Purva", "Rahu",
]
print("\n=== PDF lock strings in both files ===")
for needle in needles:
    check(f"pdf has {needle}", needle in base_all and needle in rerun_all)

print(f"\nRESULT  PASS={PASS}  FAIL={FAIL}  text_page_mismatches={text_mismatch}")
print("CURRENT", pdf_base_path)
print("RERUN  ", pdf_rerun_path)
if FAIL:
    sys.exit(1)
print("DONE")
