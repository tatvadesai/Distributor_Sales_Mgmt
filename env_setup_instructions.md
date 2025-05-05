# Environment Variables Setup Guide

This guide helps you set up the required environment variables for the Sales Management System.

## Table of Contents
1. [Loading Environment Variables](#loading-environment-variables)
2. [Email Configuration (SMTP)](#email-configuration-smtp)
3. [Security Best Practices](#security-best-practices)

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

## Security Best Practices

1. **Environment Variables**:
   - Never share your `.env` file
   - Use strong, unique passwords
   - Regularly rotate your passwords

2. **Database Backups**:
   - Backups are stored locally in the `backups/` directory
   - Automated backups run three times a week
   - Manual backups can be created through the application interface
   - Regularly copy backups to an external storage device

3. **Application Security**:
   - Keep Python and all dependencies updated
   - Use strong passwords for user accounts
   - Regularly check application logs for suspicious activity 