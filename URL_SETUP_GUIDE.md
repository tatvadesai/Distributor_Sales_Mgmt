# Setting Up Your Personal URL for Distributor Tracker

This guide will help you set up a personal URL for your Distributor Tracker application, making it easier for non-technical users to access the system.

## Option 1: Basic Local Access (Easiest)

1. **Find Your Computer's IP Address**:
   - Press `Win + R`, type `cmd` and press Enter
   - In the command prompt, type `ipconfig` and press Enter
   - Look for "IPv4 Address" (something like 192.168.1.X)

2. **Share the IP and Port**:
   - Run the application using `run.bat`
   - Share the address with others on your network: `http://YOUR_IP_ADDRESS:8080`
   - Example: `http://192.168.1.10:8080`

## Option 2: Using a Free Domain Name Service

1. **Create a No-IP Account**:
   - Go to [No-IP.com](https://www.noip.com/) and sign up for a free account
   - Click "Create Hostname" and choose a name (e.g., `yourcompany.ddns.net`)

2. **Download and Install the No-IP Client**:
   - Download from [No-IP.com/download](https://www.noip.com/download)
   - Install and sign in with your No-IP account
   - The client will automatically update your IP address

3. **Configure Port Forwarding on Your Router**:
   - Access your router's admin panel (usually http://192.168.1.1)
   - Find "Port Forwarding" settings
   - Create a new rule:
     - External port: 80
     - Internal port: 8080 (the port your app runs on)
     - Internal IP: Your computer's IP address
     - Protocol: TCP

4. **Run Your Application**:
   - Run the app using `run.bat`
   - Users can now access the app at `http://yourcompany.ddns.net`

## Option 3: Using a Reverse Proxy Service (Zero Configuration)

1. **Create an ngrok Account**:
   - Go to [ngrok.com](https://ngrok.com/) and sign up for a free account
   - Verify your email and get your auth token

2. **Download and Install ngrok**:
   - Download from [ngrok.com/download](https://ngrok.com/download)
   - Extract the file to a folder of your choice

3. **Configure ngrok**:
   - Open command prompt
   - Navigate to where you extracted ngrok
   - Run: `ngrok config add-authtoken YOUR_TOKEN`

4. **Create Start Script**:
   - Create a new file named `start_with_url.bat` with this content:
   ```
   @echo off
   start run.bat
   echo Starting ngrok tunnel...
   start ngrok http 8080
   echo When you see the ngrok interface, look for "Forwarding" to find your URL
   echo The URL will look like: https://abc123.ngrok.io
   echo Share this URL with your users
   pause
   ```

5. **Run the Application With Public URL**:
   - Double-click `start_with_url.bat`
   - The ngrok window will show your public URL
   - Share this URL with your users (it looks like `https://abc123.ngrok.io`)

## Which Option Should I Choose?

- **Option 1**: Good for small business where all users are on the same network
- **Option 2**: Good for permanent setup where users are outside your network
- **Option 3**: Best for quick setup with minimal technical knowledge

If you need further assistance, please contact IT support. 