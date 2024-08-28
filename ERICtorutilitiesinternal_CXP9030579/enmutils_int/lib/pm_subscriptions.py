# ********************************************************************
# Name    : PM Subscriptions
# Summary : Main Performance Management module. Responsible for all
#           aspects for PM subscription operations, querying,
#           creation, deletion, updating of all types of PM
#           subscriptions (CellTrace, Statistical...), counter
#           management, node validation, activation and deactivation
#           and clean up of subscriptions.
# ********************************************************************

import datetime
import json
import re
import time
from random import sample
from urlparse import urljoin

from enmutils.lib import log, mutexer
from enmutils.lib.exceptions import (TimeOutError, SubscriptionCreationError, EnmApplicationError, EnvironError)
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.flexible_counter_management import get_ebs_flex_counters, get_reserved_ebsn_flex_counters
from enmutils_int.lib.load_node import annotate_fdn_poid_return_node_objects
from enmutils_int.lib.pm_counters import get_tech_domain_counters_based_on_profile
from requests.exceptions import HTTPError


class Subscription(object):
    BASE_URL = '/pm-service/rest/subscription/'
    UPDATE_URL = urljoin(BASE_URL, '{subscription_id}/')
    SUPPORTED_POST_ENDPOINTS = ['activate', 'deactivate']
    SUPPORTED_SUBSCRIPTION_STATES = ['INACTIVE', 'ACTIVE']
    NODE_REPORTS_URL = '/pm-service/rest/nodereports/?type=list'
    PM_FUNCTION_URL = '/pm-service/rest/subscription/nodePmEnabled'
    COUNTERS_URL = "/pm-service/rest/pmsubscription/counters?mim={model_identities}&definer={definer}"
    POLLING_URL = "/pm-service/rest/subscription/"
    CORBA_ERROR_URL = "/pm-service/rest/nodereports/errors/corba"
    SUBSCRIPTION_ERROR_DETAILS_URL = "/pm-service/rest/nodereports/?type=sub&id={0}"
    GET_POS_BY_POID_URL = "/managedObjects/getPosByPoIds"

    SCANNER_COUNT_THRESHOLD_PERCENTAGES = {"activation": 90, "deactivation": 10}
    NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE = 1000
    MAX_MINUTES_TO_WAIT_FOR_SCANNERS = 30
    SLEEP_SECONDS_BETWEEN_CHECKING_SCANNERS = 60
    WAIT_TIME_MINS_IF_NO_SCANNER_STATE_CHANGE = 5
    DEFAULT_SCANNER_MASTER_POLLING_INTERVAL_MINS = 15

    def __init__(self, name, **kwargs):
        """
        Subscription Constructor.
        :param name: str representing the name of the subscription
        :type name: str
        :param kwargs: keyword arguments
        :type kwargs: dict
        """
        self.name = name
        self.description = kwargs.get("description", "WORKLOAD TESTING")
        self.user = kwargs.get("user", None)
        self.mo_class_counters_excluded = kwargs.get("mo_class_counters_excluded", None)
        self.technology_domain_counter_limits = kwargs.get("technology_domain_counter_limits", None)
        self.nodes = kwargs.get("nodes", None)
        self.parsed_nodes = None
        self.counters_events = None
        self.rop_enum = kwargs.get("rop_enum", "FIFTEEN_MIN")
        self.timeout = kwargs.get("timeout", 50 * 60)
        self.wait_for_state_sleep_seconds = kwargs.get("wait_for_state_sleep_seconds", 20)
        self.num_counters = None
        self.id = None
        self.corba_error_map = None
        self.number_of_nodes_attached_to_subscription = 0
        self.poll_scanners = False
        self.truncated_nodes_count = 100
        self.mo_class_counters_included = kwargs.get("mo_class_counters_included", None)
        self.mo_class_sub_counters_included = kwargs.get("mo_class_sub_counters_included", None)
        self.definer = kwargs.get("definer", None)
        self.cell_trace_category = kwargs.get("cell_trace_category", None)
        self.event_filter = kwargs.pop('event_filter', None)
        self.reserved_counters = kwargs.get("reserved_counters")
        self.ebs_events = kwargs.get("ebs_events", None)
        self.technology_domain = kwargs.get("technology_domain", None)
        self.node_types = kwargs.get("node_types", [])

    def _get_pos_by_poids(self, poids, attributes=None):
        """
        Gets node information from enm
        The function simulates the netex request by requesting nodes in batches of 250 nodes
        :param poids: list of node poids
        :type poids: list
        :param attributes: extra node attributes you want to get from the request
        :type attributes: list
        :return: list of nodes in dictionary format
        :rtype: list
        """
        log.logger.debug("Validating POID's")
        attributes = [] if not attributes else attributes
        attributes.extend(["neType", "ossModelIdentity", "technologyDomain"])
        enm_nodes = []

        data = {"poList": poids,
                "defaultMappings": ["syncStatus"],
                "attributeMappings": [{"moType": "NetworkElement",
                                       "attributeNames": attributes}]}

        for poid_batch in self._poid_batch_generator(poids):
            data["poList"] = poid_batch
            response = self.user.post(self.GET_POS_BY_POID_URL, json=data, headers=JSON_SECURITY_REQUEST)

            if not response.ok:
                response.raise_for_status()
            else:
                enm_nodes.extend(response.json())

        enm_nodes = self._validate_nodes_oss_model_identity(enm_nodes)

        return {int(node["poId"]): node for node in enm_nodes}

    def _poid_batch_generator(self, poids, batch_size=250):
        """
        Generates batches of POID's from list

        :param poids: List of PO ID's
        :type poids: list
        :param batch_size: Batch Size
        :type batch_size: int
        """
        for batch in range(0, len(poids), batch_size):
            yield poids[batch:min(batch + batch_size, len(poids))]

    @staticmethod
    def log_pm_disabled_nodes(json_nodes):
        """
        Check for PM disabled nodes and log the output if any
        """
        pm_disabled_nodes = {}
        log.logger.debug("Total number of nodes in response received\t{0}.".format(len(json_nodes)))
        for node in json_nodes.keys():
            if json_nodes.get(node).get("pmFunction") != "ON":
                pm_disabled_nodes[node] = json_nodes.get(node).get("pmFunction")
        if pm_disabled_nodes:
            log.logger.debug("A total of {0} nodes have returned a PMFunction not equal to 'ON'.\n{1}\n"
                             .format(len(pm_disabled_nodes.keys()), pm_disabled_nodes))

    def get_nodes_pm_function(self):
        """
        Get PmFunction for nodes and filter out those with PmFunction disabled

        returns: dict of node names with PmFunction enabled
        """
        log.logger.debug("Fetching PM Function status for nodes from ENM - started")
        attribute_mappings_response = self._get_pos_by_poids([node.poid for node in self.nodes])

        if not attribute_mappings_response:
            raise EnvironError("No valid nodes available after validation process, check logs for details")

        data = [{"fdn": "NetworkElement={0}".format(node.node_id), "poid": node.poid,
                 "mimInfo": attribute_mappings_response[int(node.poid)]["attributes"]["ossModelIdentity"],
                 "nodeType": (getattr(node, "NE_TYPE", node.primary_type) if
                              getattr(node, "NE_TYPE", node.primary_type) != 'MINI-LINK-Outdoor' else 'MINI-LINK-6352'),
                 "pmFunction": "",
                 "technologyDomain": attribute_mappings_response[int(node.poid)]["attributes"]["technologyDomain"]}
                for node in self.nodes if int(node.poid) in attribute_mappings_response]

        log.logger.info("Performing POST operation (to get PmFunction states for {0} nodes) on URL: {1} with data: "
                        "{2} ...".format(len(data), Subscription.PM_FUNCTION_URL, data[:10]))
        response = self.user.post(Subscription.PM_FUNCTION_URL, json=data, headers=JSON_SECURITY_REQUEST)

        if not response.ok:
            response.raise_for_status()

        log.logger.info("Parsing response received from ENM (which contained {0} nodes) to only include nodes with "
                        "PmFunction enabled".format(len(response.json())))

        json_nodes = {node["fdn"].split("=")[1]: node for node in response.json()}
        self.log_pm_disabled_nodes(json_nodes)
        self.parsed_nodes = [{'fdn': "NetworkElement={0}".format(node.node_id),
                              'id': json_nodes[node.node_id].get("poid"),
                              'ossModelIdentity': json_nodes[node.node_id].get("mimInfo"),
                              'neType': json_nodes[node.node_id].get("nodeType"),
                              'pmFunction': json_nodes[node.node_id].get("pmFunction"),
                              'technologyDomain': json_nodes[node.node_id].get("technologyDomain", [])}
                             for node in self.nodes if node.node_id in json_nodes and
                             json_nodes[node.node_id].get("pmFunction") == "ON"]

        if not self.parsed_nodes:
            raise EnvironError("No valid nodes available with PmFunction enabled")

        if len(response.json()) != len(self.parsed_nodes):
            log.logger.debug("Some selected nodes have PmFunction disabled and were removed from supplied list")

        log.logger.debug("Fetching PM Function status for nodes from ENM - completed")
        return self.parsed_nodes

    @property
    def nodes_list(self):
        self.nodes = annotate_fdn_poid_return_node_objects(self.nodes)
        self.get_nodes_pm_function()
        return self.parsed_nodes

    @staticmethod
    def _validate_nodes_oss_model_identity(nodes):
        """
        Checks for missing oss model identity.
        :param nodes: nodes list
        :type nodes: list
        :return: valid nodes dict
        :rtype: dict
        :raises EnvironError: if node no longer exists on ENM
        """
        log.logger.debug("Validating the OSS Model Id's")
        valid_nodes = []
        invalid_nodes = []
        check_params = {"neType": "", "ossModelIdentity": ""}
        for node in nodes:
            if node.get("moName") == "Deleted":
                message = ("ENM reports that supplied node has already been deleted - "
                           "potential POID mismatch between nodes in Workload Pool and those on ENM")
                log.logger.debug("{0}. Node info: {1}".format(message, node))
                raise EnvironError(message)
            for param in check_params:
                check_params[param] = node["attributes"][param] if param in node["attributes"] else None
            unsynced_node_types_status = ("MSC" not in check_params["neType"] and
                                          "MINI-LINK-6352" not in check_params["neType"] and
                                          "MINI-LINK-Indoor" not in check_params["neType"] and
                                          "CUDB" not in check_params["neType"])

            if not check_params["ossModelIdentity"] and unsynced_node_types_status:
                invalid_nodes.append(node.get("moName"))
            else:
                valid_nodes.append(node)
        log.logger.debug(
            "{} nodes with invalid oss model identity removed from subscription: {}".format(len(invalid_nodes),
                                                                                            invalid_nodes))
        return valid_nodes

    @property
    def ne_types(self):
        return list(set(getattr(node, 'NE_TYPE', node.primary_type) for node in self.nodes))

    def _post(self, endpoint):
        """
        Performs the actual REST request (operation) on Subscription

        :param endpoint: Operation to be performed on Subscript
        :type endpoint: str
        :raises HTTPError: Raises exception if ENM doesnt return proper response
        """
        log.logger.debug("Performing _post() functionality")

        log.logger.debug("1. Fetching current details for subscription {0} from ENM".format(self.name))
        subscription_data = self.get_subscription()

        if not self.id:
            self.id = subscription_data.get("id")
        payload = {'persistenceTime': subscription_data.get('persistenceTime')}
        url = urljoin(self.UPDATE_URL, endpoint).format(subscription_id=self.id)

        log.logger.debug("2. Performing POST operation ({0}) on subscription {1} towards ENM using URL: {2} "
                         "with data: {3}".format(endpoint, self.name, url, payload))

        response = self.user.post(url, data=json.dumps(payload), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError("Could not perform operation '{0}' on subscription '{1}'"
                            .format(endpoint, self.name), response=response)
        log.logger.debug("Successfully completed operation '{0}' for subscription '{1}' ({2})"
                         .format(endpoint, self.name, self.id))

    def _activate(self, validate=True):
        """
        Activates a subscription
        """
        log.logger.debug("Performing activation")
        self._post(endpoint=self.SUPPORTED_POST_ENDPOINTS[0])  # activate

        if validate:
            log.logger.debug("Checking ENM to determine if subscription {0} is {1}"
                             .format(self.name, self.SUPPORTED_SUBSCRIPTION_STATES[1]))  # ACTIVE
            self.wait_for_state(self.SUPPORTED_SUBSCRIPTION_STATES[1])  # ACTIVE
            log.logger.debug("Successfully activated subscription '{0}' ({1})".format(self.name, self.id))

    def activate(self, validate=True):
        """
        Activates a subscription using a mutex depending if poll_scanners is set on subscription or not
        """
        log.logger.debug("Checking if scanner poll is required then activating subscription")

        if self._is_scanner_poll_required():
            log.logger.debug("Getting scanners status associated with current subscription")
            self.check_scanner_status()

            log.logger.debug("As Scanner Poll is required here, this profile will attempt to obtain the subscription "
                             "activation lock to prevent other large subscriptions from "
                             "being activated (by other profiles) at the same time which could overload PMIC on ENM")
            with mutexer.mutex("pmic_subscription_activation_deactivation", persisted=True, log_output=True,
                               timeout=60 * self.MAX_MINUTES_TO_WAIT_FOR_SCANNERS + 5):

                self._activate(validate)

                self._wait_for_scanners(action="activation")

        else:
            log.logger.debug("No Scanner Poll is required")
            self._activate(validate)

    def check_scanner_status(self):
        """
        check for active scanners and wait till they are de-activated
        """
        log.logger.debug("Checking scanners' status")
        if self._get_number_of_active_scanners():
            self._wait_for_scanners(action="deactivation")
        else:
            log.logger.debug("No active scanners found")

    def _is_scanner_poll_required(self):
        """
        Check if Scanner Poll is to be performed

        :return: Boolean to indicate if scanner polling required
        :rtype: bool
        """
        log.logger.debug("Determining if polling of scanner states on ENM is to be performed")

        if (self.check_poll_scanners_profile_setting() or
                self.check_nodes_attached_to_subscription_object_exceeds_threshold() or
                self.check_number_of_nodes_attached_to_subscription_exceeds_threshold() or
                self.check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold()):
            return True

        log.logger.debug("Polling of scanner states on ENM will not take place")

    def check_poll_scanners_profile_setting(self):
        """
        Checks if POLL_SCANNERS attribute has been set on the profile

        :return: Boolean to indicate if scanner count polling can take place
        :rtype: bool
        """

        log.logger.debug("POLL_SCANNERS value setting on profile: {0}".format(self.poll_scanners))
        if self.poll_scanners:
            log.logger.debug("Polling will be performed as profile parameter POLL_SCANNERS is set for this profile")
            return True

    def check_nodes_attached_to_subscription_object_exceeds_threshold(self):
        """
        Checks if number of nodes attached to the subscription object within profile exceeds Scanner Polling threshold

        :return: Boolean to indicate if scanner count polling can take place
        :rtype: bool
        """

        self.number_of_nodes_attached_to_subscription = len(self.nodes) if hasattr(self, 'nodes') and self.nodes else 0
        log.logger.debug('Number of nodes attached to subscription object in profile: {0}'
                         .format(self.number_of_nodes_attached_to_subscription))
        if self.number_of_nodes_attached_to_subscription > self.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE:
            log.logger.debug("Polling will be performed as node count tied to profile ({0}) exceeds threshold of {1}"
                             .format(self.number_of_nodes_attached_to_subscription,
                                     self.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE))
            return True

    def check_number_of_nodes_attached_to_subscription_exceeds_threshold(self):
        """
        Checks if number of nodes attached to the ENM subscription exceeds the Scanner Polling threshold

        :return: Boolean to indicate if scanner count polling can take place
        :rtype: bool
        """

        number_of_nodes_attached_to_subscription_on_enm = self.get_number_of_nodes_attached_to_subscription_on_enm()
        if number_of_nodes_attached_to_subscription_on_enm > self.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE:
            log.logger.debug("Polling will be performed as node count exceeds threshold of {0}"
                             .format(self.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE))
            return True

    def get_number_of_nodes_attached_to_subscription_on_enm(self):
        """
        Get the number of nodes attached to the ENM subscription

        :return: Number of nodes attached to the ENM Subscription
        :rtype: int
        """
        log.logger.debug("Checking number of nodes attached to subscription on ENM")
        subscription_data_from_enm = self.get_subscription()
        if subscription_data_from_enm.get("nodes"):
            number_of_nodes_attached_to_subscription_on_enm = len(subscription_data_from_enm.get("nodes"))
            log.logger.debug("Number of nodes attached to subscription on ENM: {0}"
                             .format(number_of_nodes_attached_to_subscription_on_enm))
            return number_of_nodes_attached_to_subscription_on_enm
        return 0

    def check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold(self):
        """
        Checks if number of nodes scanner tied to the ENM subscription exceeds the Scanner Polling threshold

        :return: Boolean to indicate if scanner count polling can take place
        :rtype: bool
        """

        log.logger.debug("Checking number of scanners tied to subscription on ENM")
        number_of_active_scanners_for_subscription = self._get_number_of_active_scanners()
        log.logger.debug("Number of scanners active scanners on ENM: {0}"
                         .format(number_of_active_scanners_for_subscription))
        if number_of_active_scanners_for_subscription > self.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE:
            log.logger.debug("Polling will be performed as number of active scanner count exceeds threshold of {0}"
                             .format(self.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE))
            return True

    def _wait_for_scanners(self, action):
        """
        Wait for the number of active scanners to reach the acceptable level before completing the (de)activation task

        :param action: representing the action performed by subscription
        :type action: str
        """
        log.logger.debug("Waiting for number of active scanners tied to subscription to reach {0}% of total"
                         .format(self.SCANNER_COUNT_THRESHOLD_PERCENTAGES[action]))

        if not self.number_of_nodes_attached_to_subscription:
            self.number_of_nodes_attached_to_subscription = self.get_number_of_nodes_attached_to_subscription_on_enm()

        current_time = datetime.datetime.now()
        expiry_time = current_time + datetime.timedelta(minutes=self.MAX_MINUTES_TO_WAIT_FOR_SCANNERS)

        last_count_of_active_scanners = 0
        iteration_count_where_active_scanner_count_has_not_changed = 0

        log.logger.debug("Profile will attempt to check scanner states for subscription on ENM (until max time: {0})"
                         .format(expiry_time))
        while datetime.datetime.now() < expiry_time:
            number_of_active_scanners_for_subscription = self._get_number_of_active_scanners()

            if number_of_active_scanners_for_subscription == last_count_of_active_scanners:
                iteration_count_where_active_scanner_count_has_not_changed += 1

            last_count_of_active_scanners = number_of_active_scanners_for_subscription

            if self.check_if_scanner_polling_complete(
                    action, number_of_active_scanners_for_subscription,
                    iteration_count_where_active_scanner_count_has_not_changed):
                break

            log.logger.debug("Sleeping for {0}s before re-checking scanner states"
                             .format(self.SLEEP_SECONDS_BETWEEN_CHECKING_SCANNERS))
            time.sleep(self.SLEEP_SECONDS_BETWEEN_CHECKING_SCANNERS)

        log.logger.debug("Waiting for number of active scanners to reach expected levels is complete")

    def check_if_scanner_polling_complete(self, action, number_of_active_scanners_for_subscription,
                                          iteration_count_where_active_scanner_count_has_not_changed):
        """
        Check if scanner polling is complete, i.e. if number of active scanners on ENM has reached target level
        :param action: Action being performed (i.e. activation/deactivation)
        :type action: str
        :param number_of_active_scanners_for_subscription: Number of active scanners tied to subscription
        :type number_of_active_scanners_for_subscription: int
        :param iteration_count_where_active_scanner_count_has_not_changed: Number of iterations where scanner count has
                                                                                remained unchanged
        :type iteration_count_where_active_scanner_count_has_not_changed: int
        :return: Boolean to indicate if scanner polling is complete
        :rtype: bool
        """

        scanner_threshold = self.SCANNER_COUNT_THRESHOLD_PERCENTAGES[action]

        if not self.number_of_nodes_attached_to_subscription:
            log.logger.debug("No nodes tied to subscription")
            return True if action == "deactivation" else False
        percentage_of_scanners_currently_active = float(number_of_active_scanners_for_subscription * 100 /
                                                        self.number_of_nodes_attached_to_subscription)

        if (percentage_of_scanners_currently_active < scanner_threshold and action == "activation") or (
                percentage_of_scanners_currently_active > scanner_threshold and action == "deactivation"):
            log.logger.debug("Active Scanner Count ({0}) for this subscription has not yet reached {1}% of total "
                             "expected scanner count ({2})"
                             .format(number_of_active_scanners_for_subscription,
                                     scanner_threshold,
                                     self.number_of_nodes_attached_to_subscription))
            log.logger.debug("Scanner Polling incomplete")

            if (iteration_count_where_active_scanner_count_has_not_changed >=
                    self.WAIT_TIME_MINS_IF_NO_SCANNER_STATE_CHANGE * 60 /
                    self.SLEEP_SECONDS_BETWEEN_CHECKING_SCANNERS):
                log.logger.debug("Active Scanner Count for subscription ({0}) has not changed after {1}mins "
                                 "- Scanner states are unlikely to change further therefore no further checks "
                                 "on scanner states will be performed"
                                 .format(number_of_active_scanners_for_subscription,
                                         self.WAIT_TIME_MINS_IF_NO_SCANNER_STATE_CHANGE))
                return True

        else:
            exceeds_or_less_than = "exceeds" if action == "activation" else "is less than"
            log.logger.debug("Active Scanner Count for subscription ({0}) {1} {2} threshold of {3}% of total ({4})"
                             "- waiting time is complete"
                             .format(number_of_active_scanners_for_subscription, exceeds_or_less_than, action,
                                     scanner_threshold, self.number_of_nodes_attached_to_subscription))
            return True

    def _get_number_of_active_scanners(self):
        """
        Get number of Active Scanners in the Network associated with this subscription

        :return: Number of Active Scanners
        :rtype: int
        """
        scanner_count = 0
        for node_type in self.node_types:
            scanner_count += self.get_active_scanners_based_on_node_type(node_type)
            log.logger.debug("Scanners count for {0} nodes: {1}".format(node_type, scanner_count))
        return scanner_count

    def get_active_scanners_based_on_node_type(self, node_type):
        """
        Get number of Active Scanners in the specific node type associated with this subscription.

        :return: Number of Active Scanners for node type
        :rtype: int
        """
        log.logger.info("Performing cmedit command to count Active scanners for {0} nodes attached to "
                        "subscription {1} (id: {2})".format(node_type, self.name, self.id))
        cmedit_command_to_count_scanners = ("cmedit get * PMICScannerInfo.(subscriptionId=={subscription_id},"
                                            "status==ACTIVE) -cn -ne={node_type}".format(subscription_id=self.id,
                                                                                         node_type=node_type))
        log.logger.info("Command being executed: {0}".format(cmedit_command_to_count_scanners))

        try:
            response = self.user.enm_execute(cmedit_command_to_count_scanners)
        except Exception as e:
            log.logger.error("Problem encountered running cmedit command: {0}".format(str(e)))
            return 0

        cmedit_output = response.get_output()
        log.logger.info("Response received: {0}".format(cmedit_output))

        for line in cmedit_output:
            match = re.search(r'.*PMICScannerInfo (.*) instance.*', line)
            if match:
                scanner_count = match.group(1)
                try:
                    log.logger.debug("Number of {0} active scanners detected on ENM: {1}".format(node_type,
                                                                                                 int(scanner_count)))
                    return int(scanner_count)
                except ValueError:
                    log.logger.info("Number expected but received {0} instead".format(scanner_count))

        return 0

    def deactivate(self, validate=True):
        """
        Deactivates a subscription
        """
        log.logger.debug("Sending post request to deactivate the subscription")
        self._post(endpoint=self.SUPPORTED_POST_ENDPOINTS[1])  # deactivate

        if validate:
            self.wait_for_state(self.SUPPORTED_SUBSCRIPTION_STATES[0])  # INACTIVE
            log.logger.debug("Successfully deactivated subscription {0} ({1})".format(self.name, self.id))

    def wait_for_state(self, state):
        """
        Wrapper for _wait_for_state()

        :param state: The state used to control the flow. i.e, 'active' or 'inactive'
        :type state: string

        """
        log.logger.debug("Waiting for subscription to reach {0} state".format(state))
        self._wait_for_state(state)

    def _wait_for_state(self, state):
        """
        Waits and checks for the subscription to be either active or inactive

        :param state: The state used to control the flow. i.e, 'active' or 'inactive'
        :type state: string

        :raises TimeOutError: Cannot verify state
        """
        start_time = time.time()
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=self.timeout)
        while datetime.datetime.now() < expiry_time:
            try:
                subscriptions = self.user.get(self.POLLING_URL, headers=JSON_SECURITY_REQUEST)
            except Exception as e:
                log.logger.debug("Failed to fetch subscription {0}: {1}".format(self.name, str(e)))
                time.sleep(self.wait_for_state_sleep_seconds)
            else:
                if subscriptions.ok:
                    for sub in subscriptions.json():
                        if sub["name"] == self.name and sub["administrationState"] == state:
                            log.logger.debug('State of the subscription "{0}" is "{1}"'.format(self.name, state))
                            end_time = time.time()
                            log.logger.debug('PM TIMER: {0}  {1}  {2:.1} min'
                                             .format(self.name, "ACTIVATE" if state == "ACTIVE" else "DEACTIVATE",
                                                     (end_time - start_time) / 60))
                            return
                log.logger.debug("Sleeping for {0} seconds before re-trying..."
                                 .format(self.wait_for_state_sleep_seconds))
                time.sleep(self.wait_for_state_sleep_seconds)

        raise TimeOutError('The profile timed out after waiting ({0}s) for subscription "{1}" to reach {2} state'
                           .format(self.timeout, self.name, state))

    def delete(self):
        """
        Deletes a subscription

        :raises HTTPError: Cannot delete the subscription
        """
        response = self.user.delete_request(
            self.UPDATE_URL.format(subscription_id=self.id), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError('Cannot delete the subscription "{0}", rc is "{1}"'
                            .format(self.name, response.status_code), response=response)
        log.logger.debug('Successfully removed the subscription "{0}"'.format(self.name))

    def get_subscription(self):
        """
        :return: Json response
        :rtype: dict
        """
        if not self.id:
            log.logger.debug('Getting Subscription details using name of profile ({0}) via user {1}'
                             .format(self.name, self.user.username))
            return Subscription.get_by_name(self.name, self.user)
        log.logger.debug('Getting Subscription details by ID ({0}) with user {1}'.format(self.id, self.user.username))
        return Subscription.get_by_id(self.id, self.user)

    def _unique_entities(self, technology_domain=None):
        """
        Gets the Model Id information for the nodes attached to the subscription

        :param technology_domain: technology domain
        :type technology_domain: str
        :return: Model ID's String
        :rtype: str
        :raises EnvironError: if no nodes found having particular model version
        """
        if technology_domain:
            log.logger.debug("Profile has technology domain specified")
            model_ids_string = "".join(set("{ne_type}:{mim_info}:{technology_domain},"
                                           .format(ne_type=node["neType"],
                                                   mim_info=node["ossModelIdentity"],
                                                   technology_domain="%23"
                                                   .join(set(domain for domain in node.get("technologyDomain")
                                                             if node.get("technologyDomain", False))))
                                           for node in self.parsed_nodes
                                           if technology_domain in node.get("technologyDomain")))

        else:
            model_ids_string = "".join(set("{ne_type}:{mim_info},"
                                           .format(ne_type=node["neType"],
                                                   mim_info=node["ossModelIdentity"])
                                           for node in self.parsed_nodes))

        log.logger.debug("Model ID's to be used in query: '{0}'".format(model_ids_string))
        return model_ids_string

    @classmethod
    def get_all(cls, user):
        """
        Returns all subscriptions in ENM
        :param user: user to use for the REST request
        :type user: `enmutils.lib.enm_user.User` object
        :return: Json from response to Get request
        :rtype: dict
        :raises HTTPError: Cannot fetch subscriptions from ENM
        """
        response = user.get(cls.BASE_URL, headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError('Cannot fetch subscriptions from ENM', response=response)

        log.logger.debug("Successfully fetched all subscriptions")
        return response.json()

    @classmethod
    def get_system_subscription_name_by_pattern(cls, pattern, user):
        """
        Get full name of system defined subscription using the profile-specific pattern from the network configuration
        module (e.g. forty_network)

        :param pattern: the string pattern to be used to match the correct system defined subscription
        :type pattern: str
        :param user: User instance
        :type user: enm_user_2.User object
        :return: The name of the subscription
        :rtype: str

        :raises EnmApplicationError: If expected subscription is not found, then exception is raised
        """

        log.logger.debug("Fetching System Defined Subscription Name using pattern: {0}".format(pattern))

        match = 0
        system_subscription_name = None
        regex = r'\b{0}\b'.format(pattern)

        for subscription_data in cls.get_all(user):
            name = subscription_data["name"]
            description = subscription_data["description"]
            user_type = subscription_data["userType"]

            if user_type == "SYSTEM_DEF" and (re.search(regex, name) or re.search(regex, description)):
                match += 1
                system_subscription_name = name

        if system_subscription_name and match == 1:
            return system_subscription_name
        else:
            raise EnmApplicationError("Expected System Defined Subscription not found because of "
                                      "1) PM design change, or "
                                      "2) PMIC did not create the profile. "
                                      "Profile searches subscription details to find pattern: '{0}'".format(pattern))

    @classmethod
    def get_by_name(cls, name, user):
        """
        Returns all subscriptions in ENM

        :param user: user to use for the REST request
        :type user: enmutils.lib.enm_user_2.User
        :param name: Name of subscription
        :type name: str
        :return: Json from response to get request
        :rtype: dict

        :raises EnmApplicationError: Subscription doesnt exist
        """
        for sub in cls.get_all(user):
            if name.lower() == sub["name"].lower():
                return cls.get_by_id(sub["id"], user)

        raise EnmApplicationError("Subscription name {0} does not exist on ENM".format(name))

    @classmethod
    def get_by_id(cls, sub_id, user=None):
        """
        Returns the subscription information from ENM given the sub id

        :param sub_id: str representing the subscription id in ENM
        :type sub_id: str
        :param user: user to use for the REST request
        :type user: enmutils.lib.enm_user_2.User
        :return: Json from response
        :rtype: json
        :raises HTTPError: Could not get subscription
        """
        response = user.get(cls.UPDATE_URL.format(subscription_id=sub_id), headers=JSON_SECURITY_REQUEST)

        if not response.ok:
            raise HTTPError("Could not get subscription info for subscription '{0}', rc = '{1}', Output = '{2}'"
                            .format(sub_id, response.status_code, response.text), response=response)

        log.logger.debug("Successfully fetched subscription {0}".format(sub_id))
        return response.json()

    @classmethod
    def clean_subscriptions(cls, name=None, fast=False, user=None, delete_all=False):
        """
        Clears all the subscriptions from ENM

        :param name: name of the subscription
        :type name: str
        :param user: User to be used to query ENM via CM CLI
        :type user: enmutils.lib.enm_user_2.User
        :param fast: string indicating fast deletion
        :type fast: bool
        :param delete_all: boolean flag to delete all subscriptions
        :type delete_all: bool
        """
        user = user or get_workload_admin_user()
        enm_subscriptions = cls.get_all(user)  # fetch all subscriptions from ENM
        subscriptions = []

        if delete_all:
            subscriptions_to_delete = [subscription for subscription in enm_subscriptions if
                                       subscription["userType"] != "SYSTEM_DEF"]
        else:
            subscriptions_to_delete = [subscription for subscription in enm_subscriptions if
                                       subscription["userType"] != "SYSTEM_DEF" and
                                       (subscription["name"].startswith(name) or name in subscription["name"])]

        for sub_dict in subscriptions_to_delete:
            sub_type = sub_dict.get("type")
            log.logger.info("Subscription type detected: {0}".format(sub_type))
            if "STATISTICAL" in sub_type:
                sub = StatisticalSubscription(sub_dict["name"])
            elif "CELLTRACE" in sub_type:
                sub = CelltraceSubscription(sub_dict["name"])
            elif "UETRACE" in sub_type:
                ue_info = sub_dict.get("ueInfo", {u'type': u'IMSI', u'value': u'27202'})
                sub = UETraceSubscription(ue_info, name=sub_dict["name"])
            elif "EBM" in sub_type:
                sub = EBMSubscription(sub_dict["name"])
            elif "CELLTRAFFIC" in sub_dict.get("type"):
                sub = CelltrafficSubscription(sub_dict["name"])
            elif "UETR" in sub_type:
                sub = UETRSubscription(sub_dict["name"])
            elif "GPEH" in sub_type:
                sub = GpehSubscription(sub_dict["name"])
            else:
                sub = Subscription(sub_dict["name"])
            sub.id = sub_dict["id"]
            sub.user = user
            subscriptions.append(sub)

        if subscriptions:
            if fast:  # delete subscriptions from ENM without PM mediation
                Subscription.remove_subscriptions_from_enm_via_cmcli(user, subscriptions)

            else:  # delete subscriptions from ENM with PM mediation
                Subscription.remove_subscriptions_from_enm_via_pmserv(user, subscriptions)
        else:
            log.logger.info(log.red_text("No subscriptions found with name {0}").format(name))

    @classmethod
    def remove_subscriptions_from_enm_via_cmcli(cls, user, subscriptions):
        """
        Remove Subscriptions from ENM using cmedit commands

        :param user: User to be used to query ENM via CM CLI
        :type user: enmutils.lib.enm_user_2.User
        :param subscriptions: List of subscriptions to be removed
        :type subscriptions: list
        """
        delete = 'cmedit delete * {sub_type}.(name=="{sub_name}")'

        for subscription in subscriptions:
            try:
                time.sleep(1)
                user.enm_execute(delete.format(sub_type=subscription.__class__.__name__, sub_name=subscription.name))
                log.logger.info("Subscription {0} has been deleted".format(subscription.name))
            except Exception as e:
                log.logger.debug("Failed to delete {0} through cli_app - {1}".format(subscription.name, str(e)))

    @classmethod
    def remove_subscriptions_from_enm_via_pmserv(cls, user, subscriptions):
        """
        Remove Subscriptions from ENM using PM rest interface, but failing that, use CM CLI

        :param user: User to be used to query ENM via CM CLI
        :type user: enmutils.lib.enm_user_2.User
        :param subscriptions: List of subscriptions to be removed
        :type subscriptions: list
        """
        set_active = 'cmedit set * {sub_type}.(name=="{sub_name}") administrationState=ACTIVE'

        for subscription in subscriptions:
            sub_name = subscription.name
            sub_state = subscription.state
            try:
                if sub_state == 'ACTIVE':
                    log.logger.info("Deactivating {0}".format(subscription.name))
                    subscription.deactivate()
                elif sub_state == 'ACTIVATING' or sub_state == 'DEACTIVATING':
                    user.enm_execute(set_active.format(sub_type=subscription.__class__.__name__, sub_name=sub_name))
                    subscription.wait_for_state('ACTIVE')
                    log.logger.info("Deactivating {0}".format(subscription.name))
                    subscription.deactivate()
            except Exception as e:
                log.logger.info(
                    "Unable to deactivate subscription {0}, Will not delete it".format(subscription.name))
                log.logger.debug(str(e))
                continue

            try:
                log.logger.info("Subscription {0} being deleted".format(sub_name))
                subscription.delete()
                log.logger.info("Subscription {0} has been deleted".format(sub_name))
            except Exception as e:
                log.logger.debug("Subscription failed to delete through pmserv rest requests. Retrying through cliapp. "
                                 "Exception: {0}".format(str(e)))
                Subscription.remove_subscriptions_from_enm_via_cmcli(user, [subscription])

    def get_counters(self, definer='STATISTICAL_SubscriptionAttributes'):
        """
        Instantiates and returns a HTTP request object specific to fetching all services.
        i.e. stats counters, cell trace events
        :param definer: This attribute is used in the COUNTERS_URL. Counters returned can differ depending on definer
        :type definer: str
        :return: The HTTP request
        :rtype: object http.Request

        :raises HTTPError: Could not get counters
        """
        if self.technology_domain_counter_limits:
            return self.get_counters_based_on_profile(definer)

        else:
            response = self.user.get(
                self.COUNTERS_URL.format(
                    model_identities=self._unique_entities(technology_domain=self.technology_domain),
                    definer=definer), headers=JSON_SECURITY_REQUEST)
            if not response.ok:
                raise HTTPError('Cannot get counters for nodes "{0}. Response was: {1}"'
                                .format(str(self._unique_entities(technology_domain=self.technology_domain)),
                                        response.text), response=response)

            log.logger.debug("# Total number of counters returned from ENM: {0}".format(len(response.json())))

            if self.mo_class_counters_excluded:
                log.logger.debug('# Excluding the counters found under {0} MO Class(es): {1}'
                                 .format(len(self.mo_class_counters_excluded),
                                         ','.join(class_name for class_name in self.mo_class_counters_excluded)))
                return [{"moClassType": counter['sourceObject'], 'name': counter['counterName']}
                        for counter in response.json() if counter['sourceObject']
                        not in self.mo_class_counters_excluded]
            else:
                if self.mo_class_counters_included:
                    log.logger.debug("# Restricting profile to include "
                                     "specific counters only: {0}".format(self.mo_class_counters_included))
                    return [{"moClassType": counter['sourceObject'], 'name': counter['counterName']}
                            for counter in response.json() if counter['sourceObject']
                            in self.mo_class_counters_included]
                else:
                    log.logger.debug("# Including all counters returned")
                    return [{"moClassType": counter['sourceObject'], 'name': counter['counterName']}
                            for counter in response.json()]

    def filter_included_mo_class_sub_counters(self, counters):
        """
        Filter counters to include sub counters from certain MO classes only

        :param counters: List of counters
        :type counters: list

        :return: List of filtered mo class sub counters
        :rtype: list
        """
        log.logger.debug("# Restricting profile to include specific sub counters from certain "
                         "MO classes only: {0}".format(self.mo_class_sub_counters_included))
        mo_class_sub_counters = []
        for counter in counters:
            if (counter["moClassType"] in self.mo_class_sub_counters_included.keys() and counter["name"] in
                    self.mo_class_sub_counters_included[counter["moClassType"]]):
                mo_class_sub_counters.append(counter)

        return mo_class_sub_counters

    def get_counters_based_on_profile(self, definer):
        """
        Get counters based on profiles like PM_38 or PM_48
        :param definer: This attribute is used in the COUNTERS_URL.
                        Known values include OSS and NE, counters returned can differ depending on definer
        :type definer: str
        :return: list of technology domain counters
        :rtype: List
        :raises EnvironError: if no counters selected
        """
        counters = get_tech_domain_counters_based_on_profile(self)
        if not counters:
            raise EnvironError("No counters selected to add to subscription")

        return counters

    def parse_counters(self, definer='STATISTICAL_SubscriptionAttributes'):
        """
        Checks if the provided counter value is a fixed int or a float representing a percentage
        :param definer: This attribute is used in the COUNTERS_URL. Counters returned can differ depending on definer
        :type definer: str
        :return: counters
        :rtype: list
        """
        num_counters, counters = self.filter_counters_based_on_profile_name(definer)

        if len(counters) > num_counters and num_counters is not None:
            if self.name.startswith('PM_67'):
                counters = counters[0:num_counters]
                log.logger.debug("Selected first {0} counters for PM_67 ".format(num_counters))
            elif self.name.startswith('PM_76'):
                counters = counters[-num_counters:] if num_counters <= len(counters) else counters
                log.logger.debug("Selected last {0} counters for PM_76 ".format(num_counters))
            elif self.name.startswith('PM_98'):
                counters = counters[0:num_counters]
            else:
                counters = sample(counters, num_counters)
        log.logger.debug('Adding {0} counters (based on NUM_COUNTERS: {1}) to the subscription'
                         .format(num_counters or len(counters), self.num_counters))
        return counters

    def filter_counters_based_on_profile_name(self, definer):
        """
        Check, if profile name is PM_98 then returns the empty counters(0 counters), Otherwise returns the
        required counters.
        :param definer: This attribute is used in the COUNTERS_URL. Counters returned can differ depending on definer
        :type definer: str
        :return: tuple of num_counters, counters
        :rtype: tuple
        """
        counters = []
        num_counters = 0
        if not self.name.startswith('PM_98') or (self.name.startswith('PM_98') and
                                                 float(self.nodes[0].node_version.replace('-', '.')) >= 1.17):
            counters = self.get_counters(definer=definer)
            if self.mo_class_sub_counters_included:
                counters = self.filter_included_mo_class_sub_counters(counters)
            if isinstance(self.num_counters, float):
                num_counters = int(len(counters) * self.num_counters)
            else:
                num_counters = self.get_required_num_of_counters(counters)

        return num_counters, counters

    def create(self):
        raise NotImplementedError()

    def _teardown(self):
        if not self.id:
            log.logger.debug('No id set for pm subsription. Not tearing down')
            return

        subscription_state = None
        if not self.user:
            self.user = get_workload_admin_user()
        try:
            log.logger.debug("Checking Subscription state")
            subscription_state = self.state
            if subscription_state == 'ACTIVE':
                log.logger.debug("Subscription is Active - Deactivating")
                self.deactivate()
            elif subscription_state in ['ACTIVATING', 'UPDATING']:
                log.logger.debug("Subscription State is '{}' - waiting for Active state".format(subscription_state))
                self.wait_for_state('ACTIVE')
                log.logger.debug("Subscription is Active - Deactivating")
                self.deactivate()
            elif subscription_state == 'DEACTIVATING':
                log.logger.debug("Subscription State is Deactivating - waiting for Inactive state")
                self.wait_for_state('INACTIVE')
            time.sleep(2)
            log.logger.debug("Deleting subscription")
            self.delete()
            # Removing old subscriptions which exist in ENM that have the same name as this profile
            self.clean_subscriptions(name=self.name[:6], user=self.user)
        except Exception as e:
            log.logger.debug("Failed to teardown subscription {0} in state '{1}' via pmserv - "
                             "Exception encountered: {2}".format(self.name, subscription_state, str(e)))
            log.logger.debug("Profile will re-try to de-activate and delete this subscription via pmserv now")
            self.clean_subscriptions(name=self.name, user=self.user)

    @property
    def state(self):
        return self.get_subscription()['administrationState']

    def fetch_subscription_id(self, response):
        """
        Fetches the subscription id based on the returned json response

        :param response: response
        :type response: requests.Response
        :raises SubscriptionCreationError: Subscription could not be created
        :raises TimeOutError: Timeout waiting to fetch subscription
        """
        fail_after = datetime.datetime.now() + datetime.timedelta(minutes=10)
        while datetime.datetime.now() < fail_after:
            try:
                response2 = self.user.get(response.json()['url'])
                if not response2.ok:
                    if response2._content and ("could not be created" in response2._content or "System has no knowledge" in response2._content):
                        raise SubscriptionCreationError('Subscription could not be created: {0}'.format(response2._content), response=response2)
                    log.logger.debug('Failed to fetch subscription id of {0}, {1}. Retrying again..'.format(self.name, response2._content))
                    time.sleep(5)
                    continue
                self.id = response2.json()['id']
                break
            except KeyError:
                log.logger.debug('Sleeping for 15 seconds before retrying to get the ID of the subscription {0}'.format(self.name))
                time.sleep(15)
        else:
            raise TimeOutError('Timeout for 10 minutes retrying to fetch the id of {0} failed'.format(self.name))

    def sgsn_mme_exists_and_is_synchronized(self, user):
        """
        A UE Trace subscription cannot be saved unless there is at least one SGSN-MME node in the network with the
        mobileCountryCode and mobileNetworkCode attributes set in the PLMN under the node.
        Once the node is synchronised, ENM will be able to read those attributes.

        :param user: User to be used to query ENM via CM CLI
        :type user: enmutils.lib.enm_user_2.User
        :return: Boolean to indicate whether the above conditions are true or not
        :rtype: bool

        """
        get_count_of_synced_mme_nodes_cmd = "cmedit get * CmFunction.syncStatus==SYNCHRONIZED --neType=SGSN-MME -cn"
        log.logger.debug('Executing the following command to determine number of '
                         'synchronised SGSN-MME nodes exist on server: {0})'.format(get_count_of_synced_mme_nodes_cmd))

        problem_encountered = False
        try:
            response = user.enm_execute(get_count_of_synced_mme_nodes_cmd)
        except:
            problem_encountered = True

        if not problem_encountered:
            log.logger.debug("Response to CM CLI query: {0}".format(response.get_output()))

            response_string = "\n".join(response.get_output())
            match_pattern = re.compile(r'CmFunction .* instance')

            if match_pattern.search(response_string) is not None:
                number_of_nodes = int(re.split('.*?CmFunction (.*?) instance.*', response_string)[1])
                if number_of_nodes > 0:
                    return True
                else:
                    log.logger.debug("No synchronised SGSN-MME nodes have been detected on the server.")
            else:
                log.logger.debug("A problem has been detected with fetching the required info from ENM.")

        return False

    def create_subscription_on_enm(self, data):
        """
        Creates subscription on ENM

        :param data: Json data to be submitted to ENM
        :type data: dict
        :raises HTTPError: if Subscription could not be created
        """
        log.logger.debug("Sending request to ENM ({0}) to create subscription {1}".format(self.BASE_URL, self.name))
        response = self.user.post(self.BASE_URL, data=json.dumps(data), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError("Could not create subscription: '{0}', rc = '{1}'  Output = '{2}'"
                            .format(self.name, response.status_code, response.text), response=response)
        log.logger.debug("Checking ENM to ensure subscription {0} was created".format(self.name))
        self.fetch_subscription_id(response)
        log.logger.debug("Successfully created subscription {0}".format(self.name))

    def get_nodes_for_subscription(self):
        """
        :raises EnvironError: if nodes unavailable for use by subscription
        :return: List of nodes to be added to subscription
        :rtype: list
        """
        log.logger.debug("Determining nodes to be added to subscription")

        if not self.nodes:
            raise EnvironError('No nodes provided - Cannot create subscription')

        try:
            list_of_nodes_to_be_added_to_subscription = self.nodes_list

            if not list_of_nodes_to_be_added_to_subscription:
                raise ValueError("List of nodes to be added to subscription was determined to be empty")
        except (ValueError, Exception) as e:
            raise EnvironError('Problems were encountered while trying to add nodes to this subscription '
                               '- Cannot create subscription: {0}'.format(str(e)))

        return list_of_nodes_to_be_added_to_subscription

    def get_required_num_of_counters(self, counters):
        """
        Get required number of counters based on self.num_counters,
        Otherwise it returns total count of counters, when self.num_counters is None

        :param counters: List of counters
        :type counters: list

        :return: total count of counters
        :rtype: int
        """
        num_counters = self.num_counters if (self.num_counters and
                                             self.num_counters < len(counters)) else len(counters)
        return num_counters


class StatisticalSubscription(Subscription):

    def __init__(self, *args, **kwargs):
        """
        Statistical Subscription constructor
        :num_counters: int or float(percentage of counters) to indicate how many counters we need to create this sub
        """
        num_counters = kwargs.pop('num_counters', 3)
        self.cbs = kwargs.pop('cbs', False)
        self.criteria_specification = kwargs.pop('criteria_specification', [])
        poll_scanners = kwargs.pop('poll_scanners', False)
        super(StatisticalSubscription, self).__init__(*args, **kwargs)

        # Don't want constructor to overwrite self.num_counters
        self.num_counters = num_counters
        self.poll_scanners = poll_scanners

    def create(self):
        """
        Creates a statistical subscription
        """
        log.logger.debug("Creating Statistical subscription")
        data = {
            "id": None,
            "type": 'STATISTICAL',
            "administrationState": 'INACTIVE',
            "taskStatus": 'OK',
            "operationalState": "NA",
            "filterOnManagedElement": False,
            "pnpEnabled": False,
            "cbs": self.cbs,
            "filterOnManagedFunction": False,
            "userType": "USER_DEF",
            "rop": self.rop_enum,
            "@class": "statistical",
            "nodes": self.get_nodes_for_subscription(),
            "counters": self.parse_counters(definer=self.definer) if self.definer else self.parse_counters(),
            "nodesTypeVersion": [],
            "scheduleInfo": {},
            "name": self.name,
            "description": self.description,
            "userActivationDateTime": None,
            "userDeActivationDateTime": None,
            "criteriaSpecification": self.criteria_specification,
            "nodeFilter": "NODE_TYPE",
            "selectedNeTypes": self.ne_types,
            "owner": self.user.username
        }
        self.create_subscription_on_enm(data)

    def update(self, **kwargs):
        """
        Update statistical subscription
        :param kwargs: update values

        :raises HTTPError: Could not update subscription
        """
        sub = self.get_subscription()
        new_node_set = kwargs.pop('nodes', [])
        self.num_counters = kwargs.pop('counters', self.num_counters)

        if new_node_set:
            self.nodes = new_node_set
            sub["nodes"] = self.nodes_list

        sub["counters"] = self.parse_counters()

        response = self.user.put(self.UPDATE_URL.format(subscription_id=self.id), data=json.dumps(sub),
                                 headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError("Could not update statistical subscription: '{0}', rc = '{1}'  Output = '{2}'"
                            .format(self.name, response.status_code, response.text), response=response)
        self.fetch_subscription_id(response)
        log.logger.debug("Successfully updated statistical subscription {0}".format(self.name))


class CelltraceSubscription(Subscription):
    EVENTS_URL = "/pm-service/rest/pmsubscription/getEvent?eventFilter={event_filter}&mim={model_identities}"

    def __init__(self, *args, **kwargs):
        """
        Celltrace subscription constructor
        :param args: Different arguments
        :type args: *
        :param kwargs: Different arguments
        :type kwargs: *
        """
        # output_mode: str to indicate which output mode to use for this subscription
        self.output_mode = kwargs.pop('output_mode', "FILE")  # Valid options: "FILE", "STREAMING", "FILE_AND_STREAMING"
        # num_events: int or float(float between 0 and 1 represents percentage of events) to indicate how many random
        # events we need for this sub
        self.num_events = kwargs.pop("num_events", 3)
        self.ebs_output_strategy = kwargs.pop("ebs_output_strategy", "ENIQ_GZ")
        self.ebs_enabled = kwargs.pop("ebs_enabled", "false")
        self.ebs_counters = []
        self.cbs = kwargs.pop('cbs', False)
        self.criteria_specification = kwargs.pop('criteria_specification', [])
        num_counters = kwargs.pop("num_counters", None)
        poll_scanners = kwargs.pop('poll_scanners', False)
        super(CelltraceSubscription, self).__init__(*args, **kwargs)

        # Need to assign this here, otherwise the call to the super class would overwrite it
        self.num_counters = num_counters
        self.poll_scanners = poll_scanners

    def get_events(self):
        """
        Instantiates and returns a HTTP request object specific to fetching all events
        :return: List of counters
        :rtype: list

        :raises HTTPError: Cannot get events
        """
        response = self.user.get(
            self.EVENTS_URL.format(event_filter=self.event_filter,
                                   model_identities=self._unique_entities(technology_domain=self.technology_domain)),
            headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError('Cannot get events for nodes "{0}"'.format(
                str(self._unique_entities(technology_domain=self.technology_domain))), response=response)
        return [{"eventProducerId": counter["eventProducerId"], "groupName": counter['sourceObject'],
                 'name': counter['eventName']} for counter in response.json()]

    def parse_events(self):
        """
        Checks if the provided events value is a fixed int or a float representing a percentage

        :return: events
        :rtype: list
        """
        events = self.get_events()
        if isinstance(self.num_events, float):
            num_events = int(len(events) * self.num_events)
        else:
            num_events = self.num_events if self.num_events < len(events) else len(events)
        if len(events) > num_events and num_events is not None:
            events = sample(events, num_events)
        log.logger.debug('Adding {0} "{1}" events to the subscription'
                         .format(num_events or len(events), ','.join(event['name'] for event in events)))
        return events

    def create(self):
        """
        Creates a celltrace subscription
        """
        log.logger.debug("Creating CellTrace subscription")

        data = {
            "type": 'CELLTRACE',
            "id": None,
            "name": self.name,
            "description": self.description,
            "userType": "USER_DEF",
            "administrationState": 'INACTIVE',
            "operationalState": "NA",
            "taskStatus": "OK",
            "rop": self.rop_enum,
            "pnpEnabled": False,
            "filterOnManagedFunction": False,
            "filterOnManagedElement": False,
            "scheduleInfo": {},
            "nodes": self.get_nodes_for_subscription(),
            "events": self.parse_events(),
            "@class": "celltrace",
            "streamInfoList": [],
            "outputMode": self.output_mode,
            "ueFraction": 1000,
            "asnEnabled": False,
            "ebsEnabled": self.ebs_enabled,
            "ebsCounters": self.parse_ebs_counters(definer=self.definer) if self.definer else self.parse_ebs_counters(),
            "cbs": self.cbs,
            "nextVersionName": None,
            "prevVersionName": None,
            "owner": self.user.username,
            "criteriaSpecification": self.criteria_specification,
            "nodeFilter": "NODE_TYPE",
            "selectedNeTypes": self.ne_types
        }

        if self.ebs_events:
            data.update({"ebsEvents": self.parse_events()})

        if self.cell_trace_category:
            data.update({"cellTraceCategory": self.cell_trace_category})
            log.logger.debug("Adding cellTraceCategory:{}".format(self.cell_trace_category))

        self.create_subscription_on_enm(data)

    def parse_ebs_counters(self, definer="CELLTRACE_SubscriptionAttributes"):
        """
        Fetch the ebs counters from enm and parse the counters in to subscription required format.
        :param definer: This attribute is used in the COUNTERS_URL. Counters returned can differ depending on definer
        :type definer: str
        :return: returns list of ebs counters.
        :rtype: list
        """
        if self.name.startswith("EBSN_04") or self.name.startswith("EBSN_05"):
            ebs_counters = get_ebs_flex_counters(self.user)
        else:
            ebs_counters = (self.parse_counters(definer=definer)
                            if self.num_counters and self.ebs_enabled == "true" else [])
            if ebs_counters:
                log.logger.debug("Attempting to remove the flexible counters from {0} ebs counters"
                                 "".format(len(ebs_counters)))
                ebsn_flexible_counters = get_reserved_ebsn_flex_counters(self.name)
                updated_ebs_counters = [counter for counter in ebs_counters
                                        if counter["name"] not in ebsn_flexible_counters]
                log.logger.debug("Successfully removed {0} flexible counters from {1} ebs counters".format(
                    (len(ebs_counters) - len(updated_ebs_counters) if updated_ebs_counters else 0), len(ebs_counters)))
                ebs_counters = updated_ebs_counters

        log.logger.debug("Adding {0} counters to the subscription".format(len(ebs_counters)))

        return ebs_counters


class CelltrafficSubscription(Subscription):

    MO_INSTANCES_URL = "/pm-service/rest/pmsubscription/moinstances?mim={mims}&moClasses=UtranCell&subscriptionType=CELLTRAFFIC"
    CELL_TRAFFIC_EVENTS_URL = "/pm-service/rest/pmsubscription/getCellTrafficEvents?mim={mims}&moClasses=UtranCell&subscriptionType=CELLTRAFFIC"

    def __init__(self, *args, **kwargs):
        """
        Celltraffic subscription constructor
        :param args: Different arguments
        :type args: *
        :param kwargs: Different arguments
        :type kwargs: *

        """
        # output_mode: str to indicate which output mode to use for this subscription
        self.output_mode = kwargs.pop('output_mode', "FILE")  # Valid options: "FILE", "STREAMING", "FILE_AND_STREAMING"
        # num_events: int or float(float between 0 and 1 represents percentage of events) to indicate how many random
        # events we need for this sub
        self.num_events = kwargs.pop("num_events", 3)
        self.cbs = kwargs.pop('cbs', False)
        self.criteria_specification = kwargs.pop('criteria_specification', [])
        num_counters = kwargs.pop("num_counters", None)
        poll_scanners = kwargs.pop('poll_scanners', False)
        super(CelltrafficSubscription, self).__init__(*args, **kwargs)

        # Need to assign this here, otherwise the call to the super class would overwrite it
        self.num_counters = num_counters
        self.poll_scanners = poll_scanners

    def get_mo_instances(self):
        """
        Fetches the cell info
        :return: cell info list
        :rtype: list

        :raises HTTPError: Could not get cell info
        """
        response = self.user.get(
            self.MO_INSTANCES_URL.format(mims=self._parse_mim_info()), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError('Cannot get cell info for nodes "{0}"'
                            .format(str(self._parse_mim_info())), response=response)
        return [{"nodeName": node_mo_info['nodeName'], 'utranCellId': node_mo_info['moInstanceName'].split("=")[-1]} for node_mo_info in response.json()]

    def get_cell_traffic_events(self):
        """
        Fetches all cell traffic events
        :return: cell traffic events
        :rtype: list

        :raises HTTPError: Could not get cell traffic
        """
        unique_entities = self._unique_entities()
        response = self.user.get(
            self.CELL_TRAFFIC_EVENTS_URL.format(mims=unique_entities), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError("Cannot get cell traffic events for mim's {0}".format(unique_entities), response=response)
        trigger_events = [{"groupName": event["sourceObject"], "name": event["eventName"]} for event in response.json().get("triggerEvents", {})]
        non_trigger_events = [{"groupName": event["sourceObject"], "name": event["eventName"]} for event in response.json().get("nonTriggerEvents", {})]
        return trigger_events + non_trigger_events

    def parse_cell_traffic_events(self):
        """
        Checks if the provided events value is a fixed int or a float representing a percentage

        :return: events
        :rtype: list
        """
        events = self.get_cell_traffic_events()
        if isinstance(self.num_events, float):
            num_events = int(len(events) * self.num_events)
        else:
            num_events = self.num_events if self.num_events < len(events) else len(events)
        if len(events) > num_events and num_events is not None:
            events = sample(events, num_events)
        log.logger.debug('Adding {0} "{1}" events to the subscription'
                         .format(num_events or len(events), ','.join(event['name'] for event in events)))
        return events

    def _parse_mim_info(self):
        """
        Gets the unique mim info for the nodes attached to this subscription
        """
        mim = self._unique_entities()
        nodes = "&nodes={nodes_list}".format(nodes_list="%2C".join("{node_name}%3A{node_type}".format(node_name=node["fdn"].split("=")[-1], node_type=node["neType"]) for node in self.parsed_nodes))
        return mim + nodes

    def get_cell_info_list(self, nodes):
        """
        CellTrace subscription requires at least 1 cell per RNC node.
        This function will parse the complete list of cells for all nodes included in subscription and
         will return a list of cells containing one cell from each RNC node in the supplied list.
        :param nodes: list of dictionaries, with each dict containing attributes related to a particular node
        :type nodes: list
        :return: list of dictionaries, with each dict containing 1 node name and 1 cell that exists on that node
        :rtype: list
        """
        node_names = []
        cell_info_list = []
        complete_list_of_cells_on_all_selected_nodes = self.get_mo_instances()

        for node in nodes:
            node_name = node['fdn'].split('=')[-1]
            node_names.append(node_name)

            for cell_info in complete_list_of_cells_on_all_selected_nodes:
                if node_name == cell_info["nodeName"]:
                    cell_info_list.append(cell_info)
                    break

        log.logger.debug('Nodes being used: {0}'.format(node_names))
        log.logger.debug('Cells being added: {0}'.format(cell_info_list))

        return cell_info_list

    def create(self):
        """
        Creates a CellTraffic subscription
        """
        log.logger.debug("Creating CellTraffic subscription")

        nodes = self.get_nodes_for_subscription()
        events = self.parse_cell_traffic_events()
        cell_info_list = self.get_cell_info_list(nodes)

        data = {
            "type": 'CELLTRAFFIC',
            "id": None,
            "name": self.name,
            "description": self.description,
            "userType": "USER_DEF",
            "administrationState": 'INACTIVE',
            "operationalState": "NA",
            "taskStatus": "OK",
            "rop": self.rop_enum,
            "pnpEnabled": False,
            "filterOnManagedFunction": False,
            "filterOnManagedElement": False,
            "scheduleInfo": {},
            "streamInfoList": [],
            "nodes": nodes,
            "events": events,
            "triggerEventInfo": sample(events, 1)[0] if events else {},
            "@class": "celltraffic",
            "cellInfoList": cell_info_list,
            "outputMode": "FILE",
            "cbs": self.cbs,
            "nextVersionName": None,
            "prevVersionName": None,
            "owner": self.user.username,
            "criteriaSpecification": self.criteria_specification,
            "nodeFilter": "NODE_TYPE",
            "selectedNeTypes": self.ne_types
        }

        self.create_subscription_on_enm(data)


class GpehSubscription(Subscription):
    MO_INSTANCES_URL = "/pm-service/rest/pmsubscription/cells?mim={mims}&moClasses=UtranCell&subscriptionType=GPEH"
    WCDMA_EVENTS_URL = "/pm-service/rest/pmsubscription/getWcdmaEvents?mim={mims}&subscriptionType=GPEH"

    def __init__(self, *args, **kwargs):
        """
        GPEH subscription constructor
        :param args: Different arguments
        :type args: *
        :param kwargs: Different arguments
        :type kwargs: *

        """
        # output_mode: str to indicate which output mode to use for this subscription
        self.output_mode = kwargs.pop('output_mode', "FILE")  # Valid options: "FILE", "STREAMING", "FILE_AND_STREAMING"
        # num_events: int or float(float between 0 and 1 represents percentage of events) to indicate how many random
        # events we need for this sub
        self.num_events = kwargs.pop("num_events", 3)
        self.cbs = kwargs.pop('cbs', False)
        self.criteria_specification = kwargs.pop('criteria_specification', [])
        num_counters = kwargs.pop("num_counters", None)
        poll_scanners = kwargs.pop('poll_scanners', False)
        super(GpehSubscription, self).__init__(*args, **kwargs)

        # Need to assign this here, otherwise the call to the super class would overwrite it
        self.num_counters = num_counters
        self.poll_scanners = poll_scanners

    def get_wcdma_events(self):
        """
        Fetches all cell traffic events
        :return: cell traffic events
        :rtype: list

        :raises HTTPError: Could not get WCDMA events
        """
        unique_entities = self._unique_entities()
        response = self.user.get(
            self.WCDMA_EVENTS_URL.format(mims=unique_entities), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError("Cannot get wcdma events for mim's {0}".format(unique_entities), response=response)
        wcdma_events = [{"groupName": event["sourceObject"], "name": event["eventName"]} for event in response.json()]
        return wcdma_events

    def parse_wcdma_events(self):
        """
        Checks if the provided events value is a fixed int or a float representing a percentage

        :return: events
        :rtype: list
        """
        events = self.get_wcdma_events()
        if isinstance(self.num_events, float):
            num_events = int(len(events) * self.num_events)
        else:
            num_events = self.num_events if self.num_events < len(events) else len(events)
        if len(events) > num_events and num_events is not None:
            events = sample(events, num_events)
        log.logger.debug('Adding {0} "{1}" events to the subscription'
                         .format(num_events or len(events), ','.join(event['name'] for event in events)))
        return events

    def _parse_mim_info(self):
        """
        Gets the unique mim info for the nodes attached to this subscription
        :return: mim info
        :rtype: str
        """
        mim = self._unique_entities()
        nodes = "&nodes={nodes_list}".format(nodes_list="%2C".join("{node_name}%3A{node_type}".format(node_name=node["fdn"].split("=")[-1], node_type=node["neType"]) for node in self.parsed_nodes))
        return mim + nodes

    def get_mo_instances(self):
        """
        Fetches the cell info
        :return: cell info list
        :rtype: list

        :raises HTTPError: Coul dnot get cell info
        """
        response = self.user.get(
            self.MO_INSTANCES_URL.format(mims=self._parse_mim_info()), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError('Cannot get cell info for nodes "{0}"'
                            .format(str(self._parse_mim_info())), response=response)
        return [{"nodeName": node_mo_info['nodeName'], 'utranCellId': node_mo_info['moInstanceName'].split("=")[-1]} for node_mo_info in response.json()]

    def create(self):
        """
        Creates a GPEH subscription
        """

        log.logger.debug("Creating GPEH subscription")

        nodes = self.get_nodes_for_subscription()
        events = self.parse_wcdma_events()
        cell_supported = False if 'RBS' in self.ne_types else True
        cell_info_list = self.get_mo_instances() if cell_supported else []

        data = {
            "type": "GPEH",
            "id": None,
            "name": self.name,
            "description": self.description,
            "userType": "USER_DEF",
            "administrationState": "INACTIVE",
            "operationalState": "NA",
            "userActivationDateTime": None,
            "userDeActivationDateTime": None,
            "scheduleInfo": {},
            "nodeFilter": "NODE_TYPE",
            "selectedNeTypes": self.ne_types,
            "nodes": nodes,
            "@class": "gpeh",
            "outputMode": "FILE",
            "ueFraction": 1000,
            "cellsSupported": cell_supported,
            "applyOnAllCells": False,
            "cellInfoList": cell_info_list,
            "owner": self.user.username,
            "nextVersionName": None,
            "prevVersionName": None,
            "activationTime": None,
            "deactivationTime": None,
            "persistenceTime": 1489489206984,
            "criteriaSpecification": self.criteria_specification,
            "nodeListIdentity": 0,
            "taskStatus": "OK",
            "rop": self.rop_enum,
            "pnpEnabled": False,
            "filterOnManagedFunction": False,
            "filterOnManagedElement": False,
            "cbs": self.cbs,
            "streamInfoList": [],
            "events": events,
        }

        self.create_subscription_on_enm(data)


class EBMSubscription(CelltraceSubscription):

    def create(self):
        """
        Creates a EBM subscription
        """

        log.logger.debug("Creating EBM subscription")

        data = {
            "type": "EBM",
            "id": None,
            "name": self.name,
            "description": self.description,
            "userType": "USER_DEF",
            "administrationState": "INACTIVE",
            "operationalState": "NA",
            "userActivationDateTime": None,
            "userDeActivationDateTime": None,
            "scheduleInfo": {},
            "nodes": self.get_nodes_for_subscription(),
            "@class": "ebm",
            "outputMode": self.output_mode,
            "compressionEnabled": False,
            "ebsOutputStrategy": self.ebs_output_strategy,
            "ebsOutputInterval": "FIFTEEN_MIN",
            "ebsEnabled": self.ebs_enabled,
            "owner": self.user.username,
            "taskStatus": "OK",
            "rop": self.rop_enum,
            "pnpEnabled": False,
            "filterOnManagedFunction": False,
            "filterOnManagedElement": False,
            "cbs": self.cbs,
            "streamInfoList": [],
            "events": self.parse_events(),
            "ebsCounters": self.parse_ebs_counters(definer=self.definer) if self.definer else self.parse_ebs_counters(),
            "nodeFilter": "NODE_TYPE",
            "criteriaSpecification": self.criteria_specification,
            "selectedNeTypes": self.ne_types
        }

        self.create_subscription_on_enm(data)

    def parse_ebs_counters(self, definer="OSS"):
        """
        Parse EBS Counters
        :param definer: This attribute is used in the COUNTERS_URL. Counters returned can differ depending on definer
        :type definer: str
        :return: List of counters
        :rtype: list
        """
        return self.parse_counters(definer=definer) if self.num_counters and self.ebs_enabled == "true" else []


class UETraceSubscription(Subscription):
    def __init__(self, ue_info, *args, **kwargs):
        """
        :param ue_info: dict of ue info type
            and value for ex: {'type': 'IMSI', 'value': '27201'}, valid types are IMSI, IMEI, IMEI (Software)
        :type ue_info: dict
        :param args: Different arguments
        :type args: *
        :param kwargs: Different arguments
        :type kwargs: *

        """
        # interface_types: list of types of interfaces to be used in the payload
        self.interface_types = kwargs.pop(
            'interface_types', {'SGSN': ["s1_mme", "s3_s16", "s6a", "s11", "sv"],
                                'ENODEB': []})
        self.trace_depth = kwargs.pop(
            'trace_depth', 'MINIMUM'
        )
        self.stream_info = kwargs.pop(
            'stream_info', None
        )
        self.ue_info = ue_info
        self.output_mode = kwargs.pop('output_mode', "FILE")  # Valid options: "FILE", "STREAMING", "FILE_AND_STREAMING"
        poll_scanners = kwargs.pop('poll_scanners', False)
        super(UETraceSubscription, self).__init__(*args, **kwargs)

        self.poll_scanners = poll_scanners

    def create(self):
        """
        Creates UETrace subscription.
        """

        log.logger.debug("Creating UETrace subscription")

        data = {
            "type": "UETRACE",
            "id": None,
            "name": self.name,
            "description": self.description,
            "userType": "USER_DEF",
            "administrationState": "INACTIVE",
            "operationalState": "NA",
            "userActivationDateTime": None,
            "userDeActivationDateTime": None,
            "scheduleInfo": {},
            "@class": "uetrace",
            "ueInfo": self.ue_info,
            "outputMode": self.output_mode,
            "nodeInfoList": [
                {
                    "nodeGrouping": "ENODEB",
                    "traceDepth": self.trace_depth,
                    "interfaceTypes": self.interface_types['ENODEB']
                },
                {
                    "nodeGrouping": "MME",
                    "interfaceTypes": self.interface_types['SGSN']
                }
            ],
            "streamInfo": self.stream_info,
            "owner": self.user.username,
            "taskStatus": "OK",
            "rop": self.rop_enum
        }

        self.create_subscription_on_enm(data)

    def update(self, **kwargs):
        """
        Update subscription
        :param kwargs: update values

        :raises HTTPError: Could not update subscription

        """
        sub = self.get_subscription()

        sub["streamInfo"] = kwargs.pop('stream_info', sub.get("streamInfo"))
        sub["outputMode"] = kwargs.pop('output_mode', sub.get("outputMode"))

        response = self.user.put(self.UPDATE_URL.format(subscription_id=self.id), data=json.dumps(sub), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError("Could not update subscription: '{0}', rc = '{1}'  Output = '{2}'"
                            .format(self.name, response.status_code, response.text), response=response)
        self.fetch_subscription_id(response)
        log.logger.debug("Successfully updated subscription {0}".format(self.name))


class UETRSubscription(Subscription):

    WCDMA_EVENTS = "/pm-service/rest/pmsubscription/getWcdmaEvents?mim={mims}&moClasses=UtranCell&subscriptionType=UETR"

    def __init__(self, *args, **kwargs):
        """
        UETR Subscription constructor

        :param args: Different arguments
        :type args: *
        :param kwargs: Different arguments
        :type kwargs: *

        """

        # output_mode: str to indicate which output mode to use for this subscription
        self.output_mode = kwargs.pop('output_mode', "FILE")  # Valid options: "FILE", "STREAMING", "FILE_AND_STREAMING"
        # num_events: int or float(float between 0 and 1 represents percentage of events) to indicate how many random
        # events we need for this sub
        self.num_events = kwargs.pop("num_events", 3)
        self.cbs = kwargs.pop('cbs', False)
        self.imsi = kwargs.pop("imsi", [{"type": "IMSI", "value": "123546"}])
        self.stream_info = kwargs.pop('stream_info', None)
        poll_scanners = kwargs.pop('poll_scanners', False)
        super(UETRSubscription, self).__init__(*args, **kwargs)

        self.poll_scanners = poll_scanners

    def create(self):
        """
        Creates UETR Subscription
        """

        log.logger.debug("Creating UETR subscription")

        data = {
            "type": 'UETR',
            "id": None,
            "name": self.name,
            "description": self.description,
            "userType": "USER_DEF",
            "administrationState": 'INACTIVE',
            "operationalState": "NA",
            "taskStatus": "OK",
            "rop": self.rop_enum,
            "pnpEnabled": False,
            "filterOnManagedFunction": False,
            "filterOnManagedElement": False,
            "scheduleInfo": {},
            "streamInfoList": [],
            "nodes": self.get_nodes_for_subscription(),
            "events": self.parse_wcdma_events(),
            "@class": "uetr",
            "outputMode": self.output_mode,
            "ueInfoList": self.imsi,
            "nextVersionName": None,
            "prevVersionName": None,
            "cbs": self.cbs,
            "owner": self.user.username,
            "nodeFilter": "NODE_TYPE",
            "selectedNeTypes": self.ne_types
        }

        self.create_subscription_on_enm(data)

    def get_wcdma_events(self):
        """
        Instantiates and returns a HTTP request object specific to fetching all wcdma events
        :return: List of Counters
        :rtype: list
        :raises HTTPError: Cannot get WCDMA events
        """
        unique_mims = self._unique_entities()
        response = self.user.get(
            self.WCDMA_EVENTS.format(mims=unique_mims), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            raise HTTPError('Cannot get WCDMA events for nodes "{0}"'.format(str(unique_mims)), response=response)
        return [{"groupName": counter['sourceObject'], 'name': counter['eventName']} for counter in response.json()]

    def parse_wcdma_events(self):
        """
        Checks if the provided events value is a fixed int or a float representing a percentage

        :return: events
        :rtype: list
        """
        events = self.get_wcdma_events()
        if isinstance(self.num_events, float):
            num_events = int(len(events) * self.num_events)
        else:
            num_events = self.num_events if self.num_events < len(events) else len(events)
        if len(events) > num_events and num_events is not None:
            events = sample(events, num_events)
        log.logger.debug('Adding {0} "{1}" events to the subscription'
                         .format(num_events or len(events), ','.join(event['name'] for event in events)))
        return events


class BscRecordingsSubscription(Subscription):

    def __init__(self, *args, **kwargs):
        """
        BSC Recordings Subscription constructor

        :param args: Different arguments
        :type args: list
        :param kwargs: Different arguments
        :type kwargs: dict
        """

        super(BscRecordingsSubscription, self).__init__(*args, **kwargs)

    def create(self):
        """
        Creates BSC Recordings Subscription
        """

        log.logger.debug("Creating BSC Recordings subscription")

        data = {
            "@class": "bscrecordings",
            "administrationState": 'INACTIVE',
            "cbs": False,
            "description": self.description,
            "filterOnManagedFunction": False,
            "filterOnManagedElement": False,
            "id": None,
            "name": self.name,
            "nodeFilter": "NODE_TYPE",
            "nodes": self.get_nodes_for_subscription(),
            "operationalState": "NA",
            "owner": self.user.username,
            "pnpEnabled": False,
            "rop": 'FIFTEEN_MIN',
            "scheduleInfo": {},
            "selectedNeTypes": self.ne_types,
            "taskStatus": "OK",
            "type": 'BSCRECORDINGS',
            "userType": "USER_DEF"
        }

        self.create_subscription_on_enm(data)


class MtrSubscription(Subscription):

    def __init__(self, *args, **kwargs):
        """
        MTR Subscription constructor

        :param args: Different arguments
        :type args: list
        :param kwargs: Different arguments
        :type kwargs: dict
        """
        self.recording_reference = None
        self.imsi_value = kwargs.pop('imsi_value', None)
        super(MtrSubscription, self).__init__(*args, **kwargs)

    def create(self):
        """
        Creates MTR Subscription
        """

        log.logger.debug("Creating MTR subscription")

        data = {
            "@class": "mtr",
            "administrationState": 'INACTIVE',
            "cbs": False,
            "description": self.description,
            "filterOnManagedFunction": False,
            "filterOnManagedElement": False,
            "id": None,
            "name": self.name,
            "nodeFilter": "NODE_TYPE",
            "nodes": self.get_nodes_for_subscription(),
            "operationalState": "NA",
            "owner": self.user.username,
            "pnpEnabled": False,
            "rop": 'FIFTEEN_MIN',
            "scheduleInfo": {},
            "selectedNeTypes": self.ne_types,
            "taskStatus": "OK",
            "userActivationDateTime": None,
            "userDeActivationDateTime": None,
            "type": 'MTR',
            "mtrAccessTypes": ["TCN", "OCN", "OCE", "LUN", "LUP", "MSA", "MSD", "SSP", "TSM", "OSM", "LCS"],
            "criteriaSpecification": [],
            "recordingReference": self.recording_reference,
            "ueInfo": {"type": "IMSI", "value": self.imsi_value},
            "userType": "USER_DEF"
        }

        self.create_subscription_on_enm(data)


class RPMOSubscription(Subscription):

    RPMO_MO_INSTANCES_URL = "/pm-service/rest/pmsubscription/cells?mim={mims}&moClasses=GeranCell&subscriptionType=RPMO"

    def __init__(self, *args, **kwargs):
        """
        RPMO Subscription constructor

        :param args: Different arguments
        :type args: list
        :param kwargs: Different arguments
        :type kwargs: dict
        """
        super(RPMOSubscription, self).__init__(*args, **kwargs)

    def get_mo_instances(self):
        """
        Fetches the cell info
        :return: cell info list
        :rtype: list

        :raises HTTPError: Could not get cell info
        """
        mim_info = self._parse_mim_info()
        response = self.user.get(
            self.RPMO_MO_INSTANCES_URL.format(mims=mim_info), headers=JSON_SECURITY_REQUEST)
        if not response.ok:
            log.logger.debug('Cannot get cell information fro nodes')
            raise HTTPError('Cannot get cell info for nodes "{0}"'
                            .format(str(mim_info)), response=response)
        return [{"nodeName": node_mo_info['nodeName'],
                 'utranCellId': node_mo_info['moInstanceName'].split("=")[-1]} for node_mo_info in response.json()]

    def _parse_mim_info(self):
        """
        Gets the unique mim info for the nodes attached to this subscription
        """
        mim = self._unique_entities()
        nodes = "&nodes={nodes_list}".format(nodes_list="%2C".
                                             join("{node_name}%3A{node_type}".
                                                  format(node_name=node["fdn"].split("=")[-1],
                                                         node_type=node["neType"]) for node in self.parsed_nodes))
        log.logger.debug('list of unique mim info for the nodes attached to this subscription: {0}'.format(mim + nodes))
        return mim + nodes

    def get_cell_info_list(self, nodes):
        """
        RPMO subscription requires at least 1 cell per BSC node.
        This function will parse the complete list of cells for all nodes included in subscription and
         will return a list of cells containing one cell from each BSC node in the supplied list.
        :param nodes: list of dictionaries, with each dict containing attributes related to a particular node
        :type nodes: list
        :return: list of dictionaries, with each dict containing 1 node name and 1 cell that exists on that node
        :rtype: list
        """
        node_names = []
        cell_info_list = []
        complete_list_of_cells_on_all_selected_nodes = self.get_mo_instances()
        for node in nodes:
            node_name = node['fdn'].split('=')[-1]
            node_names.append(node_name)

            for cell_info in complete_list_of_cells_on_all_selected_nodes:
                if node_name == cell_info["nodeName"]:
                    cell_info_list.append(cell_info)
                    break

        log.logger.debug('Nodes being used: {0}'.format(node_names))
        log.logger.debug('Cells being added: {0}'.format(cell_info_list))

        return cell_info_list

    def create(self):
        """
        Creates RPMO Subscription
        """

        log.logger.debug("Creating RPMO subscription")
        nodes = self.get_nodes_for_subscription()
        cell_info_list = self.get_cell_info_list(nodes)
        data = {
            "@class": "rpmo",
            "administrationState": 'INACTIVE',
            "cbs": False,
            "description": self.description,
            "filterOnManagedFunction": False,
            "filterOnManagedElement": False,
            "id": None,
            "cellInfoList": cell_info_list,
            "name": self.name,
            "nodeFilter": "NODE_TYPE",
            "nodes": nodes,
            "operationalState": "NA",
            "owner": self.user.username,
            "pnpEnabled": False,
            "rop": "NOT_APPLICABLE",
            "outputMode": "STREAMING",
            "events": [{"name": "ALL", "groupName": "ALL"}],
            "scheduleInfo": {},
            "selectedNeTypes": self.ne_types,
            "taskStatus": "OK",
            "type": 'RPMO',
            "userType": "USER_DEF"
        }

        self.create_subscription_on_enm(data)


class RTTSubscription(Subscription):

    def __init__(self, *args, **kwargs):
        """
        RTT Subscription constructor

        :param args: Different arguments
        :type args: list
        :param kwargs: Different arguments
        :type kwargs: dict
        """

        super(RTTSubscription, self).__init__(*args, **kwargs)

    def generate_imei_and_imsi(self):
        """
        Generating IMEI and IMSI

        :return : dict of IMEI and IMSI
        :type : dict
        """
        log.logger.debug('Generating IMEI and IMSI info')
        ue_info_list = []
        initial_value = 123455789
        ue_types = ['IMEI', 'IMSI']
        for count, value in enumerate(xrange(initial_value, initial_value + 1000)):
            ue_type = ue_types[1] if count >= 500 else ue_types[0]
            ue_info = {'type': ue_type, 'value': '00000{0}'.format(value)}
            ue_info_list.append(ue_info)
        log.logger.debug('ueInfoList : {}'.format(ue_info_list))
        return ue_info_list

    def create(self):
        """
        Creates RTT Subscription
        """

        log.logger.debug("Creating RTT subscription")
        nodes = self.get_nodes_for_subscription()
        data = {
            "type": "RTT",
            "id": None,
            "name": self.name,
            "description": self.description,
            "userType": "USER_DEF",
            "administrationState": "INACTIVE",
            "operationalState": "NA",
            "userActivationDateTime": None,
            "userDeActivationDateTime": None,
            "owner": self.user.username,
            "scheduleInfo": {
            },
            "nodeFilter": "NODE_TYPE",
            "selectedNeTypes": [
                "BSC"
            ],
            "nodes": nodes,
            "numberOfNodes": len(nodes),
            "@class": "rtt",
            "taskStatus": "OK",
            "rop": "NOT_APPLICABLE",
            "pnpEnabled": False,
            "filterOnManagedFunction": False,
            "filterOnManagedElement": False,
            "cbs": False,
            "outputMode": "STREAMING",
            "events": [
                {
                    "name": "ALL",
                    "groupName": "ALL"
                }
            ],
            "ueInfoList": self.generate_imei_and_imsi()
        }

        self.create_subscription_on_enm(data)
