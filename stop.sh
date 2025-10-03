#!/bin/bash

# Script to stop the project

echo "🛑 Stopping Organizations Directory API..."

# Determine which Docker Compose command to use
DOCKER_COMPOSE=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ Docker Compose is not available."
    exit 1
fi

$DOCKER_COMPOSE down

if [ "$1" == "--clean" ]; then
    echo "🧹 Removing volumes..."
    $DOCKER_COMPOSE down -v
    echo "✅ All data removed"
else
    echo "✅ Application stopped"
    echo ""
    echo "💡 Tip: Use './stop.sh --clean' to remove all data including database"
fi
