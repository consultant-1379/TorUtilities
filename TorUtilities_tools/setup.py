import os
import glob
from setuptools import setup, find_packages


# This will generate the list of all our executable binary files in the required format
def get_entry_points():
    scripts = []
    scripts_paths = glob.glob("enmutilsbin/*.py")
    for sc in scripts_paths:
        file_path, _ = os.path.splitext(sc)
        module_path = file_path.replace('/', '.')
        module_name = module_path.split('.')[-1]
        if module_name not in ['__init__', '__main__']:
            scripts.append('{0}={1}:cli'.format(module_name, module_path))
    return scripts

setup(
    name='enmutils-tools',
    author='Blade Runners',
    packages=find_packages(),
    include_package_data=False,
    zip_safe=True,
    platforms='any',

    # This will also install the dependency packages i.e, pycrypto, ecdsa will be installed while installing paramiko
    # These need to be installed in order to run our production tools
    install_requires=[
        'EnmUtils'
    ],
    entry_points={
        'console_scripts': get_entry_points(),
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
