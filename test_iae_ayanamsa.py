import sys
import os
import swisseph as swe

modes = {
    'SIDM_LAHIRI': swe.SIDM_LAHIRI,
    'SIDM_LAHIRI_1940': swe.SIDM_LAHIRI_1940,
    'SIDM_LAHIRI_ICRC': swe.SIDM_LAHIRI_ICRC,
    'SIDM_LAHIRI_VP285': swe.SIDM_LAHIRI_VP285,
    'SIDM_TRUE_CITRA': swe.SIDM_TRUE_CITRA,
}

# IAE Jan 1, 2019 at 5h 29m IST:
# IAE True Ayanamsa = 24° 07' 06.0" = 24.118333°
# IAE Mean Ayanamsa = 24° 07' 21.20" = 24.122556° (at epoch 2019.0)
ut_hour = (5 + 29.0/60.0) - 5.5
jd = swe.julday(2019, 1, 1, ut_hour)

iae_true = 24 + 7/60.0 + 6.0/3600.0
iae_mean = 24 + 7/60.0 + 21.20/3600.0

print(f"IAE 2019 (Jan 1, 2019 5h 29m IST):")
print(f"  IAE True Ayanamsa (incl. nutation) : {iae_true:.6f}° (24° 07' 06.0\")")
print(f"  IAE Mean Ayanamsa (no nutation)    : {iae_mean:.6f}° (24° 07' 21.2\")\n")

for name, mode in modes.items():
    swe.set_sid_mode(mode)
    ay = swe.get_ayanamsa_ut(jd)
    diff_true = (ay - iae_true) * 3600.0
    diff_mean = (ay - iae_mean) * 3600.0
    print(f"  {name:20s}: {ay:.6f}° -> vs Mean: {diff_mean:+.2f}\" | vs True: {diff_true:+.2f}\"")
