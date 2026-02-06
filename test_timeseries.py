import datetime
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import database

today = datetime.date.today()
start_of_year = datetime.date(today.year, 1, 1)

print("Testing get_new_customers_timeseries from " + str(start_of_year) + " to " + str(today))

try:
    ts_data_daily = database.get_new_customers_timeseries(start_of_year, today, period='D')
    print("\nDaily Time Series Data:")
    print(ts_data_daily.to_string()) # Use to_string() for full DataFrame display

    ts_data_monthly = database.get_new_customers_timeseries(start_of_year, today, period='M')
    print("\nMonthly Time Series Data:")
    print(ts_data_monthly.to_string())

    ts_data_weekly = database.get_new_customers_timeseries(start_of_year, today, period='W')
    print("\nWeekly Time Series Data:")
    print(ts_data_weekly.to_string())

except database.DatabaseError as e:
    print("Error fetching time series data: " + str(e))
except Exception as e:
    print("An unexpected error occurred: " + str(e))