"""CI-style guards on Aditya lock: SAV house vector + Shadbala caps/rupas."""
import os
import sys

# Force UTF-8 stdout on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.core.constants import PLANETS_7, SIGNS
from jyotish_engine.core.mapping import house_to_sign

# ad2.pdf = JHora = PyJHora (COMBINED register row 49). NOT the retracted H1↔H2 swap.
ADITYA_SAV_BY_HOUSE = {
    1: 30, 2: 21, 3: 28, 4: 24, 5: 32, 6: 39,
    7: 18, 8: 26, 9: 29, 10: 30, 11: 35, 12: 25,
}
ADITYA_SAV_ARIES = [18, 26, 29, 30, 35, 25, 30, 21, 28, 24, 32, 39]
ADITYA_SHADBALA_RUPAS = {
    "Sun": 5.75, "Moon": 7.01, "Mars": 5.85, "Mercury": 9.83,
    "Jupiter": 8.32, "Venus": 6.66, "Saturn": 4.78,
}

PASS = FAIL = WARN = 0


def check(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {label}" + (f"  {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL  {label}" + (f"  {detail}" if detail else ""))


def warn(label, detail=""):
    global WARN
    WARN += 1
    print(f"  WARN  {label}" + (f"  {detail}" if detail else ""))


engine = JyotishEngine()
c = engine.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad",
)

print("=== SAV (Aries→Pisces + by house) ===")
sav = c.ashtakavarga["sav"]["sav"]
check("SAV total 337", sum(sav) == 337, str(sum(sav)))
check("SAV Aries-first vector", sav == ADITYA_SAV_ARIES, str(sav))
by_h = c.ashtakavarga["by_house"]
for h, want in ADITYA_SAV_BY_HOUSE.items():
    got = by_h.get(h)
    check(f"SAV H{h} {house_to_sign(h, c.lagna_index)}", got == want, f"got={got} want={want}")

virgo_sag = sav[5:9]
check(
    "Virgo–Sag is 25,30,21,28 (NOT reversed 28,21,30,25)",
    virgo_sag == [25, 30, 21, 28],
    str(virgo_sag),
)

print("\n=== Shadbala Kala / Drik caps ===")
sb = c.shadbala
for p in PLANETS_7:
    kd = sb[p]["components"]["kala_detail"]
    drik = sb[p]["components"]["drik"]
    pak = kd["paksha"]
    if p == "Moon":
        # JHora 2E/3 uncapped; flag only if wildly beyond 2*60
        if pak > 120:
            check(f"{p} paksha insane", False, str(pak))
        elif pak > 60:
            warn(f"{p} paksha {pak} > 60 (JHora leaves 2E/3 uncapped in Kala)")
        else:
            check(f"{p} paksha <= 60", True, str(pak))
    else:
        check(f"{p} paksha in [0,60]", 0 <= pak <= 60, str(pak))
    check(f"{p} drik in [-60,60]", -60 <= drik <= 60, str(drik))
    check(f"{p} drik not parked at ±60 cap", abs(abs(drik) - 60) > 0.05, str(drik))

print("\n=== Shadbala rupas vs ad2/JHora ===")
for p, want in ADITYA_SHADBALA_RUPAS.items():
    got = sb[p]["rupas"]
    diff = got - want
    # Drik /4 + Seeghra Chesta. Residual is saptavargaja (natural vs compound
    # friendship), largest on Mars. Saturn may still sit just above min 5.0.
    tol = 1.10 if p == "Mars" else 0.70
    ok = abs(diff) <= tol
    check(f"{p} rupas {got:.2f} vs {want:.2f} (±{tol:.2f})", ok, f"diff={diff:+.2f}")
    if p == "Sun":
        check("Sun sub-minimum vs 6.5 (ad2 FAIL)", got < 6.5, f"status={sb[p]['status']}")
    if p == "Saturn" and abs(diff) > 0.40:
        warn(f"Saturn still {got:.2f} vs ad2 4.78 — residual kala/sthana")

sa_che = sb["Saturn"]["components"]["cheshta"]
check("Saturn cheshta is Seeghra Kendra/3 (~45), not speed+retro (~52)", 40 <= sa_che <= 50, str(sa_che))

print("\n=== Components (Sun/Venus/Saturn/Moon) ===")
for p in ("Sun", "Venus", "Saturn", "Moon"):
    d = sb[p]["components"]
    kd = d["kala_detail"]
    print(
        f"  {p:8} rupas={sb[p]['rupas']:.2f} sthana={d['sthana']:.2f} dig={d['dig']:.2f}"
        f" kala={d['kala']:.2f} cheshta={d['cheshta']:.2f} nais={d['naisargika']:.2f}"
        f" drik={d['drik']:.2f} pak={kd['paksha']:.2f} ayana={kd['ayana']:.2f}"
    )

print(f"\nRESULT  PASS={PASS}  FAIL={FAIL}  WARN={WARN}")
if FAIL:
    sys.exit(1)
print("DONE")
