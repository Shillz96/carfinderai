"""
Unit tests for the Thryv Integrator class.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from managers.thryv_integrator import ThryvIntegrator

class TestThryvIntegrator(unittest.TestCase):
    """Test suite for the Thryv Integrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = {
            'thryv': {
                'api_key': 'test_api_key',
                'account_id': 'test_account_id'
            }
        }
        self.thryv = ThryvIntegrator(self.mock_config)
        
        # Sample lead data for testing
        self.sample_lead = {
            'title': 'Test 2022 Toyota Camry',
            'year': 2022,
            'make': 'Toyota',
            'model': 'Camry',
            'price': 28000,
            'source': 'Craigslist',
            'listing_url': 'https://example.com/test',
            'description': 'This is a test lead.',
            'phone_number': '8085551234',
            'date_posted': '2023-08-01'
        }
    
    def test_init(self):
        """Test the initialization of the ThryvIntegrator class."""
        self.assertEqual(self.thryv.api_key, 'test_api_key')
        self.assertEqual(self.thryv.account_id, 'test_account_id')
        self.assertEqual(self.thryv.base_url, 'https://api.thryv.com/v1')
        self.assertEqual(self.thryv.leads_endpoint, 'https://api.thryv.com/v1/leads')
    
    def test_get_headers(self):
        """Test the _get_headers method returns correct headers."""
        headers = self.thryv._get_headers()
        self.assertEqual(headers['Authorization'], 'Bearer test_api_key')
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['Accept'], 'application/json')
    
    def test_map_lead_to_thryv_format(self):
        """Test mapping a lead to Thryv format."""
        thryv_lead = self.thryv.map_lead_to_thryv_format(self.sample_lead)
        
        # Verify key fields
        self.assertEqual(thryv_lead['accountId'], 'test_account_id')
        self.assertEqual(thryv_lead['title'], 'Used Car Lead - 2022 Toyota Camry')
        self.assertEqual(thryv_lead['status'], 'New')
        self.assertEqual(thryv_lead['source'], 'CarFinderAI - Craigslist')
        
        # Verify custom fields
        self.assertEqual(thryv_lead['customFields']['Vehicle Year'], '2022')
        self.assertEqual(thryv_lead['customFields']['Vehicle Make'], 'Toyota')
        self.assertEqual(thryv_lead['customFields']['Vehicle Model'], 'Camry')
        self.assertEqual(thryv_lead['customFields']['Listing Price'], '$28000')
        self.assertEqual(thryv_lead['customFields']['Original Listing URL'], 'https://example.com/test')
        
        # Verify contact info is included
        self.assertIn('contact', thryv_lead)
        self.assertEqual(thryv_lead['contact']['phoneNumbers'][0]['number'], '8085551234')
    
    def test_map_lead_to_thryv_format_no_phone(self):
        """Test mapping a lead without phone number to Thryv format."""
        lead_no_phone = self.sample_lead.copy()
        lead_no_phone['phone_number'] = ''
        
        thryv_lead = self.thryv.map_lead_to_thryv_format(lead_no_phone)
        
        # Verify no contact info is included
        self.assertNotIn('contact', thryv_lead)
    
    @patch('requests.get')
    def test_authenticate_success(self, mock_get):
        """Test authentication success case."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.thryv.authenticate()
        
        # Verify result and that the request was made with correct parameters
        self.assertTrue(result)
        mock_get.assert_called_once_with(
            f"{self.thryv.base_url}/accounts/test_account_id",
            headers=self.thryv._get_headers()
        )
    
    @patch('requests.get')
    def test_authenticate_failure(self, mock_get):
        """Test authentication failure case."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        result = self.thryv.authenticate()
        
        # Verify result
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_create_thryv_lead_success(self, mock_post):
        """Test successful lead creation."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 'test_lead_id'}
        mock_post.return_value = mock_response
        
        success, result = self.thryv.create_thryv_lead(self.sample_lead)
        
        # Verify result
        self.assertTrue(success)
        self.assertEqual(result, 'test_lead_id')
        
        # Verify post was called with correct data
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], self.thryv.leads_endpoint)
        self.assertEqual(kwargs['headers'], self.thryv._get_headers())
        
        # Verify the JSON payload contains expected data
        payload = kwargs['json']
        self.assertEqual(payload['accountId'], 'test_account_id')
        self.assertEqual(payload['title'], 'Used Car Lead - 2022 Toyota Camry')
    
    @patch('requests.post')
    def test_create_thryv_lead_failure(self, mock_post):
        """Test failed lead creation."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        success, result = self.thryv.create_thryv_lead(self.sample_lead)
        
        # Verify result
        self.assertFalse(success)
        self.assertIn("Error creating lead in Thryv", result)

if __name__ == '__main__':
    unittest.main() 