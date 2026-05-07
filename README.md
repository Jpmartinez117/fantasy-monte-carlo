# Fantasy Football Monte Carlo Draft Helper

This project provides an offline command-line tool to assist with fantasy football drafts using
Monte Carlo simulations. It's designed with a modular architecture to keep components
separated and easy to understand.

## Project Structure

```
fantasy-monte-carlo/
│
├── data/                          # CSV datasets
│   ├── players.csv
│   └── players_bad.csv            # intentionally malformed; used by loader tests
│
├── docs/
│   └── SCHEMA.md                  # CSV schema and validation rules
│
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── player.py              # Player dataclass + VALID_POSITIONS
│   │
│   ├── data_loader/
│   │   ├── __init__.py
│   │   ├── base.py                # PlayerDataProvider ABC + DataLoadError
│   │   └── csv_loader.py          # CsvPlayerProvider implementation
│   │
│   ├── simulation/
│   │   ├── __init__.py
│   │   └── monte_carlo.py         # run_simulation + SimulationResults
│   │
│   ├── stats/
│   │   ├── __init__.py
│   │   └── statistics_engine.py   # compute_stats, rank_players, head_to_head
│   │
│   └── cli/
│       ├── __init__.py
│       ├── main.py                # argparse entry point + rankings/h2h modes
│       └── draft_session.py       # interactive --draft REPL
│
├── tests/
│   ├── __init__.py
│   ├── test_loader.py             # 24 tests — CSV header, validation, duplicates
│   ├── test_simulation.py         # 13 tests — Monte Carlo input/output/reproducibility
│   ├── test_stats.py              # 14 tests — percentiles, compute_stats, rank
│   ├── test_h2h.py                # 10 tests — head-to-head edge cases
│   ├── test_cli.py                # 13 tests — subprocess-driven CLI smoke tests
│   └── test_draft_session.py      #  8 tests — _resolve_pick unit tests
│
├── README.md
├── requirements.txt
└── .gitignore
```

The codebase implements a complete MVP-1 fantasy draft helper: CSV ingestion with
validation, a Monte Carlo simulation engine, a statistics engine for per-player
percentiles and head-to-head matchups, and a command-line interface offering
ranked tables, position filters, head-to-head comparisons, and an interactive
draft session.

## How to Run

### 1. Install

Python 3.10+ is required. The only runtime dependency is `pytest` (used for tests).

```bash
pip install -r requirements.txt
```

### 2. Run the CLI

All commands are invoked as a module so the `src.` package imports resolve cleanly.

**Default rankings table** (loads `data/players.csv`, runs 10,000 simulations):

```bash
python -m src.cli.main
```

**Filter and slice the rankings:**

```bash
python -m src.cli.main --pos QB --top 5
```

**Head-to-head comparison** between two rosters (comma-separated names):

```bash
python -m src.cli.main --h2h "Josh Harper,Derrick Miles" "Patrick Keller,Christian Grant"
```

**Interactive draft session** — pick by rank number or by name substring; type `q` to quit:

```bash
python -m src.cli.main --draft
```

**Use a different CSV file or simulation count:**

```bash
python -m src.cli.main --file data/players.csv --sims 50000
```

**Full flag reference:**

```bash
python -m src.cli.main --help
```

### 3. Run the tests

```bash
python -m pytest
```

The full suite is currently **82 tests** across loader, simulation, stats,
head-to-head, CLI subprocess smoke tests, and draft-session unit tests.

## Updates

### Task 1 — Cleanup

#### 1a. Removed stray `data/data_loader.py`
- **What:** Deleted `data/data_loader.py`, a tombstone file containing only a comment that pointed readers to `src/data_loader/csv_loader.py`.
- **Why:** The file lived under `data/` (a CSV-only directory), wasn't imported anywhere, and could mislead newcomers into thinking the loader had two implementations.
- **Result:** `data/` now contains only the CSV datasets (`players.csv`, `players_bad.csv`). All 61 tests still pass.

#### 1b. Cleared `__pycache__` directories from the working tree
- **What:** Deleted all seven `__pycache__/` directories under `src/` and `tests/`.
- **Why:** They are build artifacts regenerated automatically by Python on each run. Verified `.gitignore` already excludes `__pycache__/` and `*.py[cod]`, and confirmed via `git ls-files` that none were ever tracked.
- **Result:** Working tree is free of compiled-bytecode clutter. `.gitignore` was unchanged — already correct. Tests still pass (61/61); pytest will regenerate caches as needed on the next run.

#### 1c. Removed stray trailing `1` from `src/data_loader/base.py`
- **What:** The file ended with a literal `1` character on its own line (no trailing newline). Removed it so the file ends with the closing docstring of `DataLoadError` followed by a single newline.
- **Why:** The character was almost certainly an accidental keystroke. Python parsed it as a valid integer-literal expression statement (a no-op), so the module imported fine and all tests passed — but it was clearly unintended garbage and would have looked like a typo or version marker to a future reader.
- **Result:** File ends cleanly. No behavior change. Tests still pass (61/61).

#### 1d. Audited `__init__.py` re-exports across all packages
- **What:** Inspected every `__init__.py` in the project and cross-referenced against actual import statements in the codebase.
- **Findings:**
  - `src/models/`, `src/data_loader/`, `src/simulation/`, and `src/stats/` each correctly re-export their public symbols and declare `__all__`.
  - `src/__init__.py`, `src/cli/__init__.py`, and `tests/__init__.py` contain only a docstring — appropriate, since they are a top-level namespace, an entry point, and a test-package marker respectively.
  - Internal call sites consistently import from full module paths (e.g. `from src.models.player import Player`) rather than going through the package re-exports. The re-exports therefore form the documented public API surface for any future external consumer, even though no current code relies on them.
- **Why:** Confirms the package boundary is well-defined and that no `__init__.py` is missing required re-exports or carrying broken imports.
- **Result:** No code changes required. All 61 tests still pass.

### Task 2 — CLI End-to-End Verification

All six smoke tests below were executed against the real `data/players.csv` and confirmed to behave correctly. No code changes were made — this task is verification only.

#### 2a. Default rankings (`python -m src.cli.main`)
- Loads 26 players, runs 10,000 simulations, prints a fully formatted table sorted by mean. ✅ Pass.

#### 2b. Position filter + top slice (`--pos QB --top 5`)
- Output limited to the top 5 quarterbacks. Filter and slice both apply. ✅ Pass.

#### 2c. Head-to-head (`--h2h "Josh Harper,Derrick Miles" "Patrick Keller,Christian Grant"`)
- Prints win-percentage breakdown, average margin, and per-team weekly totals. Result was a near 50/50 split as expected for evenly matched rosters. ✅ Pass.

#### 2d. Interactive draft session (`--draft`)
- Drove the REPL via piped stdin: rank `1` → Patrick Keller drafted, rank `2` → Jalen Fields, name `Josh` → Josh Harper resolved by substring match, `q` → session ended. Final recap printed all three picks in draft order. ✅ Pass.
- **Minor finding:** the em-dash in the "Remaining depth —" line renders as `�` when stdout is piped on Windows (cp1252 fallback). Not visible in an interactive terminal. Logged as cosmetic; not a blocker.

#### 2e. Bad CSV (`--file data/players_bad.csv`)
- Loader emitted 11 row-level warnings (non-numeric values, out-of-range, invalid position, empty name, wrong column count, duplicate, etc.) and continued. Simulation ran on the single valid player (Gabe Repeat). ✅ Pass.

#### 2f. Missing CSV (`--file data/missing.csv`)
- Printed `[ERROR] File not found: data\missing.csv` and exited with status code `1`. ✅ Pass.

### Task 3 — CLI Test Coverage

Closed the only remaining MVP gap: prior to this task, every layer below the CLI had unit tests but the CLI itself was only verified by manual smoke tests (Task 2). Added two new test files totaling 21 new tests; full suite now 82/82.

#### 3a–3d. Subprocess-driven CLI tests (`tests/test_cli.py`)
- **What:** New file invoking `python -m src.cli.main` as a subprocess against a small temporary CSV fixture (5 players). Each test asserts on exit code and a few load-bearing strings in stdout — smoke-only, since math correctness is already covered by simulation/stats unit tests.
- **Tests added (13 total, organized into 4 classes):**
  - `TestDefaultRankings` (3a) — exit code, "Loaded 5 players" message, table header + all player names present, rank #1 is the highest-mean player.
  - `TestFilterAndSlice` (3b) — `--pos QB` includes only QBs, `--top 2` limits rows, combined `--pos QB --top 1` returns one player, position filter with no matches still exits 0 and warns.
  - `TestHeadToHead` (3c) — `--h2h` happy path prints win-percentage summary; unknown player name fails with exit 1 and "Player not found".
  - `TestFailurePaths` (3d) — missing file → exit 1 + "ERROR" + "not found"; `--sims 0` rejected by argparse (exit 2); `--draft` with `--h2h` rejected as mutually exclusive.
- **Implementation notes:** Used `--sims 100` everywhere to keep total wall time low; passed `encoding="utf-8"` to subprocess so the em-dash issue from Task 2's draft-session output doesn't cause spurious decode errors on Windows.

#### 3e. Direct unit tests for `_resolve_pick` (`tests/test_draft_session.py`)
- **What:** Unit tests that exercise `_resolve_pick` directly, no subprocess required. The function is the only real logic in `draft_session.py` (everything else is print/input I/O), so testing it as a function gives near-complete coverage of pick resolution at unit-test speed.
- **Tests added (8 total, organized into 2 classes):**
  - `TestNumericPick` — rank 1 returns first player, mid-range rank works, rank 0 returns None, rank above range returns None.
  - `TestNamePick` — unique substring match, case insensitivity, no match returns None, ambiguous substring returns None and prints a disambiguation message (verified via `capsys`).
- **Why unit tests instead of subprocess for this:** the draft REPL is interactive and would require driving stdin via subprocess. Pure-function tests are faster and more precise; the REPL loop itself was already exercised manually in Task 2d.

#### Test suite totals
- Before Task 3: 61 tests passing
- After Task 3: **82 tests passing** (+13 CLI subprocess + 8 draft-session unit)

### Task 4 — Documentation

#### 4a. Refreshed the project tree
- **What:** Replaced the project-tree section with the actual current layout. The previous tree was written before the codebase was finished and was missing `stats/`, `data_loader/base.py`, `cli/draft_session.py`, `docs/SCHEMA.md`, and most test files; it also still listed packages as "placeholder modules initially."
- **Result:** Tree now reflects the real file set, with one-line descriptions next to each non-obvious file (e.g. what `base.py` contributes, the role of each test file with test counts).

#### 4b. Added a "How to Run" section
- **What:** New top-level section documenting install, four representative CLI invocations (default rankings, filter + slice, head-to-head, interactive draft, custom file/sims), the `--help` reference, and how to run the test suite.
- **Why:** Lowers the bar to first contact. Anyone cloning the repo can now install dependencies, run the CLI, and execute the tests without reading source code first.
- **Result:** README now contains executable commands a new user can copy directly. Examples use the same player names that exist in `data/players.csv` so they work out of the box.

#### 4c. Verified `docs/SCHEMA.md` against the loader implementation
- **What:** Cross-checked every rule in `docs/SCHEMA.md` against `src/data_loader/csv_loader.py` and `src/models/player.py`.
- **Findings:**
  - Header `Name,Position,Mean,StdDev` — matches `EXPECTED_HEADER` constant.
  - Position validation `{QB,RB,WR,TE}` — matches `VALID_POSITIONS` set; loader uppercases input before checking.
  - Mean range `0–60` and StdDev range `0–25` — both enforced in `_validate_row` with inclusive bounds.
  - NaN/Infinity rejection — implemented via `math.isfinite` in `_parse_float`.
  - Exactly 4 columns per row — enforced before field validation.
  - Duplicate `(Name, Position)` — loader keeps first occurrence and warns on subsequent matches.
  - "Collapse multiple internal spaces in Name" is documented as **optional** in the spec and is intentionally not implemented (only `.strip()` is applied). Spec wording is already accurate.
- **Result:** SCHEMA.md is fully aligned with current loader behavior. No edits required.
