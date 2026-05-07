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
