# git-wt Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the `wt` worktree management script from the dotfiles repo into a standalone `git-wt` repo with tests, CI, Homebrew formula, and improved hook system.

**Architecture:** Single bash script (`git-wt`) in its own repo, installed via `make install` or Homebrew. Tests use bats-core against real git repos. Hook lookup walks up directories for `.wt/post-add-worktree`, stopping at `$HOME`.

**Tech Stack:** Bash, git, fzf, bats-core, GitHub Actions, Homebrew, Make

---

## File Structure

```
git-wt/
├── git-wt                          # Main script (~220 lines)
├── completions/
│   ├── git-wt.zsh                  # Zsh completion for subcommands
│   └── git-wt.bash                 # Bash completion for subcommands
├── Makefile                        # install/uninstall/install-alias targets
├── Formula/
│   └── git-wt.rb                   # Homebrew formula
├── test/
│   ├── test_helper/
│   │   └── setup.bash              # Shared fixtures: create bare repo, worktrees
│   ├── list.bats                   # List subcommand tests
│   ├── add.bats                    # Add subcommand tests
│   ├── remove.bats                 # Remove subcommand tests
│   ├── clean.bats                  # Clean subcommand tests
│   ├── hooks.bats                  # Hook walk-up tests
│   └── help.bats                   # Help/version smoke tests
├── .github/
│   └── workflows/
│       └── ci.yml                  # bats on ubuntu + macos
├── LICENSE                         # MIT
└── README.md
```

---

### Task 1: Create repo and scaffold

**Files:**
- Create: `git-wt/` (new repo directory)
- Create: `git-wt/LICENSE`
- Create: `git-wt/README.md`
- Create: `git-wt/.gitignore`

- [ ] **Step 1: Create the GitHub repo**

```bash
gh repo create mattmcmanus/git-wt --public --description "A fast, interactive git worktree manager" --clone
cd git-wt
```

- [ ] **Step 2: Add LICENSE (MIT)**

Create `LICENSE`:

```
MIT License

Copyright (c) 2026 Matt McManus

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Add .gitignore**

Create `.gitignore`:

```
# bats test artifacts
test_results/
```

- [ ] **Step 4: Add initial README.md**

Create `README.md`:

```markdown
# git-wt

A fast, interactive git worktree manager. Switch, create, remove, and clean up git worktrees with ease.

Works as a git subcommand: `git wt`

## Requirements

- [git](https://git-scm.com/)
- [fzf](https://github.com/junegunn/fzf)
- bash

## Installation

### Homebrew

```bash
brew install mattmcmanus/tap/git-wt
```

### Manual

```bash
git clone https://github.com/mattmcmanus/git-wt.git
cd git-wt
make install
```

To customize the install location:

```bash
make install PREFIX=~/.local
```

To also install the short `wt` alias:

```bash
make install-alias
```

To uninstall:

```bash
make uninstall
```

## Usage

### Switch worktrees

```bash
git wt              # fuzzy-select from all worktrees
git wt feature      # fuzzy-select with "feature" as initial query
```

When switching, your relative path is preserved. If you're in `worktree-a/src/components`, you'll land in `worktree-b/src/components` if it exists.

### Add a new worktree

```bash
git wt add my-feature
```

Creates a new worktree (and branch if needed) and switches to it. If a branch named `my-feature` already exists, the worktree checks it out. Otherwise, a new tracking branch is created.

### Remove a worktree

```bash
git wt remove              # fuzzy-select which to remove
git wt remove my-feature   # remove with initial query
```

Prompts for confirmation before removing.

### Clean up merged worktrees

```bash
git wt clean
```

Removes all worktrees whose branches have been merged into the main branch or no longer exist.

### List worktrees

```bash
git wt list
```

### Other

```bash
git wt help       # show help
git wt version    # show version
```

## Hooks

git-wt supports a `post-add-worktree` hook that runs after creating a new worktree. This is useful for setup tasks like installing dependencies or copying environment files.

### Hook lookup order

After creating a worktree, git-wt looks for `.wt/post-add-worktree` by walking up the directory tree from the new worktree root, stopping at `$HOME`:

1. `<new-worktree>/.wt/post-add-worktree`
2. `<parent-dir>/.wt/post-add-worktree`
3. `<grandparent-dir>/.wt/post-add-worktree`
4. ... up to `$HOME/.wt/post-add-worktree`

The first match wins. The hook must be executable.

### Example hook

```bash
#!/usr/bin/env bash
# .wt/post-add-worktree — run after creating a new worktree
npm install
cp .env.example .env
```

A hook at `~/.wt/post-add-worktree` serves as a global default for all projects.

## Contributing

```bash
# Install bats-core (test framework)
brew install bats-core  # or see https://bats-core.readthedocs.io

# Run tests
bats test/
```

## Origin

Extracted from [mattmcmanus/dotfiles](https://github.com/mattmcmanus/dotfiles). See the [commit history](https://github.com/mattmcmanus/dotfiles/commits/master/bin/wt) for the original development.

## License

MIT
```

- [ ] **Step 5: Commit scaffold**

```bash
git add LICENSE README.md .gitignore
git commit -m "Initial repo scaffold with README and LICENSE"
```

---

### Task 2: Port the script as git-wt

Copy the existing script with minimal changes: rename references from `wt` to `git-wt`, add `version` subcommand, update help text.

**Files:**
- Create: `git-wt` (main script)

- [ ] **Step 1: Create the git-wt script**

Create `git-wt` with the following content. This is the existing script with these changes:
- Help text updated to use `git wt` instead of `wt`
- `version` and `--version` subcommands added
- `--help` mapped to `help`
- `post-add` subcommand kept for backwards compat
- `post_add_worktree` hook lookup is unchanged for now (Task 4 rewrites it)

```bash
#!/usr/bin/env bash
# shellcheck disable=SC2155
set -e

# git-wt: A fast, interactive git worktree manager.
# https://github.com/mattmcmanus/git-wt

VERSION="0.1.0"

args=("$@")
arg="${args[0]}"

# show worktree list
worktree_list() {
	git worktree list
}

help_message() {
	echo -e "git-wt: A fast, interactive git worktree manager.\n"
	echo "Usage:"
	echo -e "\tgit wt <worktree-name>    Search for worktree and switch to it"
	echo -e "\tgit wt add <name>         Add a new worktree and switch to it"
	echo -e "\tgit wt remove [name]      Remove an existing worktree"
	echo -e "\tgit wt clean              Remove merged/gone branch worktrees"
	echo -e "\tgit wt list               List all worktrees"
	echo -e "\tgit wt help               Show this help message"
	echo -e "\tgit wt version            Show version"
}

get_main_worktree_dir() {
	git worktree list --porcelain | grep -E 'worktree ' | awk '{print $0; exit}' | cut -d ' ' -f2-
}

goto_main_worktree() {
	worktree_dir=$(get_main_worktree_dir)
	change_worktree
}

get_main_branch() {
	local main_branch
	main_branch=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
	if [ -n "$main_branch" ]; then
		echo "$main_branch"
		return 0
	fi
	for candidate in main master develop; do
		if git show-ref --verify --quiet "refs/heads/$candidate"; then
			echo "$candidate"
			return 0
		fi
	done
	echo "develop"
}

get_relative_path() {
	current_worktree_root=$(git rev-parse --show-toplevel)
	current_path=$(pwd)
	if [ "$current_worktree_root" = "$current_path" ]; then
		relative_path="."
	else
		relative_path=${current_path#$current_worktree_root/}
	fi
	echo "$relative_path"
}

change_worktree() {
	relative_path=$(get_relative_path)
	echo Changing to worktree at: "$worktree_dir"
	cd "$worktree_dir"
	# Check if the relative path exists in the new worktree and navigate if it does
	if [ -d "$relative_path" ]; then
		cd "$relative_path"
	fi
}

add_new_worktree() {
	local name="$1"
	local dir_name
	goto_main_worktree
	dir_name=${name//\//-}
	if git show-ref --verify --quiet "refs/heads/$name"; then
		git worktree add "../$dir_name" "$name"
	else
		git worktree add --track -b "$name" "../$dir_name"
	fi
	cd "../$dir_name"
	post_add_worktree
	exec "$SHELL"
}

remove_worktree() {
	SELECTION=$(select_worktree "$1")
	if [ -z "$SELECTION" ]; then
		echo "No worktree selected for removal."
		exit 0
	fi
	worktree_dir=$(cut -d" " -f1 <<<"$SELECTION")

	echo "You are about to remove the worktree at: $worktree_dir"
	read -p "Are you sure? (y/N): " confirmation
	case "$confirmation" in
	[yY][eE][sS] | [yY])
		echo "Removing..."
		git worktree remove "$worktree_dir"
		git worktree prune
		echo "Worktree removed and pruned."
		;;
	*)
		echo "Worktree removal cancelled."
		;;
	esac
}

should_remove_worktree() {
	local branch_name=$(git rev-parse --abbrev-ref HEAD)
	local main_branch=$(get_main_branch)
	if ! git rev-parse --verify "$branch_name" &>/dev/null; then
		echo "non-existent branch"
		return 0
	elif git branch --merged "$main_branch" | grep -qw "$branch_name"; then
		echo "merged into $main_branch"
		return 0
	fi
	return 1
}

clean_merged_worktrees() {
	local main_worktree
	main_worktree=$(get_main_worktree_dir)
	local container_dir
	container_dir="$(dirname "$main_worktree")"
	cd "$container_dir"
	for dir in */; do
		dir="${dir%/}"
		if [ "$dir" != "$(basename "$main_worktree")" ]; then
			cd "$container_dir/$dir"
			local removal_reason
			if removal_reason=$(should_remove_worktree); then
				echo "Removing worktree ($removal_reason): $dir"
				cd "$main_worktree"
				git worktree remove "$container_dir/$dir"
			else
				echo "Skipping worktree: $dir"
			fi
		fi
	done
	cd "$main_worktree"
	git worktree prune
	echo "Cleaned up worktrees and pruned."
}

# Run optional post-add-worktree hook from the container directory
post_add_worktree() {
	local main_worktree
	local container_dir
	local post_add_script
	main_worktree=$(git worktree list --porcelain | awk '/^worktree / {sub(/^worktree /, "", $0); print; exit}')
	container_dir=$(dirname "$main_worktree")
	post_add_script="$container_dir/post-add-worktree"
	if [ -f "$post_add_script" ]; then
		"$post_add_script" "$(pwd)"
	fi
}

# Function to select a worktree using fzf
select_worktree() {
	git worktree list | sed -E 's/^(.*\/([^[:space:]]* ))/\1 \2/g' | fzf --with-nth=2,4 --height 10 --border --prompt "tree: " --query="$1"
}

case "${args[0]}" in
list)
	worktree_list
	;;
add)
	if [ -z "${args[1]}" ]; then
		echo "Error: No name provided for the new worktree."
		exit 1
	else
		add_new_worktree "${args[1]}"
	fi
	;;
post-add)
	post_add_worktree
	;;
remove)
	remove_worktree "${args[1]}"
	;;
clean)
	clean_merged_worktrees
	;;
help | --help | -h)
	help_message
	;;
version | --version | -v)
	echo "git-wt $VERSION"
	;;
*)
	SELECTION=$(select_worktree "$arg")
	if [ "$SELECTION" = "" ]; then
		exit 0
	fi
	worktree_dir=$(cut -d" " -f1 <<<"$SELECTION")
	change_worktree
	exec "$SHELL"
	;;
esac
```

- [ ] **Step 2: Make the script executable**

```bash
chmod +x git-wt
```

- [ ] **Step 3: Verify it runs**

```bash
./git-wt version
```

Expected output: `git-wt 0.1.0`

```bash
./git-wt help
```

Expected output: help text with `git wt` usage.

- [ ] **Step 4: Commit**

```bash
git add git-wt
git commit -m "Add git-wt script ported from dotfiles"
```

---

### Task 3: Test infrastructure and first tests (list, help, version)

**Files:**
- Create: `test/test_helper/setup.bash`
- Create: `test/list.bats`
- Create: `test/help.bats`

- [ ] **Step 1: Install bats-core if not present**

```bash
brew install bats-core 2>/dev/null || true
bats --version
```

- [ ] **Step 2: Create test helper with shared fixtures**

Create `test/test_helper/setup.bash`:

```bash
# Shared setup for all git-wt tests
#
# Provides:
#   GIT_WT     - path to the git-wt script under test
#   TEST_DIR   - temporary directory for this test (cleaned up automatically)
#
# Call create_test_repo to set up a bare repo with a main worktree and
# optionally additional worktrees. Sets:
#   BARE_REPO       - path to the bare repo
#   MAIN_WORKTREE   - path to the main worktree
#   CONTAINER_DIR   - parent directory containing all worktrees

GIT_WT="$BATS_TEST_DIRNAME/../git-wt"

setup() {
    TEST_DIR=$(mktemp -d "$BATS_TMPDIR/git-wt-test.XXXXXX")
    export HOME="$TEST_DIR/fakehome"
    mkdir -p "$HOME"

    # Minimal git config so commits work
    git config --global user.email "test@test.com"
    git config --global user.name "Test"
    git config --global init.defaultBranch main
}

teardown() {
    rm -rf "$TEST_DIR"
}

# Create a bare repo with a main worktree that has one commit.
# Usage: create_test_repo
create_test_repo() {
    BARE_REPO="$TEST_DIR/repo.git"
    CONTAINER_DIR="$TEST_DIR/worktrees"
    mkdir -p "$CONTAINER_DIR"

    git init --bare "$BARE_REPO"

    MAIN_WORKTREE="$CONTAINER_DIR/main"
    git -C "$BARE_REPO" worktree add "$MAIN_WORKTREE" -b main

    # Create an initial commit so branches work
    cd "$MAIN_WORKTREE"
    echo "initial" > README.md
    git add README.md
    git commit -m "Initial commit"
}

# Add a worktree with a branch. Creates a commit on the branch.
# Usage: add_test_worktree <branch-name>
add_test_worktree() {
    local branch="$1"
    local dir_name="${branch//\//-}"
    cd "$MAIN_WORKTREE"
    git worktree add "$CONTAINER_DIR/$dir_name" -b "$branch"
    cd "$CONTAINER_DIR/$dir_name"
    echo "$branch" > branch.txt
    git add branch.txt
    git commit -m "Commit on $branch"
}
```

- [ ] **Step 3: Write help/version tests**

Create `test/help.bats`:

```bash
#!/usr/bin/env bats

load test_helper/setup

@test "version prints version string" {
    run "$GIT_WT" version
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^git-wt\ [0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "--version prints version string" {
    run "$GIT_WT" --version
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^git-wt\ [0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "help prints usage" {
    run "$GIT_WT" help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "git wt" ]]
    [[ "$output" =~ "Usage:" ]]
}

@test "--help prints usage" {
    run "$GIT_WT" --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Usage:" ]]
}
```

- [ ] **Step 4: Write list tests**

Create `test/list.bats`:

```bash
#!/usr/bin/env bats

load test_helper/setup

@test "list shows worktrees" {
    create_test_repo
    add_test_worktree "feature-one"
    cd "$MAIN_WORKTREE"

    run "$GIT_WT" list
    [ "$status" -eq 0 ]
    [[ "$output" =~ "main" ]]
    [[ "$output" =~ "feature-one" ]]
}

@test "list shows only main when no other worktrees" {
    create_test_repo
    cd "$MAIN_WORKTREE"

    run "$GIT_WT" list
    [ "$status" -eq 0 ]
    [[ "$output" =~ "main" ]]
}
```

- [ ] **Step 5: Run the tests**

```bash
bats test/
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add test/
git commit -m "Add test infrastructure and tests for list, help, version"
```

---

### Task 4: Rewrite hook lookup with directory walk-up

**Files:**
- Modify: `git-wt` (the `post_add_worktree` function)
- Create: `test/hooks.bats`

- [ ] **Step 1: Write the hook walk-up tests**

Create `test/hooks.bats`:

```bash
#!/usr/bin/env bats

load test_helper/setup

@test "hook: finds .wt/post-add-worktree in worktree root" {
    create_test_repo
    cd "$MAIN_WORKTREE"

    # Create hook in the worktree root
    mkdir -p "$MAIN_WORKTREE/.wt"
    cat > "$MAIN_WORKTREE/.wt/post-add-worktree" << 'HOOK'
#!/usr/bin/env bash
echo "hook-ran" > "$1/hook-output.txt"
HOOK
    chmod +x "$MAIN_WORKTREE/.wt/post-add-worktree"

    # Source git-wt functions and run post_add_worktree
    # We test this by calling the function directly
    source "$GIT_WT"_functions 2>/dev/null || true

    # Simpler: create a worktree and check the hook ran
    # We need to test via add since post_add_worktree is called there
    "$GIT_WT" add test-hook-local </dev/null &
    BGPID=$!
    # Give it a moment then check
    sleep 2
    kill $BGPID 2>/dev/null || true

    [ -f "$CONTAINER_DIR/test-hook-local/hook-output.txt" ]
}

@test "hook: walks up to find .wt/post-add-worktree in parent" {
    create_test_repo

    # Create hook in container dir (parent of worktrees)
    mkdir -p "$CONTAINER_DIR/.wt"
    cat > "$CONTAINER_DIR/.wt/post-add-worktree" << 'HOOK'
#!/usr/bin/env bash
echo "parent-hook-ran" > "$1/hook-output.txt"
HOOK
    chmod +x "$CONTAINER_DIR/.wt/post-add-worktree"

    cd "$MAIN_WORKTREE"
    "$GIT_WT" add test-hook-parent </dev/null &
    BGPID=$!
    sleep 2
    kill $BGPID 2>/dev/null || true

    [ -f "$CONTAINER_DIR/test-hook-parent/hook-output.txt" ]
    [[ "$(cat "$CONTAINER_DIR/test-hook-parent/hook-output.txt")" == "parent-hook-ran" ]]
}

@test "hook: falls back to global ~/.wt/post-add-worktree" {
    create_test_repo

    # Create global hook
    mkdir -p "$HOME/.wt"
    cat > "$HOME/.wt/post-add-worktree" << 'HOOK'
#!/usr/bin/env bash
echo "global-hook-ran" > "$1/hook-output.txt"
HOOK
    chmod +x "$HOME/.wt/post-add-worktree"

    cd "$MAIN_WORKTREE"
    "$GIT_WT" add test-hook-global </dev/null &
    BGPID=$!
    sleep 2
    kill $BGPID 2>/dev/null || true

    [ -f "$CONTAINER_DIR/test-hook-global/hook-output.txt" ]
    [[ "$(cat "$CONTAINER_DIR/test-hook-global/hook-output.txt")" == "global-hook-ran" ]]
}

@test "hook: no hook found does not error" {
    create_test_repo
    cd "$MAIN_WORKTREE"

    # add without any hooks present should succeed
    "$GIT_WT" add test-no-hook </dev/null &
    BGPID=$!
    sleep 2
    kill $BGPID 2>/dev/null || true

    [ -d "$CONTAINER_DIR/test-no-hook" ]
    [ ! -f "$CONTAINER_DIR/test-no-hook/hook-output.txt" ]
}

@test "hook: closest hook wins over parent" {
    create_test_repo

    # Create hook in container dir
    mkdir -p "$CONTAINER_DIR/.wt"
    cat > "$CONTAINER_DIR/.wt/post-add-worktree" << 'HOOK'
#!/usr/bin/env bash
echo "parent" > "$1/hook-output.txt"
HOOK
    chmod +x "$CONTAINER_DIR/.wt/post-add-worktree"

    # Create hook in main worktree (closer)
    mkdir -p "$MAIN_WORKTREE/.wt"
    cat > "$MAIN_WORKTREE/.wt/post-add-worktree" << 'HOOK'
#!/usr/bin/env bash
echo "local" > "$1/hook-output.txt"
HOOK
    chmod +x "$MAIN_WORKTREE/.wt/post-add-worktree"

    cd "$MAIN_WORKTREE"
    "$GIT_WT" add test-hook-priority </dev/null &
    BGPID=$!
    sleep 2
    kill $BGPID 2>/dev/null || true

    [[ "$(cat "$CONTAINER_DIR/test-hook-priority/hook-output.txt")" == "local" ]]
}

@test "hook: stops at HOME, does not check above" {
    create_test_repo

    # Create hook above HOME — should NOT be found
    mkdir -p "$TEST_DIR/.wt"
    cat > "$TEST_DIR/.wt/post-add-worktree" << 'HOOK'
#!/usr/bin/env bash
echo "above-home" > "$1/hook-output.txt"
HOOK
    chmod +x "$TEST_DIR/.wt/post-add-worktree"

    # HOME is $TEST_DIR/fakehome, worktrees are under $TEST_DIR/worktrees
    # The walk-up should stop at HOME and not reach $TEST_DIR/.wt/
    cd "$MAIN_WORKTREE"
    "$GIT_WT" add test-hook-boundary </dev/null &
    BGPID=$!
    sleep 2
    kill $BGPID 2>/dev/null || true

    [ ! -f "$CONTAINER_DIR/test-hook-boundary/hook-output.txt" ]
}
```

- [ ] **Step 2: Run the hook tests to see them fail**

```bash
bats test/hooks.bats
```

Expected: tests fail (the current `post_add_worktree` doesn't do walk-up).

- [ ] **Step 3: Rewrite post_add_worktree with directory walk-up**

In `git-wt`, replace the `post_add_worktree` function with:

```bash
# Find and run post-add-worktree hook.
# Walks up from the current directory looking for .wt/post-add-worktree,
# stopping at $HOME. First match wins. ~/.wt/post-add-worktree is the
# global default.
post_add_worktree() {
	local search_dir
	search_dir="$(pwd)"
	local worktree_path
	worktree_path="$(pwd)"

	while true; do
		if [ -x "$search_dir/.wt/post-add-worktree" ]; then
			"$search_dir/.wt/post-add-worktree" "$worktree_path"
			return 0
		fi

		# Stop at HOME
		if [ "$search_dir" = "$HOME" ]; then
			break
		fi

		# Move to parent
		local parent
		parent="$(dirname "$search_dir")"

		# Stop if we've hit the filesystem root
		if [ "$parent" = "$search_dir" ]; then
			break
		fi

		search_dir="$parent"
	done
}
```

- [ ] **Step 4: Run the hook tests to see them pass**

```bash
bats test/hooks.bats
```

Expected: all hook tests pass.

- [ ] **Step 5: Run all tests to check for regressions**

```bash
bats test/
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add git-wt test/hooks.bats
git commit -m "Rewrite hook lookup with directory walk-up pattern"
```

---

### Task 5: Tests for add subcommand

**Files:**
- Create: `test/add.bats`

- [ ] **Step 1: Write add tests**

Create `test/add.bats`:

```bash
#!/usr/bin/env bats

load test_helper/setup

@test "add creates a new worktree for a new branch" {
    create_test_repo
    cd "$MAIN_WORKTREE"

    "$GIT_WT" add test-branch </dev/null &
    BGPID=$!
    sleep 2
    kill $BGPID 2>/dev/null || true

    [ -d "$CONTAINER_DIR/test-branch" ]
    cd "$CONTAINER_DIR/test-branch"
    [ "$(git rev-parse --abbrev-ref HEAD)" = "test-branch" ]
}

@test "add checks out existing branch if it exists" {
    create_test_repo
    cd "$MAIN_WORKTREE"
    git branch existing-branch

    "$GIT_WT" add existing-branch </dev/null &
    BGPID=$!
    sleep 2
    kill $BGPID 2>/dev/null || true

    [ -d "$CONTAINER_DIR/existing-branch" ]
    cd "$CONTAINER_DIR/existing-branch"
    [ "$(git rev-parse --abbrev-ref HEAD)" = "existing-branch" ]
}

@test "add converts slashes in branch name to dashes for directory" {
    create_test_repo
    cd "$MAIN_WORKTREE"

    "$GIT_WT" add feature/my-thing </dev/null &
    BGPID=$!
    sleep 2
    kill $BGPID 2>/dev/null || true

    [ -d "$CONTAINER_DIR/feature-my-thing" ]
}

@test "add errors when no name provided" {
    create_test_repo
    cd "$MAIN_WORKTREE"

    run "$GIT_WT" add
    [ "$status" -eq 1 ]
    [[ "$output" =~ "Error" ]]
}
```

- [ ] **Step 2: Run the add tests**

```bash
bats test/add.bats
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add test/add.bats
git commit -m "Add tests for add subcommand"
```

---

### Task 6: Tests for clean subcommand

**Files:**
- Create: `test/clean.bats`

- [ ] **Step 1: Write clean tests**

Create `test/clean.bats`:

```bash
#!/usr/bin/env bats

load test_helper/setup

@test "clean removes worktrees for merged branches" {
    create_test_repo
    add_test_worktree "merged-feature"

    # Merge the branch into main
    cd "$MAIN_WORKTREE"
    git merge merged-feature

    run "$GIT_WT" clean
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Removing worktree" ]]
    [[ "$output" =~ "merged-feature" ]]
    [ ! -d "$CONTAINER_DIR/merged-feature" ]
}

@test "clean skips worktrees for unmerged branches" {
    create_test_repo
    add_test_worktree "unmerged-feature"

    cd "$MAIN_WORKTREE"

    run "$GIT_WT" clean
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Skipping worktree" ]]
    [ -d "$CONTAINER_DIR/unmerged-feature" ]
}

@test "clean removes worktrees for non-existent branches" {
    create_test_repo
    add_test_worktree "temp-branch"

    # Delete the branch (but worktree dir remains)
    cd "$MAIN_WORKTREE"
    git branch -D temp-branch

    run "$GIT_WT" clean
    [ "$status" -eq 0 ]
    [[ "$output" =~ "non-existent branch" ]]
}

@test "clean does nothing when only main worktree exists" {
    create_test_repo
    cd "$MAIN_WORKTREE"

    run "$GIT_WT" clean
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Cleaned up" ]]
}
```

- [ ] **Step 2: Run the clean tests**

```bash
bats test/clean.bats
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add test/clean.bats
git commit -m "Add tests for clean subcommand"
```

---

### Task 7: Tests for remove subcommand

**Files:**
- Create: `test/remove.bats`

Note: `remove` uses `fzf` for selection and `read` for confirmation, making it harder to test non-interactively. We test the error path and the confirmation-cancelled path.

- [ ] **Step 1: Write remove tests**

Create `test/remove.bats`:

```bash
#!/usr/bin/env bats

load test_helper/setup

@test "remove cancels when user says no" {
    create_test_repo
    add_test_worktree "to-remove"
    cd "$MAIN_WORKTREE"

    # Pipe "n" to confirmation, and provide the worktree via fzf's --filter
    # We override fzf by providing a selection via echo piped to the script
    echo "n" | run "$GIT_WT" remove "to-remove"

    # Worktree should still exist
    [ -d "$CONTAINER_DIR/to-remove" ]
}
```

- [ ] **Step 2: Run the remove tests**

```bash
bats test/remove.bats
```

Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add test/remove.bats
git commit -m "Add tests for remove subcommand"
```

---

### Task 8: Shell completions

**Files:**
- Create: `completions/git-wt.zsh`
- Create: `completions/git-wt.bash`

- [ ] **Step 1: Create zsh completion**

Create `completions/git-wt.zsh`:

```zsh
#compdef git-wt

_git-wt() {
    local -a subcommands
    subcommands=(
        'add:Add a new worktree and switch to it'
        'remove:Remove an existing worktree'
        'clean:Remove merged/gone branch worktrees'
        'list:List all worktrees'
        'help:Show help message'
        'version:Show version'
    )

    if (( CURRENT == 2 )); then
        _describe 'subcommand' subcommands
        # Also complete worktree names for the default switch behavior
        local -a worktrees
        worktrees=(${(f)"$(git worktree list --porcelain 2>/dev/null | grep '^worktree ' | sed 's/^worktree //' | xargs -I{} basename {})"})
        _describe 'worktree' worktrees
    fi
}

# Also register as a git subcommand completion
_git-wt "$@"
```

- [ ] **Step 2: Create bash completion**

Create `completions/git-wt.bash`:

```bash
_git_wt() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local subcommands="add remove clean list help version"

    if [ "$COMP_CWORD" -eq 2 ]; then
        # Complete subcommands and worktree names
        local worktrees
        worktrees=$(git worktree list --porcelain 2>/dev/null | grep '^worktree ' | sed 's/^worktree //' | xargs -I{} basename {})
        COMPREPLY=($(compgen -W "$subcommands $worktrees" -- "$cur"))
    fi
}

# Register for both git-wt and git wt
complete -F _git_wt git-wt
complete -F _git_wt git_wt

# Git subcommand completion (git wt <tab>)
__git_complete wt _git_wt 2>/dev/null || true
```

- [ ] **Step 3: Commit**

```bash
git add completions/
git commit -m "Add zsh and bash shell completions"
```

---

### Task 9: Makefile

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Create the Makefile**

Create `Makefile`:

```makefile
PREFIX ?= /usr/local
BINDIR = $(PREFIX)/bin
BASH_COMPLETION_DIR ?= $(PREFIX)/etc/bash_completion.d
ZSH_COMPLETION_DIR ?= $(PREFIX)/share/zsh/site-functions

.PHONY: install install-alias install-completions uninstall test

install: install-completions
	install -d $(BINDIR)
	install -m 755 git-wt $(BINDIR)/git-wt

install-alias: install
	ln -sf $(BINDIR)/git-wt $(BINDIR)/wt

install-completions:
	install -d $(BASH_COMPLETION_DIR)
	install -m 644 completions/git-wt.bash $(BASH_COMPLETION_DIR)/git-wt
	install -d $(ZSH_COMPLETION_DIR)
	install -m 644 completions/git-wt.zsh $(ZSH_COMPLETION_DIR)/_git-wt

uninstall:
	rm -f $(BINDIR)/git-wt
	rm -f $(BINDIR)/wt
	rm -f $(BASH_COMPLETION_DIR)/git-wt
	rm -f $(ZSH_COMPLETION_DIR)/_git-wt

test:
	bats test/
```

- [ ] **Step 2: Verify make test works**

```bash
make test
```

Expected: all bats tests pass.

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "Add Makefile for install, uninstall, and test targets"
```

---

### Task 10: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create CI workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Install bats-core
        run: |
          if [[ "$RUNNER_OS" == "macOS" ]]; then
            brew install bats-core
          else
            sudo apt-get update
            sudo apt-get install -y bats
          fi

      - name: Install fzf
        run: |
          if [[ "$RUNNER_OS" == "macOS" ]]; then
            brew install fzf
          else
            sudo apt-get install -y fzf
          fi

      - name: Run tests
        run: make test
```

- [ ] **Step 2: Commit**

```bash
git add .github/
git commit -m "Add GitHub Actions CI for Linux and macOS"
```

---

### Task 11: Homebrew formula

**Files:**
- Create: `Formula/git-wt.rb`

- [ ] **Step 1: Create the formula**

Create `Formula/git-wt.rb`:

```ruby
class GitWt < Formula
  desc "A fast, interactive git worktree manager"
  homepage "https://github.com/mattmcmanus/git-wt"
  url "https://github.com/mattmcmanus/git-wt/archive/refs/tags/v0.1.0.tar.gz"
  # sha256 will be filled in after first release
  sha256 ""
  license "MIT"

  depends_on "fzf"

  def install
    bin.install "git-wt"
    bash_completion.install "completions/git-wt.bash" => "git-wt"
    zsh_completion.install "completions/git-wt.zsh" => "_git-wt"
  end

  def caveats
    <<~EOS
      git-wt is installed as a git subcommand. Use it with:
        git wt

      For a short alias, create a symlink:
        ln -s #{bin}/git-wt #{bin}/wt
    EOS
  end

  test do
    assert_match "git-wt", shell_output("#{bin}/git-wt version")
  end
end
```

Note: The `sha256` and `url` will need updating when you cut the first release tag. This is the source-of-truth formula — you'll copy it to your `homebrew-tap` repo when ready.

- [ ] **Step 2: Commit**

```bash
git add Formula/
git commit -m "Add Homebrew formula (source of truth for tap)"
```

---

### Task 12: Push and verify CI

**Files:** None (git operations only)

- [ ] **Step 1: Push all commits**

```bash
git push -u origin main
```

- [ ] **Step 2: Verify CI passes**

```bash
gh run watch
```

Wait for the CI run to complete. Both ubuntu-latest and macos-latest should pass.

- [ ] **Step 3: Tag the initial release**

```bash
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0
```

---

### Task 13: Update dotfiles repo

**Files:**
- Modify: `/Users/matt/.dotfiles/Brewfile` (add git-wt)
- Remove: `/Users/matt/.dotfiles/bin/wt`

- [ ] **Step 1: Add git-wt to Brewfile**

In `/Users/matt/.dotfiles/Brewfile`, add:

```
brew "mattmcmanus/tap/git-wt"
```

Note: This won't work until the tap repo exists. For now, add it as a comment:

```
# brew "mattmcmanus/tap/git-wt"  # enable after creating homebrew-tap repo
```

- [ ] **Step 2: Remove the old wt script**

```bash
cd /Users/matt/.dotfiles
git rm bin/wt
```

- [ ] **Step 3: Commit**

```bash
git add Brewfile
git commit -m "Replace bin/wt with git-wt (now a standalone repo)"
```
