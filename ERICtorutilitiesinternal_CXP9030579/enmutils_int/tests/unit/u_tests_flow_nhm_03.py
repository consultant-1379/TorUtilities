#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from requests.exceptions import HTTPError
from testslib import unit_test_utils

from enmutils.lib.enm_node import ERBSNode
from enmutils_int.lib.nhm import NhmKpi
from enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow import Nhm03


class Nhm03UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Nhm03()
        self.user = Mock()
        self.nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', '10.154.0.3', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        self.flow.REPORTING_OBJECT = ['ENodeBFunction']

        self.flow.NUM_KPIS = 2
        self.flow.ADMIN_ROLE = ["NHM_Administrator"]
        self.flow.OPERATOR_ROLE = ["NHM_Operator"]
        self.flow.NUM_ADMINS = 1
        self.flow.NUM_OPERATORS = 1
        self.flow.SCHEDULE_SLEEP = 2

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.get_all_kpi_names')
    def test_get_kpi_names(self, mock_get_all_kpi_names):
        mock_get_all_kpi_names.return_value = [['Total_UL_PDCP_Cell_Throughput'],
                                               ['Average_UL_PDCP_UE_Throughput_For_Carrier_Aggregation']]

        self.assertTrue(self.flow._get_kpi_names(self.user) == mock_get_all_kpi_names.return_value)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.get_all_kpi_names')
    def test_get_kpi_names_exception(self, mock_get_all_kpi_names):
        mock_get_all_kpi_names.return_value = [['Total_UL_PDCP_Cell_Throughput'],
                                               ['Average_UL_PDCP_UE_Throughput_For_Carrier_Aggregation']]
        mock_get_all_kpi_names.side_effect = Exception
        self.assertRaises(Exception, self.flow._get_kpi_names(self.user))

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.update')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.activate')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.create')
    def test_create_update_activate(self, mock_create, mock_activate, mock_update, mock_log_logger_debug, *_):
        kpi = NhmKpi(user=self.user, name="unit_test_kpi", nodes=self.nodes, reporting_objects=["EUtranCellFDD"],
                     created_by=self.user.username, active="false")

        self.flow._create_update_activate_kpi(kpi, self.nodes)

        self.assertEqual(1, mock_create.call_count)
        self.assertEqual(1, mock_activate.call_count)
        self.assertEqual(4, mock_update.call_count)
        self.assertTrue(mock_log_logger_debug.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.create')
    def test_create_update_activate__exception(self, mock_create, mock_log_logger_debug, *_):
        kpi = NhmKpi(user=self.user, name="unit_test_kpi", nodes=self.nodes, reporting_objects=["EUtranCellFDD"],
                     created_by=self.user.username, active="false")
        mock_create.side_effect = Exception
        self.flow._create_update_activate_kpi(kpi, self.nodes)

        self.assertTrue(mock_create.called)
        self.assertTrue(mock_log_logger_debug.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.log.logger.debug")
    def test_set_kpi(self, mock_log_logger_debug, *_):
        counters = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr']
        self.flow._set_kpi(counters, self.user, 0, self.nodes, ['ERBS'])

        self.assertTrue(mock_log_logger_debug.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.time.sleep")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.delete')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.deactivate')
    def test_deactivate_delete_kpis(self, mock_deactivate, mock_delete, mock_time_sleep):
        kpi1 = NhmKpi(user=self.user, name="unit_test_kpi_1", nodes=self.nodes, reporting_objects=["EUtranCellFDD"],
                      created_by=self.user.username, active="false")
        kpi2 = NhmKpi(user=self.user, name="unit_test_kpi_2", nodes=self.nodes, reporting_objects=["EUtranCellFDD"],
                      created_by=self.user.username, active="false")
        self.flow.teardown_list.append(kpi1)
        self.flow.teardown_list.append(kpi2)
        self.flow._deactivate_delete_kpis([kpi1, kpi2])

        self.assertEqual(2, mock_deactivate.call_count)
        self.assertEqual(2, mock_delete.call_count)
        self.assertEqual(2, mock_time_sleep.call_count)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.time.sleep")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.delete')
    def test_deactivate_delete_kpis__exception(self, mock_delete, mock_add_error, *_):
        kpi1 = NhmKpi(user=self.user, name="unit_test_kpi_1", nodes=self.nodes, reporting_objects=["EUtranCellFDD"],
                      created_by=self.user.username, active="false")
        kpi2 = NhmKpi(user=self.user, name="unit_test_kpi_2", nodes=self.nodes, reporting_objects=["EUtranCellFDD"],
                      created_by=self.user.username, active="false")
        self.flow.teardown_list.append(kpi1)
        self.flow.teardown_list.append(kpi2)
        mock_delete.side_effect = Exception('Some error')
        self.flow._deactivate_delete_kpis([kpi1, kpi2])
        self.assertEqual(1, mock_add_error.call_count)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.get_counters_specified_by_nhm')
    def test_get_counters(self, mock_get_counters_specified_by_nhm, mock_log_logger_debug):
        mock_get_counters_specified_by_nhm.return_value = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr',
                                                           'pmLicConnectedUsersLicense', 'pmRrcConnBrEnbMax',
                                                           'pmMoFootprintMax', 'pmLicConnectedUsersMax', 'pmPagS1EdrxReceived']

        self.flow._get_counters(ne_types=['ERBS', 'RadioNode'], reporting_objects=['ENodeBFunction'])

        self.assertEqual(2, mock_get_counters_specified_by_nhm.call_count)
        self.assertEqual(1, mock_log_logger_debug.call_count)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.get_counters_specified_by_nhm')
    def test_get_counters_exception(self, mock_get_counters_specified_by_nhm):
        mock_get_counters_specified_by_nhm.return_value = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr',
                                                           'pmLicConnectedUsersLicense', 'pmRrcConnBrEnbMax',
                                                           'pmMoFootprintMax', 'pmLicConnectedUsersMax',
                                                           'pmPagS1EdrxReceived']
        mock_get_counters_specified_by_nhm.side_effect = Exception

        self.assertRaises(Exception, self.flow._get_counters(ne_types=['ERBS', 'RadioNode'], reporting_objects=['ENodeBFunction']))

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.time.sleep")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.get_kpi_info')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.get_nhm_kpi_home")
    def test_task_set__success(self, mock_get_nhm_kpi_home, mock_get_kpi_info, *_):

        self.flow.task_set(self.user, "kpi_name", self.flow)

        self.assertTrue(mock_get_nhm_kpi_home.called)
        self.assertTrue(mock_get_kpi_info.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.get_kpi_info')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.get_nhm_kpi_home")
    def test_task_set__exception(self, mock_get_nhm_kpi_home, mock_get_kpi_info, mock_add_error, *_):
        mock_get_nhm_kpi_home.side_effect = Exception
        self.flow.task_set(self.user, "kpi_name", self.flow)

        self.assertTrue(mock_get_nhm_kpi_home.called)
        self.assertTrue(mock_add_error.called)
        self.assertFalse(mock_get_kpi_info.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.remove_kpis_by_pattern_new')
    def test_clean_kpi_system__success(self, mock_remove_kpis, mock_add_error):
        self.flow._clean_kpi_system(self.flow, self.user)
        self.assertTrue(mock_remove_kpis.called)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.NhmKpi.remove_kpis_by_pattern_new')
    def test_clean_kpi_system__exception(self, mock_remove_kpis, mock_add_error):
        mock_remove_kpis.side_effect = HTTPError
        self.flow._clean_kpi_system(self.flow, self.user)
        self.assertTrue(mock_remove_kpis.called)
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03._get_kpi_names')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03._get_counters")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03._clean_kpi_system")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.create_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.setup_nhm_profile')
    def test_execute_flow_success(self, mock_setup_nhm, mock_create_users, mock_clean_kpi_system, mock_get_counters,
                                  mock_get_all_kpi_names, *_):
        mock_setup_nhm.return_value = [self.user], self.nodes
        mock_create_users.return_value = [self.user]
        mock_get_counters.return_value = ['counter_01', 'counter_02', 'counter_03']
        mock_get_all_kpi_names.return_value = [['Added_E-RAB_Establishment_Success_Rate'],
                                               ['Initial_E-RAB_Establishment_Success_Rate'],
                                               ['Average_MAC_Cell_DL_Throughput'],
                                               ['Average_UE_PDCP_DL_Throughput'],
                                               ['VoIP_Cell_Integrity']]

        with patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.'
                   'sleep_until_time') as mock_sleep_until_time:
            with patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.'
                       '_set_kpi') as mock_set_kpi:
                with patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03."
                           "_create_update_activate_kpi") as mock_create_update_activate:
                    with patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03."
                               "create_and_execute_threads") as mock_create_and_execute_threads:
                        with patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03."
                                   "_deactivate_delete_kpis") as mock_deactivate_delete:

                            self.flow.execute_flow()

                            self.assertTrue(mock_setup_nhm.called)
                            self.assertTrue(mock_create_users.called)
                            self.assertTrue(mock_clean_kpi_system.called)
                            self.assertTrue(mock_get_counters.called)
                            self.assertTrue(mock_set_kpi.called)
                            self.assertTrue(mock_get_all_kpi_names.called)
                            self.assertTrue(mock_create_update_activate.called)
                            self.assertTrue(mock_deactivate_delete.called)
                            self.assertTrue(mock_create_and_execute_threads.called)
                            self.assertTrue(mock_sleep_until_time.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03._get_kpi_names')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03._get_counters")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03._clean_kpi_system")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.create_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.setup_nhm_profile')
    def test_execute_flow__no_kpis(self, mock_setup_nhm, mock_create_users, mock_clean_kpi_system, mock_get_counters,
                                   mock_get_all_kpi_names, *_):
        mock_setup_nhm.return_value = [self.user], self.nodes
        mock_create_users.return_value = [self.user]
        mock_get_counters.return_value = ['counter_01', 'counter_02', 'counter_03']
        mock_get_all_kpi_names.return_value = []

        with patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.'
                   'sleep_until_time') as mock_sleep_until_time:
            with patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.'
                       '_set_kpi') as mock_set_kpi:
                with patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03."
                           "_create_update_activate_kpi") as mock_create_update_activate:
                    with patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03."
                               "create_and_execute_threads") as mock_create_and_execute_threads:
                        with patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03."
                                   "_deactivate_delete_kpis") as mock_deactivate_delete:

                            self.flow.execute_flow()

                            self.assertTrue(mock_setup_nhm.called)
                            self.assertTrue(mock_create_users.called)
                            self.assertTrue(mock_clean_kpi_system.called)
                            self.assertTrue(mock_get_counters.called)
                            self.assertTrue(mock_set_kpi.called)
                            self.assertTrue(mock_get_all_kpi_names.called)
                            self.assertTrue(mock_create_update_activate.called)
                            self.assertTrue(mock_deactivate_delete.called)
                            self.assertFalse(mock_create_and_execute_threads.called)
                            self.assertTrue(mock_sleep_until_time.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
