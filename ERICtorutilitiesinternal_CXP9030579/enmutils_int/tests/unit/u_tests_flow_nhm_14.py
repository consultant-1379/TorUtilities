#!/usr/bin/env python
import unittest2
from enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow import Nhm14Flow
from mock import patch, Mock
from testslib import unit_test_utils


class Nhm14UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Nhm14Flow()
        self.user = Mock()
        self.nodes = [Mock(), Mock()]
        self.flow.OPERATOR_ROLE = ["NHM_Operator"]
        self.flow.NUM_OPERATORS = 1
        self.flow.REPORTING_OBJECT = {'ERBS': ['EUtranCellFDD', 'EUtranCellTDD'],
                                      'RadioNode': ['EUtranCellFDD', 'EUtranCellTDD']}
        self.flow.SUPPORTED_TYPES_CUSTOM_CELL_LEVEL_KPI = ['ERBS', 'RadioNode']
        self.flow.SCHEDULE_SLEEP = 2
        self.flow.NUMBER_OF_KPIS = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.Nhm14Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.Nhm14Flow.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.get_nhm_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.NhmKpi.get_counters_specified_by_nhm')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.time.sleep")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.NhmKpi.create')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.Nhm14Flow.create_profile_users')
    def test_execute_flow__in_nhm_14_flow_is_successful(self, mock_create_profile_users, mock_create, mock_log,
                                                        mock_sleep, mock_get_counters, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_get_counters.return_value = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr',
                                          'pmLicConnectedUsersLicense', 'pmRrcConnBrEnbMax', 'pmMoFootprintMax',
                                          'pmLicConnectedUsersMax', 'pmPagS1EdrxReceived']

        self.flow.execute_flow()
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_log.logger.info.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.Nhm14Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.Nhm14Flow.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.get_nhm_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.NhmKpi.get_counters_specified_by_nhm')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.Nhm14Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.NhmKpi.create')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.Nhm14Flow.create_profile_users')
    def test_execute_flow__in_nhm_14_flow_exception(self, mock_create_profile_users, mock_create, mock_add_error,
                                                    mock_get_counters, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_get_counters.return_value = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr',
                                          'pmLicConnectedUsersLicense', 'pmRrcConnBrEnbMax', 'pmMoFootprintMax',
                                          'pmLicConnectedUsersMax', 'pmPagS1EdrxReceived']
        mock_create.side_effect = Exception

        self.flow.execute_flow()
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_add_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
