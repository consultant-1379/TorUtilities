from enmutils.lib import log, shell
from enmutils.lib.exceptions import EnvironError


def is_nas_accessible():
    """
    to check whether nas is accessible
    :return:is_nas_available
    :rtype:bool
    :raises EnvironError: Exception raised run_cmd_on_ms gives exception
    """
    response = shell.run_cmd_on_ms("cat /etc/hosts | grep 'nas' ")
    log.logger.debug("Response after running command to nas details {0}".format(response.stdout))
    if response.rc == 0:
        is_nas_available = True if "nasconsole" in response.stdout else False
    else:
        raise EnvironError("Unable to get the nas details due to {0}".format(response.stdout))
    return is_nas_available
