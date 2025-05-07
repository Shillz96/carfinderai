"""
Main orchestrator for the Used Car Lead Generation Agent.
Coordinates the scraping, data storage, messaging, notifications, and CRM integration.
"""

import sys
import os
import uuid
import argparse
import traceback
from datetime import datetime
from utils.logger import setup_logger
from utils.config import load_config
from utils.ui_config_manager import is_crm_enabled
from scrapers.craigslist_scraper import CraigslistScraper
from managers.messaging_manager import MessagingManager
from managers.data_manager import DataManager
from managers.notification_manager import NotificationManager
from managers.thryv_integrator import ThryvIntegrator

# Set up logger
logger = setup_logger('main_agent')

def main(use_mock=False, dry_run=False):
    """
    Main function to run the car finder agent.
    Orchestrates the entire process from scraping to CRM integration.
    
    Args:
        use_mock (bool): Whether to use mock services instead of real APIs
        dry_run (bool): If True, log actions but don't execute them
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        print("\n========= Used Car Lead Generation Agent =========")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        logger.info("Starting Used Car Lead Generation Agent")
        if use_mock:
            logger.info("*** USING MOCK SERVICES - NO REAL API CALLS WILL BE MADE ***")
            print(">>> Running with MOCK SERVICES (no real API calls)")
        if dry_run:
            logger.info("*** DRY RUN MODE - ACTIONS WILL BE LOGGED BUT NOT EXECUTED ***")
            print(">>> Running in DRY RUN MODE (actions will be logged but not executed)")
        
        # Load configuration
        print("Loading configuration...")
        logger.info("Loading configuration")
        config = load_config()
        
        # Initialize managers
        print("Initializing services and managers...")
        logger.info("Initializing managers...")
        
        # If using mock services, set up mock APIs
        if use_mock:
            from utils.mock_services import get_mock_services
            from tests.mock_managers import MockMessagingManager, MockDataManager, MockNotificationManager, MockThryvIntegrator
            
            mock_services = get_mock_services()
            messaging_manager = MockMessagingManager(config, mock_twilio_service=mock_services['twilio'])
            data_manager = MockDataManager(config, mock_sheets_service=mock_services['sheets'])
            notification_manager = MockNotificationManager(config, messaging_manager, mock_email_service=mock_services['email'])
            thryv_integrator = MockThryvIntegrator(config, mock_thryv_service=mock_services['thryv'])
        else:
            # Real service initialization
            messaging_manager = MessagingManager(config)
            data_manager = DataManager(config)
            notification_manager = NotificationManager(config, messaging_manager)
            thryv_integrator = ThryvIntegrator(config)
        
        # Verify Thryv authentication (don't block if fails)
        print("Authenticating with Thryv CRM...")
        thryv_auth_success = thryv_integrator.authenticate()
        if not thryv_auth_success:
            logger.warning("Thryv authentication failed. CRM integration will be skipped.")
            print("⚠️  Thryv authentication failed. CRM integration will be skipped.")
        else:
            print("✅ Thryv authentication successful.")
        
        # Initialize the Craigslist scraper
        print("Initializing Craigslist scraper...")
        logger.info("Initializing Craigslist scraper")
        craigslist_scraper = CraigslistScraper(config)
        
        # Scrape listings
        if dry_run:
            logger.info("DRY RUN: Would scrape Craigslist listings")
            print("DRY RUN: Loading sample listings instead of scraping...")
            # Use sample data in dry run mode
            import json
            sample_data_path = os.path.join('tests', 'sample_data', 'sample_listings.json')
            try:
                if os.path.exists(sample_data_path):
                    with open(sample_data_path, 'r') as f:
                        listings = json.load(f)
                        logger.info(f"Loaded {len(listings)} sample listings")
                        print(f"✅ Loaded {len(listings)} sample listings")
                else:
                    # Create some dummy listings if sample file doesn't exist
                    print("⚠️  Sample data file not found. Creating dummy listings...")
                    listings = [
                        {
                            'title': '2020 Toyota Camry - Low Miles!',
                            'year': 2020,
                            'make': 'Toyota',
                            'model': 'Camry',
                            'price': 22500,
                            'description': 'Great condition, only 15k miles',
                            'listing_url': 'https://craigslist.org/sample1',
                            'phone_number': '+18081234567',
                            'date_posted': '2023-05-15'
                        },
                        {
                            'title': '2019 Honda Accord - Excellent Condition',
                            'year': 2019,
                            'make': 'Honda',
                            'model': 'Accord',
                            'price': 20800,
                            'description': 'One owner, well maintained',
                            'listing_url': 'https://craigslist.org/sample2',
                            'phone_number': None,
                            'date_posted': '2023-05-14'
                        }
                    ]
                    logger.info(f"Created {len(listings)} dummy listings")
                    print(f"✅ Created {len(listings)} dummy listings")
            except Exception as e:
                logger.error(f"Error loading sample data: {str(e)}")
                print(f"❌ Error loading sample data: {str(e)}")
                listings = []
        else:
            logger.info("Scraping Craigslist listings")
            print("Scraping Craigslist for car listings... (this may take a few minutes)")
            print("Searches configured for vehicles from year", config.get('scraper', {}).get('min_vehicle_year', 'N/A'), "and newer")
            listings = craigslist_scraper.scrape_listings()
            print(f"✅ Scraping complete!")
        
        # Add source to listings
        for listing in listings:
            listing['source'] = 'Craigslist'
            
        logger.info(f"Found {len(listings)} raw listings from Craigslist")
        print(f"Found {len(listings)} raw listings from Craigslist")
        
        # Process and store new leads
        if listings:
            if dry_run:
                logger.info(f"DRY RUN: Would append {len(listings)} leads to Google Sheet")
                print(f"DRY RUN: Would append {len(listings)} leads to Google Sheet")
                # Log a few sample listings
                for i, listing in enumerate(listings[:3]):
                    logger.info(f"Sample listing {i+1}: {listing.get('title')} - ${listing.get('price')}")
                    print(f"   - {listing.get('title')} - ${listing.get('price')}")
                if len(listings) > 3:
                    logger.info(f"...and {len(listings) - 3} more listings")
                    print(f"   - ...and {len(listings) - 3} more listings")
                success = True
            else:
                logger.info("Appending new leads to Google Sheet...")
                print("Appending new leads to Google Sheet...")
                success = data_manager.append_leads_to_sheet(listings)
                if success:
                    print("✅ Leads added to Google Sheet successfully")
                else:
                    print("❌ Failed to add leads to Google Sheet")
            
            if success:
                logger.info("Leads processed and potentially added to Google Sheet.")
                # Get all leads from the sheet to find new ones and their row indices
                
                if dry_run:
                    # In dry run mode, just use our listings as "all leads"
                    print("DRY RUN: Using sample listings as stored leads")
                    all_leads = []
                    for i, listing in enumerate(listings):
                        lead = listing.copy()
                        # Add dummy row index
                        lead['_row_index'] = i + 2  # +2 because row 1 is header
                        all_leads.append(lead)
                else:
                    print("Retrieving all leads from Google Sheet...")
                    all_leads = data_manager.get_all_leads()
                    print(f"Retrieved {len(all_leads)} leads from Google Sheet")
                
                # Find new leads by matching against listings (using listing_url as unique identifier)
                listing_urls = {lead.get('listing_url'): lead for lead in listings}
                
                processed_count = 0
                total_to_process = 0
                
                # First, count how many leads need processing
                for lead in all_leads:
                    listing_url = lead.get('listing_url')
                    if listing_url in listing_urls and not lead.get('thryv_status'):
                        total_to_process += 1
                
                if total_to_process > 0:
                    print(f"\nProcessing {total_to_process} new leads:")
                    
                for index, lead in enumerate(all_leads, start=2):  # Start at 2 because row 1 is header
                    listing_url = lead.get('listing_url')
                    
                    # If this lead is in our new listings and hasn't been processed for Thryv
                    if listing_url in listing_urls and not lead.get('thryv_status'):
                        current_lead = listing_urls[listing_url]
                        logger.info(f"Processing lead: {current_lead.get('title')}")
                        processed_count += 1
                        print(f"\n({processed_count}/{total_to_process}) Processing: {current_lead.get('title')}")
                        
                        # 1. Attempt to send SMS to seller
                        sms_to_seller_status = "Not Attempted"
                        if current_lead.get('phone_number'):
                            if dry_run:
                                logger.info(f"DRY RUN: Would send SMS to seller for: {current_lead.get('title')}")
                                print(f"   DRY RUN: Would send SMS to seller at {current_lead.get('phone_number')}")
                                sms_to_seller_status = "Would Send (Dry Run)"
                            else:
                                logger.info(f"Attempting to send SMS to seller for: {current_lead.get('title')}")
                                print(f"   Sending SMS to seller at {current_lead.get('phone_number')}...")
                                inquiry_result = messaging_manager.send_listing_inquiry(current_lead)
                                if inquiry_result:
                                    sms_to_seller_status = "Sent Successfully"
                                    logger.info(f"SMS to seller for {current_lead.get('title')} sent.")
                                    print(f"   ✅ SMS sent successfully")
                                else:
                                    sms_to_seller_status = "Failed to Send"
                                    logger.warning(f"SMS to seller for {current_lead.get('title')} failed.")
                                    print(f"   ❌ Failed to send SMS")
                        else:
                            sms_to_seller_status = "No Phone Number"
                            logger.info(f"No phone number found for seller of: {current_lead.get('title')}")
                            print(f"   ⚠️ No phone number found for seller")
                        
                        # 2. Notify client about the new lead
                        if dry_run:
                            logger.info(f"DRY RUN: Would notify client about lead: {current_lead.get('title')}")
                            print(f"   DRY RUN: Would notify client about this lead")
                        else:
                            logger.info(f"Notifying client about lead: {current_lead.get('title')}")
                            print(f"   Notifying client about this lead...")
                            notification_result = notification_manager.notify_client_about_lead(current_lead, sms_to_seller_status)
                            if notification_result:
                                print(f"   ✅ Client notification sent successfully")
                            else:
                                print(f"   ⚠️ Client notification may have failed")
                        
                        # 3. Send to Thryv CRM
                        if thryv_auth_success and is_crm_enabled():
                            if dry_run:
                                logger.info(f"DRY RUN: Would send lead to Thryv CRM: {current_lead.get('title')}")
                                print(f"   DRY RUN: Would send lead to Thryv CRM")
                                # Simulate success/failure scenarios
                                import random
                                if random.random() < 0.9:  # 90% success rate in dry run
                                    thryv_success = True
                                    thryv_result = f"DRYRUN-{uuid.uuid4().hex[:8]}"
                                    logger.info(f"DRY RUN: Lead would be sent to Thryv with ID: {thryv_result}")
                                    print(f"   DRY RUN: Lead would be sent to Thryv with ID: {thryv_result}")
                                else:
                                    thryv_success = False
                                    thryv_result = "Simulated API error"
                                    logger.warning(f"DRY RUN: Lead would fail to send to Thryv: {thryv_result}")
                                    print(f"   DRY RUN: Lead would fail to send to Thryv: {thryv_result}")
                            else:
                                logger.info(f"Sending lead to Thryv CRM: {current_lead.get('title')}")
                                print(f"   Sending lead to Thryv CRM...")
                                thryv_success, thryv_result = thryv_integrator.create_thryv_lead(current_lead)
                            
                            if thryv_success:
                                # Update Google Sheet with Thryv status
                                if dry_run:
                                    logger.info(f"DRY RUN: Would update Google Sheet with Thryv status: Sent to Thryv, ID: {thryv_result}")
                                    print(f"   DRY RUN: Would update Google Sheet with Thryv status")
                                else:
                                    data_manager.update_thryv_status(index, "Sent to Thryv", thryv_result)
                                    logger.info(f"Lead sent to Thryv with ID: {thryv_result}")
                                    print(f"   ✅ Lead sent to Thryv with ID: {thryv_result}")
                            else:
                                # Update Google Sheet with error status
                                if dry_run:
                                    logger.info(f"DRY RUN: Would update Google Sheet with Thryv error status: {thryv_result}")
                                    print(f"   DRY RUN: Would update Google Sheet with Thryv error status")
                                else:
                                    data_manager.update_thryv_status(index, "Error: Failed to send to Thryv")
                                    logger.warning(f"Failed to send lead to Thryv: {thryv_result}")
                                    print(f"   ❌ Failed to send lead to Thryv: {thryv_result}")
                        elif not thryv_auth_success and is_crm_enabled():
                            logger.warning(f"Thryv authentication failed, cannot send lead: {current_lead.get('title')}")
                            print(f"   ⚠️ Thryv authentication failed, cannot send lead.")
                            thryv_status = "Error (Auth Failed)"
                        else:
                            logger.info("Thryv CRM integration skipped as it's disabled or auth failed.")
                            # No print here to avoid redundancy if already printed above for disabled case
                            if not is_crm_enabled():
                                thryv_status = "Skipped (Disabled)"
                            else: # This case should ideally not be hit if logic is sound
                                thryv_status = "Skipped (Unknown Reason)"
                        
                        # 4. Update Google Sheet with Thryv status
                        if not dry_run:
                            data_manager.update_thryv_status(index, thryv_status)
                            logger.info(f"Lead status updated to: {thryv_status}")
                            print(f"   ✅ Lead status updated to: {thryv_status}")
                    
                if total_to_process == 0:
                    print("\nNo new leads to process in this run.")
            else:
                logger.error("Failed to append leads to Google Sheet.")
                print("❌ Failed to append leads to Google Sheet.")
        else:
            logger.info("No listings found in this scrape cycle.")
            print("\nNo new listings found in this scrape cycle.")
            
        logger.info("Agent completed successfully")
        print("\n✅ Agent completed successfully")
        print("\n============== Operation Complete ==============\n")
        return 0
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"\n❌ ERROR: {str(e)}")
        print("Check the logs for more details.")
        print("\n============== Operation Failed ===============\n")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run the Used Car Lead Generation Agent')
    parser.add_argument('--mock', action='store_true', help='Use mock services instead of real APIs')
    parser.add_argument('--dry-run', action='store_true', help='Log actions but do not execute them')
    
    args = parser.parse_args()
    
    # Run the main function
    exit_code = main(use_mock=args.mock, dry_run=args.dry_run)
    sys.exit(exit_code) 