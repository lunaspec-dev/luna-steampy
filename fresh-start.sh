#!/bin/bash

# Fresh start script for luna-steampy Docker environment
# Performs a clean shutdown and rebuild of all services

set -e  # Exit on error

echo "========================================"
echo "Luna-Steampy Fresh Start"
echo "========================================"
echo ""

echo "Attempting to perform a fresh start..."
echo "Cleaning up existing containers and volumes..."
docker-compose down -v

echo ""
echo "Building Docker image..."
docker-compose up -d --build

echo ""
echo "========================================"
echo "Fresh start complete!"
echo "Services are starting up..."
echo "========================================"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To run tests: docker-compose run --rm luna-steampy pytest -v"
