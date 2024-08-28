# ********************************************************************
# Name    : NetSim MO
# Summary : Primary used by CmSync profiles. Used to create a pythonic
#           representation of an MOTree, provides a usable MO path,
#           which can be supplied to NetSim to generate notifications,
#           responsible for executing dumpmotree command on NetSim host.
# ********************************************************************

from enmutils.lib import thread_queue, log
from enmutils.lib.exceptions import FailedNetsimOperation
from enmutils_int.lib import netsim_executor


class MOType(object):
    CREATE_MO_CMD = 'createmo:parentid="{moid}",type="{motype}",name="{moname}";'
    DELETE_MO_CMD = 'deletemo:moid="{moid}";'

    def __init__(self, type_name, nodes, mo_path=None):
        """
        Creates a MOType object, used to describe a MO on a node, i.e. how to locate it, what information is required
        to create it, etc

        :param type_name: The MO type described by this object
        :type type_name: string
        :param nodes: A list of nodes that this MO type relates to
        :type nodes: list
        :param mo_path: Path to the MO
        :type mo_path: str
        """

        self.type = type_name
        self.nodes = nodes

        self.mo_path = mo_path

        # Avc burst info
        self.notification_rate = 0
        self.mo_attribute = None
        self.mo_values = None

    @property
    def parent_mo_path(self):
        parent_path = ",".join(self.mo_path.split(',')[:-1]) if self.mo_path else None
        return parent_path

    @property
    def name(self):
        return self.mo_path.split(',')[-1].split('=')[-1]

    @property
    def create_commands(self):
        # DG2 nodes include a 'Namespace' before the MO name, which can't be use in the create command
        moid_without_namespaces = ",".join([mo.split(':')[-1] for mo in self.parent_mo_path.split(',')])
        return [self.CREATE_MO_CMD.format(moid=moid_without_namespaces, motype=self.type.split(':')[-1], moname=self.name)]

    @property
    def delete_commands(self):
        return [self.DELETE_MO_CMD.format(moid=self.mo_path)]

    @property
    def mos(self):
        return [mo_info.split('=')[0] for mo_info in self.mo_path.split(',')]

    def add_avc_burst_info(self, notification_rate, mo_attribute, mo_values):
        self.notification_rate = notification_rate
        self.mo_attribute = mo_attribute
        self.mo_values = mo_values


class NewMOType(MOType):

    def __init__(self, type_name, nodes, mo_path, create_from_parent_mo=None, name="new"):
        """
        Creates a NewMOType object, used to describe a new MO on a node, i.e. how to locate it, etc. The MO currently
        doesn't exist on the node, as this MO object is intended for creation on the node.

        :param type_name: The MO type described by this object
        :type type_name: string
        :param nodes: A list of nodes that this MO type relates to
        :type nodes: list
        :param create_from_parent_mo: The highest MO type in the MO tree that requires creating prior to this MO. Only
        required where the parent must be created prior to the creation of this MO type due to number of children
        restrictions.
        :type create_from_parent_mo: str
        :param mo_path: Path to the MO
        :type mo_path: str
        :param name: Name of the MO to be created
        :type name: str
        """
        mo_path = "{0},{1}={2}".format(mo_path, type_name, name)
        super(NewMOType, self).__init__(type_name, nodes, mo_path)
        self.create_from_parent_mo = create_from_parent_mo

    @property
    def mos_to_create(self):
        create_mos = None
        if self.create_from_parent_mo:
            create_mos = self.mos[self.mos.index(self.create_from_parent_mo):]
        return create_mos

    @property
    def create_commands(self):
        commands = []
        if self.create_from_parent_mo:
            for mo_type in self.mos_to_create:
                create_from_index = self.mos.index(mo_type)
                mo_id = ",".join(self.mo_path.split(',')[:create_from_index])
                moid_without_namespaces = ",".join([mo.split(':')[-1] for mo in mo_id.split(',')])
                mo_name = [mo_info.split('=')[1] for mo_info in self.mo_path.split(',') if mo_type in mo_info][0]
                commands.append(self.CREATE_MO_CMD.format(moid=moid_without_namespaces, motype=mo_type.split(':')[-1], moname=mo_name))
        else:
            # DG2 nodes include a 'Namespace' before the MO name, which can't be use in the create command
            moid_without_namespaces = ",".join([mo.split(':')[-1] for mo in self.parent_mo_path.split(',')])
            commands.append(self.CREATE_MO_CMD.format(moid=moid_without_namespaces, motype=self.type.split(':')[-1], moname=self.name))

        return commands

    @property
    def delete_commands(self):
        commands = []
        if self.create_from_parent_mo:
            create_from_index = self.mos.index(self.create_from_parent_mo)
            mo_id = ",".join(self.mo_path.split(',')[:create_from_index + 1])
            moid_without_namespaces = ",".join([mo.split(':')[-1] for mo in mo_id.split(',')])
            commands.append(self.DELETE_MO_CMD.format(moid=moid_without_namespaces))
        else:
            moid_without_namespaces = ",".join([mo.split(':')[-1] for mo in self.mo_path.split(',')])
            commands.append(self.DELETE_MO_CMD.format(moid=moid_without_namespaces))

        return commands


def _get_mo_tree(motree, parent_types):
    """
    Update the MOTree, for the supplied parent MOs

    :param motree: Instance of MOTree` to be updated
    :type motree: `MOTree`
    :param parent_types: A list of the mo types expected in the mo path.
    :type parent_types: list

    :return: Updated MOTree object
    :rtype: MOTree`
    """
    motree.set_mo_tree_for_specific_types(parent_types)
    return motree


def _get_mo_path_to_type(mo_tree, parent_types, create_mo_from_parent_type=None):
    """
    Gets the MO path to a particular type, depending if creating a new MO or getting the path to an existing node MO.

    :param mo_tree: The MOTree object to use to locate the path of the MO
    :type mo_tree: `MOTree` instance
    :param parent_types: A list of the mo types expected in the mo path.
    :type parent_types: list
    :param create_mo_from_parent_type: If creating a new MO and a MO's parent(s) must be created
    :type create_mo_from_parent_type: str

    :return: The path to the required MO.
     :rtype: str
    """
    if create_mo_from_parent_type:
        # Get the path to the parent of the first mo type that requires creation
        path_to_type = parent_types[:parent_types.index(create_mo_from_parent_type)][-1]
        existing_mo_path = mo_tree.get_mo_path(mo_tree.mo_tree, path_to_type)

        # Generate a mo path for new mo_types
        new_parent_types_path = "=CMSYNC,".join(parent_types[parent_types.index(create_mo_from_parent_type):])
        mo_path = "{},{}=CMSYNC".format(existing_mo_path, new_parent_types_path)
    else:
        mo_path = mo_tree.get_mo_path(mo_tree.mo_tree, parent_types[-1])

    return mo_path


def get_mo_types_on_nodes(type_name, parent_types, nodes, new_mo=False, create_mo_from_parent_type=None):
    """
    Given a mo type and its parent types returns NewMOType objects for the nodes provided. Note all parent types should
    be specified.

    :param type_name: The MO type to find on the nodes
    :type type_name: str
    :param parent_types: A list of the mo types expected in the mo path.
    :type parent_types: list
    :param nodes: The enm_node.BaseNode objects to find the MO info for
    :type nodes: list
    :param new_mo: Boolean to indicate if MO is being created or not
    :type new_mo: bool
    :param create_mo_from_parent_type: If creating a new MO and a MO's parent(s) must be created
    :type create_mo_from_parent_type: str

    :return: a list of NewMOTypes
    :rtype: list
    """
    node_mo_paths = {node.netsim: {} for node in nodes}
    mo_types = []
    worklist = [MOTree(node) for node in nodes]

    parent_types = parent_types if new_mo else parent_types + [type_name]
    if worklist:
        tq = thread_queue.ThreadQueue(worklist, num_workers=4, func_ref=_get_mo_tree, args=[parent_types])
        tq.execute()
    else:
        log.logger.debug("Could not create work list for nodes: [{}]".format(nodes))

    # Determine the unique MO paths discovered and the nodes that those paths apply to
    for tree in worklist:
        if tree.mo_tree:
            mo_path = _get_mo_path_to_type(tree, parent_types, create_mo_from_parent_type)
            netsim = tree.node.netsim
            if mo_path and mo_path in node_mo_paths[netsim].keys():
                node_mo_paths[netsim][mo_path].append(tree.node)
            elif mo_path:
                node_mo_paths[netsim][mo_path] = [tree.node]
    return create_mo_types(node_mo_paths, new_mo, type_name, create_mo_from_parent_type, mo_types)


def create_mo_types(node_mo_paths, new_mo, type_name, create_mo_from_parent_type, mo_types):
    """
    Create the MO Type objects

    :param node_mo_paths: Dictionary of MO paths for each node
    :type node_mo_paths: dict
    :param new_mo: Boolean to indicate if MO is being created or not
    :type new_mo: bool
    :param type_name: The MO type to find on the nodes
    :type type_name: str
    :param create_mo_from_parent_type: If creating a new MO and a MO's parent(s) must be created
    :type create_mo_from_parent_type: str
    :param mo_types: List of existing MOType objects
    :type mo_types: list
    :return: List of MOType objects
    :rtype: list
    """
    for netsim in node_mo_paths.keys():
        for mo_path in node_mo_paths[netsim].keys():
            if new_mo:
                mo_types.append(NewMOType(type_name=type_name, nodes=node_mo_paths[netsim][mo_path], mo_path=mo_path,
                                          create_from_parent_mo=create_mo_from_parent_type))
            else:
                mo_types.append(MOType(type_name=type_name, nodes=node_mo_paths[netsim][mo_path], mo_path=mo_path))

    return mo_types


def determine_mo_types_required(mo_burst_info, nodes, for_existing_mo=True):
    """
    Given a list of nodes and the required MO information returns a list of MOType objects where each MOType represents
    a MO with a unique path located on particular nodes. E.g. if the MO's path may be found on all nodes then one MOType
    object is returned

    :type mo_burst_info: dict
    :param mo_burst_info: The dictionary element represents information on the MOType.
        The Dictionary requires the following elements:
        {"notification_percentage_rate": 0.45,
         "node_type": "ERBS",
         "mo_type_name": "EUtranCellFDD",
         "mo_path": "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=%NENAME%-1",
         "parent_mo_names": None,
         "mo_attribute": "userLabel",
         "mo_values": ["abc", "def", "ghi"]}
         NOTE: the 'mo_path' option takes precedence over the 'parent_mo_name' option, so if one is specified the other
           should be None. THe 'mo_path' option specifies the full MO path to the MO which would be common across all
           the nodes, whereas the 'parent_mo_names' is used where the path may not be common across all the nodes and we
           need to query the nodes to find the exact path
    :type nodes: list of enm_node.ENMNode objects
    :param nodes: A list of the nodes that the MOs are located on
    :type for_existing_mo: Boolean
    :param for_existing_mo: True if MO is not being created

    :rtype: list
    :return: A list of MOType objects
    """

    mo_types = []
    mo_class = MOType if for_existing_mo else NewMOType

    def _common_path_to_mo():
        try:
            return mo_burst_info["mo_path"]
        except:
            return False

    if _common_path_to_mo():
        # One MOType object may be used to describe the MO for all the nodes
        mo_type = mo_class(type_name=mo_burst_info["mo_type_name"], nodes=nodes,
                           mo_path=mo_burst_info["mo_path"])

        mo_types.append(mo_type)
    else:
        # Multiple MOType objects required as they have unique paths to the MO on the nodes
        mos = get_mo_types_on_nodes(type_name=mo_burst_info["mo_type_name"],
                                    parent_types=mo_burst_info["parent_mo_names"],
                                    nodes=nodes, new_mo=False if for_existing_mo else True)

        mo_types.extend(mos)

    return mo_types


def determine_mo_types_required_with_mcd_burst_info(mo_burst_info, nodes, required_rate):
    # Calculate the rate of the burst
    total_mo_rate = round(required_rate * mo_burst_info["notification_percentage_rate"], 3)

    # Set the required rate on the MO Types
    mo_types = determine_mo_types_required(mo_burst_info, nodes, for_existing_mo=False)
    for mo_type in mo_types:
        rate_per_burst = (total_mo_rate / len(nodes)) * len(mo_type.nodes)
        log.logger.debug(
            "MO TYPE: type: {type}, MO path: {mo_path}, # nodes: {num_nodes}, burst rate: {burst_rate}".format(
                type=mo_type.type, mo_path=mo_type.mo_path, num_nodes=len(mo_type.nodes),
                burst_rate=rate_per_burst))

        mo_type.notification_rate = rate_per_burst

    return mo_types


def determine_mo_types_required_with_avc_burst_info(mo_burst_info, nodes, required_rate):
    """
    Given a list of nodes and the required MO information returns a list of MOType objects where each MOType represents
    a MO with a unique path located on particular nodes. E.g. if the MO's path may be found on all nodes then one MOType
    object is returned

    :type mo_burst_info: dict
    :param mo_burst_info: The dictionary element represents information on the MOType.
        The Dictionary requires the following elements:
        {"notification_percentage_rate": 0.45,
         "node_type": "ERBS",
         "mo_type_name": "EUtranCellFDD",
         "mo_path": "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=%NENAME%-1",
         "parent_mo_names": None,
         "mo_attribute": "userLabel",
         "mo_values": ["abc", "def", "ghi"]}
         NOTE: the 'mo_path' option takes precedence over the 'parent_mo_name' option, so if one is specified the other
           should be None. THe 'mo_path' option specifies the full MO path to the MO which would be common across all
           the nodes, whereas the 'parent_mo_names' is used where the path may not be common across all the nodes and we
           need to query the nodes to find the exact path
    :type nodes: list of enm_node.ENMNode objects
    :param nodes: A list of the nodes that the MOs are located on
    :type required_rate: float
    :param required_rate: The overall avc burst notification rate that the MOs are attempting to achieve.

    :rtype: list
    :return: A list of MOType objects
    """

    # Calculate the rate of the burst
    total_mo_rate = round(required_rate * mo_burst_info["notification_percentage_rate"], 3)

    # Set the required rate on the MO Types
    mo_types = determine_mo_types_required(mo_burst_info, nodes, for_existing_mo=True)
    for mo_type in mo_types:
        rate_per_burst = (total_mo_rate / len(nodes)) * len(mo_type.nodes)
        log.logger.debug(
            "MO TYPE: type: {type}, MO path: {mo_path}, # nodes: {num_nodes}, burst rate: {burst_rate}".format(
                type=mo_type.type, mo_path=mo_type.mo_path, num_nodes=len(mo_type.nodes),
                burst_rate=rate_per_burst))

        mo_type.add_avc_burst_info(notification_rate=rate_per_burst,
                                   mo_attribute=mo_burst_info["mo_attribute"],
                                   mo_values=mo_burst_info["mo_values"])

    return mo_types


class MOTree(object):

    DUMP_MO_TREE_BY_TYPE_CMD = 'dumpmotree:motypes="{mo_types}";'
    DUMP_MO_TREE_CMD = 'dumpmotree:mo_id="{mo_id}"'
    DUMP_MO_TREE_VALIDATION = 'Number of MOs:'

    def __init__(self, node):
        self.node = node
        self.mo_tree = None

    def _validate_response(self, response_output):
        for line in response_output.split('\n')[-4:]:
            if self.DUMP_MO_TREE_VALIDATION in line:
                return True

        return False

    def set_mo_tree_for_specific_types(self, mo_types):
        """
        Obtains the MO tree for a node which will only contain the types specified and sets it in the self.mo_tree
        attribute. Note: Mo path will only include those mo types specified, so all parent mo types should be included
        to get a full mo_path

        :param mo_types: A list of MO Types to include in the mo tree
        :type mo_types: list of strings

        :raises FailedNetsimOperation: raised if the netsim operation fails
        """

        netsim_cmd = self.DUMP_MO_TREE_BY_TYPE_CMD.format(mo_types=','.join(mo_types))
        response = netsim_executor.run_cmd(netsim_cmd, self.node.netsim, self.node.simulation, [self.node.node_name],
                                           keep_connection_open=False, log_cmd=False)
        if response.rc == 0 and self._validate_response(response.stdout):
            self.mo_tree = self._parse_dump_tree_response(response.stdout)
        else:
            raise FailedNetsimOperation("NetsimOperation failed '{0}' for the following node {1}"
                                        "".format(netsim_cmd[:30], self.node.node_name), nodes=[self.node],
                                        command=netsim_cmd)

    def set_mo_tree_from_specific_point(self, from_mo_path):
        """
        Obtains the MO tree of a node from a specific point in the mo tree and sets it in the 'mo_tree' attribute. The
        tree will include the mo specified and all its descendants

        :param from_mo_path: The mo path of the MO in the nodes MO tree to get the mo tree from.
        :type from_mo_path: str
        """
        netsim_cmd = self.DUMP_MO_TREE_CMD.format(mo_id=from_mo_path)
        response = netsim_executor.run_cmd(netsim_cmd, self.node.netsim, self.node.simulation, [self.node.node_name],
                                           keep_connection_open=False)

        self.mo_tree = self._parse_dump_tree_response(response.stdout)

    @staticmethod
    def _parse_dump_tree_response(response_output):
        """
        Converts the netsim string response into a dictionary of MO types and their subtypes

        :param response_output: The output from a netsim dumpmotree command to convert into a dictionary
        :type response_output: str

        :raises RuntimeError: raised if mo is undefined

        :return: A dictionary of MO types and their subtypes
        :rtype: dict
        """

        def _build_mo_dict(response_list):
            all_mos = {}
            current_level = 1
            bread_crumbs = []

            for line in response_list:
                def _get_dictionary(bread_crumbs, in_dict):
                    level_dict = in_dict
                    for mo in bread_crumbs:
                        level_dict = level_dict[mo]

                    return level_dict

                if not line.startswith('Number of') and line:
                    level = line.replace('   ', ' ').count(' ')
                    mo_id = line.strip()

                    if level == current_level:
                        bread_crumbs = bread_crumbs[:-1]
                        level_dict = _get_dictionary(bread_crumbs, all_mos)
                        level_dict[mo_id] = {}
                        bread_crumbs.append(mo_id)
                    elif level > current_level:
                        level_dict = _get_dictionary(bread_crumbs, all_mos)

                        level_dict[mo_id] = {}
                        bread_crumbs.append(mo_id)
                        current_level = level
                    else:
                        # level is higher so we must figure out how to update our bread crumbs
                        bread_crumbs = bread_crumbs[:level - 1]
                        level_dict = _get_dictionary(bread_crumbs, all_mos)

                        level_dict[mo_id] = {}
                        bread_crumbs.append(mo_id)
                        current_level = level
                elif line:
                    key, value = line.split(":")
                    mo_dict[key] = value.strip()

            return all_mos

        mo_dict = {}
        # split on new lines and remove the command line
        response_list = response_output.split('\n')[1:]
        mo_name = response_list[0]

        if 'MO not defined' in mo_name:
            raise RuntimeError("MO '{0}' is not defined on the specified node".format(mo_name.split(':')[1]))
        response_list = response_list[1:]
        mo_dict[mo_name] = _build_mo_dict(response_list)

        return mo_dict

    def get_mo_path(self, mo_tree, mo_type_to_find, name=''):
        """
        Finds a MO in the specified MO tree and returns its path

        :param mo_tree: A dictionary of MOs and their descendants
        :type mo_tree: dict
        :param mo_type_to_find: The MO type to find in the mo tree
        :type mo_type_to_find: string
        :param name: The name of the MO type to locate
        :type name: string

        :return: None if not found or the path to the MO type specified as a string
        :rtype: str
        """
        # Netsim temporary relations start with E
        ignored_patterns = ["EUtranFreqRelation=E", "CMSYNC", "CELLMGT"]
        for mo_type, value in mo_tree.items():
            if (any([_ in value for _ in ignored_patterns]) or
                    any([_ in mo_type for _ in ignored_patterns])):
                continue
            if "{0}={1}".format(mo_type_to_find, name) in mo_type:
                return mo_type
            elif isinstance(value, dict):
                path = self.get_mo_path(value, mo_type_to_find, name)
                if path:
                    return "{0},{1}".format(mo_type, path)

        return None
