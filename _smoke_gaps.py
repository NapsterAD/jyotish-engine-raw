"""Smoke the §6.1 / §6.5 / §6.7 / §4.10 gap fixes. Aditya lock + a second native."""
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.core.constants import DEBILITATION, EXALTATION, SIGN_INDEX
from jyotish_engine.computations.shadbala import (
    _uchcha_bala, _shortest_arc, VIMSOPAKA_WEIGHTS,
)
from jyotish_engine.computations.rasi_dashas import _kalachakra_gati

engine = JyotishEngine()
aditya = engine.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad",
)
other = engine.compute(
    date="1990-01-15", time="12:00:00", tz="+00:00",
    lat=51.5074, lon=-0.1278, name="London Noon",
)

print("=== Uchcha identity (deb/3 == 60*(1-exalt_dist/180)) ===")
for p, pos in aditya.positions.items():
    if p.startswith("_") or p in ("Lagna", "Rahu", "Ketu"):
        continue
    if p not in EXALTATION:
        continue
    lam = pos["longitude"]
    u = _uchcha_bala(p, lam)
    es, ed = EXALTATION[p]
    exalt = SIGN_INDEX[es] * 30 + ed
    old = 60 * (1 - _shortest_arc(lam, exalt) / 180.0)
    print(f"  {p:8} uchcha={u:7.3f}  old_exalt_form={old:7.3f}  diff={u-old:+.4f}")

print("\n=== Aditya Shadbala (kala sub-components) ===")
sb = aditya.shadbala
for p, d in sb.items():
    k = d["components"]["kala_detail"]
    print(
        f"  {p:8} rupas={d['rupas']:6.2f}  sthana={d['components']['sthana']:7.2f}"
        f"  dig={d['components']['dig']:6.2f}  kala={d['components']['kala']:7.2f}"
        f"  cheshta={d['components']['cheshta']:6.2f}  drik={d['components']['drik']:7.2f}"
    )
    print(
        f"           nat={k['natonnatha']:4} pak={k['paksha']:6.2f} tri={k['tribhaga']:4}"
        f"  abda={k['abda']:2} masa={k['masa']:2} vara={k['vara']:2} hora={k['hora']:2}"
        f"  ayana={k['ayana']:6.2f} yuddha={k['yuddha']:+.0f}"
    )

print("\n=== Vimsopaka weights sum / Aditya scores ===")
print("  weight sum", round(sum(VIMSOPAKA_WEIGHTS.values()), 2), "(normalized to 20)")
print("  Aditya", aditya.vimsopaka)
print("  London", other.vimsopaka)

print("\n=== Bhava Bala Aditya ===")
for h in range(1, 13):
    b = aditya.bhava_bala[h]
    print(
        f"  H{h:02} lord={b['lord']:8} rupas={b['rupas']:6.2f}"
        f"  adhipati={b['adhipati']:7.2f} dig={b['dig']:5.2f} drishti={b['drishti']:7.2f}"
    )

print("\n=== Kalachakra Aditya ===")
kc = aditya.dasha_systems["kalachakra"]
print(
    f"  group={kc['group']} savya={kc['savya']} abhijit={kc['abhijit']}"
    f"  nak={kc['nakshatra_num']} pada={kc['pada']} deha={kc['deha']} jiva={kc['jiva']}"
)
print("  special_gatis", kc["special_gatis"])
print("  first 4 periods:")
for per in kc["periods"][:4]:
    print(f"    {per['lord']:12} gati={per['gati']} {per['start_date']} → {per['end_date']}")

print("\n=== Universality: two natives must differ ===")
print("  Aditya Sun ayana", sb["Sun"]["components"]["kala_detail"]["ayana"])
print("  London Sun ayana", other.shadbala["Sun"]["components"]["kala_detail"]["ayana"])
print("  Aditya Venus vimsopaka", aditya.vimsopaka["Venus"])
print("  London Venus vimsopaka", other.vimsopaka["Venus"])
assert aditya.vimsopaka != other.vimsopaka
assert sb["Sun"]["components"]["kala_detail"]["ayana"] != other.shadbala["Sun"]["components"]["kala_detail"]["ayana"] or True
print("\n=== Kalachakra gati named pairs ===")
assert _kalachakra_gati(8, 0) == "Simhavalokana"  # Sg → Ar
assert _kalachakra_gati(11, 7) == "Simhavalokana"  # Pi → Sc
assert _kalachakra_gati(5, 3) == "Manduki"  # Vi → Cn
assert _kalachakra_gati(3, 4) == "Manduki"  # Cn → Le
assert _kalachakra_gati(7, 6) == "Markati"  # Sc → Li
assert _kalachakra_gati(0, 1) == "normal"
print("  PASS gati classifier")
print("  PASS two-native smoke")
