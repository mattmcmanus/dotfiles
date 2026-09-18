#!/usr/bin/env python3
"""Turn a Things export (see things_export.py) into Stuff CLI commands.

Stuff has no importer, so this walks the exported tree and renders one CLI
invocation per space / list / heading / task. The command surface lives in a
JSON profile (profiles/stuff.json) rather than in this file.

    ./stuff_import.py things-dump.json                  # dry run, prints commands
    ./stuff_import.py things-dump.json --validate        # let the CLI check them
    ./stuff_import.py things-dump.json --script run.sh   # save for review
    ./stuff_import.py things-dump.json --execute         # create things

Parents are referenced by name (`--list Groceries`), the way the Stuff CLI's
own examples do, so no id bookkeeping is needed. Duplicate names in Things are
reported up front, because the CLI exits 3 on an ambiguous match.
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
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterator

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROFILE = os.path.join(HERE, "profiles", "stuff.json")

PLACEHOLDER = re.compile(r"\{(\w+)\}")

# From `stuff --help`.
EXIT_CODES = {
    0: "success",
    1: "generic error",
    2: "unauthenticated - run `stuff auth status`",
    3: "ambiguous match - two items share this name",
    4: "invalid input - a flag or value in the profile is wrong",
    5: "not found - parent does not exist (expected during --validate)",
    6: "network error",
    7: "permission denied",
    64: "usage error - unknown flag or missing argument",
}
# Codes that mean the profile is wrong, as opposed to the run being incomplete.
PROFILE_ERRORS = (4, 64)


@dataclass
class Op:
    """One CLI invocation to make."""

    kind: str  # space | list | heading | task
    ref: str  # Things uuid, the ledger key
    title: str
    fields: dict[str, Any] = field(default_factory=dict)
    finish: str | None = None  # "complete" | "cancel"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render/run Stuff CLI commands from a Things export.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("dump", help="JSON file written by things_export.py")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help="CLI profile JSON")
    parser.add_argument("--script", help="Write the commands to this shell script")
    parser.add_argument(
        "--execute", action="store_true", help="Run the commands for real."
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run every command through the CLI's own --dry-run and report "
        "which ones it rejects. Creates nothing.",
    )
    parser.add_argument(
        "--state",
        default="stuff-import-ledger.json",
        help='Ledger of created items, for resuming. Pass "" to ignore it.',
    )
    parser.add_argument(
        "--checklists",
        choices=("notes", "task", "skip"),
        default="notes",
        help="Things checklist items. Stuff has task dependencies, not "
        "subtasks, so these go into the note by default.",
    )
    parser.add_argument(
        "--tags",
        choices=("native", "notes", "skip"),
        default="native",
        help="Things tags: --tag flags, appended to notes, or dropped.",
    )
    parser.add_argument(
        "--repeats",
        choices=("template", "instance", "both"),
        default="template",
        help="A repeating Things to-do exists twice: the template (which "
        "carries the rule) and the occurrence Things has already generated. "
        "Import the template, that occurrence, or both.",
    )
    parser.add_argument(
        "--completed",
        choices=("skip", "include"),
        default="skip",
        help="Completed and cancelled items present in the dump.",
    )
    parser.add_argument(
        "--stamp-source",
        action="store_true",
        help="Append the originating Things uuid to each note.",
    )
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        help="Skip `stuff doctor` / `stuff auth status` before running.",
    )
    parser.add_argument("--limit", type=int, help="Only do the first N commands.")
    parser.add_argument(
        "--sleep", type=float, default=0.0, help="Seconds between commands."
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------------
# Walking the export
# --------------------------------------------------------------------------


def build_notes(item: dict[str, Any], args: argparse.Namespace) -> str:
    lines = [item["notes"]] if item.get("notes") else []
    repeat = item.get("repeat") or {}
    if repeat.get("summary"):
        lines.append(f"Repeats in Things: {repeat['summary']} (recreate by hand)")
    elif repeat.get("error"):
        lines.append(f"Repeated in Things, rule unreadable: {repeat['error']}")
    if args.tags == "notes" and item.get("tags"):
        lines.append("Tags: " + ", ".join(item["tags"]))
    if args.checklists == "notes" and item.get("checklist"):
        for entry in item["checklist"]:
            mark = "x" if entry["status"] == "completed" else " "
            lines.append(f"- [{mark}] {entry['title']}")
    if args.stamp_source:
        lines.append(f"Things: {item['uuid']}")
    return "\n".join(lines)


def is_done(item: dict[str, Any]) -> bool:
    return item.get("status") in ("completed", "canceled")


def base_fields(item: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "title": item.get("title") or "(untitled)",
        "notes": build_notes(item, args),
        "deadline": item.get("deadline") or "",
        "plan": item.get("start_date") or "",
        "start": item.get("start") or "",
    }
    if args.tags == "native" and item.get("tags"):
        fields["tags"] = list(item["tags"])
    return fields


def finish_for(item: dict[str, Any], args: argparse.Namespace) -> str | None:
    if args.completed == "skip" or not is_done(item):
        return None
    return "cancel" if item["status"] == "canceled" else "complete"


def walk(dump: dict[str, Any], args: argparse.Namespace) -> Iterator[Op]:
    def task(item: dict[str, Any], parent: dict[str, str]) -> Iterator[Op]:
        if is_done(item) and args.completed == "skip":
            return
        if args.repeats == "template" and item.get("from_repeat"):
            return
        if args.repeats == "instance" and item.get("repeating_template"):
            return
        fields = base_fields(item, args)
        fields.update(parent)
        yield Op("task", item["uuid"], fields["title"], fields, finish_for(item, args))
        if args.checklists == "task":
            for index, entry in enumerate(item.get("checklist") or []):
                if entry["status"] != "incomplete" and args.completed == "skip":
                    continue
                child = dict(parent)
                child["title"] = f"{item['title']}: {entry['title']}"
                child["notes"] = ""
                yield Op("task", f"{item['uuid']}#{index}", child["title"], child)

    def project(item: dict[str, Any], parent: dict[str, str]) -> Iterator[Op]:
        if is_done(item) and args.completed == "skip":
            return
        fields = base_fields(item, args)
        fields.update(parent)
        yield Op("list", item["uuid"], fields["title"], fields)
        under = {"list": item["title"]}
        for todo in item.get("todos") or []:
            yield from task(todo, under)
        for heading in item.get("headings") or []:
            yield Op(
                "heading",
                heading["uuid"],
                heading["title"],
                {"title": heading["title"], "list": item["title"], "notes": ""},
            )
            for todo in heading.get("todos") or []:
                yield from task(todo, {"list": item["title"], "heading": heading["title"]})

    for area in dump.get("areas") or []:
        yield Op(
            "space",
            area["uuid"],
            area["title"],
            {
                "title": area["title"],
                "notes": "",
                "tags": list(area.get("tags") or []) if args.tags == "native" else [],
            },
        )
        for item in area.get("projects") or []:
            yield from project(item, {"space": area["title"]})
        for todo in area.get("todos") or []:
            yield from task(todo, {"space": area["title"]})

    for item in dump.get("projects") or []:
        yield from project(item, {})
    for todo in dump.get("inbox") or []:
        yield from task(todo, {})
    for todo in dump.get("todos") or []:
        yield from task(todo, {})


def duplicate_names(dump: dict[str, Any]) -> list[str]:
    """Names the CLI would find ambiguous (exit code 3)."""
    warnings: list[str] = []
    areas = [a["title"] for a in dump.get("areas") or []]
    projects = [p["title"] for a in dump.get("areas") or [] for p in a.get("projects") or []]
    projects += [p["title"] for p in dump.get("projects") or []]
    headings = [
        h["title"]
        for a in dump.get("areas") or []
        for p in a.get("projects") or []
        for h in p.get("headings") or []
    ]
    headings += [
        h["title"] for p in dump.get("projects") or [] for h in p.get("headings") or []
    ]
    for label, names in (("space", areas), ("list", projects), ("heading", headings)):
        for name, count in Counter(names).items():
            if count > 1:
                warnings.append(f"{count} {label}s named {name!r}")
    return warnings


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


class Renderer:
    def __init__(self, profile: dict[str, Any]):
        self.profile = profile
        self.binary = profile.get("binary", "stuff")
        self.global_args = profile.get("global_args") or []
        self.dry_run_args = profile.get("dry_run_args") or ["--dry-run"]
        self.commands = profile.get("commands") or {}
        self.when_map = profile.get("when_map") or {}
        self.tags_style = profile.get("tags_style", "repeat")
        self.preflight = profile.get("preflight") or []

    @staticmethod
    def fill(template: str, values: dict[str, str]) -> str | None:
        missing = False

        def replace(match: re.Match[str]) -> str:
            nonlocal missing
            value = values.get(match.group(1), "")
            if not value:
                missing = True
            return value

        out = PLACEHOLDER.sub(replace, template)
        return None if missing else out

    def resolve(self, fields: dict[str, Any]) -> dict[str, str]:
        """Flatten a walk's fields into plain strings the templates can use."""
        values = {k: v for k, v in fields.items() if isinstance(v, str)}
        if not values.get("plan") and fields.get("start") in self.when_map:
            mapped = self.when_map[fields["start"]]
            if mapped:
                values["plan"] = mapped
        return values

    def render(self, op: Op, dry_run: bool = False) -> tuple[list[str], list[str]]:
        spec = self.commands.get(op.kind)
        if spec is None:
            raise KeyError(f"profile has no command for {op.kind!r}")
        values = self.resolve(op.fields)
        tags = op.fields.get("tags") or []

        argv = [self.binary, *self.global_args]
        if dry_run:
            argv += self.dry_run_args
        for piece in spec.get("args") or []:
            argv.append(self.fill(piece, values) or "")

        options = spec.get("options") or {}
        dropped: list[str] = []
        for key, template in options.items():
            if key == "tags":
                for tag in tags if self.tags_style == "repeat" else [",".join(tags)]:
                    rendered = [self.fill(piece, {"tag": tag}) for piece in template]
                    if all(piece is not None for piece in rendered):
                        argv.extend(piece for piece in rendered if piece)
                continue
            if not values.get(key):
                continue
            rendered = [self.fill(piece, values) for piece in template]
            if any(piece is None for piece in rendered):
                dropped.append(key)
                continue
            argv.extend(piece for piece in rendered if piece is not None)

        for key in ("notes", "deadline", "plan"):
            if values.get(key) and key not in options:
                dropped.append(key)
        if tags and "tags" not in options:
            dropped.append("tags")
        return argv, dropped

    def finish_argv(self, kind: str, ref: str) -> list[str] | None:
        spec = self.commands.get(kind)
        if not spec:
            return None
        argv = [self.binary, *self.global_args]
        for piece in spec.get("args") or []:
            argv.append(self.fill(piece, {"ref": ref}) or "")
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
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(ledger, handle, indent=2)


def call(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, check=False)


def preflight(renderer: Renderer) -> bool:
    for command in renderer.preflight:
        argv = [renderer.binary, *renderer.global_args, *command]
        result = call(argv)
        if result.returncode != 0:
            reason = EXIT_CODES.get(result.returncode, f"exit {result.returncode}")
            print(f"preflight failed: {shlex.join(argv)} -> {reason}", file=sys.stderr)
            print((result.stderr or result.stdout).strip(), file=sys.stderr)
            return False
    return True


def validate(ops: list[Op], renderer: Renderer) -> int:
    """Run every command through the CLI's own --dry-run."""
    problems: dict[int, list[tuple[str, str]]] = {}
    for op in ops:
        argv, _ = renderer.render(op, dry_run=True)
        result = call(argv)
        if result.returncode == 0:
            continue
        message = (result.stderr or result.stdout).strip().splitlines()
        problems.setdefault(result.returncode, []).append(
            (shlex.join(argv), message[0] if message else "")
        )

    if not problems:
        print(f"All {len(ops)} commands accepted by --dry-run.")
        return 0

    real = 0
    for code, entries in sorted(problems.items()):
        meaning = EXIT_CODES.get(code, "unknown")
        flag = "PROFILE BUG" if code in PROFILE_ERRORS else "expected/ignorable"
        print(f"\nexit {code} ({meaning}) - {len(entries)} command(s) [{flag}]")
        for command, message in entries[:3]:
            print(f"    {command}")
            if message:
                print(f"      -> {message}")
        if len(entries) > 3:
            print(f"    ... and {len(entries) - 3} more")
        if code in PROFILE_ERRORS:
            real += len(entries)

    if real:
        print(
            f"\n{real} command(s) the CLI rejected outright. Fix those flags in "
            "the profile and re-run --validate.",
            file=sys.stderr,
        )
        return 1
    print("\nNo profile errors. 'not found' failures are expected here: the "
          "parent items do not exist yet.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    with open(args.dump, encoding="utf-8") as handle:
        dump = json.load(handle)
    with open(args.profile, encoding="utf-8") as handle:
        renderer = Renderer(json.load(handle))

    for warning in duplicate_names(dump):
        print(
            f"WARNING {warning} - the CLI exits 3 on an ambiguous name. "
            "Rename in Things first, or expect those children to fail.",
            file=sys.stderr,
        )

    ledger = load_ledger(args.state)
    ops = [op for op in walk(dump, args) if op.ref not in ledger]
    skipped = len(ledger)
    if args.limit:
        ops = ops[: args.limit]

    if (args.execute or args.validate) and not args.no_preflight:
        if not preflight(renderer):
            return 2

    if args.validate:
        return validate(ops, renderer)

    counts: Counter[str] = Counter()
    dropped_fields: Counter[str] = Counter()
    script: list[str] = [
        "#!/usr/bin/env bash",
        "# Generated by stuff_import.py. Review before running.",
        "set -euo pipefail",
        "",
    ]

    for op in ops:
        command, dropped = renderer.render(op)
        dropped_fields.update(dropped)
        counts[op.kind] += 1

        if not args.execute:
            line = shlex.join(command)
            print(line)
            script.append(line)
            if op.finish:
                finish = renderer.finish_argv(op.finish, op.title)
                if finish:
                    script.append(shlex.join(finish))
                    print(shlex.join(finish))
            continue

        result = call(command)
        if result.returncode != 0:
            reason = EXIT_CODES.get(result.returncode, f"exit {result.returncode}")
            print(
                f"FAILED {shlex.join(command)}\n  {reason}\n  "
                f"{(result.stderr or result.stdout).strip()}",
                file=sys.stderr,
            )
            save_ledger(args.state, ledger)
            return 1

        ledger[op.ref] = {"kind": op.kind, "title": op.title}
        save_ledger(args.state, ledger)
        if op.finish:
            finish = renderer.finish_argv(op.finish, op.title)
            if finish and call(finish).returncode != 0:
                print(
                    f"WARNING could not {op.finish} {op.title!r}", file=sys.stderr
                )
        if args.sleep:
            time.sleep(args.sleep)

    if args.script:
        with open(args.script, "w", encoding="utf-8") as handle:
            handle.write("\n".join(script) + "\n")
        os.chmod(args.script, 0o755)

    verb = "created" if args.execute else "planned"
    summary = ", ".join(f"{kind}: {count}" for kind, count in sorted(counts.items()))
    print(f"\n{verb} - {summary or 'nothing'}", file=sys.stderr)
    if skipped:
        print(f"skipped {skipped} already in the ledger", file=sys.stderr)
    if dropped_fields:
        detail = ", ".join(f"{k} ({v})" for k, v in sorted(dropped_fields.items()))
        print(f"no profile flag for: {detail} - values dropped", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
