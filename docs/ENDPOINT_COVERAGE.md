# Endpoint Coverage

This document outlines the Steam Web API endpoints currently implemented in luna-steampy.

## Endpoint Completion Status

### Complete

- **ISteamUser** - All public Web API endpoints implemented. Developer-level methods (server-side operations, publishing tools) are planned for future versions with separate credential handling.

### In Progress / Planned

- **ISteamUserStats** - Core achievement and stats methods complete. Planned additions: leaderboard integration, achievement unlock rate analytics
- **ISteamWebAPIUtil** - Utility methods present. Future: introspection tools, endpoint validation helpers

## Developer-Level & Publisher Methods

Methods requiring publisher keys, developer credentials, or server-side operations are intentionally not included in the current release. These are on the roadmap for future versions with:

- Separate credential validation decorators
- Clear documentation on required access levels
- Example workflows for publisher authentication

See [DETAILS.md](DETAILS.md) for the full roadmap.

## Implemented Endpoints

### ISteamUser

Player and friend data operations. Facade methods (`get_*`) orchestrate full pipeline with aggregation and sorting; use `fetch_*` for raw API calls or intermediate methods for specific pipeline stages. **Status: Complete for public endpoints.**

| Method | Description | Access Level |
|--------|-------------|--------------|
| `get_formatted_friends_list(steamid, group_by_relationship, sort_by)` | Full pipeline: fetch friend list, format with metadata, optionally group by relationship type (friend/ignored/blocked), and sort | Public |
| `fetch_player_bans(steamids)` | Raw API response: check if players are banned (VAC, game ban, etc.) | Public |
| `fetch_player_summaries(steamids)` | Raw API response: player profile data (name, avatar, level, etc.) | Public |
| `resolve_vanity_url(vanityurl)` | Convert custom Steam URL to 64-bit Steam ID | Public |

### ISteamUserStats

Player achievement and game statistics. Facade methods (`get_*`) orchestrate the full pipeline; `fetch_*` returns raw API response; intermediate methods (prefixed `_` or public formatting methods) allow direct access to specific pipeline stages.

| Method | Description | Access Level |
|--------|-------------|--------------|
| `fetch_schema_for_game(appid)` | Raw API response: stats and achievements schema for a game | Public |
| `fetch_user_achievements(steamid, appid)` | Raw API response: player achievement data for a game | Public |
| `get_user_achievement_stats_for_game(steamid, appid, differentiate_locked, sort_by, return_raw)` | Full pipeline facade: fetch achievements and format with metadata, counts, and unlock times | Public |
| `get_user_completed_achievements(steamid, appid)` | Intermediate: achievements marked as completed with schema enrichment (pre-configured pipeline) | Public |
| `get_user_locked_achievements(steamid, appid)` | Intermediate: achievements marked as locked with schema enrichment (pre-configured pipeline) | Public |
| `get_global_achievement_percentages_for_app(appid)` | Raw API response: achievement completion percentages across all players | Public |
| `get_user_stats_for_game(steamid, appid)` | Raw API response: user-defined game statistics for a player | Public |
| `get_global_stats_for_game(appid, count, names)` | Raw API response: global statistics for a game | Public |

### ISteamWebAPIUtil

Utility methods for API inspection.

| Method | Description | Access Level |
|--------|-------------|--------------|
| `get_supported_api_list()` | List all available Steam Web API methods and their parameters | Public |

## Why Limited Coverage?

The Steam Web API has hundreds of available endpoints, but most existing wrappers focus on market interaction and trading automation. Luna-steampy intentionally implements a focused subset for a different use case:

**Core Philosophy:** Provide structured Python classes for achievement and game statistics retrieval - work with your own or others' progress data, not marketplace or client interactions.

This focus enables:

1. **Dev-Key Only Operations** - All implemented endpoints require only a public Web API dev key, no publisher credentials needed. This keeps the barrier to entry low.

2. **Use Case Clarity** - Achievement tracking, player statistics, and game schema data are the most common needs for Discord bots, leaderboards, and stats aggregators.

3. **Credential-Level Architecture** - Future versions will include decorators that validate credential levels before method access, automatically preventing misuse and guiding developers to the right endpoints.

4. **Modular Design** - Each Steam API interface (ISteamUser, ISteamUserStats, etc.) maps directly to a Python class. The structure mirrors the API itself. You work with intuitive objects and methods, not raw HTTP calls. This alignment makes the library feel natural to use and straightforward to extend/repair.

## Full API Reference

For the complete list of available Steam Web API endpoints, see the official [Steam Web API documentation](https://partner.steamgames.com/doc/webapi) or query locally:

```python
from luna_steampy.endpoints.ISteamWebAPIUtil import ISteamWebAPIUtil

util = ISteamWebAPIUtil()
all_methods = util.get_supported_api_list()

# Inspect available methods
for interface, methods in all_methods.items():
    print(f"{interface}: {len(methods)} methods")
```

Also check `config/available_endpoints.json` in the project for a cached reference.

## Contributing: Adding New Endpoints

To add a new endpoint:

1. **Create a new class** inheriting from `SteamAPIHandler`
2. **Implement endpoint methods** using `_build_endpoint()` and `_make_api_request()`
3. **Add documentation** to this file and `DETAILS.md`

Example:

```python
from luna_steampy.core.steam_api_handler import SteamAPIHandler

class ISteamApps(SteamAPIHandler):
    def get_app_list(self):
        """Get list of all Steam apps"""
        endpoint = self._build_endpoint("GetAppList")
        return self._make_api_request(endpoint, {})
    
    def get_app_details(self, appid):
        """Get details for a specific app"""
        endpoint = self._build_endpoint("GetAppDetails")
        return self._make_api_request(endpoint, {"appid": appid})
```

For architectural details, see [ARCHITECTURE.md](ARCHITECTURE.md).

````