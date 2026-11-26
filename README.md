# luna-steampy

A Python library that makes Steam Web API accessible to developers. Wraps HTTP endpoints with type-hinted classes and structured objects, eliminating manual JSON parsing and data aggregation.

> **Status: In Development**  
> This library is under active development. Not recommended for production or commercial use.

## Why

The Steam Web API requires HTTP calls and manual JSON parsing. This library simplifies integration by providing:
- **Structured responses** via Python type-hinted classes
- **Multi-layer access** - use complete facades or access intermediate processing steps
- **Game & user data** - achievements, stats, schema metadata, and player information

## Quick Example

```python
from luna_steampy.endpoints.ISteamUserStats import ISteamUserStats

stats = ISteamUserStats()

# Fetch and format in one call
raw = stats.fetch_user_achievements("76561198141974862", 409720)
formatted = stats.format_user_achievement_stats(raw, appid=409720)

print(f"Achievements: {formatted['achieved_count']}")
print(f"Unlocked: {formatted['unlocked']}")
```

## Getting Started

1. **[Setup](docs/SETUP.md)** - Configure your Steam API key and Steam ID (5 minutes)
2. **[Architecture](docs/ARCHITECTURE.md)** - Understand how the library works and its design philosophy
3. **[Available Endpoints](docs/ENDPOINT_COVERAGE.md)** - See what methods are available and their parameters
4. **[Implementation Details](docs/DETAILS.md)** - Learn about roadmap, current limitations, and future plans

## Setup

**Local (Python only):**
```bash
cd luna-steampy
pip install -r program/requirements.txt
```

**Docker (with MongoDB):**
```bash
./fresh-start.sh
```

Then follow [SETUP.md](docs/SETUP.md) to add your Steam credentials and choose your setup path.

## What You Can Do

| Endpoint | Purpose |
|----------|---------|
| **ISteamUser** | Player profiles, friends lists, bans, vanity URLs |
| **ISteamUserStats** | Achievements, game stats, schema metadata |
| **ISteamWebAPIUtil** | Discover available Steam API methods |

See [ENDPOINT_COVERAGE.md](docs/ENDPOINT_COVERAGE.md) for the full method reference.

## Architecture Overview

The library uses a **base handler pattern**. Each endpoint class inherits from `SteamAPIHandler`, which provides:
- Request building and execution
- Error handling and validation
- Credential management

Methods are structured in **three layers**:
1. Fetch raw data from Steam API
2. Parse and enrich with schema metadata
3. Return fully formatted output

Call high-level methods for complete processing, or access intermediate steps for custom workflows. See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Running Tests

```bash
pytest tests/ -v -s
```

## Documentation

- **[SETUP.md](docs/SETUP.md)** - Credentials, configuration, and "why no Docker yet?"
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Design patterns, three-layer pipeline, error handling
- **[ENDPOINT_COVERAGE.md](docs/ENDPOINT_COVERAGE.md)** - Complete method list, why limited coverage
- **[DETAILS.md](docs/DETAILS.md)** - Implementation philosophy, roadmap, data portability plans
- **[AGENTS.md](AGENTS.md)** - Context for AI assistants working on this codebase
