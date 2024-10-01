# SLSKD Metrics Collector

Welcome to the SLSKD Metrics Collector! This nifty Python script helps you gather and push metrics related to uploads and downloads from your log files to your Prometheus server. If that sounds like something you'd enjoy (and it absolutely should!), keep reading to understand how it works and how you can set it up.

## Overview

The primary aim of this script is to parse log entries from a specified log file, extract relevant data, and send that data to a Prometheus server for monitoring. It handles metrics related to uploads, downloads, queue lengths, latencies, and errors. 

### Features:
- **Automatic Metric Collection**: Every time a relevant log line is read, corresponding metrics are reported.
- **Robust Error Handling**: The script catches and logs errors during log processing and metrics pushing.
- **Customizable Configurations**: Adjust the Prometheus server address, port, and log file path to suit your needs.

## Getting Started

### Prerequisites

Before you jump into using this script, you need to ensure that you have the following items in place:

1. **Python 3.6+**: Make sure you have Python installed on your machine.
2. **Prometheus Client Library**: You'll need the Prometheus client library. Install it with:
    ```bash
    pip install prometheus_client
    ```
3. **A Prometheus Server**: You need access to a running Prometheus server where you can push your metrics.

### Configuration

The script comes with a set of configurable parameters at the top, which you can modify according to your setup. Here's a rundown:

```python
PROMETHEUS_HOST = 'your_prometheus_server'  # Replace with your Prometheus server address
PROMETHEUS_PORT = 9091                      # The default port for Prometheus push gateway
JOB_NAME = 'slskd_metrics'                   # The name of your job in Prometheus
LOG_FILE = 'slskd_logs.txt'                  # Path to your SLSKD log file
```
Make sure to replace the `PROMETHEUS_HOST` and `LOG_FILE` values with your specific configurations.

### Metric Types Explained

The script uses different types of Prometheus metrics to monitor various aspects:

1. **Counter**: A metric that only increases over time. Used for counting uploads, downloads, and errors.
2. **Gauge**: A metric that can decrease or increase. Used for measuring the current length of the upload and download queues.
3. **Histogram**: Used to observe the distribution of latencies for uploads and downloads.

### Regex Patterns

The script utilizes regular expressions (regex) to capture specific data from the log file. Here are the key patterns:
- **Uploads**: Captures the upload status and size.
- **Downloads**: Captures the download status and size.
- **Queue Lengths**: Captures the current queue length for uploads and downloads.
- **Latenices**: Captures the latency time for uploads and downloads.
- **Errors**: Captures error types for further analysis.

### Function Breakdown

- `process_log_line(line)`: This function processes each line from the log file. It checks for matches against predefined regex patterns and updates the corresponding Prometheus metrics accordingly.
  
- `main()`: The heart of the script runs in an infinite loop, continually reading the log file, processing its lines, and pushing the collected metrics to the Prometheus server. In case of any errors (e.g., file not found, connection issues), it gracefully handles exceptions and prints error messages.

### Running the Script

1. **Open a terminal**.
2. **Navigate** to the directory where your script is saved.
3. **Run the script** using:
    ```bash
    python slskd_metrics_collector.py
    ```

### Tips for Successful Running

- Ensure that the log file path is correct, and the log file is being written to concurrently.
- Check that your Prometheus server is up and properly configured to receive these metrics.
- Adjust the log file reading interval in the `time.sleep(1)` line if you have a very active log file.

### Monitoring Your Metrics

Once the script is up and running, you can visit your Prometheus server's UI to view the metrics it has been collecting. You can start creating dashboards, making alerts, or simply enjoying watching the numbers go up (or down) based on your log activity.

## Conclusion

And there you have it! You're now equipped with a powerful little tool to keep an eye on your SLSKD processes using Prometheus metrics. Feel free to modify the script further or enhance it with new features as per your requirements. Happy tracking!

If it breaks anything, we are not liable. You accept this by using the code.