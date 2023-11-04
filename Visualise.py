import streamlit as st
from glob import glob
import os
from log_helper_module import LogHelper

log_directory = '.'  # Replace with your log directory
log_files = glob(os.path.join(log_directory, 'qrt_data_extraction_analysis_*.log')) # Get a list of log files in the directory
# most_recent_log = max(log_files, key=os.path.getctime) # Find the most recent log file based on the timestamp in the filename

st.markdown(f"### Visualise Log Files")
selected_log_files = st.multiselect("Select log files", log_files)
selected_chart = st.radio("Select a chart:", ["bar", "line"])
log_helper = LogHelper(selected_log_files, selected_chart)
live_track_button = st.empty()

if live_track_button.button("Live Track", disabled=len(selected_log_files)==0):
    if live_track_button.button("Stop Live Track"):
        log_helper.is_live = False
    log_helper.is_live = True
    log_helper.live_track(log_helper.plot_graph)