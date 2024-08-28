#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock, call
from testslib import unit_test_utils

from enmutils_int.lib.workload import asr_n_01
from enmutils_int.lib.profile_flows.asrn_flows.asrn_flow import ASRN01Profile, EnvironError


class ASRN01FlowUnitTests(unittest2.TestCase):

    asrn_record_updated_response = {u'lastActivationTime': 1607594689712, u'pmicSubscriptionPoid': 12100,
                                    u'scheduleInfo': None, u'name': u'ASR-N', u'resourcesPoIds': [27246, 27227, 27389],
                                    u'asrConfigurationId': u'ASR-N', u'administrationState': u'INACTIVE',
                                    u'streamInfo': {u'ipAddress': u'141.137.172.163', u'port': 443},
                                    u'fdn': u'ASRLConfiguration=ASR-N', u'poid': 9100,
                                    u'cbs': False, u'lastModifiedUser': u'ASR_N_01_1210-10410041_u0',
                                    u'persistenceTime': 1607596869055, u'criteriaSpecification': None,
                                    u'fields': [{u'name': u'dataRadioBearerSetupTime'},
                                                {u'name': u'hoCompletionTimeTgtCell'},
                                                {u'name': u'initCtxtSetupTime'}], u'owner': u'ASR',
                                    u'lastModifiedTime': 1607596869001, u'operationalState': u'NA', u'type': u'ASR_L',
                                    u'lastDeactivationTime': 1607596785583,
                                    u'description': u'Analytic Session Record for LTE Radio'}

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.asrn_01 = asr_n_01.ASR_N_01()
        self.asrn01flow = ASRN01Profile()
        self.nodes_list = [Mock(poid="27246", primary_type="RadioNode", node_id="LTE98dg2ERBS00001",
                                profiles=["ASR_N_01"]),
                           Mock(poid="27227", primary_type="RadioNode", node_id="LTE98dg2ERBS00002",
                                profiles=["ASR_N_01"]),
                           Mock(poid="27389", primary_type="RadioNode", node_id="LTE98dg2ERBS00003",
                                profiles=["ASR_N_01"])]
        self.asrn01flow.USER_ROLES = ["ASR_Administrator", "ASR-L_Administrator", "Cmedit_Administrator"]
        self.asrn01flow.SLEEP_TIME = 60
        self.asrn01flow.USER = self.user
        self.asrn01flow.NB_IP = unit_test_utils.generate_configurable_ip()
        self.asrn01flow.PORT = "443"
        self.asrn01flow.NUMBER_OF_CELLS = 2
        self.asrn01flow.MO_TYPE = "NRcellCU"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.ASRN01Profile.execute_flow")
    def test_run__in_asrn_01_is_successful(self, _):
        self.asrn_01.run()

    # execute_flow test cases
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.ASRN01Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.ASRN01Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.ASRN01Profile.perform_asrn_operations")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.ASRN01Profile.create_profile_users")
    def test_execute_flow__is_successful(self, mock_create_profile_users, mock_perform_asrn_operations, mock_add_error,
                                         *_):
        mock_create_profile_users.return_value = [self.user]
        self.asrn01flow.execute_flow()
        self.assertTrue(mock_perform_asrn_operations.called)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.ASRN01Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.ASRN01Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.ASRN01Profile.perform_asrn_operations")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.ASRN01Profile.create_profile_users")
    def test_execute_flow__adds_error_if_str_cluster_not_exist(self, mock_create_profile_users,
                                                               mock_perform_asrn_operations, mock_add_error, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_perform_asrn_operations.side_effect = EnvironError("Required STR Clusters not found or ASRL not "
                                                                "configured in ENM")
        self.asrn01flow.execute_flow()
        self.assertTrue(mock_perform_asrn_operations.called)
        self.assertTrue(call(mock_perform_asrn_operations.side_effect in mock_add_error.mock_calls))

    # perform_asrn_operations test cases
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.perform_asr_preconditions_and_postconditions")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.output_network_basic")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.check_if_asr_record_nb_ip_port_configured")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.get_asr_config_status")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.enm_deployment.check_if_cluster_exists")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.GenericFlow.get_allocated_synced_pm_enabled_nodes")
    def test_perform_asrn_operations__is_successful(self, mock_get_nodes, mock_check_if_cluster_exists,
                                                    mock_get_asr_config_status,
                                                    mock_check_if_asr_record_nb_ip_port_configured,
                                                    mock_output_network_basic, mock_perform_asr_conditions):
        mock_check_if_cluster_exists.return_value = True
        mock_get_asr_config_status.return_value = True
        mock_check_if_asr_record_nb_ip_port_configured.return_value = True
        self.asrn01flow.perform_asrn_operations()
        mock_check_if_cluster_exists.assert_called_with("str")
        mock_get_asr_config_status.assert_called_with(self.asrn01flow.USER, "ASR-N")
        self.assertTrue(mock_check_if_asr_record_nb_ip_port_configured.called)
        self.assertTrue(mock_get_nodes.called)
        self.assertTrue(mock_perform_asr_conditions.called)
        self.assertFalse(mock_output_network_basic.called)

    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.perform_asr_preconditions_and_postconditions")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.GenericFlow.get_allocated_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.output_network_basic")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.check_if_asr_record_nb_ip_port_configured")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.get_asr_config_status")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.enm_deployment.check_if_cluster_exists")
    def test_perform_asrn_operations__raises_env_error_if_str_cluster_not_exist(
            self, mock_check_if_cluster_exists, mock_get_asr_config_status,
            mock_check_if_asr_record_nb_ip_port_configured, mock_output_network_basic, *_):
        mock_check_if_cluster_exists.return_value = False
        mock_get_asr_config_status.return_value = True
        self.assertRaises(EnvironError, self.asrn01flow.perform_asrn_operations)
        mock_check_if_cluster_exists.assert_called_with("str")
        self.assertFalse(mock_get_asr_config_status.called)
        self.assertFalse(mock_check_if_asr_record_nb_ip_port_configured.called)
        self.assertFalse(mock_output_network_basic.called)

    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.perform_asr_preconditions_and_postconditions")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.GenericFlow.get_allocated_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.output_network_basic")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.check_if_asr_record_nb_ip_port_configured")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.get_asr_config_status")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.enm_deployment.check_if_cluster_exists")
    def test_perform_asrn_operations__raises_env_error_if_asrn_not_configured_in_enm(
            self, mock_check_if_cluster_exists, mock_get_asr_config_status,
            mock_check_if_asr_record_nb_ip_port_configured, mock_output_network_basic, *_):
        mock_check_if_cluster_exists.return_value = True
        mock_get_asr_config_status.return_value = False
        self.assertRaises(EnvironError, self.asrn01flow.perform_asrn_operations)
        mock_check_if_cluster_exists.assert_called_with("str")
        mock_get_asr_config_status.assert_called_with(self.asrn01flow.USER, "ASR-N")
        self.assertFalse(mock_check_if_asr_record_nb_ip_port_configured.called)
        self.assertFalse(mock_output_network_basic.called)

    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.perform_asr_preconditions_and_postconditions")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.GenericFlow.get_allocated_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.output_network_basic")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.check_if_asr_record_nb_ip_port_configured")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.get_asr_config_status")
    @patch("enmutils_int.lib.profile_flows.asrn_flows.asrn_flow.enm_deployment.check_if_cluster_exists")
    def test_perform_asrn_operations__raises_env_error_if_nbip_port_not_configured(
            self, mock_check_if_cluster_exists, mock_get_asr_config_status,
            mock_check_if_asr_record_nb_ip_port_configured, mock_output_network_basic, *_):
        mock_check_if_cluster_exists.return_value = True
        mock_get_asr_config_status.return_value = True
        mock_check_if_asr_record_nb_ip_port_configured.return_value = False
        self.assertRaises(EnvironError, self.asrn01flow.perform_asrn_operations)
        mock_check_if_cluster_exists.assert_called_with("str")
        mock_get_asr_config_status.assert_called_with(self.asrn01flow.USER, "ASR-N")
        self.assertTrue(mock_check_if_asr_record_nb_ip_port_configured.called)
        self.assertTrue(mock_output_network_basic.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
