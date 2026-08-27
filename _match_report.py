"""
Match report: Aditya Prasad natal vs chart_ground_truth.json + COMBINED/ad2 lock.
"""
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.core.constants import SIGNS
from jyotish_engine.computations.ashtakavarga import calc_sodhya_pinda
from jyotish_engine.computations.yogas import (
    check_manglik, check_kaal_sarp, check_kemadruma, check_pancha_mahapurusha,
    check_kalatramooladdhana, check_viparita_raja,
)

GT_PATH = os.path.join(ROOT, "chart_ground_truth.json")
with open(GT_PATH, "r", encoding="utf-8") as f:
    GT = json.load(f)

engine = JyotishEngine()
c = engine.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad",
)

rows = []  # (category, label, pass, got, want, note)


def add(cat, label, ok, got, want, note=""):
    rows.append((cat, label, bool(ok), got, want, note))


def eq(cat, label, got, want, note=""):
    add(cat, label, got == want, got, want, note)


def near(cat, label, got, want, tol, note=""):
    try:
        ok = abs(float(got) - float(want)) <= tol
    except Exception:
        ok = False
    add(cat, label, ok, got, want, note or f"tol={tol}")


def days_apart(a, b):
    da = datetime.strptime(a, "%Y-%m-%d")
    db = datetime.strptime(b, "%Y-%m-%d")
    return abs((da - db).days)


def dms_to_deg(s):
    """Parse 19°15'48\" or 19d15m style to decimal degrees."""
    s = s.replace("d", "°").replace("m", "'").replace('"', "")
    s = s.replace("″", "").replace("′", "'")
    parts = s.replace("°", " ").replace("'", " ").split()
    d = float(parts[0])
    m = float(parts[1]) if len(parts) > 1 else 0
    sec = float(parts[2]) if len(parts) > 2 else 0
    return d + m / 60.0 + sec / 3600.0


# ═══════════════════════════════════════════
# 1. LONGITUDES (ad2 / COMBINED)
# ═══════════════════════════════════════════
exp_deg = {
    "Lagna": 7.373075, "Sun": 19.263425, "Moon": 25.818256, "Mars": 18.133456,
    "Mercury": 14.626203, "Jupiter": 17.315183, "Venus": 20.105519,
    "Saturn": 6.635906, "Rahu": 26.441492,
}
for p, w in exp_deg.items():
    near("Positions", f"{p} degree-in-sign", c.positions[p]["degree_in_sign"], w, 0.01)

gt_r = GT["rashi_chart"]
map_p = {
    "Lagna": "lagna", "Sun": "sun", "Moon": "moon", "Mars": "mars",
    "Mercury": "mercury", "Jupiter": "jupiter", "Venus": "venus",
    "Saturn": "saturn", "Rahu": "rahu", "Ketu": "ketu",
}
eq("Positions", "Lagna sign", c.lagna_sign, "Libra")
for p, key in map_p.items():
    if p == "Lagna":
        eq("Positions", "Lagna nakshatra", c.positions[p]["nakshatra"], "Swati")
        continue
    gt = gt_r[key]
    eq("Positions", f"{p} sign", c.positions[p]["sign"], gt["sign"])
    eq("Rashi houses", f"{p} rashi house", c.rashi_chart[p]["house_rashi"], gt["house_rashi"])
    eq("Chalit", f"{p} chalit house", c.chalit_chart[p]["house_chalit"], gt["house_chalit"])
    if gt.get("retrograde"):
        eq("Positions", f"{p} retrograde", bool(c.positions[p].get("retrograde")), True)

# ═══════════════════════════════════════════
# 2. BAV / SAV
# ═══════════════════════════════════════════
bav = c.ashtakavarga["bav"]
for p, row in GT["BAV"].items():
    if p.startswith("_") or p in ("row_totals", "aries_7H_bindus"):
        continue
    eq("Ashtakavarga", f"BAV {p}", list(bav[p]), list(row))
sav = c.ashtakavarga["sav"]["sav"]
# GT SAV is by HOUSE (1H Libra ...), engine SAV is Aries-first vector
# engine: index 0=Aries=7H ... 6=Libra=1H
# GT: 1H_Libra=30 means Libra (index 6)
gt_sav_house = {
    1: GT["SAV"]["1H_Libra"], 2: GT["SAV"]["2H_Scorpio"], 3: GT["SAV"]["3H_Sagittarius"],
    4: GT["SAV"]["4H_Capricorn"], 5: GT["SAV"]["5H_Aquarius"], 6: GT["SAV"]["6H_Pisces"],
    7: GT["SAV"]["7H_Aries"], 8: GT["SAV"]["8H_Taurus"], 9: GT["SAV"]["9H_Gemini"],
    10: GT["SAV"]["10H_Cancer"], 11: GT["SAV"]["11H_Leo"], 12: GT["SAV"]["12H_Virgo"],
}
# sign index from lagna: house h -> sign_idx = (lagna_index + h - 1) % 12
for h, val in gt_sav_house.items():
    sidx = (c.lagna_index + h - 1) % 12
    eq("Ashtakavarga", f"SAV H{h} {SIGNS[sidx]}", sav[sidx], val)
eq("Ashtakavarga", "SAV total", sum(sav), 337)

sp = calc_sodhya_pinda(bav, c.positions)
for p, want in GT["sodhya_pindas"].items():
    if p.startswith("_"):
        continue
    got = sp.get(p, {})
    eq("Ashtakavarga", f"Sodhya {p}", got.get("sodhya"), want["sodhya"])

# ═══════════════════════════════════════════
# 3. KARAKAS
# ═══════════════════════════════════════════
k8 = c.karakas_8["karakas"]
k7 = c.karakas["karakas"]
# COMBINED/ad2 8p print
eq("Karakas 8p (ad2 print)", "AK", k8.get("AK"), "Moon")
eq("Karakas 8p (ad2 print)", "AmK", k8.get("AmK"), "Venus")
eq("Karakas 8p (ad2 print)", "BK", k8.get("BK"), "Sun")
eq("Karakas 8p (ad2 print)", "MK", k8.get("MK"), "Mars")
eq("Karakas 8p (ad2 print)", "PK", k8.get("PK"), "Jupiter")
eq("Karakas 8p (ad2 print)", "PiK", k8.get("PiK"), "Mercury")
eq("Karakas 8p (ad2 print)", "GK", k8.get("GK"), "Saturn")
eq("Karakas 8p (ad2 print)", "DK", k8.get("DK"), "Rahu")
# 7p KN Rao
eq("Karakas 7p (KN Rao)", "AK", k7.get("AK"), "Moon")
eq("Karakas 7p (KN Rao)", "AmK", k7.get("AmK"), "Venus")
eq("Karakas 7p (KN Rao)", "BK", k7.get("BK"), "Sun")
eq("Karakas 7p (KN Rao)", "MK", k7.get("MK"), "Mars")
eq("Karakas 7p (KN Rao)", "PK", k7.get("PK"), "Jupiter")
eq("Karakas 7p (KN Rao)", "GK", k7.get("GK"), "Mercury")
eq("Karakas 7p (KN Rao)", "DK", k7.get("DK"), "Saturn")
km = c.karakamsa
eq("Jaimini", "Karakamsa", km.get("karakamsa") or km.get("sign"), "Scorpio")

# ═══════════════════════════════════════════
# 4. ARUDHAS / SPECIAL POINTS
# ═══════════════════════════════════════════
ar = c.arudhas
eq("Arudhas", "AL (A1)", ar["A1"]["sign"], "Cancer")
eq("Arudhas", "UL (A12)", ar["A12"]["sign"], "Scorpio")
eq("Arudhas", "A7 Darapada", ar["A7"]["sign"], "Sagittarius")

y = c.special_points["yogi"]
eq("Special points", "Yogi", y["yogi"], "Moon")
eq("Special points", "SahaYogi", y["sahayogi"], "Venus")
eq("Special points", "Avayogi", y["avayogi"], "Mercury")

bb = c.special_points["bhrigu_bindu"]
bb_sign = bb.get("sign")
eq("Special points", "Bhrigu Bindu sign", bb_sign, "Virgo")
near("Special points", "Bhrigu Bindu deg", bb.get("degree_in_sign", bb.get("longitude", 0) % 30), 26.1, 0.5)

vs = c.special_points["vivaha_saham_tajika"]
eq("Special points", "Tajika Vivaha sign", vs.get("sign"), "Sagittarius")
pvs = c.special_points["vivaha_saham_parashara"]
eq("Special points", "Parashara Vivaha sign", pvs.get("sign"), "Pisces")

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
    sign, deg = lon_sign_deg(lon)
    eq("Special lagnas", f"{name} sign", sign, want_sign)
    near("Special lagnas", f"{name} deg", deg, want_deg, 1.5)

# ═══════════════════════════════════════════
# 5. VARGAS D9 / D10
# ═══════════════════════════════════════════
d9 = c.vargas["D9"]
gt9 = GT["navamsa_d9"]
d9_map = {
    "Lagna": "lagna", "Sun": "sun", "Moon": "moon", "Mars": "mars",
    "Mercury": "mercury", "Jupiter": "jupiter", "Venus": "venus",
    "Saturn": "saturn", "Rahu": "rahu", "Ketu": "ketu",
}
for p, k in d9_map.items():
    want = gt9[k].split()[0] if "(" in gt9[k] or " " in gt9[k] else gt9[k]
    want = want.replace("(7H)", "").replace("(12H)", "").replace("(10H)", "").replace("(3H)", "").replace("(5H)", "").replace("(6H)", "").strip()
    got = d9[p] if isinstance(d9[p], str) else d9[p].get("sign")
    eq("Vargas D9", f"D9 {p}", got, want)

d10 = c.vargas["D10"]
gt10 = GT["d10_dashamsa"]
for p, k in [("Lagna", "lagna"), ("Mercury", "mercury"), ("Rahu", "rahu"),
             ("Sun", "sun"), ("Mars", "mars"), ("Jupiter", "jupiter")]:
    want = gt10[k].split()[0]
    got = d10[p] if isinstance(d10[p], str) else d10[p].get("sign")
    eq("Vargas D10", f"D10 {p}", got, want)

# ═══════════════════════════════════════════
# 6. DASHAS
# ═══════════════════════════════════════════
ra = [m for m in c.dashas if m["lord"] == "Rahu"][0]
gt_d = GT["current_dasha"]
near("Vimshottari", "Rahu MD start (days vs 2025-01-11)",
     days_apart(ra["start_date"], gt_d["mahadasha_start"]), 0, 3)
near("Vimshottari", "Rahu MD end (days vs 2043-01-12)",
     days_apart(ra["end_date"], gt_d["mahadasha_end"]), 0, 3)
ra_ra = ra["sub_periods"][0]
eq("Vimshottari", "First AD lord", ra_ra["lord"], "Rahu")
ra_ju = [ad for ad in ra["sub_periods"] if ad["lord"] == "Jupiter"][0]
near("Vimshottari", "Ra-Ju start (days vs 2027-09-27)",
     days_apart(ra_ju["start_date"], gt_d["next_AD_start"]), 0, 3)

yog = c.yogini_dasha
# list of MD
first = yog[0] if isinstance(yog, list) else yog.get("periods", [{}])[0]
# birth yogini Siddha/Venus
birth_lord = first.get("lord") or first.get("yogini")
ok_sid = birth_lord in ("Venus", "Siddha", "Siddha (Venus)")
add("Yogini", "Birth yogini Siddha/Venus", ok_sid, birth_lord, "Siddha (Venus)")

# ═══════════════════════════════════════════
# 7. KP (COMBINED True Citra equal + planet SSL)
# ═══════════════════════════════════════════
exp_planet = {
    "Lagna": ("Rahu", "Rahu"), "Sun": ("Moon", "Mercury"), "Moon": ("Venus", "Mercury"),
    "Mars": ("Venus", "Rahu"), "Mercury": ("Rahu", "Ketu"), "Jupiter": ("Moon", "Saturn"),
    "Venus": ("Jupiter", "Jupiter"), "Saturn": ("Sun", "Mercury"),
    "Rahu": ("Jupiter", "Ketu"), "Ketu": ("Venus", "Ketu"),
}
for p, (star, sub) in exp_planet.items():
    pos = c.positions[p]
    eq("KP planets", f"{p} star", pos["nakshatra_lord"], star)
    eq("KP planets", f"{p} sub", pos.get("sub_lord"), sub)

eq_cusp = c.kp["equal_cusps"]
exp_eq_sub = {1: "Rahu", 2: "Ketu", 3: "Rahu", 4: "Ketu", 5: "Rahu", 6: "Ketu",
              7: "Rahu", 8: "Ketu", 9: "Rahu", 10: "Ketu", 11: "Rahu", 12: "Ketu"}
for h, sub in exp_eq_sub.items():
    eq("KP equal CSL", f"H{h} sub", eq_cusp[h]["sub_lord"], sub)

p7 = c.house_cusps["cusps"][7]
eq("KP Placidus", "7H star", p7.get("nak_lord") or p7.get("star_lord"), "Ketu")
eq("KP Placidus", "7H sub", p7["sub_lord"], "Rahu")

# GT Placidus table is KP-ayanamsha; compare star/sub only as INFO vs True Citra
gt_kp = GT["kp_cusps_and_sublords"]
# 1H True Citra should still be Rahu/Rahu
eq("KP vs GT (True Citra vs KP-aya)", "1H sub still Rahu",
   c.house_cusps["cusps"][1]["sub_lord"], gt_kp["1H_Lagna"]["sub_lord"])

# ═══════════════════════════════════════════
# 8. YOGAS / DOSHAS
# ═══════════════════════════════════════════
pmp = check_pancha_mahapurusha(c)
malavya = any(y.get("planet") == "Venus" for y in pmp)
add("Yogas", "Malavya (Venus own/exalt Kendra)", malavya, [y["name"] for y in pmp], "Malavya Yoga")
vry = check_viparita_raja(c)
add("Yogas", "Viparita Raja present", any(y.get("formed") for y in vry), 
    [y["name"] for y in vry if y.get("formed")], "VRY 6L/8L")
kmd = check_kalatramooladdhana(c)
add("Yogas", "Kalatramooladdhana (7L in 11H)", kmd.get("formed"), kmd.get("formed"), True)
kem = check_kemadruma(c)
eq("Yogas", "Kemadruma formed", kem.get("formed"), True)
mg = check_manglik(c)
eq("Yogas", "Manglik raw from Lagna", mg.get("from_lagna"), False)
ks = check_kaal_sarp(c)
eq("Yogas", "Kaal Sarp NOT formed", ks.get("formed"), False)

# ═══════════════════════════════════════════
# 9. AVASTHAS (Baladi)
# ═══════════════════════════════════════════
av = c.avasthas
eq("Avasthas", "Moon Mrita", av.get("Moon", {}).get("avastha"), "Mrita")
eq("Avasthas", "Mercury Yuva", av.get("Mercury", {}).get("avastha"), "Yuva")
eq("Avasthas", "Venus Vriddha", av.get("Venus", {}).get("avastha"), "Vriddha")
eq("Avasthas", "Sun Vriddha", av.get("Sun", {}).get("avastha"), "Vriddha")
eq("Avasthas", "Mars Vriddha", av.get("Mars", {}).get("avastha"), "Vriddha")
eq("Avasthas", "Saturn Vriddha", av.get("Saturn", {}).get("avastha"), "Vriddha")

# ═══════════════════════════════════════════
# 10. SHADBALA (JHora full vs engine simplified — expect drift)
# ═══════════════════════════════════════════
sb = c.shadbala
want_sb = {"Mercury": 9.83, "Jupiter": 8.32, "Moon": 7.01, "Venus": 6.66,
           "Sun": 5.75, "Mars": 5.85, "Saturn": 4.78}
for p, w in want_sb.items():
    got = sb.get(p, {})
    rup = got.get("rupas") if isinstance(got, dict) else got
    near("Shadbala (JHora full)", f"{p} rupas", rup, w, 0.4, "engine is simplified")

ik = c.ishta_kashta
j_ik = ik.get("Jupiter", {})
near("Ishta-Kashta", "Jupiter Ishta", j_ik.get("ishta") or j_ik.get("Ishta"), 43.73, 5)
near("Ishta-Kashta", "Jupiter Kashta", j_ik.get("kashta") or j_ik.get("Kashta"), 16.26, 5)

# ═══════════════════════════════════════════
# 11. LORDSHIPS / PANCHANG / BADHAKA
# ═══════════════════════════════════════════
eq("Lordships", "1L", c.lordships[1], "Venus")
eq("Lordships", "7L", c.lordships[7], "Mars")
eq("Lordships", "Yogakaraka Saturn 4L+5L", c.lordships[4] == "Saturn" and c.lordships[5] == "Saturn", True)
eq("Badhaka", "house 11 (movable Libra)", c.badhaka["house"], 11)
eq("Badhaka", "Badhakesh Sun", c.badhaka["lord"], "Sun")
eq("Panchang", "tithi Shukla Navami", c.panchang["tithi"]["full_name"], "Shukla Navami")
eq("Panchang", "vara Friday/Venus", c.panchang["vara"]["lord"], "Venus")

# ═══════════════════════════════════════════
# PRINT
# ═══════════════════════════════════════════
from collections import OrderedDict
cats = OrderedDict()
for cat, label, ok, got, want, note in rows:
    cats.setdefault(cat, []).append((label, ok, got, want, note))

print("=" * 78)
print("  MATCH REPORT — Aditya Prasad  2000-10-06 07:02:21 IST  Katrasgarh")
print("  Engine vs JHora/ad2/COMBINED lock + chart_ground_truth.json")
print("=" * 78)

grand_p = grand_f = 0
for cat, items in cats.items():
    p = sum(1 for x in items if x[1])
    f = len(items) - p
    grand_p += p
    grand_f += f
    pct = 100.0 * p / len(items) if items else 0
    print(f"\n--- {cat}  {p}/{len(items)}  ({pct:.0f}%) ---")
    for label, ok, got, want, note in items:
        mark = "PASS" if ok else "FAIL"
        extra = f"  [{note}]" if note else ""
        if ok:
            print(f"  {mark}  {label}")
        else:
            print(f"  {mark}  {label}")
            print(f"         got={got}  want={want}{extra}")

print("\n" + "=" * 78)
total = grand_p + grand_f
print(f"  TOTAL  {grand_p}/{total} PASS   {grand_f} FAIL   {100.0*grand_p/total:.1f}%")
print("=" * 78)

# known-soft categories
soft = {"Shadbala (JHora full)", "Ishta-Kashta"}
core = [(cat, items) for cat, items in cats.items() if cat not in soft]
cp = sum(sum(1 for x in items if x[1]) for _, items in core)
ct = sum(len(items) for _, items in core)
print(f"  CORE (excl. simplified Shadbala)  {cp}/{ct}  {100.0*cp/ct:.1f}%")
print()
print("  Positions snapshot:")
print(f"    Lagna {c.positions['Lagna']['sign']} {c.positions['Lagna']['dms']}  ayanamsha={c.positions['_ayanamsha']:.4f}")
print(f"    Sunrise {c.sunrise_sunset.get('sunrise')}  day_birth={c.sunrise_sunset.get('is_day_birth')}")
print(f"    Rahu MD {ra['start_date']} -> {ra['end_date']}")
print(f"    Ra-Ju   {ra_ju['start_date']} -> {ra_ju['end_date']}")
print(f"    Tithi   {c.panchang['tithi']['full_name']}  Hora {c.panchang['hora']['hora_lord']}")
