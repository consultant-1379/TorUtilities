import pkgutil
import json
from urlparse import urljoin
from functools import partial
from time import sleep
from requests import HTTPError
import pexpect
from enmutils.lib import log
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils.lib.cache import (get_emp, is_host_physical_deployment, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP,
                                CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, is_enm_on_cloud_native)
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.dit import get_sed_id, get_parameter_value_from_sed_document
from enmutils_int.lib.enm_deployment import get_list_of_db_vms_host_names, get_cloud_members_ip_address
from enmutils_int.lib.esm import random_get_request_cn
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services.deployment_info_helper_methods import get_hostname_cloud_deployment

CREATE_USER_FILE = "createuser.js"
DELETE_USER_FILE = "deleteuser.js"
USER = 'cloud-user'
PASSWORD = 'passw0rd'
CMD = "sudo -- sh -c 'export RHQ_CLI_JAVA_EXE_FILE_PATH=`which java`;/opt/ericsson/rhq-cli/bin/rhq-cli.sh -u rhqadmin -p ericssonadmin -f /tmp/{}'"
ESM_FOLDER = "/home/enmutils/esm/"
INTERNAL_PACKAGE_PATH = pkgutil.get_loader("enmutils_int").filename
ESM_PASSWORD = "ericssonadmin"
USER_PASSWORD = "Test@Passw0rd"


class ESM01Flow(GenericFlow):

    PHYSICAL_DEPLOYMENT = is_host_physical_deployment()
    USERNAME = "sec_admin"
    DEFAULT_PASSWORD = "sec_admin"
    NEW_PASSWORD2 = "Test@Passw0rd2"
    ESM_VM_IP = None
    LOGIN_URL = None
    CREATE_USER_URL = None
    LOGOUT_URL = None
    NEW_PASSWORD = None

    @staticmethod
    def perform_esm_tasks(worker, profile, user, esmon_vm_ip):
        """
        UI flow to perform ESM tasks on cENM
        :param worker: list of users
        :type worker:  list
        :param profile: profile name
        :type profile: profile object
        :param user: user cretaed on ESM
        :type user: user object
        :param esmon_vm_ip: will get esmon_vm_ip
        :type esmon_vm_ip: str
        """
        log.logger.info("Sleeping for 10 seconds before login in with user:{0}".format(worker))
        sleep(10)
        profile.esm_login(user, worker, USER_PASSWORD)
        log.logger.info(
            "Sleeping for 10 seconds before performing random get request in ESM with user:{0}".format(worker))
        sleep(10)
        random_get_request_cn(worker, user, esmon_vm_ip)  # random GET to keep the session
        log.logger.info("Sleeping for 10 seconds before logging out the user:{0}".format(worker))
        sleep(10)
        profile.esm_logout(user, worker)

    def execute_flow(self):
        """
        execute flow for ESM_01
        """
        self.state = "RUNNING"
        self.set_esm_urls()
        user = get_workload_admin_user()
        users_list, user_credentials_list, user_dict = [], [], []
        self.esm_login(user, self.USERNAME, password=self.DEFAULT_PASSWORD)
        try:
            response = user.get(self.CREATE_USER_URL, headers=JSON_SECURITY_REQUEST)
            existing_users = [user_dict["username"] for user_dict in response.json()]
            users_info = [existing_users.remove(i) for i in existing_users if i == 'sec_admin']
            log.logger.debug("Users information : {0}".format(users_info))
            if existing_users:
                log.logger.debug("Deleting these existing esm_users: {0} from ESM UI".format("existing_users"))
                self.delete_esm_users_cn(existing_users, user)
            for i in range(self.NUM_USERS):
                username = "{0}_user{1}".format(self.NAME, i)
                user_credentials = {"role": "OPERATOR",
                                    "targetGroups": "All",
                                    "authMode": "local",
                                    "username": username,
                                    "name": "Profile user",
                                    "surname": "test",
                                    "email": "test@email.com",
                                    "password": "Test@Passw0rd"}
                user_credentials_list.append(user_credentials)
                users_list.append(username)
            self.create_esm_users(user, user_credentials_list, users_list)
            log.logger.debug("users list : {0}".format(users_list))
            for i in list(users_list):
                self.esm_login(user, i)
                self.esm_logout(user, i)
            while self.keep_running():
                self.sleep_until_time()
                user = get_workload_admin_user()
                self.create_and_execute_threads(workers=users_list, thread_count=len(users_list),
                                                func_ref=self.perform_esm_tasks, args=[self, user, self.ESM_VM_IP],
                                                wait=self.THREAD_QUEUE_TIMEOUT, join=self.THREAD_QUEUE_TIMEOUT)
        except Exception as e:
            self.add_error_as_exception(e)

    def esm_login(self, user, username, password="Test@Passw0rd"):
        """
        LOgging into ESM and changing default password if not changed already
        :param user: user
        :type user: user object
        :param username: username of an ESM user
        :type username: str
        :param password: password for a user to login
        :type password: str
        """
        try:
            log.logger.debug("Logging into ESM using {0}".format(username))
            payload = {"username": username, "password": password}
            response = user.post(self.LOGIN_URL, data=json.dumps(payload), headers=JSON_SECURITY_REQUEST)
            output = response.json()
            if not response.ok and output and output["changePassword"]:
                if username == "sec_admin":
                    log.logger.debug("Changing password for user: {0}".format(username))
                    self.change_esm_login_password(user, username, password, self.NEW_PASSWORD)
                else:
                    self.esm_login(user, self.USERNAME, password=self.NEW_PASSWORD)
                    log.logger.debug("Changing password for ESM user: {0}".format(username))
                    self.change_esm_login_password(user, username, password, self.NEW_PASSWORD2)
            elif not (response.ok and output):
                if username == "sec_admin":
                    self.esm_login(user, username, password=self.NEW_PASSWORD)
                else:
                    self.esm_login(user, username, password=self.NEW_PASSWORD2)
            else:
                log.logger.debug("Successfully logged into ESM using user: {0}".format(username))
        except Exception as e:
            self.add_error_as_exception(e)

    def change_esm_login_password(self, user, username, password, newpassword):
        """
        Change password of an esm user
        :param user: user
        :type user: user object
        :param username: username of an ESM user
        :type username: str
        :param password: password for a user to login
        :type password: str
        :param newpassword: New password for ESM user
        :type newpassword: str

        :raises EnmApplicationError: if password change fails
        """
        payload = {"username": username, "password": password, "newPassword": newpassword}
        log.logger.debug("old password : {0}".format(password))
        log.logger.debug("latest password : {0}".format(newpassword))
        response = user.post(self.LOGIN_URL, data=json.dumps(payload), headers=JSON_SECURITY_REQUEST)
        output = response.json()
        if response.ok and output["brand2"]:
            log.logger.debug("Password changed successfully for the user {0}".format(username))
        else:
            raise EnmApplicationError("Password change failed for user {1}. Response: {0}".format(response, username))

    def esm_logout(self, user, username):
        """
        Logout from ESM
        :param user: user
        :type user: user object
        :param username: Name of the user to logout
        :type username: str
        """
        log.logger.debug("Logout the user:{0}".format(username))
        esm_logout_response = user.post(self.LOGOUT_URL)
        if not esm_logout_response.ok:
            raise_for_status(esm_logout_response)
        else:
            log.logger.debug("Logged out the user:{0}".format(username))

    def create_esm_users(self, user, user_cred_list, users_list):
        """
        Creates esm users
        :param user: user
        :type user: user object
        :param user_cred_list: list of user data to be sent to create users
        :type user_cred_list: list
        :param users_list: list of user names
        :type users_list: list

        :raises EnvironError: when post request fails
        """
        log.logger.debug("Creating {0} ESM users".format(len(users_list)))
        user_payload = {"users": user_cred_list}
        response = user.post(self.CREATE_USER_URL, data=json.dumps(user_payload), headers=JSON_SECURITY_REQUEST)
        if response.ok:
            log.logger.debug("Successfully created {0} users on ESM".format(len(users_list)))
        else:
            raise EnvironError("Failed to create user on ESM :{0}".format(response))
        self.teardown_list.append(partial(picklable_boundmethod(self.delete_esm_users_cn), users_list, user))

    def delete_esm_users_cn(self, users_list, delete_as=None):
        """
        Deletes esm users from ESM
        :param users_list: list of usernames
        :type users_list: list
        :param delete_as: user name
        :type delete_as: user object
        """
        delete_as = delete_as or get_workload_admin_user()
        self.esm_login(delete_as, self.USERNAME, password=self.NEW_PASSWORD)
        log.logger.debug("Deleting users")
        for _ in users_list:
            response = delete_as.delete_request(urljoin(self.CREATE_USER_URL, _), headers=JSON_SECURITY_REQUEST)
            if response.ok:
                log.logger.debug("{0} user deleted successfully".format(_))
            else:
                self.add_error_as_exception(HTTPError("Failed to delete user {0}".format(_)))
        self.esm_logout(delete_as, self.USERNAME)

    def set_esm_urls(self):
        """
        Formats the Rest end points for login,logout and creation of users based on the deployment type.
        """
        try:
            if is_enm_on_cloud_native():
                base_url = '/esm-server/'
                self.LOGIN_URL = urljoin(base_url, 'login/')
                self.LOGOUT_URL = urljoin(base_url, 'logout/')
                self.CREATE_USER_URL = urljoin(base_url, "api/users/")
                self.NEW_PASSWORD = "Test@Passw0rd"
            else:
                self.ESM_VM_IP = self.get_esmon_vm_ip()
                base_url = ('https://' + str(self.ESM_VM_IP))
                self.LOGIN_URL = urljoin(base_url, '/login/')
                self.LOGOUT_URL = urljoin(base_url, '/logout/')
                self.CREATE_USER_URL = urljoin(base_url, "/api/users/")
                self.NEW_PASSWORD = "Sec_Admin12345"
        except Exception as e:
            self.add_error_as_exception(e)

    def get_esmon_vm_ip(self):
        """
        Returns the IP address of ESMON VM
        """
        log.logger.debug("Fetching the ESMON VM IP")
        if self.PHYSICAL_DEPLOYMENT:
            esmon_vm_ip = get_list_of_db_vms_host_names('esmon')
            if esmon_vm_ip:
                esmon_vm_ip = esmon_vm_ip[0]
        else:
            esmon_vm_ip = self.get_esmon_ip_of_cloud()
        if not esmon_vm_ip:
            raise EnvironError("ESMON VMs are not available in ENM {0}".format(esmon_vm_ip))
        log.logger.debug("ESMON VM IP has been retrieved:{}".format(esmon_vm_ip))
        return esmon_vm_ip

    def get_esmon_ip_of_cloud(self):
        """
        Check in cloud environment and fetch esmon_vm_ip_cloud.

        :rtype: string
        :return: esmon_vm_ip_cloud
        :raises EnvironError: if the output is not ok
        """
        try:
            _, deployment_hostname = get_hostname_cloud_deployment()
            sed_id = get_sed_id(deployment_hostname)
            if sed_id:
                sed_parameter = 'esmon_external_ip_list'
                esmon_vm_ip_cloud = get_parameter_value_from_sed_document(sed_id, sed_parameter)
            else:
                esmon_vm_ip_cloud = self.get_esmon_vm_ip_cloud()
            log.logger.debug("Esmon vm ip in cloud server {0}".format(esmon_vm_ip_cloud))
            return esmon_vm_ip_cloud
        except Exception as e:
            self.add_error_as_exception(e)

    def get_esmon_vm_ip_cloud(self):
        """
        Returns the IP address of ESMON VM of cloud
        """
        esmon_vm_ip_cloud = None
        retry = 1
        max_retries = 3
        while retry <= max_retries:
            log.logger.debug("Startring fetching of ip in Cloud")
            vnflaf = get_cloud_members_ip_address('vnflaf')
            cmd = 'ssh -o StrictHostKeyChecking=no -i {2} {0}@{1}'.format('cloud-user', get_emp(),
                                                                          CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM,
                                                                          timeout=30)
            log.logger.debug("command : {0}".format(cmd))
            child = pexpect.spawn(cmd)
            vnf_cmd = 'ssh -i {2} -o stricthostkeychecking=no {0}@{1}'.format('cloud-user', vnflaf[0],
                                                                              CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP,
                                                                              timeout=30)
            log.logger.debug("command : {0}".format(vnf_cmd))
            child.expect('cloud-user@')
            child.sendline(vnf_cmd)
            child.expect('cloud-user@')
            child.sendline('sudo su')
            child.expect('root@')
            deployment_name = child.before
            log.logger.debug("value  before {0}".format(str(deployment_name)))
            log.logger.debug("Deployment name:{}".format(deployment_name.split('-')[0]))
            sed_id = get_sed_id(deployment_name.split('-')[0])
            if not sed_id:
                log.logger.debug("Deployment name of vio:{}".format(deployment_name[:8]))
                deployment_name_vio = deployment_name[:8]
                sed_id = get_sed_id(deployment_name_vio)
                if not sed_id:
                    deployment_name_vio = str('vio_') + str(deployment_name_vio.split('-')[-1])
                    log.logger.debug("Deployment name of vio for wrong dit name format:{}".format(deployment_name_vio))
                    sed_id = get_sed_id(deployment_name_vio)
            log.logger.debug("sed id :{}".format(sed_id))
            sed_parameter = 'esmon_external_ip_list'
            esmon_vm_ip_cloud = get_parameter_value_from_sed_document(sed_id, sed_parameter)
            if not esmon_vm_ip_cloud:
                retry += 1
                log.logger.info("Sleeping for 300 secs before retrying to connect the VNF")
                sleep(300)
            else:
                break
        return esmon_vm_ip_cloud
