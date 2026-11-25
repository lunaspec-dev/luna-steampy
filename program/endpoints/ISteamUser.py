import sys
from pathlib import Path

# Add parent directory to path so we can import steam_api_core
sys.path.insert(0, str(Path(__file__).parent.parent))

from steamweb_api_core import SteamAPIHandler
from config import PERSONAL_STEAM_ID, STEAM_BAN_TYPES, EXAMPLE_STEAM_IDS

# This class interacts with the ISteamUser endpoint of the Steam API. 
# It inherits from the SteamAPIHandler class, which handles the HTTP requests and responses.

# NOTE: This class only contains methods for public web API endpoints.
# https://partner.steamgames.com/doc/webapi/ISteamUser

# Other methods that require publisher keys will potentially be implemented in future updates or specific targeted classes.

class ISteamUser(SteamAPIHandler):
    """Interact with the ISteamUser endpoint of the Steam API."""

    def __init__(self, version: str = "v1") -> None:
        """Initialize ISteamUser with the parent SteamAPIHandler."""
        super().__init__()
        self.api_interface = "ISteamUser"
        self.version = version

    def fetch_friend_list(self, steamid: str) -> dict:
        """Get the friend list for a Steam user."""
        endpoint = self._build_endpoint("GetFriendList")
        params = {"steamid": steamid}

        request = self._make_api_request(endpoint, params)
        if request.get("friendslist") is None:
            raise ValueError(f"No friends list found for Steam ID: {steamid} - check if the profile is private or if the Steam ID is valid.")

        return request

    def _retrieve_user_friend_list_from_response(self, response: dict) -> list:
        """Extract the friend list from the API response."""

        if response.get("friendslist") is None:
            raise ValueError("No friends list found in the response - check if the profile is private or if the Steam ID is valid.")

        new_response = response.get("friendslist", {}).get("friends", [])

        return new_response

    def _get_friends_list_by_relationship(self, response: dict) -> list:
        """Returns a dictionary with the friends list split by relationship type (e.g., 'friend', 'blocked', etc.)."""

        friends = self._retrieve_user_friend_list_from_response(response)

        relationship_dict = {}
        for friend in friends:
            relationship = friend.get("relationship")
            if relationship not in relationship_dict:
                relationship_dict[relationship] = []
            relationship_dict[relationship].append(friend)

        for relationship, friends in relationship_dict.items():
            relationship_dict[relationship] = {
                "count": len(friends),
                "friends": friends
            }

        return relationship_dict

    def get_formatted_friends_list(self, steamid: str, group_by_relationship: bool = True, sort_by: str = None) -> dict:
        """Get the friends list for a Steam user, optionally grouped by relationship type."""
        friend_list = self.fetch_friend_list(steamid)

        # Convert unix timestamps to human-readable format
        for friend in friend_list.get("friendslist", {}).get("friends", []):
            if "friend_since" in friend:
                friend["friend_since"] = self._convert_unix_timestamp(friend.get("friend_since"))

        if group_by_relationship:
            result = self._get_friends_list_by_relationship(friend_list)
        else:
            result = self._retrieve_user_friend_list_from_response(friend_list)

        if sort_by:
            friend_sort_mapping = {
                "username": lambda x: x.get("username", ""),
                "relationship": lambda x: x.get("relationship", ""),
                "friend_since": lambda x: x.get("friend_since", "")
            }
            if group_by_relationship:
                for relationship, data in result.items():
                    data["friends"] = self._sort_list(data["friends"], sort_by, friend_sort_mapping)
            else:
                result = self._sort_list(result, sort_by, friend_sort_mapping)

        return result

    def fetch_player_bans(self, steamids: str) -> dict:
        """Get ban status for one or more Steam users."""
        endpoint = self._build_endpoint("GetPlayerBans")
        params = {"steamids": steamids}
        return self._make_api_request(endpoint, params)

    def _retrieve_player_bans_from_response(self, response: dict) -> list:
        """Extract the player bans list from the API response.
        
        Expected API response format from GetPlayerBans:
        {
            "players": [
                {
                    "SteamId": "...",
                    "CommunityBanned": bool,
                    "VACBanned": bool,
                    "NumberOfVACBans": int,
                    "DaysSinceLastBan": int,
                    "NumberOfGameBans": int,
                    "EconomyBan": "none" | "probation" | "banned",
                    "bans": [  # Optional, only present if game bans exist
                        {
                            "AppIdMin": int,
                            "AppIdMax": int,
                            "BanStartTime": int (unix timestamp),
                            "BanType": int (1=player, 2=game, etc),
                            "BanProviderId": int
                        }
                    ]
                }
            ]
        }
        """
        if response.get("players") is None:
            raise ValueError("No players data found in the response - check if the Steam IDs are valid.")
        
        return response.get("players", [])

    def _format_player_ban(self, ban_data: dict) -> dict:
        """Format a single player ban record with detailed ban info or None if not banned.
        
        Args:
            ban_data (dict): Raw ban data from API response (fields: SteamId, CommunityBanned, VACBanned, etc).
            
        Returns:
            dict: Formatted ban data with structure:
                {
                    "steamid": "...",
                    "community_banned": {...} or None,
                    "market_banned": {...} or None,
                    "game_banned": {...} or None,
                    "vac_banned": {...} or None,
                }
                Where each ban type is None if not banned, or a dict with ban details if banned.
        """
        return {
            "steamid": ban_data.get("SteamId"),
            "community_banned": {
                "is_banned": True,
            } if ban_data.get("CommunityBanned", False) else None,
            "market_banned": {
                "type": ban_data.get("EconomyBan", "none"),
            } if ban_data.get("EconomyBan", "none") != "none" else None,
            "game_banned": {
                "count": ban_data.get("NumberOfGameBans", 0),
                "bans": ban_data.get("bans", []),  # Detailed ban info if present
            } if ban_data.get("NumberOfGameBans", 0) > 0 else None,
            "vac_banned": {
                "is_vac_banned": True,
                "number_of_bans": ban_data.get("NumberOfVACBans", 0),
                "days_since_last_ban": ban_data.get("DaysSinceLastBan", 0),
            } if ban_data.get("VACBanned", False) else None,
        }

    def _get_user_bans_by_category(self, bans: list) -> dict:
        """Categorize player bans into 4 static bins for analysis.
        
        Players can appear in multiple bins if they have multiple ban types.
        Total ban counts reflect the sum across all bins (allowing overlap).
        
        Ban type bins (from STEAM_BAN_TYPES config, overridable via env var):
            - vac_banned: Players with VAC anti-cheat bans
            - community_banned: Players with community code violations
            - game_banned: Players with game-specific developer bans
            - economy_banned: Players with trading/marketplace restrictions
        
        Args:
            bans (list): List of formatted player ban data with ban type fields.

        Returns:
            dict: Bin-based breakdown with structure:
                {
                    "total_players": int,
                    "total_bans": int,  # Sum of all bin counts (allows overlap)
                    "vac_banned": {"count": int, "players": [...]},
                    "community_banned": {"count": int, "players": [...]},
                    "game_banned": {"count": int, "players": [...]},
                    "economy_banned": {"count": int, "players": [...]},
                }
        """
        # Initialize bins for each ban type
        bins = {
            "vac_banned": [],
            "community_banned": [],
            "game_banned": [],
            "economy_banned": [],
        }
        
        # Categorize each player into applicable bins
        for ban in bans:
            if ban["vac_banned"] is not None:
                bins["vac_banned"].append(ban)
            if ban["community_banned"] is not None:
                bins["community_banned"].append(ban)
            if ban["game_banned"] is not None:
                bins["game_banned"].append(ban)
            if ban["market_banned"] is not None:
                bins["economy_banned"].append(ban)
        
        # Build result with counts
        total_ban_count = sum(len(players) for players in bins.values())
        
        result = {
            "total_players": len(bans),
            "names": [ban["steamid"] for ban in bans],
            "total_bans": total_ban_count,
        }
        
        # Add bin data for each ban type
        for ban_type, players in bins.items():
            result[ban_type] = {
                "count": len(players),
                "players": players
            }
        
        return result

    def get_formatted_player_bans(self, steamids: str, group_by_ban_category: bool = False, sort_by: str = None) -> dict:
        """Get formatted ban status for one or more Steam users.
        
        Full pipeline: fetch raw bans → format with categorized structure → return usable data.
        
        Args:
            steamids (str): Comma-separated Steam IDs to check
            group_by_ban_category (bool): If True, group bans by category combinations; if False, return flat list. Defaults to False.
            sort_by (str): Sort bans by this key (e.g., 'steamid', 'community_banned'). Defaults to None.
            
        Returns:
            dict: Formatted ban data with player counts and formatted bans list (or categorized structure if group_by_ban_category=True).
        """
        raw = self.fetch_player_bans(steamids)
        bans = self._retrieve_player_bans_from_response(raw)
        
        formatted_bans = [self._format_player_ban(ban) for ban in bans]
        
        # Apply grouping if requested
        if group_by_ban_category:
            return self._get_user_bans_by_category(formatted_bans)
        
        # Apply sorting if specified
        if sort_by:
            ban_sort_mapping = {
                "steamid": lambda x: x.get("steamid", ""),
                "community_banned": lambda x: x.get("community_banned") is not None,
                "market_banned": lambda x: x.get("market_banned") is not None,
                "game_banned": lambda x: x.get("game_banned") is not None,
                "vac_banned": lambda x: x.get("vac_banned") is not None,
            }
            formatted_bans = self._sort_list(formatted_bans, sort_by, ban_sort_mapping)
        
        # Calculate ban statistics
        banned_count = sum(1 for ban in formatted_bans if any([
            ban["game_banned"] is not None,
            ban["community_banned"] is not None,
            ban["market_banned"] is not None,
            ban["vac_banned"] is not None,
        ]))
        vac_banned_count = sum(1 for ban in formatted_bans if ban["vac_banned"] is not None)
        
        return {
            "total_users_returned": len(formatted_bans),
            "total_banned_count": banned_count,
            "total_vac_banned_count": vac_banned_count,
            "user_info": formatted_bans,
        }

    def fetch_player_summaries(self, steamids: str) -> dict:
        """Get profile information for one or more Steam users."""
        endpoint = self._build_endpoint("GetPlayerSummaries")
        params = {"steamids": steamids}
        return self._make_api_request(endpoint, params)

    def _retrieve_player_summaries_from_response(self, response: dict) -> list:
        """Extract the player summaries list from the API response."""
        if response.get("response", {}).get("players") is None:
            raise ValueError("No players data found in the response - check if the Steam IDs are valid.")
        
        return response.get("response", {}).get("players", [])

    def resolve_vanity_url(self, vanityurl: str) -> dict:
        """Resolve a custom Steam URL to a Steam ID."""
        endpoint = self._build_endpoint("ResolveVanityURL")
        params = {"vanityurl": vanityurl}
        respone = self._make_api_request(endpoint, params)

        if respone.get("response", {}).get("success") != 1:
            raise ValueError(f"Failed to resolve vanity URL '{vanityurl}': {respone.get('response', {}).get('message', 'Unknown error')}")

        return respone.get("response", {}).get("steamid")

def main():
    """Example usage of the ISteamUser class."""

    # Example usage of the ISteamUser class
    steam_user = ISteamUser()
    
    # friend_list = steam_user.fetch_friend_list(PERSONAL_STEAM_ID)
    # print(friend_list)

    # print("\nFormatted friends list grouped by relationship:")
    # formatted_friends = steam_user.get_formatted_friends_list(PERSONAL_STEAM_ID, group_by_relationship=True, sort_by="friend_since")
    # print(formatted_friends)

    # print("\nFetching player bans for the user:")
    # player_bans = steam_user.get_formatted_player_bans(PERSONAL_STEAM_ID, sort_by="is_banned")
    # print(player_bans)

    # print("\nFetching ban categories for a single user:")
    # ban_categories = steam_user.get_formatted_player_bans(PERSONAL_STEAM_ID, group_by_ban_category=True)
    # print(ban_categories)

    # print("\nFetching user bans for multiple users:")
    # multiple_steam_ids = ",".join([entry["steamid"] for entry in EXAMPLE_STEAM_IDS.values()])
    # multiple_bans = steam_user.get_formatted_player_bans(multiple_steam_ids, group_by_ban_category=True)
    # print(multiple_bans)

    user_summaries = steam_user._retrieve_player_summaries_from_response(steam_user.fetch_player_summaries(PERSONAL_STEAM_ID))
    print("\nUser summaries:")
    print(user_summaries)

if __name__ == "__main__":
    main()