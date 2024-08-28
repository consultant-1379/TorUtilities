#!/bin/bash

USAGE="Usage: $0 SERVICE_NAME {start|stop|status|restart}"

BIN_DIR="/opt/ericsson/enmutils/bin"
LOG_DIR="/home/enmutils/services"
BASHRC="/root/.bashrc"
LITP_BIN="/usr/bin/litp"

SERVICE=$1
ACTION=$2

[[ -z ${SERVICE} ]] && { echo "${USAGE}"; exit 2; }

WL_SERVICE_ENABLE_FLAG_FILE="/home/enmutils/.wl_service_enable"
if [[ ! -f ${WL_SERVICE_ENABLE_FLAG_FILE} ]]
then
    echo "Workload services not enabled - (${WL_SERVICE_ENABLE_FLAG_FILE} does not exist)"
    exit 1
fi
[[ -f ${BASHRC} ]] && source ${BASHRC}

SERVICE_PID=$(pgrep -f "${SERVICE} ${SERVICE}")
SERVICE_CONSOLE_LOGFILE="${LOG_DIR}/${SERVICE}.log.console"
touch "${SERVICE_CONSOLE_LOGFILE}"

case "${ACTION}" in
    start)
        [[ ! -z "${SERVICE_PID}" ]] && { echo "Service already running"; exit 1; }

        MESSAGE="Starting workload service ${SERVICE}"
        echo "${MESSAGE}"
        logger "TORUTILS: ${MESSAGE}"
        echo "$(date +"%Y-%m-%d %H:%M:%S") ${MESSAGE}" >> "${SERVICE_CONSOLE_LOGFILE}"

        nohup "${BIN_DIR}/services/${SERVICE}" "${SERVICE}" >> "${SERVICE_CONSOLE_LOGFILE}" 2>&1 &
        ;;
    stop)
        [[ -z "${SERVICE_PID}" ]] && { echo "Service already stopped"; exit 1; }

        MESSAGE="Stopping workload service ${SERVICE}"
        echo "${MESSAGE}"
        logger "TORUTILS: ${MESSAGE}"
        echo "$(date +"%Y-%m-%d %H:%M:%S") ${MESSAGE}" >> "${SERVICE_CONSOLE_LOGFILE}"

        pkill -f "${SERVICE} ${SERVICE}"
        ;;
    restart)
        $0 "${SERVICE}" stop
        sleep 2
        $0 "${SERVICE}" start
        ;;
    status)
        [[ -z "${SERVICE_PID}" ]] && { echo "Process not running for ${SERVICE} service - check logs in ${LOG_DIR}"; exit 1; }
        echo "Process running for ${SERVICE} service with PID: ${SERVICE_PID}"
        echo "Checking that webserver is available..."
        ${BIN_DIR}/services/${SERVICE} "${SERVICE}" status
        exit $?
        ;;
    *)
        echo "${USAGE}"
        exit 2
esac
