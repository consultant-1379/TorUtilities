from enmutils.lib import shell, log, config
from enmutils_int.lib.enm_export import toggle_pib_historicalcmexport


ENIQ_INT_SCRIPT = '/usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_enm_integration.py'
ENIQ_INT_SCRIPT_FOR_CLOUD = 'sudo /usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_venm_integration.py'
SHOW_EXPORT_TIMES = '{integration_script} showExportTimes'
LITP_PLAN = ['/usr/bin/litp show_plan -a', 'Plan Status: Successful']


def get_workload_vm_ip():
    """ Deprecated in 21.02 and will be deleted in 21.13 RTD-14986 """


def confirm_eniq_topology_export_enabled(historical=False):
    """
    Confirm ENIQ Daily Topology Export is enabled, or Historical is enabled

    :return: Boolean indicating if the exports are currently enabled.
    :rtype: bool
    """
    log_msg = "historical cm export" if historical else "daily topology export"
    log.logger.debug("Checking if {0} is enabled.".format(log_msg))
    cmd = (SHOW_EXPORT_TIMES.format(integration_script=ENIQ_INT_SCRIPT_FOR_CLOUD) if config.is_a_cloud_deployment() else
           SHOW_EXPORT_TIMES.format(integration_script=ENIQ_INT_SCRIPT))
    response = shell.run_cmd_on_emp_or_ms(cmd=cmd, timeout=60 * 2, **{'get_pty': True})
    msg = ("ENIQ Historical CM Export is currently enabled" if historical
           else "ENIQ Daily Topology export is currently enabled")
    if response.rc == 0 and msg in response.stdout:
        log.logger.debug('ENIQ {0}, enabled on ENM.'.format(log_msg))
        return True
    log.logger.debug('ENIQ {0}, is not enabled on ENM.'.format(log_msg))
    return False


def toggle_pib_inventory_export():
    """ Deprecated in 21.02 and will be deleted in 21.13 RTD-14986 """


def toggle_pib_historical_cm_export():
    """
    Function to set the inventory export to enabled.
    """
    log.logger.debug("Setting historical CM export pib values.")
    turn_inventory_mo_export_on = 'true'
    toggle_pib_historicalcmexport(turn_inventory_mo_export_on)
    log.logger.debug("Historical export values set.")
