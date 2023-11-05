# MacOS executable setup: chmod +x qrt_data_extraction-MacOS

import pandas as pd
import subprocess
import streamlit as st
import time
import re
import threading
from queue import Queue
from bs4 import BeautifulSoup
from datetime import timedelta

class LogHelper:
    def __init__(self, selected_log_files, selected_chart="bar", selected_filter="none", start_date=None, start_time=None, end_date=None, end_time=None, selected_highlighting = "no", regex_pattern = "", log_level="DEBUG"):
        self.is_live = False
        self.tasks = Queue()
        # most_recent_log = max(log_files, key=os.path.getctime) # Find the most recent log file based on the timestamp in the filename
        # LOG_FILE_PATH = most_recent_log # Set the path to your log file

        self.selected_log_files = selected_log_files
        self.selected_chart = selected_chart
        self.selected_filter = selected_filter
        self.log_level = log_level
        
        self.start_date = start_date
        self.start_time = start_time
        self.end_date = end_date
        self.end_time = end_time

        self.selected_highlighting = selected_highlighting
        self.regex_pattern = regex_pattern
        
        self.columns = ['Timestamp', 'Log Level', 'Message']
        self.dfs = []
        self.placeholders = []

        self.alerts_placeholder = None
        self.alerts = []
        self.lock = threading.Lock()

        self.statistics = pd.DataFrame(columns=["Exchange", "Order", "recv_nu", "us"])
        self.statistics_placeholder = None

    def plot_graph(self, index):
        if self.selected_chart == "bar":
            self.plot_barchart(index)
        elif self.selected_chart == "line":
            self.plot_linechart(index)
        elif self.selected_chart == "multi":
            self.plot_multi_linechart(index)
        else:
            raise(Exception("Unknown graph"))

    def plot_linechart(self, index):
        # Ensure 'Timestamp' column is of type datetime
        self.dfs[index]['Timestamp'] = pd.to_datetime(self.dfs[index]['Timestamp'])
        # Set 'Timestamp' as the index in a copy of the DataFrame
        df_copy = self.dfs[index].set_index('Timestamp').copy()
        # Create a new DataFrame for plotting (resample data to get counts per minute)
        plot_df = df_copy.resample('1T').size().reset_index(name='Count')
        # Plot the graph
        with self.placeholders[index].container():
            st.markdown(f"**File:** *{self.selected_log_files[index]}*")
            st.line_chart(plot_df, x='Timestamp', y='Count')

    def plot_barchart(self, index):
        df = self.dfs[index]
        log_level_frequencies = df['Log Level'].value_counts().reset_index(name='Count')
        with self.placeholders[index].container():
            st.markdown(f"**File:** *{self.selected_log_files[index]}*")
            st.bar_chart(log_level_frequencies, x='Log Level', y='Count')

    def plot_multi_linechart(self, index):
        # Ensure 'Timestamp' column is of type datetime
        self.dfs[index]['Timestamp'] = pd.to_datetime(self.dfs[index]['Timestamp'])
        # Set 'Timestamp' as the index in a copy of the DataFrame
        df_copy = self.dfs[index].set_index('Timestamp').copy()
        
        # Create a new DataFrame for plotting (group by log level and resample data to get counts per minute)
        plot_df = df_copy.groupby('Log Level').resample('1T').size().reset_index(name='Count')
        
        # Plot the graph
        with self.placeholders[index].container():
            st.markdown(f"**File:** *{self.selected_log_files[index]}*")
            st.line_chart(plot_df, x='Timestamp', y='Count', color='Log Level')

    def show_dataframe(self, index):
        # Ensure 'Timestamp' column is of type datetime
        self.dfs[index]['Timestamp'] = pd.to_datetime(self.dfs[index]['Timestamp'])
        # Set 'Timestamp' as the index in a copy of the DataFrame
        df_copy = self.dfs[index].set_index('Timestamp').copy()
        with self.placeholders[index].container():
            st.markdown(f"**File:** *{self.selected_log_files[index]}*")
            st.dataframe(df_copy)

    def contains_custom_regex(self, text):
        matches = re.findall(self.regex_pattern, text)
        return bool(matches)

    def filter_df_custom(self, original_df):
        original_df['ContainsCustomRegex'] = original_df['Message'].apply(self.contains_custom_regex)
        filtered_df = original_df[original_df['ContainsCustomRegex']]
        filtered_df = filtered_df[["Timestamp", "Log Level", "Message"]]
        return filtered_df

    def show_custom_filtered_dataframe(self, index):
        if self.selected_filter == "log level":
            filtered_df = self.dfs[index][self.dfs[index]['Log Level'] == self.log_level].copy()
        else:
            filtered_df = self.filter_df_custom(self.dfs[index].copy())
        
        if self.selected_highlighting == "yes":
            for rowindex, row in filtered_df.iterrows():
                filtered_df.at[rowindex, 'Message'] = self.highlight_text_with_beautiful_soup(row['Message'])
            with self.placeholders[index].container():
                st.markdown(f"**File:** *{self.selected_log_files[index]}*")
                st.write(filtered_df.to_html(index=False, escape=False), unsafe_allow_html=True)
        else:
            with self.placeholders[index].container():
                st.markdown(f"**File:** *{self.selected_log_files[index]}*")
                st.dataframe(filtered_df.set_index('Timestamp'))

    def highlight_text_with_beautiful_soup(self, text):
        soup = BeautifulSoup(text, 'html.parser')
        
        def highlight_match(match):
            return f"<span style='background-color: yellow'>{match.group()}</span>"
        
        for text_node in soup.find_all(text=True):
            text_node.replace_with(re.sub(self.regex_pattern, highlight_match, str(text_node)))
        
        return soup

    def show_datetime_filtered_dataframe(self, index):
        # Ensure 'Timestamp' column is of type datetime
        self.dfs[index]['Timestamp'] = pd.to_datetime(self.dfs[index]['Timestamp'], format="%d-%m-%Y %H:%M:%S.%f")
        # Set 'Timestamp' as the index in a copy of the DataFrame
        df_copy = self.dfs[index].set_index('Timestamp').copy()

        # Filter by date and time
        if self.start_date and self.start_time:
            start_datetime = pd.to_datetime(f"{self.start_date} {self.start_time}")
            df_copy = df_copy[df_copy.index >= start_datetime]

        if self.end_date and self.end_time:
            end_datetime = pd.to_datetime(f"{self.end_date} {self.end_time}")
            df_copy = df_copy[df_copy.index <= end_datetime]

        latency = df_copy.index.to_series().diff().dt.total_seconds().dropna()

        # Display the filtered DataFrame
        with self.placeholders[index].container():
            col1, col2 = st.columns([4,1])
            with col1.container():
                st.markdown(f"**File:** *{self.selected_log_files[index]}*")
                st.dataframe(df_copy)
            with col2.container():
                st.write("Latency statistics:")
                st.write(latency.describe())

    def show_filtered_dataframe(self, index):
        if self.selected_filter == "none":
            self.show_dataframe(index)
        elif self.selected_filter == "numeric":
            self.regex_pattern = r'\d+|zero|one|two|three|four|five|six|seven|eight|nine'
            self.show_custom_filtered_dataframe(index)
        elif self.selected_filter == "datetime":
            self.show_datetime_filtered_dataframe(index)
        elif self.selected_filter == "custom regex" or self.selected_filter == "log level":
            self.show_custom_filtered_dataframe(index)
        else:
            raise(Exception("Unknown filter"))
        
    def update_dataframe(self, log_entry, index):
        # Parse the log entry and update the DataFrame accordingly
        pattern = re.compile(r'(?P<timestamp>\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}.\d{7}|\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}.\d{9}) (?P<log_level>\w+): (?P<message>.+)')
        match = pattern.match(log_entry)

        if match:
            timestamp = match.group('timestamp')
            log_level = match.group('log_level')
            message = match.group('message')

            if log_level == "WARN":
                self.lock.acquire()
                self.alerts.append(f"{log_level}: {message}")
                if len(self.alerts) > 20:
                    self.alerts.pop(0)
                self.lock.release()
            if len(self.dfs[index]) > 0:
                latency = pd.to_datetime(timestamp) - pd.to_datetime(self.dfs[index]["Timestamp"].iloc[-1])
                if latency > timedelta(seconds=2):
                    self.lock.acquire()
                    self.alerts.append(f"LATENCY: latency exceeded threshold ({latency.total_seconds()})")
                    if len(self.alerts) > 20:
                        self.alerts.pop(0)
                    self.lock.release()
            
            # Update the DataFrame
            self.dfs[index].loc[len(self.dfs[index])] = [timestamp, log_level, message]

    def update_statistics(self, log_entry):
        ["Exchange", "Order", "recv", "nu", "(us)"]
        # Parse the log entry and update the DataFrame accordingly
        pattern = re.compile(r'\s*(?P<exchange>\w+)\s+(?P<order>\w+)\s+(?P<recv_nu>\d+)\s+(?P<us>\d+)\s*')
        match = pattern.match(log_entry)

        if match:
            exchange = match.group('exchange')
            order = match.group('order')
            recv_nu = match.group('recv_nu')
            us = match.group('us')
            
            # Update the DataFrame
            self.statistics.loc[len(self.statistics)] = [exchange, order, recv_nu, us]

    def run_thread(self, index, log_file, stop_event):
        try:
            with open(log_file) as file:
                while not stop_event.is_set():
                    where = file.tell()
                    lines = file.readlines()
                    if not lines:
                        time.sleep(1)
                        file.seek(where)
                    else:
                        for i in range(len(lines)):
                            if lines[i] == "Exchange order message timing output\n":
                                self.statistics = pd.DataFrame(columns=["Exchange", "Order", "recv_nu", "us"])
                                while lines[i] != "\n":
                                    i += 1 # skip first empty line
                                    self.update_statistics(lines[i])
                            self.update_dataframe(lines[i], index)
                        if index not in self.tasks.queue:
                            self.tasks.put(index)
        except KeyboardInterrupt:
            pass

    def live_track(self, closure):
        # Create a separate thread for each log file
        threads = []
        stop_events = []
        for index, log_file in enumerate(self.selected_log_files):
            self.dfs.append(pd.DataFrame(columns=self.columns))
            self.placeholders.append(st.empty())
            stop_event = threading.Event()
            stop_events.append(stop_event)
            thread = threading.Thread(target=self.run_thread, args=(index, log_file, stop_event,))
            threads.append(thread)
            thread.start()

        st.subheader("Statistics")
        st.write("Most recent:")
        self.statistics_placeholder = st.empty()

        st.subheader("Alerts")
        st.write("Most recent:")
        self.alerts_placeholder = st.empty()
        
        try:
            print("Live track started")
            while self.is_live:
                if self.tasks.qsize() > 0:
                    next_task = self.tasks.get()
                    print('Executing update {} on main thread'.format(next_task))
                    closure(next_task)
                else:
                    if len(self.statistics):
                        statistics = self.statistics.copy()
                        statistics.columns = ['Exchange', 'Order', 'Messages', 'Latency']
                        with self.statistics_placeholder.container():
                            col1, col2 = st.columns(2)
                            col1.bar_chart(statistics, x='Order', y='Messages', color='Exchange')
                            col2.bar_chart(statistics, x='Order', y='Latency', color='Exchange')
                            st.dataframe(self.statistics.set_index(['Exchange', 'Order']), use_container_width=True)
                    if self.alerts:
                        with self.alerts_placeholder.container():
                            self.lock.acquire()
                            for alert in reversed(self.alerts):
                                st.warning(alert)
                            self.lock.release()
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            # Set stop events to stop the threads
            for stop_event in stop_events:
                stop_event.set()

            # Wait for all threads to finish
            for thread in threads:
                thread.join()
            print("Live track stopped")