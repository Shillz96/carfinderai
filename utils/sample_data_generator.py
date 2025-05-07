"""
Sample data generator for the Used Car Lead Generation Agent.
Provides utilities to generate, manage, and validate sample data for testing.
"""

import os
import json
import argparse
import random
from datetime import datetime, timedelta

# Sample data constants
CAR_MAKES = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Tacoma", "4Runner"],
    "Honda": ["Accord", "Civic", "CR-V", "Pilot", "Odyssey"],
    "Mazda": ["CX-5", "CX-9", "Mazda3", "Mazda6", "MX-5"],
    "Subaru": ["Outback", "Forester", "Crosstrek", "Legacy", "Impreza"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X"],
    "Ford": ["F-150", "Escape", "Explorer", "Mustang", "Bronco"],
    "Chevrolet": ["Silverado", "Equinox", "Tahoe", "Malibu", "Camaro"],
    "Nissan": ["Altima", "Rogue", "Pathfinder", "Sentra", "Murano"]
}

TRIMS = {
    "Toyota": ["LE", "XLE", "Limited", "SE", "XSE", "TRD"],
    "Honda": ["LX", "EX", "EX-L", "Sport", "Touring"],
    "Mazda": ["Sport", "Touring", "Grand Touring", "Carbon Edition", "Signature"],
    "Subaru": ["Base", "Premium", "Limited", "Touring", "Wilderness"],
    "Tesla": ["Standard Range", "Long Range", "Performance", "Plaid"],
    "Ford": ["XL", "XLT", "Lariat", "Platinum", "Limited"],
    "Chevrolet": ["LS", "LT", "RS", "Premier", "High Country"],
    "Nissan": ["S", "SV", "SL", "Platinum", "SR"]
}

DESCRIPTORS = [
    "Excellent Condition", "Low Miles", "Like New", "Great Deal", "Must See",
    "Single Owner", "Well Maintained", "Garage Kept", "Price Reduced", "Fully Loaded"
]

DESCRIPTIONS = [
    "Great condition, one owner. All maintenance records available. No accidents. Cold AC, new tires.",
    "Very clean inside and out. Non-smoker. Highway miles only. All service completed at dealership.",
    "Excellent condition with low miles. Premium sound system, leather seats, backup camera.",
    "Just had full service. New brakes and tires. Clean title. No mechanical issues.",
    "Meticulously maintained. All scheduled maintenance done. Interior like new. Must see!",
    "Garage kept and barely driven. Perfect condition inside and out. All options included.",
    "Adult owned and well cared for. Factory warranty still active. Price is negotiable.",
    "Amazing vehicle in perfect condition. Low miles, lots of options. Priced to sell quickly.",
    "Local trade-in. Clean vehicle history report. Fully detailed and ready to go.",
    "Pampered vehicle with all the features. Never been in an accident. Must see to appreciate."
]

LOCATIONS = {
    "Honolulu": "oahu",
    "Kailua": "oahu",
    "Kaneohe": "oahu",
    "Waipahu": "oahu",
    "Kahului": "maui",
    "Kihei": "maui",
    "Lahaina": "maui",
    "Lihue": "kauai",
    "Kapaa": "kauai",
    "Hilo": "hawaii",
    "Kailua-Kona": "hawaii"
}

def generate_phone_number(include_null=True):
    """
    Generate a random phone number or null.
    
    Args:
        include_null (bool): If True, ~20% of generated numbers will be null
        
    Returns:
        str or None: A formatted phone number string or None
    """
    if include_null and random.random() < 0.2:
        return None
    
    area_codes = ['808']  # Hawaii area code
    return f"+1{random.choice(area_codes)}{random.randint(2, 9)}{random.randint(0, 9)}{random.randint(0, 9)}" + \
           f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"

def generate_price(make, model, year):
    """
    Generate a realistic price for a vehicle based on make, model, and year.
    
    Args:
        make (str): Vehicle make
        model (str): Vehicle model
        year (int): Vehicle year
        
    Returns:
        int: A realistic price
    """
    age = datetime.now().year - year
    
    base_prices = {
        "Toyota": {
            "Camry": 25000, "Corolla": 20000, "RAV4": 28000, 
            "Highlander": 35000, "Tacoma": 32000, "4Runner": 38000
        },
        "Honda": {
            "Accord": 24500, "Civic": 19500, "CR-V": 27000,
            "Pilot": 34000, "Odyssey": 31000
        },
        "Mazda": {
            "CX-5": 26000, "CX-9": 34000, "Mazda3": 21000,
            "Mazda6": 25000, "MX-5": 28000
        },
        "Subaru": {
            "Outback": 27000, "Forester": 26000, "Crosstrek": 24000,
            "Legacy": 23000, "Impreza": 20000
        },
        "Tesla": {
            "Model 3": 45000, "Model Y": 53000, "Model S": 85000,
            "Model X": 90000
        },
        "Ford": {
            "F-150": 40000, "Escape": 26000, "Explorer": 33000,
            "Mustang": 30000, "Bronco": 35000
        },
        "Chevrolet": {
            "Silverado": 38000, "Equinox": 25000, "Tahoe": 48000,
            "Malibu": 23000, "Camaro": 29000
        },
        "Nissan": {
            "Altima": 23000, "Rogue": 25000, "Pathfinder": 33000,
            "Sentra": 19000, "Murano": 30000
        }
    }
    
    # Get base price or use default if model not found
    base_price = base_prices.get(make, {}).get(model, 25000)
    
    # Apply age depreciation (roughly 10% per year)
    price = base_price * (0.9 ** age)
    
    # Add some randomness (±5%)
    price = price * random.uniform(0.95, 1.05)
    
    # Round to nearest 100
    return int(round(price / 100) * 100)

def generate_sample_listings(count=5, min_year=2018, max_year=None):
    """
    Generate a list of sample car listings.
    
    Args:
        count (int): Number of listings to generate
        min_year (int): Minimum vehicle year
        max_year (int): Maximum vehicle year (defaults to current year)
        
    Returns:
        list: List of car listing dictionaries
    """
    if max_year is None:
        max_year = datetime.now().year
    
    listings = []
    
    for _ in range(count):
        # Select random make and model
        make = random.choice(list(CAR_MAKES.keys()))
        model = random.choice(CAR_MAKES[make])
        
        # Generate year
        year = random.randint(min_year, max_year)
        
        # Generate trim
        trim = random.choice(TRIMS.get(make, ["Base"]))
        
        # Generate title
        descriptor = random.choice(DESCRIPTORS)
        title = f"{year} {make} {model} {trim} - {descriptor}"
        
        # Generate price
        price = generate_price(make, model, year)
        
        # Generate description
        description = random.choice(DESCRIPTIONS)
        
        # Generate location and URL
        location_name = random.choice(list(LOCATIONS.keys()))
        location_area = LOCATIONS[location_name]
        listing_id = f"sample{random.randint(10000, 99999)}"
        listing_url = f"https://{location_area}.craigslist.org/{location_area}/cto/{listing_id}"
        
        # Generate date posted (within last 30 days)
        days_ago = random.randint(0, 30)
        date_posted = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        # Generate phone number
        phone_number = generate_phone_number()
        
        # Create listing
        listing = {
            "title": title,
            "year": year,
            "make": make,
            "model": model,
            "price": price,
            "description": description,
            "listing_url": listing_url,
            "phone_number": phone_number,
            "date_posted": date_posted,
            "source": "Craigslist"
        }
        
        listings.append(listing)
    
    return listings

def create_sample_data_file(count=5, output_file=None, min_year=2018):
    """
    Create a sample data file with randomly generated listings.
    
    Args:
        count (int): Number of listings to generate
        output_file (str): Path to output file (defaults to standard location)
        min_year (int): Minimum vehicle year
        
    Returns:
        str: Path to created file
    """
    if output_file is None:
        # Default location in tests/sample_data
        output_dir = os.path.join('tests', 'sample_data')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'sample_listings.json')
    
    # Generate listings
    listings = generate_sample_listings(count, min_year)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(listings, f, indent=2)
    
    return output_file

def main():
    """Main function to run from command line."""
    parser = argparse.ArgumentParser(description='Generate sample car listings data')
    parser.add_argument('--count', type=int, default=5, help='Number of listings to generate')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--min-year', type=int, default=2018, help='Minimum vehicle year')
    
    args = parser.parse_args()
    
    output_file = create_sample_data_file(args.count, args.output, args.min_year)
    print(f"Generated {args.count} sample listings and saved to {output_file}")

if __name__ == "__main__":
    main() 