# Development Plan & Timeline (Estimate)

*This is an estimated timeline and may be adjusted based on development progress and complexities encountered. Each "day" assumes a focused development day.*

## Phase 1: Foundation & Core Craigslist Scraper (Estimated: 3-4 days)

*   **Day 1: Environment & Basic Structure**
    *   [ ] Setup Python virtual environment (`venv`).
    *   [ ] Initialize Git repository.
    *   [ ] Create project structure (folders for scrapers, managers, etc.).
    *   [ ] Install core libraries (`requests`, `beautifulsoup4`, `python-dotenv`).
    *   [ ] Basic logging setup (`logging` module).
    *   [ ] Configuration file setup (`.env` for API keys, URLs).
*   **Day 2: Craigslist Scraper - Initial Pass**
    *   [ ] Develop `craigslist_scraper.py` module.
    *   [ ] Implement function to fetch main listing page for a Craigslist region.
    *   [ ] Implement basic parsing for individual listing details (title, price, URL).
    *   [ ] Test with a single Hawaii Craigslist region.
*   **Day 3: Craigslist Scraper - Refinement & Data Extraction**
    *   [ ] Refine parsing to extract year, make, model, description, date posted.
    *   [ ] Implement year filtering (2018+).
    *   [ ] Handle pagination for Craigslist results.
    *   [ ] Basic error handling (network issues, minor HTML changes).
*   **Day 4: Initial Seller Contact (Twilio Setup & Basic Messaging)**
    *   [ ] Sign up for Twilio account (if not already done) and get credentials.
    *   [ ] Install Twilio Python library.
    *   [ ] Develop `messaging_manager.py` (basic structure).
    *   [ ] Implement function to send a hardcoded test SMS via Twilio.
    *   [ ] Integrate simple SMS sending for a scraped lead (if phone number is found - placeholder for now, as CL rarely shows phones directly).

## Phase 2: Data Storage & Client Notifications (Estimated: 2-3 days)

*   **Day 5: Google Sheets Integration**
    *   [ ] Set up Google Cloud Project, enable Sheets API, get credentials (`credentials.json`).
    *   [ ] Install Google API client libraries for Python.
    *   [ ] Develop `data_manager.py` (basic structure).
    *   [ ] Implement Google Sheets authentication.
    *   [ ] Implement function to append a list of dictionaries (leads) to a specified sheet.
    *   [ ] Define initial Google Sheet columns (as per Data Schema).
    *   [ ] Integrate `data_manager` to save Craigslist scraper output.
*   **Day 6: Client Email & SMS Notifications**
    *   [ ] Develop `notification_manager.py`.
    *   [ ] Implement email sending function using `smtplib` (or selected email API).
    *   [ ] Implement client SMS sending function using Twilio (via `messaging_manager` or direct call).
    *   [ ] Compose email and SMS notification templates for the client.
    *   [ ] Integrate to notify client after a lead is saved to Google Sheets.
*   **Day 7: Data Cleaning & Duplicate Handling**
    *   [ ] In `data_manager.py`, add functions for basic data cleaning (e.g., price normalization).
    *   [ ] Implement a basic duplicate check against Google Sheets (e.g., by listing URL) before adding new leads.

## Phase 3: Facebook Marketplace Scraper (Estimated: 2-4 days - *High Variability*)

*   **Day 8: Facebook Scraper - Initial Investigation & Attempt**
    *   [ ] Develop `facebook_scraper.py` module.
    *   [ ] Research Facebook Marketplace HTML structure and network requests for Hawaii.
    *   [ ] Attempt basic scraping using `requests` and `BeautifulSoup` (may not be fully effective).
*   **Day 9-10: Facebook Scraper - Development / Selenium (if needed)**
    *   [ ] If static scraping fails, set up `Selenium` and `WebDriver`.
    *   [ ] Implement logic to navigate FB Marketplace (search, group pages).
    *   [ ] Handle dynamic content loading (scrolling).
    *   [ ] Parse listing details (similar to Craigslist, but adapted for FB structure).
    *   [ ] Implement year filtering.
    *   [ ] Integrate output with `data_manager`.
*   **Day 11 (Contingency): Facebook Scraper - Refinement & Error Handling**
    *   [ ] Robust error handling for FB specific issues (login prompts, structure changes).
    *   [ ] Politeness mechanisms suitable for FB.

## Phase 4: Thryv CRM Integration (Estimated: 2-3 days)

*   **Day 12: Thryv API Research & Initial Setup**
    *   [ ] Investigate Thryv API documentation thoroughly (authentication, lead creation endpoints).
    *   [ ] Develop `thryv_integrator.py` module.
    *   [ ] Attempt basic API authentication and a test API call (e.g., list existing leads if possible).
*   **Day 13: Thryv Lead Creation**
    *   [ ] Implement function to map project's lead data to Thryv's lead object format.
    *   [ ] Implement function to create a new lead in Thryv via API.
    *   [ ] Error handling for API responses.
    *   [ ] Integrate with main workflow to send leads to Thryv.
*   **Day 14 (Fallback/Refinement): Zapier Setup or API Refinement**
    *   [ ] If direct Thryv API is problematic, set up and test a Zapier integration (Google Sheets new row -> Thryv lead).
    *   [ ] Refine direct API integration if successful (e.g., improve error logging).

## Phase 5: Web Interface Development (Estimated: 3-4 days)

*   **Day 15: Basic Flask App & Lead Display**
    *   [ ] Set up basic Flask application (`app.py`).
    *   [ ] Create HTML template for lead display (table format).
    *   [ ] Implement route to fetch leads from Google Sheets (via `data_manager`) and display them.
    *   [ ] Basic styling (simple CSS).
*   **Day 16: Authentication & UI Enhancements**
    *   [ ] Implement basic password protection for the web interface.
    *   [ ] Add sorting and basic filtering capabilities to the lead table (JavaScript or backend).
*   **Day 17: Environment Settings Management & Documentation Pages**
    *   [ ] Create `web_interface/templates/env_settings.html` for managing configurable environment variables.
    *   [ ] Implement Flask route in `app.py` (`/env-settings`) to:
        *   Fetch current settings using `managers.config_manager.get_all_configurable_settings_with_values`.
        *   Render `env_settings.html` with the settings.
        *   Handle POST requests to update settings using `managers.config_manager.update_multiple_config_values` and save to `.env` file.
    *   [ ] Create `web_interface/templates/documentation.html` and a route to display links to project documentation.
*   **Day 18 (Contingency): UI Polishing & Minor Features**
    *   [ ] Improve UI/UX based on initial review.
    *   [ ] Ensure responsiveness (basic).

## Phase 6: Orchestration, Testing & Deployment (Estimated: 2-3 days)

*   **Day 19: Main Orchestrator & Scheduling**
    *   [ ] Develop `main.py` (or `scheduler.py`) to orchestrate the entire workflow:
        *   Initialize all managers.
        *   Call scrapers.
        *   Process data through `data_manager`.
        *   Trigger messaging, notifications, and CRM integration for new leads.
    *   [ ] Integrate `APScheduler` for periodic execution of the workflow.
    *   [ ] Comprehensive logging throughout the orchestration process.
*   **Day 20: Thorough Testing**
    *   [ ] **Unit Tests:** Add more unit tests for critical functions in each module (especially parsing, data transformation).
    *   [ ] **Integration Tests:** Test flow between modules (scraper -> data_manager -> notification_manager, etc.).
    *   [ ] **System Testing:** Run the entire agent end-to-end with test data and live (limited) scrapes.
    *   [ ] Verify data in Google Sheets, Thryv (test instance if possible), and client notifications.
*   **Day 21: Deployment & Final Review**
    *   [ ] Choose and set up hosting platform (e.g., Heroku, AWS).
    *   [ ] Deploy the application.
    *   [ ] Configure environment variables on the server.
    *   [ ] Final end-to-end testing on the deployed environment.
    *   [ ] Prepare basic user guide/documentation for the client on how to use the web interface.

**Total Estimated Time: 14 - 21 business days.** (Increased due to more granular breakdown and contingency) 