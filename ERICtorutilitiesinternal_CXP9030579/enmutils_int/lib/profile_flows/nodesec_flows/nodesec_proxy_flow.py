import time
import os
import re
import random
from functools import partial
import lxml.etree as et
from enmutils.lib.enm_user_2 import CustomRole, RoleCapability, EnmComRole, EnmRole
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib import log, shell, filesystem
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


DEFAULT_DIR = "/home/enmutils/nodesec/"
PROXY_CLEANUP_GET_INACTIVE_FILE_PATH = os.path.join("{0}{1}".format(DEFAULT_DIR, "proxycleanup_get_inactive.xml"))


def get_user_role_capabilities(profile, role_name):
    """
    Generate required capabilities
    :type profile: `Profile`
    :param profile: Profile object
    :type role_name: str
    :param role_name: name of user role
    :return: list of capabilities required
    :rtype: list
    """
    log.logger.debug("Generating capabilities required by {0} based on resources: {1}".format(role_name,
                                                                                              profile.CAPABILITIES))
    multi_capabilities = []
    for capability, operations in profile.CAPABILITIES.iteritems():
        log.logger.debug("capability resource '{0}' with operations: {1}".format(capability, operations))
        for operation in operations:
            multi_capabilities.extend(RoleCapability.get_role_capabilities_for_resource_based_on_operation(capability,
                                                                                                           operation))
    return multi_capabilities


def create_custom_user_role(profile, name, description):
    """
    Create a custom role

    :type profile: `Profile`
    :param profile: Profile object
    :type name: str
    :param name: Name of the role
    :type description: str
    :param description: Description of the role
    :rtype: tuple
    :return: Custom role, teardown role
    """
    log.logger.debug("Attempting to create custom role: [{0}] on ENM if it does not exist".format(name))
    created_role = None
    capabilities = get_user_role_capabilities(profile, name)
    custom_role = CustomRole(name=name, roles={EnmComRole("SystemAdministrator")},
                             description=description, capabilities=capabilities, targets=None)
    teardown_role = EnmComRole(name=custom_role.name)
    roles_info = EnmRole.check_if_role_exists(custom_role.name)
    if roles_info:
        while not created_role:
            try:
                custom_role.create(role_details=roles_info)
                created_role = custom_role
                log.logger.debug("[{0}] custom role created successfully".format(name))
            except Exception as e:
                log.logger.debug("Failed to create custom role [{0}], sleeping for 120 seconds"
                                 " before retrying.".format(name))
                profile.add_error_as_exception(e)
                time.sleep(120)
    else:
        log.logger.debug("{0} custom role is already existed in ENM".format(name))

    return custom_role, teardown_role


class NodeSec17Flow(GenericFlow):
    USERS = None

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        self.state = "RUNNING"
        try:
            custom_role, teardown_role = create_custom_user_role(self, self.USER_ROLES[0],
                                                                 "Nodesec_17 profile custom user role")
            self.teardown_list.append(picklable_boundmethod(teardown_role.delete))
            log.logger.debug("Sleeping for 120 seconds to allow the UAC table update with {0} "
                             "custom role.".format(custom_role.name))
            time.sleep(120)
            self.USERS = self.create_profile_users(1, roles=[custom_role.name])
            self.teardown_list.append(picklable_boundmethod(self.USERS[0].delete))
            self.teardown_list.append(partial(filesystem.delete_file, PROXY_CLEANUP_GET_INACTIVE_FILE_PATH))

            log.logger.debug("Attempting to create directory {0}".format(DEFAULT_DIR))
            if not filesystem.does_dir_exist(DEFAULT_DIR):
                filesystem.create_dir(DEFAULT_DIR)
                log.logger.debug("Successfully created directory {0}".format(DEFAULT_DIR))
            while self.keep_running():
                self.perform_disable_delete_ldap_proxy_accounts_operations()
                self.sleep_until_time()
        except Exception as e:
            self.add_error_as_exception(e)

    def perform_disable_delete_ldap_proxy_accounts_operations(self):
        """
         Get and verify the inactive nodes proxy accounts.
         Set the administrative status of previously get proxy accounts to ENABLED/DISABLED.
         Delete the ldap proxy accounts on nodes.
        """
        try:
            inactive_proxy_accounts_status = self.get_and_verify_inactive_proxy_accounts()
            self.log_proxy_accounts_dn_from_file()
            if inactive_proxy_accounts_status:
                admin_status = self.toggle_ldap_proxy_accounts_admin_status()
                if admin_status:
                    self.delete_ldap_proxy_accounts()
        except Exception as e:
            self.add_error_as_exception(e)

    def get_and_verify_inactive_proxy_accounts(self):
        """
        Get and verify the inactive nodes proxy accounts.
        it will return the False, when 0 nodes proxy accounts found, Otherwise it will return the True
        it will return the False, when  nodes proxy accounts found.
        :rtype: bool
        :return: True or False

        :raises EnvironError: Unable to get the inactive nodes proxy accounts from ENM or
                              Unable to fetch the inactive nodes proxy accounts count from file.
        """
        inactive_proxy_accounts_status = False
        log.logger.debug("Attempting to fetch the inactive proxy accounts "
                         "for {0} Hours.".format(self.INACTIVE_HOURS))
        cmd = "secadm ldap proxy get --inactivity-hours {0}".format(self.INACTIVE_HOURS)
        response = self.USERS[0].enm_execute(cmd, outfile=PROXY_CLEANUP_GET_INACTIVE_FILE_PATH)
        enm_output = response.get_output()
        log.logger.debug("Response of inactive proxy accounts: {0}".format(enm_output))
        if "Successfully generated file" in str(enm_output):
            num_of_inactive_cmd = ('grep numOfRequestedProxyAccounts {0} | cut -d">" -f2 | '
                                   'cut -d"<" -f1').format(PROXY_CLEANUP_GET_INACTIVE_FILE_PATH)
            response = shell.run_local_cmd(shell.Command(num_of_inactive_cmd))
            if response.ok:
                log.logger.debug("Number of inactive proxy accounts: {0}".format(response.stdout.rstrip("\n")))

                if str(response.stdout).startswith("0"):
                    log.logger.debug("Inactive proxy accounts are not existed in ENM.")
                else:
                    log.logger.debug("{0} inactive proxy accounts are found in ENM.".format(
                        response.stdout.rstrip("\n")))
                    inactive_proxy_accounts_status = True
                return inactive_proxy_accounts_status
            else:
                raise EnvironError("Unable to fetch the inactive proxy accounts count "
                                   "from {0} file due to {1}.".format(PROXY_CLEANUP_GET_INACTIVE_FILE_PATH,
                                                                      response.stdout))
        else:
            raise EnvironError("Unable to get the inactive proxy accounts from ENM.")

    def toggle_ldap_proxy_accounts_admin_status(self, admin_status="DISABLED"):
        """
        Set the administrative status of previously get proxy accounts to ENABLED/DISABLED.
        :type admin_status: str
        :param admin_status: administrative status of ldap proxy account. either ENABLED or DISABLED.
        :rtype: bool
        :return: True or False

        :raises EnvironError: Unable to Enable/disable the ldap proxy admin status.
        """
        log.logger.debug("Attempting to {0} the ldap proxy admin status.".format(admin_status.lower()))
        cmd = "secadm ldap proxy set --admin-status {0} --xmlfile file:{1} --force".format(
            admin_status, PROXY_CLEANUP_GET_INACTIVE_FILE_PATH)
        response = self.USERS[0].enm_execute(cmd, file_in=PROXY_CLEANUP_GET_INACTIVE_FILE_PATH)
        enm_output = response.get_output()
        log.logger.debug("Response of {0} ldap proxy admin status : {1}".format(admin_status.lower(), enm_output))
        if "Successfully updated" in str(enm_output):
            log.logger.debug("{0} with {1} admin status for ({2})".format(enm_output[0], admin_status.lower(),
                                                                          PROXY_CLEANUP_GET_INACTIVE_FILE_PATH))
            return True
        else:
            raise EnvironError("Unable to {0} the ldap proxy admin status for ({1}) "
                               "due to {2}".format(admin_status.lower(), PROXY_CLEANUP_GET_INACTIVE_FILE_PATH,
                                                   enm_output))

    def delete_ldap_proxy_accounts(self):
        """
        delete the ldap proxy accounts.
        :rtype: bool
        :return: True or False
        :raises EnvironError: Unable to delete the ldap proxy accounts on nodes.
        """
        log.logger.debug("Attempting to delete the ldap proxy accounts.")
        cmd = "secadm ldap proxy delete --xmlfile file:{0} --force".format(PROXY_CLEANUP_GET_INACTIVE_FILE_PATH)
        response = self.USERS[0].enm_execute(cmd, file_in=PROXY_CLEANUP_GET_INACTIVE_FILE_PATH)
        enm_output = response.get_output()
        log.logger.debug("Response of delete the ldap proxy accounts : {0}".format(enm_output))
        if "Successfully deleted" in str(enm_output):
            log.logger.debug("{0} for ({1})".format(enm_output[0], PROXY_CLEANUP_GET_INACTIVE_FILE_PATH))
            return True
        else:
            raise EnvironError("Unable to delete the ldap proxy accounts for ({0}) "
                               "due to {1}".format(PROXY_CLEANUP_GET_INACTIVE_FILE_PATH, enm_output))

    def log_proxy_accounts_dn_from_file(self):
        """
        Read ldap proxy accounts dn(s) from  /home/enmutils/nodesec/proxycleanup_get_inactive.xml file
        and log each proxy account dn in profile logs
        """
        log.logger.debug("Attempting to get the ldap proxy accounts dn(s) from {0} "
                         "file.".format(PROXY_CLEANUP_GET_INACTIVE_FILE_PATH))
        try:
            tree = et.parse(PROXY_CLEANUP_GET_INACTIVE_FILE_PATH)
            proxy_accounts_data = tree.xpath('/proxyAccountsData/proxyAccounts/proxyAccount/dn/text()')
            if len(proxy_accounts_data):
                log.logger.debug("List of Inactive proxy accounts")
                for data in proxy_accounts_data:
                    log.logger.debug(data)
        except Exception as e:
            self.add_error_as_exception(EnvironError("Unable to read the proxy accounts data from {0} file "
                                                     "due to {1}".format(PROXY_CLEANUP_GET_INACTIVE_FILE_PATH, e)))


class NodeSec16Flow(GenericFlow):

    NODES_LIST_FILE = '/home/enmutils/nodesec/nodesec_16_step1_nodes_list.txt'
    NODES_LIST_FILE_TEMP = '/home/enmutils/nodesec/nodesec_16_temp_nodes_list.txt'
    NODES_STEP3_SUCCESS_LIST_FILE = '/home/enmutils/nodesec/nodesec_16_step3_success_reconfig_nodes_list.txt'
    NODES_STEP3_FAILED_LIST_FILE = '/home/enmutils/nodesec/nodesec_16_step3_failed_reconfig_nodes_list.txt'
    NODES_STEP4_SUCCESS_LIST_FILE = '/home/enmutils/nodesec/nodesec_16_step4_success_renew_nodes_list.txt'
    NODES_STEP4_FAILED_LIST_FILE = '/home/enmutils/nodesec/nodesec_16_step4_failed_renew_nodes_list.txt'
    LDAP_XML_FILE = '/home/enmutils/nodesec/nodesec_16_ldap.xml'
    MAX_POLL = 10
    GET_NODES_MASS_CMD = '/opt/ericsson/enmutils/bin/cli_app \'cmedit get * --scopefilter (CmFunction.syncStatus==' \
                         'SYNCHRONIZED AND ' \
                         'networkelement.neType==RadioNode) LdapAuthenticationMethod.administrativeState==UNLOCKED\'|' \
                         'grep FDN | awk -F \"ManagedElement=\" \'{{print $2}}\' | cut -d, -f1 | uniq > {0}'
    LDAP_RECONFIGURE_CMD = 'secadm ldap reconfigure --xmlfile file:nodesec_16_ldap.xml'
    LDAP_RENEW_CMD = 'secadm ldap renew --xmlfile file:nodesec_16_ldap.xml --force'
    USER_ROLES = None

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        self.state = "RUNNING"
        try:
            custom_role, teardown_role = create_custom_user_role(self, self.USER_ROLES[0],
                                                                 "Nodesec_16 profile custom user role")
            log.logger.debug("Sleeping for 120 seconds to allow the UAC table update with {0} "
                             "custom role.".format(custom_role.name))
            time.sleep(120)
            # Creates user with ldaprenewer custom user role.
            user = self.create_profile_users(1, roles=[custom_role.name])[0]
            self.state = "RUNNING"
            self.teardown_list.append(picklable_boundmethod(teardown_role.delete))
            self.teardown_list.append(picklable_boundmethod(user.delete))
            self.teardown_list.append(partial(filesystem.delete_file, self.NODES_LIST_FILE))
            self.teardown_list.append(partial(filesystem.delete_file, self.NODES_LIST_FILE_TEMP))
            self.teardown_list.append(partial(filesystem.delete_file, self.NODES_STEP3_SUCCESS_LIST_FILE))
            self.teardown_list.append(partial(filesystem.delete_file, self.NODES_STEP3_FAILED_LIST_FILE))
            self.teardown_list.append(partial(filesystem.delete_file, self.NODES_STEP4_SUCCESS_LIST_FILE))
            self.teardown_list.append(partial(filesystem.delete_file, self.NODES_STEP4_FAILED_LIST_FILE))
            self.teardown_list.append(partial(filesystem.delete_file, self.LDAP_XML_FILE))
            while self.keep_running():
                self.perform_ldap_proxy_renew_accounts_operations(user)
                self.sleep_until_time()
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))

    def perform_ldap_proxy_renew_accounts_operations(self, user):
        """
        Perform LDAP proxy renew accounts operation
        1 -> Get list of synced and ldap radionodes
        2 -> First LDAP reconfigure on nodes
        3 -> Second LDAP reconfigure on nodes
        4 -> Final LDAP proxy renew on nodes
        :param user: User who will query ENM and run cli commands
        :type user: `enm_user_2.User`
        """
        try:
            nodes = self.get_list_of_sync_ldap_configured_nodes(
                '1.Getting synced and ldap configured',
                self.GET_NODES_MASS_CMD.format(self.NODES_LIST_FILE_TEMP), self.NODES_LIST_FILE)
            self.create_xml_file_for_ldap(nodes)
            self.perform_ldap_commands_on_nodes(user, '2.Running first ldap reconfigure', self.LDAP_RECONFIGURE_CMD)
            self.perform_ldap_commands_on_nodes(user, '3.Running second ldap reconfigure', self.LDAP_RECONFIGURE_CMD)
            self.perform_ldap_commands_on_nodes(user, '4.Running final ldap proxy renew', self.LDAP_RENEW_CMD)
        except Exception as e:
            self.add_error_as_exception(e)

    def get_list_of_sync_ldap_configured_nodes(self, action, cmd, output_file):
        """
        This method is used to get list of synced and ldap configured nodes in workload pool
        :param action: Action to be performed
        :type action: str
        :param cmd: Command to get list of nodes
        :type cmd: str
        :param output_file: Path of a file to save list of nodes in
        :type output_file: str
        :return: Returns synced and LDAP configured nodes
        :rtype: list

        :raises EnvironError: If there are no synced and ldap configured nodes
        """
        log.logger.debug("{0} list of nodes".format(action))
        synced_ldap_nodes = []
        try:
            response = shell.run_local_cmd(shell.Command(cmd))
            log.logger.debug('Response: {0}'.format(response.stdout))
            if self.NODES_LIST_FILE_TEMP in cmd:
                log.logger.debug("Reading nodes from file {0}".format(self.NODES_LIST_FILE_TEMP))
                nodes_data = filesystem.read_lines_from_file(self.NODES_LIST_FILE_TEMP)
                random.shuffle(nodes_data)
                log.logger.debug("Total node count is {0}".format(len(nodes_data)))
                log.logger.debug("Sorting the {0} nodes randomly".format(len(nodes_data)))
                nodes = ''
                for line in nodes_data[:self.NUM_OF_NODES]:
                    nodes += line
                log.logger.debug("Writing the first {0} nodes to file {1}".format(self.NUM_OF_NODES,
                                                                                  self.NODES_LIST_FILE))
                filesystem.write_data_to_file(nodes, self.NODES_LIST_FILE)
            if 'ERROR' in cmd:
                # Log secadm job output only nodes with errors
                shell.run_local_cmd(shell.Command(cmd.split(' > ')[0].split('|cut')[0]))
            synced_ldap_nodes = filesystem.read_lines_from_file(output_file)
        except Exception as e:
            self.add_error_as_exception(e)
        if not synced_ldap_nodes and '1' in action:
            raise EnvironError('No {0} nodes available.'.format(action.split('Getting ')[1]))
        log.logger.debug("{0} nodes: {1}".format(action.split('Getting ')[1], len(synced_ldap_nodes[:1000])))
        return synced_ldap_nodes

    def create_xml_file_for_ldap(self, nodes):
        """
        This method creates a xml file of the nodes provided
        :param nodes: List of nodes
        :type nodes: list
        """
        root = et.Element('Nodes')
        for node in nodes:
            item = et.SubElement(root, 'Node')
            et.SubElement(item, 'nodeFdn').text = node.replace('\n', '')
            et.SubElement(item, 'tlsMode').text = "LDAPS"
            et.SubElement(item, 'userLabel').text = "test"
            et.SubElement(item, 'useTls').text = "true"
            et.ElementTree(root).write(self.LDAP_XML_FILE, pretty_print=True)
        log.logger.debug('Successfully created {0} file.'.format(self.LDAP_XML_FILE))
        log.logger.debug("{0} file xml input for ldap conf".format(self.LDAP_XML_FILE))

    def perform_ldap_commands_on_nodes(self, user, action, ldap_cmd):
        """
        This method performs ldap commands on nodes
        :param user: User who will query ENM and run cli commands
        :type user: `enm_user_2.User`
        :param action: Action to be performed
        :type action: str
        :param ldap_cmd: LDAP command to reconfigure/renew nodes
        :type ldap_cmd: str

        :raises EnvironError: Unable to execute command on profile allocated nodes due to some issues.
        """
        log.logger.debug('{0} command on nodes'.format(action))
        response = user.enm_execute(ldap_cmd, file_in=self.LDAP_XML_FILE)
        enm_output = response.get_output()
        log.logger.debug("{0} output: {1}".format(action.split('Running ')[1], enm_output))
        if "Internal Error" not in str(enm_output):
            job_status_cmd = str(re.split("'*'", enm_output[0])[1])
            log.logger.debug("Command to get status for certificate issue job on nodes: '{0}'".format(job_status_cmd))
            self.get_current_job_status(user, "{0} --summary".format(job_status_cmd))
            if 'second' in action:
                nodes = self.get_list_of_sync_ldap_configured_nodes(
                    'Getting Step_3 success reconfig', '/opt/ericsson/enmutils/bin/cli_app \'{0}\'|grep SUCCESS|cut -f 7 > {1}'.format(
                        job_status_cmd, self.NODES_STEP3_SUCCESS_LIST_FILE), self.NODES_STEP3_SUCCESS_LIST_FILE)
                self.create_xml_file_for_ldap(nodes)
                self.get_list_of_sync_ldap_configured_nodes(
                    'Getting Step_3 failed renew', '/opt/ericsson/enmutils/bin/cli_app \'{0}\'|grep ERROR|cut -f 7 > {1}'.format(
                        job_status_cmd, self.NODES_STEP3_FAILED_LIST_FILE), self.NODES_STEP3_FAILED_LIST_FILE)
            elif 'final' in action:
                self.get_list_of_sync_ldap_configured_nodes(
                    'Getting Step_4 success renew', '/opt/ericsson/enmutils/bin/cli_app \'{0}\'|grep SUCCESS|cut -f 7 > {1}'.format(
                        job_status_cmd, self.NODES_STEP4_SUCCESS_LIST_FILE), self.NODES_STEP4_SUCCESS_LIST_FILE)
                self.get_list_of_sync_ldap_configured_nodes(
                    'Getting Step_4 failed renew', '/opt/ericsson/enmutils/bin/cli_app \'{0}\'|grep ERROR|cut -f 7 > {1}'.format(
                        job_status_cmd, self.NODES_STEP4_FAILED_LIST_FILE), self.NODES_STEP4_FAILED_LIST_FILE)
        else:
            raise EnvironError("Unable to execute command({0}) on nodes due to {1}".format(ldap_cmd, enm_output))

    def get_current_job_status(self, user, job_status_cmd):
        """
        Function to be used to get activate/deactivate job status
        :param user: User who will query ENM and run cli commands
        :type user: `enm_user_2.User`
        :param job_status_cmd: command to execute job status
        :type job_status_cmd: str

        :raises EnvironError: If job status has not been completed within expected time/Max_poll
        """
        job_complete_status = False
        job_status_response = ''
        poll = 1
        while not job_complete_status and poll <= self.MAX_POLL:
            log.logger.debug('POLL_COUNT: {0}, MAX_POLL: {1}'.format(poll, self.MAX_POLL))
            try:
                log.logger.debug("Execute {0} command to get current job status".format(job_status_cmd))
                job_status_response = user.enm_execute(job_status_cmd)
                job_status_output = [job_status for job_status in job_status_response.get_output() if 'Status' in
                                     job_status]
                if job_status_response and job_status_output and 'COMPLETED' in job_status_output[0]:
                    log.logger.debug("Job status has been successfully completed")
                    job_complete_status = True
                log.logger.debug('Job Status Summary: {0}'.format(job_status_response))
                if not job_complete_status:
                    log.logger.debug("Sleeping for 100 seconds until job status in COMPLETED state..")
                    time.sleep(100)
                    poll += 1
            except Exception as e:
                log.logger.debug("Failed to get current job status:{0}".format(e))
                self.add_error_as_exception(EnvironError(e))
                break
        if poll > self.MAX_POLL:
            log.logger.debug('MAX_POLL limit reached - {0} retries in 1000 seconds'.format(self.MAX_POLL))
            msg = 'Job status has not completed within expected retries: {0} '.format(self.MAX_POLL)
            raise EnvironError(msg)
