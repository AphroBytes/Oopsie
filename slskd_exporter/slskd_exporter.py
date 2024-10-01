import re
import time
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, push_to_gateway

# Configuration
PROMETHEUS_HOST = 'your_prometheus_server'  # Replace with your Prometheus server address
PROMETHEUS_PORT = 9091  # Replace with your Prometheus server port
JOB_NAME = 'slskd_metrics'
LOG_FILE = 'slskd_logs.txt'  # Replace with the path to your SLSKD log file

# Prometheus metrics
registry = CollectorRegistry()
uploads_total = Counter('slskd_uploads_total', 'Total number of uploads', ['status'], registry=registry)
uploads_bytes_total = Counter('slskd_uploads_bytes_total', 'Total bytes uploaded', registry=registry)
uploads_queue_length = Gauge('slskd_uploads_queue_length', 'Current length of uploads queue', registry=registry)
uploads_latency_seconds = Histogram('slskd_uploads_latency_seconds', 'Latency of uploads in seconds', ['status'], registry=registry)
upload_errors_total = Counter('slskd_upload_errors_total', 'Total number of upload errors', ['error_type'], registry=registry)
downloads_total = Counter('slskd_downloads_total', 'Total number of downloads', ['status'], registry=registry)
downloads_bytes_total = Counter('slskd_downloads_bytes_total', 'Total bytes downloaded', registry=registry)
downloads_queue_length = Gauge('slskd_downloads_queue_length', 'Current length of downloads queue', registry=registry)
downloads_latency_seconds = Histogram('slskd_downloads_latency_seconds', 'Latency of downloads in seconds', ['status'], registry=registry)
download_errors_total = Counter('slskd_download_errors_total', 'Total number of download errors', ['error_type'], registry=registry)

# Regex patterns
upload_pattern = re.compile(r'Upload (\w+): ([\w\.-]+) (\d+) bytes, status=(\w+)')
download_pattern = re.compile(r'Download (\w+): ([\w\.-]+) (\d+) bytes, status=(\w+)')
queue_pattern = re.compile(r'Queue length: Uploads=(\d+), Downloads=(\d+)')
latency_pattern = re.compile(r'Latency: (\w+) (\w+) (\d+) seconds')
error_pattern = re.compile(r'Error: (\w+) (\w+) (\w+)')

def process_log_line(line):
    """Parses a log line and updates Prometheus metrics."""
    match = upload_pattern.search(line)
    if match:
        _, _, bytes_uploaded, status = match.groups()
        uploads_total.labels(status=status).inc()
        uploads_bytes_total.inc(int(bytes_uploaded))
        return

    match = download_pattern.search(line)
    if match:
        _, _, bytes_downloaded, status = match.groups()
        downloads_total.labels(status=status).inc()
        downloads_bytes_total.inc(int(bytes_downloaded))
        return

    match = queue_pattern.search(line)
    if match:
        uploads_queue_length.set(int(match.group(1)))
        downloads_queue_length.set(int(match.group(2)))
        return

    match = latency_pattern.search(line)
    if match:
        status, _, latency = match.groups()
        if status == 'Upload':
            uploads_latency_seconds.labels(status=status).observe(float(latency))
        elif status == 'Download':
            downloads_latency_seconds.labels(status=status).observe(float(latency))
        return

    match = error_pattern.search(line)
    if match:
        error_type, _, _ = match.groups()
        if error_type == 'Upload':
            upload_errors_total.labels(error_type=error_type).inc()
        elif error_type == 'Download':
            download_errors_total.labels(error_type=error_type).inc()
        return

def main():
    """Main function to process logs and push metrics to Prometheus."""
    while True:
        try:
            with open(LOG_FILE, "r") as f:
                for line in f:
                    process_log_line(line)
            push_to_gateway(PROMETHEUS_HOST, PROMETHEUS_PORT, job=JOB_NAME, registry=registry)
        except Exception as e:
            print(f"Error processing logs or pushing metrics: {e}")
        time.sleep(1)  # Adjust the sleep interval as needed

if __name__ == '__main__':
    main()