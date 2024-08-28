from requests.exceptions import HTTPError, ConnectionError

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.load_mgr import wait_for_setup_profile
from enmutils_int.lib.load_node import filter_nodes_having_poid_set
from enmutils_int.lib.netex import Collection
from enmutils_int.lib.netview import get_physical_links_on_nodes_by_rest_call, get_plm_dynamic_content
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class Netview02Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the main profile flow
        """
        wait_for_setup_profile("PLM_01", state_to_wait_for="SLEEPING", timeout_mins=30)
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        collection_name = "{0}_collection".format(self.NAME)
        collection = Collection(user=user, name=collection_name, num_results=0)
        self.teardown_list.append(collection)
        self.state = "RUNNING"
        all_nodes = self.all_nodes_in_workload_pool(node_attributes=["node_id", "poid"])

        while self.keep_running():
            self.sleep_until_time()
            poids = []

            try:
                node_ids = get_plm_dynamic_content()
            except Exception as e:
                self.add_error_as_exception(e)
            else:
                poids = self._get_poids(all_nodes, node_ids)

            if poids:

                self._create_collection(collection, poids)

                try:
                    get_physical_links_on_nodes_by_rest_call(user, poids)

                except (HTTPError, ConnectionError, EnvironError) as e:
                    self.add_error_as_exception(EnvironError("Rest Call to get physical links failed with following"
                                                             " message {0}".format(e.message)))
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError("Exception occurred while fetching "
                                                                    "links, error : {0}".format(e.message)))

    def _get_poids(self, all_nodes, node_ids):
        """
        Function to get poid of the nodes and reduce number of nodes
        :return values: List of node poids
        :type : list
        """
        number_of_nodes = getattr(self, 'NUMBER_OF_NODES', 0)
        ids = node_ids[:number_of_nodes]
        log.logger.info("{0} nodes selected : {1}".format((len(ids)), ids))
        valid_nodes = [node for node in all_nodes if node.node_id in ids]
        poids = [node.poid for node in filter_nodes_having_poid_set(valid_nodes)]
        log.logger.info("Found {0} POID's for {1} nodes".format((len(poids)), number_of_nodes))
        if len(poids) != number_of_nodes:
            self.add_error_as_exception(EnvironError("Selected nodes have not been populated with POID data"))
        return poids

    def _create_collection(self, collection_obj, node_poids):
        """
        Function to create and update the collection.
        :param collection_obj: Object used to access the Collection class.
        :type collection_obj: object
        :param node_poids: List of node PO IDs
        :type node_poids: list
        """
        try:
            if collection_obj.exists:
                collection_obj.delete()
            collection_obj.create()
            collection_obj.update_collection(node_poids=node_poids)
        except Exception as e:
            self.add_error_as_exception(EnvironError("Profile could not create the collection"
                                                     " Error Message: {0}".format(e.message)))
