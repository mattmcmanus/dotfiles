# git-wt: Extract worktree manager to standalone repo

**Date:** 2026-03-27
**Status:** Draft

## Overview

Extract the `wt` worktree management script from the dotfiles repo into a standalone `git-wt` repo, making it installable by anyone via `make install` or Homebrew. The script becomes a git subcommand (`git wt`) with an optional `wt` alias.

## Goals

- Make the worktree manager available to teammates and the broader community
- Provide a frictionless install experience (Homebrew + manual)
- Add tests and CI to support contributions and catch regressions
- Improve the hook system with a directory walk-up pattern
- Keep the core behavior identical — this is an extraction, not a rewrite

## Non-goals

- Modularizing the script into multiple files (it's ~200 lines)
- Making fzf optional (hard requirement for now)
- Man pages (not for v1)
- Demo GIF/asciicast (aspirational, not blocking)

## Repo Structure

```
git-wt/
├── git-wt                        # Main script
├── wt -> git-wt                  # Optional alias symlink
├── completions/
│   ├── git-wt.zsh                # Zsh completion
│   └── git-wt.bash               # Bash completion
├── Makefile                      # install/uninstall (PREFIX=/usr/local)
├── Formula/
│   └── git-wt.rb                 # Homebrew formula (source of truth)
├── test/
│   ├── test_helper/
│   │   └── setup.bash            # Shared test fixtures
│   ├── switch.bats
│   ├── add.bats
│   ├── remove.bats
│   ├── clean.bats
│   └── hooks.bats
├── .github/
│   └── workflows/
│       └── ci.yml
├── LICENSE                       # MIT
└── README.md
```

## Installation Methods

### Manual

```bash
git clone https://github.com/<user>/git-wt.git
cd git-wt
make install                    # installs to /usr/local/bin
make install PREFIX=~/.local    # or custom prefix
```

The Makefile handles:
- Copying `git-wt` to `$PREFIX/bin/`
- `make install-alias`: symlinks `wt` -> `git-wt` in the same dir
- Installing completions to appropriate shell directories
- `make uninstall` to remove everything

### Homebrew

```bash
brew install <user>/tap/git-wt
```

The formula lives in a separate `homebrew-tap` repo (standard convention). `Formula/git-wt.rb` in this repo is the source of truth, synced to the tap on release.

The formula installs `git-wt` to bin and completions to shell dirs. For the `wt` alias, the formula includes a post-install caveat suggesting `ln -s $(brew --prefix)/bin/git-wt $(brew --prefix)/bin/wt` for users who want the short form.

### Dotfiles integration (post-extraction)

The dotfiles repo drops `bin/wt` and either:
- Adds `git-wt` to the Brewfile, or
- Adds installation to `hooks/post-up`

## Script Changes

### Naming

- File renamed from `wt` to `git-wt`
- Git auto-discovers `git-*` executables on PATH, so `git wt` works automatically
- The `wt` symlink provides the short form for those who want it

### Hook lookup (new behavior)

The current script looks for a `post-add-worktree` executable in the worktree's parent directory. The new behavior uses a walk-up pattern familiar from tools like `.env`, `.nvmrc`, and `.tool-versions`:

1. Starting from the new worktree root, look for `.wt/post-add-worktree`
2. Walk up parent directories, checking each for `.wt/post-add-worktree`
3. Stop at `$HOME` (not filesystem root)
4. First match wins and is executed
5. `~/.wt/post-add-worktree` serves as a user-wide global default

The hook file must be executable. If found, it is executed with the new worktree path as the working directory.

### Version and help

- Add `git wt --version` / `git wt version`
- Improve `--help` output with examples for each subcommand

### No other behavioral changes

The switch, add, remove, clean, and list commands work exactly as they do today.

## Subcommands

| Command | Description |
|---------|-------------|
| `git wt <name>` | Fuzzy-search and switch to a worktree, preserving relative paths |
| `git wt add <name>` | Create a new worktree and switch to it |
| `git wt remove [name]` | Remove a worktree (fzf selection if no name given) |
| `git wt clean` | Remove all worktrees for merged/gone branches |
| `git wt list` | List all worktrees |
| `git wt help` | Show usage and examples |
| `git wt version` | Print version |

## Dependencies

**Required:**
- `bash` (shebang: `#!/usr/bin/env bash`)
- `git`
- `fzf`

**Standard POSIX (no extra install):**
- `sed`, `cut`, `awk`, `grep`

## Testing

### Framework

[bats-core](https://github.com/bats-core/bats-core) — the standard for bash script testing. Installed as a git submodule or via Homebrew in CI.

### Test structure

One `.bats` file per subcommand, plus one for hooks. Each test:
- Creates a temporary bare repo + worktrees in `$BATS_TMPDIR`
- Runs `git-wt` against real git repos (no mocking)
- Tears down in `teardown`

### Coverage

- **switch** — fuzzy match, exact match, relative path preservation
- **add** — creates worktree, triggers post-add hook
- **remove** — removes worktree, handles nonexistent gracefully
- **clean** — removes only merged branches, skips unmerged, handles gone branches
- **hooks** — `.wt/post-add-worktree` walk-up lookup, stops at `$HOME`, global fallback
- **list** — output format
- **help/version** — smoke tests

### Excluded from testing (for now)

- Interactive fzf selection (hard to test, low ROI)
- `exec $SHELL` behavior (replaces process, not testable in bats)

### CI

GitHub Actions workflow running on push and PR:
- **Platforms:** ubuntu-latest, macos-latest
- **Setup:** install bats-core, fzf, git
- **Run:** `bats test/`

## Documentation

### README.md

- One-liner description
- Installation: manual, Homebrew, `wt` alias option
- Usage: each subcommand with examples
- Hook system: lookup order, global defaults, example use cases
- Requirements: git, fzf, bash
- Contributing: how to run tests locally

### In-script help

`git wt help` and `git wt --help` print usage with brief examples for each subcommand.

## Migration from dotfiles

After the new repo is published:

1. Remove `bin/wt` from dotfiles
2. Add `git-wt` to Brewfile (or install via `hooks/post-up`)
3. Optionally install the `wt` alias if you want the short form
4. Note the lineage in the new repo's README (link back to dotfiles history)

Git history for the script can optionally be preserved with `git filter-repo`, or start fresh with a note about lineage.
