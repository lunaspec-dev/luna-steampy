"""
Configuration loader for Steam API Explorer.
Loads and validates configuration from steam_api_config.json and example_app_list.json

Design: Config files in examples/ can be loaded as runtime variables. Sensitive or 
temporary data (dev examples, pre-generated lists, test Steam IDs) lives locally but 
stays out of version control via .gitignore, keeping the codebase clean while allowing 
flexible local development workflows.

If you want to take advantage and make your own just create any .json file in the examples/ directory and build a function in this script to assign it to a variable.
"""

import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the config directory (same directory as this file)
CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_FILE = CONFIG_DIR / "steam_api_config.json"
GAMES_FILE = CONFIG_DIR / "examples" / "example_app_list.json"
STEAM_IDS_FILE = CONFIG_DIR / "examples" / "example_steam_ids.json"


def load_config() -> dict:
    """Load and validate the main configuration file."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {CONFIG_FILE}")
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {CONFIG_FILE}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        raise

### !!! ### LOOK HERE FOR AN EXAMPLE USAGE OF CONFIG VARIABLES ### !!! ###
def load_example_games() -> dict:
    """Load example games from the app list file."""
    try:
        with open(GAMES_FILE, "r") as f:
            games = json.load(f)
        logger.info(f"Loaded {len(games)} games from {GAMES_FILE}")
        return games
    except FileNotFoundError:
        logger.warning(f"Games file not found: {GAMES_FILE}. Proceeding without example games.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in games file: {e}")
        return {}


def load_example_steam_ids() -> dict:
    """Load example Steam IDs for testing bans feature.
    
    Returns a dict of user entries with steamid and description fields.
    Users should populate this file with their own Steam IDs or friends' IDs.
    """
    try:
        with open(STEAM_IDS_FILE, "r") as f:
            data = json.load(f)
        logger.info(f"Loaded example Steam IDs from {STEAM_IDS_FILE}")
        return data.get("users", {})
    except FileNotFoundError:
        logger.warning(f"Steam IDs file not found: {STEAM_IDS_FILE}. Using empty dict.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Steam IDs file: {e}")
        return {}


# Load configuration
import os
import dotenv

# Load environment variables from .env file
auth_file = Path(__file__).parent.parent / "auth" / ".env"
dotenv.load_dotenv(auth_file)

CONFIG = load_config()

# Expose configuration values
STEAM_API_BASE_URL = CONFIG["urls"]["base_url"]
STEAM_API_PARTNER_URL = CONFIG["urls"]["partner_url"]
PERSONAL_STEAM_ID = os.getenv("PERSONAL_STEAM_ID")

# Ban types for categorization (can be overridden via STEAM_BAN_TYPES env var)
STEAM_BAN_TYPES = os.getenv("STEAM_BAN_TYPES", "vac_banned,community_banned,game_banned,economy_banned").split(",")

# Load example games
EXAMPLE_GAMES = load_example_games()

# Convenience access to game IDs only
EXAMPLE_GAME_IDS = [game_data["appid"] for game_data in EXAMPLE_GAMES.values()]

# Load example Steam IDs for testing
EXAMPLE_STEAM_IDS = load_example_steam_ids()


# Validation
if not PERSONAL_STEAM_ID:
    logger.warning("PERSONAL_STEAM_ID not set in .env file. Please configure it in auth/.env")
