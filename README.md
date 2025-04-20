# Distributor Sales Management System

A Flask-based application for managing distributor sales targets and performance.

## Features

- Manage distributors and their contact details
- Set monthly sales targets
- Record actual sales performance
- Generate performance reports
- User authentication

## Installation

1. Clone this repository
2. Install dependencies using the provided script:

```bash
# Linux/Mac
./install_dependencies.sh

# Windows (run in Command Prompt)
pip install flask flask-login flask-sqlalchemy SQLAlchemy werkzeug jinja2 python-dotenv
```

## Running the Application

```bash
# Set the Flask application
export FLASK_APP=app.py

# Run the development server
flask run
```

On Windows:
```
set FLASK_APP=app.py
flask run
```

The application will be available at http://127.0.0.1:5000

## Date Picker Usage

The application includes a date picker for selecting date ranges. Simply click the "Select Dates" button next to any date field to open the date picker.

## Login

Default login credentials:
- Username: admin
- Password: admin123

## Overview

This application helps businesses track sales targets and actual performance for distributors. It provides tools for setting targets, recording actual sales, and generating reports.

## Quick Start

For non-technical users:

1. Double-click the `run.sh` file
2. Open your browser and navigate to: http://localhost:8080
3. Login with the default credentials:
   - Username: `admin`
   - Password: `admin123`

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## Screenshots

### Dashboard
![Dashboard](/attached_assets/dashboard.png)

### Distributors
![Distributors](/attached_assets/distributors.png)

### Reports
![Reports](/attached_assets/reports.png)

## Requirements

- Python 3.9 or higher
- Flask
- SQLAlchemy
- Other dependencies listed in `local_requirements.txt`

## Usage

After logging in, you can:

1. **Add Distributors**: Navigate to the Distributors page to add new distributors
2. **Set Targets**: Go to the Targets page to set performance goals
3. **Record Sales**: Use the Actuals page to record sales achievements
4. **View Reports**: Generate and export reports from the Reports page

## Technical Information

This application is built with:
- Flask web framework
- SQLite database (configurable)
- SQLAlchemy ORM
- Bootstrap for the UI
- ReportLab for PDF generation
- Pandas for data processing

## Support

For assistance, please contact:
- Email: support@pritenterprise.com
- Phone: +1-234-567-8900

## License

This software is proprietary and confidential.
© 2023-2024 Prit Enterprise. All rights reserved.