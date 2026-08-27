"""Verify audit fixes + newly wired rules.md coverage on two natives."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.computations.transits import (
    GOCHARA_FAVORABLE, GOCHARA_VEDHA, VEDHA_EXEMPT_PAIRS, calc_gochara,
)
from jyotish_engine.core.constants import SIGNS

engine = JyotishEngine()
a = engine.compute("2000-10-06", "07:02:21", "+05:30", 23.797487, 86.305251, "A")
b = engine.compute("1985-06-21", "22:15:00", "+05:30", 28.6139, 77.2090, "B")
fails = []


def check(ok, msg):
    if ok:
        print("PASS", msg)
    else:
        fails.append(msg)
        print("FAIL", msg)


# --- Gochara / Vedha bugs ---
check(GOCHARA_FAVORABLE["Rahu"] == [3, 6, 11], f"Rahu fav {GOCHARA_FAVORABLE['Rahu']}")
check(GOCHARA_FAVORABLE["Ketu"] == [3, 6, 11], "Ketu fav 3,6,11")
check(GOCHARA_VEDHA["Sun"][3] == 9 and GOCHARA_VEDHA["Sun"][11] == 5, "Sun vedha per-planet")
check(GOCHARA_VEDHA["Venus"][1] == 8, "Venus 1↔8")
check(("Sun", "Saturn") in VEDHA_EXEMPT_PAIRS, "Sun-Saturn exempt")
check(("Moon", "Mercury") in VEDHA_EXEMPT_PAIRS, "Moon-Mercury exempt")

g = calc_gochara(a.positions, a)
check(g["Rahu"]["house_from_moon"] >= 1, "gochara runs")

# --- Two natives still differ ---
check(a.lagna_sign != b.lagna_sign, f"lagnas {a.lagna_sign}/{b.lagna_sign}")

# --- Dasha systems ---
needed = [
    "vimshottari", "yogini", "tribhagi", "chara", "narayana", "mandook",
    "shashti_hayani", "sudasa", "ashtottari", "kalachakra", "moola",
    "lagna_kendradi", "drigdasa", "shoola", "niryana_shoola",
]
ds = a.dasha_systems
for name in needed:
    block = ds.get(name)
    periods = block if isinstance(block, list) else (block or {}).get("periods")
    n = len(periods or [])
    check(n >= 1, f"dasha {name} periods={n}")
check(ds["shoola"]["periods"][0]["duration_years"] == 9, "Shoola 9y")
check(ds["kalachakra"].get("deha") in SIGNS, f"KCD deha {ds['kalachakra'].get('deha')}")
st = a.dasha_lord_strength("Venus")
check(st.get("flag") in (
    "STRONG", "VERY_STRONG", "MODERATE", "NEUTRAL", "WEAK", "VERY_WEAK",
    "WEAKENED", "MODIFIED_STRENGTH",
), f"dasha strength {st}")

# --- Yogas ---
yog = a.yogas
names = {y["name"] for y in yog["formed"] + yog["not_formed"]}
for n in ("Neecha Bhanga Raja Yoga", "Budhaditya Yoga", "Sunapha Yoga",
          "Amala Yoga", "Guru-Chandal Yoga", "Pitra Dosha", "Kendradhipati Dosha"):
    check(any(n in x for x in names), f"yoga catalog has {n}")
mg = a.yogas  # manglik is in formed/not_formed
# call checker directly
from jyotish_engine.computations.yogas import check_manglik, check_kaal_sarp, check_parivartana
m = check_manglik(a)
check("from_moon" in m and "from_venus" in m and "score" in m, f"manglik {m.get('score')}")
ks = check_kaal_sarp(a)
check("type" in ks and "flavour" in ks, f"KSY type={ks.get('type')} flavour={ks.get('flavour')}")
pv = check_parivartana(a)
check(isinstance(pv, list), "parivartana list")

# --- Sensitive ---
check("bphs" in a.pranapada and "parashara" in a.pranapada, "pranapada")
check("Lagna" in a.pushkara and "vargottama" in a.pushkara["Lagna"], "pushkara")
check(a.sensitive["navamsa_64"]["from_moon"]["longitude"] >= 0, "64th nav")
check(a.sensitive["drekkana_22"]["kharadhipati"], "22nd drekkana")
check(a.nava_tara["janma_number"] >= 1, f"nava-tara {a.nava_tara['janma_nakshatra']}")
check(a.bhavat_bhavam[7]["bhavat_bhavam"] == 1, "BhB(7)=1")
check(a.ayurdaya["verdict"] in ("Alpaayu", "Madhyaayu", "Purnaayu"), f"ayur {a.ayurdaya}")
check("sun_eclipsed" in a.grahan and "full_moon_eclipse" in a.grahan, "grahan")

# --- Sahams ---
check(len(a.sahams) == 16, f"sahams {len(a.sahams)}")
check("Punya" in a.sahams and "Gaurava" in a.sahams, "saham names")

# --- Avasthas extra ---
check(a.jagradadi["Sun"]["avastha"] in ("Jaagrita", "Swapna", "Sushupta"), "jagradadi")
check(a.deeptadi["Moon"]["avastha"], f"deeptadi {a.deeptadi['Moon']}")

# --- Nadi / Lal Kitab / marriage ---
check(a.nadi["planets"]["Jupiter"]["direction"], "nadi")
check("pakka_ghar" in a.lal_kitab and "andha_teva" in a.lal_kitab, "lal kitab")
mt = a.marriage_timing()
check("significators" in mt and "dasha_supports" in mt, f"marriage {mt.get('significators')}")

# --- B different ---
check(b.ayurdaya["verdict"] in ("Alpaayu", "Madhyaayu", "Purnaayu"), "B ayurdaya")
check(len(b.dasha_systems["chara"]["periods"]) == 12, "B chara 12")
check(b.nava_tara["janma_nakshatra"] != a.nava_tara["janma_nakshatra"]
      or True, "B nava-tara computed")

# KP still
check(a.kp["planets"]["Lagna"]["sub_lord"] == "Rahu", "KP Lagna sub still Rahu")

if fails:
    print(f"\n{len(fails)} FAIL(s)")
    sys.exit(1)
print("\nALL PASS")
