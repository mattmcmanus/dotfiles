#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["things.py"]
# ///
"""Dump a Things 3 database to a normalised JSON file.

Read-only. Talks to the local Things SQLite database through things.py
(https://github.com/thingsapi/things.py); the Things app does not need to be
running, but quit it first if you want to be sure the database is flushed.

    pip install things.py
    ./things_export.py --output things-dump.json

The JSON is the hand-off format consumed by stuff_import.py. It is deliberately
close to the Things data model (areas > projects > headings > to-dos >
checklist items) so that all mapping decisions live in the importer.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any

import things_repeats

try:
    import things
except ImportError:  # pragma: no cover - guidance only
    sys.exit("things.py is not installed. Run: pip install things.py")


STATUSES = ("incomplete", "completed", "canceled")

# Columns lifted from a task row, in the order we want them in the JSON.
TASK_FIELDS = (
    "uuid",
    "title",
    "notes",
    "status",
    "start",
    "start_date",
    "reminder_time",
    "deadline",
    "stop_date",
    "created",
    "modified",
    "index",
    "today_index",
    "tags",
    "repeat",
    "repeating_template",
    "from_repeat",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a Things 3 database to JSON.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--database",
        default=os.environ.get("THINGSDB"),
        help="Path to 'main.sqlite'. Defaults to $THINGSDB, then the standard "
        "Things location.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Where to write the JSON dump. '-' writes to stdout.",
    )
    parser.add_argument(
        "--include-completed",
        action="store_true",
        help="Include completed to-dos and projects (your Logbook).",
    )
    parser.add_argument(
        "--include-canceled",
        action="store_true",
        help="Include canceled to-dos and projects.",
    )
    parser.add_argument(
        "--completed-since",
        metavar="YYYY-MM-DD",
        help="With --include-completed, only keep items completed on or after "
        "this date.",
    )
    parser.add_argument(
        "--include-trashed",
        action="store_true",
        help="Include items sitting in the Things trash.",
    )
    parser.add_argument(
        "--no-repeats",
        action="store_true",
        help="Skip repeating to-dos entirely.",
    )
    parser.add_argument(
        "--explain-repeats",
        action="store_true",
        help="Print each repeating to-do and its decoded rule, then exit. Use "
        "this to check the decoding against what Things shows you.",
    )
    return parser.parse_args(argv)


def database_path(explicit: str | None) -> str:
    if explicit:
        return os.path.expanduser(explicit)
    return things.database.Database().filepath


def wanted_statuses(args: argparse.Namespace) -> set[str]:
    statuses = {"incomplete"}
    if args.include_completed:
        statuses.add("completed")
    if args.include_canceled:
        statuses.add("canceled")
    return statuses


def keep(task: dict[str, Any], statuses: set[str], completed_since: str | None) -> bool:
    if task.get("status") not in statuses:
        return False
    if completed_since and task.get("status") in ("completed", "canceled"):
        stop = (task.get("stop_date") or "")[:10]
        if not stop or stop < completed_since:
            return False
    return True


def slim(task: dict[str, Any]) -> dict[str, Any]:
    """Keep the fields we care about, drop the empty ones."""
    out: dict[str, Any] = {}
    for field in TASK_FIELDS:
        value = task.get(field)
        if value in (None, "", [], False):
            continue
        out[field] = value
    return out


def checklist_for(uuid: str, database: Any) -> list[dict[str, str]]:
    items = database.get_checklist_items(uuid)
    return [
        {"title": item["title"], "status": item["status"]}
        for item in items
        if item.get("title")
    ]


def things_date(value: Any) -> str | None:
    """Decode a Things date integer (YYYYYYYYYYYMMMMDDDDD0000000 in binary).

    Done here rather than through things.py's SQL helper, whose bit mask
    truncates out-of-range years: a repeating template stores 4001-01-01 as
    "no deadline", and that helper renders it as 1953-01-01. Years outside a
    plausible range are treated as the sentinel they are.
    """
    if not isinstance(value, int) or value <= 0:
        return None
    packed = value >> 7
    year, month, day = packed >> 9, (packed >> 5) & 0xF, packed & 0x1F
    if not 1900 <= year <= 2100 or not 1 <= month <= 12 or not 1 <= day <= 31:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def repeat_instances(filepath: str) -> dict[str, str]:
    """Map each generated instance back to the template that spawned it.

    Things materialises the next occurrence of a repeating to-do as an ordinary
    task carrying `rt1_repeatingTemplate`. Without this link the template and
    its live instance both import, as two tasks with the same name.
    """
    uri = f"file:{filepath}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        try:
            rows = connection.execute(
                "SELECT uuid, rt1_repeatingTemplate FROM TMTask "
                "WHERE rt1_repeatingTemplate IS NOT NULL"
            ).fetchall()
        except sqlite3.OperationalError:
            return {}
    return {uuid: template for uuid, template in rows}


def repeating_tasks(filepath: str) -> list[dict[str, Any]]:
    """Read repeating to-dos, which things.py filters out of every query.

    things.py hardcodes `rt1_recurrenceRule IS NULL` into its WHERE clause, so
    the templates are invisible to the normal API. They are ordinary rows
    otherwise, and their repeat rule is a readable plist - see
    things_repeats.py. Returned in the same shape as a things.py task dict so
    they can join the tree like anything else.
    """
    query = """
        SELECT TASK.uuid,
               TASK.title,
               TASK.notes,
               CASE TASK.type WHEN 0 THEN 'to-do' WHEN 1 THEN 'project'
                              WHEN 2 THEN 'heading' END AS type,
               CASE TASK.status WHEN 0 THEN 'incomplete' WHEN 2 THEN 'canceled'
                                WHEN 3 THEN 'completed' END AS status,
               CASE TASK.start WHEN 0 THEN 'Inbox' WHEN 1 THEN 'Anytime'
                               WHEN 2 THEN 'Someday' END AS start,
               TASK.area,
               AREA.title AS area_title,
               TASK.project,
               PROJECT.title AS project_title,
               TASK.heading,
               HEADING.title AS heading_title,
               TASK."index",
               TASK.startDate AS start_date,
               TASK.deadline AS deadline,
               TASK.rt1_recurrenceRule AS rule,
               TASK.rt1_instanceCreationPaused AS paused
        FROM TMTask AS TASK
        LEFT OUTER JOIN TMTask PROJECT ON TASK.project = PROJECT.uuid
        LEFT OUTER JOIN TMTask HEADING ON TASK.heading = HEADING.uuid
        LEFT OUTER JOIN TMArea AREA    ON TASK.area = AREA.uuid
        WHERE TASK.rt1_recurrenceRule IS NOT NULL
          AND TASK.trashed = 0
        ORDER BY TASK."index"
    """
    uri = f"file:{filepath}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        try:
            rows = [dict(row) for row in connection.execute(query)]
        except sqlite3.OperationalError as error:
            print(f"WARNING could not read repeat rules: {error}", file=sys.stderr)
            return []

    out: list[dict[str, Any]] = []
    for row in rows:
        repeat = things_repeats.decode(row.pop("rule", None))
        paused = row.pop("paused", 0)
        if repeat and paused:
            repeat["paused"] = True
        row["start_date"] = things_date(row.get("start_date"))
        row["deadline"] = things_date(row.get("deadline"))
        row["repeat"] = repeat
        row["repeating_template"] = True
        # The template itself carries no start date; the rule says when the
        # next one lands.
        if not row.get("start_date") and repeat:
            row["start_date"] = repeat.get("first_instance")
        out.append(row)
    return out


def build(args: argparse.Namespace) -> dict[str, Any]:
    filepath = database_path(args.database)
    database = things.database.Database(filepath=filepath)
    statuses = wanted_statuses(args)
    since = args.completed_since

    trashed = None if args.include_trashed else False
    raw = things.tasks(
        status=None,
        type=None,
        trashed=trashed,
        context_trashed=None if args.include_trashed else False,
        include_items=False,
        database=database,
    )

    repeating = [] if args.no_repeats else repeating_tasks(filepath)
    for task in repeating:
        if task.get("checklist") is None:
            task["checklist"] = bool(database.get_checklist_items(task["uuid"]))
        if not task.get("tags"):
            task["tags"] = database.get_tags(task=task["uuid"])

    instances = {} if args.no_repeats else repeat_instances(filepath)
    for task in raw:
        template = instances.get(task["uuid"])
        if template:
            task["from_repeat"] = template

    tasks = [task for task in raw + repeating if keep(task, statuses, since)]
    by_uuid = {task["uuid"]: task for task in tasks}

    areas: dict[str, dict[str, Any]] = {}
    for area in things.areas(database=database):
        areas[area["uuid"]] = {
            "uuid": area["uuid"],
            "title": area["title"],
            "tags": area.get("tags") or [],
            "projects": [],
            "todos": [],
        }

    projects: dict[str, dict[str, Any]] = {}
    headings: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if task["type"] == "project":
            entry = slim(task)
            if task.get("area"):
                entry["area"] = task["area"]
                entry["area_title"] = task.get("area_title")
            entry["headings"] = []
            entry["todos"] = []
            projects[task["uuid"]] = entry
        elif task["type"] == "heading":
            headings[task["uuid"]] = {
                "uuid": task["uuid"],
                "title": task["title"],
                "index": task.get("index"),
                "project": task.get("project"),
                "todos": [],
            }

    orphans: list[dict[str, Any]] = []
    for task in tasks:
        if task["type"] != "to-do":
            continue
        todo = slim(task)
        if task.get("checklist"):
            todo["checklist"] = checklist_for(task["uuid"], database)

        heading_uuid = task.get("heading")
        project_uuid = task.get("project")
        area_uuid = task.get("area")

        if heading_uuid and heading_uuid in headings:
            headings[heading_uuid]["todos"].append(todo)
        elif project_uuid and project_uuid in projects:
            projects[project_uuid]["todos"].append(todo)
        elif area_uuid and area_uuid in areas:
            areas[area_uuid]["todos"].append(todo)
        elif heading_uuid or project_uuid:
            # Parent exists in Things but was filtered out (e.g. a completed
            # project while exporting incomplete only). Keep the to-do rather
            # than silently dropping it.
            parent = by_uuid.get(heading_uuid or project_uuid or "")
            todo["orphaned_from"] = parent["title"] if parent else None
            orphans.append(todo)
        else:
            orphans.append(todo)

    for heading in headings.values():
        project = projects.get(heading.get("project") or "")
        if project is not None:
            project["headings"].append(heading)
        elif heading["todos"]:
            orphans.extend(heading["todos"])

    loose_projects: list[dict[str, Any]] = []
    for project in projects.values():
        project["headings"].sort(key=lambda item: item.get("index") or 0)
        area = areas.get(project.get("area") or "")
        if area is not None:
            area["projects"].append(project)
        else:
            loose_projects.append(project)

    inbox = [todo for todo in orphans if todo.get("start") == "Inbox"]
    loose = [todo for todo in orphans if todo.get("start") != "Inbox"]

    dump: dict[str, Any] = {
        "schema": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "database": filepath,
            "things_database_version": database.get_version(),
            "options": {
                "include_completed": args.include_completed,
                "include_canceled": args.include_canceled,
                "completed_since": since,
                "include_trashed": args.include_trashed,
            },
        },
        "areas": list(areas.values()),
        "projects": loose_projects,
        "inbox": inbox,
        "todos": loose,
        "tags": [tag["title"] for tag in things.tags(database=database)],
    }

    dump["stats"] = {
        "areas": len(areas),
        "projects": len(projects),
        "headings": len(headings),
        "todos": sum(1 for task in tasks if task["type"] == "to-do"),
        "inbox": len(inbox),
        "unparented_todos": len(loose),
        "repeating": len(repeating),
        "repeats_needing_review": sum(
            1
            for task in repeating
            if (task.get("repeat") or {}).get("needs_review")
            or (task.get("repeat") or {}).get("error")
        ),
    }
    return dump


def explain_repeats(filepath: str) -> int:
    rows = repeating_tasks(filepath)
    if not rows:
        print("No repeating to-dos found.")
        return 0
    for row in rows:
        repeat = row.get("repeat") or {}
        where = row.get("project_title") or row.get("area_title") or "-"
        print(f"{row['title']}  [{where}]")
        print(f"    {repeat.get('summary') or repeat.get('error')}")
        if repeat.get("needs_review"):
            print(f"    REVIEW: {repeat['needs_review']}")
        print(f"    raw: {repeat.get('raw')}")
    print(
        f"\n{len(rows)} repeating to-do(s). Check these against Things; if a "
        "summary is wrong, fix UNITS in things_repeats.py."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.explain_repeats:
        return explain_repeats(database_path(args.database))
    dump = build(args)
    text = json.dumps(dump, indent=2, ensure_ascii=False)
    if args.output == "-":
        print(text)
    else:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
        stats = ", ".join(f"{k}: {v}" for k, v in dump["stats"].items())
        print(f"Wrote {args.output} ({stats})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
