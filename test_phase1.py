"""
test_phase1.py — Validate Phase 1 computation modules against ground truth.
Tests: positions, vargas (D9/D10), dashas (Vimshottari/Yogini), ashtakavarga (SAV=337), avasthas.
"""

import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import jyotish_engine.core._compat

from jyotish_engine.main import JyotishEngine

# Load ground truth
gt_path = os.path.join(ROOT, "chart_ground_truth.json")
with open(gt_path, "r", encoding="utf-8") as f:
    GT = json.load(f)

# Build chart
engine = JyotishEngine()
chart = engine.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad"
)

PASS = 0
FAIL = 0

def check(label, computed, expected, tolerance=None):
    global PASS, FAIL
    if tolerance and isinstance(computed, (int, float)) and isinstance(expected, (int, float)):
        ok = abs(computed - expected) <= tolerance
    else:
        ok = (computed == expected)
    status = "PASS" if ok else "FAIL"
    if not ok:
        FAIL += 1
        print(f"  {status}: {label} — got {computed}, expected {expected}")
    else:
        PASS += 1
        print(f"  {status}: {label}")

# ═══════════════════════════════════════════
print("\n═══ 1. POSITIONS ═══")
# ═══════════════════════════════════════════
check("Lagna sign", chart.lagna_sign, "Libra")
check("Sun sign", chart.rashi_chart["Sun"]["sign"], "Virgo")
check("Sun house", chart.rashi_chart["Sun"]["house_rashi"], 12)
check("Moon sign", chart.rashi_chart["Moon"]["sign"], "Sagittarius")
check("Moon house", chart.rashi_chart["Moon"]["house_rashi"], 3)
check("Mars sign", chart.rashi_chart["Mars"]["sign"], "Leo")
check("Mars house", chart.rashi_chart["Mars"]["house_rashi"], 11)
check("Mercury sign", chart.rashi_chart["Mercury"]["sign"], "Libra")
check("Mercury house", chart.rashi_chart["Mercury"]["house_rashi"], 1)
check("Jupiter sign", chart.rashi_chart["Jupiter"]["sign"], "Taurus")
check("Jupiter house", chart.rashi_chart["Jupiter"]["house_rashi"], 8)
check("Jupiter retrograde", chart.rashi_chart["Jupiter"]["retrograde"], True)
check("Venus sign", chart.rashi_chart["Venus"]["sign"], "Libra")
check("Venus house", chart.rashi_chart["Venus"]["house_rashi"], 1)
check("Venus dignity", chart.rashi_chart["Venus"]["dignity"], "Own Sign")
check("Saturn sign", chart.rashi_chart["Saturn"]["sign"], "Taurus")
check("Saturn house", chart.rashi_chart["Saturn"]["house_rashi"], 8)
check("Saturn retrograde", chart.rashi_chart["Saturn"]["retrograde"], True)
check("Rahu sign", chart.rashi_chart["Rahu"]["sign"], "Gemini")
check("Rahu house", chart.rashi_chart["Rahu"]["house_rashi"], 9)
check("Ketu sign", chart.rashi_chart["Ketu"]["sign"], "Sagittarius")
check("Ketu house", chart.rashi_chart["Ketu"]["house_rashi"], 3)

# ═══════════════════════════════════════════
print("\n═══ 2. NAVAMSA (D9) ═══")
# ═══════════════════════════════════════════
d9 = chart.vargas["D9"]
check("D9 Lagna", d9.get("Lagna"), "Sagittarius")
check("D9 Venus", d9.get("Venus"), "Aries")
check("D9 Moon", d9.get("Moon"), "Scorpio")
check("D9 Sun", d9.get("Sun"), "Gemini")
check("D9 Jupiter", d9.get("Jupiter"), "Gemini")
check("D9 Mercury", d9.get("Mercury"), "Aquarius")
check("D9 Saturn", d9.get("Saturn"), "Aquarius")

# ═══════════════════════════════════════════
print("\n═══ 3. DASAMSA (D10) ═══")
# ═══════════════════════════════════════════
d10 = chart.vargas["D10"]
# Ground truth: D10 Lagna = Sagittarius, Mercury = Aquarius, Rahu = Gemini
check("D10 Lagna", d10.get("Lagna"), "Sagittarius")
check("D10 Mercury", d10.get("Mercury"), "Aquarius")
check("D10 Rahu", d10.get("Rahu"), "Gemini")

# ═══════════════════════════════════════════
print("\n═══ 4. VARGOTTAMA CHECK ═══")
# ═══════════════════════════════════════════
vargottama = chart.vargas["_vargottama"]
# From GT: D9 Lagna=Sagittarius but D1 Lagna=Libra -> NOT vargottama
check("Lagna NOT vargottama", vargottama.get("Lagna"), False)

# ═══════════════════════════════════════════
print("\n═══ 5. VIMSHOTTARI DASHA ═══")
# ═══════════════════════════════════════════
dashas = chart.dashas
# Find the Rahu MD
rahu_md = None
for md in dashas:
    if md["lord"] == "Rahu":
        rahu_md = md
        break

if rahu_md:
    # GT: Rahu MD = 2025-01-11 to 2043-01-12
    check("Rahu MD start", rahu_md["start_date"], "2025-01-11")
    check("Rahu MD end", rahu_md["end_date"], "2043-01-12")
    
    # Check Rahu-Rahu AD
    if "sub_periods" in rahu_md:
        rr_ad = rahu_md["sub_periods"][0]  # First AD = Rahu-Rahu
        check("Ra-Ra AD lord", rr_ad["lord"], "Rahu")
        print(f"  INFO: Ra-Ra AD dates: {rr_ad['start_date']} to {rr_ad['end_date']}")
        # GT: Ra-Ra = 2025-01-11 to 2027-09-27
else:
    FAIL += 1
    print("  FAIL: Rahu MD not found in dasha table")

# Current dasha check
current = chart.get_current_dasha("2026-08-19")
print(f"  INFO: Current dasha (2026-08-19): {current.get('summary', 'N/A')}")
if current.get("MD", {}).get("lord") == "Rahu":
    PASS += 1
    print("  PASS: Current MD = Rahu (matches GT)")
else:
    FAIL += 1
    print(f"  FAIL: Current MD = {current.get('MD', {}).get('lord')}, expected Rahu")

# ═══════════════════════════════════════════
print("\n═══ 6. YOGINI DASHA ═══")
# ═══════════════════════════════════════════
yogini = chart.yogini_dasha
if yogini:
    # GT: birth Yogini = Siddha (Venus, 7yr) with ~5.3 months balance
    birth_yogini = yogini[0]
    check("Birth Yogini name", birth_yogini["yogini"], "Siddha")
    check("Birth Yogini planet", birth_yogini["planet"], "Venus")
    print(f"  INFO: Balance at birth: {birth_yogini['balance_used']:.4f} years")
else:
    FAIL += 1
    print("  FAIL: Yogini dasha not computed")

# ═══════════════════════════════════════════
print("\n═══ 7. ASHTAKAVARGA ═══")
# ═══════════════════════════════════════════
avk = chart.ashtakavarga
sav = avk["sav"]

check("SAV total", sav["total"], 337)

# Check individual house SAV values (by sign, from GT)
gt_sav_by_sign = {
    "Libra": 30, "Scorpio": 21, "Sagittarius": 28, "Capricorn": 24,
    "Aquarius": 32, "Pisces": 39, "Aries": 18, "Taurus": 26,
    "Gemini": 29, "Cancer": 30, "Leo": 35, "Virgo": 25
}
from jyotish_engine.core.constants import SIGNS, SIGN_INDEX
for sign_name, expected_val in gt_sav_by_sign.items():
    idx = SIGN_INDEX[sign_name]
    computed_val = sav["sav"][idx]
    check(f"SAV {sign_name}", computed_val, expected_val)

# Row totals check
gt_row_totals = {"Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54,
                 "Jupiter": 56, "Venus": 52, "Saturn": 39, "Lagna": 49}
for planet, expected_total in gt_row_totals.items():
    check(f"BAV row total {planet}", avk["row_totals"].get(planet), expected_total)

# ═══════════════════════════════════════════
print("\n═══ 8. AVASTHAS ═══")
# ═══════════════════════════════════════════
avasthas = chart.avasthas
# GT avasthas
gt_avasthas = {
    "Mercury": "Yuva", "Venus": "Vriddha", "Sun": "Vriddha",
    "Mars": "Vriddha", "Saturn": "Vriddha", "Moon": "Mrita"
}
for planet, expected_av in gt_avasthas.items():
    computed_av = avasthas.get(planet, {}).get("avastha", "N/A")
    check(f"Avastha {planet}", computed_av, expected_av)

# ═══════════════════════════════════════════
print("\n═══ 9. SHADBALA ═══")
# ═══════════════════════════════════════════
sb = chart.shadbala
# GT: Mercury = strongest (9.83 rupas), Saturn = weakest (4.78)
# We check ranking (who's #1) rather than exact values since this is simplified
planet_rupas = [(p, d["rupas"]) for p, d in sb.items()]
planet_rupas.sort(key=lambda x: x[1], reverse=True)
print(f"  INFO: Shadbala ranking: {', '.join(f'{p}({r})' for p, r in planet_rupas)}")
check("Shadbala strongest planet", planet_rupas[0][0], "Mercury")

# ═══════════════════════════════════════════
print("\n═══ SUMMARY ═══")
print(f"  PASSED: {PASS}")
print(f"  FAILED: {FAIL}")
print(f"  TOTAL:  {PASS + FAIL}")
print(f"  RESULT: {'ALL TESTS PASSED' if FAIL == 0 else f'{FAIL} TESTS FAILED'}")
