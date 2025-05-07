# Project Specification

## 1. Project Title
Used Car Lead Generation Agent for Hawaii

## 2. Client
wealthymindshi

## 3. Goal
To build an automated agent that performs the following key functions:
*   Scrubs online listings for used vehicles (model year 2018 and newer) in Hawaii.
*   Sends an initial, standardized SMS message to the sellers of qualifying vehicles.
*   Notifies the client (wealthymindshi) of each new lead via both email and SMS.
*   Integrates the captured lead information with the client's Thryv CRM system.

## 4. Key Requirements

### 4.1. Target Listing Sources
*   **Craigslist:** Hawaii regions (e.g., Oahu, Maui, Big Island, Kauai).
*   **Facebook Marketplace:** Relevant Hawaii-based groups and general marketplace searches for the Hawaiian islands.

### 4.2. Vehicle Criteria
*   **Year of Manufacture:** 2018 or newer.
*   **Other Criteria:** No specific make, model, price, or mileage restrictions at this time, beyond the year.

### 4.3. Initial Seller Messaging
*   **Channel:** SMS.
*   **Content:** A standard, friendly, and concise message. Example: "Hi, I saw your listing for the [Year] [Make] [Model]. Is it still available?"
*   **Trigger:** Sent automatically upon identifying a new, qualifying lead with available contact information.

### 4.4. Lead Notification (to Client)
*   **Channels:** Email and SMS.
*   **Trigger:** Sent whenever a new lead is captured AND the initial message has been attempted/sent to the seller.
*   **Content:** Include essential lead details (Vehicle Year/Make/Model, Price, Listing Link, Seller Contact Info if available).

### 4.5. CRM Integration
*   **System:** Client's Thryv CRM.
*   **Method:** Prioritize direct API integration. If not feasible, use Zapier as a fallback (Google Sheets to Thryv).
*   **Data:** Transfer all relevant lead information (as per the defined data schema).

### 4.6. Lead Tracking
*   **System:** Google Sheet.
*   **Content:** Maintain a comprehensive record of all captured leads, including scraped data, messaging status, notification status, and CRM integration status (see Data Schema in Technical Design Document).

### 4.7. User Interface (Private Web Portal)
*   **Access:** Private, secure access for the client.
*   **Functionality:**
    *   View captured leads (with filtering and sorting).
    *   Manage key application environment variables through a dedicated settings page (e.g., API keys, scraper parameters, notification settings defined as configurable).
    *   Access to project documentation.

## 5. Success Criteria

The project will be considered successful when the following are achieved:

*   **SC1:** The agent consistently and reliably scrapes used car listings (vehicles manufactured in 2018 or later) from the specified Craigslist (Hawaii) and Facebook Marketplace (Hawaii) sources.
*   **SC2:** Initial SMS messages are automatically and successfully sent to sellers for a high percentage of leads where valid contact information is extracted.
*   **SC3:** The client (wealthymindshi) receives timely and accurate email and SMS notifications for all new, qualified leads.
*   **SC4:** Lead information (including vehicle details, seller contact, and source) is accurately and automatically transferred to the client's Thryv CRM for each new lead.
*   **SC5:** All captured leads and their processing statuses are accurately recorded and maintained in the designated Google Sheet.
*   **SC6:** The client can securely access the private web interface to view lead data, understand the agent's activity, and access documentation.
*   **SC7:** The system operates stably with appropriate error handling and logging to identify and diagnose issues. 