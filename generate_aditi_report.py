import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine

OUT = os.path.join(ROOT, "jyotish_engine", "output")
os.makedirs(OUT, exist_ok=True)

print("Computing Aditi Chart in JyotishEngine...")
engine = JyotishEngine()
chart = engine.compute(
    date="2006-01-30",
    time="13:31:30",
    tz="+05:30",
    lat=23.0 + 46.0 / 60.0,
    lon=86.0 + 10.0 / 60.0,
    name="Aditi",
)
chart.birth_data["place"] = "Karmatanr, Jharkhand"

# 1. HTML Report
html_path = os.path.join(OUT, "Aditi_A4_Report.html")
saved_html = chart.to_html_report(html_path)
print(f"Generated HTML: {saved_html} ({os.path.getsize(saved_html)} bytes)")

# 2. PDF Report
pdf_path = os.path.join(OUT, "Aditi_A4_Report.pdf")
saved_pdf = chart.to_pdf_report(pdf_path)
print(f"Generated PDF:  {saved_pdf} ({os.path.getsize(saved_pdf)} bytes)")

# 3. Synthesis JSON
syn_path = os.path.join(OUT, "Aditi_A4_Report_synthesis.json")
saved_syn = chart.to_synthesis_json(syn_path)
print(f"Generated Synthesis JSON: {saved_syn} ({os.path.getsize(saved_syn)} bytes)")

# 4. Advanced JSON
adv_path = os.path.join(OUT, "Aditi_A4_Report_advanced.json")
saved_adv = chart.to_advanced_json(adv_path)
print(f"Generated Advanced JSON:  {saved_adv} ({os.path.getsize(saved_adv)} bytes)")

print("\nALL 4 OUTPUTS SUCCESSFULLY GENERATED AND SAVED TO OUTPUT FOLDER!")
