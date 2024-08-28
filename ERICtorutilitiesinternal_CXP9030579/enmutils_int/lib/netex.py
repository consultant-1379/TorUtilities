# ********************************************************************
# Name    : Network Explorer
# Summary : Contains the main functionality used to interact with
#           Network Explorer. Allows the user to create, delete, query
#           and update Collection objects in Network Explorer,
#           including custom topology objects, nested collections,
#           also provides options to perform Network Explorer search
#           queries or create, delete, query saved searches, also
#           allows searching for Network Objects and POID(s).
# ********************************************************************

import json
import random
import re
import time
import os

from requests.exceptions import HTTPError
from enmutils.lib import filesystem, log
from enmutils.lib.exceptions import EnmApplicationError, EnvironError, EnvironWarning
from enmutils.lib.headers import (JSON_SECURITY_REQUEST, SECURITY_REQUEST_HEADERS, NETEX_HEADER,
                                  NETEX_COLLECTION_HEADER, NETEX_IMPORT_HEADER)

GET_POS_BY_POID_URL = "/managedObjects/getPosByPoIds"
IMPORT_EXPORT_SERVICE = "/network-explorer-import/v1/collection/"
EXPORT_COLLECTION_URL = IMPORT_EXPORT_SERVICE + "export"
EXPORT_CUSTOM_TOPOLOGY_URL = EXPORT_COLLECTION_URL + "/nested/"
EXPORT_COLLECTION_STATUS_URL = EXPORT_COLLECTION_URL + "/status/"
DOWNLOAD_COLLECTION_URL = EXPORT_COLLECTION_URL + "/download/"
IMPORT_COLLECTION_URL = IMPORT_EXPORT_SERVICE + "import/"

COLLECTION_ENDPOINT = "/object-configuration/collections/v4/"
SEARCH_COLLECTION_ENDPOINT = "/object-configuration/collections/search/v4/"
UPDATE_COLLECTION_FILE_V1 = "/network-explorer-import/v1/collections/file"
CREATE_COLLECTION_FILE_V2 = "/network-explorer-import/v2/collections/file"

NUM_ATTEMPTS_EXPORT_COLLECTION_STATUS = 120
SLEEP_TIME_EXPORT_COLLECTION_STATUS = 5
NUM_ATTEMPTS_IMPORT_COLLECTION_STATUS = 35
SLEEP_TIME_IMPORT_COLLECTION_STATUS = 60

DEFAULT_DIR = "/home/enmutils/netex/"
EXPORT_DIR = DEFAULT_DIR + "/export/"


def search_collections(user, payload=None):
    """
    Search collections using the given payload.
    :param user: ENM user
    :type user: `enm_user_2.User`
    :param payload: custom payload to search collections
    :type payload: dict
    :raises HTTPError when status code of the response is in 400 or 500 series.
    :rtype: Response object
    :return: `Response` object
    """
    payload = payload if payload else {}
    log.logger.debug("Attempting to search all collections with parameters - {0}".format(payload))
    response = user.post(SEARCH_COLLECTION_ENDPOINT, json=payload, headers=NETEX_COLLECTION_HEADER)
    response.raise_for_status()
    log.logger.debug("Successfully searched all collections with parameters - {0}".format(payload))
    return response


def get_all_collections(user):
    """
    Get all collections.
    :param user: ENM user
    :type user: `enm_user_2.User`
    :rtype: Response object
    :return: `Response` object
    """
    log.logger.debug("Attempting to retrieve details of all collections.")
    response = search_collections(user, payload={})
    log.logger.debug("Successfully retrieved details of all collections.")
    return response


class Collection(object):
    """
    Class for various methods on Collections
    """

    def __init__(self, user, name, nodes=None, query="NetworkElement", public=True, **kwargs):
        """
        Constructor for Collection object

        :type name: string
        :param name: The name of the collection
        :type nodes: list
        :param nodes: List of nodes we want to add to collection
        :type query: str
        :param query: The query to be executed as part of the flow
        :type public: bool
        :param public: flag to show whether the category is public or not
        :type user : enm_user.User object
        :param user: user we use to create the Collection
        :type kwargs : dict
        :param kwargs: "custom_topology" - Collection is a root of custom topology.
                                           Default value is False
                       "fdn_file_name"   - name of the file if no name given then it is set to.
                                           Default value is 'fdn_list.txt'
                       "labels"          - List of labels to the collection to be created.
                                           Default value is None
                       "num_results"     - Number of elements in the collection to be limited.
                                           Default value is 0
                       "parent_ids"      - List of parent ids to the collection to be created.
                                           Default value is None
                       "sharing"         - Sharing access of collection e.g. public or private.
                                           Default value is 'public'
                       "type"            - Type of collection e.g. LEAF or BRANCH.
                                           Default value is 'LEAF'
                       "version"         - Version of network explorer collection API to be used.
                                           Default value is 'v4'
        """
        self.name = name.lower()
        self.nodes = nodes
        self.query = query
        self.user = user
        self.id = None
        self.custom_topology = kwargs.get("custom_topology", False)
        self.fdn_file_name = kwargs.get("fdn_file_name", "fdn_list.txt")
        self.labels = kwargs.get("labels", None)
        self.num_results = kwargs.get("num_results", 0)
        self.parent_ids = kwargs.get("parent_ids", None)
        self.sharing = "public" if public else "private"
        self.type = kwargs.get("type", "LEAF")
        self.version = kwargs.get("version", "v4")
        self.poids = kwargs.get("poids", None)

    def _teardown(self):
        """
        Secret teardown method
        """
        self.delete()

    @property
    def exists(self):
        """
        Check if the collection exists in ENM

        :return: Boolean indicating if the collection exists in ENM
        :rtype: bool
        :raises EnmApplicationError: when collection response status code is not 200
        """
        exists = False
        if self.id:
            try:
                response = self.user.get(COLLECTION_ENDPOINT + self.id, headers=NETEX_COLLECTION_HEADER)
                if response.status_code == 200:
                    exists = True
            except HTTPError:
                log.logger.debug("Could not find collection {0}".format(self.id))

        # If we didn't find by id, check for the name
        if not exists:
            collections = get_all_collections(user=self.user)
            log.logger.debug('print all collections status codes {0}'.format(collections.status_code))
            if collections.status_code != 200:
                raise EnmApplicationError("ENM service failed to return a valid response. Response status_code {0}, "
                                          "unable to get all collections".format(collections.status_code))
            all_collections = collections.json()
            if any([self.name == _.get('name') for _ in all_collections]):
                exists = True
        return exists

    def create(self):
        """
        Creates a Collection on ENM

        :raises: HTTPError
        """
        log.logger.debug("Attempting to create collection named {0}".format(self.name))
        if self.nodes:
            node_mos = Search(user=self.user, query=self.query, nodes=self.nodes).execute()
            node_poids = [node_mo["poId"] for node_mo in node_mos.values()]
        elif self.poids:
            node_poids = self.poids[:self.num_results]
        else:
            response = Search(user=self.user, query=self.query, version="v2").execute()
            node_poids = [node_mo["id"] for node_mo in response["objects"]][:self.num_results]
        payload = {"name": self.name, "sharing": self.sharing, "contents": node_poids,
                   "type": self.type, "isCustomTopology": self.custom_topology, "labels": self.labels}
        if self.parent_ids:
            payload.update({"parentIds": self.parent_ids})
        response = self.user.post(COLLECTION_ENDPOINT, json=payload, headers=NETEX_COLLECTION_HEADER)
        if response.status_code != 201:
            response.raise_for_status()
        try:
            self.id = response.json()['id']
        except (ValueError, TypeError) as e:
            raise EnmApplicationError(e)
        log.logger.debug("Successfully created collection named {0} with id {1}".format(self.name, self.id))

    def create_list_of_fdns(self, num_fdns_required=25000):
        """
        Creates a Collection and saves it to a file at location "/network-explorer-import/v1/c/collections/file"
        :raises: HTTPError
        :type num_fdns_required : int
        :param num_fdns_required: the number of FDN's required
        :rtype: list
        :returns: list of FDN's
        """
        cmds = ['cmedit get * MeContext', 'cmedit get * ManagedElement', 'cmedit get * NetworkElement']
        key = 'FDN : '
        fdn_list = []
        for cmd in cmds:
            response = self.user.enm_execute(cmd)
            if any(re.search(r'^0\sinstance\(s\)', line, re.I) for line in response.get_output()):
                log.logger.debug("Command {0} failed to find any objects.Response was {1}"
                                 .format(cmd, " ".join(response.get_output())))
                continue
            for line in response.get_output():
                if line.startswith(key):
                    fdn_list.append(line.split(key)[-1])
        return fdn_list[0:num_fdns_required]

    def create_file(self):
        """
        create the file and write fdns to it
        """
        if not filesystem.does_dir_exist(DEFAULT_DIR):
            filesystem.create_dir(DEFAULT_DIR)
        filesystem.touch_file(os.path.join(DEFAULT_DIR, self.fdn_file_name))
        fdns = self.create_list_of_fdns()
        if not fdns:
            raise EnvironError("Fdn list is empty, failed to retrieve FDNs from enm query. "
                               "Please ensure node objects created on ENM deployment.")
        filesystem.write_data_to_file("\n".join(fdns), "{0}{1}".format(DEFAULT_DIR, self.fdn_file_name))

    def create_collection_from_file(self):
        """
        Creates a collection of FDN's on ENM from A file
        """
        log.logger.debug("Attempting to create collection named {0} from file".format(self.name))
        payload = {'name': self.name, 'sharing': self.sharing, 'labels': self.labels,
                   'isCustomTopology': self.custom_topology, 'type': self.type}
        files = {'collection': (None, json.dumps(payload), 'application/json'),
                 'contents': (self.fdn_file_name, open("{0}{1}".format(DEFAULT_DIR, self.fdn_file_name), "rb"),
                              'application/octet-stream')}
        response = self.user.post(CREATE_COLLECTION_FILE_V2, files=files, headers=SECURITY_REQUEST_HEADERS, timeout=300)
        if response.status_code != 201:
            response.raise_for_status()
        self.id = response.json().get('collection').get('id')
        log.logger.debug("Successfully created collection named {0} "
                         "from file with collection id {1}".format(self.name, self.id))

    def update_collection(self, node_poids):
        """
        Updates a Collection on ENM

        :param node_poids: List of node PO IDs
        :type node_poids: list
        """
        log.logger.debug("Attempting to update collection named {0}".format(self.name))
        collection_dict = self.get_collection_by_id(collection_id=self.id).json()
        payload = {"contents": [{"attributes": {}, "id": node_poid} for node_poid in node_poids],
                   "name": collection_dict["name"], "sharing": collection_dict["sharing"],
                   "type": self.type, "isCustomTopology": self.custom_topology}
        response = self.user.put(COLLECTION_ENDPOINT + self.id, json=payload, headers=NETEX_HEADER)
        if response.status_code != 200:
            response.raise_for_status()
        log.logger.debug("Successfully updated collection named {}".format(self.name))

    def update_collection_from_file(self, replace='false'):
        """
        Updates a collection of FDNs on ENM from A file.

        :param replace: flag whether to replace objections in collection or not
        :type replace: str
        """
        log.logger.debug("Attempting to update collection named {0} from file".format(self.name))
        files = {'file': (self.fdn_file_name, open("{0}{1}".format(DEFAULT_DIR, self.fdn_file_name), "rb")),
                 'collectionId': self.id, 'replace': replace}
        response = self.user.put(UPDATE_COLLECTION_FILE_V1, files=files, headers=SECURITY_REQUEST_HEADERS)
        if response.status_code != 201:
            response.raise_for_status()
        log.logger.debug("Successfully updated collection named {0} "
                         "from file with collection id {1}".format(self.name, self.id))

    def get_collection_by_id(self, collection_id=None, include_contents=False):
        """
        Get a collection based on ID , ie. Retrieve a collection based on id
        :param collection_id: collection id of collection to be retrieved
        :type collection_id: str
        :param include_contents: Retrieve contents of the collection or not
        :type include_contents: bool
        :raises EnvironError: when there is no collection_id
        :return: Respnse object
        :rtype: `Response`
        """
        collection_id = collection_id if collection_id else self.id
        log.logger.debug("Attempting to retrieve collection with id {0}.".format(collection_id))
        if not collection_id:
            raise EnvironError("no collection id")
        if include_contents:
            params = {"includeContents": True}
            response = self.user.get(COLLECTION_ENDPOINT + collection_id, params=params,
                                     headers=NETEX_COLLECTION_HEADER)
        else:
            response = self.user.get(COLLECTION_ENDPOINT + collection_id, headers=NETEX_COLLECTION_HEADER)
        if response.status_code != 201:
            response.raise_for_status()
        log.logger.debug("Successfully retrieved collection with id {0}.".format(collection_id))
        return response

    def get_collection_ids_for_delete(self, collection_ids=None):
        """
        Obtain collection ids depending on whether they are present/provided.
        Will search for the collection with the name if ids are not present/provided.

        :param collection_ids: Collection ids if provided
        :type collection_ids: list
        :return: Collection ids after the complete
        :rtype: list
        """
        enm_collection_ids = None
        if collection_ids:
            enm_collection_ids = collection_ids
        elif self.id:
            enm_collection_ids = [self.id]
        if not enm_collection_ids:
            response = get_all_collections(user=self.user).json()
            for collection in response:
                if collection.get("name") == self.name:
                    collection_id = collection.get("id")
                    enm_collection_ids = [collection_id] if collection_id else None
        return enm_collection_ids

    def delete(self, collection_ids=None):
        """
        Deletes a Collection on ENM
        :param collection_ids: List of collection ids
        :type collection_ids: list
        :raises EnmApplicationError: if the response status code is not 204
        :return: Respnse object
        :rtype: `Response`
        """
        log.logger.debug("Attempting to delete collection(s).")
        enm_collection_ids = self.get_collection_ids_for_delete(collection_ids)
        # Check that the id is not None
        if enm_collection_ids:
            log.logger.debug("Collection id(s) to be deleted - {0}.".format(enm_collection_ids))
            response = self.user.delete_request(COLLECTION_ENDPOINT, json={"collectionIds": enm_collection_ids},
                                                headers=NETEX_COLLECTION_HEADER)
            response.raise_for_status()
            if self.id:
                self.id = None
            if response.status_code == 204:
                log.logger.debug("Successfully deleted collection(s).")
            else:
                log.logger.debug("Collection delete failed either partially/completely. "
                                 "Response is - {0}".format(response.json()))
            return response
        else:
            log.logger.debug("No matching Collection id(s) to be deleted.")


class Search(object):
    SEARCH_QUERY_ENDPOINT = "/managedObjects/query?searchQuery={0}"
    SEARCH_QUERY_ENDPOINT_V2 = "/managedObjects/search/v2?query={0}"
    SAVE_SEARCH_ENDPOINT = "/topologyCollections/savedSearches/"
    SAVE_SEARCH_ENDPOINT_FORMATTED = SAVE_SEARCH_ENDPOINT + "{}"

    def __init__(self, user, query, name=None, nodes=None, category="Public", version="v1"):
        """
        Constructor for Search Object

        :type query: string
        :param query: netex query to use to filter nodes
        :type name: str
        :param name: Name of the displayed saved search in ENM
        :type nodes: list
        :param nodes: List of nodes we want to add to collection
        :type category: string
        :param category: Category of the saved search. Private or Public
        :type user : enm_user.User object
        :param user: user we use to create the Collection
        :type version: str
        :param version: Version of network explorer search API to be used
        """
        self.name = name.lower() if name else query.lower()
        self.query = query
        self.node_ids = None if not nodes else [node.node_id for node in nodes]
        self.user = user
        self.category = category
        self.headers_dict = JSON_SECURITY_REQUEST
        self.id = None
        self.version = version

    def _teardown(self):
        """
        Secret teardown method
        """
        self.delete()

    @classmethod
    def query_enm_netex(cls, query, user, **kwargs):
        """
        Run query on ENM.

        :param query: query to be added to the SEARCH_QUERY_ENDPOINT and run
        :type query: str
        :param user: User who will perform the query
        :type user: `enm_user_2.User`
        :param kwargs: Builtin magic method
        :type kwargs: dict

        :return: Result of the query
        :rtype: `Response` object
        """
        query_with_no_spaces = "%20".join(query.split())
        additional_options = '' if not kwargs else '&' + '&'.join(
            [str(k + '=' + kwargs[k]) for k in kwargs if k not in ('version', 'timeout')])
        query = query_with_no_spaces + additional_options
        timeout = kwargs.get("timeout", 120)
        if 'version' in kwargs and kwargs['version'] == 'v2':
            response = user.get(cls.SEARCH_QUERY_ENDPOINT_V2.format(query), profile_name=kwargs.get('profile_name'),
                                headers=NETEX_HEADER, timeout=timeout)
        else:
            response = user.get(cls.SEARCH_QUERY_ENDPOINT.format(query), profile_name=kwargs.get('profile_name'),
                                headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            response.raise_for_status()

        return response

    def execute(self, **kwargs):
        """
        Executes netex search query

        :raises: HTTPError
        :rtype: dict
        :returns: json dict of nodes that are returned from the search query
        """
        response = self.query_enm_netex(self.query, self.user, version=self.version, **kwargs)

        if self.version == "v1":
            node_mos = {}
            for json_node in response.json():
                if not self.node_ids or json_node['moName'] in self.node_ids:
                    node_mos[json_node['moName']] = json_node

            if not node_mos:
                log.logger.debug("No nodes found for '{0}' search query".format(self.query))

            return node_mos
        else:
            return response.json()

    def save(self):
        """
        Creates a Saved Search on ENM

        :raises: HTTPError
        """
        payload = {"name": self.name, "category": self.category, "searchQuery": self.query}
        response = self.user.post(self.SAVE_SEARCH_ENDPOINT, json=payload, headers=self.headers_dict)

        if response.status_code != 200:
            response.raise_for_status()

        self.id = response.text
        log.logger.debug("Successfully saved search named {0}".format(self.name))

    def delete(self):
        """
        Deletes a Saved Search on ENM.

        :raises: HTTPError
        """
        # Get the search ID if None

        if not self.id:
            response = self._get_saved_searches()
            for json_node in response.json():
                if self.name == json_node['name']:
                    self.id = json_node['poId']
                    break
        if self.id:
            response = self.user.delete_request(self.SAVE_SEARCH_ENDPOINT_FORMATTED.format(self.id))
            if response.status_code != 200:
                response.raise_for_status()
            log.logger.debug("Successfully deleted saved search named {0}".format(self.name))

    def _get_saved_searches(self):
        """
        Gets all saved searches

        :raises: HTTPError

        :rtype: Response object
        :return: `Response` object
        """
        response = self.user.get(self.SAVE_SEARCH_ENDPOINT, headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()
        return response

    def get_saved_search_by_id(self):
        """
        Get a saved search based on ID

        :return: Response object
        :rtype: `Response` object
        """
        response = self.user.get(self.SAVE_SEARCH_ENDPOINT + self.id, headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()
        return response

    @property
    def exists(self):
        """
        Check if the saved search exists in ENM, when name is given

        :return: Boolean indicating if the saved search exists in ENM
        :rtype: bool
        """
        exists = False
        searches = self._get_saved_searches().json()
        if any([self.name == _.get('name') for _ in searches]):
            exists = True
        return exists


def get_all_enm_network_elements(user, fullMo='false'):
    """
    Get all NetworkElement objects from ENM

    :param user: object to be used to make http requests
    :type user: `enm_user_2.User`
    :param fullMo: Boolean flag indicating whether or not query with request full MO
    :type fullMo: str

    :return: Result of the query
    :rtype: `Response` object
    """
    return Search.query_enm_netex('select NetworkElement', user, fullMo=fullMo)


def get_pos_by_poids(user, poList=None, attributeMappings=None, payload=None):
    """
    Make POST request to getPosByPoIds netex endpoint

    :param user: object to be used to make http requests
    :type user: `enm_user_2.User`
    :param poList: List of POIDS
    :type poList: list
    :param attributeMappings: List of dict(s) of attribute mappings
    :type attributeMappings: list
    :param payload: Payload to be sent as part of the POST request
    :type payload: dict

    :return: Result of the query
    :rtype: `Response` object
    """
    payload = payload or {
        "attributeMappings": attributeMappings or [
            {
                "moType": "NetworkElement",
                "attributeNames": [
                    "neType"
                ]
            }
        ],
        "poList": poList
    }

    response = user.post(GET_POS_BY_POID_URL, data=json.dumps(payload), headers=JSON_SECURITY_REQUEST)

    if not response.ok:
        response.raise_for_status()

    return response


class NetexFlow(object):
    NETEX_APP_HELP_URLS = ["#help/app/networkexplorer/topic/tutorials/search",
                           "#help/app/networkexplorer/topic/tutorials/collections",
                           "#help/app/networkexplorer/topic/tutorials/savedSearches",
                           "#help/app/networkexplorer/topic/tutorials/otherApplications"]

    def __init__(self, profile, user, query, **kwargs):
        """
        Constructor for NetexFlow object.

        :param profile: profile object
        :type profile: enmutils_int.profile.Profile
        :param user: user object
        :type user: enm_user_2.User object
        :param query: a search query
        :type query: str
        :param kwargs: dictionary of key word arguments
                       collection: an enm collection
                       saved_search: an enm saved search
                       erbs_collection: an enm collection
        :type kwargs: dict
        """
        self.profile = profile
        self.user = user
        self.query = query
        self.large_collection = kwargs.get("large_collection")
        self.small_collection = kwargs.get("small_collection")
        self.saved_search = kwargs.get("saved_search")
        self.version = kwargs.get("version", "v2")
        self.execute_query = True

    def _navigate_netex_app_help(self):
        for url in self.NETEX_APP_HELP_URLS:
            self.user.get(url)
            self._sleep()

    @staticmethod
    def _sleep(sec=1):
        log.logger.debug("Sleeping for {0} second(s).".format(sec))
        time.sleep(sec)

    def collection_query_flow(self, collection):
        """
        Validate whether collection exists or not
        :param collection: collection where the query is performed
        :type collection: `enmutils_int.lib.netex.Collection`
        """
        if collection.id:
            self.user.get("/#networkexplorer/collection/{collection_id}"
                          .format(collection_id=collection.id))
            log.logger.info("Executing query on collection - {0}".format(collection.name))
            self._sleep()
        else:
            self.execute_query = False
            self.profile.add_error_as_exception(EnmApplicationError("Collection ({0}) may not have been "
                                                                    "created cannot execute query"
                                                                    .format(collection.name)))

    def search_query_flow(self, saved_search):
        """
        Validate whether saved search exists or not
        :param saved_search: saved search where the query is performed
        :type saved_search: `enmutils_int.lib.netex.Search`
        """
        if saved_search.id:
            self.user.get("/#networkexplorer/savedsearch/{saved_search_id}"
                          .format(saved_search_id=saved_search.id))
            log.logger.info("Executing query on saved search - {0}".format(saved_search.name))
            self._sleep()
        else:
            self.execute_query = False
            self.profile.add_error_as_exception(EnmApplicationError("Collection ({0}) may not have been "
                                                                    "created cannot execute query"
                                                                    .format(saved_search.name)))

    def query_on_partial_node_name(self):
        """
        Formats the search query for partial node name.
        """
        small_collection_response = self.small_collection.get_collection_by_id(collection_id=self.small_collection.id,
                                                                               include_contents=True)
        if not small_collection_response or not small_collection_response.text:
            raise EnmApplicationError("ENM service failed to return a valid response, "
                                      "unable to get collection given collection id.")
        small_collection_dict = small_collection_response.json()
        if "contents" in small_collection_dict and small_collection_dict["contents"]:
            random_node_poid = random.choice(small_collection_dict["contents"])["id"]
            random_node_po_data = get_pos_by_poids(self.user, [random_node_poid])
            if not random_node_po_data or not random_node_po_data.text and not random_node_po_data.status_code == 200:
                raise EnmApplicationError("ENM service failed to return a valid response, Response status_code {0} "
                                          "unable to get pos from poids.".format(random_node_po_data.statuscode))
            random_node_po_dict = random_node_po_data.json()
            if random_node_po_dict and "moName" in random_node_po_dict[0]:
                random_node_name = random_node_po_dict[0]["moName"]
            else:
                raise EnmApplicationError("ENM service failed to return a valid response, "
                                          "unable to retrieve node name from the response.")
            if "ieatnetsimv" in random_node_name:
                partial_node_regex = random_node_name[:23]
            elif "CORE" in random_node_name:
                partial_node_regex = random_node_name[:6]
            elif "NR" in random_node_name:
                partial_node_regex = random_node_name[:4]
            else:
                partial_node_regex = random_node_name[:5]
            self.query = self.query.format(partial_node_regex=partial_node_regex)
        else:
            raise EnvironWarning("Error in partial node name search since there are "
                                 "no node objects found in - {0}".format(self.small_collection.name))

    def execute_flow(self):
        """
        Format search query and perform the search
        """
        try:
            if "{large_collection_name}" in self.query:
                self.query = self.query.format(large_collection_name=self.large_collection.name)
                self.collection_query_flow(self.large_collection)
            if "{small_collection_name}" in self.query:
                self.query = self.query.format(small_collection_name=self.small_collection.name)
                self.collection_query_flow(self.small_collection)
            if "{saved_search_name}" in self.query:
                self.query = self.query.format(saved_search_name=self.saved_search.name)
                self.search_query_flow(self.saved_search)
            if self.execute_query:
                log.logger.debug(
                    "Attempting to execute query - {0} with user - {1}.".format(self.query, self.user.username))
                if "{partial_node_regex}" in self.query:
                    self.query_on_partial_node_name()
                Search(query=self.query, user=self.user, version=self.version).execute()
                log.logger.debug(
                    "Query - {0} executed successfully with user - {1}.".format(self.query, self.user.username))
                self._sleep()
        except Exception as e:
            self.profile.add_error_as_exception(e)


def search_and_create_collection(profile, user, search_query, collection_name, nodes, num_nodes=10000, **kwargs):
    """
    Execute a search via network explorer, and create, and save the returned collection of nodes

    :param profile: Profile object using the saved search
    :type profile: `enmutils_int.lib.profile.Profile`
    :param user: Enm user who will create/own the collection
    :type user: `enm_user_2.User`
    :param search_query: Query to be executed to create collection
    :type search_query: str
    :param collection_name: Name used to display and retrieve the collection
    :type collection_name: str
    :param nodes: List of nodes to be used in the collection
    :type nodes: list
    :param num_nodes: Maximum number of nodes to include
    :type num_nodes: int
    :param kwargs: Keyword arguments
                    delete_existing: Boolean flag determining,
                                     whether or not to check/delete collection if it exists.
                                     Default value is False
                    labels: List of labels to the collection to be created.
                            Default value is None
                    num_results: Limit for the number of results when no nodes are provided (Integer)
                                 Default value is 10000
                    parent_ids: List of parent ids to the collection to be created.
                                Default value is None
                    teardown: Boolean flag whether to add collection to profile teardown
                              Default value is True
    :type kwargs: dict

    :return: Tuple containing `netex.Collection`, `netex.Collection`
    :rtype: tuple
    """
    delete_existing = kwargs.get("delete_existing", False)
    labels = kwargs.get("labels", None)
    num_results = kwargs.get("num_results", 10000)
    parent_ids = kwargs.get("parent_ids", None)
    teardown = kwargs.get("teardown", True)
    if nodes:
        nodes = nodes[:num_nodes]
        network_collection = Collection(user=user, name=collection_name, nodes=nodes, query=search_query,
                                        parent_ids=parent_ids, labels=labels)
    else:
        network_collection = Collection(user=user, name=collection_name, nodes=[], query=search_query,
                                        num_results=num_results, parent_ids=parent_ids, labels=labels)
    teardown_collection = None
    if teardown:
        teardown_collection = network_collection
    try:
        search_collections_response = get_all_collections(user=user).json()
        if delete_existing and any([collection_name == _.get('name') for _ in search_collections_response]):
            log.logger.debug("A collection already exists with the same name - {0}. "
                             "Attempting to delete it.".format(collection_name))
            admin_collection = Collection(user=user, name=collection_name, nodes=nodes, query=search_query)
            admin_collection.delete()
            log.logger.debug("Successfully deleted collection already existing "
                             "with the same name - {0}.".format(collection_name))
        network_collection.create()
        if teardown:
            teardown_collection.id = network_collection.id
            profile.teardown_list.append(teardown_collection)
    except Exception as e:
        profile.add_error_as_exception(EnmApplicationError(e))

    return network_collection, teardown_collection


def search_and_save(profile, user, search_query, search_name, nodes, **kwargs):
    """
    Execute and save a search via network explorer

    :param profile: Profile object using the saved search
    :type profile: `enmutils_int.lib.profile.Profile`
    :param user: Enm user who will create/own the saved search
    :type user: `enm_user_2.User`
    :param search_query: Query to be executed to create the saved search
    :type search_query: str
    :param search_name: Name used to display and retrieve the saved search
    :type search_name: str
    :param nodes: List of nodes to be used in the search query
    :type nodes: list
    :param kwargs: dictionary of parameters or keyword arguments
            num_nodes: Maximum number of nodes to include
            delete_existing: Boolean flag determining, whether or not to check/delete search if it exists
    :type kwargs:dict

    :return: Tuple containing `netex.Search`, `netex.Search`
    :rtype: tuple
    """
    delete_existing = kwargs.get("delete_existing", False)
    version = kwargs.get("version", "v2")

    if not nodes:
        saved_search = Search(user=user, query=search_query, name=search_name, version=version)
    else:
        num_nodes = kwargs.get("num_nodes", 10000)
        nodes = nodes[:num_nodes]
        saved_search = Search(user=user, query=search_query, name=search_name, nodes=nodes, version=version)

    teardown_search = Search(user=user, query=search_query, name=search_name, version=version)

    try:
        if delete_existing:
            saved_search.delete()
        saved_search.execute()
        saved_search.save()
        teardown_search.id = saved_search.id
        profile.teardown_list.append(teardown_search)
    except Exception as e:
        profile.add_error_as_exception(e)

    return saved_search, teardown_search


def export_collections(user, collection_ids, nested=False):
    """
    Send request to export collections

    :param user: ENM user
    :type user: `enm_user_2.User`
    :param collection_ids: ids of collections to be exported
    :type collection_ids: list
    :param nested: Type of collection whether nested or not
    :type nested: bool
    :return: Response object from ENM request
    :rtype: `http.Response`
    """
    log.logger.debug("Attempting to initiate export of collections.")
    payload = {"collections": collection_ids}
    if nested:
        response = user.post(EXPORT_CUSTOM_TOPOLOGY_URL,
                             json=payload, headers=JSON_SECURITY_REQUEST)
    else:
        response = user.post(EXPORT_COLLECTION_URL,
                             json=payload, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    log.logger.debug("Successfully initiated export of collections "
                     "with session id - {0} .".format(response.json()["sessionId"]))
    return response


def get_status_of_export_collections(user, session_id):
    """
    Get status of export collections

    :param user: ENM user
    :type user: `enm_user_2.User`
    :param session_id: session id
    :type session_id: str
    :return: Response object from ENM request
    :rtype: `http.Response`
    """
    log.logger.debug("Attempting to retrieve status of export of collections.")
    response = user.get(EXPORT_COLLECTION_STATUS_URL + session_id, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    log.logger.debug("Successfully retrieved status of export of collections.")
    return response


def initiate_export_collections(profile, user, collection_ids, nested=False):
    """
    Initiate export collections and get the session id to check status of export

    :param profile: Profile object using the saved search
    :type profile: `enmutils_int.lib.profile.Profile`
    :param user: ENM user
    :type user: `enm_user_2.User`
    :param collection_ids: ids of collections to be exported
    :type collection_ids: list
    :param nested: Type of collection whether nested or not
    :type nested: bool
    :return: session id to check status of export
    :rtype: str
    """
    session_id = None
    try:
        if nested:
            export_response = export_collections(user=user, collection_ids=collection_ids, nested=True)
        else:
            export_response = export_collections(user=user, collection_ids=collection_ids, nested=False)
    except Exception:
        profile.add_error_as_exception(EnmApplicationError("Unable to initiate export of collections."))
    else:
        session_id = export_response.json()["sessionId"]
    return session_id


def retrieve_export_collection_status(profile, user, session_id, num_attempts=NUM_ATTEMPTS_EXPORT_COLLECTION_STATUS):
    """
    Periodically retrieve status of export collections until it gets completed

    :param profile: Profile object using the saved search
    :type profile: `enmutils_int.lib.profile.Profile`
    :param user: ENM user
    :type user: `enm_user_2.User`
    :param session_id: session id to check status of export
    :type session_id: str
    :param num_attempts: Number of attempts to retry for status of export collections
    :type num_attempts: int
    """
    attempt = 0
    while attempt < num_attempts:
        attempt += 1
        try:
            export_status_response = get_status_of_export_collections(user=user, session_id=session_id)
            export_status = export_status_response.json()["status"]
            if "COMPLETED" in export_status:
                log.logger.debug("Export of collections has been completed.")
                break
        except Exception:
            profile.add_error_as_exception(EnmApplicationError("Unable to get status for export of collections."))
        log.logger.debug("Sleeping {0} seconds before retrying as the export collection status "
                         "is not yet complete.".format(SLEEP_TIME_EXPORT_COLLECTION_STATUS))
        time.sleep(SLEEP_TIME_EXPORT_COLLECTION_STATUS)
    else:
        profile.add_error_as_exception(
            EnmApplicationError("Export of collections could not be completed even after "
                                "{0} attempts and {1} seconds after export collections "
                                "has been initiated.".format(num_attempts,
                                                             num_attempts * SLEEP_TIME_EXPORT_COLLECTION_STATUS)))


def download_exported_collections(user, session_id):
    """
    Download the exported collections file through REST calls.

    :param user: ENM user
    :type user: `enm_user_2.User`
    :param session_id: session id
    :type session_id: str
    :return: Response object from ENM request
    :rtype: `http.Response`
    """
    log.logger.debug("Attempting to download the exported collections file.")
    response = user.get(DOWNLOAD_COLLECTION_URL + session_id, headers=SECURITY_REQUEST_HEADERS)
    response.raise_for_status()
    log.logger.debug("Successfully downloaded the exported collections file.")
    return response


def initiate_import_collections(user, file_name):
    """
    Initiate import collections and get the session id to check status of import.

    :param user: ENM user
    :type user: `enm_user_2.User`
    :param file_name: File from which collections are to be imported
    :type file_name: str
    :return: session id
    :rtype: str
    """
    log.logger.debug("Attempting to initiate import of collections.")
    files = {'file': (file_name, open("{0}{1}".format(EXPORT_DIR, file_name), "rb"),
                      'application/x-zip-compressed')}
    response = user.post(IMPORT_COLLECTION_URL, files=files, headers=NETEX_IMPORT_HEADER, timeout=300)
    response.raise_for_status()
    log.logger.debug("Initiated import of collections.")
    return response.json()["sessionId"]


def get_status_of_import_collections(user, session_id):
    """
    Get status of import collections.

    :param user: ENM user
    :type user: `enm_user_2.User`
    :param session_id: session id
    :type session_id: str
    :return: Response object from ENM request
    :rtype: `http.Response`
    """
    log.logger.debug("Attempting to retrieve status of import of collections.")
    response = user.get(IMPORT_COLLECTION_URL + session_id, headers=NETEX_HEADER)
    response.raise_for_status()
    log.logger.debug("Successfully retrieved status of import of collections.")
    return response


def retrieve_import_collection_status(profile, user, session_id, num_attempts=NUM_ATTEMPTS_IMPORT_COLLECTION_STATUS):
    """
    Periodically retrieve status of import collections until it gets completed.

    :param profile: Profile object using the saved search
    :type profile: `enmutils_int.lib.profile.Profile`
    :param user: ENM user
    :type user: `enm_user_2.User`
    :param session_id: session id to check status of export
    :type session_id: str
    :param num_attempts: Number of attempts to retry for status of export collections
    :type num_attempts: int
    """
    attempt = 0
    num_errors_format = 0
    num_errors_rest = 0
    rest_exception = None
    while attempt < num_attempts:
        attempt += 1
        try:
            import_status_response = get_status_of_import_collections(user=user, session_id=session_id)
            import_status_json_response = import_status_response.json()
            if not import_status_json_response:
                num_errors_format += 1
                continue
            log.logger.debug("Response content for import status - {0}".format(import_status_json_response))
            import_status = import_status_json_response.get('status')
            if "COMPLETED" in import_status:
                log.logger.debug("Import of collections has been completed.")
                break
        except Exception as rest_exception:
            num_errors_rest += 1
        log.logger.debug("Sleeping {0} seconds before retrying as the import collection status "
                         "is not yet complete.".format(SLEEP_TIME_IMPORT_COLLECTION_STATUS))
        time.sleep(SLEEP_TIME_IMPORT_COLLECTION_STATUS)
    else:
        handle_errors_in_retreive_import_collection_status(num_errors_format, num_errors_rest, num_attempts,
                                                           rest_exception, profile)


def handle_errors_in_retreive_import_collection_status(num_errors_format, num_errors_rest, num_attempts, rest_exception,
                                                       profile):
    """
    Handle errors in retrieving status of import collections.

    :param num_errors_format: Number of errors found in the unexpected format.
    :type num_errors_format: int
    :param num_errors_rest: Number of errors found in the REST calls.
    :type num_errors_rest: int
    :param num_attempts: Number of attempts
    :type num_attempts: int
    :param rest_exception: Exception object from API calls
    :type rest_exception: Exception
    :param profile: Profile to add errors to
    :type profile: `enmutils_int.lib.profile.Profile`
    """
    if num_errors_format:
        log.logger.debug("The import of collections response is not in an expected "
                         "format in {0}/{1} attempts.".format(num_errors_format, num_attempts))
    if num_errors_rest:
        log.logger.debug("Unable to get status for import of collections through API "
                         "in {0}/{1} attempts. Most recent error string "
                         "is. - {2}".format(num_errors_rest, num_attempts, str(rest_exception)))
    profile.add_error_as_exception(
        EnmApplicationError("Import of collections could not be completed even after "
                            "{0} attempts and {1} seconds after import collections "
                            "has been initiated.".format(num_attempts,
                                                         num_attempts * SLEEP_TIME_IMPORT_COLLECTION_STATUS)))


def create_export_dir_and_file(data, file_name):
    """
    Create the export directory and file.

    :param data: data to be used to create export file
    :type data: str
    :param file_name: File name for the export
    :type file_name: str
    """
    log.logger.debug("Attempting to create the export file - {0} "
                     "in the directory - {1}.".format(file_name, EXPORT_DIR))
    output_file = os.path.join(EXPORT_DIR, file_name)
    filesystem.write_data_to_file(data, output_file)
    log.logger.debug("Successfully created the export file - {0} "
                     "in the directory - {1}.".format(file_name, EXPORT_DIR))
