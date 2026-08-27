import sys; sys.path.insert(0, '.'); sys.stdout.reconfigure(encoding='utf-8')
from jyotish_engine.main import JyotishEngine
from jyotish_engine.computations.dashas import _vimshottari_balance, _jd_to_date_str

e = JyotishEngine()
c = e.compute(date="2000-10-06", time="07:02:21", tz="+05:30",
              lat=23.797487, lon=86.305251)
moon_long = c.positions["Moon"]["longitude"]
birth_jd = c.positions["_jd"]

lord, balance, nak_idx, remaining_pct = _vimshottari_balance(moon_long)
print(f"Moon longitude: {moon_long:.6f}")
nak = c.positions["Moon"]["nakshatra"]
pada = c.positions["Moon"]["pada"]
print(f"Birth nakshatra: {nak} P{pada}")
print(f"Birth dasha lord: {lord}")
print(f"Remaining pct: {remaining_pct:.4f}%")
print(f"Balance years: {balance:.6f}")
print(f"Balance days: {balance * 365.25:.2f}")
print(f"Birth JD: {birth_jd:.6f}")
print(f"Birth date: {_jd_to_date_str(birth_jd)}")

# List first few MDs
dashas = c.dashas
for md in dashas[:8]:
    print(f"{md['lord']:<8} {md['start_date']} to {md['end_date']}  ({md['duration_years']:.4f} years)")
