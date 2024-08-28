from setuptools import setup, find_packages


# These are the folders we want to explicitely include in our installation because by default setup only includes python packages i.e folders containing '__init__.py'
PACKAGE_DATA = {'enmutils': ['etc/*.whl', 'etc/*.conf', 'etc/version_specific/*.conf', 'external_sources/*.*', 'external_sources/db/*', 'lib/resources/*.*']}

setup(
    name='EnmUtils',
    author='Blade Runners',
    packages=find_packages(),
    package_data=PACKAGE_DATA,
    include_package_data=False,
    zip_safe=True,
    platforms='any',

    # This will also install the dependency packages i.e, pycrypto, ecdsa will be installed while installing paramiko
    # These need to be installed in order to run our production tools
    install_requires=[
        "docopt",
        "six>=1.9.0",
        "enm_client_scripting>=1.21.1",
        "enum34",
        "lxml",
        "paramiko>=2.4.2",
        "redis",
        "pycrypto",
        "requests",
        "Unipath",
        "wheel>=0.22"
    ],
    entry_points={
        'console_scripts': ['daemon=enmutils.bin.daemon:cli'],
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
