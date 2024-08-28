# ********************************************************************
# Name    : Utilities Helper Methods
# Summary : Contains helper methods to help perform various TorUtilities actions
# ********************************************************************

from enmutils.lib import filesystem, log, shell

BASHRC = "/root/.bashrc"
BASHRC_TORUTILS = "/root/.bashrc_torutils"
SHOPT_CMD = 'shopt -s histappend'
HIST_TIME = 'export HISTTIMEFORMAT="%h/%d - %H:%M:%S "'
HIST_SIZE = 'export HISTSIZE=2000'
DEFAULT_PROMPT = r'PS1="[\\t \u@\h:\W ]# "'
PROMPT_CMD = 'PROMPT_COMMAND=\'history -a;\''
FILE_CONTENT = "{0}\n{1}\n{2}\n{3}\n{4}".format(SHOPT_CMD, HIST_TIME, HIST_SIZE, DEFAULT_PROMPT, PROMPT_CMD)


def append_history_of_commands():
    """
    Appends history of commands
    """
    log.logger.debug("Creating bashrc_torutils file and updating the bashrc file to save history of command execution")
    filesystem.write_data_to_file(data=FILE_CONTENT, output_file=BASHRC_TORUTILS, append=False, log_to_log_file=False)
    shell.run_local_cmd("chmod 755 {0}".format(BASHRC_TORUTILS))
    response = shell.run_local_cmd("egrep '{0}' {1}".format(BASHRC_TORUTILS, BASHRC))
    if not response.ok:
        shell.run_local_cmd("echo '. {0}' >> {1}".format(BASHRC_TORUTILS, BASHRC))
    log.logger.debug("The bashrc file to save history of command execution has been updated")
