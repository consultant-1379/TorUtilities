# ********************************************************************
# Name    : Auto Provision Project
# Summary : Provides functionality for generating a valid project
#           (.zip archive) which can be ordered by the Auto Provision
#           application. Allows users to generate directory
#           structure, node XML files, fetches software packages.
# ********************************************************************

import os
import pkgutil
import shutil
import string

from jinja2 import Environment, FileSystemLoader

from enmutils.lib import shell, filesystem, log, arguments
from enmutils.lib.cache import (is_host_physical_deployment, is_emp, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM,
                                is_enm_on_cloud_native)
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, EnmApplicationError, EnvironError
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.enm_deployment import get_pod_hostnames_in_cloud_native
from enmutils_int.lib.shm_utilities import SHMUtils, SoftwarePackage
from enmutils_int.lib.shm_software_ops import SoftwareOperations
from enmutils_int.lib.simple_sftp_client import download

INT_PACKAGE = pkgutil.get_loader('enmutils_int').filename
Env = Environment(loader=FileSystemLoader(os.path.join(INT_PACKAGE, 'templates', 'ap')))
PKG_SVR = {'uname': 'APTUSER', 'upass': r"]~pR:'Aw6cwpJR4dDY$k85\t", 'file_path': '/enmcisftp/shm_packages'}
PKGS = ['CXP9024418_15-R69C29.zip']
CLOUD_SCP = 'scp -r -i {1} {0} cloud-user@$EMP:/tmp'
PHYSICAL_SCP = 'scp -r {0} root@$LMS_HOST:/tmp'
SERVER_SOURCE_IP = "sfts.seli.gic.ericsson.se"


class InvalidProjectException(Exception):
    pass


def create_ap_pkg_directory():
    """
    Create /home/enmutils/ap/ directory for AP Pkg's to be downloaded

    :return: path of AP pkg's directory
    :rtype: str

    :raises EnvironError: raised if failed to create AP pkg directories
    """
    ap_pkg_path = os.path.join("/home", "enmutils", "ap")
    if not os.path.exists(ap_pkg_path):
        try:
            os.makedirs(ap_pkg_path)
            log.logger.debug("{0} directories were created to download AP pkg's".format(ap_pkg_path))
        except Exception as e:
            raise EnvironError("Failed to create AP pkg directories, Exception: {0}".format(e.message))
    else:
        log.logger.debug("Selected directory to download AP pkg's is {0}".format(ap_pkg_path))
    return ap_pkg_path


def scp_upgrade_packages(use_proxy=True):
    """
    Download upgrade package for RadioNode and MSRBS

    :param use_proxy: Boolean indicating if a proxy connection is required
    :type use_proxy: bool

    :raises EnvironError: raised if unable to download AP pkg's
    """
    ap_pkg_path = create_ap_pkg_directory()
    for pkg in PKGS:
        if not filesystem.does_file_exist("{0}/{1}".format(ap_pkg_path, pkg)):
            try:
                # To run on vApp set use_proxy=False
                download(SERVER_SOURCE_IP, PKG_SVR.get('uname'), PKG_SVR.get('upass'),
                         "{0}/{1}".format(PKG_SVR.get('file_path'), pkg), "{0}/{1}".format(ap_pkg_path, pkg),
                         use_proxy=use_proxy)
            except Exception as e:
                raise EnvironError("Unable to download file, {0}.".format(e.message))


def raise_invalid_project(condition, msg):
    """
    Helper method to determine if action is None

    :param condition: expression, condition to check if false
    :type condition: object
    :param msg: String to output if condition is false
    :type msg: str

    :raises InvalidProjectException: raised if project validation fails
    """
    if not condition:
        raise InvalidProjectException(msg)


class Project(object):
    PROJECT_INFO = 'projectInfo.xml'
    PROJECT_DIR = '/tmp/{0}'
    SHM_IMPORT = 'shm import -s file:{0}'
    PACKAGES = {      # Package Name      Filter text
        "RadioNode": ['CXP9024418_15-R69C29', 'R69C29']
    }

    GENERIC_CM = ['Bulk-CM-Configuration-file.xml']

    RADIONODE_INFO = 'radio_nodeInfo.xml'
    RADIONODE = ['radio_siteInstallation.xml', 'Optional-feature-file.xml', 'Unlock-cells-file.xml',
                 'radio_siteBasic.xml']
    RADIONODE_GENERIC = ['radio_siteEquipment.xml']

    def __init__(self, name, user, description="Workload sample template description", nodes=None):
        """
        Constructor for object

        :type name: str
        :param name: Name for Project, will be used to perform actions upon once imported
        :type user: `enm_user_2.User`
        :param user: User object which create the project
        :type description: str
        :param description: Description of Project
        :type nodes: list
        :param nodes: list of enm_node.BaseNode objects
        """
        self.name = name
        self.description = description
        self.nodes = nodes if nodes else []
        self.user = user

    def _teardown(self):
        """
        Secret teardown method
        """
        path = "{}.zip".format(get_internal_file_path_for_import("etc", "data", self.name))
        if filesystem.does_file_exist(path):
            cmd = shell.Command('rm -rf {0}'.format(path))
            raise_invalid_project(shell.run_local_cmd(cmd), "Failed to delete project archive, with command: [{0}]".format(cmd))

    @staticmethod
    def get_template(template):
        """
        Returns the .xml template

        :param template: Path to template to be returned
        :type template: str

        :return: returns the requested template
        :rtype: Template
        """
        return Env.get_template(template)

    def _prepare_project_info_xml_file(self):
        """
        Generates the projectInfo.xml of the project, at the top level directory
        """
        with open("{0}/{1}".format(self.PROJECT_DIR.format(self.name), self.PROJECT_INFO), 'w') as f:
            f.write(self.get_template(self.PROJECT_INFO).render(name=self.name, description=self.description))

    def get_model_id(self, node):
        """

        If the oss-model-identity is not parsed, try to build it from mim version and node version

        :type node: `enm_node.Node`
        :param node: Node to determine if a oss-model-identity is available

        :raises EnmApplicationError: raised if describe command fails

        :rtype: str
        :return: Model identity of the node
        """
        models = []
        model_ids = []
        cmd = 'cmedit describe -neType={netype} -t'
        response = self.user.enm_execute(cmd.format(netype=node.primary_type))
        if "Error " in response.get_output():
            raise EnmApplicationError("Failed to retrieve NetworkElement describe information.")
        else:
            for line in response.get_output():
                if node.mim_version and node.mim_version in line:
                    models.append(line)
                elif len(line.split('\t')) == 7 and "Model ID" not in line:
                    model_ids.append(line)

            if models:
                return models[0].split('\t')[6]
            elif model_ids:
                return model_ids[0].split('\t')[6]
            else:
                raise EnmApplicationError("Failed to retrieve NetworkElement model Id information.")

    def get_node_secure_username_and_password(self, node):
        """

        Fetch node's secure username and password for nodeInfo.xml

        :type node: `enm_node.Node`
        :param node: Node to determine it's credentials using secadm

        :raises EnmApplicationError: raised if it fails to retrieve the credentials

        :rtype: str
        :return: secure username and password of the provided node
        """
        cmd = 'secadm credentials get -pt show --nodelist {node_name}'
        response = self.user.enm_execute(cmd.format(node_name=node.node_id))
        if "Error" in " ".join(response.get_output()):
            raise EnmApplicationError("Failed to retrieve node's secureUserName and secureUserPassword, "
                                      "response: {0}".format(response.get_output()))
        else:
            for line in response.get_output():
                if "secureUserName" in line and node.node_id in line:
                    secure_user = line.split()[1].split("secureUserName:")[1]
                    secure_password = line.split()[2].split("secureUserPassword:")[1]
                    return secure_user, secure_password

    @staticmethod
    def update_subnetwork_name(node):
        """
        Updates the subnetwork name of nodes in the project

        :type node: `enm_node.Node`
        :param node: Node to update its subnetwork name

        :rtype: str
        :return: Modified subnetwork of the node
        """
        sub = node.subnetwork.split("SubNetwork=", 1)
        if len(sub) < 2:
            subnet = node.subnetwork
        else:
            subnet = sub[1]
        return subnet

    def update_generic_cm(self, node):
        """
        Updates the Bulk-CM-Configuration-file.xml of the project

        :type node: `enm_node.Node`
        :param node: Node to update its cm template file
        """
        subnet = self.update_subnetwork_name(node)
        for template in self.GENERIC_CM:
            file_name = "{0}/{1}/{2}".format(self.PROJECT_DIR.format(self.name), node.node_id,
                                             template.split('_')[1] if '_' in template else template)
            with open(file_name, 'w') as f:
                f.write(self.get_template(template).render(node_id=node.node_id,
                                                           node_subnetwork=subnet))

    def update_template_with_node_details(self, node, xmls):
        """
        Updates the nodetype info xml file with the node details

        :type node: `enm_node.Node`
        :param node: Node to update its template files

        :type xmls: dict
        :param xmls: dict of nodetype and there template files
        """
        subnet = self.update_subnetwork_name(node)
        template = xmls.get(node.primary_type)[0]
        letters = arguments.get_random_string(size=5, exclude="OI" + string.ascii_lowercase + string.digits)
        digits = arguments.get_random_string(size=8, exclude=string.ascii_letters)
        serial = "{0}{1}".format(letters, digits)
        with open("{0}/{1}/{2}".format(self.PROJECT_DIR.format(self.name), node.node_id,
                                       template.split('_')[1] if '_' in template else template), 'w') as f:
            f.write(self.get_template(template).render(node_id=node.node_id, node_ip=node.node_ip,
                                                       model_identity=node.model_identity,
                                                       primary_type=node.primary_type,
                                                       serial=serial, subnetwork=subnet,
                                                       user=node.secure_user, passwd=node.secure_password))

    def _prepare_node_xml_files(self):
        """
        Generates the radio, transport, site, and installation.xml for each node

        :raises InvalidProjectException: raised if project validation fails
        """
        raise_invalid_project(self.nodes, "Unable to create project, invalid node(s) or no node(s) provided: [%s]" %
                              [type(node) for node in self.nodes])
        xmls = {
            "RadioNode": [self.RADIONODE_INFO, self.RADIONODE, self.RADIONODE_GENERIC]
        }
        for node in self.nodes:
            raise_invalid_project(node.primary_type, "Unable to determine valid primary type for node, Primary Type %s"
                                  % node.primary_type)
            self.update_template_with_node_details(node, xmls)

            subnet = self.update_subnetwork_name(node)
            for template in xmls.get(node.primary_type)[1]:
                file_name = "{0}/{1}/{2}".format(self.PROJECT_DIR.format(self.name), node.node_id,
                                                 template.split('_')[1] if '_' in template else template)
                with open(file_name, 'w') as f:
                    f.write(self.get_template(template).render(node_id=node.node_id, subnetwork=subnet,
                                                               user=node.secure_user, passwd=node.secure_password))

            for template in xmls.get(node.primary_type)[2]:
                with open("{0}/{1}/{2}".format(self.PROJECT_DIR.format(self.name),
                                               node.node_id,
                                               template.split('_')[1] if '_' in template else template), 'w') as f:
                    f.write(self.get_template(template).render())

            self.update_generic_cm(node)

    def _create_directory_structure(self):
        """
        Create a valid directory structure

        :raises InvalidProjectException: raised if project validation fails
        """
        if filesystem.does_dir_exist(self.PROJECT_DIR.format(self.name)):
            self.delete_directory_structure()
        cmd = shell.Command('mkdir {0}'.format(self.PROJECT_DIR.format(self.name)))
        raise_invalid_project(shell.run_local_cmd(cmd), "Failed to create parent directory, with command: [%s]" % cmd)
        raise_invalid_project(self.nodes, "Unable to create project, invalid node(s) or no node(s) provided: [%s]"
                              % [type(node) for node in self.nodes])
        for node in self.nodes:
            cmd = shell.Command('mkdir {0}/{1}'.format(self.PROJECT_DIR.format(self.name), node.node_id))
            raise_invalid_project(shell.run_local_cmd(cmd),
                                  "Failed to create node %s directory, with command: [%s]" % (node, cmd))

    def delete_directory_structure(self):
        """
        Create a valid directory structure

        :raises InvalidProjectException: raised if project validation fails
        """
        cmd = shell.Command('rm -rf {0}'.format(self.PROJECT_DIR.format(self.name)))
        raise_invalid_project(shell.run_local_cmd(cmd), "Failed to delete parent directory, with command: [%s]" % cmd)

    def _install_software_packages(self):
        """
        Install a valid Basic/Upgrade package to use

        :raises ScriptEngineResponseValidationError: raised if cmcli command fails
        :raises IndexError: raised if primary type is not present
        """
        try:
            packages_to_install = self.PACKAGES.get(self.nodes[0].primary_type)
        except IndexError:
            raise IndexError("Unable to determine valid primary type of node: %s" % self.nodes[0].primary_type)
        software_package = SoftwarePackage(self.nodes, user=self.user)
        log.logger.debug("package filter is: {0}".format(packages_to_install[1]))
        pkg_list = SoftwareOperations(user=self.user, package=software_package).get_all_software_packages(
            user=self.user, filter_text=packages_to_install[1])
        log.logger.debug("packages list is: {0}".format(pkg_list))
        if not any(pkg_list):
            ap_pkg_path = create_ap_pkg_directory()
            _upgrade = os.path.join(ap_pkg_path, "%s.zip" % packages_to_install[0])
            response = self.user.enm_execute(self.SHM_IMPORT.format("%s.zip" % packages_to_install[0]), file_in=_upgrade)
            if "already imported" in str(response.get_output()):
                log.logger.debug("Package is already imported...")
            elif any([error_op in str(response.get_output()) for error_op in ["Please Import a file", "ERROR"]]):
                raise ScriptEngineResponseValidationError(
                    "Failed to import the specified software"
                    " package, Response was {0}".format(','.join(response.get_output())), response=response)

    @staticmethod
    def run_command_and_check_response(cmd, fail_message):
        response = shell.run_local_cmd(cmd)
        if response.rc:
            raise EnvironError(fail_message.format(response.stdout))

    def make_dir_executable(self, client):
        """
        Makes the test client files directory executable
        :param client: List containing test_client_files
        :type client: list
        """
        for cmd in [shell.Command('chmod -R u+x {0}'.format(client[0])),
                    shell.Command("sed -i 's/^M$//g' {0}/{1}".format(client[2], client[3]))]:
            self.run_command_and_check_response(cmd, "Failed to make directory executable, Response was {0}")

    @staticmethod
    def copy_test_client_files_to_pod(dir_name):
        """
        Copies the test client files directory to the Cloud Native Pod
        :param dir_name: test_client file directory
        :type dir_name: str
        :raises EnvironError: if the directory was not able to be copied
        """
        ap_serv_ip = get_pod_hostnames_in_cloud_native('apserv')
        copy_to_cloud_native_pod = shell.copy_file_between_wlvm_and_cloud_native_pod(ap_serv_ip[0], dir_name,
                                                                                     '/tmp', 'to')
        if copy_to_cloud_native_pod.rc:
            raise EnvironError("Failed to copy the dir {0} to {1}".format(dir_name, ap_serv_ip[0]))
        else:
            log.logger.debug("Test client files have been successfully copied to the Cloud Native Pod")

    def import_node_up(self):
        """
        Add node-up .zip to /tmp
        :raises Exception: if the installation of unzip is unsuccessful
        """
        ap_dir = "/tmp"
        clients = {
            'ecim': ['{}/node-discovery-ecim-test-client'.format(ap_dir), 'ecim-node-up.zip',
                     '{}/node-discovery-ecim-test-client/bin/sh/'.format(ap_dir), 'ecim-node-up.sh']
        }
        try:
            SHMUtils().install_unzip()
        except Exception as e:
            log.logger.debug(str(e))
        if is_enm_on_cloud_native():
            self.import_node_up_for_cloud_native(ap_dir, clients)
        else:
            for client in clients.itervalues():
                if filesystem.does_file_exist_on_ms("{0}{1}".format(client[2], client[3])):
                    continue
                self.unzip_test_client_files(ap_dir, client)

                if is_emp():
                    cmd = shell.Command(CLOUD_SCP.format(client[0], CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM))
                elif is_host_physical_deployment():
                    cmd = shell.Command(PHYSICAL_SCP.format(client[0]))
                else:
                    log.logger.debug("Skipping secure copy of test-client ...")
                    continue
                self.run_command_and_check_response(cmd, "Failed to copy directory, Response was {0}")

    def import_node_up_for_cloud_native(self, ap_dir, clients):
        """
        :param ap_dir: ap directory
        :type ap_dir: str
        :param clients: test clients to copy
        :type clients: dict
        """
        apserv_hostnames = get_pod_hostnames_in_cloud_native('apserv')
        for apserv in apserv_hostnames:
            for client in clients.itervalues():
                if filesystem.does_file_exists_on_cloud_native_pod('apserv', apserv,
                                                                   "{0}{1}".format(client[2], client[3])):
                    continue
                else:
                    self.unzip_test_client_files(ap_dir, client)
                    self.copy_test_client_files_to_pod(client[0])

    def unzip_test_client_files(self, ap_dir, client):
        '''
         install unzip and runs unzip command on test client files
        :param ap_dir: ap directory
        :type ap_dir: str
        :param client: client list
        :type client:list
        '''
        node_up = get_internal_file_path_for_import("etc", "data", client[1])
        cmd = shell.Command("unzip -o {zip_file} -d {ap_dir}".format(zip_file=node_up, ap_dir=ap_dir))
        self.run_command_and_check_response(cmd, "Failed to extract zip, Response was {0}")
        self.make_dir_executable(client)

    def _create_archive(self):
        """
        Creates the .zip archive

        :raises InvalidProjectException: raised if project validation fails
        """
        path = get_internal_file_path_for_import("etc", "data", self.name)
        raise_invalid_project(shutil.make_archive("{0}".format(path), 'zip', self.PROJECT_DIR.format(self.name)),
                              "Failed to create archive file.")

    def create_project(self):
        """
        Create the usable project as a .zip archive
        """
        self._create_directory_structure()
        self._prepare_project_info_xml_file()
        self._prepare_node_xml_files()
        self._install_software_packages()
        self.import_node_up()
        self._create_archive()
        self.delete_directory_structure()

    def delete_copied_scripts_from_pod(self, cmd, file_path, file_name):
        """
        Deletes scripts copied from apserv:
        ecim-node-up.sh
        nodeup-unsecure.sh

        :param cmd: Command to run on Cloud Native Pod
        :type cmd: str
        :param file_path: Path of the file
        :type file_path: str
        :param file_name: Name of the file to delete
        :type file_name: str
        """
        ap_serv_hostnames = get_pod_hostnames_in_cloud_native("apserv")
        for ap_serv in ap_serv_hostnames:
            if filesystem.does_file_exists_on_cloud_native_pod('apserv', ap_serv,
                                                               "{0}{1}".format(file_path, file_name)):
                res = shell.run_cmd_on_cloud_native_pod('apserv', ap_serv, cmd)
                if res.rc == 0:
                    log.logger.debug("Successfully deleted the file: {0}".format(file_name))
                else:
                    log.logger.debug("Failed to delete the file: {0}".format(file_name))

    def delete_scripts_copied_remote_host(self):
        """
        Deletes scripts copied to lms/emp:
        ecim-node-up.sh
        nodeup-unsecure.sh
        """
        log.logger.debug("Attempting to delete scripts on lms/emp/pod")
        clients = {
            'cpp': ['/tmp/node-discovery-test-client/bin/sh/unsecure/', 'nodeup-unsecure.sh'],

            'ecim': ['/tmp/node-discovery-ecim-test-client/bin/sh/', 'ecim-node-up.sh']
        }
        for client in clients.itervalues():
            cmd = 'rm {0}{1}'.format(client[0], client[1])
            if is_enm_on_cloud_native():
                self.delete_copied_scripts_from_pod(cmd, client[0], client[1])
            elif filesystem.does_file_exist_on_ms("{0}{1}".format(client[0], client[1])):
                res = shell.run_cmd_on_emp_or_ms(cmd)
                if res.rc == 0:
                    log.logger.debug("Successfully deleted the file: {0}".format(client[1]))
                else:
                    log.logger.debug("Failed to delete this file: {0}".format(client[1]))
