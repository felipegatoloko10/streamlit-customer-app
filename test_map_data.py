import datetime
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import database

today = datetime.date.today()
start_of_year = datetime.date(today.year, 1, 1)

print("Testing get_customers_by_state_for_map from " + str(start_of_year) + " to " + str(today))

try:
    map_data = database.get_customers_by_state_for_map(start_of_year, today)
    print("\nMap Data (Customers by State):")
    print(map_data.to_string())

except database.DatabaseError as e:
    print("Error fetching map data: " + str(e))
except Exception as e:
    print("An unexpected error occurred: " + str(e))