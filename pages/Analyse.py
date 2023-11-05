import streamlit as st
from glob import glob
import os
from log_helper_module import LogHelper
from datetime import timedelta

log_directory = '.'  # Replace with your log directory
log_files = glob(os.path.join(log_directory, 'qrt_data_extraction_analysis_*.log')) # Get a list of log files in the directory
# most_recent_log = max(log_files, key=os.path.getctime) # Find the most recent log file based on the timestamp in the filename

st.subheader("Analyse Log Files")
selected_log_files = st.multiselect("Select log files", log_files)

filters_col1, filters_col2 = st.columns(2)
with filters_col1:
    selected_filter = st.radio("Select a filter:", ["none", "numeric", "datetime", "custom regex"])
    if selected_filter == "custom regex":
        regex_pattern = st.text_input("Enter regex pattern:")
    else:
        regex_pattern = ""
with filters_col2:
    selected_highlighting = st.radio("Highlight filtered expression?", ["no", "yes"])

start_date, start_time, end_date, end_time = None, None, None, None
if selected_filter == "datetime":
    col1, col2, col3, col4 = st.columns(4)
    start_date = col1.date_input("Select start date")
    start_time = col2.time_input("Select start time", step=timedelta(minutes=1))
    end_date = col3.date_input("Select end date")
    end_time = col4.time_input("Select end time", step=timedelta(minutes=1))

log_helper = LogHelper(selected_log_files, selected_filter=selected_filter, start_date=start_date, start_time=start_time, end_date=end_date, end_time=end_time, selected_highlighting=selected_highlighting, regex_pattern=regex_pattern)
live_track_button = st.empty()

if live_track_button.button("Live Track", disabled=len(selected_log_files)==0):
    if live_track_button.button("Stop Live Track"):
        log_helper.is_live = False
    log_helper.is_live = True
    log_helper.live_track(log_helper.show_filtered_dataframe)