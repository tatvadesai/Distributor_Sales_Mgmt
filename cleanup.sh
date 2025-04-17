#!/bin/bash

echo "Cleaning up unnecessary files for Mac development environment..."

# Remove Windows-specific files
rm -f cleanup.bat
rm -f run.bat
rm -f start_with_url.bat
rm -f WINDOWS_SETUP.md

# Remove Linux-specific files
rm -f distributor-tracker.service

# Remove Replit-specific files
rm -f .replit
rm -f replit.nix
rm -f uv.lock

# Remove old documentation
rm -f README.md
rm -f INSTALL.md
rm -f env_setup_instructions.md

# Remove migration and initialization tools
rm -f migrate_target_table.py
rm -f init_db.py
rm -f main.py

# Create a simple Mac README
cat > README.md << 'EOF'
# Distributor Performance Tracker

## Setup for Mac

1. **Prerequisites**:
   - Python 3.8 or higher
   - pip package manager

2. **Installation**:
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd <repository-directory>
   
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r local_requirements.txt
   ```

3. **Running the application**:
   ```bash
   # Set environment variables
   export FLASK_APP=app.py
   export FLASK_DEBUG=True
   
   # Run the application
   flask run --host=0.0.0.0 --port=8080
   ```

4. **Access the application**:
   - Open your browser and navigate to: `http://localhost:8080`
   - Login with default credentials:
     - Username: `admin`
     - Password: `admin123`

## Testing
Run the tests with:
```bash
python -m pytest
```
EOF

# Create a run script for Mac
cat > run.sh << 'EOF'
#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if required packages are installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "Flask is not installed. Installing required packages..."
    pip3 install -r local_requirements.txt
    if [ $? -ne 0 ]; then
        echo "Failed to install required packages. Please check your internet connection."
        exit 1
    fi
fi

# Ensure database directory exists
mkdir -p instance

# Start the application
export FLASK_APP=app.py
export FLASK_DEBUG=True

echo "Starting server on port 8080..."
python3 -m flask run --host=0.0.0.0 --port=8080
EOF

# Make the run script executable
chmod +x run.sh

echo "Done! The following files have been kept:"
echo "- app.py (Main application)"
echo "- routes.py (Application routes)"
echo "- models.py (Database models)"
echo "- utils.py (Utility functions)"
echo "- wsgi.py (WSGI entry point)"
echo "- templates/ (HTML templates)"
echo "- static/ (CSS/JS assets)"
echo "- instance/ (Database directory)"
echo "- backup_utils.py (Backup functionality)"
echo "- run.sh (Mac startup script)"
echo "- README.md (Installation instructions)"
echo "- local_requirements.txt (Dependencies)"
echo "- .env & .env.production (Environment configurations)"

echo "Created test directory with basic tests" 