import os

import paramiko

from enmutils.lib import cache, log, shell
from enmutils.lib.shell import create_proxy, close_proxy


def get_proxy_details():
    """
    Selects the appropriate proxy information depending upon the underlying deployment type

    :return: Tuple containing the proxy host, host user and ssh identity key to be used
    :rtype: tuple
    """
    if cache.is_emp():
        emp = cache.get_emp()
        log.logger.debug("Returning proxy information for EMP: [{0}].".format(emp))
        proxy_host = emp
        user = "cloud-user"
        ssh_identity_file = cache.CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM
    else:
        ms_host = cache.get_ms_host()
        log.logger.debug("Returning proxy information for LMS Host: [{0}].".format(ms_host))
        proxy_host = ms_host
        user = "root"
        ssh_identity_file = None
    return user, proxy_host, ssh_identity_file


def open_sftp_session(hostname, username, password, use_proxy=None, port=22):
    """
    Creates and opens the SFTP client session

    :param hostname: Name of the SFTP host
    :type hostname: str
    :param username: User who will connect to the SFTP host
    :type username: str
    :param password: Password of the user who will connect to the SFTP host
    :type password: str
    :param use_proxy: Boolean indicating if a proxy is required
    :type use_proxy: bool
    :param port: Port number to connect to if not 22
    :type port: int

    :return: Tuple containing the created sftp client instance and the proxy object
    :rtype: tuple
    """
    proxy = None
    log.logger.debug("Attempting to open SFTPClient for host: ['{0}'] with username: ['{1}'].".format(
        hostname, username))
    if use_proxy and not cache.is_enm_on_cloud_native():
        user, proxy_host, ssh_identity_file = get_proxy_details()
        proxy = create_proxy(hostname, user, proxy_host, ssh_identity_file=ssh_identity_file)
        transport = paramiko.Transport(sock=proxy)
    else:
        transport = paramiko.Transport((hostname, port))
    transport.connect(None, username, password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    log.logger.debug("Successfully opened SFTPClient for host: [{0}].".format(hostname))
    return sftp, proxy


def sftp_get(sftp_client, remote_file_path, local_file_path, proxy=None):
    """
    Performs a SFTP get request using the supplied client and file paths

    :param sftp_client: SFTPClient which will perform the get
    :type sftp_client: `SFTPClient`
    :param remote_file_path: Path to the file on the remote host
    :type remote_file_path: str
    :param local_file_path: Path to the file on the local host
    :type local_file_path: str
    :param proxy: ProxyCommand object to be closed if supplied
    :type proxy: `paramiko.ProxyCommand`
    """
    log.logger.debug("Attempting to get: [{0}] from sftp client.".format(remote_file_path))
    sftp_client.get(remote_file_path, local_file_path)
    log.logger.debug("Successfully got: [{0}] from sftp client.".format(remote_file_path))
    log.logger.debug("Attempting to close sftp client.")
    sftp_client.close()
    log.logger.debug("Successfully closed sftp client")
    if proxy:
        log.logger.debug("Closing proxy object.")
        close_proxy(proxy)
        log.logger.debug("Successfully closed proxy object.")


def download(hostname, username, password, remote_file_path, local_file_path, use_proxy=None):
    """
    Downloads the file from the SFTP client

    :param hostname: Name of the SFTP host
    :type hostname: str
    :param username: User who will connect to the SFTP host
    :type username: str
    :param password: Password of the user who will connect to the SFTP host
    :type password: str
    :param remote_file_path: Path to the file on the remote host
    :type remote_file_path: str
    :param local_file_path: Path to the file on the local host
    :type local_file_path: str
    :param use_proxy: Boolean indicating if a proxy is required
    :type use_proxy: bool

    """
    log.logger.debug("Starting download of [{0}] from host: [{1}] to local path: [{2}].".format(
        remote_file_path, hostname, local_file_path))
    sftp_client, proxy = open_sftp_session(hostname, username, password, use_proxy)
    sftp_get(sftp_client, remote_file_path, local_file_path, proxy)
    log.logger.debug("Completed download of [{0}] from host: [{1}] to local path: [{2}].".format(
        remote_file_path, hostname, local_file_path))


def sftp_put(sftp_client, remote_file_path, local_file_path, proxy=None, file_permissions=None):
    """
    Performs a SFTP put request using the supplied client and file paths

    :param sftp_client: SFTPClient which will perform the get
    :type sftp_client: `SFTPClient`
    :param remote_file_path: Path to the file on the remote host
    :type remote_file_path: str
    :param local_file_path: Path to the file on the local host
    :type local_file_path: str
    :param proxy: ProxyCommand object to be closed if supplied
    :type proxy: `paramiko.ProxyCommand`
    :param file_permissions: Integer value representing file permissions to be set
    :type file_permissions: int
    """
    log.logger.debug("Attempting to put: [{0}] to sftp client.".format(local_file_path))
    base_dir = os.path.dirname(remote_file_path)
    octal_values = {755: 0o755, 777: 0o777, 600: 0o600, 644: 0o644}
    try:
        sftp_client.chdir(base_dir)  # Test if remote_path exists
    except IOError:
        sftp_client.mkdir(base_dir)
    sftp_client.put(local_file_path, remote_file_path, confirm=True)
    if file_permissions:
        sftp_client.chmod(path=remote_file_path, mode=octal_values.get(file_permissions))
    log.logger.debug("Successfully put: [{0}] to sftp client.".format(local_file_path))
    log.logger.debug("Attempting to close sftp client.")
    sftp_client.close()
    log.logger.debug("Successfully closed sftp client")
    if proxy:
        log.logger.debug("Closing proxy object.")
        close_proxy(proxy)
        log.logger.debug("Successfully closed proxy object.")


def upload(hostname, username, password, remote_file_path, local_file_path, use_proxy=None, file_permissions=None):
    """
    Uploads the file to the SFTP client

    :param hostname: Name of the SFTP host
    :type hostname: str
    :param username: User who will connect to the SFTP host
    :type username: str
    :param password: Password of the user who will connect to the SFTP host
    :type password: str
    :param remote_file_path: Path to the file on the remote host
    :type remote_file_path: str
    :param local_file_path: Path to the file on the local host
    :type local_file_path: str
    :param use_proxy: Boolean indicating if a proxy is required
    :type use_proxy: bool
    :param file_permissions: Integer value representing file permissions to be set
    :type file_permissions: int

    """
    log.logger.debug("Starting upload of [{0}] from host: [{1}] to local path: [{2}].".format(
        remote_file_path, hostname, local_file_path))
    sftp_client, proxy = open_sftp_session(hostname, username, password, use_proxy)
    sftp_put(sftp_client, remote_file_path, local_file_path, proxy, file_permissions=file_permissions)
    log.logger.debug("Completed upload of [{0}] from host: [{1}] to local path: [{2}].".format(
        remote_file_path, hostname, local_file_path))


def download_file(remote_path, local_path, host, user, password=None, ms_proxy=False):
    """
    Copies a file from the specified path on the remote host to the local host

    :param remote_path: Absolute path on the remote host to which the file should be copied
    :type remote_path: str
    :param local_path: Absolute path to the local file to be copied to the remote host
    :type local_path: str
    :param host: Hostname or IP address of the host to which the keys should be copied
    :type host: str
    :param user: SSH username to use to log in to the remote host
    :type user: str
    :param password: Password for the SSH user account specified in L{user}
    :type password: str
    :param ms_proxy: set to True to create an open socket to use for communication to the target host
    :type ms_proxy: bool
    """

    # Get a connection from the pool
    connection = shell.get_connection_mgr().get_connection(host, user, password, ms_proxy=ms_proxy)

    # Check to see if an SFTP client has already been initialized for this connection; if not, initialize one
    if not getattr(connection, "sftp_client", None):
        connection.sftp_client = connection.open_sftp()
    try:
        connection.sftp_client.get(remote_path, local_path)
    finally:
        # Return the connection to the pool
        shell.connection_mgr.return_connection(host, connection)
