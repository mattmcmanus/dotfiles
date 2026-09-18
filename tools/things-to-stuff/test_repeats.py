#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Checks for the Things repeat-rule decoder.

Two kinds of check:

1. Fixed expectations for one rule of each shape.
2. A self-consistency sweep: for every rule, the first instance Things
   generated (`ia`) must land on exactly the weekday, day-of-month, nth
   weekday, or month-and-day that the `of` entry claims. That is what pins
   down the zero-based indexing without having to trust anyone's memory.

The rules below are the structures of 52 real repeats, with titles removed.

    python3 test_repeats.py
"""

from __future__ import annotations

import calendar
import plistlib
import sys
from datetime import datetime, timezone

from things_repeats import decode

BASE = {"ed": 64092211200.0, "rc": 0, "rrv": 4, "ts": 0}


def rule(**kwargs) -> bytes:
    return plistlib.dumps({**BASE, **kwargs})


CASES = [
    # daily: the {'dy': 0} is filler and must not be reported
    (rule(fa=5, fu=16, ia=1739750400.0, of=[{"dy": 0}], tp=1),
     "every 5 days, starting 2025-02-17"),
    # weekly, fixed schedule: wd 0 = Sunday
    (rule(fa=2, fu=256, ia=1746662400.0, of=[{"wd": 4}], tp=1),
     "every 2 weeks on Thursday, starting 2025-05-08"),
    (rule(fa=16, fu=256, ia=1738454400.0, of=[{"wd": 0}], tp=1),
     "every 16 weeks on Sunday, starting 2025-02-02"),
    # after completion: the anchor is reported without claiming it constrains
    (rule(fa=1, fu=256, ia=1763856000.0, of=[{"wd": 0}], tp=0),
     "every week after completion, anchored to Sunday, starting 2025-11-23"),
    (rule(fa=1, fu=256, ia=1738540800.0,
          of=[{"wd": 1}, {"wd": 2}, {"wd": 3}, {"wd": 4}, {"wd": 5}], tp=0),
     "every week after completion, anchored to Monday, Tuesday, Wednesday, "
     "Thursday, Friday, starting 2025-02-03"),
    # monthly: dy is zero-based
    (rule(fa=1, fu=8, ia=1781740800.0, of=[{"dy": 17}], tp=1),
     "every month on the 18th, starting 2026-06-18"),
    (rule(fa=3, fu=8, ia=1768694400.0, of=[{"dy": 17}], tp=1),
     "every 3 months on the 17th... placeholder"),  # replaced below
    # monthly, last day of month
    (rule(fa=3, fu=8, ia=1738281600.0, of=[{"dy": -1}], tp=0),
     "every 3 months after completion, anchored to the last day, "
     "starting 2025-01-31"),
    # monthly, nth weekday
    (rule(fa=1, fu=8, ia=1783382400.0, of=[{"wd": 2, "wdo": 1}], tp=1),
     "every month on the 1st Tuesday, starting 2026-07-07"),
    # yearly: mo and dy both zero-based
    (rule(fa=1, fu=4, ia=1764460800.0, of=[{"dy": 29, "mo": 10}], tp=1),
     "every year on November 30, starting 2025-11-30"),
    (rule(fa=1, fu=4, ia=1738454400.0, of=[{"dy": 1, "mo": 1}], tp=1),
     "every year on February 2, starting 2025-02-02"),
    # an unknown unit is reported, never guessed
    (rule(fa=1, fu=999, ia=1738454400.0, of=[], tp=1),
     "every 1 [unknown unit 999], starting 2025-02-02"),
]
CASES[6] = (
    rule(fa=3, fu=8, ia=1768694400.0, of=[{"dy": 17}], tp=1),
    "every 3 months on the 18th, starting 2026-01-18",
)

# (fa, fu, of, ia, tp) for 52 real rules, titles removed.
REAL = [
    (1, 8, [{"dy": 17}], 1781740800.0, 1), (2, 256, [{"wd": 3}], 1762905600.0, 0),
    (2, 256, [{"wd": 2}], 1763424000.0, 0), (2, 256, [{"wd": 2}], 1762819200.0, 0),
    (2, 256, [{"wd": 1}], 1763337600.0, 0), (1, 256, [{"wd": 2}], 1762819200.0, 0),
    (1, 256, [{"wd": 1}], 1762732800.0, 0),
    (1, 4, [{"dy": 0, "mo": 8}], 1788220800.0, 0),
    (1, 8, [{"dy": 20}], 1771632000.0, 0), (1, 8, [{"dy": 0}], 1764547200.0, 0),
    (1, 256, [{"wd": 1}], 1763337600.0, 0), (1, 256, [{"wd": 2}], 1768867200.0, 0),
    (1, 256, [{"wd": 1}], 1772409600.0, 0), (1, 8, [{"dy": 23}], 1766534400.0, 1),
    (2, 256, [{"wd": 4}], 1765411200.0, 1),
    (1, 4, [{"dy": 29, "mo": 10}], 1764460800.0, 1),
    (1, 256, [{"wd": 3}], 1775001600.0, 0),
    (1, 4, [{"dy": 6, "mo": 0}], 1767744000.0, 0),
    (1, 4, [{"dy": 0, "mo": 0}], 1767225600.0, 0),
    (2, 256, [{"wd": 2}], 1774915200.0, 1), (3, 8, [{"dy": 0}], 1743465600.0, 0),
    (1, 4, [{"dy": 0, "mo": 8}], 1756684800.0, 0),
    (9, 8, [{"dy": 13}], 1765670400.0, 1), (2, 256, [{"wd": 4}], 1747872000.0, 1),
    (5, 16, [{"dy": 0}], 1739750400.0, 1), (1, 256, [{"wd": 0}], 1763856000.0, 0),
    (1, 8, [{"dy": 0}], 1740787200.0, 0), (9, 8, [{"dy": 14}], 1739577600.0, 1),
    (3, 8, [{"dy": 17}], 1768694400.0, 1), (3, 8, [{"dy": -1}], 1738281600.0, 0),
    (1, 256, [{"wd": 0}], 1738454400.0, 0), (1, 256, [{"wd": 6}], 1738972800.0, 0),
    (6, 8, [{"dy": 21}], 1750550400.0, 1), (1, 256, [{"wd": 6}], 1763769600.0, 0),
    (2, 256, [{"wd": 0}], 1738454400.0, 1), (3, 8, [{"dy": 0}], 1740787200.0, 0),
    (3, 8, [{"dy": 1}], 1738454400.0, 1), (16, 256, [{"wd": 0}], 1738454400.0, 1),
    (1, 4, [{"dy": 1, "mo": 1}], 1738454400.0, 1),
    (3, 256, [{"wd": 0}], 1738454400.0, 1), (1, 8, [{"dy": 6}], 1772841600.0, 0),
    (1, 8, [{"dy": 0}], 1772323200.0, 0),
    (1, 256, [{"wd": 1}, {"wd": 2}, {"wd": 3}, {"wd": 4}, {"wd": 5}],
     1738540800.0, 0),
    (2, 256, [{"wd": 4}], 1746662400.0, 1), (3, 8, [{"dy": 6}], 1783382400.0, 0),
    (5, 256, [{"wd": 0}], 1738454400.0, 1),
    (1, 4, [{"dy": 6, "mo": 9}], 1791331200.0, 0),
    (2, 256, [{"wd": 0}], 1738454400.0, 1), (1, 256, [{"wd": 1}], 1759708800.0, 1),
    (1, 8, [{"wd": 2, "wdo": 1}], 1783382400.0, 0),
    (3, 8, [{"dy": 0}], 1743465600.0, 0), (1, 8, [{"dy": 0}], 1769904000.0, 0),
]


def check_summaries() -> list[str]:
    failures = []
    for blob, expected in CASES:
        got = (decode(blob) or {}).get("summary")
        if got != expected:
            failures.append(f"  expected {expected!r}\n  got      {got!r}")
    return failures


def check_consistency() -> list[str]:
    """Each rule's first instance must match what its `of` entry predicts."""
    failures = []
    for fa, fu, of, ia, _tp in REAL:
        date = datetime.fromtimestamp(ia, timezone.utc).date()
        entry = of[0]
        weekday = (date.weekday() + 1) % 7  # Python Monday=0 -> Things Sunday=0
        if fu == 256:
            if weekday not in [e["wd"] for e in of]:
                failures.append(f"  weekly {of} but {date} is weekday {weekday}")
        elif fu == 8 and "wdo" in entry:
            nth = (date.day - 1) // 7 + 1
            if (weekday, nth) != (entry["wd"], entry["wdo"]):
                failures.append(f"  nth-weekday {entry} but {date} is {nth}/{weekday}")
        elif fu == 8 and entry.get("dy") == -1:
            if date.day != calendar.monthrange(date.year, date.month)[1]:
                failures.append(f"  dy=-1 but {date} is not the last day")
        elif fu == 8:
            if date.day != entry["dy"] + 1:
                failures.append(f"  monthly dy={entry['dy']} but {date} is day {date.day}")
        elif fu == 4:
            if (date.month, date.day) != (entry["mo"] + 1, entry["dy"] + 1):
                failures.append(f"  yearly {entry} but {date}")
    return failures


def main() -> int:
    failures = check_summaries() + check_consistency()
    if failures:
        print(f"FAILED ({len(failures)}):")
        print("\n".join(failures))
        return 1
    print(f"ok - {len(CASES)} summaries, {len(REAL)} rules self-consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
