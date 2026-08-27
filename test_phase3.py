"""Test Phase 3 — Transits, Tajika, Matching, Kakshya against ground truth."""
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

def check_approx(label, computed, expected, tolerance=1.0):
    global PASS, FAIL
    if abs(computed - expected) <= tolerance:
        PASS += 1; print(f"  PASS: {label} (±{tolerance})")
    else:
        FAIL += 1; print(f"  FAIL: {label} — got {computed}, expected {expected} (±{tolerance})")


# ═══ KAKSHYA ═══
print("\n=== KAKSHYA ===")
from jyotish_engine.computations.kakshya import get_kakshya, calc_kakshya_map

# Test kakshya calculation for known positions
# Moon at Sagittarius ~25.80° -> Kakshya = ceil(25.80 / 3.75) = 7 -> Moon kakshya lord
moon_long = chart.positions["Moon"]["longitude"]
moon_kakshya = get_kakshya(moon_long)
print(f"  INFO: Moon at {moon_long:.4f}° -> {moon_kakshya['sign']} K{moon_kakshya['kakshya_num']} ({moon_kakshya['kakshya_lord']})")
check("Moon kakshya num valid", 1 <= moon_kakshya['kakshya_num'] <= 8, True)
check("Moon kakshya lord valid", moon_kakshya['kakshya_lord'] in 
      ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"], True)

# Verify kakshya arithmetic: degree_in_sign / 3.75 should give kakshya_num - 1
expected_kakshya = int(moon_kakshya['degree_in_sign'] / 3.75)
if expected_kakshya >= 8: expected_kakshya = 7
check("Moon kakshya arithmetic", moon_kakshya['kakshya_num'], expected_kakshya + 1)

# Test kakshya map has 8 entries
kmap = calc_kakshya_map(0)  # Aries
check("Kakshya map has 8 entries", len(kmap), 8)
check("Kakshya 1 lord = Saturn", kmap[0]["lord"], "Saturn")
check("Kakshya 8 lord = Lagna", kmap[7]["lord"], "Lagna")

# Test natal kakshyas via chart property
natal_kakshyas = chart.kakshyas
check("Natal kakshyas has Moon", "Moon" in natal_kakshyas, True)
check("Natal kakshyas has Lagna", "Lagna" in natal_kakshyas, True)
print(f"  INFO: All natal kakshyas computed for {len(natal_kakshyas)} bodies")


# ═══ TRANSITS ═══
print("\n=== TRANSITS ===")
from jyotish_engine.computations.transits import (
    calc_transit_positions, calc_transit_to_natal,
    calc_double_transit, calc_gochara
)

# Calculate transit positions for today (2026-08-19)
transit_pos = calc_transit_positions("2026-08-19", "12:00:00", "+05:30",
                                     lat=23.797487, lon=86.305251)
check("Transit Sun exists", "Sun" in transit_pos, True)
check("Transit Moon exists", "Moon" in transit_pos, True)
check("Transit Jupiter exists", "Jupiter" in transit_pos, True)
check("Transit Saturn exists", "Saturn" in transit_pos, True)

# Verify transit Sun is in a valid sign
t_sun_sign = transit_pos["Sun"]["sign"]
check("Transit Sun sign valid", t_sun_sign in [s for s in
      ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
       "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]], True)
print(f"  INFO: Transit Sun: {t_sun_sign} {transit_pos['Sun']['dms']}")
print(f"  INFO: Transit Jupiter: {transit_pos['Jupiter']['sign']} {transit_pos['Jupiter']['dms']}")
print(f"  INFO: Transit Saturn: {transit_pos['Saturn']['sign']} {transit_pos['Saturn']['dms']}")

# Transit-to-natal overlay
t2n = calc_transit_to_natal(transit_pos, chart)
check("T2N has all 9 planets", len(t2n) >= 9, True)
check("T2N Sun has natal_house", "natal_house" in t2n.get("Sun", {}), True)
check("T2N Sun natal_house valid", 1 <= t2n["Sun"]["natal_house"] <= 12, True)

# Double transit
dt = calc_double_transit(transit_pos, chart)
check("Double transit has jupiter_influences", "jupiter_influences" in dt, True)
check("Double transit has saturn_influences", "saturn_influences" in dt, True)
check("Double transit houses exist", "double_transit_houses" in dt, True)
print(f"  INFO: Jupiter influences houses: {dt['jupiter_influences']}")
print(f"  INFO: Saturn influences houses: {dt['saturn_influences']}")
print(f"  INFO: Double transit houses: {dt['double_transit_houses']}")
print(f"  INFO: Activated signs: {dt['activated_signs']}")

# Gochara (transit from Moon)
gochara = calc_gochara(transit_pos, chart)
check("Gochara has all 9 planets", len(gochara) >= 9, True)
check("Gochara Sun has house_from_moon", "house_from_moon" in gochara.get("Sun", {}), True)
check("Gochara Sun has net_effect", "net_effect" in gochara.get("Sun", {}), True)
print(f"  INFO: Gochara summary:")
for p in ["Sun", "Moon", "Jupiter", "Saturn", "Rahu"]:
    g = gochara.get(p, {})
    print(f"    {p:<10} H{g.get('house_from_moon', '?')} from Moon — {g.get('net_effect', '?')}")

# Full transit report via chart method
tr = chart.transits_for("2026-08-19")
check("Full transit report has date", tr.get("date"), "2026-08-19")
check("Full transit report has double_transit", "double_transit" in tr, True)
check("Full transit report has gochara", "gochara" in tr, True)


# ═══ TAJIKA ═══
print("\n=== TAJIKA (Varshaphala) ===")
from jyotish_engine.computations.tajika import calc_muntha, build_varsha_chart

# Test Muntha calculation
# Aditya: Libra lagna (idx=6), age 25 in 2026
# Muntha = (6 + 25) % 12 = 31 % 12 = 7 -> Scorpio
muntha = calc_muntha(6, 25)
check("Muntha sign", muntha["muntha_sign"], "Scorpio")
check("Muntha house from Lagna", muntha["house_from_lagna"], 2)
print(f"  INFO: Muntha for age 25: {muntha['muntha_sign']} (H{muntha['house_from_lagna']}) — {muntha['effect']}")

# Test Muntha at age 0 (should be same as Lagna)
muntha_0 = calc_muntha(6, 0)
check("Muntha at birth = Lagna sign", muntha_0["muntha_sign"], "Libra")

# Test Muntha at age 12 (should cycle back to Lagna)
muntha_12 = calc_muntha(6, 12)
check("Muntha at age 12 = Lagna sign", muntha_12["muntha_sign"], "Libra")

# Build Varsha chart for 2026
try:
    varsha = build_varsha_chart(chart.birth_data, 2026)
    check("Varsha chart year", varsha["year"], 2026)
    check("Varsha chart age", varsha["age"], 2026 - 2000)
    check("Varsha has positions", "positions" in varsha, True)
    check("Varsha has varsha_lagna", "varsha_lagna" in varsha, True)
    check("Varsha has muntha", "muntha" in varsha, True)
    print(f"  INFO: Solar Return: {varsha['solar_return_date']} {varsha['solar_return_time_ut']} UT")
    print(f"  INFO: Varsha Lagna: {varsha['varsha_lagna']}")
    print(f"  INFO: Muntha: {varsha['muntha']['muntha_sign']}")
except Exception as e:
    FAIL += 5
    print(f"  FAIL: Varsha chart build error: {e}")

# Full Tajika analysis via chart method
try:
    tajika = chart.varshaphala(2026)
    check("Tajika has varshesha", "varshesha" in tajika, True)
    check("Tajika has tajika_yogas", "tajika_yogas" in tajika, True)
    vs = tajika["varshesha"]
    print(f"  INFO: Varshesha (Year Lord): {vs['varshesha']}")
    print(f"  INFO: Tajika Yogas found: {tajika['tajika_yogas_count']}")
    for ty in tajika["tajika_yogas"][:5]:
        print(f"    {ty.get('yoga', '?')}: {ty.get('faster_planet', '?')}-{ty.get('slower_planet', '?')} ({ty.get('aspect_type', '?')})")
except Exception as e:
    FAIL += 2
    print(f"  FAIL: Tajika analysis error: {e}")


# ═══ MATCHING ═══
print("\n=== MATCHING (Ashtakoota) ===")
from jyotish_engine.computations.matching import (
    calc_ashtakoota, check_varna, check_nadi, check_bhakoot
)

# Test with Aditya's chart: Moon in Sagittarius, nakshatra Purva Ashadha (20)
# Self-match should give high score
nak_aditya = 20  # Purva Ashadha
sign_aditya = "Sagittarius"

self_match = calc_ashtakoota(nak_aditya, sign_aditya, nak_aditya, sign_aditya)
check("Self-match Varna = 1", self_match["kootas"][0]["score"], 1)
check("Self-match Vashya = 2", self_match["kootas"][1]["score"], 2)
check("Self-match Tara = 3", self_match["kootas"][2]["score"], 3)
check("Self-match Yoni = 4", self_match["kootas"][3]["score"], 4)
check("Self-match Graha Maitri = 5", self_match["kootas"][4]["score"], 5)
check("Self-match Gana = 6", self_match["kootas"][5]["score"], 6)
check("Self-match Bhakoot = 7", self_match["kootas"][6]["score"], 7)
# Note: Self-match Nadi = 0 (same nadi = dosha) UNLESS same nakshatra cancellation
nadi_result = self_match["kootas"][7]
print(f"  INFO: Self-match Nadi: score={nadi_result['score']}, dosha={nadi_result['dosha']}, cancel={nadi_result.get('cancellation')}")
# Same nakshatra -> cancellation should apply
check("Self-match Nadi cancelled", nadi_result["dosha"], False)
check("Self-match Nadi = 8", nadi_result["score"], 8)

print(f"  INFO: Self-match total: {self_match['total_score']}/{self_match['max_score']}")
check("Self-match = 36", self_match["total_score"], 36)

# Test with a different nakshatra (Ashwini = 1, Aries)
cross_match = calc_ashtakoota(nak_aditya, sign_aditya, 1, "Aries")
check("Cross-match total <= 36", cross_match["total_score"] <= 36, True)
check("Cross-match total >= 0", cross_match["total_score"] >= 0, True)
print(f"  INFO: Aditya × Ashwini/Aries: {cross_match['total_score']}/36 ({cross_match['percentage']}%)")
print(f"  INFO: Recommendation: {cross_match['recommendation']}")

# Print koota breakdown
for k in cross_match["kootas"]:
    dosha_flag = " ⚠️" if k.get("dosha") else ""
    print(f"    {k['koota']:<15} {k['score']}/{k['max_score']}{dosha_flag}")

# Test Bhakoot Dosha (6/8 pair)
# Aries(0) to Scorpio(7) = 8 houses distance -> 6/8 dosha
bhakoot_68 = check_bhakoot("Aries", "Scorpio")
print(f"  INFO: Bhakoot Aries-Scorpio: dosha={bhakoot_68['dosha']}, type={bhakoot_68.get('dosha_type')}")
# Mars rules both -> same lord cancellation
check("Bhakoot 6/8 cancelled (same lord Mars)", bhakoot_68["dosha"], False)

# Test 2/12 dosha without cancellation
bhakoot_212 = check_bhakoot("Aries", "Pisces")
print(f"  INFO: Bhakoot Aries-Pisces: dosha={bhakoot_212['dosha']}, type={bhakoot_212.get('dosha_type')}")

# Test chart-based matching (self-match via chart method)
try:
    chart2 = engine.compute(date="2000-10-06", time="07:02:21", tz="+05:30",
                            lat=23.797487, lon=86.305251, name="Aditya Copy")
    match = chart.match_with(chart2)
    check("Chart matching works", "ashtakoota" in match, True)
    check("Chart matching has manglik", "manglik_status" in match, True)
    print(f"  INFO: Chart match score: {match['ashtakoota']['total_score']}/36")
    print(f"  INFO: Manglik status: {match['manglik_status']}")
except Exception as e:
    FAIL += 2
    print(f"  FAIL: Chart matching error: {e}")


# ═══ SUMMARY ═══
print(f"\n=== PHASE 3 SUMMARY ===")
print(f"  PASSED: {PASS}")
print(f"  FAILED: {FAIL}")
print(f"  RESULT: {'ALL TESTS PASSED' if FAIL == 0 else f'{FAIL} TESTS FAILED'}")
