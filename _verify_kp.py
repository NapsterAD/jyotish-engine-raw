"""Verify KP planet triples and equal-cusp SSL vs COMBINED MASTER §2."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from jyotish_engine.main import JyotishEngine

e = JyotishEngine()
c = e.compute(
    date="2000-10-06", time="07:02:21", tz="+05:30",
    lat=23.797487, lon=86.305251, name="Aditya Prasad",
)

PASS = FAIL = 0

def check(label, got, want):
    global PASS, FAIL
    if got == want:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}  got={got}  want={want}")

# COMBINED: Sign/Star/Sub  (we check star + sub)
exp_planet = {
    "Lagna":   ("Rahu", "Rahu"),
    "Sun":     ("Moon", "Mercury"),
    "Moon":    ("Venus", "Mercury"),
    "Mars":    ("Venus", "Rahu"),
    "Mercury": ("Rahu", "Ketu"),
    "Jupiter": ("Moon", "Saturn"),
    "Venus":   ("Jupiter", "Jupiter"),
    "Saturn":  ("Sun", "Mercury"),
    "Rahu":    ("Jupiter", "Ketu"),
    "Ketu":    ("Venus", "Ketu"),
}

print("=== PLANET STAR / SUB ===")
for p, (star, sub) in exp_planet.items():
    pos = c.positions[p]
    print(f"  INFO {p}: {pos['sign']} {pos.get('sign_lord')} / {pos['nakshatra_lord']} / {pos.get('sub_lord')} / {pos.get('sub_sub_lord')}")
    check(f"{p} star", pos["nakshatra_lord"], star)
    check(f"{p} sub", pos.get("sub_lord"), sub)

print("\n=== EQUAL CUSPS SSL (COMBINED odd=Rahu even=Ketu) ===")
eq = c.kp["equal_cusps"]
exp_eq_sub = {
    1: "Rahu", 2: "Ketu", 3: "Rahu", 4: "Ketu", 5: "Rahu", 6: "Ketu",
    7: "Rahu", 8: "Ketu", 9: "Rahu", 10: "Ketu", 11: "Rahu", 12: "Ketu",
}
exp_eq_star = {
    1: "Rahu", 2: "Saturn", 3: "Ketu", 4: "Sun", 5: "Rahu", 6: "Saturn",
    7: "Ketu", 8: "Sun", 9: "Rahu", 10: "Saturn", 11: "Ketu", 12: "Sun",
}
for h in range(1, 13):
    print(f"  INFO H{h} {eq[h]['sign']} {eq[h]['nakshatra']} star={eq[h]['star_lord']} sub={eq[h]['sub_lord']}")
    check(f"eq H{h} star", eq[h]["star_lord"], exp_eq_star[h])
    check(f"eq H{h} sub", eq[h]["sub_lord"], exp_eq_sub[h])

print("\n=== PLACIDUS 7H CSL ===")
p7 = c.house_cusps["cusps"][7]
print(f"  INFO 7H {p7['sign']} {p7['degree']:.2f} nak={p7['nakshatra']} star={p7['nak_lord']} sub={p7['sub_lord']} ssl={p7.get('sub_sub_lord')}")
check("Placidus 7H star Ketu", p7["nak_lord"], "Ketu")
check("Placidus 7H sub Rahu", p7["sub_lord"], "Rahu")

print("\n=== RP / ABCD 7H ===")
rp = c.kp_ruling_planets()
print("  INFO RP", rp["list"], "nodes", rp["nodes_added"])
sig7 = c.kp_significators(7)
print("  INFO 7H ABCD", {k: sig7[k] for k in "ABCD"}, "CSL", sig7["cusp_sub_lord"], "agents", sig7["agents"])
fr = c.kp_fruitful([2, 7, 11], deny_houses=[1, 6, 10])
print("  INFO marriage fruitful", {h: v for h, v in fr["csl"].items()})

print(f"\n========== PASS={PASS} FAIL={FAIL} ==========")
