import sys
import swisseph as swe

# IAE Jan 1, 2020 5h 29m IST (UT = -0.016667h, or Dec 31, 2019 23:59:00 UT)
jd = swe.julday(2020, 1, 1, (5 + 29.0/60.0) - 5.5)

iae_planets_sayana = {
    "Sun": (280, 0, 31),
    "Moon": (346, 7, 44),
    "Mercury": (274, 22, 55),
    "Venus": (314, 24, 31),
    "Mars": (238, 23, 3),
    "Jupiter": (276, 40, 13),
    "Saturn": (291, 23, 42),
}

planet_ids = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
}

print("=== TROPICAL (SAYANA) APPARENT LONGITUDE vs IAE 2019 (Page 434) ===")
print("Date: Jan 1, 2020 at 5h 29m IST\n")

for p, (d, m, s) in iae_planets_sayana.items():
    iae_lon = d + m/60.0 + s/3600.0
    # Calculate tropical apparent geocentric longitude
    res, flags = swe.calc_ut(jd, planet_ids[p], swe.FLG_SWIEPH | swe.FLG_SPEED)
    swe_lon = res[0]
    diff_sec = (swe_lon - iae_lon) * 3600.0
    
    deg, rem = divmod(swe_lon, 1)
    m_val, rem = divmod(rem*60, 1)
    s_val = rem * 60
    
    print(f"  {p:8s}: IAE={d:03d}° {m:02d}' {s:02d}\" ({iae_lon:.4f}°) | Swe={int(deg):03d}° {int(m_val):02d}' {s_val:04.1f}\" ({swe_lon:.4f}°) -> Delta: {diff_sec:+.2f}\"")
