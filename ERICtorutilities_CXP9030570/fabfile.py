import os
import sys

from fabric.api import env, run, prefix
from fabric.context_managers import cd, settings
from fabric.contrib.files import exists, append, comment
from fabric.operations import get, put

VENV_DIR_NAME = '.env'
ENMUTILS_PROJECT_DIR_NAME = 'common-python-utils'
INSTALL_TESTER_SCRIPT = 'install_tester.sh'


def copy_new():
    """
    Usage: fab copy_new remote_dir:<name_of_dir>

    Either provide the host as a global env var in env.hosts in this
    module above or enter host on the command line as hosts:<host>. If
    host is not found, it will be prompted for on the command line.
    """

    run("mkdir -p {0}".format(env.project_root))
    put(local_path=os.path.join(env.local_path, '*'), remote_path=env.project_root, mirror_local_mode=True)


def ensure_virtualenv():
    """
    Ensure that virtualenv is installed on the remote host
    """

    # If '.env' is already installed return
    if exists('{0}/bin'.format(env.venv)):
        return

    interpreter = '/opt/ericsson/enmutils/.env/bin/python2.7'

    # Change to project root directory and install virtualenv with the specified interpreter
    with cd(env.project_root):
        run("virtualenv --no-site-packages -p {0} {1}".format(interpreter, env.venv))


def change_local_prop(prop_name, prop_val):
    """
    Change the ENVIRON from 'local' to 'testing'  in the local properties file

    @type prop_name: string
    @param prop_name: The property name to look for in the file
    @type prop_val: string
    @param prop_val: The property value to replace with in the file
    @rtype: void
    """
    local_props_file = os.path.join(env.enmutils_package_path, 'local_properties.py')

    # Change to the parent root directory an
    with cd(env.project_root):
        prop_name = prop_name.upper()
        # Find 'ENVIRON' pattern in the local props file and comment the line away
        comment(local_props_file, r"^{0}\s*=".format(prop_name))
        prop_string = '{0}="{1}"'.format(prop_name, prop_val)
        # Add a new string pattern to the file
        append(local_props_file, prop_string)


def install_packages():
    # We need to activate the virtualenv first in order to install production and internal packages. Deactivate when done
    with prefix('source {0}/bin/activate'.format(env.venv)):
        with cd(env.project_root):
            # Install the production lib package
            run('pip install --no-index --find-links={0} --ignore-installed --editable {1}'.format(env.epp, env.enmutils_path))
            run('sh {0}'.format(os.path.join(env.project_root, INSTALL_TESTER_SCRIPT)))


def deploy():
    """
    Copy the code to a remote server and enable virtualenv

    @type remote_dir: string
    @param remote_dir: The remote directory to deploy the code on
    @type clean: string
    @param clean: Option to remove the target directory on the remote MS before copying
    @rtype: void
    """
    copy_new()
    change_local_prop("ENVIRON", "testing")
    ensure_virtualenv()
    install_packages()


def _setup_env(remote_path, local_path):
    env.project_root = remote_path
    env.enmutils_path = env.project_root
    env.enmutils_package_path = os.path.join(env.enmutils_path, 'enmutils')
    env.venv = os.path.join(env.project_root, VENV_DIR_NAME)
    env.epp = os.path.join(env.enmutils_package_path, '3pp')
    env.local_path = local_path


def run_acceptance(remote_dir, local_dir):
    """
    Copy the code to a remote server and enable virtualenv and run acceptance tests
    @type remote_dir: string
    @param remote_dir: The remote directory to deploy the code on
    @rtype: void
    """

    _setup_env(remote_dir, local_dir)
    out_path = '.'  # Current path on jenkins build directory
    remote_log_path = os.path.join(remote_dir, 'test-results/allure-results')

    deploy()

    # Activate the virtualenv and run acceptance job
    with prefix('source {0}/bin/activate'.format(env.venv)):
        with settings(warn_only=True):
            result = run('tester acceptance --root_path=%s' % remote_dir)

    # Get allure reports from the server
    get(remote_path=remote_log_path, local_path=out_path)
    sys.exit(result.return_code)
