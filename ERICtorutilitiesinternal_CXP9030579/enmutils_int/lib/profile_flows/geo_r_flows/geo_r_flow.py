import time
import configparser
import pexpect

from enmutils.lib import log, shell, config, filesystem, cache
from enmutils.lib.cache import is_enm_on_cloud_native, get_enm_cloud_native_namespace, is_host_physical_deployment
from enmutils.lib.exceptions import EnmApplicationError, EnvironError, ProfileWarning, ShellCommandReturnedNonZero
from enmutils.lib.shell import Command, run_local_cmd
from enmutils.lib.enm_user_2 import CustomRole, RoleCapability, EnmComRole, EnmRole
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.kubectl_commands import CHECK_SERVICES_CMD_ON_CN
from enmutils_int.lib.enm_deployment import (get_values_from_global_properties,
                                             get_list_of_db_vms_host_names,
                                             update_pib_parameter_on_enm, get_pod_hostnames_in_cloud_native)
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_list_of_scripting_service_ips

NO_HOST_CHECK = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
LOGIN_TO_POD = "kubectl exec -it {0} -n {1} -c {2} -- /bin/bash"


class GeoRFlow(GenericFlow):

    def __init__(self):
        super(GeoRFlow, self).__init__()
        self.system_user = None
        self.user_name = None
        self.setup_finished = False
        self.key_location = ""
        self.list_of_db_vms = None
        self.list_of_scripting_vms = None
        self.db_vm = None
        self.list_of_scp_vms = None
        self.scripting_vm = None
        self.is_cloud = None
        self.password = None
        self.cenm_namespace = None
        self.is_cloud_native = None
        self.is_physical = None
        self.user_password = None

    def setup(self):
        """
        Setting the environment for the geo-r profile to run the exports
        """
        self.password = cache.get_workload_vm_credentials()[1]
        self.is_cloud = config.is_a_cloud_deployment()
        self.cenm_namespace = get_enm_cloud_native_namespace()
        self.is_cloud_native = is_enm_on_cloud_native()
        self.is_physical = is_host_physical_deployment()
        self.setup_vms()
        self.setup_finished = False
        log.logger.debug("Start of setup\n"
                         "The scripting vm ip used is {0}\n"
                         "The scripting vm name is {1}\n"
                         "The db vm ip is {2}\n"
                         "The export size is {3}\n"
                         "The maxSizeForHistoryAlarmsForGeoReplication "
                         "size is {4}\n".format(self.scripting_vm, self.get_vm_name(self.scripting_vm),
                                                self.db_vm, self.EXPORT_SIZE, self.MAX_FM_HISTORY_SIZE))

        # Will retry the setup if its not completed
        max_attempts = 3
        attempt = 0
        while not self.system_user:
            try:
                log.logger.debug("Start of attempt {0} for creating GEO-R user.".format(attempt + 1))
                if attempt == max_attempts:
                    self.add_error_as_exception(
                        EnvironError("{0} attempts reached, Create user failed! Attempt to restart the profile "
                                     "later to check if the issue is resolved.".format(max_attempts)))
                    break
                # Create one geo user
                self.create_geo_user()
                log.logger.debug("Attempt {0} for creating GEO-R user finished successfully.".format(attempt + 1))
            except Exception as e:
                attempt += 1
                self.add_error_as_exception(e)
                log.logger.debug("Create user attempt {0} failed, retrying in 30 seconds".format(attempt))
                time.sleep(30)
        attempt = 0
        while not self.setup_finished and self.system_user:
            try:
                log.logger.debug("Start of attempt {0} for setup.".format(attempt + 1))
                if attempt == max_attempts:
                    self.add_error_as_exception(
                        EnvironError("{0} attempts reached, Setup failed! Attempt to restart the profile "
                                     "later to check if the issue is resolved.".format(max_attempts)))
                    break
                self.residue_cleanup()
                self.configure_geo_user()
                self.configure_certs_encryption()
                self.configure_ldap_export()
                self.create_configure_cfg_file()
                self.copy_cfg_file()
                self.geo_rep_export()
                self.nfs_and_fmx_export()
                log.logger.debug("Setup finished successfully in attempt {0}.".format(attempt + 1))
                self.setup_finished = True
            except Exception as e:
                attempt += 1
                self.add_error_as_exception(
                    EnvironError("Unexpected response from the environment or application "
                                 "during setup attempt {0}. Will sleep 30 seconds and retry "
                                 "if attempt number is less than {1}. "
                                 "Error message is - {2}".format(attempt, max_attempts, str(e))))
                time.sleep(30)

    def check_pod_is_running(self, scripting_vm):
        """
        wait and checks for pod to become 'Running'
        :return: True when pod is running.
        :rtype: bool
        :raises EnvironError: exception raised if there is a problem is with the Environment
        """
        log.logger.debug("Attempt to check the {0} service running status on Cloud native.".format(scripting_vm))
        cmd = Command(CHECK_SERVICES_CMD_ON_CN.format(self.cenm_namespace, scripting_vm))
        response = run_local_cmd(cmd)
        if not response.ok:
            raise EnvironError("Issue occurred while checking {0} on Cloud native, Please check logs.".format(scripting_vm))
        return True

    def set_scripting_vm_ip(self):
        """
        Loop through scripting vms and set to vm ip which can be connected
        """
        # Tests and logs if the scripting vm is reachable
        if self.is_cloud_native:
            self.list_of_scp_vms = get_pod_hostnames_in_cloud_native("general-scripting")
        else:
            self.list_of_scp_vms = get_list_of_scripting_service_ips()
        for ip in self.list_of_scp_vms:
            self.scripting_vm = ip
            if self.is_cloud_native:
                scripting_valid = self.check_pod_is_running(self.list_of_scp_vms[0])
            else:
                scripting_valid = self.test_scripting_vm()
            if scripting_valid:
                break
            else:
                self.add_error_as_exception(EnvironError("Cannot find a reachable scripting vm"))

    def set_db_vm_ip(self):
        """
        Loop through db vms and set to vm ip which can be connected
        """
        # Tests and logs if the db vm is reachable
        for ip in self.list_of_db_vms:
            self.db_vm = ip
            if self.is_cloud:
                db_valid = self.test_opendj_vm()
            elif self.is_cloud_native:
                log.logger.debug("On cloud native db check")
                db_valid = self.check_pod_is_running(self.list_of_db_vms[0])
            else:
                db_valid = self.test_db_vm()
            if db_valid:
                break
        else:
            self.add_error_as_exception(EnvironError("Cannot find a reachable DB node with OpenDJ running on it"))

    def setup_vms(self):
        """
        Sets and tests the scripting and db vm variable
        """
        self.set_db_vms()

        self.set_key_location()

        self.set_scripting_vm_ip()

        self.set_db_vm_ip()

        update_pib_parameter_on_enm("fmhistory", "maxSizeForHistoryAlarmsForGeoReplication", self.MAX_FM_HISTORY_SIZE)

    def set_key_location(self):
        """
        Sets the key location based on whether it is on cloud or physical
        """
        if self.is_cloud:
            self.key_location = "/var/tmp/enm_keypair.pem"
        elif self.is_physical:
            self.key_location = "/root/.ssh/vm_private_key"
        if self.is_cloud_native:
            log.logger.debug("No need to check Key file")
        else:
            if not filesystem.does_file_exist(self.key_location):
                self.add_error_as_exception(EnvironError("Cannot find pem key!!"))
                log.logger.debug("Key file not found!!!")

    def list_files_in_scripting_vm_dir(self, path):
        """
        Lists the file in remote directory given path in scripting vm.
        :param path: path of the directory.
        :type path: str
        :return: list of files in the directory.
        :rtype: list
        :raises EnvironError: If scripting pod is not available.
        """
        if self.is_cloud_native:
            file_path = "ls {0}".format(path)
            response = shell.run_cmd_on_cloud_native_pod("general-scripting", self.list_of_scp_vms[0], file_path)
            if response.rc != 0:
                raise EnvironError("Could not get list of files in directory {0}".format(file_path))
            current_list = response.stdout
        else:
            current_list = filesystem.get_files_in_remote_directory(path, self.scripting_vm,
                                                                    user=self.user_name,
                                                                    password=self.system_user.password)
        return current_list

    def residue_cleanup(self):
        """
        Cleans up the files and directories that were created by previous runs
        :raises EnvironError: when residue files detected
        """
        try:
            log.logger.debug("Cleaning up residue")
            if self.is_cloud_native:
                child = pexpect.spawn(
                    LOGIN_TO_POD.format(self.list_of_scp_vms[0], self.cenm_namespace, "general-scripting"))
                child.expect(["{0}".format(self.list_of_scp_vms[0]), pexpect.EOF, pexpect.TIMEOUT])
                time.sleep(1)
                log.logger.debug("Successfully logged in to scripting pod ")
            else:
                child = pexpect.spawn("ssh {0} -i {1} cloud-user@{2}".format(NO_HOST_CHECK, self.key_location, self.scripting_vm))
                child.sendline("sudo su")
                time.sleep(1)

            update_pib_parameter_on_enm("fmserv", "exportHistoryAlarmsForGeoReplication", "false")

            self.command_handler("rm -rf /ericsson/georeplication/alarm_levels.json "
                                 "/ericsson/georeplication/nfs.lck /ericsson/georeplication/georep.lck "
                                 "/ericsson/georeplication/fmx.lck /ericsson/georeplication/geoReplication.cfg"
                                 " /ericsson/georeplication/.crypt /ericsson/georeplication/.workingDir "
                                 "/ericsson/georeplication/dataSets /ericsson/georeplication/.ldap/;"
                                 "crontab -u {0} -l | grep -v 'geo'  | crontab -u {0} -;"
                                 "crontab -u {1} -l | grep -v 'geo'  | crontab -u {1} -;"
                                 .format(self.user_name, "root"), child)

            current_list = self.list_files_in_scripting_vm_dir("/ericsson/georeplication/")

            new_residue = ["nfs.lck", "fmx.lck", "georep.lck", "dataSets", "geoReplication.cfg"]

            if any(residue in current_list for residue in new_residue):
                raise EnvironError("Residue cleanup failed since files are not cleaned up properly.")
            else:
                log.logger.debug("Finished cleaning up residue")
            child.terminate()
        except Exception:
            raise EnvironError("Residue cleanup failed due to environment or application issue.")

    def create_geo_user(self):
        """
        Create a geo user with the necessary user roles
        """
        user_roles = self.USER_ROLES
        if self.is_cloud_native:
            user_roles.append("Elect_Administrator")

        capabilities = self.geo_r_role_capabilities()
        self.create_geo_r_role_on_enm(capabilities)
        self.system_user = self.create_profile_users(1, roles=user_roles)[0]
        self.user_name = self.system_user.username
        self.user_password = self.system_user.password
        log.logger.debug("Username = {0}".format(self.user_name))

    @staticmethod
    def geo_r_role_capabilities():
        """
        Generate required capabilities for geo_r_role
        :return: list of capabilites required by geo_r_role
        :rtype: list
        """
        log.logger.debug("Generating capabilities required by geo_r_role")
        capabilities = ["credentials_plain_text", "snmpv3_plain_text"]
        multi_capabilities = []
        # Gets a set of role capabilities
        for capability in capabilities:
            multi_capabilities.extend(RoleCapability.get_role_capabilities_for_resource(capability))
        return multi_capabilities

    @staticmethod
    def create_geo_r_role_on_enm(capabilities):
        """
        Create geo_r_role on ENM
        :param capabilities: list of capabilities required for geo_r_role
        :type capabilities: list
        """
        log.logger.debug("Attempting to create geo_r_role on ENM if it does not exist")
        create_geo_r_role = EnmRole.check_if_role_exists("geo_r_role")
        if not create_geo_r_role:
            log.logger.debug("Geo role found")
        else:
            log.logger.debug("Geo role not found, creating new geo role")
            custom_role = CustomRole(name="geo_r_role", roles={EnmComRole("SystemAdministrator")},
                                     description="geo_user custom role", capabilities=capabilities, targets=None)
            custom_role.create(role_details=create_geo_r_role)

    def configure_geo_user(self):
        """
        Configure the geo user on the scripting server
        """
        log.logger.debug("Starting to configure the geo-user")
        if self.is_cloud_native:
            self.configure_geo_user_cloud_native()
        else:
            child = pexpect.spawn("ssh {0} -i {1} cloud-user@{2}".format(NO_HOST_CHECK,
                                                                         self.key_location,
                                                                         self.scripting_vm), timeout=120)
            child.sendline("sudo su")
            child.expect(["root", pexpect.EOF, pexpect.TIMEOUT])

            host_name = cache.get_haproxy_host()

            self.command_handler('yes | cp -rf /opt/ericsson/georeplication/config/alarm_levels.json '
                                 '/ericsson/georeplication/', child)
            self.command_handler('curl -k -c cookie_GeoOperator.txt -X POST "https://{0}/login" '
                                 '-d "IDToken1=Administrator&IDToken2=TestPassw0rd"'.format(host_name), child)
            self.command_handler('curl -s -k -b cookie_GeoOperator.txt '
                                 '-H "Accept:application/json" '
                                 '-H "Content-Type:application/json" '
                                 '-X PUT "https://{0}/oss/idm/usermanagement/users/{1}" '
                                 '-d \'{{"username":"{1}","maxSessionTime":"1051200",'
                                 '"maxIdleTime":"1051200"}}\''.format(host_name, self.user_name), child)

            self.command_handler("usermod -a -G wheel,jboss,fmhistoryusers,geor {0}".format(self.user_name), child)
            self.command_handler("chmod g+rwXs /ericsson/georeplication/;sleep 2;"
                                 "chown -R :geor /ericsson/georeplication/", child)
            log.logger.debug("checking if geor role is reflected through stat /ericsson/georeplication/")
            child.sendline("stat /ericsson/georeplication/")
            child.expect("geor")
            log.logger.debug("Before command: {0}".format(child.before))
            log.logger.debug("After command: {0}".format(child.after))
            child.terminate()
        log.logger.debug("Finished configuring the geo-user")

    def configure_geo_user_cloud_native(self):
        """
        Configure the geo user on the scripting server
        """
        child = pexpect.spawn(LOGIN_TO_POD.format(self.list_of_scp_vms[0], self.cenm_namespace, "general-scripting"))
        child.expect(["{0}".format(self.list_of_scp_vms[0]), pexpect.EOF, pexpect.TIMEOUT])
        child.sendline("sudo su")
        child.expect(["root", pexpect.EOF, pexpect.TIMEOUT])

        host_name = cache.get_haproxy_host()

        self.command_handler('yes | cp -rf /opt/ericsson/georeplication/config/alarm_levels.json '
                             '/ericsson/georeplication/', child)
        self.command_handler('curl -k -c cookie_GeoOperator.txt -X POST "https://{0}/login" '
                             '-d "IDToken1=Administrator&IDToken2=TestPassw0rd"'.format(host_name), child)
        self.command_handler('curl -s -k -b cookie_GeoOperator.txt '
                             '-H "Accept:application/json" '
                             '-H "Content-Type:application/json" '
                             '-X PUT "https://{0}/oss/idm/usermanagement/users/{1}" '
                             '-d \'{{"username":"{1}","maxSessionTime":"1051200",'
                             '"maxIdleTime":"1051200"}}\''.format(host_name, self.user_name), child)

        child.terminate()
        child = pexpect.spawn(LOGIN_TO_POD.format(self.list_of_scp_vms[0], self.cenm_namespace, "general-scripting"))
        child.expect(["{0}".format(self.list_of_scp_vms[0]), pexpect.EOF, pexpect.TIMEOUT])
        child.sendline("sudo su")
        time.sleep(1)
        self.command_handler("usermod -a -G wheel,jboss,fmhistoryusers,geor {0}".format(self.user_name), child)
        self.command_handler("chmod g+rwXs /ericsson/georeplication/", child)
        time.sleep(2)
        self.command_handler("chown -R :geor /ericsson/georeplication/", child)
        log.logger.debug("checking if geor role is reflected through stat /ericsson/georeplication/")
        child.sendline("stat /ericsson/georeplication/")
        child.expect("geor")
        log.logger.debug("Before command: {0}".format(child.before))
        log.logger.debug("After command: {0}".format(child.after))
        child.terminate()

    def configure_certs_encryption(self):
        """
        Runs a set of commands to copy and configure the encryption files
        :raises EnvironError: when the dirs/files are not found in the expected place
        """
        # Logs on to scripting vm and creates .crypt dir as geo_user
        log.logger.debug("Starting configuring encryptions")
        if self.is_cloud_native:
            self.configure_certs_encryption_cloud_native()
        else:
            child = pexpect.spawn("ssh {0} -i {1} cloud-user@{2}".format(NO_HOST_CHECK, self.key_location,
                                                                         self.scripting_vm))
            child.sendline("sudo su {0}".format(self.user_name))
            self.command_handler("mkdir -p /ericsson/georeplication/.crypt/;", child)
            child.sendline("exit")

            if filesystem.does_remote_dir_exist("/ericsson/georeplication/.crypt/", self.scripting_vm,
                                                user=self.user_name, password=self.system_user.password):
                log.logger.debug("Created the .crypt dir")
            else:
                raise EnvironError("Failed to create .crypt dir")

            # Finds and copies the p.12 file from database to the scripting vm
            p_12_file_location = get_internal_file_path_for_import("etc", "data", "ENM_GRS.p12")
            shell.run_local_cmd("scp {0} -i {1} {2} cloud-user@{3}:".format(NO_HOST_CHECK, self.key_location,
                                                                            p_12_file_location, self.scripting_vm))
            self.command_handler("sudo cp ~/ENM_GRS.p12 /ericsson/georeplication/.crypt/; "
                                 "sudo chown {0} /ericsson/georeplication/.crypt/ENM_GRS.p12; "
                                 "sudo rm -f ~/ENM_GRS.p12".format(self.user_name), child)

            # Finds and copies the pem file from database to the scripting vm
            pem_file_location = get_internal_file_path_for_import("etc", "data", "geo_rep_sec_cert.pem")
            shell.run_local_cmd("scp {0} -i {1} {2} cloud-user@{3}:".format(NO_HOST_CHECK, self.key_location,
                                                                            pem_file_location, self.scripting_vm))
            self.command_handler("sudo cp ~/geo_rep_sec_cert.pem /ericsson/georeplication/.crypt/; "
                                 "sudo chown {0} /ericsson/georeplication/.crypt/geo_rep_sec_cert.pem; "
                                 "sudo rm -f ~/geo_rep_sec_cert.pem".format(self.user_name), child)

            # Checking if the 2 files in the right place
            files = self.list_files_in_scripting_vm_dir("/ericsson/georeplication/.crypt/")

            if ("ENM_GRS.p12" not in files) or ("geo_rep_sec_cert.pem" not in files):
                raise EnvironError("Failed to copy encryption files")

            self.command_handler("sudo chmod 666 /ericsson/georeplication/.crypt/geo_rep_sec_cert.pem", child)
            log.logger.debug("Changed the permission of the pem file")

            if self.is_cloud:
                # Changing the file permission

                log.logger.debug("Creating the private key and giving it accesses")
                self.command_handler("sudo cp /ericsson/enm/dumps/.cloud_user_keypair.pem "
                                     "/ericsson/georeplication/.crypt/private_key.pem;"
                                     "sudo chown {0} /ericsson/georeplication/.crypt/private_key.pem;"
                                     "sudo chmod 600 /ericsson/georeplication/.crypt/private_key.pem".format(self.user_name),
                                     child)

            child.terminate()
        log.logger.debug("Finished configuring encryptions")

    def configure_certs_encryption_cloud_native(self):
        """
        Runs a set of commands to copy and configure the encryption files
        :raises EnvironError: when the dirs/files are not found in the expected place
        """
        child = pexpect.spawn(LOGIN_TO_POD.format(self.list_of_scp_vms[0], self.cenm_namespace, "general-scripting"))
        child.expect(["{0}".format(self.list_of_scp_vms[0]), pexpect.EOF, pexpect.TIMEOUT])
        child.sendline("sudo su {0}".format(self.user_name))
        self.command_handler("mkdir -p /ericsson/georeplication/.crypt/;", child)
        child.sendline("exit")

        file_path = "/ericsson/georeplication/.crypt/"
        if filesystem.does_file_exists_on_cloud_native_pod("general-scripting", self.list_of_scp_vms[0], file_path):
            log.logger.debug("Created the .crypt dir")
        else:
            raise EnvironError("Failed to create .crypt dir")

        # Finds and copies the p.12 file from database to the scripting vm
        p_12_file_location = get_internal_file_path_for_import("etc", "data", "ENM_GRS.p12")
        shell.copy_file_between_wlvm_and_cloud_native_pod(self.list_of_scp_vms[0], p_12_file_location,
                                                          "/ericsson/georeplication/.crypt/", 'to')
        self.command_handler("sudo cp ~/ENM_GRS.p12 /ericsson/georeplication/.crypt/; "
                             "sudo chown {0} /ericsson/georeplication/.crypt/ENM_GRS.p12; "
                             "sudo rm -f ~/ENM_GRS.p12".format(self.user_name), child)

        # Finds and copies the pem file from database to the scripting vm
        pem_file_location = get_internal_file_path_for_import("etc", "data", "geo_rep_sec_cert.pem")
        shell.copy_file_between_wlvm_and_cloud_native_pod(self.list_of_scp_vms[0], pem_file_location,
                                                          "/ericsson/georeplication/.crypt/", 'to')
        self.command_handler("sudo cp ~/geo_rep_sec_cert.pem /ericsson/georeplication/.crypt/; "
                             "sudo chown {0} /ericsson/georeplication/.crypt/geo_rep_sec_cert.pem; "
                             "sudo rm -f ~/geo_rep_sec_cert.pem".format(self.user_name), child)

        # Checking if the 2 files in the right place
        files = self.list_files_in_scripting_vm_dir("/ericsson/georeplication/.crypt/")

        if ("ENM_GRS.p12" not in files) or ("geo_rep_sec_cert.pem" not in files):
            raise EnvironError("Failed to copy encryption files")

        self.command_handler("sudo chmod 666 /ericsson/georeplication/.crypt/geo_rep_sec_cert.pem", child)
        log.logger.debug("Changed the permission of the pem file")
        child.terminate()

    def copy_cfg_file(self):
        """"
        Copy the cfg file to the cloud, rm the old copy, move the copied file to the correct location
        :raises EnvironError: when cfg file is not coped
        """
        log.logger.debug("Copying cfg file")
        if self.is_cloud_native:
            self.copy_cfg_file_cloud_native()
        else:
            scp_child = pexpect.spawn("scp {0} /home/enmutils/dynamic_content/geoReplication.cfg "
                                      "{1}@{2}:/home/shared/{1}".format(NO_HOST_CHECK, self.user_name, self.scripting_vm))
            time.sleep(1)
            response = scp_child.expect(["password", pexpect.EOF, pexpect.TIMEOUT])
            time.sleep(1)
            if response == 0:
                scp_child.sendline(self.system_user.password)
                time.sleep(1)
                log.logger.debug("Copying cfg file to {0} vm: rc={1}".format(self.scripting_vm, response))
                ssh_child = pexpect.spawn(
                    "ssh {0} {1}@{2}".format(NO_HOST_CHECK, self.user_name, self.scripting_vm))
                ssh_child.expect(["password", pexpect.EOF, pexpect.TIMEOUT])
                ssh_child.sendline(self.system_user.password)
                time.sleep(1)
                log.logger.debug("Copy geoReplication.cfg file from /home/shared/{0} to "
                                 "/ericsson/georeplication/".format(self.user_name))
                ssh_child.sendline("cp /home/shared/{0}/geoReplication.cfg "
                                   "/ericsson/georeplication/".format(self.user_name))
                ssh_child.sendline("ls /ericsson/georeplication/geoReplication.cfg")
                ssh_child.expect(["geoReplication.cfg", pexpect.EOF, pexpect.TIMEOUT])
                time.sleep(2)
                current_list = self.list_files_in_scripting_vm_dir("/ericsson/georeplication/")

                if "geoReplication.cfg" not in current_list:
                    raise EnvironError("Failed to copy cfg file")
            else:
                raise EnvironError("Cannot connect to scripting vm")
            time.sleep(5)
            response = shell.run_local_cmd("sudo rm /home/enmutils/dynamic_content/geoReplication.cfg")
            if response.rc != 0:
                raise EnvironError("Failed to delete geoReplication.cfg")
            log.logger.debug("Removed local geoReplication.cfg")

            ssh_child.terminate()
            scp_child.terminate()
        log.logger.debug("Finished copying cfg file")

    def copy_cfg_file_cloud_native(self):
        """
        Copy the cfg file to the cloud, rm the old copy, move the copied file to the correct location
        :raises EnvironError: when cfg file is not coped
        """
        file_location = "/home/enmutils/dynamic_content/geoReplication.cfg"
        response = shell.copy_file_between_wlvm_and_cloud_native_pod(self.list_of_scp_vms[0], file_location,
                                                                     "/home/shared/{0}".format(self.user_name), 'to')
        time.sleep(1)
        child = pexpect.spawn(LOGIN_TO_POD.format(self.list_of_scp_vms[0], self.cenm_namespace, "general-scripting"))
        rc = child.expect(["{0}".format(self.list_of_scp_vms[0]), pexpect.EOF, pexpect.TIMEOUT])
        if rc == 0:
            log.logger.debug("Copying cfg file to {0} vm: rc={1}".format(self.list_of_scp_vms[0], response.rc))
            child.sendline("sudo su {0}".format(self.user_name))
            child.sendline(self.system_user.password)
            time.sleep(1)
            log.logger.debug("Copy geoReplication.cfg file from /home/shared/{0} to "
                             "/ericsson/georeplication/".format(self.user_name))
            child.sendline("cp /home/shared/{0}/geoReplication.cfg "
                           "/ericsson/georeplication/".format(self.user_name))
            child.sendline("ls /ericsson/georeplication/geoReplication.cfg")
            child.expect(["geoReplication.cfg", pexpect.EOF, pexpect.TIMEOUT])
            time.sleep(2)
            current_list = self.list_files_in_scripting_vm_dir("/ericsson/georeplication/")

            if "geoReplication.cfg" not in current_list:
                raise EnvironError("Failed to copy cfg file")
        else:
            raise EnvironError("Cannot connect to scripting vm")
        time.sleep(5)
        command = "sudo rm -rf /home/enmutils/dynamic_content/geoReplication.cfg"
        response = shell.run_cmd_on_cloud_native_pod("general-scripting", self.list_of_scp_vms[0], command)
        if response.rc != 0:
            raise EnvironError("Failed to delete geoReplication.cfg")
        log.logger.debug("Removed local geoReplication.cfg")
        child.terminate()

    def create_configure_cfg_file(self):
        """
        Creates a cfg file with the required configurations
        """
        log.logger.debug("Creating cfg file")
        parser = configparser.ConfigParser()
        parser.add_section("GeoRep")
        parser.set("GeoRep", "mode", "export")
        parser.set("GeoRep", "encryption", "Yes")
        parser.set("GeoRep", "dailyCronExecutionTimes", "04:00,10:00,16:00,22:00")
        parser.set("GeoRep", "cronJobHost", "{}".format(self.get_vm_name(self.scripting_vm)))
        parser.set("GeoRep", "enable_non_critical_data", "true")
        if self.is_cloud:
            parser.set("GeoRep", "non_critical_data_list", '"idam, fm_alarm_history, fcmgt, '
                                                           'enm_logs, service_config_params, vnflcm, pm, '
                                                           'collections_and_savedsearches, shm"')
        else:
            parser.set("GeoRep", "non_critical_data_list", '"idam, fm_alarm_history, enm_logs, '
                                                           'service_config_params, fcmgt, '
                                                           'pm, collections_and_savedsearches, shm"')
        parser.set("GeoRep", "enm_logs_export_path", "/ericsson/georeplication")
        parser.set("GeoRep", "enm_logs_max_size", "{}".format(self.EXPORT_SIZE))
        parser.set("GeoRep", "enm_logs_cron_exec_time", "01:00,07:00,13:00,19:00")
        parser.set("GeoRep", "nfs_max_size", "{}".format(self.EXPORT_SIZE))
        parser.set("GeoRep", "geo_system_user", "{}".format(self.user_name))

        with open("/home/enmutils/dynamic_content/geoReplication.cfg", "w") as f:
            parser.write(f)
        log.logger.debug("Local cfg file created")

    def configure_ldap_export(self):
        """
        Runs the ldap_configure.sh
        :raises EnvironError: Cannot reach the desired vm
        :raises EnmApplicationError: when ldap_configure.sh fails
        """
        # Logs on to the scripting vm and creates the .ldap dir
        log.logger.debug("Starting ldap configuration")
        if self.is_cloud_native:
            self.configure_ldap_export_cloud_native()
        else:
            child = pexpect.spawn("ssh {0} {1}@{2}".format(NO_HOST_CHECK, self.user_name, self.scripting_vm))
            time.sleep(1)
            child.sendline(self.system_user.password)
            time.sleep(1)
            self.command_handler("mkdir -p /ericsson/georeplication/.ldap/", child)
            child.terminate()

            if self.is_cloud:
                self.login_to_cloud_db()
            else:
                # Logs on to the db vm as litp-admin then switch to root user, cannot login as root directly
                child = pexpect.spawn("ssh {0} root@{1}".format(NO_HOST_CHECK, cache.get_ms_host()))
                time.sleep(1)
                child.sendline("ssh {0} litp-admin@{1}".format(NO_HOST_CHECK, self.db_vm))
                time.sleep(1)
                rc = child.expect(["password:", pexpect.EOF, pexpect.TIMEOUT], timeout=30)
                if rc == 0:
                    child.sendline(self.password)
                    child.sendline("su root")
                    child.expect("Password:", timeout=30)
                    child.sendline(self.password)
                    self.command_handler("setfacl -R -m u:opendj:rwx /ericsson/georeplication/.ldap/", child)
                else:
                    log.logger.debug("Before:{0} \n\n After:{1}".format(child.before, child.after))
                    raise EnvironError("Connection attempt failed")

                self.command_handler("rm -f /root/.georep_ldap_pass;"
                                     "echo 'ldapadmin' >> /root/.georep_ldap_pass;"
                                     "chmod 400 /root/.georep_ldap_pass", child)

                # Run the ldap_configure.sh, which will create crons for ldap
                child.sendline("/ericsson/georeplication/ldap/ldap_configure.sh")
                rc = child.expect(["successfully", pexpect.EOF, pexpect.TIMEOUT])
                if rc != 0:
                    raise EnmApplicationError("Problem running ldap_configure.sh, \nBefore:{0} "
                                              "\nAfter:{1}".format(child.before, child.after))

                self.command_handler("rm -f /etc/cron.d/geo_r_ldap;"
                                     "echo '5 * * * * root /ericsson/georeplication/ldap/ldap_configure.sh' "
                                     ">> /etc/cron.d/geo_r_ldap;"
                                     "chmod 644 /etc/cron.d/geo_r_ldap", child)

                child.terminate()
        log.logger.debug("Finished configuring ldap export")

    def login_to_cloud_db(self):
        """
        login to cloud_db for ldap_configure.sh
        :raises EnvironError: Cannot reach the desired vm
        :raises EnmApplicationError: when ldap_configure.sh fails
        """
        log.logger.debug("Connecting to opendj")
        child = pexpect.spawn("ssh {0} -i {1} cloud-user@{2}".format(NO_HOST_CHECK, self.key_location, cache.get_emp()))
        rc = child.expect(["emp", pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnvironError("Cannot connect to emp because {0} \n Before:{1} \n After:{2}"
                               .format(rc, child.before, child.after))
        time.sleep(1)

        child.sendline("ssh {0} -i /ericsson/enm/dumps/.cloud_user_keypair.pem cloud-user@{1}"
                       .format(NO_HOST_CHECK, self.db_vm))
        time.sleep(3)
        rc = child.expect(["opendj", pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnvironError("Cannot connect to opendj because {0} \n Before:{1} \n After:{2}"
                               .format(rc, child.before, child.after))

        child.sendline("sudo su")
        time.sleep(2)
        rc = child.expect(["root", pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnvironError("Cannot switch to root because {0} \n Before:{1} \n After:{2}"
                               .format(rc, child.before, child.after))
        self.command_handler("chmod 757 /ericsson/georeplication/.ldap/", child)
        time.sleep(1)
        self.command_handler("rm -f /root/.georep_ldap_pass;"
                             "echo 'ldapadmin' >> /root/.georep_ldap_pass;"
                             "chmod 400 /root/.georep_ldap_pass", child)

        # Run the ldap_configure.sh, which will create crons for ldap
        child.sendline("/ericsson/georeplication/ldap/ldap_configure.sh")
        rc = child.expect(["successfully", pexpect.EOF, pexpect.TIMEOUT])
        if rc != 0:
            raise EnmApplicationError("Problem running ldap_configure.sh, \nBefore:{0} "
                                      "\nAfter:{1}".format(child.before, child.after))

        self.command_handler("rm -f /etc/cron.d/geo_r_ldap;"
                             "echo '5 * * * * root /ericsson/georeplication/ldap/ldap_configure.sh' "
                             ">> /etc/cron.d/geo_r_ldap;"
                             "chmod 644 /etc/cron.d/geo_r_ldap", child)

        child.terminate()

    def configure_ldap_export_cloud_native(self):
        """
        Runs the ldap_configure.sh
        :raises EnvironError: Cannot reach the desired vm
        :raises EnmApplicationError: when ldap_configure.sh fails
        """
        child = pexpect.spawn(LOGIN_TO_POD.format(self.list_of_scp_vms[0], self.cenm_namespace, "general-scripting"))
        child.expect(["{0}".format(self.list_of_scp_vms[0]), pexpect.EOF, pexpect.TIMEOUT])
        child.sendline("sudo su {0}".format(self.user_name))
        time.sleep(1)
        self.command_handler("mkdir -p /ericsson/georeplication/.ldap/", child)
        child.terminate()

        log.logger.debug("Connecting to opendj")
        child = pexpect.spawn(LOGIN_TO_POD.format(self.list_of_db_vms[0], self.cenm_namespace, "opendj"))
        rc = child.expect(["opendj", pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnvironError("Cannot connect to opendj because {0} \n Before:{1} \n After:{2}"
                               .format(rc, child.before, child.after))
        nfs_cmd = "nfs4_setfacl -R -a A::502:rwaDxtcy /ericsson/georeplication/.ldap"
        log.logger.debug("Attempting to execute the command: {0}".format(nfs_cmd))
        child.sendline(nfs_cmd)
        output = child.expect(["(?i)error", pexpect.EOF, pexpect.TIMEOUT, "root"])
        log.logger.debug("Before command: {0}".format(child.before))
        log.logger.debug("After command: {0}".format(child.after))
        if output == 0:
            setfacl_cmd = "setfacl -R -m u:opendj:rwx /ericsson/georeplication/.ldap/"
            log.logger.debug("Attempting to execute the command: {0}".format(setfacl_cmd))
            child.sendline(setfacl_cmd)
            response = child.expect(["Operation not supported", "command not found", pexpect.EOF, pexpect.TIMEOUT, "root"])
            log.logger.debug("Before command: {0}".format(child.before))
            log.logger.debug("After command: {0}".format(child.after))
            if response < 2:
                raise EnmApplicationError("The command not executed correctly because {0} \n Before:{1} \n After:{2}"
                                          .format(response, child.before, child.after))
        self.command_handler("rm -f /root/.georep_ldap_pass;"
                             "echo 'ldapadmin' >> /root/.georep_ldap_pass;"
                             "chmod 400 /root/.georep_ldap_pass", child)

        # Run the ldap_configure.sh, which will create crons for ldap
        child.sendline("/ericsson/georeplication/ldap/ldap_configure.sh")
        rc = child.expect(["successfully", pexpect.EOF, pexpect.TIMEOUT])
        if rc != 0:
            raise EnmApplicationError("Problem running ldap_configure.sh, \nBefore:{0} "
                                      "\nAfter:{1}".format(child.before, child.after))

        self.command_handler("rm -f /etc/cron.d/geo_r_ldap;"
                             "echo '5 * * * * root /ericsson/georeplication/ldap/ldap_configure.sh' "
                             ">> /etc/cron.d/geo_r_ldap;"
                             "chmod 644 /etc/cron.d/geo_r_ldap", child)
        child.terminate()

    def geo_rep_export(self):
        """
        Runs the georep.py script
        :raises EnvironError: when cannot log in as geo-user
        :raises EnmApplicationError: when geo_rep.py fails
        """
        if self.is_cloud_native:
            self.geo_rep_export_cloud_native()
        else:
            child = pexpect.spawn("ssh {0}@{1}".format(self.user_name, self.scripting_vm))
            time.sleep(1)
            rc = child.expect(["password", pexpect.EOF, pexpect.TIMEOUT])
            time.sleep(1)
            if rc == 0:
                child.sendline(self.system_user.password)
            else:
                raise EnvironError("Cannot log in as Geo_user")
            log.logger.debug("Running georep.py")
            child.sendline("/opt/ericsson/georeplication/georep.py -v --setup")
            rc = child.expect(["Setup crontab job has finished!", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError("Failed running georep.py -v --setup \nRc:{rc}, \nBefore:{0} "
                                          "\nAfter:{1}".format(child.before, child.after, rc=rc))
            child.terminate()

    def geo_rep_export_cloud_native(self):
        """
        Runs the georep.py script
        :raises EnvironError: when cannot log in as geo-user
        :raises EnmApplicationError: when geo_rep.py fails
        """
        child = pexpect.spawn(LOGIN_TO_POD.format(self.list_of_scp_vms[0], self.cenm_namespace, "general-scripting"))
        child.expect(["{0}".format(self.list_of_scp_vms[0]), pexpect.EOF, pexpect.TIMEOUT])

        log.logger.debug("logging as {0}".format(self.user_name))
        child.sendline("ssh {0}@{1}".format(self.user_name, self.list_of_scp_vms[0]))
        result = child.expect(["Password:", pexpect.EOF, pexpect.TIMEOUT])
        if result == 0:
            child.sendline(self.user_password)
            rc = child.expect(["{0}".format(self.user_name), pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                log.logger.debug("Before:{0} \n After:{1}".format(child.before, child.after))
                raise EnvironError("Cannot log in as {0}".format(self.user_name))
        else:
            child.sendline("yes")
            child.expect(["Password:", pexpect.EOF, pexpect.TIMEOUT])
            child.sendline(self.user_password)
            rc = child.expect(["{0}".format(self.user_name), pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                log.logger.debug("Before:{0} \n After:{1}".format(child.before, child.after))
                raise EnvironError("Cannot log in as {0}".format(self.user_name))

        log.logger.debug("Running georep.py")
        child.sendline("/opt/ericsson/georeplication/georep.py -v --setup")
        rc = child.expect(["Setup crontab job has finished!", pexpect.EOF, pexpect.TIMEOUT])
        if rc != 0:
            raise EnmApplicationError("Failed running georep.py -v --setup \nRc:{rc}, \nBefore:{0} "
                                      "\nAfter:{1}".format(child.before, child.after, rc=rc))
        child.terminate()

    def nfs_and_fmx_export(self):
        """
        Runs the terminal command to do the nfs and fmx exports
        :raises EnmApplicationError: when nfsshare_export.py or  fmx_rules_export.py fails
        """
        # Logs on to scripting vm and configures the nfsshare.cfg file
        if self.is_cloud_native:
            self.nfs_export_cloud_native()
        else:
            child = pexpect.spawn("ssh {0} -i {1} cloud-user@{2}".format(NO_HOST_CHECK, self.key_location, self.scripting_vm))
            child.sendline("sudo su")
            log.logger.debug("Writing content to nfsshare.cfg")
            self.command_handler("sudo rm -f /ericsson/georeplication/nfsshare.cfg;"
                                 "echo '/home/shared/administrator' >> /ericsson/georeplication/nfsshare.cfg;"
                                 "echo '/home/shared/{username}' >> "
                                 "/ericsson/georeplication/nfsshare.cfg".format(username=self.user_name), child)

            # Runs the nfsshare_export.py
            log.logger.debug("Running nfsshare_export.py")
            child.sendline("/opt/ericsson/georeplication/nfs_share/nfsshare_export.py -s")
            rc = child.expect(["(?i)Sucessfully", pexpect.TIMEOUT, pexpect.EOF])
            if rc != 0:
                raise EnmApplicationError("Failed running nfsshare_export.py, \nBefore:{0} "
                                          "\nAfter:{1}".format(child.before, child.after))

            # Runs the fmx_rules_export.py
            log.logger.debug("Running fmx_rules_export.py")
            child.sendline("/opt/ericsson/georeplication/fm/fmx_rules_export.py  -s")
            rc = child.expect(["(?i)Sucessfully", pexpect.TIMEOUT, pexpect.EOF])
            if rc != 0:
                raise EnmApplicationError("Failed running fmx_rules_export.py, \nBefore:{0} "
                                          "\nAfter:{1}".format(child.before, child.after))
            child.terminate()

    def nfs_export_cloud_native(self):
        """
        Runs the terminal command to do the nfs and fmx exports
        :raises EnmApplicationError: when nfsshare_export.py or  fmx_rules_export.py fails
        """
        child = pexpect.spawn(LOGIN_TO_POD.format(self.list_of_scp_vms[0], self.cenm_namespace, "general-scripting"))
        child.expect(["{0}".format(self.list_of_scp_vms[0]), pexpect.EOF, pexpect.TIMEOUT])
        child.sendline("sudo su")
        log.logger.debug("Writing content to nfsshare.cfg")
        self.command_handler("sudo rm -f /ericsson/georeplication/nfsshare.cfg;"
                             "echo '/home/shared/administrator' >> /ericsson/georeplication/nfsshare.cfg;"
                             "echo '/home/shared/{username}' >> "
                             "/ericsson/georeplication/nfsshare.cfg".format(username=self.user_name), child)

        # Runs the nfsshare_export.py
        log.logger.debug("Running nfsshare_export.py")
        child.sendline("/opt/ericsson/georeplication/nfs_share/nfsshare_export.py -s")
        rc = child.expect(["(?i)Sucessfully", pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnmApplicationError("Failed running nfsshare_export.py, \nBefore:{0} "
                                      "\nAfter:{1}".format(child.before, child.after))

        # Runs the fmx_rules_export.py
        log.logger.debug("Running fmx_rules_export.py")
        child.sendline("/opt/ericsson/georeplication/fm/fmx_rules_export.py  -s")
        rc = child.expect(["(?i)Sucessfully", pexpect.TIMEOUT, pexpect.EOF])
        if rc != 0:
            raise EnmApplicationError("Failed running fmx_rules_export.py, \nBefore:{0} "
                                      "\nAfter:{1}".format(child.before, child.after))
        child.terminate()

    def command_handler(self, cmd, child):
        """
        Handles pexpect commands and logs error accordingly

        :param cmd: The command that is to be ran through the pexpect child
        :type cmd: str
        :param child: pexpect.spawn
        :type child: pexpect.spawn

        :raises EnmApplicationError: When the command send to the child has failed
        """
        log.logger.debug("Attempting to execute the command: {0}".format(cmd))
        time.sleep(1)
        child.sendline(cmd)
        response = child.expect(["(?i)error", "(?i)fail", pexpect.EOF, pexpect.TIMEOUT,
                                 "root", "cloud-user@", "{}@".format(self.user_name)])
        log.logger.debug("Before command: {0}".format(child.before))
        log.logger.debug("After command: {0}".format(child.after))
        if response < 4:
            raise EnmApplicationError(
                "The command {0} has failed with status code {1}. \nBefore: {2} \nAfter: {3}".format(
                    cmd, response, child.before, child.after))
        else:
            log.logger.debug("Successful executing command: {0}, \nRc: {1}".format(cmd, response))
        time.sleep(1)

    def set_db_vms(self):
        """
        Set the db vm based on cloud or physical
        """
        if self.is_cloud:
            log.logger.debug("On cloud")
            self.list_of_db_vms = get_values_from_global_properties("opendj")
        elif self.is_cloud_native:
            log.logger.debug("On cloud native")
            self.list_of_db_vms = get_pod_hostnames_in_cloud_native("opendj")
            log.logger.debug("db vm on cloud native is {0}".format(self.list_of_db_vms))
        else:
            log.logger.debug("On physical")
            self.list_of_db_vms = get_list_of_db_vms_host_names()
        self.db_vm = self.list_of_db_vms[0]

    @staticmethod
    def get_vm_name(ip):
        """
        Gets the hostname of the vm

        :param ip: The ip address of the vm
        :type ip: str
        :returns: The vm's hostname
        :rtype: str
        :raises ShellCommandReturnedNonZero: if execution of run_cmd_on_vm failed
        """

        if is_enm_on_cloud_native():
            response = get_pod_hostnames_in_cloud_native(ip)
            log.logger.debug("The scripting vm name {0}".format(response))
            return response[0]
        else:
            cmd = shell.Command("hostname", timeout=10)
            response = shell.run_cmd_on_vm(cmd, ip)
            if response.rc != 0:
                raise ShellCommandReturnedNonZero("Execution of run command failed while fetching VM name", response)
            return response.stdout

    def test_scripting_vm(self):
        """
        Tests if the scripting vm is reachable

        :returns: Boolean to indicate whether it has connected to the vm
        :rtype: bool
        """
        log.logger.debug("Trying to connect to the scripting vm")
        child = pexpect.spawn("ssh {0} -i {1} cloud-user@{2}".format(NO_HOST_CHECK, self.key_location, self.scripting_vm))
        rc = child.expect(["fingerprint", "cloud-user", pexpect.EOF, pexpect.TIMEOUT])
        if rc == 2 or rc == 3:
            log.logger.debug("Cannot connect to scripting vm")
            self.add_error_as_exception(EnvironError("Cannot reach scripting vm "))
            child.terminate()
            return False
        elif rc == 0:
            child.sendline("yes")
            time.sleep(1)
        child.terminate()
        return True

    def test_db_vm(self):
        """
        Tests if the db vm is reachable and opendj is running on it

        :returns: Boolean to indicate whether it has connected to the vm and opendj is running
        :rtype: bool
        """
        log.logger.debug("Trying to connect to the DB vm")

        child = pexpect.spawn("ssh {0} root@{1}".format(NO_HOST_CHECK, cache.get_ms_host()))
        time.sleep(1)
        child.sendline("ssh {0} litp-admin@{1}".format(NO_HOST_CHECK, self.db_vm))
        rc = child.expect(["password:", pexpect.EOF, pexpect.TIMEOUT])

        if rc == 0:
            log.logger.debug("Issuing password")
            child.sendline(self.password)
        else:
            log.logger.debug("Cannot connect to DB vm {}".format(self.db_vm))
            log.logger.warn("Check if DB node {} is online".format(self.db_vm))
            child.terminate()
            return False

        rc = child.expect(["litp-admin", pexpect.EOF, pexpect.TIMEOUT])

        if rc == 0:
            log.logger.debug("Successfully logged into DB Node: {}".format(self.db_vm))
        else:
            log.logger.debug("Cannot login to DB node : {}".format(self.db_vm))
            child.terminate()
            return False

        log.logger.debug("Checking if OpenDJ is running on DB node: {}".format(self.db_vm))
        child.sendline("/etc/init.d/opendj status")
        rc = child.expect(["is running", pexpect.EOF, pexpect.TIMEOUT])

        if rc == 0:
            log.logger.debug("OpenDJ is running on DB node: {} ".format(self.db_vm))
            log.logger.debug("Continuing with DB node: {}".format(self.db_vm))
        else:
            log.logger.debug("OpenDJ is not running on DB node:{} ".format(self.db_vm))
            child.terminate()
            return False

        child.terminate()
        return True

    def test_opendj_vm(self):
        """
        Tests if the opendj vm is reachable
        :returns: Boolean to indicate whether it has connected to the vm
        :rtype: bool
        """
        log.logger.debug("Trying to connect to the opendj")
        child = pexpect.spawn("ssh {0} -i {1} cloud-user@{2}".format(NO_HOST_CHECK, self.key_location, cache.get_emp()))
        time.sleep(1)
        # Connecting to EMP
        rc = child.expect(["fingerprint", "emp", pexpect.EOF, pexpect.TIMEOUT])
        if rc == 0:
            child.sendline("yes")
        elif rc != 1:
            self.add_error_as_exception(EnvironError(
                "Cannot connect to emp because {0} \n Before:{1} \n After:{2}".format(rc, child.before, child.after)))
            child.terminate()
            return False
        # Connecting to opendj
        child.sendline("ssh {0} -i /ericsson/enm/dumps/.cloud_user_keypair.pem cloud-user@{1}".format(NO_HOST_CHECK, self.db_vm))
        time.sleep(1)
        rc = child.expect(["fingerprint", "opendj", pexpect.EOF, pexpect.TIMEOUT])
        if rc == 0:
            child.sendline("yes")
            time.sleep(1)
        elif rc != 1:
            self.add_error_as_exception(EnvironError("Cannot connect to opendj because {0} \n Before:{1} \n After:{2}"
                                                     .format(rc, child.before, child.after)))
            child.terminate()
            return False
        time.sleep(1)
        child.terminate()
        return True

    def set_teardown_objects(self):
        """
        Adds teardown objects to the teardown list
        """
        self.teardown_list.append(picklable_boundmethod(self.teardown_role_and_user))
        self.teardown_list.append(picklable_boundmethod(self.residue_cleanup))

    def teardown_role_and_user(self):
        """
        Deletes GEO user and role on ENM when the profile is stopped
        """
        log.logger.debug("Cleaning up GEO user and role")
        self.user_cleanup()
        geo_r_role = CustomRole('geo_r_role')
        geo_r_role.delete()

    def login_to_scripting_vm_as_geo_user(self):
        """
        Login to scripting vm as geo user to refresh the session.
        """
        common_message = "into scripting vm : {0} as user : {1} to refresh the session.".format(self.scripting_vm,
                                                                                                self.user_name)
        error_message = "Issue faced in logging {0}".format(common_message)
        log.logger.debug("Attempting to login {0}".format(common_message))
        if self.is_cloud_native:
            child = pexpect.spawn(
                LOGIN_TO_POD.format(self.list_of_scp_vms[0], self.cenm_namespace, "general-scripting"))
            child.expect(["{0}".format(self.list_of_scp_vms[0]), pexpect.EOF, pexpect.TIMEOUT])
            child.sendline("sudo su {0}".format(self.user_name))
            rc = child.expect(["{0}@".format(self.user_name), pexpect.EOF, pexpect.TIMEOUT])
            if rc == 0:
                log.logger.debug("Successfully logged in {0}".format(common_message))
            else:
                log.logger.debug(error_message)
            child.terminate()
        else:
            child = pexpect.spawn("ssh {0}@{1}".format(self.user_name, self.scripting_vm))
            rc = child.expect(["password", pexpect.EOF, pexpect.TIMEOUT])
            if rc == 0:
                child.sendline(self.system_user.password)
                rc = child.expect([self.user_name, pexpect.EOF, pexpect.TIMEOUT])
                if rc == 0:
                    log.logger.debug("Successfully logged in {0}".format(common_message))
                else:
                    log.logger.debug(error_message)
            else:
                log.logger.debug(error_message)
            child.terminate()

    def verify_tarball_creation(self, old_list):
        """
        Verifies if new tarball has been added

        :param old_list: List of old tarballs in the dataset dir
        :type old_list: list

        :return: A list of files in the dataSets dir
        :rtype: list
        """
        current_list = []
        try:
            self.set_scripting_vm_ip()
            current_list = self.list_files_in_scripting_vm_dir("/ericsson/georeplication/dataSets/")
        except Exception as e:
            self.add_error_as_exception(EnvironError("Unable to connect to scripting vm {0} and "
                                                     "verify if new tarball is created. "
                                                     "Tarball still could have been created. "
                                                     "Please manually check dataSets directory and "
                                                     "georep logs on scripting vm. "
                                                     "Error message is - {1}".format(self.scripting_vm, str(e))))
        log.logger.debug("Current files in dataSet dir: {}".format(current_list))

        if old_list == current_list:
            log.logger.debug("No new tarball found")
            self.add_error_as_exception(ProfileWarning(
                "Tarball creation failure, check georep logs on scripting vm."
                "Please ignore if this message is shown during or just after ENM upgrade."
                "Ensure cron is not commented for user : {0} in scripting vm : {1} "
                "after the upgrade.".format(self.user_name, self.scripting_vm)))
        return current_list

    def execute_flow(self):
        """
        The flow for geo_r
        """
        # Setup runs once
        self.set_teardown_objects()
        self.setup()
        current_tarball_list = ["EMPTY"]
        self.state = "RUNNING"

        while self.keep_running() and self.setup_finished:
            self.sleep_until_time()
            current_tarball_list = self.verify_tarball_creation(current_tarball_list)
            self.login_to_scripting_vm_as_geo_user()
