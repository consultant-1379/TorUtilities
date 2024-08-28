from __future__ import print_function

import os
import glob

from setuptools import setup, find_packages

# This will generate the list of all our executable binary files in the required format


def get_entry_points():
    scripts = []
    scripts_paths = glob.glob("enmutils_int/bin/*.py")
    for sc in scripts_paths:
        file_path, _ = os.path.splitext(sc)
        module_path = file_path.replace('/', '.')
        module_name = module_path.split('.')[-1]
        if module_name not in ['__init__', '__main__']:
            scripts.append('{0}={1}:cli'.format(module_name, module_path))
    return scripts


# These are the folders we want to explicitely include in our installation because by default setup only includes
# python packages i.e folders containing '__init__.py'
PACKAGE_DATA = {'enmutils_int': ['etc/*.conf', 'etc/*.json', 'etc/openapi/*.yml', 'etc/data/*.*', 'etc/ui/*.conf',
                                 'etc/load/*/*.conf', 'etc/pm_49_ftpes_setup_files/*.*',
                                 'external_sources/scripts/*.*', 'external_sources/scripts/celltrace/*.*',
                                 'external_sources/scripts/test_client/*.*', 'external_sources/man_pages/*.*',
                                 'templates/*.*', 'templates/*/*.*', 'templates/*/*/*.*']}

setup(
    name='EnmUtilsInt',
    author='Blade Runners',
    packages=find_packages(),
    package_data=PACKAGE_DATA,
    include_package_data=True,
    zip_safe=False,
    platforms='any',

    # This will also install the dependency packages i.e, pycrypto, ecdsa will be installed while installing paramiko
    # These need to be installed in order to run our internal tools
    install_requires=[
        "waitress",
        "flask",
        'EnmUtils',
        'click>=5.1',
        'selenium',
        'Unipath',
        'pexpect',
        'ptyprocess',
        'jinja2>=2.10',
        'jsonpickle',
        'tabulate>=0.8.7',
        'websocket-client',
        'json2html',
        'cli2man',
        'configparser',
        'flask-swagger-ui',
        'pyyaml',
        'python-dateutil',
        'apscheduler',
        'pytz',
        'packaging',
        'expiringdict',
        'typing',
        'retrying'
    ],
    entry_points={
        'console_scripts': get_entry_points(),
    },

    # These extra packages are specific for running our tests. Therefore, we only want to install them when we test.
    classifiers=[
        'Development Status :: 1 - Beta',
        'Environment :: Shell Scripting',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
