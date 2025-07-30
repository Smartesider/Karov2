#!/bin/bash

# 🧷 Backend monitoring script for JuridiskPorten
# Checks if FastAPI server is running on port 8095 and restarts if needed
# Sends email alerts to terje@trollhagen.no if failures occur

DOMAIN="skycode.no"
PORT_FILE="/home/${DOMAIN}/port.txt"
APP_DIR="/home/${DOMAIN}/karo"
LOG_FILE="${APP_DIR}/monitor.log"
PID_FILE="${APP_DIR}/app.pid"
ALERT_EMAIL="terje@trollhagen.no"
MAX_RESTART_ATTEMPTS=3
RESTART_COUNT_FILE="${APP_DIR}/restart_count.txt"

# Read port from file
# 🧷 Dette skal være en fetch til FastAPI på portnummer du finner under home/{domene}/port.txt, som svarer med JSON
if [ -f "$PORT_FILE" ]; then
    PORT=$(cat "$PORT_FILE")
else
    echo "$(date): ERROR - Port file not found: $PORT_FILE" >> "$LOG_FILE"
    exit 1
fi

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

# Function to send email alert
send_alert() {
    local subject="$1"
    local message="$2"
    
    # Create email content
    cat << EOF > /tmp/alert_email.txt
To: $ALERT_EMAIL
Subject: [ALERT] JuridiskPorten Backend - $subject

$message

Server: $(hostname)
Time: $(date)
Domain: $DOMAIN
Port: $PORT

This is an automated alert from the JuridiskPorten monitoring system.
EOF

    # Send email using sendmail (if available) or mail command
    if command -v sendmail >/dev/null 2>&1; then
        sendmail "$ALERT_EMAIL" < /tmp/alert_email.txt
    elif command -v mail >/dev/null 2>&1; then
        mail -s "[ALERT] JuridiskPorten Backend - $subject" "$ALERT_EMAIL" < /tmp/alert_email.txt
    else
        log_message "WARNING: No email system available to send alert"
    fi
    
    rm -f /tmp/alert_email.txt
}

# Function to check if backend is responding
check_backend() {
    # Test HTTP endpoint locally (backend runs on localhost:PORT)
    if curl -s -f "http://localhost:${PORT}/health" >/dev/null 2>&1; then
        # Also check external accessibility (what users actually access)
        if curl -s -f "http://${DOMAIN}:${PORT}/health" >/dev/null 2>&1; then
            return 0
        else
            log_message "WARNING: Backend responds locally but not externally on ${DOMAIN}:${PORT}"
            return 1
        fi
    else
        return 1
    fi
}

# Function to check if process is running
check_process() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to start backend
start_backend() {
    log_message "Starting FastAPI backend..."
    
    cd "$APP_DIR"
    # 🧷 Kun MariaDB skal brukes – ingen andre drivere!
    nohup python3 app.py > app.log 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment for startup
    sleep 5
    
    if check_backend; then
        log_message "Backend started successfully (PID: $pid)"
        # Reset restart count on successful start
        echo "0" > "$RESTART_COUNT_FILE"
        return 0
    else
        log_message "ERROR: Backend failed to start properly"
        return 1
    fi
}

# Function to stop backend
stop_backend() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" >/dev/null 2>&1; then
            kill "$pid"
            sleep 3
            if ps -p "$pid" >/dev/null 2>&1; then
                kill -9 "$pid"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Kill any remaining python processes running app.py
    pkill -f "python3 app.py" >/dev/null 2>&1
}

# Main monitoring logic
main() {
    log_message "Backend monitor started"
    
    # Initialize restart count if doesn't exist
    if [ ! -f "$RESTART_COUNT_FILE" ]; then
        echo "0" > "$RESTART_COUNT_FILE"
    fi
    
    local restart_count=$(cat "$RESTART_COUNT_FILE")
    
    # Check if backend is responding
    if check_backend; then
        log_message "Backend is healthy and responding"
        exit 0
    fi
    
    log_message "Backend is not responding - attempting recovery"
    
    # Check restart count
    if [ "$restart_count" -ge "$MAX_RESTART_ATTEMPTS" ]; then
        log_message "CRITICAL: Maximum restart attempts ($MAX_RESTART_ATTEMPTS) exceeded"
        send_alert "CRITICAL FAILURE" "Backend has failed $MAX_RESTART_ATTEMPTS times and cannot be automatically restarted. Manual intervention required."
        exit 1
    fi
    
    # Increment restart count
    restart_count=$((restart_count + 1))
    echo "$restart_count" > "$RESTART_COUNT_FILE"
    
    log_message "Restart attempt $restart_count of $MAX_RESTART_ATTEMPTS"
    
    # Stop any existing backend processes
    stop_backend
    
    # Start backend
    if start_backend; then
        log_message "Backend recovery successful"
        send_alert "Backend Recovered" "Backend was down but has been successfully restarted (attempt $restart_count/$MAX_RESTART_ATTEMPTS)"
    else
        log_message "Backend recovery failed"
        if [ "$restart_count" -ge "$MAX_RESTART_ATTEMPTS" ]; then
            send_alert "CRITICAL FAILURE" "Backend recovery failed after $MAX_RESTART_ATTEMPTS attempts. Manual intervention required."
        else
            send_alert "Backend Restart Failed" "Backend restart attempt $restart_count failed. Will try again on next monitoring cycle."
        fi
        exit 1
    fi
}

# Run main function
main "$@"
