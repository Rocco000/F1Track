import csv
from datetime import datetime


input_file = 'F1TrackDBRaces.csv'
output_file = 'Races.csv'

# Open the input CSV file for reading and the output CSV file for writing
with open("./preprocessingData/"+input_file, 'r') as input_csv, open("./preprocessingData/"+output_file, 'w', newline='') as output_csv:
    reader = csv.DictReader(input_csv)
    writer = csv.DictWriter(output_csv, fieldnames=reader.fieldnames)
    
    # Write the header row to the output CSV file
    writer.writeheader()
    
    for row in reader:
        datetime_str = row['date'] 
    
        # Convert the datetime string to a datetime object
        datetime_obj = datetime.fromisoformat(datetime_str)
        
        # Extract only the date part
        date_only = datetime_obj.date()
        
        # Convert the date to a string in the desired format
        date_str = date_only.isoformat()
        
        # Update the value in the row with the extracted date
        row['date'] = date_str
        
        # Write the updated row to the output CSV file
        writer.writerow(row)

print("CSV file processed successfully.")
