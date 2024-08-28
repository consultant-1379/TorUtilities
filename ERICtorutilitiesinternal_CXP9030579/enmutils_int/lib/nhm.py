# ********************************************************************
# Name    : NHM (Network Health Monitor)
# Summary : Primary module used by the NHM (KPI Management application)
#           profiles. Contains functionality to perform extensive
#           operations, relating to NHM KPI jobs, creating, deleting,
#           updating KPIs, querying existing KPIs, activating and
#           deactivating KPI, selecting counters, selecting reporting
#           objects, along with some helper functions for the profiles,
#           selecting nodes used, waiting for setup profile to complete.
# ********************************************************************

import json
import time
from random import (randint, randrange, sample, choice)

from enmscripting.exceptions import TimeoutException
from requests.exceptions import HTTPError, ConnectionError
from retrying import retry

from enmutils.lib import log, persistence
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib.load_node import annotate_fdn_poid_return_node_objects

# KPI NHM endpoints
NHM_KPI_ENDPOINT_NEW = "kpi-specification-rest-api-war/kpi/get?kpiNames={name}"
NHM_KPI_ENDPOINT_EDIT = "kpi-specification-rest-api-war/kpi/edit/"
NHM_KPI_ENDPOINT_SAVE = "kpi-specification-rest-api-war/kpi/save/async/"
NHM_KPI_ENDPOINT_DELETE = "kpi-specification-rest-api-war/kpi/delete/{name}"
NHM_RTKPI_ENDPOINT_ACTIVATE = "kpi-specification-rest-api-war/rtkpi/activate"
NHM_KPI_ENDPOINT_ACTIVATE = "kpi-specification-rest-api-war/kpi/active/{status}"
NHM_KPI_ENDPOINT_ATTRIBUTE = "kpi-specification-rest-api-war/kpi/attributes"
NHM_COUNTERS = "kpi-specification-rest-api-war/pmCounters/{0}/{1}"
CREATED_BY_DEFAULT = "Ericsson"

# KPI information position
KPI_NAME = 0
KPI_CREATED_BY = 7

KPI_BODY = {
    "kpiModel": {
        "unit": "NUMBER_OF_COUNTS",
        "kpiFormulaList": [{
            "formulaTypeInfoList": [],
            "computation": {
                "preComputation": {},
                "abstractFormulaOperand": {
                    "varName": "theRO",
                    "iterationSet": {
                        "var": {
                            "name": "INPUT"
                        }
                    },
                    "setVariables": [],
                    "operands": [{
                        "reportingInstructions": {
                            "reportingObjectIdSource": "theRO"
                        },
                        "operands": [{
                            "value": 1
                        }]
                    }]
                }
            }
        }]
    },
    "kpiActivation": {
        "active": False,
        "threshold": {
            'thresholdDomain': None,
            'thresholdValue': None},
        "nodeCount": 0,
        "poidList": [],
        "queries": [""],
        "autoUpdateKpiScope": False
    },
    "name": "",
    "allNeTypes": []
}

ROUTER_COUNTERS = {'port-history': ['queue3_drop_red_bytes', 'queue4_tx_yellow_bytes', 'queue6_drop_total_packets',
                                    'queue0_drop_green_bytes', 'policing_class6_violate_drop_octets', 'ipv6_inpackets',
                                    'policing_class1_conform_octets', 'policing_class1_exceed_octets',
                                    'policing_class4_conform_octets', 'policing_class3_exceed_packets'],
                   'link-group-history': ['queue3_drop_red_bytes', 'queue4_tx_yellow_bytes',
                                          'queue6_drop_total_packets', 'queue0_drop_green_bytes',
                                          'policing_class6_violate_drop_octets', 'ipv6_inpackets',
                                          'policing_class1_conform_octets', 'policing_class1_exceed_octets',
                                          'policing_class4_conform_octets', 'policing_class3_exceed_packets'],
                   'dot1q-history': ['queue3_drop_red_bytes', 'queue4_tx_yellow_bytes', 'queue6_drop_total_packets',
                                     'queue0_drop_green_bytes', 'policing_class6_violate_drop_octets', 'ipv6_inpackets',
                                     'policing_class1_conform_octets', 'policing_class1_exceed_octets',
                                     'policing_class4_conform_octets', 'policing_class3_exceed_packets'],
                   'global': ['free_user_mem', 'average_user_mem', 'load5min', 'peak_user_mem', 'load15min', 'cpu5sec',
                              'cpu1min', 'load1min', 'total_user_mem', 'peakcpu5min', 'cpu5min'],
                   'tdm1001-pdh-history': ['epochtime', 'severelyErroredSecondsHC', 'backgroundBlockErrorsHC',
                                           'erroredBlocksHC', 'erroredSecondsHC', 'unavailableTimeHC'],
                   'ces-pw-history': ['outpackets', 'inpackets', 'epochtime', 'inoctets', 'outoctets',
                                      'missingPackets']}

RECOMMENDED_KPIS_FOR_NHM_13 = ['Downlink_Latency', 'Average_DL_Packet_Error_Loss', 'Average_DL_UE_Latency',
                               'Average_MAC_Cell_DL_Throughput', 'Average_PDCP_Cell_DL_Throughput',
                               'Average_UE_PDCP_DL_Throughput', 'Average_UE_UL_PDCP_Throughput',
                               'Initial_E-RAB_Establishment_Success_Rate']
SETUP_PROFILE = "NHM_SETUP"


def wait_for_nhm_setup_profile(profile_name=SETUP_PROFILE, wait_time=60, initial_wait_time=600, flag="COMPLETED"):
    """
    Function to wait util a flag is set up on the profile object
    Profile will wait for 15 given time intervals but after this period of time each iteration time will be doubled
    until it reaches 6 hours. It should reduce excessive logging in case of profile being left unattended for
    number of days
    :param profile_name: Key to wait for
    :type profile_name: str
    :param wait_time: Ininitial wait time given to profile to perform it's actions
    :type wait_time: int
    :param initial_wait_time: Time interval
    :type initial_wait_time: int
    :param flag: Flag to wait for
    :type flag: str
    """
    profile = persistence.get(profile_name)
    if profile.FLAG != flag:
        log.logger.info("{0} has started. Waiting for {1} seconds to check for completion".format(profile_name,
                                                                                                  initial_wait_time))
        time.sleep(initial_wait_time)
    else:
        log.logger.info("{} is started and complete. Starting the profile".format(profile_name))
    if not persistence.has_key(profile_name):
        sleep_until_profile_persisted(profile_name)
    i = 0
    profile = persistence.get(profile_name)
    while not profile.FLAG == flag:
        if i < 15:
            log.logger.info("{0} has not successfully completed waiting for {1} seconds.".format(profile_name,
                                                                                                 wait_time))
            time.sleep(wait_time)
            i = i + 1
            profile = persistence.get(profile_name)
        else:
            wait_time = wait_time * 2 if wait_time <= 21600 else wait_time
            log.logger.info("{0} has not successfully completed waiting for {1} seconds.".format(profile_name,
                                                                                                 wait_time))
            time.sleep(wait_time)
            profile = persistence.get(profile_name)
        if not profile:
            sleep_until_profile_persisted(profile_name)
            profile = persistence.get(profile_name)

    log.logger.info("{0} Complete.".format(profile_name))


def sleep_until_profile_persisted(profile_name, sleep_time=60):
    """
    Function to wait for given profile name being added to persistence.
    Profile will wait for 15 given time intervals but after this period of time each iteration time will be doubled
    until it reaches 6 hours. It should reduce excessive logging in case of profile being left unattended for
    number of days
    :param profile_name: Key to wait for
    :type profile_name: str
    :param sleep_time: Time interval
    :type sleep_time: int
    """
    i = 0
    while not persistence.has_key(profile_name):
        if i < 15:
            log.logger.info("{} is not running on the system. Profile can't proceed !!!".format(profile_name))
            log.logger.info("Sleeping for {} seconds.".format(sleep_time))
            time.sleep(sleep_time)
            i = i + 1
        else:
            sleep_time = sleep_time * 2 if sleep_time <= 21600 else sleep_time
            log.logger.info("{} is not running on the system. Profile can't proceed !!!".format(profile_name))
            log.logger.info("Sleeping for {} seconds.".format(sleep_time))
            time.sleep(sleep_time)


def get_nhm_nodes(nhm_profile, user, nodes):
    """
    Gets the nodes with correct POIDs to use for NHM

    :param nhm_profile: NHM profile to get nodes for
    :type nhm_profile: enmutils_int.lib.profile.Profile
    :param user: User object to be used to create the widgets
    :type user: enmutils.lib.enm_user_2.User
    :param nodes: nodes to verify
    :type nodes: list
    :return: verified nodes for the NHM profile
    :rtype: list
    """
    nodes_verified_on_enm = []

    while not nodes_verified_on_enm:
        try:
            nodes_verified_on_enm = annotate_fdn_poid_return_node_objects(nodes)
        except (HTTPError, TimeoutException) as e:
            nhm_profile.add_error_as_exception(
                EnmApplicationError('Profile could not get nodes with poids. Error message: {0}'.format(e)))
        if not nodes_verified_on_enm:
            log.logger.debug("Profile could not get nodes with poids. Retrying in 5 minutes")
            time.sleep(60 * 5)

    return nodes_verified_on_enm


@retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=30000, stop_max_attempt_number=3)
def get_kpi(user, name=None):
    """
    Get kpi attributes

    :param user: user to make requests
    :type user: enmutils.lib.enm_user_2.User
    :param name: name of the KPI to return
    :type name: str

    :return: All KPIs info or the info of the KPI matching the name parameter
    :rtype: json dict
    """

    body = {"kpiNames": "NAME",
            "attributes": ["NAME", "ACTIVE", "UNIT", "THRESHOLD", "NE_TYPES", "REPORTING_OBJECT_TYPES",
                           "NODE_COUNT", "CREATED_BY", "LAST_MODIFIED_BY", "LAST_MODIFIED_TIME"]}

    if name:
        body["kpiNames"] = name

    response = user.post(url=NHM_KPI_ENDPOINT_ATTRIBUTE, data=json.dumps(body), headers=JSON_SECURITY_REQUEST)
    if response.status_code != 200:
        response.raise_for_status()
    return response.json()


def check_is_kpi_usable_and_assign_to_node_type(user, kpi_name, node_kpi_dict, supported_node_types, supported_mos,
                                                unsupported_kpis=None):
    """
    Check is predefined KPI usable and assign it to the Node Type
    :param user: user to carry out requests
    :type user: enm_user_2.User
    :param kpi_name: Name of the KPI to check
    :type kpi_name: str
    :param node_kpi_dict: Dictionary with predefined KPIs that can be created for a node type
    :type node_kpi_dict: dict
    :param supported_node_types: node types supported by the profile
    :type supported_node_types: list
    :param supported_mos: Managed Objects supported by the profile
    :type supported_mos: dict
    :param unsupported_kpis: List of predefined KPIs to exclude
    :type unsupported_kpis: list
    :return: Dictionary of node types that can be used with the KPI
    :rtype: dict
    """

    # Get attributes of given KPI
    kpi = get_kpi(user, kpi_name)
    kpi_name = kpi[0][0]
    kpi_reporting_objects = kpi[0][5]
    kpi_node_types = kpi[0][4]

    # Return dict with no values if KPI name is on the unsupported list.
    if [kpi_name] in unsupported_kpis:
        return node_kpi_dict

    # If some kpi can be set on one or may supported node types and reporting objects match. Add to the dictionary.
    for node_type in kpi_node_types:
        if node_type in supported_node_types:
            comprehension = [node_kpi_dict[node_type].append(kpi_name) for reporting_object in kpi_reporting_objects if
                             node_type in supported_node_types and reporting_object in supported_mos[node_type] and
                             kpi_name not in node_kpi_dict[node_type]]
            del comprehension

    return node_kpi_dict


def get_counters_if_enodeb(ne_type):
    """
    Returns the counters for a KPI if reporting object is ENODEBFUNCTION.
    :param ne_type: Node type
    :type ne_type: str
    :return: List of counters specified by NHM design
    :rtype: list
    """
    counters = []
    if ne_type in ['ERBS', 'RadioNode']:
        counters = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr', 'pmLicConnectedUsersLicense',
                    'pmRrcConnBrEnbMax', 'pmMoFootprintMax', 'pmLicConnectedUsersMax', 'pmPagS1EdrxReceived']
    elif ne_type == 'MSRBS_V1':
        counters = ['pmPagS1Received', 'pmPagS1Discarded']
    else:
        log.logger.debug("Node type not supported by NHM")
    return counters


def transport_counters(reporting_object):
    """
    Returns the counters for a KPI if reporting object are global,tdm1001-pdh-history and ces-pw-history.
    :param reporting_object: Reporting object of the KPI
    :type reporting_object: object
    :return: List of counters specified by NHM design
    :rtype: list
    """
    counters = []
    if 'global' in reporting_object:
        counters = ROUTER_COUNTERS['global']
    elif 'tdm1001-pdh-history' in reporting_object:
        counters = ROUTER_COUNTERS['tdm1001-pdh-history']
    elif 'ces-pw-history' in reporting_object:
        counters = ROUTER_COUNTERS['ces-pw-history']
    return counters


class NhmKpi(object):

    def __init__(self, user=None, name=None, nodes=None, **kwargs):
        """
        NHM KPI Constructor

        :param user: user to make requests
        :type user: enmutils.lib.enm_user_2.User
        :param name: str representing the name of the KPI
        :type name: str
        :param nodes: list of nodes to be used with the KPI
        :type nodes: list
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary
        """

        self.name = name
        self.counters = kwargs.get('counters')
        self.reporting_objects = kwargs.get('reporting_objects')
        self.operators = kwargs.get('operators') if kwargs.get('operators') else ['ADDITION', 'SUBTRACTION', 'MULTIPLICATION']
        self.active = kwargs.get('active')
        self.node_types = list(set(kwargs.get('node_types'))) if kwargs.get('node_types') else ["ERBS"]
        self.kpi_unit = kwargs.get('kpi_unit') if kwargs.get('kpi_unit') else 'NO_OF_COUNTS'
        self.threshold_value = kwargs.get('threshold_value') if kwargs.get('threshold_value') else randint(1, 250)
        self.threshold_domain = kwargs.get('threshold_domain') if kwargs.get('threshold_domain') else 'GREATER_THAN'
        self.user = user
        self.po_ids = kwargs.get('po_ids')
        self.created_by = kwargs.get('created_by')
        if not self.created_by:
            self.created_by = self.user.username
        self.headers_dict = JSON_SECURITY_REQUEST
        if nodes:
            self.node_poids = [node.poid for node in nodes if node.poid]

    def _teardown(self):
        log.logger.debug("Tearing down KPI {0}, created_by: {1}".format(self.name, self.created_by))
        try:
            self.deactivate()
        except Exception as e:
            log.logger.debug(str(e))
        finally:
            if self.created_by == CREATED_BY_DEFAULT:
                self.update(remove_all_nodes=True)
            else:
                self.delete()

    @classmethod
    def get_kpi_info(cls, user, name=None):
        """
        Gets the kpi information (the kpi body)

        :param user: user to make requests
        :type user: enmutils.lib.enm_user.User
        :param name: name of the KPI
        :type name: str

        :return: Dictionary with the KPI body
        :rtype: json dict
        """
        response = user.get(url=NHM_KPI_ENDPOINT_NEW.format(name=name), headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    @classmethod
    def get_all_kpi_names(cls, user, exclude=None):
        """
        Get all KPI names created in NHM

        :param user: user to make requests
        :type user: enmutils.lib.enm_user_2.User
        :param exclude: value to exclude KPI profiles with the particular pattern
        :type exclude: str

        :return: names of all the KPIs
        :rtype: json dict
        """

        body = {"attributes": ["NAME"]}
        response = user.post(url=NHM_KPI_ENDPOINT_ATTRIBUTE, data=json.dumps(body), headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            response.raise_for_status()
        if exclude:
            for kpi in response.json():
                if exclude in kpi[0]:
                    response.json().remove(kpi)
        return response.json()

    @classmethod
    def get_all_kpi_names_active(cls, user, exclude=None):
        """
        Get all KPI names created in NHM

        :param user: user to make requests
        :type user: enmutils.lib.enm_user_2.User
        :param exclude: String value to exclude KPI profiles with the particular pattern (NHM_03)
        :type exclude: str

        :return: All the active KPI names
        :rtype: list
        :raises EnvironError: if no active KPIs are found on the system
        """
        body = {"attributes": ["NAME", "ACTIVE"]}

        response = user.post(url=NHM_KPI_ENDPOINT_ATTRIBUTE, data=json.dumps(body), headers=JSON_SECURITY_REQUEST)
        raise_for_status(response, message_prefix='No active KPIs found: ')

        if not response.json():
            raise EnvironError('No active KPIs found on the system. Please ensure {0} profile has run '
                               'successfully, or manually activate KPIs'.format(SETUP_PROFILE))

        kpi_response = []
        if exclude:
            for kpi in response.json():
                if exclude not in kpi[0] and kpi[1]:
                    kpi_response.append([kpi[0]])
        else:
            for kpi in response.json():
                if kpi[1]:
                    kpi_response.append([kpi[0]])

        return kpi_response

    @classmethod
    def get_kpis_created_by(cls, user, kpi_name=None):
        """
        Get the 'created_by' attribute of the KPI specified, to find the creator of the KPI.
        If no KPI name is specified, all KPIs created by the user will be returned.

        :param user: user to make requests
        :type user: enmutils.lib.enm_user.User
        :param kpi_name: KPI names
        :type kpi_name: list

        :return: all KPIs created by a user
        :rtype: json dict
        """
        body = {"kpiNames": kpi_name, "attributes": ["CREATED_BY"]}
        response = user.post(url=NHM_KPI_ENDPOINT_ATTRIBUTE, data=json.dumps(body), headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            response.raise_for_status()
        else:
            if not response.json() or not response.json()[0]:
                log.logger.debug("Failed to get the created by attribute for the kpi {0},proceeding to the "
                                 "next KPI".format(kpi_name))
            else:
                return response.json()[0][0]

    @classmethod
    def get_kpi_by_name(cls, user, name):
        """
        Get specific KPI created in NHM

        :param user: user to make requests
        :type user: enmutils.lib.enm_user.User
        :param name: Name of the KPI to return
        :type name: str

        :return: Information of a specific KPI
        :rtype: json dict
        """

        kpi_dict = cls._get_kpi(user, name)
        log.logger.debug("Successfully fetched kpi {0}".format(name))
        return kpi_dict

    @classmethod
    def get_kpi(cls, user, name=None):
        """
        Calls _get_kpi to get kpi attributes

        :param user: user to make requests
        :type user: enmutils.lib.enm_user_2.User
        :param name: name of the KPI to return
        :type name: str

        :return: All KPIs info or the info of the KPI matching the name parameter
        :rtype: json.response
        """

        return cls._get_kpi(user, name=name)

    @classmethod
    def _get_kpi(cls, user, name=None):
        """
        Get kpi attributes

        :param user: user to make requests
        :type user: enmutils.lib.enm_user_2.User
        :param name: name of the KPI to return
        :type name: str

        :return: All KPIs info or the info of the KPI matching the name parameter
        :rtype: json dict
        """

        if name:
            body = {"kpiNames": name,
                    "attributes": ["NAME", "ACTIVE", "UNIT", "THRESHOLD", "NE_TYPES", "REPORTING_OBJECT_TYPES",
                                   "NODE_COUNT", "CREATED_BY", "LAST_MODIFIED_BY", "LAST_MODIFIED_TIME"]}
        else:
            body = {"attributes": ["NAME", "ACTIVE", "UNIT", "THRESHOLD", "NE_TYPES", "REPORTING_OBJECT_TYPES",
                                   "NODE_COUNT", "CREATED_BY", "LAST_MODIFIED_BY", "LAST_MODIFIED_TIME"]}
        response = user.post(url=NHM_KPI_ENDPOINT_ATTRIBUTE, data=json.dumps(body), headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    @classmethod
    def get_counters_specified_by_nhm(cls, reporting_object=None, ne_type="ERBS"):
        """
        Returns the counters for a KPI based on the KPI reporting object and node type to be used in the KPI formula.
        As petition of NHM design there are a reduced number of counters based on the reporting_object and ne_type.

        :param reporting_object: Reporting object of the KPI, cell or node based KPI
        :type reporting_object: object
        :param ne_type: Node type
        :type ne_type: str

        :return: List of counters specified by NHM design
        :rtype: list
        """
        counters = []
        if reporting_object == 'ENodeBFunction':
            counters = get_counters_if_enodeb(ne_type)
        elif 'UtranCell' in reporting_object and ne_type == 'RNC':
            counters = ['pmNoFailedRrcConnectReqCsHw', 'pmTotNoRrcConnectReqCs', 'pmTotNoRrcConnectReqPs',
                        'pmNoFailedRrcConnectReqPsHw', 'pmTotNoRrcConnReqHsFach', 'pmTotNoRrcConnectSetup',
                        'pmTotNoRrcConnectReqSuccess', 'pmTotNoRrcConnectReqSms',
                        'pmNoRabEstablishAttemptPacketStream', 'pmNoRabEstAttPsHoCsfb']
        elif ('EUtranCellFDD' in reporting_object or 'EUtranCellTDD' in reporting_object) and (ne_type == 'RadioNode' or
                                                                                               ne_type == 'ERBS'):
            counters = ['pmRrcConnEstabAtt', 'pmRrcConnEstabAttMod', 'pmRrcConnReestAtt', 'pmRrcConnEstabSuccMod',
                        'pmRrcConnEstabSuccMos', 'pmRrcConnEstabSucc', 'pmRrcConnReestSucc', 'pmRrcConnReestAttHo',
                        'pmErabEstabAttInit', 'pmRrcConnReestSuccHo']
        elif any([_ in reporting_object for _ in ['dot1q-history', 'port-history', 'link-group-history']]) and \
                (ne_type in ['Router6672', 'Router6675']):
            counters = ROUTER_COUNTERS['port-history']
        elif any([_ in reporting_object for _ in ['global', 'tdm1001-pdh-history', 'ces-pw-history']]) and \
                (ne_type in ['Router6672', 'Router6675']):
            counters = transport_counters(reporting_object)
        else:
            log.logger.debug("Reporting object not supported by NHM")
        return counters

    @classmethod
    def clean_down_system_kpis(cls, user):
        """
        Deactivate the KPIs CREATED_BY_DEFAULT (i.e. by Ericsson), and remove all nodes from the KPI.
        These KPIs cannot be deleted.

        :param user: user to make requests
        :type user: enmutils.lib.enm_user_2.User

        """

        body = {"attributes": ["NAME"]}
        response = user.post(url=NHM_KPI_ENDPOINT_ATTRIBUTE, data=json.dumps(body), headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            response.raise_for_status()
        all_kpi_names_list = response.json()
        for kpi_name in all_kpi_names_list:
            kpi_created_by = NhmKpi.get_kpis_created_by(user, kpi_name=kpi_name)
            if CREATED_BY_DEFAULT == kpi_created_by:
                kpi_object = cls(name=kpi_name[0], user=user)
                try:
                    kpi_object.deactivate()
                except Exception as e:
                    log.logger.debug(
                        "Exception raised while trying to deactivate KPI with name {0}: {1}".format(kpi_name, str(e)))
                log.logger.debug("KPI name: {0} created by {1} deactivated".format(kpi_name, kpi_created_by))
                time.sleep(1)
                try:
                    kpi_object.update(remove_all_nodes=True)
                except Exception as e:
                    log.logger.debug("Exception raised while trying to remove nodes from system kpi: {0}".format(str(e)))
                log.logger.debug("KPI name: {0} created by {1} removed all nodes".format(kpi_name, kpi_created_by))
            else:
                log.logger.debug("KPI name: {0} created by {1} not deactivated".format(kpi_name, kpi_created_by))

    @classmethod
    def remove_kpis_by_pattern_new(cls, user, pattern):
        """
        Deactivates and deletes KPIs from the system which contain any of the patterns passed in

        :param pattern: Patterns to match on to remove KPIs from enm (e.g. NHM_SETUP)
        :type pattern: str
        :param user: user to make requests
        :type user: enmutils.lib.enm_user.User

        """

        body = {"attributes": ["NAME"]}
        response = user.post(url=NHM_KPI_ENDPOINT_ATTRIBUTE, data=json.dumps(body), headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            response.raise_for_status()
        all_kpi_names_list = response.json()
        for kpi in all_kpi_names_list:
            if pattern in kpi[KPI_NAME]:
                kpi_object = cls(name=kpi[0], user=user)
                try:
                    kpi_object.deactivate()
                except Exception as e:
                    log.logger.debug(
                        "Exception raised while trying to deactivate KPI with name {0}: {1}".format(kpi[KPI_NAME], str(e)))
                try:
                    kpi_object.delete()
                except Exception as e:
                    log.logger.debug(
                        "Exception raised while trying to delete KPI with name {0}: {1}".format(kpi[KPI_NAME], str(e)))
                log.logger.debug("KPI name: {0} deactivated and deleted".format(kpi[KPI_NAME]))

    @classmethod
    def check_reporting_object(cls, user, name, profile_reporting_objects):
        """
        Get the KPI info and check the reporting objects. Return True if the reporting objects include the profile
        reporting objects, else False

        :param profile_reporting_objects: reporting objects supported by the profile
        :type profile_reporting_objects: list
        :param user: user to make requests
        :type user: enmutils.lib.enm_user.User
        :param name: name of the KPI
        :type name: str
        :return: True if the profile reporting objects are in the KPI reporting objects, else False
        :rtype: boolean
        """

        kpi_info_response = cls.get_kpi(user, name)
        kpi_reporting_objects = kpi_info_response[0][5]
        if any(reporting_object in kpi_reporting_objects for reporting_object in profile_reporting_objects):
            return True

        return False

    @classmethod
    def check_supported_node_types(cls, user, name, supported_node_types):
        """
        Get the KPI info and check the NE types. Return True if the ne types include the profile supported node types,
        else False

        :param supported_node_types: node types supported by the profile
        :type supported_node_types: list
        :param user: user to make requests
        :type user: enmutils.lib.enm_user.User
        :param name: name of the KPI
        :type name: str
        :return: True if the profile supported node types are in the KPI NE types, else False
        :rtype: boolean
        """

        kpi_info_response = cls.get_kpi(user, name)
        kpi_ne_types = kpi_info_response[0][4]

        if all(ne_type in kpi_ne_types for ne_type in supported_node_types):
            return True

        return False

    def _create_node_level_body(self):
        """
        Returns the body used to create a node level KPI for all node types in KPI

        :return: KPI node level body values
        :rtype: json dictionary
        """
        log.logger.debug('Creating Node Level KPI body')

        kpi_body = KPI_BODY
        kpi_body["name"] = self.name
        kpi_body["kpiActivation"]["active"] = False
        kpi_body["kpiModel"]["kpiFormulaList"][0]["computation"][
            "abstractFormulaOperand"] = self._create_kpi_equation()
        kpi_body["kpiModel"]["kpiFormulaList"][0]["neTypes"] = self.node_types
        kpi_body["kpiModel"]["kpiFormulaList"][0]["formulaTypeInfoList"] = []

        kpi_body["allNeTypes"] = self.node_types
        for node_type in self.node_types:
            kpi_body["kpiModel"]["kpiFormulaList"][0]["formulaTypeInfoList"].append({
                "neType": node_type,
                "reportingObjectType": "ENodeBFunction",
                "inputData": {
                    "inputScope": "OBJECTS_FOR_TARGET",
                    "inputResourceMap": {
                        "INPUT": [{"ns": "UNKNOWN", "name": "ENodeBFunction"}]}}})
        return kpi_body

    def _create_cell_level_body(self):
        """
        Returns the body used to create a cell level KPI for all node type in KPI

        :return: KPI cell level body values
        :rtype: json dictionary
        """
        log.logger.debug('Creating Cell Level KPI body')
        kpi_body = KPI_BODY
        kpi_body["name"] = self.name
        kpi_body["kpiActivation"]["active"] = False
        kpi_body["kpiActivation"]["threshold"] = {}
        kpi_body["kpiModel"]["kpiFormulaList"][0]["computation"][
            "abstractFormulaOperand"] = self._create_kpi_equation()
        kpi_body["kpiModel"]["kpiFormulaList"][0]["neTypes"] = self.node_types
        kpi_body["kpiModel"]["kpiFormulaList"][0]["formulaTypeInfoList"] = []
        kpi_body["allNeTypes"] = self.node_types
        for node_type in self.node_types:
            ns_value = ''
            if node_type == 'ERBS':
                ns_value = 'ERBS_NODE_MODEL'
            elif node_type == 'RadioNode':
                ns_value = 'Lrat'
            elif node_type == 'MSRBS_V1':
                ns_value = 'MSRBS_V1_eNodeBFunction'
            elif node_type == 'RNC':
                ns_value = 'RNC_NODE_MODEL'
            else:
                log.logger.debug("No name space value for {} - Node not supported !".format(node_type))
            for reporting_object in self.reporting_objects:
                if ns_value:
                    kpi_body["kpiModel"]["kpiFormulaList"][0]["formulaTypeInfoList"].append({
                        "neType": node_type,
                        "reportingObjectType": reporting_object,
                        "inputData": {
                            "inputScope": "SINGLE_OBJECT",
                            "inputResourceMap": {
                                "INPUT": [{"ns": ns_value, "name": reporting_object}]}}
                    })

        return kpi_body

    def _create_nhm_12_kpi_payload(self):
        """
        Returns the body used to create a Node level KPI with formula and threshold values required for nhm_12
        :return: nhm_12 kpi payload
        :rtype: json dictionary
        """

        formula_list = [{"formulaTypeInfoList":
                         [{"neType": "ERBS",
                           "reportingObjectType": "ENodeBFunction",
                           "inputData": {"inputScope": "OBJECTS_FOR_TARGET",
                                         "computationInput": [{"ns": "UNKNOWN", "name": "ENodeBFunction"}],
                                         "inputResourceMap": {"INPUT": [{"ns": "UNKNOWN", "name": "ENodeBFunction"}],
                                                              'EUtranCellFDD':
                                                                  [{"ns": "UNKNOWN", "name": "EUtranCellFDD"}]}}}],
                         "computation": {"preComputation": {},
                                         "abstractFormulaOperand":
                                             {"varName": "theRO",
                                              "iterationSet": {"var": {"name": "INPUT"}},
                                              "setVariables": [],
                                              "operands": [{"reportingInstructions":
                                                            {"reportingObjectIdSource": "theRO"},
                                                            "operands": [{"operands": [{"value": 2},
                                                                                       {"value": 2}],
                                                                          "operator": "ADDITION"}]}]}}}]

        kpi_payload = KPI_BODY
        kpi_payload["name"] = self.name
        kpi_payload["kpiActivation"]["active"] = False
        kpi_payload["kpiActivation"]["threshold"] = {"thresholdDomain": self.threshold_domain,
                                                     "fmAlarmStatus": True,
                                                     "thresholdValue": self.threshold_value}
        kpi_payload["kpiModel"]["kpiFormulaList"] = formula_list

        kpi_payload["allNeTypes"] = self.node_types
        return kpi_payload

    def _create_router_node_kpi_body(self):
        """
        Returns the body used to create a router 6672 and 6675 KPI

        :return: Payload to create a router node KPI
        :rtype: dict
        """
        node_types = self.node_types
        kpi_body = KPI_BODY
        kpi_body["kpiModel"]['unit'] = 'NUMBER_OF_COUNTS'
        kpi_body["name"] = self.name
        kpi_body["kpiActivation"]["active"] = False
        kpi_body["allNeTypes"] = node_types
        kpi_formula_list = []
        for reporting_object in set(ROUTER_COUNTERS.keys()).intersection(self.reporting_objects):
            info = {"formulaTypeInfoList": [{"neType": self.node_types[0],
                                             "reportingObjectType": reporting_object,
                                             "inputData": {"inputScope": "OBJECTS_FOR_TARGET",
                                                           "inputResourceMap": {"INPUT": [{"ns": "UNKNOWN",
                                                                                           "name": reporting_object}]},
                                                           'computationInput': [{'ns': 'UNKNOWN',
                                                                                 'name': reporting_object}]}}],
                    "computation": {"preComputation": {},
                                    "abstractFormulaOperand":
                                        self._create_router_equation(ROUTER_COUNTERS[reporting_object])}}
            kpi_formula_list.append(info)
        kpi_body["kpiModel"]['kpiFormulaList'] = kpi_formula_list
        return kpi_body

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=30000, stop_max_attempt_number=3)
    def create(self):
        """
        Creates a NHM KPI

        """
        if self.name[:5] == "NHM12":
            kpi_body_create = self._create_nhm_12_kpi_payload()
        elif any(set(["Router6672", "Router_6672", "Router6675", "Router_6675"]) & set(self.node_types)):
            kpi_body_create = self._create_router_node_kpi_body()
        elif self.reporting_objects[0] == 'ENodeBFunction':
            kpi_body_create = self._create_node_level_body()
        else:
            if self.created_by == CREATED_BY_DEFAULT:
                kpi_body_create = self._get_kpi_body()
                kpi_body_create["kpiActivation"]["active"] = self.active
            else:
                kpi_body_create = self._create_cell_level_body()
        if self.node_poids:
            kpi_body_create["kpiActivation"]["poidList"] = self.node_poids
            kpi_body_create["kpiActivation"]["nodeCount"] = len(self.node_poids)
            if self.name[:6] == "NHM_14":
                kpi_body_create["kpiActivation"]["queries"] = ["all nodes"]
                kpi_body_create["kpiActivation"]["autoUpdateKpiScope"] = True
            response = self.user.post(url=NHM_KPI_ENDPOINT_SAVE, data=json.dumps(kpi_body_create),
                                      headers=self.headers_dict)
            if response.status_code != 200:
                response.raise_for_status()
            log.logger.debug("KPI '{0}' was successfully created with {1} poids".format(
                self.name, len(self.node_poids)))
            return response
        else:
            log.logger.info("No nodes selected to create the KPI")

    def _get_kpi_body(self):
        """
        Gets the KPI body of the KPI name

        :raises: HTTPError

        :rtype: dict
        :return: json dict
        """
        response = self.user.get(url=NHM_KPI_ENDPOINT_NEW.format(name=self.name), headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            raise_for_status(response, message_prefix="Could not get KPI body: '{0}'".format(self.name))

        return response.json()

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=30000, stop_max_attempt_number=3)
    def update(self, remove_all_nodes=None, remove_nodes=None, add_nodes=None, threshold_domain=None,
               threshold_value=None, replace_formula=False):
        """
        Update a KPI

        :param remove_all_nodes: whether to remove all nodes from the KPI
        :type remove_all_nodes: boolean
        :param remove_nodes: remove list of nodes/poids from KPI
        :type remove_nodes: list
        :param add_nodes: add list of nodes/poids from KPI
        :type add_nodes: list
        :param threshold_domain: Set the kpi threshold. Options: GREATER_THAN, LESS_THAN
        :type threshold_domain: str
        :param threshold_value: update the threshold value
        :type threshold_value: int
        :param replace_formula: whether to change the formula for a kpi
        :type replace_formula: boolean
        """

        body = self._get_kpi_body()
        active = body["kpiActivation"]["active"]
        if remove_all_nodes:
            body["kpiActivation"]["poidList"] = []
            body["kpiActivation"]["nodeCount"] = 0
            body["kpiActivation"]["autoUpdateKpiScope"] = False
            body["kpiActivation"]["queries"] = []
            log.logger.debug("Attempting to remove all nodes from KPI {0}".format(self.name))
        if remove_nodes:
            body["kpiActivation"]["poidList"] = remove_nodes
            body["kpiActivation"]["nodeCount"] = len(remove_nodes)
            log.logger.debug("Attempting to remove {0} nodes from KPI {1}".format(len(remove_nodes), self.name))
        if add_nodes and not active:
            body["kpiActivation"]["poidList"] = add_nodes
            body["kpiActivation"]["nodeCount"] = len(add_nodes)
            log.logger.debug("Attempting to add nodes {0} to KPI {1}".format(add_nodes, self.name))
        if add_nodes and active:
            nodes_present = body["kpiActivation"]["poidList"]
            present_nodes_count = len(nodes_present)
            body["kpiActivation"]["poidList"] = add_nodes + nodes_present
            body["kpiActivation"]["nodeCount"] = present_nodes_count + len(add_nodes)
        if threshold_domain and threshold_value:
            body["kpiActivation"]["threshold"] = {"thresholdValue": threshold_value, "thresholdDomain": threshold_domain}
            log.logger.debug("Attempting to update threshold value to {0} on KPI {1}"
                             .format(threshold_value, self.name))
        if not threshold_domain and threshold_value:
            body["kpiActivation"]["threshold"] = {"thresholdValue": threshold_value,
                                                  "thresholdDomain": body["kpiActivation"]["threshold"]["thresholdDomain"]}
            log.logger.debug("Attempting to update threshold value to {0} on KPI {1}"
                             .format(threshold_value, self.name))
        if threshold_domain and not threshold_value:
            body["kpiActivation"]["threshold"] = {"thresholdValue": body["kpiActivation"]["threshold"],
                                                  "thresholdDomain": threshold_domain}
            log.logger.debug("Attempting to update threshold value to {0} on KPI {1}"
                             .format(threshold_value, self.name))
        if replace_formula:
            body["kpiModel"]["kpiFormulaList"][0]["computation"]["abstractFormulaOperand"] = self._create_kpi_equation()
            log.logger.debug("Attempting to update formula on KPI {0}".format(self.name))

        response = self.user.post(url=NHM_KPI_ENDPOINT_EDIT, data=json.dumps(body), headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()
        log.logger.debug("The KPI {0} was successfully updated".format(self.name))

    def activate(self):
        """
        Activates a NHM KPI
        """

        self._set_activation(True)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=30000, stop_max_attempt_number=3)
    def deactivate(self):
        """
        Deactivates a NHM KPI
        """

        self._set_activation(False)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=30000, stop_max_attempt_number=3)
    def delete(self):
        """
        Deletes a NHM KPI
        """

        if self.created_by != CREATED_BY_DEFAULT:
            response = self.user.delete_request(url=NHM_KPI_ENDPOINT_DELETE.format(name=self.name))
            if response.status_code != 200:
                log.logger.debug('Failed try delete KPI. Retry: {0}'.format(self.name))
                response.raise_for_status()
            log.logger.debug("KPI '{0}' was successfully deleted".format(self.name))
        else:
            log.logger.info("KPI profile created by default, it can't be deleted")

    @retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=30000,
           stop_max_attempt_number=3)
    def _set_activation(self, status):
        if self.user.username[:6] == "NHM_13":
            payload = {"appName": "NetworkHealthAnalysis", "poList": self.po_ids, "kpiName": self.name,
                       "indexValue": None}
            response = self.user.post(url=NHM_RTKPI_ENDPOINT_ACTIVATE.format(status=status), data=json.dumps(payload),
                                      headers=self.headers_dict)
        else:
            response = self.user.put(url=NHM_KPI_ENDPOINT_ACTIVATE.format(status=status), data=json.dumps([self.name]),
                                     headers=self.headers_dict)
        if response.status_code != 200:
            log.logger.debug('Failed to activate KPI to {0}. Retry: {1}'.format(status, self.name))
            response.raise_for_status()

        log.logger.debug("Activation status of KPI {0} was set to {1}".format(self.name, status))

    def _create_kpi_equation(self):
        for _ in xrange(randint(1, 4)):
            counters = [{"piName": counter, "on": "theRO"} for counter in
                        sample(self.counters, randint(2, len(self.counters)))]
        operator = self.operators[randrange(0, len(self.operators))]
        if operator == "DIVISION" and len(counters) > 2:
            counters = sample(counters, 2)

        equation = {
            "varName": "theRO",
            "iterationSet": {
                "var": {
                    "name": "INPUT"
                },
                "setVariables": [],
            },
            "operands": [{
                "reportingInstructions": {
                    "reportingObjectIdSource": "theRO"
                },
                'operands': [{
                    'operands': counters,
                    'operator': operator
                }]
            }]}
        return equation

    def _create_router_equation(self, counters):
        """
        Creates equation used in a Router KPI

        :param counters: PM counter used in the KPI
        :type counters: list
        :return: Equation part of the Router KPI payload
        :rtype: dict
        """

        equation = {'varName': 'theRO',
                    'iterationSet': {'var': {'name': 'INPUT'}},
                    'operands': [{'reportingInstructions': {'reportingObjectIdSource': 'theRO'},
                                  'operands': [{'operator': 'MULTIPLICATION',
                                                'operands': [{'on': 'theRO', 'piName': choice(counters)},
                                                             {'on': 'theRO', 'piName': choice(counters)}]}]}],
                    'setVariables': []}
        return equation
