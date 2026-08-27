"""Time cached layers vs first compute; check SAV/BAV and ingress sanity."""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine


def lap(label, fn):
    t0 = time.perf_counter()
    val = fn()
    dt = time.perf_counter() - t0
    print(f"{label:28s} {dt:7.3f}s")
    return val, dt


engine = JyotishEngine()
chart, t_chart = lap("BirthChart.compute", lambda: engine.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad",
))

_, t_kp1 = lap("kp_advanced first", lambda: chart.kp_advanced)
_, t_kp2 = lap("kp_advanced cached", lambda: chart.kp_advanced)
_, t_ep1 = lap("extra_points first", lambda: chart.extra_points)
_, t_ep2 = lap("extra_points cached", lambda: chart.extra_points)
_, t_rl1 = lap("raw_layers first", lambda: chart.raw_layers)
_, t_rl2 = lap("raw_layers cached", lambda: chart.raw_layers)
tp, t_tp1 = lap("time_pack first", lambda: chart.get_time_pack(from_date="2026-09-01"))
_, t_tp2 = lap("time_pack cached", lambda: chart.get_time_pack(from_date="2026-09-01"))
_, t_tp3 = lap("time_pack slice 12mo", lambda: chart.get_time_pack(from_date="2026-09-01", months=12))
_, t_v1 = lap("varshaphala 2026 first", lambda: chart.varshaphala(2026))
_, t_v2 = lap("varshaphala 2026 cached", lambda: chart.varshaphala(2026))

ing = (chart.raw_layers.get("ingress_2025_2043") or {}).get("planets") or {}
ton = (chart.raw_layers.get("transit_over_natal") or {})
go = tp.get("monthly_gochara") or []
sav_ok = 0
sav_none = 0
for row in go:
    for p, block in (row.get("planets") or {}).items():
        if block.get("sav_score") is None:
            sav_none += 1
        else:
            sav_ok += 1

print("gochara months", len(go), "sav filled", sav_ok, "sav missing", sav_none)
print("tara years", len((tp.get("tara_bala_years") or {}).get("years") or []))
print("varsha years", [v.get("year") for v in (tp.get("varshaphala") or []) if isinstance(v, dict)])
print("eclipses", len(tp.get("eclipses") or []))
print("ingress Ju", len(ing.get("Jupiter") or []), "Sa", len(ing.get("Saturn") or []))
print("transit_over_natal keys", list((ton.get("hits") or {}).keys()))
print("indu", (chart.extra_points.get("indu_lagna") or {}).get("sign"))
print("kp Moon chain", ((chart.kp_advanced.get("ssl_tables") or {}).get("bodies") or {}).get("Moon"))
print("ABCD H1", (chart.kp_advanced.get("abcd_all_houses") or {}).get("1"))

fails = []
if t_kp2 > 0.05:
    fails.append("kp cache miss")
if t_rl2 > 0.05:
    fails.append("raw_layers cache miss")
if t_tp2 > 0.05:
    fails.append("time_pack cache miss")
if t_v2 > 0.05:
    fails.append("varsha cache miss")
if sav_none:
    fails.append("monthly SAV missing")
if len(go) != 36:
    fails.append(f"gochara months {len(go)}")
if not ing.get("Jupiter"):
    fails.append("no Jupiter ingresses")
if isinstance(ton.get("hits"), dict) and not ton["hits"]:
    fails.append("transit_over_natal empty")
if fails:
    print("FAIL", fails)
    sys.exit(1)
print("PASS caches + SAV/BAV + ingress")
