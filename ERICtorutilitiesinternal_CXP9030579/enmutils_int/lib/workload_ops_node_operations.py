# ********************************************************************
# Name    : Workload Ops Node Operations
# Summary : Core functionality of the workload tool. Responsible for
#           node operations such as add, remove and reset.
# ********************************************************************

import os

from enmutils.lib import filesystem, arguments, config, log
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services import nodemanager_adaptor
from enmutils_int.lib.services.nodemanager_helper_methods import reset_nodes, update_total_node_count

NSS_UTILS_NODE_DIR = os.path.join('/opt', 'ericsson', 'nssutils', 'etc', 'nodes')


class NodesOperation(object):

    def __init__(self, argument_dict):
        """
        Operation object for removing nodes from workload pool.

        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        """
        self.nodes_file_identifier = argument_dict['IDENTIFIER']
        self.nodes_range = argument_dict.pop('RANGE', None)
        self.nodes_file_path = None
        self.range_start = None
        self.range_end = None
        self.deleted = []
        self.missing = []
        self.total_nodes = 0
        self.can_service_be_used = nodemanager_adaptor.can_service_be_used()
        self.no_ansi = argument_dict.get('--no-ansi')

    def _validate(self):
        """
        validates the existence of node data file
        """
        if not isinstance(self, AddNodesOperation) and self.nodes_file_identifier == "all":
            self.nodes_file_path = "all"
        else:
            self.set_file_path_and_numeric_range()

    def execute(self):
        """
        Execute the internal execute_operation function
        """
        self._validate()
        self._execute_operation()

    def _execute_operation(self):
        """
        Raises not implemented
        """

    def calculate_num_items(self, succeeded, failed):
        """
        Calculate the total number of items supplied to the node operation

        :param succeeded: List of successful operation nodes
        :type succeeded: list
        :param failed: List of failed operation nodes
        :type failed: list

        :return: Total number of items supplied to the node operation
        :rtype: int
        """
        if self.range_start and self.range_end:
            num_items = int(self.range_end) - int(self.range_start) + 1
        else:
            num_items = len(succeeded) + len(failed)
        return num_items

    def set_file_path_and_numeric_range(self):
        """
        Set file path to be used and the start/end range

        :raises RuntimeError: raised if the file is not found
        """
        self.nodes_file_path = self.get_parsed_file_location()
        if not filesystem.does_file_exist(self.nodes_file_path):
            raise RuntimeError("Could not find node data file {0}; please run the node populator tool and the"
                               " parse operation first.".format(self.nodes_file_path))
        if self.nodes_range:
            self.range_start, self.range_end = arguments.get_numeric_range(self.nodes_range)

    def get_parsed_file_location(self):
        """
        Check if the parsed file is in the NSSUtils directory or in ENMUtils

        :return: Path to the parsed file
        :rtype: str
        """
        nssutils_path = os.path.join(NSS_UTILS_NODE_DIR, self.nodes_file_identifier.split('/')[-1])
        enmutils_path = os.path.join(config.get_nodes_data_dir(), self.nodes_file_identifier)
        if filesystem.does_file_exist(enmutils_path) and not filesystem.does_file_exist(nssutils_path):
            return enmutils_path
        return nssutils_path

    def _print_add_removed_summary(self, num_items, action="REMOVED"):
        """
        Prints a summary of the nodes add/removed

        :param num_items: the number of items removed successfully
        :type num_items: int
        :param action: Node action being performed
        :type action: str
        """
        message = ["\nNODE MANAGER SUMMARY\n--------------------\n",
                   "  NODES {3}: {0}/{1}\n  NODE POOL SIZE: {2}\n".format(
                       str(len(self.added if hasattr(self, "added") else self.deleted)), str(num_items),
                       self.total_nodes, action)]
        log.logger.info(log.purple_text(message[0]))
        log.logger.info(log.cyan_text(message[1]))

    def _print_failed_summary(self):
        """
        Prints a summary of the nodes that were not removed
        """
        message = ["FAILED NODES\n------------", "\nNOTE: The list of nodes below could not be removed because they "
                                                 "are not in the pool.\n{0}".format(",".join(self.missing))]
        log.logger.info(log.purple_text(message[0]))
        log.logger.warn(message[1])


class RemoveNodesOperation(NodesOperation):

    def __init__(self, argument_dict):
        """
        Operation object for removing nodes from workload pool.

        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        """

        super(RemoveNodesOperation, self).__init__(argument_dict)
        self.force = argument_dict.pop('--force', None)
        self.allocated = []

    def _execute_operation(self):
        """
        Removes nodes from the workload pool
        """
        if self.can_service_be_used:
            nodemanager_adaptor.remove_nodes({"IDENTIFIER": self.get_parsed_file_location(),
                                              "RANGE": self.nodes_range, "force": self.force})
        else:
            still_running_msg = ("\nCould not remove all nodes from the workload pool as some profiles are still "
                                 "running.\nIf all profiles are stopped, execute ./workload reset and retry the remove "
                                 "command.")
            if self.nodes_file_path == "all":
                result = node_pool_mgr.remove_all(force=self.force)
                if result:
                    self.total_nodes = update_total_node_count(update=False)
                    all_nodes_removed = "\n  All {0} nodes removed from the pool\n".format(self.total_nodes)
                    log.logger.info(log.cyan_text(all_nodes_removed))
                    self.total_nodes = update_total_node_count()
                else:
                    log.logger.error(still_running_msg)
            else:
                self.deleted, self.missing, self.allocated = node_pool_mgr.remove(self.nodes_file_path,
                                                                                  self.range_start, self.range_end,
                                                                                  force=self.force)
                self.total_nodes = update_total_node_count()
                num_items = self.calculate_num_items(self.deleted, self.missing)
                self._print_add_removed_summary(num_items)
                if self.allocated:
                    log.logger.error(still_running_msg)
                if self.missing:
                    self._print_failed_summary()


class AddNodesOperation(NodesOperation):

    def __init__(self, argument_dict):
        """
        Operation object which adds nodes to the workload pool

        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        """

        super(AddNodesOperation, self).__init__(argument_dict=argument_dict)
        self.validate = argument_dict.pop('--validate', False)
        self.added = []
        self.not_added = []
        self.missing_nodes = {}

    def _execute_operation(self):
        """
        Adds nodes to the workload pool
        """
        log.logger.info(log.cyan_text("\nStarting node add operation, please ensure your nodes are created and "
                                      "managed by ENM to ensure node value accuracy."))
        if self.can_service_be_used:
            nodemanager_adaptor.add_nodes({"IDENTIFIER": self.get_parsed_file_location(),
                                           "RANGE": self.nodes_range})
        else:
            try:
                self.added, self.missing_nodes = node_pool_mgr.add(self.nodes_file_path, self.range_start,
                                                                   self.range_end, validate=self.validate)
                for errored in self.missing_nodes.values():
                    self.not_added.extend(errored)
                self.total_nodes = update_total_node_count()

                num_items = self.calculate_num_items(self.added, self.not_added)
                self._print_add_removed_summary(num_items, action="ADDED")

                if self.not_added:
                    self._print_failed_summary()
            finally:
                self.total_nodes = update_total_node_count(update=bool(self.added))
                if self.added:
                    try:
                        GenericFlow().update_nodes_with_poid_info()
                    except Exception as e:
                        log.logger.info(str(e))

    def _print_failed_summary(self):
        """
        Prints the summary of the nodes that were already in the pool
        """
        base_msg = "\nNOTE: The list of nodes below were not added because they are {0}\n"
        keys = ["NOT_ADDED", "NOT_SYNCED", "MISSING_PRIMARY_TYPE", "ALREADY_IN_POOL"]
        reasons = ["not created on ENM.", "not synced.", "not supported by the workload pool.", "already in the pool."]
        for key, reason in zip(keys, reasons):
            if self.missing_nodes[key]:
                log.logger.info(log.purple_text(base_msg.format(reason)))
                log.logger.warn(",".join(self.missing_nodes[key]))


class ResetNodesOperation(object):

    def __init__(self, argument_dict):
        """
        Operation object for resetting nodes from workload pool.

        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        """
        self.reset_network_values = argument_dict['--network-values']
        self.no_ansi = argument_dict.get('--no-ansi')

    def execute(self):
        """
        Resets all nodes in the workload pool to their initial state
        """
        if nodemanager_adaptor.can_service_be_used():
            log.logger.debug("Using nodemanager services for node reset operation.")
            nodemanager_adaptor.reset_nodes(reset_network_values=self.reset_network_values, no_ansi=self.no_ansi)
        else:
            log.logger.info(reset_nodes(reset_network_values=self.reset_network_values, no_ansi=self.no_ansi))


# Replace once workload ops is restructured and circular imports are not an issue RTD-5544
def get_workload_operations(operation_type, argument_dict):
    """
    Returns the workload operation object.

    :param operation_type: the operation to be executed
    :type operation_type: str
    :param argument_dict: argument dictionary with user input.
    :type argument_dict: dict

    :return: WorkloadOperation object
    :rtype: workload_ops.WorkloadOperations
    """

    operations_classes = {
        "add": {"operation": AddNodesOperation, "kwargs": {'argument_dict': argument_dict}},
        "remove": {"operation": RemoveNodesOperation, "kwargs": {'argument_dict': argument_dict}},
        "reset": {"operation": ResetNodesOperation, "kwargs": {'argument_dict': argument_dict}},
    }
    return operations_classes[operation_type]["operation"](**operations_classes[operation_type]["kwargs"])
