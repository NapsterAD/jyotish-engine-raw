"""Whole-sign mapping: identity, rotation, adjacent houses, cross-module."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.core.constants import SIGNS
from jyotish_engine.core.mapping import (
    sign_to_house, house_to_sign, house_to_sign_index, houses_from,
    house_counted_from, bhavat_bhavam, badhaka_house, badhaka_sign,
    build_house_map,
)
from jyotish_engine.computations.ashtakavarga import calc_sav_by_house
from jyotish_engine.main import JyotishEngine

PASS = FAIL = 0


def check(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {label}" + (f"  {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL  {label}" + (f"  {detail}" if detail else ""))


print("=== identity: house_to_sign_index(sign_to_house(s,L), L) == s ===")
for lagna in range(12):
    for sign in range(12):
        h = sign_to_house(sign, lagna)
        back = house_to_sign_index(h, lagna)
        if back != sign:
            check(f"roundtrip L={lagna} s={sign}", False, f"h={h} back={back}")
            break
    else:
        continue
    break
else:
    check("12×12 roundtrip", True)

print("\n=== golden adjacent houses (12,1,2,3) ===")
# movable / fixed / dual + Aditya Libra
golden = {
    0: (11, 0, 1, 2),   # Aries: Pi, Ar, Ta, Ge
    1: (0, 1, 2, 3),    # Taurus
    2: (1, 2, 3, 4),    # Gemini
    6: (5, 6, 7, 8),    # Libra: Vi, Li, Sc, Sg
}
for lagna, want in golden.items():
    got = tuple(house_to_sign_index(h, lagna) for h in (12, 1, 2, 3))
    names = tuple(SIGNS[i] for i in got)
    check(f"{SIGNS[lagna]} H12/1/2/3", got == want, str(names))

print("\n=== Badhaka by modality ===")
check("Aries movable H11", badhaka_house(0) == 11 and badhaka_sign(0) == "Aquarius")
check("Taurus fixed H9", badhaka_house(1) == 9 and badhaka_sign(1) == "Capricorn")
check("Gemini dual H7", badhaka_house(2) == 7 and badhaka_sign(2) == "Sagittarius")
check("Libra movable H11 Sun", badhaka_house("Libra") == 11 and badhaka_sign("Libra") == "Leo")

print("\n=== house helpers ===")
check("7th from 1 = 7", house_counted_from(1, 7) == 7)
check("7th from 12 = 6", house_counted_from(12, 7) == 6)
check("houses_from(3,1)=3", houses_from(3, 1) == 3)
check("bhavat_bhavam(1)=1", bhavat_bhavam(1) == 1)
check("bhavat_bhavam(7)=1", bhavat_bhavam(7) == 1)
check("bhavat_bhavam(2)=3", bhavat_bhavam(2) == 3)

print("\n=== Aditya: SAV rotation invariant + cross-module ===")
engine = JyotishEngine()
chart = engine.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad",
)
bav = chart.ashtakavarga["bav"]
sav = chart.ashtakavarga["sav"]["sav"]
by_h = chart.ashtakavarga["by_house"]
hm = chart.get_house_map("rashi")

check("sav_by_house set == sav set", sorted(by_h.values()) == sorted(sav))
for h in range(1, 13):
    sign = hm[h]["sign"]
    sidx = house_to_sign_index(h, chart.lagna_index)
    ok = sign == SIGNS[sidx] and by_h[h] == sav[sidx]
    check(f"cross H{h} {sign}", ok, f"map={sign} sav={by_h[h]}")

rot_ok = True
for lagna in range(12):
    rotated = calc_sav_by_house(bav, lagna)
    if sorted(rotated.values()) != sorted(sav):
        rot_ok = False
        check(f"rotation L={SIGNS[lagna]} set", False, str(sorted(rotated.values())))
        break
    for h in range(1, 13):
        if rotated[h] != sav[house_to_sign_index(h, lagna)]:
            rot_ok = False
            check(f"rotation L={SIGNS[lagna]} H{h}", False)
            break
    if not rot_ok:
        break
if rot_ok:
    check("SAV set invariant under all 12 Lagna rotations", True)

# Lagna-independent: planetary longitudes / SAV sign row
check("Libra lagna (Aditya)", chart.lagna_sign == "Libra")
check("SAV Aries still 18 after mapping", sav[0] == 18)
check("H1 Libra SAV 30", by_h[1] == 30)
check("H2 Scorpio SAV 21", by_h[2] == 21)
check("H12 Virgo SAV 25", by_h[12] == 25)

print(f"\nRESULT  PASS={PASS}  FAIL={FAIL}")
if FAIL:
    sys.exit(1)
print("DONE")
