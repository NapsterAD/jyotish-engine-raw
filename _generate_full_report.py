import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

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

html_path = os.path.join(OUT, "Aditya_Prasad_A4_Report.html")
saved = chart.to_html_report(html_path)
print("HTML", saved, os.path.getsize(saved))
with open(saved, encoding="utf-8") as f:
    html = f.read()

needles = [
    "Page 14 of 14",
    "Sthana sub-scores",
    "Varga sphuta",
    "10-Year Ingress",
    "AD → PD",
    "ABCD Significators",
    "Narayana",
    "Kalachakra",
    "Double transit",
    "Lal Kitab",
    "Bhrigu Nandi",
    "Ayurdaya",
    "Vimsopaka",
    "BAV 8",
    "KP-249",
    "249",
    "Indu",
    "not formed",
]
for n in needles:
    print(("PASS" if n in html else "FAIL"), n)

pdf_path = os.path.join(OUT, "Aditya_Prasad_A4_Report.pdf")
pdf = chart.to_pdf_report(pdf_path)
print("PDF", pdf, os.path.getsize(pdf))
print("DONE")
