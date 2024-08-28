#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock, call
from testslib import unit_test_utils

from enmutils_int.lib.workload import asr_l_01
from enmutils_int.lib.profile_flows.asr_flows.asrl_flow import ASRL01Profile, EnvironError


class ASRL01FlowUnitTests(unittest2.TestCase):

    asrl_record_updated_response = {u'lastActivationTime': 1607594689712, u'pmicSubscriptionPoid': 12100,
                                    u'scheduleInfo': None, u'name': u'ASR-L', u'resourcesPoIds': [27246, 27227, 27389],
                                    u'asrConfigurationId': u'ASR-L', u'administrationState': u'INACTIVE',
                                    u'streamInfo': {u'ipAddress': u'141.137.172.163', u'port': 443},
                                    u'fdn': u'ASRLConfiguration=ASR-L', u'poid': 9100,
                                    u'cbs': False, u'lastModifiedUser': u'ASR_L_01_1210-10410041_u0',
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
        self.asrl_01 = asr_l_01.ASR_L_01()
        self.asrl01flow = ASRL01Profile()
        self.nodes_list = [Mock(poid="27246", primary_type="RadioNode", node_id="LTE98dg2ERBS00001",
                                profiles=["ASR_L_01"]),
                           Mock(poid="27227", primary_type="ERBS", node_id="netsim_LTE02ERBS00040",
                                profiles=["ASR_L_01"]),
                           Mock(poid="27389", primary_type="ERBS", node_id="netsim_LTE02ERBS00041",
                                profiles=["ASR_L_01"])]
        self.asrl01flow.USER_ROLES = ["ASR_Administrator", "ASR-L_Administrator", "Cmedit_Administrator"]
        self.asrl01flow.SLEEP_TIME = 60
        self.asrl01flow.USER = self.user
        self.asrl01flow.NB_IP = unit_test_utils.generate_configurable_ip()
        self.asrl01flow.PORT = "443"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.execute_flow")
    def test_run__in_asrl_01_is_successful(self, _):
        self.asrl_01.run()

    # execute_flow test cases
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.perform_asrl_operations")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.create_profile_users")
    def test_execute_flow__is_successful(self, mock_create_profile_users, mock_perform_asrl_operations, mock_add_error,
                                         *_):
        mock_create_profile_users.return_value = [self.user]
        self.asrl01flow.execute_flow()
        self.assertTrue(mock_perform_asrl_operations.called)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.perform_asrl_operations")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.create_profile_users")
    def test_execute_flow__adds_error_if_str_cluster_not_exist(self, mock_create_profile_users,
                                                               mock_perform_asrl_operations, mock_add_error, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_perform_asrl_operations.side_effect = EnvironError("Required STR Clusters not found or ASRL not "
                                                                "configured in ENM")
        self.asrl01flow.execute_flow()
        self.assertTrue(mock_perform_asrl_operations.called)
        self.assertTrue(call(mock_perform_asrl_operations.side_effect in mock_add_error.mock_calls))

    # perform_asrl_operations test cases
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.output_network_basic")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.check_if_asr_record_nb_ip_port_configured")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.get_asr_config_status")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.enm_deployment.check_if_cluster_exists")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.perform_asr_preconditions_and_postconditions")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.GenericFlow.get_allocated_synced_pm_enabled_nodes")
    def test_perform_asrl_operations__is_successful(self, mock_get_synced_pm_enabled_nodes, mock_perform_operations,
                                                    mock_check_if_cluster_exists, mock_get_asr_config_status,
                                                    mock_check_if_asr_record_nb_ip_port_configured,
                                                    mock_output_network_basic):
        mock_check_if_cluster_exists.return_value = True
        mock_get_asr_config_status.return_value = True
        mock_check_if_asr_record_nb_ip_port_configured.return_value = True
        mock_get_synced_pm_enabled_nodes.return_value = self.nodes_list[:2]
        self.asrl01flow.perform_asrl_operations()
        mock_check_if_cluster_exists.assert_called_with("str")
        mock_get_asr_config_status.assert_called_with(self.asrl01flow.USER, "ASR-L")
        self.assertTrue(mock_check_if_asr_record_nb_ip_port_configured.called)
        self.assertTrue(mock_perform_operations.called)
        self.assertFalse(mock_output_network_basic.called)

    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.perform_asr_preconditions_and_postconditions")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.GenericFlow.get_allocated_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.output_network_basic")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.check_if_asr_record_nb_ip_port_configured")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.get_asr_config_status")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.enm_deployment.check_if_cluster_exists")
    def test_perform_asrl_operations__raises_env_error_if_str_cluster_not_exist(
            self, mock_check_if_cluster_exists, mock_get_asr_config_status,
            mock_check_if_asr_record_nb_ip_port_configured, mock_output_network_basic, *_):
        mock_check_if_cluster_exists.return_value = False
        mock_get_asr_config_status.return_value = True
        self.assertRaises(EnvironError, self.asrl01flow.perform_asrl_operations)
        mock_check_if_cluster_exists.assert_called_with("str")
        self.assertFalse(mock_get_asr_config_status.called)
        self.assertFalse(mock_check_if_asr_record_nb_ip_port_configured.called)
        self.assertFalse(mock_output_network_basic.called)

    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.perform_asr_preconditions_and_postconditions")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.GenericFlow.get_allocated_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.output_network_basic")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.check_if_asr_record_nb_ip_port_configured")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.get_asr_config_status")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.enm_deployment.check_if_cluster_exists")
    def test_perform_asrl_operations__raises_env_error_if_asrn_not_configured_in_enm(
            self, mock_check_if_cluster_exists, mock_get_asr_config_status,
            mock_check_if_asr_record_nb_ip_port_configured, mock_output_network_basic, *_):
        mock_check_if_cluster_exists.return_value = True
        mock_get_asr_config_status.return_value = False
        self.assertRaises(EnvironError, self.asrl01flow.perform_asrl_operations)
        mock_check_if_cluster_exists.assert_called_with("str")
        mock_get_asr_config_status.assert_called_with(self.asrl01flow.USER, "ASR-L")
        self.assertFalse(mock_check_if_asr_record_nb_ip_port_configured.called)
        self.assertFalse(mock_output_network_basic.called)

    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.perform_asr_preconditions_and_postconditions")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.GenericFlow.get_allocated_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.output_network_basic")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.check_if_asr_record_nb_ip_port_configured")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.get_asr_config_status")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.enm_deployment.check_if_cluster_exists")
    def test_perform_asrl_operations__raises_env_error_if_nbip_port_not_configured(
            self, mock_check_if_cluster_exists, mock_get_asr_config_status,
            mock_check_if_asr_record_nb_ip_port_configured, mock_output_network_basic, *_):
        mock_check_if_cluster_exists.return_value = True
        mock_get_asr_config_status.return_value = True
        mock_check_if_asr_record_nb_ip_port_configured.return_value = False
        self.assertRaises(EnvironError, self.asrl01flow.perform_asrl_operations)
        mock_check_if_cluster_exists.assert_called_with("str")
        mock_get_asr_config_status.assert_called_with(self.asrl01flow.USER, "ASR-L")
        self.assertTrue(mock_check_if_asr_record_nb_ip_port_configured.called)
        self.assertTrue(mock_output_network_basic.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
