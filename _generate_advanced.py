"""Build Aditya advanced raw-calculation JSON (no PDF)."""
import os
import sys
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

path = os.path.join(OUT, "Aditya_Prasad_A4_Report_advanced.json")
saved = chart.to_advanced_json(path, from_date="2026-09-01")
size = os.path.getsize(saved)
print("WROTE", saved, size, "bytes")

with open(saved, encoding="utf-8") as f:
    pack = json.load(f)

must = [
    "kp_advanced", "extra_points", "time_pack", "dasha_md_full",
    "positions", "shadbala", "vargas", "vimsopaka", "derived_yoga_hints",
]
for k in must:
    ok = k in pack and not (isinstance(pack[k], dict) and pack[k].get("error"))
    print(("PASS" if ok else "FAIL"), k, type(pack.get(k)).__name__,
          list(pack[k].keys())[:8] if isinstance(pack.get(k), dict) else "")
    if isinstance(pack.get(k), dict) and pack[k].get("error"):
        print("  ERROR", pack[k]["error"])

kp = pack.get("kp_advanced") or {}
ssl = (kp.get("ssl_tables") or {}).get("bodies") or {}
print("SSL Moon chain", ssl.get("Moon"))
mx = ((kp.get("significator_matrix_placidus") or {}).get("grid") or {}).get("Venus")
print("Venus fold H1", (mx or {}).get("1"))
print("CRL interlink count",
      len((kp.get("cuspal_interlinks_placidus") or {}).get("interlinks") or []))

ep = pack.get("extra_points") or {}
print("Indu", (ep.get("indu_lagna") or {}).get("sign"),
      (ep.get("indu_lagna") or {}).get("house_from_lagna"))
print("Tithi Lagna", (ep.get("tithi_lagna") or {}).get("sign"))
print("D10 lagna", (ep.get("d10_facts") or {}).get("d10_lagna"),
      "10th-from", (ep.get("d10_facts") or {}).get("tenth_from_d10_lagna"))

tp = pack.get("time_pack") or {}
print("varsha years", [v.get("year") for v in (tp.get("varshaphala") or []) if isinstance(v, dict)])
print("gochara months", len(tp.get("monthly_gochara") or []))
print("eclipses", len(tp.get("eclipses") or []))
print("tara years", len((tp.get("tara_bala_years") or {}).get("years") or []))
print("BB windows", {k: len(v) for k, v in ((tp.get("bhrigu_bindu_windows") or {}).get("windows") or {}).items()})
print("DONE")
