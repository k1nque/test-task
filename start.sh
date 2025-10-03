#!/bin/bash

# Script to start the project using Docker

echo "🚀 Starting Organizations Directory API..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Determine which Docker Compose command to use
DOCKER_COMPOSE=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo "✓ Using 'docker compose' (Docker Compose V2)"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo "✓ Using 'docker-compose' (Docker Compose V1)"
else
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please review and update if needed."
fi

# Stop and remove existing containers
echo "🧹 Cleaning up existing containers..."
$DOCKER_COMPOSE down

# Build and start containers
echo "🔨 Building and starting containers..."
$DOCKER_COMPOSE up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo ""
    echo "✅ Application started successfully!"
    echo ""
    echo "📚 API Documentation:"
    echo "   - Swagger UI: http://localhost:8000/docs"
    echo "   - ReDoc: http://localhost:8000/redoc"
    echo "   - API Endpoint: http://localhost:8000/api/v1/"
    echo ""
    echo "🔑 API Key: your-secret-api-key-change-in-production"
    echo ""
    echo "📊 To view logs:"
    echo "   $DOCKER_COMPOSE logs -f"
    echo ""
    echo "🛑 To stop the application:"
    echo "   $DOCKER_COMPOSE down"
else
    echo "❌ Failed to start application. Check logs with: $DOCKER_COMPOSE logs"
    exit 1
fi
