# ********************************************************************
# Name    : Shell
# Summary : Provides varying levels of functionality for connecting to
#           remote hosts from pool of connections, Connection Pool
#           Manager, Connection Details classes.
#           Provides local and remote host command functionality,
#           Executor, Remote Executor, Local Executor, Command and
#           Response classes.
# ********************************************************************

import Queue
import collections
import json
import random
import time

import paramiko

import cache
import config
import filesystem
import mutexer
import timestamp
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.kubectl_commands import COPY_FILES
import executor
import log
import command_execution

MAX_CONNECTIONS_PER_REMOTE_HOST = 10
DEFAULT_VM_SSH_KEYPATH = "/root/.ssh/vm_private_key"
connection_mgr = None


class ConnectionPoolManager(object):
    id_counter = 1

    def __init__(self):
        """
        ConnectionPoolManager constructor
        """

        self.remote_connection_pool = {}

    def get_connection(self, host, user, password=None, new_connection=False, ssh_identity_file=None, ms_proxy=False, allow_agent=True, look_for_keys=True):
        """
        Get a connection from the connection pool, creating one if none are available and the queue isn't full

        NOTE: Waits up to 30s for a connection to become available to return, otherwise returns None

        :param host: IP address or hostname of the remote host on which the command is to be executed
        :type host: string
        :param user: Username of the account to use for the SSH connection
        :type user: string
        :param password: Password for the aforementioned user account (optional; not required for public key based connections)
        :type password: string
        :param new_connection: set to True to set up a new connection.
        :type new_connection: bool
        :param ssh_identity_file: the filename of optional private key to try for authentication
        :type ssh_identity_file: string
        :param ms_proxy: set to True to create an open socket or socket-like object (such as a `.Channel`) to use for communication to the target host
        :type ms_proxy: bool
        :param allow_agent: set to False to disable connecting to the SSH agent
        :type allow_agent: bool
        :param look_for_keys: set to False to disable searching for discoverable private key files in ``~/.ssh/``
        :type look_for_keys: bool

        :returns: a connection from the connection pool, creating one if none are available and the queue isn't full
        :rtype: paramiko.Client

        """
        if new_connection:
            return self._establish_connection(host, user, password, ssh_identity_file=ssh_identity_file, ms_proxy=ms_proxy, allow_agent=allow_agent, look_for_keys=look_for_keys)

        create_connection = False

        # Use a mutex to synchronize access to the remote session dictionary
        with mutexer.mutex("shell-connection-manager-get-connection"):

            if host not in self.remote_connection_pool:
                self.remote_connection_pool[host] = {}
                self.remote_connection_pool[host]['available'] = Queue.Queue(MAX_CONNECTIONS_PER_REMOTE_HOST)
                self.remote_connection_pool[host]['used'] = collections.deque()

            # Pull the connection queue for this host from the dictionary
            available = self.remote_connection_pool[host]['available']
            used = self.remote_connection_pool[host]['used']

            # Try to pull a connection from the queue if one is available
            connection = None
            checked_connections = collections.deque()
            while connection is None:
                try:
                    possible_connection = available.get(False)
                    if hasattr(possible_connection, 'user') and possible_connection.user == user:
                        connection = possible_connection
                    # Following required for rpm upgrades where we have connections in our pool that do not have the
                    # user attribute set and so it just works like it did previously
                    elif not hasattr(possible_connection, 'user'):
                        connection = possible_connection
                    else:
                        checked_connections.append(possible_connection)
                except Queue.Empty:
                    break

            for checked_connection in checked_connections:
                available.put(checked_connection)

            # If no connection was immediately available...
            if connection is None or not self.is_connected(connection):
                # Cycle through the used queue and make sure there are no dead connections in there
                for _ in range(1, len(used) + 1):
                    connection = used.pop()
                    if self.is_connected(connection):
                        used.append(connection)

                # If the length of the available and used queues is less than max connections, let's create a new connection
                if (available.qsize() + len(used)) < MAX_CONNECTIONS_PER_REMOTE_HOST:
                    create_connection = True
                # Otherwise, if the queue is full, we just need to sit and wait for a connection to free up, and remove
                # it from the queue to allow us to create another one with the correct user
                else:
                    try:
                        # pop one off the queue to make room for a new user connection)
                        available.get(True, 120)
                        create_connection = True

                    except Queue.Empty:
                        connection = None

                    # Check to see if we got a dead connection; if so, let's create a new one
                    if connection is not None and not self.is_connected(connection):
                        create_connection = True

            # Create a new connection if we need to
            if create_connection:
                connection = self._establish_connection(host, user, password, ssh_identity_file=ssh_identity_file, ms_proxy=ms_proxy, allow_agent=allow_agent, look_for_keys=look_for_keys)

                if connection is not None:
                    total_connections = available.qsize() + len(used) + 1
                    log.logger.debug("There are {0} connections in the connection pool for remote host {1}".format(total_connections, host))

            # If we have a valid connection, make sure it is added to the used list to reflect that it's in use
            if connection is not None:
                used.append(connection)

        return connection

    def return_connection(self, host, connection, keep_connection_open=False):
        """
        Returns a connection to the connection pool if the pool isnt full and its a valid connection otherwise just close the connection

        :param host: IP address or hostname of the remote host on which the command is to be executed
        :type host: str
        :param connection: Connection to be returned to the connection pool
        :type connection: paramiko.Client
        :param keep_connection_open: False if you want the connection to close after you return it else True
        :type keep_connection_open: bool
        """
        try:
            if not keep_connection_open and connection.get_transport():
                connection.close()
        except Exception as e:
            log.logger.debug("Failed to close connection, exception encountered: {0}".format(str(e)))
        with mutexer.mutex("shell-connection-manager-return-connection"):
            # Once pool is managed properly - take out independent calls to _establish_connection when they dont want to
            # use the pool and just want a once off connection. This will be implemented as per JIRA TORF-244099.
            # Then we should remove this if condition as once we only use the pool,
            # the host will always be in self.remote_connection_pool
            if host in self.remote_connection_pool:
                available = self.remote_connection_pool[host]["available"]
                used = self.remote_connection_pool[host]["used"]

                # Once JIRA TORF-241993 is done then this try catch should be removed as there is no need for it.
                try:
                    used.remove(connection)
                except ValueError:
                    log.logger.debug(
                        "The specified connection with id: {0} did not exist in the used connection queue.".format(
                            connection.id))

                if keep_connection_open and connection.get_transport() and self.is_connected(connection):
                    try:
                        available.put(connection, False)
                        return
                    except Queue.Full:
                        log.logger.debug("The available connections queue is already full and therefore "
                                         "cant add the valid connection with id {0}.".format(connection.id))

    def is_connected(self, connection):
        """
        Checks to see if the connection to the remote host is active and established or not

        :param connection: connection to check
        :type connection: paramiko.Client
        :return: True if connection is authenticated
        :rtype: bool

        """

        result = False

        # If we encounter an exception checking the connection, swallow it since we're going to report a false anyway
        try:
            if connection is not None and connection.get_transport().is_authenticated():
                result = True
        except Exception as e:
            log.logger.debug("Exception in shell.ConnectionPoolManager.is_connected: {0}".format(str(e)))

        return result

    def establish_connection(self, *args, **kwargs):
        """
        Wrapper used to establish SSH connection

        :type args: list
        :param args: List of connection properties
        :type kwargs: dict
        :param kwargs: Dictionary of connection properties
        :returns: a new SSH connection and proxy (if created)
        :rtype: paramiko.Client or tuple
        """
        return self._establish_connection(*args, **kwargs)

    def _establish_connection(self, *args, **kwargs):
        """
        Establishes a new SSH connection

        :param args: List of connection properties
        :type args: list
        :param kwargs: Dictionary of connection properties
        :type kwargs: dict
        :returns: SSH connection and proxy (if created)
        :rtype: paramiko.Client or tuple

        """
        host, user, _ = args
        connection = self._make_connection_with_host(*args, **kwargs)

        log.logger.debug("Initial connection established; Request a pseudo-terminal from the server... ")
        transport = connection.get_transport()
        channel = transport.open_session()
        channel.get_pty()

        with mutexer.mutex("shell-establish-connection-set-id"):
            connection.id = ConnectionPoolManager.id_counter
            ConnectionPoolManager.id_counter += 1

        connection.host = host
        connection.user = user
        connection.timed_out = False

        log.logger.debug("Established SSH connection {0}@{1} [connection ID {2}]".format(user, host, connection.id))

        return connection

    def _make_connection_with_host(self, *args, **kwargs):
        """
        Make connection with host.
        :param args: List of arguments
        :type args: list
                    param host: Hostname being connected to
                    type host: str
                    param user_details: Tuple of user details (username, password & ssh_identity_file)
                    type user_details: tuple
                    param allow_agent: Flag to allow connecting to SSH proxy agent
                    type allow_agent: bool
                    param look_for_keys: Flag to allow for searching for discoverable private key
                    type look_for_keys: bool
                    param ms_proxy: Flag to indicate if SSH proxy is to be used or not
                    type ms_proxy: bool
        :param kwargs: Dictionary of arguments
        :type kwargs: dict
                    param retry: Max retries in case of ssh exceptions
                    type retry: int

        :return: SSH connection object
        :rtype: paramiko.Client

        :raises EnvironError: if the ssh_identity_file does not exist
        """
        host, user, password = args
        allow_agent = kwargs.get("allow_agent", True)
        look_for_keys = kwargs.get("look_for_keys", True)
        retry = kwargs.get("retry", 3)
        proxy = kwargs.get("ms_proxy", None)

        ssh_identity_file = kwargs.get("ssh_identity_file")
        if ssh_identity_file and not filesystem.does_file_exist(ssh_identity_file, verbose=False):
            raise EnvironError("The ssh_identity_file does not exist - cannot create connection")

        connection = paramiko.SSHClient()

        try:
            connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            connection.load_system_host_keys()
            log.logger.debug("Making connection to {0} (Details: {1})"
                             .format(host, (user, password, ssh_identity_file, 7, proxy,
                                            allow_agent, look_for_keys, 30)))
            connection.connect(host, username=user, password=config.get_encoded_password_and_decode(user, password),
                               key_filename=ssh_identity_file, timeout=7,
                               sock=proxy, allow_agent=allow_agent, look_for_keys=look_for_keys, auth_timeout=30)
            log.logger.debug("Connection established to {0}".format(host))
            return connection

        except Exception as e:
            connection.close()
            retry = self.check_multiple_retry_needed(e, host, proxy, retry)
            kwargs.update({"retry": retry})
            return self._make_connection_with_host(*args, **kwargs)

    @staticmethod
    def check_multiple_retry_needed(error, host, ms_proxy, retry):
        """
        Check if multiple retries are needed

        :param error: Exception that occurred while trying to connect to host
        :type error: 'paramiko.BadHostKeyException` or `paramiko.AuthenticationException`
        :param host: Hostname of remote machine
        :type host: str
        :param ms_proxy: Flag to indicate if proxy host is being used
        :type ms_proxy: bool
        :param retry: integer to indicate indicate if retry is applicable
        :type retry: int
        :return: Number of retries remaining
        :rtype: int

        :raises EnvironError: if number of retries is zero and unable to fetch Host Details
        """
        log.logger.debug("Exception '{0}' when connecting to host: {1}".format(str(error), host))
        max_retry_delay_secs = 10

        if retry:
            retry = retry - 1
            retry_delay = round(random.uniform(1, max_retry_delay_secs), 2)

            if isinstance(error, paramiko.BadHostKeyException):
                log.logger.debug("Clearing old ssh host key entries")
                run_local_cmd("ssh-keygen -R {0}".format(host))

            if isinstance(error, paramiko.AuthenticationException) and ms_proxy:
                log.logger.debug("Authentication failed, fetching vm_private_key from MS")
                run_local_cmd('scp root@{0}:/root/.ssh/vm_private_key ~/.ssh'.format(cache.get_ms_host()))

            if isinstance(error, paramiko.SSHException) and "protocol banner" in error.message:
                log.logger.debug("SSH Contention encountered trying to connect to host")

            if isinstance(error, paramiko.SSHException) and "No existing session" in error.message:
                log.logger.debug("Session no longer available, reconnecting to session.")

            log.logger.debug("Sleeping for {0}s before retrying".format(retry_delay))
            time.sleep(retry_delay)

            return retry

        log.logger.debug("Max retries reached - raising error")
        raise EnvironError("Unable to get Host Details: {0}".format(str(error)))


class Command(object):

    def __init__(self, cmd, log_cmd=True, timeout=None, allow_retries=True, check_pass=False, cwd=None,
                 activate_virtualenv=False, retry_limit=None, async=False):
        """
        Command Constructor

        :param cmd: The shell command to be execute
        :type cmd: str
        :param log_cmd: Flag controlling whether command is to be logged to debug log (defaults to True)
        :type log_cmd: bool
        :param timeout: Length of time to allow command to run before terminating the command
        :type timeout: int
        :param allow_retries: Flag controlling whether the command is to be retried if it times out (defaults to True)
        :type allow_retries: bool
        :param check_pass: Flags whether the check for an rc of 0 after executing command (defaults to False)
        :type check_pass: bool
        :param cwd: Option to change the current working directory when executing the command (defaults to None)
        :type cwd: str
        :param activate_virtualenv: Flags if virtualenv needs to be activated prior to running the command
        :type activate_virtualenv: bool
        :param retry_limit: limit set for retries
        :type retry_limit: int
        :param async: Flags whether to wait for a command response or just run the command and return
        :type async: bool
        """

        self.cmd = cmd
        self.log_cmd = log_cmd
        self.timeout = timeout
        self.check_pass = check_pass
        self.allow_retries = allow_retries
        self.cwd = cwd
        self.async = async

        self.retry_count = 1
        self.retry_limit = retry_limit
        self.execution_host = None
        self.finished = False
        self.current_timeout = self.timeout
        self.response = None
        self.activate_virtualenv = activate_virtualenv

    def initialize_attributes(self):
        """
        Sets attributes to their initial state before executing the command
        """
        self.retry_count = 1
        self.execution_host = None

        if not self.retry_limit:
            self.retry_limit = 2 if self.allow_retries else 1
        if not self.timeout:
            self.timeout = 60

    def _set_attributes(self):
        """
        Sets or resets attributes to default state before each command execution (including retries)
        """
        self.current_timeout = self.timeout
        self.finished = False
        self.response = Response(command=self.cmd)

    def pre_execute(self):
        """
        Performs any setup and/or logging tasks to be done before command execution is started
        """
        # Set attributes or reset them in the event that a command is being rerun
        self._set_attributes()
        # Adjust the timeout if necessary
        self._set_command_timeout()

        if self.log_cmd:
            log.logger.debug("Executing command on {0}: '{1}' [timeout {2}s]".format(
                self.execution_host, self.cmd, self.current_timeout))
        # Record the start timestamp
        self.response._start_timestamp = timestamp.get_current_time()

    def post_execute(self):
        """
        Performs any teardown and/or logging tasks after command execution
        """
        # Figure out the elapsed execution time
        self.response._end_timestamp = timestamp.get_current_time()
        self.response._elapsed_time = timestamp.get_elapsed_time(self.response.start_timestamp)

        # If command timed out or the connection was closed, log the error
        if self.response.rc in [executor.COMMAND_TIMEOUT_RC, executor.COMMAND_CONNECTION_CLOSED_RC,
                                executor.COMMAND_EXCEPTION_RC]:
            self._log_error_result()
            if self._can_retry():
                self._sleep_between_attempts()
        else:
            if self.log_cmd:
                # Log the successful execution
                log.logger.debug(
                    "Executed command '{0}' on {1} [elapsed time {2}s]\n  Command return code: {3}\n  Command output: "
                    "{4}".format(self.cmd, self.execution_host, self.response.elapsed_time, str(self.response.rc),
                                 self.response.stdout))
            self.finished = True

        if self.finished and self.check_pass:
            self._check_command_passed()

    def _set_command_timeout(self):
        """
        Sets timeout value for the command
        """
        if self.retry_count > 1:
            self.current_timeout = self.current_timeout * 2
            log.logger.debug("Increasing command execution timeout to {0}s for next execution attempt...".format(
                self.current_timeout))

    def _check_command_passed(self):
        """
        Checks command for a return code of 0 and raises a RuntimeError if the rc is not 0
        """
        if self.response.rc != 0:
            error_message = "Command was expected to pass, but produced a non-zero return code [{0}]; CMD: {1}".format(
                self.response.rc, self.cmd)
            raise RuntimeError(error_message)

    @staticmethod
    def _sleep_between_attempts():
        """
        Sleeps between command execution attempts
        """
        # Sleep for a small bit to give the system some breathing room
        sleep_interval = float("{:.2f}".format((random.random() * 4)))
        log.logger.debug("Sleeping for {0} seconds before re-attempting...".format(sleep_interval))

        time.sleep(sleep_interval)

    def _can_retry(self):
        """
        Checks whether a command that has erred can be run again

        :return: True if can retry else False
        :rtype: bool
        """
        if not self.allow_retries or self.retry_count == self.retry_limit:
            result = False
            self.finished = True
        else:
            result = True
            self.retry_count += 1
        return result

    def _log_error_result(self):
        """
        Logs information to debug log on failed command execution attempt

        :raises EnvironError: if process terminates unexpectedly
        """
        with mutexer.mutex("log-command-error-result"):
            try:
                if self.response.rc == executor.COMMAND_TIMEOUT_RC:
                    log.logger.debug(
                        "   ERROR: Process exceeded timeout and was forcibly terminated [attempt {0}/{1}]".format(
                            self.retry_count, self.retry_limit))
                    log.logger.debug(" TIMEOUT: {0}s".format(self.current_timeout))
                elif self.response.rc == executor.COMMAND_CONNECTION_CLOSED_RC:
                    raise EnvironError("ERROR: Process terminated unexpectedly Please refer to logs")
            except EnvironError as e:
                log.logger.debug("Encountered an error while carrying out the command : {0}".format(e))

            log.logger.debug(
                "     CMD: {0}\n  STDOUT: {1}\n      RC: {2}\nCMD TIME: {3}s".format(
                    self.cmd, self.response.stdout, self.response.rc, self.response.elapsed_time))


class Response(object):

    def __init__(self, rc=None, stdout=None, elapsed_time=None, command=None, pid=None):
        """
        Response Constructor

        :param rc: return code
        :type rc: int
        :param stdout: the stout to be displayed
        :type stdout: str
        :param elapsed_time: the time elapsed before the response
        :type elapsed_time: int
        :param command: the command that was executed
        :type command: str
        :param pid: process id to check
        :type pid: str
        """
        self._rc = rc
        self._stdout = stdout
        self._elapsed_time = None
        self._start_timestamp = elapsed_time
        self._end_timestamp = None
        self._pid = pid
        self.command = command

    @property
    def rc(self):
        """
        Return code

        :return: return code
        :rtype: int
        """
        return self._rc

    @property
    def stdout(self):
        """
        Standard-out

        :return: the stout
        :rtype: str
        """
        return self._stdout

    @property
    def start_timestamp(self):
        """
        Command start timestamp

        :return: The start timestamp of the command.
        :rtype: str
        """
        return self._start_timestamp

    @property
    def end_timestamp(self):
        """
        Command end timestamp

        :return: The end timestamp of the command.
        :rtype: str
        """
        return self._end_timestamp

    @property
    def elapsed_time(self):
        """
        Command total elapsed time

        :return: The elapsed timestamp of the command.
        :rtype: str
        """
        return self._elapsed_time

    @property
    def ok(self):
        """
        OK the return code

        :return: Boolean indicating if the rc is equal to zero.
        :rtype: bool
        """
        return self.rc == 0

    @property
    def pid(self):
        """
        The process id value

        :return: The process ID of the command.
        :rtype: str

        """
        return self._pid

    def json(self):
        """
        Function to load the stdout to python object

        :return: Load the stdout of the command to a python object
        :rtype: any
        """
        return json.loads(self._stdout)


# Function to ensure that our ConnectionPoolManager is used as a singleton
def get_connection_mgr():
    """
    Function to ensure that our ConnectionPoolManager is used as a singleton

    :returns: the singleton shell.ConnectionPoolManager instance
    :rtype: shell.ConnectionPoolManager

    """
    global connection_mgr

    if connection_mgr is None:
        connection_mgr = ConnectionPoolManager()

    return connection_mgr


def create_proxy(remote_host, username, ms_host, ssh_identity_file=None):
    """
    Create SSH proxy (to allow port-forwarding) on Management Server (EMP/LMS)

    :param remote_host: Remote Host
    :type remote_host: str
    :param ssh_identity_file: Path to filename containing ssh private key
    :type ssh_identity_file: str
    :param username: Username that will setup Proxy on Management Server (i.e. EMP/LMS)
    :type username: str
    :param ms_host: Management Host IP
    :type ms_host: str
    :return: ProxyCommand object
    :rtype: paramiko.ProxyCommand
    :raises RuntimeError: if cannot setup proxy
    """

    log.logger.debug("Creating ssh proxy towards host {0} on {1}".format(remote_host, ms_host))
    if ssh_identity_file and not filesystem.does_file_exist(ssh_identity_file):
        raise RuntimeError("Cannot setup proxy as ssh_identity_file does not exist: {0}".format(ssh_identity_file))

    identity_file_option = "-i {0}".format(ssh_identity_file) if ssh_identity_file else ""
    command = ("ssh {identity_file_option} -x -a -q -o StrictHostKeyChecking=no "
               "{username}@{ms_host} nc {remote_host} 22"
               .format(identity_file_option=identity_file_option, username=username, ms_host=ms_host,
                       remote_host=remote_host))

    log.logger.debug("Using command: '{0}'".format(command))
    try:
        return paramiko.ProxyCommand(command)
    except Exception as e:
        raise RuntimeError("Unable to setup proxy on {0}: {1}".format(ms_host, str(e)))


def close_proxy(proxy):
    """
    Shutdown Proxy to remote host
    """
    log.logger.debug("Closing proxy to remote host")
    proxy.close()
    proxy.process.poll()
    log.logger.debug("Proxy closed")


# Convenience functions to shield consumers from the executors and underlying data structures
def run_local_cmd(cmd):
    """
    Executes a command on the local host

    :param cmd: Command to be executed
    :type cmd: shell.Command or string

    :returns: a shell.Response instance
    :rtype: shell.Response

    """
    return execute_command_wrapper(cmd)


def run_remote_cmd(
        cmd, host, user, password=None, new_connection=False, ping_host=False, **kwargs):
    """
    Executes a command on a remote host using an ssh connection

    :param cmd: shell.Command instance containing command to be executed
    :type cmd: Command|str
    :param host: IP address or hostname of the remote host on which the command is to be executed
    :type host: str
    :param user: Username of the account to use for the SSH connection
    :type user: str
    :param password: Password for the aforementioned user account (optional; not required for public key based connections)
    :type password: str
    :param new_connection: True if you want to establish a new ssh connection by default else False
    :type new_connection: bool
    :param ping_host: True if you want to check if the provided host is reachable else False
    :type ping_host: bool
    :param kwargs: dictionary of keyword arguments that can be passed to the function
    :type kwargs: dict
            keep_connection_open: True if you want the connection to the host to remain open after running the command else False
            keep_connection_open: bool

    :return: a shell.Response instance with rc=5 if host is not pingable and check was performed else rc=0
    :rtype: Response
    """
    keep_connection_open = kwargs.pop("keep_connection_open", False)
    return execute_command_wrapper(cmd, host, user, password=password, new_connection=new_connection,
                                   ping_host=ping_host, keep_connection_open=keep_connection_open, remote_cmd=True,
                                   **kwargs)


def run_remote_cmd_with_ms_proxy(*args, **kwargs):
    """
    Run command on remote machine

    :param args: List of connection properties
    :type args: list
    :param kwargs: Dictionary of connection properties
    :type kwargs: dict
    :return: Command execution response
    :rtype: RemoteExecutor
    :raises RuntimeError: if command execution on remote server is not successful
    """
    return execute_command_wrapper(*args, **kwargs)


def run_cmd_on_vm(cmd, vm_host, user="cloud-user", password=None, ssh_identity_file=None, **kwargs):
    """
    Executes a command on a remote host using ssh

    :param cmd: shell.Command instance containing command to be executed
    :type cmd: Command|str
    :param vm_host: IP address or hostname of the vm on which the command is to be executed
    :type vm_host: str
    :param user: Username of the account to use for the SSH connection
    :type user: str
    :param password: Password for the aforementioned user account (optional; not required for public key based
                        connections)
    :type password: str
    :param ssh_identity_file: location of the ssh identity file
    :type ssh_identity_file: str
    :param kwargs: dictionary of keyword arguments that can be passed to the function
    :type kwargs: dict

    :return: a shell.response object containing the results of issuing the command
    :rtype: Response
    """
    return execute_command_wrapper(cmd, vm_host, user, password=password, ssh_identity_file=ssh_identity_file,
                                   remote_cmd=True, **kwargs)


def run_cmd_on_ms(cmd, **kwargs):
    """
    Runs command on MS. If running on MS it will run command locally
    :param cmd: shell.Command to be executed
    :type cmd: str or `Command`
    :param kwargs: dictionary of keyword arguments that can be passed to the function
    :type kwargs: dict
    :return: a shell.response object containing the results of issuing the command
    :rtype: shell.Response
    """
    return execute_command_wrapper(cmd, remote_cmd=True, **kwargs)


def run_cmd_on_emp_or_ms(cmd, timeout=None, **kwargs):
    """
    Runs command on emp or ms depending on deployment type.

    :param cmd: common/specific command to run on both deployments/ms server
    :type cmd: str
    :param timeout: timeout for command to run
    :type timeout: int
    :param kwargs: a list of keyword arguments
    :type kwargs: list
    :return: a shell.response object containing the results of issuing the command
    :rtype: Response
    """
    if config.is_a_cloud_deployment():
        return run_cmd_on_vm(cmd, vm_host=cache.get_emp(), timeout=timeout, **kwargs)
    else:
        return execute_command_wrapper(cmd, timeout=timeout, remote_cmd=True, **kwargs)


def run_cmd_on_cloud_native_pod(pod_name, container_name, command, suppress_error=True, *args, **kwargs):
    """
    Runs command on Cloud Native Pod.

    :param command: Command to be run
    :type command: str
    :param pod_name: Cloud Native Pod Name
    :type pod_name: str
    :param container_name: Cloud Native Container Name
    :type container_name: str
    :param suppress_error: Suppresses the error output, when True
    :type suppress_error: bool
    :param args: Positional arguments
    :type args: Any
    :param kwargs: Dictionary of optional keyword arguments
    :type kwargs: dict
    :return: shell.Response
    :rtype: Response
    """
    return execute_command_wrapper(command, pod_name=pod_name, container_name=container_name, suppress_error=suppress_error, *args, **kwargs)


def execute_command_wrapper(*args, **kwargs):
    """
    Wrapper function to be called by each of the specific command functions

    :param args: Positional arguments
    :type args: Any
    :param kwargs: Dictionary of optional keyword arguments
    :type kwargs: dict

    :return: Returns the Response objected generated from the command
    :rtype: Response
    """
    return command_execution.execute_cmd(*args, **kwargs)


def copy_file_between_wlvm_and_cloud_native_pod(pod_name, source_file, dest_file, pod_direction):
    """
    Copies files between Workload VM and Cloud Native Pod

    :param pod_name: Cloud Native Pod Name
    :type pod_name: str
    :param source_file: Path to source file
    :type source_file: str
    :param dest_file: Path to destination file
    :type dest_file: str
    :param pod_direction: Direction of transfer wrt pod (i.e. 'to' pod or 'from' pod)
    :type pod_direction: str
    :return: shell.Response
    :rtype: Response
    """
    log.logger.debug("Copying file {0} {1} Cloud Native pod".format(source_file, pod_direction))
    enm_namespace = cache.get_enm_cloud_native_namespace()
    pod_machine_path = "{enm_namespace}/{pod_name}:".format(enm_namespace=enm_namespace, pod_name=pod_name)

    source_machine = destination_machine = ""

    if "from" in pod_direction:
        source_machine = pod_machine_path
    else:
        destination_machine = pod_machine_path

    log.logger.debug("Copying source file '{source_machine}{source_file}' "
                     "to destination file: '{destination_machine}{dest_file}'"
                     .format(source_machine=source_machine, source_file=source_file,
                             destination_machine=destination_machine, dest_file=dest_file))

    cmd = (COPY_FILES.format(source_machine=source_machine, source_file=source_file,
                             destination_machine=destination_machine,
                             dest_file=dest_file))
    return run_local_cmd(Command(cmd))
