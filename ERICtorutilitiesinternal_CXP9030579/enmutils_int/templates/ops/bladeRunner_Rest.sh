#!/bin/bash

ITERATION=$1
SCRIPT_PATH=$2
NODE_NAME=$3
USER_NAME=$4
HOST=$5
_ECHO=/bin/echo
_MKDIR=/bin/mkdir

if [ $# -ne 5 ]; then
   echo -e "Please enter no. of executions, script file path, node name, user name and host. \nFor Example: sh /home/shared/bladeRunner_Rest.sh 4 /home/shared/common/script.txt BSC01 administrator ops-0"
   exit;
fi

if [ $ITERATION -lt 1 ]; then
   echo "Number of Iteration should be greater than 0."
   exit;
fi

SSO_TOKEN_FILE=$(head -n 1 $HOME/.enm_login)
LOG_TIME_STAMP=`date +%d%b%Y_%T`
LOG_FILE_DIRECTORY=$HOME/bladerunnerLog/$LOG_TIME_STAMP/$NODE_NAME
$_MKDIR -p $LOG_FILE_DIRECTORY

for i in `seq 1 $ITERATION`
do
	curl -k --cookie "iPlanetDirectoryPro=$SSO_TOKEN_FILE" -H Content-Type:application/json -X POST "https://$HOST.ops/ops-service/launchers/v1/ops-nui-launcher/" -d "{\"userName\":\"$USER_NAME\",\"scriptFilePath\":\"$SCRIPT_PATH\",\"routefile\":\"$LOG_FILE_DIRECTORY/log_$i\",\"user\":\"$USER_NAME\",\"nodeName\":\"$NODE_NAME\"}" &
done

$_ECHO "bladeRunner_Rest.sh execution completed. please check logs at $LOG_FILE_DIRECTORY"
