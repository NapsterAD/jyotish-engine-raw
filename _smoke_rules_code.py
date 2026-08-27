"""Verify engine fields match recent rules.md updates."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.computations.transits import _bb_orb, check_bb_transit
from jyotish_engine.computations.matching import check_nadi

e = JyotishEngine()
c = e.compute("2000-10-06", "07:02:21", "+05:30", 23.797487, 86.305251, "Aditya")

fails = []
moon = c.positions["Moon"]
lag = c.positions["Lagna"]
h1 = c.house_cusps["cusps"][1]
for label, d in (("Moon", moon), ("Lagna", lag), ("H1 cusp", h1)):
    for k in ("sub_lord", "sub_sub_lord", "sssl_lord", "kp_249"):
        if d.get(k) in (None, ""):
            fails.append(f"{label} missing {k}")

if not c.positions["Rahu"].get("retrograde") or not c.positions["Ketu"].get("retrograde"):
    fails.append("nodes not retrograde")
rs, ks = c.positions["Rahu"]["speed"], c.positions["Ketu"]["speed"]
if abs(rs - ks) > 1e-6:
    fails.append(f"Ketu speed {ks} != Rahu {rs}")

ns = c.dasha_systems["niryana_shoola"]
if ns.get("start_house") not in (2, 7, 8):
    fails.append(f"niryana start_house {ns.get('start_house')}")
print("niryana", ns.get("start_sign"), "H", ns.get("start_house"), ns.get("house_scores"))

kp = c.kp["planets"]["Moon"]
print("Moon KP", kp.get("sub_lord"), kp.get("sub_sub_lord"), kp.get("sssl_lord"), kp.get("kp_249"))

print("deeptadi", {p: (c.deeptadi[p]["avastha"], c.deeptadi[p].get("d9_dignity")) for p in c.deeptadi})
print("sav patterns", len(c.ashtakavarga.get("patterns") or []))

assert _bb_orb("Jupiter") == 5 and _bb_orb("Moon") == 2
bb = (c.special_points.get("bhrigu_bindu") or {}).get("longitude")
hits = check_bb_transit(c.positions, bb)  # natal overlay as dummy snapshot
print("BB natal-as-transit hits", [(h["planet"], h["kind"], h["orb"]) for h in hits])

r = check_nadi(20, 20, "Sagittarius", "Sagittarius", 3, 4)
if r["dosha"] or r["score"] != 8:
    fails.append("nadi same-nak diff-pada should cancel")

print("Moon ishta/kashta", c.ishta_kashta.get("Moon"))
if fails:
    print("FAIL", fails)
    sys.exit(1)
print("PASS")
