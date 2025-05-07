# Master Development Guide: Used Car Lead Generation Agent

## 0. Introduction

This guide provides a comprehensive step-by-step plan for developing the "Used Car Lead Generation Agent for Hawaii." It integrates information from the `Project Specification.md`, `Technical Design Document.md`, `Development Plan & Timeline.md`, `Testing Plan.md`, and `Risk Assessment.md`.

**Key Objectives:**
*   Scrape Craigslist and Facebook Marketplace for used cars (2018+).
*   Send SMS to sellers.
*   Notify client via Email/SMS.
*   Integrate with Thryv CRM.
*   Store leads in Google Sheets.
*   Provide a private web UI for the client.

**Before You Begin:**
*   Ensure all API keys and credentials (Twilio, Google Cloud Platform for Sheets, Email service, Thryv) are ready or accounts are set up.
*   Familiarize yourself with the overall architecture in `Technical Design Document.md`.
*   Keep the `Risk Assessment.md` handy to be mindful of potential challenges.

## Phase 1: Foundation & Core Craigslist Scraper (Estimated: 3-4 days)

### Day 1: Environment & Basic Structure

*   **Objective:** Set up the development environment and project skeleton.
*   **Tasks:**
    1.  [ ] **Setup Python Virtual Environment:**
        *   Command: `python -m venv venv`
        *   Activate: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows).
    2.  [ ] **Initialize Git Repository:**
        *   Command: `git init`
        *   Create a `.gitignore` file (e.g., for `venv/`, `__pycache__/`, `.env`, `credentials.json`).
    3.  [ ] **Create Project Structure:**
        *   Directories: `scrapers/`, `managers/`, `utils/`, `tests/`, `web_interface/`, `docs/` (can copy existing MD files here).
        *   Refer to `Technical Design Document.md` for module names.
    4.  [ ] **Install Core Libraries:**
        *   Command: `pip install requests beautifulsoup4 python-dotenv APScheduler`
        *   Create `requirements.txt`: `pip freeze > requirements.txt`.
    5.  [ ] **Basic Logging Setup:**
        *   Create `utils/logger.py` to configure a project-wide logger (e.g., logging to console and a file).
    6.  [ ] **Configuration File Setup:**
        *   Create a `.env` file in the root directory.
        *   Add placeholders for API keys, Craigslist URLs, client contact info, etc. Example:
            ```
            TWILIO_ACCOUNT_SID="your_twilio_sid"
            TWILIO_AUTH_TOKEN="your_twilio_auth_token"
            TWILIO_PHONE_NUMBER="your_twilio_phone_number"
            # ... other config ...
            ```
        *   Ensure `.env` is in `.gitignore`.
*   **Testing:**
    *   Verify virtual environment activation.
    *   Confirm initial libraries install.
    *   Test basic logging.
*   **Definition of Done:** Basic project structure, environment, logging, and configuration are in place.

### Day 2: Craigslist Scraper - Initial Pass

*   **Objective:** Develop the initial version of the Craigslist scraper.
*   **Tasks:**
    1.  [ ] **Develop `scrapers/craigslist_scraper.py`:**
        *   Import `requests`, `BeautifulSoup`, logger.
        *   Function to load target Craigslist URLs from config.
    2.  [ ] **Implement Fetching Logic:**
        *   Function `fetch_listing_page(url)`: Makes HTTP GET request, handles basic errors (timeouts, status codes).
    3.  [ ] **Implement Basic Parsing:**
        *   Function `parse_listings(html_content)`: Uses BeautifulSoup to find main listing elements.
        *   Extract initial data points: Listing Title, Price, Listing URL.
        *   (Risk T001, T003): Be mindful of CL's structure; it can change. Start with robust selectors if possible.
    4.  [ ] **Test Scraper:**
        *   Create a `main.py` (temporary) or a test script in `tests/` to run the scraper for a single Hawaii Craigslist region/category.
        *   Print extracted data to console.
*   **Testing:**
    *   `Unit Test (T1.1)`: Test `fetch_listing_page` with valid and invalid URLs.
    *   `Unit Test (T1.2)`: Test `parse_listings` with sample saved HTML from Craigslist.
    *   Verify basic data extraction for a few listings.
*   **Definition of Done:** Scraper can fetch and parse basic information from one Craigslist category page.

### Day 3: Craigslist Scraper - Refinement & Data Extraction

*   **Objective:** Enhance the Craigslist scraper for more detailed data and robustness.
*   **Tasks:**
    1.  [ ] **Refine Parsing in `scrapers/craigslist_scraper.py`:**
        *   Extract additional fields: Year, Make, Model (requires careful string parsing/regex from title/description), Vehicle Description, Date Posted.
        *   (Project Spec 4.2): Implement filtering for vehicles year 2018+.
    2.  [ ] **Handle Pagination:**
        *   Logic to find "next page" links and iterate through them.
    3.  [ ] **Error Handling:**
        *   Improve error handling in fetching and parsing (e.g., what if an element is missing?).
        *   Log errors comprehensively.
*   **Testing:**
    *   `Unit Test (T1.3)`: Test year extraction and filtering.
    *   `Unit Test (T1.4)`: Test pagination logic (mocking if necessary).
    *   Run scraper across multiple pages and verify data variety and accuracy.
*   **Definition of Done:** Craigslist scraper can get multiple pages, extract detailed fields, and filter by year.

### Day 4: Initial Seller Contact (Twilio Setup & Basic Messaging)

*   **Objective:** Set up Twilio and implement basic SMS sending functionality.
*   **Tasks:**
    1.  [ ] **Twilio Account & Credentials:**
        *   Ensure Twilio account is active and `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` are in `.env`.
    2.  [ ] **Install Twilio Library:** `pip install twilio`. Add to `requirements.txt`.
    3.  [ ] **Develop `managers/messaging_manager.py`:**
        *   Initialize Twilio client using credentials from `.env`.
        *   Function `send_sms(to_number, message_body)`:
            *   (Project Spec 4.3): Use the standard message template: "Hi, I saw your listing for the [Year] [Make] [Model]. Is it still available?".
            *   Sends SMS using Twilio API.
            *   Log success/failure and Twilio Message SID.
    4.  [ ] **Integrate with Scraper (Conceptual):**
        *   Modify `craigslist_scraper.py` to attempt to find phone numbers (note: Craigslist often hides these. This step is more about setting up the messaging manager for when numbers *are* found, e.g. from Facebook). For now, can test `send_sms` with your own phone number.
*   **Testing:**
    *   `Unit Test (T2.1)`: Test `send_sms` function (can mock Twilio API or send actual test SMS).
    *   Verify SMS is received and content is correct.
*   **Definition of Done:** `messaging_manager.py` can send a templated SMS via Twilio.

## Phase 2: Data Storage & Client Notifications (Estimated: 2-3 days)

### Day 5: Google Sheets Integration

*   **Objective:** Store scraped leads into Google Sheets.
*   **Tasks:**
    1.  [ ] **Google Cloud Project & Sheets API Setup:**
        *   Create a GCP project. Enable Google Sheets API.
        *   Create service account credentials (`credentials.json`). Store securely and add to `.gitignore`.
        *   Share the target Google Sheet with the service account's email address.
    2.  [ ] **Install Google API Libraries:** `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`. Add to `requirements.txt`.
    3.  [ ] **Develop `managers/data_manager.py`:**
        *   Implement Google Sheets authentication using `credentials.json`.
        *   Function `get_sheet_service()` to initialize the Sheets service.
        *   Function `append_leads_to_sheet(leads_data)`:
            *   Takes a list of lead dictionaries.
            *   Appends them as new rows to the specified Google Sheet.
            *   (TDD 4. Data Schema): Ensure columns match the defined schema.
    4.  [ ] **Integrate with Craigslist Scraper:**
        *   Modify main workflow to pass scraped leads from `craigslist_scraper.py` to `data_manager.py` to be saved.
*   **Testing:**
    *   `Unit Test (T3.1)`: Test Google Sheets authentication.
    *   `Unit Test (T3.2)`: Test `append_leads_to_sheet` (can use a test sheet).
    *   `Integration Test (T4.1)`: Run Craigslist scraper and verify leads appear correctly in Google Sheets.
*   **Definition of Done:** Scraped leads from Craigslist are successfully stored in Google Sheets according to the schema.

### Day 6: Client Email & SMS Notifications

*   **Objective:** Notify the client about new leads via email and SMS.
*   **Tasks:**
    1.  [ ] **Develop `managers/notification_manager.py`:**
        *   Function `send_email_notification(client_email, subject, body)`:
            *   Use `smtplib` (and `email.mime`) or a chosen email API (e.g., SendGrid). Configure credentials in `.env`.
        *   Function `send_sms_notification_to_client(client_phone, message_body)`:
            *   Utilize `messaging_manager.send_sms` or a direct Twilio call if preferred for client SMS.
    2.  [ ] **Compose Notification Templates (Project Spec 4.4):**
        *   Email: Subject ("New Car Lead: [Year] [Make] [Model]"), Body (lead details, listing link, seller contact, status of initial seller SMS).
        *   Client SMS: Concise message about the new lead.
    3.  [ ] **Integrate into Workflow:**
        *   After a lead is saved by `data_manager.py` and seller SMS is attempted by `messaging_manager.py`, trigger `notification_manager.py` to inform the client.
        *   Load client contact details from `.env`.
*   **Testing:**
    *   `Unit Test (T2.2)`: Test email sending function.
    *   `Unit Test (T2.3)`: Test client SMS sending function.
    *   `Integration Test (T4.2)`: Full flow: scrape -> save to Sheets -> attempt seller SMS -> send client email & SMS. Verify content.
*   **Definition of Done:** Client receives email and SMS notifications for new leads.

### Day 7: Data Cleaning & Duplicate Handling

*   **Objective:** Improve data quality and prevent duplicate entries.
*   **Tasks:**
    1.  [ ] **Data Cleaning in `managers/data_manager.py`:**
        *   Add functions to clean/normalize data before saving (e.g., convert price to number, standardize date formats).
    2.  [ ] **Duplicate Detection in `managers/data_manager.py`:**
        *   Before appending new leads, implement `check_for_duplicates(leads_data, sheet_service)`:
            *   Read existing Listing URLs (or other unique identifiers) from Google Sheets.
            *   Filter out leads that already exist.
            *   (Risk T003): This helps manage inconsistent data if a slightly modified ad is re-scraped.
*   **Testing:**
    *   `Unit Test (T3.3)`: Test data cleaning functions.
    *   `Unit Test (T3.4)`: Test duplicate detection logic (with test data in a sheet).
    *   Run scraper multiple times and verify duplicates are not added.
*   **Definition of Done:** Data is cleaned, and duplicate leads are not re-added to Google Sheets.

## Phase 3: Facebook Marketplace Scraper (Estimated: 2-4 days - *High Variability*)

*(Risk T005: FB Marketplace scraping is complex. Be prepared for challenges and potential need for Selenium.)*

### Day 8: Facebook Scraper - Initial Investigation & Attempt

*   **Objective:** Begin development of the Facebook Marketplace scraper.
*   **Tasks:**
    1.  [ ] **Develop `scrapers/facebook_scraper.py`:** Basic structure.
    2.  [ ] **Research FB Marketplace:**
        *   Manually inspect HTML structure, network requests (using browser dev tools) for Hawaii listings.
        *   Identify how listings are loaded (dynamic, infinite scroll).
    3.  [ ] **Attempt Static Scraping:**
        *   Try using `requests` and `BeautifulSoup` to fetch and parse. This may have limited success.
        *   Focus on extracting basic info first.
*   **Testing:**
    *   Manual inspection of fetched content.
    *   Small-scale tests, print output to console.
*   **Definition of Done:** Initial assessment of FB scraping feasibility with static methods.

### Day 9-10: Facebook Scraper - Development / Selenium (if needed)

*   **Objective:** Implement a working Facebook scraper, potentially using Selenium.
*   **Tasks:**
    1.  [ ] **Setup Selenium (if static scraping failed):**
        *   `pip install selenium`. Add to `requirements.txt`.
        *   Download appropriate WebDriver (e.g., `chromedriver`) and ensure it's in PATH or configured.
    2.  [ ] **Implement Navigation & Interaction (Selenium):**
        *   Logic to open browser, navigate to FB Marketplace (search queries, group URLs from config).
        *   Handle login if absolutely necessary (use with caution, consider dedicated FB account).
        *   Implement scrolling to load dynamic content.
    3.  [ ] **Parse Listing Details:**
        *   Adapt parsing logic (similar to Craigslist) for FB's HTML structure. Extract same fields.
        *   (Project Spec 4.2): Implement year filtering (2018+).
    4.  [ ] **Error Handling & Politeness:**
        *   Implement robust error handling for dynamic content.
        *   Use appropriate delays to avoid aggressive scraping.
    5.  [ ] **Integrate with `data_manager.py`:** Pass scraped FB leads for storage.
*   **Testing:**
    *   `Unit Test (T1.5)`: Test Selenium navigation basics (if used).
    *   `Unit Test (T1.6)`: Test FB data parsing with sample HTML (static or Selenium-retrieved).
    *   `Integration Test (T4.1)`: Run FB scraper and verify leads save to Google Sheets (and duplicates are handled).
*   **Definition of Done:** Facebook scraper can extract and save leads to Google Sheets.

### Day 11 (Contingency): Facebook Scraper - Refinement & Error Handling

*   **Objective:** Improve robustness and address issues found in FB scraper.
*   **Tasks:**
    1.  [ ] **Address FB Specific Issues:** Handle login prompts more gracefully, adapt to minor structure changes identified during testing.
    2.  [ ] **Refine Politeness Mechanisms:** Adjust delays, potentially add user-agent rotation if signs of blocking appear.
*   **Testing:**
    *   Extended runs of the FB scraper to check for stability.
*   **Definition of Done:** Facebook scraper is more stable and handles common issues.

## Phase 4: Thryv CRM Integration (Estimated: 2-3 days)

*(Risk T004: Thryv API might have issues. Prioritize direct API, fallback to Zapier.)*

### Day 12: Thryv API Research & Initial Setup

*   **Objective:** Investigate Thryv API and set up basic integration.
*   **Tasks:**
    1.  [ ] **Thryv API Documentation Review:**
        *   Understand authentication methods, lead creation/management endpoints, rate limits.
        *   Store Thryv API key/credentials in `.env`.
    2.  [ ] **Develop `managers/thryv_integrator.py`:** Basic structure.
    3.  [ ] **API Authentication Test:**
        *   Implement Thryv API authentication.
        *   Make a simple test call (e.g., fetch account details, list existing test leads if possible).
*   **Testing:**
    *   Verify successful authentication with Thryv API.
*   **Definition of Done:** Basic authenticated communication with Thryv API is established.

### Day 13: Thryv Lead Creation

*   **Objective:** Implement functionality to create leads in Thryv.
*   **Tasks:**
    1.  [ ] **Map Lead Data to Thryv Format:**
        *   In `thryv_integrator.py`, create a function to transform a lead dictionary (from our Google Sheet schema) into the format expected by Thryv's "create lead" endpoint.
    2.  [ ] **Implement `create_thryv_lead(lead_data)` function:**
        *   Makes the API call to create a new lead in Thryv.
        *   Handles API responses (success, errors). Log Thryv Lead ID if successful.
    3.  [ ] **Integrate into Workflow:**
        *   After a lead is processed and client notified, call `create_thryv_lead`.
        *   Update Google Sheet with Thryv status ("Sent to Thryv", "Error", Thryv Lead ID).
*   **Testing:**
    *   `Unit Test (T5.1)`: Test data mapping function for Thryv.
    *   `Integration Test (T4.3)`: Create a test lead via the agent and verify it appears correctly in Thryv.
    *   Verify Google Sheet is updated with Thryv status.
*   **Definition of Done:** New leads are successfully created in Thryv CRM via API.

### Day 14 (Fallback/Refinement): Zapier Setup or API Refinement

*   **Objective:** Implement Zapier fallback if Thryv API is problematic, or refine API integration.
*   **Tasks:**
    1.  [ ] **If Thryv API is difficult/unreliable:**
        *   Set up a Zapier "Zap": New Row in Google Sheets -> Create Lead in Thryv.
        *   Test this Zap thoroughly.
        *   The `thryv_integrator.py` might then just become a logger for "to be processed by Zapier".
    2.  [ ] **If Thryv API is working:**
        *   Refine error handling based on testing.
        *   Improve logging for Thryv interactions.
*   **Testing:**
    *   Test Zapier integration end-to-end if used.
    *   Review logs for Thryv API interactions for clarity.
*   **Definition of Done:** Reliable mechanism (API or Zapier) for getting leads into Thryv is in place.

## Phase 5: Web Interface Development (Estimated: 3-4 days)

*(TDD 5. Web Interface UI/UX Design provides conceptual details.)*

### Day 15: Basic Flask App & Lead Display

*   **Objective:** Create a basic Flask web application to display leads.
*   **Tasks:**
    1.  [ ] **Setup Flask Application:**
        *   `pip install Flask`. Add to `requirements.txt`.
        *   Create `web_interface/app.py`.
        *   Basic Flask app structure with a route for displaying leads.
        *   Create `templates/` folder within `web_interface/`.
    2.  [ ] **HTML Template for Leads:**
        *   Create `web_interface/templates/leads.html`.
        *   Use HTML table to display lead data. Columns as per TDD 5.1.
    3.  [ ] **Fetch and Display Leads:**
        *   In `app.py`, create a route (`/leads` or `/`) that:
            *   Uses `data_manager.py` to fetch all leads from Google Sheets.
            *   Passes lead data to the `leads.html` template.
    4.  [ ] **Basic Styling:**
        *   Create `web_interface/static/css/style.css` for simple styling.
*   **Testing:**
    *   `System Test (T6.1)`: Launch Flask app and verify leads from Google Sheets are displayed correctly.
    *   Check basic layout and readability.
*   **Definition of Done:** A web page displays leads from Google Sheets.

### Day 16: Authentication & UI Enhancements

*   **Objective:** Add basic security and improve usability of the web interface.
*   **Tasks:**
    1.  [ ] **Implement Basic Authentication:**
        *   Use Flask-HTTPAuth or a simple hardcoded password check (for a private UI, ensure it's not committed in plain text if hardcoded - better to use environment variables for credentials).
        *   Protect all routes.
    2.  [ ] **Lead Table Enhancements (Client-Side or Server-Side):**
        *   Add sorting functionality to table columns (e.g., using JavaScript library like DataTables.js, or server-side).
        *   Add basic filtering/search box.
*   **Testing:**
    *   `System Test (T6.2)`: Verify authentication works.
    *   Test sorting and filtering on the leads page.
*   **Definition of Done:** Web interface is password-protected, and leads can be sorted/filtered.

### Day 17: Environment Settings Management & Documentation Pages

*   **Objective:** Implement a web page for managing configurable application environment variables and a page for accessing documentation.
*   **Tasks:**
    1.  [ ] **Develop Environment Settings Page (`web_interface/templates/env_settings.html`):**
        *   Create an HTML form that dynamically renders input fields (text, select, boolean) based on settings defined in `managers.config_manager.CONFIGURABLE_SETTINGS`.
        *   Display descriptions for each setting.
        *   Handle display of sensitive information (masking existing values).
    2.  [ ] **Implement Backend for Environment Settings in `web_interface/app.py`:**
        *   Create a route (e.g., `/env-settings`) supporting GET and POST requests.
        *   GET: Fetch settings using `managers.config_manager.get_all_configurable_settings_with_values()` and pass to the template.
        *   POST: Receive form data, use `managers.config_manager.update_multiple_config_values()` to update the `.env` file. Provide feedback to the user (flash messages).
    3.  [ ] **Documentation Page (`web_interface/templates/documentation.html`):**
        *   Create a simple HTML page.
        *   Add links to key project Markdown documents (e.g., User Guide, Project Spec, Technical Design Document, Environment Settings Guide).
        *   Create a route in `app.py` for `/documentation` to render this page.
*   **Testing:**
    *   Verify the `/env-settings` page displays all configurable settings correctly.
    *   Test updating various types of settings (string, integer, boolean, select, sensitive) and confirm changes are reflected in the `.env` file and on the page after refresh.
    *   Verify error handling for invalid inputs (if implemented in `config_manager`).
    *   Verify documentation page displays correctly and links work.
*   **Definition of Done:** Client can manage configurable environment variables via the web interface, and a documentation links page is available.

### Day 18 (Contingency): UI Polishing & Minor Features

*   **Objective:** Refine the UI and address any minor pending features.
*   **Tasks:**
    1.  [ ] **Improve UI/UX:** Based on initial review, make small improvements to layout, styling, and usability.
    2.  [ ] **Responsiveness:** Ensure basic responsiveness for desktop/tablet.
*   **Testing:**
    *   Review UI on different screen sizes (simulated).
*   **Definition of Done:** Web interface is polished and user-friendly.

## Phase 6: Orchestration, Testing & Deployment (Estimated: 2-3 days)

### Day 19: Main Orchestrator & Scheduling

*   **Objective:** Create the main script to run the entire agent workflow and schedule it.
*   **Tasks:**
    1.  [ ] **Develop `main_agent.py` (or rename existing `main.py`):**
        *   This script will orchestrate the entire process:
            *   Load configuration (from `.env`).
            *   Initialize all manager objects (`data_manager`, `messaging_manager`, `notification_manager`, `thryv_integrator`).
            *   Call Craigslist scraper, then Facebook scraper.
            *   Pass scraped data to `data_manager` (handles cleaning, duplicate check, saving to Sheets).
            *   For each new, unique lead:
                *   Call `messaging_manager` to attempt seller SMS.
                *   Call `notification_manager` to alert client.
                *   Call `thryv_integrator` to send to CRM.
        *   Implement comprehensive logging for the entire workflow.
    2.  [ ] **Integrate APScheduler:**
        *   Use `APScheduler` within `main_agent.py` to schedule the orchestration logic to run periodically (e.g., every 4 hours - configurable in `.env`).
*   **Testing:**
    *   `System Test (T7.1)`: Run `main_agent.py` manually and verify the full end-to-end workflow for a few test listings.
    *   Check logs for completeness and errors.
    *   Verify scheduler triggers the workflow as expected (can test with a short interval initially).
*   **Definition of Done:** `main_agent.py` orchestrates the full workflow, and it's scheduled for periodic execution.

### Day 20: Thorough Testing

*   **Objective:** Conduct comprehensive testing of all components and the system as a whole.
*   **Tasks:**
    1.  [ ] **Review and Augment Unit Tests (Testing Plan 1):**
        *   Ensure good coverage for critical functions in all modules (parsing, data transformation, API interactions).
    2.  [ ] **Execute Integration Tests (Testing Plan 2):**
        *   Test data flow between modules:
            *   Scrapers -> Data Manager
            *   Data Manager -> Google Sheets
            *   Data Manager -> Messaging Manager -> Seller SMS
            *   Data Manager -> Notification Manager -> Client Email/SMS
            *   Data Manager -> Thryv Integrator -> Thryv CRM
    3.  [ ] **Perform System Testing (Testing Plan 3):**
        *   Run the entire agent end-to-end using a mix of test data and limited live scrapes (if safe).
        *   Verify all success criteria from `Project Specification.md` (SC1-SC7).
        *   Check data consistency across Google Sheets, Thryv, and notifications.
        *   Test error handling: e.g., what happens if a website is down? If an API key is invalid?
    4.  [ ] **Web Interface Testing:** Thoroughly test all functionalities of the web UI (lead display, auth, sorting, filtering).
*   **Testing Metrics (Testing Plan 6):** Track number of passed/failed tests, identify defects.
*   **Definition of Done:** All planned tests executed, critical defects fixed, system meets requirements.

### Day 21: Deployment & Final Review

*   **Objective:** Deploy the application and prepare for client handoff.
*   **Tasks:**
    1.  [ ] **Choose and Setup Hosting Platform:** (e.g., Heroku, AWS Elastic Beanstalk, PythonAnywhere).
        *   Considerations: Python support, scheduling (for APScheduler or cron), environment variable management, logging.
    2.  [ ] **Prepare for Deployment:**
        *   Ensure `requirements.txt` is up-to-date.
        *   Create deployment scripts if needed (e.g., `Procfile` for Heroku).
    3.  [ ] **Deploy Application:** Follow platform-specific deployment instructions.
    4.  [ ] **Configure Environment Variables on Server:** Set all API keys, URLs, client contacts, etc., in the hosting environment. **DO NOT COMMIT `.env` or `credentials.json` to Git.**
    5.  [ ] **Final End-to-End Testing on Deployed Environment:**
        *   Run the agent on the server to ensure it works as expected in the production-like environment.
    6.  [ ] **Prepare User Documentation (Client-Facing):**
        *   Create a simple `User Guide.md` explaining:
            *   How to access and use the web interface.
            *   What the different statuses mean.
            *   How to interpret the data in Google Sheets.
            *   Basic troubleshooting or who to contact for issues.
    7.  [ ] **Code Cleanup & Final Commit:** Review code for clarity, remove unused test code, add final comments.
*   **UAT (User Acceptance Testing - Testing Plan 4):** Provide client access to the deployed agent and web UI for their review and approval.
*   **Definition of Done:** Application deployed and running, client has access and basic documentation, UAT initiated/completed.

## Post-Deployment
*   Monitor logs for errors.
*   Be prepared for maintenance (especially scraper adjustments due to website changes - Risk T001).

This Master Development Guide provides a detailed roadmap. Remember to commit your code frequently and communicate progress as per the `Communication Plan.md`. 