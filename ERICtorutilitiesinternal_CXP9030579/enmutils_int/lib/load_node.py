# ********************************************************************
# Name    : Load Node
# Summary : Extends BaseNode module. Every node in the workload pool
#           is an instance of LoadNode, responsible for managing the
#           profiles allocated.
# ********************************************************************

from requests.exceptions import HTTPError

from enmutils.lib import persistence, mutexer, log
from enmutils.lib.enm_node import (BaseNode, ERBSNode, ExtremeNode, SGSNNode, RadioNode, MGWNode, Router6672Node,
                                   MiniLinkIndoorNode,
                                   MINILink510R2Node, MINILink810R1Node, MINILink810R2Node, MiniLink2020Node, PICONode,
                                   EPGNode, RNCNode, VEPGNode, SAPCNode, RBSNode, SIU02Node, TCU02Node, TCU04Node,
                                   RadioTNode, CiscoNode, ECILightSoftNode, JuniperNode, JuniperMXNode,
                                   Fronthaul6080Node, Fronthaul6020Node, C608Node, StnNode, MTASNode,
                                   MTASTspNode, MiniLinkOutdoorNode, BSCNode, DSCNode, WCGNode, EMENode, MSCDBNode,
                                   MSCBCNode, MSCISNode, ESCNode, ERSSupportNode, Router6274Node, SbgIsNode)
from enmutils.lib.exceptions import RemoveProfileFromNodeError, AddProfileToNodeError
from enmutils.lib.persistence import persistable
from enmutils_int.lib.nrm_default_configurations.basic_network import EXCLUSIVE_PROFILES


NETEX_ENDPOINT = '/managedObjects/query?searchQuery=select%20NetworkElement'


class LoadNodeMixin(object):

    def __init__(self, *args, **kwargs):
        """
        Node Constructor

        :type args: *
        :param args: dict containing profile name and nodes exclusivity
        :type kwargs: *
        :param kwargs: list containing errors
        """
        self.profiles = kwargs.pop('profiles', [])
        self.available_to_profiles = kwargs.pop('available_to_profiles', set())
        self._is_exclusive = kwargs.pop('_is_exclusive', False)
        self.lte_cell_type = kwargs.pop('lte_cell_type', None)
        super(LoadNodeMixin, self).__init__(*args, **kwargs)

    def __eq__(self, other_node):
        """
        Check if the two instance dictionaries are equal

        :param other_node: Node instance to compare against
        :type other_node: `LoadNodeMixin`

        :return: Boolean indicating if the dictionaries are equal
        :rtype: bool
        """
        return self.__dict__ == other_node.__dict__

    @property
    def used(self):
        return bool(self.profiles)

    @property
    def is_exclusive(self):
        return self._is_exclusive

    def add_profile(self, profile):
        """
        Adds the profile to the list of profiles associated with the node

        :param profile: Profile to be added to the node.
        :type profile: enmutils_int.lib.profile.Profile
        :returns: Updated node object
        :rtype: `load_node.LoadNodeMixin`

        :raises AddProfileToNodeError: if cant add profiel to node
        """

        def _add_profile(node, in_persistence=True):
            """
            Adds the profile to the list of profiles associated with the node

            :param node: load_node.LoadNodeMixin, Node which the profile will be added to
            :type node: LoadNodeMixin
            :param in_persistence: boolean, True if the node was retrieved from persistence or False if it wasn't
            :type in_persistence: bool
            :returns: Updated node object
            :rtype: `load_node.LoadNodeMixin`

            :raises AddProfileToNodeError: if Profile cant be added to node
            """

            error_occurred = False
            if profile.NAME in node.profiles:
                error_message = ("Profile: '{0}' already exists in the list of profiles: ({1}) assigned to node:"
                                 " '{2}' .".format(profile, ','.join(profile_obj for profile_obj in node.profiles),
                                                   node.node_id))
                log.logger.debug(error_message)
                error_occurred = True
            else:
                node.profiles.append(profile.NAME)
                node._is_exclusive = True if profile.EXCLUSIVE else False
                node._persist()

            if in_persistence:
                self.profiles = node.profiles

            if error_occurred:
                raise AddProfileToNodeError

            return node

        with mutexer.mutex("persist-{}".format(self.node_id), log_output=False):
            uptodate_node = persistence.get_from_default_db(self.node_id)
            if not uptodate_node:
                return _add_profile(self, in_persistence=False)
            else:

                return _add_profile(self.compare_and_update_persisted_node(uptodate_node))

    def compare_and_update_persisted_node(self, persisted_node):
        """
        Compare the persisted node with the supplied node and update differing values

        :param persisted_node: Persisted node instance
        :type persisted_node:`LoadNodeMixin`

        :return: Persisted node instance, updated if necessary
        :rtype: `LoadNodeMixin`
        """
        if not self.__eq__(persisted_node):
            for attr, value in self.__dict__.items():
                if getattr(persisted_node, attr, None) is None and getattr(self, attr, None):
                    setattr(persisted_node, attr, value)
        return persisted_node

    def remove_profile(self, profile):
        """

        Removes the profile from the list of profiles associated with the node

        :param profile: profile.Profile, Profile to be removed from the node.
        :type profile: enmutils_int.lib.profile.Profile

        :raises RemoveProfileFromNodeError: if Profile cant be removed from node
        """

        def _remove_profile(node, in_persistence=True):
            """
            Removes the profile from the list of profiles associated with the node

            :param node: load_node.LoadNodeMixin, Node which the profile association will be removed from
            :type node: LoadNodeMixin
            :param in_persistence: boolean, True if the node was retrieved from persistence or False if it wasn't
            :type in_persistence: bool

            :raises RemoveProfileFromNodeError: if Profile cant be removed from node
            """

            try:
                node.profiles.remove(profile.NAME)
            except ValueError:
                error_message = ("Profile: '{0}' does not exist in the list of profiles: ({1}) assigned to node:"
                                 " '{2}' .".format(profile, ','.join(profile_obj for profile_obj in node.profiles),
                                                   node.node_id))
                log.logger.debug(error_message)
                raise RemoveProfileFromNodeError
            finally:
                node._is_exclusive = False
                if in_persistence:
                    # We want to sync the node object in use with the object in persistence.
                    self.profiles = node.profiles
                node._persist()

        with mutexer.mutex("persist-{}".format(self.node_id), persisted=True, log_output=False):
            # If the node is not stored yet in persistence the latest information on the node object is currently in use
            uptodate_node = persistence.get_from_default_db(self.node_id)
            if not uptodate_node:
                _remove_profile(self, in_persistence=False)
            else:
                _remove_profile(uptodate_node)

    def _persist_with_mutex(self):
        with mutexer.mutex("persist-{}".format(self.node_id)):
            self._persist()

    def _persist(self):
        """
        Add the node to the respective available persistence service
        """
        persistence.default_db().set(self.node_id, self, -1, log_values=False)

    def reset(self):
        """
        B{Resets the workload attributes}
        """
        self.profiles = []
        self._is_exclusive = False
        self._persist()

    def is_available_for(self, profile):
        """
        B{Checks node availability}
        :param profile: Profile to be checked
        :type profile: enmutils_int.lib.profile.Profile

        :return: Boolean to indicate if available
        :rtype: bool
        """
        if hasattr(profile, "EXCLUDE_NODES_FROM") and not self.exclude_nodes_from(profile):
            return False
        if EXCLUSIVE_PROFILES and self.profiles and any(prof in self.profiles for prof in EXCLUSIVE_PROFILES):
            self._is_exclusive = True
            return False
        if not self.is_exclusive and not (profile.EXCLUSIVE and self.profiles):
            return True
        else:
            if not self.used or profile.NAME in self.profiles:
                self._is_exclusive = False
                return True
        return False

    def exclude_nodes_from(self, profile):
        """
        Confirms if the node needs to be excluded if in use by conflicting profile(s)

        :param profile: Profile to be checked
        :type profile: enmutils_int.lib.profile.Profile
        :return: Boolean indicating if the node needs to be excluded or not
        :rtype: bool
        """
        if hasattr(profile, "NODE_TYPES_TO_EXCLUDE_FROM") and self.primary_type not in profile.NODE_TYPES_TO_EXCLUDE_FROM:
            return True
        else:
            for has_profile in self.profiles:
                if has_profile in profile.EXCLUDE_NODES_FROM:
                    return False
        return True

    def is_pre_allocated_to_profile(self, profile):
        return profile.NAME.upper() in self.available_to_profiles

    def set_fdn_poid(self, fdn, poid):
        self.fdn = fdn      # pylint: disable=W0201
        self.poid = poid    # pylint: disable=W0201
        self._persist_with_mutex()


@persistable
class BaseLoadNode(LoadNodeMixin, BaseNode):
    pass


@persistable
class ERBSLoadNode(LoadNodeMixin, ERBSNode):
    pass


@persistable
class ExtremeLoadNode(LoadNodeMixin, ExtremeNode):
    pass


@persistable
class SGSNLoadNode(LoadNodeMixin, SGSNNode):
    pass


@persistable
class RadioLoadNode(LoadNodeMixin, RadioNode):
    pass


@persistable
class MGWLoadNode(LoadNodeMixin, MGWNode):
    pass


@persistable
class SpitFireLoadNode(LoadNodeMixin, Router6672Node):
    pass


@persistable
class Router6672LoadNode(LoadNodeMixin, Router6672Node):
    pass


@persistable
class PICOLoadNode(LoadNodeMixin, PICONode):
    pass


@persistable
class MiniLinkLoadNode(LoadNodeMixin, MiniLinkIndoorNode):
    pass


@persistable
class MINILink510R2LoadNode(LoadNodeMixin, MINILink510R2Node):
    pass


@persistable
class MINILink810R1LoadNode(LoadNodeMixin, MINILink810R1Node):
    pass


@persistable
class MINILink810R2LoadNode(LoadNodeMixin, MINILink810R2Node):
    pass


@persistable
class MiniLinkPTLoadNode(LoadNodeMixin, MiniLink2020Node):
    pass


@persistable
class EPGLoadNode(LoadNodeMixin, EPGNode):
    pass


@persistable
class VEPGLoadNode(LoadNodeMixin, VEPGNode):
    pass


@persistable
class RNCLoadNode(LoadNodeMixin, RNCNode):
    pass


@persistable
class SAPCLoadNode(LoadNodeMixin, SAPCNode):
    pass


@persistable
class RBSLoadNode(LoadNodeMixin, RBSNode):
    pass


@persistable
class RadioTLoadNode(LoadNodeMixin, RadioTNode):
    pass


@persistable
class JuniperLoadNode(LoadNodeMixin, JuniperNode):
    pass


@persistable
class JuniperMXLoadNode(LoadNodeMixin, JuniperMXNode):
    pass


@persistable
class StnLoadNode(LoadNodeMixin, StnNode):
    pass


@persistable
class SIU02LoadNode(LoadNodeMixin, SIU02Node):
    pass


@persistable
class TCU02LoadNode(LoadNodeMixin, TCU02Node):
    pass


@persistable
class CiscoLoadNode(LoadNodeMixin, CiscoNode):
    pass


@persistable
class ECILightSoftLoadNode(LoadNodeMixin, ECILightSoftNode):
    pass


@persistable
class TCU04LoadNode(LoadNodeMixin, TCU04Node):
    pass


@persistable
class C608LoadNode(LoadNodeMixin, C608Node):
    pass


@persistable
class Fronthaul6080LoadNode(LoadNodeMixin, Fronthaul6080Node):
    pass


@persistable
class Fronthaul6020LoadNode(LoadNodeMixin, Fronthaul6020Node):
    pass


@persistable
class MTASLoadNode(LoadNodeMixin, MTASNode):
    pass


@persistable
class MTASTspLoadNode(LoadNodeMixin, MTASTspNode):
    pass


@persistable
class MiniLinkOutdoorLoadNode(LoadNodeMixin, MiniLinkOutdoorNode):
    pass


@persistable
class BSCLoadNode(LoadNodeMixin, BSCNode):
    pass


@persistable
class DSCLoadNode(LoadNodeMixin, DSCNode):
    pass


@persistable
class WCGLoadNode(LoadNodeMixin, WCGNode):
    pass


@persistable
class EMELoadNode(LoadNodeMixin, EMENode):
    pass


@persistable
class MSCDBLoadNode(LoadNodeMixin, MSCDBNode):
    pass


@persistable
class MSCBCLoadNode(LoadNodeMixin, MSCBCNode):
    pass


@persistable
class MSCISLoadNode(LoadNodeMixin, MSCISNode):
    pass


@persistable
class ESCLoadNode(LoadNodeMixin, ESCNode):
    pass


@persistable
class ERSSupportLoadNode(LoadNodeMixin, ERSSupportNode):
    pass


@persistable
class Router6274LoadNode(LoadNodeMixin, Router6274Node):
    pass


@persistable
class SbgIsLoadNode(LoadNodeMixin, SbgIsNode):
    pass


NODE_CLASS_MAP = {
    'BaseLoadNode': BaseLoadNode,
    'BSC': BSCLoadNode,
    'C608': C608LoadNode,
    'CCDM': BaseLoadNode,
    'CISCO': CiscoLoadNode,
    'CISCO-ASR900': BaseLoadNode,
    'CISCO-ASR9000': BaseLoadNode,
    'CUDB': BaseLoadNode,
    'Shared-CNF': BaseLoadNode,
    'DSC': DSCLoadNode,
    'ECI-LightSoft': ECILightSoftLoadNode,
    'EME': EMELoadNode,
    'vEME': EMELoadNode,
    'EPG': EPGLoadNode,
    'EPG-OI': BaseLoadNode,
    'VEPG': VEPGLoadNode,
    'EPG-SSR': EPGLoadNode,
    'ERBS': ERBSLoadNode,
    'ESC': ESCLoadNode,
    'ERS-SupportNode': ERSSupportLoadNode,
    'EXTREME-EOS': ExtremeLoadNode,
    'Fronthaul-6080': Fronthaul6080LoadNode,
    'FRONTHAUL-6080': BaseLoadNode,
    'FRONTHAUL-6020': Fronthaul6020LoadNode,
    'JUNIPER': JuniperLoadNode,
    'JUNIPER-MX': JuniperMXLoadNode,
    'LH': MiniLinkLoadNode,
    'MGW': MGWLoadNode,
    'MINI-LINK-Indoor': BaseLoadNode,
    'MINI-LINK-6352': MiniLinkOutdoorLoadNode,
    'MINI-LINK-CN510R2': MINILink510R2LoadNode,
    'MINI-LINK-CN810R1': MINILink810R1LoadNode,
    'MINI-LINK-CN810R2': MINILink810R2LoadNode,
    'MINI-LINK-PT2020': MiniLinkPTLoadNode,
    'MINI-LINK-669x': BaseLoadNode,
    'MLTN': MiniLinkLoadNode,
    'MSRBS_V2': RadioLoadNode,
    'MSRBS_V1': PICOLoadNode,
    'MSC-DB-BSP': MSCDBLoadNode,
    'MSC-BC-BSP': MSCBCLoadNode,
    'MSC-BC-IS': MSCISLoadNode,
    'MTAS': MTASLoadNode,
    'MTAS-TSP': MTASTspLoadNode,
    'PCG': BaseLoadNode,
    'RadioNode': RadioLoadNode,
    'RadioTNode': RadioTLoadNode,
    'RBS': RBSLoadNode,
    'RNC': RNCLoadNode,
    'Router_6672': Router6672LoadNode,
    'Router6672': Router6672LoadNode,
    'Router_6274': Router6274LoadNode,
    'Router6274': Router6274LoadNode,
    'Router6675': BaseLoadNode,
    'SBG-IS': SbgIsLoadNode,
    'SAPC': SAPCLoadNode,
    'SCU': BaseLoadNode,
    'SGSN': SGSNLoadNode,
    'SGSN-MME': BaseLoadNode,
    'SpitFire': SpitFireLoadNode,
    'STN': StnLoadNode,
    'SIU02': SIU02LoadNode,
    'Switch-6391': MiniLinkPTLoadNode,
    'TCU02': TCU02LoadNode,
    'TCU04': TCU04LoadNode,
    'vWCG': WCGLoadNode,
    'WCG': WCGLoadNode
}


def get_all_enm_network_element_objects(user):
    """
    Get all NetworkElement objects from ENM

    :param user: object to be used to make http requests
    :type user: enm_user_2.User
    :return: response
    :rtype: `Response` object
    :raises HTTPError: if the response is not ok
    """

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = user.get(NETEX_ENDPOINT, headers=headers)
    if not response.ok:
        raise HTTPError("Unable to get data from Network Explorer", response=response)

    return response


def fetch_latest_node_obj(node_ids, nodes):
    """
    Fetches latest node objects from persistence if exists
    :param node_ids: list of node ids
    :type node_ids: list
    :param nodes: list of node objects
    :type nodes: list
    :return: list of latest node objects from persistence
    :rtype: list
    """

    node_obj_list = []
    for node in nodes:
        if node.node_id in node_ids:
            node_obj = persistence.get(node.node_id)
            node_obj_list.append(node_obj if node_obj else node)
    return node_obj_list


def verify_nodes_against_enm(nodes, user):
    """
    This should verify that (passed in) nodes still exist on ENM. Log it otherwise.

    :param nodes: list of Node objects to be populated
    :type nodes: enm_node.Node
    :param user:object to be used to make http requests
    :type user: enm_user_2.User
    :return: common nodes object, node ids not on enm, enm nodes partial data
    :rtype: list, list, dict
    """
    log.logger.debug("Verifying selected nodes exist in ENM")
    all_enm_network_elements_data_json = get_all_enm_network_element_objects(user).json()

    nodes_ids = {node.node_id for node in nodes}
    # build data structure to hold nodes information received from ENM
    enm_nodes_partial_data = {
        node['moName']: (node['moType'], node['poId']) for node in all_enm_network_elements_data_json}

    # from within supplied nodes, only work with nodes that are also found on ENM
    common_nodes_ids = set(enm_nodes_partial_data).intersection(nodes_ids)
    common_nodes_obj = fetch_latest_node_obj(list(common_nodes_ids), nodes)

    node_ids_not_on_enm = list(set(nodes_ids).difference(set(enm_nodes_partial_data.keys())))

    if node_ids_not_on_enm:
        log.logger.debug("WARNING: These nodes don't appear to exist on ENM: {0}".format(node_ids_not_on_enm))

    log.logger.debug("Verifying selected nodes exist in ENM is complete")
    return common_nodes_obj, node_ids_not_on_enm, enm_nodes_partial_data


def filter_nodes_having_poid_set(nodes):
    """
    Filter nodes that have poid set

    :param nodes: list of Node objects
    :type nodes: list
    :return: list of Node objects
    :rtype: list
    """

    nodes_with_poid = [node for node in nodes if node.poid]
    log.logger.debug("Number of supplied nodes ({0}) having POID set on them: ({1})"
                     .format(len(nodes), len(nodes_with_poid)))
    return nodes_with_poid


def annotate_fdn_poid_return_node_objects(nodes):
    """
    Return Node objects having POID set.

    :param nodes: list of `LoadNodeMixin` objects
    :type nodes: list

    :return: list of Node objects
    :rtype: list
    """

    return filter_nodes_having_poid_set(nodes)
