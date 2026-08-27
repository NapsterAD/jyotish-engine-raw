"""Any-native robustness: valid charts compute; garbage raises; no IST leak."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import jyotish_engine.core._compat

from jyotish_engine.main import JyotishEngine
from jyotish_engine.core.inputs import BirthDataError, parse_timezone, normalize_birth_inputs

engine = JyotishEngine()
PASS = FAIL = 0


def check(ok, msg, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print("PASS", msg, detail)
    else:
        FAIL += 1
        print("FAIL", msg, detail)


def must_raise(fn, msg):
    try:
        fn()
        check(False, msg, "did not raise")
    except (BirthDataError, ValueError):
        check(True, msg)


print("=== timezone ===")
check(abs(parse_timezone("+05:30") - 5.5) < 1e-9, "+05:30")
check(abs(parse_timezone("IST (+5:30)") - 5.5) < 1e-9, "IST (+5:30)")
check(abs(parse_timezone("UTC") - 0.0) < 1e-9, "UTC")
check(abs(parse_timezone("-05:00") + 5.0) < 1e-9, "-05:00")
check(abs(parse_timezone("America/New_York", "1992-03-15", "03:40:00") + 5.0) < 1e-9, "NY IANA EST")
check(abs(parse_timezone("America/New_York", "1992-07-15", "12:00:00") + 4.0) < 1e-9, "NY IANA EDT")
check(abs(parse_timezone("Asia/Kolkata", "2000-10-06", "07:02:21") - 5.5) < 1e-9, "Asia/Kolkata")
must_raise(lambda: parse_timezone("not-a-zone"), "junk tz raises")
must_raise(lambda: parse_timezone(""), "empty tz raises")

print("=== input rejects ===")
must_raise(lambda: normalize_birth_inputs("2000-13-01", "07:00:00", "+00:00", 0, 0), "bad month")
must_raise(lambda: normalize_birth_inputs("2000-10-06", "25:00:00", "+00:00", 0, 0), "bad hour")
must_raise(lambda: normalize_birth_inputs("2000-10-06", "07:00:00", "+00:00", 95, 0), "lat 95")
must_raise(lambda: normalize_birth_inputs("2000-10-06", "07:00:00", "+00:00", 0, 200), "lon 200")
must_raise(lambda: normalize_birth_inputs("2000-10-06", "07:00:00", "+00:00", 0, 0, "foobar"), "bad ayanamsha")

print("=== any-native compute ===")
a = engine.compute("2000-10-06", "07:02:21", "+05:30", 23.797487, 86.305251, "A")
b = engine.compute("1985-06-21", "22:15:00", "+05:30", 28.6139, 77.2090, "B")
c = engine.compute("1992-03-15", "03:40:00", "-05:00", 40.7128, -74.0060, "NY")
d = engine.compute("1978-12-01", "14:00:00", "-03:00", -33.4489, -70.6693, "SCL")
e = engine.compute("2001-06-21", "12:00:00", "+00:00", 78.2, 15.6, "Svalbard")
f = engine.compute("1969-07-20", "20:17:00", "UTC", 1.0, 10.0, "UTC-alias")
g = engine.compute("2000-10-06", "07:02", "+05:30", "23.797487", "86.305251", "str-coords")

check(a.lagna_sign == "Libra", "A still Libra", a.lagna_sign)
check(a.lagna_sign != b.lagna_sign, "A≠B lagna", f"{a.lagna_sign}/{b.lagna_sign}")
check(c.lagna_sign != a.lagna_sign or abs(c.positions["Moon"]["longitude"] - a.positions["Moon"]["longitude"]) > 1,
      "NY chart not a silent IST clone")
check("Lagna" in d.positions and "Moon" in d.positions, "south-hemisphere positions")
check(len(e.house_cusps.get("cusps") or {}) == 12, "polar 12 cusps")
check(e.house_cusps.get("house_system") in ("P", "E"), "polar house system tagged", e.house_cusps.get("house_system"))
ss = e.sunrise_sunset or {}
check(ss.get("polar_estimated") is True, "Svalbard polar_estimated")
check(
    abs((ss.get("sunset_jd") or 0) - (ss.get("sunrise_jd") or 0)) > 0.6,
    "polar rise/set searched adjacent days (not fake noon±6h)",
    f"dt={abs((ss.get('sunset_jd') or 0)-(ss.get('sunrise_jd') or 0)):.2f}d mode={ss.get('polar_mode')}",
)
w = engine.compute("2001-12-21", "12:00:00", "+00:00", 78.2, 15.6, "Svalbard-winter")
check(w.sunrise_sunset.get("polar_estimated") is True, "winter polar_estimated")
check(w.sunrise_sunset.get("polar_mode") == "night", "winter polar night", w.sunrise_sunset.get("polar_mode"))
check(w.sunrise_sunset.get("is_day_birth") is False, "winter noon is night at 78N")
ny_iana = engine.compute("1992-03-15", "03:40:00", "America/New_York", 40.7128, -74.0060, "NY-IANA")
check(abs(ny_iana.positions["_tz_offset"] + 5.0) < 1e-9, "compute IANA America/New_York EST")
check(f.positions["_tz_offset"] == 0.0, "UTC offset 0")
check(g.lagna_sign == a.lagna_sign, "HH:MM + string lat/lon")
check(a.ashtakavarga["sav"]["total"] == 337, "A SAV 337")
check(b.ashtakavarga["sav"]["total"] == 337, "B SAV 337")
check(sorted(b.ashtakavarga["by_house"].values()) == sorted(b.ashtakavarga["sav"]["sav"]),
      "B sav_by_house is a rotation of sav")
check(a.badhaka["house"] == 11, "A movable badhaka 11")
check(b.panchang["hora"]["is_day_hora"] is False, "B night hora")

print("=== compute rejects ===")
must_raise(lambda: engine.compute("2000-10-06", "07:02:21", "xyz", 0, 0), "compute junk tz")
must_raise(lambda: engine.compute("2000-10-06", "07:02:21", "+05:30", 91, 0), "compute lat 91")

print(f"\nRESULT PASS={PASS} FAIL={FAIL}")
if FAIL:
    sys.exit(1)
print("DONE")
