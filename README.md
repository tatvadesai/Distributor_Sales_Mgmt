# Distributor Performance Tracking System

A Flask-based system for tracking distributor sales performance with territorial management, custom date ranges, and reporting capabilities.

## Features

- User authentication system
- Distributor management with territory assignment
- Sales target setting by week, month, quarter, or year
- Flexible sales data logging with customizable date ranges
- Performance reporting with PDF and Excel exports
- Dashboard with performance visualization

## Local Setup

### Prerequisites

- Python 3.11 or later
- PostgreSQL database

### Installation

1. Clone or download the repository to your local machine.

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r local_requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root with:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/dbname
   SESSION_SECRET=your_secret_key_here
   ```

5. Initialize the database:
   ```
   python
   >>> from app import app, db
   >>> with app.app_context():
   >>>     db.create_all()
   >>> exit()
   ```

6. Run the application:
   ```
   python -m flask run --host=0.0.0.0 --port=5000
   ```
   or with Gunicorn:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

7. Access the application at `http://localhost:5000`

## Default Login

The system doesn't come with a default user. You'll need to create one in the database:

```python
from app import db, app
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    user = User(
        username="admin",
        password_hash=generate_password_hash("your_password")
    )
    db.session.add(user)
    db.session.commit()
```

## Database Structure

- **User**: Authentication and system access
- **Distributor**: Company information with area/territory
- **Target**: Sales targets by period (weekly, monthly, quarterly, yearly)
- **Actual**: Actual sales with flexible date ranges

## Customization

- Modify templates in the `/templates` directory
- Static assets are in the `/static` directory
- CSS styling is primarily through Bootstrap with custom styling in `/static/css/custom.css`