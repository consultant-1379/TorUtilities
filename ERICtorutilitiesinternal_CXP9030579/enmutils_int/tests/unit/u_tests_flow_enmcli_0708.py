#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock

from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708 import ENMCLI0708Flow


class EnmCli0708FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.node = Mock()
        self.node.node_name = "ABC"
        self.nodes_list = [self.node, self.node]
        self.flow = ENMCLI0708Flow()
        self.flow.geran_id = 123
        self.flow.NUM_USERS = 2
        self.flow.USER_ROLES = ["Admin"]
        self.flow.SCHEDULED_TIMES_STRINGS = ["08:00:00"]
        self.flow.SLEEP_TIME_BETWEEN_COMMANDS = 0
        self.flow.command = "TEST_COMMAND"
        self.flow.node = self.nodes_list
        self.flow.DAILY_ITERATION_COUNT_LIMIT = 102

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.keep_running',
           side_effect=[False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.create_profile_users',
           return_value=[Mock(), Mock()])
    def test_execute_flow__is_skipped(self, mock_create_profile_users, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow'
           '.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.execute_command_on_enm_cli')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.get_node_gerancell_value',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.create_profile_users',
           return_value=[Mock(), Mock()])
    def test_execute_flow__success(self, mock_create_profile_users, mock_geran_cells, mock_enm_cli, mock_nodes, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_nodes.side_effect = [self.nodes_list]
        self.flow.execute_flow()
        self.assertTrue(mock_geran_cells.called)
        self.assertTrue(mock_enm_cli.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.keep_running',
           side_effect=[True for _ in range(0, 102)])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow'
           '.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.task_set_serial')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.get_node_gerancell_value',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.create_profile_users',
           return_value=[Mock(), Mock()])
    def test_execute_flow__success_node_exchange(self, mock_create_profile_users, mock_geran_cells, mock_exchange, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_geran_cells.called)
        self.assertTrue(mock_exchange.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow'
           '.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.execute_command_on_enm_cli',
           side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.get_node_gerancell_value',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.add_error_as_exception')
    def test_execute_flow__exception_when_enmcli_command_execution_fails(self, mock_error, mock_create_profile_users,
                                                                         mock_geran_cells, mock_nodes, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_nodes.side_effect = [self.nodes_list]
        self.flow.execute_flow()
        self.assertTrue(mock_geran_cells.called)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow'
           '.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.get_node_gerancell_value',
           side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.add_error_as_exception')
    def test_execute_flow__exception_when_fetching_node_gerancell_value(self, mock_error, mock_create_profile_users,
                                                                        *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.execute_command_on_enm_cli')
    def test_check_existence_of_gerancellrelationid_return_True(self, mock_execute_enmcli):
        response = Mock()
        response.get_output.return_value = [u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimG,'
                                            u'MeContext=GSM02BSC02,ManagedElement=GSM02BSC02,BscFunction=1,'
                                            u'BscM=1,GeranCellM=1,GeranCell=173027O,GeranCellRelation=1',
                                            u'awOffset : 5', u'bqOffset : 3', u'bqOffsetAfr : 3', u'bqOffsetAwb : 3',
                                            u'cand : BOTH', u'cs : NO', u'geranCellRelationId : 1', u'gprsValid : YES',
                                            u'hiHyst : 5', u'kHyst : 3', u'kOffset : 0', u'lHyst : 3', u'lOffset : 0',
                                            u'loHyst : 3', u'offset : 0', u'pROffset : null',
                                            u'relationDirection : MUTUAL', u'relType : NEUTRAL', u'tRHyst : 2',
                                            u'tROffset : 0', u'', u'', u'1 instance(s)']
        mock_execute_enmcli.return_value = response
        self.assertEqual(True, self.flow.check_existence_of_gerancellrelationid(self.user, self.node, 2, 121))
        self.assertTrue(mock_execute_enmcli.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.execute_command_on_enm_cli')
    def test_check_existence_of_gerancellrelationid_return_False(self, mock_execute_enmcli):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        mock_execute_enmcli.return_value = response
        self.assertEqual(False, self.flow.check_existence_of_gerancellrelationid(self.user, self.node, 2, 121))
        self.assertTrue(mock_execute_enmcli.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.execute_command_on_enm_cli')
    def test_confirm_create_delete_run_create_skips_when_existence_true(self, mock_execute_enmcli):
        response = Mock()
        response.get_output.return_value = [u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimG,'
                                            u'MeContext=GSM02BSC02,ManagedElement=GSM02BSC02,BscFunction=1,'
                                            u'BscM=1,GeranCellM=1,GeranCell=173027O,GeranCellRelation=1',
                                            u'awOffset : 5', u'bqOffset : 3', u'bqOffsetAfr : 3', u'bqOffsetAwb : 3',
                                            u'cand : BOTH', u'cs : NO', u'geranCellRelationId : 1', u'gprsValid : YES',
                                            u'hiHyst : 5', u'kHyst : 3', u'kOffset : 0', u'lHyst : 3', u'lOffset : 0',
                                            u'loHyst : 3', u'offset : 0', u'pROffset : null',
                                            u'relationDirection : MUTUAL', u'relType : NEUTRAL', u'tRHyst : 2',
                                            u'tROffset : 0', u'', u'', u'1 instance(s)']
        mock_execute_enmcli.return_value = response
        self.assertEqual(False, self.flow.confirm_create_delete_run("cmedit create ",
                                                                    self.user, self.node, 2, 12))
        self.assertTrue(mock_execute_enmcli.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.execute_command_on_enm_cli')
    def test_confirm_create_delete_run_create_executes_when_existence_false(self, mock_execute_enmcli):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        mock_execute_enmcli.return_value = response
        self.assertEqual(True, self.flow.confirm_create_delete_run("cmedit create ",
                                                                   self.user, self.node, 2, 12))
        self.assertTrue(mock_execute_enmcli.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.execute_command_on_enm_cli')
    def test_confirm_create_delete_run_delete_skips_when_existence_false(self, mock_execute_enmcli):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        mock_execute_enmcli.return_value = response
        self.assertEqual(False, self.flow.confirm_create_delete_run("cmedit delete ",
                                                                    self.user, self.node, 2, 12))
        self.assertTrue(mock_execute_enmcli.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.execute_command_on_enm_cli')
    def test_confirm_create_delete_run_delete_executes_when_existence_true(self, mock_execute_enmcli):
        response = Mock()
        response.get_output.return_value = [u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimG,'
                                            u'MeContext=GSM02BSC02,ManagedElement=GSM02BSC02,BscFunction=1,'
                                            u'BscM=1,GeranCellM=1,GeranCell=173027O,GeranCellRelation=1',
                                            u'awOffset : 5', u'bqOffset : 3', u'bqOffsetAfr : 3', u'bqOffsetAwb : 3',
                                            u'cand : BOTH', u'cs : NO', u'geranCellRelationId : 1', u'gprsValid : YES',
                                            u'hiHyst : 5', u'kHyst : 3', u'kOffset : 0', u'lHyst : 3', u'lOffset : 0',
                                            u'loHyst : 3', u'offset : 0', u'pROffset : null',
                                            u'relationDirection : MUTUAL', u'relType : NEUTRAL', u'tRHyst : 2',
                                            u'tROffset : 0', u'', u'', u'1 instance(s)']
        mock_execute_enmcli.return_value = response
        self.assertEqual(True, self.flow.confirm_create_delete_run("cmedit delete ",
                                                                   self.user, self.node, 2, 12))
        self.assertTrue(mock_execute_enmcli.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
