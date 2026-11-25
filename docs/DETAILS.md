# Implementation Details & Roadmap

## Design Philosophy

This library focuses on data fetching and storage, allowing downstream projects (Discord bots, web apps, leaderboards) to build their own outputs on top of it. Code is intentionally designed to be modular, testable, and maintainable.

## Currently Implemented

- **ISteamUser** - Player summaries, friend lists, bans, vanity URLs
- **ISteamUserStats** - User achievements, game stats, achievement schemas
- **ISteamWebAPIUtil** - API capability discovery

## Planned Endpoints

- Achievement tracking and stats per player
- Global achievement percentages and tracking
- Game library browsing and search
- Steam Workshop integration for mod/item tracking
- Server tracking for multiplayer games
- Market data analysis

## Why Limited Coverage

Currently only implements a subset of Steam's available APIs. See [ENDPOINT_COVERAGE.md](ENDPOINT_COVERAGE.md) for details.

- Different endpoints require different authentication levels (public vs. developer)
- Some endpoints require game-specific credentials
- It's better to have few working endpoints than many untested ones

## Achievement Processing Pipeline

The `ISteamUserStats` class implements a three-layer processing pipeline:

1. **Raw Fetching** - `fetch_user_achievements(steamid, appid)` gets raw data from the API
2. **Schema Integration** - `format_user_achievement_stats(raw, appid)` merges player data with achievement metadata (display names, descriptions, icons)
3. **Quick Lookup** - `fetch_achievement_display_names(schema)` provides a simple name mapping for UI rendering

This design allows different use cases: work with raw data, fully enriched data, or quick lookup tables as needed.

For details on the architecture and design patterns, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Authentication & Access Levels

Steam API methods have varying access requirements:

- **Public Web API** - Freely available with an API key. Covers most user/game data queries.
- **Developer/Publisher API** - Requires publisher credentials. Access is game-specific.

Using a method without proper credentials will raise an error with context about what's needed.

## Data Storage & Docker

**Current approach:** Data instances are kept in program memory for the lifetime of the application. The library outputs structured Python objects and JSON natively. This works well for simple workflows and testing.

**Future:** Once database integration is added, Docker containerization will be implemented to simplify deployment and data persistence across application restarts. The library will provide transformation methods to shape fetched data for any backend (SQL, MongoDB, pandas, web apps) without vendor lock-in. All data remains portable and backend-agnostic.

Planned storage backends:
- **SQL (PostgreSQL/SQLite)** - For relational queries and analytics
- **MongoDB** - For flexible document storage
- **JSON output** - For web apps and dashboards
