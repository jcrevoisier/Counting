import csv
import sys

def extract_first_n_rows(input_file, output_file, n=10000):
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            
            # Read the header row
            header = next(reader)
            
            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile)
                
                # Write the header row to the output file
                writer.writerow(header)
                
                # Write the first n rows to the output file
                count = 0
                for row in reader:
                    writer.writerow(row)
                    count += 1
                    if count >= n:
                        break
                
                print(f"Successfully extracted {count} rows (plus header) to {output_file}")
                if count < n:
                    print(f"Note: The input file only contained {count} rows of data (plus header)")
    
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_first_10000.py <input_csv_file> <output_csv_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        extract_first_n_rows(input_file, output_file)
