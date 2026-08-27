"""Test Phase 2 — Karakas, Arudhas, Special Points, Yogas against ground truth."""
import sys, json
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from jyotish_engine.main import JyotishEngine

with open("chart_ground_truth.json", "r", encoding="utf-8") as f:
    GT = json.load(f)

engine = JyotishEngine()
chart = engine.compute(date="2000-10-06", time="07:02:21", tz="+05:30",
                       lat=23.797487, lon=86.305251, name="Aditya Prasad")

PASS = FAIL = 0
def check(label, computed, expected):
    global PASS, FAIL
    if computed == expected:
        PASS += 1; print(f"  PASS: {label}")
    else:
        FAIL += 1; print(f"  FAIL: {label} — got {computed}, expected {expected}")

# ═══ KARAKAS ═══
print("\n=== CHARA KARAKAS (7-planet) ===")
k7 = chart.karakas["karakas"]
check("AK", k7.get("AK"), "Moon")
check("AmK", k7.get("AmK"), "Venus")
check("BK", k7.get("BK"), "Sun")
check("MK", k7.get("MK"), "Mars")
check("PK", k7.get("PK"), "Jupiter")
check("GK", k7.get("GK"), "Mercury")
check("DK", k7.get("DK"), "Saturn")
print(f"  INFO: 7-planet ranking: {chart.karakas['ranking']}")

print("\n=== CHARA KARAKAS (8-planet) ===")
k8 = chart.karakas_8["karakas"]
check("8P AK", k8.get("AK"), "Moon")
check("8P AmK", k8.get("AmK"), "Venus")
print(f"  INFO: 8-planet ranking: {chart.karakas_8['ranking']}")

# ═══ KARAKAMSA ═══
print("\n=== KARAKAMSA ===")
km = chart.karakamsa
check("Karakamsa sign", km["karakamsa"], "Scorpio")
check("Karakamsa 7H", km["karakamsa_7h"], "Taurus")

# ═══ ARUDHAS ═══
print("\n=== ARUDHA PADAS ===")
arudhas = chart.arudhas
# GT: AL = Cancer (10H)
check("Arudha Lagna (A1)", arudhas["A1"]["sign"], "Cancer")
check("A1 house", arudhas["A1"]["house_from_lagna"], 10)
# GT: Upapada (A12) = Scorpio (2H)
check("Upapada (A12)", arudhas["A12"]["sign"], "Scorpio")
# GT: Dara Pada (A7) = Sagittarius (3H)
check("Darapada (A7)", arudhas["A7"]["sign"], "Sagittarius")
check("A7 house", arudhas["A7"]["house_from_lagna"], 3)

# Print all arudhas for reference
for key in [f"A{i}" for i in range(1, 13)]:
    a = arudhas[key]
    print(f"  INFO: {key} = {a['sign']} (H{a['house_from_lagna']})")

# ═══ SPECIAL POINTS ═══
print("\n=== SPECIAL POINTS ===")
sp = chart.special_points
# GT: Yogi = Moon
check("Yogi planet", sp["yogi"]["yogi"], "Moon")
# GT: Avayogi = Mercury
check("Avayogi", sp["yogi"]["avayogi"], "Mercury")
# GT: SahaYogi = Venus
check("SahaYogi", sp["yogi"]["sahayogi"], "Venus")
print(f"  INFO: Yogi Point: {sp['yogi']['yogi_point_sign']} {sp['yogi']['yogi_point_dms']}")
print(f"  INFO: Yogi Nakshatra: {sp['yogi']['yogi_nakshatra']}")

# Bhrigu Bindu — GT: Virgo 26d06m
bb = sp["bhrigu_bindu"]
print(f"  INFO: Bhrigu Bindu: {bb['sign']} {bb['dms']}")
check("BB sign", bb["sign"], "Virgo")

# ═══ YOGAS ═══
print("\n=== YOGAS ===")
yogas = chart.yogas
formed_names = [y["name"] for y in yogas["formed"]]
print(f"  INFO: {yogas['total_formed']} yogas formed / {yogas['total_checked']} checked")

# GT key yogas
check("Malavya Yoga", "Malavya Yoga" in formed_names, True)
check("Kemadruma Yoga", "Kemadruma Yoga" in formed_names, True)
check("Manglik NOT formed", "Manglik Dosha (Kuja Dosha)" not in formed_names, True)
check("Kaal Sarp NOT formed", "Kaal Sarp Yoga" not in formed_names, True)
# GT: 7L Mars in 11H = Kalatramooladdhana
check("Kalatramooladdhana", "Kalatramooladdhana Yoga" in formed_names, True)

# Check for VRY
vry_formed = [y for y in yogas["formed"] if "Viparita" in y["name"]]
print(f"  INFO: VRY count: {len(vry_formed)}")
for v in vry_formed:
    print(f"    {v['name']}: {v.get('description', '')}")

# Print all formed yogas
print("\n  All formed yogas:")
for y in yogas["formed"]:
    desc = y.get("description", y.get("connection", ""))
    print(f"    + {y['name']}: {desc}")

# ═══ SUMMARY ═══
print(f"\n=== SUMMARY ===")
print(f"  PASSED: {PASS}")
print(f"  FAILED: {FAIL}")
print(f"  RESULT: {'ALL TESTS PASSED' if FAIL == 0 else f'{FAIL} TESTS FAILED'}")
