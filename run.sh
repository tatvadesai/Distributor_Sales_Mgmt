#!/bin/bash

echo "===== Distributor Tracker App ====="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing dependencies..."
pip install -r local_requirements.txt

# Ensure database directory exists
mkdir -p instance

# Start the application
export FLASK_APP=app.py
export FLASK_DEBUG=True

echo "Starting server on port 8080..."
echo "Access the application at: http://localhost:8080"
python -m flask run --host=0.0.0.0 --port=8080 