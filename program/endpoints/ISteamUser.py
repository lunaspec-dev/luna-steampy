import sys
from pathlib import Path

# Add parent directory to path so we can import steam_api_core
sys.path.insert(0, str(Path(__file__).parent.parent))

from steamweb_api_core import SteamAPIHandler
from config import PERSONAL_STEAM_ID

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

    def _get_user_friend_list_from_response(self, response: dict) -> list:
        """Extract the friend list from the API response."""

        if response.get("friendslist") is None:
            raise ValueError("No friends list found in the response - check if the profile is private or if the Steam ID is valid.")

        new_response = response.get("friendslist", {}).get("friends", [])

        return new_response

    def _get_friends_list_by_relationship(self, response: dict) -> list:
        """Returns a dictionary with the friends list split by relationship type (e.g., 'friend', 'blocked', etc.)."""

        friends = self._get_user_friend_list_from_response(response)

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
            result = self._get_user_friend_list_from_response(friend_list)

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

    def fetch_player_summaries(self, steamids: str) -> dict:
        """Get profile information for one or more Steam users."""
        endpoint = self._build_endpoint("GetPlayerSummaries")
        params = {"steamids": steamids}
        return self._make_api_request(endpoint, params)

    def resolve_vanity_url(self, vanityurl: str) -> dict:
        """Resolve a custom Steam URL to a Steam ID."""
        endpoint = self._build_endpoint("ResolveVanityURL")
        params = {"vanityurl": vanityurl}
        return self._make_api_request(endpoint, params)

def main():
    # Example usage of the ISteamUser class
    steam_user = ISteamUser()
    friend_list = steam_user.fetch_friend_list(PERSONAL_STEAM_ID)
    print(friend_list)

    print("\nFormatted friends list grouped by relationship:")
    formatted_friends = steam_user.get_formatted_friends_list(PERSONAL_STEAM_ID, group_by_relationship=True, sort_by="friend_since")
    print(formatted_friends)

if __name__ == "__main__":
    main()