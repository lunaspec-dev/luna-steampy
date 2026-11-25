"""
Unit tests for ISteamUser endpoint class.
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from endpoints.ISteamUser import ISteamUser
from config import PERSONAL_STEAM_ID


class TestISteamUserInitialization(unittest.TestCase):
    """Test cases for ISteamUser initialization."""

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.user_api = ISteamUser()

    def tearDown(self) -> None:
        """Clean up after each test."""
        pass

    def test_isteamuser_initialization(self) -> None:
        """Test that ISteamUser initializes correctly."""
        self.assertIsNotNone(self.user_api)
        self.assertEqual(self.user_api.api_interface, "ISteamUser")
        self.assertEqual(self.user_api.version, "v1")

    def test_isteamuser_custom_version(self) -> None:
        """Test that ISteamUser accepts custom version."""
        user_api_v2 = ISteamUser(version="v2")
        self.assertEqual(user_api_v2.version, "v2")


class TestFriendListParsing(unittest.TestCase):
    """Test cases for friend list parsing and structuring."""

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.user_api = ISteamUser()

    def tearDown(self) -> None:
        """Clean up after each test."""
        pass

    def test_get_user_friend_list_from_response_valid(self) -> None:
        """Test extracting friend list from valid response."""
        response = {
            "friendslist": {
                "friends": [
                    {"steamid": "123456", "relationship": "friend", "friend_since": 1700000000},
                    {"steamid": "789012", "relationship": "friend", "friend_since": 1700100000},
                ]
            }
        }
        
        result = self.user_api._retrieve_user_friend_list_from_response(response)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["steamid"], "123456")
        self.assertEqual(result[1]["steamid"], "789012")

    def test_get_user_friend_list_from_response_empty(self) -> None:
        """Test extracting empty friend list from response."""
        response = {
            "friendslist": {
                "friends": []
            }
        }
        
        result = self.user_api._retrieve_user_friend_list_from_response(response)
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_get_user_friend_list_from_response_missing_friendslist(self) -> None:
        """Test error handling when friendslist is missing."""
        response = {}
        
        with self.assertRaises(ValueError) as context:
            self.user_api._retrieve_user_friend_list_from_response(response)
        
        self.assertIn("No friends list found", str(context.exception))

    def test_get_user_friend_list_from_response_null_friendslist(self) -> None:
        """Test error handling when friendslist is None."""
        response = {"friendslist": None}
        
        with self.assertRaises(ValueError) as context:
            self.user_api._retrieve_user_friend_list_from_response(response)
        
        self.assertIn("No friends list found", str(context.exception))


class TestFriendsListByRelationship(unittest.TestCase):
    """Test cases for grouping friends by relationship type."""

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.user_api = ISteamUser()

    def tearDown(self) -> None:
        """Clean up after each test."""
        pass

    def test_get_friends_list_by_relationship_single_type(self) -> None:
        """Test grouping friends when all have the same relationship."""
        response = {
            "friendslist": {
                "friends": [
                    {"steamid": "123456", "relationship": "friend", "friend_since": 1700000000},
                    {"steamid": "789012", "relationship": "friend", "friend_since": 1700100000},
                ]
            }
        }
        
        result = self.user_api._get_friends_list_by_relationship(response)
        
        self.assertIn("friend", result)
        self.assertEqual(result["friend"]["count"], 2)
        self.assertEqual(len(result["friend"]["friends"]), 2)

    def test_get_friends_list_by_relationship_multiple_types(self) -> None:
        """Test grouping friends with multiple relationship types."""
        response = {
            "friendslist": {
                "friends": [
                    {"steamid": "123456", "relationship": "friend", "friend_since": 1700000000},
                    {"steamid": "789012", "relationship": "blocked", "friend_since": 1700100000},
                    {"steamid": "345678", "relationship": "friend", "friend_since": 1700200000},
                ]
            }
        }
        
        result = self.user_api._get_friends_list_by_relationship(response)
        
        self.assertEqual(len(result), 2)
        self.assertIn("friend", result)
        self.assertIn("blocked", result)
        self.assertEqual(result["friend"]["count"], 2)
        self.assertEqual(result["blocked"]["count"], 1)

    def test_get_friends_list_by_relationship_empty(self) -> None:
        """Test grouping with empty friend list."""
        response = {
            "friendslist": {
                "friends": []
            }
        }
        
        result = self.user_api._get_friends_list_by_relationship(response)
        
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, dict)


class TestGetFormattedFriendsList(unittest.TestCase):
    """Test cases for the formatted friends list facade."""

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.user_api = ISteamUser()
        self.mock_response = {
            "friendslist": {
                "friends": [
                    {"steamid": "123456", "relationship": "friend", "friend_since": 1700000000},
                    {"steamid": "789012", "relationship": "friend", "friend_since": 1700100000},
                    {"steamid": "345678", "relationship": "blocked", "friend_since": 1700200000},
                ]
            }
        }

    def tearDown(self) -> None:
        """Clean up after each test."""
        pass

    @patch.object(ISteamUser, 'fetch_friend_list')
    def test_get_formatted_friends_list_grouped(self, mock_fetch):
        """Test formatted friends list with grouping by relationship."""
        mock_fetch.return_value = self.mock_response
        
        result = self.user_api.get_formatted_friends_list(PERSONAL_STEAM_ID, group_by_relationship=True)
        
        self.assertIn("friend", result)
        self.assertIn("blocked", result)
        self.assertEqual(result["friend"]["count"], 2)
        self.assertEqual(result["blocked"]["count"], 1)

    @patch.object(ISteamUser, 'fetch_friend_list')
    def test_get_formatted_friends_list_not_grouped(self, mock_fetch):
        """Test formatted friends list without grouping."""
        mock_fetch.return_value = self.mock_response
        
        result = self.user_api.get_formatted_friends_list(PERSONAL_STEAM_ID, group_by_relationship=False)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    @patch.object(ISteamUser, 'fetch_friend_list')
    def test_get_formatted_friends_list_with_sorting(self, mock_fetch):
        """Test formatted friends list with sorting."""
        mock_fetch.return_value = self.mock_response
        
        result = self.user_api.get_formatted_friends_list(
            PERSONAL_STEAM_ID, 
            group_by_relationship=False, 
            sort_by="friend_since"
        )
        
        self.assertIsInstance(result, list)
        # Verify sorting by checking timestamps are in order
        for i in range(len(result) - 1):
            self.assertLessEqual(result[i]["friend_since"], result[i + 1]["friend_since"])

    @patch.object(ISteamUser, 'fetch_friend_list')
    def test_get_formatted_friends_list_grouped_with_sorting(self, mock_fetch):
        """Test formatted friends list grouped and sorted."""
        mock_fetch.return_value = self.mock_response
        
        result = self.user_api.get_formatted_friends_list(
            PERSONAL_STEAM_ID, 
            group_by_relationship=True, 
            sort_by="friend_since"
        )
        
        self.assertIn("friend", result)
        # Verify friends within group are sorted
        friend_list = result["friend"]["friends"]
        for i in range(len(friend_list) - 1):
            self.assertLessEqual(friend_list[i]["friend_since"], friend_list[i + 1]["friend_since"])

    @patch.object(ISteamUser, 'fetch_friend_list')
    def test_timestamp_conversion_in_formatted_list(self, mock_fetch):
        """Test that unix timestamps are converted to readable format."""
        mock_fetch.return_value = self.mock_response
        
        result = self.user_api.get_formatted_friends_list(PERSONAL_STEAM_ID, group_by_relationship=False)
        
        # Check that at least one friend has a converted timestamp
        for friend in result:
            if "friend_since" in friend:
                # Should be a string after conversion, not an int
                self.assertIsInstance(friend["friend_since"], str)
                # Should contain date-like format
                self.assertRegex(friend["friend_since"], r"\d{4}-\d{2}-\d{2}")


class TestFetchMethodValidation(unittest.TestCase):
    """Test cases for fetch method response validation."""

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.user_api = ISteamUser()

    def tearDown(self) -> None:
        """Clean up after each test."""
        pass

    @patch.object(ISteamUser, '_make_api_request')
    def test_fetch_friend_list_valid_response(self, mock_request):
        """Test fetch_friend_list with valid response."""
        mock_request.return_value = {
            "friendslist": {
                "friends": [
                    {"steamid": "123456", "relationship": "friend", "friend_since": 1700000000}
                ]
            }
        }
        
        result = self.user_api.fetch_friend_list(PERSONAL_STEAM_ID)
        
        self.assertIsNotNone(result)
        self.assertIn("friendslist", result)

    @patch.object(ISteamUser, '_make_api_request')
    def test_fetch_friend_list_missing_friendslist(self, mock_request):
        """Test fetch_friend_list raises error when friendslist is missing."""
        mock_request.return_value = {}
        
        with self.assertRaises(ValueError) as context:
            self.user_api.fetch_friend_list(PERSONAL_STEAM_ID)
        
        self.assertIn("No friends list found", str(context.exception))

    @patch.object(ISteamUser, '_make_api_request')
    def test_fetch_friend_list_null_friendslist(self, mock_request):
        """Test fetch_friend_list raises error when friendslist is None."""
        mock_request.return_value = {"friendslist": None}
        
        with self.assertRaises(ValueError) as context:
            self.user_api.fetch_friend_list(PERSONAL_STEAM_ID)
        
        self.assertIn("No friends list found", str(context.exception))


class TestOtherMethods(unittest.TestCase):
    """Test cases for other ISteamUser methods."""

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.user_api = ISteamUser()

    def tearDown(self) -> None:
        """Clean up after each test."""
        pass

    @patch.object(ISteamUser, '_make_api_request')
    def test_fetch_player_bans(self, mock_request):
        """Test fetch_player_bans calls correct endpoint."""
        mock_request.return_value = {
            "players": [
                {
                    "steamid": "123456",
                    "CommunityBanned": False,
                    "VACBanned": False,
                    "NumberOfVACBans": 0,
                    "DaysSinceLastBan": 0,
                    "GameBans": 0,
                    "EconomyBan": "none"
                }
            ]
        }
        
        result = self.user_api.fetch_player_bans("123456")
        
        self.assertIsNotNone(result)
        self.assertIn("players", result)

    @patch.object(ISteamUser, '_make_api_request')
    def test_fetch_player_summaries(self, mock_request):
        """Test fetch_player_summaries calls correct endpoint."""
        mock_request.return_value = {
            "response": {
                "players": [
                    {
                        "steamid": "123456",
                        "communityvisibilitystate": 3,
                        "profilestate": 1,
                        "personaname": "TestPlayer",
                        "profileurl": "https://steamcommunity.com/profiles/123456/"
                    }
                ]
            }
        }
        
        result = self.user_api.fetch_player_summaries("123456")
        
        self.assertIsNotNone(result)
        self.assertIn("response", result)

    @patch.object(ISteamUser, '_make_api_request')
    def test_resolve_vanity_url(self, mock_request):
        """Test resolve_vanity_url calls correct endpoint."""
        mock_request.return_value = {
            "response": {
                "steamid": "123456",
                "success": 1
            }
        }
        
        result = self.user_api.resolve_vanity_url("testvanity")
        
        self.assertIsNotNone(result)
        self.assertEqual(result, "123456")


class TestPlayerBanCategories(unittest.TestCase):
    """Test cases for player ban formatting and categorization."""

    def setUp(self) -> None:
        """Set up test fixtures before each test."""
        self.user_api = ISteamUser()

    def tearDown(self) -> None:
        """Clean up after each test."""
        pass

    @patch.object(ISteamUser, '_make_api_request')
    def test_fetch_player_bans_single_clean_user(self, mock_request):
        """Test fetching bans for a single clean user (no bans)."""
        mock_request.return_value = {
            "players": [
                {
                    "SteamId": "12345",
                    "CommunityBanned": False,
                    "VACBanned": False,
                    "NumberOfVACBans": 0,
                    "DaysSinceLastBan": 0,
                    "NumberOfGameBans": 0,
                    "EconomyBan": "none"
                }
            ]
        }
        
        result = self.user_api.fetch_player_bans("12345")
        self.assertIsNotNone(result)
        self.assertEqual(len(result["players"]), 1)
        self.assertFalse(result["players"][0]["CommunityBanned"])

    @patch.object(ISteamUser, '_make_api_request')
    def test_fetch_player_bans_single_vac_banned(self, mock_request):
        """Test fetching bans for a single VAC banned user."""
        mock_request.return_value = {
            "players": [
                {
                    "SteamId": "67890",
                    "CommunityBanned": False,
                    "VACBanned": True,
                    "NumberOfVACBans": 2,
                    "DaysSinceLastBan": 100,
                    "NumberOfGameBans": 0,
                    "EconomyBan": "none"
                }
            ]
        }
        
        result = self.user_api.fetch_player_bans("67890")
        self.assertIsNotNone(result)
        self.assertTrue(result["players"][0]["VACBanned"])
        self.assertEqual(result["players"][0]["NumberOfVACBans"], 2)

    @patch.object(ISteamUser, '_make_api_request')
    def test_format_player_ban_clean_user(self, mock_request):
        """Test formatting a clean player (all None values)."""
        mock_request.return_value = {
            "players": [
                {
                    "SteamId": "11111",
                    "CommunityBanned": False,
                    "VACBanned": False,
                    "NumberOfVACBans": 0,
                    "DaysSinceLastBan": 0,
                    "NumberOfGameBans": 0,
                    "EconomyBan": "none"
                }
            ]
        }
        
        result = self.user_api.get_formatted_player_bans("11111")
        player = result["user_info"][0]
        
        self.assertIsNone(player["vac_banned"])
        self.assertIsNone(player["community_banned"])
        self.assertIsNone(player["game_banned"])
        self.assertIsNone(player["market_banned"])

    @patch.object(ISteamUser, '_make_api_request')
    def test_format_player_ban_all_bans(self, mock_request):
        """Test formatting a player with multiple ban types."""
        mock_request.return_value = {
            "players": [
                {
                    "SteamId": "22222",
                    "CommunityBanned": True,
                    "VACBanned": True,
                    "NumberOfVACBans": 1,
                    "DaysSinceLastBan": 500,
                    "NumberOfGameBans": 2,
                    "EconomyBan": "banned",
                    "bans": [
                        {"AppIdMin": 730, "AppIdMax": 730, "BanStartTime": 1780525984, "BanType": 2, "BanProviderId": 0}
                    ]
                }
            ]
        }
        
        result = self.user_api.get_formatted_player_bans("22222")
        player = result["user_info"][0]
        
        self.assertIsNotNone(player["vac_banned"])
        self.assertIsNotNone(player["community_banned"])
        self.assertIsNotNone(player["game_banned"])
        self.assertIsNotNone(player["market_banned"])
        self.assertEqual(player["game_banned"]["count"], 2)

    @patch.object(ISteamUser, '_make_api_request')
    def test_get_formatted_player_bans_flat_list(self, mock_request):
        """Test flat list return (group_by_ban_category=False)."""
        mock_request.return_value = {
            "players": [
                {
                    "SteamId": "33333",
                    "CommunityBanned": False,
                    "VACBanned": True,
                    "NumberOfVACBans": 1,
                    "DaysSinceLastBan": 50,
                    "NumberOfGameBans": 0,
                    "EconomyBan": "none"
                },
                {
                    "SteamId": "44444",
                    "CommunityBanned": True,
                    "VACBanned": False,
                    "NumberOfVACBans": 0,
                    "DaysSinceLastBan": 0,
                    "NumberOfGameBans": 0,
                    "EconomyBan": "none"
                }
            ]
        }
        
        result = self.user_api.get_formatted_player_bans("33333,44444", group_by_ban_category=False)
        
        self.assertEqual(result["total_users_returned"], 2)
        self.assertEqual(len(result["user_info"]), 2)
        self.assertIn("total_banned_count", result)
        self.assertIn("total_vac_banned_count", result)

    @patch.object(ISteamUser, '_make_api_request')
    def test_get_formatted_player_bans_categorized(self, mock_request):
        """Test categorized return (group_by_ban_category=True)."""
        mock_request.return_value = {
            "players": [
                {
                    "SteamId": "55555",
                    "CommunityBanned": False,
                    "VACBanned": True,
                    "NumberOfVACBans": 1,
                    "DaysSinceLastBan": 50,
                    "NumberOfGameBans": 0,
                    "EconomyBan": "none"
                },
                {
                    "SteamId": "66666",
                    "CommunityBanned": True,
                    "VACBanned": True,
                    "NumberOfVACBans": 1,
                    "DaysSinceLastBan": 100,
                    "NumberOfGameBans": 1,
                    "EconomyBan": "none"
                }
            ]
        }
        
        result = self.user_api.get_formatted_player_bans("55555,66666", group_by_ban_category=True)
        
        self.assertEqual(result["total_players"], 2)
        self.assertIn("vac_banned", result)
        self.assertIn("community_banned", result)
        self.assertEqual(result["vac_banned"]["count"], 2)  # Both users have VAC bans
        self.assertEqual(result["community_banned"]["count"], 1)  # Only second user

    @patch.object(ISteamUser, '_make_api_request')
    def test_ban_categorization_with_overlap(self, mock_request):
        """Test that players with multiple bans appear in multiple bins."""
        mock_request.return_value = {
            "players": [
                {
                    "SteamId": "77777",
                    "CommunityBanned": False,
                    "VACBanned": False,
                    "NumberOfVACBans": 0,
                    "DaysSinceLastBan": 0,
                    "NumberOfGameBans": 0,
                    "EconomyBan": "none"
                },
                {
                    "SteamId": "88888",
                    "CommunityBanned": True,
                    "VACBanned": True,
                    "NumberOfVACBans": 2,
                    "DaysSinceLastBan": 200,
                    "NumberOfGameBans": 1,
                    "EconomyBan": "banned"
                }
            ]
        }
        
        result = self.user_api.get_formatted_player_bans("77777,88888", group_by_ban_category=True)
        
        # Second user should appear in all 4 bins
        self.assertEqual(result["vac_banned"]["count"], 1)
        self.assertEqual(result["community_banned"]["count"], 1)
        self.assertEqual(result["game_banned"]["count"], 1)
        self.assertEqual(result["economy_banned"]["count"], 1)
        # Total bans = 4 (one player in all bins)
        self.assertEqual(result["total_bans"], 4)

    @patch.object(ISteamUser, '_make_api_request')
    def test_ban_market_probation_state(self, mock_request):
        """Test economy ban with probation status."""
        mock_request.return_value = {
            "players": [
                {
                    "SteamId": "99999",
                    "CommunityBanned": False,
                    "VACBanned": False,
                    "NumberOfVACBans": 0,
                    "DaysSinceLastBan": 0,
                    "NumberOfGameBans": 0,
                    "EconomyBan": "probation"
                }
            ]
        }
        
        result = self.user_api.get_formatted_player_bans("99999")
        player = result["user_info"][0]
        
        self.assertIsNotNone(player["market_banned"])
        self.assertEqual(player["market_banned"]["type"], "probation")

    @patch.object(ISteamUser, '_make_api_request')
    def test_ban_with_detailed_game_bans(self, mock_request):
        """Test game ban with detailed ban information."""
        mock_request.return_value = {
            "players": [
                {
                    "SteamId": "111111",
                    "CommunityBanned": False,
                    "VACBanned": False,
                    "NumberOfVACBans": 0,
                    "DaysSinceLastBan": 0,
                    "NumberOfGameBans": 2,
                    "EconomyBan": "none",
                    "bans": [
                        {"AppIdMin": 730, "AppIdMax": 730, "BanStartTime": 1780525984, "BanType": 2, "BanProviderId": 0},
                        {"AppIdMin": 570, "AppIdMax": 570, "BanStartTime": 1780525900, "BanType": 2, "BanProviderId": 0}
                    ]
                }
            ]
        }
        
        result = self.user_api.get_formatted_player_bans("111111")
        player = result["user_info"][0]
        
        self.assertEqual(player["game_banned"]["count"], 2)
        self.assertEqual(len(player["game_banned"]["bans"]), 2)


if __name__ == "__main__":
    unittest.main()
