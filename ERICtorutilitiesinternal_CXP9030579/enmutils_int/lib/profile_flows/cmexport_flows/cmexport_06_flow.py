from datetime import datetime
from functools import partial

import pexpect

from enmutils.lib import log, filesystem
from enmutils.lib.cache import get_emp, get_ms_host, is_enm_on_cloud_native
from enmutils.lib.config import is_a_cloud_deployment
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.enm_export import CmExport, toggle_pib_historicalcmexport
from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_common_utils import (confirm_eniq_topology_export_enabled,
                                                                                 toggle_pib_historical_cm_export)
from enmutils_int.lib.services.deployment_info_helper_methods import is_eniq_server
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class CmExport19Flow(GenericFlow):

    ENIQ_HISTORICAL_SETUP_CMD = '{integration_script} eniqcmexport'
    HISTORICAL_EXPORT = True
    ENIQ_INT_SCRIPT = '/usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_enm_integration.py'
    ENIQ_INT_SCRIPT_FOR_CLOUD = 'sudo /usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_venm_integration.py'

    def execute_flow(self):
        """
        Configures ENIQ events and stats on wlvm
        """
        self.set_teardown_objects()
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        self.state = "RUNNING"
        while self.keep_running():
            try:
                if is_enm_on_cloud_native():
                    cmexport = CmExport(name="ExportTesting", user=user, nodes=None, verify_timeout=180 * 60,
                                        filetype="3GPP", file_compression="gzip")
                    job_name = datetime.today().strftime("%d%m%Y")
                    cmexport.create_over_nbi(job_name="CMEXPORT_19_{0}".format(job_name))
                    cmexport.validate_over_nbi()
                else:
                    eniq_configured = is_eniq_server(emp=get_emp(), lms=get_ms_host())[0]
                    if eniq_configured and not confirm_eniq_topology_export_enabled(historical=self.HISTORICAL_EXPORT):
                        log.logger.debug("Export is not currently enabled.")
                        log.logger.debug("Executing setup commands.")
                        self.execute_setup_commands()
                        log.logger.debug("Setup commands completed.")
                    elif not eniq_configured:
                        raise EnvironError("ENIQ is not integrated. If physical environment, please check whether PM_44 "
                                           "profile is running without any errors on the workload vm. If cloud "
                                           "environment, integrate ENIQ with ENM, until then the profile will not execute "
                                           "the use-case")
                    self.confirm_export_configured()
            except Exception as e:
                self.add_error_as_exception(EnvironError(e))
            self.sleep_until_time()

    def confirm_export_configured(self):
        """
        Confirm the ENIQ export has been fully configured or Error the profile
        """
        if confirm_eniq_topology_export_enabled(historical=self.HISTORICAL_EXPORT):
            log.logger.debug("Export is enabled, setting pib values.")
            toggle_pib_historical_cm_export()
        else:
            self.add_error_as_exception(EnvironError("Failed to correctly configure ENIQ export jobs."))

    def set_teardown_objects(self):
        """
        Add callable objects to the teardown list
        """
        # Disable Historical CM Export
        turn_eniq_historical_export_off = 'false'
        self.teardown_list.append(partial(toggle_pib_historicalcmexport, turn_eniq_historical_export_off))

    def execute_setup_commands(self):
        """
        Executes the setup commands for both ENIQ stats and events

        """
        physical_ssh_cmd = 'ssh root@{0}'.format(get_ms_host())
        cloud = is_a_cloud_deployment()
        key_location = "/var/tmp/enm_keypair.pem"
        if cloud and not filesystem.does_file_exist(key_location):
            self.add_error_as_exception(EnvironError("Cannot find pem key!!"))
            log.logger.debug("Key file not found!!!")
        cloud_ssh_cmd = 'ssh -i {1} cloud-user@{0}'.format(get_emp(), key_location)
        integration_script = self.ENIQ_INT_SCRIPT_FOR_CLOUD if cloud else self.ENIQ_INT_SCRIPT
        initial_expect = "root@" if not cloud else "cloud-user@"
        with pexpect.spawn(physical_ssh_cmd) if not cloud else pexpect.spawn(cloud_ssh_cmd) as child:
            log.logger.debug("Enabling Historical CM Export.")
            child.expect([initial_expect, pexpect.EOF])
            child.sendline(self.ENIQ_HISTORICAL_SETUP_CMD.format(integration_script=integration_script))
            child.expect("Please Choose Daily or Weekly Export")
            child.sendline("1")
            child.expect(["Please set the Hour for the Export (0 - 23)", pexpect.EOF, pexpect.TIMEOUT])
            child.sendline("0")
            child.expect(["Please set the Minute for the Export(0 - 59)", pexpect.EOF, pexpect.TIMEOUT])
            child.sendline("0")
            child.expect("Historical CM Export successfully enabled")
            log.logger.debug("Historical CM Export successfully enabled")
