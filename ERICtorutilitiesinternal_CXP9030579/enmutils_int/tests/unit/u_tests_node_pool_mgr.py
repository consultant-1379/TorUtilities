#!/usr/bin/env python
import unittest2
from mock import patch, PropertyMock, Mock, call
from parameterizedtestcase import ParameterizedTestCase


from enmutils.lib.enm_node import NODE_CLASS_MAP as enm_node__node_class_map, RadioNode as radionode, BaseNode
from enmutils.lib.exceptions import (NoNodesAvailable, RemoveProfileFromNodeError, TimeOutError, AddProfileToNodeError,
                                     NoOuputFromScriptEngineResponseError, ScriptEngineResponseValidationError)
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.load_node import NODE_CLASS_MAP, ERBSNode, ERBSLoadNode
from enmutils_int.lib.node_pool_mgr import NodesFilter, handle_one_total_node_and_multiple_support_types
from enmutils_int.lib.profile import Profile, CMImportProfile
from testslib import unit_test_utils
from testslib.unit_test_utils import get_profile, get_nodes, TestProfile, generate_configurable_ip


@patch('enmutils.lib.enm_user_2.User.open_session')
@patch('enmutils_int.lib.enm_user.get_workload_admin_user')
class NodeMgrUnitTests(ParameterizedTestCase):

    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.update_node_ids')
    def setUp(self, _):  # pylint: disable=arguments-differ
        unit_test_utils.setup()
        self.pool = node_pool_mgr.ProfilePool()
        Profile.NAME = "TEST_PROFILE"

    def tearDown(self):
        unit_test_utils.tear_down()

    @staticmethod
    def _get_errored_nodes(error_dict):
        not_added = []
        for errored in error_dict.values():
            if errored:
                not_added.extend(errored)
        return not_added

    # exchange_nodes ###################################################################################################

    @patch("enmutils_int.lib.node_pool_mgr.initialize_cached_nodes_list")
    @patch('enmutils_int.lib.profile.Profile.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.process.get_current_rss_memory_for_current_process')
    @patch('enmutils_int.lib.node_pool_mgr.exchange_nodes_allocated_to_profile')
    @patch('enmutils_int.lib.node_pool_mgr.multitasking.create_single_process_and_execute_task')
    def test_exchange_nodes__successfully_exchanges_nodes(
            self, mock_create_single_process_and_execute_task, mock_exchange_nodes_allocated_to_profile, *_):
        profile = Profile()
        self.assertEqual(None, node_pool_mgr.exchange_nodes(profile))
        mock_create_single_process_and_execute_task.assert_called_once_with(
            mock_exchange_nodes_allocated_to_profile, args=(profile.NAME, ))

    # allocate_nodes ###################################################################################################

    @patch('enmutils_int.lib.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.node_pool_mgr.get_pool')
    @patch('enmutils.lib.log.logger.debug')
    def test_allocate_nodes__successfully_allocates_nodes(self, mock_debug_log, mock_get_pool, *_):
        profile = Profile()
        mock_allocate_nodes = mock_get_pool.return_value.allocate_nodes
        self.assertEqual(None, node_pool_mgr.allocate_nodes(profile))
        self.assertEqual(2, mock_debug_log.call_count)
        mock_allocate_nodes.assert_called_once_with(profile=profile, nodes=None)

    # get_nodes_with_required_num_of_mos ###############################################################################

    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.allocate_batch_by_mo_profile_using_num_nodes')
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.node_dict', new_callable=PropertyMock)
    def test_allocate_batch_by_mo_num_nodes(self, mock_node_dict, mock_debug, mock_allocate_nodes_with_mos, *_):
        profile = Mock()
        profile.MO_VALUES = {"UtranCell": 1}
        profile.SUPPORTED_NODE_TYPES = ["ERBS", "RadioNode"]
        mock_node_dict.return_value = {"ERBS": [Mock()] * 5, "RadioNode": [Mock()]}
        self.pool.allocate_batch_by_mo(profile)
        self.assertEqual(1, mock_debug.call_count)
        self.assertEqual(1, mock_allocate_nodes_with_mos.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.allocate_nodes_with_mos')
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.node_dict', new_callable=PropertyMock)
    def test_allocate_batch_by_mo(self, mock_node_dict, mock_debug, mock_allocate_nodes_with_mos, *_):
        profile = Mock()
        profile.MO_VALUES = {"UtranCell": 1}
        profile.SUPPORTED_NODE_TYPES = ["ERBS", "RadioNode"]
        mock_node_dict.return_value = {"ERBS": [Mock()] * 5, "RadioNode": [Mock()]}
        delattr(profile, 'NUM_NODES')
        self.pool.allocate_batch_by_mo(profile)
        self.assertEqual(0, mock_debug.call_count)
        self.assertEqual(1, mock_allocate_nodes_with_mos.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.allocate_nodes_with_mos')
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.node_dict', new_callable=PropertyMock)
    def test_allocate_batch_by_mo_profile_using_num_nodes_total_nodes(self, mock_node_dict, mock_debug,
                                                                      mock_allocate_nodes_with_mos, *_):
        profile = Mock()
        profile.MO_VALUES = {"UtranCell": 1}
        profile.NUM_NODES = {"ERBS": -1, "RadioNode": 20, "RNC": 1}
        profile.TOTAL_NODES = 4
        profile.nodes_list = ["1"]
        mock_node_dict.return_value = {"ERBS": [Mock()] * 5, "RadioNode": [Mock()], "RNC": [Mock()]}
        self.pool.allocate_batch_by_mo_profile_using_num_nodes(profile)
        self.assertEqual(3, mock_allocate_nodes_with_mos.call_count)
        self.assertDictEqual({"RadioNode": 20, "RNC": 1, "ERBS": -1}, profile.NUM_NODES)
        self.assertEqual(11, mock_debug.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.sort_num_node_by_total_nodes',
           return_value={"ERBS": -1, "RadioNode": 20, "RNC": 1})
    @patch('enmutils_int.lib.node_pool_mgr.allocate_nodes_with_mos')
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.node_dict', new_callable=PropertyMock)
    def test_allocate_batch_by_mo_profile_using_num_nodes(self, mock_node_dict, mock_debug,
                                                          mock_allocate_nodes_with_mos, *_):
        profile = Mock()
        profile.MO_VALUES = {"UtranCell": 1}
        profile.TOTAL_NODES = 4
        profile.nodes_list = ["1"]
        mock_node_dict.return_value = {"ERBS": [Mock()] * 5, "RadioNode": [Mock()], "RNC": [Mock()]}
        delattr(profile, "TOTAL_NODES")
        self.pool.allocate_batch_by_mo_profile_using_num_nodes(profile)
        self.assertEqual(3, mock_allocate_nodes_with_mos.call_count)
        self.assertDictEqual({"RadioNode": 20, "RNC": 1, "ERBS": -1}, profile.NUM_NODES)
        self.assertEqual(11, mock_debug.call_count)

    def test_sort_num_node_by_total_nodes_no_total_nodes(self, *_):
        profile = Mock()
        profile.NUM_NODES = {"ERBS": -1, "RadioNode": 20, "RNC": 1}
        delattr(profile, "TOTAL_NODES")
        self.assertDictEqual(self.pool.sort_num_node_by_total_nodes(profile), {"ERBS": -1, "RadioNode": 20, "RNC": 1})

    ####################################################################################################################

    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_ids')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.reset')
    @patch('enmutils.lib.mutexer.mutex')
    def test_reset_interface_calls_reset(self, mock_mutex, mock_reset, *_):
        node_pool_mgr.reset()
        self.assertTrue(mock_mutex.called)
        self.assertTrue(mock_reset.called)

    @patch('enmutils_int.lib.node_pool_mgr.cached_nodes_list', [Mock()])
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.persist', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.get_num_required_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.add_profile_to_profiles_attr_on_nodes')
    def test_allocate_nodes__successful_if_nodes_specified(
            self, mock_add_profile_to_profiles_attr_on_nodes, mock_update_node_dict, mock_get_num_required_nodes, *_):
        pool = node_pool_mgr.ProfilePool()
        profile = Mock()
        nodes = [Mock()]
        pool.allocate_nodes(profile, nodes)
        mock_add_profile_to_profiles_attr_on_nodes.assert_called_with(profile, nodes)
        self.assertFalse(mock_update_node_dict.called)
        self.assertFalse(mock_get_num_required_nodes.called)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.allocate_batch_by_mo')
    def test_allocate_nodes_calls_allocate_nodes_with_mos_with_cmimport_profile(self, mock_allocate_by_batch_mo, *_):
        profile = CMImportProfile()
        profile.BATCH_MO_SIZE = 100
        profile.TOTAL_NODES = 100
        profile.NAME = "CMIMPORT_TEST_01"
        self.pool.allocate_nodes(profile)
        self.assertTrue(mock_allocate_by_batch_mo.called)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.allocate_nodes_by_ne_type', return_value=[])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_types', return_value=['ERBS'])
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils.lib.persistence')
    def test_allocate_nodes__with_no_supported_type_nodes_present_in_pool(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 20, primary_type='SGSN')
        profile = Profile()
        profile.NAME = "TEST_01"
        profile.TOTAL_NODES = 5
        profile.SUPPORTED_NODE_TYPES = ['ERBS']
        self.assertRaises(NoNodesAvailable, self.pool.allocate_nodes, profile)

    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    def test_allocate_nodes__to_profile_with_no_supported_type(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 20)
        profile = Profile()
        profile.TOTAL_NODES = 20
        profile.NAME = "TEST_01"
        self.assertRaises(NoNodesAvailable, self.pool.allocate_nodes, profile)

    @patch('enmutils.lib.persistence')
    def test_ensure_max_total_nodes_returns_expected_list_of_tuples(self, *_):
        profile = Profile()
        profile.TOTAL_NODES = 15
        profile.NAME = "FM_01"
        total_nodes_by_type = [('ERBS', 14), ('RadioNode', 0), ('RNC', 1), ('RBS', 4)]
        sum_of_required_nodes = sum([num for _, num in total_nodes_by_type])
        expected_result = [('ERBS', 10), ('RadioNode', 0), ('RNC', 1), ('RBS', 4)]
        call = self.pool._ensure_max_total_nodes(profile, total_nodes_by_type, sum_of_required_nodes)
        self.assertEqual(call, expected_result)

    @patch('enmutils.lib.persistence')
    def test_ensure_max_total_nodes_returns_same_list_of_tuples(self, *_):
        profile = Profile()
        profile.TOTAL_NODES = 4
        profile.NAME = "FM_01"
        total_nodes_by_type = [('ERBS', 14), ('RadioNode', 0), ('RNC', 1), ('RBS', 4)]
        sum_of_required_nodes = sum([num for _, num in total_nodes_by_type])
        expected_result = [('ERBS', 14), ('RadioNode', 0), ('RNC', 1), ('RBS', 4)]
        call = self.pool._ensure_max_total_nodes(profile, total_nodes_by_type, sum_of_required_nodes)
        self.assertEqual(call, expected_result)

    def test_group_nodes_per_sim__success(self, *_):
        node = Mock(simulation="LTE01", netsim="netsim")
        node1 = Mock(simulation="LTE02", netsim="netsim2")
        nodes = [node] * 3 + [node1] * 5
        result = node_pool_mgr.group_nodes_per_sim(nodes)
        self.assertEqual(2, len(result.keys()))
        self.assertEqual(3, len(result.get('netsim').get('LTE01')))
        self.assertEqual(5, len(result.get('netsim2').get('LTE02')))

    @patch('enmutils.lib.persistence')
    def test_add_nodes(self, *_):
        node_pool_mgr.cached_nodes_list = []
        num_nodes = 10
        added, _ = unit_test_utils.add_nodes_to_pool(self.pool, num_nodes)
        self.assertEqual(num_nodes, len(added))
        self.assertEqual(num_nodes, len(self.pool.nodes))
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils.lib.persistence')
    def test_add_already_added_nodes(self, *_):
        node_pool_mgr.cached_nodes_list = []
        num_nodes = 10
        unit_test_utils.add_nodes_to_pool(self.pool, num_nodes)
        (_, not_added) = unit_test_utils.add_nodes_to_pool(self.pool, num_nodes)
        self.assertEqual(num_nodes, len(self._get_errored_nodes(not_added)))
        self.assertEqual(num_nodes, len(self.pool.nodes))
        node_pool_mgr.cached_nodes_list = []

    @patch("enmutils_int.lib.node_pool_mgr.Pool.node_dict", new_callable=PropertyMock)
    def test_handle_backward_compatibility__is_successful_if_node_type_defined(self, mock_node_dict, *_):
        node1, node2 = Mock(node_id="SPFRER60001"), Mock(node_id="SPFRER60002")
        mock_node_dict.return_value = {"Router6672": {node1.node_id: node1}, "Router_6672": {node2.node_id: node2}}
        self.assertEqual([node1, node2], self.pool.handle_backward_compatibility([node1], "Router6672"))

    @patch("enmutils_int.lib.node_pool_mgr.Pool.node_dict", new_callable=PropertyMock)
    def test_handle_backward_compatibility__when_no_backward_compatibility_node_type_in_node_dict(self, mock_node_dict, *_):
        node1, node2 = Mock(node_id="SPFRER60001"), Mock(node_id="SPFRER60002")
        mock_node_dict.return_value = {"Router6672": {node1.node_id: node1}, "Router6274": {node2.node_id: node2}}
        self.pool.handle_backward_compatibility([node1], "Router6274")
        self.assertEqual([node1], self.pool.handle_backward_compatibility([node1], "Router6274"))

    @patch("enmutils_int.lib.node_pool_mgr.Pool.node_dict", new_callable=PropertyMock)
    def test_handle_backward_compatibility__is_successful_if_node_type_not_set_in_node_dict(self, mock_node_dict, *_):
        node1, node2 = Mock(node_id="SPFRER60001"), Mock(node_id="SPFRER60002")
        mock_node_dict.return_value = {"Router6672": {node1.node_id: node1},
                                       "Router_6672": {node2.node_id: node2},
                                       "Router9999": {}}
        self.assertEqual([node1], self.pool.handle_backward_compatibility([node1], "Router9999"))

    @patch("enmutils_int.lib.node_pool_mgr.Pool.node_dict", new_callable=PropertyMock)
    def test_handle_backward_compatibility__is_successful_if_node_type_not_defined(self, mock_node_dict, *_):
        node1, node2 = Mock(node_id="SPFRER60001"), Mock(node_id="SPFRER60002")
        mock_node_dict.return_value = {"Router6672": {node1.node_id: node1}, "Router_6672": {node2.node_id: node2}}
        self.assertEqual([node1], self.pool.handle_backward_compatibility([node1]))

    @patch("enmutils_int.lib.node_pool_mgr.Pool.node_dict", new_callable=PropertyMock)
    def test_handle_backward_compatibility__is_successful_if_node_type__in_updated_dict(self, mock_node_dict, *_):
        node1, node2 = Mock(node_id="SGSN01"), Mock(node_id="SGSN02")
        mock_node_dict.return_value = {"SGSN": {node1.node_id: node1}, "SGSN-MME": {node2.node_id: node2}}
        self.assertListEqual([node2, node1], self.pool.handle_backward_compatibility([node2], "SGSN-MME"))

    @patch('enmutils_int.lib.node_pool_mgr.update_lte_node')
    @patch('enmutils_int.lib.node_pool_mgr.Pool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.Pool._load_nodes_from_file')
    def test_add__nodes_if_profiles_passed_in(self, mock_load_nodes_from_file, *_):
        profile = get_profile()
        profile2 = get_profile()
        profile = [profile, profile2]
        nodes = get_nodes(5)
        mock_load_nodes_from_file.return_value = (nodes, [])
        self.pool.add('mock_file_path', profiles=profile)

    @patch('enmutils_int.lib.node_pool_mgr.Pool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.Pool._load_nodes_from_file')
    def test_add_nodes__if_primary_type_not_in_nodes_dict(self, mock_load_from_file, *_):
        node = Mock(node_id="LTE01", primary_type=None)
        mock_load_from_file.return_value = ([node], [])
        _, missing = self.pool.add('file_path')
        self.assertEqual(len(missing["MISSING_PRIMARY_TYPE"]), 1)

    @patch('enmutils_int.lib.node_pool_mgr.Pool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.validate_nodes_against_enm', return_value=["LTE01"])
    @patch('enmutils_int.lib.node_pool_mgr.Pool._load_nodes_from_file')
    def test_add__validates_sync(self, mock_load_from_file, *_):
        node = Mock(node_id="LTE01", primary_type="ERBS")
        mock_load_from_file.return_value = ([node], [])
        _, missing = self.pool.add('file_path', validate=True)
        self.assertEqual(len(missing["NOT_SYNCED"]), 1)

    @patch('enmutils_int.lib.node_pool_mgr.node_parse.get_node_data')
    def test_load_nodes_from_file__if_no_key_for_primary_type__defaults_to_base_load_node(self, mock_get_node_data, *_):
        mock_get_node_data.return_value = ([{'primary_type': 'mock_type'}], [])
        nodes, _ = self.pool._load_nodes_from_file('mock_file_path')
        self.assertEqual(1, len(nodes))

    @patch('enmutils_int.lib.node_pool_mgr.node_parse.get_node_data')
    def test_load_nodes_from_file__success(self, mock_get_node_data, *_):
        mock_get_node_data.return_value = ([{'primary_type': 'ERBS'}], [])
        nodes, _ = self.pool._load_nodes_from_file('mock_file_path')
        self.assertEqual(1, len(nodes))

    @patch('enmutils_int.lib.node_pool_mgr.persistence.has_key', side_effect=[True, False])
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get')
    @patch('enmutils_int.lib.node_pool_mgr.node_parse.get_node_data')
    @patch('enmutils_int.lib.node_pool_mgr.node_parse.get_node_names_from_xml')
    def test_load_nodes_from_file__removes_without_querying_enm(self, mock_data_from_xml, mock_get_node_data,
                                                                mock_get, *_):
        mock_data_from_xml.return_value = ["Node", "Node1"]
        self.pool._load_nodes_from_file('mock_file_path', remove_operation=True)
        self.assertEqual(1, mock_data_from_xml.call_count)
        self.assertEqual(0, mock_get_node_data.call_count)
        self.assertEqual(1, mock_get.call_count)

    def test_load_nodes_from_file__check_all_primary_types_in_enm_node(self, *_):
        load_node_support_not_delivered_yet = ['HSS-FE-TSP', 'VPN-TSP', 'vMSC', 'ECM', 'switch-6391', 'Fronthaul-6392',
                                               'MINI-LINK-6351', 'MSC-BC-BSP', 'WMG', 'SBG', 'SBG-IS', 'CSCF-TSP', 'PT',
                                               'MSC-DB', 'IP-STP', 'EPDG', 'STP', 'CCN-TSP', 'CSCF', 'cSAPC-TSP',
                                               'PT2020', 'vWMG', 'vIP-STP', 'BSP', 'BGF', 'vBGF']
        unsupported_nodes = []
        for enm_node_primary_type in enm_node__node_class_map.keys():
            if (enm_node_primary_type not in load_node_support_not_delivered_yet and
                    not NODE_CLASS_MAP.get(enm_node_primary_type)):
                unsupported_nodes.append(enm_node_primary_type)

        if unsupported_nodes:
            raise (Exception("Missing support in load_node for Primary Types in enm_node: {}"
                             .format(unsupported_nodes)))

    @patch('enmutils_int.lib.node_pool_mgr.cached_nodes_list', [])
    @patch('enmutils.lib.persistence')
    def test_filter__returns_correct_node(self, *_):
        num_nodes = 10
        unit_test_utils.add_nodes_to_pool(self.pool, num_nodes)
        nodes_to_filter = ["netsimlin537_ERBS0001", "netsimlin537_ERBS0002"]
        filtered_nodes = self.pool.filter(nodes_to_filter)
        self.assertEqual(2, len(filtered_nodes))

    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.node_dict', new_callable=PropertyMock)
    def test_grep_returns_correct_nodes_from_pool(self, mock_node_dict, *_):
        mock_node_dict.return_value = {
            "ERBS": {"netsimlin537_ERBS00100": ERBSNode(node_id="netsimlin537_ERBS00100"),
                     "netsimlin538_ERBS00100": ERBSNode(node_id="netsimlin538_ERBS00100"),
                     "netsimlin537_ERBS00101": ERBSNode(node_id="netsimlin537_ERBS00101")}
        }
        self.assertEqual(len(self.pool.grep(["netsimlin537_ERBS001*"])), 2)
        self.assertEqual(len(self.pool.grep(["netsimlin53?_*RBS001*"])), 3)
        self.assertEqual(len(self.pool.grep(["netsimlin53[7,8]_ERBS001*"])), 3)
        self.assertEqual(len(self.pool.grep(["netsimlin53[!6,8]_ERBS001*"])), 2)

    @patch('enmutils_int.lib.node_pool_mgr.remove_node')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.node_dict', new_callable=PropertyMock)
    @patch('enmutils_int.lib.node_pool_mgr.Pool._load_nodes_from_file')
    def test_remove__success(self, mock_load, mock_node_dict, mock_remove_node, *_):
        node, node1, node3 = (Mock(node_id="Node", primary_type="ERBS"), Mock(node_id="Node1", primary_type="ERBS"),
                              Mock(node_id="Node3", primary_type="ERBS"))
        node.profiles, node1.profiles = [], ["TEST_01"]
        nodes = [node, node1, node3]
        mock_load.return_value = nodes, ["Node2", "Node4"]
        mock_node_dict.return_value = {"ERBS": {node.node_id: node for node in nodes[:-1]}}
        self.pool._nodes = {"ERBS": ["Node", "Node1", "Node2"]}
        self.pool.remove("nodes")
        self.assertEqual(1, mock_remove_node.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool._is_in_use', return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.nodes', new_callable=PropertyMock)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.reset')
    def test_reset(self, mock_reset, mock_nodes, *_):
        mock_nodes.return_value = [ERBSLoadNode()] * 4
        self.pool.reset()
        self.assertEqual(4, mock_reset.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=True)
    @patch('enmutils_int.lib.node_pool_mgr.Pool._is_in_use', return_value=True)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.nodes', new_callable=PropertyMock)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.reset')
    def test_reset_calls_node_reset_errors_only_if_nodes_are_in_use_and_profiles_are_active(self, mock_reset,
                                                                                            mock_nodes, *_):
        mock_nodes.return_value = [ERBSLoadNode()] * 4
        self.pool.reset()
        self.assertEqual(0, mock_reset.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=True)
    @patch('enmutils_int.lib.node_pool_mgr.Pool._is_in_use', return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.nodes', new_callable=PropertyMock)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.reset')
    def test_reset_calls_node_reset_if_profiles_are_not_active(self, mock_reset, mock_nodes, *_):
        mock_nodes.return_value = [ERBSLoadNode()] * 4
        self.pool.reset()
        self.assertEqual(4, mock_reset.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=["HA_01"])
    @patch('enmutils_int.lib.node_pool_mgr.Pool._is_in_use', return_value=True)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.nodes', new_callable=PropertyMock)
    def test_reset_calls_node_reset__if_profiles_are_active_but_exclusive_are_not(self, mock_nodes, *_):
        node, node1 = Mock(profiles=["AP_01"], is_exclusive=True), Mock(profiles=["HA_01"], is_exclusive=True)
        mock_nodes.return_value = [node, node1]
        self.pool.reset()
        self.assertEqual(1, node.reset.call_count)
        self.assertEqual(0, node1.reset.call_count)

    def test_remove_all_removes_every_node_in_the_pool_and_returns_true_if_no_profile_is_running(self, *_):
        node_pool_mgr.cached_nodes_list = []
        num_nodes = 10
        unit_test_utils.add_nodes_to_pool(self.pool, num_nodes)
        with patch('enmutils.lib.persistence.Persistence.remove') as mock_persistence_remove:
            self.assertTrue(self.pool.remove_all())
            self.assertEqual(11, mock_persistence_remove.call_count)
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_remove_all_returns_false_if_profiles_are_running(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 2)
        fm_01 = TestProfile(name="FM_01", num_nodes={'ERBS': -1})
        self.pool.allocate_nodes(fm_01)
        self.assertFalse(self.pool.remove_all())

    @patch('enmutils.lib.persistence')
    def test_remove_all_removes_all_and_returns_true_using_force_if_profiles_are_running(self, *_):
        node = Mock()
        node.profiles = ["FM_01"]
        self.pool._nodes = {"ERBS": {"Node1": node}}
        self.assertTrue(self.pool.remove_all(force=True))

    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.nodes', new_callable=PropertyMock)
    def test_is_in_use_returns_true_if_a_profile_is_running(self, mock_nodes, *_):
        node = Mock()
        mock_nodes.return_value = [node]
        self.assertTrue(self.pool._is_in_use())

    @patch('enmutils.lib.persistence')
    def test_is_in_use_returns_false_if_no_profile_is_running(self, *_):
        node_pool_mgr.cached_nodes_list = []
        num_nodes = 10
        unit_test_utils.add_nodes_to_pool(self.pool, num_nodes)
        self.assertFalse(self.pool._is_in_use())
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.node_pool_mgr.cached_nodes_list', [])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    def test_get_available_nodes__is_successful(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': 5, 'RadioNode': 3}
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        available_nodes = self.pool.get_available_nodes(profile)
        self.assertEqual(len(available_nodes), 5)

    @patch('enmutils_int.lib.node_pool_mgr.cached_nodes_list', [])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    def test_get_available_nodes__is_successful_if_profile_name_is_ha_01_and_radionodes_not_available(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': 5, 'RadioNode': 3}
        profile.NAME = "HA_01"
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        available_nodes = self.pool.get_available_nodes(profile)
        self.assertEqual(len(available_nodes), 5)

    @patch('enmutils_int.lib.node_pool_mgr.cached_nodes_list', [])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    def test_get_available_nodes__is_successful_if_profile_name_is_ha_01_and_erbs_radionodes_are_available(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': 5, 'RadioNode': 3}
        profile.NAME = "HA_01"
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        unit_test_utils.add_nodes_to_pool(self.pool, 10, primary_type="RadioNode")
        available_nodes = self.pool.get_available_nodes(profile)
        self.assertEqual(len(available_nodes), 5)
        for node in available_nodes:
            self.assertEqual(node.primary_type, "ERBS")

    @patch('enmutils_int.lib.node_pool_mgr.cached_nodes_list', [])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    def test_get_available_nodes__is_successful_if_profile_name_is_ha_01_and_only_radionodes_are_available(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': 5, 'RadioNode': 3}
        profile.NAME = "HA_01"
        unit_test_utils.add_nodes_to_pool(self.pool, 10, primary_type="RadioNode")
        available_nodes = self.pool.get_available_nodes(profile)
        self.assertEqual(len(available_nodes), 3)
        for node in available_nodes:
            self.assertEqual(node.primary_type, "RadioNode")

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    def test_get_available_nodes_is_successful_for_profile_with_empty_num_nodes(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {}
        unit_test_utils.add_nodes_to_pool(self.pool, 5)
        available_nodes = self.pool.get_available_nodes(profile)
        self.assertEqual(len(available_nodes), len(self.pool.nodes))

    @patch('enmutils_int.lib.node_pool_mgr.cached_nodes_list', [])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    def test_get_available_nodes__is_successful_for_profile_with_total_nodes_minus_one(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': 5, 'RadioNode': -1}
        profile.TOTAL_NODES = 10
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        available_nodes = self.pool.get_available_nodes(profile)
        self.assertEqual(len(available_nodes), 5)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    def test_get_available_nodes_raises_value_error(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': -1, 'RadioNode': -1}
        profile.TOTAL_NODES = 10
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        self.assertRaises(ValueError, self.pool.get_available_nodes, profile)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    def test_get_available_nodes_raises_no_nodes_available_error(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {'RadioNode': 5}
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        self.assertRaises(NoNodesAvailable, self.pool.get_available_nodes, profile)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    def test_get_random_available_nodes_is_successful(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': 5}
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        available_nodes = self.pool.get_random_available_nodes(profile)
        self.assertEqual(len(available_nodes), len(self.pool.nodes))

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message',
           return_value={'RadioNode': {'managed_element_type': ['ENodeB', 'GNodeB']}})
    def test_get_random_available_nodes__is_successful_cmimport_31(self, *_):
        profile = get_profile()
        profile.NUM_NODES = {'RadioNode': 5}
        profile.NAME = "CMIMPORT_31"
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        self.pool.get_random_available_nodes(profile)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.nodes', new_callable=PropertyMock, return_value=[])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.remove_upgind_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.distribute_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.node_dict', new_callable=PropertyMock)
    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter')
    @patch('enmutils_int.lib.node_pool_mgr.get_synced_nodes')
    def test_get_random_available_nodes_is_successful_check_sync(self, mock_get_synced_nodes, mock_filter,
                                                                 mock_nodes_dict, mock_distribute, *_):
        profile = Mock()
        profile.NUM_NODES = {'ERBS': 3}
        profile.CHECK_NODE_SYNC = True
        profile.CELL_CARDINALITY_NES = ["ERBS"]
        node, node1, node2, node3 = Mock(), Mock(), Mock(), Mock()
        node.node_id, node1.node_id, node2.node_id, node3.node_id = "ERBS01", "ERBS02", "ERBS03", "ERBS04"
        nodes = [node, node1, node2, node3]
        mock_nodes_dict.return_value = {"ERBS": nodes}
        mock_distribute.return_value = nodes
        mock_filter.return_value.execute.return_value = nodes
        mock_get_synced_nodes.return_value = ["ERBS01", "ERBS02"]
        available_nodes = self.pool.get_random_available_nodes(profile)
        self.assertEqual(len(available_nodes), 2)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.remove_upgind_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter.execute', return_value=[])
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_get_random_available_nodes_raises_value_error(self, mock_add_error, *_):
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': 5}
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        with self.assertRaises(NoNodesAvailable):
            self.pool.get_random_available_nodes(profile)
            self.assertTrue(mock_add_error.called)

    def test_add_filtered_node_types_in_message__returns_the_same_message_when_no_filter_information(self, *_):
        profile = Mock()
        profile.NODE_FILTER = {}
        node_types = self.pool.add_filtered_node_types_in_message('RadioNode', profile)

        self.assertEqual('RadioNode', node_types)

    def test_add_filtered_node_types_in_message__returns_same_message_when_no_radionode_in_node_types(self, *_):
        profile = Mock()
        profile.NODE_FILTER = {'RadioNode': {'managed_element_type': ['ENodeB', 'GNodeB']}}
        node_types = self.pool.add_filtered_node_types_in_message('ERBS, RBS', profile)

        self.assertEqual("ERBS, RBS", node_types)

    def test_add_filtered_node_types_in_message__add_the_filtered_nodes_in_message(self, *_):
        profile = Mock()
        profile.NODE_FILTER = {'RadioNode': {'managed_element_type': ['ENodeB', 'GNodeB']}}
        node_types = self.pool.add_filtered_node_types_in_message('ERBS, RadioNode, RBS', profile)

        self.assertEqual("ERBS, RadioNode (Node Filter: ['ENodeB', 'GNodeB']), RBS", node_types)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_get_random_available_nodes_is_unsuccessful_with_num_nodes(self, mock_add_error, *_):
        node_pool_mgr.cached_nodes_list = []
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': 5}
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        self.pool.get_random_available_nodes(profile, num_nodes=20)
        self.assertTrue(mock_add_error.called)
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.node_pool_mgr.cached_nodes_list', [])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.distribute_nodes')
    def test_get_random_available_nodes__calls_distribute_nodes(self, mock_distribute, *_):
        profile = get_profile()
        profile.NUM_NODES = {'ERBS': 5}
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        self.pool.get_random_available_nodes(profile, num_nodes=10)
        self.assertTrue(mock_distribute.called)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes_allocates_nodes_to_profile(self, *_):
        num_nodes = 10
        unit_test_utils.add_nodes_to_pool(self.pool, num_nodes)
        fm_01 = TestProfile(name="FM_01", num_nodes={'ERBS': -1})
        fm_01.NUM_NODES = {"ERBS": 7}
        self.pool.allocate_nodes(fm_01)
        self.assertEqual(sum(fm_01.NUM_NODES.values()), len(self.pool.allocated_nodes_as_dict(fm_01)["ERBS"]))

    @patch("enmutils_int.lib.node_pool_mgr.Pool.__init__", return_value=None)
    @patch("enmutils_int.lib.node_pool_mgr.ProfilePool._node_is_used_by", return_value=True)
    @patch("enmutils_int.lib.node_pool_mgr.ProfilePool.nodes", new_callable=PropertyMock)
    def test_allocate_all_nodes_allocates_nodes_to_profile(self, mock_nodes, *_):
        test_profile = Mock()
        pool = node_pool_mgr.ProfilePool()
        mock_nodes.return_value = [Mock(primary_type="ERBS")]
        self.assertEqual(1, len(pool.allocated_nodes_as_dict(test_profile)["ERBS"]))

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.get_allocated_node_summary')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.add_profile', side_effect=AddProfileToNodeError)
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_allocate_nodes_adds_error_if_error_allocating_nodes(self, mock_add_error, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 5)
        profile = get_profile()
        profile.NUM_NODES = {"ERBS": 5}
        self.pool.allocate_nodes(profile)
        self.assertTrue(mock_add_error.called)
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils.lib.persistence')
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.remove_profile')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.nodes', new_callable=PropertyMock)
    def test_deallocate_nodes_successfully_deallocates_the_profile_from_all_nodes(self, mock_nodes, mock_remove_profile,
                                                                                  mock_add_error_as_exception,
                                                                                  mock_debug, *_):
        nodes = get_nodes(2)
        for node in nodes:
            node.profiles.append("FM_01")
        mock_nodes.return_value = nodes
        profile = get_profile(name="FM_01")
        self.pool.deallocate_nodes(profile)
        self.assertTrue(mock_remove_profile.called)
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.persistence')
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.remove_profile')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.nodes', new_callable=PropertyMock)
    def test_deallocate_nodes_does_not_successfully_deallocate_the_profile_from_all_nodes(self, mock_nodes,
                                                                                          mock_remove_profile,
                                                                                          mock_add_error_as_exception,
                                                                                          mock_debug, *_):
        nodes = get_nodes(2)
        for node in nodes:
            node.profiles.append("FM_01")
        mock_nodes.return_value = nodes
        profile = get_profile(name="FM_01")
        mock_remove_profile.side_effect = RemoveProfileFromNodeError
        self.pool.deallocate_nodes(profile)
        self.assertTrue(mock_remove_profile.called)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.remove_profile')
    @patch('enmutils_int.lib.node_pool_mgr.log.logger.debug')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.nodes', new_callable=PropertyMock)
    def test_deallocate_nodes__calls_log_if_there_are_no_nodes_allocated_to_that_profile(
            self, mock_nodes, mock_log, mock_remove_profile, *_):
        nodes = get_nodes(2)
        mock_nodes.return_value = nodes
        profile = get_profile(name="FM_01")
        self.pool.deallocate_nodes(profile)
        self.assertFalse(mock_remove_profile.called)
        mock_log.assert_any_call("The profile: 'FM_01' is not allocated to any node")

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes_allocates_nodes_randomly(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        fm_01 = TestProfile(name="FM_01", num_nodes={'ERBS': 3})
        previous_nodes = []
        results = []
        for _ in range(0, 2):
            self.pool.allocate_nodes(fm_01)
            current_nodes = []
            for nodes in self.pool.allocated_nodes_as_dict(fm_01).values():
                current_nodes = current_nodes + nodes
            results.append(sorted(previous_nodes) == sorted(current_nodes))
            self.pool.deallocate_nodes(fm_01)
            previous_nodes = current_nodes
        self.assertFalse(all(results))

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__allocates_as_many_nodes_as_it_can_to_profile(self, *_):
        num_nodes = 10
        unit_test_utils.add_nodes_to_pool(self.pool, num_nodes)
        fm_01 = TestProfile(name="FM_01", num_nodes={'ERBS': -1})
        fm_01.NUM_NODES = {"ERBS": 70}
        self.pool.allocate_nodes(fm_01)
        self.assertEqual(len(fm_01.nodes_list), 10)

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__allocates_as_many_nodes_as_it_can_to_profile_for_exclusive_nodes(self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        profile = Profile()
        profile.NAME = "TEST_01"
        profile.EXCLUSIVE = True
        profile.NUM_NODES = {"ERBS": 9}
        profile2 = Profile()
        profile2.NAME = "TEST_02"
        profile2.EXCLUSIVE = True
        profile2.NUM_NODES = {"ERBS": 2}
        self.pool.allocate_nodes(profile)
        self.pool.allocate_nodes(profile2)
        self.assertEqual(len(profile.nodes_list), 9)
        self.assertEqual(len(profile2.nodes_list), 1)
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes_on_multiple_profiles_can_allocate_nodes_exclusively_successfully(self, *_):
        node_pool_mgr.cached_nodes_list = []
        num_nodes = 10
        unit_test_utils.add_nodes_to_pool(self.pool, num_nodes)
        profile = Profile()
        profile.NAME = "TEST_01"
        profile.EXCLUSIVE = True
        profile2 = Profile()
        profile2.NAME = "TEST_02"
        profile2.EXCLUSIVE = True
        profile.NUM_NODES = {"ERBS": 5}
        profile2.NUM_NODES = {"ERBS": 5}
        self.pool.allocate_nodes(profile)
        self.pool.allocate_nodes(profile2)

        profile_nodes = self.pool.allocated_nodes_as_dict(profile)["ERBS"]
        profile2_nodes = self.pool.allocated_nodes_as_dict(profile2)["ERBS"]

        for node in profile_nodes:
            self.assertFalse(node in profile2_nodes)
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__will_fill_missing_sgsn_nodes_with_erbs_nodes(self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        unit_test_utils.add_nodes_to_pool(self.pool, 5, primary_type="SGSN")
        profile = Profile()
        profile.NAME = "TEST_01"
        profile.TOTAL_NODES = 10
        profile.NUM_NODES = {"ERBS": -1, "SGSN": 10}
        self.pool.allocate_nodes(profile)
        self.assertEqual(len(profile.nodes["SGSN"]), 5)
        self.assertEqual(len(profile.nodes["ERBS"]), 5)
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__will_get_all_nodes_for_erbs_and_sgsn_nodes(self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 2)
        unit_test_utils.add_nodes_to_pool(self.pool, 2, primary_type="SGSN")
        profile = Profile()
        profile.NAME = "TEST_01"
        profile.NUM_NODES = {"ERBS": -1, "SGSN": -1}
        self.pool.allocate_nodes(profile)
        self.assertEqual(len(profile.nodes["SGSN"]), 2)
        self.assertEqual(len(profile.nodes["ERBS"]), 2)
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    def test_allocate_nodes__errors_when_not_enough_nodes_in_pool(self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 5)
        unit_test_utils.add_nodes_to_pool(self.pool, 1, primary_type="SGSN")
        profile = Profile()
        profile.NAME = "TEST_01"
        profile.NUM_NODES = {"ERBS": 6, "SGSN": 1}
        self.pool.allocate_nodes(profile)
        self.assertEqual(len(profile.nodes), 2)
        self.assertEqual(len(profile.nodes["ERBS"]), 5)
        self.assertEqual(len(profile.warnings), 2)
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    def test_allocate_nodes_raises_no_nodes_available_error_when_no_nodes_have_been_allocated_to_profile(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 1)
        profile = Profile()
        profile.NAME = "TEST_01"
        profile.NUM_NODES = {"SGSN": -1}
        self.assertRaises(NoNodesAvailable, self.pool.allocate_nodes, profile)

    @patch("enmutils_int.lib.node_pool_mgr.mutex")
    @patch("enmutils_int.lib.node_pool_mgr.get_pool")
    def test_deallocate_nodes__is_successful(self, mock_get_pool, *_):
        profile = Mock()
        node_pool_mgr.deallocate_nodes(profile)
        mock_get_pool.return_value.deallocate_nodes.assert_called_with(profile)

    @patch("enmutils_int.lib.node_pool_mgr.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.node_pool_mgr.deallocate_unused_nodes_from_profile")
    @patch("enmutils_int.lib.node_pool_mgr.multitasking.create_single_process_and_execute_task")
    def test_deallocate_unused_nodes__is_successful(
            self, mock_create_single_process_and_execute_task, mock_deallocate_unused_nodes_from_profile, *_):
        nodes = [Mock, Mock()]
        node_pool_mgr.deallocate_unused_nodes(nodes, "TEST_01")
        mock_create_single_process_and_execute_task.assert_called_with(mock_deallocate_unused_nodes_from_profile,
                                                                       args=(nodes, "TEST_01"), fetch_result=False)

    @patch("enmutils_int.lib.node_pool_mgr.mutex")
    @patch("enmutils_int.lib.node_pool_mgr.remove_profile_from_nodes")
    def test_deallocate_unused_nodes_from_profile__is_successful(self, mock_remove_profile_from_nodes, *_):
        node = Mock()
        node_pool_mgr.deallocate_unused_nodes_from_profile([node], "TEST_01")
        mock_remove_profile_from_nodes.assert_called_with([node], "TEST_01")

    @patch("enmutils_int.lib.node_pool_mgr.mutexer.mutex")
    @patch("enmutils_int.lib.node_pool_mgr.log.logger.debug")
    @patch("enmutils_int.lib.node_pool_mgr.update_cached_list_of_nodes")
    @patch("enmutils_int.lib.node_pool_mgr.persistence")
    def test_remove_profile_from_nodes__doesnt_remove_any_profile_from_nodes(
            self, mock_persistence, mock_update_cached_list_of_nodes, mock_debug, *_):
        node_pool_mgr.cached_nodes_list = []
        node1 = Mock(node_id="node1", profiles=["TEST_02"])

        node_pool_mgr.remove_profile_from_nodes([node1], "TEST_01")

        self.assertFalse(mock_persistence.get.called)
        self.assertFalse(mock_update_cached_list_of_nodes.called)
        self.assertTrue(call("Node node1 not allocated to profile TEST_01") in mock_debug.mock_calls)

        node_pool_mgr.cached_nodes_list = []

    @patch("enmutils_int.lib.node_pool_mgr.mutexer.mutex")
    @patch("enmutils_int.lib.node_pool_mgr.log.logger.debug")
    @patch("enmutils_int.lib.node_pool_mgr.update_cached_list_of_nodes")
    @patch("enmutils_int.lib.node_pool_mgr.persistence")
    def test_remove_profile_from_nodes__updates_cached_nodes_list(
            self, mock_persistence, mock_update_cached_list_of_nodes, *_):
        node1 = Mock(node_id="node1", profiles=["TEST_01", "TEST_02"])
        node2 = Mock(node_id="node2", profiles=["TEST_01"])
        node3 = Mock(node_id="node3", profiles=["TEST_02"])
        node_pool_mgr.cached_nodes_list = [node1, node2, node3]

        persisted_node1 = Mock(node_id="node1", profiles=["TEST_01", "TEST_02"])
        persisted_node2 = Mock(node_id="node2", profiles=["TEST_01"])

        mock_persistence.get.side_effect = [persisted_node1, persisted_node2]

        node_pool_mgr.cached_nodes_list = [node1, node2, node3]
        node_pool_mgr.remove_profile_from_nodes([node1, node2, node3], "TEST_01")
        node_pool_mgr.cached_nodes_list = [node3, persisted_node1, persisted_node2]
        mock_update_cached_list_of_nodes.assert_called_with({persisted_node1.node_id: persisted_node1,
                                                             persisted_node2.node_id: persisted_node2})
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.get_allocated_node_summary')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_pool_serialize(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        fm_01 = TestProfile(name="FM_01", num_nodes={'ERBS': -1})
        self.pool.allocate_nodes(fm_01)
        serialized = self.pool.jsonify()
        self.assertTrue(serialized.startswith('{"netsims": [{"name": "netsimlin537", "simulations": [{"nodes": ['))

    @patch('enmutils.lib.persistence')
    def test_pool_has_mgw(self, *_):
        haskey = False
        if "MGW" in self.pool._nodes:
            haskey = True
        self.assertTrue(haskey)

    @patch('enmutils.lib.persistence')
    def test_pool_has_pico(self, *_):
        haskey = False
        if "MSRBS_V1" in self.pool._nodes:
            haskey = True
        self.assertTrue(haskey)

    @patch('enmutils.lib.persistence')
    def test_pool_has_epg(self, *_):
        haskey = False
        if "EPG" in self.pool._nodes:
            haskey = True
        self.assertTrue(haskey)

    def test_setting_nodes_per_host_limits_allocated_nodes(self, *_):
        profile = Mock()
        profile.NAME = "TEST_02"
        profile.NUM_NODES = {"ERBS": -1}
        profile.NODES_PER_HOST = 2
        delattr(profile, 'NODE_FILTER')
        node, node1, node2, node3 = Mock(), Mock(), Mock(), Mock()
        node.netsim, node1.netsim, node2.netsim, node3.netsim = "host", "host", "host", "host"
        nodes = [node, node1, node2, node3]
        nodes_filter = NodesFilter(profile, nodes, 'ERBS')
        retained_nodes = nodes_filter.execute()
        self.assertEqual(len(retained_nodes), 2)

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__shm_nodes_per_host_check_nodes_being_allocated_correctly_using_nodes_per_host_value(
            self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 6)
        for node in self.pool.nodes[:3]:
            node.netsim = "netsimX"
            node._persist()
        profile = Profile()
        profile.NAME = "SHM_02"
        profile.NODES_PER_HOST = 2
        profile.NUM_NODES = {"ERBS": -1}
        self.pool.allocate_nodes(profile)
        self.assertEqual(4, len(profile.nodes_list))
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__shm_check_nodes_per_hosts_allocates_all_nodes_in_pool_correctly_using_three_netsims(
            self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 6)
        for node in self.pool.nodes[:2]:
            node.netsim = "netsimX"
            node._persist()
        for node in self.pool.nodes[2:4]:
            node.netsim = "netsimY"
            node._persist()
        profile = Profile()
        profile.NAME = "SHM_02"
        profile.NODES_PER_HOST = 2
        profile.NUM_NODES = {"ERBS": -1}
        self.pool.allocate_nodes(profile)
        self.assertEqual(6, len(profile.nodes_list))
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.allocate_nodes_by_ne_type', return_value=[])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_types', return_value=['ERBS'])
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__dynamically_assigning_nodes_based_on_pool_config_with_no_total_property_set_on_profile(
            self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        mock_fm_01 = TestProfile(name="FM_01", num_nodes={'ERBS': 5}, supported_node_types=['ERBS'])
        self.pool.allocate_nodes(mock_fm_01)
        self.assertEqual(5, len(mock_fm_01.nodes_list))
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_types', return_value=['ERBS', 'SGSN'])
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__dynamically_assign_nodes_based_on_pool_configuration_with_total_property_set_on_profile(
            self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        mock_fm_01 = TestProfile(name="FM_01", num_nodes={'ERBS': 5}, total_nodes=5, supported_node_types=['ERBS'])
        self.pool.allocate_nodes(mock_fm_01)
        self.assertEqual(5, len(mock_fm_01.nodes_list))
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_types', return_value=['ERBS', 'SGSN'])
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__dynamically_assign_nodes_based_on_pool_configuration_with_different_node_types_in_pool(
            self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        unit_test_utils.add_nodes_to_pool(self.pool, 5, primary_type='SGSN')
        mock_fm_01 = TestProfile(name="FM_01", num_nodes={'ERBS': 5}, total_nodes=6,
                                 supported_node_types=['ERBS', 'SGSN'])
        self.pool.allocate_nodes(mock_fm_01)
        self.assertEqual(4, len(mock_fm_01.nodes['ERBS']))
        self.assertEqual(2, len(mock_fm_01.nodes['SGSN']))
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_types', return_value=['ERBS', 'SGSN'])
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__assign_nodes_by_supported_node_type_where_dominant_node_not_in_supported_types(self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 10)
        unit_test_utils.add_nodes_to_pool(self.pool, 5, primary_type='SGSN')
        unit_test_utils.add_nodes_to_pool(self.pool, 15, primary_type='RadioNode')
        mock_fm_01 = TestProfile(name="FM_01", num_nodes={'ERBS': 5}, total_nodes=6,
                                 supported_node_types=['ERBS', 'SGSN'])
        self.pool.allocate_nodes(mock_fm_01)
        self.assertEqual(4, len(mock_fm_01.nodes['ERBS']))
        self.assertEqual(2, len(mock_fm_01.nodes['SGSN']))
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_types', return_value=['ERBS', 'SGSN'])
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__assign_nodes_by_supported_node_type_where_no_all_node_types_available(self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 4)
        unit_test_utils.add_nodes_to_pool(self.pool, 4, primary_type='SGSN')
        unit_test_utils.add_nodes_to_pool(self.pool, 4, primary_type='RadioNode')
        mock_fm_02 = TestProfile(name="FM_02", total_nodes=6, supported_node_types=['ERBS', 'SGSN'])
        self.pool.allocate_nodes(mock_fm_02)
        self.assertEqual(3, len(mock_fm_02.nodes['ERBS']))
        self.assertEqual(3, len(mock_fm_02.nodes['SGSN']))
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_types', return_value=['ERBS', 'SGSN', 'RadioNode',
                                                                                  'Router_6672', 'RNC'])
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__dynamically_assign_nodes_based_on_pool_config_where_split_is_not_an_even_number(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 9)
        unit_test_utils.add_nodes_to_pool(self.pool, 3, primary_type='SGSN')
        unit_test_utils.add_nodes_to_pool(self.pool, 3, primary_type='RadioNode')
        unit_test_utils.add_nodes_to_pool(self.pool, 3, primary_type='Router_6672')
        unit_test_utils.add_nodes_to_pool(self.pool, 3, primary_type='RNC')
        mock_fm_01 = TestProfile(name="FM_01", total_nodes=6, supported_node_types=['ERBS', 'SGSN', 'RadioNode',
                                                                                    'Router_6672', 'RNC'])

        self.pool.allocate_nodes(mock_fm_01)
        self.assertEqual(6, sum([len(nodes) for nodes in mock_fm_01.nodes.values()]))

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__node_filter_filters_nodes_on_attributes(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 6, node_version="16B")
        for node in self.pool.nodes[:3]:
            node.node_version = "16A"
            node._persist()
        mock_profile = TestProfile(name="FM_01", num_nodes={"ERBS": 3}, node_filter={"ERBS": {"node_version": ["16A"]}})
        self.pool.allocate_nodes(mock_profile)
        for node in mock_profile.nodes['ERBS']:
            self.assertEqual(node.node_version, "16A")

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_allocate_nodes__node_filter_returns_all_nodes_if_node_type_not_in_node_filter(self, *_):
        node_pool_mgr.cached_nodes_list = []
        unit_test_utils.add_nodes_to_pool(self.pool, 3, node_version="16B")
        for node in self.pool.nodes[:3]:
            node.node_version = "16A"
            node._persist()
        mock_profile = TestProfile(name="FM_01", num_nodes={"ERBS": 3},
                                   node_filter={"SGSN": {"node_version": ["16A"]}})
        self.pool.allocate_nodes(mock_profile)
        self.assertEqual(len(mock_profile.nodes['ERBS']), 3)
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.remove_upgind_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    def test_node_filter_filters_nodes_on_attributes_returns_no_nodes_if_none_match(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 3, node_version="16B")
        for node in self.pool.nodes[:3]:
            node.node_version = "16C"
            node._persist()
        mock_profile = TestProfile(name="FM_01", num_nodes={"ERBS": 3},
                                   node_filter={"ERBS": {"node_version": ["16A"]}})
        self.assertRaises(NoNodesAvailable, self.pool.allocate_nodes, mock_profile)

    @patch('enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool._update_node_dict')
    @patch('enmutils_int.lib.node_pool_mgr.get_allocated_node_summary')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.error_profile_if_node_under_allocation')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_types', return_value=['ERBS', 'SGSN'])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.allocated_nodes', return_value=[])
    def test_allocate_nodes__node_filter_works_on_profiles_with_supported_types(self, *_):
        node_pool_mgr.cache = []
        unit_test_utils.add_nodes_to_pool(self.pool, 2)
        unit_test_utils.add_nodes_to_pool(self.pool, 2, primary_type='SGSN', node_version="16B")
        mock_profile = TestProfile(name="FM_01", total_nodes=2, supported_node_types=['ERBS', 'SGSN'],
                                   node_filter={"SGSN": {"node_version": ["16A"]}})
        self.pool.allocate_nodes(mock_profile)
        self.assertEqual(len(mock_profile.nodes['ERBS']), 2)
        self.assertEqual(len(mock_profile.nodes['SGSN']), 0)
        node_pool_mgr.cache = []

    @patch('enmutils.lib.persistence')
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.is_pre_allocated_to_profile', return_value=True)
    def test_node_filter_retains_pre_allocated_nodes_is_successful(self, *_):
        unit_test_utils.add_nodes_to_pool(self.pool, 5)
        profile = get_profile()
        nodes = get_nodes(5)
        nodes_filter = NodesFilter(profile, nodes, 'ERBS')
        retained_nodes = nodes_filter.execute()
        self.assertEqual(len(retained_nodes), 5)

    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter._filter_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter.__init__', return_value=None)
    def test_execute__for_node_filter_has_no_attribute_NAME(self, *_):
        profile = Mock()
        delattr(profile, "NAME")
        profile.NODE_FILTER = {"ERBS": "node1"}
        nodes = get_nodes(5)
        nodes_filter = NodesFilter(profile, nodes, "ERBS")
        nodes_filter.item = profile
        nodes_filter.nodes = ["TOP", "ABC", "BCD"]
        nodes_filter.node_type = "ERBS"
        retained_nodes = nodes_filter.execute()
        self.assertEqual(len(retained_nodes), 0)

    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.allocate_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.deallocate_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.log.logger.debug')
    def test_exchange_nodes__is_successful(self, mock_log, mock_deallocate, mock_allocate, *_):
        pool = node_pool_mgr.ProfilePool()
        pool.exchange_nodes("ENM")
        mock_deallocate.assert_called_with("ENM")
        mock_allocate.assert_called_with("ENM")
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_clear__successful(self, mock_db, *_):
        node_pool_mgr.Pool.key = 123
        node_pool_mgr.Pool.db = mock_db = Mock()
        pool = node_pool_mgr.Pool()
        pool.clear()
        mock_db.remove.assert_called_with(123)

    @patch('enmutils_int.lib.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.add')
    def test_add__success(self, mock_add, *_):
        path = "enm/path"
        node_pool_mgr.add(path)
        mock_add.assert_called_with(path)

    @patch('enmutils_int.lib.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.remove')
    def test_remove__successful(self, mock_remove, *_):
        node_pool_mgr.remove("TOP", end=None, force=None, start=None)
        mock_remove.assert_called_with("TOP", end=None, force=None, start=None)

    @patch('enmutils_int.lib.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.remove_all')
    def test_remove_all__success(self, mock_remove_all, *_):
        node_pool_mgr.remove_all(force=None)
        mock_remove_all.assert_called_with(force=None)

    @patch('enmutils_int.lib.node_pool_mgr.persistence')
    def test_has_node__successful(self, mock_persistence, *_):
        node_pool_mgr.has_node("node_id")
        mock_persistence.has_key.assert_called_with("node_id")

    @patch('enmutils_int.lib.node_pool_mgr.persistence')
    def test_get_node__successful(self, mock_persistence, *_):
        node_pool_mgr.get_node("node_id")
        mock_persistence.get.assert_called_with("node_id")

    @patch('enmutils.lib.persistence')
    def test_update_node_dict_updates_correctly(self, *_):
        test_key = 'UnitTestKey'
        NODE_CLASS_MAP.update({test_key: []})
        self.pool._update_node_dict()
        self.assertTrue(set(self.pool._nodes.keys()).issubset(NODE_CLASS_MAP.keys()))
        self.assertIn(test_key, self.pool._nodes.keys())

    @patch('enmutils.lib.persistence')
    def test_distribute_nodes(self, *_):
        num_nodes = 2
        nodes = [ERBSNode() for _ in range(3)]
        nodes[0].node_id = "LTE01"
        nodes[1].node_id = "LTE02"
        nodes[2].node_id = "LTE03"
        nodes[0].netsim = "LTE01"
        nodes[1].netsim = "LTE01"
        nodes[2].netsim = "LTE03"
        self.assertEqual([nodes[1]] + [nodes[2]], node_pool_mgr.distribute_nodes(nodes, num_nodes))

    @patch('enmutils.lib.persistence')
    def test_distribute_nodes_returns_successfully_if_too_few_nodes(self, *_):
        num_nodes = 2
        nodes = [ERBSNode()]
        nodes[0].node_id = "LTE01"
        nodes[0].netsim = "LTE01"
        self.assertEqual(1, len(node_pool_mgr.distribute_nodes(nodes, num_nodes)))

    @patch('enmutils_int.lib.node_pool_mgr.group_nodes_per_netsim_host')
    def test_distribute_nodes__returns_successfully_if_no_key(self, mock_group, *_):
        num_nodes = 1
        nodes = ["ABC", "BCD", "CDE"]
        mock_group.return_value = {"node1": "", "node2": ["enode"]}
        assigned_nodes = node_pool_mgr.distribute_nodes(nodes, num_nodes)
        self.assertEqual(1, len(assigned_nodes))

    @patch('enmutils_int.lib.node_pool_mgr.get_pool')
    @patch('enmutils_int.lib.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.persist')
    @patch('enmutils_int.lib.load_node.ERBSLoadNode._persist')
    def test_individually_allocate_node_to_profile(self, *_):
        node = Mock()
        node.profiles = ["Test_01"]
        node_pool_mgr.individually_allocate_node_to_profile("Test_01", node)
        node.profiles = []
        node_pool_mgr.individually_allocate_node_to_profile("Test_01", node)

    @patch('enmutils.lib.log.logger.debug')
    def test_get_num_required_nodes(self, mock_debug, *_):
        profile = Mock(NAME="TEST_01", MAX_NODES_TO_ALLOCATE=10)
        self.assertEqual(10, self.pool.get_num_required_nodes(profile))
        mock_debug.assert_called_with("Number of nodes required by TEST_01 (based upon profile attributes): 10")

        delattr(profile, "MAX_NODES_TO_ALLOCATE")
        profile.TOTAL_NODES = 5
        self.assertEqual(5, self.pool.get_num_required_nodes(profile))

        delattr(profile, "TOTAL_NODES")
        profile.NODES = {"ERBS": 3}
        self.assertEqual(3, self.pool.get_num_required_nodes(profile))

        delattr(profile, "NODES")
        profile.NUM_NODES = {"ERBS": 2, "RadioNode": 2}
        self.assertEqual(4, self.pool.get_num_required_nodes(profile))

    def test_calculate_total_nodes(self, *_):
        profile = Mock()
        profile.MAX_NODES_TO_ALLOCATE = 10
        self.assertEqual(10, self.pool.calculate_total_nodes(-1, profile, "BSC", {}))
        delattr(profile, "MAX_NODES_TO_ALLOCATE")
        delattr(profile, "TOTAL_NODES")
        profile.NUM_NODES = {"BSC": -1}
        self.assertEqual(2, self.pool.calculate_total_nodes(-1, profile, "BSC", {"BSC": ["Node"] * 2}))

    def test_node_filter_nodes_per_host_multi_nes(self, *_):
        profile = Mock()
        profile.MAX_NODES = 10
        profile.NODES_PER_HOST = 2
        profile.NAME = "SHM_27"

        node = Mock(primary_type="SIU02", netsim="01")
        node1 = Mock(primary_type="SIU02", netsim="01")
        node2 = Mock(primary_type="SIU02", netsim="01")
        node3 = Mock(primary_type="SIU02", netsim="02")
        node4 = Mock(primary_type="SIU02", netsim="03")
        node5 = Mock(primary_type="SIU02", netsim="03")
        node22 = Mock(primary_type="TCU02", netsim="011")
        node12 = Mock(primary_type="TCU02", netsim="011")
        node23 = Mock(primary_type="TCU02", netsim="011")
        node33 = Mock(primary_type="TCU02", netsim="021")
        node43 = Mock(primary_type="TCU02", netsim="03")
        nodes = [node, node1, node2, node3, node4, node5, node22, node12, node23, node33, node43]
        nodes_filter = NodesFilter(profile, nodes, 'SIU02')
        retained_nodes = nodes_filter._filter_nodes_per_netsim_host(nodes)
        self.assertEqual(len(retained_nodes), 8)

    @patch('enmutils_int.lib.load_node.LoadNodeMixin.is_available_for')
    def test_filter_nodes__when_me_type_nodes_percentage_value_is_empty(self, mock_avaialable, *_):
        profile = Mock()
        profile.MAX_NODES = 10
        profile.NODES_PER_HOST = 2
        profile.NAME = "SHM_05"
        profile.ME_TYPE_NODES_PERCENTAGE = {}

        node = radionode(node_ip=generate_configurable_ip(), primary_type='RadioNode', managed_element_type="ENodeB",
                         model_identity="-")
        node1 = radionode(node_ip=generate_configurable_ip(ipversion=6), primary_type='RadioNode',
                          managed_element_type="ENodeB", model_identity="ABC")
        node2 = radionode(node_ip=generate_configurable_ip(), primary_type='RadioNode',
                          managed_element_type="ENodeB", model_identity="ABC")
        node.is_available_for = mock_avaialable
        node1.is_available_for = mock_avaialable
        node2.is_available_for = mock_avaialable
        nodes = [node, node1, node2, node1, node2, node1, node, node1, node2, node, node2]
        nodes_filter = NodesFilter(profile, nodes, 'SIU02')
        nodes = nodes_filter._filter_nodes({'node_ip': ':', 'managed_element_type': ["ENodeB"],
                                            'model_identity': ['', '-'], 'no_variable': ""})
        self.assertEqual(len(nodes), 4)

    @patch('enmutils_int.lib.load_node.LoadNodeMixin.is_available_for')
    def test_filter_nodes__when_me_type_nodes_percentage_value_is_not_empty(self, mock_avaialable, *_):
        profile = Mock()
        profile.MAX_NODES = 10
        profile.NUM_NODES = {'RadioNode': 20}
        profile.NODES_PER_HOST = 2
        profile.NAME = "SHM_05"
        profile.ME_TYPE_NODES_PERCENTAGE = {"ENodeB": 10, "GNodeB": 90}

        node = radionode(node_ip=generate_configurable_ip(), primary_type='RadioNode', managed_element_type="ENodeB",
                         model_identity="-")
        node1 = radionode(node_ip=generate_configurable_ip(ipversion=6), primary_type='RadioNode',
                          managed_element_type="ENodeB", model_identity="ABC")
        node2 = radionode(node_ip=generate_configurable_ip(), primary_type='RadioNode',
                          managed_element_type="ENodeB", model_identity="ABC")
        node.is_available_for = mock_avaialable
        node1.is_available_for = mock_avaialable
        node2.is_available_for = mock_avaialable
        nodes = [node, node1, node2, node1, node2, node1, node, node1, node2, node, node2]
        nodes_filter = NodesFilter(profile, nodes, 'SIU02')
        nodes = nodes_filter._filter_nodes({'node_ip': ':', 'managed_element_type': ["ENodeB"],
                                            'model_identity': ['', '-'], 'no_variable': ""})
        self.assertEqual(len(nodes), 2)

    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter.fill_ne_type_requirement', return_value=[])
    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter._sort_by_host_and_ne_type')
    def test_sort_by_host_evenly_adds_exception(self, mock_sort, *_):
        profile = Mock()
        profile.MAX_NODES = 100
        profile.NODES_PER_HOST = 2
        node, node1 = Mock(), Mock()
        node.primary_type, node1.primary_type = "SIU02", "TCU02"
        nodes_filter = NodesFilter(profile, [], '')
        mock_sort.return_value = {"host": {"SIU02": [node], "TCU02": [node1]}}
        nodes_filter.sort_by_host_evenly({})
        self.assertEqual(profile.add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter._sort_by_host_and_ne_type')
    def test_sort_by_host_evenly(self, mock_sort, *_):
        profile = Mock()
        profile.MAX_NODES = 2
        profile.NODES_PER_HOST = 2
        node, node1 = Mock(), Mock()
        node.primary_type, node1.primary_type = "SIU02", "TCU02"
        nodes_filter = NodesFilter(profile, [], '')
        mock_sort.return_value = {"host1": {"SIU02": [node]}, "host": {"TCU02": [node1]}}
        nodes_filter.sort_by_host_evenly({})
        self.assertEqual(profile.add_error_as_exception.call_count, 0)

    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter.balance_siu_tcu_indexes')
    def test_fill_ne_type_requirement_all_nodes_allocated(self, mock_balance, *_):
        profile = Mock()
        profile.MAX_NODES = 4
        profile.NODES_PER_HOST = 2
        node, node1 = Mock(), Mock()
        node.primary_type, node1.primary_type = "SIU02", "TCU02"
        nodes = [node] * 2 + [node1] * 2
        unused_nodes = {"host1": {"SIU02": [node], "TCU02": [node]}, "host": {"SIU02": [node], "TCU02": [node1]}}
        nodes_filter = NodesFilter(profile, [], '')
        nodes_filter.fill_ne_type_requirement(unused_nodes, 2, nodes)
        self.assertEqual(0, mock_balance.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter.extend_filtered_list', return_value=(0, 0, []))
    def test_fill_ne_type_requirement_available_in_first_host(self, mock_extend, *_):
        profile = Mock()
        profile.MAX_NODES = 10
        profile.NODES_PER_HOST = 2
        node, node1 = Mock(), Mock()
        node.primary_type, node1.primary_type = "SIU02", "TCU02"
        nodes = [node] * 4 + [node1] * 4
        unused_nodes = {"host1": {"SIU02": [node], "TCU02": [node]}}
        nodes_filter = NodesFilter(profile, [], '')
        nodes_filter.fill_ne_type_requirement(unused_nodes, 5, nodes)
        self.assertEqual(1, mock_extend.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter.balance_siu_tcu_indexes', return_value=(0, 2, ["Node"]))
    def test_fill_ne_type_requirement_balance_nodes(self, mock_balance, *_):
        profile = Mock()
        profile.MAX_NODES = 10
        profile.NODES_PER_HOST = 2
        node, node1 = Mock(), Mock()
        node.primary_type, node1.primary_type = "SIU02", "TCU02"
        nodes = [node] * 1 + [node1] * 4
        unused_nodes = {"host1": {"SIU02": [node], "TCU02": [node]}, "host": {"SIU02": [node, node], "TCU02": [node]}}
        nodes_filter = NodesFilter(profile, [], '')
        nodes_filter.fill_ne_type_requirement(unused_nodes, 5, nodes)
        self.assertEqual(1, mock_balance.call_count)

    def test_extend_filtered_list(self, *_):
        unused_nodes = {"host": {"SIU02": ["node"], "TCU02": ["node1"]}}
        available = ["node2"]
        profile = Mock()
        nodes_filter = NodesFilter(profile, [], '')
        siu_required, tcu_required, nodes = nodes_filter.extend_filtered_list((1, 1), ["SIU02", "TCU02"], "host",
                                                                              unused_nodes, available)
        self.assertEqual(["node", "node1", "node2"], sorted(nodes))
        self.assertEqual(siu_required, tcu_required, 0)
        available = ["node2"]
        siu_required, tcu_required, nodes = nodes_filter.extend_filtered_list((3, 3), ["SIU02"], "host", unused_nodes,
                                                                              available, index=1)
        self.assertEqual(["node", "node2"], sorted(nodes))
        self.assertEqual(siu_required, 2)
        self.assertEqual(tcu_required, 3)

        available = ["node2"]
        siu_required, tcu_required, nodes = nodes_filter.extend_filtered_list((2, 1), ["SIU02", "TCU02"], "host",
                                                                              unused_nodes, available, index=1)
        self.assertEqual(["node", "node1", "node2"], sorted(nodes))
        self.assertEqual(siu_required, 1)
        self.assertEqual(tcu_required, 0)

    def test_balance_siu_tcu_indexes(self, *_):
        profile = Mock()
        profile.NODES_PER_HOST = 100
        nodes_filter = NodesFilter(profile, [], '')
        siu_required, tcu_required, nodes = nodes_filter.balance_siu_tcu_indexes(
            (45, 155, 50), ["SIU02", "TCU02"], "host", {"host": {"SIU02": ["node"], "TCU02": ["node1"]}}, ["node2"])
        self.assertEqual(["node", "node1", "node2"], sorted(nodes))
        self.assertEqual(siu_required, 0)
        self.assertEqual(tcu_required, 100)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.add_filtered_node_types_in_message')
    @patch('enmutils_int.lib.node_pool_mgr.match_cardinality_requirements')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.remove_upgind_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.handle_backward_compatibility')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.determine_if_nodes_not_available', return_value='')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.determine_if_environ_warning_to_be_added_to_profile')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.node_dict', new_callable=PropertyMock,
           return_value={"SIU": {"node": "node"}})
    @patch('enmutils_int.lib.node_pool_mgr.NodesFilter.execute')
    def test_get_random_available_nodes_shm_27_no_nodes_filter(self, mock_execute, *_):
        profile = Mock()
        profile.NAME = "SHM_27"
        profile.CHECK_NODE_SYNC = False
        self.pool.get_random_available_nodes(profile, node_type="SIU")
        self.assertEqual(0, mock_execute.call_count)

    def test_determine_if_environ_warning_to_be_added_to_profile__profile_excluded(self, *_):
        profile = Mock()
        profile.NAME = "CMSYNC_02"
        self.pool.determine_if_environ_warning_to_be_added_to_profile("nodes available (1)", profile)
        self.assertEqual(0, profile.add_error_as_exception.call_count)

    def test_determine_if_environ_warning_to_be_added_to_profile__profile_included(self, *_):
        profile = Mock()
        profile.NAME = "CMSYNC_01"
        self.pool.determine_if_environ_warning_to_be_added_to_profile("nodes available (1)", profile)
        self.assertEqual(1, profile.add_error_as_exception.call_count)

    def test_determine_if_environ_warning_to_be_added_to_profile__fm_alarm_profiles(self, *_):
        profile = Mock()
        profile.NAME = "FM_01"
        self.pool.determine_if_environ_warning_to_be_added_to_profile("nodes available (1)", profile)
        self.assertEqual(0, profile.add_error_as_exception.call_count)

    def test_determine_if_environ_warning_to_be_added_to_profile__allowable_reached(self, *_):
        profile = Mock(MINIMUM_ALLOWABLE_NODE_COUNT=15)
        profile.NAME = "SHM_31"
        self.pool.determine_if_environ_warning_to_be_added_to_profile("nodes available (15)", profile)
        self.assertEqual(0, profile.add_error_as_exception.call_count)

    def test_determine_if_environ_warning_to_be_added_to_profile__allowable_not_reached(self, *_):
        profile = Mock(MINIMUM_ALLOWABLE_NODE_COUNT=16)
        profile.NAME = "SHM_31"
        self.pool.determine_if_environ_warning_to_be_added_to_profile("nodes available (15)", profile)
        self.assertEqual(1, profile.add_error_as_exception.call_count)

    def test_update_node_types(self, *_):
        profile = Mock(SUPPORTED_NODE_TYPES=["Router6672", "Router_6672"])
        nodes_dict = {"Router6672": [], "Router_6672": ["node"]}
        self.assertEqual(self.pool.update_node_types(profile, nodes_dict), ['Router_6672'])

    @patch('enmutils_int.lib.node_pool_mgr.get_workload_admin_user')
    @patch('enmutils_int.lib.node_pool_mgr.enm_node_management.CmManagement.get_status',
           return_value={Mock(node_id="LTE01"): "UNSYNCHRONIZED"})
    def test_validate_nodes_against_enm__checks_sync(self, *_):
        synced = self.pool.validate_nodes_against_enm()
        self.assertEqual(synced, ["LTE01"])

    @patch('enmutils_int.lib.node_pool_mgr.NODE_CLASS_MAP', return_value={"RadioNode": []})
    @patch('enmutils.lib.log.logger.debug')
    def test_update_node_dict__no_missing_keys(self, mock_debug, *_):
        self.pool._nodes = {"RadioNode": []}
        self.pool._update_node_dict()
        self.assertDictEqual({"RadioNode": []}, self.pool._nodes)
        self.assertEqual(2, mock_debug.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.ProfilePool.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.persistence.default_db', return_value={})
    def test_db_property__calls_persistence_default_db_on_base_pool(self, mock_default_db, *_):
        self.assertIsNotNone(self.pool.db)
        self.assertEqual(1, mock_default_db.call_count)

    def test_nodes__returns_cached_node_list_if_it_is_set(self, *_):
        node = Mock()
        node_pool_mgr.cached_nodes_list = [node]
        self.assertEqual(self.pool.nodes, [node])
        node_pool_mgr.cached_nodes_list = []

    @patch('enmutils_int.lib.node_pool_mgr.log.logger.debug')
    def test_update_cached_list_of_nodes__updates_cached_nodes_list(self, mock_debug, *_):
        node1_old = Mock(node_id="TEST_NODE1", profiles=["TEST_01"])
        node1_new = Mock(node_id="TEST_NODE1", profiles=["TEST_01", "TEST_02"])
        node2 = Mock(node_id="TEST_NODE2", profiles=["TEST_02"])
        node3 = Mock(node_id="TEST_NODE3", profiles=["TEST_03"])
        node_pool_mgr.cached_nodes_list = [node1_old, node2]

        node_pool_mgr.update_cached_list_of_nodes({"TEST_NODE1": node1_new, "TEST_NODE3": node3})
        self.assertEqual(node_pool_mgr.cached_nodes_list, [node1_new, node2, node3])
        self.assertTrue(call("Cache nodes: 3 (Total) 1 (Updated) 1 (Added)") in mock_debug.mock_calls)
        node_pool_mgr.cached_nodes_list = []

    def test_update_cached_list_of_nodes__does_nothing_if_cached_nodes_not_set(self, *_):
        node_pool_mgr.cached_nodes_list = []

        node_pool_mgr.update_cached_list_of_nodes({"TEST_NODE1": Mock(), "TEST_NODE2": Mock()})
        self.assertEqual(node_pool_mgr.cached_nodes_list, [])
        node_pool_mgr.cached_nodes_list = []


class NodePoolMgrUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes_list = get_nodes(2)
        Profile.NAME = "TEST"
        profile = CMImportProfile()
        profile.NAME = 'CMIMPORT_TEST'
        profile.MO_VALUES = {'RetSubUnit': 1, 'AntennaSubunit': 1}
        profile.TOTAL_NODES = 2
        profile.SUPPORTED_NODE_TYPES = ['ERBS', 'RadioNode']
        profile.BATCH_MO_SIZE = 1
        self.profile = profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.node_pool_mgr.persist_dict_value')
    @patch('enmutils_int.lib.node_pool_mgr.get_random_available_nodes', return_value=[])
    def test_allocate_nodes_with_mos_raises_no_nodes_error_if_no_nodes(self, *_):
        with self.assertRaises(NoNodesAvailable):
            node_pool_mgr.allocate_nodes_with_mos(self.profile)

    @patch('enmutils_int.lib.node_pool_mgr.persist_dict_value')
    @patch('enmutils_int.lib.node_pool_mgr.get_allocated_node_summary')
    @patch('enmutils_int.lib.node_pool_mgr.mutexer.mutex')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    @patch('enmutils_int.lib.node_pool_mgr.get_batch_nodes_with_mos')
    @patch('enmutils_int.lib.node_pool_mgr.get_random_available_nodes')
    def test_allocate_nodes_with_mos_is_successful(self, mock_get_nodes, mock_get_batch, mock_persistence_set,
                                                   mock_mutex, *_):
        mock_get_nodes.return_value = self.nodes_list
        mock_get_batch.return_value = self.nodes_list
        node_pool_mgr.allocate_nodes_with_mos(self.profile)
        self.assertTrue(mock_persistence_set.called)
        self.assertTrue(mock_mutex.called)

    @patch('enmutils_int.lib.node_pool_mgr.get_allocated_node_summary')
    @patch('enmutils_int.lib.node_pool_mgr.persist_dict_value')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    @patch('enmutils_int.lib.node_pool_mgr.get_batch_nodes_with_mos')
    @patch('enmutils_int.lib.node_pool_mgr.get_random_available_nodes')
    def test_allocate_nodes_with_mos_is_successful_supplied_values(self, mock_get_nodes, mock_get_batch,
                                                                   mock_persistence_set, *_):
        mock_get_nodes.return_value = self.nodes_list
        mock_get_batch.return_value = self.nodes_list
        profile = Mock()
        profile.NAME = "TEST_01"
        delattr(profile, 'MAX_NODES_TO_ALLOCATE')
        delattr(profile, 'LARGE_BSC_ONLY')
        delattr(profile, 'SMALL_BSC_ONLY')
        delattr(profile, 'CHECK_NODE_SYNC')
        delattr(profile, 'BSC_250_CELL')
        node_pool_mgr.allocate_nodes_with_mos(profile, supported_ne_types=["ERBS"], total_nodes=10)
        self.assertFalse(mock_persistence_set.called)

    @patch('enmutils_int.lib.node_pool_mgr.get_allocated_node_summary')
    @patch('enmutils_int.lib.node_pool_mgr.check_fetch_set_mos_to_persistence')
    @patch('enmutils_int.lib.node_pool_mgr.get_batch_nodes_with_mos')
    @patch('enmutils_int.lib.node_pool_mgr.get_random_available_nodes')
    def test_allocate_nodes_with_mos_is_successful_for_tranposrt_profile(self, mock_get_nodes, mock_get_batch, mock_get_allocated_node_summary, *_):
        mock_get_nodes.return_value = self.nodes_list
        mock_get_batch.return_value = self.nodes_list
        profile = Mock()
        profile.NAME = "CMIMPORT_25"
        delattr(profile, 'MAX_NODES_TO_ALLOCATE')
        delattr(profile, 'LARGE_BSC_ONLY')
        delattr(profile, 'SMALL_BSC_ONLY')
        delattr(profile, 'CHECK_NODE_SYNC')
        delattr(profile, 'BSC_250_CELL')
        node_pool_mgr.allocate_nodes_with_mos(profile, supported_ne_types=["ERBS"], total_nodes=10)
        self.assertTrue(mock_get_allocated_node_summary.called)

    @patch('enmutils_int.lib.node_pool_mgr.persist_dict_value')
    @patch('enmutils_int.lib.node_pool_mgr.mutexer.mutex')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.node_pool_mgr.get_allocated_node_summary')
    @patch('enmutils_int.lib.node_pool_mgr.get_batch_nodes_with_mos')
    @patch('enmutils_int.lib.node_pool_mgr.get_random_available_nodes')
    def test_allocate_nodes_with_mos_adds_profile_error(self, mock_get_nodes, mock_get_batch,
                                                        mock_get_allocated_node_summary, mock_add_error, *_):
        mock_get_nodes.return_value = self.nodes_list
        mock_get_batch.return_value = self.nodes_list
        self.profile.TOTAL_NODES = 5
        node_pool_mgr.allocate_nodes_with_mos(self.profile)
        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_get_allocated_node_summary.called)

    @patch('enmutils_int.lib.node_pool_mgr.persist_dict_value')
    @patch('enmutils_int.lib.node_pool_mgr.get_batch_nodes_with_mos')
    @patch('enmutils_int.lib.node_pool_mgr.get_random_available_nodes')
    def test_allocate_nodes_with_mos_raises_no_nodes_error_if_no_nodes_with_mos(self, mock_get_nodes, mock_get_batch,
                                                                                *_):
        mock_get_nodes.return_value = 'ERBS01'
        mock_get_batch.return_value = {}
        with self.assertRaises(NoNodesAvailable):
            node_pool_mgr.allocate_nodes_with_mos(self.profile)

    @patch('enmutils_int.lib.node_pool_mgr.persist_dict_value')
    @patch('enmutils.lib.log.logger.info')
    @patch('enmutils_int.lib.node_pool_mgr.get_batch_nodes_with_mos')
    @patch('enmutils_int.lib.node_pool_mgr.get_random_available_nodes')
    def test_allocate_nodes_with_mos_excepts_timeout_error_from_get_batch(self, mock_get_nodes, mock_get_batch,
                                                                          mock_info_logger, *_):
        mock_get_nodes.return_value = 'ERBS01'
        mock_get_batch.side_effect = TimeOutError
        with self.assertRaises(NoNodesAvailable):
            node_pool_mgr.allocate_nodes_with_mos(self.profile)
            self.assertTrue(mock_info_logger.called)

    def test_check_for_pcg_version__success(self):
        profile = Mock()
        setattr(profile, 'NAME', "CMIMPORT_26")
        node1 = Mock()
        setattr(node1, 'node_version', '1-17')
        node_pool_mgr.check_for_pcg_version(profile, [node1], {'predef': 1}, {'predef': ['action']})

    def test_check_for_pcg_version__no_available_nodes(self):
        profile = Mock()
        setattr(profile, 'NAME', "CMIMPORT_26")
        node_pool_mgr.check_for_pcg_version(profile, [], {'predef': 1}, {'predef': ['action']})

    def test_check_for_pcg_version__no_higher_version_pcg(self):
        profile = Mock()
        setattr(profile, 'NAME', "CMIMPORT_26")
        node1 = Mock()
        setattr(node1, 'node_version', '1')
        node2 = Mock()
        setattr(node2, 'node_version', '1-1')
        node_pool_mgr.check_for_pcg_version(profile, [node1, node2], {'predef': 1}, {'predef': ['action']})

    @patch('enmutils_int.lib.node_pool_mgr.get_nodes_mos')
    @patch('enmutils_int.lib.node_pool_mgr.get_mixed_nodes_mos')
    def test_determine_if_mixed_nodes_mos__detects_5g_nodes(self, mock_mixed_nodes, mock_get_nodes_mos):
        profile = Mock()
        node_pool_mgr.determine_if_mixed_nodes_mos("user", {}, [], profile)
        self.assertEqual(1, mock_mixed_nodes.call_count)
        self.assertEqual(0, mock_get_nodes_mos.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.get_nodes_mos')
    @patch('enmutils_int.lib.node_pool_mgr.get_mixed_nodes_mos')
    def test_determine_if_mixed_nodes_mos__no_5g_nodes(self, mock_mixed_nodes, mock_get_nodes_mos):
        node_pool_mgr.determine_if_mixed_nodes_mos("user", {}, [], "Profile")
        self.assertEqual(0, mock_mixed_nodes.call_count)
        self.assertEqual(1, mock_get_nodes_mos.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.get_nodes_mos')
    @patch('enmutils_int.lib.node_pool_mgr.create_gnodeb_mo_dict_and_attrs')
    def test_get_mixed_nodes_mos__alters_node_mos_and_attrs(self, mock_create_mos_attrs, mock_get_mos):
        mo_dict = {"MO": 1, "MO1": 2}
        profile = Mock()
        profile.MAPPING_FOR_5G_NODE_MO = {"MO": {"MO2": 3}, "MO1": {"MO3": 4}}
        attrs = {'MO': ['attr'], 'MO1': ['attr1']}
        node = Mock(managed_element_type="ENodeB")
        node1 = Mock(managed_element_type="GNodeB")
        mock_create_mos_attrs.return_value = ({'MO3': 2, 'MO2': 1}, {'MO2': ['attr'], 'MO3': ['attr1']})
        node_pool_mgr.get_mixed_nodes_mos("user", mo_dict, [node, node1], profile, attrs)
        self.assertDictEqual({'MO3': ['attr1'], 'MO2': ['attr']}, mock_get_mos._mock_call_args_list[0][1].get("attrs"))
        self.assertDictEqual({'MO1': ['attr1'], 'MO': ['attr']}, mock_get_mos._mock_call_args_list[1][1].get("attrs"))

    @patch('enmutils_int.lib.node_pool_mgr.get_nodes_mos')
    @patch('enmutils_int.lib.node_pool_mgr.create_gnodeb_mo_dict_and_attrs')
    def test_get_mixed_nodes_mos__no_alteration_required(self, mock_create_mos_attrs, mock_get_mos):
        mo_dict = {"MO": 1, "MO1": 2}
        profile = Mock()
        profile.MAPPING_FOR_5G_NODE_MO = {"MO": {"MO2": 3}, "MO1": {"MO3": 4}}
        attrs = {'MO': ['attr'], 'MO1': ['attr1']}
        node = Mock(managed_element_type="ENodeB")
        node1 = Mock(managed_element_type="ENodeB")
        node_pool_mgr.get_mixed_nodes_mos("user", mo_dict, [node, node1], profile, attrs)
        self.assertDictEqual({'MO1': ['attr1'], 'MO': ['attr']}, mock_get_mos._mock_call_args_list[0][1].get("attrs"))
        self.assertEqual(0, mock_create_mos_attrs.call_count)

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.node_pool_mgr.get_nodes_mos')
    @patch('enmutils_int.lib.node_pool_mgr.create_gnodeb_mo_dict_and_attrs')
    def test_get_mixed_nodes_mos__logs_exception(self, mock_create_mos_attrs, mock_get_mos, mock_debug):
        mo_dict = {"MO": 1, "MO1": 2}
        profile = Mock()
        profile.MAPPING_FOR_5G_NODE_MO = {"MO": {"MO2": 3}, "MO1": {"MO3": 4}}
        attrs = {'MO': ['attr'], 'MO1': ['attr1']}
        node = Mock(managed_element_type="ENodeB")
        mock_get_mos.side_effect = Exception("Error")
        node_pool_mgr.get_mixed_nodes_mos("user", mo_dict, [node], profile, attrs)
        self.assertEqual(0, mock_create_mos_attrs.call_count)
        mock_debug.assert_called_with("Error")
        self.assertEqual(1, mock_debug.call_count)

    def test_create_gnodeb_mo_dict_and_attrs__correctly_alters_mos(self):
        mo_dict = {"MO": 1, "MO1": 2, "MO4": 1}
        profile = Mock()
        profile.MAPPING_FOR_5G_NODE_MO = {"MO": {"MO2": 3}, "MO1": {"MO3": 4}}
        update_mo_dict, update_mo_attrs = node_pool_mgr.create_gnodeb_mo_dict_and_attrs(mo_dict, {}, profile)
        self.assertEqual(None, update_mo_attrs)
        self.assertDictEqual(update_mo_dict, {'MO3': 4, 'MO2': 3})

    def test_create_gnodeb_mo_dict_and_attrs__correctly_alters_attrs(self):
        mo_dict = {"MO": 1}
        attrs = {'MO': ['attr'], "MO2": ['attr1']}
        profile = Mock()
        profile.MAPPING_FOR_5G_NODE_MO = {"MO": {"MO2": 1}, "MO1": {"MO3": 1}}
        profile.MAPPING_FOR_5G_NODE_ATTRS = {"MO2": ['attr3'], "MO3": ['attr4']}
        update_mo_dict, update_mo_attrs = node_pool_mgr.create_gnodeb_mo_dict_and_attrs(mo_dict, attrs, profile)
        self.assertEqual({'MO2': ['attr3']}, update_mo_attrs)
        self.assertDictEqual(update_mo_dict, {'MO2': 1})

    @patch('enmutils_int.lib.node_pool_mgr.get_mos_and_allocate_nodes', side_effect=(["node"], ["node", "node1"]))
    def test_get_batch_nodes_with_mos__success(self, mock_get_mos):
        node_pool_mgr.get_batch_nodes_with_mos("profile", {"MO": 1}, ["node", "node1"] * 3, user="user", batch_size=3,
                                               fail_on_empty_response=True, num_nodes_needed=2)
        self.assertEqual(2, mock_get_mos.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.get_mos_and_allocate_nodes', return_value=[])
    def test_get_batch_nodes_with_mos__raises_no_nodes_available(self, mock_get_mos):
        self.assertRaises(NoNodesAvailable, node_pool_mgr.get_batch_nodes_with_mos, "profile", {"MO": 1}, ["node"] * 3,
                          user="user", batch_size=4, fail_on_empty_response=True, num_nodes_needed=2)
        self.assertEqual(1, mock_get_mos.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.get_mos_and_allocate_nodes', return_value=[])
    def test_get_batch_nodes_with_mos___fail_on_empty_response_false(self, mock_get_mos):
        node_pool_mgr.get_batch_nodes_with_mos("profile", {"MO": 1}, ["node"] * 3, user="user", batch_size=4,
                                               num_nodes_needed=2)
        self.assertEqual(1, mock_get_mos.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.get_mos_and_allocate_nodes', side_effect=[TimeOutError("Error")])
    def test_get_batch_nodes_with_mos___returns_some_nodes_if_timeout_reached(self, _):
        nodes = node_pool_mgr.get_batch_nodes_with_mos("profile", {"MO": 1}, ["node"] * 3, user="user", batch_size=4,
                                                       num_nodes_needed=2)
        self.assertIsInstance(nodes, list)

    @patch('enmutils_int.lib.node_pool_mgr.allocate_batch_mo_node')
    @patch('enmutils_int.lib.node_pool_mgr.determine_if_mixed_nodes_mos')
    def test_get_mos_and_allocate_nodes__allocates_available_node(self, mock_check_mixed_nodes, mock_allocate):
        mo_dict, attrs, profile = {"MO": 1}, None, "profile"
        mo_values = (mo_dict, attrs, profile)
        node = Mock()
        node.is_avaialble_for.return_value = True
        timeout, timeout_mins, now = 10, 1, 5
        timeout_values = (timeout, timeout_mins, now)
        mock_check_mixed_nodes.return_value = [node]
        node_pool_mgr.get_mos_and_allocate_nodes(timeout_values, "user", mo_values, [node], [], 10, True)
        self.assertEqual(1, mock_check_mixed_nodes.call_count)
        self.assertEqual(1, mock_allocate.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.allocate_batch_mo_node')
    @patch('enmutils_int.lib.node_pool_mgr.determine_if_mixed_nodes_mos')
    def test_get_mos_and_allocate_nodes__does_not_allocate_if_requirement_met(self, mock_check_mixed_nodes,
                                                                              mock_allocate):
        mo_dict, attrs, profile = {"MO": 1}, None, "profile"
        mo_values = (mo_dict, attrs, profile)
        node = Mock()
        node.is_avaialble_for.return_value = True
        timeout, timeout_mins, now = 10, 1, 5
        timeout_values = (timeout, timeout_mins, now)
        mock_check_mixed_nodes.return_value = [node]
        node_pool_mgr.get_mos_and_allocate_nodes(timeout_values, "user", mo_values, [node], [node], 1, True)
        self.assertEqual(1, mock_check_mixed_nodes.call_count)
        self.assertEqual(0, mock_allocate.call_count)

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.node_pool_mgr.allocate_batch_mo_node')
    @patch('enmutils_int.lib.node_pool_mgr.determine_if_mixed_nodes_mos',
           side_effect=NoOuputFromScriptEngineResponseError("Error", response=Mock()))
    def test_get_mos_and_allocate_nodes__logs_output_error(self, mock_check_mixed_nodes, mock_allocate, mock_debug):
        mo_dict, attrs, profile = {"MO": 1}, None, "profile"
        mo_values = (mo_dict, attrs, profile)
        node = Mock()
        node.is_avaialble_for.return_value = True
        timeout, timeout_mins, now = 10, 1, 5
        timeout_values = (timeout, timeout_mins, now)
        node_pool_mgr.get_mos_and_allocate_nodes(timeout_values, "user", mo_values, [node], [], 10, True)
        self.assertEqual(1, mock_check_mixed_nodes.call_count)
        self.assertEqual(0, mock_allocate.call_count)
        mock_debug.assert_called_with("Error")

    @patch('enmutils_int.lib.node_pool_mgr.allocate_batch_mo_node')
    @patch('enmutils_int.lib.node_pool_mgr.determine_if_mixed_nodes_mos')
    def test_get_mos_and_allocate_nodes__raises_timeout_error(self, mock_check_mixed_nodes, mock_allocate):
        mo_dict, attrs, profile = {"MO": 1}, None, "profile"
        mo_values = (mo_dict, attrs, profile)
        node = Mock()
        node.is_avaialble_for.return_value = True
        timeout, timeout_mins, now = 5, 1, 6
        timeout_values = (timeout, timeout_mins, now)
        mock_check_mixed_nodes.return_value = [node]
        self.assertRaises(TimeOutError, node_pool_mgr.get_mos_and_allocate_nodes, timeout_values, "user", mo_values,
                          [node], [], 10, True)
        self.assertEqual(0, mock_check_mixed_nodes.call_count)
        self.assertEqual(0, mock_allocate.call_count)

    def test_allocate_batch_mo_node__adds_allocated_nodes_to_nodes_list(self):
        node = Mock()
        profile = Mock()
        node_pool_mgr.allocate_batch_mo_node(node, profile)
        self.assertEqual(1, node.add_profile.call_count)

    def test_allocate_batch_mo_node__already_added_node(self):
        node = Mock()
        profile = Mock()
        node.add_profile.side_effect = AddProfileToNodeError("Error")
        added_node = node_pool_mgr.allocate_batch_mo_node(node, profile)
        self.assertEqual(added_node, node)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    @patch('enmutils_int.lib.node_pool_mgr.fetch_and_build_mos_dict')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get')
    def test_check_fetch_set_mos_to_persistence__unsuccessful_with_some_attrs(self, mock_db_output, *_):
        mock_db_output.return_value = {'CORE22ML6691-1-5-11': {('ManagedElement', 'CORE22ML6691-1-5-11'): {(u'Transport', u'1'): {(u'NetworkInstances', u'1')}}}}
        node_pool_mgr.check_fetch_set_mos_to_persistence(self.profile, {"MO": 1}, ["node", "node1"] * 3, {"MO2": 1}, user='user')

    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    @patch('enmutils_int.lib.node_pool_mgr.fetch_and_build_mos_dict')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get')
    def test_check_fetch_set_mos_to_persistence__successful_with_attrs(self, mock_db_output, *_):
        mock_db_output.return_value = {'CORE22ML6691-1-5-11': {('ManagedElement', 'CORE22ML6691-1-5-11'): {(u'Transport', u'1'): {(u'NetworkInstances', u'1')}}}}
        node_pool_mgr.check_fetch_set_mos_to_persistence(self.profile, {"MO": 1}, ["node", "node1"] * 3, {"MO2": 1}, user='user')

    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    @patch('enmutils_int.lib.node_pool_mgr.fetch_and_build_mos_dict')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get')
    def test_check_fetch_set_mos_to_persistence__successful_for_no_attrs(self, mock_db_output, *_):
        mock_db_output.return_value = {'CORE22ML6691-1-5-11': {('ManagedElement', 'CORE22ML6691-1-5-11'): {}}}
        node_pool_mgr.check_fetch_set_mos_to_persistence(self.profile, {"MO": 1}, ["node", "node1"] * 3, {"MO2": 1}, user='user')

    @patch('enmutils_int.lib.node_pool_mgr.EnmMo.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    def test_fetch_and_build_mos_dict_no_subnetwork(self, mock_get_fdn, mock_enm_mo):
        mock_get_fdn.return_value = ([u'FDN : GeranCell=0,GeranCellRelation=173020C',
                                      u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimG,'
                                      u'MeContext=GSM02BSC02,ManagedElement=GSM02BSC02,'
                                      u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=173027O,GeranCellRelation=173024C',
                                      u'', u'04 instance(s)'], None)
        node, user, = Mock(), Mock()
        node.node_id, node.ROOT_ELEMENT = "GSM02BSC02", "GSM"
        node_pool_mgr.fetch_and_build_mos_dict(user, {}, [node, node], ignore_mo_val="173024C", profile=Mock())
        self.assertEqual(0, mock_enm_mo.call_count)

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    def test_fetch_and_build_mos_dict_returns_valid_node_objects(self, mock_fetch_build_mos, _):
        response_output = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1, ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1']
        mock_fetch_build_mos.return_value = [response_output, None]
        node_pool_mgr.fetch_and_build_mos_dict(user=self.user, mo_values={'TermPointToENB': 1}, nodes=self.nodes_list,
                                               profile=Mock())

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    def test_fetch_and_build_mos_dict__returns_valid_node_objects_with_any_number_mos(self, mock_fetch_build_mos, _):
        response_output = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1, ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=1', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=CMSYNC01,TermPointToENB2=2', u'',
                           u'FDN : ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=3']
        mock_fetch_build_mos.return_value = [response_output, None]
        node_pool_mgr.fetch_and_build_mos_dict(user=self.user, mo_values={'TermPointToENB': 2, 'TermPointToENB2': 1},
                                               nodes=self.nodes_list, profile=Mock())

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    def test_fetch_and_build_mos_dict__skips_eutranfreqrelation_beginning_with_e(self, mock_fetch_build_mos, *_):
        response_output = [u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE32dg'
                           u'2ERBS00057,ENodeBFunction=1,EUtranCellTDD=LTE32dg2ERBS00057-1,EUtranFreqRelation=E55940']
        mock_fetch_build_mos.return_value = [response_output, None]
        nodes = node_pool_mgr.fetch_and_build_mos_dict(user=self.user, mo_values={'EUtranFreqRelation': 2},
                                                       nodes=self.nodes_list, profile=Mock())
        self.assertDictEqual({}, nodes)

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    def test_fetch_and_build_mos_dict_returns_valid_node_objects_with_some_number_mos(self, mock_fetch_build_mos, _):
        response_output = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1, ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=1', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=2', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=3']
        mock_fetch_build_mos.return_value = [response_output, None]
        node_pool_mgr.fetch_and_build_mos_dict(user=self.user, mo_values={'TermPointToENB': 2, 'TermPointToENB2': 1},
                                               nodes=self.nodes_list, profile=Mock())

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    def test_fetch_and_build_mos_dictreturns_valid_node_objects_with_exact_number_mos(self, mock_fetch_build_mos, _):
        response_output = [
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1, ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=1', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=2', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=3']
        mock_fetch_build_mos.return_value = [response_output, None]
        node_pool_mgr.fetch_and_build_mos_dict(user=self.user, mo_values={'TermPointToENB': 2, 'TermPointToENB2': 1},
                                               nodes=self.nodes_list, profile=Mock())

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    @patch('enmutils_int.lib.node_pool_mgr.get_filtered_nodes', return_value=[])
    def test_get_nodes_mos_returns_valid_node_objects(self, mock_filtered_nodes, mock_get_mos, _):
        response_output = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1, ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1']
        mock_get_mos.return_value = [response_output, None]
        node_pool_mgr.get_nodes_mos(user=self.user, mos_dict={'TermPointToENB': 1}, nodes=self.nodes_list,
                                    profile=Mock())
        self.assertIn('exact', mock_filtered_nodes.call_args[0][1])
        self.assertDictEqual(mock_filtered_nodes.call_args[0][2], {'TermPointToENB': 1})

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    @patch('enmutils_int.lib.node_pool_mgr.get_filtered_nodes', return_value=[])
    def test_get_nodes_mos__returns_valid_node_objects_with_any_number_mos(self, mock_filtered_nodes, mock_get_mos, _):
        response_output = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1, ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=1', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=CMSYNC01,TermPointToENB2=2', u'',
                           u'FDN : ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=3']
        mock_get_mos.return_value = [response_output, None]
        node_pool_mgr.get_nodes_mos(user=self.user, mos_dict={'TermPointToENB': 2, 'TermPointToENB2': 1},
                                    match_number_mos='any', nodes=self.nodes_list, profile=Mock())
        self.assertIn('any', mock_filtered_nodes.call_args[0][1])
        self.assertDictEqual(mock_filtered_nodes.call_args[0][2], {'TermPointToENB': 2, 'TermPointToENB2': 1})

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_filtered_nodes', return_value=[])
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    def test_get_nodes_mos__skips_eutranfreqrelation_beginning_with_e(self, mock_get_mos, *_):
        response_output = [u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE32dg'
                           u'2ERBS00057,ENodeBFunction=1,EUtranCellTDD=LTE32dg2ERBS00057-1,EUtranFreqRelation=E55940']
        mock_get_mos.return_value = [response_output, None]
        nodes = node_pool_mgr.get_nodes_mos(user=self.user, mos_dict={'EUtranFreqRelation': 2}, match_number_mos='any',
                                            nodes=self.nodes_list, profile=Mock())
        self.assertListEqual([], nodes)

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    @patch('enmutils_int.lib.node_pool_mgr.get_filtered_nodes', return_value=[])
    def test_get_nodes_mos_returns_valid_node_objects_with_some_number_mos(self, mock_filtered_nodes, mock_get_mos, _):
        response_output = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1, ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=1', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=2', u'',
                           u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=3']
        mock_get_mos.return_value = [response_output, None]
        node_pool_mgr.get_nodes_mos(user=self.user, mos_dict={'TermPointToENB': 2, 'TermPointToENB2': 1},
                                    match_number_mos='some', nodes=self.nodes_list, profile=Mock())
        self.assertIn('some', mock_filtered_nodes.call_args[0][1])
        self.assertDictEqual(mock_filtered_nodes.call_args[0][2], {'TermPointToENB2': 1, 'TermPointToENB': 2})

    @patch('time.sleep')
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    @patch('enmutils_int.lib.node_pool_mgr.get_filtered_nodes', return_value=[])
    def test_get_nodes_mos_returns_valid_node_objects_with_exact_number_mos(self, mock_filtered_nodes, mock_get_mos, _):
        response_output = [
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1, ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB=1',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=1', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=2', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,'
            u'EUtraNetwork=1,ExternalENodeBFunction=LTE1,TermPointToENB2=3']
        mock_get_mos.return_value = [response_output, None]
        node_pool_mgr.get_nodes_mos(user=self.user, mos_dict={'TermPointToENB': 2, 'TermPointToENB2': 1},
                                    match_number_mos='exact', nodes=self.nodes_list, profile=Mock())
        self.assertIn('exact', mock_filtered_nodes.call_args[0][1])
        self.assertDictEqual(mock_filtered_nodes.call_args[0][2], {'TermPointToENB2': 1, 'TermPointToENB': 2})

    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_ids')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.allocated_nodes')
    def test_get_allocated_node_summary_is_successful(self, mock_allocated_nodes, _):
        node_pool_mgr.get_allocated_node_summary(self.profile)
        self.assertTrue(mock_allocated_nodes.called)

    @patch('enmutils_int.lib.node_pool_mgr.network_mo_info.group_mos_by_node')
    @patch('enmutils_int.lib.node_pool_mgr.get_workload_admin_user')
    def test_generate_cell_dict(self, mock_get_or_create_admin_user, mock_group_mos_by_node):
        response = Mock()
        expected = {'LARGE_BSC': set(['BSC01']), "TDD": set(["netsim_LTE09ERBS00001"]),
                    "FDD": set(["netsim_LTE08ERBS00001"]), "SMALL_BSC": set(['BSC02', 'BSC04']),
                    "BSC_250_CELL": set(['BSC02'])}
        response.get_output.return_value = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE08ERBS00001,'
                                            u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE08ERBS00001-1',
                                            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE09ERBS00001,'
                                            u'ManagedElement=1,ENodeBFunction=1,EUtranCellTDD=LTE09ERBS00001-1',
                                            u'', u'', u'2 instance(s)']
        mock_get_or_create_admin_user.return_value.enm_execute.return_value = response
        mock_group_mos_by_node.return_value = {
            'netsim_LTE08ERBS00001': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE08ERBS00001,ManagedElement=1,'
                                      u'ENodeBFunction=1,EUtranCellFDD=LTE08ERBS00001-1'],
            'netsim_LTE09ERBS00001': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE09ERBS00001,ManagedElement=1,'
                                      u'ENodeBFunction=1,EUtranCellTDD=LTE09ERBS00001-1'],
            'BSC01': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=BSC01,ManagedElement=1,BSCm=1,GeranCell=123456'] * 2000,
            'BSC02': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=BSC02,ManagedElement=1,BSCm=1,GeranCell=123456'] * 250,
            'BSC03': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=BSC02,ManagedElement=1,BSCm=1,GeranCell=123456'] * 500,
            'BSC04': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=BSC02,ManagedElement=1,BSCm=1,GeranCell=123456'] * 100
        }
        self.assertDictEqual(node_pool_mgr.generate_cell_dict('LARGE_BSC'), expected)

    @patch('enmutils_int.lib.node_pool_mgr.get_workload_admin_user')
    def test_generate_cell_dict_no_output(self, mock_get_or_create_admin_user):
        response = Mock()
        expected = {"TDD": set([]), "FDD": set([]), "LARGE_BSC": set([]), "SMALL_BSC": set([]), "BSC_250_CELL": set([])}
        response.get_output.return_value = None
        mock_get_or_create_admin_user.return_value.enm_execute.return_value = response
        self.assertDictEqual(node_pool_mgr.generate_cell_dict(None), expected)

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.node_pool_mgr.get_workload_admin_user')
    def test_generate_cell_dict_logs_exception(self, mock_get_or_create_admin_user, mock_debug):
        response = Mock()
        expected = {"TDD": set([]), "FDD": set([]), "LARGE_BSC": set([]), "SMALL_BSC": set([]), "BSC_250_CELL": set([])}
        response.get_output.side_effect = Exception("Error")
        mock_get_or_create_admin_user.return_value.enm_execute.return_value = response
        self.assertDictEqual(node_pool_mgr.generate_cell_dict("FDD"), expected)
        mock_debug.assert_called_with("Failed to retrieve list of cells from ENM, response: Error")

    @patch('enmutils_int.lib.node_pool_mgr.generate_cell_dict', return_value={"FDD": [], "TDD": []})
    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    def test_persist_eutrancell_dict_only_persists_dict_containing_mos(self, mock_set, *_):
        node_pool_mgr.persist_dict_value("EUTRANCELL_NODE_DICT")
        self.assertEqual(mock_set.call_count, 0)

    @patch('enmutils_int.lib.node_pool_mgr.generate_cell_dict', return_value={"FDD": ["LTE01"], "TDD": []})
    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    def test_persist_eutrancell_dict(self, mock_set, *_):
        node_pool_mgr.persist_dict_value("EUTRANCELL")
        self.assertEqual(mock_set.call_count, 1)

    @patch('enmutils_int.lib.node_pool_mgr.persistence')
    @patch('enmutils_int.lib.node_pool_mgr.log.logger.debug')
    def test_persist_dict_value__no_key_to_be_set_in_persistence(self, mock_log, _):
        node_pool_mgr.persist_dict_value("")
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.node_pool_mgr.generate_cell_dict', return_value={"LARGE_BSC": [], "TDD": ["LTE01"]})
    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    def test_large_bsc_nodes_only_persists_dict_containing_mos(self, mock_set, *_):
        node_pool_mgr.persist_dict_value("LARGE_BSC")
        self.assertEqual(mock_set.call_count, 0)

    @patch('enmutils_int.lib.node_pool_mgr.generate_cell_dict', return_value={"LARGE_BSC": ["BSC01"], "TDD": []})
    @patch('enmutils_int.lib.node_pool_mgr.persistence.set')
    def test_persist_bsc_key_nodes(self, mock_set, *_):
        node_pool_mgr.persist_dict_value("GSM_KEYS")
        self.assertEqual(mock_set.call_count, 1)

    def test_remove_upgind_nodes__skips_profile_without_filter(self):
        profile = Mock(NO_UPGIND=False)
        node = Mock()
        delattr(node, 'simulation')
        self.assertListEqual([node], node_pool_mgr.Pool.remove_upgind_nodes(profile, [node]))

    def test_remove_upgind_nodes__filters_upgind_node(self):
        profile = Mock(NO_UPGIND=True)
        node = Mock(simulation="UPGIND")
        self.assertListEqual([], node_pool_mgr.Pool.remove_upgind_nodes(profile, [node]))

    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_ids')
    def test_error_profile_if_node_under_allocation_only_adds_error_on_under_allocation(self, _):
        pool = node_pool_mgr.ProfilePool()
        profile = Mock()
        pool.error_profile_if_node_under_allocation(10, 10, profile)
        self.assertEqual(0, profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.update_available_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.persist_dict_value')
    def test_filter_bsc_nodes_based_upon_size(self, mock_persist_dict_value, mock_update_available_nodes):
        node = Mock()
        nodes = [node]
        profile = Mock()
        profile.MAX_NODES_TO_ALLOCATE = 1
        profile.LARGE_BSC_ONLY = True
        node_pool_mgr.filter_bsc_nodes_based_upon_size(profile, nodes)
        mock_persist_dict_value.assert_called_with("GSM_KEYS")
        mock_update_available_nodes.assert_called_with(nodes, "LARGE_BSC", exclude=False)
        delattr(profile, "LARGE_BSC_ONLY")
        profile.SMALL_BSC_ONLY = True
        node_pool_mgr.filter_bsc_nodes_based_upon_size(profile, nodes)
        mock_persist_dict_value.assert_called_with("GSM_KEYS")
        mock_update_available_nodes.assert_called_with(nodes, "SMALL_BSC", exclude=None)
        delattr(profile, "SMALL_BSC_ONLY")
        node_pool_mgr.filter_bsc_nodes_based_upon_size(profile, nodes)
        self.assertEqual(3, mock_update_available_nodes.call_count)
        profile.BSC_250_CELL = True
        node_pool_mgr.filter_bsc_nodes_based_upon_size(profile, nodes)
        mock_persist_dict_value.assert_called_with("GSM_KEYS")
        mock_update_available_nodes.assert_called_with(nodes, "BSC_250_CELL", exclude=None)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=["BSC01"])
    def test_update_available_nodes(self, *_):
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        nodes = [node, node1]
        nodes = node_pool_mgr.update_available_nodes(nodes, node_pool_mgr.SMALL_BSC)
        self.assertListEqual([node], nodes)

    @patch('enmutils_int.lib.node_pool_mgr.persist_dict_value')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', side_effect=[None, None, None, ["BSC01"]])
    def test_update_available_nodes_no_key(self, *_):
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        nodes = [node, node1]
        result = node_pool_mgr.update_available_nodes(nodes, node_pool_mgr.SMALL_BSC)
        self.assertListEqual(nodes, result)
        result = node_pool_mgr.update_available_nodes(nodes, node_pool_mgr.SMALL_BSC)
        self.assertListEqual([node], result)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=["BSC01"])
    def test_update_available_nodes_exclude_nodes(self, *_):
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        nodes = [node, node1]
        nodes = node_pool_mgr.update_available_nodes(nodes, node_pool_mgr.SMALL_BSC, exclude=True)
        self.assertListEqual([node1], nodes)

    @patch('enmutils_int.lib.node_pool_mgr.get_workload_admin_user')
    def test_get_synced_nodes(self, mock_get_or_create_admin_user):
        response = Mock()
        expected = ["MSC47BSC94", "MSC48BSC95", "MSC48BSC96"]
        cmd = 'cmedit get * CmFunction.SyncStatus==SYNCHRONIZED -ne=BSC'
        response.get_output.return_value = [u'FDN : NetworkElement=MSC47BSC94,CmFunction=1',
                                            u'syncStatus : SYNCHRONIZED', u'',
                                            u'FDN : NetworkElement=MSC48BSC95,CmFunction=1',
                                            u'syncStatus : SYNCHRONIZED', u'',
                                            u'FDN : NetworkElement=MSC48BSC96,CmFunction=1',
                                            u'syncStatus : SYNCHRONIZED', u'', u'', u'3 instance(s)']
        mock_get_or_create_admin_user.return_value.enm_execute.return_value = response
        self.assertEqual(expected, node_pool_mgr.get_synced_nodes(ne_type="BSC"))
        mock_get_or_create_admin_user.return_value.enm_execute.assert_called_with(cmd)

    @patch('enmutils_int.lib.node_pool_mgr.get_workload_admin_user')
    def test_get_synced_nodes_exception(self, mock_get_or_create_admin_user):
        expected = []
        cmd = 'cmedit get * CmFunction.SyncStatus==SYNCHRONIZED'
        mock_get_or_create_admin_user.return_value.enm_execute.side_effect = Exception("error")
        self.assertEqual(expected, node_pool_mgr.get_synced_nodes())
        mock_get_or_create_admin_user.return_value.enm_execute.assert_called_with(cmd)

    @patch('enmutils_int.lib.node_pool_mgr.get_workload_admin_user')
    def test_get_synced_nodes_no_output(self, mock_get_or_create_admin_user):
        response = Mock()
        expected = []
        response.get_output.return_value = None
        mock_get_or_create_admin_user.return_value.enm_execute.return_value = response
        self.assertEqual(expected, node_pool_mgr.get_synced_nodes())

    @patch('enmutils_int.lib.node_pool_mgr.get_pool')
    def test_get_allocated_node_summary_raises_no_nodes_available(self, mock_allocated_nodes):
        mock_allocated_nodes.return_value.allocated_nodes.return_value = []
        self.assertRaises(NoNodesAvailable, node_pool_mgr.get_allocated_node_summary, "TEST_01")

    def test_remove_gerancell_in_range(self):
        output = [u'FDN : GeranCell=0,GeranCellRelation=173020C', u'FDN : GeranCell=100,GeranCellRelation=173028B',
                  u'FDN : GeranCell=101,GeranCellRelation=173030A', u'FDN : GeranCell=-1,GeranCellRelation=173030B',
                  u'', u'', u'04 instance(s)']
        result = node_pool_mgr.remove_gerancell_in_range(output)
        self.assertListEqual(output, result)

    @patch('enmutils_int.lib.node_pool_mgr.remove_gerancell_in_range')
    def test_get_node_mos_fdns_and_attrs__checks_gerancells(self, mock_gerancell_range):
        node, user, response = Mock(), Mock(), Mock()
        node.node_id = "Node1"
        response.get_output.return_value = [u'FDN : GeranCell=0,GeranCellRelation=173020C', u'', u'04 instance(s)']
        user.enm_execute.return_value = response
        mock_gerancell_range.return_value = response.get_output.return_value
        node_pool_mgr.get_node_mos_fdns_and_attrs(user, [node], Mock(), {"GeranCellRelation": 1})
        self.assertEqual(1, mock_gerancell_range.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.remove_gerancell_in_range')
    def test_get_node_mos_fdns_and_attrs__cmimport_35(self, mock_gerancell_range):
        node, user, response = Mock(), Mock(), Mock()
        node.node_id = "Node1"
        response.get_output.return_value = [u'FDN : UtranCell=0,UtranCellRelation=173020C', u'', u'04 instance(s)']
        user.enm_execute.return_value = response
        mock_gerancell_range.return_value = response.get_output.return_value
        profile = Mock()
        setattr(profile, 'NAME', "CMIMPORT_35")
        node_pool_mgr.get_node_mos_fdns_and_attrs(user, [node], profile, {"UtranCell": 1})

    @patch('enmutils_int.lib.node_pool_mgr.remove_gerancell_in_range')
    def test_get_node_mos_fdns_and_attrs__returns_output(self, mock_gerancell_range):
        node, user, response = Mock(), Mock(), Mock()
        node.node_id = "Node1"
        response.get_output.return_value = [u'FDN : UtranCell=0,UtranCellRelation=173020C', u'', u'04 instance(s)']
        user.enm_execute.return_value = response
        mock_gerancell_range.return_value = response.get_output.return_value
        output, attrs = node_pool_mgr.get_node_mos_fdns_and_attrs(user, [node], Mock(), {"UtranCell": 1})
        self.assertEqual(0, mock_gerancell_range.call_count)
        self.assertEqual(output, response.get_output.return_value)
        self.assertIsNone(attrs)

    @patch('enmutils_int.lib.node_pool_mgr.MoAttrs.fetch')
    def test_get_node_mos_fdns_and_attrs__fetches_attributes(self, mock_fetch_attrs):
        node, user, response = Mock(), Mock(), Mock()
        node.node_id = "Node1"
        response.get_output.return_value = [u'FDN : UtranCell=0,UtranCellRelation=173020C', u'', u'04 instance(s)']
        user.enm_execute.return_value = response
        mock_fetch_attrs.return_value = ["attrs"]
        output, attrs = node_pool_mgr.get_node_mos_fdns_and_attrs(user, [node], Mock(), {"UtranCell": 1},
                                                                  attrs={"attrs": 1})
        self.assertEqual(1, mock_fetch_attrs.call_count)
        self.assertEqual(output, response.get_output.return_value)
        self.assertEqual(attrs, ["attrs"])

    def test_get_node_mos_fdns_and_attrs__raises_script_engine_error(self):
        node, user, response = Mock(), Mock(), Mock()
        node.node_id = "Node1"
        response.get_output.return_value = None
        user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, node_pool_mgr.get_node_mos_fdns_and_attrs, user, [node],
                          Mock(), {"UtranCell": 1})

    @patch('enmutils_int.lib.node_pool_mgr.get_filtered_nodes')
    @patch('enmutils_int.lib.node_pool_mgr.EnmMo.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.get_node_mos_fdns_and_attrs')
    def test_get_nodes_mos_no_subnetwork(self, mock_get_fdn, mock_enm_mo, mock_get_filtered_nodes):
        mock_get_fdn.return_value = ([u'FDN : GeranCell=0,GeranCellRelation=173020C',
                                      u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimG,'
                                      u'MeContext=GSM02BSC02,ManagedElement=GSM02BSC02,'
                                      u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=173027O,GeranCellRelation=173024C',
                                      u'', u'04 instance(s)'], None)
        node, user, = Mock(), Mock()
        node.node_id, node.ROOT_ELEMENT = "GSM02BSC02", "GSM"
        node_pool_mgr.get_nodes_mos(user, {}, [node, node], ignore_mo_val="173024C", profile=Mock())
        self.assertEqual(0, mock_enm_mo.call_count)
        self.assertEqual(2, mock_get_filtered_nodes.call_count)

    @patch("enmutils_int.lib.node_pool_mgr.group_nodes_per_netsim_host")
    def test_match_cardinality_requirements_returns_if_invalid_attr(self, mock_group, *_):
        profile = Mock()
        profile.CELL_CARDINALITY_NES = ["ERBS"]
        node_pool_mgr.match_cardinality_requirements(profile, [], "ERBS")
        self.assertEqual(0, mock_group.call_count)

    @patch("enmutils_int.lib.node_pool_mgr.nss_mo_info.NssMoInfo.fetch_and_parse_netsim_simulation_files",
           side_effect=Exception("Error"))
    @patch("enmutils_int.lib.node_pool_mgr.get_pool", return_value=Mock())
    @patch("enmutils_int.lib.node_pool_mgr.group_nodes_per_netsim_host")
    @patch("enmutils_int.lib.node_pool_mgr.node_mo_selection.NodeMoSelection.select_all_with_required_mo_cardinality")
    def test_match_cardinality_requirements(self, mock_get_nodes, *_):
        profile = Mock()
        profile.CELL_CARDINALITY = {"CELL": (1, 1), "CELL1": 1}
        profile.CELL_CARDINALITY_NES = ["ERBS"]
        node_pool_mgr.match_cardinality_requirements(profile, [Mock()], "ERBS")
        self.assertEqual(2, mock_get_nodes.call_count)

    @patch("enmutils_int.lib.node_pool_mgr.nss_mo_info.NssMoInfo.fetch_and_parse_netsim_simulation_files",
           side_effect=Exception("Error"))
    @patch("enmutils_int.lib.node_pool_mgr.get_pool", return_value=Mock())
    @patch("enmutils_int.lib.node_pool_mgr.group_nodes_per_netsim_host")
    @patch("enmutils_int.lib.node_pool_mgr.node_mo_selection.NodeMoSelection.select_all_with_required_mo_cardinality")
    def test_match_cardinality_requirements__no_match_returns_empty_list(self, mock_get_nodes, *_):
        profile = Mock()
        profile.CELL_CARDINALITY = {"CELL": (1, 1), "CELL1": 1}
        profile.CELL_CARDINALITY_NES = ["ERBS"]
        mock_get_nodes.return_value = []
        self.assertEqual([], node_pool_mgr.match_cardinality_requirements(profile, [], "ERBS"))

    @patch("enmutils_int.lib.node_pool_mgr.nss_mo_info.NssMoInfo.fetch_and_parse_netsim_simulation_files")
    @patch("enmutils_int.lib.node_pool_mgr.get_pool", return_value=Mock())
    @patch("enmutils_int.lib.node_pool_mgr.group_nodes_per_netsim_host")
    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils_int.lib.node_pool_mgr.node_mo_selection.NodeMoSelection.select_all_with_required_mo_cardinality")
    def test_match_cardinality_requirements_multiple_mos(self, mock_get_nodes, *_):
        profile = Mock()
        profile.CELL_CARDINALITY = {"CELL": (1, 1), "CELL1": 1}
        profile.CELL_CARDINALITY_NES = ["ERBS"]
        mock_get_nodes.side_effect = [["Node", "Node1"], ["Node1", "Node2"]]
        self.assertListEqual(node_pool_mgr.match_cardinality_requirements(profile, ["Node", "Node1", "Node2"], "ERBS"),
                             ["Node1"])

    @patch("enmutils_int.lib.node_pool_mgr.nss_mo_info.NssMoInfo.fetch_and_parse_netsim_simulation_files")
    @patch("enmutils_int.lib.node_pool_mgr.get_pool", return_value=Mock())
    @patch("enmutils_int.lib.node_pool_mgr.group_nodes_per_netsim_host")
    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils_int.lib.node_pool_mgr.node_mo_selection.NodeMoSelection.select_all_with_required_mo_cardinality")
    def test_match_cardinality_requirements__returns_empty_list_when_no_matched_nodes(self, mock_get_nodes, *_):
        profile = Mock()
        profile.CELL_CARDINALITY = {"CELL": (1, 1), "CELL1": 1}
        profile.CELL_CARDINALITY_NES = ["ERBS"]
        mock_get_nodes.return_value = []
        self.assertEqual(node_pool_mgr.match_cardinality_requirements(profile, ["Node", "Node1", "Node2"], "ERBS"), [])

    @patch("enmutils_int.lib.node_pool_mgr.nss_mo_info.NssMoInfo.fetch_and_parse_netsim_simulation_files",
           side_effect=Exception("Error"))
    @patch("enmutils_int.lib.node_pool_mgr.get_pool", return_value=Mock())
    @patch("enmutils_int.lib.node_pool_mgr.group_nodes_per_netsim_host")
    @patch("enmutils_int.lib.node_pool_mgr.node_mo_selection.NodeMoSelection.select_all_with_required_mo_cardinality")
    @patch("enmutils.lib.log.logger.debug")
    def test_match_cardinality_requirements_logs_error(self, mock_debug, mock_get_nodes, *_):
        profile = Mock()
        profile.CELL_CARDINALITY = {"CELL": (1, 1), "CELL1": 1}
        profile.CELL_CARDINALITY_NES = ["ERBS"]
        node_pool_mgr.match_cardinality_requirements(profile, [Mock()], "ERBS")
        mock_debug.assert_any_call("Failed to generate one or more files, error encountered: Error")
        self.assertEqual(2, mock_get_nodes.call_count)

    @patch("enmutils_int.lib.node_pool_mgr.nss_mo_info.NssMoInfo.fetch_and_parse_netsim_simulation_files",
           side_effect=Exception("Error"))
    @patch("enmutils_int.lib.node_pool_mgr.group_nodes_per_netsim_host")
    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils_int.lib.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.node_pool_mgr.node_mo_selection.NodeMoSelection.select_all_with_required_mo_cardinality")
    def test_match_cardinality_requirements_returns_single_cell_requirement(self, mock_matched, *_):

        profile, node, node1, node2 = Mock(), Mock(), Mock(), Mock()
        mock_matched.return_value = [node, node1, node2]
        profile.CELL_CARDINALITY = {"CELL": 1}
        profile.CELL_CARDINALITY_NES = ["ERBS"]
        result = node_pool_mgr.match_cardinality_requirements(profile, [Mock()], "ERBS")
        self.assertListEqual(sorted([node, node1, node2]), sorted(result))

    def test_handle_one_total_node_and_multiple_support_types__reduce_number_of_nodes(self):
        self.profile.TOTAL_NODES = 1
        self.profile.SUPPORTED_NODE_TYPES = ['ERBS', 'RADIONODE']
        self.assertEqual(1, len(handle_one_total_node_and_multiple_support_types(self.profile, ['ERBS_1', 'ERBS_DG2_1'])))

    def test_handle_one_total_node_and_multiple_support_types__number_of_nodes_unchanged(self):
        self.profile.TOTAL_NODES = 2
        self.profile.SUPPORTED_NODE_TYPES = ['ERBS', 'RADIONODE']
        self.assertEqual(2, len(handle_one_total_node_and_multiple_support_types(self.profile, ['ERBS_1', 'ERBS_DG2_1'])))

    @patch('enmutils_int.lib.node_pool_mgr.datetime')
    @patch("enmutils.lib.enm_node.BaseNode.__init__", return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get_key_values_from_default_db')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get_all_default_keys')
    def test_get_nodes_from_redis__success(
            self, mock_get_all_default_keys, mock_get, mock_get_key_values_from_default_db, *_):
        node = BaseNode()
        node.node_id = "Node1"

        some_other_key = Mock()
        mock_get_all_default_keys.return_value = ["Profile1", "Node1", "some_other_key", "Profile-mos"]
        mock_get.return_value = ["Profile1", "Profile2"]
        mock_get_key_values_from_default_db.return_value = [node, some_other_key]
        self.assertEqual([node], node_pool_mgr.get_all_nodes_from_redis(["Profile"]))
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_get_key_values_from_default_db.call_count)

    @patch("enmutils_int.lib.node_pool_mgr.process.get_current_rss_memory_for_current_process")
    @patch('enmutils_int.lib.node_pool_mgr.datetime')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get_key_values_from_default_db')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get')
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get_all_default_keys')
    def test_get_nodes_from_redis__returns_empty_list_if_no_nodes_in_redis(
            self, mock_get_all_default_keys, mock_get, mock_get_key_values_from_default_db, *_):
        mock_get_all_default_keys.return_value = ["Profile", "Profile-mos"]
        mock_get.return_value = ["Profile"]
        self.assertListEqual([], node_pool_mgr.get_all_nodes_from_redis(["Profile"]))
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(0, mock_get_key_values_from_default_db.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.get_all_nodes_from_redis')
    def test_update_node_ids__adds_missing_node_ids(self, mock_redis_nodes, *_):
        pool = node_pool_mgr.Pool()
        pool._nodes = {"ERBS": ["Node1", "Node3"]}
        mock_redis_nodes.return_value = [Mock(node_id="Node2", primary_type="ERBS"),
                                         Mock(node_id="Node3", primary_type="ERBS")]
        pool.update_node_ids()
        self.assertEqual(3, len(pool._nodes.get("ERBS")))

    @patch('enmutils_int.lib.node_pool_mgr.get_workload_admin_user')
    def test_get_node_oss_prefixes__success(self, mock_workload_admin):
        response = Mock()
        response.get_output.return_value = [
            u'FDN : NetworkElement=netsim_LTE02ERBS00001',
            u'ossPrefix : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001',
            u'', u'FDN : NetworkElement=netsim_LTE02ERBS00003',
            u'ossPrefix : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00003',
            u'', u'FDN : NetworkElement=netsim_LTE02ERBS00002',
            u'ossPrefix : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002',
            u'', u'FDN : NetworkElement=LTE84dg2ERBS00027',
            u'ossPrefix : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1',
            u'', u'', u'4 instance(s)']
        mock_workload_admin.return_value.enm_execute.return_value = response
        prefixes = node_pool_mgr.get_node_oss_prefixes(["Node"])
        self.assertEqual("SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1",
                         prefixes.get("LTE84dg2ERBS00027"))
        self.assertEqual("SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002",
                         prefixes.get("netsim_LTE02ERBS00002"))
        self.assertEqual("SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00003",
                         prefixes.get("netsim_LTE02ERBS00003"))
        self.assertEqual("SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001",
                         prefixes.get("netsim_LTE02ERBS00001"))

    @patch('enmutils_int.lib.node_pool_mgr.get_workload_admin_user')
    def test_get_node_oss_prefixes__raises_enm_application_error(self, mock_workload_admin):
        mock_workload_admin.return_value.enm_execute.side_effect = Exception("Error")
        self.assertRaises(node_pool_mgr.EnmApplicationError, node_pool_mgr.get_node_oss_prefixes, ["Node"])

    def test_get_filtered_nodes__exact(self):
        node = Mock(node_id="Node1", subnetwork="LTE1")
        node.ROOT_ELEMENT = "MeContext"
        result = node_pool_mgr.get_filtered_nodes(node, "exact", {'TermPointToENB': 1},
                                                  {u'Node1': {u'TermPointToENB': 1}}, {(u'MeContext', u'Node1'): {(u' ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtraNetwork', u'1'): {(u'ExternalENodeBFunction', u'LTE1'): {u'TermPointToENB': [Mock()]}}}}}})
        self.assertListEqual(result, [node])

    def test_get_filtered_nodes__no_exact_match(self):
        node = Mock(node_id="Node1", subnetwork="LTE1")
        node.ROOT_ELEMENT = "MeContext"
        result = node_pool_mgr.get_filtered_nodes(node, "exact", {'TermPointToENB2': 1, 'TermPointToENB': 2}, {u'Node1': {u'TermPointToENB2': 3, u'TermPointToENB': 2}}, {(u'MeContext', u'Node1'): {(u'ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtraNetwork', u'1'): {(u'ExternalENodeBFunction', u'LTE1'): {u'TermPointToENB2': [Mock(), Mock(), Mock()], u'TermPointToENB': [Mock()]}}}}, (u' ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtraNetwork', u'1'): {(u'ExternalENodeBFunction', u'LTE1'): {u'TermPointToENB': [Mock()]}}}}}})
        self.assertListEqual(result, [])

    def test_get_filtered_nodes__any(self):
        node = Mock(node_id="Node1", subnetwork="LTE1")
        node.ROOT_ELEMENT = "MeContext"
        result = node_pool_mgr.get_filtered_nodes(node, "any", {'TermPointToENB2': 1, 'TermPointToENB': 2}, {u'Node1': {u'TermPointToENB2': 3, u'TermPointToENB': 2}}, {(u'MeContext', u'Node1'): {(u'ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtraNetwork', u'1'): {(u'ExternalENodeBFunction', u'LTE1'): {u'TermPointToENB2': [Mock(), Mock(), Mock()], u'TermPointToENB': [Mock()]}}}}, (u' ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtraNetwork', u'1'): {(u'ExternalENodeBFunction', u'LTE1'): {u'TermPointToENB': [Mock()]}}}}}})
        self.assertListEqual(result, [node])

    def test_get_filtered_nodes__some(self):
        node = Mock(node_id="Node1", subnetwork="LTE1")
        node.ROOT_ELEMENT = "MeContext"
        result = node_pool_mgr.get_filtered_nodes(node, "some", {'TermPointToENB2': 1, 'TermPointToENB': 2}, {u'Node1': {u'TermPointToENB2': 3, u'TermPointToENB': 2}}, {(u'MeContext', u'Node1'): {(u'ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtraNetwork', u'1'): {(u'ExternalENodeBFunction', u'LTE1'): {u'TermPointToENB2': [Mock(), Mock(), Mock()], u'TermPointToENB': [Mock()]}}}}, (u' ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtraNetwork', u'1'): {(u'ExternalENodeBFunction', u'LTE1'): {u'TermPointToENB': [Mock()]}}}}}})
        self.assertListEqual(result, [node])

    def test_get_filtered_nodes__some_no_match(self):
        node = Mock(node_id="Node1", subnetwork="LTE1")
        node.ROOT_ELEMENT = "MeContext"
        result = node_pool_mgr.get_filtered_nodes(node, "some", {'EUtranCellFDD': 1, 'EUtranCellTDD': 2}, {u'Node1': {u'TermPointToENB2': 3, u'TermPointToENB': 2}}, {(u'MeContext', u'Node1'): {(u'ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtraNetwork', u'1'): {(u'ExternalENodeBFunction', u'LTE1'): {u'TermPointToENB2': [Mock(), Mock(), Mock()], u'TermPointToENB': [Mock()]}}}}, (u' ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtraNetwork', u'1'): {(u'ExternalENodeBFunction', u'LTE1'): {u'TermPointToENB': [Mock()]}}}}}})
        self.assertListEqual(result, [])

    def test_get_all_nodes_list__returns_empty_if_profile_expects_certain_node_type_but_type_not_found_in_pool(
            self, *_):
        profile = Profile()
        profile.NUM_NODES = {"UNKNOWN": -1}
        node_dict = {"SGSN": {"SGSN01": Mock(), "SGSN02": Mock()}}
        nodes = node_pool_mgr.get_unique_nodes(node_dict, "SGSN-MME")
        self.assertEqual(len(nodes), 0)

    def test_get_unique_nodes__is_successful_if_profile_expect_certain_node_type_but_only_nodes_of_old_type_in_pool(
            self, *_):
        profile = Profile()
        profile.NUM_NODES = {"SGSN-MME": -1}
        node_dict = {"SGSN": {"SGSN01": Mock(), "SGSN02": Mock()}, "SGSN-MME": {}}
        nodes = node_pool_mgr.get_unique_nodes(node_dict, "SGSN-MME")
        self.assertEqual(len(nodes), 2)

    def test_get_unique_nodes__is_successful_if_profile_expect_certain_node_type_but_both_old_and_new_types_in_pool(
            self, *_):
        profile = Profile()
        profile.NUM_NODES = {"SGSN-MME": -1}
        node_dict = {"SGSN": {"SGSN01": Mock(), "SGSN02": Mock()}, "SGSN-MME": {"SGSN03": Mock()}}
        nodes = node_pool_mgr.get_unique_nodes(node_dict, "SGSN-MME")
        self.assertEqual(len(nodes), 3)

    def test_get_unique_nodes__is_successful_if_node_listed_under_both_old_and_new_types_in_pool(
            self, *_):
        node_dict = {"SGSN": {"SGSN01": Mock(), "SGSN02": Mock()}, "SGSN-MME": {"SGSN01": Mock()}}
        nodes = node_pool_mgr.get_unique_nodes(node_dict, "SGSN-MME")
        self.assertEqual(len(nodes), 2)

    def test_fetching_lite_nodes_with_node_attributes(self):
        nodes = [Mock(node_id="Node1"), Mock(node_id="Node2"), Mock(node_id="Node3")]
        result = node_pool_mgr.create_lite_nodes_using_attribute_filter(nodes, node_attributes=["node_id"])
        self.assertEqual(len(result), 3)

    def test_fetching_lite_nodes_without_node_attributes(self):
        nodes = [Mock(node_id="Node1"), Mock(node_id="Node2"), Mock(node_id="Node3")]
        result = node_pool_mgr.create_lite_nodes_using_attribute_filter(nodes)
        self.assertEqual(len(result), 3)

    @patch("enmutils_int.lib.node_pool_mgr.create_lite_nodes_using_attribute_filter")
    @patch("enmutils_int.lib.node_pool_mgr.get_pool")
    def test_get_all_nodes_with_predefined_attributes__is_successful_if_profile_has_num_nodes_attribute(
            self, mock_get_pool, mock_create_lite_nodes_using_attribute_filter):
        node1 = Mock(primary_type="ERBS")
        node3 = Mock(primary_type="ERBS")
        node2 = Mock(primary_type="RadioNode")
        mock_get_pool.return_value.node_dict = {"ERBS": {"node1": node1, "node3": node3}, "RadioNode": {"node2": node2}}
        profile = Profile()
        profile.NUM_NODES = {"ERBS": -1}
        node_pool_mgr.get_all_nodes_with_predefined_attributes(profile)
        mock_create_lite_nodes_using_attribute_filter.assert_called_with([node1, node3], node_attributes=None)

    @patch("enmutils_int.lib.node_pool_mgr.create_lite_nodes_using_attribute_filter")
    @patch("enmutils_int.lib.node_pool_mgr.get_pool")
    def test_get_all_nodes_with_predefined_attributes__is_successful_if_profile_doesnt_have_num_nodes_attribute(
            self, mock_get_pool, mock_create_lite_nodes_using_attribute_filter):
        node1 = Mock(primary_type="ERBS")
        node3 = Mock(primary_type="ERBS")
        node2 = Mock(primary_type="RadioNode")
        mock_get_pool.return_value.node_dict = {"ERBS": {"node1": node1, "node3": node3}, "RadioNode": {"node2": node2}}
        profile = Profile()
        node_pool_mgr.get_all_nodes_with_predefined_attributes(profile, node_attributes=["node_id", "poid"])
        mock_create_lite_nodes_using_attribute_filter.assert_called_with(sorted([node1, node2, node3]),
                                                                         node_attributes=["node_id", "poid"])

    @patch("enmutils_int.lib.node_pool_mgr.get_all_nodes_with_predefined_attributes")
    @patch("enmutils_int.lib.node_pool_mgr.multitasking.create_single_process_and_execute_task")
    def test_get_all_nodes_using_seperate_process__is_successful(
            self, mock_create_single_process_and_execute_task, mock_get_all_nodes_with_predefined_attributes):
        profile = Profile()
        node_pool_mgr.get_all_nodes_using_separate_process(profile, node_attributes=["node_id"])
        mock_create_single_process_and_execute_task.assert_called_with(mock_get_all_nodes_with_predefined_attributes,
                                                                       args=(profile, ["node_id"]), fetch_result=True)

    @patch("enmutils_int.lib.node_pool_mgr.get_pool")
    def test_get_allocated_nodes_with_predefined_attributes__is_successful(self, mock_get_pool, *_):
        nodes = [Mock(node_id="node1", ABC="abc1", XYZ="xyz1")]

        mock_get_pool.return_value.allocated_nodes.return_value = nodes
        result = node_pool_mgr.get_allocated_nodes_with_predefined_attributes("TEST_PROFILE",
                                                                              node_attributes=["node_id", "XYZ"])

        mock_get_pool.return_value.allocated_nodes.assert_called_with("TEST_PROFILE")
        self.assertEqual(result[0].__dict__, {"node_id": "node1", "XYZ": "xyz1"})

    @patch("enmutils_int.lib.node_pool_mgr.get_pool")
    def test_get_allocated_nodes_with_predefined_attributes__returns_node_id_only_if_no_attributes_specified(
            self, mock_get_pool):
        nodes = [Mock(node_id="node1", ABC="abc1", XYZ="xyz1")]

        mock_get_pool.return_value.allocated_nodes.return_value = nodes
        result = node_pool_mgr.get_allocated_nodes_with_predefined_attributes("TEST_PROFILE")

        mock_get_pool.return_value.allocated_nodes.assert_called_with("TEST_PROFILE")
        self.assertEqual(result[0].__dict__, {"node_id": "node1"})

    @patch("enmutils_int.lib.node_pool_mgr.get_allocated_nodes_with_predefined_attributes")
    @patch("enmutils_int.lib.node_pool_mgr.multitasking.create_single_process_and_execute_task")
    def test_get_allocated_nodes__is_successful(
            self, mock_create_single_process_and_execute_task, mock_get_allocated_nodes_with_predefined_attributes):
        node_pool_mgr.get_allocated_nodes("TEST_PROFILE", node_attributes=["XYZ"])
        mock_create_single_process_and_execute_task.assert_called_with(
            mock_get_allocated_nodes_with_predefined_attributes, args=("TEST_PROFILE", ["XYZ"]), fetch_result=True)

    @patch("enmutils_int.lib.node_pool_mgr.deallocate_nodes")
    @patch("enmutils_int.lib.node_pool_mgr.allocate_nodes")
    @patch("enmutils_int.lib.node_pool_mgr.persistence.get")
    def test_exchange_nodes_allocated_to_profile__is_successful(
            self, mock_get, mock_allocate_nodes, *_):
        mock_profile = Mock()
        mock_get.return_value = mock_profile
        node_pool_mgr.exchange_nodes_allocated_to_profile("TEST_PROFILE")
        mock_allocate_nodes.assert_called_with(profile=mock_profile)

    @patch("enmutils_int.lib.node_pool_mgr.deallocate_nodes")
    @patch("enmutils_int.lib.node_pool_mgr.allocate_nodes")
    @patch("enmutils_int.lib.node_pool_mgr.persistence.get")
    def test_exchange_nodes_allocated_to_profile__calls_add_error_for_exception(
            self, mock_get, mock_allocate_nodes, *_):
        mock_profile = Mock()
        mock_get.return_value = mock_profile
        mock_allocate_nodes.side_effect = NoNodesAvailable("No nodes")
        node_pool_mgr.exchange_nodes_allocated_to_profile("TEST_PROFILE")
        self.assertTrue(mock_profile.add_error_as_exception.called)

    def test_update_node_types__modifies_node_type_based_on_the_condition(self):
        mock_profile = Mock()
        mock_profile.SUPPORTED_NODE_TYPES = ['ERBS', 'MINI-LINK-Indoor', 'BSC', 'Router6672', 'SGSN-MME']
        mock_node_dict = {'ERBS': ['LTE01'], 'MLTN': ['ML01-0001', 'ML02-0001'], 'MINI-LINK-Indoor': [],
                          'Router6672': ['R6672001'], 'SGSN': ['SGSN-MME01'], 'SGSN-MME': ['SGSN-MME02']}
        nodes_list = node_pool_mgr.Pool.update_node_types(mock_profile, mock_node_dict)
        self.assertListEqual(sorted(nodes_list), sorted(['ERBS', 'MLTN', 'Router6672', 'BSC', 'SGSN', 'SGSN-MME']))

    @patch("enmutils_int.lib.node_pool_mgr.get_pool")
    def test_get_random_available_nodes__is_successful(self, mock_get_pool):
        profile = Mock()
        node_pool_mgr.get_random_available_nodes(profile, "ERBS")
        mock_get_pool.return_value.get_random_available_nodes.assert_called_with(profile=profile, node_type="ERBS")

    def test_initialize_cached_nodes__is_successful(self):
        node_pool_mgr.initialize_cached_nodes_list()
        self.assertEqual(node_pool_mgr.cached_nodes_list, [])

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get')
    def test_update_lte_node__skips_non_lte_nodes(self, mock_get):
        node = Mock(primary_type="RNC", lte_cell_type=None)
        node_pool_mgr.LTE_DICT = {}
        node_pool_mgr.update_lte_node(node)
        self.assertEqual(0, mock_get.call_count)
        self.assertIsNone(node.lte_cell_type)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get')
    def test_update_lte_node__uses_cached_dict(self, mock_get):
        node = Mock(primary_type="ERBS", lte_cell_type=None, node_id="Node")
        node_pool_mgr.LTE_DICT = {"FDD": ["Node"]}
        node_pool_mgr.update_lte_node(node)
        self.assertEqual(0, mock_get.call_count)
        self.assertEqual("FDD", node.lte_cell_type)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value={"FDD": ["Node"], "BSC": []})
    def test_update_lte_node__uses_persisted_dict(self, mock_get):
        node = Mock(primary_type="ERBS", lte_cell_type=None, node_id="Node")
        node_pool_mgr.LTE_DICT = {}
        node_pool_mgr.update_lte_node(node)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual("FDD", node.lte_cell_type)

    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.persist_dict_value')
    def test_update_lte_node__creates_dict(self, mock_persist, _):
        node = Mock(primary_type="ERBS", lte_cell_type=None, node_id="Node")
        node_pool_mgr.LTE_DICT = {}
        node_pool_mgr.update_lte_node(node)
        self.assertEqual(1, mock_persist.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_ids')
    @patch('enmutils_int.lib.node_pool_mgr.update_lte_node')
    @patch('enmutils_int.lib.node_pool_mgr.log.logger.debug')
    def test_nodes_to_be_allocated__updates_lte_check(self, mock_debug, *_):
        profile = Mock(LTE_CELL_CHECK=True)
        node_pool_mgr.Pool.nodes_to_be_allocated([], profile, [])
        mock_debug.assert_called_with("Updating LTE cell value before returning nodes.")

    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_node_ids')
    @patch('enmutils_int.lib.node_pool_mgr.update_lte_node')
    def test_nodes_to_be_allocated__skips_lte_check(self, mock_lte_update, _):
        profile = Mock(LTE_CELL_CHECK=False)
        node_pool_mgr.Pool.nodes_to_be_allocated([], profile, [])
        self.assertEqual(0, mock_lte_update.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.determine_if_ne_type_under_allocation')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.select_ne_type_available_nodes', return_value=["1"] * 3)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.correct_ne_type_under_allocation')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.set_expected_total_nodes_by_type', return_value=0)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.get_all_available_nodes_for_supported_node_types_attribute',
           return_value={})
    def test_allocate_nodes_by_ne_type__success(self, mock_set, mock_get_all, mock_correct, *_):
        pool = node_pool_mgr.Pool()
        profile = Mock()
        profile.NAME = 'FMX_01'
        node_dict = {'ERBS': ['Node'], 'RadioNode': ['Node']}
        profile.SUPPORTED_NODE_TYPES = ["ERBS", "RadioNode"]
        profile.TOTAL_NODES = 2
        self.assertEqual(2, len(pool.allocate_nodes_by_ne_type(profile, node_dict)))
        self.assertEqual(1, mock_set.call_count)
        self.assertEqual(1, mock_get_all.call_count)
        self.assertEqual(1, mock_correct.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.determine_if_ne_type_under_allocation')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.select_ne_type_available_nodes', return_value=["1"] * 3)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.update_bsc_node_requirements_for_fm')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.correct_ne_type_under_allocation')
    @patch('enmutils_int.lib.node_pool_mgr.Pool.set_expected_total_nodes_by_type', return_value=0)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.get_all_available_nodes_for_supported_node_types_attribute',
           return_value={})
    def test_allocate_nodes_by_ne_type__success_for_fm_01(self, mock_set, mock_get_all, mock_correct,
                                                          mock_update_bsc_allocation, *_):
        pool = node_pool_mgr.Pool()
        profile = Mock()
        profile.NAME = 'FM_01'
        node_dict = {'ERBS': ['Node'], 'RadioNode': ['Node'], 'BSC': ['Node']}
        profile.SUPPORTED_NODE_TYPES = ["ERBS", "RadioNode", "BSC"]
        profile.TOTAL_NODES = 2
        self.assertEqual(2, len(pool.allocate_nodes_by_ne_type(profile, node_dict)))
        self.assertEqual(1, mock_set.call_count)
        self.assertEqual(1, mock_get_all.call_count)
        self.assertEqual(1, mock_correct.call_count)
        self.assertTrue(mock_update_bsc_allocation.called)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_update_bsc_node_requirements_for_fm__is_successful(self, *_):
        expected_output = {'ERBS': 1, 'RadioNode': 1, 'BSC': 15}
        pool = node_pool_mgr.Pool()
        profile = Mock()
        profile.NAME = 'FM_01'
        profile.TOTAL_NODES = 3
        requirement = {'ERBS': 1, 'RadioNode': 1, 'BSC': 1}
        node_dict = {'ERBS': [Mock()], 'RadioNode': [Mock()], 'BSC': [Mock()] * 20}
        actual_output = pool.update_bsc_node_requirements_for_fm(node_dict, requirement, profile)
        self.assertEqual(expected_output, actual_output)
        self.assertEqual(profile.TOTAL_NODES, 17)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_update_bsc_node_requirements_for_fm__will_not_update_requirements(self, *_):
        expected_output = {'ERBS': 1, 'RadioNode': 1, 'BSC': 2}
        pool = node_pool_mgr.Pool()
        profile = Mock()
        profile.NAME = 'FM_01'
        profile.TOTAL_NODES = 4
        requirement = {'ERBS': 1, 'RadioNode': 1, 'BSC': 2}
        node_dict = {'ERBS': [Mock()], 'RadioNode': [Mock()], 'BSC': [Mock()] * 10}
        actual_output = pool.update_bsc_node_requirements_for_fm(node_dict, requirement, profile)
        self.assertEqual(expected_output, actual_output)
        self.assertEqual(profile.TOTAL_NODES, 4)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_select_ne_type_available_nodes__success(self, _):
        required = {"ERBS": 1, "RadioNode": 3, "BSC": 1, "Router6672": 0}
        available = {"ERBS": ["ERBS"], "RadioNode": ["DG2", "DG2"], "BSC": ["BSC"], "ROUTER6672": ["6672"]}
        pool = node_pool_mgr.Pool()
        self.assertListEqual(["ERBS", "BSC", "DG2", "DG2"], pool.select_ne_type_available_nodes(required, available))

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.alter_allocation_dict')
    def test_correct_ne_type_under_allocation__success(self, mock_alter, _):
        diffs = {"ERBS": (7, 0), "RadioNode": (0, 30), "BSC": (6, 0)}
        required = {"ERBS": 10, "RadioNode": 10, "BSC": 10}
        mock_alter.return_value = {"ERBS": 0, "RadioNode": 0, "BSC": 0}, required
        pool = node_pool_mgr.Pool()
        pool.correct_ne_type_under_allocation(diffs, required)
        self.assertEqual(2, mock_alter.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.alter_allocation_dict')
    def test_correct_ne_type_under_allocation__no_excess_nodes(self, mock_alter, _):
        diffs = {"ERBS": (7, 0), "RadioNode": (0, 0), "BSC": (6, 0)}
        required = {"ERBS": 10, "RadioNode": 10, "BSC": 10}
        pool = node_pool_mgr.Pool()
        pool.correct_ne_type_under_allocation(diffs, required)
        self.assertEqual(0, mock_alter.call_count)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_alter_allocation_dict__decrease(self, _):
        pool = node_pool_mgr.Pool()
        result = pool.alter_allocation_dict({"ERBS": 1}, {"ERBS": 10})
        self.assertDictEqual({"ERBS": 9}, result[1])
        self.assertDictEqual({"ERBS": 0}, result[0])

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_alter_allocation_dict__increase(self, _):
        pool = node_pool_mgr.Pool()
        result = pool.alter_allocation_dict({"ERBS": 1}, {"ERBS": 10}, increase=True)
        self.assertDictEqual({"ERBS": 11}, result[1])
        self.assertDictEqual({"ERBS": 0}, result[0])

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_alter_allocation_dict__no_initial_update(self, _):
        pool = node_pool_mgr.Pool()
        result = pool.alter_allocation_dict({"ERBS": 0, "RadioNode": 1}, {"ERBS": 10, "RadioNode": 10}, increase=True)
        self.assertDictEqual({"ERBS": 10, "RadioNode": 11}, result[1])
        self.assertDictEqual({"ERBS": 0, "RadioNode": 0}, result[0])

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_alter_allocation_dict__no_update(self, _):
        pool = node_pool_mgr.Pool()
        result = pool.alter_allocation_dict({"ERBS": 0, "RadioNode": 0}, {"ERBS": 10, "RadioNode": 10}, increase=True)
        self.assertDictEqual({"ERBS": 10, "RadioNode": 10}, result[1])
        self.assertDictEqual({"ERBS": 0, "RadioNode": 0}, result[0])

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_determine_if_ne_type_under_allocation__success(self, _):
        node = Mock()
        node.primary_type = "RadioNode"
        available = {"ERBS": [], "RadioNode": [node, node]}
        required = {"ERBS": 1, "RadioNode": 2}
        pool = node_pool_mgr.Pool()
        self.assertDictEqual(
            {"ERBS": (1, 0), "RadioNode": (0, 0)}, pool.determine_if_ne_type_under_allocation(required, available))

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_validate_required_count_is_available__success(self, _):
        pool = node_pool_mgr.Pool()
        self.assertEqual(1, pool.validate_required_count_is_available(10, 9))

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_validate_required_count_is_available__no_diff(self, _):
        pool = node_pool_mgr.Pool()
        self.assertEqual(0, pool.validate_required_count_is_available(10, 11))

    @patch('enmutils_int.lib.node_pool_mgr.Pool.get_random_available_nodes', return_value=["Node"])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_get_all_available_nodes_for_supported_node_types_attribute__success(self, *_):
        profile = Mock()
        profile.NAME = "TEST"
        pool = node_pool_mgr.Pool()
        available_nodes = pool.get_all_available_nodes_for_supported_node_types_attribute(
            profile, ["ERBS", "RadioNode"], {})
        self.assertDictEqual({'ERBS': ['Node'], 'RadioNode': ['Node']}, available_nodes)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.get_random_available_nodes', side_effect=[["Node"], NoNodesAvailable])
    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_get_all_available_nodes_for_supported_node_types_attribute__no_nodes_available(self, *_):
        profile = Mock()
        profile.NAME = "TEST"
        pool = node_pool_mgr.Pool()
        available_nodes = pool.get_all_available_nodes_for_supported_node_types_attribute(
            profile, ["ERBS", "RadioNode"], {})
        self.assertDictEqual({'ERBS': ['Node'], 'RadioNode': []}, available_nodes)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.calculate_total_node_values_type', return_value=({}, 10))
    @patch('enmutils_int.lib.node_pool_mgr.Pool.determine_expected_ne_type_count', return_value=1)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_set_expected_total_nodes_by_type__success(self, *_):
        profile = Mock()
        profile.TOTAL_NODES = 0
        pool = node_pool_mgr.Pool()
        ne_type_totals = pool.set_expected_total_nodes_by_type(profile, ["ERBS", "RadioNode"],
                                                               {"ERBS": ["Node"], "RadioNode": ["Node1"]})
        self.assertDictEqual({"ERBS": 1, "RadioNode": 1}, ne_type_totals)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.calculate_total_node_values_type', return_value=({}, 0))
    @patch('enmutils_int.lib.node_pool_mgr.Pool.determine_expected_ne_type_count', return_value=1)
    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_set_expected_total_nodes_by_type__no_total_nodes(self, *_):
        profile = Mock(NAME="Test")
        profile.TOTAL_NODES = 0
        pool = node_pool_mgr.Pool()
        ne_type_totals = pool.set_expected_total_nodes_by_type(profile, ["ERBS", "RadioNode"],
                                                               {"ERBS": ["Node"], "RadioNode": ["Node1"]})
        self.assertDictEqual({}, ne_type_totals)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_calculate_total_node_values_type__success(self, _):
        node_dict = {"ERBS": ["Node"], "RadioNode": ["Node1"], "BSC": ["Node2"]}
        pool = node_pool_mgr.Pool()
        total_nodes_by_type, sum_of_total_nodes = pool.calculate_total_node_values_type(
            ["ERBS", "RadioNode"], node_dict)
        self.assertDictEqual({"ERBS": 1, "RadioNode": 1}, total_nodes_by_type)
        self.assertEqual(2, sum_of_total_nodes)

    @patch('enmutils_int.lib.node_pool_mgr.Pool.__init__', return_value=None)
    def test_determine_expected_ne_type_count__success(self, _):
        pool = node_pool_mgr.Pool()
        self.assertEqual(10, pool.determine_expected_ne_type_count(40, 25, 100))

    def test_group_nodes_per_ne_type__is_successful(self):
        self.assertEqual(2, len(node_pool_mgr.group_nodes_per_ne_type([Mock(primary_type="ERBS"),
                                                                       Mock(primary_type="ERBS"),
                                                                       Mock(primary_type="RadioNode")])))

    def test_group_nodes_per_ne_type__if_no_nodes(self):
        self.assertEqual({}, node_pool_mgr.group_nodes_per_ne_type([]))

    def test_group_nodes_per_ne_type__only_radio_nodes_exist(self):
        self.assertEqual(1, len(node_pool_mgr.group_nodes_per_ne_type([Mock(primary_type="RadioNode")])))

    @patch('enmutils_int.lib.node_pool_mgr.log.logger.debug')
    def test_wl_nodes__is_successful(self, mock_debug_log):
        _ = node_pool_mgr.get_pool().wl_nodes
        self.assertEqual(mock_debug_log.call_count, 9)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
