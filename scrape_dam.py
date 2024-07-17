import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from pandasql import sqldf

# Disable SSL warnings (not recommended for production code)
requests.packages.urllib3.disable_warnings()
# Fetch the page content
url = 'https://www.pagasa.dost.gov.ph/flood#dam-information'
response = requests.get(url, verify=False)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the table by class name
table = soup.find('table', {'class': 'table dam-table'})

# Extract headers
headers = ['Dam Name', 'Observation Date', 'Reservoir Water Level (RWL) (m)', 'Water Level Deviation - Hr', 'Water Level Deviation - Amount', 'Normal High Water Level (NHWL) (m)', 'Deviation from NHWL (m)', 'Rule Curve Elevation (m)', 'Deviation from Rule Curve (m)', 'Gates', 'Meters', 'Inflow', 'Outflow']

# Extract rows
data = []
for row in table.find_all('tr'):
    cells = row.find_all(['th', 'td'])
    if len(cells) > 1:  # Check if there are at least 2 cells
        row_data = [cell.text.strip() for cell in cells]
        
        # Check if the row_data contains a time indicator like 'AM' or 'PM'
        if any('AM' in cell or 'PM' in cell for cell in row_data):
            # Find the cell with the time and extract the date from the adjacent cell 
            for i, cell in enumerate(row_data):
                if 'AM' in cell or 'PM' in cell:
                    time = cell
                    # Access the next row for the date
                    next_row = row.find_next_sibling('tr')
                    date_cell = next_row.find('td') if next_row else None
                    date = date_cell.text.strip() if date_cell else None
                    row_data[1] = f"{date}" if date else time  
                    # Combine time with date if available
                    if date:
                        # Concatenate the extracted date with the current year
                        current_year = datetime.now().year
                        full_date_string = f"{date}-{current_year}"
                        # Parse the concatenated date string into a datetime object
                        observation_datetime = datetime.strptime(full_date_string, '%b-%d-%Y')
                        row_data[1] = observation_datetime.strftime('%Y-%m-%d')
                    else:
                        row_data[1] = time
                    break
            
            data.append(row_data[:13])  # Get only the columns up to 'Outflow'

# Create DataFrame
current_data_df = pd.DataFrame(data, columns=headers)


current_date = datetime.now().date()
current_date_str = current_date.strftime('%Y-%m-%d')
current_data_df.to_csv(f'dam_info_{current_date_str}.csv', index=False)



current_q = """
select 
`Observation Date`,
`Dam Name`,
CAST(`Reservoir Water Level (RWL) (m)` as FLOAT) as `Reservoir Water Level (RWL) (m)`
from current_data_df
"""
current_r = sqldf(current_q, globals())



df1 = pd.read_csv('Data Dam Info - Final.csv')

final_df = pd.concat([df1, current_r], ignore_index=True).drop_duplicates()

final_df.to_csv('Data Dam Info - Final.csv', index=False) #save to my current repo
print(final_df.tail())


final_df.to_csv('Data Dam Info - Final.csv', index=False) #save to my workspace dir as backup
