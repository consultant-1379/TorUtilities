# ***************************************************************************
# Name    : Winfiol Operations
# Summary : Allows the user to login to winfiol to create user home directory,
#           download tls certificates, creates pki entities, revoke entities.
# **************************************************************************

import time
from retrying import retry
from enmutils.lib import log, mutexer, shell, arguments
from enmutils.lib.exceptions import EnmApplicationError, EnvironError, ScriptEngineResponseValidationError
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.services import deploymentinfomanager_adaptor


WINFIOL_CMD = '/usr/local/bin/wfcli -v'
WINFIOL_TIMEOUT_SECS = 3600
CMD_LIST_TMP_DIR = 'ls /tmp'
CMD_PKI_SETUP_COMMAND = "/opt/ericsson/security/eeforamos/setupEEForAMOSUsers.py --amosuserlist {0}"


def login_to_general_scripting_to_download_certificates(username, password, scripting_ip):
    """
    Login to winfiol server using profile user to download necessary certificates
    :param username: User name to login to winfiol service
    :type username: str
    :param password: password for a given ENM user
    :type password: str
    :param scripting_ip: IP address for the provided service name
    :type scripting_ip: str
    :raises EnvironError: when WINFIOL_CMD fails
    :return: True if winfiol operation is successful else False
    :rtype: bool
    """
    result = True
    log.logger.debug("Starting execution of wfcli script for user: {0}".format(username))
    msg_log = "Winfiol operation is {0} for {1} on {2}!"
    try:
        response = shell.run_remote_cmd(shell.Command(WINFIOL_CMD), scripting_ip, username, password, ping_host=True)
        if response.rc == 5 and "Error: Unable to reach host" in response.stdout:
            raise EnvironError(response.stdout)
    except EnvironError:
        raise
    except Exception as e:
        log.logger.debug("Exception({0}) occured while executing wifiol command.. Trying to verify if certs have been downloaded!".format(e))
        cert_folder = "/home/shared/{0}/Ericsson/OMSec/".format(username)
        cmd = shell.Command("ls {0}".format(cert_folder))
        try:
            verify_response = shell.run_remote_cmd(cmd, scripting_ip, username, password)
            cert_msg = "Certificate folder({0}) has {1} found for the user {2}!"
            if verify_response.rc == 0:
                log.logger.debug(cert_msg.format(cert_folder, "been", username))
            else:
                log.logger.debug(cert_msg.format(cert_folder, "not been", username))
                result = False
        except Exception as e:
            log.logger.debug("Exception occured while verifying if certificate folder was created - {0}".format(e))
            result = False
    if result:
        log.logger.debug(msg_log.format("successful", username, scripting_ip))
    else:
        log.logger.debug(msg_log.format("failed", username, scripting_ip))
    return result


def perform_winfiol_operations(user_list, scripting_cluster_ips):
    """
    Perform winfiol operations for
    SHM_06, SHM_36, SHM_39, AMOS_01, AMOS,_02, AMOS_03, AMOS_04, AMOS_05, AMOS_08, OPS_01 profiles
    :param user_list: list of User Object(s)
    :type user_list: list
    :param scripting_cluster_ips: scripting VM ip addresses
    :type scripting_cluster_ips: list
    :raises EnmApplicationError: when CMD_PKI_SETUP_COMMAND fails to run
    """
    successful_users = set()
    log.logger.debug("Starting to execute WINFIOL operations..")
    for scripting_ip in scripting_cluster_ips:
        failed_user_count = 0
        for each_user in user_list:
            if each_user.username not in successful_users and execute_script_with_user(each_user, scripting_ip):
                successful_users.add(each_user.username)
                # Reset failed count on success
                failed_user_count = 0
            else:
                failed_user_count += 1
            # Break if winfiol operations failed consecutively for 10 users on one vm
            if failed_user_count > 10:
                log.logger.debug("Winfiol operations continuously failed for 10 users on {} scripting vm! Skipping further operations on this vm!".format(scripting_ip))
                break
        if len(successful_users) == len(user_list):
            break
    if not len(successful_users) == len(user_list):
        failed_users = [user.username for user in user_list if user.username not in successful_users]
        raise EnmApplicationError("Winfiol operations have failed for users : {0}".format(failed_users))
    log.logger.debug("Successfully completed executing WINFIOL operations..")


def execute_script_with_user(user_info, scripting_ip):
    """
    Executes the download certificates flow for the given user on given scripting vm
    :param user_info: User Object
    :type user_info: enm_user.User
    :param scripting_ip: scripting VM ip addresses
    :type scripting_ip: str
    :return: True, if execution is successful
    :rtype: bool
    """
    try:
        log.logger.debug("login user name is {0} and scripting IP: {1}".format(user_info.username, scripting_ip))
        return login_to_general_scripting_to_download_certificates(user_info.username, user_info.password, scripting_ip)
    except Exception as e:
        log.logger.debug("Failed to run the script {0} on {1}, error encountered: {2}".format(
            WINFIOL_CMD, scripting_ip, str(e)))


def run_setupeeforamosusers_scripting_cluster(users, scripting_cluster_ips):
    """
    Login to scripting cluster to run setupEEForAMOSUsers to get the PKI entity added to profile user
    :param users: users created by the profile
    :type users: list
    :param scripting_cluster_ips: general scripting ip addresses
    :type scripting_cluster_ips: list
    :raises EnmApplicationError: when CMD_PKI_SETUP_COMMAND fails
    :raises EnvironError: when there are no scripting cluster ips
    """
    try:
        admin_user = get_workload_admin_user()
        ip_user_data_dict = divide_users_per_scripting_vm(scripting_cluster_ips, users)
        for cluster_ip, users_batch in ip_user_data_dict.iteritems():
            if users_batch:
                log.logger.debug("SCP IP : {0}, Batch of users : {1}".format(cluster_ip, users_batch))
                user_data = ','.join([str(each_user.username) for each_user in users_batch])
                command_response = shell.run_remote_cmd(shell.Command(CMD_PKI_SETUP_COMMAND.format(user_data),
                                                                      timeout=WINFIOL_TIMEOUT_SECS),
                                                        host=cluster_ip, user=admin_user.username,
                                                        password=admin_user.password)
                if command_response.rc == 0:
                    log.logger.debug("Successfully completed setupEEForAMOSUsers script execution")
                else:
                    log.logger.warning("Unable to run the script {0} in scripting cluster {1}, \n "
                                       "Response : {2}".format(CMD_PKI_SETUP_COMMAND.format(user_data), cluster_ip,
                                                               command_response.stdout))
    except Exception as e:
        raise EnmApplicationError(str(e))


def divide_users_per_scripting_vm(scripting_cluster_ips, users):
    """
    divides the users equally among the scripting VMs for load balancing\
    :param scripting_cluster_ips: scripting VM ip addresses
    :type scripting_cluster_ips: list
    :param users: number of users created by the profile
    :type users: list
    :return: users to be used per scripting vm
    :rtype: dict
    """
    ip_user_data_dict = {}
    ips_users_list = []
    num_of_users = len(users)
    num_of_scp_vms = len(scripting_cluster_ips)
    if num_of_users > num_of_scp_vms:
        num_of_users_per_scripting_vm = int(num_of_users / num_of_scp_vms)
        batch_of_users = arguments.split_list_into_chunks(users, num_of_users_per_scripting_vm)
        log.logger.debug("Number of batches of users : {0}, number of scripting VM's : {1}".format(len(batch_of_users),
                                                                                                   num_of_scp_vms))
        if len(batch_of_users) > num_of_scp_vms:
            delta = len(batch_of_users) - num_of_scp_vms
            scripting_cluster_ips.extend(scripting_cluster_ips[:delta])
        ips_users_list = zip(batch_of_users, scripting_cluster_ips)
    else:
        user_list = [[user] for user in users]
        ips_users_list = zip(user_list, scripting_cluster_ips)
    log.logger.debug("IP and users list : {0}".format(ips_users_list))
    for users_batch, cluster_ip in ips_users_list:
        if cluster_ip not in ip_user_data_dict:
            ip_user_data_dict[cluster_ip] = users_batch
        else:
            ip_user_data_dict[cluster_ip].extend(users_batch)
    log.logger.debug("Scripting IP's and the corresponding users : {0}".format(ip_user_data_dict))
    return ip_user_data_dict


@retry(retry_on_exception=lambda e: isinstance(e, EnvironError), wait_fixed=30000, stop_max_attempt_number=2)
def create_pki_entity_and_download_tls_certs(users):
    """
    Executes for SHM_06, SHM_36, SHM_39, AMOS_01, AMOS_02, AMOS_03, AMOS_04, AMOS_05, AMOS_08, OPS_01, ASU_01
    :param users: List of User Objects
    :type users: list
    :raises EnvironError: when winfiol/pki commands failed to run
    """
    log.logger.debug("Starting creation of PKI entities and download of TLS certs")
    scripting_cluster_ips = deploymentinfomanager_adaptor.get_list_of_scripting_service_ips()
    if not scripting_cluster_ips:
        raise EnvironError("Failed to get list of scripting cluster ips")
    try:
        log.logger.debug('Number of users for which PKI entities are to be created : {0}'.format(len(users)))
        with mutexer.mutex("create_pki_and_download_tls_cert", persisted=True, timeout=WINFIOL_TIMEOUT_SECS,
                           log_output=True):
            log.logger.debug("Sleeping for 2 mins before executing the script")
            time.sleep(120)
            run_setupeeforamosusers_scripting_cluster(users, scripting_cluster_ips)
        perform_winfiol_operations(users, scripting_cluster_ips)
    except Exception as e:
        raise EnvironError("Issue while executing the winfiol/pki commands with error {0}".format(str(e)))


def perform_revoke_activity(users):
    """
    Perform revoke activity
    :param users: list of User Object
    :type users: list
    """
    for user in users:
        revoke_entity_cmd = 'pkiadm revmgmt EE --revoke --entityname "{entity_name}"'
        admin_user = get_workload_admin_user()
        revoke_response = admin_user.enm_execute(revoke_entity_cmd.format(entity_name=user.username))
        for rvk_response in revoke_response.get_output():
            check_revoke_delete_entity_status(user=user, admin_user=admin_user, revoke_response=rvk_response)


def check_revoke_delete_entity_status(user, admin_user, revoke_response):
    """
    Check entity status for revoke and delete cases
    :param user: User Object
    :type user: object
    :param admin_user: Workload admin user
    :type admin_user: `enm_user_2.User` instance
    :param revoke_response: command output from Response object
    :type revoke_response: str
    :raises ScriptEngineResponseValidationError: when entity fail to revoke or delete
    """""
    delete_entity_cmd = 'pkiadm entitymgmt --delete --entitytype ee --name "{entity_name}"'
    if 'revoked successfully' in revoke_response:
        delete_response = admin_user.enm_execute(delete_entity_cmd.format(entity_name=user.username))
        if any(["successfully deleted" in line for line in delete_response.get_output()]):
            log.logger.debug("{0} entity deleted successfully".format(user.username))
        else:
            raise ScriptEngineResponseValidationError('Unable to delete the entity for user {0}. Response was {1}'
                                                      .format(user.username, delete_response), response=delete_response)
    else:
        raise ScriptEngineResponseValidationError('Unable to revoke the entity for user {0}. Response was {1}'
                                                  .format(user.username, revoke_response), response=revoke_response)
