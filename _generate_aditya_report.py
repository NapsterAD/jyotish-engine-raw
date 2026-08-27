"""Generate Aditya Prasad A4 HTML + PDF + synthesis JSON."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT_DIR, exist_ok=True)

engine = JyotishEngine()
chart = engine.compute(
    date="2000-10-06",
    time="07:02:21",
    tz="+05:30",
    lat=23.797487,
    lon=86.305251,
    name="Aditya Prasad",
)
chart.birth_data["place"] = "Katrasgarh, Jharkhand"

html_path = os.path.join(OUT_DIR, "Aditya_Prasad_A4_Report.html")
pdf_path = os.path.join(OUT_DIR, "Aditya_Prasad_A4_Report.pdf")
json_path = os.path.join(OUT_DIR, "Aditya_Prasad_A4_Report_synthesis.json")

saved_html = chart.to_html_report(html_path)
print("HTML", saved_html, os.path.getsize(saved_html), "bytes")

# Confirm identity is in the HTML
with open(saved_html, encoding="utf-8") as f:
    html = f.read()
for needle in (
    "Aditya Prasad",
    "Katrasgarh",
    "2000-10-06",
    "07:02:21",
    "23.797487",
    "86.305251",
    "Libra",
    "KP Placidus CSL",
    "PK=Jupiter",
    "PiK=Mercury",
):
    ok = needle in html
    print(("PASS" if ok else "FAIL"), "html contains", needle)
    if not ok:
        raise SystemExit(f"missing {needle}")
if "Lakshmi Yoga" in html:
    raise SystemExit("Lakshmi Yoga still listed as formed")
if ">0.00</td>" in html and "Moon" in html:
    # Moon Kashta must not be 0.00 — look at the ishta table more carefully below
    pass

saved_pdf = chart.to_pdf_report(pdf_path)
print("PDF", saved_pdf, os.path.getsize(saved_pdf), "bytes")
print("JSON", json_path, os.path.exists(json_path), 
      os.path.getsize(json_path) if os.path.exists(json_path) else 0, "bytes")

print("Lagna", chart.lagna_sign, chart.positions["Lagna"]["dms"])
print("Moon", chart.positions["Moon"]["sign"], chart.positions["Moon"]["nakshatra"])

# Four report-error checks
k8 = chart.karakas_8["karakas"]
print("8p PK", k8.get("PK"), "PiK", k8.get("PiK"))
assert k8.get("PK") == "Jupiter" and k8.get("PiK") == "Mercury", k8
moon_k = chart.ishta_kashta["Moon"]["kashta"]
print("Moon Kashta", moon_k)
assert abs(moon_k - 34.34) < 0.2, moon_k
formed_names = [y.get("name") for y in chart.yogas.get("formed", [])]
print("formed yogas", formed_names)
assert "Lakshmi Yoga" not in formed_names
assert any("Raj" in n or "Dhana" in n for n in formed_names)
cusps = chart.house_cusps["cusps"]
subs = [cusps[h]["sub_lord"] for h in range(1, 13)]
print("Placidus CSL", subs)
assert subs != ["Rahu", "Ketu"] * 6
assert len(set(subs)) > 2
print("DONE four-error checks PASS")
