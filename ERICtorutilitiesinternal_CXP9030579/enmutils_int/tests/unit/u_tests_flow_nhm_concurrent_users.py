#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from testslib import unit_test_utils
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow import NhmConcurrentUsersFlow


class NhmConcurrentUsersFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = NhmConcurrentUsersFlow()
        self.users = [Mock(), Mock(), Mock(), Mock(), Mock()]
        self.nodes = unit_test_utils.get_nodes(2)
        self.flow.REPORTING_OBJECT = ['ENodeBFunction']
        self.flow.NUM_KPIS = 2
        self.flow.USER_ROLES = ["NHM_Operator"]
        self.flow.NUM_OPERATORS = 5
        self.flow.SCHEDULE_SLEEP = 2
        self.flow.WIDGETS = ["NodesBreached", "WorstPerforming", "MostProblematic", "NetworkOperationalState",
                             "NetworkSyncStatus"]
        self.widgets = ["NodesBreached", "WorstPerforming", "MostProblematic", "NetworkOperationalState",
                        "NetworkSyncStatus"]

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_widget_iterator_success(self):
        widget_iterator = self.flow.get_widget_iterator(self.widgets)
        self.assertTrue(widget_iterator.next() in ['NodesBreached', 'WorstPerforming', 'MostProblematic',
                                                   'NetworkOperationalState', 'NetworkSyncStatus'])

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.time.sleep')
    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkSyncStatus')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.WorstPerforming')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmKpi.get_all_kpi_names_active')
    def test_init_widget_objects_success(self, mock_get_all_kpi_names_active, mock_nodes_breached,
                                         mock_worst_performing, mock_most_problematic, mock_net_op_state,
                                         mock_net_sync_status, mock_teardown_append, *_):

        mock_get_all_kpi_names_active.return_value = [['Added_E-RAB_Establishment_Success_Rate'],
                                                      ['Initial_E-RAB_Establishment_Success_Rate'],
                                                      ['Average_MAC_Cell_DL_Throughput'],
                                                      ['Average_UE_PDCP_DL_Throughput'],
                                                      ['VoIP_Cell_Integrity']]

        self.flow.init_widgets(self.users, self.nodes, self.widgets)
        self.assertTrue(mock_get_all_kpi_names_active.called, 5)
        self.assertTrue(mock_nodes_breached.called)
        self.assertTrue(mock_worst_performing.called)
        self.assertTrue(mock_most_problematic.called)
        self.assertTrue(mock_net_op_state.called)
        self.assertTrue(mock_net_sync_status.called)
        self.assertTrue(mock_teardown_append.called)

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkSyncStatus')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.WorstPerforming')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmKpi.get_all_kpi_names_active')
    def test_init_widget_objects_no_active_kpis_adds_error_as_exception_and_continues(self,
                                                                                      mock_get_all_kpi_names_active,
                                                                                      mock_sleep, mock_add_error, *_):

        mock_get_all_kpi_names_active.side_effect = [], ['Added_E-RAB_Establishment_Success_Rate']
        self.flow.init_widgets(self.users, self.nodes, self.widgets)
        self.assertEqual(mock_get_all_kpi_names_active.call_count, 3)
        self.assertEqual(mock_add_error.call_count, 2)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkSyncStatus')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.WorstPerforming')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmKpi.get_all_kpi_names_active')
    def test_init_widget_objects_adds_error_as_exception_and_continues(self, mock_get_all_kpi_names_active, mock_sleep,
                                                                       mock_add_error, *_):

        mock_get_all_kpi_names_active.side_effect = EnvironError, ['Added_E-RAB_Establishment_Success_Rate']
        self.flow.init_widgets(self.users, self.nodes, self.widgets)
        self.assertEqual(mock_get_all_kpi_names_active.call_count, 3)
        self.assertEqual(mock_add_error.call_count, 2)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkSyncStatus')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.WorstPerforming')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmKpi.get_all_kpi_names_active')
    def test_init_widget_objects_does_not_add_error_at_specified_num_exceptions(self, mock_get_all_kpi_names_active, mock_sleep, mock_add_error, *_):

        mock_get_all_kpi_names_active.side_effect = (EnvironError, EnvironError, EnvironError, EnvironError,
                                                     EnvironError, EnvironError, ['Added_E-RAB_Establishment_Success_Rate'])
        self.flow.init_widgets(self.users, self.nodes, self.widgets)
        self.assertEqual(mock_add_error.call_count, 4)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkSyncStatus')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.WorstPerforming')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.nhm_ui.call_widget_flow')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.process_thread_queue_errors')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.ThreadQueue')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.create_and_configure_widgets')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmKpi.get_all_kpi_names_active')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.setup_nhm_profile')
    def test_execute_profile_flow_is_successful(self, mock_setup, mock_get_all_kpi_names_active, mock_create_and_configure,
                                                mock_keep_running, mock_thread_queue, mock_process_tq_errors, mock_sleep,
                                                mock_call_widget_flow, *_):
        mock_setup.return_value = self.users, self.nodes
        mock_get_all_kpi_names_active.return_value = [['Added_E-RAB_Establishment_Success_Rate'],
                                                      ['Initial_E-RAB_Establishment_Success_Rate'],
                                                      ['Average_MAC_Cell_DL_Throughput'],
                                                      ['Average_UE_PDCP_DL_Throughput'],
                                                      ['VoIP_Cell_Integrity']]
        mock_keep_running.side_effect = [True, False]

        self.flow.execute_profile_flow()
        self.assertTrue(mock_setup.called)
        self.assertTrue(mock_get_all_kpi_names_active.called)
        self.assertTrue(mock_create_and_configure.called)
        mock_thread_queue.execute.assert_called()
        mock_thread_queue.assert_any_calls(self.widgets, func_ref=mock_call_widget_flow, num_workers=5)
        mock_process_tq_errors.assert_any_calls(last_error_only=True)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkSyncStatus')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.WorstPerforming')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.nhm_ui.call_widget_flow')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.process_thread_queue_errors')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.ThreadQueue')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.create_and_configure_widgets')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmKpi.get_all_kpi_names_active')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow.NhmConcurrentUsersFlow.setup_nhm_profile')
    def test_execute_profile_flow_does_not_run_when_keep_running_is_false(self, mock_setup, mock_get_all_kpi_names_active,
                                                                          mock_create_and_configure, mock_keep_running,
                                                                          mock_thread_queue, mock_process_tq_errors,
                                                                          mock_sleep, mock_call_widget_flow, *_):
        mock_setup.return_value = self.users, self.nodes
        mock_get_all_kpi_names_active.return_value = [['Added_E-RAB_Establishment_Success_Rate'],
                                                      ['Initial_E-RAB_Establishment_Success_Rate'],
                                                      ['Average_MAC_Cell_DL_Throughput'],
                                                      ['Average_UE_PDCP_DL_Throughput'],
                                                      ['VoIP_Cell_Integrity']]
        mock_keep_running.side_effect = [False, False]

        self.flow.execute_profile_flow()
        self.assertTrue(mock_setup.called)
        self.assertTrue(mock_get_all_kpi_names_active.called)
        self.assertTrue(mock_create_and_configure.called)
        mock_thread_queue.execute.assert_called()
        mock_thread_queue.assert_any_calls(self.widgets, func_ref=mock_call_widget_flow, num_workers=5)
        mock_process_tq_errors.assert_any_calls(last_error_only=True)
        self.assertFalse(mock_sleep.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
