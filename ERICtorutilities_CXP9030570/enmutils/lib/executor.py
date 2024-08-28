import os
import subprocess
import sys
import threading

from paramiko.ssh_exception import ProxyCommandFailure

import exception
import log

COMMAND_TIMEOUT_RC = 177
COMMAND_CONNECTION_CLOSED_RC = 255
COMMAND_EXCEPTION_RC = 211


class Executor(object):

    def __init__(self, cmd_obj):
        """
        Executor abstract base class constructor

        :param cmd_obj: Command to be executed
        :type cmd_obj: shell.Command
        """

        self.cmd_obj = cmd_obj
        self.execution_host = None
        self.timer = None

    def execute(self):
        """
        Executes command based on the attributes specified in the object instance

        :return: a shell.Response instance containing output, return code, etc.
        :rtype: shell.Response
        """
        # Initialize command attributes (or reset them in the case of re-exeuction of a command)
        self.cmd_obj.initialize_attributes()
        # Set the execution context in the command so the command has an idea where he was executed
        self.cmd_obj.execution_host = self.execution_host
        # Loop until we get a successful execution or we run out of attempts
        self.cmd_obj.finished = False

        while not self.cmd_obj.finished:
            # Do any necessary pre-execute setup
            self.cmd_obj.pre_execute()
            # Execute the command
            self.execute_command()
            # Do any post-execute teardown
            self.cmd_obj.post_execute()
        return self.cmd_obj.response

    def execute_command(self):
        """
        Executes command
        """
        raise NotImplementedError("This method should be overridden by the derived class")

    def _start_timer(self, proc_or_connection, timeout_killer):
        """
        Creates and starts command timer and defines callback function to be invoked if timeout expires

        :param proc_or_connection: subprocess object which interacts with the shell
        :type proc_or_connection: subprocess.Popen | paramiko.Client
        :param timeout_killer: Function reference to perform the timeout
        :type timeout_killer: function reference
        """
        # Spawn the timer thread
        self.timer = threading.Timer(self.cmd_obj.current_timeout, timeout_killer, [proc_or_connection])
        self.timer.daemon = True
        self.timer.start()

    def _command_cleanup(self, proc=None):
        """
        Kills subprocess and timer if they are still running

        :param proc: subprocess object which interacts with the shell
        :type proc: subprocess.Popen
        """
        # If for some reason the process hasn't terminated, kill it
        try:
            if proc and proc.poll() is None:
                proc.kill()
        except Exception as err:
            log.logger.error("ERROR: {0}".format(str(err)))
            exception.process_exception("Exception raised while trying to kill process")

        # Make sure the timer thread is finished
        if getattr(self.timer, 'is_alive', None) and self.timer.is_alive():
            self.timer.cancel()
            self.timer = None


class RemoteExecutor(Executor):

    def __init__(self, cmd_obj, connection, **kwargs):
        """
        RemoteExecutor constructor

        :type cmd_obj: shell.Command
        :param cmd_obj: Command to be executed
        :type connection: Connection whose command execution is to be terminated
        :param connection: paramiko.Client
        :type kwargs: dict
        :param kwargs: Dictionary of keyword arguments to be passed to the function/method when it is invoked
        """

        super(RemoteExecutor, self).__init__(cmd_obj)
        self.connection = connection
        self.execution_host = connection.host
        # Ability to pass parameter for get_pty as workaround for limitation in ENM as per TORF-151381,
        # i.e. use pseudo-terminal when running certain ENM python scripts via ssh connection
        self.get_pty = kwargs.pop("get_pty", False)
        # threading.Timer only kills the SSH connection not the netsim pipe spawned process for some reason.
        # Underlying issue of why processes sent through netsim pipe are hanging still exists.
        self.add_linux_timeout = kwargs.pop("add_linux_timeout", False)

        # Remote retries are not enabled by default
        cmd_obj.allow_retries = False

    def execute_command(self):
        """
        Creates SSH connection to remote host and executes command, returning a shell.Response instance containing
        output, return code, etc.
        """

        # Start the timer thread to make sure that the remote command doesn't hang and create a deadlock
        self._start_timer(self.connection, remote_timeout_killer)
        # Check if the command uses sudo, if it does set get_pty argument to exec_command to True
        if (not self.get_pty and self.cmd_obj.cmd.startswith('sudo') or not self.get_pty and
                self.cmd_obj.cmd.startswith('/usr/bin/sudo')):
            # NOTE: We are going to run the sudo command with pseudo terminal remotely. This has
            # its own side effects. If the output is unexpected please have a look at:
            # http://unix.stackexchange.com/a/122624
            self.get_pty = True

        if self.add_linux_timeout:
            self.cmd_obj.cmd = "timeout --kill-after={0} {0} {1}".format(self.cmd_obj.timeout, self.cmd_obj.cmd)

        # Execute the command and immediately close stdin
        try:
            (stdin, stdout, stderr) = self.connection.exec_command(self.cmd_obj.cmd, timeout=self.cmd_obj.timeout,
                                                                   get_pty=self.get_pty)
            stdin.close()
            if getattr(self.cmd_obj, 'async', None):
                return

            # Attempt to get the return code and output
            self.cmd_obj.response._rc = stdout.channel.recv_exit_status()
            self.cmd_obj.response._stdout = stdout.read() + stderr.read()

            stdout.close()
            stderr.close()
        except ProxyCommandFailure:
            log.logger.error('Bug in paramiko preventing the tunnel to close if this exception occurs resulting in '
                             'socket spiking the CPU usage, check https://github.com/paramiko/paramiko/issues/495')
            self.cmd_obj.response._rc = -1
            self.cmd_obj.response._stdout = ""
        except Exception as err:
            log.logger.error("ERROR: {0}".format(str(err)))
            exception.process_exception("Exception raised while running remote command: '{0}'".format(self.cmd_obj.cmd))
            self.cmd_obj.response._rc = -1
            self.cmd_obj.response._stdout = ""
        finally:
            log.logger.debug(
                "Attempting to close connection with id: '{0}' to host '{1}'.".format(self.connection.id,
                                                                                      self.connection.host))
            self.connection.close()
            log.logger.debug(
                "Connection with id: '{0}' to host '{1}' closed successfully.".format(self.connection.id,
                                                                                      self.connection.host))
            self._command_cleanup()

        # If the command timed out and was killed, update the rc
        if self.connection.timed_out:
            self.cmd_obj.response._rc = COMMAND_TIMEOUT_RC
            self.cmd_obj.response._stdout = ""
        # If the command was interrupted or the remote host died
        elif self.cmd_obj.response._rc == -1:
            self.cmd_obj.response._rc = COMMAND_CONNECTION_CLOSED_RC
            self.cmd_obj.response._stdout = ""


class LocalExecutor(Executor):

    def __init__(self, cmd_obj):
        """
        LocalExecutor constructor

        :param cmd_obj: Command to be executed
        :type cmd_obj: shell.Command
        """

        super(LocalExecutor, self).__init__(cmd_obj)
        self.execution_host = "localhost"

    def execute_command(self):
        """
        Opens subprocess and executes the local command, returning a shell.Reponse instance containing output,
        return code, etc.
        """
        # Kick off the subprocess to execute the command
        prefix = ('source {0};'.format(os.path.join(os.path.dirname(sys.executable), 'activate')) if
                  self.cmd_obj.activate_virtualenv else '')
        proc = subprocess.Popen(
            prefix + self.cmd_obj.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
            cwd=self.cmd_obj.cwd)
        self.cmd_obj.response._pid = getattr(proc, "pid", None)
        try:
            if getattr(self.cmd_obj, 'async', None):
                return
            # Start the timer thread to make sure that the command doesn't hang and create a deadlock
            self._start_timer(proc, local_timeout_killer)
            # Kick off the process and wait for it to finish
            self.cmd_obj.response._stdout = proc.communicate()[0]
            self.cmd_obj.response._rc = proc.returncode
        except Exception as err:
            log.logger.error("ERROR: {0}".format(str(err)))
            exception.process_exception("Exception raised while running local command: '{0}'".format(self.cmd_obj.cmd))
            self.cmd_obj.response._rc = COMMAND_EXCEPTION_RC
            self.cmd_obj.response._stdout = ""
        finally:
            self._command_cleanup(proc)


def remote_timeout_killer(connection):
    """
    Callback function used to kill remote command execution

    :type connection: paramiko.Client
    :param connection: Connection whose command execution is to be terminated
    """

    connection.timed_out = True
    log.logger.debug("Remote command execution has timed out; connection will be closed [connection ID {0}]".format(
        connection.id))
    connection.close()
    if connection.get_transport():
        log.logger.debug("Connection [connection ID {0}] has not closed correctly, re-attempting close "
                         "operation.".format(connection.id))
        connection.close()


def local_timeout_killer(proc):
    """
    Callback function used to kill local command execution

    :param proc: Subprocess object which interacts with the shell
    :type proc: subprocess.Popen
    """

    log.logger.debug("Local command execution has timed out; process will be terminated")

    if proc.poll() is None:
        proc.kill()

    proc.returncode = COMMAND_TIMEOUT_RC
