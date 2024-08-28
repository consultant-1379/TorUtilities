# ********************************************************************
# Name    : CMSYNC MO INFO
# Summary : Module used to calculate the Network CM notifications per
#           day, by Mediation layer, node type and per applicable
#           profile.
# ********************************************************************

import math
import re

from enmutils.lib import log, persistence
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, DependencyException
from enmutils_int.lib import load_node, node_pool_mgr

MSCM_MCD_RATE = 0.04
MSCMCE_MCD_RATE = 0.5
MAX_NOTIFICATION_FIVEK = 7000000


class CmSyncMoInfo(object):

    UTRANCELL = "UtranCell"
    EUTRANCELLFDD = "EUtranCellFDD"
    EUTRANCELLTDD = "EUtranCellTDD"
    GERANCELL = "GeranCell"
    NRCELLCU = "NRCellCU"
    MO_TYPES = [UTRANCELL, EUTRANCELLFDD, EUTRANCELLTDD, NRCELLCU]
    MSCM, MSCMCE = "MSCM", "MSCMCE"
    MEDIATORS = [MSCM, MSCMCE]
    PROFILES = ["CMSYNC_01", "CMSYNC_02", "CMSYNC_04", "CMSYNC_06"]
    LTE_BASE_NOTIFICATION_RATE = 2
    WRAN_BASE_NOTIFICATION_RATE = 4
    RADIO_NODE, ERBS, RNC, MSRBS_V1 = "RadioNode", "ERBS", "RNC", "MSRBS_V1"
    ENODEB, WRAN, UMTS, EPS, MANAGED_ELEMENT_TYPE = "ENodeB", "WRAN", "UMTS", "EPS", "managed_element_type"
    RADIO_NODE_CMD = "cmedit get * NetworkElement.(neType=='{0}',technologyDomain) --table".format(RADIO_NODE)

    MEDIATION_MAP = {
        MSCM: {EUTRANCELLFDD: [ERBS], UTRANCELL: [RNC], EUTRANCELLTDD: [ERBS]},
        MSCMCE: {EUTRANCELLFDD: [RADIO_NODE, MSRBS_V1], EUTRANCELLTDD: [RADIO_NODE, MSRBS_V1], NRCELLCU: [RADIO_NODE]}
    }

    def __init__(self, user, mediation_dict, network_mo_count, mscm_ratio=0.50, mscmce_ratio=0.50, **kwargs):
        """
        Init method for CmSyncMOInfo

        :param user: User object which will query the ENM system
        :type user: `enm_user_2.User`
        :param mediation_dict: Dictionary containing information in relation to the MO breakdown of the network
        :type mediation_dict: dict
        :param network_mo_count: The total count of the network MOs
        :type network_mo_count: int
        :param mscm_ratio: Ratio of the total to be allocated to MSCM i.e 0.5 decrease by 50%
        :type mscm_ratio: float
        :param mscmce_ratio: Ratio of the total to be allocated to MSCMCE i.e 0.5 decrease by 50%
        :type mscmce_ratio: float
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary
        """
        self.user = user
        self.network_size_key = None
        self.mediator_dict = mediation_dict
        self.network_mo_count = network_mo_count
        self.mediator_ratio = {self.MSCM: mscm_ratio, self.MSCMCE: mscmce_ratio}
        self.values_per_profile = kwargs.pop("values_per_profile", {})
        self.values_per_profile_from_network_file = self.values_per_profile
        self.total_notifications = self.get_network_notification_total()
        self.max_mos_per_rnc = kwargs.pop("max_mos_per_rnc", 500)
        self.max_mos_mscmce = kwargs.pop("max_mos_mscmce", 76000)

        self.notification_ratios_per_mo_per_profile_per_mediation = {
            self.PROFILES[0]: {
                self.EUTRANCELLFDD: {
                    "UtranCellRelation": .40, "ExternalEUtranCellFDD": .05, "EUtranCellRelation": .20,
                    "GeranCellRelation": .10, "ExternalUtranCellFDD": .10, "ExternalGeranCell": .15
                },
                self.EUTRANCELLTDD: {
                    "UtranCellRelation": .40, "ExternalEUtranCellTDD": .05, "EUtranCellRelation": .20,
                    "GeranCellRelation": .10, "ExternalUtranCellTDD": .10, "ExternalGeranCell": .15
                },
                self.UTRANCELL: {
                    "GsmRelation": .0, "Rach": .0, "Pch": .0, "Hsdsch": .0, "Fach": .0
                }
            },
            self.PROFILES[1]: {
                self.EUTRANCELLFDD: {
                    "EUtranCellFDD": .49, "PmEventService": .15, "UtranCellRelation": .10,
                    "TermPointToENB": .15, "ExternalEUtranCellFDD": .05, "EUtranCellRelation": .05,
                    "EUtranFreqRelation": .01
                },
                self.EUTRANCELLTDD: {
                    "EUtranCellTDD": .49, "PmEventService": .15, "UtranCellRelation": .10,
                    "TermPointToENB": .15, "ExternalEUtranCellTDD": .05, "EUtranCellRelation": .05,
                    "EUtranFreqRelation": .01
                },
                self.UTRANCELL: {
                    "UtranCell": .30, "Rach": .10, "Pch": .10, "Hsdsch": .10, "Fach": .10, "GsmRelation": .30
                }
            },
            self.PROFILES[2]: {
                self.EUTRANCELLFDD: {
                    "EUtranCellFDD": .50, "TermPointToENB": .15, "PmEventService": .15, "UtranCellRelation": .10,
                    "EUtranCellRelation": .05, "ExternalEUtranCellFDD": .05
                },
                self.EUTRANCELLTDD: {
                    "EUtranCellTDD": .50, "TermPointToENB": .15, "PmEventService": .15, "UtranCellRelation": .10,
                    "EUtranCellRelation": .05, "ExternalEUtranCellTDD": .05
                },
                self.UTRANCELL: {
                    "UtranCell": .0, "Rach": .0, "Pch": .0, "Hsdsch": .0, "Fach": .0, "GsmRelation": .0
                }
            },
            self.PROFILES[3]: {
                self.EUTRANCELLFDD: {
                    "EUtranCellFDD": .50, "TermPointToENB": .15, "PmEventService": .15, "UtranCellRelation": .10,
                    "EUtranCellRelation": .05, "ExternalEUtranCellFDD": .05
                },
                self.EUTRANCELLTDD: {
                    "EUtranCellTDD": .50, "TermPointToENB": .15, "PmEventService": .15, "UtranCellRelation": .10,
                    "EUtranCellRelation": .05, "ExternalEUtranCellTDD": .05
                },
                self.UTRANCELL: {
                    "UtranCell": .0, "Rach": .0, "Pch": .0, "Hsdsch": .0, "Fach": .0, "GsmRelation": .0
                }
            }
        }
        self.profile_notification_calculations = {
            self.PROFILES[0]: [],
            self.PROFILES[1]: [],
            self.PROFILES[2]: [],
            self.PROFILES[3]: [],
        }
        self.profile_node_allocations = {
            self.PROFILES[0]: {},
            self.PROFILES[1]: {},
            self.PROFILES[2]: {},
            self.PROFILES[3]: {},
        }

        self.profile_duration_secs = {
            self.PROFILES[0]: 86400,
            self.PROFILES[1]: 86400,
            self.PROFILES[2]: 28800,
            self.PROFILES[3]: 720,
        }

        self.values_per_profile = self.values_per_profile_from_network_file

    def apply_mediation_limits(self):
        """
        Applies the notification limitations to RNC and MSCMCE
        """
        rnc_utrancell_limit = self.get_total_rnc_count() * self.max_mos_per_rnc
        rnc_utrancell_count = self.mediator_dict.get(self.MSCM).get(self.UTRANCELL)

        self.mediator_dict[self.MSCM][self.EUTRANCELLFDD] += (rnc_utrancell_count - rnc_utrancell_limit if
                                                              rnc_utrancell_count > rnc_utrancell_limit else 0)
        self.mediator_dict[self.MSCM][self.UTRANCELL] = (rnc_utrancell_limit if
                                                         rnc_utrancell_count > rnc_utrancell_limit else
                                                         rnc_utrancell_count)

        self.mediator_dict[self.MSCMCE][self.EUTRANCELLFDD] += (self.mediator_dict[self.MSCMCE][self.GERANCELL] +
                                                                self.mediator_dict[self.MSCMCE][self.NRCELLCU])
        self.mediator_dict[self.MSCMCE][self.GERANCELL] = 0
        self.mediator_dict[self.MSCMCE][self.NRCELLCU] = 0
        fdd_cell_count, tdd_cell_count, reduce_count_by = (self.apply_limit_mscmce_cell_count())
        self.mediator_dict[self.MSCMCE][self.EUTRANCELLFDD], self.mediator_dict[self.MSCMCE][self.EUTRANCELLTDD] = (
            fdd_cell_count, tdd_cell_count)

        self.total_notifications = self.get_network_notification_total(reduce_count_by)
        self.network_mo_count -= reduce_count_by
        log.logger.debug("Updated mediation dict: {0}".format(self.mediator_dict))

    def apply_limit_mscmce_cell_count(self):
        """
        Function to limit the notification load applied to MSCMCE

        :return: Tuple containing MSCMCE FDD/TDD cell counts, and any reduction required for total notifications
        :rtype: tuple
        """
        fdd_cell_count, tdd_cell_count = (self.mediator_dict[self.MSCMCE][self.EUTRANCELLFDD],
                                          self.mediator_dict[self.MSCMCE][self.EUTRANCELLTDD])
        total_cells = fdd_cell_count + tdd_cell_count
        reduce_count_by = 0
        if total_cells > self.max_mos_mscmce:
            reduce_count_by = total_cells - self.max_mos_mscmce
            log.logger.debug("Total cell counts for MSCMCE [{0}] exceeds limit of [{1}], reducing total count by: "
                             "[{2}].".format(total_cells, self.max_mos_mscmce, reduce_count_by))
            if fdd_cell_count == tdd_cell_count:
                fdd_cell_count -= reduce_count_by / 2
                tdd_cell_count -= reduce_count_by / 2
            elif tdd_cell_count > fdd_cell_count:
                tdd_cell_count -= reduce_count_by
            else:
                fdd_cell_count -= reduce_count_by
        return fdd_cell_count, tdd_cell_count, reduce_count_by

    def get_total_rnc_count(self):
        """
        Queries ENM for the total count of type RNC nodes

        :return: Total count of type RNC nodes
        :rtype: int
        """
        cmd = "cmedit get * NetworkElement --neType=RNC -cn"
        count = 0
        try:
            response = self.user.enm_execute(cmd)
            if response and not any(re.match(r'error', resp, re.I) for resp in response.get_output()):
                count = response.get_output()[-1].split(' ')[0]
        except Exception as e:
            log.logger.debug("Command failed, response was: {0}".format(str(e)))
        return int(count)

    def calculate_notification_per_profile_per_day(self):
        """
        Calculate the total notifications per day, for the profile
        """
        for profile_name in self.values_per_profile.iterkeys():
            if profile_name in ["CMSYNC_02"]:
                log.logger.debug("Estimated daily notifications for {0} will be calculated more granularly as the "
                                 "profile requires more UtranCell notifications.".format(profile_name))
            else:
                log.logger.debug("Estimated daily notifications for {0} is {1}.".format(
                    profile_name, self.total_notifications * self.values_per_profile.get(profile_name)))

    def get_network_notification_total(self, reduce_count_by=0):
        """
        Calculate the total number of notifications based on the total cell count

        :param reduce_count_by: Integer value to reduce the total cell
        :type reduce_count_by: int

        :return: Total number of notifications based on the total cell count
        :rtype: float
        """
        if 4000 < self.network_mo_count < 9000:
            total_count = (self.network_mo_count - reduce_count_by) * 1500.0
            return total_count if total_count < MAX_NOTIFICATION_FIVEK else MAX_NOTIFICATION_FIVEK
        else:
            return (self.network_mo_count - reduce_count_by) * 1000.0

    def set_profile_node_allocations_values(self):
        """
        Update the Num Nodes values for each profile
        """
        for profile in self.profile_notification_calculations.iterkeys():
            self.profile_node_allocations[profile] = self.determine_node_allocation_for_profile(
                self.profile_notification_calculations.get(profile))

    @staticmethod
    def determine_node_allocation_for_profile(profile_notification_lists):
        """
        Creates a node dictionary usable by load_manager

        :param profile_notification_lists: List of list containing node type, MO, total nodes, notification rate
        :type profile_notification_lists: list

        :return: Node dictionary usable by load_manager
        :rtype: dict
        """
        profile_node_dictionary = {}
        for notification_list in profile_notification_lists:
            ne_type, total_nodes = notification_list[0], notification_list[2]
            if notification_list[0] not in profile_node_dictionary.iterkeys():
                profile_node_dictionary[ne_type] = int(total_nodes) or 1
            else:
                profile_node_dictionary[ne_type] += int(total_nodes) or 1
        return profile_node_dictionary

    def set_radio_node_managed_element_type(self):
        """
        Updates the managed element type, of retrieved RadioNode objects based on the result of the ENM query
        """
        response = self.user.enm_execute(self.RADIO_NODE_CMD)
        if any(re.search(r'(error|failed)', line, re.I) for line in response.get_output()):
            raise ScriptEngineResponseValidationError("Failed to execute command: {0}.Response was {1}"
                                                      .format(self.RADIO_NODE_CMD, " ".join(response.get_output())),
                                                      response=response)
        filtered_response = response.get_output()[2::3]
        if filtered_response and self.RADIO_NODE not in filtered_response[0]:
            raise DependencyException(host='cmserv', command=self.RADIO_NODE_CMD,
                                      error='Change in format of command output: {0}'.format(filtered_response[0]))
        nodes_on_enm = {_.split('\t')[0].encode('utf-8'): _.split('\t')[-1].encode('utf-8') for _ in filtered_response}
        with node_pool_mgr.mutex():
            pool = node_pool_mgr.get_pool()
            for node in pool.node_dict.get(self.RADIO_NODE).values():
                if not node.managed_element_type:
                    tech_domain = nodes_on_enm.get(node.node_id)
                    managed_element_type = self.select_technology_domain_key(tech_domain)
                    self.persist_updated_radio_load_node(node, managed_element_type)
            pool.persist()

    @staticmethod
    def persist_updated_radio_load_node(node, managed_element_type):
        """
        Creates and persists the updated, replacement RadioLoadNode

        :param node: RadioLoadNode to be updated
        :type node: `load_node.RadioLoadNode`
        :param managed_element_type: Value to set the manage_element_type attribute to equal
        :type managed_element_type: str
        """
        n_dict = node.__dict__
        new_node = load_node.RadioLoadNode(**n_dict)
        new_node.managed_element_type = managed_element_type
        persistence.set(node.node_id, new_node, -1)

    def select_technology_domain_key(self, tech_domain):
        """
        Selects the appropriate string base on the supplied technology domain

        :param tech_domain: String containing the ENM technology domain
        :type tech_domain: str

        :return: String base on the supplied technology domain
        :rtype: str
        """
        if self.UMTS in tech_domain and self.EPS not in tech_domain:
            managed_element_type = self.WRAN
        elif self.EPS in tech_domain and self.UMTS not in tech_domain:
            managed_element_type = self.ENODEB
        else:
            managed_element_type = ",".join([self.ENODEB, self.WRAN])
        return managed_element_type

    def set_values_for_all_profiles(self):
        """
        Updates the values for the each profile
        """
        self.apply_mediation_limits()
        self.set_radio_node_managed_element_type()
        for profile_name in self.profile_notification_calculations.iterkeys():
            if self.values_per_profile.get(profile_name):
                self.set_profile_values_for_each_mediator(profile_name)

    def set_profile_values_for_each_mediator(self, profile_name):
        """
        Updates the values for the each MO type under the supplied profile, mediator

        :param profile_name: Name of the profile
        :type profile_name: str
        """
        for mediator in self.MEDIATORS:
            if sum(self.mediator_dict.get(mediator).values()):
                self.set_profile_values_for_each_mo_type(profile_name, mediator)

    def set_profile_values_for_each_mo_type(self, profile_name, mediator):
        """
        Updates the values for the each MO type under the supplied profile, mediator

        :param mediator: Name of the mediation layer
        :type mediator: str
        :param profile_name: Name of the profile
        :type profile_name: str
        """
        for mo_type in self.MO_TYPES:
            if self.mediator_dict.get(mediator).get(mo_type):
                self.set_profile_values_for_managed_object(profile_name, mediator, mo_type)

    def set_profile_values_for_managed_object(self, profile_name, mediator, mo_type):
        """
        Updates the values for the each MO type under the supplied profile, mediator

        :param mediator: Name of the mediation layer
        :type mediator: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param mo_type: MO type to be selected
        :type mo_type: str
        """
        for managed_object in self.notification_ratios_per_mo_per_profile_per_mediation.get(profile_name).get(
                mo_type).iterkeys():
            adjusted_nodes = self.calculate_adjusted_nodes_for_each_mo_per_profile(profile_name, mediator, mo_type,
                                                                                   managed_object)
            node_values = self.MEDIATION_MAP.get(mediator).get(mo_type)
            self.sort_profile_values_for_managed_object(profile_name, node_values, adjusted_nodes, managed_object)

    def sort_profile_values_for_managed_object(self, profile_name, node_values, adjusted_nodes, managed_object):
        """
        Updates the values for the each mo under the supplied profile, mediator and MO type

        :param profile_name: Name of the profile
        :type profile_name: str
        :param node_values: List containing required number of nodes
        :type node_values: list
        :param adjusted_nodes: Tuple containing the adjusted number of nodes (if applicable)
        :type adjusted_nodes: tuple
        :param managed_object: MO of which the rate is being set
        :type managed_object: str
        """
        if node_values:
            if len(adjusted_nodes) == 4:
                if adjusted_nodes[0]:
                    self.profile_notification_calculations.get(profile_name).append(
                        [node_values[0], managed_object, adjusted_nodes[0], adjusted_nodes[1]])
                if adjusted_nodes[2]:
                    self.profile_notification_calculations.get(profile_name).append(
                        [node_values[0], managed_object, adjusted_nodes[2], adjusted_nodes[3]])
            else:
                if adjusted_nodes[0]:
                    self.profile_notification_calculations.get(profile_name).append(
                        [node_values[0], managed_object, adjusted_nodes[0], adjusted_nodes[1]])

    def calculate_adjusted_nodes_for_each_mo_per_profile(self, profile_name, mediator, mo_type, managed_object):
        """
        Calculate the adjusted  nodes required for each MO

        :param mediator: Name of the mediation layer
        :type mediator: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param mo_type: MO type to be selected
        :type mo_type: str
        :param managed_object: Managed Object to send the notification to
        :type managed_object: str

        :return: Adjusted nodes required for each MO by the supplied profile
        :rtype: tuple
        """
        netsim_node_notification_rate = (self.WRAN_BASE_NOTIFICATION_RATE if mo_type == self.UTRANCELL
                                         else self.LTE_BASE_NOTIFICATION_RATE)
        if profile_name.upper() in ["CMSYNC_0{0}".format(_) for _ in range(1, 6, 2)]:
            if mediator == self.MSCM:
                netsim_node_notification_rate = MSCM_MCD_RATE
            else:
                netsim_node_notification_rate = MSCMCE_MCD_RATE
        if profile_name.upper() == "CMSYNC_06":
            # Storm rate needs to be increased to reduce high volume of node requirement
            netsim_node_notification_rate *= 8
        nodes = self.calculate_node_count_per_mo_per_profile(profile_name, mediator, mo_type, managed_object,
                                                             netsim_node_notification_rate)
        if nodes.is_integer():
            return int(math.ceil(nodes)), netsim_node_notification_rate
        else:
            rate, nodes = math.modf(nodes)
            # Rate becomes decimal, nodes becomes rate
            return int(math.ceil(nodes)), netsim_node_notification_rate, netsim_node_notification_rate, rate

    def calculate_node_count_per_mo_per_profile(self, profile_name, mediator, mo_type, managed_object,
                                                notification_rate):
        """
        Calculate the total nodes required for each MO

        :param mediator: Name of the mediation layer
        :type mediator: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param mo_type: MO type to be selected
        :type mo_type: str
        :param managed_object: Managed Object to send the notification to
        :type managed_object: str
        :param notification_rate: rate at which notifications should ideally be sent per second per node
        :type notification_rate: int

        :return: Total nodes required for each MO by the supplied profile
        :rtype: float
        """

        notifications_per_second = self.calculate_notification_rate_per_mo_per_profile_per_mo_type_per_mediator(
            profile_name, mediator, mo_type, managed_object)
        return notifications_per_second / notification_rate

    def calculate_notification_rate_per_mo_per_profile_per_mo_type_per_mediator(self, profile_name, mediator,
                                                                                mo_type, managed_object):
        """
        Calculate the total notifications per mo per profile per MO type per mediator per second

        :param mediator: Name of the mediation layer
        :type mediator: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param mo_type: MO type to be selected
        :type mo_type: str
        :param managed_object: Managed Object to send the notification to
        :type managed_object: str

        :return: Total notifications per mo per profile per MO type per mediator per second
        :rtype: float
        """
        total_notifications_per_mo = self.calculate_notifications_per_day_per_mo(profile_name, mediator, mo_type,
                                                                                 managed_object)
        return round(total_notifications_per_mo / self.profile_duration_secs.get(profile_name), 4)

    def calculate_notifications_per_day_per_mo(self, profile_name, mediator, mo_type, managed_object):
        """
        Calculate the total number of notifications per MO per day for the supplied profile

        :param mediator: Name of the mediation layer
        :type mediator: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param mo_type: MO type to be selected
        :type mo_type: str
        :param managed_object: Managed Object to send the notification to
        :type managed_object: str
        :var updated_rate: Updates percentage rate of values_per_profile for UtranCell notifications to 1.0

        :return: Total number of notifications per MO per day for the supplied profile
        :rtype: float
        """
        updated_rate = None
        if profile_name in ["CMSYNC_02"] and mo_type == "UtranCell":
            updated_rate = 1.0
        log.logger.debug("Calculating daily notifications for profile: {0}.".format(profile_name))
        total = self.calculate_notifications_per_profile_per_day_per_mo(profile_name,
                                                                        mediator, mo_type, updated_rate)
        mo_percentage = self.notification_ratios_per_mo_per_profile_per_mediation.get(profile_name).get(
            mo_type).get(managed_object)
        result = round(total * mo_percentage, 4)
        log.logger.debug("Daily notifications calculated successfully")
        return result

    def calculate_notifications_per_profile_per_day_per_mo(self, profile_name, mediator, mo_type,
                                                           updated_rate=None):
        """
        Calculate the total number of notifications per MO type per day for the supplied profile

        :param mediator: Name of the mediation layer
        :type mediator: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param mo_type: MO type to be selected
        :type mo_type: str
        :param updated_rate: Updates percentage rate of values_per_profile for UtranCell notifications to 1.0
        :type updated_rate: float

        :return: Total number of notifications per mo_type per day for the supplied profile
        :rtype: float
        """

        log.logger.debug("Calculating the number of notifications per MO type for {0}.".format(profile_name))
        total = self.calculate_notification_per_profile_per_day_per_mediator(profile_name, mediator, updated_rate)

        percentage_mediator = self.get_network_percentage_for_mediator_per_mo(mediator, mo_type)
        result = round(total * percentage_mediator, 4)
        log.logger.debug("Successfully calculated notifications per MO per day for {0}.".format(profile_name))
        return result

    def calculate_notification_per_profile_per_day_per_mediator(self, profile_name, mediator, updated_rate=None):
        """
        Calculate the total notifications per day, for the supplied mediator and profile

        :param mediator: Name of the mediation layer
        :type mediator: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param updated_rate: Updates percentage rate of values_per_profile for UtranCell notifications to 1.0
        :type updated_rate: float

        :return: Total notifications per day, for the supplied mediator and profile
        :rtype: float
        """
        total = self.total_notifications_count_per_mediator_per_day(mediator)
        log.logger.debug("Calculating the number of notifications per day per mediator: {0} for Profile: {1}."
                         .format(mediator, profile_name))
        result = int(total * updated_rate) if updated_rate else int(total * self.values_per_profile.get(profile_name)) if self.values_per_profile.get(profile_name) else 0
        log.logger.debug("Notifications successfully calculated per day per mediator: {0} for Profile: {1}."
                         .format(mediator, profile_name))
        return result

    def total_notifications_count_per_mediator_per_day(self, mediator):
        """
        Calculate the breakdown of total notifications * mediator percentage

        :param mediator: Name of the mediation layer
        :type mediator: str

        :return: Total notifications * mediator percentage
        :rtype: int
        """

        return round(self.total_notifications * self.get_network_percentage_for_mediator(mediator), 4)

    def get_network_percentage_for_mediator_per_mo(self, mediator, mo_type):
        """
        Return the count of given mediation layer, expressed as a percentage of the MO

        :param mediator: Name of the mediation layer
        :type mediator: str
        :param mo_type: MO type to be selected
        :type mo_type: str

        :return: Mediator percentage value for the MO type
        :rtype: float
        """
        total_mos_for_all_mo_types_in_mediator = sum(self.mediator_dict.get(mediator).values())
        total_mos_for_particular_mo_type_in_mediator = self.mediator_dict.get(mediator).get(mo_type)
        if float(total_mos_for_all_mo_types_in_mediator):
            return round(total_mos_for_particular_mo_type_in_mediator /
                         float(total_mos_for_all_mo_types_in_mediator), 4)
        else:
            return 0.00

    def get_network_percentage_for_mediator(self, mediator):
        """
        Return the count of given mediation layer, expressed as a percentage of the whole network

        :param mediator: Name of the mediation layer
        :type mediator: str

        :return: Total percentage value for the mediation layer
        :rtype: int
        """
        if self.mediator_ratio.get(mediator) and self.mediator_ratio.get(mediator) != 0.50:
            return self.mediator_ratio.get(mediator)
        try:
            return float(self.get_percentage_total(sum(self.mediator_dict.get(mediator).values())) / 100)
        except AttributeError:
            log.logger.debug("Mediation service {0} not found, no results.".format(mediator))

    def get_percentage_total(self, mo_type_count, total=None):
        """
        Calculates the given number of MOs as a percentage of the total MOs provided

        :param mo_type_count: Number to be determined as a percentage
        :type mo_type_count: int
        :param total: Total volume of MOs to be representative of 100%
        :type total: int

        :return: Percentage calculation of MO type / total_MOs
        :rtype: float
        """
        total = total if total is not None else self.network_mo_count
        if not total:
            log.logger.debug("Total volume of MOs supplied: {0}".format(total))
            return 0
        return round(100 * mo_type_count / float(total), 4)
