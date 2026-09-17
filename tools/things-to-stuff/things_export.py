#!/usr/bin/env python3
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
        "--no-recurring-report",
        action="store_true",
        help="Skip the list of repeating-to-do templates (see README: repeat "
        "rules cannot be exported).",
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


def recurring_templates(filepath: str) -> list[dict[str, Any]]:
    """List repeating to-dos/projects, which things.py filters out entirely.

    Things stores the repeat rule as an opaque blob, so we only report the
    titles and where they live: enough to recreate them by hand.
    """
    query = """
        SELECT TASK.title,
               CASE TASK.type WHEN 0 THEN 'to-do' WHEN 1 THEN 'project'
                              WHEN 2 THEN 'heading' END AS type,
               PROJECT.title AS project_title,
               AREA.title    AS area_title
        FROM TMTask AS TASK
        LEFT OUTER JOIN TMTask PROJECT ON TASK.project = PROJECT.uuid
        LEFT OUTER JOIN TMArea AREA    ON TASK.area = AREA.uuid
        WHERE TASK.rt1_recurrenceRule IS NOT NULL
          AND TASK.trashed = 0
          AND TASK.status = 0
        ORDER BY TASK."index"
    """
    uri = f"file:{filepath}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(query).fetchall()
        except sqlite3.OperationalError as error:
            return [{"error": f"could not read repeat rules: {error}"}]
    return [{k: v for k, v in dict(row).items() if v} for row in rows]


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

    tasks = [task for task in raw if keep(task, statuses, since)]
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

    if not args.no_recurring_report:
        dump["repeating_not_exported"] = recurring_templates(filepath)

    dump["stats"] = {
        "areas": len(areas),
        "projects": len(projects),
        "headings": len(headings),
        "todos": sum(1 for task in tasks if task["type"] == "to-do"),
        "inbox": len(inbox),
        "unparented_todos": len(loose),
        "repeating_not_exported": len(dump.get("repeating_not_exported", [])),
    }
    return dump


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
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
