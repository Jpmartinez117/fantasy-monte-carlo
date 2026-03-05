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
