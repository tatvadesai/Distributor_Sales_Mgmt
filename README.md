# Distributor Sales Management System

A comprehensive application for tracking distributor sales targets and performance.

## Overview

This application helps businesses track sales targets and actual performance for distributors. It provides tools for setting targets, recording actual sales, and generating reports.

## Features

- **User Authentication**: Secure login system
- **Distributor Management**: Add, edit, and manage distributors
- **Target Setting**: Set weekly, monthly, quarterly, or yearly targets
- **Sales Tracking**: Record actual sales for each period
- **Performance Analytics**: View performance metrics and trends
- **Reporting**: Generate PDF and Excel reports
- **Email Functionality**: Send reports via email
- **Backup System**: Automated database backups

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