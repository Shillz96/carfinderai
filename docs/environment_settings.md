# Environment Variables Configuration

CarFinderAI uses environment variables (stored in a `.env` file) to configure many aspects of the application. This document explains how to use the web interface to manage these settings.

## Overview

The Environment Variables Configuration page provides an easy-to-use interface for viewing and editing the application's configuration without directly editing the `.env` file. This feature is helpful for users who are not comfortable with text editing or need guidance on available settings.

## Accessing Environment Settings

1. Log in to the CarFinderAI web interface
2. Navigate to the "Settings" page from the main navigation menu
3. Click on the "Manage Environment Variables" button in the Application Environment Configuration section

## Managing Settings

### Types of Settings

The interface displays various types of configuration settings:

- **Text Fields**: For general string values (API keys, URLs, email addresses, etc.)
- **Number Fields**: For numeric values (minimum vehicle year, timeouts, etc.)
- **Dropdown Menus**: For settings with predefined options (log levels, etc.)
- **Boolean Fields**: For true/false settings (displayed as dropdown menus)

### Sensitive Information

Some settings contain sensitive information (like API keys or passwords). These are handled specially:

- Existing values are masked with asterisks (`********`)
- To keep an existing sensitive value, leave the masked value as is
- To change a sensitive value, enter a new value
- To clear a sensitive value, delete the masked value and leave the field blank

### Saving Changes

1. Modify the desired settings
2. Click the "Save All Settings" button at the bottom of the page
3. Review the success/failure messages that appear

## Important Notes

- Some changes may require an application restart to take full effect
- Settings are stored in the `.env` file in the project root directory
- Each setting includes a helpful description explaining its purpose and format
- Invalid values (wrong format, etc.) will be rejected with an appropriate error message

## Common Settings

Some of the most frequently modified settings include:

- `GOOGLE_SHEET_ID`: The ID of the Google Sheet used to store leads
- `MIN_VEHICLE_YEAR`: The minimum year for vehicles to be considered as leads
- `LOG_LEVEL`: The verbosity of application logging
- `TWILIO_PHONE_NUMBER`: The phone number used for SMS notifications

## Troubleshooting

If you encounter issues with environment settings:

1. Check the flash messages at the top of the page for specific error details
2. Ensure values match the expected format (numbers for numeric fields, etc.)
3. For API integration issues, verify that your credentials are correct
4. Restart the application after changing critical settings 