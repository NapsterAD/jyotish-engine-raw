"""Generate HTML + advanced JSON on one chart (shared caches). No PDF."""
import os
import sys
import time
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT, exist_ok=True)

engine = JyotishEngine()
chart = engine.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad",
)
chart.birth_data["place"] = "Katrasgarh, Jharkhand"

t0 = time.perf_counter()
html_path = os.path.join(OUT, "Aditya_Prasad_A4_Report.html")
saved = chart.to_html_report(html_path)
t_html = time.perf_counter() - t0
print("HTML", saved, os.path.getsize(saved), f"{t_html:.3f}s")

with open(saved, encoding="utf-8") as f:
    html = f.read()

needles = [
    "Page 16 of 16",
    "Sthana sub-scores",
    "Varga sphuta",
    "ABCD Significators",
    "Indu",
    "Purva Ashadha",
    "Capricorn",
]
for n in needles:
    print(("PASS" if n in html else "FAIL"), n)

t1 = time.perf_counter()
json_path = os.path.join(OUT, "Aditya_Prasad_A4_Report_advanced.json")
savedj = chart.to_advanced_json(json_path, from_date="2026-09-01")
t_json = time.perf_counter() - t1
print("JSON", savedj, os.path.getsize(savedj), f"{t_json:.3f}s")

with open(savedj, encoding="utf-8") as f:
    pack = json.load(f)

for k in ("kp_advanced", "extra_points", "time_pack", "raw_layers"):
    block = pack.get(k)
    err = isinstance(block, dict) and block.get("error")
    print(("FAIL" if err else "PASS"), k, "" if not err else err)

go = (pack.get("time_pack") or {}).get("monthly_gochara") or []
print("json gochara months", len(go))
if go:
    ju = (go[0].get("planets") or {}).get("Jupiter") or {}
    print("json Sep-2026 Jupiter", ju.get("sign"), "H", ju.get("natal_house"), "SAV", ju.get("sav_score"))
print("DONE")
