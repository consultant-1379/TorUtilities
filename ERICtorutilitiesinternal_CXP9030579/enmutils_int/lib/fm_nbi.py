# ********************************************************************
# Name    : FM North-bound Interface (NBI)
# Summary : Module for connecting and interacting with FM north bound
#           interface. Allows the user to connect to the FM NBI, sets
#           up the test client, create and subscribe to FM SNMP NBI
#           subscriptions.
# ********************************************************************


import os.path
import re
import shutil
import json
from time import sleep
import pexpect
from enmutils.lib.mutexer import mutex
from enmutils.lib import log, shell
from enmutils.lib.cache import (get_emp, get_ms_host, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP,
                                CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, is_emp, is_host_physical_deployment)
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.exceptions import ShellCommandReturnedNonZero, EnvironError
from enmutils_int.lib.enm_deployment import (get_service_ip, get_pod_hostnames_in_cloud_native,
                                             get_cloud_members_ip_address)
from enmutils_int.lib.services import deployment_info_helper_methods
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

IPv4, IPv6 = range(2)
CMD_GET_SUBSCRIPTIONS_IDS = 'cd /opt/ericsson/com.ericsson.oss.nbi.fm/test_client/; ./testclient.sh subscriptionData'
CMD_UNSUBSCRIBE_NBI_SUBSCRIPTION = 'cd /var/tmp/test_client;{0}testclient.sh unsubscribe id {1} nshost {2}'
CMD_KILL_TESTCLIENT_1 = "ps -ef | grep testclient | grep -v grep | awk '{print $2}' | xargs -r kill 15"
CMD_KILL_TESTCLIENT_2 = "ps -ef | grep corbaserver-testClient | grep -v grep | awk '{print $2}' | xargs -r kill 15"
CMD_REMOVE_FOLDER = "rm -rf {export_file}"
FM_SNMP_NBI_CREATE = "fmsnmp create v2c -n {name} -ip {ip} -cm {community} -as unlocked"
FM_SNMP_NBI_GET = "fmsnmp get nmslist"
FM_SNMP_NBI_DELETE = "fmsnmp delete -n {name}"


class FmNbi(object):
    IP = ''
    WORKLOAD_VM_IP = ''
    VISINAMINGPUB_IP = []
    NBALARMIRP = []
    NBFMSNMP = []
    SRCDIR = '/opt/ericsson/enmutils/.env/lib/python2.7/site-packages/enmutils_int/external_sources/scripts/test_client/'

    command_1f1 = ('cd {0};(/bin/sh testclient.sh subscribe category 1f1 detectOutOfOrder false nshost {1} clientIp {2} port {3} filter \"\'{4}\' ~ \\$f\" subscriptionTime {5} &> /dev/null &)')
    command_1z1 = ('cd {0};(/bin/sh testclient.sh subscribe category 1z1 detectOutOfOrder false nshost {1} clientIp {2} port {3} filter \"\'{4}\' ~ \\$f\" subscriptionTime {5} &> /dev/null &)')
    SRCDIR_ON_NBI_VM = "/opt/ericsson/com.ericsson.oss.nbi.fm/test_client/"
    DSTDIR = '/var/tmp/test_client/'
    PORTS = []
    number_ports_used = 0
    NUMBER_FILTERS_USED = 0
    USER = 'cloud-user'
    PASSWORD = 'passw0rd'
    PHYSICAL_KEYPAIR = '/root/.ssh/vm_private_key'
    child = None
    CHANNEL_FLAG = False
    SNMP_SUBSCRIPTION_NAME = "snmpSub{0}"
    SNMP_COMMUNITY_STRING = "snmpCommunity{0}"

    def __init__(self, user, timeout=None, ip=None, ports=0, snmp_subs_count=0):
        """
        Initializes FM NBI instance
        :param user: Object to be used for CRUD operations
        :type user: `enmutils.lib.enm_user_2.User`
        :param timeout: timeout to run commands
        :type timeout: int
        :param ip: Type of IP address to use: IPv4 or IPV6
        :type ip: enumerate
        :param ports: Number of ports used. One for each FM NBI subscription
        :type ports: int
        :param snmp_subs_count: number of snmp subscriptions to create
        :type snmp_subs_count: int
        """
        self.user = user
        self.timeout = timeout
        self.IP = ip
        self.PORTS = list(range(ports))
        for port in self.PORTS:
            self.PORTS[port] = self.PORTS[port]
        log.logger.debug("List of ports used by FM NBI: " + str(self.PORTS))
        self.snmp_subs_list = range(snmp_subs_count)
        self.PHYSICAL = self.CLOUD = self.CLOUD_NATIVE = False
        self.check_deployment_type()

    def check_deployment_type(self):
        """
        Checks for the deployment type and modifies the class variables as required
        """
        if is_host_physical_deployment():
            self.PHYSICAL = True
        elif is_emp():
            self.CLOUD = True
        else:
            self.CLOUD_NATIVE = True

    @property
    def is_nbi_framework_ok(self):
        """
        if the NHM Framework is set which the necessary values

        :return: The NBI Framework status
        :rtype: bool
        """
        return len(self.NBALARMIRP) > 0 and self.WORKLOAD_VM_IP != '' and len(self.VISINAMINGPUB_IP) > 0

    @property
    def _is_ipv4(self):
        """
        It return if IPv4 address are used

        :return: if testclient run with IPv4 addresses
        :rtype: bool
        """
        return self.IP == IPv4

    @property
    def _is_ipv6(self):
        """
        Checks if provided IP is IPv6
        :return: True if IPv6, False if not
        :rtype: bool
        """
        return self.IP == IPv6

    def _get_ip_of_service(self, service_name):
        """
        It gets the clients IPv4 address
        :param service_name: service name for which IP needs to be fetched
        :type service_name: str
        :return: IP address for the provided service name
        :rtype: list
        """
        log.logger.debug('Trying to get Service IP address')
        if self.CLOUD_NATIVE:
            service_ip = get_pod_hostnames_in_cloud_native(service_name)
        elif self.CLOUD:
            service_ip = get_cloud_members_ip_address(service_name)
        else:
            interface = 'internal' if 'nbfmsnmp' in service_name else 'services'
            service_ip = get_service_ip(service_name, interface=interface).split(',')
        log.logger.info("Service name is {0} and the ip is {1}".format(service_name, service_ip))
        return service_ip

    def _nbalarmirp_ip(self):
        """
        It returns the nbalarmirp IP address

        :return: IP of nbalarmirp
        :rtype: str
        """
        ip_list = self.NBALARMIRP
        for ip in ip_list:
            return ip

    def get_workload_vm_ip(self):
        """
        Get workload vm ip and set it to the class variable
        """
        try:
            response = shell.run_local_cmd(shell.Command("hostname -i"))
            self.WORKLOAD_VM_IP = str(response.stdout).strip()
            log.logger.info("Workload VM response: {0}".format(response.stdout))
        except Exception:
            raise EnvironError("Workload VM IP could not be found")

    def create_nbi_framework(self):
        """
        Gets the IPs necessary for the creation of FM NBI subscriptions: client_ip, workload_vm_ip, nbalarmrip and visinamingpub_ip
        :raises EnvironError: if visinamingpub or the nbalarmirp could not be found
        :raises EnmApplicationError: if nbalarmirp IP is not found
        :raises EnmApplicationError: if visinamingnb public IP is not found
        """
        self.get_workload_vm_ip()
        if self._is_ipv4:
            try:
                self.NBALARMIRP = self._get_ip_of_service('nbalarmirp')
                log.logger.info("NBALARMIRP IPs are {0}".format(self.NBALARMIRP))
            except Exception:
                raise EnmApplicationError("NbAlarmIrp IP could not be found")
            try:
                self.VISINAMINGPUB_IP = self._get_ip_of_service('visinamingnb')
                log.logger.info("VISINAMINGNB Public IP is {0}".format(self.VISINAMINGPUB_IP))
            except Exception:
                raise EnmApplicationError("VisinamingNb public IP could not be found")
            if not (len(self.NBALARMIRP) > 0 and len(self.VISINAMINGPUB_IP) > 0):
                raise EnvironError("Either of the services or both of them are not available, nbalarmirp : {0}, "
                                   "visinamingNb : {1}".format(self.NBALARMIRP, self.VISINAMINGPUB_IP))
        else:
            log.logger.debug("Profile not prepared to use IPv6 addresses")

    def fetch_snmp_nbi_service_ip(self):
        """
        Fetches the FM SNMP NBI service IP
        :return: snmp nbi service IP address
        :rtype: list
        """
        try:
            snmp_nbi_service = "nbfmsnmp"
            self.NBFMSNMP = self._get_ip_of_service(snmp_nbi_service)
            log.logger.info("nbfmsnmp IPs are {0}".format(self.NBFMSNMP))
        except Exception as e:
            log.logger.debug("Exception encountered while fetching nbfmsnmp service IP : {0}".format(e))
        return self.NBFMSNMP

    def reset_ports(self):
        """
        Resets number of ports to 0
        """
        self.number_ports_used = 0

    def reset_num_filters(self):
        """
        Resets number of filters to 0
        """
        self.NUMBER_FILTERS_USED = 0

    def check_test_client_exist(self):
        """
        It checks and copies the testclient files
        """
        src_files = os.listdir(self.SRCDIR)
        if os.path.exists(self.DSTDIR):
            log.logger.debug(self.DSTDIR + ' folder found in system')
            for file_profile in src_files:
                if not os.path.exists(self.DSTDIR + file_profile):
                    self.copy_test_client_file(self.SRCDIR + file_profile)
                    log.logger.info("File {0} copied to '/var/tmp/test_client/{0}'".format(self.SRCDIR + file_profile))
                else:
                    log.logger.info("File {0} already in '/var/tmp/test_client/{0}'".format(self.SRCDIR + file_profile))
        else:
            self.create_dir()
            self.copy_test_client_files()

    def create_dir(self):
        """
        It created the destination folder for the testclient files
        """
        if os.path.exists(self.DSTDIR):
            log.logger.debug("Folder " + self.DSTDIR + " exists")
        else:
            log.logger.debug("folder" + self.DSTDIR + " does not exist")
            dir_profile = os.path.dirname(self.DSTDIR)
            os.makedirs(dir_profile)

    def create_test_client_dir_on_ms_or_emp(self):
        """
        It created the testclient directory on the ms (or emp in the case of a cloud environment)
        """
        dir_profile = " /bin/mkdir -p {0}".format(self.DSTDIR)
        if self.CLOUD:
            shell.run_cmd_on_vm(dir_profile, get_emp())
            log.logger.debug("{0} folder created on emp".format(dir_profile))
        if self.PHYSICAL:
            shell.run_cmd_on_ms(dir_profile)
            log.logger.debug("{0} folder created on ms".format(dir_profile))

    def remove_test_client_dir_on_ms_or_emp(self):
        """
        It removes the testclient folder from the ms or emp if it is a cloud environment
        """
        if self.CLOUD:
            shell.run_cmd_on_vm(shell.Command(CMD_REMOVE_FOLDER.format(export_file=self.DSTDIR), timeout=60 * 1),
                                get_emp())
        elif self.PHYSICAL:
            shell.run_cmd_on_ms(shell.Command(CMD_REMOVE_FOLDER.format(export_file=self.DSTDIR), timeout=60 * 1))
        else:
            log.logger.debug("Deployment is a cloud-native type, no need to remove the files")

    def return_test_client_files_from_nbalarmirp_vm(self, child):
        """
        It returns the testclient files from nbalarmirp
        :raises ShellCommandReturnedNonZero: if failed to transfer files from nbalarmirp to EMP
        :raises EnvironError: if failed to transfer files from nbalarmirp to MS
        :param child: emote shell terminal to execute commands spawned using pexpect
        :type child: pexpect.spawn
        """
        ip = self.NBALARMIRP[0]
        cmd = "scp -r -i {keypair} -o stricthostkeychecking=no {user}@nbalarmirp_ip:/opt/ericsson/com.ericsson.oss.nbi.fm/test_client/* {destination}".format(
            keypair=CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP if self.CLOUD else self.PHYSICAL_KEYPAIR,
            user=self.USER, destination=self.DSTDIR)
        if self.CLOUD:
            cmd_response = shell.run_cmd_on_vm(cmd.replace('nbalarmirp_ip', str(ip)), get_emp())
            if cmd_response.rc != 0:
                self.NBALARMIRP[0], self.NBALARMIRP[1] = self.NBALARMIRP[1], self.NBALARMIRP[0]
                ip = self.NBALARMIRP[0]
                log.logger.debug('Retry for other Nbalarmirp {0}'.format(ip))
                cmd_response = shell.run_cmd_on_vm(cmd.replace('nbalarmirp_ip', str(ip)), get_emp())
                if cmd_response.rc != 0:
                    raise ShellCommandReturnedNonZero("Failed to transfer files from Nbalarmirp to emp.", cmd_response)
            log.logger.info("Test Client files have been transferred to {0} on emp".format(self.DSTDIR))
        if self.PHYSICAL:
            try:
                child.sendline(cmd.replace('nbalarmirp_ip', str(ip)))
                response = child.expect(["root@ieatlms", pexpect.EOF], timeout=120, searchwindowsize=-1)
                if not response:
                    self.NBALARMIRP[0], self.NBALARMIRP[1] = self.NBALARMIRP[1], self.NBALARMIRP[0]
                    ip = self.NBALARMIRP[0]
                    log.logger.debug('Retry for other Nbalarmirp {0}'.format(ip))
                    child.sendline(cmd.replace('nbalarmirp_ip', str(ip)))
                    child.expect(["root@ieatlms", pexpect.EOF], timeout=120, searchwindowsize=-1)
                log.logger.info("Test Client files have been transferred to {0} on ms".format(self.DSTDIR))
            except Exception as e:
                raise EnvironError("Failed to transfer files from nbalarmirp to ms. Exception: {0}".format(e))

    @staticmethod
    def check_and_remove_old_files(dir_path):
        """
        It removes old testclient files if found in the dir_path location
        :param dir_path: path where the testclient files are located
        :type dir_path: str
        """
        remove_old_files = shell.run_local_cmd(
            shell.Command("/usr/bin/find {workload_dir}* -delete".format(workload_dir=dir_path), timeout=60 * 1))
        log.logger.info("Older Test Client files have been removed from {0} on workload vm".format(dir_path))
        if not remove_old_files:
            log.logger.debug("Older Test client files were not successfully removed")

    def transfer_test_client_files_to_workload_vm(self):
        """
        It transfers the testclient files from the ms (or emp) to the Workload VM
        """
        self.check_and_remove_old_files(self.SRCDIR)
        if self.CLOUD:
            cmd = "scp -r -i {0} -o stricthostkeychecking=no {1}@{2}:{3}* {4}".format(
                CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM,
                self.USER, get_emp(), self.DSTDIR, self.SRCDIR)
            workload_transfer_files = shell.run_local_cmd(cmd)
        elif self.CLOUD_NATIVE:
            workload_transfer_files = shell.copy_file_between_wlvm_and_cloud_native_pod(self.NBALARMIRP[0],
                                                                                        self.SRCDIR_ON_NBI_VM,
                                                                                        self.SRCDIR, 'from')
        else:
            cmd = "scp -r -o stricthostkeychecking=no root@{0}:{1}* {2}".format(get_ms_host(), self.DSTDIR, self.SRCDIR)
            workload_transfer_files = shell.run_local_cmd(cmd)
        if workload_transfer_files.rc != 0:
            log.logger.info("Test client files were not successfully copied up to the Workload VM")
        else:
            log.logger.info("Test client files were successfully copied up to the Workload VM")
        self.remove_test_client_dir_on_ms_or_emp()

    def transfer_files_to_ms_or_emp(self):
        """
        It transfers the testclient files to the ms
        """
        if not self.CLOUD_NATIVE:
            self.create_test_client_dir_on_ms_or_emp()
            child = GenericFlow.switch_to_ms_or_emp()
            self.return_test_client_files_from_nbalarmirp_vm(child)
        self.transfer_test_client_files_to_workload_vm()
        self.clear_test_client_folder_on_workload_vm()

    def clear_test_client_folder_on_workload_vm(self):
        """
        It deletes the testclient folder from the Workload VM
        """
        shell.run_local_cmd(shell.Command(CMD_REMOVE_FOLDER.format(export_file=self.DSTDIR), timeout=60 * 1))
        log.logger.debug("{0} folder removed on workload vm".format(self.DSTDIR))

    def copy_test_client_file(self, srcfile):
        """
        Copies the testclient files in the destination folder
        :param srcfile: Source file where testclient files are located
        :type srcfile: str
        """
        shutil.copy(srcfile, self.DSTDIR)
        log.logger.debug("File '{0}' copied in /var/tmp/test_client/'".format(srcfile))

    def copy_test_client_files(self):
        """
        Copies the testclient files from the SRCDIR to the DSTDIR location
        """
        FILES = os.listdir(self.SRCDIR)
        for file_profile in FILES:
            self.copy_test_client_file(self.SRCDIR + file_profile)
            log.logger.info('Files transferred to the destination directory: {0}'.format(self.SRCDIR + file_profile))

    def subscribe_nbi(self, timeout=20, nbi_filters=None):
        """
        It creates FM NBI subscriptions using testclient
        :raises EnvironError: if failed to create CORBA subscriptions
        :param timeout: Timeout to run the local command
        :type timeout: int
        :param nbi_filters: List of CORBA NBI filters
        :type nbi_filters: list
        """
        num_of_filters = len(nbi_filters)
        with mutex('subscribe_nbi_variables'):
            if self.NUMBER_FILTERS_USED >= num_of_filters:
                self.NUMBER_FILTERS_USED = 0
                log.logger.debug("Num Filters is reset to : {0}".format(self.NUMBER_FILTERS_USED))
            log.logger.debug("Ports index : {0}, Filters index : {1}".format(self.number_ports_used,
                                                                             self.NUMBER_FILTERS_USED))
            port = self.PORTS[self.number_ports_used] + 5111
            nbi_filter = nbi_filters[self.NUMBER_FILTERS_USED]
            log.logger.debug("Port : {0}, Filter : {1}".format(port, nbi_filter))
            self.number_ports_used += 1
            self.NUMBER_FILTERS_USED += 1
            cmd = self.corba_sub_test(port, nbi_filter, timeout)
        try:
            shell.run_local_cmd(cmd)
        except:
            raise EnvironError('FM CORBA NBI Subscription not created')

    def corba_sub_test(self, port, nbi_filter, timeout):
        """
        It construct the shell command which is used to create FM NBI subscriptions
        :param port: port number
        :type port: int
        :param nbi_filter: List of CORBA NBI filters
        :type nbi_filter: list
        :param timeout: Timeout to run the local command
        :type timeout: int
        :return: command
        :rtype: str
        """
        if self.CLOUD_NATIVE:
            ip = deployment_info_helper_methods.get_cloud_native_service_vip("msfm")
        else:
            ip = self.VISINAMINGPUB_IP[0]
        if not self.CHANNEL_FLAG:
            cmd = shell.Command(self.command_1f1.format(self.DSTDIR, ip, self.WORKLOAD_VM_IP,
                                                        port, nbi_filter, timeout), allow_retries=False)
            self.CHANNEL_FLAG = True
        else:
            cmd = shell.Command(self.command_1z1.format(self.DSTDIR, ip, self.WORKLOAD_VM_IP,
                                                        port, nbi_filter, timeout), allow_retries=False)
            self.CHANNEL_FLAG = False
        return cmd

    def unsubscribe_nbi(self, id_subscription):
        """
        Unsubscribe the NBI subscription
        :param id_subscription:
        :type id_subscription: str
        """
        if self.CLOUD_NATIVE:
            ip = deployment_info_helper_methods.get_cloud_native_service_vip("msfm")
        else:
            ip = str(self.VISINAMINGPUB_IP[0])
        shell.run_local_cmd("chmod 755 {0}".format(self.DSTDIR + 'testclient.sh'))
        cmd = CMD_UNSUBSCRIBE_NBI_SUBSCRIPTION.format(str(self.DSTDIR), id_subscription, ip)
        response = shell.run_local_cmd(cmd)
        log.logger.debug("Unsubscribe command: {0}".format(cmd))
        log.logger.debug(str(response.stdout))
        log.logger.debug('Unsubscribed CORBA FM NBI subscription: {0}'.format(id_subscription))

    def unsubscribe_all_nbi(self, subscriptions):
        """
        Unsubscribe all active subscriptions
        :param subscriptions: List of subscriptions to unsubscribe
        :type subscriptions: list
        """
        log.logger.debug(str(subscriptions))
        num_of_subs = len(subscriptions)
        if num_of_subs:
            for subscription in subscriptions:
                self.unsubscribe_nbi(subscription)
        else:
            log.logger.debug('No FM CORBA NBI subscriptions to unsubscribe')

    def get_subscription_ids(self):
        """
        It returns all the filters and subscription IDs from a cluster

        :raises EnvironError: if unable to connect to nbalarmirp VM's
        :raises ShellCommandReturnedNonZero: if unable to fetch NBI subscription details
        :return: List of CORBA subscription filters and IDs
        :rtype: list
        """
        log.logger.debug('Checking subscriptions nbalarmirp cluster: ' + self.NBALARMIRP[0])
        key_pair = CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP if self.CLOUD else self.PHYSICAL_KEYPAIR
        cmd = "ssh -i {0} -o StrictHostKeyChecking=no {1}@{2} \"{3}\"".format(key_pair, self.USER, self.NBALARMIRP[0],
                                                                              CMD_GET_SUBSCRIPTIONS_IDS)
        try:
            if self.CLOUD_NATIVE:
                command_response = shell.run_cmd_on_cloud_native_pod('nbalarmirp1', self.NBALARMIRP[0],
                                                                     CMD_GET_SUBSCRIPTIONS_IDS)
            else:
                command_response = shell.run_cmd_on_emp_or_ms(cmd)
                if command_response.rc == 255 or command_response.rc == 1:
                    self.NBALARMIRP[0], self.NBALARMIRP[1] = self.NBALARMIRP[1], self.NBALARMIRP[0]
                    log.logger.debug('Checking subscriptions for another nbalarmirp cluster due to present nbalarmirp '
                                     'cluster is down: ' + self.NBALARMIRP[0])
                    cmd = "ssh -i {0} -o StrictHostKeyChecking=no {1}@{2} \"{3}\"".format(key_pair, self.USER,
                                                                                          self.NBALARMIRP[0],
                                                                                          CMD_GET_SUBSCRIPTIONS_IDS)
                    command_response = shell.run_cmd_on_emp_or_ms(cmd)
        except Exception as e:
            raise EnvironError('Unable to connect to NbalarmIrp VMs. Exception: {0}'.format(e))
        if command_response.rc == 0:
            log.logger.debug(str(command_response.stdout))
            subscriptions = re.findall(r'subscriptionId=(\d+)', command_response.stdout)
            filters = re.findall(r"filter='(.*)'.*", command_response.stdout)
            subscriptions_tuples = zip(filters, subscriptions)
            log.logger.debug("subscription filter and id tuples")
            log.logger.debug(str(subscriptions_tuples))
            num_of_subscriptions = len(subscriptions_tuples)
            if not num_of_subscriptions:
                log.logger.debug('No CORBA NBI subscription available: ' + str(self.NBALARMIRP[0]))
        else:
            raise ShellCommandReturnedNonZero(
                "Error trying to get the NBI subscriptions {0}: ".format(command_response.stdout),
                command_response)
        return subscriptions_tuples

    def print_info(self, subscriptions=None):
        """
        It prints out all profile information related to IP addresses involved in the testclient run
        :param subscriptions: The list of all subscriptions to close
        :type subscriptions: list
        """
        i = 0
        num_of_nbalarmirp_vm = len(self.NBALARMIRP)
        if self._is_ipv4:
            log.logger.info('FM CORBA NBI for IPv4')
            log.logger.info('VISINAMINGPUB_IPv4: {0}'.format(self.VISINAMINGPUB_IP))
            log.logger.info('Workload VM: {0}'.format(self.WORKLOAD_VM_IP))
            if num_of_nbalarmirp_vm:
                for nbalarmirp in self.NBALARMIRP:
                    log.logger.debug('NBALARMIRP_{0}_IPv4: '.format(str(i + 1)) + str(nbalarmirp))
                    i += 1
            else:
                log.logger.debug('No NBALARMIRP Group Service found')
        else:
            log.logger.debug('FM CORBA NBI for IPv6')
            log.logger.debug('VISINAMINGPUB_IPv6: {0}'.format(self.VISINAMINGPUB_IP))
            log.logger.debug('CLIENT_IPv6: {0}'.format(self.WORKLOAD_VM_IP))
            if num_of_nbalarmirp_vm:
                for nbalarmirp in self.NBALARMIRP:
                    log.logger.debug('NBALARMIRP_{0}_IPv6: '.format(str(i + 1)) + str(nbalarmirp))
                    i += 1
            else:
                log.logger.debug('No NBALARMIRP Group Service found')
        if subscriptions:
            log.logger.debug('List of Subscriptions: {0}'.format(subscriptions))
        else:
            log.logger.debug('No active FM CORBA NBI subscriptions found')

    @staticmethod
    def close():
        """
        Closes all the nbi subscriptions
        """
        response = shell.run_local_cmd(CMD_KILL_TESTCLIENT_1)
        log.logger.debug(str(response.stdout))
        response = shell.run_local_cmd(CMD_KILL_TESTCLIENT_2)
        log.logger.debug(str(response.stdout))

    def create_fm_snmp_nbi_subscriptions(self):
        """
        This method will create SNMP NBI subscriptions based on the number of SNMP subscriptions provided
        :raises EnmApplicationError if failed to create SNMP subscription
        """
        failed_subscriptions = {}
        num_of_snmp_subs = len(self.snmp_subs_list)
        self.get_workload_vm_ip()
        if num_of_snmp_subs:
            for snmp_sub in self.snmp_subs_list:
                name = self.SNMP_SUBSCRIPTION_NAME.format(snmp_sub)
                community = self.SNMP_COMMUNITY_STRING.format(snmp_sub)
                try:
                    response = self.user.enm_execute(FM_SNMP_NBI_CREATE.format(name=name, ip=self.WORKLOAD_VM_IP, community=community))
                    result = response.get_output()
                    if "fmsnmp create command executed" in result:
                        log.logger.debug("FM SNMP NBI subscription has been created with {0} name".format(name))
                    else:
                        failed_subscriptions[name] = result
                except Exception as e:
                    log.logger.debug("Exception raised while executing fmsnmp cli command : \n {0}".format(str(e)))
                sleep(30)
            num_of_failed_subs = len(failed_subscriptions.keys())
            if num_of_failed_subs:
                log.logger.debug("Failed SNMP subscriptions and their responses : \n {0}".format(failed_subscriptions))
                raise EnmApplicationError("Failed to create SNMP subscriptions : {0}".format(failed_subscriptions.keys()))
        else:
            log.logger.debug("No SNMP subscriptions to create")

    def get_fm_snmp_nbi_subscriptions(self):
        """
        This method will fetch the SNMp NBI subscriptions created by the profile
        :return: returns the SNMP NBI subscription names
        :rtype: list
        """
        subscriptions = []
        response = self.user.enm_execute(FM_SNMP_NBI_GET, timeout_seconds=120)
        response_string = "\n".join(response.get_output())
        match_pattern = re.compile(r'.* instance')
        if match_pattern.search(response_string) is not None:
            num_of_existing_subs = int(re.split('(.*?) instance.*', response_string)[1])
            if num_of_existing_subs:
                json_string = json.dumps(response.get_output())
                subscriptions = re.findall(self.SNMP_SUBSCRIPTION_NAME.format(r'\d{1,2}'), json_string)
                log.logger.debug("Subscriptions found on the system : {0}".format(subscriptions))
            else:
                log.logger.debug("No active SNMP NBI subscriptions are present on the system")
        return subscriptions

    def delete_fm_snmp_nbi_subscriptions(self, subscriptions):
        """
        This method will delete the SNMP NBI subscriptions which were created by the profile
        :param subscriptions: SNMP NBI subscription names
        :type subscriptions: list
        """
        for sub in subscriptions:
            response = self.user.enm_execute(FM_SNMP_NBI_DELETE.format(name=sub), timeout_seconds=120)
            resp_output = response.get_output()
            if "subscription {0} deleted".format(sub) in resp_output:
                log.logger.debug("FM SNMP NBI subscription with name {0} has been deleted".format(sub))
            else:
                log.logger.debug("Failed to delete SNMP subscription {0}, Response : {1}".format(sub, resp_output))
            log.logger.debug("Sleeping for 60 seconds before trying to delete the next subscription")
            sleep(60)

    def snmp_nbi_teardown(self):
        """
        SNMP NBI Teardown
        """
        if self.NBFMSNMP:
            subscriptions = self.get_fm_snmp_nbi_subscriptions()
            log.logger.debug("Sleeping for 60 seconds before deleting the SNMP_NBI subscriptions")
            sleep(60)
            if subscriptions:
                self.delete_fm_snmp_nbi_subscriptions(subscriptions)
        else:
            log.logger.info("NBFMSNMP service is not available to teardown SNMP subscriptions")

    def corba_nbi_teardown(self, filters=None):
        """
        CORBA NBI Teardown
        :param filters: List of filters
        :type filters: list
        """
        if self.is_nbi_framework_ok:
            subscriptions_tuples = self.get_subscription_ids()
            subscriptions_to_delete = [subscription for nbi_filter, subscription in subscriptions_tuples if nbi_filter in filters]
            self.close()
            if subscriptions_to_delete:
                log.logger.debug("Subscriptions to un-subscribe: {0}".format(subscriptions_to_delete))
                self.print_info(subscriptions_to_delete)
                self.unsubscribe_all_nbi(subscriptions_to_delete)
        else:
            log.logger.info("CORBA NBI service is not available to teardown CORBA subscriptions")

    def teardown(self, filters=None):
        """
        This will teardown the profile un-subscribing all CORBA and SNMP NBI subscriptions
        :param filters: List of filters
        :type filters: list
        """
        # SNMP NBI Teardown
        self.snmp_nbi_teardown()
        # CORBA NBI Teardown
        self.corba_nbi_teardown(filters=filters)
