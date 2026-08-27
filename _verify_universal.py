"""
Smoke-test: the same formulas run on two different natives.
Does not depend on COMBINED lock tables.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.computations.kp import kp_249_index, _KP249_TABLE
from jyotish_engine.computations.graha_state import jaimini_aspect_signs
from jyotish_engine.core.constants import SIGNS, SIGN_MODALITY

engine = JyotishEngine()

# Native A — morning, Libra lagna (historic verification chart)
a = engine.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="A",
)
# Native B — night birth, different place
b = engine.compute(
    date="1985-06-21", time="22:15:00", tz="+05:30",
    lat=28.6139, lon=77.2090, name="B",
)

fails = []


def check(ok, msg):
    if not ok:
        fails.append(msg)
        print("FAIL", msg)
    else:
        print("PASS", msg)


# Two natives must not share a chart
check(a.lagna_sign != b.lagna_sign, f"different lagnas ({a.lagna_sign} vs {b.lagna_sign})")
check(
    abs(a.positions["Sun"]["longitude"] - b.positions["Sun"]["longitude"]) > 1.0,
    "different Sun longitudes",
)

# KP-249 table integrity
check(len(_KP249_TABLE) == 249, f"KP-249 table length {len(_KP249_TABLE)}")
check(kp_249_index(0.0) == 1, "KP-1 at 0°")
check(kp_249_index(359.999) == 249, f"KP-249 at 359.999 got {kp_249_index(359.999)}")
check(1 <= a.kp["planets"]["Lagna"]["kp_249"] <= 249, "A Lagna kp_249 in 1-249")
check(1 <= b.kp["planets"]["Moon"]["kp_249"] <= 249, "B Moon kp_249 in 1-249")

# Regression: A Lagna SSL (known True-Citra triple)
la = a.kp["planets"]["Lagna"]
check(
    (la["sign_lord"], la["star_lord"], la["sub_lord"]) == ("Venus", "Rahu", "Rahu"),
    f"A Lagna triple {la['sign_lord']}/{la['star_lord']}/{la['sub_lord']}",
)

# Panchang
for chart, tag in ((a, "A"), (b, "B")):
    p = chart.panchang
    t = p["tithi"]["number"]
    check(1 <= t <= 30, f"{tag} tithi {t}")
    check(1 <= p["karana"]["number"] <= 60, f"{tag} karana")
    check(1 <= p["yoga"]["number"] <= 27, f"{tag} nithya yoga")
    check(p["vara"]["lord"] in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"),
          f"{tag} vara {p['vara']}")
    check(p["hora"]["hora_lord"] is not None, f"{tag} hora {p['hora']['hora_lord']} k={p['hora']['hora_index']}")
    # tithi self-consistency
    elong = (chart.positions["Moon"]["longitude"] - chart.positions["Sun"]["longitude"]) % 360
    expect = int(elong / 12) + 1
    if expect > 30:
        expect = 30
    check(t == expect, f"{tag} tithi formula {t} vs {expect}")

check(a.panchang["hora"]["is_day_hora"] is True, "A morning birth is day hora")
check(b.panchang["hora"]["is_day_hora"] is False, "B 22:15 is night hora")

# Combustion
for chart, tag in ((a, "A"), (b, "B")):
    c = chart.combustion
    check(c["Sun"]["is_combust"] is False, f"{tag} Sun not combust")
    check(c["Rahu"]["is_combust"] is False, f"{tag} Rahu exempt")
    check(c["Ketu"]["is_combust"] is False, f"{tag} Ketu exempt")
    for pl in ("Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        check("is_combust" in c[pl], f"{tag} {pl} combustion key")

# Yuddha structure
for chart, tag in ((a, "A"), (b, "B")):
    y = chart.yuddha
    check("wars" in y, f"{tag} yuddha wars key")
    for w in y["wars"]:
        check(w["separation"] <= 1.0, f"{tag} yuddha orb {w}")

# Badhaka from THIS lagna
for chart, tag in ((a, "A"), (b, "B")):
    bd = chart.badhaka
    modality = SIGN_MODALITY[chart.lagna_sign]
    expect_h = {"Movable": 11, "Fixed": 9, "Dual": 7}[modality]
    check(bd["house"] == expect_h, f"{tag} badhaka house {bd['house']} vs {expect_h} ({modality})")
    check(bd["lord"] == chart.lordships[expect_h], f"{tag} badhakesh {bd['lord']}")

# Jaimini: every sign aspects exactly 3 signs
for s in SIGNS:
    asp = jaimini_aspect_signs(s)
    check(len(asp) == 3, f"Jaimini {s} aspects {len(asp)} {asp}")
    check(s not in asp, f"Jaimini {s} does not aspect itself")

check(len(a.jaimini_drishti["planets"]["Lagna"]["aspected_signs"]) == 3, "A Lagna Jaimini 3 signs")
check(len(b.jaimini_drishti["planets"]["Moon"]["aspected_signs"]) == 3, "B Moon Jaimini 3 signs")

# Sade-sati: natal Saturn vs natal Moon is a valid call; query date too
sa = a.sade_sati_for("2000-10-06", "07:02:21")
sb = b.sade_sati_for("1985-06-21", "22:15:00")
check("sade_sati" in sa and "phase" in sa, f"A natal sade-sati {sa}")
check("sade_sati" in sb and "phase" in sb, f"B natal sade-sati {sb}")
# Query a date far from both births
sq = a.sade_sati_for("2024-01-01")
check(sq["transit_saturn_sign"] in SIGNS, f"A 2024 Saturn {sq['transit_saturn_sign']}")
check(a.sade_sati_for("2024-01-01")["natal_moon_sign"] != b.sade_sati_for("2024-01-01")["natal_moon_sign"]
      or a.positions["Moon"]["sign"] == b.positions["Moon"]["sign"],
      "sade-sati uses each native's Moon")

# Positions carry latitude (needed for yuddha)
check("latitude" in a.positions["Mars"], "A Mars latitude stored")
check("latitude" in b.positions["Venus"], "B Venus latitude stored")

print()
print(f"A Lagna={a.lagna_sign} tithi={a.panchang['tithi']['full_name']} "
      f"hora={a.panchang['hora']['hora_lord']} badhaka={a.badhaka['lord']} "
      f"kp249L={a.kp['planets']['Lagna']['kp_249']}")
print(f"B Lagna={b.lagna_sign} tithi={b.panchang['tithi']['full_name']} "
      f"hora={b.panchang['hora']['hora_lord']} badhaka={b.badhaka['lord']} "
      f"kp249L={b.kp['planets']['Lagna']['kp_249']}")

if fails:
    print(f"\n{len(fails)} FAIL(s)")
    sys.exit(1)
print("\nALL PASS")
