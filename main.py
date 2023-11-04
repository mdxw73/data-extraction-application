import pandas as pd
import subprocess
import sys
import streamlit as st
import time

import os
from glob import glob
from datetime import datetime
import re

log_directory = '.'  # Replace with your log directory

# Get a list of log files in the directory
log_files = glob(os.path.join(log_directory, 'qrt_data_extraction_analysis_*.log'))

# Find the most recent log file based on the timestamp in the filename
most_recent_log = max(log_files, key=os.path.getctime)

# Set the path to your log file
LOG_FILE_PATH = most_recent_log

# Create an empty DataFrame with your desired column names
columns = ['Timestamp', 'Log Level', 'Message']
df = pd.DataFrame(columns=columns)

# set graph placeholder
placeholder = st.empty()

def update_log_file():
    # Read the last 10 lines from the log file
    output = subprocess.check_output(['tail', '-n', '10', LOG_FILE_PATH], universal_newlines=True)

    # Update the DataFrame for each line
    for log_entry in output.splitlines():
        update_dataframe(log_entry)

def update_dataframe(log_entry):
    # Parse the log entry and update the DataFrame accordingly
    pattern = re.compile(r'(?P<timestamp>\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}.\d{9}) (?P<log_level>\w+): (?P<message>.+)')
    match = pattern.match(log_entry)

    if match:
        timestamp = match.group('timestamp')
        log_level = match.group('log_level')
        message = match.group('message')
        
        # Update the DataFrame
        df.loc[len(df)] = [timestamp, log_level, message]

def plot_graph():
    # Ensure 'Timestamp' column is of type datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Set 'Timestamp' as the index in a copy of the DataFrame
    df_copy = df.set_index('Timestamp').copy()

    # Create a new DataFrame for plotting (resample data to get counts per minute)
    plot_df = df_copy.resample('1T').size().reset_index(name='Count')

    # Plot the graph
    placeholder.line_chart(plot_df.set_index('Timestamp'))

if __name__ == "__main__":
    try:
        with open(LOG_FILE_PATH) as file:
            while True:
                where = file.tell()
                lines = file.readlines()
                if not lines:
                    time.sleep(1)
                    file.seek(where)
                else:
                    for line in lines:
                        update_dataframe(line)
                    plot_graph()
                print(len(df))
    except KeyboardInterrupt:
        pass