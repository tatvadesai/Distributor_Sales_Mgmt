# Sales Tracker Application - Windows Edition

## Overview

This is the Windows-optimized version of the Sales Tracker application, designed to run seamlessly as a desktop application with browser interface. The app helps you track distributor sales targets and achievements.

## Key Features

- **Desktop Integration**: Runs as a native Windows application with desktop shortcut
- **Auto-Launch**: Can be configured to start automatically when Windows boots
- **Browser Interface**: Automatically opens in your default web browser
- **Offline Capability**: Fully functional without internet (except for Supabase backups)
- **Local Data Storage**: Uses SQLite for robust local data storage

## Installation

See the included `WINDOWS_INSTALL.md` file for detailed installation instructions.

## Quick Start

1. Double-click the desktop shortcut
2. The application will launch and open in your browser
3. Log in with the default credentials:
   - Username: `admin`
   - Password: `admin123`

## Default Port

The application runs on port 5001 by default. You can access it at:
```
http://127.0.0.1:5001
```

## Troubleshooting

If you encounter any issues:

1. Check the `app_launcher.log` file in the installation directory
2. Try restarting the application
3. Refer to the troubleshooting section in `WINDOWS_INSTALL.md`

## Security

- The application only accepts connections from localhost (127.0.0.1)
- All data is stored locally in a SQLite database
- The application runs with user privileges, not system privileges

## For Developers

If you need to modify or rebuild the application, see the "For Developers" section in `WINDOWS_INSTALL.md`. 