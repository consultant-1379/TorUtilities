#!/usr/bin/env bash

SERVICE=$1
ENABLE_FILE="/home/enmutils/.wl_service_enable"
INSTALL_RUNNING="/home/enmutils/.install_running"
MAX_RETRIES=3

if [[ $# -ne 1 ]]; then
    /bin/logger "Illegal number of arguments, exiting script."
    exit 2
fi

if [ -f $INSTALL_RUNNING ] || [ ! -f $ENABLE_FILE ]
then
    /bin/logger "TORUTILS: Service(s) may not be installed or enabled, no restart will be attempted."
    exit 0
fi

soa_services=("nodemanager" "usermanager" "deploymentinfomanager" "profilemanager")
if [[ " ${soa_services[@]} " =~ " $SERVICE " ]]; then
    # Attempt to check service status and restart up to MAX_RETRIES times
    for ((i = 1; i <= MAX_RETRIES; i++)); do
        status_output=$(/sbin/service "$SERVICE" status)
        if [[ $status_output == *"is running"* ]]; then
            echo "$SERVICE is already running."
            break
        else
            # Check if the process is running and terminate it
            if [[ $status_output == *"Process running for $SERVICE service with PID:"* ]]; then
                echo "Process is running and $SERVICE is not running."
                pid_value=$(awk '/Process running for '"$SERVICE"' service with PID:/ {print $NF}' <<< "$status_output")
                echo "Killing process with PID: $pid_value"
                kill -9 "$pid_value"
                sleep 30
            fi
            echo "Restarting $SERVICE... (attempt $i)"
            /sbin/service "$SERVICE" restart
            sleep 60  # Wait for the service to restart
        fi
    done
else
  /sbin/service "$SERVICE" status
  if [ $? -ne 0 ]; then
    /bin/logger "TORUTILS: $SERVICE is not currently started, attempting to restart service."
    /sbin/service "$SERVICE" restart
  fi
fi