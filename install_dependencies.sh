#!/bin/bash

echo "Installing required dependencies for Distributor Sales Management..."

# Try pip3 first, fall back to pip if not available
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

# Install required packages
echo "Installing Flask and dependencies..."
$PIP_CMD install flask flask-login flask-sqlalchemy SQLAlchemy werkzeug jinja2 python-dotenv

echo "Installation complete!"
echo "You can now run the application with: export FLASK_APP=app.py && flask run"

# Make the script executable
chmod +x install_dependencies.sh 