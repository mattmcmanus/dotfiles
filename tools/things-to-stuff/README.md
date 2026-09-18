# Things 3 → Stuff, one-time migration

Stuff has no importer. These scripts do a one-way dump: read the Things
database, then replay it through the Stuff CLI.

| File | What it does | Touches |
| --- | --- | --- |
| `things_export.py` | Things SQLite → normalised JSON | Read-only |
| `things_repeats.py` | Decodes Things repeat rules | Pure function |
| `stuff_import.py` | JSON → `stuff` CLI commands | Writes only with `--execute` |
| `profiles/stuff.json` | Every command and flag the import issues | Data, not code |

The models line up better than expected — Things areas, projects, headings and
to-dos map onto Stuff spaces, lists, headings and tasks one for one.

## Before you start

- macOS with Things 3. Quit Things first so the database is flushed.
- The Stuff CLI on `$PATH`. It needs an Extra Stuff membership.
- Ideally an empty Stuff account. There is no undo.

`things_export.py` needs [things.py](https://github.com/thingsapi/things.py).
Both scripts carry PEP 723 inline metadata, so the simplest route installs
nothing:

```sh
brew install uv          # if you do not have it
uv run ./things_export.py --output things-dump.json
```

`uv` reads the dependency off the script header and builds a throwaway
environment. Otherwise, a virtualenv:

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install things.py
```

Or, since you have pyenv, `pyenv shell 3.9.11 && pip install things.py` — a
pyenv interpreter is not externally managed, so PEP 668 does not block it.
Homebrew's `python3` does: `pip3 install` there fails with
`externally-managed-environment`, and `--break-system-packages` is not worth
the risk to your Homebrew install.

Verified on Python 3.9.11 (the version `tag-python/python-version` pins) and
3.11.

Things' [URL scheme](https://culturedcode.com/things/support/articles/2803573/)
is not used — it writes *into* Things, the wrong direction. It is the tool for
migrating back.

## 1. Export

```sh
./things_export.py --output things-dump.json      # or: uv run ./things_export.py ...
```

Incomplete items only by default. Also available:

```sh
--include-completed --completed-since 2025-01-01
--include-canceled
--include-trashed
--explain-repeats                 # print decoded repeat rules and exit
--database ~/path/main.sqlite     # or set $THINGSDB
```

## 2. Let the CLI check the profile

`profiles/stuff.json` holds every command the import issues, written from
`stuff --help`. A few flags are not in that help output and are marked
`_unverified` in the file — chiefly whether `add task` takes `--heading`,
`--space` and `--notes`.

You do not have to guess at them. Stuff has a global `--dry-run` that
validates a mutation without committing it, so the CLI can check the whole
plan for you:

```sh
./stuff_import.py things-dump.json --validate
```

Every command runs through `--dry-run`, and failures are grouped by the exit
codes Stuff documents. The distinction that matters:

- **exit 4 / 64 → the profile is wrong.** An unknown flag or a bad value. Fix
  it in `profiles/stuff.json` and re-run.
- **exit 5 (not found) → expected.** Parents do not exist during validation.
- **exit 3 (ambiguous match) → two items share a name.** The importer warns
  about these before it starts; rename in Things first.
- **exit 2 → not authenticated.** `stuff auth status`.

`--validate` also runs `stuff doctor` and `stuff auth status` first.

## 3. Dry run, then commit

```sh
./stuff_import.py things-dump.json                      # print every command
./stuff_import.py things-dump.json --script plan.sh     # save for review
./stuff_import.py things-dump.json --limit 5 --execute  # smoke test
./stuff_import.py things-dump.json --execute            # the real thing
```

Parents are referenced by name (`--list Groceries`), the way the CLI's own
examples do, so there is no id bookkeeping and the generated script is
readable. `--execute` writes a ledger after every command; re-running skips
what is already there, so an interrupted run resumes instead of duplicating.

```sh
--repeats template|instance|both   # see below
--checklists notes|task|skip
--tags native|notes|skip
--completed skip|include           # replays via `stuff complete` / `stuff cancel`
--stamp-source                     # append the Things uuid to each note
--sleep 0.2
```

## Repeating to-dos

A repeating to-do exists twice in Things: the **template**, which carries the
rule, and the **occurrence** Things has already generated. `things.py` hides
templates from every query (`rt1_recurrenceRule IS NULL` is hardcoded into its
WHERE clause), so a naive export silently loses the repeat and keeps only the
occurrence.

`rt1_recurrenceRule` is an XML plist, not an opaque blob. `things_repeats.py`
decodes it:

```
{'fa': 1, 'fu': 256, 'of': [{'wd': 0}], 'ia': 1616889600.0, ...}
  → "every week on Sunday, starting 2021-03-28"
```

`fa` is the interval, `of` the weekdays, `ia` the first instance, and `ed` is
`4001-01-01` when the repeat never ends. `fu` holds Apple's NSCalendarUnit
values; only 256 (weekly) has been confirmed against a real rule, so any other
value is reported with `needs_review` and its raw number rather than guessed
at. Check yours and extend `UNITS`:

```sh
./things_export.py --explain-repeats
```

Since nothing in the Stuff CLI mentions repeats, the rule is written into the
task's note as a line you can act on:

```
Repeats in Things: every week on Sunday, starting 2021-03-28 (recreate by hand)
```

`--repeats template` (the default) imports the template and drops the
already-generated occurrence, so you get one task per repeat rather than two.
The link is `rt1_repeatingTemplate` on the occurrence.

## What does not come across

- **The repeat itself.** No repeat flag exists anywhere in the Stuff CLI, so
  the rule is a note. Everything else about the task survives.
- **Reminder times.** Exported as `reminder_time`; `--plan` takes a date.
- **Today ordering.** `index` / `today_index` are in the dump, unused.
- **Attachments, images, and `things:///` links**, which point at Things
  forever.
- **Tag hierarchy** — tags come across flat.
- **Checklists** become note lines by default; Stuff has task *dependencies*,
  not subtasks. `--checklists task` promotes them to real tasks instead.
- **Logbook and Trash**, unless asked for at export time.

## Notes

`things_export.py` decodes Things' packed date integers itself rather than
using things.py's SQL helper, whose bit mask truncates out-of-range years: a
repeating template stores `4001-01-01` to mean "no deadline", and that helper
renders it as `1953-01-01`.

## Testing

Both scripts run against the `things.py` test database, not just a live
account:

```sh
curl -sSLO https://raw.githubusercontent.com/thingsapi/things.py/main/tests/main.sqlite
./things_export.py --database ./main.sqlite -o dump.json --include-completed
./stuff_import.py dump.json --state "" --script plan.sh
```

Point `binary` at a stub in a copy of the profile to exercise `--execute` and
`--validate` without touching Stuff.
