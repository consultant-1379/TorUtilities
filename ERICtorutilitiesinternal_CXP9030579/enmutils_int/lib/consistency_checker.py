# ********************************************************************
# Name    : Consistency Checker
# Summary : Module used by the Consistency tool.
#           Allows the tool to query the existing workload pool, to
#           compare pool values versus ENM NE values, and can also
#           check for nodes within the pool.
# ********************************************************************

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.node_pool_mgr import get_pool


class ConsistencyChecker(object):

    ALL_NODES_CMD = 'cmedit get * NetworkElement'

    @property
    def all_nodes(self):
        """
        Property for the workload pool node
        :return: Persisted pool nodes or empty list
        :rtype: list
        """
        return get_pool().nodes or []

    @property
    def pool_dict(self):
        """
        Property which returns a dictionary based upon the all_nodes value
        :return: Dict of the pool nodes
        :rtype: dict
        """
        nodes = self.all_nodes
        return {node.primary_type: [node for node in nodes] for node in nodes}

    def get_enm_nodes_list(self, user=None):
        """
        Retrieves any and all, network elements currently created on the ENM deployment

        :type user: `enm_user_2.User` instance
        :param user: Enm user instance who will execute the command

        :raises EnmApplicationError: raised if there is no response from ENM

        :rtype: `shell.Response.json`
        :return: Stdout of the command execution decoded to a python object

        """
        user = user or get_workload_admin_user()
        response = user.enm_execute(self.ALL_NODES_CMD)
        if not response:
            raise EnmApplicationError('Failed to retrieve network elements from ENM.')
        else:
            return response.get_output()

    def filter_enm_nodes_list(self):
        """
        Filter the response from enm into a usable set of node ids

        :rtype: set
        :return: Set of `enm_node.Node`.node_ids
        """
        return {line.split('=')[-1].encode('utf-8') for line in self.get_enm_nodes_list() if 'instance' not in line and line.split('=')[-1].encode('utf-8') is not None and line.split('=')[-1].encode('utf-8') != ''}

    def pool_is_consistent_with_enm(self):
        """
        Compares the pool against the nodes created on ENM


        """
        enm_nodes = self.filter_enm_nodes_list()
        pool_nodes = set([node.node_id for node in self.all_nodes if 'AP_01' not in node.profiles])
        return self._check_pool_consistency(pool_nodes, enm_nodes)

    def enm_is_consistent_with_pool(self):
        """
        Compares ENM nodes against the nodes in the pool

        :return: Difference between enm and the workload pool
        :rtype: list
        """
        enm_nodes = self.filter_enm_nodes_list()
        pool_nodes = set([node.node_id for node in self.all_nodes])
        return self._check_pool_consistency(enm_nodes, pool_nodes)

    @staticmethod
    def _check_pool_consistency(pool, target_pool):
        """
        Compares one set against another, taking into account the NULL set

        :type pool: set
        :param pool: Set representing the identifiable objects within a pool
        :type target_pool: set
        :param target_pool: Set representing the identifiable objects within the comparative pool

        :return: Difference between two sets
        :rtype: list
        """
        if len(pool) is 0:
            log.logger.debug("Consistency check successful, no nodes found in pool, pool may be empty.")
            return []
        elif pool.issubset(target_pool):
            return []
        else:
            return pool.difference(target_pool)

    def get_all_unused_nodes(self, netype=None):
        """
        Retrieves all currently unused nodes in the workload pool

        :type netype: str
        :param netype: Optional value to refine the nodes based on primary type

        :rtype: list
        :return: List of `enm_node.Node` instances
        """
        if netype:
            return [node for node in self.all_nodes if len(node.profiles) is 0 and node.primary_type == netype]
        return [node for node in self.all_nodes if len(node.profiles) is 0]
