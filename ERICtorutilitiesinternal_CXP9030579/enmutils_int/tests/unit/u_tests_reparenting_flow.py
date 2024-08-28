from datetime import datetime
from enmutils.lib.exceptions import EnvironWarning

import unittest2
from mock import patch, Mock, PropertyMock

from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import (ReparentingFlow, Reparenting01Flow,
                                                                               EnmApplicationError, Reparenting02Flow)
from testslib import unit_test_utils


class ReparentingFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = ReparentingFlow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.get_tg_mos')
    def test_get_tg_mos_values__success(self, mock_get):
        self.flow.get_tg_mos_values(Mock(), [])
        self.assertEqual(1, mock_get.call_count)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.build_base_station_json')
    def test_get_base_station_json__success(self, mock_build):
        self.flow.get_base_station_json([], '')
        self.assertEqual(1, mock_build.call_count)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.build_cell_json')
    def test_get_geran_cell_json__success(self, mock_build):
        self.flow.get_geran_cell_json([], '', '', False)
        self.assertEqual(1, mock_build.call_count)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.ReparentingFlow'
           '.select_target_controller_and_cells', return_value=("", []))
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.build_cell_json')
    def test_get_geran_cell_json__selects_targets(self, mock_build, mock_select):
        self.flow.get_geran_cell_json([], '', '', False, include_attributes=True)
        self.assertEqual(1, mock_build.call_count)
        self.assertEqual(1, mock_select.call_count)

    def test_select_target_controller_and_cells__success(self):
        cells = ["cell"] * 3
        self.flow.GERAN_CELLS = {"BSC": cells}
        self.assertEqual(('BSC', cells), self.flow.select_target_controller_and_cells(cells, "BSC"))

    def test_select_target_controller_and_cells__selects_alternative_target_and_cells(self):
        cells = ["BSC1=cell"] * 3
        self.flow.GERAN_CELLS = {"BSC": cells[:-1], "BSC1": cells, "BSC2": cells}
        self.assertEqual(('BSC2', cells), self.flow.select_target_controller_and_cells(cells, "BSC"))

    def test_select_target_controller_and_cells__raises_enm_application_error(self):
        cells = ["cell"] * 3
        self.flow.GERAN_CELLS = {}
        self.assertRaises(EnmApplicationError, self.flow.select_target_controller_and_cells, cells, "BSC")

    def test_select_volume_of_base_stations__success(self):
        base_stations = {'base': ['cell'] * 3, 'base1': ['cell'] * 3, 'base2': ['cell'] * 4, 'base3': ['cell'] * 3}
        count, result = self.flow.select_volume_of_base_stations(base_stations, max_cells=8)
        self.assertEqual(6, len(count))
        self.assertEqual(2, len(result))

    def test_get_resource_id__success(self):
        response = Mock()
        response.json.return_value = {'resourceId': 'id'}
        self.assertEqual('id', self.flow.get_resource_id(response))

    def test_get_resource_id__raises_enm_application_error(self):
        response = Mock()
        response.json.return_value = {}
        self.assertRaises(EnmApplicationError, self.flow.get_resource_id, response)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.ReparentingFlow.'
           'get_tg_mos_values', return_value={})
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.ReparentingFlow.'
           'select_volume_of_base_stations')
    def test_get_base_station_values__success(self, mock_select, _):
        self.flow.NAME = "REPARENTING_10"
        mock_select.side_effect = [(['cell'] * 5, [{'base': 'cell'}]), (['cell'] * 5, [{'base': 'cell'}])]
        self.flow.get_base_station_values(Mock(), ['id', 'id1', 'id2'], 10)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.ReparentingFlow.'
           'get_tg_mos_values', side_effect=[Exception('Error'), {}, {}])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.ReparentingFlow.'
           'select_volume_of_base_stations')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.debug')
    def test_get_base_station_values__skips_to_next_node(self, mock_debug, mock_select, _):
        mock_select.return_value = (['cell'] * 5, [{'base': 'cell'}])
        self.flow.get_base_station_values(Mock(), ['id', 'id1', 'id2'], 10)
        self.assertEqual(2, mock_select.call_count)
        mock_debug.assert_any_call("Unable to select base station, error encountered: Error")

    def test_get_base_station_values__raises_enm_application_error(self):
        self.assertRaises(EnmApplicationError, self.flow.get_base_station_values, Mock(), [], 10)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.get_bsc_network_elements',
           return_value=["BSC", "BSC1", "BSC2"])
    def test_select_target_bsc__returns_bsc(self, _):
        selected_cells = ["NetworkElement=BSC,GeranCell=1", "NetworkElement=BSC1,GeranCell1"]
        self.assertEqual("BSC2", self.flow.select_target_bsc(Mock(), selected_cells))

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.get_bsc_network_elements',
           return_value=["BSC"])
    def test_select_target_bsc__raises_enm_application_error(self, _):
        selected_cells = ["NetworkElement=BSC,GeranCell=1"]
        self.assertRaises(EnmApplicationError, self.flow.select_target_bsc, Mock(), selected_cells)

    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.info")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.persistence")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.datetime.datetime")
    def test_wait_for_first_iteration_to_complete_successful(self, mock_datetime, mock_persistence, *_):
        mock_persistence.get.return_value = Mock(state="RUNNING", status="OK")
        mock_datetime.now.return_value = datetime(2021, 10, 21, 2, 0, 0)
        self.flow.wait_for_first_iteration_to_complete(profile_name="Testing", state_to_wait_for="RUNNING", timeout_mins=30,
                                                       sleep_between=60)

    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.info")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.persistence")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.datetime.datetime")
    def test_wait_for_first_iteration_to_complete__status_nok(self, mock_datetime, mock_persistence, mock_log_info, *_):
        mock_persistence.get.return_value = Mock(state="RUNNING", status="NOK")
        mock_datetime.now.side_effect = [datetime(2021, 10, 21, 2, 0, 0), datetime(2021, 10, 21, 2, 29, 0), datetime(2021, 10, 21, 2, 31, 0)]
        self.flow.wait_for_first_iteration_to_complete(profile_name="Testing", state_to_wait_for="RUNNING",
                                                       timeout_mins=30,
                                                       sleep_between=60)
        self.assertTrue(mock_log_info.called)

    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.info")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.persistence")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.datetime.datetime")
    def test_wait_for_first_iteration_to_complete__timeout_exceeded(self, mock_datetime, mock_persistence, mock_log, *_):
        mock_persistence.get.return_value = Mock(state="RUNNING", status="OK")
        mock_datetime.now.return_value = datetime(2021, 10, 21, 2, 0, 0)
        self.flow.wait_for_first_iteration_to_complete(profile_name="Testing", state_to_wait_for="RUNNING", timeout_mins=-30,
                                                       sleep_between=60)
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.info")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.persistence")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.datetime.datetime")
    def test_wait_for_first_iteration_to_complete__raises_environ_warning(self, mock_datetime, mock_persistence, *_):
        mock_persistence.has_key.return_value = False
        mock_datetime.now.return_value = datetime(2021, 10, 21, 2, 0, 0)
        with self.assertRaisesRegexp(EnvironWarning, ""):
            self.flow.wait_for_first_iteration_to_complete(profile_name="Testing", state_to_wait_for="RUNNING",
                                                           timeout_mins=30, sleep_between=60)


class Reparenting01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Reparenting01Flow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.'
           'get_base_station_values', return_value=([{'base': 'cell'}], ['cell']))
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.get_and_sort_geran_cells',
           return_value={})
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.'
           'get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.get_base_station_json')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.send_post_request')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.get_resource_id')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.poll_for_completed_status')
    def test_execute_flow__success(self, mock_poll, mock_get, mock_post, mock_json, mock_nodes, *_):
        node = Mock()
        node.node_id = "Node"
        nodes = [node, node]
        mock_nodes.return_value = nodes
        mock_post.return_value = Mock()
        self.flow.execute_flow()
        self.assertEqual(1, mock_json.call_count)
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(0, mock_poll.call_count)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.get_base_station_json')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.get_resource_id')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.poll_for_completed_status')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.get_and_sort_geran_cells',
           return_value={})
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.send_post_request')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.'
           'get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting01Flow.'
           'get_base_station_values', return_value=([{'base': 'cell'}], ['cell']))
    def test_execute_flow__only_selects_base_stations_once(self, mock_get_base, mock_nodes, mock_post, mock_error, *_):
        node = Mock()
        node.node_id = "Node"
        nodes = [node, node]
        mock_nodes.return_value = nodes
        mock_post.side_effect = [Mock(), Exception("Error")]
        self.flow.execute_flow()
        self.assertEqual(1, mock_get_base.call_count)
        self.assertEqual(2, mock_post.call_count)
        self.assertEqual(2, mock_error.call_count)


class Reparenting02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Reparenting02Flow()
        self.flow.TARGET_BSC_ID = Mock()
        self.user = Mock()
        self.node = Mock()
        self.node.node_id = "Node"
        self.nodes = [self.node, self.node]
        self.max_cells = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.ReparentingFlow.wait_for_first_iteration_to_complete")
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.json_creation_and_post_request')
    def test_execute_flow__success(self, mock_json_creation, *_):
        self.flow.NAME = "REPARENTING_07"
        self.flow.execute_flow()
        self.assertEqual(1, mock_json_creation.call_count)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.ReparentingFlow.wait_for_first_iteration_to_complete")
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.json_creation_and_post_request')
    def test_execute_flow__wrong_profile_name(self, mock_json_creation, mock_wait_iter, *_):
        self.flow.NAME = "Wrong_Name"
        self.flow.execute_flow()
        self.assertEqual(1, mock_json_creation.call_count)
        self.assertFalse(mock_wait_iter.called)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.ReparentingFlow.wait_for_first_iteration_to_complete")
    @patch(
        'enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.json_creation_and_post_request')
    def test_execute_flow__waits_for_sleeping_state(self, mock_json_creation, mock_wait_iter, *_):
        self.flow.NAME = "REPARENTING_07"
        mock_wait_iter.side_effect = [False, True]
        self.flow.execute_flow()
        self.assertEqual(2, mock_wait_iter.call_count)
        self.assertEqual(1, mock_json_creation.call_count)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile.Profile.add_error_as_exception")
    @patch(
        "enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.ReparentingFlow.wait_for_first_iteration_to_complete")
    @patch(
        'enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.json_creation_and_post_request')
    def test_execute_flow__exception_raised(self, mock_json_creation, mock_wait_iter, mock_add_error_as_exception, *_):
        self.flow.NAME = "REPARENTING_07"
        mock_wait_iter.side_effect = [Exception]
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error_as_exception.call_count)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'get_base_station_values', return_value=(['base'], ['cell']))
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.get_and_sort_geran_cells',
           return_value={})
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.set_inter_ran_mobility_attribute')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.get_geran_cell_json')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.send_post_request')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.get_resource_id')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.poll_for_completed_status')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.select_target_bsc')
    def test_json_creation_and_post_request__success(self, mock_target, mock_poll, mock_get, mock_post, mock_json, *_):
        mock_post.return_value = Mock()
        selected_base_stations = []
        selected_cells = []
        delattr(self.flow, "TARGET_BSC_ID")
        self.flow.json_creation_and_post_request(self.nodes, self.max_cells, self.user, selected_base_stations,
                                                 selected_cells)
        self.assertEqual(1, mock_json.call_count)
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(0, mock_poll.call_count)
        self.assertEqual(1, mock_target.call_count)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.select_target_bsc')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.get_geran_cell_json')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.get_resource_id')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.poll_for_completed_status')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.get_and_sort_geran_cells',
           return_value={})
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.set_inter_ran_mobility_attribute')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.send_post_request')
    def test_json_creation_and_post_request__only_selects_base_stations_once(self, mock_post, mock_error, mock_set, *_):
        mock_post.side_effect = [Exception("Error")]
        selected_base_stations = ['base_station']
        selected_cells = ['cells']
        self.flow.TARGET_NETWORK_CONTROLLER_REQUIRED = False
        self.flow.SET_INTER_RAN_MOBILITY = True
        self.flow.json_creation_and_post_request(self.nodes, self.max_cells, self.user, selected_base_stations,
                                                 selected_cells)
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_error.call_count)
        self.assertEqual(0, mock_set.call_count)

    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.get_geran_cell_json')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.get_resource_id')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.poll_for_completed_status')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.get_and_sort_geran_cells',
           return_value={})
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.set_inter_ran_mobility_attribute')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.send_post_request')
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.'
           'get_base_station_values', return_value=(['base'], ['cell']))
    @patch('enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow.Reparenting02Flow.select_target_bsc')
    def test_json_creation_and_post_request__target_bsc_id_success(self, mock_select_target, mock_get_base, mock_post,
                                                                   mock_set, *_):
        selected_base_stations = []
        selected_cells = []
        self.flow.SET_INTER_RAN_MOBILITY = True
        self.flow.json_creation_and_post_request(self.nodes, self.max_cells, self.user, selected_base_stations,
                                                 selected_cells)
        self.assertEqual(1, mock_get_base.call_count)
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(0, mock_select_target.call_count)
        self.assertEqual(1, mock_set.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
