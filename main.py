"""
Test script for Thryv CRM integration
"""

import os
from dotenv import load_dotenv
from utils.config import load_config
from managers.thryv_integrator import ThryvIntegrator
from utils.logger import setup_logger

# Set up logger
logger = setup_logger('thryv_test')

def test_thryv_integration():
    """Test Thryv CRM integration"""
    # Load configuration
    load_dotenv()
    config = load_config()
    
    # Initialize Thryv integrator
    thryv = ThryvIntegrator(config)
    
    # Test authentication
    logger.info("Testing Thryv authentication...")
    auth_result = thryv.authenticate()
    
    if auth_result:
        logger.info("✅ Thryv authentication successful")
    else:
        logger.error("❌ Thryv authentication failed")
        return
    
    # Test lead creation with sample data
    logger.info("Testing Thryv lead creation...")
    sample_lead = {
        'title': 'Test 2022 Toyota Camry (TESTING ONLY)',
        'year': 2022,
        'make': 'Toyota',
        'model': 'Camry',
        'price': 28000,
        'source': 'Test Script',
        'listing_url': 'https://example.com/test',
        'description': 'This is a test lead created by the CarFinderAI testing script.',
        'phone_number': '',  # Intentionally empty for testing
        'date_posted': '2023-08-01'
    }
    
    # Map lead to Thryv format and display for verification
    logger.info("Mapping lead to Thryv format...")
    thryv_formatted = thryv.map_lead_to_thryv_format(sample_lead)
    logger.info(f"Thryv formatted lead: {thryv_formatted}")
    
    # Only attempt to create the lead if THRYV_TEST_CREATE_LEAD is set to "true"
    if os.getenv('THRYV_TEST_CREATE_LEAD', '').lower() == 'true':
        logger.info("Creating test lead in Thryv...")
        success, result = thryv.create_thryv_lead(sample_lead)
        
        if success:
            logger.info(f"✅ Thryv lead created successfully with ID: {result}")
        else:
            logger.error(f"❌ Thryv lead creation failed: {result}")
    else:
        logger.info("Skipping actual lead creation. Set THRYV_TEST_CREATE_LEAD=true to test creation.")

if __name__ == "__main__":
    test_thryv_integration() 