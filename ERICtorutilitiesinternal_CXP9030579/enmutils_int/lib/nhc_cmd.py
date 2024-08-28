# ********************************************************************
# Name    : NHC Command
# Summary : Module primarily used by NHC profiles. Allows the user to
#           construct and execute node health check commands in the
#           NHC application, and verify the result.
# ********************************************************************

import time
from datetime import datetime, timedelta

from enmutils.lib import log
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, TimeOutError


class NHCCmds(object):

    NHC_CMD = "nhc rep run -n {node_names}"

    def __init__(self, user, timeout=None):
        """
        Constructor for NHCcmd

        :type user : enm_user.User object
        :param user: user we use to run nhc_cmd
        :type timeout : int
        :param timeout: time (in minutes) command will wait to complete
        """

        self.user = user
        self.timeout = timeout

    def execute(self, nodes):
        """
        Executes NHC Command in the CLI

        :type nodes: list of `enm_node.Node` instances
        :param nodes: node instances on which to perform nhc_cmd
        :raises ScriptEngineResponseValidationError:
        """
        node_names = [node.node_id for node in nodes]
        command = self.NHC_CMD.format(node_names=";".join(node_names))

        command_response = self.user.enm_execute(command)
        log.logger.info("Information output: {0}".format(command_response.get_output()[1]))
        if 'successfully created.' in command_response.get_output()[1]:
            log.logger.debug("Successfully run NHC healthcheck for {} nodes".format(len(node_names)))
        else:
            raise ScriptEngineResponseValidationError(
                "NHC Command failed, run NHC healthcheck for {} nodes".format(len(node_names)), response=command_response)

    def check_result(self, nodes):
        """
        Executes NHC REP -ST Command in the CLI
        to check if the NHC reports have been completed
        :param nodes: nodes to be used by this function
        :type nodes: nodes
        :return: the time that all nhc reports have taken to all be completed
        :rtype: int
        :raises TimeOutError:
        """

        command = "nhc rep -st"
        command_response = self.user.enm_execute(command, timeout_seconds=self.timeout * 60)

        ini_execution_time = datetime.now()
        minutes = self.timeout
        timeout_from_now = ini_execution_time + timedelta(minutes=minutes)

        while "progress" in str(command_response.get_output()):
            if datetime.now() > timeout_from_now:
                break
            log.logger.debug("NHC report in progress. Checking every 30s")
            time.sleep(30)
            command_response = self.user.enm_execute(command, timeout_seconds=self.timeout * 60)

        end_execution_time = datetime.now()
        execution_time = (end_execution_time.minute - ini_execution_time.minute) * 60 + end_execution_time.second - ini_execution_time.second
        if datetime.now() > timeout_from_now:
            raise TimeOutError('Command %s in %s nodes did not become complete in %d seconds. It took %d seconds' %
                               ("nhc rep run -n", len(nodes), self.timeout, execution_time))

        return execution_time
