import datetime
import time
from enmutils.lib import log, persistence
from enmutils.lib.exceptions import EnvironWarning
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.reparenting import (build_base_station_json, get_tg_mos,
                                          send_post_request, CANDIDATE_CELLS_URl, poll_for_completed_status, IMPACT_URL,
                                          DELETE_CANDIDATE_CELLS_URL, build_cell_json,
                                          get_bsc_network_elements, CONFLICTING_RELATIONS_URL,
                                          CONFLICTING_DELETE_RELATIONS_URL, REPARENTED_CELLS_URL,
                                          RELATION_TYPES_INTRA_RAT_URL, RELATION_TYPES_INTER_RAT_URL,
                                          CUTOVER_CANDIDATE_CELLS_URL, CUTOVER_REPARENTED_CELLS_URL,
                                          CUSTOMIZE_REPARENTED_CELLS_URL, DELETE_CANDIDATE_RELATIONS_URL,
                                          EnmApplicationError, get_and_sort_geran_cells,
                                          set_inter_ran_mobility_attribute, set_channel_group_active)

GSM_MAX_CELLS = 450
GSM_TECHNOLOGY_TYPE = "GSM"


class ReparentingFlow(GenericFlow):
    GERAN_CELLS = {}

    def get_tg_mos_values(self, user, node_ids):
        """
        Function to get the Connected Channel MO information to determine the cells per base station

        :param user: User who make the GET request to ENM
        :type user: `enm_user_2.User`
        :param node_ids: List of node ids to be supplied to the ENM query
        :type node_ids: list

        :return: Dictionary containing the grouped base station and count of the connected channel groups
        :rtype: dict
        """
        return get_tg_mos(user, node_ids, self.GERAN_CELLS)

    @staticmethod
    def get_base_station_json(base_stations, technology_type):
        """
        Function to build the base station JSON to be sent in the POST request

        :param base_stations: List of the base stations to be included in the POST JSON
        :type base_stations: list
        :param technology_type: Technology type of the NE(s) to be included in the POST JSON
        :type technology_type: str

        :return: Dictionary containing the POST JSON for base station(s)
        :rtype: dict
        """

        return build_base_station_json(base_stations, technology_type=technology_type)

    def get_geran_cell_json(self, cells, technology_type, target_network_controller, include_msc_operations,
                            base_stations=None, include_attributes=None):
        """
        Function to build the base station JSON to be sent in the POST request

        :param cells: List of the cells to be included in the POST JSON
        :type cells: list
        :param technology_type: Technology type of the NE(s) to be included in the POST JSON
        :type technology_type: str
        :param target_network_controller: The BSC which will be the target of the moved cells
        :type target_network_controller: str
        :param include_msc_operations: Boolean indicating if the MSC operations should also be included
        :type include_msc_operations: bool
        :param base_stations: List of base stations to be included in the POST JSON
        :type base_stations: list
        :param include_attributes: Boolean indicating if additional attribute are needed for each cell
        :type include_attributes: bool

        :return: Dictionary containing the POST JSON for base station(s)
        :rtype: dict
        """
        target_cells = []
        if include_attributes:
            target_network_controller, target_cells = self.select_target_controller_and_cells(cells,
                                                                                              target_network_controller)
        return build_cell_json(
            base_stations, technology_type=technology_type, target_network_controller=target_network_controller,
            include_mo_operations=include_msc_operations, include_attributes=include_attributes,
            target_cells=target_cells)

    def select_target_controller_and_cells(self, cells, target_network_controller):
        """
        Function to select the existing cells on the target to be used for the newName attribute
        :param cells: List of the cells to be included in the POST JSON
        :type cells: list
        :param target_network_controller: The BSC which will be the target of the moved cells
        :type target_network_controller: str

        :raises EnmApplicationError: raised if target cells value cannot be matched

        :return: Tuple containing the target controller and target cells
        :rtype: tuple
        """
        log.logger.debug("Selecting target cells and controller.")
        target_cells = []
        if (target_network_controller in self.GERAN_CELLS.keys() and
                len(cells) <= len(self.GERAN_CELLS.get(target_network_controller))):
            target_cells = sorted(self.GERAN_CELLS.get(target_network_controller), reverse=True)[:len(cells)]
        else:
            for bsc in self.GERAN_CELLS.keys():
                if not any([cell for cell in cells if bsc in cell]) and len(cells) <= len(self.GERAN_CELLS.get(bsc)):
                    target_network_controller = bsc
                    target_cells = sorted(self.GERAN_CELLS.get(target_network_controller), reverse=True)[:len(cells)]
                    break
        log.logger.debug("Completed selecting target controller: {0}. Target cells: [{1}].".format(
            target_network_controller, len(target_cells)))
        if not target_cells:
            raise EnmApplicationError("Unable to select target cells for newName attribute.")
        return target_network_controller, target_cells

    @staticmethod
    def select_volume_of_base_stations(base_stations, max_cells=450):
        """
        Function to select base stations based upon the determined count of connected channel groups

        :param base_stations: Dictionary containing the mapped base station and count of connected channel groups
        :type base_stations: dict
        :param max_cells: Maximum number of cells which should be selected
        :type max_cells: int

        :return: Tuple containing the currently selected count and the list of the selected base stations
        :rtype: tuple
        """
        selected_base_stations = []
        selected_cells = []
        log.logger.debug("Selecting base stations from supplied dictionary.")
        for base_station, cells in base_stations.items():
            if len(cells) % 2 and len(selected_cells) + len(cells) <= max_cells:
                selected_cells.extend(cells)
                selected_base_stations.append({base_station: cells})
        log.logger.debug("Completed selecting base stations from supplied dictionary.")
        return selected_cells, selected_base_stations

    @staticmethod
    def get_resource_id(response):
        """
        Function to get the Resource ID from the supplied HTTPResponse

        :param response: HTTPResponse object containing the resourceId value
        :type response: `requests.HTTPResponse`

        :raises EnmApplicationError: raised if the response does not contain a resourceId

        :return: The value of the resourceId variable available in the HTTPResponse
        :rtype: str
        """
        log.logger.debug("Retrieving Resource Id value from supplied response.")
        response_json = response.json()
        if response_json and response_json.get('resourceId'):
            log.logger.debug("Resource ID: {0}".format(response_json.get('resourceId')))
            return response_json.get('resourceId')
        else:
            msg = "Could not determine resource id value from response json: {0}".format(response.json())
            log.logger.debug(msg)
            raise EnmApplicationError(msg)

    def get_base_station_values(self, user, node_ids, max_cells):
        """
        Function to query ENM for base station information to be used in the POST request

        :param user: User who make the GET request to ENM
        :type user: `enm_user_2.User`
        :param node_ids: List of node ids to be supplied to the ENM query
        :type node_ids: list
        :param max_cells: Maximum number of cells to be selected
        :type max_cells: int

        :raises EnmApplicationError: raised if no base stations can be selected

        :return: Tuple containing list of the selected base stations with their cells to be sent in the POST request and list of cells
        :rtype: tuple
        """
        base_stations_with_cells = []
        cells = []
        log.logger.debug("Starting selection of base stations.")
        for node_id in node_ids:
            if not max_cells:
                break
            try:
                channel_groups = self.get_tg_mos_values(user, [node_id])
                selected_cells, selected_base_stations = self.select_volume_of_base_stations(channel_groups, max_cells=max_cells)
                if self.NAME == "REPARENTING_10":
                    set_channel_group_active(user, selected_cells)
                max_cells -= len(selected_cells)
                for base_station in selected_base_stations:
                    for station, station_cells in base_station.items():
                        required_cells = [cell.split(',ChannelGroup')[0] for cell in station_cells]
                        cells.extend(required_cells)
                        base_stations_with_cells.extend([{station: required_cells}])
            except Exception as e:
                log.logger.debug("Unable to select base station, error encountered: {0}".format(str(e)))
        if not base_stations_with_cells:
            raise EnmApplicationError("No base stations selected, please check logs for further information.")
        log.logger.debug("Completed selecting base stations, total selected: {0}".format(len(base_stations_with_cells)))
        return base_stations_with_cells, cells

    @staticmethod
    def select_target_bsc(user, selected_cells):
        """
        Function to select a target BSC which is NOT in the list of selected GeranCells

        :param user: User who make the GET request to ENM
        :type user: `enm_user_2.User`
        :param selected_cells: List of the GeranCells to be sent in the POST request
        :type selected_cells: list

        :raises EnmApplicationError: raised if there is no available target BSC

        :return: The selected BSC
        :rtype: str
        """
        log.logger.debug("Starting selection of target Bsc.")
        for bsc in get_bsc_network_elements(user):
            if not any([selected_cell for selected_cell in selected_cells if bsc in selected_cell]):
                log.logger.debug("Completed selection of target Bsc: {0}".format(bsc))
                return bsc
        raise EnmApplicationError("No target BSC selected, unable to send request with no available target BSC.")

    def wait_for_first_iteration_to_complete(self, profile_name, state_to_wait_for="RUNNING",
                                             timeout_mins=30, sleep_between=60):
        """
        Checks the CMIMPORT_27 completed minimum one iteration successfully

        :param profile_name: indicates which setup profile we are waiting to complete (str)
        :type profile_name: str
        :param state_to_wait_for: the state which is queried.
        :type state_to_wait_for: str
        :param timeout_mins: timeout of this function in minutes
        :type timeout_mins: int
        :param sleep_between: sleep time between query for profile status
        :type sleep_between: int
        :return: Boolean to indicate success or failure of operation
        :rtype: bool

        :raises EnvironWarning: raised if the required profile is not running on the deployment.
        """

        profile_key = profile_name.upper()
        if not persistence.has_key(profile_key):
            raise EnvironWarning("{0} profile is not running on this deployment. Please start {0} and then restart {1}."
                                 .format(profile_key, self.NAME))

        timeout = (datetime.datetime.now() + datetime.timedelta(minutes=timeout_mins))

        while datetime.datetime.now() < timeout:
            profile = persistence.get(profile_key)
            if profile.state == state_to_wait_for and profile._last_run is not None and profile.status == "OK":
                return True
            log.logger.info(log.red_text(
                "Profile: {0} is not yet {1} waiting for {2} seconds".format(profile_name, state_to_wait_for,
                                                                             sleep_between)))
            time.sleep(sleep_between)
        log.logger.debug("{0} failed to move to state {1} within the timeout period ({2} minutes)"
                         "".format(profile_key, state_to_wait_for, timeout_mins))
        return False


class Reparenting01Flow(ReparentingFlow):
    URL = CANDIDATE_CELLS_URl

    def execute_flow(self):
        """
        Executes the profile flow.
        """
        self.state = "RUNNING"
        users = self.create_profile_users(1, getattr(self, 'USER_ROLES', ['ADMINISTRATOR']))
        node_ids = [node.node_id for node in self.get_nodes_list_by_attribute()]
        max_cells = getattr(self, 'MAX_CELLS', GSM_MAX_CELLS)
        user = users[0]
        selected_base_stations = []
        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            try:
                if not selected_base_stations:
                    self.GERAN_CELLS = get_and_sort_geran_cells(user)
                    base_stations, _ = self.get_base_station_values(user, node_ids, max_cells=max_cells)
                    selected_base_stations = [base_station for base_station_with_cells in base_stations for base_station in base_station_with_cells.keys()]
                json = self.get_base_station_json(selected_base_stations, GSM_TECHNOLOGY_TYPE)
                response = send_post_request(user, self.URL, json)
                resource_id = self.get_resource_id(response)
                poll_for_completed_status(user, resource_id, timeout=self.TIMEOUT)
            except Exception as e:
                self.add_error_as_exception(e)


class Reparenting02Flow(ReparentingFlow):
    URL = IMPACT_URL
    TARGET_NETWORK_CONTROLLER = None
    TARGET_NETWORK_CONTROLLER_REQUIRED = True
    INCLUDE_MSC_OPERATIONS = None
    REQUIRES_BASE_STATIONS = True
    SET_INTER_RAN_MOBILITY = False

    def execute_flow(self):
        """
        Executes the profile flow.
        """
        if self.NAME == "REPARENTING_07":
            try:
                while not self.wait_for_first_iteration_to_complete("CMIMPORT_27",
                                                                    state_to_wait_for="SLEEPING"):
                    log.logger.debug("{0} sleeping until next iteration".format(self.NAME))
                    self.sleep_until_next_scheduled_iteration()
            except Exception as e:
                self.add_error_as_exception(e)
                return
        users = self.create_profile_users(1, getattr(self, 'USER_ROLES', ['ADMINISTRATOR']))
        node_ids = [node.node_id for node in self.get_nodes_list_by_attribute()]
        max_cells = getattr(self, 'MAX_CELLS', GSM_MAX_CELLS)
        user = users[0]
        selected_base_stations, selected_cells = [], []
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            self.json_creation_and_post_request(node_ids, max_cells, user, selected_base_stations, selected_cells)

    def json_creation_and_post_request(self, node_ids, max_cells, user, selected_base_stations, selected_cells):
        """
        Creates a json file for reparenting

        :param node_ids: indicates node id
        :type node_ids: list
        :param max_cells: maximum number of cells
        :type max_cells: int
        :param user: User who will perform the reparenting
        :type user: 'enm_user_2.User`
        :param selected_base_stations: selected base stations
        :type selected_base_stations: list
        :param selected_cells: selected cells
        :type selected_cells: list

        """
        try:
            if not selected_base_stations or not selected_cells:
                self.GERAN_CELLS = get_and_sort_geran_cells(user)
                selected_base_stations, selected_cells = self.get_base_station_values(
                    user, node_ids, max_cells=max_cells)
                if self.SET_INTER_RAN_MOBILITY:
                    set_inter_ran_mobility_attribute(user, selected_cells[:100], "ON")
            if self.TARGET_NETWORK_CONTROLLER_REQUIRED and not self.TARGET_NETWORK_CONTROLLER and selected_cells:
                if hasattr(self, "TARGET_BSC_ID"):
                    self.TARGET_NETWORK_CONTROLLER = self.TARGET_BSC_ID
                else:
                    self.TARGET_NETWORK_CONTROLLER = self.select_target_bsc(user, selected_cells)
            json = self.get_geran_cell_json(
                selected_cells, GSM_TECHNOLOGY_TYPE, self.TARGET_NETWORK_CONTROLLER, self.INCLUDE_MSC_OPERATIONS,
                base_stations=selected_base_stations if self.REQUIRES_BASE_STATIONS else None,
                include_attributes=getattr(self, 'INCLUDE_ATTRIBUTES', None))
            response = send_post_request(user, self.URL, json)
            resource_id = self.get_resource_id(response)
            poll_for_completed_status(user, resource_id, timeout=self.TIMEOUT)
        except Exception as e:
            self.add_error_as_exception(e)


class Reparenting03Flow(Reparenting02Flow):
    URL = DELETE_CANDIDATE_CELLS_URL
    TARGET_NETWORK_CONTROLLER_REQUIRED = False


class Reparenting04Flow(Reparenting02Flow):
    URL = CONFLICTING_RELATIONS_URL


class Reparenting05Flow(Reparenting02Flow):
    URL = CONFLICTING_DELETE_RELATIONS_URL


class Reparenting06Flow(Reparenting02Flow):
    URL = REPARENTED_CELLS_URL


class Reparenting07Flow(Reparenting02Flow):
    URL = RELATION_TYPES_INTRA_RAT_URL
    INCLUDE_ATTRIBUTES = True


class Reparenting08Flow(Reparenting02Flow):
    URL = RELATION_TYPES_INTER_RAT_URL
    INCLUDE_ATTRIBUTES = True


class Reparenting09Flow(Reparenting02Flow):
    URL = CUTOVER_CANDIDATE_CELLS_URL
    TARGET_NETWORK_CONTROLLER_REQUIRED = False


class Reparenting10Flow(Reparenting02Flow):
    URL = CUTOVER_REPARENTED_CELLS_URL
    INCLUDE_ATTRIBUTES = True


class Reparenting11Flow(Reparenting02Flow):
    URL = CUSTOMIZE_REPARENTED_CELLS_URL
    SET_INTER_RAN_MOBILITY = True


class Reparenting12Flow(Reparenting02Flow):
    URL = DELETE_CANDIDATE_RELATIONS_URL
    INCLUDE_ATTRIBUTES = True
