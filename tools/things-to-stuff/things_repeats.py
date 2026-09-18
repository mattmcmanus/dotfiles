"""Decode Things 3 repeat rules.

`TMTask.rt1_recurrenceRule` is an XML property list, not an opaque blob. A
weekly rule looks like this:

    {'fa': 1, 'fu': 256, 'of': [{'wd': 0}], 'ia': 1616889600.0,
     'ed': 64092211200.0, 'rc': 0, 'tp': 1, 'rrv': 4, 'ts': -99}

Field meanings, as far as they have been confirmed:

    fa   frequency amount    "every N ..."          confirmed
    fu   frequency unit      NSCalendarUnit value   see UNITS
    of   on                  [{'wd': 0}] = Sunday   confirmed
    ia   first instance      Unix seconds, UTC      confirmed
    sr   schedule reference  Unix seconds, UTC      likely rule anchor
    ed   end date            Unix seconds, UTC      4001-01-01 = never ends
    rc   repeat count        0 = unlimited          likely
    tp   type                1 = fixed schedule     likely; 0 = after completion
    rrv  rule version        4 in Things 3.15+
    ts   unknown

UNITS maps `fu` onto Apple's documented NSCalendarUnit constants, which is
where these values come from (256 = NSCalendarUnitWeekday, and the sample
above is indeed a weekly-by-weekday rule). Only 256 has been seen in a real
database here, so anything else is reported with its raw value rather than
guessed at: run `things_export.py --explain-repeats` against your own
database and check the descriptions against what Things shows you.
"""

from __future__ import annotations

import plistlib
from datetime import datetime, timezone
from typing import Any

# NSCalendarUnit values. 256 (Weekday) is confirmed against a real rule.
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


def _date(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(value, timezone.utc).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _on(entries: Any) -> list[str]:
    """Render the 'of' array: which weekdays or days-of-month a rule fires on."""
    out: list[str] = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        if "wd" in entry:
            index = entry["wd"]
            name = WEEKDAYS[index] if 0 <= index < len(WEEKDAYS) else f"weekday {index}"
            ordinal = entry.get("wdo")
            out.append(f"the {ordinal}. {name}" if ordinal else name)
        elif "dy" in entry:
            out.append(f"day {entry['dy']}")
        else:
            out.append(str(entry))
    return out


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
    on = _on(rule.get("of"))

    if unit:
        every = f"every {unit}" if amount == 1 else f"every {amount} {unit}s"
    else:
        every = f"every {amount} [unknown unit {unit_raw}]"

    summary = every
    if on:
        summary += " on " + ", ".join(on)
    if rule.get("tp") == 0:
        summary += ", counted from completion"

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
        "on": on,
        "first_instance": first,
        "from_completion": rule.get("tp") == 0,
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
