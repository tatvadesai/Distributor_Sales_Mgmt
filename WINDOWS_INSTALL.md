# Windows Installation Guide for Sales Tracker

This guide explains how to install and run the Sales Tracker application on Windows.

## Prerequisites

- Windows 10 or 11
- Internet access (for initial installation only)

## Installation Instructions

### Step 1: Package the Application (For Developers Only)

If you are a developer packaging the application:

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```

2. Package the application using the spec file:
   ```
   pyinstaller app.spec
   ```

3. The packaged application will be in the `dist` folder.

### Step 2: Install the Application (For End Users)

1. Copy the entire `dist` folder to your preferred location (e.g., `C:\Program Files\SalesTracker` or `C:\Users\<YourUsername>\SalesTracker`).

2. Right-click on either:
   - `start_sales_tracker.bat` (shows a brief command window)
   - `start_sales_tracker_silent.vbs` (completely invisible startup)

3. Select "Send to" → "Desktop (create shortcut)".

4. Rename the shortcut on your desktop to "Sales Tracker" or your preferred name.

### Step 3: Configure Auto-Start (Optional)

To make the application start automatically when Windows boots:

1. Press `Win + R` to open the Run dialog.
2. Type `shell:startup` and press Enter.
3. Copy the shortcut you created (from your desktop) to this Startup folder.

## Usage

1. Double-click the "Sales Tracker" shortcut on your desktop.
2. The application will start in the background and automatically open in your default web browser.
3. Default login credentials:
   - Username: `admin`
   - Password: `admin123`

## Troubleshooting

If the application doesn't start:

1. Check the `app_launcher.log` file in the installation directory for error messages.
2. Ensure all required files are present in the installation directory.
3. Try running the executable directly by double-clicking `SalesTracker.exe`.
4. If you see a database error, ensure the application has write permissions to its directory.

## Uninstallation

1. Delete the shortcut from your desktop.
2. If configured for auto-start, open the startup folder (`Win + R`, type `shell:startup`) and remove the shortcut.
3. Delete the entire application folder.

## Security Notes

1. The application runs a local web server on port 5001, accessible only from your computer.
2. All data is stored locally in a SQLite database.
3. The application is configured to only accept connections from your local machine (127.0.0.1) for security. 