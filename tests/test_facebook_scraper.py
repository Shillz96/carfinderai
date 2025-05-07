"""
Unit tests for the Facebook Marketplace scraper.
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Add the parent directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.facebook_scraper import (
    scrape_facebook_marketplace, 
    fetch_page_content_statically,
    parse_fb_listings
)


class TestFacebookScraper(unittest.TestCase):
    """Test cases for Facebook Marketplace scraper."""

    def setUp(self):
        """Set up test environment."""
        # Load environment variables
        load_dotenv()
        
        # Test configuration
        self.test_config = {
            "FACEBOOK_MARKETPLACE_URLS": [
                "https://www.facebook.com/marketplace/honolulu/vehicles/"
            ]
        }
        
        # Sample HTML content for testing
        self.sample_html = """
        <html>
        <body>
            <div data-testid="marketplace_feed_item">
                <span class="a8c37x1j">2020 Toyota Camry</span>
                <span class="d2edcug0">$15,000</span>
                <a href="/marketplace/item/123456789/">View</a>
            </div>
            <div data-testid="marketplace_feed_item">
                <span class="a8c37x1j">2017 Honda Accord</span>
                <span class="d2edcug0">$12,500</span>
                <a href="/marketplace/item/987654321/">View</a>
            </div>
            <div data-testid="marketplace_feed_item">
                <span class="a8c37x1j">2022 Nissan Altima</span>
                <span class="d2edcug0">$19,999</span>
                <a href="/marketplace/item/567891234/">View</a>
            </div>
        </body>
        </html>
        """

    @patch('scrapers.facebook_scraper.requests.get')
    def test_fetch_page_content_statically(self, mock_get):
        """Test static page content fetching."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.sample_html
        mock_get.return_value = mock_response

        # Test function
        content = fetch_page_content_statically("https://www.facebook.com/marketplace/test")
        
        # Assertions
        self.assertIsNotNone(content)
        self.assertEqual(content, self.sample_html)
        mock_get.assert_called_once()

    def test_parse_fb_listings(self):
        """Test parsing of Facebook Marketplace listings."""
        # Parse the sample HTML
        listings = parse_fb_listings(self.sample_html)
        
        # Assertions
        self.assertEqual(len(listings), 2)  # Should find 2 valid listings (2020 and 2022 models, not 2017)
        
        # Check if years were parsed correctly
        years = [listing.get('year') for listing in listings]
        self.assertIn(2020, years)
        self.assertIn(2022, years)
        self.assertNotIn(2017, years)  # 2017 < MIN_YEAR (2018)
        
        # Check if a listing has the expected attributes
        toyota = next((l for l in listings if l.get('make') == 'Toyota'), None)
        if toyota:
            self.assertEqual(toyota.get('model'), 'Camry')
            self.assertEqual(toyota.get('price'), 15000.0)
            self.assertTrue(toyota.get('url').endswith('/123456789/'))
        
    @patch('scrapers.facebook_scraper.fetch_page_content_statically')
    @patch('scrapers.facebook_scraper.parse_fb_listings')
    @patch('scrapers.facebook_scraper.scrape_with_selenium')
    def test_scrape_facebook_marketplace_static_success(self, mock_selenium, mock_parse, mock_fetch):
        """Test successful static scraping, Selenium not needed."""
        # Setup mocks
        mock_fetch.return_value = self.sample_html
        mock_parse.return_value = [
            {'title': '2020 Toyota Camry', 'year': 2020, 'price': 15000.0, 'url': 'https://fb.com/marketplace/item/123'}
        ]
        
        # Run the scraper
        leads = scrape_facebook_marketplace(self.test_config)
        
        # Assertions
        self.assertEqual(len(leads), 1)
        mock_fetch.assert_called_once()
        mock_parse.assert_called_once()
        mock_selenium.assert_not_called()  # Selenium should not be called when static scraping succeeds
    
    @patch('scrapers.facebook_scraper.fetch_page_content_statically')
    @patch('scrapers.facebook_scraper.parse_fb_listings')
    @patch('scrapers.facebook_scraper.scrape_with_selenium')
    def test_scrape_facebook_marketplace_fallback_to_selenium(self, mock_selenium, mock_parse, mock_fetch):
        """Test fallback to Selenium when static scraping fails."""
        # Setup mocks
        mock_fetch.return_value = self.sample_html
        mock_parse.return_value = []  # Static parsing finds no leads
        mock_selenium.return_value = [
            {'title': '2020 Toyota Camry', 'year': 2020, 'price': 15000.0, 'url': 'https://fb.com/marketplace/item/123'}
        ]
        
        # Run the scraper
        leads = scrape_facebook_marketplace(self.test_config)
        
        # Assertions
        self.assertEqual(len(leads), 1)
        mock_fetch.assert_called_once()
        mock_parse.assert_called_once()
        mock_selenium.assert_called_once()  # Selenium should be called when static scraping finds no leads


if __name__ == '__main__':
    unittest.main() 