# Setup

**Prerequisites:** Python 3.8+ and pip

## 1. API Key & Steam ID

Get your API key from [Steam API Key registration](https://steamcommunity.com/dev/apikey).

Find your 64-bit Steam ID at [steamid.io](https://steamid.io).

Create `auth/.env` and add both:
```
STEAM_API_KEY=YOUR_KEY_HERE
PERSONAL_STEAM_ID=YOUR_ID_HERE
```

## 2. Test

```bash
python3 -c "from config import STEAM_API_KEY, PERSONAL_STEAM_ID; print('OK' if STEAM_API_KEY and PERSONAL_STEAM_ID else 'Missing credentials')"
```

Keep `auth/.env` in `.gitignore` (it already is by default). Use `auth/example.env` as a reference.

## Why No Docker Yet?

Currently running locally without containerization. Priority was validating data fetching from Steam API before adding infrastructure. Docker integration planned post-database implementation. See [DETAILS.md](DETAILS.md#data-storage--docker) for roadmap.
