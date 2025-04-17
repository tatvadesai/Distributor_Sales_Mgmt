# Simple Setup Guide for Mac

## One-time Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment (you need to do this each time you open a new terminal)
source venv/bin/activate

# Install dependencies
pip install -r local_requirements.txt
```

## Running the Application

```bash
# Activate the virtual environment (if not already activated)
source venv/bin/activate

# Set up Flask environment variables
export FLASK_APP=app.py
export FLASK_DEBUG=True

# Start the application
flask run --host=0.0.0.0 --port=8080
```

## Running Tests

```bash
# Activate the virtual environment (if not already activated)
source venv/bin/activate

# Install test dependencies if needed
pip install pytest pytest-flask pytest-cov

# Run the tests
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=term

# Generate HTML coverage report
pytest --cov=. --cov-report=html
```

## Troubleshooting

If you see errors about missing modules:

1. Make sure your virtual environment is activated (you should see `(venv)` in your prompt)
2. Try reinstalling dependencies: `pip install -r local_requirements.txt`
3. Check if Flask is installed: `pip list | grep Flask`

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Deactivate virtual environment
deactivate

# Update pip
pip install --upgrade pip

# Show installed packages
pip list
``` 