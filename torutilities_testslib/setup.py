from __future__ import print_function
import os
from setuptools import setup, find_packages

_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(data_folder):
    package_name = 'testslib'
    files = []
    for (dirpath, _, filenames) in os.walk(os.path.join(_ROOT, package_name, data_folder)):
        for file_name in filenames:
            fp = os.path.join(dirpath, file_name).split(package_name + '/')[1]
            files.append(fp)
    return files


def get_data_for_testslib():
    results = []
    for folder_name in ['etc', 'resources', 'scripts']:
        results.extend(get_data(folder_name))
    return results


# These are the folders we want to explicitely include in our installation because by default setup only includes python packages i.e folders containing '__init__.py'
PACKAGE_DATA = {'testslib': get_data_for_testslib()}
setup(
    name='EnmUtilsTestware',
    author='Blade Runners',
    packages=find_packages(),
    package_data=PACKAGE_DATA,
    include_package_data=True,
    zip_safe=False,
    platforms='any',

    # This will also install the dependency packages i.e, pycrypto, ecdsa will be installed while installing paramiko
    # These need to be installed in order to run our internal tools
    install_requires=[
        'EnmUtilsInt',
        'unittest2',
        'responses',
        'mock',
        'epydoc',
        'fabric',
        'parameterizedtestcase',
        'pep8',
        'pylint',
        'fakeredis',
        'coverage',
        'autopep8',
        'nose-cprof',
        'nose-allure-plugin',
        'beautifulsoup4',
        'openapi_spec_validator'
    ],
    entry_points={
        'console_scripts': ['tester=testslib.tester:cli'],
    },

    classifiers=[
        'Development Status :: 1 - Beta',
        'Environment :: Shell Scripting',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
