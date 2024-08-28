# ********************************************************************
# Name    : Network View
# Summary : Provides functionality used primarily by Network View
#           profiles. Allows the user to set the GEO location of nodes,
#           set the GEO point, set longitude and latitude of a node,
#           query existing information, remove the GEO location, also
#           includes functionality related to querying Physical link
#           information.
# ********************************************************************

import json
from retrying import retry
from requests.exceptions import HTTPError, ConnectionError
from enmutils.lib import log, persistence
from enmutils.lib.headers import JSON_HEADER
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.cmcli import execute_command_on_enm_cli
from enmutils_int.lib.plm import PLM_FILES_IMPORTED_KEY

SET_LOCATION_URL = "network-visualization/v1/network-elements/"
GET_LOCATION_URL = "network-visualization/v1/network-element-templates/neGeolocations"
GET_RELATIONS_URL = "topology-relationship-service/rest/v1/relation/getRelations"
CMEDIT_GET_NODES = "cmedit get * NetworkElement.neType=={node_type} -t"


class NodeLocation(object):
    def __init__(self, user, node_id, longitude, latitude):
        self.user = user
        self.node_id = node_id
        self.longitude = longitude
        self.latitude = latitude

    def create_geo_location(self):
        """
        Function to create location attributes on a node.
        """
        log.logger.debug("Creating Geographical Location attribute on {0}".format(self.node_id))
        cmd = "cmedit create NetworkElement={0}, GeographicLocation=1 geographicLocationId=1 -ns=OSS_GEO -v=2.0.0".format(self.node_id)
        execute_command_on_enm_cli(self.user, cmd)

    def create_geo_point(self):
        """
        Function to create geometric point MO and set coordinates
        """
        log.logger.debug("Creating Geometric Point attribute on {0}".format(self.node_id))
        cmd = "cmedit create NetworkElement={0}, GeographicLocation=1,GeometricPoint=1 geometricPointId=1 -ns=OSS_GEO -v=2.0.1".format(self.node_id)
        execute_command_on_enm_cli(self.user, cmd)

    def create_latitude_and_longitude(self):

        log.logger.debug("Setting Latitude: {0}, Longitude: {1} on {2}".format(self.latitude, self.longitude,
                                                                               self.node_id))
        cmd = "cmedit set NetworkElement={0}, GeographicLocation=1, GeometricPoint=1 latitude={1}, longitude={2}".format(self.node_id, self.latitude, self.longitude)
        execute_command_on_enm_cli(self.user, cmd)

    def delete(self):
        """
        Function to delete location attributes on a node.
        """
        log.logger.debug("Deleting Geographical Location object on {0}".format(self.node_id))
        cmd = "cmedit delete NetworkElement={} GeographicLocation -ALL".format(self.node_id)
        execute_command_on_enm_cli(self.user, cmd)

    def _teardown(self):
        """
        Function to delete created location attributes on the profile termination.
        """
        log.logger.debug("Tearing down Geographical location attribute on {0}".format(self.node_id))
        try:
            self.delete()
        except Exception as e:
            log.logger.error(str(e.message))
        else:
            log.logger.debug("Teardown of Geographical Location {0} completed.".format(self.node_id))


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=10000,
       stop_max_attempt_number=3)
def update_node_location_by_rest(user, node_id, lat, lng):
    """
    Function to update coordinates of given node by rest
    :param user: User object to perform request
    :type user: enm_user_2.User
    :param node_id: Id of the node
    :type node_id: str
    :param lat: Latitude
    :type lat: int
    :param lng: Longitude
    :type lng: int
    """
    payload = [{"type": "GeographicLocation",
                "attributes": [{"key": "latitude", "type": "DOUBLE", "value": lat},
                               {"key": "longitude", "type": "DOUBLE", "value": lng}]}]

    log.logger.info("Updating coordinates of {0} to Latitude: {1} , Longitude: {2}".format(node_id, lat, lng))
    response = user.put(SET_LOCATION_URL + node_id, data=json.dumps(payload), headers=JSON_HEADER)
    response.raise_for_status()
    log.logger.info("Successfully updated coordinates on {0}".format(node_id))


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=10000,
       stop_max_attempt_number=3)
def get_node_location_by_rest(user, node_id, node_poid):
    """
    Function to get node location by rest call
    :param user: user to perform request
    :type user: enm_user_2.User
    :param node_id: Node Id
    :type node_id: str
    :param node_poid: Node poid
    :type node_poid: str
    :return: Coordinates
    :rtype: tuple
    :raises EnmApplicationError: when profile failed to get coordinates
    """
    log.logger.info("Checking coordinates of node: {0} and its poid : {1}".format(node_id, node_poid))
    response = user.post(GET_LOCATION_URL, data=json.dumps([node_poid]), headers=JSON_HEADER)
    response.raise_for_status()
    try:
        response = response.json()
        lat = response["treeNodes"][0]["geoCoordinates"]["latLng"][0]
        lng = response["treeNodes"][0]["geoCoordinates"]["latLng"][1]
        log.logger.info("Current location of {0} Latitude: {1}, Longitude: {2}".format(node_id, lat, lng))
        return lat, lng
    except Exception as e:
        raise EnmApplicationError("Failed to get coordinates with error message {0}".format(e))


def get_existing_locations(user):
    """
    Function to look for coordinates present on the nodes
    :param user: User to perform request
    :type user: enm_user_2.User
    :return: list of locations
    :rtype: list
    """
    log.logger.info("Checking for coordinates on the system.")

    nodes_with_locations = []
    response = user.enm_execute("cmedit get * GeographicLocation -t", on_terminal=False)
    if response.is_complete() and response.get_output().groups():
        groups = response.get_output().groups()[0]
        nodes_with_locations = [group.find_by_label('NodeId')[0] for group in groups]
    else:
        log.logger.info("No existing coordinates found on the system")

    return nodes_with_locations


def delete_location_on_node(user, node_id):
    """
    Function to delete location on node
    :param user: User to perform request
    :type user: enm_user_2.User
    :param node_id: id of the node
    :type node_id: str
    """
    log.logger.debug("Deleting location on {0}".format(node_id))
    cmd = "cmedit delete NetworkElement={0} GeographicLocation -ALL".format(node_id)
    execute_command_on_enm_cli(user, cmd)


def get_physical_links_on_nodes_by_rest_call(user, poids):
    """
    Function to perform the get relations netview call and validate the response
    :param user: User to perform request
    :type user: enm_user_2.User
    :param poids: List of node poids
    :type poids: list
    :raises EnmApplicationError: when there is no valid response from ENM
    :raises EnvironError: When no physical links are found in the response
    """
    payload = {"relationTypes": ["X2_eNB-gNB", "TRANSPORT_LINK"],
               "relationTypesHavingFilters": {"X2_eNB-gNB": [], "TRANSPORT_LINK": ["PHYSICAL", "RADIO_BONDING",
                                                                                   "AGGREGATION"]},
               "poIds": poids, "applicationId": "network-viewer-logical"}
    enb_eng_links = []
    transport_links = []

    response = user.post(GET_RELATIONS_URL, data=json.dumps(payload), headers=JSON_HEADER)
    response.raise_for_status()
    try:
        response_json = response.json()
    except ValueError as e:
        raise EnmApplicationError("No valid json response from ENM service with error message:{0}".format(e))

    if response_json and "relationTypeToTargets" in response_json:
        if "X2_eNB-gNB" in response_json["relationTypeToTargets"]:
            enb_eng_links = response_json["relationTypeToTargets"]["X2_eNB-gNB"]
        if "TRANSPORT_LINK" in response_json["relationTypeToTargets"]:
            transport_links = response_json["relationTypeToTargets"]["TRANSPORT_LINK"]
    if not enb_eng_links and not transport_links:
        raise EnvironError("Could not find any Physical Links check if PLM_01 is running on the system.")
    else:
        log.logger.info("Successfully retrieved Physical Links.\n"
                        "Number of eNB-gNB physical links : {0}\n"
                        "Number of TRANSPORT physical links : {1}".format(len(enb_eng_links), len(transport_links)))
        log.logger.info("enb_eng_links : {0}\n"
                        "transport_links : {1}".format((enb_eng_links), (transport_links)))


def get_plm_dynamic_content():
    """
    Function to get node names from the files imported by PLM
    :return: List of nodes with Physical Links
    :rtype: list
    :raises EnvironError: When dynamic content is not present or error occurs when retrieving
    """
    plm_import_files = None
    node_ids = []
    try:
        if persistence.has_key(PLM_FILES_IMPORTED_KEY):
            plm_import_files = persistence.get(PLM_FILES_IMPORTED_KEY)
    except Exception as e:
        raise EnvironError("Could not fetch PLM imported files! Error Message: {0}".format(e.message))
    if plm_import_files:
        for import_file in plm_import_files:
            with open(import_file, 'rb') as csv_file:
                csv_file.next()
                node_ids.extend([node for line in csv_file for node in (line.split(',')[1::2]) if node])
        node_ids = set(node_ids)
    else:
        raise EnvironError("No PLM dynamic content found on the system. Please check is PLM_01 running.")
    return list(node_ids)
