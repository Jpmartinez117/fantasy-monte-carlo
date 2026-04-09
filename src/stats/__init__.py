"""Statistics subpackage: summary stats over simulation results."""

from src.stats.statistics_engine import H2HResult, PlayerStats, compute_stats, head_to_head, rank_players

__all__ = ["H2HResult", "PlayerStats", "compute_stats", "head_to_head", "rank_players"]
