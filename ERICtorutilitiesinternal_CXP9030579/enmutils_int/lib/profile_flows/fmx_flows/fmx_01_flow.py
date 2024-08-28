import time
from requests.exceptions import HTTPError
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile
from enmutils_int.lib.fmx_mgr import FmxMgr, ACTIVE_SIMULATION_STATE, SIMULATION_MODULE
from enmutils_int.lib.enm_user import user_exists, get_workload_admin_user, CustomUser
from enmutils.lib import log
from enmutils.lib.enm_user_2 import EnmRole, Target
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.exceptions import (NotLoadedFmxModuleError, NotActivatedFmxModuleError, EnvironError,
                                     EnmApplicationError)
from enmutils.lib.cache import is_enm_on_cloud_native


class FMX01(FlowProfile):
    #  These are utilities modules: BASEBLOCKS-MODULE, ENM-BLOCKS-MODULE, EXCLUSIVE-REGION-MODULE
    #  and are dependencies of the NSX modules! These only need to be imported & loaded
    FMX_UTILITYMODULES = ['baseblocks-module', 'enm-blocks-module', 'exclusive-region-module', 'enmcli-blocks-module']
    INITIAL_RUN = True
    ALL_MODULES = []
    USER_NAME = "fmxenmcli"       # username has to be fmxenmcli for vieweing ENM node topology in FMX UI as documented in ENM SAG
    PASSWORD = "TestPassw0rd"
    ROLES = ['FM_Operator', 'Cmedit_Administrator']
    USER_NAME_1 = "fmxenmmml"
    ROLES_1 = ['WinFIOL_Operator', 'Element_Manager_Operator']

    def execute_filter_updates(self, fmx_mgr):
        """
        Executes FMX filter updates if Router 6672 has to be added on Transport network
        or if profile is running on physical deployment.

        :param fmx_mgr: FmxMgr object which will execute filter updates
        :type fmx_mgr: enmutils_int.lib.fmx_mgr.FmxMgr
        """
        if not fmx_mgr.vm_addresses:
            self.add_error_as_exception(EnvironError("FMX VM address is not present. Filter update could not be "
                                                     "executed!"))
        else:
            try:
                cloud = self.cloud
                execute_on_transport = self.execute_on_transport
                fmx_mgr.execute_filter_file_updates(execute_on_transport=execute_on_transport, cloud=cloud)
            except Exception as e:
                self.add_error_as_exception(EnvironError("FMX Filter updates failed! Exception : {}".format(e)))

    def load_activate_fmx_modules(self, fmx_mgr):
        """
        Imports/Loads/Activates the given fmx modules and checks their status after the initial run
        :param fmx_mgr: Instance of FmxMgr class
        :type fmx_mgr: enmutils_int.lib.fmx_mgr.FmxMgr
        :raises NotLoadedFmxModuleError: raised if any of the required module is not loaded after initial run
        :raises NotActivatedFmxModuleError: raised if any of the required rule module is not activated after initial run
        """
        log.logger.info("Fetching the loaded and active modules from FMX module management")
        loaded_modules, _, active_rule_modules = fmx_mgr._get_loaded_rule_active_modules(fmx_mgr.get_loaded_modules())

        if self.INITIAL_RUN:
            if loaded_modules:
                log.logger.debug("NOTE :  This is an initial run, but these modules "
                                 "were already loaded: {0}".format(', '.join(loaded_modules)))
            fmx_mgr.import_load()
            self.execute_filter_updates(fmx_mgr)
            fmx_mgr.activate_fmx_modules()
            check = fmx_mgr.enable_simulation_module(SIMULATION_MODULE) if \
                (ACTIVE_SIMULATION_STATE[0] == 'NotEnabled' and 'CN_Signalling_Disturbances' in self.FMX_RULEMODULES) \
                else (log.logger.debug("Simulation already enabled or unsupported deployment to enable simulation"))
            log.logger.debug('simulation check {}'.format(check))
            self.INITIAL_RUN = False
        else:
            # this is not initial run, so it is expected that all modules are loaded
            missing_modules = set(self.ALL_MODULES).difference(set(loaded_modules))
            if missing_modules:
                raise NotLoadedFmxModuleError("These FMX modules are not loaded: '{0}'".format(
                    ','.join(missing_modules)))

            not_activated = set(self.FMX_RULEMODULES).difference(set(active_rule_modules))
            check = fmx_mgr.enable_simulation_module(SIMULATION_MODULE) if\
                (ACTIVE_SIMULATION_STATE[0] == 'NotEnabled' and 'CN_Signalling_Disturbances' in self.FMX_RULEMODULES) \
                else (log.logger.debug("Simulation already enabled or unsupported deployment to enable simulation"))
            log.logger.debug('simulation check {}'.format(check))
            if not_activated:
                raise NotActivatedFmxModuleError("These FMX rule-modules are not activated: '{0}'".format(
                    ','.join(not_activated)))

    def create_fmxenmcli_user(self):
        """
        creates a custom user fmxenmcli for FMX operations
        :return: fmxenmcli user object
        :rtype: enmutils_int.lib.enm_user.CustomUser
        :raises EnmApplicationError: is user session is not established
        :raises e: is user session is not established
        """
        retries = 0
        sleep_time = 300
        roles = list(EnmRole(role) if isinstance(role, basestring) else role for role in self.ROLES)
        targets = [Target("ALL")]
        fmxenmcli_user = CustomUser(username=self.USER_NAME, password=self.PASSWORD, roles=roles, targets=targets,
                                    fail_fast=False, safe_request=False, retry=True, persist=False,
                                    keep_password=True)
        while retries < 3:
            try:
                fmxenmcli_user.create()
                log.logger.info("fmxenmcli user created successfully in ENM, sleeping for {0} sec before trying "
                                "to login".format(sleep_time))
                time.sleep(sleep_time)
                break
            except Exception as e:
                log.logger.debug("Exception : {0}".format(e))
                log.logger.debug("Failed to create fmxenmcli user in ENM, sleeping for {0} "
                                 "seconds before retrying.".format(sleep_time))
                time.sleep(sleep_time)
                retries += 1
        try:
            session_established = fmxenmcli_user.is_session_established()
            if not session_established:
                raise EnmApplicationError("fmxenmcli user is unable to login to ENM, "
                                          "please check the profile log for more details")
        except Exception as e:
            raise e
        return fmxenmcli_user

    def create_fmxenmmml_user(self):
        """
        creates a custom user fmxenmmml for FMX operations
        :return: fmxenmmml user object
        :rtype: enmutils_int.lib.enm_user.CustomUser
        :raises EnmApplicationError: is user session is not established
        :raises e: is user session is not established
        """
        retries = 0
        sleep_time = 300
        roles = list(EnmRole(role) if isinstance(role, basestring) else role for role in self.ROLES_1)
        targets = [Target("ALL")]
        fmxenmmml_user = CustomUser(username=self.USER_NAME_1, password=self.PASSWORD, roles=roles, targets=targets,
                                    fail_fast=False, safe_request=False, retry=True, persist=False,
                                    keep_password=True)
        while retries < 3:
            try:
                fmxenmmml_user.create()
                log.logger.info("fmxenmmml user created successfully in ENM, sleeping for {0} sec before trying "
                                "to login".format(sleep_time))
                time.sleep(sleep_time)
                break
            except Exception as e:
                log.logger.debug("Exception : {0}".format(e))
                log.logger.debug("Failed to create fmxenmmml user in ENM, sleeping for {0} "
                                 "seconds before retrying.".format(sleep_time))
                time.sleep(sleep_time)
                retries += 1
        try:
            session_established = fmxenmmml_user.is_session_established()
            if not session_established:
                raise EnmApplicationError("fmxenmmml user is unable to login to ENM, "
                                          "please check the profile log for more details")
        except Exception as e:
            raise e
        return fmxenmmml_user

    def check_for_fmxenmcli_user(self):
        """
        Checks in ENM if fmxenmcli user exists, if not creates one
        :return: True if user exists else Flase
        :rtype: bool
        """
        user_available = False
        try:
            user_available = user_exists(get_workload_admin_user(), search_for_username=self.USER_NAME)
            log.logger.info("{0} user already exists in ENM".format(self.USER_NAME))
            return user_available
        except HTTPError as e:
            if e.response.status_code == 404 and 'Not Found' in e.response.reason:
                log.logger.info("Response : {0}".format(e.response.reason))
                log.logger.info("{0} user is not found in ENM, creating the user now".format(self.USER_NAME))
                self.create_fmxenmcli_user()
            else:
                log.logger.debug("Exception encountered while checking if fmxenmcli user exists : {0}".format(e))

    def check_for_fmxenmmml_user(self):
        """
        Checks in ENM if fmxenmmml user exists, if not creates one
        :return: True if user exists else Flase
        :rtype: bool
        """
        user_available = False
        try:
            user_available = user_exists(get_workload_admin_user(), search_for_username=self.USER_NAME_1)
            log.logger.info("{0} user already exists in ENM".format(self.USER_NAME_1))
            return user_available
        except HTTPError as e:
            if e.response.status_code == 404 and 'Not Found' in e.response.reason:
                log.logger.info("Response : {0}".format(e.response.reason))
                log.logger.info("{0} user is not found in ENM, creating the user now".format(self.USER_NAME_1))
                self.create_fmxenmmml_user()
            else:
                log.logger.debug("Exception encountered while checking if fmxenmmml user exists : {0}".format(e))

    def check_post_user_creation(self, fmx_mgr):
        """
        Checks for deployment type and perform post user creation steps
        param fmx_mgr: FmxMgr object which will check post user creation
        :type fmx_mgr: enmutils_int.lib.fmx_mgr.FmxMgr
        """
        if not is_enm_on_cloud_native():
            fmx_mgr.execute_post_fmxenmcli_creation_steps(self.USER_NAME, self.PASSWORD)
        else:
            fmx_mgr.execute_post_fmxenmcli_creation_steps_cloudnative(self.USER_NAME, self.PASSWORD)
        log.logger.info("post user creation steps are completed")

    def execute_fmx_01_flow(self):
        """
        Executes the flow of fmx_01 profile
        """
        user = None
        fmx_mgr = None
        self.ALL_MODULES = self.FMX_UTILITYMODULES + self.FMX_RULEMODULES
        self.state = "RUNNING"
        fmxenmcli_user_exists = self.check_for_fmxenmcli_user()
        self.check_for_fmxenmmml_user()
        while self.keep_running():
            try:
                if not user:
                    user, = self.create_users(1, self.USER_ROLES, retry=True, fail_fast=False)
                    if user:
                        fmx_mgr = FmxMgr(all_modules=self.ALL_MODULES, user=user)
                        self.teardown_list.append(picklable_boundmethod(fmx_mgr._teardown))
                        self.load_activate_fmx_modules(fmx_mgr)
                        if not fmxenmcli_user_exists:
                            self.check_post_user_creation(fmx_mgr)
                    else:
                        log.logger.info("User creation failed, profile will re-try in the next iteration!")
                else:
                    self.load_activate_fmx_modules(fmx_mgr)
            except Exception as e:
                self.add_error_as_exception(e)

            self.sleep()
