#!/bin/bash

DIRNAME=/usr/bin/dirname
CMD="python epydoc-3.0.1/scripts/epydoc.py "

function get_absolute_path_to_repo
{
  _dir_=`${DIRNAME} $0`
  SCRIPT_HOME=`cd ${_dir_}/../ 2>/dev/null && pwd || ${ECHO} ${_dir_}`
}

get_absolute_path_to_repo
_docHome_=${SCRIPT_HOME}/tests
cd ${_docHome_}

rm -rf ../bin/*.pyc ../lib/*.pyc ../int/bin/*.pyc ../int/lib/*.pyc
$CMD -v --fail-on-docstring-warning --name torutilities --no-private ../bin/*.py ../lib/*.py ../int/bin/*.py ../int/lib/*.py
_status_=$?

# Rremove everything from docs folder
rm -rf html/ 2>/dev/null
exit ${_status_}
