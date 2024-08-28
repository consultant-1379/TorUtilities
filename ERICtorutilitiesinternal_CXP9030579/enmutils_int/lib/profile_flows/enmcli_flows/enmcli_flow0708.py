from datetime import datetime, timedelta
from time import sleep
import re

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.cmcli import execute_command_on_enm_cli, get_node_gerancell_value
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

CLI_LIVE_CREATE_COMMAND = ("cmedit create {3},MeContext={0},ManagedElement={0},BscFunction=1,BscM=1,GeranCellM=1,"
                           "GeranCell={2},GeranCellRelation={1} geranCellRelationId={1},relationDirection=SINGLE")

CLI_LIVE_DELETE_COMMAND = ("cmedit delete {3},MeContext={0},ManagedElement={0},BscFunction=1,BscM=1,GeranCellM=1,"
                           "GeranCell={2},GeranCellRelation={1} -force")

CLI_LIVE_GET_COMMAND = ("cmedit get {3},MeContext={0},ManagedElement={0},BscFunction=1,BscM=1,GeranCellM=1,"
                        "GeranCell={2},GeranCellRelation={1}")


class ENMCLI0708Flow(GenericFlow):

    GERAN_ID = ""
    SCHEDULED_TIMES = ""
    GERAN_CELL_PHRASE = "geranCellRelationId :"
    GERAN_CELL_INSTANCE = "1 instance(s)"

    def calculate_scheduled_time(self):
        """
        Function to calculate the scheduled times.
        Profile will run from 8 AM to 8 PM and triggeres total 100 create MO s and 100 delete MOs , where
            -> For the first 11 hours, 2 users create and delete (2 commands per 15 min) : 11 * 8 = 88 create and delete
            -> For the last 12th hour, 2 users create and delete (3 commands per 15 min ): 1 * 12 = 12 create and delete
        """
        start_time = datetime.strptime(self.SCHEDULED_TIMES_STRINGS[0], '%H:%M:%S').replace(year=datetime.now().year,
                                                                                            month=datetime.now().month,
                                                                                            day=datetime.now().day)
        # To schedule one Create and one delete command per each 12 minutes duration
        interval_minutes = [minutes for minutes in xrange(8, 604, 4)]  # Scheduled minutes for 10 hours
        del interval_minutes[2::3]   # Deletes every third instance of list starting from 2nd position element

        self.SCHEDULED_TIMES = [start_time + timedelta(minutes=minutes) for minutes in interval_minutes]
        log.logger.debug("SCHEDULED TIMES - {0}".format(self.SCHEDULED_TIMES))

    def execute_flow(self):
        """
        Executes the flow for the profiles ENMCLI_07 and ENMCLI_08
        """
        self.state = "RUNNING"
        try:
            users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
            create_iteration = True
            self.calculate_scheduled_time()
            command_count = [1, 2]
            nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "node_name", "subnetwork"])
            geran_ids = get_node_gerancell_value(users, nodes)
            while self.keep_running():
                self.sleep_until_time()
                try:
                    command = CLI_LIVE_CREATE_COMMAND if create_iteration else CLI_LIVE_DELETE_COMMAND
                    user_command_data = zip(users, command_count)
                    node_geran_data = zip(nodes, geran_ids)
                    log.logger.debug("{0}".format(user_command_data))
                    log.logger.debug("{0}".format(node_geran_data))
                    self.task_set_serial(user_command_data, node_geran_data, command)
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))
                command_count = command_count if create_iteration else [relation + 2 for relation in command_count]
                create_iteration ^= True
                # change the nodes, and update nodes_list and geran_ids
                if self.DAILY_ITERATION_COUNT_LIMIT in command_count:
                    self.exchange_nodes()
                    nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "node_name", "subnetwork"])
                    geran_ids = get_node_gerancell_value(users, nodes)
                    command_count = [1, 2]
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))

    def check_existence_of_gerancellrelationid(self, user, node, command_count, geran):
        """
        Checks for existence of gerancellrelationid before creation or deletion using CLI_LIVE_GET_COMMAND
        :param user: User object to be used to make requests
        :type user: enm_user_2.User object
        :param node: node on which status should be checked
        :type node: `enm_node.Node`
        :param command_count: gerancellrelationid for which existence should be checked.
        :type command_count: int
        :param geran: geran id for the particular node cell
        :type geran: int
        :return: boolean value which refers to existence of gerancellrelationid for the node
        :rtype: bool
        """
        response = execute_command_on_enm_cli(user, command=CLI_LIVE_GET_COMMAND.format(node.node_name,
                                                                                        command_count, str(geran),
                                                                                        node.subnetwork),
                                              timeout=600)
        output = response.get_output()
        return True if re.search(self.GERAN_CELL_PHRASE,
                                 " ".join(output)) and self.GERAN_CELL_INSTANCE in output else False

    def confirm_create_delete_run(self, command, user, node, command_count, geran):
        """
        Checks for existence of gerancellrelationid before creation or deletion
        If gerancellrelationid exists, it skips creation and allows deletion
        If gerancellrelationid doesnot exists, it allows creation and skips deletion
        :param command: checks if it is a creation or deletion
        :type command: str
        :param user: User object to be used to make requests
        :type user: enm_user_2.User object
        :param node: node on which status should be checked
        :type node: `enm_node.Node`
        :param command_count: gerancellrelationid for which existence should be checked.
        :type command_count: int
        :param geran: geran id for the particular node cell
        :type geran: int
        :return: boolean value to proceed/not with creation/deletion
        :rtype: bool
        """
        existence = self.check_existence_of_gerancellrelationid(user, node, command_count, geran)
        if existence is True:
            return False if "create" in command else True
        else:
            return True if "create" in command else False

    def task_set_serial(self, worker, node_geran_data, command):
        """
        UI Flow to be used to run this profile

        :param worker: A tuple with user_data and command_count included
        :type worker: tuple
        :param node_geran_data: A tuple with `lib.enm_node.Node` instances and geran ids included
        :type node_geran_data: tuple
        :param command: Command to be executed on cli
        :type command: str

        :raises EnmApplicationError: raised if execution in cli fails
        """
        for node_geran in node_geran_data:
            node, geran = node_geran
            for user_data in worker:
                user, command_count = user_data
                try:
                    if self.confirm_create_delete_run(command, user, node, command_count, geran):
                        execute_command_on_enm_cli(user, command=command.format(node.node_name, command_count,
                                                                                str(geran), node.subnetwork),
                                                   timeout=600)
                        log.logger.debug(
                            "Sleeping for {0} seconds in between commands".format(self.SLEEP_TIME_BETWEEN_COMMANDS))
                        sleep(self.SLEEP_TIME_BETWEEN_COMMANDS)
                    else:
                        log.logger.debug("Skipping the command run '{0}'".format(command.format(node.node_name,
                                                                                                command_count,
                                                                                                str(geran),
                                                                                                node.subnetwork)))
                except Exception as e:
                    raise EnmApplicationError(e)
