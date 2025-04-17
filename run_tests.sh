#!/bin/bash

echo "===== Running Tests for Distributor Tracker ====="

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

# Install required packages (including test dependencies)
echo "Installing dependencies..."
pip install -r local_requirements.txt
pip install pytest-cov

echo "Running tests..."
python -m pytest -v

# Ask if the user wants to generate a coverage report
echo ""
echo "Do you want to generate a test coverage report? (y/n)"
read -r generate_coverage

if [[ $generate_coverage == "y" || $generate_coverage == "Y" ]]; then
    echo "Generating coverage report..."
    python -m pytest --cov=. --cov-report=term
    
    echo ""
    echo "Do you want to generate an HTML coverage report? (y/n)"
    read -r generate_html
    
    if [[ $generate_html == "y" || $generate_html == "Y" ]]; then
        python -m pytest --cov=. --cov-report=html
        echo "HTML report generated in the htmlcov directory."
        echo "Open htmlcov/index.html in a browser to view it."
    fi
fi

echo "Tests completed!" 