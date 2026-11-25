# This script will handle the main functionality for handling HTTP requests to the Steam API. 
#
# The idea is to keep functionality separated into separate files based on the the endpoints being reached so that aggregate functionality can be handled in a single file.
#
# That being said, the subsequent modular files will import classes from this file to handle the actual HTTP requests and return the data in a usable format.

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests # Handles the HTTP requests to the Steam API

import os # Handles the environment variables for the Steam API key as well as the file paths for the JSON files that will be created
import dotenv # Handles the loading of environment variables from a .env file
import json # Handles the JSON data returned from the Steam API

import time # Handles the time delays between requests to the Steam API

import logging # Handles the logging of errors and other information
from datetime import datetime # For converting unix timestamps to human-readable format

import tqdm # This isnt strictly necessary, but it's an easy library to use for progress bars
# Some requests will need to be done in small batches over time as to not upset the Steam overlords.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # basic logging configuration
auth_file = Path(__file__).parent.parent / "auth" / ".env" # Get the path to the .env file relative to this script
dotenv.load_dotenv(auth_file) # Load environment variables from .env file

def load_available_endpoints(endpoints_info_file_path="config/steam_api_endpoints_info.json") -> dict:
    """Load available Steam API endpoints from a JSON file."""
    endpoints_file = Path(__file__).parent / endpoints_info_file_path
    try:
        with open(endpoints_file, "r") as f:
            return json.load(f)
        
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to load endpoints file: {e}")
        return {}

def load_error_codes(error_codes_path="config/api_error_codes.json") -> dict:
    """Load HTTP error codes and descriptions from a JSON file."""
    error_file = Path(__file__).parent / error_codes_path
    try:
        with open(error_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to load error codes file: {e}")
        return {}

ALL_ENDPOINTS = load_available_endpoints()
ERROR_CODES_CONFIG = load_error_codes()

class SteamAPIHandler:
    def __init__(self):
        self.api_key = os.getenv("STEAM_API_KEY") # Get the Steam API key from the environment variable
        if not self.api_key:
            raise ValueError("Steam API key not found. Please set STEAM_API_KEY environment variable.")
        
        self.base_url = "https://api.steampowered.com" # Base URL for the Steam API
        self.partner_url = "https://partner.steam-api.com" # Base URL for the Steam Partner API
        self.available_endpoints = ALL_ENDPOINTS # Available endpoints loaded from the JSON file

        ###################
        # This is a lazy way to pull the api key and url and stuff, the api key will be stored safely in an environment variable, and the base urls will be stored in a config file. 
        # This is to avoid hardcoding sensitive information into the codebase. (Even though steam api enpoints are public, will help to keep it out of hardcoded variables)
        ###################

    def _get_api_url(self, partner_api: bool = False) -> str:
        """Get the appropriate API URL based on configuration."""
        return self.partner_url if partner_api else self.base_url

    def _display_available_endpoints(self) -> None:
        """Display available Steam API endpoints."""
        print("Available Steam API Endpoints:")
        for category, endpoints in self.available_endpoints.items():
            print(f"\n{category}:")
            for endpoint in endpoints:
                print(f"  - {endpoint}")

    def _build_endpoint(self, method: str, api_interface: str = None, version: str = None) -> str:
        """
        Build the endpoint path using the class's api_interface and version.
        """
        ver = version or self.version
        interface = api_interface or self.api_interface

        return f"/{interface}/{method}/{ver}/"
    
    def _convert_unix_timestamp(self, timestamp: int, format: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Convert unix timestamp to human-readable string.
        
        Args:
            timestamp (int): Unix timestamp (seconds since epoch)
            format (str): strftime format string. Defaults to '%Y-%m-%d %H:%M:%S'
            
        Returns:
            str: Formatted datetime string, or 0 if timestamp is 0 or missing
        """
        if timestamp:
            return datetime.fromtimestamp(timestamp).strftime(format)
        return 0
    
    def _check_response(self, status_code: int, response: dict) -> dict:
        """Check and handle HTTP response based on status code.
        
        Validates response and logs appropriate messages based on HTTP status.
        Captures both standard error codes (from config) and server-provided error messages.
        See config/api_error_codes.json for reference.
        
        Args:
            status_code (int): HTTP status code from response
            response (dict): Response data from API
        
        Returns:
            dict: Validated response data with error info if applicable
        """
        error_config = ERROR_CODES_CONFIG.get("error_codes", {})
        status_info = error_config.get(str(status_code), {})
        
        # Extract server error message if present (common fields: error, message, strError)
        server_response = response.get("error") or response.get("message") or response.get("strError")
        
        # Success case
        if 200 <= status_code < 300:
            if not response:
                logging.warning(f"Status {status_code}: Empty response body")
                return {"error": f"Empty response (status {status_code})"}
            return response
        
        # Error cases (4xx and 5xx)
        elif status_code >= 400:
            error_category = "Client error" if 400 <= status_code < 500 else "Server error"
            known_error = f"{status_info.get('status', 'Unknown')}: {status_info.get('description', error_category)}"
            error_msg = known_error if not server_response else f"{known_error} - Server: {server_response}"
            logging.error(f"Status {status_code}: {error_msg}")
            return {"error": error_msg, "status_code": status_code, "server_response": server_response}
        
        # Other
        else:
            logging.warning(f"Unexpected status code: {status_code}")
            return response if response else {"error": f"Unexpected status {status_code}"}
    
    def _make_api_request(self, endpoint: str, params: dict = {}, partner_api: bool = False, return_status: bool = False) -> dict | tuple:
        """Make a request to the Steam API and return the JSON response.
        
        Args:
            endpoint (str): The API endpoint to call (e.g., "/ISteamUser/GetPlayerSummaries/v2/").
            params (dict, optional): Additional parameters to include in the request. Defaults to {}.
            partner_api (bool, optional): Whether to use the partner API URL. Defaults to False.
            return_status (bool, optional): If True, return (status_code, response). If False, return response only. Defaults to False.
        
        Returns:
            dict: JSON response (if return_status=False) or empty dict on error
            tuple: (status_code, response_dict) if return_status=True, or (500, {}) on error
        """
        params["key"] = self.api_key
        api_url = self._get_api_url(partner_api)
        request_url = f"{api_url}{endpoint}"

        try:
            response = requests.get(request_url, params=params)
            json_response = response.json()
            validated_response = self._check_response(response.status_code, json_response)
            
            if return_status:
                return response.status_code, validated_response
            return validated_response

        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            error_response = {"error": f"Request failed: {str(e)}"}
            if return_status:
                return 500, error_response
            return error_response

def main():
    # Example usage of the SteamAPIHandler class
    steam_api_handler = SteamAPIHandler()
    
    # Display available endpoints
    steam_api_handler.display_available_endpoints()

    print("\nMaking a sample API request to ISteamUser...")

if __name__ == "__main__":
    main()