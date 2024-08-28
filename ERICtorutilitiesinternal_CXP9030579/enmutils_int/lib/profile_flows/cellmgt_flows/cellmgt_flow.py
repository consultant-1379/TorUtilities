# ********************************************************************
# Name    : Cellmgt Flow
# Summary : This is a series of CellMgt profile flows.
# ********************************************************************

import time
from functools import partial

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib import cellmgt, node_pool_mgr, common_utils
from enmutils_int.lib.cellmgt import (populate_node_cell_data, revert_cell_attributes, get_cell_name,
                                      update_cells_attributes_via_cell_management,
                                      DEFAULT, NEW, create_list_of_node_poids,
                                      fetch_cell_fdns_for_specified_poid_list_via_cell_mgt)
from enmutils_int.lib.cell_management import RncCreateDeleteCells, ERBSCreateDeleteCells
from enmutils_int.lib.network_mo_info import group_mos_by_node
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from requests.exceptions import RequestException
from retrying import retry


class ViewAllLteCellsInTheNetwork(GenericFlow):

    def execute_flow(self):
        """
        Read all cells in Network using Cell Management Northbound REST Interface
        """
        user = self.create_profile_users(1, self.USER_ROLES)[0]
        nodes = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'lte_cell_type', 'poid'])
        poid_data = cellmgt.create_list_of_node_poids(user, nodes)

        if poid_data:
            self.state = 'RUNNING'

            while self.keep_running():
                cell_data = []  # clearing cell data after every iteration
                try:
                    cell_data = cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(user, poid_data)
                except Exception as e:
                    self.add_error_as_exception(e)

                if cell_data:
                    log.logger.debug("Total number of cells returned is: {}".format(len(cell_data)))
                    log.logger.debug("{0} ... {1}".format(cell_data[0:10], cell_data[-10:]))
                else:
                    log.logger.debug("Unexpected situation - no cells were returned from ENM - "
                                     "Check profile log file for more details")

                self.sleep()

        else:
            self.add_error_as_exception(EnvironError("Restart the profile as the poid data available"))


class CreateAndDeleteCells(GenericFlow):
    FAILED_CREATES = []

    def create_target_gsm_cgi_proxy_object(self, connected_msc, num_to_create=1):
        """
        Generate the required dictionary(ies) to send as REST request as target fdn in create create operations

        :param connected_msc: Name of the MSC the source FDN is connected to
        :type connected_msc: str
        :param num_to_create: Number of CGI
        :type num_to_create: int

        :return: List of dictionary(ies) to send as REST request as target fdn in create create operations
        :rtype: list
        """
        target_cgi_values = []
        log.logger.debug("Starting creation of CGI dictionary for target sources nodes.")
        for _ in xrange(num_to_create):
            reserved_cgi = {}
            reserved_cgi.update(self.RESERVED_CGI_VALUE)
            _ += self.MO_ID_START_RANGE
            reserved_cgi.update({"cellIdentity": _})
            target_cgi_values.append({
                "frequency": "6",
                "cellGlobalIdentity": reserved_cgi,
                "attributes": {
                    "ExternalGeranCell": {
                        "externalGeranCellId": "{0}".format(_),
                        "cSysType": "GSM900",
                        "ncc": "1"
                    }
                },
                "targetMscId": connected_msc
            })
        log.logger.debug("Completed creation of CGI dictionary for target sources nodes.\nCreated {0} cgi target "
                         "sources.".format(len(target_cgi_values)))
        return target_cgi_values

    def generate_resources_for_create_delete(self, sorted_fdns, synced, users):
        """
        Build the zipped objects to be supplied to the threads

        :param sorted_fdns: List of sorted FDNs which can be used by the profile
        :type sorted_fdns: list
        :param synced: List of synchronised nodes allocated to the profile
        :type synced: list
        :param users: List of `enm_user_2.User` instances
        :type users: list

        :return: Tuple containing the zipped objects to be supplied to the threads, and the matched nodes list
        :rtype: tuple
        """
        fdn_tuples = []
        grouped_fdns = group_mos_by_node(sorted_fdns)
        matched_nodes = self.get_nodes_with_fdn_result(synced, grouped_fdns.keys())
        fdns_for_nodes = self.get_fdn_for_nodes(matched_nodes, grouped_fdns)
        for source_fdns in fdns_for_nodes:
            connected_msc = source_fdns[0].split("ManagedElement=")[-1].split("BSC")[0]
            fdn_tuples.append((source_fdns, self.create_target_gsm_cgi_proxy_object(
                connected_msc, num_to_create=self.NUM_CELLS_PER_USER)))
        return zip(users[:len(matched_nodes)], fdn_tuples), matched_nodes

    @staticmethod
    def get_nodes_with_fdn_result(nodes, list_of_fdn_keys):
        """
        Check for a matching FDN value or remove the node from usage

        :param nodes: List of nodes to be matched to a FDN value
        :type nodes: list
        :param list_of_fdn_keys: List of FDN key results from ENM
        :type list_of_fdn_keys: list

        :return: List of nodes to be grouped by the connected_msc
        :rtype: list
        """
        log.logger.debug("Checking supplied nodes, for matching FDN value.")
        nodes_in_fdn = [node for node in nodes if node.node_id in list_of_fdn_keys]
        unmatched = set(nodes).difference(nodes_in_fdn)
        if unmatched:
            log.logger.debug("Failed to match {0} nodes to supplied list of FDNs, nodes will be removed."
                             .format(len(unmatched)))
        log.logger.debug("Returning a total of {0} matched nodes.".format(len(nodes_in_fdn)))
        return nodes_in_fdn

    def get_fdn_for_nodes(self, nodes, fdns):
        """
        Retrieve a FDN value for each node in the grouped node lists

        :param nodes: List of nodes
        :type nodes: list
        :param fdns: Dictionary of FDN results from ENM, sorted by node id
        :type fdns: dict

        :return: List of list, each containing two or more fdns
        :rtype: list
        """
        log.logger.debug("Starting matching of nodes to a FDN value.")
        node_fdns = []
        for node in nodes:
            try:
                node_fdns.append(fdns.get(node.node_id)[:self.NUM_CELLS_PER_USER])
            except TypeError as e:
                self.add_error_as_exception(e)
        log.logger.debug("Successfully completed matching of nodes to a FDN value, returning")
        return node_fdns

    @retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_fixed=300000,
           stop_max_attempt_number=3)
    def get_gsm_relation_info(self, user, fdn_list, direction="OUTGOING", relation="ExternalGeranCellRelation"):
        """
        Retrieve the requested GSM relation(s)

        :param user: User who will perform the query
        :type user: `enm_user_2.User`
        :param fdn_list: List of FDNS to use in the view query
        :type fdn_list: list
        :param direction: Direction of the relation between the two nodes: INCOMING/OUTGOING
        :type direction: str
        :param relation: GSM Relation to view
        :type relation: str
        :raises EnmApplicationError: If no relations retrieved for provided list of FDNs
        :return: List containing information about the GSM relations
        :rtype: list
        """
        log.logger.debug("Retrieving cell relation data.")
        successful_mos = []
        fdn_chunks = common_utils.chunks(fdn_list, 500)
        for fdn_chunk in fdn_chunks:
            relation_to_view = (direction, 'readRelations', 'GSM', relation)
            user_node_data = (user, fdn_chunk)
            try:
                response = cellmgt.get_cell_relations(user_node_data, relation_to_view)
                if not response.json().get("successfulMoOperations") and response.json().get("failedMoOperations"):
                    self.add_error_as_exception(
                        EnvironError("Failed to retrieve some relation information.\nResponse: {0}"
                                     .format(response.json())))
                    continue
                successful_mos.extend(response.json().get("successfulMoOperations"))

            except Exception as e:
                self.add_error_as_exception(EnmApplicationError("REST request has failed, response: [{0}]"
                                                                .format(str(e))))
                log.logger.debug("Waiting for 30 seconds before attempting next request, as previous has failed.")
                time.sleep(30)

        if not successful_mos:
            raise EnmApplicationError("Profile could not retrieve any cell relations. "
                                      "See profile log file for more details.")

        log.logger.debug("Successfully retrieved cell relation data.")
        return successful_mos

    @staticmethod
    def cmedit_clean_up(fdn, user, delete_all=True):
        """
        Cleans up leftover cell relations from previous profile run.
        :param fdn: str of relation FDNs to delete.
        :type fdn: str
        :param user: User who will execute cmedit command
        :type user: `enm_user_2.User`
        :param delete_all: Flag to delete all children MOs
        :type delete_all: bool
        :return: Relation deleted successfully
        :rtype: bool
        """
        cmd = "cmedit delete {0} --all" if delete_all else "cmedit delete {0}"
        try:
            user.enm_execute(cmd.format(fdn))
            return True
        except Exception as e:
            log.logger.debug("Failed to delete {0}: {1}".format(fdn, e.message))

    def validate_gsm_relations(self, user, gsm_relation_data):
        """
        Removes and deletes any existing relations that are in a reserved cgi range.
        :param gsm_relation_data: List of dicts containing relation data.
        :type gsm_relation_data: list of dict
        :param user: User who will execute cmedit command
        :type user: `enm_user_2.User`
        :return: : list of dicts with deleted relations removed.
        :rtype: list of dict
        """
        log.logger.debug("Validating relations")
        for relation in gsm_relation_data[:]:
            if relation.get("targetCellGlobalIdentity"):
                cgi = relation.get("targetCellGlobalIdentity")
                log.logger.debug("Relation has CGI value: {}".format(cgi))
                if self.check_cgi_in_reserved_range(cgi):
                    relation_fdn = relation.get('relationFdn')
                    log.logger.debug("Relation {0} left from previous profile run.".format(
                        relation.get('relationFdn')))
                    if self.cmedit_clean_up(relation_fdn, user):
                        gsm_relation_data.remove(relation)

        return gsm_relation_data

    def check_cgi_in_reserved_range(self, cgi):
        """
        Checks if the cgi is in a reserved range.
        :param cgi:
        :type cgi: dict
        :return: bool to indicate if cgi is in reserved range
        :rtype: bool
        """
        cgi.pop("cellIdentity")
        if cgi == self.RESERVED_CGI_VALUE:
            return True

    def clean_up_failed_creates(self, user, failed_creates):
        """
        Clean up any potential left behind cells.
        :param user: ENM user.
        :type user: `enm_user_2.User`
        :param failed_creates: List of Cells that may have failed relation creates
        :type failed_creates: list
        """
        source_cells = list(set(failed_creates))
        node_fdns = list(set([cell.split(",ManagedElement")[0] for cell in source_cells]))
        try:
            relation_data = self.get_gsm_relation_info(user, source_cells)
            self.validate_gsm_relations(user, relation_data)
        except EnmApplicationError as e:
            log.logger.debug("Failed to ensure all relations were deleted: {0}".format(e.message))

        self.clean_up_external_geran_cells(user, node_fdns)

    def clean_up_external_geran_cells(self, user, node_fdns):
        """
        Cleans up any left over ExternalGeranCell's
        :param user: ENM user
        :type user: `enm_user_2.User`
        :param node_fdns: list of node fdns
        :type node_fdns: list
        """

        for node_fdn in node_fdns:
            try:
                cmd = "cmedit get {0} ExternalGeranCell.cgi".format(node_fdn)
                response = user.enm_execute(cmd.format(node_fdn))
                output = response.get_output()
                for i, line in enumerate(output):
                    if i + 1 < len(output) and "FDN" in line and 'cgi' in output[i + 1]:
                        fdn = line.split(" : ")[-1]
                        cgi = output[i + 1].split(" : ")[-1]
                        cgi = [int(num) for num in cgi.split("-")][:-1]
                        cgi = {"mnc": cgi[0], "mcc": cgi[1], "lac": cgi[2]}
                        if cgi == self.RESERVED_CGI_VALUE:
                            log.logger.debug("External cell found with reserved CGI  value: {0}".format(fdn))
                            self.cmedit_clean_up(fdn, user)
            except Exception as e:
                log.logger.debug("Could not verify the clean up of cells for {0} due to {1}".format(
                    node_fdn, e.message))

    @staticmethod
    def get_cell_relation_cardinality(relations):
        """
        Counts the number of relations for each cell.
        :param relations: List containing information about the supplied GSM relations
        :type relations: list

        dict = {
            "Node1":{"Cell1" : 5, "Cell2": 10},
            "Node2":{"Cell1" : 11, "Cell2": 20}
        }

        :return: dict containing cardinality values for each source cell
        :rtype: dict
        """
        node_relations = {}
        for relation in relations:
            source_fdn = relation.get("sourceFdn")
            source_node = source_fdn.split("ManagedElement=")[1].split(",BscFunction")[0]
            source_cell = source_fdn.split("GeranCell=")[1]
            if source_node not in node_relations.iterkeys():
                node_relations[source_node] = {}
            if source_cell not in node_relations[source_node].iterkeys():
                node_relations[source_node][source_cell] = 0

            node_relations[source_node][source_cell] += 1

        return node_relations

    def remove_invalid_cardinality_cells(self, user, fdn_list):
        """
        Detect and remove any existing cells already at the maximum cardinality

        :param user: User who will perform the query
        :type user: `enm_user_2.User`
        :param fdn_list: List of FDNS to use in the view query
        :type fdn_list: list
        :raises e: (EnmApplicationError) if no relation info could be fetched.
        :return: Updated list of FDNs after the removal of any FDN already at max cardinality
        :rtype: list
        """
        log.logger.debug("Removing cells with maximum cell relation cardinality.")
        try:
            gsm_relation_data = self.get_gsm_relation_info(user, fdn_list)
        except EnmApplicationError as e:
            log.logger.debug("No cells to check cardinality values.")
            raise e
        validated_relation_data = self.validate_gsm_relations(user, gsm_relation_data)

        exceed_list = self.get_max_cardinality_cells(self.get_cell_relation_cardinality(validated_relation_data))
        log.logger.debug("\n\nTotal FDNs before removal [{0}]\nTotal Max Cardinality Cells [{1}]"
                         .format(len(fdn_list), len(exceed_list)))
        if exceed_list:
            for exceeded in exceed_list:
                node, cell = exceeded
                for fdn in fdn_list[:]:
                    if node in fdn and cell in fdn:
                        log.logger.debug("Removing unusable cell FDN: {0}".format(fdn))
                        fdn_list.remove(fdn)
            log.logger.debug("\n\nTotal FDNs after removal [{0}].".format(len(fdn_list)))
        log.logger.debug("Successfully removed cells with maximum cell relation cardinality.")
        return fdn_list

    @staticmethod
    def get_max_cardinality_cells(cell_cardinality, max_cardinality=64):
        """
        Query the supplied cell relation structure for the total relations under each cell

        :param cell_cardinality:  Dictionary containing sorted information about the supplied GSM relations
        :type cell_cardinality: dict
        :param max_cardinality: The maximum allowable cardinality for each cell
        :type max_cardinality: int

        :return: List of tuples, containing any node and cell which exceed the max cardinality
        :rtype: list
        """
        log.logger.debug("Determining cells with maximum cell relation cardinality.")
        exceeds = []
        for node, value in cell_cardinality.iteritems():
            for cell_key, cardinality in value.iteritems():
                if cardinality >= max_cardinality:
                    exceeds.append((node, cell_key))
        log.logger.debug("Successfully determined cells with maximum cell relation cardinality.")
        return exceeds

    def determine_usable_node_fdns(self, user, nodes, standard, cell_type, sleep_time=120):
        """
        Query ENM to determine the FDN for the supplied nodes, removing any with maximum cardinality reached.
        The profile cannot continue until usable fdns have been found.

        :param user: User who will perform the query
        :type user:`enm_user_2.User`
        :param nodes: List nodes allocated to the profile
        :type nodes: list
        :param standard: Technology standard to use in the query, for example LTE, GSM
        :type standard: str
        :param cell_type: Type of cell to filter the response upon, for example GeranCell, UtranCell
        :type cell_type: str
        :param sleep_time: time in seconds to sleep if the ENM query fails
        :type sleep_time: int
        :raises EnmApplicationError: If profile has reached max read relation retries.
        :return: List of FDNs which can be used by the profile
        :rtype: list
        """

        log.logger.debug("Querying ENM for node POID and FDN information")
        list_of_fdns = []
        valid_cells = []
        while not list_of_fdns:
            try:
                list_of_node_poids = create_list_of_node_poids(user, nodes)
                list_of_fdns = fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(user, list_of_node_poids,
                                                                                    standard=standard,
                                                                                    cell_type=cell_type)
            except Exception as e:
                self.add_error_as_exception(e)
                log.logger.debug("Failed to correctly fetch resource information, response: [{0}].\nProfile will "
                                 "retry in {1} seconds.".format(str(e), sleep_time))
                time.sleep(sleep_time)
                continue
        log.logger.debug("Completed querying ENM for node POID and FDN information")

        # Remove cells which cannot support further relations
        attempts = 0
        while not valid_cells:
            try:
                valid_cells = self.remove_invalid_cardinality_cells(user, list_of_fdns[:])
            except EnmApplicationError as e:
                attempts += 1
                if attempts == 20:
                    raise EnmApplicationError('Profile has reached max number of attempts({0}) to determine max '
                                              'cardinality cells, likely due to Cell management being unavailable.'
                                              'Please ensure the service is running and restart the profile. '
                                              'See profile logs for more details.'.format(attempts))
                self.add_error_as_exception(e)
                log.logger.debug("The profile cannot progress without valid cells. The profile will retry in "
                                 "{0} seconds.".format(sleep_time))

                time.sleep(sleep_time)
        return valid_cells

    def execute_flow(self):
        """
        Executes the create, delete relation flow
        """
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        nodes_specified_for_use_by_profile = self.get_nodes_list_by_attribute(
            node_attributes=['node_id', 'lte_cell_type', 'poid'])
        self.state = "RUNNING"
        standard = self.STANDARD if hasattr(self, "STANDARD") else None
        cell_type = self.CELL_TYPE if hasattr(self, "CELL_TYPE") else None
        sleep_time = 120
        synced = node_pool_mgr.filter_unsynchronised_nodes(nodes_specified_for_use_by_profile, ne_type="BSC")
        try:
            sorted_fdns = self.determine_usable_node_fdns(users[0], synced, standard, cell_type, sleep_time=300)
        except EnmApplicationError as e:
            self.add_error_as_exception(e)
            log.logger.debug('Profile will now go to COMPLETED state until manual intervention')
            return
        while self.keep_running():
            setattr(self, "RELATIONS_TO_DELETE", [])
            self.sleep_until_time()
            user_node_lists, matched_nodes = self.generate_resources_for_create_delete(sorted_fdns, synced, users)
            if user_node_lists:
                self.create_and_execute_threads(user_node_lists, len(user_node_lists), func_ref=cellmgt.create_flow,
                                                args=[self, self.RELATION_TYPE])
                log.logger.debug("Sleeping for {0} seconds before attempting cell deletion.\nReturned a total {1} "
                                 "created objects.\n".format(sleep_time, len(self.RELATIONS_TO_DELETE)))
                time.sleep(sleep_time)
                grouped_sorted_relations = group_mos_by_node(self.RELATIONS_TO_DELETE)
                user_node_lists = zip(users[:len(matched_nodes)], grouped_sorted_relations.values())
                self.create_and_execute_threads(user_node_lists, len(user_node_lists), func_ref=cellmgt.delete_flow,
                                                args=[self], wait=90 * 60, join=60 * 90)
                if self.FAILED_CREATES:
                    log.logger.debug("Sleeping for {0} seconds before attempting clean-up".format(240))
                    time.sleep(240)
                    self.clean_up_failed_creates(users[0], self.FAILED_CREATES)
            else:
                self.add_error_as_exception(EnvironError("Empty user/node data structure, nothing to do."))


class ReadCellDataForDifferentNodes(GenericFlow):

    def calculate_num_nodes_per_available_user(self, list_of_node_poids):
        """
        Calculate the number of nodes per user

        :param list_of_node_poids: List of poids on ENM
        :type list_of_node_poids: list
        :return: Nodes per user
        :rtype: int
        """
        nodes_per_user = 0
        if self.NUM_USERS and list_of_node_poids:
            nodes_per_user = len(list_of_node_poids) / self.NUM_USERS
        return nodes_per_user or 1

    def execute_flow(self):
        """
        Method to control the flow of events for users reading cell information from ENM

        :return: boolean to indicate if flow was successful or not
        :rtype: bool
        """
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)

        selected_nodes = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'lte_cell_type', 'poid'])
        ui_display_limit = self.UI_DISPLAY_LIMIT
        sleep_time = 120
        user = users[0]
        self.state = "RUNNING"
        standard = self.STANDARD if hasattr(self, "STANDARD") else None
        cell_type = self.CELL_TYPE if hasattr(self, "CELL_TYPE") else None

        if selected_nodes:
            while self.keep_running():
                self.sleep_until_time()

                list_of_node_poids = cellmgt.create_list_of_node_poids(user, selected_nodes)
                if list_of_node_poids:

                    num_of_nodes_per_user = self.calculate_num_nodes_per_available_user(list_of_node_poids)

                    lists_of_node_names_per_user = [list_of_node_poids[i:i + num_of_nodes_per_user]
                                                    for i in range(0, len(list_of_node_poids),
                                                                   num_of_nodes_per_user)]

                    user_node_data = zip(users, lists_of_node_names_per_user)

                    self.create_and_execute_threads(workers=user_node_data, thread_count=len(users),
                                                    func_ref=cellmgt.read_cell_data_ui_flow,
                                                    args=[sleep_time, ui_display_limit, standard, cell_type],
                                                    wait=self.THREAD_QUEUE_TIMEOUT,
                                                    join=self.THREAD_QUEUE_TIMEOUT,
                                                    last_error_only=True)

                else:
                    self.add_error_as_exception(
                        EnvironError('Could not retrieve list of node POIDs, will retry on next iteration.'))

                self.exchange_nodes()
        else:
            self.add_error_as_exception(EnvironError("Failed to get nodes from pool"))
            return False

        return True


class ExecuteModifyCellParameters(GenericFlow):

    def populate_teardown_list(self, node_cell_data):
        """
        This function will populate the teardown list with functions to be called at teardown that will allow all
        the modified cell attributes to be reverted to their default values, so as to leave the network
        back in its original state.

        :param node_cell_data: dictionary of data related to the cells and the particular attributes being changed
        :type node_cell_data: dict
        :raises EnvironError: raises if there is empty data in node cell and if there is null value in node cell
        """

        # Allow the profile to revert all attribute values to DEFAULT ones during profile shutdown:
        cell_counter = 1
        for node_name in node_cell_data:
            for cell_fdn in node_cell_data[node_name]:
                if not node_cell_data[node_name][cell_fdn][DEFAULT]:
                    raise EnvironError("# Unexpected empty attribute data encountered for cell: {0}".format(cell_fdn))

                for attribute in node_cell_data[node_name][cell_fdn][DEFAULT]:
                    if not node_cell_data[node_name][cell_fdn][DEFAULT][attribute]:
                        raise EnvironError(
                            "# Unexpected Null value encountered for attribute: {0} in cell: {1}".format(attribute,
                                                                                                         cell_fdn))
                log.logger.debug(
                    "# Updating teardown list to allow DEFAULT values to be restored to cell {0} ({1}) once profile is stopped".format(
                        get_cell_name(cell_fdn), cell_counter))
                self.teardown_list.append(partial(revert_cell_attributes,
                                                  cell_counter,
                                                  cell_fdn,
                                                  node_cell_data[node_name][cell_fdn][DEFAULT]))
                cell_counter += 1

    def prepare_data_for_use_during_each_iteration(self, user, nodes):
        """
        This function will use a batch of nodes assigned to the profile and from that batch will pick a number of nodes
          having a set number of cells.

        From that selection of nodes, the profile will read the cell attribute values for a predefined list of attributes from
        the cells themselves and populate a dictionary with the relevant node, cell and attribute values.
        It will also calculate the new attributes values which the profile will use to set on the cells themselves.
        These attribute values will also be added to the dictionary.

        :param user: user to be used to query ENM
        :type user: enm_user_2.User
        :param nodes: List of `enm_node.Node` instances
        :type nodes: list

        :return: node_cell_data: dictionary containing nodes, cell fdn's along with default & new attribute values
        :rtype: dict
        :raises RuntimeError: raises when exception is caught
        """
        log.logger.debug("# Node(s) selected for operations: {0}"
                         .format(', '.join(str(node_name) for node_name in nodes)))
        log.logger.debug("# Preparing New Attribute values to be used in main use case. "
                         "New Data is based on Default values read from cells being used")
        node_cell_data = {}
        fdd_nodes = []
        if self.MO_TYPE == "EUtranCellFDD":
            mo_types = list(set(["EUtranCell{0}".format(node.lte_cell_type) for node in nodes if node.lte_cell_type]))
            fdd_nodes = [node for node in nodes if node.lte_cell_type == "FDD"]
            tdd_nodes = [node for node in nodes if node.lte_cell_type == "TDD"]
        else:
            mo_types = [self.MO_TYPE]
            tdd_nodes = nodes
        for mo_type in mo_types:
            mo_nodes = fdd_nodes if mo_type.endswith("FDD") else tdd_nodes
            node_cell_data.update(populate_node_cell_data(user, self.REQUIRED_NUMBER_OF_CELLS_PER_NODE, mo_type,
                                                          mo_nodes, self.MO_ATTRIBUTE_DATA))
        self.populate_teardown_list(node_cell_data)
        return node_cell_data

    def execute_flow(self):
        """
        This function executes the main flow for the Modify Cell parameters use case
        """

        run_type = DEFAULT
        user = self.create_profile_users(1, self.USER_ROLES)[0]
        nodes = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'lte_cell_type'])
        node_cell_data = {}

        try:
            node_cell_data = self.prepare_data_for_use_during_each_iteration(user, nodes)
        except (EnvironError, RequestException) as e:
            self.add_error_as_exception(e)
        if node_cell_data:
            self.state = 'RUNNING'
            while self.keep_running():
                self.sleep_until_time()
                # Toggle the run_type for each iteration here - this will flip the attribute values back and forth
                run_type = NEW if run_type == DEFAULT else DEFAULT
                try:
                    update_cells_attributes_via_cell_management(user, run_type, self.REQUIRED_NUMBER_OF_NODES,
                                                                node_cell_data)
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))
        else:
            self.add_error_as_exception(EnvironError('Required data could not be read from ENM.'
                                                     'Profile cannot continue - check log file'))


class CreateDeleteCellsAndRelationsFlow(GenericFlow):
    """ Cellmgt 03 and 05 flow"""

    def create_cells_flow(self, create_object_list):
        """
        Creates cells for each object in provided list.
        :param create_object_list: List of CreateDeleteCells objects.
        :type create_object_list: list
        :return: If cells created.
        :rtype: bool
        """
        for obj in create_object_list:
            obj.create_cells()
            if not obj.created_cells:
                self.add_error_as_exception(EnmApplicationError(
                    "Profile execution failed due to no cells for node: {0} created".format(obj.node_name)))
                return False
        return True

    @staticmethod
    def delete_relations_flow(user, delete_object_list):
        """
        Deletes all created relations for each object in passed list.

        :param user: Enm user who will perform the delete operation(s)
        :type user: `enm_user_2.User`
        :param delete_object_list: List of CreateDeleteCell objects.
        :type delete_object_list: list
        """
        for obj in delete_object_list:
            if getattr(obj, 'relations_created_on_cell', []):
                for fdn in set(obj.relations_created_on_cell):
                    try:
                        cellmgt.delete_cell_relation(user, fdn)
                    except Exception as e:
                        log.logger.debug(str(e))
                        continue

    def setup_create_delete_objects(self, create_delete_object_list):
        """
        Invokes the setup method for each object in the passed list.
        :param create_delete_object_list: List of CreateDeleteCellsObject's.
        :type create_delete_object_list: list
        """
        log.logger.debug("Attempting to call the setup method for each CreateDeleteCellObject.")
        for obj in create_delete_object_list:
            while not obj.setup_completed:
                obj.setup()
                if not obj.setup_completed:
                    log.logger.debug("Setup failed for {0}. Cannot continue setup. Will retry on next "
                                     "iteration.".format(obj.node_name))
                    self.sleep_until_time()

    def get_create_delete_object_list(self, user, nodes):
        """
        Returns a list of CreateDeleteCells objects depending on profile node type.
        :param user: user object.
        :type user: `enm2.user`
        :param nodes: List of node objects.
        :type nodes: list
        :return: List of CreateDeleteCells objects.
        :rtype: list
        """

        if "RNC" in self.SUPPORTED_NODE_TYPES:
            return [RncCreateDeleteCells(self, user, node) for node in nodes]
        elif "ERBS" in self.SUPPORTED_NODE_TYPES:
            return [ERBSCreateDeleteCells(self, user, node) for node in nodes]

    @staticmethod
    def create_relations_flow(create_object_list):
        """
        Executes steps required to create relations.
        :param create_object_list: List of CreateDeleteCellsObject objects
        :type create_object_list: list
        """

        for obj in create_object_list:
            target_objs = [target for target in create_object_list if obj != target]
            log.logger.debug('Attempting to create cell relations for {0}.'.format(obj.node_name))
            obj.create_relations(target_objs=target_objs)

    @staticmethod
    def delete_cells_flow(delete_object_list):
        """
        Deletes all created cells for each object in passed list.
        :param delete_object_list: List of CreateDeleteCell objects.
        :type delete_object_list: list
        """

        for obj in delete_object_list:
            obj.delete_all_cells(attempts=2)
            obj.summary_report()
            obj.reset()

    def execute_flow(self):
        """
        Flow to create cells, relations and delete created MOs.
        """

        user = self.create_profile_users(1, self.USER_ROLES)[0]
        nodes = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'lte_cell_type', 'poid'])

        self.state = 'RUNNING'

        while self.keep_running():
            self.sleep_until_time()
            synced_nodes = self.get_synchronised_nodes(nodes, user)
            if not synced_nodes:
                self.add_error_as_exception(
                    EnvironError("Nodes allocated to the profile got unsynchronized. Ensure allocated nodes "
                                 "are synchronized and then the profile will continue from the next iteration."))
                continue
            create_delete_object_list = self.get_create_delete_object_list(user, synced_nodes)
            self.setup_create_delete_objects(create_delete_object_list)
            if self.create_cells_flow(create_delete_object_list):
                log.logger.debug("Sleeping for 300s after creation of cells.")
                time.sleep(300)
                self.create_relations_flow(create_delete_object_list)
                log.logger.debug("Sleeping for 1200s after creation of relations.")
                time.sleep(1200)
                self.delete_relations_flow(user, create_delete_object_list)
                log.logger.debug("Sleeping for 1200s after deletion of relations.")
                time.sleep(1200)
                self.delete_cells_flow(create_delete_object_list)
            else:
                log.logger.debug("Could not create cells. Profile will sleep until next iteration.")


class LockUnlockAllCellsOnAnNode(GenericFlow):

    def execute_flow(self):
        """
        Method to controls the flow of operations to lock/unlock all cells on a node

        :return: boolean to indicate that flow has completed
        :rtype: bool
        """

        sleep_time = 120

        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)

        nodes_specified_for_use_by_profile = self.get_nodes_list_by_attribute(
            node_attributes=['node_id', 'lte_cell_type', 'poid'])
        num_cells_per_user = self.NUM_CELLS_PER_USER if hasattr(self, "NUM_CELLS_PER_USER") else None
        standard = self.STANDARD if hasattr(self, "STANDARD") else None
        cell_type = self.CELL_TYPE if hasattr(self, "CELL_TYPE") else None
        remove_reserved_gerancells = self.REMOVE_RESERVED_GERANCELLS if hasattr(self, "REMOVE_RESERVED_GERANCELLS") else False

        self.state = "RUNNING"
        while self.keep_running():
            log.logger.debug("Node(s) selected for operations: {0}".format(
                ', '.join(str(node_name) for node_name in nodes_specified_for_use_by_profile)))

            list_of_node_poids = create_list_of_node_poids(users[0], nodes_specified_for_use_by_profile)
            user_node_data = zip(users, list_of_node_poids)
            if user_node_data:
                self.create_and_execute_threads(workers=user_node_data, thread_count=len(users),
                                                func_ref=cellmgt.lock_unlock_cells_flow,
                                                args=[sleep_time, num_cells_per_user,
                                                      standard, cell_type,
                                                      remove_reserved_gerancells],
                                                wait=self.THREAD_QUEUE_TIMEOUT,
                                                join=self.THREAD_QUEUE_TIMEOUT)
            else:
                self.add_error_as_exception(EnvironError("Empty user/node data structure, nothing to do."))
            self.sleep_until_next_scheduled_iteration()

        return True
