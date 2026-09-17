#!/usr/bin/env python3
"""Turn a Things export (see things_export.py) into Stuff CLI commands.

Stuff has no importer, so this walks the exported tree and renders one CLI
invocation per space / list / task / subtask. The exact command surface lives
in a JSON profile (profiles/stuff.json) rather than in this file: check the
profile against `stuff --help` once, edit it, and the whole migration follows.

    ./stuff_import.py things-dump.json                  # dry run, prints commands
    ./stuff_import.py things-dump.json --script run.sh  # save them for review
    ./stuff_import.py things-dump.json --execute        # actually create things

--execute keeps a ledger (--state) mapping Things uuid -> created Stuff id, so
an interrupted run resumes instead of duplicating.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Iterator

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROFILE = os.path.join(HERE, "profiles", "stuff.json")

PLACEHOLDER = re.compile(r"\{(\w+)\}")
VAR_TOKEN = re.compile(r"'?__VAR__(\w+)__'?")
DEFAULT_ID_FILTER = "grep -oE '[0-9A-Za-z_-]{6,}' | tail -1"


def var_name(ref: str) -> str:
    return "id_" + re.sub(r"\W", "_", ref)


@dataclass
class Op:
    """One CLI invocation to make."""

    kind: str  # space | list | task | subtask
    ref: str  # Things uuid, used as the ledger key
    title: str
    context: dict[str, str] = field(default_factory=dict)
    parents: dict[str, str] = field(default_factory=dict)  # context key -> ref
    complete: bool = False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render/run Stuff CLI commands from a Things export.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("dump", help="JSON file written by things_export.py")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help="CLI profile JSON")
    parser.add_argument(
        "--script", help="Write the rendered commands to this shell script"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the commands. Without this the script only prints them.",
    )
    parser.add_argument(
        "--state",
        default="stuff-import-ledger.json",
        help="Ledger of already-created items, for resuming a run. "
        'Pass "" to ignore it.',
    )
    parser.add_argument(
        "--headings",
        choices=("prefix", "task", "ignore"),
        default="prefix",
        help="Things headings: prefix the to-do title, become a parent task, "
        "or be dropped.",
    )
    parser.add_argument(
        "--checklists",
        choices=("subtask", "notes", "skip"),
        default="subtask",
        help="Checklist items: separate subtasks, appended to notes, or dropped.",
    )
    parser.add_argument(
        "--tags",
        choices=("native", "notes", "skip"),
        default="native",
        help="Things tags: native tag flag, appended to notes, or dropped.",
    )
    parser.add_argument(
        "--completed",
        choices=("skip", "include"),
        default="skip",
        help="What to do with completed/canceled items present in the dump.",
    )
    parser.add_argument(
        "--stamp-source",
        action="store_true",
        help="Append the originating Things uuid to each item's notes.",
    )
    parser.add_argument(
        "--limit", type=int, help="Only emit the first N commands (smoke tests)."
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Seconds to wait between commands when executing.",
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------------
# Walking the export
# --------------------------------------------------------------------------


def note_lines(todo: dict[str, Any], args: argparse.Namespace) -> list[str]:
    extra: list[str] = []
    if args.tags == "notes" and todo.get("tags"):
        extra.append("Tags: " + ", ".join(todo["tags"]))
    if args.checklists == "notes" and todo.get("checklist"):
        for item in todo["checklist"]:
            mark = "x" if item["status"] == "completed" else " "
            extra.append(f"- [{mark}] {item['title']}")
    if args.stamp_source:
        extra.append(f"Things: {todo['uuid']}")
    return extra


def context_for(item: dict[str, Any], args: argparse.Namespace) -> dict[str, str]:
    notes = [item["notes"]] if item.get("notes") else []
    notes += note_lines(item, args)
    when = ""
    if item.get("start_date"):
        when = item["start_date"]
    elif item.get("start") == "Someday":
        when = "someday"
    elif item.get("start") == "Anytime":
        when = "anytime"

    context = {
        "title": item.get("title") or "(untitled)",
        "notes": "\n".join(notes),
        "deadline": item.get("deadline") or "",
        "start_date": item.get("start_date") or "",
        "when": when,
        "status": item.get("status") or "",
    }
    if args.tags == "native" and item.get("tags"):
        context["tags"] = ",".join(item["tags"])
        context["tag"] = item["tags"][0]
    return context


def is_done(item: dict[str, Any]) -> bool:
    return item.get("status") in ("completed", "canceled")


def walk(dump: dict[str, Any], args: argparse.Namespace) -> Iterator[Op]:
    def emit_todo(
        todo: dict[str, Any], parents: dict[str, str], title_prefix: str = ""
    ) -> Iterator[Op]:
        if is_done(todo) and args.completed == "skip":
            return
        context = context_for(todo, args)
        if title_prefix:
            context["title"] = f"{title_prefix}{context['title']}"
        yield Op(
            kind="task",
            ref=todo["uuid"],
            title=context["title"],
            context=context,
            parents=dict(parents),
            complete=is_done(todo),
        )
        if args.checklists == "subtask":
            for index, item in enumerate(todo.get("checklist") or []):
                if item["status"] != "incomplete" and args.completed == "skip":
                    continue
                yield Op(
                    kind="subtask",
                    ref=f"{todo['uuid']}#{index}",
                    title=item["title"],
                    context={"title": item["title"], "notes": ""},
                    parents={"parent_id": todo["uuid"]},
                    complete=item["status"] != "incomplete",
                )

    def emit_project(project: dict[str, Any], parents: dict[str, str]) -> Iterator[Op]:
        if is_done(project) and args.completed == "skip":
            return
        yield Op(
            kind="list",
            ref=project["uuid"],
            title=project["title"],
            context=context_for(project, args),
            parents=dict(parents),
            complete=is_done(project),
        )
        child = dict(parents)
        child["list_id"] = project["uuid"]
        child.pop("space_id", None)
        for todo in project.get("todos") or []:
            yield from emit_todo(todo, child)
        for heading in project.get("headings") or []:
            if args.headings == "task":
                yield Op(
                    kind="task",
                    ref=heading["uuid"],
                    title=heading["title"],
                    context={"title": heading["title"], "notes": ""},
                    parents=dict(child),
                )
                for todo in heading.get("todos") or []:
                    yield from emit_todo(
                        todo, {"parent_id": heading["uuid"]}
                    )
            else:
                prefix = "" if args.headings == "ignore" else f"{heading['title']}: "
                for todo in heading.get("todos") or []:
                    yield from emit_todo(todo, child, title_prefix=prefix)

    for area in dump.get("areas") or []:
        yield Op(
            kind="space",
            ref=area["uuid"],
            title=area["title"],
            context={"title": area["title"], "notes": ""},
        )
        parents = {"space_id": area["uuid"]}
        for project in area.get("projects") or []:
            yield from emit_project(project, parents)
        for todo in area.get("todos") or []:
            yield from emit_todo(todo, parents)

    for project in dump.get("projects") or []:
        yield from emit_project(project, {})

    for todo in dump.get("inbox") or []:
        yield from emit_todo(todo, {})

    for todo in dump.get("todos") or []:
        yield from emit_todo(todo, {})


# --------------------------------------------------------------------------
# Rendering against the profile
# --------------------------------------------------------------------------


class Renderer:
    def __init__(self, profile: dict[str, Any]):
        self.profile = profile
        self.binary = profile.get("binary", "stuff")
        self.global_args = profile.get("global_args") or []
        self.commands = profile.get("commands") or {}
        self.when_map = profile.get("when_map") or {}
        self.id_pattern = re.compile(profile.get("id_pattern", r"([\w-]{6,})"))

    def fill(self, template: str, context: dict[str, str]) -> str | None:
        """Substitute {placeholders}; return None if any is empty."""
        missing = False

        def replace(match: re.Match[str]) -> str:
            nonlocal missing
            value = context.get(match.group(1), "")
            if not value:
                missing = True
            return value

        out = PLACEHOLDER.sub(replace, template)
        return None if missing else out

    def render(self, op: Op, context: dict[str, str]) -> tuple[list[str], list[str]]:
        spec = self.commands.get(op.kind)
        if spec is None:
            raise KeyError(f"profile has no command for {op.kind!r}")
        context = dict(context)
        if context.get("when") in self.when_map:
            context["when"] = self.when_map[context["when"]]

        argv = [self.binary, *self.global_args]
        for piece in spec.get("args") or []:
            filled = self.fill(piece, context)
            argv.append(filled if filled is not None else "")

        dropped: list[str] = []
        for key, option in (spec.get("options") or {}).items():
            if not context.get(key):
                continue
            rendered = [self.fill(piece, context) for piece in option]
            if any(piece is None for piece in rendered):
                dropped.append(key)
                continue
            argv.extend(piece for piece in rendered if piece is not None)

        # Anything the export carries but the profile has no flag for.
        for key in ("notes", "deadline", "when", "tags"):
            if context.get(key) and key not in (spec.get("options") or {}):
                dropped.append(key)
        return argv, dropped

    @property
    def id_filter(self) -> str:
        return self.profile.get("script_id_filter") or DEFAULT_ID_FILTER

    def captures_id(self, kind: str) -> bool:
        return bool((self.commands.get(kind) or {}).get("capture_id"))

    def complete_argv(self, kind: str, item_id: str) -> list[str] | None:
        spec = self.commands.get(f"complete_{kind}") or self.commands.get("complete")
        if not spec:
            return None
        argv = [self.binary, *self.global_args]
        for piece in spec.get("args") or []:
            argv.append(self.fill(piece, {"id": item_id}) or "")
        return argv


# --------------------------------------------------------------------------
# Running
# --------------------------------------------------------------------------


def load_ledger(path: str) -> dict[str, Any]:
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def save_ledger(path: str, ledger: dict[str, Any]) -> None:
    if not path:
        return
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(ledger, handle, indent=2)


def run(argv: list[str], renderer: Renderer) -> str:
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"{shlex.join(argv)}\n  exit {result.returncode}: "
            f"{(result.stderr or result.stdout).strip()}"
        )
    output = (result.stdout or "").strip()
    match = renderer.id_pattern.search(output)
    return match.group(1) if match else ""


def script_line(op: Op, renderer: Renderer, ledger: dict[str, Any]) -> str:
    """Same command, but wired up with shell variables for parent ids."""
    context = dict(op.context)
    for key, ref in op.parents.items():
        known = ledger.get(ref)
        context[key] = known["id"] if known else f"__VAR__{var_name(ref)}__"
    command, _ = renderer.render(op, context)
    line = VAR_TOKEN.sub(r'"$\1"', shlex.join(command))
    if renderer.captures_id(op.kind):
        line = f"{var_name(op.ref)}=$({line} | {renderer.id_filter})"
    return line


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    with open(args.dump, encoding="utf-8") as handle:
        dump = json.load(handle)
    with open(args.profile, encoding="utf-8") as handle:
        renderer = Renderer(json.load(handle))

    # Loaded in both modes: a dry run after a partial import then shows
    # only what is left. Pass --state "" to always see the full plan.
    ledger = load_ledger(args.state)
    script: list[str] = [
        "#!/usr/bin/env bash",
        "# Generated by stuff_import.py. Review before running.",
        "# Parent ids are captured from stdout with:",
        f"#   {renderer.id_filter}",
        "# Edit that (script_id_filter in the profile) if your CLI prints",
        "# something else.",
        "set -euo pipefail",
        "",
    ]
    counts = {"space": 0, "list": 0, "task": 0, "subtask": 0}
    skipped = 0
    dropped_fields: dict[str, int] = {}

    ops = list(walk(dump, args))
    if args.limit:
        ops = ops[: args.limit]

    for op in ops:
        if op.ref in ledger:
            skipped += 1
            continue

        context = dict(op.context)
        for key, ref in op.parents.items():
            known = ledger.get(ref)
            context[key] = known["id"] if known else f"<id:{ref}>"

        command, dropped = renderer.render(op, context)
        for key in dropped:
            dropped_fields[key] = dropped_fields.get(key, 0) + 1
        counts[op.kind] = counts.get(op.kind, 0) + 1

        if not args.execute:
            print(shlex.join(command))
            if args.script:
                script.append(script_line(op, renderer, ledger))
            continue

        try:
            item_id = run(command, renderer)
        except RuntimeError as error:
            print(f"FAILED {error}", file=sys.stderr)
            save_ledger(args.state, ledger)
            return 1

        if not item_id and renderer.captures_id(op.kind):
            print(
                f"WARNING no id captured for {op.kind} {op.title!r}; children "
                "will be unparented. Check id_pattern in the profile.",
                file=sys.stderr,
            )
        ledger[op.ref] = {"id": item_id, "kind": op.kind, "title": op.title}
        save_ledger(args.state, ledger)
        if op.complete and item_id:
            finish = renderer.complete_argv(op.kind, item_id)
            if finish:
                try:
                    run(finish, renderer)
                except RuntimeError as error:
                    print(f"WARNING could not complete: {error}", file=sys.stderr)
        if args.sleep:
            time.sleep(args.sleep)

    if args.script:
        with open(args.script, "w", encoding="utf-8") as handle:
            handle.write("\n".join(script) + "\n")
        os.chmod(args.script, 0o755)

    summary = ", ".join(f"{kind}: {count}" for kind, count in counts.items())
    verb = "created" if args.execute else "planned"
    print(f"\n{verb} — {summary}", file=sys.stderr)
    if skipped:
        print(f"skipped {skipped} already in the ledger", file=sys.stderr)
    if dropped_fields:
        detail = ", ".join(f"{k} ({v})" for k, v in sorted(dropped_fields.items()))
        print(
            f"no profile flag for: {detail} — these values were dropped. "
            "Add them to the profile, or re-run with --tags notes / "
            "--checklists notes.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
