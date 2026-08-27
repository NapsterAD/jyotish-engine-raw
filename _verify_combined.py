"""Verify engine against COMBINED/JHora locked values."""
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from jyotish_engine.main import JyotishEngine
from jyotish_engine.core.constants import SIGNS

e = JyotishEngine()
c = e.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad",
)
PASS = FAIL = 0

def check(label, got, want, tol=None):
    global PASS, FAIL
    ok = abs(got - want) <= tol if (tol is not None and isinstance(got, (int, float))) else got == want
    if ok:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}  got={got}  want={want}")

print("ayanamsha", round(c.positions["_ayanamsha"], 4))
print("sunrise", c.sunrise_sunset)
print("special_lagnas", c.special_lagnas)

print("\n=== DEGREES vs ad2 ===")
exp_deg = {
    "Lagna": 7.373075, "Sun": 19.263425, "Moon": 25.818256, "Mars": 18.133456,
    "Mercury": 14.626203, "Jupiter": 17.315183, "Venus": 20.105519,
    "Saturn": 6.635906, "Rahu": 26.441492,
}
for p, w in exp_deg.items():
    check(f"{p} deg", c.positions[p]["degree_in_sign"], w, tol=0.01)

print("\n=== CHALIT ===")
for p in ["Moon", "Saturn", "Rahu", "Ketu", "Jupiter", "Sun"]:
    ch = c.chalit_chart[p]
    print(f"  {p}: rashi={ch['house_rashi']} cusp={ch['house_chalit']} madhya={ch['house_chalit_madhya']} {ch['shift_description']}")
check("Saturn chalit 7H", c.chalit_chart["Saturn"]["house_chalit"], 7)
check("Moon chalit 4H", c.chalit_chart["Moon"]["house_chalit"], 4)
check("Rahu chalit 10H", c.chalit_chart["Rahu"]["house_chalit"], 10)
check("Ketu chalit 4H", c.chalit_chart["Ketu"]["house_chalit"], 4)
check("Jupiter chalit 8H", c.chalit_chart["Jupiter"]["house_chalit"], 8)

print("\n=== BAV / SAV ===")
exp_bav = {
    "Sun":     [3, 4, 4, 3, 4, 7, 3, 2, 4, 3, 4, 7],
    "Moon":    [3, 4, 5, 5, 5, 3, 4, 2, 6, 3, 5, 4],
    "Mars":    [1, 4, 2, 2, 5, 2, 3, 3, 3, 2, 6, 6],
    "Mercury": [2, 6, 4, 4, 6, 3, 5, 4, 4, 5, 5, 6],
    "Jupiter": [4, 3, 7, 6, 6, 3, 5, 6, 2, 3, 5, 6],
    "Venus":   [3, 2, 4, 5, 6, 2, 4, 4, 6, 6, 6, 4],
    "Saturn":  [2, 3, 3, 5, 3, 5, 6, 0, 3, 2, 1, 6],
    "Lagna":   [0, 6, 4, 4, 6, 2, 6, 5, 3, 4, 5, 4],
}
bav = c.ashtakavarga["bav"]
for p, row in exp_bav.items():
    got = bav[p]
    if got == row:
        PASS += 1
        print(f"  PASS  BAV {p}")
    else:
        FAIL += 1
        diffs = [(SIGNS[i], got[i], row[i]) for i in range(12) if got[i] != row[i]]
        print(f"  FAIL  BAV {p} tot={sum(got)} vs {sum(row)} {diffs}")
got_sav = c.ashtakavarga["sav"]["sav"]
check("SAV total", sum(got_sav), 337)
check("SAV vector", got_sav, [18, 26, 29, 30, 35, 25, 30, 21, 28, 24, 32, 39])
check("SAV 7H", got_sav[0], 18)
check("SAV 6H Pisces", got_sav[11], 39)

print("\n=== KARAKAS 8p ===")
k8 = c.karakas_8["karakas"]
print(" ", k8)
check("8p PK", k8.get("PK"), "Jupiter")
check("8p PiK", k8.get("PiK"), "Mercury")
check("8p GK", k8.get("GK"), "Saturn")
check("8p DK", k8.get("DK"), "Rahu")
check("7p PK", c.karakas["karakas"]["PK"], "Jupiter")
check("7p DK", c.karakas["karakas"]["DK"], "Saturn")

print("\n=== SPECIAL POINTS ===")
y = c.special_points["yogi"]
check("Yogi", y["yogi"], "Moon")
check("SahaYogi", y["sahayogi"], "Venus")
check("Avayogi", y["avayogi"], "Mercury")

print("\n=== DASHA ===")
ra = [m for m in c.dashas if m["lord"] == "Rahu"][0]
print(" Rahu MD", ra["start_date"], "->", ra["end_date"])
ra_ju = [ad for ad in ra["sub_periods"] if ad["lord"] == "Jupiter"][0]
print(" Ra-Ju", ra_ju["start_date"], "->", ra_ju["end_date"])
d = abs((datetime.strptime(ra["start_date"], "%Y-%m-%d") - datetime.strptime("2025-01-11", "%Y-%m-%d")).days)
check("Rahu MD start within 3d of 2025-01-11", d <= 3, True)
d2 = abs((datetime.strptime(ra_ju["start_date"], "%Y-%m-%d") - datetime.strptime("2027-09-27", "%Y-%m-%d")).days)
check("Ra-Ju start within 3d of 2027-09-27", d2 <= 3, True)

print("\n=== SPECIAL LAGNAS (MASTER) ===")
# MASTER: BL 9 Li 16, HL 29 Li 20, GL 29 Sg 32, VL 0 Sc 32, Varnada 7 Ta 22, Sree 14 Vi 28
# Maandi 18 Li 46, Gulika 9 Li 01
sl = c.special_lagnas

def lon_sign_deg(lon):
    return SIGNS[int(lon / 30) % 12], lon % 30

for name, want_sign, want_deg in [
    ("bhava_lagna", "Libra", 9.27),
    ("hora_lagna", "Libra", 29.34),
    ("ghati_lagna", "Sagittarius", 29.54),
    ("sree_lagna", "Virgo", 14.47),
    ("varnada_lagna", "Taurus", 7.37),
]:
    lon = sl.get(name)
    if lon is None:
        check(name, None, want_sign)
        continue
    sign, deg = lon_sign_deg(lon)
    print(f"  INFO {name}: {sign} {deg:.2f}°")
    check(f"{name} sign", sign, want_sign)
    check(f"{name} deg", deg, want_deg, tol=1.5)

for name in ("maandi", "gulika", "vighati_lagna"):
    lon = sl.get(name)
    if lon:
        sign, deg = lon_sign_deg(lon)
        print(f"  INFO {name}: {sign} {deg:.2f}°")

print(f"\n========== PASS={PASS} FAIL={FAIL} ==========")
