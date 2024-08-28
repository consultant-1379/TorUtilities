# ********************************************************************
# Name    : Process
# Summary : Generic functionality for managing system level processes.
# ********************************************************************

import commands
import os
import time
import signal
import re

# These modules are imported relatively from current python package i.e. lib
# and to avoid circular imports we cannot do from . import ...
import log
import shell
# End circular imports


def is_pid_running(pid):
    """
    B{Checks whether the specified process is running}.

    :type pid: str
    :param pid: Process ID to be checked
    :rtype: bool
    :return: True if D R S I is in status else False
    """

    pid = str(pid)

    response = shell.run_local_cmd(shell.Command("ps --no-headers -p %s -o stat" % pid))
    status = response.stdout

    if "D" in status or "R" in status or "S" in status or "T" in status:
        log.logger.debug("Process ID %s is running on the deployment" % pid)
        return True
    else:
        log.logger.debug("Process ID %s is not running on the deployment" % pid)
        return False


def kill_pid(pid, sig=None):
    """
    Kills a local process group with user-specified signal

    :type pid: str
    :param pid: Process ID to be killed
    :type sig: int
    :param sig: Signal to be sent to the process (defaults to SIGKILL)
    :rtype: bool
    :return: True if pid is not running
    """

    sig = sig or signal.SIGKILL

    result = False

    os.killpg(os.getpgid(pid), sig)
    time.sleep(.001)

    if not is_pid_running(pid):
        result = True

    return result


def get_current_rss_memory_for_current_process(pid=None):
    """
    Get current RSS memory usage for Process
    :param pid: Process Id
    :type pid: int

    :return: Current RSS memory usage of current process (kB)
    :rtype: int
    """
    pid = pid or os.getpid()
    rss_parameter = "VmRSS"
    cmd = 'egrep {0} /proc/{1}/status'.format(rss_parameter, pid)

    response = shell.run_local_cmd(shell.Command(cmd, log_cmd=False))
    if response.ok and rss_parameter in response.stdout:
        m = re.search(r"\d+", response.stdout)
        if m:
            rss_memory_usage = int(m.group(0))
            log.logger.debug("Process {0} RSS Memory usage: {1} (kB)".format(pid, rss_memory_usage))
            return rss_memory_usage

    log.logger.debug("Cannot fetch current RSS memory usage for process {0}".format(pid))
    return 0


def kill_process_id(pid, signal_id=signal.SIGTERM):
    """
    Kill specific process id with user-specified signal

    :param pid: Process Id
    :type pid: int
    :param signal_id: Signal Number
    :type signal_id: int
    """

    if pid and os.path.isdir('/proc/{0}/'.format(pid)):
        log.logger.debug("Sending signal {0} to process {1}".format(signal_id, pid))
        os.kill(pid, signal_id)


def kill_spawned_process(profile_name, profile_pid, retry=0):
    """
    Kill any child processes still running after teardown
    """
    log.logger.debug("Checking for any child processes spawned by profile pid {0}".format(profile_pid))
    for pid in get_profile_daemon_pid(profile_name):
        if pid.isdigit() and int(pid) != profile_pid:
            kill_process_id(int(pid), signal.SIGKILL)
    if retry < 1:
        retry += 1
        kill_spawned_process(profile_name, profile_pid, retry)


def get_profile_daemon_pid(profile_name):
    """
    Gets profile daemon pid(s).
    Will return multiple pids if process has been forked (having same name and arguments as parent, except diff pid)

    :param profile_name: Profile name
    :type profile_name: str
    :return: List of Process id's
    :rtype: list
    """
    log.logger.debug("Fetching profile daemon pid's")
    cmd = '/usr/bin/pgrep -f "daemon.* {0}(|_stop) {1}"'.format(profile_name.upper(), profile_name.lower())
    pid_response = shell.run_local_cmd(shell.Command(cmd))
    if 'error' in pid_response.stdout:
        return [pid_response.stdout.split('\n')[1]]
    elif pid_response.ok and pid_response.stdout.strip():
        return pid_response.stdout.strip().split("\n")
    else:
        return []


def get_process_name(process_id):
    """
    Get process name given process id.

    :param process_id: process id.
    :type process_id: str
    :return: process name
    :rtype: str
    """
    log.logger.debug("Attempting to retrieve process name given process id {0}.".format(process_id))
    rc, output = commands.getstatusoutput("ps --no-headers -p {0} -o comm".format(process_id))
    process_name = output if rc == 0 else "unable_to_get_process_name"
    log.logger.debug("Attempt completed to retrieve process name {0} given process id {1}.".format(process_name,
                                                                                                   process_id))
    return process_name
