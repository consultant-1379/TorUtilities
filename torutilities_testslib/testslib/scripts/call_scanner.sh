#!/bin/bash

BASE_DIR=/home/ejamliv/workspace/TorUtilities

# Find the absolute path to the module we've been given
MODULE_PATH=$(find $BASE_DIR -name $1 -print)

if [ ! -f $MODULE_PATH ]; then
    echo "ERROR: Could not find module $1"
    exit 1
fi

# Get list of all functions/methods in module
FUNCTIONS=$(grep -E '^\s*def ' $MODULE_PATH | sed -e 's/\s*def\s*//g' | sed -e 's/(.*$//g')
echo ""
echo "Functions/methods in module $1:"

for FUNCTION in $FUNCTIONS; do
    echo "  $FUNCTION"
done

# Check to see if anyone is using the function/method
OLD_IFS=$IFS
IFS='
'
for FUNCTION in $FUNCTIONS; do
    echo ""
    echo "${FUNCTION}():"
    CALLERS=$(cd $BASE_DIR; grep -rnF $FUNCTION ./* | grep -v _tests_ | grep -v "def $FUNCTION(")
    CALLER_COUNT=0

    # Print out all of the callers
    for CALLER in $CALLERS; do
        echo "  $CALLER"
        CALLER_COUNT=$((CALLER_COUNT+1))
    done

    # Print out a message in red if we didn't find any callers
    if [ $CALLER_COUNT -eq 0 ]; then
        echo -e "  \e[31m************\e[0m"
        echo -e "  \e[31m*** NONE ***\e[0m"
        echo -e "  \e[31m************\e[0m"
    fi
done
