# Fantasy Football Monte Carlo Draft Helper

This project provides an offline command-line tool to assist with fantasy football drafts using
Monte Carlo simulations. It's designed with a modular architecture to keep components
separated and easy to understand.

## Project Structure

```
fantasy-monte-carlo/
│
├── data/                  # CSV datasets
│   ├── players.csv
│   └── players_bad.csv
│
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── player.py
│   │
│   ├── data_loader/
│   │   ├── __init__.py
│   │   └── csv_loader.py
│   │
│   ├── simulation/
│   │   ├── __init__.py
│   │   └── monte_carlo.py
│   │
│   ├── stats/
│   │   ├── __init__.py
│   │   └── statistics_engine.py
│   │
│   └── cli/
│       ├── __init__.py
│       └── main.py
│
├── tests/
│   ├── __init__.py
│   └── test_loader.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

Each package contains placeholder modules initially. Development will implement functionality
for loading data, modeling players, running simulations, computing statistics, and interacting
through a CLI.

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
