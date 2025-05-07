import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import requests

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.craigslist_scraper import CraigslistScraper

class TestCraigslistScraper(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.config = {
            'scraper': {
                'craigslist_urls': ['https://honolulu.craigslist.org/search/cta'],
                'min_vehicle_year': 2018
            }
        }
        self.scraper = CraigslistScraper(self.config)
    
    def test_extract_make(self):
        """Test extracting car make from title"""
        # Test basic extraction
        title = "2020 Toyota Camry - Low Miles!"
        self.assertEqual(self.scraper._extract_make(title), "Toyota")
        
        # Test with lowercase
        title = "2019 honda civic for sale"
        self.assertEqual(self.scraper._extract_make(title), "Honda")
        
        # Test with unknown make
        title = "2021 Car for Sale"
        self.assertEqual(self.scraper._extract_make(title), "Unknown")
    
    def test_extract_model(self):
        """Test extracting car model from title"""
        # Basic extraction
        title = "2020 Toyota Camry - Excellent Condition"
        self.assertEqual(self.scraper._extract_model(title), "Camry")
        
        # Test with unknown make
        title = "2021 Car for Sale"
        self.assertEqual(self.scraper._extract_model(title), "")
    
    @patch('requests.get')
    def test_fetch_listing_page(self, mock_get):
        """Test fetching listing page"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test page</body></html>"
        mock_get.return_value = mock_response
        
        result = self.scraper.fetch_listing_page("https://test.com")
        self.assertEqual(result, "<html><body>Test page</body></html>")
        
        # Mock failed response
        mock_response.status_code = 404
        result = self.scraper.fetch_listing_page("https://test.com")
        self.assertIsNone(result)
        
        # Mock exception - need to reset before setting side_effect
        mock_get.reset_mock()
        mock_get.side_effect = requests.RequestException("Connection error")
        result = self.scraper.fetch_listing_page("https://test.com")
        self.assertIsNone(result)
    
    def test_parse_listings(self):
        """Test parsing listings from HTML content"""
        # Sample HTML content - updated to match current structure
        html_content = """
        <html>
            <body>
                <ul id="search-results">
                    <li class="cl-static-search-result">
                        <div class="title">
                            <a href="https://honolulu.craigslist.org/post/123" data-testid="listing-title">2020 Toyota Camry - Great Condition</a>
                        </div>
                        <span data-testid="listing-price">$20,000</span>
                    </li>
                    <li class="cl-static-search-result">
                        <div class="title">
                            <a href="https://honolulu.craigslist.org/post/456" data-testid="listing-title">2017 Honda Accord - Low Miles</a>
                        </div>
                        <span data-testid="listing-price">$15,000</span>
                    </li>
                </ul>
            </body>
        </html>
        """
        
        listings = self.scraper.parse_listings(html_content)
        
        # Should only include the 2020 Toyota (year >= 2018)
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0]['make'], 'Toyota')
        self.assertEqual(listings[0]['year'], 2020)
        self.assertEqual(listings[0]['price'], '$20,000')
        
        # Test empty HTML
        self.assertEqual(len(self.scraper.parse_listings("")), 0)

if __name__ == '__main__':
    unittest.main() 