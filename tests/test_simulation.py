"""Unit tests for the Monte Carlo simulation engine."""

import pytest
from src.models.player import Player
from src.simulation.monte_carlo import SimulationResults, run_simulation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def single_player():
    return [Player(name="Test QB", position="QB", mean=20.0, std_dev=4.0)]


@pytest.fixture
def small_roster():
    return [
        Player(name="QB1", position="QB", mean=25.0, std_dev=5.0),
        Player(name="RB1", position="RB", mean=15.0, std_dev=3.0),
        Player(name="WR1", position="WR", mean=14.0, std_dev=3.5),
    ]


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_empty_player_list_raises(self):
        with pytest.raises(ValueError, match="empty"):
            run_simulation([])

    def test_zero_simulations_raises(self):
        with pytest.raises(ValueError, match="n_simulations"):
            run_simulation([Player("A", "QB", 20.0, 4.0)], n_simulations=0)

    def test_negative_simulations_raises(self):
        with pytest.raises(ValueError, match="n_simulations"):
            run_simulation([Player("A", "QB", 20.0, 4.0)], n_simulations=-1)


# ---------------------------------------------------------------------------
# Output shape
# ---------------------------------------------------------------------------

class TestOutputShape:
    def test_result_has_correct_player_count(self, small_roster):
        results = run_simulation(small_roster, n_simulations=100)
        assert len(results.scores) == len(small_roster)

    def test_each_player_has_correct_sim_count(self, small_roster):
        n = 500
        results = run_simulation(small_roster, n_simulations=n)
        for scores in results.scores.values():
            assert len(scores) == n

    def test_n_simulations_stored_on_result(self, single_player):
        results = run_simulation(single_player, n_simulations=200)
        assert results.n_simulations == 200

    def test_all_player_names_present(self, small_roster):
        results = run_simulation(small_roster, n_simulations=10)
        for player in small_roster:
            assert player.name in results.scores


# ---------------------------------------------------------------------------
# Score properties
# ---------------------------------------------------------------------------

class TestScoreProperties:
    def test_no_negative_scores(self, small_roster):
        # Scores are clamped to 0; even a high-std_dev player should never go negative
        results = run_simulation(small_roster, n_simulations=5_000)
        for name, scores in results.scores.items():
            assert all(s >= 0 for s in scores), f"{name} had a negative score"

    def test_scores_are_floats(self, single_player):
        results = run_simulation(single_player, n_simulations=10)
        for score in results.scores["Test QB"]:
            assert isinstance(score, float)

    def test_mean_close_to_player_mean(self, single_player):
        """With enough simulations the sample mean should converge near the true mean."""
        results = run_simulation(single_player, n_simulations=50_000, seed=42)
        scores = results.scores["Test QB"]
        sample_mean = sum(scores) / len(scores)
        # Allow ±0.5 tolerance — very unlikely to fail with 50k draws
        assert abs(sample_mean - 20.0) < 0.5


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

class TestReproducibility:
    def test_same_seed_produces_identical_results(self, small_roster):
        r1 = run_simulation(small_roster, n_simulations=100, seed=99)
        r2 = run_simulation(small_roster, n_simulations=100, seed=99)
        assert r1.scores == r2.scores

    def test_different_seeds_produce_different_results(self, small_roster):
        r1 = run_simulation(small_roster, n_simulations=100, seed=1)
        r2 = run_simulation(small_roster, n_simulations=100, seed=2)
        # Astronomically unlikely to be identical
        assert r1.scores != r2.scores

    def test_no_seed_does_not_raise(self, single_player):
        # Unseeded runs should work without error (just non-deterministic)
        results = run_simulation(single_player, n_simulations=10)
        assert len(results.scores["Test QB"]) == 10
