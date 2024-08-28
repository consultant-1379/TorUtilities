# ********************************************************************
# Name    : Command Execution
# Summary : Provides local and remote host command functionality,
#           using the Executor, Remote Executor, Local Executor,
#           Command and Response classes.
# ********************************************************************
import socket
import log
import config
import cache
import shell
import executor

NETSIM = "netsim"
PROXY_HOSTS = []


def is_host_pingable(host):
    """
    Function to try and the ping the supplied host

    :param host: Name or IP of the host to be pinged
    :type host: str

    :return: Boolean indicating if the host was pingable
    :rtype: bool
    """
    result = False
    cmd = "ping -c 1 -w 4 {0}".format(host)
    response = execute_cmd(cmd)
    if response.rc == 0:
        log.logger.debug("Verified that host {0} is pingable".format(host))
        result = True
    else:
        log.logger.debug("Verified that host {0} is not pingable".format(host))
    return result


def convert_command_if_required(command, pod_name=None, container_name=None, suppress_error=True, **kwargs):
    """
    Function to convert the supplied command str to convert to Command instance if required

    :param command: Command str to convert to Command instance if required
    :type command: str|shell.Command
    :param pod_name: Optional POD name if Cloud Native
    :type pod_name: str
    :param suppress_error: Suppresses error output, when true
    :type suppress_error: bool
    :param container_name: Optional Container name if Cloud Native
    :type container_name: str
    :param kwargs: Optional dictionary arguments
    :type kwargs: dict

    :return: The command str as an instance of Command or the original Command instance
    :rtype: shell.Command
    """
    if any([pod_name, container_name]):
        enm_namespace = cache.get_enm_cloud_native_namespace()
        command = shell.Command((
            "/usr/local/bin/kubectl --kubeconfig /root/.kube/config exec -n {enm_namespace} -c {pod_name} "
            "{container_name} -- bash -c '{command}' {suppress_error}".format(
                enm_namespace=enm_namespace,
                pod_name=pod_name,
                container_name=container_name,
                command=command,
                suppress_error='2>/dev/null' if suppress_error else '')), **kwargs)

    if not hasattr(command, 'cmd'):
        command_keyword_args = {'timeout': kwargs.pop('timeout', None), 'log_cmd': kwargs.pop('log_cmd', True),
                                'allow_retries': kwargs.pop('allow_retries', True),
                                'retry_limit': kwargs.pop('retry_limit', None), 'async': kwargs.pop('async', False),
                                'activate_virtualenv': kwargs.pop('activate_virtualenv', False),
                                'check_pass': kwargs.pop('check_pass', False), 'cwd': kwargs.pop('cwd', None)}
        command = shell.Command(command, **command_keyword_args)
    log.logger.debug("Command to be executed:: {0}".format(command.cmd))
    return command


def get_host_values(hostname=None, username=None):
    """
    Function to get the basic host values if no specific hostname was supplied, LMS or EMP

    :param hostname: Name of the hostname if supplied
    :type hostname: str
    :param username: Username to connect to the host if known
    :type username: str

    :return: Tuple containing the hostname and username to be used in the command
    :rtype: tuple
    """
    if not hostname:
        cloud_user = 'cloud-user'
        username = cloud_user if config.is_a_cloud_deployment() else 'root'
        hostname = cache.get_emp() if username == cloud_user else cache.get_ms_host()
    return hostname, username


def get_ssh_identity_file(**kwargs):
    """
    Function to select the ssh_identity_file for the respective deployment type

    :param kwargs: Optional dictionary arguments
    :type kwargs: dict

    :return: Path to the selected ssh_identity_file
    :rtype: str
    """
    log.logger.debug("Determing SSH Identity file.")
    ssh_identity_key = kwargs.get('ssh_identity_file')
    if not ssh_identity_key and not kwargs.get('password'):
        ssh_identity_key = (cache.CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM if config.is_a_cloud_deployment() else
                            shell.DEFAULT_VM_SSH_KEYPATH)
    return ssh_identity_key


def get_proxy_values():
    """
    Function to determine the host and user to create the proxy connection

    :return: Tuple containing the proxy host and user
    :rtype: tuple
    """
    log.logger.debug("Determining proxy values.")
    if config.is_a_cloud_deployment():
        hostname, user = cache.get_emp(), 'cloud-user'
    else:
        hostname, user = cache.get_ms_host(), 'root'
    return hostname, user


def get_connection_and_proxy(hostname, new_connection=False, keep_connection_open=False, **kwargs):
    """
    Function to retrieve or create the connection, proxy and an instance of ConnectionPoolManager

    :param hostname: Name of the hostname used in the connection
    :type hostname: str
    :param new_connection: Boolean indicating if a new connection should be made
    :type new_connection: bool
    :param keep_connection_open: Boolean indicating if the connection should remain open
    :type keep_connection_open: bool
    :param kwargs: Optional dictionary arguments
    :type kwargs: dict

    :raises RuntimeError: raised the connection fails to be opened

    :return: Tuple containing the created proxy (optional), paramiko.Client and ConnectionPoolManager
    :rtype: tuple
    """
    proxy = None
    ssh_identity_file = get_ssh_identity_file(**kwargs)
    kwargs.update({'ssh_identity_file': ssh_identity_file})
    use_proxy = kwargs.pop('use_proxy', False)
    if use_proxy or (not all([kwargs.get('user'), kwargs.get('password')]) and hostname not in PROXY_HOSTS):
        log.logger.debug("Creating proxy for command execution.")
        proxy_host, proxy_user = get_proxy_values()
        # If our proxy is equal to the LMS host, we should have password-less access
        ssh_identity_file = ssh_identity_file if proxy_host != cache.get_ms_host() else None
        proxy = shell.create_proxy(hostname, proxy_user, proxy_host, ssh_identity_file=ssh_identity_file)
    try:
        connection_manager = shell.get_connection_mgr()
        log.logger.debug("Getting connection for command execution.")
        connection = connection_manager.get_connection(
            hostname, new_connection=new_connection or not keep_connection_open, ms_proxy=proxy, **kwargs)
    except Exception as e:
        raise RuntimeError("Unable to setup connection to remote host - Error: {0}".format(str(e)))
    return proxy, connection, connection_manager


def close_connection_and_proxy(hostname, connection, connection_manager, keep_connection_open=False, proxy=None):
    """
    Function to return the open connection to the ConnectionPoolManager and close the proxy

    :param hostname: Name of the hostname used in the connection
    :type hostname: str
    :param connection: Connect to be returned to the ConnectionPoolManager
    :type connection: paramiko.Client
    :param connection_manager: Instance of the ConnectionPoolManager to manage the return of the connection to the Pool
    :type connection_manager: shell.ConnectionPoolManager
    :param keep_connection_open: Boolean indicating if the connection should remain open
    :type keep_connection_open: bool
    :param proxy: ProxyCommand instance to be closed after usage.
    :type proxy: paramiko.ProxyCommand
    """
    log.logger.debug("Returning connection and closing any open proxy.")
    if proxy:
        shell.close_proxy(proxy)
    connection_manager.return_connection(hostname, connection, keep_connection_open=keep_connection_open)


def execute_remote_cmd(command, hostname, **kwargs):
    """
    Function to manage the execution of a remote command

    :param command: Command to be executed
    :type command: str|shell.Command
    :param hostname: Name of the hostname where the command should be executed
    :type hostname: str
    :param kwargs: Optional dictionary arguments
    :type kwargs: dict

    :raises RuntimeError: raised if the remote command execution fails

    :return: Response instance from the executed command
    :rtype: shell.Response
    """
    keep_connection_open = kwargs.pop('keep_connection_open', False)
    new_connection = kwargs.pop('new_connection', False)
    get_pty = kwargs.pop('get_pty', False)
    add_linux_timeout = kwargs.pop("add_linux_timeout", False)
    timeout = kwargs.pop("timeout", None)
    if kwargs.get('password') and kwargs.get('password') == NETSIM:
        keep_connection_open = True
    proxy, connection, connection_manager = get_connection_and_proxy(
        hostname, new_connection=new_connection, keep_connection_open=keep_connection_open, **kwargs)
    try:
        kwargs.update({'get_pty': get_pty, 'add_linux_timeout': add_linux_timeout, 'timeout': timeout})
        return executor.RemoteExecutor(command, connection, **kwargs).execute()
    except Exception as e:
        raise RuntimeError("Exception occurred while executing command: {0}".format(str(e)))
    finally:
        close_connection_and_proxy(
            hostname, connection, connection_manager, keep_connection_open=keep_connection_open, proxy=proxy)


def execute_cmd(command, hostname=None, username=None, pod_name=None, container_name=None, **kwargs):
    """
    Function to manage the execution of a local or remote command

    :param command: Command to be executed
    :type command: str|shell.Command
    :param hostname: Name of the hostname where the command should be executed
    :type hostname: str
    :param username: Username who will execute the command
    :type username: str
    :param pod_name: Optional POD name if Cloud Native
    :type pod_name: str
    :param container_name: Optional Container name if Cloud Native
    :type container_name: str
    :param kwargs: Optional dictionary arguments
    :type kwargs: dict

    :return: Response instance from the executed command
    :rtype: shell.Response
    """
    remote_cmd = kwargs.pop('remote_cmd', False)
    ping_host = kwargs.pop('ping_host', False)
    suppress_error = kwargs.pop('suppress_error', True)
    command = convert_command_if_required(
        command, pod_name=pod_name, container_name=container_name, suppress_error=suppress_error, **kwargs)
    if determine_local_command(remote_cmd, hostname):
        log.logger.debug("Executing local command.")
        return executor.LocalExecutor(command).execute()
    else:
        global PROXY_HOSTS
        if not PROXY_HOSTS:
            PROXY_HOSTS.append(cache.get_emp())
            PROXY_HOSTS.append(cache.get_ms_host())
        hostname, username = get_host_values(hostname=hostname, username=username)
        if (hostname in PROXY_HOSTS or ping_host) and not is_host_pingable(hostname):
            return shell.Response(
                rc=5, stdout="Error: Unable to reach host, please ensure the host: {0} is available.".format(hostname))
        kwargs.update({'user': username})
        log.logger.debug("Executing remote command.")
        return execute_remote_cmd(command, hostname, **kwargs)


def determine_local_command(remote_cmd, hostname):
    """
    Wrapper function for the multiple boolean checks

    :param remote_cmd:
    :type remote_cmd: str
    :param hostname:
    :type hostname: str

    :return: Boolean indicating if a local command should be executed
    :rtype: bool
    """
    return (not remote_cmd and not hostname or hostname == 'localhost' or
            (socket.gethostname() == "cloud-ms-1" and not hostname) or
            (not hostname and cache.get_ms_host() == 'localhost'))
