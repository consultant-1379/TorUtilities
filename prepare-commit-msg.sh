#!/bin/bash
COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2
SHA1=$3

# Check for valid jira reference

MSG=$(head -n1 $COMMIT_MSG_FILE)

tester commit-msg "$MSG"
rc=$?
if [[ $rc != 0 ]]; then
    exit $rc
fi

