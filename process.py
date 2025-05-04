import re
import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import quote

def setup_driver():
    """Set up and return a Chrome WebDriver instance."""
    chrome_options = Options()
    # Uncomment the line below if you want to run headless (no browser window)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Add user agent to appear more like a regular browser
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Install and set up the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def normalize_address(address):
    """Normalize address for comparison by expanding abbreviations."""
    # Convert to lowercase
    address = address.lower()
    
    # Expand common abbreviations
    replacements = [
        ('s.', 'south'),
        ('s ', 'south '),
        ('n.', 'north'),
        ('n ', 'north '),
        ('e.', 'east'),
        ('e ', 'east '),
        ('w.', 'west'),
        ('w ', 'west '),
        ('st.', 'street'),
        ('st ', 'street '),
        ('ave.', 'avenue'),
        ('ave ', 'avenue '),
        ('blvd.', 'boulevard'),
        ('blvd ', 'boulevard '),
        ('dr.', 'drive'),
        ('dr ', 'drive '),
        ('ln.', 'lane'),
        ('ln ', 'lane '),
        ('rd.', 'road'),
        ('rd ', 'road '),
        ('hwy.', 'highway'),
        ('hwy ', 'highway '),
        (',', ' '),
        ('.', ' '),
        ('  ', ' ')
    ]
    
    for old, new in replacements:
        address = address.replace(old, new)
    
    return address.strip()

def extract_address_parts(address):
    """Extract key parts from an address for matching."""
    # Extract street number
    street_num_match = re.search(r'^\d+', address)
    street_num = street_num_match.group(0) if street_num_match else None
    
    # Extract street name (simplified)
    street_name_match = re.search(r'\d+\s+([^,]+)', address)
    street_name = street_name_match.group(1).strip() if street_name_match else None
    
    # Extract city and state
    parts = [p.strip() for p in address.split(',')]
    city = parts[-2].strip() if len(parts) >= 2 else None
    state_zip = parts[-1].strip() if len(parts) >= 1 else None
    
    # Extract just the state abbreviation if possible
    state_match = re.search(r'([A-Z]{2})', state_zip) if state_zip else None
    state = state_match.group(1) if state_match else state_zip
    
    return {
        'street_num': street_num,
        'street_name': street_name,
        'city': city,
        'state': state
    }

def is_matching_facility(html, facility_name, address):
    """Check if the search result contains the facility address with street number."""
    soup = BeautifulSoup(html, 'html.parser')
    full_text = soup.get_text()
    
    # Extract key parts from the address
    address_parts = extract_address_parts(address)
    
    # Normalize the full text and address for better matching
    normalized_text = normalize_address(full_text)
    
    # Require street number to be present
    if not address_parts['street_num']:
        print(f"Warning: Could not extract street number from address: {address}")
        return False
    
    # Check if street number is in the text
    if address_parts['street_num'] not in full_text:
        print(f"Street number {address_parts['street_num']} not found in search results")
        return False
    
    # Check for street name (more permissive)
    if address_parts['street_name']:
        # Normalize the street name
        normalized_street_name = normalize_address(address_parts['street_name'])
        
        # Extract key words from street name (removing common words like "street", "avenue")
        street_keywords = [word for word in normalized_street_name.split() 
                          if word not in ['street', 'avenue', 'drive', 'road', 'lane', 'boulevard', 'highway']]
        
        # Check if the main part of the street name is in the text
        street_name_found = False
        for keyword in street_keywords:
            if len(keyword) > 2 and keyword in normalized_text:  # Only check keywords longer than 2 chars
                street_name_found = True
                break
        
        if not street_name_found:
            print(f"Street name keywords {street_keywords} not found in search results")
            return False
    
    # Check for city
    if address_parts['city'] and address_parts['city'].lower() not in normalized_text:
        print(f"City '{address_parts['city']}' not found in search results")
        return False
    
    # Check for state
    if address_parts['state'] and address_parts['state'].lower() not in normalized_text:
        print(f"State '{address_parts['state']}' not found in search results")
        return False
    
    # If we get here, we've verified street number, a key part of the street name, city and state
    print(f"Address match confirmed for {facility_name} at {address}")
    return True

def extract_licensed_beds(html):
    """Extract the number of licensed beds from the search results."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # First try to find the specific result snippets
    snippets = soup.find_all(class_=lambda c: c and ("snippet" in c.lower() or "result" in c.lower()))
    
    for snippet in snippets:
        text = snippet.get_text()
        # Look for patterns like "60 Licensed Beds" or "Licensed Beds 60"
        match = re.search(r'(\d+)\s+Licensed\s+Beds', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'Licensed\s+Beds\s+(\d+)', text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # If not found in snippets, try a more general approach with the full text
    full_text = soup.get_text()
    
    # Try different patterns
    patterns = [
        r'(\d+)\s+Licensed\s+Beds',
        r'Licensed\s+Beds\s+(\d+)',
        r'(\d+)\s+beds',
        r'beds\s+(\d+)',
        r'capacity\s+of\s+(\d+)',
        r'(\d+)\s+bed\s+facility'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)
    
    # Last resort: look for any number near "Licensed Beds"
    beds_index = full_text.lower().find("licensed beds")
    if beds_index != -1:
        # Look for numbers in the vicinity (100 chars before and after)
        vicinity = full_text[max(0, beds_index-100):min(len(full_text), beds_index+100)]
        numbers = re.findall(r'\d+', vicinity)
        if numbers:
            # Return the closest number to "Licensed Beds"
            return numbers[0]
    
    return "Unknown"

def search_facility_beds(driver, facility_name, address):
    """Search for a facility's licensed beds and return the result."""
    # Extract city and state from address
    address_parts = address.split(',')
    if len(address_parts) >= 2:
        # Get the last two parts which should be city and state+zip
        location_parts = [part.strip() for part in address_parts[-2:]]
        city_state = ' '.join(location_parts)
    else:
        city_state = address.strip()
    
    # Construct search query and URL
    query = f'site:carelistings.com {facility_name} in {city_state} "Licensed Beds"'
    encoded_query = quote(query)
    search_url = f"https://duckduckgo.com/?q={encoded_query}&t=h_&ia=web"
    
    print(f"Searching for: {facility_name}")
    print(f"Search URL: {search_url}")
    
    # Navigate directly to the search URL
    driver.get(search_url)
    
    # Wait for the page to load
    time.sleep(3)
    
    # Get the page source
    search_results = driver.page_source
    
    # Save the HTML to a file for debugging (optional)
    # safe_name = ''.join(c if c.isalnum() else '_' for c in facility_name)
    # with open(f"result_{safe_name}.html", "w", encoding="utf-8") as f:
    #     f.write(search_results)
    
    # First check if we found the right facility
    if is_matching_facility(search_results, facility_name, address):
        # Extract licensed beds
        licensed_beds = extract_licensed_beds(search_results)
        return licensed_beds
    else:
        return "Unknown"

def process_csv(input_csv, output_csv):
    """Process facilities with Unknown bed counts and write to a new CSV."""
    # Initialize the driver
    driver = setup_driver()
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_csv)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Open input and output files
        with open(input_csv, 'r', encoding='utf-8') as infile, \
             open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            # Process each row
            for i, row in enumerate(reader):
                if i == 0:  # Write header row as is
                    writer.writerow(row)
                    continue
                
                if len(row) < 8:  # Skip incomplete rows
                    print(f"Warning: Row {i+1} is incomplete. Skipping.")
                    writer.writerow(row)  # Write the incomplete row as is
                    continue
                
                facility_name = row[0]
                address = row[1]
                bed_count = row[5]
                
                # Only search for bed count if it's Unknown
                if bed_count.strip() == "Unknown":
                    print(f"Processing {facility_name} (row {i+1})...")
                    
                    # Search for licensed beds
                    licensed_beds = search_facility_beds(driver, facility_name, address)
                    
                    # Update the bed count in the row
                    row[5] = licensed_beds
                    
                    # Print the result
                    print(f"Facility: {facility_name}")
                    print(f"Address: {address}")
                    print(f"Licensed Beds: {licensed_beds}")
                    print("-" * 50)
                    
                    # Be nice to the search engine
                    time.sleep(2)
                else:
                    print(f"Skipping {facility_name} (row {i+1}) - already has bed count: {bed_count}")
                
                # Write the updated row to the output file
                writer.writerow(row)
        
        print(f"Processing complete. Results written to {output_csv}")
    
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    input_csv = "first_30000_facilities.csv"
    output_csv = "updated_facilities_30000.csv"
    
    if not os.path.exists(input_csv):
        print(f"Error: File '{input_csv}' not found.")
        exit(1)
    
    process_csv(input_csv, output_csv)
