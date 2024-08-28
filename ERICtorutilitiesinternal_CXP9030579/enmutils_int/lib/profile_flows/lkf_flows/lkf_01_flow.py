import re
import time
import pexpect
from retrying import retry

from enmutils.lib import log, arguments
from enmutils.lib.cache import get_ms_host
from enmutils.lib.exceptions import EnvironError, EnvironWarning, NetsimError
from enmutils.lib.filesystem import does_remote_file_exist
from enmutils.lib.shell import run_cmd_on_ms, Command, run_cmd_on_vm, run_remote_cmd
from enmutils_int.lib.cmcli import execute_command_on_enm_cli
from enmutils_int.lib.enm_deployment import get_enm_service_locations
from enmutils_int.lib.lkf import LkfJob
from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow import EnmCli08Flow
from enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow import SAS_MANUAL_SETUP_PAGE
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm
from enmutils_int.lib.services.profilemanager_adaptor import timestamp
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

SAS_USERNAME = "root"
SAS_PASSWORD = "shroot"
SRCDIR = "/ericsson/enm/dumps/"
CERT_DIR = "/ericsson/credm/data/certs/"
KEY_PATH = "/ericsson/tor/data/shm"
KEY_FILE = "{0}/sftp/sftp_key.pub".format(KEY_PATH)
KEY_GEN = "bash ne_software_store_configuration.bsh --generate_keys"
FILE_NAME = "authorized_keys"
PEM_FILE = "cas_sim_ca_cert.pem"
IMPORT_CERT_CMD = "sudo keytool -importcert -file {0}{1} -keystore shmIL-trustStore.jks -storepass athlone -noprompt " \
                  "-alias cascert".format(SRCDIR, PEM_FILE)
DELETE_CERT_CMD = "sudo keytool -delete -alias cascert -keystore shmIL-trustStore.jks -storepass athlone -noprompt"
IMPORT_CERT_CMD_SAS = "keytool -importcert -keystore simcastrust.p12 -file {0}.cer -storetype PKCS12"
GENERATE_PEM_FILE = "openssl pkcs12 -in elis_sim_root_ca.p12 -out {0} -clcerts -nokeys".format(PEM_FILE)
GENERATE_PEM_FILE_PWD = "athlone"
SET_ADMIN_STATE_LOCK_CMD = "cmedit set {0} administrativeState=LOCKED"
SET_ADMIN_STATE_UNLOCK_CMD = "cmedit set {0} administrativeState=UNLOCKED"
SSH_DIR = "/home/enmuser/.ssh/"
JOB_NAME = "CapacityExpansionLicenseJob"


class Lkf01Flow(ShmFlow):

    SAS_IP = None
    CLEANUP = None

    def cleanup_imported_keys_on_shmserv(self, shmserv_hostnames):
        """
        Deletes imported keys from shm keystore

        :param shmserv_hostnames: List of shm_serv hostnames (strings)
        :type shmserv_hostnames: list
        """
        log.logger.debug("Attempting to delete imported keys in shm keystore")
        for shm_serv in shmserv_hostnames:
            delete_cmd_response = run_cmd_on_vm(Command("cd {0}; {1}".format(CERT_DIR, DELETE_CERT_CMD)),
                                                vm_host=shm_serv)
            response_check = "keytool error: java.lang.Exception: Alias <cascert> does not exist"
            if delete_cmd_response.rc != 0 and response_check not in delete_cmd_response.stdout:
                log.logger.debug("As {0} cert deletion failed, we are retrying by sleeping for 5 "
                                 "seconds".format(PEM_FILE))
                time.sleep(5)
                delete_cmd_response = run_cmd_on_vm(Command("cd {0}; {1}".format(CERT_DIR, DELETE_CERT_CMD)),
                                                    vm_host=shm_serv)
                if delete_cmd_response.rc != 0 and response_check not in delete_cmd_response.stdout:
                    self.add_error_as_exception(EnvironError("{0} cert deletion failed in {1}. Reason {2}"
                                                             .format(PEM_FILE, shm_serv, delete_cmd_response.stdout)))
            if delete_cmd_response.rc == 0:
                log.logger.debug("Successfully deleted {0} cert in {1}".format(PEM_FILE, shm_serv))

    def execute_and_check_lkf_job(self, user, nodes_list):
        """
        Executes the Capacity Expansion License job on node from netsim and check the job in UI

        :type user: `enm_user_2.User`
        :param user: User executes the command on ENM
        :type nodes_list: list
        :param nodes_list: `lib.enm_node.Node` instance
        """
        current_time = timestamp.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
        log.logger.debug("current time to validate lkf jobs in UI as job start time is {0}".format(current_time))
        lkf_job = LkfJob(user, nodes_list, job_type="LICENSE_REQUEST", name="CapacityExpansionLicenseJob",
                         current_time=current_time)
        lkf_job.update_pib_parameters(self.SAS_IP)
        try:
            lkf_job.execute_il_netsim_cmd_on_nodes(nodes_list)
        except NetsimError as e:
            self.add_error_as_exception(e)
        log.logger.debug("Sleeping for 10 min before checking the job in UI")
        time.sleep(10 * 60)
        lkf_job.check_lkf_job_status()

    def import_sas_key_to_shmserv(self, shmserv_hostnames):
        """
        Importing cert on all instances of shmserv using PEM file of SAS

        :param shmserv_hostnames: List of shm_serv hostnames (strings)
        :type shmserv_hostnames: list
        :raises EnvironError: If importing key file on shm_serv fails
        """
        log.logger.debug("Attempting to import keys to shmserv keystore")
        self.CLEANUP = True
        for shm_serv in shmserv_hostnames:
            import_cmd_response = run_cmd_on_vm(Command("cd {0}; {1}".format(CERT_DIR, IMPORT_CERT_CMD)),
                                                vm_host=shm_serv)
            response_check = "Certificate not imported, alias <cascert> already exists"
            if import_cmd_response.rc != 0:
                if response_check in import_cmd_response.stdout:
                    log.logger.debug(
                        "The {0} file which we trying to import already exists, so before retrying import we "
                        "are cleaning the cert".format(PEM_FILE))
                    self.cleanup_imported_keys_on_shmserv([shm_serv])
                log.logger.debug("Sleeping for 5 seconds before retrying to import cert to shmserv")
                time.sleep(5)
                import_cmd_response = run_cmd_on_vm(Command("cd {0}; {1}".format(CERT_DIR, IMPORT_CERT_CMD)),
                                                    vm_host=shm_serv)
                if import_cmd_response.rc != 0:
                    raise EnvironError("Importing {0} file to shmserv is not successful after "
                                       "retrying. Reason {1}".format(PEM_FILE, import_cmd_response.stdout))
            log.logger.debug("Successfully imported cert to {0}".format(shm_serv))

    def copy_pem_file_to_enm(self):
        """
        Copies pem file to enm and perform commands on all instances of shmserv

        :raises EnvironError: If copying of PEM file to enm fails
        """
        child = None
        try:
            log.logger.debug("Copying {0} file to ENM".format(PEM_FILE))
            cmd = ("scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {0}@{1}:/app/{2} "
                   "{3}".format(SAS_USERNAME, self.SAS_IP, PEM_FILE, SRCDIR))
            child = GenericFlow.switch_to_ms_or_emp()
            log.logger.debug("Executing {0} command".format(cmd))
            child.sendline(cmd)
            child.expect('password:')
            log.logger.debug("Issuing password {0}".format(SAS_PASSWORD))
            child.sendline(SAS_PASSWORD)
            child.expect(PEM_FILE)
            log.logger.debug("Successfully copied the {0} file to {1} on ENM".format(PEM_FILE, SRCDIR))
        except Exception as e:
            raise EnvironError("Copying {0} file to enm is not successful. Reason {1}".format(PEM_FILE, e))
        finally:
            if child:
                child.close()

    def auth_between_enm_and_sas(self):
        """
        Generating PEM file on SAS and copy generated pem to enm to create cert on enm

        :raises EnvironError: If PEM file generation fails on SAS
        """
        log.logger.debug("Checking whether {0} file exists on SAS before generating".format(PEM_FILE))
        file_check = does_remote_file_exist("/app/{0}".format(PEM_FILE), self.SAS_IP, SAS_USERNAME, SAS_PASSWORD)
        if not file_check:
            try:
                cmd = ("ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {0}@{1} \"cd /app; {2}\""
                       .format(SAS_USERNAME, self.SAS_IP, GENERATE_PEM_FILE))
                with pexpect.spawn(cmd) as child:
                    child.expect("password:")
                    log.logger.debug("Issuing SAS password {0}".format(SAS_PASSWORD))
                    child.sendline(SAS_PASSWORD)
                    child.expect("Enter Import Password:")
                    log.logger.debug("Issuing {0} password".format(GENERATE_PEM_FILE_PWD))
                    child.sendline(GENERATE_PEM_FILE_PWD)
                    child.expect("MAC verified OK")
                    log.logger.debug("Successfully created {0} file on SAS".format(PEM_FILE))
            except Exception as e:
                raise EnvironError("{0} file generation fails on SAS. Reason: {1}".format(PEM_FILE, e))
        else:
            log.logger.debug("File {0} is already available on SAS".format(PEM_FILE))
        self.copy_pem_file_to_enm()

    def copy_sftp_keys_to_sas(self):
        """
        Copies the generated sftp key from ms to SAS

        :raises EnvironError: If copying sftp keys to SAS fails
        """
        try:
            log.logger.debug("Attempting to copy sftp keys to SAS")
            command_response = run_cmd_on_ms("cat {0}".format(KEY_FILE))
            if command_response.rc != 0:
                raise EnvironError("Invalid response code {0}".format(command_response.rc))
            log.logger.debug("Completed fetching generated sftp public key on ms")
            key = command_response.stdout.strip('\n')
            copy_key_response = run_remote_cmd(Command("echo -e {0} >>{1}/{2}".format(key, SSH_DIR, FILE_NAME)),
                                               self.SAS_IP, SAS_USERNAME, SAS_PASSWORD)
            if copy_key_response.rc != 0:
                raise EnvironError("As copying key activity failed, we cannot continue to perform the usecase. "
                                   "Reason {0}".format(copy_key_response.stdout))
            log.logger.debug("Copying sftp keys to SAS successfully completed")
        except Exception as e:
            raise EnvironError("As copying key activity failed, we cannot continue to perform the "
                               "usecase. {0}".format(str(e)))

    def set_administrator_state(self, user, nodes):
        """
        Setting the administrator state to LOCKED and UNLOCKED

        :type user: `enm_user_2.User`
        :param user: User who will execute the command on ENM
        :type nodes: list
        :param nodes: `lib.enm_node.Node` instance

        :raises EnvironError: if fdn list is empty
        :rtype: list
        :return: list of nodes
        """
        log.logger.debug("Attempting to set administrative state to LOCKED and UNLOCKED on nodes")
        fdn_cmd = "cmedit get {node_id} InstantaneousLicensing=1"
        failed_nodes = []
        fdn_list = []
        enmcli_obj = EnmCli08Flow()
        for node in nodes:
            try:
                fdn = enmcli_obj.get_mo(user=user, cmd=fdn_cmd.format(node_id=node.node_id))
                if fdn:
                    fdn_list.append(fdn)
                else:
                    failed_nodes.append(node)
            except Exception as e:
                failed_nodes.append(node)
                self.add_error_as_exception(e)
        if fdn_list:
            fdn_per_batch = arguments.split_list_into_chunks(fdn_list, self.NUM_NODES_PER_BATCH)
            for fdn_batch in fdn_per_batch:
                try:
                    fdns = ";".join(fdn_batch)
                    lock_cmd = SET_ADMIN_STATE_LOCK_CMD.format(fdns)
                    execute_command_on_enm_cli(user, lock_cmd)
                    log.logger.debug("Setting administrativeState locked command executed successfully on {0} "
                                     "nodes".format(len(fdn_batch)))
                    log.logger.debug("Sleeping for 30 sec before unlocking the administrative state")
                    time.sleep(30)
                    unlock_cmd = SET_ADMIN_STATE_UNLOCK_CMD.format(fdns)
                    execute_command_on_enm_cli(user, unlock_cmd)
                    log.logger.debug("Setting administrativeState unlocked command executed successfully on {0} "
                                     "nodes".format(len(fdn_batch)))
                except Exception as e:
                    self.add_error_as_exception(e)
        else:
            raise EnvironError("Failed to execute lock and unlock administrative state on {0} nodes".format(len(nodes)))
        nodes_list = [node for node in nodes if node not in failed_nodes]
        if nodes_list and len(nodes_list) < self.MAX_NODES:
            self.add_error_as_exception(EnvironWarning("Profile will be continuing with available {0} "
                                                       "nodes".format(len(nodes_list))))
        return nodes_list

    @staticmethod
    @retry(retry_on_exception=lambda e: isinstance(e, EnvironError), wait_fixed=10000, stop_max_attempt_number=1)
    def generate_sftp_keys():
        """
        Generate sftp keys on ms

        :raises EnvironError: If sftp key file generation fails
        """
        log.logger.debug("Generating sftp key on ms required to connect to SAS server")
        command_response = run_cmd_on_ms("cd {0}; {1}".format(KEY_PATH, KEY_GEN))
        if command_response.rc != 0:
            raise EnvironError("Invalid response code {0}".format(command_response.rc))
        key_check = does_remote_file_exist(KEY_FILE, get_ms_host(), SAS_USERNAME)
        if not key_check:
            raise EnvironError("sftp key generation failed on ms. we cannot continue to execute the usecase")
        log.logger.debug("sftp key successfully generated")

    def lkf_configuration_setup(self, shmserv_hostnames):
        """
        Performs setup activity for LKF_01 profile

        :param shmserv_hostnames: List of shm_serv hostnames (strings)
        :type shmserv_hostnames: list
        """
        self.generate_sftp_keys()
        self.copy_sftp_keys_to_sas()
        self.auth_between_enm_and_sas()
        self.import_sas_key_to_shmserv(shmserv_hostnames)

    def is_elis(self):
        """
        Checking ELIS tool configured on SAS as a prerequisite to trigger the IL usecase by checking
        PID for running process
        """
        cmd = "netstat -ltnp | grep -w ':443'"
        log.logger.debug("Checking the ELIS setup on SAS through fetching the PID")
        response = run_remote_cmd(Command(cmd), self.SAS_IP, SAS_USERNAME, SAS_PASSWORD)
        if response.rc != 0 or response.stdout == '':
            raise EnvironError("There is no running process on SAS or we could not retrieve the PID, "
                               "ELIS is not configured on SAS. Reason: {0}".format(response.stdout))
        return True

    def lkf_prerequisites(self, user, nodes):
        """
        Performs Instantaneous Licensing prerequisites such as applying nodes_per_host filter, fetching sas_ip
        and shmserv hostnames

        :type user: `enm_user_2.User`
        :param user: User who will execute the command on ENM
        :type nodes: list
        :param nodes: `lib.enm_node.Node` instance

        :raises EnvironError: Fails to retrieve sasurl from pib(cmserv) as manual set up is not completed.
        :rtype: tuple
        :return: Tuple of two lists, containing synced nodes and shmserv hostnames
        """
        log.logger.debug("Performing prerequisites required for instantaneous licensing usecase")
        synced_nodes = self.get_filtered_nodes_per_host(nodes)
        nodes_list = self.set_administrator_state(user, synced_nodes)
        sas_url = get_pib_value_on_enm('cmserv', 'sasDomainProxy_sasUrl', service_identifier='domain-proxy-service')
        if sas_url and '[]' not in sas_url:
            self.SAS_IP = re.findall(r'[0-9]+(?:\.[0-9]+){3}', sas_url)[0]
        else:
            raise EnvironError("Profile's initial setup has failed: {0}. Ensure manual set up steps have been "
                               "completed".format(SAS_MANUAL_SETUP_PAGE))
        shmserv_hostnames = get_enm_service_locations("shmserv")
        log.logger.debug("Completed all the prerequisites required for instantaneous licensing usecase")
        return nodes_list, shmserv_hostnames

    def execute_flow(self):
        """
        Executes the flow for the LKF_01 profile
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        while self.keep_running():
            self.sleep_until_day()
            nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "node_ip", "netsim", "primary_type",
                                                                      "simulation", "node_name", "poid", "mim_version"])
            shmserv_hostnames = None
            try:
                nodes_list, shmserv_hostnames = self.lkf_prerequisites(user, nodes)
                if nodes_list and self.is_elis():
                    self.lkf_configuration_setup(shmserv_hostnames)
                    self.execute_and_check_lkf_job(user, nodes_list)
                else:
                    raise EnvironError("No nodes available to execute the {0} usecase".format(JOB_NAME))
                self.exchange_nodes()
            except Exception as e:
                self.add_error_as_exception(e)
            finally:
                if shmserv_hostnames and self.CLEANUP:
                    self.cleanup_imported_keys_on_shmserv(shmserv_hostnames)
