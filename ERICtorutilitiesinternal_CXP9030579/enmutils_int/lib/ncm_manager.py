# ********************************************************************
# Name    : Network Connectivity Manager
# Summary : It allows the user to perform re-alignment of nodes and
#           links using rest end points.
# ********************************************************************
import pexpect
from retrying import retry
from requests.exceptions import HTTPError
from enmutils.lib.cache import (is_emp, is_enm_on_cloud_native, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP)
from enmutils.lib.enm_user_2 import build_user_message
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils.lib import log, shell
from enmutils_int.lib.enm_deployment import get_values_from_global_properties
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

ERROR_DATA = ["NCM Agent is not avaialble", "NCM Agent is not connected", "Invalid inputs",
              "Unable to order the realignment for some of the nodes"]
APP_ADMIN = 'sudo su ncmuser -c "/opt/ericsson/ncm/app/app-admin.ksh {0}"'
DISABLE_HEALTH_CHECK = 'sudo mv /usr/lib/ocf/resource.d/ncm_jboss_healthcheck.sh /var/tmp'
NCM_STOP = APP_ADMIN.format('stopall')
NCM_DB_RESTORE = APP_ADMIN.format('dbrestore')
NCM_DB_UPGRADE = APP_ADMIN.format('dbupgrade')
NCM_START = APP_ADMIN.format('start')
NCM_CHECK_STATUS = APP_ADMIN.format('monitor')
ENABLE_HEALTH_CHECK = 'sudo mv /var/tmp/ncm_jboss_healthcheck.sh /usr/lib/ocf/resource.d/'
GRANT_ACCESS_HEALTH_CHECK = 'sudo chmod 755 /usr/lib/ocf/resource.d/ncm_jboss_healthcheck.sh'


def ncm_rest_query(user, rest_url, data=None):
    """
    Performs NCM rest query request for provided data
    :type user: `enm_user_2.User`
    :param user: User who will create the job
    :type rest_url: str
    :param rest_url: name of rest end point
    :type data: str
    :param data: nodes json string
    :raises HTTPError: when job response is not ok
    """
    log.logger.debug("Attempting to send post request to: {0}".format(rest_url))
    log.logger.debug("Rest_body for the post request is: {0}".format(data))
    response = user.post(rest_url, data=data, headers=JSON_SECURITY_REQUEST, timeout=300)
    log.logger.debug("Response status code {0}, and body is {1}".format(response.status_code, response.text))
    if response.status_code == 200 and (not response.text or response.text == "{}"):
        log.logger.debug("Successfully completed realignment")
    elif response.status_code == 200 and response.text and response.json().get('errorMessage') in ERROR_DATA:
        message_prefix = response.json().get('errorMessage')
        failed_info = response.json().get('failedNodes')
        log.logger.debug("{0},{1}".format(message_prefix, failed_info))
    elif 400 <= response.status_code < 600 and response.text and response.json().get('errorMessage') in ERROR_DATA:
        message_prefix = response.json().get('errorMessage')
        message = build_user_message(response)
        raise HTTPError(message_prefix + message, response=response)


def check_db_backup_file_available(restore_file_name, vm_ncm):
    """
    Checks the db backup file is available on the ncm vm
    :type restore_file_name: str
    :param restore_file_name: backup file name used for restore activity
    :type vm_ncm: str
    :param vm_ncm: ip of vm ncm
    :raises EnvironError: when invalid file name provided or unsupported deployment or commands execution fail

    """
    try:
        log.logger.debug("Checking if db backup file is available on the vm!")
        cmd = "ls {0}".format(restore_file_name)
        ncm_run_cmd_on_vm(cmd, vm_ncm)
    except EnmApplicationError as e:
        log.logger.error("Error occured while checking for backup file - {0}".format(e))
        raise EnvironError("Exception occured while checking for backup file. "
                           "Please follow the mentioned confluence page to complete the pre-requisites.\n"
                           "NCM_MEF_LCM_01 - https://eteamspace.internal.ericsson.com/pages/viewpage.action?pageId=2057399300 \n"
                           "NCM_L3_VPN_01 - https://eteamspace.internal.ericsson.com/pages/viewpage.action?pageId=2057399300 \n"
                           "                https://eteamspace.internal.ericsson.com/display/BTT/How+to+create+L3+VPN+Service+on+NCM")


def lcm_db_restore(restore_file_name):
    """
    Perform db restore activity for ncm lcm
    :type restore_file_name: str
    :param restore_file_name: backup file name used for restore activity
    :raises EnvironError: when invalid file name provided or unsupported deployment or commands execution fail
    """
    vm_ncm = fetch_ncm_vm()
    check_db_backup_file_available(restore_file_name, vm_ncm)
    try:
        log.logger.debug("Starting NCM LCM restore activity")
        ncm_run_cmd_on_vm(DISABLE_HEALTH_CHECK, vm_ncm)
        ncm_run_cmd_on_vm(NCM_STOP, vm_ncm)
        log.logger.debug("Performing restore activity using file: {0}".format(restore_file_name))
        perform_db_restore(vm_ncm, restore_file_name)
    except Exception as e:
        log.logger.debug("Encountered Exception : {0}".format(e))
    finally:
        try:
            ncm_run_cmd_on_vm(NCM_START, vm_ncm)
            ncm_run_cmd_on_vm(NCM_CHECK_STATUS, vm_ncm)
        finally:
            ncm_run_cmd_on_vm(ENABLE_HEALTH_CHECK, vm_ncm)
            ncm_run_cmd_on_vm(GRANT_ACCESS_HEALTH_CHECK, vm_ncm)
            log.logger.debug("Completed NCM LCM restore activity")


def fetch_ncm_vm():
    """
    List NCM vm from global properties config file
    :return: ncm vm ip
    :rtype: str
    :raises EnvironError: when deployment is cloud native
    """
    log.logger.debug("Fetching NCM vm")
    if is_enm_on_cloud_native():
        raise EnvironError("Unable to fetch NCM vm for Cloud Native Deployment")
    else:
        vm_ncm = get_values_from_global_properties("ncm=")[0]
        log.logger.debug("NCM vm is: {0}".format(vm_ncm))
        return vm_ncm


@retry(retry_on_exception=lambda e: isinstance(e, EnvironError), wait_fixed=300000, stop_max_attempt_number=3)
def switch_to_application_vm(child, ncm_vm):
    """
    Switches the user from cloud-user to root on cloud or physical
    :param child: child of ssh terminal spawned
    :type child: pexpect.spawn
    :param ncm_vm: ncm vm ip
    :type ncm_vm: str
    :return: child with ssh terminal which has the user switched to root
    :rtype: pexpect.spawn
    :raises EnvironError: if ssh connection fails towards the fmx vm
    """
    if is_emp():
        try:
            log.logger.debug("Connecting to NCM VM {0} from EMP".format(ncm_vm))
            child.sendline("ssh -o StrictHostKeyChecking=no -i {2} {0}@{1}".format("cloud-user", ncm_vm,
                                                                                   CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP))
            child.expect("cloud-user@")
            log.logger.debug("Connected to NCM VM on cloud deployment")
        except Exception as e:
            raise EnvironError('Unable to connect to NCM vm {0} from EMP. Exception: {1}'.format(ncm_vm, e))
    else:
        try:
            log.logger.debug("Connecting to NCM VM {0} from LMS".format(ncm_vm))
            child.sendline("ssh -t -o StrictHostKeyChecking=no -i /root/.ssh/vm_private_key {0}@{1}".format("cloud-user",
                                                                                                            ncm_vm))
            child.expect(["cloud-user@", pexpect.EOF], timeout=300, searchwindowsize=-1)
            log.logger.debug("Connected to NCM VM on physical deployment")
        except Exception as e:
            raise EnvironError('Unable to connect to NCM vm {0} from LMS. Exception: {1}'.format(ncm_vm, e))
    return child


def perform_db_restore(vm_ncm, restore_file_name):
    """
    Perform db restore and upgrade activity
    :param vm_ncm: ncm vm ip
    :type vm_ncm: str
    :param restore_file_name: backup file name used to perform restore
    :type restore_file_name: str
    :raises EnvironError: when invalid file name provided or unsupported deployment or commands execution fail
    """
    child = GenericFlow.switch_to_ms_or_emp()
    child = switch_to_application_vm(child, vm_ncm)
    log.logger.debug("Executing DB-RESTORE command {0} on {1}".format(NCM_DB_RESTORE, vm_ncm))
    child.sendline(NCM_DB_RESTORE)
    child.expect("Please specify the fully qualified archive file name: ")
    child.sendline(restore_file_name)
    log.logger.debug("Passed the filename {0} as input to the script".format(restore_file_name))
    result = child.expect(["Error: database backup archive file", "Error: NCM database is still running", ":",
                           pexpect.EOF, pexpect.TIMEOUT])
    if result == 0:
        log.logger.debug("Error: Invalid NCM backup file format provided or file does not exist in specified location")
        log.logger.debug("Output : {0}".format(child.before))
        child.sendline("exit")
        child.close()
        raise EnvironError("Invalid NCM backup file format provided or file does not exist in specified location")
    elif result == 1:
        log.logger.debug("NCM database is still running...")
        log.logger.debug("Output : {0}".format(child.before))
        child.sendline("exit")
        child.close()
        raise EnvironError("NCM database is still running. Please stop NCM database manually and restart the profile.")
    elif result == 2:
        log.logger.debug("Overwrite existing NCM database")
        child.sendline("y")
        child.expect("cloud-user@", timeout=300)
        log.logger.debug("Successfully completed ncm db restore")
        log.logger.debug("Output : {0}".format(child.before))
        log.logger.debug("Executing DB-UPGRADE command {0} on {1}".format(NCM_DB_UPGRADE, vm_ncm))
        child.sendline(NCM_DB_UPGRADE)
        child.expect("cloud-user@", timeout=300)
        log.logger.debug("Output : {0}".format(child.before))
        child.sendline("exit")
        child.close()
    else:
        log.logger.debug("Encountered Timeout or EOF : {0}".format(child.before))


def ncm_run_cmd_on_vm(cmd, vm):
    """
    Executes provided NCM command on provided NCM vm
    :param cmd: ncm command to be executed on vm
    :type cmd: str
    :param vm: IP address or hostname of the vm on which the command is to be executed
    :type vm: str
    :raises EnmApplicationError: when failed to execute NCM command
    """
    command_response = shell.run_cmd_on_vm(shell.Command(cmd, timeout=60 * 10), vm_host=vm)
    if command_response.rc == 0:
        log.logger.debug("Executed NCM command: {0} successfully".format(cmd))
    else:
        raise EnmApplicationError("Unable to execute NCM command {0}, response code is: {1}"
                                  .format(cmd, command_response.rc))
