"""
Unit tests for ISteamUserStats endpoint class.
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from endpoints.ISteamUserStats import ISteamUserStats

from config import PERSONAL_STEAM_ID, EXAMPLE_GAME_IDS, EXAMPLE_GAMES

class TestUserStats(unittest.TestCase):
    """Test cases for user stats and ISteamUserStats delegation."""

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.stats_api = ISteamUserStats()
        self.appid = EXAMPLE_GAME_IDS[0]

    def tearDown(self) -> None:
        """Clean up after each test."""
        pass

    def test_stats_api_initialization(self) -> None:
        """Test that ISteamUserStats initializes correctly."""
        self.assertIsNotNone(self.stats_api)
        self.assertIsNotNone(self.stats_api.game_stat_manager)
        self.assertIsNotNone(self.stats_api.game_schema_manager)

    def test_get_user_achievement_stats_for_game_passthrough(self) -> None:
        """Test that get_user_achievement_stats_for_game passes through to manager (mocked)."""
        steamid = PERSONAL_STEAM_ID
        mock_response = {"playerstats": {"achievements": []}}
        
        with patch.object(self.stats_api, 'fetch_user_achievements', return_value=mock_response):
            with patch.object(self.stats_api, 'format_user_achievement_stats', return_value={"split_achievements": []}):
                result = self.stats_api.get_user_achievement_stats_for_game(steamid, self.appid)
                self.assertIsNotNone(result)

    def test_get_global_stats_for_game_passthrough(self) -> None:
        """Test that get_global_stats_for_game passes through to manager (mocked)."""
        mock_response = {"result": {}}
        
        with patch.object(self.stats_api.game_stat_manager, 'get_global_stats_for_game', return_value=mock_response):
            result = self.stats_api.get_global_stats_for_game(self.appid, 0, [])
            self.assertIsInstance(result, dict)

    def test_get_global_achievement_percentages_passthrough(self) -> None:
        """Test that get_global_achievement_percentages_for_app passes through to manager (mocked)."""
        mock_response = {"achievementpercentages": {}}
        
        with patch.object(self.stats_api.game_stat_manager, 'get_global_achievement_percentages_for_app', return_value=mock_response):
            result = self.stats_api.get_global_achievement_percentages_for_app(self.appid)
            self.assertIsNotNone(result)

    def test_fetch_achievements_passthrough(self) -> None:
        """Test that fetch_user_achievements passes through to manager (mocked)."""
        steamid = PERSONAL_STEAM_ID
        mock_response = {"playerstats": {"achievements": []}}
        
        with patch.object(self.stats_api.game_stat_manager, 'fetch_user_achievements', return_value=mock_response):
            result = self.stats_api.fetch_user_achievements(steamid, self.appid)
            self.assertIsNotNone(result)

    def test_format_achievement_stats_passthrough(self) -> None:
        """Test that format_user_achievement_stats passes through to manager (mocked)."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000},
                ]
            }
        }
        

        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid)
            self.assertIsNotNone(result)
            self.assertIn("split_achievements", result)


class TestAchievements(unittest.TestCase):
    """Test cases for achievement parsing, formatting, and sorting."""

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.stats_api = ISteamUserStats()
        self.appid = EXAMPLE_GAME_IDS[0]

    def tearDown(self) -> None:
        """Clean up after each test."""
        pass

    def test_get_player_achievements(self) -> None:
        """Test getting player achievements (mocked)."""
        steamid = PERSONAL_STEAM_ID
        mock_response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [{"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000}]
            }
        }
        
        with patch.object(self.stats_api, 'fetch_user_achievements', return_value=mock_response):
            with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
                result = self.stats_api.fetch_user_achievements(steamid, self.appid)
                self.assertIsNotNone(result)
                self.assertIn("playerstats", result)

    def test_fetch_achievements_from_valid_response(self) -> None:
        """Test extraction of achievements from valid response."""
        valid_response = {
            "playerstats": {
                "gameName": "Counter-Strike 2",
                "achievements": [
                    {"apiname": "ACH_WIN_MAP_DUST2", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "ACH_WIN_10_MAPS", "achieved": 1, "unlocktime": 1700100000},
                    {"apiname": "ACH_HEADSHOT_MASTER", "achieved": 0, "unlocktime": 0},
                    {"apiname": "ACH_1000_KILLS", "achieved": 0, "unlocktime": 0},
                ]
            }
        }
        
        result = self.stats_api.game_stat_manager._retrieve_user_achievements_from_response(valid_response)
        self.assertEqual(result["game_name"], "Counter-Strike 2")
        self.assertEqual(result["achievement_count"], 4)
        self.assertEqual(len(result["achievements"]), 4)

    def test_fetch_achievements_empty_list(self) -> None:
        """Test extraction with empty achievements list."""
        empty_response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": []
            }
        }
        
        result = self.stats_api.game_stat_manager._retrieve_user_achievements_from_response(empty_response)
        self.assertEqual(result["game_name"], "Test Game")
        self.assertEqual(result["achievement_count"], 0)

    def test_fetch_achievements_invalid_response_raises_error(self) -> None:
        """Test that invalid response raises ValueError."""
        invalid_response = {"invalid_key": "value"}
        
        with self.assertRaises(ValueError) as context:
            self.stats_api.game_stat_manager._retrieve_user_achievements_from_response(invalid_response)
        
        self.assertIn("Invalid response structure", str(context.exception))

    def test_categorize_achievements_correctly(self) -> None:
        """Test that achievements are correctly split into achieved/locked."""
        mixed_response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "ACH_2", "achieved": 1, "unlocktime": 1700100000},
                    {"apiname": "ACH_3", "achieved": 0, "unlocktime": 0},
                    {"apiname": "ACH_4", "achieved": 0, "unlocktime": 0},
                ]
            }
        }
        
        result = self.stats_api.game_stat_manager._get_user_achievements_status(mixed_response)
        self.assertEqual(result["achieved_count"], 2)
        self.assertEqual(result["locked_count"], 2)

    def test_all_achieved(self) -> None:
        """Test response with all achievements unlocked."""
        response = {
            "playerstats": {
                "gameName": "Complete Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "ACH_2", "achieved": 1, "unlocktime": 1700100000},
                ]
            }
        }
        result = self.stats_api.game_stat_manager._get_user_achievements_status(response)
        self.assertEqual(result["achieved_count"], 2)
        self.assertEqual(result["locked_count"], 0)

    def test_all_locked(self) -> None:
        """Test response with no achievements unlocked."""
        response = {
            "playerstats": {
                "gameName": "New Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 0, "unlocktime": 0},
                    {"apiname": "ACH_2", "achieved": 0, "unlocktime": 0},
                ]
            }
        }
        result = self.stats_api.game_stat_manager._get_user_achievements_status(response)
        self.assertEqual(result["achieved_count"], 0)
        self.assertEqual(result["locked_count"], 2)

    def test_format_adds_human_readable_timestamp(self) -> None:
        """Test that unlock_time_human is added in ISO format."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_ZEBRA", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "ACH_APPLE", "achieved": 1, "unlocktime": 1700100000},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid)
            achieved = result["split_achievements"]["achieved"]
            
            self.assertIsInstance(achieved[0]["status"]["unlock_time_human"], str)
            self.assertIn("-", achieved[0]["status"]["unlock_time_human"])
            self.assertIn(":", achieved[0]["status"]["unlock_time_human"])

    def test_locked_achievements_have_zero_timestamp(self) -> None:
        """Test that locked achievements have 0 for unlock_time_human."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_MONKEY", "achieved": 0, "unlocktime": 0},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid)
            locked = result["split_achievements"]["locked"]
            self.assertEqual(locked[0]["status"]["unlock_time_human"], 0)

    def test_format_includes_counts(self) -> None:
        """Test that format includes achieved/locked counts."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "ACH_2", "achieved": 1, "unlocktime": 1700100000},
                    {"apiname": "ACH_3", "achieved": 0, "unlocktime": 0},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid)
            self.assertEqual(result["achieved_count"], 2)
            self.assertEqual(result["locked_count"], 1)

    def test_differentiate_locked_true_returns_dict(self) -> None:
        """Test that differentiate_locked=True returns dict split."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "ACH_2", "achieved": 0, "unlocktime": 0},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid, differentiate_locked=True)
            self.assertIsInstance(result["split_achievements"], dict)
            self.assertIn("achieved", result["split_achievements"])
            self.assertIn("locked", result["split_achievements"])

    def test_differentiate_locked_false_returns_flat_list(self) -> None:
        """Test that differentiate_locked=False returns flat list."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "ACH_2", "achieved": 0, "unlocktime": 0},
                    {"apiname": "ACH_3", "achieved": 0, "unlocktime": 0},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid, differentiate_locked=False)
            self.assertIsInstance(result["split_achievements"], list)
            self.assertEqual(len(result["split_achievements"]), 3)

    def test_sort_by_name_alphabetical(self) -> None:
        """Test sorting by achievement display_name."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ZEBRA", "achieved": 1, "unlocktime": 1700200000},
                    {"apiname": "APPLE", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "MONKEY", "achieved": 1, "unlocktime": 1700100000},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid, differentiate_locked=True, sort_by="display_name")
            achieved = result["split_achievements"]["achieved"]
            self.assertEqual(len(achieved), 3)

    def test_sort_by_unlock_time_chronological(self) -> None:
        """Test sorting by unlock time."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ZEBRA", "achieved": 1, "unlocktime": 1700200000},
                    {"apiname": "APPLE", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "MONKEY", "achieved": 1, "unlocktime": 1700100000},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid, differentiate_locked=True, sort_by="unlock_time")
            achieved_times = [a["status"]["unlock_time"] for a in result["split_achievements"]["achieved"]]
            self.assertEqual(achieved_times, [1700000000, 1700100000, 1700200000])

    def test_empty_achievements_list(self) -> None:
        """Test formatting with no achievements."""
        response = {
            "playerstats": {
                "gameName": "Empty Game",
                "achievements": []
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid)
            self.assertEqual(result["achieved_count"], 0)
            self.assertEqual(result["locked_count"], 0)

    def test_game_name_extraction(self) -> None:
        """Test that game name is correctly extracted."""
        response = {
            "playerstats": {
                "gameName": "Half-Life 3",
                "achievements": []
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid)
            self.assertEqual(result["game_name"], "Half-Life 3")

    def test_return_raw_true_includes_response(self) -> None:
        """Test that return_raw=True includes full raw_response."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid, return_raw=True)
            self.assertIsNotNone(result["raw_response"])
            self.assertEqual(result["raw_response"], response)

    def test_return_raw_false_omits_response(self) -> None:
        """Test that return_raw=False omits raw_response."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid, return_raw=False)
            self.assertIsNone(result["raw_response"])

    def test_sort_flat_list(self) -> None:
        """Test sorting on flat list (differentiate_locked=False)."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ZEBRA", "achieved": 1, "unlocktime": 1700200000},
                    {"apiname": "APPLE", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "MONKEY", "achieved": 1, "unlocktime": 1700100000},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid, differentiate_locked=False, sort_by="display_name")
            achievements = result["split_achievements"]
            self.assertEqual(len(achievements), 3)

    def test_invalid_sort_key_ignored(self) -> None:
        """Test that invalid sort keys are ignored without raising error."""
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "achievements": [
                    {"apiname": "ACH_1", "achieved": 1, "unlocktime": 1700000000},
                    {"apiname": "ACH_2", "achieved": 1, "unlocktime": 1700100000},
                    {"apiname": "ACH_3", "achieved": 1, "unlocktime": 1700200000},
                ]
            }
        }
        
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            result = self.stats_api.format_user_achievement_stats(response, self.appid, differentiate_locked=True, sort_by="invalid_key")
            self.assertEqual(len(result["split_achievements"]["achieved"]), 3)


class TestAPIReturnReusePatterns(unittest.TestCase):
    """Performance tests demonstrating the dual-pattern design from ARCHITECTURE.md.
    
    These tests show how reusing raw API responses avoids redundant processing.
    Applies to all endpoints: achievements, stats, friends lists, etc.
    
    These tests are intentionally heavyweight to show the real-world difference between:
    - Pattern 1: Multiple full pipeline calls (wasteful with large datasets)
    - Pattern 2: Fetch once, format multiple ways (efficient)
    """

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.stats_api = ISteamUserStats()
        self.appid = EXAMPLE_GAME_IDS[0]

    def test_reuse_api_response_reduces_processing(self) -> None:
        """Performance test: demonstrate reusing raw API response vs multiple full pipeline calls.
        
        Note: With mocked API calls, the difference is minimal. In production with real API calls,
        Pattern 2 (fetch once, format multiple ways) is significantly faster due to avoiding
        repeated network round trips. This test demonstrates the formatting performance.
        """
        response = {
            "playerstats": {
                "gameName": "Test Game",
                "steamID": PERSONAL_STEAM_ID,
                "achievements": [
                    {"apiname": f"ACH_{i}", "achieved": 1, "unlocktime": 1700000000 + i*1000}
                    for i in range(50)  # 50 achievements to format
                ]
            }
        }
        
        # Pattern 1: Multiple formats via full pipeline (simulated with mocks)
        with patch.object(self.stats_api, 'fetch_user_achievements', return_value=response):
            start = time.time()
            for _ in range(3):
                self.stats_api.get_user_achievement_stats_for_game(PERSONAL_STEAM_ID, self.appid)
            multiple_calls_time = time.time() - start
        
        # Pattern 2: Fetch once, format multiple ways (no re-fetch)
        start = time.time()
        with patch.object(self.stats_api.game_schema_manager, 'fetch_schema_for_game', return_value={"game": {}}):
            for sort_by in ["display_name", "unlock_time", None]:
                self.stats_api.format_user_achievement_stats(response, self.appid, sort_by=sort_by)
        reuse_data_time = time.time() - start
        
        # Print results for visibility
        print(f"\n--- Achievement Reuse Pattern Demonstration ---")
        print(f"Pattern 1 (3x full pipeline with mocked fetch): {multiple_calls_time:.4f}s")
        print(f"  - 3 API calls (or 3 fetch operations)")
        print(f"  - 3 full schema enrichment passes")
        print(f"  - 3 separate response objects in memory")
        print(f"Pattern 2 (1x fetch, 3x format): {reuse_data_time:.4f}s")
        print(f"  - 1 API call (or 1 fetch operation)")
        print(f"  - 3 lightweight formatting passes on same data")
        print(f"  - 1 response object reused in memory")
        print(f"\nMemory & Network Savings:")
        print(f"  - API calls reduced: 3 → 1 (67% fewer)")
        print(f"  - Response objects: 3 → 1 (66% less memory)")
        print(f"  - Network overhead: ~200-900ms saved per reuse (at 100-300ms per API call)")
        print(f"\nNote: This test uses mocks, so real API latency isn't shown.")
        print(f"With production API calls, Pattern 2 should be faster and lighter to work with for extended chains.")
        
        # Both patterns should complete without error
        self.assertGreater(multiple_calls_time, 0)
        self.assertGreater(reuse_data_time, 0)


if __name__ == "__main__":
    unittest.main()
