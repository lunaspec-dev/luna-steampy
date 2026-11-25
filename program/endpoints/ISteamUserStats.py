# This class interacts with the ISteamUserStats endpoint of the Steam API.
# It inherits from the SteamAPIHandler class, which handles the HTTP requests and responses.

from datetime import datetime # For converting unlocktime to human-readable format
import sys
from pathlib import Path
import os

import json

# Add parent directory to path so we can import steam_api_core
sys.path.insert(0, str(Path(__file__).parent.parent))

from steamweb_api_core import SteamAPIHandler
from config import PERSONAL_STEAM_ID, EXAMPLE_GAME_IDS

class ISteamUserStats(SteamAPIHandler):
    """Interact with the ISteamUserStats endpoint of the Steam API."""

    def __init__(self, version: str = "v1") -> None:
        """Initialize ISteamUserStats with the parent SteamAPIHandler."""
        super().__init__()
        self.api_interface = "ISteamUserStats"
        self.version = version
        self.game_stat_manager = GameStatManager(self.api_interface, self.version)  # Initialize GameStatManager instance
        self.game_schema_manager = GameSchemaManager(self.api_interface, self.version)  # Initialize GameSchemaManager instance

    def fetch_schema_for_game(self, appid: int) -> dict:
        """Get the stats and achievements schema for a game."""
        return self.game_schema_manager.fetch_schema_for_game(appid)

    def get_global_achievement_percentages_for_app(self, appid: int) -> dict:
        """Get global achievement percentages for a game."""
        return self.game_stat_manager.get_global_achievement_percentages_for_app(appid)

    def fetch_user_achievements(self, steamid: str, appid: int) -> dict:
        """Get achievements unlocked by a player in a specific game."""
        return self.game_stat_manager.fetch_user_achievements(steamid, appid)

    def format_user_achievement_stats(self, raw_response: dict, appid: int, differentiate_locked: bool = True, sort_by: str = None, return_raw: bool = False) -> dict:
        """Get achievements with unlocked/locked status and human-readable unlock times."""
        return self.game_stat_manager.format_user_achievement_stats(raw_response, appid, differentiate_locked, sort_by, return_raw)

    def get_user_achievement_stats_for_game(self, steamid: str, appid: int, differentiate_locked: bool = True, sort_by: str = None, return_raw: bool = False) -> dict:
        """Get formatted achievement stats for a player in a specific game.
        
        Full pipeline: fetch raw achievements → format with metadata → return usable data.
        
        Args:
            steamid (str): Steam ID of the player
            appid (int): App ID of the game
            differentiate_locked (bool): Split achievements into achieved/locked dict. Defaults to True.
            sort_by (str): Sort achievements by this key (e.g., 'name', 'unlock_time'). Defaults to None.
            return_raw (bool): Include raw API response in result. Defaults to False.
            
        Returns:
            dict: Formatted achievement stats with counts, game name, and achievements.
        """
        raw = self.fetch_user_achievements(steamid, appid)
        return self.format_user_achievement_stats(raw, appid, differentiate_locked, sort_by, return_raw)

    def get_user_stats_for_game(self, steamid: str, appid: int) -> dict:
        """Get statistics for a player in a specific game."""
        return self.game_stat_manager.get_user_stats_for_game(steamid, appid)

    def get_global_stats_for_game(self, appid: int, count: int, names: list) -> dict:
            """Get global statistics for a game."""
            return self.game_stat_manager.get_global_stats_for_game(appid, count, names)


class GameStatManager(SteamAPIHandler):
    def __init__(self, api_interface: str = "ISteamUserStats", version: str = "v1"):
        """Initialize the GameManager with API interface and version."""
        super().__init__()
        self.api_interface = api_interface
        self.version = version
        self.example_game_ids = EXAMPLE_GAME_IDS

    def get_example_game_ids(self) -> list:
        """Return the list of example game IDs."""
        return self.example_game_ids

    def fetch_user_achievements(self, steamid: str, appid: int) -> dict:
        """Get achievements unlocked by a player in a specific game."""
        endpoint = self._build_endpoint("GetPlayerAchievements")
        params = {"steamid": steamid, "appid": appid}
        return self._make_api_request(endpoint, params)

    def _fetch_user_achievements_from_response(self, raw_response: dict) -> dict:
        """Validate response structure and extract basic achievement metadata.
        
        Args:
            raw_response (dict): Raw API response from GetPlayerAchievements.
            
        Returns:
            dict: Contains game_name, achievements list, and achievement_count.
            
        Raises:
            ValueError: If response lacks required keys.
        """

        return_dict = {
            "game_name": None,
            "achievements": [],
            "achievement_count": 0,
        }

        if "playerstats" in raw_response and "achievements" in raw_response["playerstats"]:

            return_dict["game_name"] = raw_response["playerstats"].get("gameName")
            achievements = raw_response["playerstats"]["achievements"]
            return_dict["achievements"] = achievements
            return_dict["achievement_count"] = len(achievements)

            return return_dict

        else:
            raise ValueError("Invalid response structure: 'playerstats' or 'achievements' key missing in raw response.")

    def _get_user_achievements_status(self, raw_response: dict) -> dict:
        """Categorize achievements by unlock status: achieved or locked.
        
        Args:
            raw_response (dict): Raw API response from GetPlayerAchievements.
            
        Returns:
            dict: Contains game_name, two achievement lists (achieved, locked), and counts.
        """
        
        # Achievement buckets based on unlock status
        ACHIEVED = "achieved"
        LOCKED = "locked"
        
        # Initialize return structure
        return_dict = {
            "game_name": None,
            ACHIEVED: [],
            LOCKED: [],
            "achieved_count": 0,
            "locked_count": 0,
        }

        # Extract and categorize achievements from response
        if "playerstats" in raw_response and "achievements" in raw_response["playerstats"]:
            return_dict["game_name"] = raw_response["playerstats"].get("gameName")
            achievements = raw_response["playerstats"]["achievements"]

            # Categorize by unlock status
            for achievement in achievements:
                if achievement.get("achieved"):
                    return_dict[ACHIEVED].append(achievement)
                    return_dict["achieved_count"] += 1
                else:
                    return_dict[LOCKED].append(achievement)
                    return_dict["locked_count"] += 1

            return return_dict

    def get_user_completed_achievements(self, steamid: str, appid: int) -> dict:
        """Get achievements marked as completed by a player in a specific game, enriched with full schema metadata."""

        raw_response = self.fetch_user_achievements(steamid, appid)
        
        # Use helper to categorize achievements
        categorized = self._get_user_achievements_status(raw_response)
        
        # Fetch full schema once
        achievement_schema = self._fetch_achievement_schema_for_game(appid) or {}
        
        # Apply schema enrichment to completed achievements
        formatted_completed = []
        for achievement in categorized["achieved"]:
            steam_internal_name = achievement.get("apiname")
            schema_entry = achievement_schema.get(steam_internal_name, {})
            formatted_completed.append(self._format_achievement_with_schema(achievement, schema_entry))
        
        return {
            "game_name": categorized["game_name"],
            "completed_achievements": formatted_completed,
            "completed_count": categorized["achieved_count"]
        }

    def get_user_locked_achievements(self, steamid: str, appid: int) -> dict:
        """Get achievements marked as locked by a player in a specific game, enriched with full schema metadata."""

        raw_response = self.fetch_user_achievements(steamid, appid)
        
        # Use helper to categorize achievements
        categorized = self._get_user_achievements_status(raw_response)
        
        # Fetch full schema once
        achievement_schema = self._fetch_achievement_schema_for_game(appid) or {}
        
        # Apply schema enrichment to locked achievements
        formatted_locked = []
        for achievement in categorized["locked"]:
            steam_internal_name = achievement.get("apiname")
            schema_entry = achievement_schema.get(steam_internal_name, {})
            formatted_locked.append(self._format_achievement_with_schema(achievement, schema_entry))
        
        return {
            "game_name": categorized["game_name"],
            "locked_achievements": formatted_locked,
            "locked_count": categorized["locked_count"]
        }

    def _fetch_schema_for_game(self, appid: int) -> dict:
        """Get the stats and achievements schema for a game."""
        schema_manager = GameSchemaManager(self.api_interface, self.version)
        schema = schema_manager.fetch_schema_for_game(appid)
        return schema

    def _fetch_achievement_schema_for_game(self, appid: int) -> dict:
        """Get the achievements schema (dict keyed by apiname) for a game."""

        schema_response = self._fetch_schema_for_game(appid)
        if "game" in schema_response:
            return schema_response["game"].get("availableGameStats", {}).get("achievements", {})
        
        else:
            raise ValueError("Invalid response structure: 'game' key missing in schema response.")

    def _format_achievement_with_schema(self, achievement: dict, schema_entry: dict) -> dict:
        """Format a single achievement with schema metadata and human-readable unlock time.
        
        Args:
            achievement (dict): Raw player achievement data from API.
            schema_entry (dict): Schema metadata for this achievement (or empty dict if not found).
            
        Returns:
            dict: Formatted achievement with display_name, description, status, icons, etc.
        """
        display_name = schema_entry.get("displayName", "Unknown Achievement")
        description = schema_entry.get("description") or ""
        hidden_by_default = schema_entry.get("hidden", 0)
        icon_url = schema_entry.get("icon", "")
        icon_url_gray = schema_entry.get("icongray", "")
        
        return {
            "steam_internal_name": achievement.get("apiname"),
            "display_name": display_name,
            "description": description,
            "status": {
                "hidden_by_default": hidden_by_default,
                "achieved": achievement.get("achieved"),
                "unlock_time": achievement.get("unlocktime"),
                "unlock_time_human": self._convert_unix_timestamp(achievement.get("unlocktime")),
                "icon_url": icon_url,
                "icon_url_gray": icon_url_gray,
            },
        }

    def format_user_achievement_stats(self, raw_response: dict, appid: int, differentiate_locked: bool = True, sort_by: str = None, return_raw: bool = False) -> dict:
        """Get achievements with unlocked/locked status and human-readable unlock times.
        
        Args:
            raw_response (dict): Raw API response from GetPlayerAchievements.
            appid (int): Application ID for fetching achievement schema.
            differentiate_locked (bool): If True, split achievements into achieved/locked buckets; if False, return flat list.
            return_raw (bool): If True, includes full raw_response in output; if False, omits it.
            
        Returns:
            dict: Contains game_name, achievements (dict or list based on differentiate_locked), counts, and optional raw_response.
        """

        # Reuse categorization logic to avoid re-parsing
        status = self._get_user_achievements_status(raw_response)
        
        # Extract steamid from response
        steamid = raw_response.get("playerstats", {}).get("steamID") if raw_response else None
        
        # Build formatted response with categorized counts
        return_dict = {
            "steamuserid": steamid,
            "game_name": status["game_name"],
            "raw_response": raw_response if return_raw else None,
            "achieved_count": status["achieved_count"],
            "locked_count": status["locked_count"],
        }

        # Format each achievement with schema metadata and human-readable unlock time
        if "playerstats" in raw_response and "achievements" in raw_response["playerstats"]:
            achievements = raw_response["playerstats"]["achievements"]
            achievement_schema = self._fetch_achievement_schema_for_game(appid) or {}
            formatted = []
            
            for achievement in achievements:
                steam_internal_name = achievement.get("apiname")
                schema_entry = achievement_schema.get(steam_internal_name, {})
                formatted.append(self._format_achievement_with_schema(achievement, schema_entry))
            
            # Return achievements as categorized dict or flat list
            if differentiate_locked:
                return_dict["split_achievements"] = {
                    "achieved": [a for a in formatted if a["status"]["achieved"]],
                    "locked": [a for a in formatted if not a["status"]["achieved"]],
                }
            else:
                return_dict["split_achievements"] = formatted

            # add sorting logic if specified
            achievement_sort_mapping = {
                "display_name": lambda x: x["display_name"],
                "unlock_time": lambda x: x["status"].get("unlock_time", 0)
            }
            if sort_by:
                if differentiate_locked:
                    return_dict["split_achievements"]["achieved"] = self._sort_list(
                        return_dict["split_achievements"]["achieved"], sort_by, achievement_sort_mapping
                    )
                    return_dict["split_achievements"]["locked"] = self._sort_list(
                        return_dict["split_achievements"]["locked"], sort_by, achievement_sort_mapping
                    )
                else:
                    return_dict["split_achievements"] = self._sort_list(
                        return_dict["split_achievements"], sort_by, achievement_sort_mapping
                    )

        return return_dict

    def get_user_stats_for_game(self, steamid: str, appid: int) -> dict:
        """Get statistics for a player in a specific game."""
        endpoint = self._build_endpoint("GetUserStatsForGame")
        params = {"steamid": steamid, "appid": appid}
        return self._make_api_request(endpoint, params)

    def get_global_achievement_percentages_for_app(self, appid: int) -> dict:
            """Get global achievement percentages for a game."""
            endpoint = self._build_endpoint("GetGlobalAchievementPercentagesForApp")
            params = {"gameid": appid}
            return self._make_api_request(endpoint, params)

    def get_global_stats_for_game(self, appid: int, count: int, names: list) -> dict:
        """Get global statistics for a game."""
        endpoint = self._build_endpoint("GetGlobalStatsForGame")
        params = {"appid": appid, "count": count, "name": names}
        return self._make_api_request(endpoint, params)


class GameSchemaManager(SteamAPIHandler):
    def __init__(self, api_interface: str = "ISteamUserStats", version: str = "v1"):
        """Initialize the GameSchemaManager with API interface and version."""
        super().__init__()
        self.api_interface = api_interface
        self.version = version

    def fetch_schema_for_game(self, appid: int) -> dict:
        """Fetch the stats and achievements schema for a game."""
        endpoint = self._build_endpoint("GetSchemaForGame")
        params = {"appid": appid}
        return self._make_api_request(endpoint, params)

    def _parse_schema_response(self, raw_response: dict) -> dict:
        """Parse the schema response to extract relevant information."""
        return_dict = {
            "game_name": None,
            "game_version": None,
            "achievements": []
        }

        if "game" in raw_response:
            return_dict["steam_internal_name"] = raw_response["game"].get("gameName")
            return_dict["game_version"] = raw_response["game"].get("gameVersion")
            return_dict["achievements"] = raw_response["game"].get("availableGameStats", {}).get("achievements", [])

        else:
            raise ValueError("Invalid response structure: 'game' key missing in raw response.")

        return return_dict

    def get_steam_internal_name(self, appid: int, schema_response: dict = None) -> str:
        """Extract the Steam internal name of the game from the schema response.
        
        Args:
            appid (int): Game app ID
            schema_response (dict, optional): Pre-fetched schema response. If not provided, fetches it.
            
        Returns:
            str: Steam internal game name
        """
        if schema_response is None:
            schema_response = self.fetch_schema_for_game(appid)
            
        if "game" in schema_response:
            return schema_response["game"].get("gameName")
        else:
            raise ValueError("Invalid response structure: 'game' key missing in schema response.")

    def get_game_version(self, appid: int, schema_response: dict = None) -> str:
        """Extract the game version from the schema response.
        
        Args:
            appid (int): Game app ID
            schema_response (dict, optional): Pre-fetched schema response. If not provided, fetches it.
            
        Returns:
            str: Game version string
        """
        if schema_response is None:
            schema_response = self.fetch_schema_for_game(appid)
            
        if "game" in schema_response:
            return schema_response["game"].get("gameVersion")
        else:
            raise ValueError("Invalid response structure: 'game' key missing in schema response.")

    def fetch_all_achievements_schema(self, appid: int) -> dict:
        """Extract all achievements schema as dict keyed by apiname from the schema response."""

        raw_response = self.fetch_schema_for_game(appid)
        if "game" in raw_response:
            return raw_response["game"].get("availableGameStats", {}).get("achievements", {})
        
        else:
            raise ValueError("Invalid response structure: 'game' key missing in raw response.")
    
    def get_achievement_schema(self, appid: int, apiname: str) -> dict:
        """Get the schema for a single achievement.
        
        Args:
            appid (int): Game app ID
            apiname (str): Achievement internal name (e.g. "ACHIEVEMENT_141")
            
        Returns:
            dict: Formatted schema entry with displayName, description, icons, hidden flag, etc.
        """
        schema = self.fetch_all_achievements_schema(appid)
        return schema.get(apiname, {})

    def fetch_achievement_display_names(self, achievements_schema: dict, sort_by: str = "apiname") -> dict:
        """Fetch a mapping of achievement internal names to display names from full schema dict.
        
        Args:
            achievements_schema (dict): Full schema dict keyed by apiname (from fetch_all_achievements_schema)
            sort_by (str): Sort key - "apiname" (default), "displayName", or None for no sorting
            
        Returns:
            dict: Mapping of apiname to displayName
        """
        
        if sort_by == "displayName":
            sorted_items = sorted(achievements_schema.items(), key=lambda x: x[1].get("displayName", ""))
        elif sort_by == "apiname" or sort_by is not None:
            sorted_items = sorted(achievements_schema.items())
        else:
            sorted_items = achievements_schema.items()
        
        display_name_mapping = {
            steam_internal_name: achievement.get("displayName") 
            for steam_internal_name, achievement in sorted_items
            if "displayName" in achievement
        }
        return display_name_mapping


def main():
    # stats = ISteamUserStats()
    # steamid = PERSONAL_STEAM_ID
    # appid = EXAMPLE_GAME_IDS[0] if EXAMPLE_GAME_IDS else 730
    
    # raw_response = stats.fetch_user_achievements(steamid, appid)
    # formatted_stats = stats.format_user_achievement_stats(raw_response, appid, differentiate_locked=True, sort_by="display_name")
    
    # print(f"\n--- Achievement Summary ---")
    # print(f"SteamUserID: {formatted_stats.get('steamuserid')}")
    # print(f"Game: {formatted_stats.get('game_name')}")
    # print(f"Achieved: {formatted_stats.get('achieved_count')} | Locked: {formatted_stats.get('locked_count')}")
    
    # def print_achievements(achievements, title):
    #     print(f"\n--- {title} ---")
    #     for achievement in achievements[:10]:
    #         print(f"  {achievement['steam_internal_name']}: {achievement['display_name']}")
    #         if achievement['description']:
    #             print(f"  {achievement['description']}")
    #         print(f"  {achievement['status']['unlock_time_human']}")
    
    # achieved = formatted_stats.get("split_achievements", {}).get("achieved", [])
    # locked = formatted_stats.get("split_achievements", {}).get("locked", [])
    
    # print_achievements(achieved, "First 3 Achieved")
    # print_achievements(locked, "First 10 Locked")

    stats = ISteamUserStats()
    steamid = PERSONAL_STEAM_ID
    appid = EXAMPLE_GAME_IDS[0] if EXAMPLE_GAME_IDS else 730

    raw_response = stats.fetch_user_achievements(steamid, appid)
    formatted_stats = stats.format_user_achievement_stats(raw_response, appid, differentiate_locked=True, sort_by="display_name")

    print(f"\n--- Achievement Summary ---")
    print(json.dumps(raw_response, indent=4))


if __name__ == "__main__":
    main()