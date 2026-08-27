"""Compute Aditya natal and write HTML + PDF + synthesis/advanced JSON."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.core.constants import PLANETS_9

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT, exist_ok=True)

engine = JyotishEngine()
chart = engine.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad",
)
chart.birth_data["place"] = "Katrasgarh, Jharkhand"

lag = chart.positions["Lagna"]
moon = chart.positions["Moon"]
print("NAME", chart.birth_data["name"])
print("BIRTH", chart.birth_data["date"], chart.birth_data["time"], chart.birth_data["tz"])
print("PLACE", chart.birth_data.get("place"), chart.birth_data["lat"], chart.birth_data["lon"])
print("AYANAMSHA", chart.positions.get("_ayanamsha"), chart.birth_data.get("ayanamsha"))
print("LAGNA", lag.get("sign"), lag.get("dms"), "nak", lag.get("nakshatra"), "p", lag.get("pada"))
print("MOON", moon.get("sign"), moon.get("dms"), moon.get("nakshatra"), "p", moon.get("pada"),
      "lord", moon.get("nakshatra_lord"))
print("SAV total", (chart.ashtakavarga or {}).get("sav", {}).get("total"))

print("--- GRAHAS ---")
for p in PLANETS_9:
    pos = chart.positions.get(p) or {}
    rc = chart.rashi_chart.get(p) or {}
    print(
        f"{p:8s} {pos.get('sign','?'):12s} {pos.get('dms','?'):12s} "
        f"H{rc.get('house_rashi','?'):<2} {rc.get('dignity','')}"
        f"{' R' if pos.get('retrograde') else ''}"
    )

k7 = chart.karakas or {}
k8 = chart.karakas_8 or {}
print("KARAKA 7", {k: (v.get("planet") if isinstance(v, dict) else v) for k, v in k7.items()}
      if isinstance(k7, dict) else k7)
print("KARAKA 8", {k: (v.get("planet") if isinstance(v, dict) else v) for k, v in k8.items()}
      if isinstance(k8, dict) else k8)

cur = chart.get_current_dasha("2026-08-20") or {}
md = cur.get("MD") or {}
ad = cur.get("AD") or {}
pd = cur.get("PD") or {}
print("DASHA now MD", md.get("lord"), md.get("start_date"), "->", md.get("end_date"))
print("         AD", ad.get("lord"), ad.get("start_date"), "->", ad.get("end_date"))
print("         PD", pd.get("lord"), pd.get("start_date"), "->", pd.get("end_date"))

indu = (chart.extra_points.get("indu_lagna") or {})
print("INDU", indu.get("sign"), "H", indu.get("house_from_lagna"))
moon_kp = ((chart.kp_advanced.get("ssl_tables") or {}).get("bodies") or {}).get("Moon") or {}
print("MOON KP", moon_kp.get("sign_lord"), moon_kp.get("star_lord"), moon_kp.get("sub_lord"),
      moon_kp.get("sub_sub_lord"), moon_kp.get("sssl_lord"), "249", moon_kp.get("kp_249"))

html_path = os.path.join(OUT, "Aditya_Prasad_A4_Report.html")
saved = chart.to_html_report(html_path)
print("HTML", saved, os.path.getsize(saved))
with open(saved, encoding="utf-8") as f:
    html = f.read()
for n in ("cover-page", "Contents", "Page 16 of 16", "Janma Kundali", "Ve*"):
    print(("PASS" if n in html else "FAIL"), n)

pdf_path = os.path.join(OUT, "Aditya_Prasad_A4_Report.pdf")
pdf = chart.to_pdf_report(pdf_path)
print("PDF", pdf, os.path.getsize(pdf))

syn = os.path.join(OUT, "Aditya_Prasad_A4_Report_synthesis.json")
adv = os.path.join(OUT, "Aditya_Prasad_A4_Report_advanced.json")
for p in (syn, adv):
    print(("JSON" if os.path.exists(p) else "MISSING"), p,
          os.path.getsize(p) if os.path.exists(p) else 0)
print("DONE")
