"""
Civil birth-data normalisation. Called by BirthChart before any Swiss call.

Rejects garbage instead of silently substituting IST / Aditya / 0°.
"""

from datetime import datetime, timedelta, timezone

try:
    import tzdata  # noqa: F401  — IANA database; required on Windows for ZoneInfo
except ImportError:
    tzdata = None

AYANAMSHA_ALIASES = {
    "lahiri": "lahiri",
    "true_chitrapaksha": "lahiri",
    "true_citra": "lahiri",
    "chitrapaksha": "lahiri",
    "lahiri_official": "lahiri_official",
    "raman": "raman",
    "krishnamurti": "krishnamurti",
    "kp": "krishnamurti",
    "yukteshwar": "yukteshwar",
    "yukteshvara": "yukteshwar",
}

# Explicit civil aliases only — never used as a silent fallback.
TZ_ALIASES = {
    "UTC": 0.0,
    "UT": 0.0,
    "GMT": 0.0,
    "Z": 0.0,
    "IST": 5.5,
    "LMT": None,  # not a fixed offset
}


class BirthDataError(ValueError):
    """Invalid civil birth inputs."""


def _parse_date(date):
    text = str(date).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    raise BirthDataError(f"date must be YYYY-MM-DD, got {date!r}")


def _parse_time(time):
    text = str(time).strip().replace(".", ":")
    parts = text.split(":")
    if len(parts) < 2:
        raise BirthDataError(f"time must be HH:MM or HH:MM:SS, got {time!r}")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(float(parts[2])) if len(parts) > 2 else 0
    except (TypeError, ValueError) as exc:
        raise BirthDataError(f"time must be HH:MM or HH:MM:SS, got {time!r}") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise BirthDataError(f"time out of range: {time!r}")
    return hour, minute, second


def parse_timezone(tz, date_str=None, time_str=None):
    """
    Return offset hours east of UT.

    Accepts +HH:MM, +HHMM, ±H, UTC/Z/GMT, IST, a float, or an IANA name
    (America/New_York) using the offset *on that civil date* (DST-aware).
    Unparseable values raise — they do not become IST.
    """
    if tz is None or tz == "":
        raise BirthDataError("timezone is required (e.g. +05:30, UTC, America/New_York)")
    if isinstance(tz, (int, float)):
        off = float(tz)
        if not -14.0 <= off <= 14.0:
            raise BirthDataError(f"timezone hours out of range: {tz}")
        return off

    text = str(tz).strip()
    key = text.upper().replace(" ", "")
    if key in TZ_ALIASES:
        if TZ_ALIASES[key] is None:
            raise BirthDataError(f"timezone {tz!r} is not a fixed offset")
        return TZ_ALIASES[key]

    import re
    m = re.search(r"([+-])(\d{1,2})(?::(\d{2}))?", text)
    if m:
        sign = -1 if m.group(1) == "-" else 1
        hours = int(m.group(2))
        minutes = int(m.group(3) or 0)
        if hours > 14 or minutes > 59:
            raise BirthDataError(f"timezone out of range: {tz!r}")
        return sign * (hours + minutes / 60.0)

    # IANA zone (America/New_York). Windows ZoneInfo needs the tzdata package.
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    except ImportError as exc:
        raise BirthDataError(
            "IANA timezones require Python 3.9+ zoneinfo"
        ) from exc

    def _zone(name):
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError as exc:
            if tzdata is None:
                raise BirthDataError(
                    f"IANA timezone {tz!r} needs the tzdata package on this OS "
                    f"(pip install tzdata), or pass a numeric offset like +05:30"
                ) from exc
            try:
                return ZoneInfo(name)
            except Exception as exc2:
                raise BirthDataError(
                    f"unrecognised timezone {tz!r}; use +HH:MM, UTC, IST, or IANA "
                    f"(e.g. America/New_York)"
                ) from exc2

    try:
        d = _parse_date(date_str or "2000-01-01")
        h, mi, s = _parse_time(time_str or "12:00:00")
        local = datetime(d.year, d.month, d.day, h, mi, s, tzinfo=_zone(text))
        off = local.utcoffset()
        if off is None:
            raise BirthDataError(f"timezone {tz!r} has no UTC offset")
        return off.total_seconds() / 3600.0
    except BirthDataError:
        raise
    except Exception as exc:
        raise BirthDataError(
            f"unrecognised timezone {tz!r}; use +HH:MM, UTC, IST, or IANA "
            f"(e.g. America/New_York)"
        ) from exc


def normalize_birth_inputs(date, time, tz, lat, lon, ayanamsha="lahiri"):
    """Return cleaned (date_iso, time_hms, tz_hours, lat, lon, ayanamsha)."""
    d = _parse_date(date)
    h, mi, s = _parse_time(time)
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError) as exc:
        raise BirthDataError(f"lat/lon must be numbers, got {lat!r}, {lon!r}") from exc
    if not -90.0 <= lat_f <= 90.0:
        raise BirthDataError(f"latitude must be in [-90, 90], got {lat_f}")
    if not -180.0 <= lon_f <= 180.0:
        raise BirthDataError(f"longitude must be in [-180, 180], got {lon_f}")

    aya = str(ayanamsha or "lahiri").strip().lower()
    if aya not in AYANAMSHA_ALIASES:
        raise BirthDataError(
            f"unknown ayanamsha {ayanamsha!r}; valid: {sorted(set(AYANAMSHA_ALIASES.values()))}"
        )
    tz_hours = parse_timezone(tz, d.isoformat(), f"{h:02d}:{mi:02d}:{s:02d}")
    return (
        d.isoformat(),
        f"{h:02d}:{mi:02d}:{s:02d}",
        tz_hours,
        lat_f,
        lon_f,
        AYANAMSHA_ALIASES[aya],
    )
