#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow import Nhm12
from mock import patch, Mock, PropertyMock, call
from requests.exceptions import HTTPError
from testslib import unit_test_utils


class Nhm12UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Nhm12()
        self.flow.USER_ROLES = ["NHM_Administrator"]
        self.flow.NODES = {"RadioNode": 2}
        self.flow.teardown_list = []

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.time', return_value=12345)
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.wait_for_nhm_setup_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.NhmKpi')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.allocate_nodes_from_other_profile')
    def test_execute_flow__in_nhm_12_flow_is_successful(
            self, mock_allocate_nodes_from_other_profile, mock_nhmkpi, mock_log, mock_wait_for_setup_profile,
            mock_create_users, *_):
        nodes = [Mock(primary_type="RadioNode") for _ in xrange(2)]
        mock_allocate_nodes_from_other_profile.return_value = nodes

        nhm_12_kpi = mock_nhmkpi.return_value
        mock_user = Mock()
        mock_create_users.return_value = [mock_user]
        self.flow.execute_flow()

        self.assertTrue(mock_wait_for_setup_profile.called)
        self.assertTrue(call(mock_user, "NHM12KPI12345", nodes=nodes, reporting_objects=['eNodeBFunction'],
                             node_types=['RadioNode'], threshold_value=3, threshold_domain="LESS_THAN")
                        in mock_nhmkpi.mock_calls)

        self.assertTrue(nhm_12_kpi.activate.called)
        self.assertTrue(mock_log.logger.info.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.time', return_value=12345)
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.wait_for_nhm_setup_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.allocate_nodes_from_other_profile',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.NhmKpi')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.add_error_as_exception')
    def test_execute_flow__in_nhm_12_flow_adds_error_if_no_nodes_allocated(
            self, mock_add_error_as_exception, mock_nhmkpi, mock_log, *_):
        self.flow.execute_flow()

        self.assertFalse(mock_nhmkpi.called)
        self.assertFalse(mock_log.logger.info.called)
        self.assertFalse(mock_nhmkpi.return_value.activate.called)
        message = ("No ENodeB Radionodes/ERBS allocated. Profile needs to use subset of Radionodes/ERBS assigned to "
                   "setup profile: NHM_SETUP")
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertEqual(str(mock_add_error_as_exception.mock_calls[0]), str(call(EnvironError(message))))

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.time', return_value=12345)
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.wait_for_nhm_setup_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.allocate_nodes_from_other_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.NhmKpi')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.add_error_as_exception')
    def test_execute_flow__in_nhm_12_flow_adds_error_if_httperror_occurs_during_create(
            self, mock_add_error_as_exception, mock_nhmkpi, mock_log, *_):
        mock_nhmkpi.return_value.create.side_effect = HTTPError("some_error")
        self.flow.execute_flow()

        self.assertFalse(mock_log.logger.info.called)
        self.assertFalse(mock_nhmkpi.return_value.activate.called)

        message = "Error occurred during NHM_12 KPI creation msg: some_error"
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertEqual(str(mock_add_error_as_exception.mock_calls[0]), str(call(EnvironError(message))))

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.get_nodes_list_by_attribute',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.allocate_specific_nodes_to_profile")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.get_allocated_nodes")
    def test_allocate_nodes_from_other_profile__is_successful(
            self, mock_get_allocated_nodes, mock_allocate_specific_nodes_to_profile, *_):
        nodes = [Mock(primary_type="RadioNode") for _ in xrange(3)]
        mock_get_allocated_nodes.return_value = nodes
        node_type = "RadioNode"
        self.flow.allocate_nodes_from_other_profile("some_profile", node_type)
        self.assertTrue(len(mock_allocate_specific_nodes_to_profile._mock_call_args) ==
                        self.flow.NODES[node_type])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
