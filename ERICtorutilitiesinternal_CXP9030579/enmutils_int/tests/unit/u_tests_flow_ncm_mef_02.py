#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow import NcmMef02Flow
from enmutils_int.lib.workload import ncm_mef_02
from mock import patch, Mock, PropertyMock
from requests.exceptions import HTTPError
from testslib import unit_test_utils


class NcmMef02UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [[Mock(node_id="ML_06")], [Mock(node_id="ML_07")]]
        self.ncm_mef_02 = ncm_mef_02.NCM_MEF_02()
        self.flow = NcmMef02Flow()
        self.flow.NAME = "NCM_MEF_02"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Administrator"]
        self.flow.BATCH_SLEEP = 1
        self.flow.NODES_PER_BATCH = 2

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.execute_flow')
    def test_run__in_ncm_mef_02_is_successful(self, mock_execute_flow):
        self.ncm_mef_02.run()
        self.assertTrue(mock_execute_flow.called)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.fetch_ncm_vm")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.arguments.split_list_into_chunks')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.perform_nodes_realignment")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.keep_running')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.create_profile_users")
    def test_execute_flow__success(self, mock_create_profile_users, mock_keep_running, mock_nodes, mock_nodes_list,
                                   mock_realign, mock_nodes_per_batch, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_nodes_list.return_value = self.nodes
        mock_nodes.return_value = (self.nodes, [])
        mock_nodes_per_batch.return_value = self.nodes
        self.flow.execute_flow()
        self.assertEqual(2, len(mock_nodes_list.call_args[1]["node_attributes"]))
        self.assertTrue(mock_realign.called)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.fetch_ncm_vm")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.keep_running')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.create_profile_users")
    def test_execute_flow__raise_environ_error(self, mock_create_profile_users, mock_keep_running, mock_nodes,
                                               mock_nodes_list, mock_error, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_nodes_list.return_value = self.nodes
        mock_nodes.return_value = ([], self.nodes)
        self.flow.execute_flow()
        self.assertEqual(2, len(mock_nodes_list.call_args[1]["node_attributes"]))
        self.assertIsInstance(mock_error.call_args[0][0], EnvironError)

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.keep_running')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.NcmMef02Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.fetch_ncm_vm")
    def test_execute_flow__raises_environ_error_at_fetch_ncm_vm(self, mock_exception, mock_create_profile_users,
                                                                mock_keep_running, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_exception.return_value = "1.1.1.1"
        self.assertRaises(EnvironError, self.flow.execute_flow())

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.ncm_rest_query")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.json.dumps")
    def test_perform_nodes_realignment__success(self, mock_json, mock_ncm_rest_query, mock_log, _):
        mock_json.return_value = {"nodes": ["CORE77ML6691-002"]}
        self.flow.perform_nodes_realignment(self.user, self.nodes)
        self.assertTrue(mock_ncm_rest_query.called)
        self.assertEqual(3, mock_log.call_count)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.ncm_rest_query")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow.json.dumps")
    def test_perform_nodes_realignment__raises_enm_application_error(self, mock_json, mock_ncm_rest_query, _):
        mock_json.return_value = {"nodes": ["CORE77ML6691-002"]}
        mock_ncm_rest_query.side_effect = HTTPError
        self.assertRaises(EnmApplicationError, self.flow.perform_nodes_realignment, self.user, self.nodes)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
