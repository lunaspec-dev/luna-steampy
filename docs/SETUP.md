# Setup

**Prerequisites:** Python 3.8+ and pip (for local setup) or Docker & Docker Compose (for containerized setup)

## 1. API Key & Steam ID

Get your API key from [Steam API Key registration](https://steamcommunity.com/dev/apikey).

Find your 64-bit Steam ID at [steamid.io](https://steamid.io).

Create `auth/.env` and add both:
```
STEAM_API_KEY=YOUR_KEY_HERE
PERSONAL_STEAM_ID=YOUR_ID_HERE
```

Keep `auth/.env` in `.gitignore` (it already is by default). Use `auth/example.env` as a reference.

## 2. Local Python Setup (No Docker)

Install dependencies:
```bash
pip install -r program/requirements.txt
```

Test your credentials:
```bash
python3 -c "from config import STEAM_API_KEY, PERSONAL_STEAM_ID; print('OK' if STEAM_API_KEY and PERSONAL_STEAM_ID else 'Missing credentials')"
```

Run scripts directly from `program/`:
```bash
python3 program/main.py
```

Or run tests:
```bash
cd program
pytest -v
```

## 3. Docker Setup (With MongoDB)

If you want containerized execution with database integration:

### Quick Start
```bash
./fresh-start.sh
```

This performs a clean shutdown, removes old volumes, rebuilds the image, and starts all services fresh.

### Manual Setup
```bash
# Start services
docker-compose up -d --build

# Run tests
docker-compose run --rm luna-steampy pytest -v

# Access bash in container
docker-compose run --rm luna-steampy bash

# View logs
docker-compose logs -f

# Shutdown
docker-compose down
```

### Services
- **luna-steampy**: Python application running Python 3.12
- **mongodb**: MongoDB database on `localhost:27017` (health check included)
- **Network**: Shared `luna-network` for service-to-service communication

MongoDB data persists in the `mongo_data` volume. Environment variables from `auth/.env` are automatically loaded into the container.

## Which Setup Should I Use?

**Local Python**: Install dependencies with pip, run scripts directly, quick iteration
**Docker**: Container isolation, integrated database, consistent environment across machines


