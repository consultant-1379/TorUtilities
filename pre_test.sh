#!/bin/bash
if [ $(echo $JOB_NAME | grep "Release") ]; then
  rm -rf .env .deploy

  echo 'check glibc version '
  ldd --version ldd

  echo "Setting the path to the python installation that will be bundled as part of the RPM"
  export PATH_TO_PYTHON_INSTALLATION="/proj/ciexadm200/tools/bladerunners/.env"

  # Exporting LITP python paths because it contains python 2.7 interpreter and we bundle that with this project
  export LITP_PY=/proj/litpadm200/tools/litp-requirements-py
  export PATH=$LITP_PY/usr/bin:$PATH
  export PYTHONPATH=$LITP_PY/usr/lib/python2.6/site-packages:$LITP_PY/usr/lib64/python2.6/site-packages
  INSTALL_PATH_ESC='\/opt\/ericsson\/enmutils'
  wget https://bootstrap.pypa.io/pip/2.7/get-pip.py -O ${WORKSPACE}/get-pip.py
  python ${WORKSPACE}/get-pip.py

  virtualenv -p ${PATH_TO_PYTHON_INSTALLATION}/bin/python2.7 --no-site-packages .env && source .env/bin/activate

  export PYTHONPATH=


  rsync .env/lib/python2.7/ python2.7/ -a --copy-links
  rm -rf .env/lib/python2.7/
  mv python2.7/ .env/lib/
  cp -r ${PATH_TO_PYTHON_INSTALLATION}/lib/python2.7/* .env/lib/python2.7/
  rm -r .env/lib/python2.7/test
  .env/bin/python .env/bin/pip install --no-index --find-links=ERICtorutilitiesinternal_CXP9030579/enmutils_int/3pp --upgrade --force-reinstall pip
  .env/bin/python .env/bin/pip install --ignore-installed --no-index --find-links=ERICtorutilities_CXP9030570/enmutils/3pp ./ERICtorutilities_CXP9030570/
  .env/bin/python .env/bin/pip install --ignore-installed --no-index --find-links=ERICtorutilitiesinternal_CXP9030579/enmutils_int/3pp selenium
  .env/bin/pip2.7 install TorUtilities_tools/
  .env/bin/python .env/bin/pip install --no-index --find-links=ERICtorutilitiesinternal_CXP9030579/enmutils_int/3pp ERICtorutilitiesinternal_CXP9030579/
  .env/bin/python .env/bin/pip install --ignore-installed --no-index --find-links=ERICtorutilitiesinternal_CXP9030579/enmutils_int/3pp configparser requests==2.6.0 kubernetes requests-oauthlib pyyaml requests-toolbelt
  .env/bin/python .env/bin/pip install google-auth==2.18.1
  .env/bin/python .env/bin/pip wheel --wheel-dir=ERICtorutilitiesinternal_CXP9030579/wheel_dir ERICtorutilitiesinternal_CXP9030579/ --no-deps
  .env/bin/python .env/bin/pip wheel --wheel-dir=ERICtorutilitiesinternal_CXP9030579/wheel_dir torutilities_testslib/ --no-deps

  echo "printing python version"
  python -V

  echo "printing which python"
  which python

  echo "printing python -m site"
  python -m site

  cp ERICtorutilitiesinternal_CXP9030579/enmutils_int/3pp/*.whl ERICtorutilitiesinternal_CXP9030579/wheel_dir
  cp torutilities_testslib/3pp/*.whl ERICtorutilitiesinternal_CXP9030579/wheel_dir

  find . -type f -exec sed -i "s/$(pwd|sed 's_/_\\/_g')/$INSTALL_PATH_ESC/g" {} \;

  .env/bin/python post_install_script.py --package=production
  .env/bin/python post_install_script.py --package=internal

  find ${WORKSPACE} -name \*.py[co] -delete
fi
if [ $(echo $JOB_NAME | grep "PCR") ]; then
  INTERNAL_PKG="ERICtorutilitiesinternal_CXP9030579"
  PRODUCTION_PKG="ERICtorutilities_CXP9030570"

  export PATH_TO_PYTHON_INSTALLATION="/proj/ciexadm200/tools/bladerunners/.env"
  export LITP_PY=/proj/litpadm200/tools/litp-requirements-py
  export PATH=$LITP_PY/usr/bin:$PATH
  export PYTHONPATH=$LITP_PY/usr/lib/python2.6/site-packages:$LITP_PY/usr/lib64/python2.6/site-packages
  virtualenv -p ${PATH_TO_PYTHON_INSTALLATION}/bin/python2.7 --no-site-packages .env && source .env/bin/activate
  export PYTHONPATH=
  cp ${PRODUCTION_PKG}/enmutils/config/jenkins/local_properties.py ${PRODUCTION_PKG}/enmutils/

  .env/bin/python2.7 .env/bin/pip2.7 install --no-index --find-links=${INTERNAL_PKG}/enmutils_int/3pp --upgrade pip
  .env/bin/python2.7 .env/bin/pip2.7 install --ignore-installed --no-index --find-links=${PRODUCTION_PKG}/enmutils/3pp --editable ./${PRODUCTION_PKG}/

  .env/bin/pip2.7 install --no-index --editable TorUtilities_tools/
  .env/bin/pip2.7 install --no-index --find-links=${INTERNAL_PKG}/enmutils_int/3pp --editable ${INTERNAL_PKG}/
  .env/bin/pip2.7 install --no-index --find-links=${INTERNAL_PKG}/enmutils_int/3pp --upgrade --force-reinstall kubernetes requests-oauthlib pyyaml requests-toolbelt
  .env/bin/pip2.7 install --no-index --find-links=torutilities_testslib/3pp --editable torutilities_testslib/
  .env/bin/python2.7 .env/bin/pip2.7 install google-auth==2.18.1 retrying==1.3.3

  # Perform source code analysis to identify any syntax errors, formatting violations or code inefficiencies, and runs unit tests
  tester check
  tester unit --cover_min_percentage=95
fi