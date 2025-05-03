import csv
import re

def analyze_beds_data(csv_file):
    numeric_beds_count = 0
    unknown_beds_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)  # Skip header row
        
        # Find the index of the "Number of beds estimated" column
        beds_index = headers.index("Number of beds estimated") if "Number of beds estimated" in headers else -1
        
        if beds_index == -1:
            print("Error: Could not find 'Number of beds estimated' column in the CSV file.")
            return
        
        for row in reader:
            if beds_index < len(row):
                bed_value = row[beds_index].strip()
                
                # Check if the value is "Unknown"
                if bed_value == "Unknown":
                    unknown_beds_count += 1
                # Check if the value is a number
                elif re.match(r'^\d+$', bed_value):
                    numeric_beds_count += 1
                # Handle empty values or other non-numeric values
                else:
                    print(f"Note: Found non-numeric, non-Unknown value: '{bed_value}'")
    
    print(f"Facilities with numeric bed counts: {numeric_beds_count}")
    print(f"Facilities with 'Unknown' bed counts: {unknown_beds_count}")
    print(f"Total facilities analyzed: {numeric_beds_count + unknown_beds_count}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python analyze_beds.py <csv_file_path>")
    else:
        analyze_beds_data(sys.argv[1])
