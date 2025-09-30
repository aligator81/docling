#!/bin/bash

# Docling Streamlit Application - Systemd Deployment Script
# This script sets up the systemd service for production deployment

set -e

echo "🚀 Starting Docling Streamlit Systemd Setup..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Variables
APP_DIR="/opt/docling-app"
SERVICE_FILE="/etc/systemd/system/docling-streamlit.service"
VENV_DIR="$APP_DIR/venv"
PYTHON_VERSION="3.11"

echo "📋 Setting up deployment environment..."

# Create application directory
if [[ ! -d "$APP_DIR" ]]; then
    echo "📁 Creating application directory: $APP_DIR"
    mkdir -p "$APP_DIR"
    chown docling:docling "$APP_DIR"
else
    echo "✅ Application directory already exists: $APP_DIR"
fi

# Create docling user if it doesn't exist
if ! id "docling" &>/dev/null; then
    echo "👤 Creating docling user..."
    useradd --system --shell /bin/bash --home "$APP_DIR" --create-home docling
else
    echo "✅ Docling user already exists"
fi

# Copy application files (assuming they're in current directory)
if [[ -f "requirements.txt" && -f "5-chat.py" ]]; then
    echo "📋 Copying application files to $APP_DIR..."
    cp -r . "$APP_DIR/"
    chown -R docling:docling "$APP_DIR"
    chmod +x "$APP_DIR"/*.py
    chmod +x "$APP_DIR"/*.sh
else
    echo "⚠️  Application files not found in current directory"
    echo "   Please ensure requirements.txt and 5-chat.py are present"
fi

# Set up Python virtual environment
if [[ ! -d "$VENV_DIR" ]]; then
    echo "🐍 Creating Python virtual environment..."
    cd "$APP_DIR"
    python$PYTHON_VERSION -m venv venv
    chown -R docling:docling "$VENV_DIR"
else
    echo "✅ Virtual environment already exists"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd "$APP_DIR"
sudo -u docling "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u docling "$VENV_DIR/bin/pip" install -r requirements.txt

# Create necessary directories
echo "📁 Creating data directories..."
sudo -u docling mkdir -p "$APP_DIR/data/uploads"
sudo -u docling mkdir -p "$APP_DIR/output"
sudo -u docling mkdir -p "$APP_DIR/cache"

# Copy systemd service file
echo "⚙️  Installing systemd service..."
cp "docling-streamlit.service" "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable the service
echo "🔗 Enabling docling-streamlit service..."
systemctl enable docling-streamlit.service

# Create environment file for sensitive data
ENV_FILE="$APP_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "📝 Creating environment file template..."
    cat > "$ENV_FILE" << EOF
# Docling Streamlit Environment Variables
# Copy this file and update with your actual values

# Neon Database Connection String
NEON_CONNECTION_STRING=postgresql://username:password@host/database

# OpenAI API Key (if using OpenAI)
OPENAI_API_KEY=your-openai-api-key-here

# Mistral API Key (if using Mistral)
MISTRAL_API_KEY=your-mistral-api-key-here

# Other environment variables as needed
EOF
    chown docling:docling "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "✅ Created $ENV_FILE template"
    echo "⚠️  IMPORTANT: Edit $ENV_FILE with your actual API keys and database credentials!"
else
    echo "✅ Environment file already exists: $ENV_FILE"
fi

echo ""
echo "🎉 Systemd service setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit $ENV_FILE with your actual credentials"
echo "2. Start the service: sudo systemctl start docling-streamlit"
echo "3. Check status: sudo systemctl status docling-streamlit"
echo "4. View logs: sudo journalctl -u docling-streamlit -f"
echo ""
echo "🌐 The application will be available at: http://your-server:8501"
echo ""
echo "🔧 Useful systemctl commands:"
echo "   sudo systemctl start docling-streamlit     # Start service"
echo "   sudo systemctl stop docling-streamlit      # Stop service"
echo "   sudo systemctl restart docling-streamlit   # Restart service"
echo "   sudo systemctl status docling-streamlit    # Check status"
echo "   sudo systemctl enable docling-streamlit    # Enable on boot"
echo "   sudo systemctl disable docling-streamlit   # Disable on boot"