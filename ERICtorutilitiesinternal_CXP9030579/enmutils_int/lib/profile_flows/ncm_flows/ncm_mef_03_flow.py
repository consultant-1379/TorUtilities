from enmutils_int.lib.ncm_manager import fetch_ncm_vm, ncm_rest_query, ncm_run_cmd_on_vm
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils.lib.exceptions import EnvironError
from enmutils.lib import log


class NcmMef03Flow(GenericFlow):

    HEALTH_CHECK_DISABLE = 'sudo su -c \'mv /usr/lib/ocf/resource.d/ncm_jboss_healthcheck.sh /tmp\''
    NCM_DB_REMOVE = 'sudo su ncmuser -c \'/opt/ericsson/ncm/app/app-admin.ksh dbremove -s\''
    NCM_DB_CREATE = 'sudo su ncmuser -s /opt/ericsson/ncm/app/app-admin.ksh dbcreate'
    NCM_START = 'sudo su ncmuser -c \'/etc/init.d/ncm start\''
    HEALTH_CHECK_ENABLE = 'sudo su -c \'mv /tmp/ncm_jboss_healthcheck.sh /usr/lib/ocf/resource.d/\''
    FULL_RE_ALIGNEMENT = "/ncm/rest/management/realign"

    def execute_flow(self):
        """
        Executes the flow for the mef_03 profile
        """
        self.state = "RUNNING"
        try:
            users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
            self.perform_ncm_db_activites()
            ncm_rest_query(users[0], self.FULL_RE_ALIGNEMENT)
        except Exception as e:
            self.add_error_as_exception(e)

    def perform_ncm_db_activites(self):
        """
        Executes NCM DB activites - Disabling/enabling ncm health check and removing/creating ncm db
                                    and stating ncm application
        :raises EnvironError: when ncm vm is not available
        """
        log.logger.debug("performing ncm_db activites")
        vm = fetch_ncm_vm()
        if vm:
            log.logger.debug("Disabling NCM jboss healthcheck on vm: {0}".format(vm))
            ncm_run_cmd_on_vm(self.HEALTH_CHECK_DISABLE, vm)
            log.logger.debug("Running NCM dbremove command....")
            ncm_run_cmd_on_vm(self.NCM_DB_REMOVE, vm)
            log.logger.debug("Running NCM dbcreate command....")
            ncm_run_cmd_on_vm(self.NCM_DB_CREATE, vm)
            log.logger.debug("Running NCM start command....")
            ncm_run_cmd_on_vm(self.NCM_START, vm)
            log.logger.debug("Enabling ncm_jboss_healthcheck....")
            ncm_run_cmd_on_vm(self.HEALTH_CHECK_ENABLE, vm)
        else:
            raise EnvironError("NCM vm is not listed")
