# Context for this directory

A one-time Things 3 → Stuff migration. Built in a cloud session that had no
macOS, no Things database and no Stuff CLI; everything here was developed
against the `things.py` test fixture plus repeat-rule structures pasted in by
hand. A local agent has the real thing and should finish the calibration.

Read `README.md` first — it covers the design and the data mapping. This file
is the working state.

## Ground rules

- `things_export.py` is read-only. `stuff_import.py` writes **only** with
  `--execute`; everything else prints.
- Never run a full `--execute` before a `--validate` pass and a
  `--limit 5 --execute` smoke test. There is no undo in Stuff.
- Quit Things before exporting so its SQLite file is flushed.
- Matt's task data is personal and business (deli, rental properties). Keep
  dumps, ledgers and any fixture out of git — `.gitignore` covers
  `__pycache__` and `.ruff_cache`, nothing else. Do not commit a
  `things-dump.json`, a ledger, or anything with real task titles.
- `test_repeats.py` deliberately carries rule structures with titles stripped.
  Keep it that way.

## How to run things

```sh
uv run ./things_export.py --explain-repeats      # PEP 723 header pulls things.py
uv run ./things_export.py --output things-dump.json
./stuff_import.py things-dump.json --validate
python3 test_repeats.py                          # decoder tests, no deps
ruff check .
```

Verified on Python 3.9.11 (what `tag-python/python-version` pins) and 3.11.

To exercise anything without a real database:

```sh
curl -sSLO https://raw.githubusercontent.com/thingsapi/things.py/main/tests/main.sqlite
uv run ./things_export.py --database ./main.sqlite -o dump.json --include-completed
```

## State: what is done

- Export is complete and tested: areas, projects, headings, to-dos,
  checklists, tags, dates, status, plus repeating to-dos.
- Repeat rules decode correctly. Confirmed against 52 of Matt's real rules
  covering all four frequency units. `test_repeats.py` asserts each rule's
  generated occurrence lands where its `of` entry predicts.
- `profiles/stuff.json` is written from the real `stuff --help` output.

## State: what is not done

**1. Four flags in the profile are unverified.** They are listed under
`_unverified` in `profiles/stuff.json`. None appear in `stuff --help`:

- does `stuff add task` accept `--heading`? (`add heading` exists, but nothing
  documents filing a task under one)
- does `add task` accept `--space`? Needed for Things to-dos that sit in an
  area with no project.
- does `add task` accept `--notes`? `--notes` is documented for `add space`
  only.
- does `--tag` repeat, or does it want a joined list? (`tags_style` in the
  profile)

Do not guess at these. Run `./stuff_import.py things-dump.json --validate`:
it puts every command through the CLI's global `--dry-run` and groups failures
by Stuff's documented exit codes. **Exit 4 or 64 means the profile is wrong.
Exit 5 (not found) is expected** — parents do not exist during validation.
`stuff help add task` answers them directly too.

**2. One open question about repeat semantics.** After-completion rules
(`tp: 0`) still carry an `of` entry. Nothing in the database says whether it
constrains the next occurrence or merely records where the current one landed,
so `things_repeats.py` reports it as "anchored to ..." — true either way.

To settle it: open **Order: Stockertown** in Things. If the repeat reads
"every 2 weeks after completion" with no weekday shown, the anchor is
vestigial and should be dropped from the summary. If it shows Wednesday, it is
a real constraint and should read "on Wednesday". Update `decode()` in
`things_repeats.py` and the expectations in `test_repeats.py` either way.

**3. The migration has not been run.** Nothing has been created in Stuff.

## Then

Once `--validate` is clean: `--limit 5 --execute`, check the result in Stuff by
hand, then the full `--execute`. It writes a ledger after every command, so an
interrupted run resumes rather than duplicating.
