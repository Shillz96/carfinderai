# Technical Design Document

## 1. Architecture

(As previously outlined)

```mermaid
graph LR
    A[Listing Websites <br/> (Craigslist, FB)] --> B(Web Scraping Agent <br/> Python);
    B --> C{Data Processing & <br/> Storage <br/> Google Sheets};
    C --> D(Thryv Integration <br/> API or Zapier);
    D --> E[Thryv CRM];
    C --> F(Notification System <br/> Email & Twilio);
    F --> G[Client Email & SMS];
    C --> H(Messaging System <br/> Twilio);
    H --> I[Seller SMS via Twilio];
    C --> J(Private Web Interface <br/> Python/Framework);
    J --> K[Client Access];
```

## 2. Technology Stack

*   **Programming Language:** Python (v3.9+)
*   **Web Scraping Libraries:**
    *   `Requests`: For making HTTP requests to websites.
    *   `Beautiful Soup 4`: For parsing HTML and XML content.
    *   *(Consideration: `Selenium` if Facebook Marketplace proves too difficult for static scraping, for browser automation).*
*   **SMS Communication:** Twilio API
    *   Python Twilio Helper Library.
*   **Email Communication:**
    *   Python `smtplib` and `email.mime` modules for standard library solution.
    *   *(Alternative: Email service API like SendGrid or Mailgun if advanced features or deliverability become a concern).*
*   **Data Storage:** Google Sheets API
    *   Python Google Client Library (`google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`).
*   **CRM Integration:**
    *   Thryv API (primary goal, requires investigation of its capabilities and Python client availability).
    *   Zapier (fallback if direct Thryv API integration is overly complex or not feasible).
*   **Web Framework (for UI):** Flask (lightweight, suitable for a simple private interface).
    *   HTML, CSS, JavaScript for the front-end.
*   **Task Scheduling:**
    *   `APScheduler` library within the Python application for periodic scraping tasks.
    *   *(Alternative: OS-level cron jobs if the agent is deployed as a script on a server).*
*   **Deployment:** Cloud hosting platform (e.g., Heroku, AWS Elastic Beanstalk, Vercel for Python/Flask).
*   **Configuration Management:** Environment variables or a configuration file (e.g., `config.ini` or `.env`) for API keys, credentials, and settings.

## 3. Module Breakdown

### 3.1. Scrapers

*   **Craigslist Scraper (`craigslist_scraper.py`):**
    *   Inputs: List of Hawaii Craigslist region URLs, target year (2018+).
    *   Functionality:
        1.  Iterate through specified Craigslist regions/subcategories for cars and trucks.
        2.  Fetch listing pages.
        3.  Parse HTML to extract:
            *   Listing Title
            *   Price
            *   Year, Make, Model (requires careful parsing, may involve pattern matching)
            *   Location (if available and distinct)
            *   Date Posted
            *   Listing URL
            *   Seller Contact Information (phone number if listed directly, or link to contact form if applicable - note: direct phone numbers are rare on CL now).
            *   Vehicle Description
        4.  Filter listings by year (>= 2018).
        5.  Handle pagination to get multiple pages of results.
        6.  Implement error handling for network issues, changes in website structure.
        7.  Incorporate politeness mechanisms (delays, user-agent rotation if needed).
    *   Output: List of dictionaries, each representing a scraped vehicle lead.

*   **Facebook Marketplace Scraper (`facebook_scraper.py`):**
    *   Inputs: List of Hawaii Facebook Marketplace group URLs/search queries, target year (2018+).
    *   Functionality:
        1.  *(Challenge: FB Marketplace is dynamic and may require login. Initial approach will attempt direct requests, but `Selenium` might be necessary).*
        2.  Navigate to specified FB Marketplace groups or search results.
        3.  Scroll/interact to load more listings (if using `Selenium`).
        4.  Parse HTML/dynamic content to extract similar data points as Craigslist scraper.
        5.  Filter listings by year.
        6.  Handle complex HTML structure and potential A/B testing by Facebook.
        7.  Error handling and politeness.
    *   Output: List of dictionaries, each representing a scraped vehicle lead.

### 3.2. Data Manager (`data_manager.py`)

*   Inputs: Scraped lead data (list of dictionaries).
*   Functionality:
    1.  **Data Cleaning & Standardization:**
        *   Normalize data formats (e.g., consistent date format, price to numeric).
        *   Attempt to further parse Make/Model/Year from title/description if not directly available.
        *   Handle missing values gracefully.
    2.  **Duplicate Detection:**
        *   Check against recently added leads in Google Sheets to avoid duplicates (based on Listing URL or a combination of key fields).
    3.  **Google Sheets Integration:**
        *   Authenticate with Google Sheets API.
        *   Append new, unique leads to the designated Google Sheet.
        *   Update existing leads if necessary (e.g., status change - though not initially planned).
        *   Read from Google Sheets (e.g., for duplicate checking or UI display).
*   Output: Confirmation of data storage, potentially returning the processed lead data.

### 3.3. Messaging Manager (`messaging_manager.py`)

*   Inputs: Lead data (specifically seller contact info, vehicle details).
*   Functionality:
    1.  **Twilio API Integration:**
        *   Initialize Twilio client with credentials.
    2.  **SMS Composition:**
        *   Format the standard SMS message (e.g., "Hi, I saw your listing for the [Year] [Make] [Model]. Is it still available?").
    3.  **SMS Sending:**
        *   Send SMS to the seller's phone number (if available and valid).
        *   Handle errors from Twilio API (e.g., invalid number, sending failure).
    4.  **Logging:** Log SMS sending attempts and outcomes.
*   Output: Status of SMS sending (success/failure, message SID).

### 3.4. Notification Manager (`notification_manager.py`)

*   Inputs: New lead data, status of seller SMS.
*   Functionality:
    1.  **Client Notification Composition (Email & SMS):**
        *   Format email content: Subject (e.g., "New Car Lead: [Year] [Make] [Model]"), Body (lead details, link to listing, seller contact, status of initial seller SMS).
        *   Format SMS content for client (concise notification).
    2.  **Email Sending:**
        *   Use `smtplib` or email service API to send email to the client.
    3.  **Client SMS Sending (via Twilio):**
        *   Send SMS notification to the client's phone number.
    4.  **Error Handling:** Manage failures in sending notifications.
*   Output: Status of client notifications.

### 3.5. Thryv Integrator (`thryv_integrator.py`)

*   Inputs: Lead data.
*   Functionality:
    1.  **Thryv API Investigation:**
        *   Research Thryv API documentation for lead creation/management endpoints.
        *   Determine authentication methods.
    2.  **API Client Implementation (if direct API):**
        *   Develop functions to map lead data to Thryv's expected format.
        *   Make API calls to create/update leads in Thryv.
        *   Handle API responses and errors.
    3.  **Zapier Setup (if fallback):**
        *   If direct API is not feasible, configure a Zap: Google Sheets (new row) -> Thryv (create lead). This module would then primarily ensure data is correctly formatted in Google Sheets for Zapier.
*   Output: Status of Thryv integration.

### 3.5.1. Configuration Manager (`managers/config_manager.py`)
*   Inputs: None directly for getting all settings; dictionary of settings for updates.
*   Functionality:
    1.  **Defines Configurable Settings:** Maintains a dictionary (`CONFIGURABLE_SETTINGS`) of environment variables that can be managed via the UI, including their descriptions, types (string, int, bool, select), and sensitivity.
    2.  **.env File Interaction:** Uses `python-dotenv` to read from and write to the `.env` file.
    3.  **Get Settings:** Provides a function (`get_all_configurable_settings_with_values`) to retrieve all defined configurable settings along with their current values (masking sensitive ones) and metadata for UI display.
    4.  **Update Settings:** Provides a function (`update_multiple_config_values`) to validate and save multiple settings back to the `.env` file.
    5.  **Value Validation:** Includes basic validation for setting types (int, float, bool, select options).
*   Output: For retrieval, a dictionary of settings with their values and metadata. For updates, a dictionary of results indicating success/failure for each setting. 

### 3.6. Web Interface (`app.py` using Flask)

*   Functionality:
    1.  **Authentication:** Basic authentication for client access (e.g., password protected).
    2.  **Lead Display:**
        *   Fetch lead data from Google Sheets (via Data Manager).
        *   Display leads in a sortable, filterable table or list.
        *   Show key details: Date, Vehicle Info, Seller Contact, Listing Link, Status (e.g., "Messaged Seller", "Client Notified").
    3.  **Settings Management (Interactive):**
        *   Allow client to view and edit a defined set of application environment variables (API keys, operational parameters) through a dedicated `/env-settings` page.
        *   Interface with `managers/config_manager.py` to load and save these settings.
    4.  **Documentation Access:**
        *   Links to project documentation (e.g., this TDD, User Guide).
    5.  **Manual Actions (Potential Future Enhancement):**
        *   Manually trigger a scrape.
        *   Mark leads as "Contacted" or "Closed".
*   Output: Serves HTML pages to the client's browser.

### 3.7. Main Orchestrator (`main.py` or `scheduler.py`)

*   Functionality:
    1.  **Initialization:** Load configuration, set up logging.
    2.  **Scheduling:** Implement a schedule for running the scraping and processing pipeline (e.g., every X hours using APScheduler).
    3.  **Workflow Control:**
        *   Call Craigslist Scraper.
        *   Call Facebook Scraper.
        *   Combine and pass data to Data Manager.
        *   For each new lead:
            *   Call Messaging Manager (if seller contact available).
            *   Call Notification Manager.
            *   Call Thryv Integrator.
    4.  **Error Handling & Logging:** Global error handling and comprehensive logging of the agent's operations.

## 4. Data Schema (for Google Sheet)

A single sheet named "Leads" with the following columns:

*   `Lead ID` (Primary Key, e.g., generated UUID or combination of source+listing_id)
*   `Date Scraped` (YYYY-MM-DD HH:MM:SS)
*   `Source` (e.g., "Craigslist", "Facebook Marketplace")
*   `Listing URL` (Direct link to the ad)
*   `Vehicle Year` (Integer, e.g., 2019)
*   `Vehicle Make` (Text)
*   `Vehicle Model` (Text)
*   `Vehicle Price` (Numeric, or Text if price contains "obo" etc.)
*   `Seller Name` (Text, if available)
*   `Seller Phone` (Text, if available and extracted)
*   `Seller Email` (Text, if available and extracted)
*   `Initial Seller SMS Sent` (Boolean: TRUE/FALSE)
*   `Seller SMS SID` (Text, from Twilio)
*   `Seller SMS Status` (e.g., "sent", "failed", "delivered" - if tracking enabled)
*   `Client Notified Email` (Boolean: TRUE/FALSE)
*   `Client Notified SMS` (Boolean: TRUE/FALSE)
*   `Thryv Status` (e.g., "Pending", "Sent to Thryv", "Error")
*   `Thryv Lead ID` (Text, if successfully created in Thryv)
*   `Notes` (Text, for any manual notes or errors specific to this lead)
*   `Listing Description` (Text, full or snippet of the ad description)
*   `Location` (Text, if available)
*   `Date Posted` (Text or Date, from listing)

## 5. Web Interface UI/UX Design (Conceptual)

The private web interface will be simple, functional, and provide the client with essential information and controls.

### 5.1. Core Pages & Functionality

*   **Login Page:**
    *   Simple username/password form for client access.

*   **Dashboard / Leads View (Default Page after Login):**
    *   **Layout:** Clean, tabular display of leads.
    *   **Information per Lead (Columns):**
        *   `Date Scraped`
        *   `Source` (Craigslist/FB)
        *   `Vehicle` (e.g., "2019 Honda Civic")
        *   `Price`
        *   `Listing Link` (clickable)
        *   `Seller Contact` (Phone, if available)
        *   `Initial SMS Sent?` (Yes/No/Pending)
        *   `Client Notified?` (Yes/No)
        *   `Thryv Status`
        *   *(Potentially a "Details" button to see more info like full description)*
    *   **Controls:**
        *   **Search/Filter:** By keyword (e.g., make, model), date range, source.
        *   **Sort:** By any column (Date Scraped, Price, etc.).
        *   **Pagination:** If many leads exist.
        *   *(Potential Action Buttons: "Mark as Contacted by Client" - future enhancement)*

*   **Settings Page (`/env-settings`):**
    *   **Functionality:** Provides a form for viewing and editing all environment variables defined in `managers.config_manager.CONFIGURABLE_SETTINGS`.
    *   **Display:** Shows current values (sensitive ones masked), descriptions, and appropriate input fields (text, number, select, boolean) for each setting.
    *   **Interaction:** Allows users to modify values and submit changes, which are then saved to the `.env` file.

*   **General Settings Information Page (`/settings` - distinct from `/env-settings`):
    *   **Display (Read-only sections combined with links):**
        *   Links to the interactive "Manage Environment Variables" page (`/env-settings`).
        *   Display other UI-specific settings (e.g., CRM toggle) or status information (e.g., Google OAuth connection status).
*   **Documentation Page:**
    *   Links to key project documents (Project Specification, this TDD, User Guide).
    *   Contact information for support/questions.

*   **Status/Log Overview (Optional - more technical):**
    *   A brief overview of the last run:
        *   Timestamp of last scrape.
        *   Number of new leads found.
        *   Number of errors (if any).
    *   Link to more detailed logs (if stored and accessible).

### 5.2. Look and Feel

*   **Theme:** Professional, clean, and uncluttered.
*   **Branding:** Minimal, perhaps client's logo if provided.
*   **Responsive:** Usable on desktop and tablet devices.

## 6. Deployment Considerations

*   **Environment Configuration:** Securely manage API keys (Twilio, Google, Thryv, Email) using environment variables or a `.env` file not committed to version control. The web interface provides a way to manage many of these settings once the application is running with an initial `.env` configuration.
*   **Database/Storage:** Google Sheets is the primary data store. Ensure appropriate sharing and permissions.
*   **Scheduler:**
    *   If using `APScheduler`, the Python application needs to be continuously running.
    *   If using `cron`, the deployment environment needs to support cron jobs.
*   **Logging:** Implement robust logging to files or a cloud logging service (e.g., Papertrail, AWS CloudWatch Logs) for monitoring and troubleshooting.
*   **Error Notifications:** Set up alerts for critical failures in the agent's operation (e.g., email to admin if scraping fails multiple times).
*   **Resource Requirements:** Estimate CPU/memory needs, especially if `Selenium` is used.

## 7. Security Considerations

*   **Web Interface Access:** Secure login mechanism (HTTPS, strong password policy).
*   **API Keys:** Store and handle API keys securely. Do not hardcode them in the source code.
*   **Data Privacy:** Be mindful of any PII (Personally Identifiable Information) scraped and ensure it's handled according to privacy best practices and client requirements.
*   **Input Validation:** Validate any inputs if the web interface allows for configuration changes.
*   **Polite Scraping:** Adhere to `robots.txt` (where applicable, though less common for these sites), implement delays, and manage user agents to avoid being blocked.