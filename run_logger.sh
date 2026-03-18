#!/bin/bash
# Shell script to run the timestamp logger in the background
# This allows the script to continue running even when you log out

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/log_timestamp.py"
LOG_OUTPUT="$SCRIPT_DIR/logger_output.log"

# Run the Python script in background with nohup so it survives logout
nohup python3 "$PYTHON_SCRIPT" > "$LOG_OUTPUT" 2>&1 &

# Capture the PID
PID=$!

echo "Logger started with PID: $PID"
echo "Script: $PYTHON_SCRIPT"
echo "Output: $LOG_OUTPUT"
