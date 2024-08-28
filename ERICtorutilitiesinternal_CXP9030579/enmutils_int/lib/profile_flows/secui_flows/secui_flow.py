import json
import random
import re
import string
import time
from functools import partial

from requests.exceptions import HTTPError
from retrying import retry

from enmutils.lib import log, config
from enmutils.lib.arguments import get_random_string
from enmutils.lib.enm_user_2 import (CustomRole, EnmComRole, RoleCapability, Target, User, raise_for_status, EnmRole)
from enmutils.lib.exceptions import (EnmApplicationError, EnvironError, ValidationError)
from enmutils.lib.headers import JSON_SECURITY_REQUEST, SECURITY_REQUEST_HEADERS
from enmutils.lib.persistence import get, picklable_boundmethod
from enmutils_int.lib.enm_user import CustomUser
from enmutils_int.lib.enm_user import get_workload_admin_user, recreate_deleted_user, user_exists
from enmutils_int.lib.ldap import LDAP
from enmutils_int.lib.load_mgr import get_active_profile_names
from enmutils_int.lib.pkiadm import CertificateProfile, Entity, EntityProfile, get_all_entity_profiles
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.shm_utilities import SHMUtils
from enmutils_int.lib.federated_identity_management import FIDM_interface


class SecuiFlow(GenericFlow):
    CAPABILITIES = []
    COMROLE = "SystemAdministrator"

    @property
    def capabilities(self):
        multi_capabilities = []
        for capability in self.CAPABILITIES:
            multi_capabilities.extend(RoleCapability.get_role_capabilities_for_resource(capability))
        return multi_capabilities

    def _set_teardown_objects(self, method):
        """
        Add method to the teardown list

        :type method: method
        :param method: Bound method which we want to call at teardown
        """
        self.teardown_list.append(picklable_boundmethod(method))

    def create_custom_role(self, name, description, user):
        """
        Create a custom role, which will have access to our custom target groups by default

        :type name: str
        :param name: Name of the target group
        :type description: str
        :param description: Description of the target group
        :type user: `enm_user_2.User`
        :param user: User who will created the custom user

        :rtype: tuple
        :return: Custom role, teardown role
        """
        log.logger.debug("Attempting to create custom role: [{}]".format(name))
        created_role = None
        custom_role = CustomRole(user=user, name=name, description=description, roles={EnmComRole(self.COMROLE)},
                                 capabilities=set(self.capabilities))
        teardown_role = EnmComRole(name=custom_role.name)
        roles_info = EnmRole.check_if_role_exists(custom_role.name)
        if roles_info:
            while not created_role:
                try:
                    custom_role.create(role_details=roles_info)
                    created_role = custom_role
                    log.logger.debug("[{}] custom role created successfully".format(name))
                except Exception as e:
                    log.logger.debug("Failed to create custom role [{}], sleeping for 120 seconds"
                                     " before retrying.".format(name))
                    self.add_error_as_exception(e)
                    time.sleep(120)

        return custom_role, teardown_role

    def create_custom_target_groups(self, target_groups, user=None):
        """
        Create the custom target groups

        :type user: `enm_user_2.User`
        :param user: User who create the groups
        :type target_groups: list
        :param target_groups: List of target groups

        :rtype: list
        :return: List of `enm_user_2.TargetGroup` instances
        """
        target_groups_list = []
        log.logger.debug("Attempting to create the {0} custom target groups".format(
            ','.join(str(group) for group in target_groups)))
        for target_group in target_groups:
            target = Target(name=target_group, description="{0} Target Group".format(target_group))
            if target.exists:
                target.delete(user=user)
            target.create(create_as=user)
            self.teardown_list.append(target)
            target_groups_list.append(target)
        log.logger.debug("Successfully created {0} custom target groups".format(
            ','.join(str(group) for group in target_groups_list)))
        return target_groups_list

    def create_custom_user(self, i, roles, targets):
        """
        Create a custom user, using with a CustomRole and Custom Targets

        :type i: int
        :param i: Iterator to handle multiple user creations
        :type roles: list
        :param roles: The `enm_user_2.CustomRole` that will be assigned to the user
        :type targets: list
        :param targets: The `enm_user_2.Target` that will be assigned to the user
        :raises: EnmApplicationError
        :rtype: list[`enm_user.User`]
        :return: List of newly created custom user
        """
        users = []
        while len(users) <= i:
            user = CustomUser("{0}_u{1}".format(self.identifier, i), "TestPassw0rd", roles=roles, targets=targets,
                              safe_request=True, persist=False, keep_password=True)
            try:
                user.create()
                self.teardown_list.append(user)
                users.append(user)
            except Exception as e:
                log.logger.debug("Failed to create custom user, sleeping for 120 seconds before retrying.")
                self.add_error_as_exception(e)
                time.sleep(120)
        return users

    def check_ldap_is_configured_on_nodes(self, user, synced_nodes):
        """
        This method is used for check if nodes are configured with ldap or not ,which are assigned to workload profiles
        :param user: User object to be used to make requests
        :type user: enm_user_2.User object
        :param synced_nodes: List of allocated synced nodes to profile
        :type synced_nodes: list
        :return: Returns LDAP configured nodes
        :rtype: list
        """
        log.logger.debug("Checking the ldap configured status on {0} nodes ".format(len(synced_nodes)))
        nodes_without_ldap_configured = []
        nodes_ldap_configured = []
        try:
            all_ldap_configured_nodes_response = user.enm_execute(LDAP.LDAP_STATUS_CMD_ON_ALL_NODES)
            enm_output = all_ldap_configured_nodes_response.get_output()
            if enm_output:
                for node in synced_nodes:
                    if any(node.node_id in fdn for fdn in enm_output):
                        nodes_ldap_configured.append(node)
                    else:
                        nodes_without_ldap_configured.append(node)
        except Exception as e:
            self.add_error_as_exception(e)
        if nodes_without_ldap_configured:
            self.add_error_as_exception(EnvironError("LDAP is not configured on {0} nodes"
                                                     .format(len(nodes_without_ldap_configured))))
            log.logger.debug(
                "Nodes not having LDAP configured : {0}".format([node.node_id for node in nodes_without_ldap_configured]))

        log.logger.debug("{0} nodes have LDAP configured, {1} nodes don't have LDAP configured".format(
            len(nodes_ldap_configured), len(nodes_without_ldap_configured)))
        return nodes_ldap_configured

    def create_custom_roles_and_target_groups(self, custom_user_roles, target_groups):
        """
        Create the custom user roles and custom target groups

        :type custom_user_roles: list
        :param custom_user_roles: List of `enm_user_2.EnmRole` instances to be apply
        :type target_groups: list
        :param target_groups: List of custom target groups
        :raises EnmApplicationError: if custome user roles creation failed.
        """
        custom_roles = []
        self.create_custom_target_groups(target_groups)
        log.logger.debug("Attempting to create the {0} custom user roles".format(
            ','.join(str(role) for role in custom_user_roles)))
        user = None
        for role in custom_user_roles:
            try:
                user = user or get_workload_admin_user()
                custom_role, teardown_role = self.create_custom_role(role, role, user=user)
                custom_roles.append(custom_role.name)
                self.teardown_list.append(picklable_boundmethod(teardown_role.delete))
            except Exception as e:
                raise EnmApplicationError("Failed to create custom role: {0} due to {1}".format(role, e))

        log.logger.debug("Successfully created {0} custom user roles".format(
            ','.join(str(role) for role in custom_roles)))


class Secui01Flow(SecuiFlow):

    SECURITY_ADMIN_USERS = []

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        self.SECURITY_ADMIN_USERS = self.create_profile_users(self.NUMBER_OF_SECURITY_ADMINS, roles=["SECURITY_ADMIN"])
        try:
            number_of_users = self.get_number_of_users_count_based_admin_users()

            if number_of_users:
                self.create_and_execute_threads(self.SECURITY_ADMIN_USERS, thread_count=len(self.SECURITY_ADMIN_USERS),
                                                args=[self, number_of_users], join=self.THREAD_QUEUE_TIMEOUT,
                                                wait=self.THREAD_QUEUE_TIMEOUT)
            else:
                self.add_error_as_exception(EnvironError("Unable to divide the number of users to create "
                                                         "for each admin user"))
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))

    @staticmethod
    def task_set(security_admin_user, profile, number_of_users):  # pylint: disable=arguments-differ
        """
        Method to split up number of users each admin should create

        :param security_admin_user: User with which to perform the creations
        :type security_admin_user: EnmUser
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        :type number_of_users: list
        :param number_of_users: list of number of users to create
        """
        if len(number_of_users) > 1:
            users_per_admin = number_of_users[profile.SECURITY_ADMIN_USERS.index(security_admin_user)]
        else:
            users_per_admin = number_of_users[0]

        for i in xrange(users_per_admin):
            user = User("{0}_USER_{1}_{2}".format(profile.identifier, get_random_string(size=8), i), "TestPassw0rd",
                        roles=random.sample(profile.USER_ROLES, profile.NUMBER_OF_ROLES_TO_ASSIGN), persist=False)
            try:
                user.create(create_as=security_admin_user)
                user.remove_session()
            except Exception as e:
                profile.add_error_as_exception(EnmApplicationError(e.message))

    def get_number_of_users_count_based_admin_users(self):
        """
        This method used for split the number of user to create per each admin user.

        :rtype: list
        :return: List of number of users to create per each admin user.
        """
        number_of_users = []
        try:
            remaining_users = self.NUMBER_OF_USERS_TO_CREATE % self.NUMBER_OF_SECURITY_ADMINS
            if remaining_users != 0:
                users = range(self.NUMBER_OF_USERS_TO_CREATE)
                number_of_users = [len(users[_::self.NUMBER_OF_SECURITY_ADMINS])
                                   for _ in range(self.NUMBER_OF_SECURITY_ADMINS)]
            else:
                number_of_users = [self.NUMBER_OF_USERS_TO_CREATE / self.NUMBER_OF_SECURITY_ADMINS]
            log.logger.debug("Successfully generated user counts for each admin user: {0}".format(number_of_users))
        except Exception as e:
            self.add_error_as_exception(e)
        return number_of_users


class Secui02Flow(SecuiFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        security_admin_user = self.create_profile_users(1, roles=["SECURITY_ADMIN"])[0]
        while self.keep_running():
            roles_created = self.create_roles_as(security_admin_user, self.NUMBER_OF_ROLES)
            users_created = self.create_users_as(roles_created, security_admin_user, self.NUMBER_OF_USERS)
            log.logger.debug("Completed create with {0} user roles and {1} users.".format(len(roles_created),
                                                                                          len(users_created)))
            self.delete_users(users_created, security_admin_user)
            self.delete_roles(roles_created)
            self.sleep()

    def create_users_as(self, roles, create_as, required):
        """
        Create the ENM users

        :type roles: list
        :param roles: List of `enm_user_2.EnmRole` instances to be apply
        :type create_as: `enm_user_2.User`
        :param create_as: Enm User who will perform the deletion
        :type required: int
        :param required: Number of users required to be created

        :rtype: list
        :return: List of `enm_user_2.User` instances
        """
        users = []
        for i in xrange(required):
            user = User("{0}-{1}-{2}".format(self.identifier, "SECUI_02_USERS", i), "TestPassw0rd",
                        roles=roles, keep_password=True)
            try:
                user.create(create_as=create_as)
                self.teardown_list.append(user)
                users.append(user)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e.message))
        return users

    def create_roles_as(self, create_as, required):
        """
        Create the required roles

        :type create_as: `enm_user_2.User`
        :param create_as: Enm User who will perform the deletion
        :type required: int
        :param required: Number of users required to be created

        :rtype: list
        :return: List of `enm_user_2.EnmRole` instances
        """
        roles = []
        for i in xrange(required):
            role = EnmComRole("{0}-{1}-{2}".format(self.identifier, "SECUI_02_ROLES", i),
                              description="SECUI_02_03_description", user=create_as)
            try:
                role.create()
                self.teardown_list.append(role)
                roles.append(role)
            except Exception as e:
                self.add_error_as_exception(e)
        return roles

    def delete_users(self, users, delete_as):
        """
        Delete the created users

        :type users: list
        :param users: List of `enm_user_2.User` instances to be deleted
        :type delete_as: `enm_user_2.User`
        :param delete_as: Enm User who will perform the deletion
        """
        for user in users:
            try:
                user.delete(delete_as=delete_as)
                self.teardown_list.remove(user)
            except Exception as e:
                self.add_error_as_exception(e)

    def delete_roles(self, roles):
        """
        Delete the created roles

        :type roles: list
        :param roles: List of `enm_user_2.EnmRole` instances to be deleted
        """
        for role in roles:
            try:
                role.delete()
                self.teardown_list.remove(role)
            except Exception as e:
                self.add_error_as_exception(e)


class Secui03Flow(SecuiFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, ["SECURITY_ADMIN"])[0]
        while self.keep_running():
            try:
                toggle_password_aging_policy(user, enabled=False)
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep_until_time()


@retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=60000, stop_max_attempt_number=3)
def toggle_password_aging_policy(user, enabled=True):
    url = "/oss/idm/config/passwordsettings/enmuser"
    payload = {
        "passwordComplexity": [
            {"name": "minimumLength", "value": 8},
            {"name": "minimumLowerCase", "value": 1, "enabled": True},
            {"name": "minimumUpperCase", "value": 1, "enabled": True},
            {"name": "minimumDigits", "value": 1, "enabled": True},
            {"name": "minimumSpecialChars", "value": 1, "enabled": False},
            {"name": "maximumRepeatingChars", "value": 4, "enabled": False},
            {"name": "maximumConsecutiveChars", "value": 4, "enabled": False},
            {"name": "mustNotContainUserId", "enabled": False},
            {"name": "mustNotContainDictionaryWords", "enabled": False},
            {"name": "mustNotBeOldPassword", "value": 1, "enabled": False}],
        "passwordAgeing": {"pwdMaxAge": 90, "pwdExpireWarning": 7, "graceLoginCount": 0},
        "accountLockout": {
            "enabled": True, "loginLockoutExpiration": True, "loginFailureExpiration": True,
            "loginMaxFailedAttempts": 3, "loginLockoutExpirationTime": 3, "loginFailureExpirationTime": 5}
    }
    payload["passwordAgeing"]["enabled"] = enabled
    response = user.put(url, headers=JSON_SECURITY_REQUEST, data=json.dumps(payload))
    raise_for_status(response)


class Secui05Flow(SecuiFlow):
    CAPABILITIES = ["cm_editor", "cm_config", "cm_config_rest_nbi", "lcm", "nhm", "service_definition",
                    "service_manager", "cm-events-nbi", "fm_services", "topologyCollectionsService",
                    "connectivity_manager"]
    SECUI_01_KEY = "SECUI_01"

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        self.state = "SLEEPING"
        self.wait_until_secui_01_active()
        self.state = "RUNNING"
        self.delete_existing_secui_roles(users[0])
        self.create_custom_roles_for_users(users, self.capabilities)

    def delete_existing_secui_roles(self, user):
        """
        Delete any SECUI_05 roles leftover from previous runs

        :param user: User who will request the role deletion
        :type user: enm_user_2.User`
        """
        all_roles = EnmComRole("all_roles").get_all_roles(user)
        for role in all_roles:
            if self.NAME in role.name:
                try:
                    role.delete()
                except Exception as e:
                    self.add_error_as_exception(e)

    def create_custom_roles_for_users(self, users, multi_capabilities):
        """
        Create custom roles, based upon the provided users and capabilities

        :type users: list
        :param users: List of `enm_user_2.User` instances
        :type multi_capabilities: list
        :param multi_capabilities: List of ENM defined user capabilities
        """
        for user in users:
            for _ in xrange(self.CREATED_ROLE_COUNT):
                if _ is not 0:
                    user = None
                name = "{0}-{1}-{2}".format(self.identifier, "_ROLES", get_random_string(size=6))
                description = "SECUI_05 Description"
                custom_role = CustomRole(user=user, name=name, description=description,
                                         roles={EnmComRole("SystemAdministrator")},
                                         capabilities=set(multi_capabilities))
                try:
                    custom_role.create()
                    teardown_role = EnmComRole(name=custom_role.name)
                    self.teardown_list.append(picklable_boundmethod(teardown_role.delete))
                except Exception as e:
                    self.add_error_as_exception(e)

    def wait_until_secui_01_active(self):
        """
        Polls until the dependent profile is active
        """
        log.logger.debug("Profile waiting for SECUI_01 to be in correct state before proceeding")
        check_counter = 1

        while True:
            log.logger.debug("Checking to see if profile is active")
            if self.SECUI_01_KEY in get_active_profile_names():
                log.logger.debug("SECUI_01 now active - checking state")
                profile = get(self.SECUI_01_KEY)
                if profile and profile.state in ["STARTING", "RUNNING", "COMPLETED"]:
                    log.logger.debug("SECUI_01 now in {0} state".format(profile.state))
                    return

                log.logger.debug("Profile not in expected state yet")

            log.logger.debug("Sleeping 1 min before rechecking")
            time.sleep(60)
            check_counter += 1

            if not check_counter % 60:
                self.add_error_as_exception(EnvironError("Profile cannot proceed while SECUI_01 is not active"))


class Secui06Flow(SecuiFlow):
    REQUIRED = 600

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        self.state = "RUNNING"
        self.teardown_list.append(partial(recreate_deleted_user, user.username, self.USER_ROLES,
                                          get_workload_admin_user()))
        failed_certificates = 0
        self.clean_up_old_pki_profiles(user)
        pki_names_list = []
        for _ in xrange(self.REQUIRED):
            try:
                name = self.PKI_NAME.format(get_random_string(size=6, exclude=string.digits))
                self.create_certificate_profile(user, name)
                self.create_entity_profile(user, name)
                pki_names_list.append(name)
            except Exception as e:
                failed_certificates += 1
                log.logger.debug("Encountered exception for profile {0} Exception: {1}".format(name, e))
        all_entity_profiles = get_all_entity_profiles(user, limit=6000)
        for name in pki_names_list:
            self.create_and_issue_entity_certificate(user, name, all_entity_profiles)

        log.logger.debug("{0}/{1} Certificates created successfully".format((self.REQUIRED - failed_certificates),
                                                                            self.REQUIRED))
        if failed_certificates > 0:
            self.add_error_as_exception(EnmApplicationError("{0} Certificates failed to create".format(
                failed_certificates)))

    def create_certificate_profile(self, user, name):
        """
        Creates the certificate profile

        :type user: `enm_user_2.User`
        :param user: Enm user who will create the certificate profile
        :type name: str
        :param name: Identifier of the certificate profile
        """
        certificate_profile = CertificateProfile(user=user, name=name)
        try:
            certificate_profile.create()
            self.teardown_list.append(picklable_boundmethod(certificate_profile.delete))
        except Exception as e:
            self.add_error_as_exception(e)

    def create_entity_profile(self, user, name):
        """
        Creates the entity profile

        :type user: `enm_user_2.User`
        :param user: Enm user who will create the entity profile
        :type name: str
        :param name: Identifier of the entity profile
        """
        entity_profile = EntityProfile(user=user, name=name)
        try:
            entity_profile.create()
            self.teardown_list.append(picklable_boundmethod(entity_profile.delete))
        except Exception as e:
            self.add_error_as_exception(e)

    def create_and_issue_entity_certificate(self, user, name, all_entity_profiles):
        """
        Creates the entity

        :type user: `enm_user_2.User`
        :param user: Enm user who will create the entity
        :type name: str
        :param name: Identifier of the entity
        :param all_entity_profiles: list of available entity profiles
        :type all_entity_profiles: list
        """
        entity = Entity(user=user, name=name, all_profiles=all_entity_profiles)
        try:
            entity.set_all_profiles()
            entity.set_entity_profile_name_and_id()
            entity.create()
            self.teardown_list.append(picklable_boundmethod(entity._teardown))
            entity.issue()
        except Exception as e:
            self.add_error_as_exception(e)

    def clean_up_old_pki_profiles(self, user):
        """
        Clean up function to remove the old pki profiles (entities, entity profiles, certificate profiles) in ENM
        from previous runs

        :type user: `enm_user_2.User`
        :param user: Enm user who will perform the remove the old pki profiles activity.
        """
        entity = Entity(user, "Clean up instance")
        entity.remove_old_entities()
        entity_profile = EntityProfile(user=user, name=self.PKI_NAME)
        entity_profile.remove_old_entity_profiles()
        cert_profile = CertificateProfile(user=user, name=self.PKI_NAME)
        cert_profile.remove_old_certificate_profiles()


class Secui07Flow(SecuiFlow):
    CAPABILITIES = ["alarm_export", "alarm_overview", "alarm_search", "open_alarms", "nodes", "error_event",
                    "persistentobjectservice", "rootAssociations", "topologySearchService"]
    TARGET_GROUPS = []
    LIMIT = 100

    @property
    def role_name(self):
        return "{0}{1}".format(self.NAME, get_random_string(size=5))

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        # Create target groups
        self.TARGET_GROUPS = self.create_target_groups_and_assign_nodes()
        user = self.create_profile_users(1, roles=["SECURITY_ADMIN"])[0]

        if self.TARGET_GROUPS:
            # Create the role, and create the users with the role and 500 target groups
            users_required = len(self.TARGET_GROUPS) / self.LIMIT
            custom_role, teardown_role = self.create_custom_role(self.role_name, self.role_name, user)
            users = []
            for _ in xrange(users_required or 1):
                user, = self.create_custom_user(0, [custom_role],
                                                self.TARGET_GROUPS[_ * self.LIMIT: (_ + 1) * self.LIMIT])
                users.append(user)
            self.flow_cleanup(teardown_role, users)
        else:
            self.add_error_as_exception(EnmApplicationError("Failed to create traget groups, please check logs."))

    def flow_cleanup(self, role, users):
        """
        Perform clean up of the users, added our objects to the teardown

        :type role: `enm_user_2.CustomRole`
        :param role: Custom created role to be torn down
        :type users: list
        :param users: List of `enm_user_2.CustomUser` to be deleted
        """
        self._set_teardown_objects(role.delete)
        for group in self.TARGET_GROUPS:
            self._set_teardown_objects(group.delete)
        log.logger.debug("Waiting 60 seconds before attempting to delete user. "
                         "Required to break the association to the role and target groups.")
        time.sleep(60)
        for user in users:
            try:
                user.delete()
                if user in self.teardown_list:
                    self.teardown_list.remove(user)
            except Exception as e:
                log.logger.debug("Failed to delete user, response: {0}, teardown may be impacted.".format(e.message))

    def create_target_groups_and_assign_nodes(self):
        """
        Create the target groups, and update the groups with nodes

        :rtype: list
        :return: List of created Target Groups
        """
        profile_nodes = self.nodes_list
        total = 1
        target_groups = []
        while total <= self.NUM_TARGET_GROUPS:
            target = Target(name="Secui07_target_%s" % get_random_string(size=4), description="SecUI 07 Target Group.")
            try:
                if target.exists:
                    target.delete(user=get_workload_admin_user())
                target.create(create_as=get_workload_admin_user())
                target_groups.append(target)
                if target.exists:
                    target.update_assignment(nodes=profile_nodes, user=get_workload_admin_user())
                total += 1
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))
        return target_groups


class Secui08Flow(SecuiFlow):

    @property
    def description(self):
        return "SecUI 08 Target Group: {0}.".format(self.get_timestamp_str())

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["SECURITY_ADMIN"])[0]
        target_groups = []
        while len(target_groups) < self.NUM_TARGET_GROUPS:
            target_groups.extend(self.create_target_groups(user, self.NUM_TARGET_GROUPS - len(target_groups)))
        while self.keep_running():
            for group in target_groups:
                try:
                    group.update(description=self.description, user=get_workload_admin_user())
                except Exception as e:
                    self.add_error_as_exception(e)
            self.sleep()

    def create_target_groups(self, user, required):
        """
        Create the required number of target groups

        :type user: `enm_user_2.User`
        :param user: User who create the groups
        :type required: int
        :param required: Number of users required to be created

        :rtype: list
        :return: List of `enm_user_2.TargetGroup` instances
        """
        target_groups = []
        for _ in xrange(required):
            target = Target(name="%s_target_%d" % (self.NAME, _), description="%s Target Group" % self.NAME)
            try:
                if target.exists:
                    target.delete(user=user)
                target.create(create_as=user)
                self.teardown_list.append(target)
                target_groups.append(target)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))
        return target_groups


class Secui09Flow(Secui08Flow):

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["SECURITY_ADMIN"])[0]
        while self.keep_running():
            target_groups = self.create_target_groups(user, 30)
            self.delete_target_groups(target_groups)
            self.sleep()

    def delete_target_groups(self, target_groups):
        """
        Delete the supplied list of target groups

        :type target_groups: list
        :param target_groups: List of `enm_user_2.TargetGroup` instances
        """
        for target in target_groups:
            try:
                target.delete(user=get_workload_admin_user())
                self.teardown_list.remove(target)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))


class Secui10Flow(SecuiFlow):

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        self.state = "RUNNING"
        while self.keep_running():
            ldap_nodes_list = []
            nodes = self.determine_nodes(user)
            log.logger.debug("{0} synced radio nodes: {1}".format(len(nodes), [node.node_id for node in nodes]))
            if nodes:
                ldap_configured_nodes = self.check_ldap_is_configured_on_nodes(user, nodes)
                for node in ldap_configured_nodes:
                    ldap_nodes_list.append([user, node])
                if ldap_nodes_list:
                    self.create_and_execute_threads(ldap_nodes_list, len(ldap_nodes_list), args=[self])
                else:
                    self.add_error_as_exception(EnvironError("Nodes not LDAP configured"))
            else:
                self.add_error_as_exception(EnvironError("Nodes not synchronized"))
            self.sleep()
            self.exchange_nodes()

    def determine_nodes(self, user):
        """
        Identify usable nodes, return unused nodes to the pool

        :type user: `enm_user_2.User`
        :param user: User who will query the sync status
        :rtype: list
        :return: List of `enm_node.Node` instances
        """
        all_nodes = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'profiles', 'oss_prefix'])
        synced = self.get_synchronised_nodes(all_nodes, user)
        nodes = [node for node in synced][:50]
        unused = set(all_nodes) - set(nodes)
        SHMUtils.deallocate_unused_nodes(list(unused), self)
        return nodes

    @staticmethod
    def task_set(ldap_nodes_list, profile, validation_string=None):  # pylint: disable=arguments-differ
        """
        Task set to be perform ed the threads

        :type ldap_nodes_list: list
        :param ldap_nodes_list: List containing user object and the nodes to be configured
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        :type validation_string:
        :param validation_string: String to search for within the returned response
        :raises EnvironError: raised if the command is not successful
        :raises EnmApplicationError: if there is no output from the command
        :rtype: list
        :return: List of values returned from the command execution
        """
        user = ldap_nodes_list[0]
        node = ldap_nodes_list[1]
        label = get_random_string(size=4, exclude=string.digits)
        set_label_cmd = ('cmedit set {subnetwork},ManagedElement={node_id},SystemFunctions=1,SecM=1,UserManagement=1,'
                         'LdapAuthenticationMethod=1,Ldap=1 userLabel="{label}"')
        try:
            cmd = set_label_cmd.format(subnetwork=node.oss_prefix, node_id=node.node_id, label=label.upper())
            response = user.enm_execute(cmd)
            if not response.get_output():
                raise EnmApplicationError('Command Execution, returned no response.')
            if any(re.search(r'({0}|error|^[0]\sinstance)'.format(validation_string), line, re.I) for line in
                   response.get_output()):
                raise EnvironError('Command [{0}] execution failed. Response: {1}'.format(cmd, response.get_output()))
            log.logger.debug('Successfully executed: [{0}].'.format(cmd))
            return response.get_output()
        except Exception as e:
            profile.add_error_as_exception(e)


class Secui11Flow(SecuiFlow):

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        self.state = "RUNNING"
        message = ("All ENM users have TBAC enabled because the default Target Group 'ALL' is assigned to each user "
                   "when the user is created.")
        log.logger.info("This profile is just for informational purposes only: {0}".format(message))


class Secui12Flow(SecuiFlow, FIDM_interface, GenericFlow):
    EXTERNAL_LDAP_SETTINGS = '/oss/idm/config/extidp/settings'
    LDAP_SERVER_CONNECTIVITY = '/oss/idm/config/extidp/settings/test/connectivity'
    LDAP_SERVER_AUTHENTICATION = '/oss/idm/config/extidp/settings/test/authentication'
    NUMBER_OF_RETRIES = 10

    def get_external_ldap_settings(self, user):
        """
        Returns External ldap settings
        :param user: user to use for the REST request
        :type user: enmutils.lib.enm_user_2.User

        :return: Json from response to Get request
        :rtype: dict
        """
        response = user.get(self.EXTERNAL_LDAP_SETTINGS, headers=JSON_SECURITY_REQUEST)
        raise_for_status(response, "Failed to get external ldap settings from ENM")
        log.logger.debug("Successfully fetched External ldap settings")
        log.logger.debug("Response: {0} ".format(response.json()))
        return response.json()

    def check_external_ldap_settings(self, external_ldap_settings):
        """
        This function checks the Ldap settings are configured correctly or not based on forty_network file values
        :param external_ldap_settings: configurations of external ldap
        :type external_ldap_settings: dict
        :return: returns the True or False
        :rtype: boolean
        """
        ldap_configured = True
        required_external_ldap_settings = {"authType": self.authType, "remoteAuthProfile": self.remoteAuthProfile,
                                           "baseDN": self.baseDN, "ldapConnectionMode": self.ldapConnectionMode,
                                           "primaryServerAddress": config.get_prop('primary_ldap_server'),
                                           "secondaryServerAddress": config.get_prop('secondary_ldap_server'),
                                           "userBindDNFormat": self.userBindDNFormat, "bindDN": self.bindDN}

        existing_ext_ldap_settings = external_ldap_settings['extIdpSettings']
        log.logger.debug("existing external ldap settings : {0}".format(existing_ext_ldap_settings))
        for setting_key, setting_value in required_external_ldap_settings.iteritems():
            if setting_key in existing_ext_ldap_settings and setting_value != existing_ext_ldap_settings[setting_key]:
                ldap_configured = False
                break
        log.logger.debug("ldap configured :{0} ".format(ldap_configured))
        return ldap_configured

    def configure_external_ldap_settings_in_enm(self, user):
        """
        configure the ldap external settings
        :param user: user to send for the REST request
        :type user: enmutils.lib.enm_user_2.User
        """
        payload = {"authType": self.authType, "remoteAuthProfile": self.remoteAuthProfile,
                   "baseDN": self.baseDN, "primaryServerAddress": config.get_prop('primary_ldap_server'),
                   "secondaryServerAddress": config.get_prop('secondary_ldap_server'),
                   "ldapConnectionMode": self.ldapConnectionMode, "userBindDNFormat": self.userBindDNFormat,
                   "bindDN": self.bindDN, "bindPassword": self.bindPwd}

        response = user.put(self.EXTERNAL_LDAP_SETTINGS, json=payload, headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, "Failed to configure the external ldap settings")
        log.logger.debug("Successfully configured External ldap settings, Response : {0}".format(response.status_code))

    def create_ldap_user_in_enm(self):
        """ Deprecated 23.16 Delete 24.11 JIRA:ENMRTD-23821 """

    def verify_external_ldap_connectivity(self, user):
        """
        Verifies if the connection between ENM and external LDAP is established or not
        :param user: ENM user for verifying connectivity
        :type user: enmutils.lib.enm_user_2.User
        :raises ValidationError: If external LDAP connectivity is not successful
        """
        payload = {'bindDN': self.bindDN, 'ldapConnectionMode': self.ldapConnectionMode,
                   'serverAddress': config.get_prop('primary_ldap_server')}
        response = user.post(self.LDAP_SERVER_CONNECTIVITY, data=json.dumps(payload), headers=JSON_SECURITY_REQUEST)
        raise_for_status(response, "Failed to validate external ldap connectivity")
        json_response = response.json()
        result = json_response['successfulTest']
        if result:
            log.logger.info("External ldap connectivity is success : {0}".format(result))
        else:
            raise ValidationError("Unable to establish connectivity with external ldap server, "
                                  "Response : {0}, Result : {1}".format(json_response, result))

    def verify_external_ldap_authentication(self, user):
        """
        Verifies if the authentication between ENM and external LDAP
        :param user: enmutils.lib.enm_user_2.User
        :type user: ENM user for verifying authentication
        :raises ValidationError: If external LDAP authentication is not successful
        """
        payload = {'bindDN': self.bindDN, 'ldapConnectionMode': self.ldapConnectionMode,
                   'serverAddress': config.get_prop('primary_ldap_server')}
        response = user.post(self.LDAP_SERVER_AUTHENTICATION, data=json.dumps(payload), headers=JSON_SECURITY_REQUEST)
        raise_for_status(response, "Failed to validate external ldap authentication")
        json_response = response.json()
        result = json_response['successfulTest']
        if result:
            log.logger.info("External ldap authentication is successful : {0}".format(result))
        else:
            raise ValidationError("Unable to authenticate external ldap server, "
                                  "Response : {0}, Result : {1}".format(json_response, result))

    def ldap_configuration_prerequisites(self):
        """
        Checks if there is an existing ldap configuration. If yes, will compare with required settings. If no, will
        update the ldap settings as per the requirement
        :raises EnmApplicationError: If unable to fetch existing external LDAP settings from ENM
        """
        user = get_workload_admin_user()
        external_ldap_settings = self.get_external_ldap_settings(user)
        if external_ldap_settings:
            ldap_configured = self.check_external_ldap_settings(external_ldap_settings)
            log.logger.debug("Ldap configured : {0}".format(ldap_configured))
            if not ldap_configured:
                self.configure_external_ldap_settings_in_enm(user)
            self.verify_external_ldap_connectivity(user)
            self.verify_external_ldap_authentication(user)
        else:
            raise EnmApplicationError("Could not fetch external ldap settings from ENM, please check profile logs")

    def perform_fidm_sync_postconditions(self, ldap_user):
        """
        This method performs some set of operations like, i.e. force sync the federated identity synchronization,
        get the federated identity synchronization sync state and get last federated identity synchronization report.

        :param ldap_user: remote ldap user
        :type ldap_user: enmutils_int.lib.enm_user.CustomUser
        """
        self.force_sync_federated_identity_synchronization(ldap_user)
        self.wait_force_sync_federated_identity_synchronization_to_complete(ldap_user)
        log.logger.debug("Sleeping for {0} seconds before get the last federated identity synchronization "
                         "report".format(30))
        time.sleep(30)
        self.get_federated_identity_last_synchronization_report(ldap_user)

    def perform_fidm_sync_preconditions(self, ldap_user):
        """
        This method Performs the set of federated identity synchronization operations,
        like, i.e. import federated identity synchronization, set period for federated identity synchronization,
        set federated identity synchronization sync state (enabled)

        :param ldap_user: remote ldap user
        :type ldap_user: enmutils_int.lib.enm_user.CustomUser
        """
        self.import_federated_identity_synchronization(ldap_user)
        self.set_federated_identity_synchronization_period(ldap_user)
        self.set_federated_identity_synchronization_admin_state(ldap_user, "enabled")
        self.perform_fidm_sync_postconditions(ldap_user)

    def set_fidm_sync_teardown_objects(self, ldap_user):
        """
        Adds federated identity synchronization teardown objects to the teardown list.

        :param ldap_user: remote ldap user
        :type ldap_user: enmutils_int.lib.enm_user.CustomUser
        """
        self.teardown_list.append(partial(picklable_boundmethod(
            self.restore_to_defaults_federated_identity_synchronization), ldap_user))
        self.teardown_list.append(partial(picklable_boundmethod(self.verify_federated_users_deletion_status)))
        self.teardown_list.append(partial(picklable_boundmethod(
            self.wait_force_delete_federated_identity_synchronization_to_complete), ldap_user))
        self.teardown_list.append(partial(picklable_boundmethod(self.force_delete_federated_identity_synchronization),
                                          ldap_user))
        self.teardown_list.append(partial(picklable_boundmethod(
            self.set_federated_identity_synchronization_admin_state), ldap_user, "disabled"))

    def federated_user_login(self, federated_user):
        """
        login to ENM with federated user
        """
        try:
            federated_user.open_session(reestablish=True)
            log.logger.debug("Sleeping for 60 sec before removing the {0} federated user session".format(
                self.FEDERATED_USER_NAME))
            time.sleep(60)
            federated_user.remove_session()
        except Exception as e:
            log.logger.debug("Unable to open session with the {0} federated user, Error : {1}".format(
                str(e), self.FEDERATED_USER_NAME))
            self.add_error_as_exception(EnmApplicationError(e))

    def external_ldap_user_login(self, ldap_user):
        """
        login to ENM with external ldap user

        :param ldap_user: remote ldap user
        :type ldap_user: enmutils_int.lib.enm_user.CustomUser
        """
        try:
            ldap_user.open_session(reestablish=True)
            log.logger.debug("Sleeping for 60 sec before removing the user session")
            time.sleep(60)
            ldap_user.remove_session()
        except Exception as e:
            log.logger.debug("Unable to open session with the ldap user, Error : {0}".format(str(e)))
            self.add_error_as_exception(EnmApplicationError(e))

    def create_federated_user_instance(self):
        """
        creates CustomUser instance for federated user.

        :return: federated user
        :rtype: enmutils_int.lib.enm_user.CustomUser
        """
        roles = self.USER_ROLES + self.CUSTOM_USER_ROLES
        roles = list(set(EnmRole(role) if isinstance(role, basestring) else role for role in roles))
        targets = list(set(Target(tg_group) if isinstance(tg_group, basestring) else tg_group for tg_group
                           in self.CUSTOM_TARGET_GROUPS))
        federated_user = CustomUser(username=self.FEDERATED_USER_NAME, password=self.FEDERATED_USER_NAME, roles=roles,
                                    targets=targets, safe_request=False, retry=True, persist=False,
                                    keep_password=True, authmode='remote')
        return federated_user

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        remote_user = None
        self.state = "RUNNING"
        try:
            self.check_remove_old_federated_users_with_roles_tgs()
            self.ldap_configuration_prerequisites()
            self.create_custom_roles_and_target_groups(self.CUSTOM_USER_ROLES, self.CUSTOM_TARGET_GROUPS)
            remote_user = self.create_custom_user_in_enm()
            self.perform_fidm_sync_preconditions(remote_user)
            federated_user = self.create_federated_user_instance()
        except Exception as e:
            if remote_user:
                self.set_federated_identity_synchronization_admin_state(remote_user, "disabled")
            self.add_error_as_exception(EnmApplicationError(e))
        else:
            self.set_fidm_sync_teardown_objects(remote_user)

            while self.keep_running():
                self.federated_user_login(federated_user)
                self.external_ldap_user_login(remote_user)

                self.sleep()

    def verify_federated_users_deletion_status(self, required_return_value=False):
        """
        Checking the federated users deleted in enm or not.
        :raises EnvironError: If still federated users existed in enm even
        federated identity synchronization forced delete operation completed.

        :return: True if federated users existed in ENM, otherwise returns false,
                 when required_return_value value is True
        :rtype: bool
        """
        all_user_names = User.get_usernames()
        federated_users = [user_name for user_name in all_user_names if self.FEDERATED_USER_NAME[:14] in user_name]
        log.logger.debug("{0} federated users existed in ENM".format(len(federated_users)))
        if required_return_value:
            return True if federated_users else False
        if federated_users:
            raise EnvironError("Still {0} Federated users existed in ENM even federated identity synchronization "
                               "forced delete operation completed.".format(len(federated_users)))
        else:
            log.logger.debug("Federated users deleted successfully in ENM")

    def check_remove_old_federated_users_with_roles_tgs(self):
        """
        Checks and remove the old federated users, ldap user, custom user roles and target groups.
        """
        log.logger.debug("Attempt to Clear the old federated users, ldap user, "
                         "federated custom user roles and target groups")
        try:
            user = get_workload_admin_user()
            if self.verify_federated_users_deletion_status(required_return_value=True):
                self.delete_old_ldap_user()
                self.delete_old_federated_users(user)
                self.delete_existing_federated_users_required_roles(user)
                self.delete_existing_federated_users_required_target_groups(user)
                log.logger.debug("Successfully removed old federated users, ldap user, "
                                 "federated custom user roles and target groups")
            elif self.check_old_ldap_user_exist():
                self.delete_old_ldap_user()
                self.delete_existing_federated_users_required_roles(user)
                self.delete_existing_federated_users_required_target_groups(user)
                log.logger.debug("Successfully removed old ldap user, federated custom user roles and target groups")
            else:
                log.logger.debug("Old federated users and {0} ldap user not existed in ENM".format(self.USER_NAME))
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))

    def delete_old_federated_users(self, user):
        """
        Deletes the old federated users in ENM by performing required FIDM operations.
        :type user: enm_user_2.User
        :param user: User instance
        """
        try:
            self.set_federated_identity_synchronization_admin_state(user, "disabled")
            self.force_delete_federated_identity_synchronization(user)
            self.wait_force_delete_federated_identity_synchronization_to_complete(user)
            self.verify_federated_users_deletion_status()
            self.restore_to_defaults_federated_identity_synchronization(user)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))

    def delete_existing_federated_users_required_roles(self, user):
        """
        Deletes the old federated users required roles in ENM.
        :type user: enm_user_2.User
        :param user: User instance
        """
        log.logger.debug("Attempting to delete the {0} custom user roles".format(
            ','.join(str(role) for role in self.CUSTOM_USER_ROLES)))
        for usr_role in self.CUSTOM_USER_ROLES:
            try:
                custom_role = CustomRole(user=user, name=usr_role, description=usr_role,
                                         roles={EnmComRole(self.COMROLE)},
                                         capabilities=set(self.capabilities))
                custom_role.delete()
            except Exception as e:
                log.logger.debug("Failed to delete the custom role: {0} due to {1}".format(usr_role, e))

    def delete_existing_federated_users_required_target_groups(self, user):
        """
        Deletes the old federated users required target groups in ENM.
        :type user: enm_user_2.User
        :param user: User instance:
        """
        log.logger.debug("Attempting to delete the {0} custom target groups".format(
            ','.join(str(group) for group in self.CUSTOM_TARGET_GROUPS)))
        for tg in self.CUSTOM_TARGET_GROUPS:
            try:
                target_group = Target(name=tg, description="{0} Target Group".format(tg))
                target_group.delete(user=user)
            except Exception as e:
                log.logger.debug("Failed to delete the custom target group: {0} due to {1}".format(tg, e))

    def delete_old_ldap_user(self):
        """
        Deletes the old ldap user in ENM.
        """
        try:
            log.logger.debug("Attempting to delete the {0} user".format(self.USER_NAME))
            ldap_user = CustomUser(username=self.USER_NAME, password=self.USER_PASSWORD, roles=[],
                                   targets=[], safe_request=False, retry=True, persist=False,
                                   keep_password=True, authmode='remote')
            ldap_user.delete()
        except Exception as e:
            log.logger.debug("Failed to delete the {0} user due to {1}".format(self.USER_NAME, e))

    def check_old_ldap_user_exist(self):
        """
        Checks in ENM if RemoteUser_01 user (ldap user) exists
        :return: True if user exists else False
        :rtype: bool
        """
        user_available = False
        try:
            user_available = user_exists(get_workload_admin_user(), search_for_username=self.USER_NAME)
            log.logger.debug("{0} user already exists in ENM".format(self.USER_NAME))
        except Exception as e:
            log.logger.debug("Failed to get the {0} user exist status due to {1}".format(self.USER_NAME, e))
        return user_available
