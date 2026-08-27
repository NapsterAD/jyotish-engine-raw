"""
dashas.py — Dasha systems: Vimshottari (up to 5 levels), Yogini (both formulas).
100% offline — pure arithmetic from Moon's sidereal longitude.
"""

from datetime import datetime, timedelta
from ..core.constants import (
    NAKSHATRAS, NAKSHATRA_SPAN,
    VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS, VIMSHOTTARI_TOTAL,
    YOGINI_NAMES, YOGINI_PLANETS, YOGINI_YEARS, YOGINI_TOTAL,
)

# Sidereal year used for dasha spans (rules.md §4.1).
SIDEREAL_YEAR_DAYS = 365.256364


# ═══════════════════════════════════════════
# JULIAN DAY ↔ DATETIME HELPERS
# ═══════════════════════════════════════════

def _jd_to_datetime(jd):
    """Convert Julian Day to Python datetime (UT)."""
    # J2000.0 = JD 2451545.0 = 2000-01-01 12:00:00 UT
    j2000 = 2451545.0
    ref = datetime(2000, 1, 1, 12, 0, 0)
    delta = jd - j2000
    return ref + timedelta(days=delta)


def _datetime_to_jd(dt):
    """Convert Python datetime to Julian Day (UT)."""
    j2000 = 2451545.0
    ref = datetime(2000, 1, 1, 12, 0, 0)
    delta = (dt - ref).total_seconds() / 86400.0
    return j2000 + delta


def _jd_to_date_str(jd):
    """Convert JD to date string YYYY-MM-DD."""
    dt = _jd_to_datetime(jd)
    return dt.strftime("%Y-%m-%d")


def _date_str_to_jd(date_str):
    """Convert YYYY-MM-DD to JD."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return _datetime_to_jd(dt)


# ═══════════════════════════════════════════
# VIMSHOTTARI DASHA — BALANCE AT BIRTH
# ═══════════════════════════════════════════

def _vimshottari_balance(moon_longitude):
    """
    Calculate the balance of Vimshottari Mahadasha at birth.
    
    Args:
        moon_longitude: sidereal longitude of Moon (0-360)
        
    Returns:
        (birth_dasha_lord, balance_years, nak_index, remaining_pct)
    """
    longitude = moon_longitude % 360.0
    nak_idx = int(longitude / NAKSHATRA_SPAN)
    nak_idx = min(nak_idx, 26)

    nak = NAKSHATRAS[nak_idx]
    degree_in_nak = longitude - (nak_idx * NAKSHATRA_SPAN)

    # Remaining fraction of nakshatra
    remaining_frac = 1.0 - (degree_in_nak / NAKSHATRA_SPAN)

    # The dasha lord = nakshatra lord
    birth_lord = nak["lord"]

    # Balance = remaining fraction * total years of that lord's dasha
    balance_years = remaining_frac * VIMSHOTTARI_YEARS[birth_lord]

    return birth_lord, balance_years, nak_idx, remaining_frac * 100


# ═══════════════════════════════════════════
# VIMSHOTTARI — MAHADASHA + ANTARDASHA + PRATYANTARDASHA
# ═══════════════════════════════════════════

def calc_vimshottari(moon_longitude, birth_jd, levels=3):
    """
    Calculate Vimshottari dasha periods.
    
    Args:
        moon_longitude: sidereal longitude of Moon
        birth_jd: Julian Day of birth
        levels: 1=MD only, 2=MD+AD, 3=MD+AD+PD, 4=+SD, 5=+PAD
        
    Returns:
        list of dasha periods, each with:
            lord, start_jd, end_jd, start_date, end_date, duration_years,
            level ("MD"/"AD"/"PD"/"SD"/"PAD"), sub_periods (if deeper levels)
    """
    birth_lord, balance_years, _, _ = _vimshottari_balance(moon_longitude)

    # Find position of birth lord in the Vimshottari sequence
    lord_idx = VIMSHOTTARI_ORDER.index(birth_lord)

    # Build Mahadasha sequence
    periods = []
    current_jd = birth_jd

    for cycle in range(2):  # 2 cycles = 240 years (more than enough)
        for i in range(9):
            md_lord_idx = (lord_idx + i + cycle * 9) % 9
            md_lord = VIMSHOTTARI_ORDER[md_lord_idx]
            full_years = VIMSHOTTARI_YEARS[md_lord]

            # First period uses balance
            if cycle == 0 and i == 0:
                years = balance_years
            else:
                years = full_years

            duration_days = years * SIDEREAL_YEAR_DAYS
            end_jd = current_jd + duration_days

            period = {
                "lord": md_lord,
                "level": "MD",
                "start_jd": current_jd,
                "end_jd": end_jd,
                "start_date": _jd_to_date_str(current_jd),
                "end_date": _jd_to_date_str(end_jd),
                "duration_years": round(years, 4),
                "full_years": full_years,
            }

            if levels >= 2:
                period["sub_periods"] = _calc_sub_periods(
                    md_lord, current_jd, end_jd, years, 2, levels
                )

            periods.append(period)
            current_jd = end_jd

            # Stop after reasonable coverage (120+ years from birth)
            if current_jd - birth_jd > 120 * SIDEREAL_YEAR_DAYS:
                return periods

    return periods


def _calc_sub_periods(parent_lord, start_jd, end_jd, parent_years, current_level, max_level):
    """
    Recursively calculate sub-periods within a dasha period.
    
    The sub-period sequence starts from the parent lord and cycles through
    the Vimshottari order. Each sub-period's duration is proportional to
    its lord's years relative to the total cycle (120 years).
    
    Level 2 = AD (Antardasha/Bhukti)
    Level 3 = PD (Pratyantardasha)
    Level 4 = SD (Sookshma dasha)
    Level 5 = PAD (Prana dasha)
    """
    level_names = {2: "AD", 3: "PD", 4: "SD", 5: "PAD"}
    level_name = level_names.get(current_level, f"L{current_level}")

    parent_idx = VIMSHOTTARI_ORDER.index(parent_lord)
    total_duration = end_jd - start_jd
    sub_periods = []
    current_jd = start_jd

    for i in range(9):
        sub_lord_idx = (parent_idx + i) % 9
        sub_lord = VIMSHOTTARI_ORDER[sub_lord_idx]

        # Duration proportional to sub-lord's years / total cycle
        proportion = VIMSHOTTARI_YEARS[sub_lord] / VIMSHOTTARI_TOTAL
        sub_duration = total_duration * proportion
        sub_end_jd = current_jd + sub_duration

        period = {
            "lord": sub_lord,
            "level": level_name,
            "start_jd": current_jd,
            "end_jd": sub_end_jd,
            "start_date": _jd_to_date_str(current_jd),
            "end_date": _jd_to_date_str(sub_end_jd),
            "duration_days": round(sub_duration, 2),
        }

        if current_level < max_level:
            sub_years = sub_duration / SIDEREAL_YEAR_DAYS
            period["sub_periods"] = _calc_sub_periods(
                sub_lord, current_jd, sub_end_jd, sub_years,
                current_level + 1, max_level
            )

        sub_periods.append(period)
        current_jd = sub_end_jd

    return sub_periods


def calc_vimshottari_5_levels(moon_longitude, birth_jd):
    """Convenience: calculate Vimshottari with all 5 levels (MD/AD/PD/SD/PAD)."""
    return calc_vimshottari(moon_longitude, birth_jd, levels=5)


# ═══════════════════════════════════════════
# CURRENT DASHA FINDER
# ═══════════════════════════════════════════

def get_current_dasha(dasha_table, target_date=None):
    """
    Find the active dasha period for a given date.
    
    Args:
        dasha_table: list of periods from calc_vimshottari()
        target_date: "YYYY-MM-DD" or None for today
        
    Returns:
        dict with current MD, AD, PD lords and dates
    """
    if target_date is None:
        target_jd = _datetime_to_jd(datetime.utcnow())
    else:
        target_jd = _date_str_to_jd(target_date)

    result = {}

    # Find current MD
    for md in dasha_table:
        if md["start_jd"] <= target_jd < md["end_jd"]:
            result["MD"] = {
                "lord": md["lord"],
                "start": md["start_date"],
                "end": md["end_date"],
            }

            # Find current AD
            if "sub_periods" in md:
                for ad in md["sub_periods"]:
                    if ad["start_jd"] <= target_jd < ad["end_jd"]:
                        result["AD"] = {
                            "lord": ad["lord"],
                            "start": ad["start_date"],
                            "end": ad["end_date"],
                        }

                        # Find current PD
                        if "sub_periods" in ad:
                            for pd in ad["sub_periods"]:
                                if pd["start_jd"] <= target_jd < pd["end_jd"]:
                                    result["PD"] = {
                                        "lord": pd["lord"],
                                        "start": pd["start_date"],
                                        "end": pd["end_date"],
                                    }

                                    # Find current SD
                                    if "sub_periods" in pd:
                                        for sd in pd["sub_periods"]:
                                            if sd["start_jd"] <= target_jd < sd["end_jd"]:
                                                result["SD"] = {
                                                    "lord": sd["lord"],
                                                    "start": sd["start_date"],
                                                    "end": sd["end_date"],
                                                }
                                                if "sub_periods" in sd:
                                                    for pad in sd["sub_periods"]:
                                                        if pad["start_jd"] <= target_jd < pad["end_jd"]:
                                                            result["PAD"] = {
                                                                "lord": pad["lord"],
                                                                "start": pad["start_date"],
                                                                "end": pad["end_date"],
                                                            }
                                                            break
                                                break
                                    break
                        break
            break

    # Build summary string
    parts = []
    for level in ["MD", "AD", "PD", "SD", "PAD"]:
        if level in result:
            parts.append(result[level]["lord"])
    result["summary"] = "-".join(parts) if parts else "Not found"

    return result


# ═══════════════════════════════════════════
# YOGINI DASHA
# ═══════════════════════════════════════════

def _yogini_balance(moon_longitude, formula="B"):
    """
    Calculate balance of Yogini Dasha at birth.
    
    Formula A: (Nakshatra # + 3) mod 8 → Yogini index  (some traditions)
    Formula B: (Nakshatra # + 3) mod 8 → Yogini index  (same formula, different traditions
               interpret #s differently; we use Shastric standard: 1-indexed nak)
    
    The canonical formula used in ad2.pdf:
        Yogini index = (nak_num + 3) % 8
        where nak_num is 1-based (Ashwini=1...Revati=27)
        
    Args:
        moon_longitude: sidereal longitude of Moon
        formula: "A" or "B" (both use same underlying formula per Shastric standard)
        
    Returns:
        (yogini_index, balance_years, yogini_name, yogini_planet)
    """
    longitude = moon_longitude % 360.0
    nak_idx = int(longitude / NAKSHATRA_SPAN)
    nak_idx = min(nak_idx, 26)
    nak_num = nak_idx + 1  # 1-indexed

    degree_in_nak = longitude - (nak_idx * NAKSHATRA_SPAN)
    remaining_frac = 1.0 - (degree_in_nak / NAKSHATRA_SPAN)

    # Canonical shastric formula: (nak_num + 3) / 8, take remainder
    # Remainder 1=Mangala(idx 0), 2=Pingala(idx 1), ... 7=Siddha(idx 6), 0→8=Sankata(idx 7)
    # For 0-based indexing: (nak_num + 2) % 8
    yogini_idx = (nak_num + 2) % 8  # 0-7

    yogini_name = YOGINI_NAMES[yogini_idx]
    yogini_planet = YOGINI_PLANETS[yogini_idx]
    yogini_years = YOGINI_YEARS[yogini_idx]

    balance_years = remaining_frac * yogini_years

    return yogini_idx, balance_years, yogini_name, yogini_planet


def calc_yogini(moon_longitude, birth_jd, formula="B"):
    """
    Calculate Yogini Dasha periods.
    
    Args:
        moon_longitude: sidereal longitude of Moon
        birth_jd: Julian Day of birth
        formula: "A" or "B" (standard shastric formula)
        
    Returns:
        list of Yogini dasha periods (major + sub)
    """
    yogini_idx, balance_years, birth_yogini, birth_planet = _yogini_balance(
        moon_longitude, formula
    )

    periods = []
    current_jd = birth_jd

    for cycle in range(4):  # 4 cycles of 36 years = 144 years
        for i in range(8):
            y_idx = (yogini_idx + i + cycle * 8) % 8
            y_name = YOGINI_NAMES[y_idx]
            y_planet = YOGINI_PLANETS[y_idx]
            y_years = YOGINI_YEARS[y_idx]

            # First period uses balance
            if cycle == 0 and i == 0:
                years = balance_years
            else:
                years = y_years

            duration_days = years * SIDEREAL_YEAR_DAYS
            end_jd = current_jd + duration_days

            period = {
                "yogini": y_name,
                "planet": y_planet,
                "level": "Major",
                "years": y_years,
                "balance_used": round(years, 4) if (cycle == 0 and i == 0) else y_years,
                "start_jd": current_jd,
                "end_jd": end_jd,
                "start_date": _jd_to_date_str(current_jd),
                "end_date": _jd_to_date_str(end_jd),
            }

            # Sub-periods within each Yogini major period
            sub_periods = []
            sub_jd = current_jd
            sub_total_duration = end_jd - current_jd

            for j in range(8):
                sub_y_idx = (y_idx + j) % 8
                sub_y_name = YOGINI_NAMES[sub_y_idx]
                sub_y_planet = YOGINI_PLANETS[sub_y_idx]
                sub_y_years = YOGINI_YEARS[sub_y_idx]

                # Proportion: sub_years / total_yogini_cycle (36)
                proportion = sub_y_years / YOGINI_TOTAL
                sub_duration = sub_total_duration * proportion
                sub_end_jd = sub_jd + sub_duration

                sub_periods.append({
                    "yogini": sub_y_name,
                    "planet": sub_y_planet,
                    "level": "Sub",
                    "start_jd": sub_jd,
                    "end_jd": sub_end_jd,
                    "start_date": _jd_to_date_str(sub_jd),
                    "end_date": _jd_to_date_str(sub_end_jd),
                    "duration_days": round(sub_duration, 2),
                })
                sub_jd = sub_end_jd

            period["sub_periods"] = sub_periods
            periods.append(period)
            current_jd = end_jd

            # Stop after 120+ years
            if current_jd - birth_jd > 120 * SIDEREAL_YEAR_DAYS:
                return periods

    return periods


# ═══════════════════════════════════════════
# DASHA SUMMARY
# ═══════════════════════════════════════════

def format_dasha_table(dasha_periods, system="Vimshottari"):
    """
    Format dasha periods as a readable text table.
    
    Args:
        dasha_periods: output from calc_vimshottari() or calc_yogini()
        system: "Vimshottari" or "Yogini" (affects column labels)
        
    Returns:
        formatted string
    """
    lines = []
    lines.append(f"═══ {system} Dasha Table ═══\n")

    if system == "Vimshottari":
        lines.append(f"{'MD Lord':<10} {'Start':<12} {'End':<12} {'Years':<8}")
        lines.append("─" * 45)

        for md in dasha_periods:
            lines.append(
                f"{md['lord']:<10} {md['start_date']:<12} {md['end_date']:<12} "
                f"{md['duration_years']:<8.2f}"
            )

            if "sub_periods" in md:
                for ad in md["sub_periods"]:
                    lines.append(
                        f"  {md['lord']}-{ad['lord']:<8} "
                        f"{ad['start_date']:<12} {ad['end_date']:<12} "
                        f"{ad['duration_days']:<.0f}d"
                    )

    elif system == "Yogini":
        lines.append(f"{'Yogini':<12} {'Planet':<10} {'Start':<12} {'End':<12} {'Years':<6}")
        lines.append("─" * 55)

        for period in dasha_periods:
            lines.append(
                f"{period['yogini']:<12} {period['planet']:<10} "
                f"{period['start_date']:<12} {period['end_date']:<12} "
                f"{period['balance_used']:<6}"
            )

    return "\n".join(lines)
