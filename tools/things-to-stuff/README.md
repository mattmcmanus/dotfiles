# Things 3 → Stuff, one-time migration

Stuff has no importer. These two scripts do a one-way dump: read the Things
database, then replay it through the Stuff CLI.

They are deliberately split so the risky half is reviewable:

| Script | What it does | Touches |
| --- | --- | --- |
| `things_export.py` | Things SQLite → normalised JSON | Read-only |
| `stuff_import.py` | JSON → `stuff` CLI commands | Writes, but only with `--execute` |

## Before you start

- macOS with Things 3 installed. Quit Things first so the database is flushed.
- `pip install things.py` — reads the local Things SQLite file
  ([thingsapi/things.py](https://github.com/thingsapi/things.py)).
- The Stuff CLI on `$PATH` as `stuff`.
- Ideally a fresh/empty Stuff account. There is no undo.

Things' [URL scheme](https://culturedcode.com/things/support/articles/2803573/)
is not used here — it writes *into* Things, which is the wrong direction. It is
the tool to reach for if you ever migrate back.

## 1. Export

```sh
./things_export.py --output things-dump.json
```

Incomplete items only by default. Useful additions:

```sh
--include-completed --completed-since 2025-01-01   # bring some Logbook across
--include-canceled
--include-trashed
--database ~/path/to/main.sqlite                   # or set $THINGSDB
```

The dump keeps the Things shape — areas → projects → headings → to-dos →
checklist items, plus `inbox`, loose `todos`, `tags` and a `stats` block. Read
it; it is the last point where fixing something is cheap.

## 2. Calibrate the profile

**This is the one manual step.** `profiles/stuff.json` holds every `stuff`
command this migration issues, and it is written from a *guess* at the CLI's
flags — the [Stuff CLI docs](https://www.themitycompany.com/docs/stuff-cli)
could not be reached from where this was built. Open `stuff --help` and
`stuff <command> --help`, fix the strings, and nothing else needs to change.

What the profile controls:

- `binary`, `global_args` — add `--json`/`--porcelain` here if the CLI has one.
- `commands.<kind>.args` — the base invocation for `space`, `list`, `task`,
  `subtask` and `complete`.
- `commands.<kind>.options` — one entry per field. An option is only emitted
  when every `{placeholder}` in it has a value, so empty fields drop out by
  themselves. Delete an entry the CLI does not support and the importer will
  tell you how many values it dropped as a result.
- `capture_id` + `id_pattern` — how a new item's id is read back out of stdout
  and handed to its children. Get this wrong and everything lands unparented.
- `script_id_filter` — the shell equivalent, used by `--script`.
- `when_map` — how `anytime` / `someday` are spelled.

## 3. Dry run, then commit

```sh
./stuff_import.py things-dump.json                      # prints every command
./stuff_import.py things-dump.json --script plan.sh     # runnable script, ids wired through
./stuff_import.py things-dump.json --limit 5 --execute  # smoke test on five items
./stuff_import.py things-dump.json --execute            # the real thing
```

`--execute` writes a ledger (`stuff-import-ledger.json`) after every command,
mapping Things uuid → created Stuff id. Re-running skips what is already there,
so an interrupted or failed run resumes instead of duplicating. Delete the
ledger to start over — after deleting the items in Stuff.

Mapping choices, all with sane defaults:

```sh
--headings prefix|task|ignore    # Things headings have no obvious Stuff equivalent
--checklists subtask|notes|skip
--tags native|notes|skip
--completed skip|include         # what to do with done items in the dump
--stamp-source                   # append the Things uuid to each note
--sleep 0.2                      # throttle, if the CLI dislikes a firehose
```

## What survives, and what does not

Carried over: areas, projects, headings (flattened per `--headings`), to-dos,
notes, checklist items, tags, start dates, deadlines, Someday/Anytime, Inbox,
and completion state where the dump includes it.

Left behind:

- **Repeat rules.** Things stores them as an opaque blob and `things.py`
  filters repeating templates out of every query. The export lists them under
  `repeating_not_exported` so you can recreate them by hand — the already
  generated instances do come across, which means a repeating to-do can appear
  both in that list and as a normal task.
- **Reminder times.** Exported as `reminder_time`, but no profile flag maps
  them until the CLI is confirmed to support times.
- **Today ordering.** `index` / `today_index` are in the dump; nothing replays
  them.
- **Attachments and images** in notes, and `things:///` links, which will point
  at Things forever.
- **Tag hierarchy.** Tags come across as flat names.
- **Logbook and Trash**, unless you ask for them at export time.

## Testing

Both scripts were exercised against the `things.py` test database
(`tests/main.sqlite` from that repo), not just a live account:

```sh
curl -sSLO https://raw.githubusercontent.com/thingsapi/things.py/main/tests/main.sqlite
./things_export.py --database ./main.sqlite -o dump.json --include-completed
./stuff_import.py dump.json --state "" --script plan.sh
```

Point `binary` at `echo` in a copy of the profile to watch the whole thing run
without touching Stuff.
