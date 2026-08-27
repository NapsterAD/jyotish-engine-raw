"""Smoke the spec/code fixes from the rules.md audit."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.computations.matching import check_nadi
from jyotish_engine.computations.transits import _bb_orb

assert _bb_orb("Jupiter") == 5.0
assert _bb_orb("Saturn") == 5.0
assert _bb_orb("Moon") == 2.0
assert _bb_orb("Venus", orb=1.0) == 1.0

# same nadi, different nak — dosha
r = check_nadi(1, 10)  # Ashwini + Magha both Aadi typically
print("nadi different nak same type", r["dosha"], r["score"], r["cancellation"])

# same nak different pada → cancel
r = check_nadi(20, 20, "Sagittarius", "Sagittarius", 3, 4)
print("same nak diff pada", r["dosha"], r["cancellation"], r["score"])

# same nak same pada, different sign — still dosha unless same sign cancels
r = check_nadi(20, 20, "Sagittarius", "Capricorn", 4, 4)
print("same nak same pada diff sign", r["dosha"], r["cancellation"], r["score"])

# same sign cancel
r = check_nadi(1, 10, "Aries", "Aries")
print("same sign", r["dosha"], r["cancellation"], r["score"])

engine = JyotishEngine()
c = engine.compute("2000-10-06", "07:02:21", "+05:30", 23.797487, 86.305251, "Aditya Prasad")
print("niryana start", c.dasha_systems["niryana_shoola"]["start_sign"])
print("deeptadi", {p: c.deeptadi[p]["avastha"] for p in c.deeptadi})
print("sav patterns", c.ashtakavarga.get("patterns"))
print("PASS")
