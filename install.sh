#!/bin/bash

# Installation script for Raspberry Pi Supabase Controller

echo "Installing Raspberry Pi Supabase Controller..."

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install Python if not installed
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    sudo apt-get install -y python3 python3-pip
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y python3-rpi.gpio python3-psutil

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit the .env file with your Supabase credentials and control unit ID"
fi

# Create systemd service
echo "Creating systemd service..."
SERVICE_PATH="/etc/systemd/system/rpi-supabase-controller.service"

if [ ! -f "$SERVICE_PATH" ]; then
    echo "Creating systemd service file..."

    # Get current directory
    CURRENT_DIR=$(pwd)

    # Create service file content
    SERVICE_CONTENT="[Unit]
Description=Raspberry Pi Supabase Controller
After=network.target

[Service]
User=$USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/main.py
Restart=on-failure
RestartSec=10s
StandardOutput=append:$CURRENT_DIR/controller.log
StandardError=append:$CURRENT_DIR/controller.log

[Install]
WantedBy=multi-user.target"

    # Write service file
    echo "$SERVICE_CONTENT" | sudo tee "$SERVICE_PATH" > /dev/null

    echo "Systemd service created at $SERVICE_PATH"
    echo "You can start it with: sudo systemctl start rpi-supabase-controller"
    echo "Enable it at boot with: sudo systemctl enable rpi-supabase-controller"
else
    echo "Systemd service already exists at $SERVICE_PATH"
fi

echo "Installation complete!"
echo "Please edit the .env file with your Supabase credentials and control unit ID before starting the controller."
echo "Run the controller with: python3 main.py"