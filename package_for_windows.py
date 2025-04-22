#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys

def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def run_command(command):
    print(f"Running: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"Command failed with exit code {process.returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False
    
    print(f"Command succeeded")
    return True

def check_pyinstaller():
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
        return True
    except ImportError:
        print("PyInstaller is not installed. Installing now...")
        if not run_command("pip install pyinstaller"):
            print("Failed to install PyInstaller. Please install it manually: pip install pyinstaller")
            return False
        return True

def copy_files_to_dist():
    dist_dir = "dist"
    if not os.path.exists(dist_dir):
        print(f"Error: {dist_dir} directory not found. PyInstaller build may have failed.")
        return False
    
    files_to_copy = [
        "start_sales_tracker.bat",
        "start_sales_tracker_silent.vbs",
        "WINDOWS_INSTALL.md"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            try:
                shutil.copy2(file, os.path.join(dist_dir, file))
                print(f"Copied {file} to {dist_dir}/")
            except Exception as e:
                print(f"Error copying {file}: {str(e)}")
        else:
            print(f"Warning: {file} not found, skipping")
    
    return True

def main():
    print_header("Windows Packaging Tool for Sales Tracker")
    
    # Check if PyInstaller is installed
    if not check_pyinstaller():
        return 1
    
    # Run PyInstaller
    print_header("Building application with PyInstaller")
    if not run_command("pyinstaller app.spec"):
        print("PyInstaller build failed.")
        return 1
    
    # Copy additional files to dist directory
    print_header("Copying additional files to distribution directory")
    if not copy_files_to_dist():
        print("Failed to copy some files.")
        return 1
    
    print_header("Packaging completed successfully!")
    print("\nThe packaged application is available in the 'dist' directory.")
    print("You can distribute the contents of the 'dist' directory to end users.")
    print("For installation instructions, see dist/WINDOWS_INSTALL.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 