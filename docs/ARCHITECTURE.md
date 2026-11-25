# Architecture

## Base Handler + Modular Subclasses

All endpoint classes inherit from `SteamAPIHandler` which provides:
- Request building (`_build_endpoint()`)
- Request execution (`_make_api_request()`)
- Error handling (`_check_response()`)
- Credential/config management

This eliminates duplication. Each subclass implements domain-specific methods:

```python
class ISteamUser(SteamAPIHandler):
    def get_friend_list(self, steamid):
        endpoint = self._build_endpoint("GetFriendList")
        return self._make_api_request(endpoint, {"steamid": steamid})
```

## Three-Layer Achievement Pipeline

Data fetching and processing is structured in layered "stops" - you can call facade methods for complete processing, or access any intermediate step directly.

### Pipeline Layers

Each endpoint implements a generalized processing pipeline:

1. **Request** - Fetch raw HTTP response from Steam API
2. **Parse & Enrich** - Extract and structure the response, merge with schema metadata
3. **Present Final Output** - Return fully formatted, queryable data structure

### Why Layered

The Steam API uses `interfaces` with independent and sometimes overlapping concerns. For example:
- `ISteamUserStats.GetUserStatsForGame` logically fits under "User Stats"
- `ISteamUserStats.GetGlobalStatsForGame` has no better home, also goes here
- Each interface often needs data from multiple underlying sources

This structure lets you:
- **Use facades** - Call high-level methods that do fetch → parse → format → return
- **Access stops** - Call intermediate methods when you only need raw data or just names
- **Compose custom flows** - Pull data at different layers and recombine as needed

### Example: Flexible Access

```python
from luna_steampy.endpoints.ISteamUserStats import ISteamUserStats

stats = ISteamUserStats()

# Full pipeline: one call, complete data
raw = stats.fetch_user_achievements("76561198141974862", 409720)
formatted = stats.format_user_achievement_stats(raw, appid=409720)
print(f"Achieved: {formatted['achieved_count']}")

# Quick lookup: skip full enrichment, just get display names
schema = stats.game_schema_manager.fetch_achievements_schema(409720)
names = stats.game_schema_manager.fetch_achievement_display_names(schema)
print(f"Achievement names: {names}")

# Direct access: grab raw response, process locally
raw_response = stats.fetch_user_achievements("76561198141974862", 409720)
print(f"Raw data: {raw_response}")
```

### Flexible Usage Patterns: Full Pipeline vs Custom Workflows

The three-layer design enables two distinct workflows:

**Pattern 1: Full Pipeline (Simple Use Case)**
Call the facade method (`get_*`), which orchestrates fetch + format in one call:
```python
# One call, complete output
achievements = stats.get_user_achievement_stats_for_game(steamid, appid, sort_by="unlock_time")
print(achievements["split_achievements"]["achieved"])
```

**Pattern 2: Reusable Raw Data (Advanced Use Case)**
Fetch once, format multiple ways without re-hitting the API:
```python
# Fetch once
raw = stats.fetch_user_achievements(steamid, appid)

# Format with different options
sorted_by_time = stats.format_user_achievement_stats(raw, appid, sort_by="unlock_time")
sorted_by_name = stats.format_user_achievement_stats(raw, appid, sort_by="display_name")
flat_list = stats.format_user_achievement_stats(raw, appid, differentiate_locked=False)

# Use all three formatted views without additional API calls
```

**Design Philosophy:**
- **`fetch_*` methods** return raw API responses—no processing, minimal cost, fully reusable
- **`format_*` methods** are lightweight transformations—take raw data, return formatted output
- **`get_*` facades** chain them together for convenience—one-liner for common workflows

This structure assumes: if you're calling a method on this library, you either want the full formatted output (facade) or you want raw data to process yourself (fetch + format separately). The passthrough tests verify the facade correctly chains both operations.

### Facade vs Manager Methods

Only the most important, commonly-used methods are exposed as facades on the main class (e.g., `stats.fetch_user_achievements()`). Intermediate operations and specialized concerns are accessed through their manager instances (e.g., `stats.game_schema_manager.fetch_achievement_display_names()`).

**Reason:**
- **Reduces clutter** - The main class surface stays focused; not every helper method clutters the namespace
- **Improves code tracing** - When you see `stats.game_schema_manager`, it's immediately clear you're crossing a concern boundary
- **Enforces separation** - GameSchemaManager handles schema concerns, GameStatManager handles stats concerns. This makes the codebase easier to reason about and maintain
- **Signals importance** - If a method lives on the main instance, it's something developers should commonly reach for (see `fetch_user_achievements()` vs `fetch_achievement_display_names()`)

---

## Error Handling

All API calls flow through `_make_api_request()` and `_check_response()` in the base handler:

- **Network/HTTP Errors** - Caught and wrapped with context about which endpoint failed
- **API Errors** - Steam API returns error codes in response JSON; `_check_response()` extracts and raises appropriate exceptions
- **Missing Credentials** - Requests without valid API key fail with clear error messages
- **Rate Limiting** - Steam API may return 429 Too Many Requests; handle with exponential backoff (future feature)

Downstream code should catch exceptions from endpoint methods and handle gracefully:

```python
from luna_steampy.endpoints.ISteamUser import ISteamUser

user = ISteamUser()

try:
    summary = user.get_player_summaries(steamid)
except Exception as e:
    print(f"Failed to fetch player: {e}")
```

---

For setup, see [SETUP.md](SETUP.md). For vision/endpoints, see [DETAILS.md](DETAILS.md).
