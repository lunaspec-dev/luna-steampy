import sys
from pathlib import Path

import json

# Add parent directory to path so we can import steam_api_core
sys.path.insert(0, str(Path(__file__).parent.parent))

from steamweb_api_core import SteamAPIHandler

class ISteamWebAPIUtil(SteamAPIHandler):
    """Interact with the ISteamWebAPIUtil endpoint of the Steam API."""

    def __init__(self, version: str = "v1") -> None:
        """Initialize ISteamWebAPIUtil with the parent SteamAPIHandler."""
        super().__init__()
        self.api_interface = "ISteamWebAPIUtil"
        self.version = version

    def get_supported_api_list(self) -> dict:
        """Get the complete list of supported Steam Web API methods."""
        endpoint = self._build_endpoint("GetSupportedAPIList")
        return self._make_api_request(endpoint)

def main():
    # Example usage of the ISteamWebAPIUtil class
    api_util = ISteamWebAPIUtil()
    supported_apis = api_util.get_supported_api_list()
    print(json.dumps(supported_apis, indent=4))

if __name__ == "__main__":
    main()