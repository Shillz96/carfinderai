# Facebook Marketplace Scraper

This module provides functionality to scrape car listings from Facebook Marketplace in Hawaii, focusing on vehicles from 2018 and newer.

## How It Works

The scraper uses a two-stage approach:

1. **Static Approach**: First attempts to scrape using standard HTTP requests and BeautifulSoup parsing. This is faster but may fail due to Facebook's heavy reliance on JavaScript.

2. **Selenium Approach**: If static scraping fails, it falls back to using Selenium WebDriver to automate a Chrome browser. This approach can handle dynamic content but requires additional setup.

## Prerequisites

### Required Python Packages
- beautifulsoup4
- requests
- selenium
- python-dotenv

### Additional Requirements for Selenium
- Chrome or Chromium browser installed
- ChromeDriver installed and accessible in PATH
  - Download from: https://sites.google.com/chromium.org/driver/
  - Make sure the version matches your Chrome/Chromium version

## Configuration

In your `.env` file, add:

```
FACEBOOK_MARKETPLACE_URLS="https://www.facebook.com/marketplace/honolulu/vehicles/,https://www.facebook.com/marketplace/maui/vehicles/"
```

You can add multiple URLs separated by commas.

## Using the Scraper

### Basic Usage

```python
from scrapers.facebook_scraper import scrape_facebook_marketplace
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get configuration
fb_urls = os.getenv('FACEBOOK_MARKETPLACE_URLS', '').split(',')
config = {
    "FACEBOOK_MARKETPLACE_URLS": fb_urls
}

# Run the scraper
leads = scrape_facebook_marketplace(config)

# Process results
for lead in leads:
    print(f"{lead.get('year')} {lead.get('make')} {lead.get('model')} - ${lead.get('price')}")
```

## Common Issues and Solutions

### No Listings Found

- **CSS Selectors Not Matching**: Facebook frequently changes its HTML structure. If no listings are found, check the CSS selectors in `parse_fb_listings()` and `extract_listing_from_element()`.

### Selenium Issues

- **ChromeDriver Not Found**: Ensure ChromeDriver is installed and in your PATH.
- **Browser Closes Immediately**: This is normal in headless mode. For debugging, you can disable headless mode by removing the `--headless` option.
- **Facebook Login Required**: The scraper attempts to work with public listings, but some regions may require login. If needed, implement a secure login mechanism.

### Anti-Scraping Measures

Facebook has sophisticated anti-scraping measures. To reduce the risk of being blocked:

- Use random delays between requests
- Rotate user agents
- Limit the number of pages scraped in a single session
- Consider using proxies for large-scale scraping

## Testing

To run the unit tests:

```
python -m unittest tests.test_facebook_scraper
```

For manual testing, you can run the scraper directly:

```
python -m scrapers.facebook_scraper
```

## Maintenance

This scraper requires regular maintenance due to:

1. Facebook's frequent UI changes
2. Updates to their anti-scraping measures
3. Changes in how car listings are displayed

Review and update the CSS selectors periodically if the scraper stops finding listings. 