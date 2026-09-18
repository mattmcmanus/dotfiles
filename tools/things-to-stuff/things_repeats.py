"""Decode Things 3 repeat rules.

`TMTask.rt1_recurrenceRule` is an XML property list, not an opaque blob:

    {'fa': 1, 'fu': 256, 'of': [{'wd': 0}], 'ia': 1616889600.0,
     'ed': 64092211200.0, 'rc': 0, 'tp': 1, 'rrv': 4, 'ts': -99}

    fa   frequency amount    "every N ..."
    fu   frequency unit      NSCalendarUnit value, see UNITS
    of   on                  which weekdays / days of month, see below
    ia   first instance      Unix seconds, UTC
    sr   schedule reference  Unix seconds; 0001-01-01 when unset
    ed   end date            Unix seconds; 4001-01-01 means never
    rc   repeat count        0 = unlimited
    tp   type                1 = fixed schedule, 0 = after completion
    rrv  rule version        4 in Things 3.15+
    ts   unknown

The `of` entries are all zero-based, which is the easy thing to get wrong:

    {'wd': 0}            Sunday (weekly rules)
    {'dy': 17}           the 18th (monthly rules)
    {'dy': -1}           the last day of the month
    {'wd': 2, 'wdo': 1}  the 1st Tuesday (monthly rules)
    {'dy': 0, 'mo': 8}   September 1 (yearly rules)

Daily rules carry a meaningless `{'dy': 0}`, which is not reported.

After-completion rules (`tp == 0`) are scheduled from when you tick the task,
yet they still carry an `of` entry. Whether that entry constrains the next
occurrence or merely records where the current one landed is not something
the database says, so it is reported as "anchored to ..." - true under either
reading, and the detail is worth keeping: a "1st Tuesday" or a "September"
anchor cannot be derived from a completion date at all.

Every claim above was checked against 52 real rules covering all four units:
each rule's `ia` lands on exactly the weekday, day-of-month, nth-weekday or
month-and-day its `of` entry predicts. See test_repeats.py.
"""

from __future__ import annotations

import calendar
import plistlib
from datetime import datetime, timezone
from typing import Any

# NSCalendarUnit values. All four confirmed against real rules.
UNITS = {
    16: "day",
    256: "week",
    8: "month",
    4: "year",
}

WEEKDAYS = (
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
)

# Things writes 4001-01-01 when a repeat has no end.
NEVER_ENDS = 64092211200.0


def ordinal(number: int) -> str:
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _date(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(value, timezone.utc).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _weekday(index: int) -> str:
    return WEEKDAYS[index] if 0 <= index < len(WEEKDAYS) else f"weekday {index}"


def describe_on(unit: str | None, entries: Any) -> str:
    """Render the 'of' array for a given unit. Zero-based throughout."""
    entries = [entry for entry in entries or [] if isinstance(entry, dict)]
    if not entries or unit == "day":
        return ""

    if unit == "week":
        return ", ".join(_weekday(e["wd"]) for e in entries if "wd" in e)

    if unit == "month":
        parts: list[str] = []
        for entry in entries:
            if "wdo" in entry and "wd" in entry:
                parts.append(f"the {ordinal(entry['wdo'])} {_weekday(entry['wd'])}")
            elif entry.get("dy") == -1:
                parts.append("the last day")
            elif "dy" in entry:
                parts.append(f"the {ordinal(entry['dy'] + 1)}")
        return ", ".join(parts)

    if unit == "year":
        parts = []
        for entry in entries:
            month = entry.get("mo")
            day = entry.get("dy")
            if month is None or day is None:
                continue
            parts.append(f"{calendar.month_name[month + 1]} {day + 1}")
        return ", ".join(parts)

    return ""


def decode(blob: bytes | None) -> dict[str, Any] | None:
    """Turn a recurrence rule into fields plus a human-readable summary."""
    if not blob:
        return None
    try:
        rule = plistlib.loads(bytes(blob))
    except Exception as error:  # noqa: BLE001 - report, never crash an export
        return {"error": f"could not parse repeat rule: {error}"}
    if not isinstance(rule, dict):
        return {"error": "repeat rule was not a dictionary"}

    amount = rule.get("fa") or 1
    unit_raw = rule.get("fu")
    unit = UNITS.get(unit_raw)
    after_completion = rule.get("tp") == 0

    if unit:
        summary = f"every {unit}" if amount == 1 else f"every {amount} {unit}s"
    else:
        summary = f"every {amount} [unknown unit {unit_raw}]"

    on = describe_on(unit, rule.get("of"))
    if after_completion:
        summary += " after completion"
        if on:
            summary += f", anchored to {on}"
    elif on:
        summary += f" on {on}"

    first = _date(rule.get("ia"))
    if first:
        summary += f", starting {first}"

    end = rule.get("ed")
    count = rule.get("rc") or 0
    if count:
        summary += f", {count} times"
    elif isinstance(end, (int, float)) and end != NEVER_ENDS:
        until = _date(end)
        if until:
            summary += f", until {until}"

    decoded: dict[str, Any] = {
        "summary": summary,
        "interval": amount,
        "unit": unit or f"unknown:{unit_raw}",
        "on": describe_on(unit, rule.get("of")),
        "first_instance": first,
        "from_completion": after_completion,
        "raw": {k: v for k, v in rule.items() if not isinstance(v, bytes)},
    }
    if count:
        decoded["count"] = count
    if isinstance(end, (int, float)) and end != NEVER_ENDS:
        decoded["until"] = _date(end)
    if unit is None:
        decoded["needs_review"] = (
            f"unit {unit_raw} is not in the confirmed table; check this one "
            "against Things and add it to UNITS in things_repeats.py"
        )
    return decoded
