import time
from datetime import datetime

import pexpect

from enmutils.lib import log, shell
from enmutils.lib.cache import (CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP,
                                get_emp, get_ms_host, is_emp, is_enm_on_cloud_native)
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.shell import DEFAULT_VM_SSH_KEYPATH
from enmutils_int.lib.enm_deployment import get_enm_service_locations
from enmutils_int.lib.helper_methods import generate_basic_dictionary_from_list_of_objects
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow


class Shm45Flow(ShmFlow):

    SERVICE_NAME = "smrsserv"
    SERVICE_HOST = None
    SLEEP_TIMES = {"SGSN-MME": 170, "FRONTHAUL-6020": 1, "MGW": 45, "DSC": 350, "MTAS": 170}
    SLEEP_TIMES_SERV = {"SGSN-MME": 80, "FRONTHAUL-6020": 0, "MGW": 30, "DSC": 150, "MTAS": 80}
    SLEEP = None
    NE_TYPE = None

    def execute_flow(self):
        """
        Executes SHM_45 Backup profile flow
        """
        self.state = "RUNNING"
        node_attributes = ["node_id", "node_ip", "netsim", "primary_type", "simulation", "node_name", "poid"]
        nodes_dict = generate_basic_dictionary_from_list_of_objects(
            self.get_nodes_list_by_attribute(node_attributes=node_attributes), "primary_type")

        while self.keep_running():
            try:
                self.sleep_until_time()
                self.check_and_update_pib_values_for_backups()
                self.set_smrs_filetransfer_service_location()
                if is_enm_on_cloud_native():
                    self.install_zip_on_pod()
                self.perform_iteration_actions(nodes_dict)
            except Exception as e:
                self.add_error_as_exception(e)

    def set_smrs_filetransfer_service_location(self):
        """
        Fetches smrsserv/filetransferservice details
        """
        try:
            self.SERVICE_HOST = get_enm_service_locations(self.SERVICE_NAME)[0]
        except EnvironError:
            self.SERVICE_NAME = "filetransferservice"
            self.SERVICE_HOST = get_enm_service_locations(self.SERVICE_NAME)[0]

    def perform_iteration_actions(self, nodes_dict):
        """
        Creates the backup folders according to nodes' primary type.
        It also creates backup files in the created folder of provided size

        :type nodes_dict: dict
        :param nodes_dict: Nodes based on type

        :raises EnvironError: when flow goes to unexpected state
        """
        for node_type in nodes_dict:
            nodes = nodes_dict.get(node_type)
            num_nodes = len(nodes)
            node_string = " ".join([node.node_name for node in nodes])
            folder_path = "/home/smrs/smrsroot/backup/{0}/".format(node_type.lower())
            create_folder_cmd = ("for i in {0};do mkdir -p {1}$i;chown -R jboss_user:mm-smrsusers {1}$i;sleep 2;done"
                                 .format(node_string, folder_path))
            datetime_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            backupinfoxml = (('<?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?><backup name=\\"${{i}}_{0}.backup\\" '
                              'version=\\"1\\" xmlns:xsi=\\"http://www.w3.org/2001/XMLSchema-instance\\" '
                              'xsi:noNamespaceSchemaLocation=\\"backupinfo.xsd\\"><creationTime>{0}</creationTime>'
                              '<userLabel></userLabel><type>System Local Data</type>'
                              '<creationType>MANUAL</creationType>'
                              '<domain>System Local</domain><managedElement '
                              'dnPrefix=\\"SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,MeContext=$i\\" '
                              'id=\\"$i\\" release=\\"1.5\\" siteLocation=\\"\\" type=\\"{1}\\"></managedElement>'
                              '<softwareInventory><softwareVersion productName=\\"$i\\" productNumber=\\"AVA90129/9\\" '
                              'productRevision=\\"R4A\\" productionDate=\\"{0}\\" description=\\"$i\\" '
                              'type=\\"{1}\\">$i-AVA90129/9-R4A</softwareVersion></softwareInventory>'
                              '<exportTime>{0}</exportTime></backup>')
                             .format(datetime_str, node_type))
            create_backup_cmd = ('head -c {1} /dev/urandom > {2}dummy;for i in {0};'
                                 'do cp {2}dummy {2}$i/${{i}}_{3}.backup;printf "{4}" > {2}$i/backupinfo.xml;'
                                 'zip -0 -mj {2}$i/${{i}}_{3} {2}$i/${{i}}_{3}.backup {2}$i/backupinfo.xml;'
                                 'chown -R jboss_user:mm-smrsusers {2}$i;sleep {5};ls -larth {2}$i;done;rm -f {2}dummy'
                                 .format(node_string, self.BACKUP_SIZES.get(node_type),
                                         folder_path, datetime_str, backupinfoxml, self.SLEEP_TIMES_SERV.get(node_type)))
            self.SLEEP = self.SLEEP_TIMES[node_type]
            self.NE_TYPE = node_type
            log.logger.debug("Performing iteration actions on {0} nodes in path - {1} on {2}"
                             .format(node_type, folder_path, self.SERVICE_HOST))
            self.execute_cmd_on_host(create_folder_cmd, create_backup_cmd, num_nodes)

    def execute_cmd_on_host(self, create_folder_cmd, create_backup_cmd, num_nodes):
        """
        Executes command on smrsserv/filetransferservice based on the deployment type

        :type create_folder_cmd: Command to create folders
        :param create_folder_cmd: str
        :type create_backup_cmd: Command to create backups
        :param create_backup_cmd: str
        :type num_nodes: Number of nodes
        :param num_nodes: int

        :raises EnvironError: when any command execution fails
        """
        try:
            if is_emp():
                log.logger.debug("Connecting to EMP")
                child = pexpect.spawn("ssh -i {0} cloud-user@{1}".format("/var/tmp/enm_keypair.pem", get_emp()))
                time.sleep(1)
                rc = child.expect(["emp", pexpect.TIMEOUT, pexpect.EOF])
                if rc != 0:
                    raise EnvironError("Can't connect to EMP because {0} \nBefore:{1} \nAfter:{2}"
                                       .format(rc, child.before, child.after))
                log.logger.debug("Connecting to {0} - {1}".format(self.SERVICE_NAME, self.SERVICE_HOST))
                child.sendline("ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i {0} cloud-user@{1}"
                               .format(CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP, self.SERVICE_HOST))
                self.execute_on_service_vm(child, create_folder_cmd, create_backup_cmd, num_nodes)
            elif is_enm_on_cloud_native():
                timeout_value = (num_nodes * 110) + 110
                log.logger.debug("Starting folder creation")
                response = shell.run_cmd_on_cloud_native_pod(self.SERVICE_NAME, self.SERVICE_HOST, create_folder_cmd,
                                                             suppress_error=False, timeout=timeout_value)
                if response.rc != 0:
                    raise EnvironError(
                        "Unexpected response while executing create folder command. Stdout - {0} \n Return code - {1}"
                        .format(response.stdout, response.rc))
                log.logger.debug("Starting backups' creation")
                response = shell.run_cmd_on_cloud_native_pod(self.SERVICE_NAME, self.SERVICE_HOST, create_backup_cmd,
                                                             suppress_error=False, timeout=timeout_value)
                if response.rc != 0:
                    raise EnvironError(
                        "Unexpected response while executing create backup command. Stdout - {0} \n Return code - {1}"
                        .format(response.stdout, response.rc))
                log.logger.debug("Backups' creation successfully completed on {0} pod".format(self.SERVICE_HOST))
            else:
                log.logger.debug("Connecting to LMS")
                child = pexpect.spawn(
                    "ssh  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@{0}"
                    .format(get_ms_host()))
                rc = child.expect(["root", pexpect.TIMEOUT, pexpect.EOF])
                if rc != 0:
                    raise EnvironError(
                        "Cannot connect to LMS because {0} \n Before:{1} \n After:{2}"
                        .format(rc, child.before, child.after))
                time.sleep(1)

                log.logger.debug("Connecting to {0}".format(self.SERVICE_NAME))
                child.sendline(
                    "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i {0} cloud-user@{1}"
                    .format(DEFAULT_VM_SSH_KEYPATH, self.SERVICE_HOST))

                self.execute_on_service_vm(child, create_folder_cmd, create_backup_cmd, num_nodes)
        except Exception as e:
            raise EnvironError("Exception: {0}".format(e.message))

    def execute_on_service_vm(self, child, create_folder_cmd, create_backup_cmd, num_nodes):
        """
        Executes command on the service vm (smrsserv/filetransferservice) using pexpect child object

        :type child: pexpect child object
        :param child: pexpect.spawn
        :type create_folder_cmd: Command to create folder
        :param create_folder_cmd: str
        :type create_backup_cmd: Command to create backups
        :param create_backup_cmd: str
        :type num_nodes: Number of nodes
        :param num_nodes: int

        :raises EnvironError: when any command execution fails
        """
        time.sleep(1)
        rc = child.expect([self.SERVICE_NAME, pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnvironError("Can't connect to {0} because {1} \n Before:{2} \n After:{3}"
                               .format(self.SERVICE_NAME, rc, child.before, child.after))
        log.logger.debug("Switching to root user on {0} - {1}".format(self.SERVICE_NAME, self.SERVICE_HOST))
        child.sendline("sudo su")
        time.sleep(1)
        rc = child.expect(["root", pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnvironError("Can't switch to root on {0} because {1} \n Before:{2} \n After:{3}"
                               .format(self.SERVICE_NAME, rc, child.before, child.after))
        time.sleep(1)
        log.logger.debug("Starting folders' creation on {0}.\nExecuting following command - {1}"
                         .format(self.SERVICE_HOST, create_folder_cmd))
        # Create folders for each node
        child.sendline(create_folder_cmd)
        log.logger.debug("Sleeping for {0} seconds, {1} nodes, 2 secs/node".format((num_nodes * 2) + 10, num_nodes))
        time.sleep((num_nodes * 2) + 10)
        rc = child.expect(["root", pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnvironError(
                "Couldn't execute create folders' command on {0} because {1} \n Before:{2} \n After:{3}"
                .format(self.SERVICE_HOST, rc, child.before, child.after))
        log.logger.debug("Folders' creation successfully completed on {0}.".format(self.SERVICE_HOST))
        log.logger.debug("Starting backup files' creation on {0}.\nExecuting the following command - \n{1}"
                         .format(self.SERVICE_HOST, create_backup_cmd))
        # Create backup files for each node
        child.sendline(create_backup_cmd)
        total_sleep = (num_nodes * self.SLEEP) + 40
        hours, remainder = divmod(total_sleep, 3600)
        minutes, seconds = divmod(remainder, 60)
        log.logger.debug("For {0} {1} nodes, {2} secs/node, total sleep - {3} i.e. {4} hours {5} minutes {6} seconds"
                         .format(num_nodes, self.NE_TYPE, self.SLEEP, total_sleep, hours, minutes, seconds))
        time.sleep(total_sleep)
        rc = child.expect(["root", pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnvironError(
                "Couldn't execute create backup file command {0} \n Before:{1} \n After:{2}"
                .format(rc, child.before, child.after))
        log.logger.debug("Backups' creation successfully completed on {0}".format(self.SERVICE_HOST))
        child.terminate()

    def install_zip_on_pod(self):
        """
        Installs zip executable on smrs/filetransferserv pod
        """
        install_zip_cmd = "zypper -n install zip"
        response = shell.run_cmd_on_cloud_native_pod(self.SERVICE_NAME, self.SERVICE_HOST, install_zip_cmd,
                                                     suppress_error=False)
        if response.rc != 0:
            self.add_error_as_exception(EnvironError(
                "Unexpected response while installing zip by using {0}.\nStdout - {1}\nReturn code - {2}"
                .format(install_zip_cmd, response.stdout, response.rc)))
