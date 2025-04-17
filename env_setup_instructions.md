# Environment Variables Setup Guide

This guide helps you set up the required environment variables for the Sales Management System.

## Table of Contents
1. [Loading Environment Variables](#loading-environment-variables)
2. [Email Configuration (SMTP)](#email-configuration-smtp)
3. [Supabase Configuration](#supabase-configuration)
4. [Security Best Practices](#security-best-practices)

## Loading Environment Variables

The application uses environment variables stored in a `.env` file. Follow these steps to set up:

1. Make sure the `python-dotenv` package is installed:
   ```
   pip install python-dotenv
   ```

2. Place the `.env` file in the root directory of your application.

3. Never commit the `.env` file to version control (it should be in your `.gitignore`).

## Email Configuration (SMTP)

The application uses SMTP to send emails. Here's how to set up email credentials:

### For Gmail

1. **Create an App Password** (recommended over using your regular password):
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Make sure 2-Step Verification is enabled
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Other (Custom name)" - name it "Sales Management System"
   - Copy the generated 16-character password

2. **Update your `.env` file**:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_16_char_app_password
   EMAIL_FROM=your_email@gmail.com
   ```

### For Other Email Providers

1. Find your email provider's SMTP details:
   - **Outlook/Hotmail**: 
     - Server: `smtp-mail.outlook.com`
     - Port: `587`
   - **Yahoo Mail**:
     - Server: `smtp.mail.yahoo.com`
     - Port: `587`

2. Update the `.env` file accordingly.

3. Test the email configuration using the Email Test page in the application.

## Supabase Configuration

Supabase is used for cloud database backups. Follow these steps to set up:

1. **Create a Supabase Account**:
   - Go to [Supabase](https://supabase.com) and sign up
   - Create a new project with a name like "Sales-Management-Backups"

2. **Create the Backups Table**:
   - Go to the "Table Editor" in your Supabase dashboard
   - Click "Create a new table"
   - Name it `backups`
   - Add the following columns:
     - `id` (type: `uuid`, check "Primary Key")
     - `backup_id` (type: `text`)
     - `table_name` (type: `text`)
     - `timestamp` (type: `text`)
     - `data` (type: `text`)
   - Click "Save"

3. **Get Your Credentials**:
   - Go to Project Settings > API
   - Find your Project URL and API Key (use the "anon" public key)
   - Copy these values to your `.env` file:
     ```
     SUPABASE_URL=https://your-project-id.supabase.co
     SUPABASE_KEY=your_supabase_api_key
     ```

4. **Test the Backup System**:
   - Restart your application
   - Go to the Backup page
   - Click "Backup Now" to test

## Security Best Practices

1. **Generate a Strong Session Secret**:
   - Open a terminal and run:
     ```
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   - Copy the output to the `SESSION_SECRET` variable

2. **Limit Access to Your .env File**:
   - Set restrictive file permissions:
     ```
     chmod 600 .env
     ```
   - Ensure only the application user can read it

3. **Rotate Credentials Regularly**:
   - Change the API keys and passwords every 90 days
   - Update the `.env` file after each rotation

4. **Use Minimum Required Permissions**:
   - For Supabase, use the "anon" key which has limited permissions
   - Create a dedicated email account for sending notifications

5. **Monitoring**:
   - Regularly check your Supabase usage
   - Monitor email sending logs for unauthorized use 