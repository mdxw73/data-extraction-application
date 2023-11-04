import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
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

class LogFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Check if the modified file is the log file
        if event.src_path == LOG_FILE_PATH:
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
        timestamp_str = match.group('timestamp')
        log_level = match.group('log_level')
        message = match.group('message')
        
        # Convert timestamp string to a datetime object
        print(timestamp_str)
        
        # Update the DataFrame
        df.loc[len(df)] = [timestamp_str, log_level, message]

def plot_graph():
    # Ensure 'Timestamp' column is of type datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Set 'Timestamp' as the index
    df.set_index('Timestamp', inplace=True)

    # Create a new DataFrame for plotting (resample data to get counts per minute)
    plot_df = df.resample('1T').size().reset_index(name='Count')

    # Plot the graph
    st.line_chart(plot_df.set_index('Timestamp'))

if __name__ == "__main__":
    # Update dataframe
    log_content = []
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'r') as log_file:
            log_content = log_file.readlines()

    for log_entry in log_content:
        update_dataframe(log_entry)
    
    st.dataframe(df)

    # # Set up the watchdog observer and handler
    # event_handler = LogFileHandler()
    # observer = Observer()
    # observer.schedule(event_handler, path='.', recursive=False)
    # observer.start()

    # try:
    #     while True:
    #         # This loop will keep the script running
    #         print(df)
    #         plot_graph()
    #         time.sleep(60)  # Update every minute
    # except KeyboardInterrupt:
    #     observer.stop()

    # observer.join()