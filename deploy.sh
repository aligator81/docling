#!/bin/bash

# Docling Application Deployment Script
set -e

echo "🚀 Docling Application Deployment Script"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Function to check if .env file exists with OpenAI key
check_env() {
    if [ ! -f .env ]; then
        echo "⚠️  .env file not found. Creating from example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            echo "✅ Created .env file from example"
            echo "📝 Please edit .env file and add your OPENAI_API_KEY"
            exit 1
        else
            echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
            echo "✅ Created .env file"
            echo "📝 Please edit .env file and add your OPENAI_API_KEY"
            exit 1
        fi
    fi
    
    if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env; then
        echo "❌ OPENAI_API_KEY not configured in .env file"
        echo "📝 Please edit .env file and add your actual OpenAI API key"
        exit 1
    fi
}

# Function to build and start the application
deploy_app() {
    echo "🏗️  Building Docker image..."
    docker-compose build
    
    echo "🚀 Starting application..."
    docker-compose up -d
    
    echo "⏳ Waiting for application to start..."
    sleep 10
    
    # Check if application is running
    if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo "✅ Application deployed successfully!"
        echo "🌐 Open your browser and go to: http://localhost:8501"
    else
        echo "⚠️  Application might be starting up. Check logs with: docker-compose logs"
    fi
}

# Function to deploy to specific cloud platforms
deploy_to_platform() {
    local platform=$1
    
    case $platform in
        "render")
            echo "📦 Deploying to Render.com..."
            echo "1. Connect your GitHub repository to Render"
            echo "2. Set build command: docker build -t docling-app ."
            echo "3. Set start command: docker run -p 8501:8501 -e OPENAI_API_KEY=\$OPENAI_API_KEY docling-app"
            echo "4. Add environment variable OPENAI_API_KEY in Render dashboard"
            ;;
        "railway")
            echo "📦 Deploying to Railway..."
            echo "1. Connect your GitHub repository to Railway"
            echo "2. Railway will automatically detect the Dockerfile"
            echo "3. Add OPENAI_API_KEY environment variable in Railway dashboard"
            ;;
        "flyio")
            echo "📦 Deploying to Fly.io..."
            echo "1. Install flyctl: curl -L https://fly.io/install.sh | sh"
            echo "2. Run: flyctl launch --now"
            echo "3. Set secrets: flyctl secrets set OPENAI_API_KEY=your_key"
            ;;
        "heroku")
            echo "📦 Deploying to Heroku..."
            echo "1. Install Heroku CLI and login"
            echo "2. Create app: heroku create your-app-name"
            echo "3. Add buildpacks: heroku buildpacks:add heroku/python"
            echo "4. Set config: heroku config:set OPENAI_API_KEY=your_key"
            echo "5. Deploy: git push heroku main"
            ;;
        *)
            echo "❌ Unknown platform: $platform"
            echo "Supported platforms: render, railway, flyio, heroku"
            ;;
    esac
}

# Main execution
case "${1:-}" in
    "render"|"railway"|"flyio"|"heroku")
        deploy_to_platform "$1"
        ;;
    "")
        check_env
        deploy_app
        ;;
    "stop")
        echo "🛑 Stopping application..."
        docker-compose down
        ;;
    "logs")
        echo "📋 Showing logs..."
        docker-compose logs -f
        ;;
    "restart")
        echo "🔄 Restarting application..."
        docker-compose restart
        ;;
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker-compose down -v --rmi all --remove-orphans
        ;;
    *)
        echo "Usage: $0 [render|railway|flyio|heroku|stop|logs|restart|clean]"
        echo ""
        echo "Commands:"
        echo "  (no args)    Deploy locally with Docker Compose"
        echo "  render       Deploy to Render.com"
        echo "  railway      Deploy to Railway"
        echo "  flyio        Deploy to Fly.io"
        echo "  heroku       Deploy to Heroku"
        echo "  stop         Stop the application"
        echo "  logs         Show application logs"
        echo "  restart      Restart the application"
        echo "  clean        Remove all Docker resources"
        ;;
esac