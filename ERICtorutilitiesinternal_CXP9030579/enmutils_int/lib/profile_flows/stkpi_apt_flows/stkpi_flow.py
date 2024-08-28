from enmutils.lib import log, persistence
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib import assertions_utils
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services import nodemanager_adaptor


class STKPIFlow(GenericFlow):
    """
    Executes STKPI profile flow
    """
    ALL_NODES = []

    def execute_flow(self):
        """
        Executes the profile flow
        """
        self.state = "RUNNING"
        assertion_values = assertions_utils.AssertionValues(self.NAME)
        # When started on restricted deployments such as transport only, the basic is not loaded.
        setattr(self, 'EXCLUSIVE', True)

        try:
            all_keys = persistence.get_all_keys()
            self.check_nodes_present_in_persistence_db(all_keys)
            nodes = self.get_nodes_list_by_attribute()
            assertion_values.update(nodes)
            self.teardown_list.append(assertion_values)
            log.logger.debug("DEFAULT_NODES: {0}".format(self.DEFAULT_NODES))
            self.get_ran_core_nodes()
            self.get_transport_nodes()
        except AttributeError as e:
            self.add_error_as_exception(EnvironError(str(e)))
        except Exception as adding_profile_to_node:
            self.add_error_as_exception(adding_profile_to_node)

    def check_nodes_present_in_persistence_db(self, all_keys):
        """
        Checks the nodes are present in persistence.
        The name of each node
        :param all_keys:
        :type all_keys: list
        :raises ValueError: if the node is not found in persistence
        """
        for node_type in self.DEFAULT_NODES:
            for node_name in self.DEFAULT_NODES[node_type]:
                if node_name in all_keys:
                    node_obj = persistence.get(node_name)
                    self.ALL_NODES.append(node_obj)
                else:
                    raise ValueError("Default node {node_name} was not found in persistence"
                                     .format(node_name=node_name))
        self.add_nodes_to_profile()

    def add_nodes_to_profile(self):
        """
        Allocate nodes to profile and make them exclusive
        """
        if not nodemanager_adaptor.can_service_be_used(self):
            for node_object in self.ALL_NODES:
                node_object.add_profile(self)
        else:
            nodemanager_adaptor.allocate_nodes(self, nodes=self.ALL_NODES)
        for node_object in self.ALL_NODES:
            node_object._is_exclusive = True

    def get_ran_core_nodes(self):
        """
        Gets all the ERBS, SGSN and Radionodes from the config file
        :raises EnvironError: when both ERBS and RadioNode are passed in config file
        """
        if 'ERBS' in self.DEFAULT_NODES and 'RadioNode' in self.DEFAULT_NODES:
            raise EnvironError("Profile is configured with both ERBS and RadioNode! "
                               "Please configure the profile with only ERBS or RadioNode")
        if ('ERBS' in self.DEFAULT_NODES or 'RadioNode' in self.DEFAULT_NODES) and 'SGSN' in self.DEFAULT_NODES:
            ran_core_nodes = []
            if 'ERBS' in self.DEFAULT_NODES:
                erbs_nodes = self.DEFAULT_NODES['ERBS'][:1]
                self.add_nodes_to_list_to_print(erbs_nodes, ran_core_nodes)
            if 'RadioNode' in self.DEFAULT_NODES:
                radio_nodes = self.DEFAULT_NODES['RadioNode'][:1]
                self.add_nodes_to_list_to_print(radio_nodes, ran_core_nodes)
            sgsn_nodes = self.DEFAULT_NODES['SGSN'][:3]
            self.add_nodes_to_list_to_print(sgsn_nodes, ran_core_nodes)

            log.logger.debug("Ran Core Nodes used by APT: {0}".format(ran_core_nodes))

    def get_transport_nodes(self):
        """
        Gets all the MINILINK_6352 and ROUTER_6672 described in the config file
        """
        if 'MINILINK_Indoor' in self.DEFAULT_NODES and 'ROUTER_6000' in self.DEFAULT_NODES:
            minilink_indoor_nodes = self.DEFAULT_NODES['MINILINK_Indoor'][:3]
            router_6000_nodes = self.DEFAULT_NODES['ROUTER_6000'][:1]
            transport_nodes = []
            self.add_nodes_to_list_to_print(minilink_indoor_nodes, transport_nodes)
            self.add_nodes_to_list_to_print(router_6000_nodes, transport_nodes)

            log.logger.debug("APT Transport Nodes used: {0}".format(transport_nodes))

    @staticmethod
    def add_nodes_to_list_to_print(nodes, node_list):
        """
        Add the nodes which were ring fenced to a list which will be printed into a log.
        This allows an APT_01 user to find out which nodes were ring fenced.
        :param nodes:
        :type nodes: list
        :param node_list:
        :type node_list: list
        """
        for node in nodes:
            node_list.append(node)
