#!/usr/bin/env python3
"""
Dummy script that logs timestamps every 10 minutes to a text file.
Useful for testing background script execution workflows.
"""

import time
import datetime
from pathlib import Path

# Log file location
log_file = Path(__file__).parent / "timestamp_log.txt"

def log_timestamp():
    """Append current timestamp to log file."""
    timestamp = datetime.datetime.now().isoformat()
    with open(log_file, "a") as f:
        f.write(f"{timestamp}\n")
    print(f"Logged: {timestamp}")

def main():
    """Run logging loop every 10 minutes."""
    print(f"Starting timestamp logger. Logging to: {log_file}")
    
    # Log initial startup
    log_timestamp()
    
    # Loop every 10 minutes (600 seconds)
    interval = 10 * 60  # 600 seconds = 10 minutes
    
    try:
        while True:
            time.sleep(interval)
            log_timestamp()
    except KeyboardInterrupt:
        print("\nLogger stopped.")

if __name__ == "__main__":
    main()
