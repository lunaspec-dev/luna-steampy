"""
Configuration module for Steam API Explorer.
Exposes all configuration variables and loaders.
"""

from .settings import (
    CONFIG,
    STEAM_API_BASE_URL,
    STEAM_API_PARTNER_URL,
    PERSONAL_STEAM_ID,
    STEAM_BAN_TYPES,
    EXAMPLE_GAMES,
    EXAMPLE_GAME_IDS,
    EXAMPLE_STEAM_IDS,
    load_config,
    load_example_games,
    load_example_steam_ids,
)

__all__ = [
    "CONFIG",
    "STEAM_API_BASE_URL",
    "STEAM_API_PARTNER_URL",
    "PERSONAL_STEAM_ID",
    "STEAM_BAN_TYPES",
    "EXAMPLE_GAMES",
    "EXAMPLE_GAME_IDS",
    "EXAMPLE_STEAM_IDS",
    "load_config",
    "load_example_games",
    "load_example_steam_ids",
]
