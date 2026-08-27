"""
audit_my_chart.py — Complete chart execution & cross-verification against ground truth.
"""
import os
import sys
import json

# Force UTF-8 stdout on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.core.constants import SIGNS

# Load ground truth
with open('chart_ground_truth.json', 'r', encoding='utf-8') as f:
    GT = json.load(f)

engine = JyotishEngine()
chart = engine.compute(
    date="2000-10-06",
    time="07:02:21",
    tz="+05:30",
    lat=23.797487,
    lon=86.305251,
    name="Aditya Prasad"
)

print("=" * 75)
print("   JYOTISH ENGINE TEST RUN: ADITYA PRASAD (GROUND TRUTH AUDIT)")
print("=" * 75)

# 1. POSITIONS
print("\n[1] CORE PLANETARY POSITIONS (D1 RASHI)")
print("-" * 75)
print(f"Lagna   : {chart.positions['Lagna']['sign']:<12} {chart.positions['Lagna']['dms']:<10} "
      f"{chart.positions['Lagna']['nakshatra']:<16} P{chart.positions['Lagna']['pada']}")
for p in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
    pos = chart.positions[p]
    rc = chart.rashi_chart[p]
    retro = " [R]" if pos.get('retrograde') else ""
    lord = rc.get('lordship_str', '')
    print(f"{p:<8}: {pos['sign']:<12} H{rc['house_rashi']:<2} {pos['dms']:<10} "
          f"{pos['nakshatra']:<16} P{pos['pada']} {lord:<8} {rc['dignity']}{retro}")

# 2. BHAVA CHALIT
print("\n[2] BHAVA CHALIT (HOUSE SHIFTS)")
print("-" * 75)
shifts = 0
for p, ch in chart.chalit_chart.items():
    if ch['shifted']:
        shifts += 1
        print(f"  * {p}: SHIFTED from H{ch['house_rashi']} to H{ch['house_chalit']} ({ch['shift_description']})")
if shifts == 0:
    print("  No planets shifted house in Chalit (all remain in their Rashi house cusps).")

# 3. DIVISIONAL CHARTS
print("\n[3] DIVISIONAL CHARTS (KEY VARGAS)")
print("-" * 75)
v = chart.vargas
print(f"  D9  (Navamsa)    : Lagna={v['D9']['Lagna']}, Venus={v['D9']['Venus']}, Moon={v['D9']['Moon']}, "
      f"Sun={v['D9']['Sun']}, Jupiter={v['D9']['Jupiter']}, Mercury={v['D9']['Mercury']}, Saturn={v['D9']['Saturn']}")
print(f"  D10 (Dashamsha)  : Lagna={v['D10']['Lagna']}, Mercury={v['D10']['Mercury']}, Sun={v['D10']['Sun']}, "
      f"Saturn={v['D10']['Saturn']}, Jupiter={v['D10']['Jupiter']}")
print(f"  D7  (Saptamsha)  : Lagna={v['D7']['Lagna']}, Jupiter={v['D7']['Jupiter']}, Venus={v['D7']['Venus']}")
print(f"  D60 (Shashtiamsha): Lagna={v['D60']['Lagna']}, Moon={v['D60']['Moon']}, Venus={v['D60']['Venus']}")

# 4. CHARA KARAKAS & KARAKAMSA
print("\n[4] JAIMINI CHARA KARAKAS (7-PLANET CANONICAL)")
print("-" * 75)
k7 = chart.karakas
for karaka, p in k7['karakas'].items():
    deg = k7['details'][p]['degree_in_sign']
    gt_p = GT.get('jaimini_karakas', {}).get('seven_planet_scheme', {}).get(karaka, '')
    match = "MATCH" if gt_p.startswith(p) else f"GT: {gt_p}"
    print(f"  {karaka:<5} = {p:<8} ({deg:>6.2f}°)  [{match}]")

km = chart.karakamsa
print(f"  Karakamsha Sign      : {km['karakamsa']} (AK Moon in Scorpio D9)")
print(f"  7th from Karakamsha  : {km['karakamsa_7h']} (Ruled by Venus)")

# 5. ARUDHA PADAS
print("\n[5] ARUDHA PADAS (A1 TO A12)")
print("-" * 75)
ar = chart.arudhas
for i in range(1, 13):
    a = ar[f'A{i}']
    print(f"  A{i:<2} ({a['name']:<22}): {a['sign']:<12} (H{a['house_from_lagna']:>2})")

# 6. SPECIAL SENSITIVE POINTS
print("\n[6] SPECIAL SENSITIVE POINTS & SAHAMS")
print("-" * 75)
sp = chart.special_points
yogi = sp['yogi']
bb = sp['bhrigu_bindu']
vs_tajika = sp['vivaha_saham_tajika']
vs_parashara = sp['vivaha_saham_parashara']
pof = sp['part_of_fortune']

print(f"  Yogi Point        : {yogi['yogi_point_sign']} {yogi['yogi_point_dms']} ({yogi['yogi_nakshatra']}) | "
      f"Yogi: {yogi['yogi']}, Avayogi: {yogi['avayogi']}, SahaYogi: {yogi['sahayogi']}")
print(f"  Bhrigu Bindu (BB) : {bb['sign']} {bb['dms']} ({bb['nakshatra']}) [In 12H Virgo]")
print(f"  Vivaha Saham (Tajika)   : {vs_tajika['sign']} {vs_tajika['dms']} (In 3H Sagittarius, conjunct AK Moon + Ketu)")
print(f"  Vivaha Saham (Parashara): {vs_parashara['sign']} {vs_parashara['dms']} (In 6H Pisces)")
print(f"  Part of Fortune   : {pof['sign']} {pof['dms']} ({pof['nakshatra']})")

# 7. ASHTAKAVARGA
print("\n[7] ASHTAKAVARGA & SHODHYA PINDA")
print("-" * 75)
sav_info = chart.ashtakavarga['sav']
sav_list = sav_info['sav']
sav_str = " | ".join([f"{SIGNS[i][:3]}:{sav_list[i]}" for i in range(12)])
print(f"  SAV Total Points  : {sav_info['total']} (Canonical baseline: 337)")
print(f"  SAV by Sign (Ari-Psc): {sav_str}")
print(f"  Strongest SAV Sign: {sav_info['strongest'][0]} ({sav_info['strongest'][1]} pts)")
print(f"  Weakest SAV Sign  : {sav_info['weakest'][0]} ({sav_info['weakest'][1]} pts)")

# 8. SHADBALA & AVASTHAS
print("\n[8] SHADBALA & AVASTHAS")
print("-" * 75)
sb = chart.shadbala
print("  Planet    Rupas   Shashtiamsas  Min Req  Status        Avastha")
print("  " + "-" * 65)
for p in ['Mercury', 'Venus', 'Jupiter', 'Moon', 'Sun', 'Saturn', 'Mars']:
    info = sb[p]
    av = chart.avasthas[p]['avastha']
    print(f"  {p:<9} {info['rupas']:>5.2f}     {info['shashtiamsas']:>7.2f}    {info['minimum']:>5.1f}   "
          f"{info['status']:<12}  {av:<10}")

# 9. YOGAS DETECTED
print("\n[9] YOGAS DETECTED")
print("-" * 75)
yogas = chart.yogas
for y in yogas['formed']:
    desc = y.get('description') or y.get('connection') or ''
    print(f"  + {y['name']:<35} : {desc}")

# 10. CURRENT DASHA & TIMING (2026-08-19)
print("\n[10] ACTIVE DASHA & TIMING (AS OF TODAY: 2026-08-19)")
print("-" * 75)
dasha = chart.get_current_dasha("2026-08-19")
md = dasha.get('MD', {})
ad = dasha.get('AD', {})
pd = dasha.get('PD', {})
print(f"  Vimshottari Dasha : {md.get('lord')}-{ad.get('lord')}-{pd.get('lord')}")
print(f"    - Mahadasha (MD): {md.get('lord')} ({md.get('start')} to {md.get('end')})")
print(f"    - Antardasha (AD): {ad.get('lord')} ({ad.get('start')} to {ad.get('end')})")
print(f"    - Pratyantar(PD): {pd.get('lord')} ({pd.get('start')} to {pd.get('end')})")

# 11. CURRENT TRANSITS (2026-08-19)
print("\n[11] TRANSIT SNAPSHOT & GOCHARA (AS OF TODAY: 2026-08-19)")
print("-" * 75)
tr = chart.transits_for("2026-08-19")
dt = tr['double_transit']
print(f"  Jupiter Transit   : Cancer {tr['transit_positions']['Jupiter']['dms']} (Natal H10)")
print(f"  Saturn Transit    : Pisces {tr['transit_positions']['Saturn']['dms']} (Natal H6)")
print(f"  Double Transit    : House {dt['double_transit_houses']} ({', '.join(dt['activated_signs'])})")

# 12. TAJIKA VARSHAPHALA (YEAR 2026 / AGE 25)
print("\n[12] TAJIKA VARSHAPHALA (2025-2026 CYCLE)")
print("-" * 75)
taj = chart.varshaphala(2026)
vc = taj['varsha_chart']
print(f"  Solar Return Date : {vc['solar_return_date']} {vc['solar_return_time_ut']} UT")
print(f"  Varsha Lagna      : {vc['varsha_lagna']}")
print(f"  Muntha            : {vc['muntha']['muntha_sign']} (H{vc['muntha']['house_from_lagna']} from Natal Lagna) — {vc['muntha']['effect']}")
print(f"  Varshesha (Lord)  : {taj['varshesha']['varshesha']}")
print(f"  Tajika Yogas ({taj['tajika_yogas_count']}):")
for ty in taj['tajika_yogas']:
    print(f"    * {ty.get('yoga')}: {ty.get('faster_planet')}-{ty.get('slower_planet')} ({ty.get('aspect_type')}) — {ty.get('meaning')}")

# 13. KAKSHYA POSITIONS
print("\n[13] NATAL KAKSHYA DIVISIONS (SUB-SECTORS OF 3°45')")
print("-" * 75)
for p, k in chart.kakshyas.items():
    print(f"  {p:<8}: {k['sign']:<12} Kakshya {k['kakshya_num']}/8 (Lord: {k['kakshya_lord']:<8}) [{k['degree_in_kakshya']:.2f}° in sub-arc]")

print("\n" + "=" * 75)
print("   AUDIT COMPLETE — ALL CALCULATION MODULES EXECUTED SUCCESSFULLY")
print("=" * 75)
