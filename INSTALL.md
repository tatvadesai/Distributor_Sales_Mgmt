# Distributor Sales Tracker - Installation Guide

This guide will help you set up the Distributor Sales Tracker application on your server.

## Quick Start for Non-Technical Users

1. **For Local Test/Development:**
   - Double-click the `run.sh` file to start the application
   - Open your browser and go to: http://localhost:8080
   - Login with username: `admin` and password: `admin123`

2. **For Production Deployment:**
   Follow the complete installation guide below or ask your IT administrator to help you set it up.

## Complete Installation Guide

### Prerequisites

- Python 3.9 or higher
- Access to a terminal/command prompt
- Basic knowledge of server administration (or assistance from IT)

### Step 1: Set Up the Environment

```bash
# Create the application directory
sudo mkdir -p /var/www/distributor-tracker
sudo mkdir -p /var/lib/distributor_tracker
sudo mkdir -p /var/log/distributor-tracker

# Set appropriate permissions
sudo chown -R www-data:www-data /var/www/distributor-tracker
sudo chown -R www-data:www-data /var/lib/distributor_tracker
sudo chown -R www-data:www-data /var/log/distributor-tracker

# Copy the application files
sudo cp -r * /var/www/distributor-tracker/
sudo cp .env.production /var/www/distributor-tracker/.env

# Create a Python virtual environment
cd /var/www/distributor-tracker
sudo python3 -m venv venv
sudo venv/bin/pip install -r local_requirements.txt
sudo venv/bin/pip install gunicorn
```

### Step 2: Configure the Database

The database will be automatically created when the application runs for the first time.

### Step 3: Set Up the Service

```bash
# Copy the service file
sudo cp distributor-tracker.service /etc/systemd/system/

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable distributor-tracker
sudo systemctl start distributor-tracker
```

### Step 4: Configure a Web Server (Optional, but Recommended)

For better security and performance, you can set up Nginx as a reverse proxy:

```bash
# Install Nginx
sudo apt update
sudo apt install nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/distributor-tracker
```

Add the following content:

```
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or server IP

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then:

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/distributor-tracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5: Access the Application

Open a web browser and go to:
- http://your-domain.com (if you configured Nginx)
- or http://your-server-ip:8080 (direct access)

Log in with the default credentials:
- Username: `admin`
- Password: `admin123`

**Important:** Change the default password immediately after your first login!

## Troubleshooting

If you encounter any issues:

1. Check the log files in `/var/log/distributor-tracker/`
2. Ensure all services are running: `sudo systemctl status distributor-tracker`
3. Check the application permissions: `sudo chown -R www-data:www-data /var/www/distributor-tracker` 