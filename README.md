# CarFinderAI: Used Car Lead Generation Agent

An automated system to help car dealerships find qualified leads from used car listings online.

## Overview

CarFinderAI scrapes online listings from sites like Craigslist, automatically contacts sellers, and helps dealerships acquire quality inventory for less. The system filters listings based on criteria like year, make, and model to focus on the most valuable opportunities.

## Quick Start

1. Clone this repository
2. Set up a Python virtual environment:
   ```
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
3. Configure your environment:
   ```
   cp .env.template .env
   # Edit .env with your actual credentials
   ```
   - Or use the built-in web interface for configuration management (see [Environment Settings](./docs/environment_settings.md))
4. Run the application:
   ```
   python main.py
   ```

## Features

- Automatic scraping of Craigslist car listings
- Filtering by year, make, and model
- Automated seller contact via SMS through Twilio
- Lead tracking and management
- Web-based environment configuration management

## Documentation

See the [docs](./docs) directory for detailed documentation on:
- [Setup and configuration](./docs/environment_settings.md)
- Testing
- Development guidelines
- Project architecture 