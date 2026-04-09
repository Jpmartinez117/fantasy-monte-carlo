"""Unit tests for the statistics engine."""

import pytest
from src.models.player import Player
from src.simulation.monte_carlo import run_simulation
from src.stats.statistics_engine import (
    PlayerStats,
    _percentile,
    compute_stats,
    rank_players,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def two_players():
    return [
        Player(name="Alpha", position="QB", mean=25.0, std_dev=5.0),
        Player(name="Beta",  position="RB", mean=15.0, std_dev=3.0),
    ]


@pytest.fixture
def two_player_results(two_players):
    # Seeded for determinism across test runs
    return run_simulation(two_players, n_simulations=10_000, seed=0)


# ---------------------------------------------------------------------------
# _percentile helper
# ---------------------------------------------------------------------------

class TestPercentile:
    def test_p0_returns_minimum(self):
        assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0) == 1.0

    def test_p100_returns_maximum(self):
        assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 100) == 5.0

    def test_p50_of_odd_list(self):
        # Median of [1,2,3,4,5] is 3.0
        assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50) == pytest.approx(3.0)

    def test_p50_of_even_list(self):
        # Midpoint of [1,2,3,4] = 2.5 via linear interpolation
        assert _percentile([1.0, 2.0, 3.0, 4.0], 50) == pytest.approx(2.5)

    def test_interpolation_between_values(self):
        # p25 of [0, 100] → index 0.25 → 0 + 0.25*(100-0) = 25.0
        assert _percentile([0.0, 100.0], 25) == pytest.approx(25.0)

    def test_single_element_list(self):
        assert _percentile([42.0], 50) == 42.0


# ---------------------------------------------------------------------------
# compute_stats
# ---------------------------------------------------------------------------

class TestComputeStats:
    def test_returns_one_stat_per_player(self, two_players, two_player_results):
        stats = compute_stats(two_player_results, two_players)
        assert len(stats) == len(two_players)

    def test_stat_fields_populated(self, two_players, two_player_results):
        stats = compute_stats(two_player_results, two_players)
        for s in stats:
            assert s.name
            assert s.position in {"QB", "RB", "WR", "TE"}
            assert s.mean > 0
            assert s.std_dev >= 0
            # Percentiles should be non-decreasing
            assert s.p10 <= s.p25 <= s.median <= s.p75 <= s.p90

    def test_position_mapped_correctly(self, two_players, two_player_results):
        stats = compute_stats(two_player_results, two_players)
        stat_map = {s.name: s for s in stats}
        assert stat_map["Alpha"].position == "QB"
        assert stat_map["Beta"].position == "RB"

    def test_mean_close_to_player_mean(self, two_players, two_player_results):
        """Simulated mean should be near the configured player mean."""
        stats = compute_stats(two_player_results, two_players)
        stat_map = {s.name: s for s in stats}
        assert abs(stat_map["Alpha"].mean - 25.0) < 0.5
        assert abs(stat_map["Beta"].mean  - 15.0) < 0.5

    def test_std_dev_close_to_player_std_dev(self, two_players, two_player_results):
        """Simulated std_dev should roughly match configured std_dev.

        The clamping at 0 compresses the left tail slightly, so we allow ±0.5.
        """
        stats = compute_stats(two_player_results, two_players)
        stat_map = {s.name: s for s in stats}
        assert abs(stat_map["Alpha"].std_dev - 5.0) < 0.5
        assert abs(stat_map["Beta"].std_dev  - 3.0) < 0.5


# ---------------------------------------------------------------------------
# rank_players
# ---------------------------------------------------------------------------

class TestRankPlayers:
    def test_sorted_descending_by_mean(self, two_players, two_player_results):
        stats = compute_stats(two_player_results, two_players)
        ranked = rank_players(stats)
        means = [s.mean for s in ranked]
        assert means == sorted(means, reverse=True)

    def test_highest_mean_player_is_first(self, two_players, two_player_results):
        stats = compute_stats(two_player_results, two_players)
        ranked = rank_players(stats)
        # Alpha (mean=25) should outrank Beta (mean=15)
        assert ranked[0].name == "Alpha"

    def test_rank_does_not_mutate_input(self, two_players, two_player_results):
        stats = compute_stats(two_player_results, two_players)
        original_order = [s.name for s in stats]
        rank_players(stats)
        # compute_stats order should be unchanged after ranking
        assert [s.name for s in stats] == original_order
