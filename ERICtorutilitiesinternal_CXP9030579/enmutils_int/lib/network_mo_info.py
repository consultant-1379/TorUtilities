# ********************************************************************
# Name    : Network MO Info
# Summary : Used by CmSync Setup to determine network cell breakdown.
#           Allows the user to query ENM for type and count of cells
#           in the network, LTE/Geran/Utran/NR cells, counts each
#           cell type and sorts them by mediation type and NE type,
#           queries ENM for RNC cells and generates content of query
#           as readable file to be used by CmSync profiles.
# ********************************************************************

import re

from enmutils.lib import log, filesystem
from enmutils.lib.exceptions import (ScriptEngineResponseValidationError, NoNodesWithReqMosOnEnm,
                                     NoRequestedMoInfoOnEnm, EnvironError)
from enmutils_int.lib.enm_user import get_workload_admin_user

DYNAMIC_DIR = "/home/enmutils/dynamic_content"
CARDINALITY_FILE = DYNAMIC_DIR + "/.cardinality_data.json"
MO_FILE = DYNAMIC_DIR + "/.simulation_mo_data.json"
UTRANCELL_FILE_PATH = ""
GSM_RELATION_FILE_PATH = DYNAMIC_DIR + "/.cmsync_gsm_relation_data"


class UnsupportedNeTypeException(EnvironError):
    pass


class NetworkMoInfo(object):

    UTRANCELL = "UtranCell"
    EUTRANCELLFDD = "EUtranCellFDD"
    EUTRANCELLTDD = "EUtranCellTDD"
    GERANCELL = "GeranCell"
    NRCELLCU = "NRCellCU"
    MO_TYPES = [UTRANCELL, EUTRANCELLFDD, EUTRANCELLTDD, GERANCELL, NRCELLCU]
    MSCM, MSCMCE = "MSCM", "MSCMCE"
    RADIO_NODE, ERBS, RNC, MSRBS_V1, BSC = "RadioNode", "ERBS", "RNC", "MSRBS_V1", "BSC"

    MEDIATION_MAP = {
        MSCM: {EUTRANCELLFDD: [ERBS], UTRANCELL: [RNC], EUTRANCELLTDD: [ERBS]},
        MSCMCE: {EUTRANCELLFDD: [RADIO_NODE, MSRBS_V1], EUTRANCELLTDD: [RADIO_NODE, MSRBS_V1], GERANCELL: [BSC], NRCELLCU: [RADIO_NODE]}
    }

    def __init__(self, user):
        """
        Initialiser for NetworkCellInfo

        :param user: User object which will query the ENM system
        :type user: `enm_user_2.User`
        """
        self.user = user
        self.mediator_dict = {
            self.MSCM: {self.EUTRANCELLFDD: 0, self.EUTRANCELLTDD: 0, self.UTRANCELL: 0, self.GERANCELL: 0, self.NRCELLCU: 0},
            self.MSCMCE: {self.EUTRANCELLFDD: 0, self.EUTRANCELLTDD: 0, self.UTRANCELL: 0, self.GERANCELL: 0, self.NRCELLCU: 0}
        }
        self.network_mo_count = 0

    def get_network_mos_info(self, mo_types=None):

        """
        Gets all or a specified list of MO instances on the network via cm cli application and groups them in a dict
        of, MO type : list of associated FDN's e.g. :
        {'GeranCell': [], 'EUtranCellFDD': [
        u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,
        EUtranCellFDD=LTE02ERBS00001-1',
        u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,ENodeBFunction=1,
        EUtranCellFDD=LTE02ERBS00002-1']}

        If it fails to get MO instances it will retry for max of 5 times.

        :param mo_types: list of MO types to query ENM for
        :type mo_types: list

        :rtype: dict
        :return: dict, the key being the MO type and the value being a list of associated FDN's containing that MO
        """
        mo_types = self.MO_TYPES if not mo_types else mo_types
        log.logger.debug('Attempting to get all MO instances of type "{mo_types}" as available on ENM.'.format(
            mo_types=mo_types))

        cmds = []
        for mo in mo_types:
            cmds.append('cmedit get * {0}'.format(mo))

        fdns_per_mo_type = {}
        for cmd in cmds:
            response = self.user.enm_execute(cmd)
            if "Error 9999" in str(response.get_output()):
                for _retry in range(5):
                    log.logger.debug("retrying {0}".format(_retry + 1))
                    response = self.user.enm_execute(cmd)
                    if "Error 9999" in str(response.get_output()):
                        log.logger.debug("command executed: {0} and got Error 9999 response from ENM".format(cmd))
                    else:
                        break

            if any(re.search(r'^0\sinstance\(s\)', line, re.I) for line in response.get_output()):
                log.logger.debug('Failed to execute command: "{0}". Response was {1}'
                                 .format(cmd, " ".join(response.get_output())))
            fdns = [line for line in response.get_output() if "FDN : " in line]
            fdns_per_mo_type[cmd.split()[-1]] = fdns

        self.network_mo_count = sum(len(_) for _ in fdns_per_mo_type.values())
        log.logger.debug(
            'The Total Volume of Network MO of type "{0}" is: "{1}" .'.format(mo_types, self.network_mo_count))

        log.logger.debug('Successfully retrieved all MO instances of type "{MO_types}" as available on ENM.'.format(
            MO_types=mo_types))

        return fdns_per_mo_type

    def get_mo_network_info_subgrouped_by_node(self):
        """
        Gets all the MO instances on the network via cm cli application and groups them firstly by MO type and then
        by node withing the MO type. e.g. :
        MO type : { Node_Name : list of associated FDN's} e.g. :
        Updates the network MO type dictionary into node, MO type per node values

        {'GeranCell': {}, 'EUtranCellFDD': {
            'LTE06dg2ERBS00007': [
                u'FDN : SubNetwork=NETSimW,ManagedElement=LTE06dg2ERBS00007,ENodeBFunction=1,
                EUtranCellFDD=LTE06dg2ERBS00007-1',
                u'FDN : SubNetwork=NETSimW,ManagedElement=LTE06dg2ERBS00007,ENodeBFunction=1,
                EUtranCellFDD=LTE06dg2ERBS00007-2']}

        ::return: dictionary of dictionaries, key being the MO type and the value being a dict with the node name as
                  the key and the value being a list of associated FDN's
        :rtype: dict
        """

        log.logger.debug('Attempting to get the MO instances of types "{MO_types}" as available on ENM and '
                         'subgroup them by node'.format(MO_types=self.MO_TYPES))

        mo_type_dict = self.get_network_mos_info()
        for key in mo_type_dict.iterkeys():
            mo_type_dict[key] = group_mos_by_node(mo_type_dict.get(key))

        log.logger.debug('Successfully retrieved the MO instances of type "{mo_types}" as available on ENM '
                         'subgrouping them by node'.format(mo_types=self.MO_TYPES))

        return mo_type_dict

    def group_ne_type_per_mo_type_and_count(self):
        """
        Queries ENM for node NetworkElement, then groups according to Ne Type which groups further to MO type and the
        total count of the MO types

        :return: Returns a dictionary of dictionaries, the keys being the Ne Type (str), and the values being another
        dict with the key being the MO type (str) and the value being the total number of those MOs (int)
        :rtype: dict
        """

        log.logger.debug('Attempting to group all the MOs by their respective ne types.')

        result = {}
        mos_dict = self.get_mo_network_info_subgrouped_by_node()
        self.generate_and_update_gsm_relation_file()
        ne_type_dict = self.build_ne_type_dict()

        for mo_type in mos_dict.iterkeys():
            for key, value in mos_dict.get(mo_type).iteritems():
                ne_type = ne_type_dict.get(key)
                if ne_type not in result.iterkeys():
                    result[ne_type] = {}
                if mo_type not in result.get(ne_type).iterkeys():
                    result[ne_type][mo_type] = 0
                result[ne_type][mo_type] = result.get(ne_type).get(mo_type) + len(value)

        log.logger.debug('Successfully grouped all the MOs by their respective ne types.')

        return result

    def build_ne_type_dict(self):
        """
        Groups the Node with the associated neType

        :raises ScriptEngineResponseValidationError: if the ENM query response has errors or
        no instance of nodes with neTypes

        :return: dict
        :rtype: dict, the key being the Node Name and the Value being the neType

        """

        log.logger.debug('Attempting to build a dictionary of Node Names and associated neTypes')

        query = "cmedit get * NetworkElement.neType"
        response = self.user.enm_execute(query)
        if any(re.search(r'(^0\sinstance\(s\)|error)', line, re.I) for line in response.get_output()):
            raise ScriptEngineResponseValidationError("Failed to execute command: {0}.Response was {1}"
                                                      .format(query, " ".join(response.get_output())),
                                                      response=response)
        output = response.get_output()
        ne_type_dict = {}
        for i, line in enumerate(output):
            if "FDN : " in line:
                ne_type_dict[line.split(": NetworkElement=")[-1].strip().encode('utf-8')] = output[i + 1].split("neType : ")[-1].encode('utf-8')

        log.logger.debug('Successfully built a dictionary of Node Names and associated neTypes')

        return ne_type_dict

    def retrieve_list_of_rnc_nodes_from_enm(self):
        """
        Query ENM for all RNCs created on the system

        :return: List of all RNCs created on the system
        :rtype: list
        """
        rncs = []
        try:
            response = self.user.enm_execute("cmedit get * NetworkElement -ne=RNC")
            output = response.get_output()
            rncs = [line.split("NetworkElement=")[-1] for line in output if "FDN" in line]
        except Exception as e:
            log.logger.debug(str(e))
        return rncs

    def generate_and_update_gsm_relation_file(self):
        """
        Create directory under /var/log/enmutils, generating a file containing all found GsmRelations
        """
        log.logger.debug("Starting query of ENM for existing RNC GsmRelation values.")

        if filesystem.does_file_exist(GSM_RELATION_FILE_PATH):
            filesystem.delete_file(GSM_RELATION_FILE_PATH)
            filesystem.touch_file(GSM_RELATION_FILE_PATH)
        rncs = self.retrieve_list_of_rnc_nodes_from_enm()
        for rnc in rncs:
            try:
                response = self.user.enm_execute("cmedit get {0} GsmRelation -ne=RNC".format(rnc.strip()))
                filesystem.write_data_to_file(
                    "\n".join(["ManagedElement=1{0}".format(line.split(',ManagedElement=1')[-1])
                               for line in response.get_output() if "FDN : " in line]), GSM_RELATION_FILE_PATH,
                    append=True)
                filesystem.write_data_to_file("\n", GSM_RELATION_FILE_PATH, append=True)
            except Exception as e:
                log.logger.debug("Failed to retrieve mo GsmRelation information, error encountered: {0}".format(str(e)))
        log.logger.debug("Completed query of ENM for existing RNC GsmRelation values.")

    def map_ne_types_to_mediator_and_update_mo_count(self):
        """
        Matches the ne type to the mediation, and updates the respective mediation MO type count
        """
        ne_type_mo_type_dict = self.group_ne_type_per_mo_type_and_count()
        unmatched_ne_types = []
        for ne_type in ne_type_mo_type_dict.iterkeys():
            mediator = self.match_to_mediatior(ne_type)
            if not mediator:
                unmatched_ne_types.append(ne_type)
                continue
            self.mediator_dict[mediator] = self.update_mediation_mo_count_values(self.mediator_dict.get(mediator),
                                                                                 ne_type_mo_type_dict.get(ne_type))
        log.logger.debug("Unable to locate NeType(s): [{0}] in mediation dictionary.".format(set(unmatched_ne_types)))

    def match_to_mediatior(self, ne_type):
        """
        Matches the given Ne Type to the respective CM mediator

        :param ne_type: Node Ne Type
        :type ne_type: str

        :return: Relevant mediation key
        :rtype: str
        """
        for mediator in self.MEDIATION_MAP.iterkeys():
            for value in self.MEDIATION_MAP.get(mediator).itervalues():
                if ne_type in value:
                    return mediator

    @staticmethod
    def update_mediation_mo_count_values(mo_mediation_dict, ne_type_mo_mediation):
        """
        Update the MO type totals per mediation service based on the ne type dictionary

        :param mo_mediation_dict: Current values for the MO, total for the particular mediation service
        :type mo_mediation_dict: dict
        :param ne_type_mo_mediation: Current values for the MO, total for the ne type matched to the mediator
        :type ne_type_mo_mediation: dict

        :return: Updated values for the MO, total for the particular mediation service
        :rtype: dict
        """
        for key, value in ne_type_mo_mediation.iteritems():
            mo_type_total = mo_mediation_dict.get(key) + value
            mo_mediation_dict[key] = mo_type_total
        return mo_mediation_dict


def get_nodes_with_required_num_of_mos_on_enm(mo_and_count_per_node):
    """
    Gets all the nodes on ENM that have the required number of MOs specified in the network file for each profile
    e.g. MO_AND_COUNT_PER_NODE: {GERANCELL : 250}

    :param mo_and_count_per_node: containing the MO type as the key and the total MO count required as the value
    :type mo_and_count_per_node: dict

    :raises NoRequestedMoInfoOnEnm: if no MO information for the MO specified existed in ENM
    :raises NoNodesWithReqMosOnEnm: if no nodes with the required MOs were found on ENM

    :return: list of node names that contain the required number of MOs requested
    :rtype: list
    """

    log.logger.debug('Attempting to get nodes with the required num of MOs: "{0}" on ENM'.format(mo_and_count_per_node))

    network_mo_info_obj = NetworkMoInfo(get_workload_admin_user())
    # strip out blank mo values before returning
    mo_info = network_mo_info_obj.get_network_mos_info(mo_and_count_per_node.keys())
    if not mo_info:
        raise NoRequestedMoInfoOnEnm(
            'No MO information retrieved from ENM for MOs: "{0}" '.format(mo_and_count_per_node.keys()))

    node_names_with_req_num_mos = []

    for mo_type, fdns in mo_info.iteritems():
        num_mos_required = mo_and_count_per_node[mo_type]

        node_to_mos_dict = network_mo_info_obj.group_mos_by_node(fdns)
        for node_name, mos in node_to_mos_dict.iteritems():
            if len(mos) >= num_mos_required:
                node_names_with_req_num_mos.append(node_name)

    if not node_names_with_req_num_mos:
        raise NoNodesWithReqMosOnEnm(
            'No nodes with the required num of MOs: "{0}" found on ENM.'.format(mo_and_count_per_node))

    log.logger.debug('Successfully retrieved "{0}" nodes with the required num of MOs: "{1}" on ENM'.format(
        len(node_names_with_req_num_mos), mo_and_count_per_node))

    return node_names_with_req_num_mos


def group_mos_by_node(mo_list):
    """
    Group MOs by their respective nodes

    :param mo_list: list of node MOs to be grouped
    :type mo_list: list

    :return: dict, with the node name as the keys and a list of the associated MOs as the value
    :rtype: dict
    """

    log.logger.debug('Attempting to group all the MOs by their respective node.')

    data_store = {}
    mecontext_key = "MeContext="
    for fdn in mo_list:
        node_name = fdn.encode('utf-8').split(mecontext_key)[-1].split(",")[0] if mecontext_key in fdn.encode('utf-8') else fdn.encode('utf-8').split("ManagedElement=")[-1].split(",")[0]
        if node_name not in data_store.iterkeys():
            data_store[node_name] = []
        data_store[node_name].append(fdn)

    log.logger.debug('Successfully grouped all the MOs by their respective nodes.')

    return data_store
