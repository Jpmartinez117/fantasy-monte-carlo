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

### Task 5 — Bug Fixes from Audit (round 1)

A whole-project audit identified five small bugs and three robustness gaps. This round closes the three CSV-loader issues, which all live in the same file-read pipeline and were cleanest to fix together.

#### Fix #1. UTF-8 BOM at start of file no longer breaks the header check
- **Bug:** Files saved by Excel, Google Sheets, or Notepad++ start with a UTF-8 BOM (`﻿`). Reading with `encoding="utf-8"` made the first header field decode as `"﻿Name"`, which failed `EXPECTED_HEADER` comparison and raised `DataLoadError("Bad header: ...")` even though the file was valid.
- **Fix:** `src/data_loader/csv_loader.py` now reads with `encoding="utf-8-sig"`, which transparently strips the BOM if present and otherwise behaves identically to UTF-8.
- **New test:** `TestFileEncoding::test_utf8_bom_at_start_of_file_is_handled` writes a BOM-prefixed CSV via `tmp_path` and asserts the player loads cleanly.

#### Fix #2. Non-UTF-8 files now raise a friendly `DataLoadError` instead of a traceback
- **Bug:** A CSV saved as cp1252/latin-1 (default for many Windows tools) raised a raw `UnicodeDecodeError` from `Path.read_text`. The exception was uncaught and surfaced as a Python traceback to the user.
- **Fix:** `load_players()` now catches `UnicodeDecodeError` and re-raises as `DataLoadError("File is not valid UTF-8: ... Re-save the CSV as UTF-8 and try again.")`. The CLI's existing `DataLoadError` handler then prints `[ERROR] ...` and exits cleanly with status 1.
- **New test:** `TestFileEncoding::test_non_utf8_file_raises_friendly_error` writes raw cp1252 bytes via `tmp_path` and asserts a `DataLoadError` matching `"UTF-8"`.

#### Fix #7. Quoted multi-line fields are now parsed correctly
- **Bug:** `_parse_csv` previously called `csv.reader(text.splitlines())`, which pre-splits the file into individual lines before the CSV parser sees it. A quoted field containing a literal newline (e.g. `"Smith\nJr."`) was therefore broken into two rows, each failing column-count validation.
- **Fix:** Now uses `csv.reader(io.StringIO(text))`, which preserves embedded newlines inside quoted fields. As a side benefit, `reader.line_num` is used for warning line numbers — equivalent for one-line rows, but more accurate when a row spans multiple physical lines.
- **New test:** `TestEmbeddedNewlines::test_quoted_field_with_embedded_newline_parses_as_one_row` confirms the row is treated as a single cell with no spurious column-count warnings.

#### Test suite totals
- Before round-1 fixes: 82 tests passing
- After round-1 fixes: **85 tests passing** (+3 new loader tests). All previously-passing tests still pass — the change is fully backward compatible.

### Task 6 — Bug Fixes from Audit (round 2)

Closes the two robustness/UX bugs in the draft session REPL.

#### Fix #6. Ctrl-C / EOF in the draft REPL no longer crashes with a traceback
- **Bug:** During `--draft`, the REPL called `input()` directly. Hitting Ctrl-C raised `KeyboardInterrupt` and Ctrl-Z + Enter (Windows) or Ctrl-D (Unix) raised `EOFError`. Both surfaced as a Python traceback to the user.
- **Fix:** `src/cli/draft_session.py` now wraps the `input()` call in `try/except (KeyboardInterrupt, EOFError)` and breaks out of the loop with an `"Draft session interrupted."` message. Any picks made before the interrupt still appear in the final recap.
- **New tests:**
  - `TestDraftSession::test_eof_on_first_prompt_exits_cleanly` — sends empty stdin and asserts exit code 0, no `Traceback` in stderr, "interrupted" message in stdout.
  - `TestDraftSession::test_eof_after_one_pick_shows_recap` — sends one pick then EOF and asserts the recap (`DRAFT RECAP`) prints with the chosen player.

#### Fix #3. Empty input no longer matches every player on the board
- **Bug:** Pressing Enter with no input left `pick = ""`, which made the substring fallback match every available player (`"" in any_name.lower()` is always True). The user got an "Ambiguous" message listing the entire board, looking like a bug.
- **Fix:** Added `if not pick: continue` between the quit-check and the resolution call so an empty pick silently re-prompts. Bundled into the same patch as #6 since it sits in the same loop.
- **New test:**
  - `TestDraftSession::test_empty_pick_is_ignored_and_does_not_match_all_players` — sends `"\nq\n"` and asserts the ambiguity message never appears and no player is drafted.

#### Test infrastructure note
- The new draft-session subprocess tests exposed the Windows em-dash piping issue from Task 2d (the `—` byte in `"Remaining depth —"` is invalid UTF-8 when the child's stdout falls back to cp1252). Resolved at the test boundary by setting `PYTHONIOENCODING=utf-8` in `run_cli`'s subprocess env. End-user behavior is unchanged; this just makes piped output on Windows decode cleanly during tests.

#### Test suite totals
- Before round-2 fixes: 85 tests passing
- After round-2 fixes: **88 tests passing** (+3 new draft-session subprocess tests). Backward compatible.

### Task 7 — Bug Fixes from Audit (round 3)

Closes the remaining three audit findings: head-to-head input validation (#4, #5) and Player whitespace-name validation (#8).

#### Fix #4. Head-to-head rejects within-team duplicate players
- **Bug:** `head_to_head` accepted a roster with the same player listed twice (e.g. `["Josh Harper", "Josh Harper"]`). The duplicate's score was added to the team total each time, silently inflating the result. A typo on the CLI's comma-split path (e.g. `"Smith, Jr."` accidentally splitting a comma-containing name) could produce this without warning.
- **Fix:** `src/stats/statistics_engine.py` now raises `ValueError("Team A has duplicate players")` (or "Team B") when `len(set(names)) != len(names)`. Cross-team duplicates (the same player on both rosters) are still allowed — that's a degenerate but well-defined scenario the simulator handles correctly.
- **New tests:** `test_team_a_with_duplicate_player_raises`, `test_team_b_with_duplicate_player_raises`, `test_same_player_on_both_teams_is_allowed`.

#### Fix #5. Head-to-head rejects empty rosters
- **Bug:** Passing an empty list for one team gave the other team a 100% win rate against zero points, returning a misleading `H2HResult`.
- **Fix:** Added `if not team_a_names: raise ValueError("Team A roster cannot be empty")` (and equivalent for B) at the top of `head_to_head`.
- **New tests:** `test_empty_team_a_raises`, `test_empty_team_b_raises`.

#### Fix #8. `Player(name="   ")` is now rejected
- **Bug:** `Player.__post_init__` checked `if not self.name`, which is `False` for any whitespace-only string (those are truthy in Python). The CSV loader already strips before constructing, so the file path was safe — but anyone constructing `Player` directly (tests, future modules) could create a "blank-named" player.
- **Fix:** Changed the check to `if not self.name.strip():` in `src/models/player.py`. Empty and whitespace-only names are now both rejected with `ValueError("Player name cannot be empty")`.
- **New file:** `tests/test_player.py` with seven tests covering valid construction, empty/whitespace/tab-only name rejection, and the existing position / mean / stddev range guards.

#### Test suite totals
- Before round-3 fixes: 88 tests passing
- After round-3 fixes: **100 tests passing** (+5 new h2h validation tests + 7 new player validation tests). Backward compatible.

#### Audit closeout
All eight findings from the project audit are now resolved:
| # | Issue | Round |
|---|---|---|
| #1 | UTF-8 BOM breaks header check | 1 |
| #2 | Non-UTF-8 file → uncaught traceback | 1 |
| #7 | Quoted multi-line field misparsed | 1 |
| #6 | Ctrl-C / EOF in draft REPL crashes | 2 |
| #3 | Empty draft input matches every player | 2 |
| #4 | Head-to-head ignores within-team duplicates | 3 |
| #5 | Head-to-head accepts empty rosters | 3 |
| #8 | Whitespace-only Player name passes validation | 3 |

The clamping bias and Windows-pipe em-dash items remain documented as known accepted limitations, not bugs.

### Task 8 — Optimization Pass (in progress)

A whole-codebase audit identified eight low-risk improvements across performance, readability, and maintainability — all within MVP scope (no new dependencies, no architectural shifts). Picking off the highest-value ones in small, isolated commits.

#### Opt #O1. Monte Carlo loop inversion + pre-allocated lists
- **What:** Replaced the nested `for sim in range(N): for player in players: scores[name].append(...)` pattern with a single dict comprehension that builds each player's full sample list in one pass:
  ```python
  scores = {
      p.name: [max(0.0, rng.gauss(p.mean, p.std_dev)) for _ in range(n_simulations)]
      for p in players
  }
  ```
- **Why:** Avoids one dict lookup per draw and lets the inner list comprehension pre-size each list, sidestepping the incremental `.append`/resize cost. Reads as a direct expression of intent ("each player's batch of N draws").
- **Behavior change to be aware of:** the RNG draw order changes from per-trial-interleaved (`p1_sim1, p2_sim1, ..., p1_sim2, ...`) to per-player-batched (`p1_sim1, p1_sim2, ..., p1_simN, p2_sim1, ...`). For any given seed, the exact numeric output therefore differs from the previous version — but the statistical properties (mean, std_dev, percentiles, head-to-head probabilities) are identical, which is what every test asserts on. All 100 tests still pass with no tolerance changes.
- **Measured speedup** on a 26-player realistic roster (Python 3.14, single benchmark run on this machine):

  | n_simulations | Before | After  | Speedup |
  |---------------|--------|--------|---------|
  | 10,000        | 76 ms  | 62 ms  | ~18%    |
  | 50,000        | 386 ms | 319 ms | ~17%    |
  | 100,000       | 761 ms | 624 ms | ~18%    |

  Honest note: the original audit projected 2-3× speedup. That overestimated the gain — `rng.gauss()` itself dominates the inner loop, so removing the dict lookup + `.append` saves only a small fraction of total work. The change is still strictly better (faster + clearer + fewer lines), just by less than first claimed.
- **Effort:** ~10 lines changed in `src/simulation/monte_carlo.py`. Zero new tests needed; existing reproducibility, score-property, and statistics tests already cover the contract.

#### Opt #O2. `head_to_head` — hoisted score lookups + `zip` transpose
- **What:** Replaced the per-trial nested generator pattern that re-resolved `results.scores[name]` for every simulation with a two-step approach: dereference each rostered player's score list **once** up front, then use `zip(*lists)` to transpose into per-trial tuples and `sum()` each tuple.
  ```python
  # Before — re-resolved results.scores[name] inside every trial
  team_a_totals = [
      sum(scores[i] for scores in (results.scores[name] for name in team_a_names))
      for i in range(n)
  ]
  # After
  team_a_lists = [results.scores[name] for name in team_a_names]
  team_a_totals = [sum(trial) for trial in zip(*team_a_lists)]
  ```
- **Why:** Removes 8 × 100,000 = 800k redundant dict lookups for a typical 8-player roster at 100k sims. `zip(*lists)` and `sum(tuple)` are both highly optimized in CPython. The new code also reads as a direct expression of intent ("transpose, then sum each column").
- **Measured speedup** on a 100k-sim, 8-vs-8 head-to-head (averaged over 20 calls):

  | Implementation | Time per call |
  |---|---|
  | Before (nested generators)         | ~302 ms |
  | After (hoist + `zip` transpose)    | ~134 ms |
  | **Speedup**                        | **~2.25×** |

  Much bigger win than O1 because the old code's redundant dict lookups dominated the trial loop, whereas in `run_simulation` the `rng.gauss()` call dominated.
- **Behavior:** Identical to before — same totals, same H2HResult fields. All 100 tests pass unchanged.
- **Effort:** ~10 lines changed in `src/stats/statistics_engine.py`.

#### Opt #R1. Numeric range bounds extracted to named constants
- **What:** The legal range for a Player's `mean` (0–60) and `std_dev` (0–25) was hard-coded in two places: `Player.__post_init__` in `src/models/player.py` and `_validate_row` in `src/data_loader/csv_loader.py`. Tuning either side without the other would have left the loader and the model disagreeing on what's valid. Now `player.py` defines four module-level constants (`MIN_MEAN`, `MAX_MEAN`, `MIN_STD_DEV`, `MAX_STD_DEV`) and both files import and reference them in their bounds checks and error messages.
- **Why:** Single source of truth. Changing `MAX_MEAN` from 60 to 70 (e.g. for a different scoring rule) is now a one-line edit, and the loader's error message stays in sync automatically.
- **Behavior:** Identical to before — same accept/reject behavior on every input, error messages still embed the same numeric bounds (just sourced from the constants now). All 100 tests pass unchanged.
- **Effort:** ~15 lines across two files. No new tests needed; the existing range-boundary tests in `test_player.py` and `test_loader.py` already cover both sides.

#### Opt #R2. Collapsed `print_table` duplicate format paths
- **What:** `src/cli/main.py::print_table` previously had two near-identical format paths — one for `show_rank=True` (rankings mode) and one for `show_rank=False` (draft recap). Each path duplicated the column header string and the per-row format string, with the only difference being the optional `Rank` column. Refactored to compute the rank prefix once per call site (`header_rank` for the header line, `row_rank` for each data row) and embed it in a single shared format string.
- **Why:** Eliminated the two-format-strings-must-stay-in-sync hazard (any column-width tweak previously had to be applied four places to stay aligned). Function is now ~15 lines shorter and reads top-to-bottom without an `if/else` straddle. Verified visually that both modes still produce perfectly aligned tables — rankings table (with `Rank` column) and draft recap (without).
- **Behavior:** Identical visual output in both modes. All 100 tests pass; manual CLI smoke test (`python -m src.cli.main --top 3` and `--draft`) confirms identical alignment to before.
- **Effort:** ~15 net lines deleted in `src/cli/main.py`. No new tests needed; the existing CLI subprocess tests assert on table content (header strings, player names, rank ordering) which all still pass.

#### Opt #R3. Hoisted `VALID_POSITIONS` import in `draft_session.py`
- **What:** `src/cli/draft_session.py::_display_position_summary` was doing a deferred `from src.models.player import VALID_POSITIONS` inside the function body. Moved that import to the top of the module alongside the other top-level imports.
- **Why:** Top-level imports are this codebase's default style. The lazy import had no circular-dependency justification (`src.models.player` does not import from anything in `src.cli`); it was just a copy-paste from the *other* lazy import in the same file (`from src.cli.main import print_table`), which **does** need to stay deferred to break the `cli.main` ↔ `cli.draft_session` cycle. The two imports were structurally different even though they looked similar — the refactor fixes that.
- **Behavior:** Identical. All 100 tests pass. Module load time is fractionally shorter (one fewer deferred import resolution per draft pick) but the gain is invisible in practice.
- **Effort:** Moved 1 import line. Removed the inline comment. Net 1 line less.

#### Closeout
With O1, O2, R1, R2, and R3 done, the recommended optimization subset is complete:

| Item | Source files | Visible win |
|---|---|---|
| O1 — Monte Carlo loop inversion | `simulation/monte_carlo.py` | ~18% faster simulation |
| O2 — head_to_head zip transpose | `stats/statistics_engine.py` | ~2.25× faster h2h |
| R1 — extract range constants | `models/player.py`, `data_loader/csv_loader.py` | single source of truth |
| R2 — collapse `print_table` paths | `cli/main.py` | ~15 lines deleted, no parallel formats |
| R3 — hoist `VALID_POSITIONS` import | `cli/draft_session.py` | conventional import style |

The deferred items (M1: decouple loader I/O; M2: switch to `csv.DictReader`; M3: shared test fixtures via `conftest.py`) are documented in this section's earlier audit list as known smells to revisit post-MVP, not now. None of them are correctness issues — they're either coupling-style concerns the existing tests already work around, or refactors whose payoff doesn't justify rewriting working tests.

#### Optimization summary & how the CLEAR checklist guided this work

A compact recap of the five optimizations applied:

1. **O1 — Monte Carlo loop inversion.** Replaced nested `for sim: for player: append` with a single dict comprehension that builds each player's full sample list in one pass. ~18% faster.
2. **O2 — `head_to_head` zip transpose.** Hoisted `results.scores[name]` lookups out of the trial loop and used `zip(*lists)` to transpose into per-trial tuples. ~2.25× faster.
3. **R1 — Range constants.** Extracted `MIN_MEAN`, `MAX_MEAN`, `MIN_STD_DEV`, `MAX_STD_DEV` to `models/player.py`; both the model's `__post_init__` and the loader's `_validate_row` now reference them.
4. **R2 — `print_table` consolidation.** Collapsed two parallel format paths (with/without rank column) into a single shared format string with a computed prefix. ~15 lines deleted.
5. **R3 — Hoisted `VALID_POSITIONS` import.** Moved a lazy in-function import in `draft_session.py` to the module's top-of-file imports.

The collaboration with AI throughout this optimization pass followed the **CLEAR** checklist:

- **C — Context.** The AI was given the post-bug-fix state of the codebase: 100 tests passing, MVP-1 functionally complete, every module already audited. It read each source file before proposing changes so suggestions targeted real lines rather than hypothetical patterns.
- **L — Limits.** "Keep all suggestions within MVP 1 scope" was stated up front. That ruled out new dependencies (no NumPy), no new features (no async, no caching layer), and no stretch items (API integration, historical data, GUI). Every accepted optimization is a pure local rewrite of existing code.
- **E — Examples.** Each proposal came with a concrete before/after code snippet and, where relevant, a measured benchmark (e.g., O1 was projected at 2-3× and benchmarked at ~18%; O2 was projected as "the better win" and benchmarked at ~2.25×). Examples replaced abstract claims so the cost/benefit was visible.
- **A — Ask.** The original request was scoped to three dimensions — performance, readability, maintainability. The AI returned a categorized list of 8 candidates across those exact three buckets, each annotated with effort and a do/skip/defer recommendation, instead of a flat undifferentiated list.
- **R — Refinements.** Mid-implementation refinements happened twice. (1) The O1 speedup claim was corrected from "2-3×" to "~18%" after benchmarking — the README explicitly records the original projection and the honest measured number side by side. (2) The recommended subset was narrowed from the 8 candidates to 5: O1, O2, R1, R2, R3 were applied; M1, M2, M3 were explicitly deferred or skipped, with the reason recorded for each.

The net result: five low-risk optimizations applied across five commits, every change behavior-preserving, every change covered by the existing 100-test suite without modification.

### Task 9 — Security Audit & Defensive Hardening

Performed a security review of the entire codebase across four categories: missing input validation, hardcoded secrets, overly permissive logic, and lack of error handling. Honest preface: this is an offline single-user CLI tool with no network, no auth, no `eval`/`subprocess`/`pickle`, and no SQL — the realistic attack surface is small. Most "security" findings turned out to be denial-of-service or robustness gaps, not exploitable vulnerabilities.

#### What's clean (verified, no changes needed)
- **Hardcoded secrets:** none. The project has no auth or network code, so there's nothing to leak.
- **Code injection** (eval, exec, subprocess on user input, pickle): none.
- **Path traversal** in `--file`: not a vulnerability, since the user runs the tool on their own machine and supplies their own paths.
- **CSV input validation:** already strong — header, column count, range bounds, NaN/Inf rejection, encoding errors handled, duplicates detected, position whitelist.
- **CLI argparse:** strong — `type=int`, `choices`, mutual-exclusion, positive-value guards.
- **Draft REPL:** strong post-fix — EOF/Ctrl-C handled, empty input handled, `isdigit` check before integer coercion.

#### Findings ranked + fixes applied

##### S1 (Medium) — `--sims` upper bound
- **Issue:** `--sims` was unbounded. A typo like `--sims 99999999999` would attempt to allocate trillions of floats and crash with `MemoryError` partway through. Not exploitable, but a footgun.
- **Fix:** Added `MAX_SIMS = 10_000_000` constant in `src/cli/main.py` and a corresponding argparse-level check that converts overshoots into a friendly error before any allocation happens.
- **New test:** `TestSecurityGuards::test_sims_above_ceiling_rejected_by_argparse` asserts exit code 2 and that the cap value appears in the error message.

##### S2 (Low–Medium) — `--h2h` roster size cap
- **Issue:** Each `--h2h` team list was unbounded. Pasting an entire ranking into one argument (e.g. accidentally) would force a multi-second h2h computation against pointless data.
- **Fix:** Added `MAX_ROSTER_SIZE = 50` constant and a check at the top of `_run_h2h` that prints `[ERROR] Team A has N players (maximum allowed is 50)` and exits 1 if either roster is over the cap. 50 is several times a real fantasy roster, so legitimate use is never affected.
- **New test:** `TestSecurityGuards::test_h2h_oversized_roster_rejected` builds a 51-name roster and asserts the friendly error and exit code 1.

##### S3 (Low) — defensive empty-list guards in stats
- **Issue:** `_percentile([], …)` would raise `IndexError` on the `sorted_values[-1]` fallback. `compute_stats` would silently produce a `PlayerStats` with garbage if any player's score list was empty. Both unreachable today (the simulation enforces `n_simulations >= 1`), but the failure mode would be cryptic if the contract changed.
- **Fix:** Added explicit `ValueError("Cannot compute percentile of an empty list")` in `_percentile` and `ValueError("No simulated scores for player {name!r} ...")` in `compute_stats`.
- **New tests:** `TestPercentile::test_empty_list_raises_value_error` and `TestComputeStatsEmptyGuard::test_empty_scores_for_player_raises` — the latter hand-builds a degenerate `SimulationResults` to exercise the guard directly.

#### Findings explicitly skipped (not worth fixing for an offline CLI)
- **S4 (Low)** — no max CSV file size: would be relevant only if the tool grew network or untrusted-input ingestion paths. Premature for the current use case.
- **S5 (Negligible)** — no max length on player name: cosmetic at worst.

#### Test suite totals
- Before security audit: 100 tests passing
- After security audit: **104 tests passing** (+2 CLI subprocess guards + 1 percentile guard + 1 compute_stats guard). Backward compatible.

#### Security risk audit summary
| # | Severity | Status |
|---|---|---|
| S1 — `--sims` unbounded | Medium | ✅ fixed |
| S2 — `--h2h` roster unbounded | Low–Medium | ✅ fixed |
| S3 — empty-input crash in stats | Low | ✅ fixed |
| S4 — no max CSV size | Low | ⏭ skipped (out of scope for offline CLI) |
| S5 — no max name length | Negligible | ⏭ skipped (cosmetic) |

The codebase passes the four-category security audit. No exploitable vulnerabilities were present — the closest items were resource-exhaustion footguns, all now bounded.

---

## Deferred Items, Stretch Features & Future Work

A consolidated index of everything that was considered during MVP-1 work but intentionally not implemented. Each item is recorded with a reason so future-me (or anyone else) doesn't have to re-derive the decision. Nothing here is a correctness gap in MVP-1 — these are scope-bounded "knowns."

### A. Stretch features (excluded from MVP-1 by original spec)

These were called out as out-of-scope from day one. Listed here as the natural next-feature roadmap:

| Feature | Notes for future work |
|---|---|
| **Historical player data ingestion** | The most useful stretch item — would replace fake/projected `mean` and `std_dev` with empirically-derived values from past weekly fantasy points. Recommended path: `nfl_data_py` (a Python wrapper around nflverse). New module like `src/data_loader/historical_loader.py` that fetches per-player weekly history and writes a properly-formatted CSV. The existing CSV-based simulation core stays untouched. |
| **Live API integration** | Sleeper API is free and unauthenticated but exposes player metadata, not projections. ESPN/Yahoo require OAuth and are non-trivial. Not worth the auth/deps complexity unless the historical pipeline is already in place. |
| **Injury simulation** | Add a per-player `injury_rate` field, then in each simulation trial Bernoulli-sample whether the player plays before sampling their score. Would change the CSV schema (one new column) and the Monte Carlo loop. |
| **Positional scarcity modeling** | Adjust ranking/draft recommendation by "Value Over Replacement" — how much better is this RB than the worst-startable RB? Mostly a stats-layer change, not a simulation change. |
| **Visualization charts** | The simulation already produces all the data needed for histograms, boom/bust scatter, etc. Would add a plotting dependency (matplotlib or plotly). Currently the percentile table communicates the same info textually. |
| **GUI interface** | A tk/PyQt frontend over the same engine. Would not change `src/` at all if it consumes the existing `compute_stats` / `head_to_head` / `run_simulation` API. |

### B. Real-data ingestion paths (discussed, not built)

When the question "how do I use this with real player data?" came up, three options were sketched. Recording them here so the analysis isn't lost:

- **Option A — Manual export from a projections site (~30 min, lowest effort).** Pull season-long projections from FantasyPros / ESPN / Sleeper, divide by 17 to get weekly mean. Approximate `StdDev` as a fraction of mean (~0.25 × mean for QBs, ~0.30 × mean for RB/WR/TE). Quality: rough but defensible.
- **Option B — Historical-derived stats (best quality, a few hours).** Use `nfl_data_py` to pull last season's weekly fantasy points per player; compute `mean` and `std_dev` empirically from each player's weekly score history. Quality: real volatility from real data. Natural fit for the "Historical player data ingestion" stretch feature.
- **Option C — Live API (days of work).** Sleeper API is free but doesn't return projections; ESPN/Yahoo require OAuth. Not worth pursuing standalone.

### C. Optimization audit — deferred items

From the optimization pass, three candidates were rated "good in principle, not worth it now":

- **M1 — Decouple loader I/O from data loading.** `CsvPlayerProvider.load_players()` directly calls `print(f"[WARNING] {w}")`, coupling I/O to data parsing. A library user can't suppress or redirect. Tests already work around this by calling `_parse_csv` directly. The minimal future fix is to expose a public `parse_csv_text(text)` that returns `(players, warnings)` and let callers decide how to surface warnings. Real change for a library/CLI separation; pre-mature for the current single-CLI consumer.
- **M2 — Switch from `csv.reader` to `csv.DictReader`.** Would remove the manual `dict(zip(EXPECTED_HEADER, raw_row))` step, but `DictReader`'s failure modes (extra columns get joined under a `None` key; missing get `None` values) would force re-validation of all column-count tests. Marginal gain for a real test rewrite.
- **M3 — Share test fixtures via `tests/conftest.py`.** Each test file defines its own roster with names tuned to that file's assertions ("Elite QB" / "Weak QB" in `test_h2h.py` makes the tests read cleanly). Hoisting them up would actually hurt readability.

### D. Security audit — deferred items

- **S4 — No max CSV file size.** A 50GB CSV would exhaust RAM via `read_text()`. Would matter if the tool ever ingested untrusted input or grew a network surface. Pre-mature for an offline CLI on user-supplied data.
- **S5 — No max length on player name.** Cosmetic at worst — a 10MB name field produces an ugly table. No correctness impact.

### E. Known accepted limitations (not bugs, intentional)

These came up during audits and were explicitly characterized as design trade-offs rather than fixes-in-waiting:

- **Clamping bias in the Monte Carlo loop.** `max(0.0, rng.gauss(mean, std_dev))` is technically a truncated normal, so the sample mean of clamped scores is slightly higher than the parameter mean. For realistic projection ranges (mean 9–25, std_dev 2.4–5.2 in our dataset) the bias is well under 0.5 points — tests already allow ±0.5 tolerance. Becomes wrong-feeling only for very-low-mean / high-stddev edge cases. A proper fix would use `scipy.stats.truncnorm`, which adds a dependency for a sub-percent improvement.
- **Em-dash renders as `?` when stdout is piped on Windows.** The `—` character in `"Remaining depth —"` is a single byte (0x97) in cp1252, which is invalid UTF-8. Visible only when output is redirected; interactive terminal output is fine. Test infrastructure works around it by setting `PYTHONIOENCODING=utf-8` on the subprocess env. Real fix would be to replace em-dashes with ASCII hyphens in user-facing strings, but that's a stylistic loss for a marginal-case issue.
- **Pure-Python simulation loop.** A NumPy rewrite of `run_simulation` would be 50–100× faster (single vectorized `np.random.normal` call clamped with `np.maximum`). Currently 10,000 sims × 26 players takes ~62 ms post-O1 — already imperceptible. Adding NumPy as a runtime dependency for a scenario nobody is hitting is the wrong trade. If the user routinely runs `--sims 1_000_000+`, revisit.

### F. Quality / tooling improvements not pursued

- **Test parametrization.** `TestInvalidRows` in `test_loader.py` repeats the same pattern across ~10 cases. Could be `@pytest.mark.parametrize`'d to ~3 lines. Each test is independently meaningful as-is and the test names read naturally — left alone deliberately.
- **Coverage measurement.** Not currently set up. `pytest-cov` is a one-line dev dependency; useful as the codebase grows.
- **Type checking.** `mypy` isn't set up. Type hints exist throughout the codebase and are correct; running mypy in CI would pin them in place.
- **CI pipeline.** No GitHub Actions / pre-commit hooks. For a single-developer project this is fine; would be the next thing to add for a team.

### G. Things worth knowing now

A short list of project-shape facts that aren't obvious from any single file:

- The package boundary is intentional: every subpackage with public symbols re-exports them via `__all__`. Internal call sites currently import from full module paths instead of going through the package. The re-exports exist for *future* external consumers — they are not vestigial.
- `cli/main.py` and `cli/draft_session.py` have a circular dependency at the function level (each calls into the other). It is broken via lazy in-function imports of `print_table`. The `VALID_POSITIONS` import in `draft_session.py` was *not* part of that cycle and was hoisted to module level (Opt R3). Don't re-defer it without a real reason.
- The simulation's RNG draw order is per-player-batched (post-O1), not per-trial-interleaved. Same-seed reproducibility is preserved within the new code, but exact numeric output for any given seed differs from pre-O1 versions. All tests assert on statistical properties, not pinned values.
- Warnings from the CSV loader are printed to stdout (not stderr) because the CLI's `[ERROR]` path also uses stdout — keeping them on the same stream avoids interleaving issues when the user redirects either one. If the loader gets decoupled (M1), revisit this.
- `data/players_bad.csv` is intentional — it is not bad data left behind, it is the regression fixture for `TestBadFile` in `test_loader.py`.
