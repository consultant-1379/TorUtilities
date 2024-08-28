# ********************************************************************
# Name    : AMOS Command
# Summary : Allows user to fetch list of scripting clusters, manage
#           scripting server sessions, create MO Batch commands and
#           execute those commands.
# ********************************************************************


from itertools import cycle
from random import shuffle

from enmutils.lib import log, shell
from enmutils.lib.exceptions import EnmApplicationError, MoBatchCommandReturnedError, EnvironError
from enmutils.lib.headers import DELETE_SECURITY_REQUEST
from enmutils_int.lib.services import deploymentinfomanager_adaptor


def get_specific_scripting_iterator():
    """
    Returns iterator of the all scripting VMs within the scripting cluster on ENM deployment

    return: A list with all scripting clusters in deployment
    rtype: list
    """
    scripting_distribution = deploymentinfomanager_adaptor.get_list_of_scripting_service_ips()
    shuffle(scripting_distribution)
    return cycle(scripting_distribution)


def delete_left_over_sessions(user, session_deleter):
    """
    Delete any open enm user sessions for user
    Invokes the _teardown method on all user session objects that have been added to the teardown list and
    removes the object from persistence

    :type user: enm_user_2.User object
    :param user: User is each mobatch user who has an open enm session
    :type session_deleter: enm_user_2.User object
    :param session_deleter: session_deleter is another admin_user that will delete the left over open enm user sessions

    :raises EnmApplicationError: raised if user session fails to be deleted from scripting cluster

    """

    url = "/oss/sso/utilities/users/{username}".format(username=user.username)
    try:
        session_deleter.delete_request(url, headers=DELETE_SECURITY_REQUEST)
        if user.session:
            user.remove_session()
    except:
        raise EnmApplicationError("User session {0} could not be deleted from scripting cluster".format(user.username))


class MoBatchCmd(object):

    MO_BATCH_CMD = "/opt/ericsson/amos/bin/mobatch {num_in_parallel} {timeout} {node_ids} '{commands}'"

    def __init__(self, nodes, user, commands, num_in_parallel=None, scripting_hostname=None, timeout=None):
        """
        Constructor for MoBatchCmd

        :type nodes: list of `enm_node.Node` instances
        :param nodes: node instances on which to perform mo_batch_cmd
        :type user : enm_user.User object
        :param user: user we use to run run mo_batch_cmd
        :type commands : list of strings
        :param commands: amos commands we want to run against the nodes
        :type num_in_parallel : int
        :param num_in_parallel: Number of sessions we want user to run in parallel
        :type timeout : int
        :param timeout: time (in minutes) command will wait to complete
        :param scripting_hostname: Name of the scripting cluster
        :type scripting_hostname: str
        """
        self.node_ids = [node.node_id for node in nodes]
        self.user = user
        self.commands = commands
        self.num_in_parallel = num_in_parallel
        self.timeout = timeout
        self.scripting_hostname = scripting_hostname

    def execute(self):
        """
        Executes MO Batch Command for AMOS against the scripting vm (scp-x-scripting) defined in the class

        :raises: MoBatchCommandReturnedError(EnvironError) signalling that either AMOS Service or netsim node is down
        """

        num_in_parallel = "" if not self.num_in_parallel else "-p {0}".format(self.num_in_parallel)
        timeout = "" if not self.timeout else "-t {0}".format(self.timeout)
        node_ids = ",".join(self.node_ids)
        commands = ";".join(self.commands)

        command = (self.MO_BATCH_CMD.format(num_in_parallel=num_in_parallel, timeout=timeout,
                                            node_ids=node_ids, commands=commands))

        timeout = 15 * 60 if not self.timeout else self.timeout * 60
        try:
            command_response = shell.run_remote_cmd(shell.Command(command, timeout=timeout), self.scripting_hostname,
                                                    self.user.username, password=self.user.password,
                                                    new_connection=True)
        except Exception as e:
            raise EnvironError(str(e))

        if command_response.rc == 177:
            log.logger.debug('{0}: This Mobatch shell terminal is killed after 10 minutes to avoid hanging sessions '
                             'and allow the profile to run constantly as per ENM TERE.'.format(command_response.stdout))
        elif command_response.rc != 0 or command_response.stdout.count("OK") != len(self.node_ids) * 3:
            raise MoBatchCommandReturnedError(
                "MO Batch Command failed, giving error {0}".format(command_response.stdout), command_response)
