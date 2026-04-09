"""Unit tests for head-to-head roster comparison."""

import pytest
from src.models.player import Player
from src.simulation.monte_carlo import run_simulation
from src.stats.statistics_engine import H2HResult, head_to_head


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def roster_players():
    return [
        Player("Elite QB",  "QB", mean=30.0, std_dev=3.0),  # clearly best
        Player("Weak QB",   "QB", mean=10.0, std_dev=2.0),  # clearly worst
        Player("Mid RB",    "RB", mean=15.0, std_dev=3.0),
        Player("Mid WR",    "WR", mean=14.0, std_dev=3.0),
    ]


@pytest.fixture
def roster_results(roster_players):
    return run_simulation(roster_players, n_simulations=20_000, seed=7)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestH2HValidation:
    def test_unknown_player_raises(self, roster_results):
        with pytest.raises(ValueError, match="not found"):
            head_to_head(roster_results, ["Ghost Player"], ["Elite QB"])

    def test_unknown_player_in_team_b_raises(self, roster_results):
        with pytest.raises(ValueError, match="not found"):
            head_to_head(roster_results, ["Elite QB"], ["Nobody Here"])


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

class TestH2HOutput:
    def test_returns_h2h_result(self, roster_results):
        result = head_to_head(roster_results, ["Elite QB"], ["Weak QB"])
        assert isinstance(result, H2HResult)

    def test_win_pcts_sum_to_100(self, roster_results):
        result = head_to_head(roster_results, ["Elite QB"], ["Weak QB"])
        total = result.team_a_win_pct + result.team_b_win_pct + result.tie_pct
        assert abs(total - 100.0) < 0.01

    def test_all_fields_are_floats(self, roster_results):
        result = head_to_head(roster_results, ["Elite QB"], ["Weak QB"])
        for field in (result.team_a_win_pct, result.team_b_win_pct,
                      result.tie_pct, result.avg_margin,
                      result.team_a_mean, result.team_b_mean):
            assert isinstance(field, float)


# ---------------------------------------------------------------------------
# Statistical correctness
# ---------------------------------------------------------------------------

class TestH2HStats:
    def test_better_team_wins_more(self, roster_results):
        """Elite QB roster should beat Weak QB roster the vast majority of the time."""
        result = head_to_head(roster_results, ["Elite QB"], ["Weak QB"])
        assert result.team_a_win_pct > 90.0

    def test_margin_positive_for_stronger_team(self, roster_results):
        """avg_margin should be positive when Team A is stronger."""
        result = head_to_head(roster_results, ["Elite QB"], ["Weak QB"])
        assert result.avg_margin > 0

    def test_margin_negative_when_teams_flipped(self, roster_results):
        """Flipping the teams should negate the margin."""
        r1 = head_to_head(roster_results, ["Elite QB"], ["Weak QB"])
        r2 = head_to_head(roster_results, ["Weak QB"], ["Elite QB"])
        assert abs(r1.avg_margin + r2.avg_margin) < 0.01

    def test_multi_player_rosters(self, roster_results):
        """Multi-player rosters should work and totals should be additive."""
        result = head_to_head(
            roster_results,
            ["Elite QB", "Mid RB"],
            ["Weak QB",  "Mid WR"],
        )
        # Elite QB (mean 30) + Mid RB (mean 15) should beat Weak QB (mean 10) + Mid WR (mean 14)
        assert result.team_a_win_pct > 90.0
        assert result.team_a_mean > result.team_b_mean

    def test_equal_rosters_near_50_pct(self):
        """Two identical players should each win ~50% of the time."""
        players = [
            Player("Clone A", "QB", mean=20.0, std_dev=5.0),
            Player("Clone B", "QB", mean=20.0, std_dev=5.0),
        ]
        results = run_simulation(players, n_simulations=50_000, seed=42)
        result = head_to_head(results, ["Clone A"], ["Clone B"])
        # With identical distributions, each side should win ~50% (ties excluded)
        assert abs(result.team_a_win_pct - result.team_b_win_pct) < 3.0
        assert abs(result.avg_margin) < 0.5
