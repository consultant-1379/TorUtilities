import math
import random
import time

from requests.exceptions import HTTPError

from enmutils.lib import log
from enmutils.lib.exceptions import (NoOuputFromScriptEngineResponseError, ScriptEngineResponseValidationError,
                                     EnvironError)
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.load_mgr import get_active_profile_names
from enmutils_int.lib.nhm import CREATED_BY_DEFAULT
from enmutils_int.lib.nhm import NhmKpi
from enmutils_int.lib.nhm import get_nhm_nodes, check_is_kpi_usable_and_assign_to_node_type
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class Nhm0102(GenericFlow):
    """
    Class to run the flow for NHM_01 and NHM_02 profiles
    """

    def __init__(self, *args, **kwargs):

        self.supported_node_types = []
        self.reminder = 0
        self.FLAG = ""
        super(Nhm0102, self).__init__(*args, **kwargs)

    def _clean_system_nhm_01(self, user):
        """
        Deletes Node Level KPIs created by NHM_01

        :param user: user to carry out requests
        :type user: enmutils.lib.enm_user.User
        """

        try:
            NhmKpi.remove_kpis_by_pattern_new(user=user, pattern="NHM_SETUP")
        except Exception as e:
            self.add_error_as_exception(e)
        log.logger.debug("KPI cleaned down system. Removed node level KPIs created by profile")

    def _clean_system_nhm_02(self, user):
        """
        Deactivates default Cell Level KPIs and removes nodes from NHM_02 KPIs

        :param user: user to carry out requests
        :type user: enmutils.lib.enm_user.User
        """

        try:
            NhmKpi.clean_down_system_kpis(user)
        except Exception as e:
            self.add_error_as_exception(e)
        log.logger.debug("KPI cleaned down system. Deactivated default cell level KPIs")

    @staticmethod
    def check_output_for_num_cells(output):
        """
        Check the script engine output for the number of cell instances

        :param output: output from the script engine
        :type output: list
        :raises ScriptEngineResponseValidationError: if no instance(s) found in script engine output
        :return: number of cells
        :rtype: int
        """

        num_cells_per_batch = [0]

        if not any('instance(s)' in output_string for output_string in output):
            raise ScriptEngineResponseValidationError(
                "Number of cell instances could not be found - no 'instance(s)' found in output.", response=output)

        for output_string in output:
            if 'instance(s)' in output_string:
                num_cells_per_batch = [int(string) for string in output_string.split() if string.isdigit()]

        return sum(num_cells_per_batch)

    def get_profile_node_types(self):
        """
        Get list of nodes used by the profile
        :return: list of node type names
        :rtype: list
        """
        return self.NUM_NODES.keys() if hasattr(self, "NUM_NODES") else self.SUPPORTED_NODE_TYPES

    def get_nodes_of_primary_type(self, node_type, nodes_verified_on_enm):
        """
        Get list of nodes of given type from nodes verified on ENM
        :param node_type: node type
        :type node_type: str
        :param nodes_verified_on_enm: nodes to be used
        :type nodes_verified_on_enm: list
        :return: list of node objects
        :rtype: list
        """
        return [node for node in nodes_verified_on_enm if node.primary_type == node_type]

    def get_max_number_of_node_level_kpis(self, nodes_verified_on_enm):
        """
        Get maximum number of Node Level KPI instances
        :param nodes_verified_on_enm: nodes to be used
        :type nodes_verified_on_enm: list
        :return: Returns maximum number of Node level KPI instances that can be generated:
        :rtype: float
        """
        return (len([node for node in nodes_verified_on_enm if node.primary_type
                     not in self.UNSUPPORTED_TYPES_NODE_LEVEL_KPI]) * self.NUM_KPIS_01)

    def get_node_cell_count_dict(self, user, nodes_verified_on_enm):
        """
        Get dictionary with total count of usable cells for a given node type
        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param nodes_verified_on_enm: nodes to be used
        :type nodes_verified_on_enm: list
        :return: dictionary with cell count per node type
        :rtype: dict
        """
        node_cell_count_dict = {}
        for node_type in self.get_profile_node_types():
            try:
                nodes = self.get_nodes_of_primary_type(node_type, nodes_verified_on_enm)
                node_cell_count_dict[node_type] = {'number_of_nodes': len(nodes), 'number_of_cells': 0}
                node_cell_count = self.get_number_of_cells_for_given_node_type(user, node_type, nodes)
                node_cell_count_dict.update({node_type: {'number_of_nodes': node_cell_count[0],
                                                         'number_of_cells': node_cell_count[1]}})
            except Exception as e:
                self.add_error_as_exception(EnvironError("Could not get number of cells for {0}."
                                                         "Profile will not set KPIs. msg: {1}".format(node_type,
                                                                                                      e.message)))
                continue
        return node_cell_count_dict

    def get_number_of_cells_for_given_node_type(self, user, node_type, nodes):
        """
        Gets the number of cells for required nodes
        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param node_type: node type
        :type node_type: str
        :param nodes: nodes to be used
        :type nodes: list
        :raises NoOuputFromScriptEngineResponseError:
        :return: number of nodes, total number of cells
        :rtype: tuple
        """
        number_of_nodes = len(nodes)
        mo_names = ";".join(mo_name for mo_name in self.REPORTING_OBJECT_02[node_type])
        start = 0
        total_cells = 0
        batch_size = 100
        total_num_to_search = number_of_nodes

        while total_num_to_search > 0:
            if batch_size > total_num_to_search:
                batch_size = total_num_to_search
            batch_nodes = nodes[start:start + batch_size]

            nodes_identifier = ';'.join(node.node_id for node in batch_nodes)
            response = user.enm_execute('cmedit get {nodes_identifier} {mo_name} -cn'
                                        .format(nodes_identifier=nodes_identifier, mo_name=mo_names))
            output = response.get_output()

            if not output:
                raise NoOuputFromScriptEngineResponseError('No output received from script engine', response=response)
            else:
                num_cells_per_batch = self.check_output_for_num_cells(output)
                total_cells += num_cells_per_batch
                start += batch_size
                total_num_to_search -= batch_size

        return number_of_nodes, total_cells

    def get_usable_kpis(self, user):
        """
        Get dictionary with the predefined KPIs that can be used for a given node type
        :param user: user to carry out requests
        :type user: enm_user_2.User
        :return: dictionary with the predefined KPIs that can be used for a given node type
        :rtype: dict
        """
        default_kpi_names = self.get_default_kpis(user)

        # Create dictionary with supported node types as keys
        usable_kpis = {str(node_type): [] for node_type in self.supported_node_types}

        # check is KPI usable
        for kpi_name in default_kpi_names:
            try:
                check_is_kpi_usable_and_assign_to_node_type(user, kpi_name, usable_kpis, self.supported_node_types,
                                                            self.REPORTING_OBJECT_02, self.UNSUPPORTED_KPIS)
            except HTTPError:
                self.add_error_as_exception(EnvironmentError("KPI '{}' not checked skipping to the next one."
                                                             .format(kpi_name)))

        return usable_kpis

    def calculate_the_total_number_of_kpi_instances_avaiable(self, node_level_total, number_of_cells_per_node_type,
                                                             usable_kpis):
        """
        Get dictionary with the predefined KPIs that can be used for a given node type
        :param node_level_total: Total number of KPI instance that will be created on node level
        :type node_level_total: float
        :param number_of_cells_per_node_type: dictionary with total cell count for a given node type
        :type number_of_cells_per_node_type: dict
        :param usable_kpis: Dictionary with predefined KPIs that can be created for a node type
        :type usable_kpis: dict
        :raises EnvironError: If no cells found
        :return: Max number of KPI instances that can be created using predefined KPIs and node level KPIs
        :rtype: float
        """

        log.logger.info('Number of instances generated form Node Level KPIs: {}'.format(node_level_total))
        total_number = node_level_total
        total_number_of_cells = 0
        for node_type in usable_kpis:
            number_of_usable_kpis = len(usable_kpis[node_type])
            number_of_nodes = number_of_cells_per_node_type[node_type]['number_of_nodes']
            total_number_of_cells_per_type = number_of_cells_per_node_type[node_type]['number_of_cells']
            total_number_per_type = total_number_of_cells_per_type * number_of_usable_kpis
            log.logger.info('Number of {} nodes: {}, with total of: {} cells available'.
                            format(node_type,
                                   number_of_nodes,
                                   total_number_of_cells_per_type))
            log.logger.info('Number of instances that can be generated from predefined cell level KPIs: {} cells on '
                            '{} nodes * {} default KPIs = {} KPI Instances'.format(total_number_of_cells_per_type,
                                                                                   node_type, number_of_usable_kpis,
                                                                                   total_number_per_type))
            total_number_of_cells += total_number_of_cells_per_type
            total_number += total_number_per_type

        if not total_number_of_cells:
            raise EnvironError("No cells found to create the cell level kpis,cannot execute the profile flow")
        log.logger.info('Total number of instances that can be created form predefined and node level KPIS: {}'
                        .format(total_number))

        return total_number

    def get_number_of_custom_kpis_to_create(self, number_of_available_instances, node_cell_dict, instances_required):
        """
        Get dictionary with custom KPIs to create in order to achieve required number of KPI instances
        :param number_of_available_instances: Max number of KPI instances that can be created using predefined
        KPIs and node level KPIs
        :type number_of_available_instances: float
        :param node_cell_dict: dictionary with total cell count for a given node type
        :type node_cell_dict: dict
        :param instances_required: Number of KPI instances required to be produced as per load
        :type instances_required: float
        :return: Dictionary with custom KPIs to create in order to achieve required number of KPI instances
        :rtype: dict
        """
        custom_kpis_to_create = {node_type: 0 for node_type in self.SUPPORTED_TYPES_CUSTOM_CELL_LEVEL_KPI}
        total = 0
        supported_node_types = self.SUPPORTED_TYPES_CUSTOM_CELL_LEVEL_KPI
        number_of_instances_needed = instances_required - number_of_available_instances
        log.logger.info('Required number of KPI instances ({0}) is greater than number of instance that can be '
                        'created using predefined and node level KPIs'.format(int(instances_required)))

        while number_of_instances_needed > 0:
            log.logger.info('Number of instances needed: {}'.format(number_of_instances_needed))
            node_type = random.choice(supported_node_types)
            number_of_instances = node_cell_dict[node_type]['number_of_cells']
            if number_of_instances:
                number_of_nodes = node_cell_dict[node_type]['number_of_nodes']
                log.logger.info('Adding one custom KPI for {0} X {1} nodes resulting in {2} extra instances'
                                .format(number_of_nodes, node_type, int(number_of_instances)))
                number_of_instances_needed -= number_of_instances
                custom_kpis_to_create[node_type] += 1
                if node_type == 'ERBS':
                    num_cells_radio_node = node_cell_dict['RadioNode']['number_of_cells']
                    number_of_instances_needed -= num_cells_radio_node
                    log.logger.info('Adding RadioNodes to the new KPI resulting in {} extra instances '
                                    .format(num_cells_radio_node))
                elif node_type == 'RadioNode':
                    num_cells_erbs = node_cell_dict['ERBS']['number_of_cells']
                    number_of_instances_needed -= num_cells_erbs
                    log.logger.info('Adding ERBS nodes to the new KPI resulting in {} extra instances '
                                    .format(num_cells_erbs))
                total += 1
                if total >= self.MAX_NUMBER_OF_CUSTOM_KPIS:
                    log.logger.info('Max number of custom cell level KPIs ({0}) has been excceded !'
                                    .format(self.MAX_NUMBER_OF_CUSTOM_KPIS))
                    return custom_kpis_to_create
            else:
                log.logger.info("No cell found on {} nodes skipping to another type.".format(node_type))

        return custom_kpis_to_create

    def reduce_number_of_kpis(self, usable_kpis, number_of_kpis_not_needed, number_of_nodes_and_cells_per_node_type):
        """
        Take out some of the usable KPIs from the dictonary of predefined KPIs to create in order to reduce number of
        instances to mach the required number
        :param usable_kpis: Dictionary with predefined KPIs that can be created for a node type
        :type usable_kpis: dict
        :param number_of_kpis_not_needed: Total of KPI instances to be reduced
        :type number_of_kpis_not_needed: float
        :param number_of_nodes_and_cells_per_node_type: Number of nodes of given type and total number of cell it
        :type number_of_nodes_and_cells_per_node_type: dict
        :return: Dictionary with custom KPIs to create in order to achieve required number of KPI instances
        :rtype: dict
        """

        while number_of_kpis_not_needed > 0:
            log.logger.info('Number of KPI instances that can be created using predefined KPIs excedes required '
                            'number by: {0}'.format(number_of_kpis_not_needed))
            ne_type = random.choice(usable_kpis.keys())
            if ne_type not in usable_kpis:
                continue
            kpi_to_remove = random.choice(usable_kpis[ne_type])
            for ne_type in self.supported_node_types:
                if number_of_kpis_not_needed > 0 and kpi_to_remove in usable_kpis[ne_type]:
                    number_of_instances_removed = number_of_nodes_and_cells_per_node_type[ne_type][
                        'number_of_cells']
                    number_of_kpis_not_needed -= number_of_instances_removed
                    if number_of_kpis_not_needed < 0:
                        return usable_kpis
                    usable_kpis[ne_type].remove(kpi_to_remove)
                    self.reminder = number_of_kpis_not_needed
                    log.logger.info('Removing the "{0}" for node type: {1} from the list of KPIs to use'
                                    .format(kpi_to_remove, ne_type))

    def get_default_kpis(self, user):
        """
        Get the list of KPIs that are CREATED_BY_DEFAULT

        :param user: user to carry out requests
        :type user: enm_user_2.User
        :return: list of default KPIs
        :rtype: list
        """

        default_kpis = []

        try:
            default_kpis = [kpi_name for kpi_name in NhmKpi.get_all_kpi_names(user) if
                            NhmKpi.get_kpis_created_by(user, kpi_name=kpi_name) == CREATED_BY_DEFAULT]
        except Exception as e:
            self.add_error_as_exception(e)

        return default_kpis

    def create_and_activate_user_created_cell_level_kpi(self, kpi_name, user, nodes, ne_types, counters,
                                                        reporting_objects):
        """
        Create and activate single custom cell level KPIs
        :param kpi_name: Name
        :type kpi_name: str
        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param nodes: list of enm_node.Node objects
        :type nodes: list
        :param ne_types: node types
        :type ne_types: list
        :param counters: list of counters to use for the KPI
        :type counters: list
        :param reporting_objects: reporting object used by the KPI
        :type reporting_objects: str
        """
        kpi = NhmKpi(user=user, name=kpi_name, reporting_objects=reporting_objects, nodes=nodes,
                     node_types=ne_types, active=False,
                     counters=counters)
        self.track_kpi_creation(kpi.create(), user, kpi_name)
        self.teardown_list.append(NhmKpi(user=user, name=kpi_name))
        kpi.activate()

    def create_and_activate_cell_level_kpi(self, user, nodes, node_type_kpi_dict):
        """
        Create and activate predefined cell level KPIs
        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param nodes: nodes to be used
        :type nodes: list
        :param node_type_kpi_dict: Dictionary with predefined KPIs that can be created for a node type
        :type node_type_kpi_dict: dict
        """
        for node_type in node_type_kpi_dict.keys():
            po_ids = [node.poid for node in nodes if node.primary_type == node_type]
            if po_ids:
                usable_kpis = node_type_kpi_dict[node_type]
                for kpi_name in usable_kpis:
                    default_kpi = NhmKpi(name=kpi_name, user=user, created_by=CREATED_BY_DEFAULT)
                    default_kpi.update(add_nodes=po_ids)
                    self.teardown_list.append(picklable_boundmethod(default_kpi._teardown))
                    default_kpi.activate()

    def set_node_types_for_custom_cell_kpis(self, node_type, nodes):
        """
        Group the nodes if they are of similiar type
        :param node_type: ne type
        :type node_type: str
        :param nodes: list of node objects
        :type nodes: list
        :return: nodes list and type of nodes in the list
        :rtype: tuple
        """
        ran_nodes = ['ERBS', 'RadioNode']
        if node_type in ran_nodes:
            nodes_list = [node for node in nodes if node.primary_type == 'ERBS' or
                          node.primary_type == 'RadioNode']
            node_types = ran_nodes
        else:
            nodes_list = [node for node in nodes if node.primary_type == node_type]
            node_types = [node_type]

        return nodes_list, node_types

    def create_and_activate_node_level_kpi(self, kpi_name, user, nodes, ne_types, counters, reporting_object):
        """
        Create and activate a node level KPI

        :param kpi_name: name of KPI to create
        :type kpi_name: str
        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param nodes: list of enm_node.Node objects
        :type nodes: list
        :param ne_types: node types
        :type ne_types: list
        :param counters: list of counters to use for the KPI
        :type counters: list
        :param reporting_object: reporting object used by the KPI
        :type reporting_object: str
        """
        kpi = NhmKpi(user=user, name=kpi_name, reporting_objects=[reporting_object], nodes=nodes,
                     node_types=ne_types, active=False,
                     counters=random.sample(counters, random.randint(2, len(counters))))
        self.track_kpi_creation(kpi.create(), user, kpi_name)
        self.teardown_list.append(NhmKpi(user=user, name=kpi_name))
        kpi.activate()

    def execute_flow_nhm_01(self, user, nodes):
        """
        Runs the flow of NHM_01 profile which creates Node Level KPIs created by the NHM_01 user

        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param nodes: nodes to be used
        :type nodes: list
        """

        counters = []
        nodes = [node for node in nodes if node.primary_type not in self.UNSUPPORTED_TYPES_NODE_LEVEL_KPI]
        reporting_object = self.REPORTING_OBJECT_01["ERBS"]
        if nodes:
            ne_types = list(set(node.primary_type for node in nodes))

            for ne_type in ne_types:
                for counter in NhmKpi.get_counters_specified_by_nhm(self.REPORTING_OBJECT_01[ne_type], ne_type):
                    counters.append(counter)

            for i in xrange(self.NUM_KPIS_01):
                try:
                    kpi_name = "{0}_KPI_{1}".format(self.identifier, i)
                    self.create_and_activate_node_level_kpi(kpi_name, user, nodes, ne_types, counters, reporting_object)
                except Exception as e:
                    self.add_error_as_exception(e)

    def execute_flow_nhm_02(self, user, nodes, number_of_custom_kpis, usable_kpis):
        """
        Runs the flow of NHM_02 profile which activates Cell Level KPIs which are created by Ericsson
        (CREATED_BY_DEFAULT)

        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param nodes: list of enm_node.Node objects
        :type nodes: list
        :param number_of_custom_kpis: Dict with number of custom kpis to create for a given node type
        :type number_of_custom_kpis: dict
        :param usable_kpis: Dict with names of predefined KPIs to activate for a given node type
        :type usable_kpis: dict
        """
        number_created = 0
        if number_of_custom_kpis:
            for node_type in number_of_custom_kpis.keys():
                reporting_objects = self.REPORTING_OBJECT_02[node_type]
                counters = NhmKpi.get_counters_specified_by_nhm(reporting_objects, node_type)
                nodes_list, node_types = self.set_node_types_for_custom_cell_kpis(node_type, nodes)
                for i in xrange(number_of_custom_kpis[node_type]):
                    try:
                        kpi_name = "{0}_KPI_{1}".format(self.identifier, i)
                        self.create_and_activate_user_created_cell_level_kpi(kpi_name, user, nodes_list,
                                                                             node_types,
                                                                             counters,
                                                                             reporting_objects=reporting_objects)
                        number_created += 1
                    except Exception as e:
                        self.add_error_as_exception(e)
        log.logger.info('Sucessfuly created and activated {} custom cell level KPIs.'.format(number_created))
        try:
            self.create_and_activate_cell_level_kpi(user, nodes, usable_kpis)  # Create and activate default cell level KPIs
        except Exception as e:
            self.add_error_as_exception(e)

    def log_calculation(self, total_available, kpi_overhead=None, reminder=None, custom_cell_level=None,
                        cells_per_node=None):
        if reminder:
            log.logger.info('Expected total number of KPI instances: {}'
                            .format(int(total_available - kpi_overhead + reminder)))
        elif custom_cell_level:
            total = total_available
            for node_type in custom_cell_level:
                if node_type in ['ERBS', 'RadioNode']:
                    total += custom_cell_level[node_type] * (cells_per_node['RadioNode']['number_of_cells'] +
                                                             cells_per_node['ERBS']['number_of_cells'])
                else:
                    total += custom_cell_level[node_type] * cells_per_node[node_type]['number_of_cells']
            log.logger.info('Expected total number of KPI instances: {}'.format(total))

    def calculate_expected_kpi_instances(self, user, nodes_verified_on_enm, number_of_instances_required):
        """
        Calculates the expected number of KPI instances to be generated by the profile
        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param nodes_verified_on_enm: list of enm_node.Node objects
        :type nodes_verified_on_enm: list
        :param number_of_instances_required: Number of KPI instances required to be produced as per load
        :type number_of_instances_required: float
        :return: Tuple containing number of cell_level_kpis to create, usable KPIs
        :rtype: tuple
        """
        number_of_cell_level_kpis_to_create = None
        number_of_nodes_and_cells_per_node_type = self.get_node_cell_count_dict(user, nodes_verified_on_enm)
        max_number_of_node_level_kpis = self.get_max_number_of_node_level_kpis(nodes_verified_on_enm)
        usable_kpis = self.get_usable_kpis(user)

        total_number_of_kpi_instances_available = (self.calculate_the_total_number_of_kpi_instances_avaiable
                                                   (max_number_of_node_level_kpis,
                                                    number_of_nodes_and_cells_per_node_type, usable_kpis))
        if total_number_of_kpi_instances_available >= number_of_instances_required:
            log.logger.info("Removing KPIs as number of instances that can be created from the nodes assigned "
                            "to the profile excedes the required number of KPI instances")
            kpi_overhead = total_number_of_kpi_instances_available - number_of_instances_required
            usable_kpis = self.reduce_number_of_kpis(usable_kpis, kpi_overhead,
                                                     number_of_nodes_and_cells_per_node_type)
            self.log_calculation(total_number_of_kpi_instances_available, kpi_overhead=kpi_overhead,
                                 reminder=self.reminder)
        else:
            number_of_cell_level_kpis_to_create = (self.get_number_of_custom_kpis_to_create
                                                   (total_number_of_kpi_instances_available,
                                                    number_of_nodes_and_cells_per_node_type,
                                                    number_of_instances_required))
            self.log_calculation(total_number_of_kpi_instances_available,
                                 custom_cell_level=number_of_cell_level_kpis_to_create,
                                 cells_per_node=number_of_nodes_and_cells_per_node_type)
        return number_of_cell_level_kpis_to_create, usable_kpis

    def get_number_of_router_kpis_to_create(self, number_of_routers, num_reporting_objects=4):
        """
        Returns the number of KPIs to create in order to generate required load
        5 in the equations represents number of reporting objects on router nodes

        :param number_of_routers: Number of routers in the Network
        :type number_of_routers: int
        :param num_reporting_objects: Number of reporting objects to be used
        :type num_reporting_objects: int

        :return: Number of KPIs to create
        :rtype: int
        """
        number_of_kpis = int(math.ceil(self.NUMBER_OF_INSTANCES_REQUIRED / float(
            number_of_routers * num_reporting_objects)))
        if number_of_kpis >= self.MAX_NUMBER_OF_CUSTOM_KPIS:
            log.logger.info("Number of KPIs to generate exceeds the limit of: {kpi}. Creating {kpi} KPIs"
                            .format(kpi=self.MAX_NUMBER_OF_CUSTOM_KPIS))
        return number_of_kpis if number_of_kpis <= self.MAX_NUMBER_OF_CUSTOM_KPIS else self.MAX_NUMBER_OF_CUSTOM_KPIS

    def create_router_kpis(self, user, nodes):
        """
        Creates the Router KPIs
        :param user: User which will perform creation
        :type user: enm_user_2.User
        :param nodes: nodes to be used
        :type nodes: list
        """
        nodes = [node for node in nodes if node.primary_type in self.supported_node_types]
        number_of_routers = len(nodes)
        reporting_objects = self.REPORTING_OBJECT
        number_of_kpis = self.get_number_of_router_kpis_to_create(number_of_routers, len(reporting_objects))
        counters = NhmKpi.get_counters_specified_by_nhm(reporting_object=reporting_objects,
                                                        ne_type=self.supported_node_types[0])

        for i in xrange(number_of_kpis):
            try:
                kpi_name = "{0}_KPI_{1}".format(self.identifier, i)
                kpi = NhmKpi(user=user, name=kpi_name, nodes=nodes, reporting_objects=reporting_objects,
                             counters=counters, node_types=self.supported_node_types, active=False)
                self.teardown_list.append(NhmKpi(user=user, name=kpi_name))
                self.track_kpi_creation(kpi.create(), user, kpi_name)
                kpi.activate()
            except Exception as e:
                self.add_error_as_exception(e)

        log.logger.info("Successfully created {} KPIs. {} Router nodes added. Expected load: {} KPI instances"
                        .format(number_of_kpis, number_of_routers, (number_of_routers * len(self.REPORTING_OBJECT) *
                                                                    number_of_kpis)))

    @staticmethod
    def track_kpi_creation(response, user, kpi_name):
        """
        Function to query KPI application for the create status

        :param response: HTTPResponse object returned by the create command
        :type response: `HTTPResponse`
        :param user: User who will query create status of KPI
        :type user: enm_user_2.User
        :param kpi_name: Name of the KPI
        :type kpi_name: str
        """
        retry_count = 0
        while retry_count < 3:
            retry_count += 1
            try:
                tracker_id = response.__dict__.get('_content')
                response = user.get('/kpi-specification-rest-api-war/kpi/status/{0}'.format(tracker_id))
                if response.status_code == 200:
                    break
            except Exception as e:
                log.logger.debug("KPI create status request failed, error encountered: {0}".format(str(e)))
            log.logger.debug("Sleeping for 30 seconds before checking create status of the KPI:{0}".format(kpi_name))
            time.sleep(30)

    def execute_flow(self):
        """
        Executes the flow of NHM_01 and NHM_02 setup test cases
        """
        number_of_instances_required = (self.NUMBER_OF_INSTANCES_REQUIRED - self.INSTANCES_GENERATED_BY_NPA_01 if
                                        "NPA_01" in get_active_profile_names() else self.NUMBER_OF_INSTANCES_REQUIRED)
        self.state = "RUNNING"
        user = self.create_profile_users(1, self.USER_ROLES)[0]
        self.supported_node_types = self.get_profile_node_types()
        allocated_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid", "primary_type"])
        nodes_verified_on_enm = get_nhm_nodes(self, user, allocated_nodes)
        self._clean_system_nhm_01(user)
        self._clean_system_nhm_02(user)

        if nodes_verified_on_enm and not self.TRANSPORT_SETUP:
            try:
                self.execute_flow_nhm_01(user, nodes_verified_on_enm)
                number_of_cell_level_kpis_to_create, usable_kpis = (self.calculate_expected_kpi_instances(user,
                                                                                                          nodes_verified_on_enm,
                                                                                                          number_of_instances_required))
                self.execute_flow_nhm_02(user, nodes_verified_on_enm, number_of_cell_level_kpis_to_create, usable_kpis)
            except Exception as e:
                self.add_error_as_exception(e)
            self.FLAG = 'COMPLETED'
        elif nodes_verified_on_enm:
            # Transport setup Flow
            self.create_multi_primary_type_router_nodes(user, nodes_verified_on_enm)
            self.FLAG = 'COMPLETED'
        else:
            log.logger.error('No nodes verified on ENM. Setup failed to complete. NHM profiles will not execute!!!')
            self.add_error_as_exception(EnvironError("No nodes verified on ENM. Setup failed to complete. "
                                                     "NHM profiles will not execute!"))

    def create_multi_primary_type_router_nodes(self, user, nodes_on_enm):
        """
        Create Transport KPIs based upon the primary type of the node supplied

        :param user: ENM user who will create the KPI
        :type user: `enm_user_2.User`
        :param nodes_on_enm: List of nodes created on ENM
        :type nodes_on_enm: list
        """
        node_groups = {primary_type: [] for primary_type in {node.primary_type for node in nodes_on_enm}}
        for primary_type in node_groups.keys():
            node_groups[primary_type].extend(
                [node for node in nodes_on_enm if node.primary_type == primary_type])
        for primary_type, nodes in node_groups.items():
            self.supported_node_types = [primary_type]
            self.create_router_kpis(user, nodes)
