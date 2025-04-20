#!/bin/bash
# Setup script for Distributor Tracker application
# This script will set up a Python virtual environment and install all required dependencies

echo "Setting up Distributor Tracker Application..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.8 or higher."
    exit 1
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
fi

# Activate the virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate

# Upgrade pip to the latest version
echo "Upgrading pip to the latest version..."
pip install --upgrade pip

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

# Install additional packages explicitly in case the requirements.txt doesn't work
echo "Installing critical packages explicitly..."
pip install flask flask-login SQLAlchemy Flask-SQLAlchemy

# Initialize the database if it doesn't exist
if [ ! -f "data.db" ]; then
    echo "Initializing the database..."
    python init_db.py
    if [ $? -ne 0 ]; then
        echo "Error: Failed to initialize the database."
        exit 1
    fi
fi

echo
echo "Setup completed successfully!"
echo
echo "To run the application:"
echo "1. In this directory, run: source venv/bin/activate"
echo "2. Then run: python app.py"
echo
echo "The application will be accessible at http://127.0.0.1:5000"
echo

# Make the script executable
chmod +x setup.sh 