# ********************************************************************
# Name    : Cache
# Summary : Managed interaction with global cache, along with a number
#           of helper functions to retrieve system information.
# ********************************************************************

from pkgutil import get_loader
import os
import random
import socket
import threading
import time

import config
import filesystem
import log
import mutexer

import shell
from enmutils.lib.exceptions import EnvironError

access_mutex = threading.Lock()

__global_cache_dict = {}
CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM = '/var/tmp/enm_keypair.pem'
CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP = '/ericsson/enm/dumps/.cloud_user_keypair.pem'
INTERNAL_ID = 'enmutils_int'
LITP_EXECUTABLE = '/usr/bin/litp'


def has_key(key):
    """
    B{Checks if the cache has the specified key}.

    :param key: cache key
    :type key: string
    :return: bool
    :rtype: bool
    """

    return bool(__global_cache_dict.has_key(key))


def get(key):
    """
    B{Returns the primitive or object associated with the specified key}

    :param key: cache key
    :type key: str
    :return: __global_cache_dict[key]
    :rtype: primitive || object
    """

    if not __global_cache_dict.has_key(key):
        return None

    return __global_cache_dict[key]


def set(key, value):  # pylint: disable=redefined-builtin
    """
    B{Sets the specified primitive or object in the cache with the specified key}

    :param key: cache
    :type key: str
    :param value: data to be stored in cache
    :type value: primitive || object
    """

    global __global_cache_dict
    access_mutex.acquire()
    __global_cache_dict[key] = value
    access_mutex.release()


def remove(key):
    """
    B{Removes the key-value pair from the cache for the specified key}

    :param key: cache key
    :type key: str
    """

    if has_key(key):
        access_mutex.acquire()
        del __global_cache_dict[key]
        access_mutex.release()


def clear():
    """
    B{Resets the cache by removing all existing key-value pairs}
    """

    global __global_cache_dict
    access_mutex.acquire()
    __global_cache_dict = {}
    access_mutex.release()


def copy_cloud_user_ssh_private_key_to_enm():
    """
    Check to see if the cloud-user ssh private key needs to be copied to ENM.
    Attempt to copy key file if hasnt been attempted by current process before, or was done more than 1 day ago
    """

    key = "cloud-user-ssh-private-key-copied"
    with mutexer.mutex("{0}-check".format(key)):
        time_now_secs = time.time()
        if not has_key(key) or (time_now_secs - int(get(key)) > 24 * 60 * 60):
            copy_cloud_user_ssh_private_key_file_to_emp()
            set(key, time_now_secs)


def copy_cloud_user_ssh_private_key_file_to_emp():
    """
    Checks cloud-user private key file exists on EMP,if not copies the key from Workload VM to EMP
    During ENM upgrade, /var/tmp/enm_keypair.pem on EMP gets removed.
    Profiles using enm_keypair.pem on EMP to connect to other servers must call this function
    before using the enm_keypair.pem, to ensure that enm_keypair.pem exists on EMP
    :return: True if enm_keypair exists on EMP or enm_keypair is successfully copied to EMP
    :rtype: bool
    :raises EnvironError: when response returns return code
    """
    log.logger.debug("Copying cloud-user ssh private key to EMP, if needed")
    temporary_storage_location = "/tmp/enm_keypair.pem"
    enm_user = "cloud-user"
    emp_host = get_emp()
    cmd = shell.Command("ls -la {0}".format(CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP))
    response = shell.run_remote_cmd(cmd, emp_host, enm_user)
    if response.rc:
        cmd = "scp  -i {0} -o stricthostkeychecking=no {0} {1}@{2}:{3}".format(CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM,
                                                                               enm_user,
                                                                               emp_host,
                                                                               temporary_storage_location)
        response = shell.run_local_cmd(cmd)
        if response.rc:
            raise EnvironError(
                "Failed to copy {0} from Workload VM to {1} on {2}".format(CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM,
                                                                           temporary_storage_location,
                                                                           emp_host))
        else:
            log.logger.debug("Successfully copied {0} from Workload VM to {1} on {2}"
                             .format(CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, temporary_storage_location, emp_host))

        cmd = shell.Command("sudo mv {0} {1}".format(temporary_storage_location,
                                                     CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP))
        response = shell.run_remote_cmd(cmd, emp_host, enm_user, get_pty=True)
        if response.rc:
            raise EnvironError("Failed to move {0} to {1} on {2}".format(temporary_storage_location,
                                                                         CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP,
                                                                         emp_host))
        else:
            log.logger.debug("Successfully moved  {0} to {1} on {2}"
                             .format(temporary_storage_location, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP, emp_host))
    else:
        log.logger.debug("File {0} exists on {1} - Copying from Workload VM to {1} is not required"
                         .format(CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP, emp_host))
    return True


def get_apache_url():
    """
    Builds the base FQDN Apache URL

    :return: hostname
    :rtype: str
    """

    return 'https://' + get_haproxy_host()


def get_apache_ip_url():
    """
    Builds the base FQDN Apache IP address

    :return: IP Address
    :rtype: str
    """

    with mutexer.mutex("acquire-httpd-ip"):
        if not has_key('httpd-ip_url'):
            hostname = get_haproxy_host()
            port = 443
            addrs = socket.getaddrinfo(hostname, port)
            ips = []

            ipv4_addrs = [addr[4][0] for addr in addrs if addr[0] == socket.AF_INET]
            if ipv4_addrs:
                ips.append("https://{0}:{1}".format(random.choice(ipv4_addrs), port))

            ipv6_addrs = [addr[4][0] for addr in addrs if addr[0] == socket.AF_INET6]
            if ipv6_addrs:
                ips.append("https://[{0}]:{1}".format(random.choice(ipv6_addrs), port))

            ip = random.choice(ips)
            set("httpd-ip_url", ip)

    return get("httpd-ip_url")


def get_haproxy_host():
    """
    Builds the base FQDN Apache URL

    :return: hostname for haproxy
    :rtype: str
    :raises RuntimeError: if there is no hostname for Apache
    """

    enm_url_key = "ENM_URL"

    if not has_key("httpd-hostname"):
        with mutexer.mutex("acquire-httpd-fqdn"):
            if enm_url_key in os.environ:
                set("httpd-hostname", "{}".format(os.environ[enm_url_key]))
            else:
                # Check if we are on the cloud
                if is_emp():
                    cmd = "sudo consul kv get enm/deprecated/global_properties/UI_PRES_SERVER"
                else:
                    cmd = "getent hosts haproxy | awk '{ print $3 }'"

                response = shell.run_cmd_on_ms(cmd)
                if response.rc == 0 and response.stdout:
                    set("httpd-hostname", "{}".format(response.stdout.strip()))

    haproxy_host = get("httpd-hostname")

    if haproxy_host is None:
        raise RuntimeError("Could not get hostname for Apache")

    return haproxy_host


def get_ms_host():
    ms_host_key = 'LMS_HOST'
    host = None
    if config.has_prop(ms_host_key):
        host = config.get_prop(ms_host_key)
    elif ms_host_key in os.environ:
        host = os.environ[ms_host_key]
    return host or 'localhost'


def is_host_ms():
    return get_ms_host() == 'localhost'


def is_host_physical_deployment():
    return True if get_ms_host() != 'localhost' else False


def get_vnf_laf():
    """
    Perform a check for the vnflaf key in config dict or environment

    :rtype: str
    :return: Returns either the vnflaf ip as a string or None
    """
    vnf_host_key = 'VNF_LAF'
    host = None
    if config.has_prop(vnf_host_key):
        host = config.get_prop(vnf_host_key)
    elif vnf_host_key in os.environ:
        host = os.environ[vnf_host_key]
    return host or None


def get_emp():
    """
    Perform a check for the emp key in config dict or environment

    :rtype: str
    :return: Returns either the emp ip as a string or None
    """
    emp_host_key = 'EMP'
    host = None
    # Todo: add EMP to config file
    if config.has_prop(emp_host_key):
        host = config.get_prop(emp_host_key)
    elif emp_host_key in os.environ:
        host = os.environ[emp_host_key]
    return host or None


def is_emp():
    """
    Indicate whether or not we have retrieved the key for the emp

    :rtype: bool
    :return: Returns either the emp ip as a string or None
    """
    return bool(get_emp() or is_vnf_laf())


def is_vnf_laf():
    """
    Indicate whether or not we have retrieved the key for the vnflaf

    :rtype: bool
    :return: Returns either the vnflaf ip as a string or None
    """
    return bool(get_vnf_laf() or None)


def is_enm_on_cloud():
    """
    B{Determines whether the enm environment is on the cloud or not
    :rtype: bool
    :return: True if enm is on cloud
    """
    response = shell.run_cmd_on_ms("sudo consul kv get enm/deprecated/global_properties/DDC_ON_CLOUD")
    return bool(response.ok and response.stdout.strip() == "TRUE")


def is_enm_on_cloud_native():
    """
    Checks if the ENM deployment is a Cloud Native deployment

    :return: Boolean to indicate if ENM is on Cloud Native or not
    :rtype: bool

    """
    log.logger.debug("Checking if ENM deployment is Cloud Native")
    return True if get_enm_cloud_native_namespace() else False


def get_enm_cloud_native_namespace():
    """
    Get Cloud Native Namespace (from Kubernetes cluster) corresponding to ENM_URL

    :return: ENM Namespace
    :rtype: str
    """

    log.logger.debug("Fetching ENM namespace key value, if set")
    enm_namespace_key = "enm_cloud_native_namespace"
    enm_namespace = ""

    if not has_key(enm_namespace_key):
        enm_url = get_haproxy_host()
        cmd = ("/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ingress "
               "--all-namespaces 2>/dev/null | egrep ui")
        log.logger.debug("Checking Kubernetes client")
        response = shell.run_local_cmd(shell.Command(cmd))
        if not response.rc and response.stdout and enm_url in response.stdout:
            enm_namespace = response.stdout.split()[0]

        if enm_namespace:
            log.logger.debug("ENM Namespace detected that matches ENM_URL - setting key")
            set(enm_namespace_key, enm_namespace)
        else:
            log.logger.debug("ENM Namespace not found matching ENM_URL value ({0}) and therefore profile now assumes "
                             "that deployment is not Cloud Native".format(enm_url))

    else:
        enm_namespace = get(enm_namespace_key)

    log.logger.debug("ENM Namespace: '{0}'".format(enm_namespace))
    return enm_namespace


def check_if_on_workload_vm():
    """
    Indicate whether the workload vm is being used.
    Creates a key with a boolean value based on the following:
    Checks if the internal package is installed.
    Checks that the LITP_EXECUTABLE file does not exist. If the file exists this indicates the user is on the LMS.

    :rtype: bool
    :return: Boolean of whether the internal package is installed and the LITP_EXECUTABLE file does not exist.
    """
    enm_internal_wlvm_key = "check_is_on_workload_vm"
    if not has_key(enm_internal_wlvm_key):
        log.logger.debug("{0} key is currently not set".format(enm_internal_wlvm_key))
        if get_loader(INTERNAL_ID) and not filesystem.does_file_exist(LITP_EXECUTABLE):
            log.logger.debug("Internal package is installed and is not on the LMS - Setting key to true")
            set(enm_internal_wlvm_key, True)
        else:
            log.logger.debug("Internal package is not installed or is on the LMS - Setting key to false")
            set(enm_internal_wlvm_key, False)
    enm_internal_wlvm_key_value = get(enm_internal_wlvm_key)
    return enm_internal_wlvm_key_value


def _get_credentials(username_key, password_key):
    """
    Gets credentials from credentials file

    :raises ValueError: - If credentials can't be defined
    :returns: vm user credentials
    :rtype: tuple

    """
    if has_key(username_key) and has_key(password_key):
        return get(username_key), get(password_key)

    credentials = config.load_credentials_from_props(username_key, password_key)

    # Check that we have VM credentials in props
    if not credentials:
        raise ValueError("Property '{0}' and/or '{1}' is undefined".format(username_key, password_key))

    if len(credentials) > 1:
        set(password_key, credentials[1])
    set(username_key, credentials[0])

    return credentials


def get_litp_admin_credentials():
    """
    Gets LITP admin credentials

    :returns: LITP admin user credentials
    :rtype: tuple

    """
    return _get_credentials('litp_username', 'root_password')


def get_workload_vm_credentials():
    """
    Gets Workload VM credentials, as the LMS details may be modified

    :returns: Workload VM user credentials
    :rtype: tuple

    """
    return _get_credentials('workload_vm_username', 'root_password')
