# Testing Plan

This document outlines the strategy, types, and scope of testing for the "Used Car Lead Generation Agent for Hawaii" project.

## 1. Testing Objectives
*   Verify that all functional requirements outlined in `Project Specification.md` are met.
*   Ensure the system is robust, handles errors gracefully, and performs reliably.
*   Validate data integrity throughout the workflow (scraping -> storage -> CRM -> notifications).
*   Confirm the usability and functionality of the private web interface for the client.
*   Identify and rectify defects early in the development lifecycle.

## 2. Testing Levels & Scope

### 2.1. Unit Testing
*   **Objective:** Test individual modules and functions in isolation to verify they work correctly according to their specifications.
*   **Scope & Examples:**
    *   **Scrapers (`craigslist_scraper.py`, `facebook_scraper.py`):**
        *   `T1.1:` Test HTML fetching function (e.g., `fetch_listing_page`) with valid URLs, invalid URLs, and simulated network errors.
        *   `T1.2:` Test parsing logic (e.g., `parse_listings`) with sample saved HTML files representing various listing formats (including edge cases like missing fields, unusual formatting).
        *   `T1.3:` Test specific data extraction functions (e.g., year, price, contact info parsing, year filtering).
        *   `T1.4:` Test pagination logic (can be mocked if direct testing is hard).
        *   `T1.5 (FB/Selenium):` Test browser navigation, element interaction, and dynamic content handling if Selenium is used.
        *   `T1.6 (FB):` Test parsing of FB-specific listing details.
    *   **Messaging Manager (`messaging_manager.py`):**
        *   `T2.1:` Test `send_sms` function, potentially mocking the Twilio API to verify correct API calls and parameter formatting without sending actual SMS during most tests. Test with valid/invalid phone numbers.
    *   **Notification Manager (`notification_manager.py`):**
        *   `T2.2:` Test email composition and sending (mock `smtplib` or email service).
        *   `T2.3:` Test client SMS composition and sending (can use `messaging_manager` mock or Twilio mock).
    *   **Data Manager (`data_manager.py`):**
        *   `T3.1:` Test Google Sheets authentication.
        *   `T3.2:` Test `append_leads_to_sheet` with various lead data structures (correct, missing fields) against a test Google Sheet.
        *   `T3.3:` Test data cleaning functions (e.g., price normalization, date formatting).
        *   `T3.4:` Test duplicate detection logic with pre-populated test data in a sheet.
    *   **Thryv Integrator (`thryv_integrator.py`):**
        *   `T5.1:` Test data mapping function from internal lead format to Thryv API format.
        *   `T5.2:` Test Thryv API call functions (e.g., `create_thryv_lead`), mocking the Thryv API to check request formation and response handling.
*   **Tools:** Python's `unittest` or `pytest` framework.
*   **Responsibility:** AI Assistant (with USER oversight).

### 2.2. Integration Testing
*   **Objective:** Test the interactions and data flow between different integrated modules.
*   **Scope & Examples:**
    *   `T4.1:` **Scraper to Google Sheets:**
        *   Test the flow: `craigslist_scraper` -> `data_manager` -> Google Sheets.
        *   Test the flow: `facebook_scraper` -> `data_manager` -> Google Sheets.
        *   Verify correct data structure, duplicate handling, and error logging.
    *   `T4.2:` **Lead Processing and Client Notification:**
        *   Test the flow: New lead in `data_manager` -> `messaging_manager` (attempt seller SMS) -> `notification_manager` (client email & SMS).
        *   Verify correct template usage and information propagation.
    *   `T4.3:` **Lead Processing to Thryv CRM:**
        *   Test the flow: New lead in `data_manager` -> `thryv_integrator` -> Thryv CRM (or Zapier trigger).
        *   Verify data mapping and successful lead creation in a test Thryv environment or by checking Zapier logs.
        *   Verify Google Sheet update with Thryv status.
    *   `T4.4:` **Web Interface to Data Manager:**
        *   Test: Flask app routes in `web_interface/app.py` correctly call `data_manager` to fetch leads for display.
*   **Tools:** `pytest` or manual execution of combined module workflows with specific test data.
*   **Responsibility:** AI Assistant (with USER oversight).

### 2.3. System Testing
*   **Objective:** Test the entire agent as a whole, end-to-end, in an environment that mimics production as closely as possible.
*   **Scope & Examples:**
    *   `T7.1:` **Full End-to-End Workflow:**
        *   Execute the main orchestrator (`main_agent.py`).
        *   Simulate real-world usage: Scrape actual (but limited and controlled) listings from Craigslist and Facebook Marketplace.
        *   Verify leads are processed: Seller SMS sent/attempted, client notifications sent, Thryv updated, Google Sheet populated correctly.
        *   Verify all success criteria from `Project Specification.md` (SC1-SC7).
    *   `T7.2:` **Error Handling & Resilience:**
        *   Simulate error conditions: Target website down, API key invalid, Thryv API unresponsive, incorrect data format in a listing.
        *   Verify the system handles these errors gracefully, logs them appropriately, and recovers if possible (e.g., retries).
    *   `T7.3:` **Scheduler Functionality:**
        *   Verify `APScheduler` triggers the main workflow at the configured intervals.
    *   `T6.1, T6.2:` **Web Interface Functionality (as part of system):**
        *   Test all features of the private web interface: login, lead display, sorting, filtering, access to settings/documentation pages.
*   **Tools:** Manual execution, review of logs, Google Sheets, Thryv (test instance), email/SMS clients.
*   **Responsibility:** AI Assistant for initial runs, USER for validation.

### 2.4. User Acceptance Testing (UAT)
*   **Objective:** Provide the client (USER) with access to the deployed agent to test and confirm it meets their specific needs and expectations.
*   **Scope & Examples:**
    *   Client independently uses the web interface to view leads.
    *   Client verifies the accuracy and timeliness of notifications (email, SMS).
    *   Client confirms leads appear correctly in their Thryv CRM.
    *   Client checks data in Google Sheets for accuracy and completeness.
    *   Client provides feedback on usability, functionality, and any discrepancies from `Project Specification.md`.
*   **Environment:** Deployed production or staging environment.
*   **Documentation:** Provide clear instructions, `User Guide.md`, and access to relevant project documents.
*   **Responsibility:** USER (Client: wealthymindshi).

## 3. Testing Environment
*   **Development & Unit/Integration Testing:** Local developer machine with mocked external services where appropriate.
*   **System Testing:** A dedicated testing environment that closely mirrors production if possible. Otherwise, local machine with live (but controlled) API calls to test instances of services (e.g., test Twilio numbers, test email accounts, test Google Sheet, test Thryv instance if available).
*   **UAT:** Deployed production environment (or a staging environment if one is used prior to full production).
*   **Test Data:**
    *   Use a mix of valid, invalid, edge-case, and high-volume data (where appropriate).
    *   Sample HTML files for scraper unit tests.
    *   Pre-populated Google Sheets for testing duplicate handling and data manager reads.
    *   Use test accounts/numbers for Twilio, email to avoid impacting real data or contacts during development.

## 4. Testing Metrics
*   **Defect Density:** Number of defects found per phase or module.
*   **Test Case Coverage:** Percentage of requirements or code paths covered by test cases (can be informal for this project, but aim for good coverage of critical paths).
*   **Pass/Fail Rate:** Number of successful vs. failed test cases.
*   **System Response Time:** (Informal) Ensure the agent processes leads and the web UI loads within acceptable timeframes.
*   **Data Accuracy:** Percentage of leads processed with 100% accurate data transfer through the system.
*   **UAT Feedback:** Number of issues raised, successful scenarios confirmed by the client.

## 5. Defect Management
*   **Tracking:** For this project, defects can be tracked via this chat interface or a simple list within a project document if preferred by the USER.
*   **Prioritization:** Defects will be prioritized based on severity (Critical, High, Medium, Low) and impact on core functionality.
*   **Resolution:** AI Assistant will address defects, re-test, and USER will verify fixes.

This Testing Plan will be referred to throughout the development lifecycle as outlined in the `Master Development Guide.md`. 