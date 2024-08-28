#!/usr/bin/env python
import datetime
import unittest2
from mock import patch, Mock, call
from requests.exceptions import HTTPError
from enmutils.lib.exceptions import EnvironError

from enmutils_int.lib.services import deployment_info_helper_methods as helper
from testslib import unit_test_utils

ENIQ_SERVER_ERR_MSG = "Unable to determine if ENIQ Server is integrated."
TEXT = """cellcounts_tableParam = {
    "data": [
        {
            "mo": "Total",
            "namespace": "",
            "count": 80253
        }
    ],
    "downloadURL": """
TEXT_1 = """cellcounts = {
    "data": [
        {
            "mo": "Total",
            "namespace": "",
            "count": 80253
        }
    ],
    "downloadURL": """


class DeploymentInfoHelperMethodsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=0)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_cell_count_from_cmedit', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_ddp_total_cell_count', return_value=0)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.set')
    def test_get_total_cell_count__returns_existing_key(self, mock_user, mock_set, *_):
        response = Mock()
        response.get_output.return_value = [u'', u'0 instance(s)']
        mock_user.return_value.enm_execute.return_value = response
        self.assertEqual(0, helper.get_total_cell_count())
        self.assertEqual(0, mock_set.call_count)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=10)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.set')
    def test_get_total_cell_count__returns_non_zero(self, mock_user, mock_set, *_):
        response = Mock()
        response.get_output.return_value = [u'', u'0 instance(s)']
        mock_user.return_value.enm_execute.return_value = response
        self.assertEqual(10, helper.get_total_cell_count())
        self.assertEqual(0, mock_set.call_count)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.set')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    def test_get_total_cell_count__success_from_cmedit(self, mock_user, mock_set, *_):
        response = Mock()
        response.get_output.return_value = [u'', u'500 instance(s)']
        mock_user.return_value.enm_execute.return_value = response
        self.assertEqual(500, helper.get_total_cell_count())
        self.assertEqual(1, mock_set.call_count)
        mock_user.return_value.enm_execute.assert_called_with('cmedit get * EUtranCellFDD;EUtranCellTDD;UtranCell;'
                                                              'GeranCell;NRCellCU -cn', timeout_seconds=1200)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_cell_count_from_cmedit', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.set')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_ddp_total_cell_count', return_value=500)
    def test_get_total_cell_count__success_from_ddp(self, mock_ddp, mock_set, *_):
        self.assertEqual(500, helper.get_total_cell_count())
        self.assertEqual(1, mock_set.call_count)
        self.assertTrue(mock_ddp.called)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_cell_count_from_cmedit', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.set')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value='SOEM_5K_NETWORK')
    def test_get_total_cell_count__to_check_deployment(self, mock_trans, mock_set, *_):
        self.assertEqual(0, helper.get_total_cell_count())
        self.assertEqual(0, mock_set.call_count)
        self.assertTrue(mock_trans.called)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.set')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_cell_count_from_cmedit', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_ddp_total_cell_count', return_value=None)
    def test_get_total_cell_count__raise_error(self, mock_ddp, mock_set, *_):
        self.assertEqual(0, helper.get_total_cell_count())
        self.assertEqual(1, mock_set.call_count)
        self.assertTrue(mock_ddp.called)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    def test_get_cell_count_from_cmedit__success(self, mock_user, *_):
        response = Mock()
        response.get_output.return_value = [u'', u'500 instance(s)']
        mock_user.return_value.enm_execute.return_value = response
        self.assertEqual(500, helper.get_cell_count_from_cmedit(1))
        mock_user.return_value.enm_execute.assert_called_with('cmedit get * EUtranCellFDD;EUtranCellTDD;UtranCell;'
                                                              'GeranCell;NRCellCU -cn', timeout_seconds=1200)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.time.sleep')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    def test_get_cell_count_from_cmedit__error_in_response(self, mock_user, *_):
        response = Mock()
        response.get_output.return_value = [u'', u'Error']
        mock_user.return_value.enm_execute.return_value = response
        self.assertEqual(None, helper.get_cell_count_from_cmedit(1))

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.time.sleep')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    def test_get_cell_count_from_cmedit__retries_with_no_response(self, mock_user, *_):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        mock_user.return_value.enm_execute.side_effect = [None, response]
        self.assertEqual(None, helper.get_cell_count_from_cmedit(1))

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_ddp_and_deployment_hostname')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_historic_date_and_directory_of_ddp')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.execute_ddp_url_and_fetch_cell_count')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug')
    def test_get_ddp_total_cell_count_success(self, mock_debug, mock_execute, mock_historic, mock_ddp_hostname, *_):
        mock_ddp_hostname.return_value = ("ddp_hostname", "deployment_hostname")
        mock_historic.return_value = (["previous_date_1", "previous_date_2", "previous_date_3"], ["dir_num_1", "dir_num_2", "dir_num_3"])
        mock_execute.return_value = 10
        self.assertEqual(10, helper.get_ddp_total_cell_count())
        mock_debug.assert_called_with("The max cell count value : 10 ")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_ddp_and_deployment_hostname')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_historic_date_and_directory_of_ddp')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.execute_ddp_url_and_fetch_cell_count')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug')
    def test_get_ddp_total_cell_count_failure(self, mock_debug, mock_execute, mock_historic, mock_ddp_hostname, *_):
        mock_ddp_hostname.return_value = (None, "deployment_hostname")
        helper.get_ddp_total_cell_count()

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.is_enm_on_cloud_native", return_value=True)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_hostname_in_cloud_native')
    def test_get_ddp_and_deployment_hostname__success_in_cloud_native(self, mock_get_hostname, *_):
        mock_get_hostname.return_value = ("ddp_cloud_native", "deployment_cloud_native")
        ddp_hostname, deployment_hostname = helper.get_ddp_and_deployment_hostname()
        self.assertEqual(ddp_hostname, "ddp_cloud_native")
        self.assertEqual(deployment_hostname, "deployment_cloud_native")

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.is_enm_on_cloud_native", return_value=False)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.config.is_a_cloud_deployment', return_value=True)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_hostname_cloud_deployment')
    def test_get_ddp_and_deployment_hostname__success_in_cloud(self, mock_get_hostname, *_):
        mock_get_hostname.return_value = ("ddp_cloud", "deployment_cloud")
        ddp_hostname, deployment_hostname = helper.get_ddp_and_deployment_hostname()
        self.assertEqual(ddp_hostname, "ddp_cloud")
        self.assertEqual(deployment_hostname, "deployment_cloud")

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.is_enm_on_cloud_native", return_value=False)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.config.is_a_cloud_deployment', return_value=False)
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.is_host_physical_deployment", return_value=True)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_hostname_physical_deployment')
    def test_get_ddp_and_deployment_hostname__success_in_physical(self, mock_get_hostname, *_):
        mock_get_hostname.return_value = ("ddp_physical", "deployment_physical")
        ddp_hostname, deployment_hostname = helper.get_ddp_and_deployment_hostname()
        self.assertEqual(ddp_hostname, "ddp_physical")
        self.assertEqual(deployment_hostname, "deployment_physical")

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.is_enm_on_cloud_native", return_value=False)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.config.is_a_cloud_deployment', return_value=False)
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.is_host_physical_deployment", return_value=False)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_hostname_physical_deployment')
    def test_get_ddp_and_deployment_hostname__not_able_to_physical(self, mock_get_hostname, *_):
        helper.get_ddp_and_deployment_hostname()

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug")
    def test_get_ddp_and_deployment_hostname__add_error_exception(self, mock_debug):
        helper.get_ddp_and_deployment_hostname()
        mock_debug.assert_called_with('Error Encountered - Could not get hostname for Apache')

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.run_cmd_on_ms')
    def test_get_hostname_physical_deployment__success_on_first_command(self, mock_run_cmd):
        mock_run_cmd.side_effect = [Mock(stdout="some output someDDP something any thing anything -d moretheing -s someDeployment\n"),
                                    Mock(stdout="Never gets here")]
        ddp_hostname, deployment_hostname = helper.get_hostname_physical_deployment()
        self.assertEqual(ddp_hostname, "moretheing")
        self.assertEqual(deployment_hostname, "someDeployment")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.run_cmd_on_ms')
    def test_get_hostname_physical_deployment__success_on_second_command(self, mock_run_cmd):
        mock_run_cmd.side_effect = [Mock(stdout="No such file or directory"),
                                    Mock(stdout="some output someDDP something any thing anything -d moretheing -s someDeployment\n")]
        ddp_hostname, deployment_hostname = helper.get_hostname_physical_deployment()
        self.assertEqual(ddp_hostname, "moretheing")
        self.assertEqual(deployment_hostname, "someDeployment")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.run_cmd_on_ms')
    def test_get_hostname_physical_deployment__raise_error(self, mock_run_cmd):
        mock_run_cmd.side_effect = [Mock(stdout="No such file or directory"),
                                    Mock(stdout="no crontab")]
        self.assertRaises(EnvironError, helper.get_hostname_physical_deployment)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.run_cmd_on_vm')
    def test_get_hostname_cloud_deployment__success_on_first_command(self, mock_run_cmd):
        mock_run_cmd.side_effect = [Mock(stdout="some output someDDP something any thing anything -d more moretheing -s someDeployment\n"),
                                    Mock(stdout="Never gets here")]
        ddp_hostname, deployment_hostname = helper.get_hostname_cloud_deployment()
        self.assertEqual(ddp_hostname, "more")
        self.assertEqual(deployment_hostname, "someDeployment")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.run_cmd_on_vm')
    def test_get_hostname_cloud_deployment__success_on_second_command(self, mock_run_cmd):
        mock_run_cmd.side_effect = [Mock(stdout="No such file or directory"),
                                    Mock(stdout="some output someDDP something any thing anything -d more moretheing -s someDeployment\n")]
        ddp_hostname, deployment_hostname = helper.get_hostname_cloud_deployment()
        self.assertEqual(ddp_hostname, "more")
        self.assertEqual(deployment_hostname, "someDeployment")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.run_cmd_on_vm')
    def test_get_hostname_cloud_deployment__raise_error(self, mock_run_cmd):
        mock_run_cmd.side_effect = [Mock(stdout="No such file or directory"),
                                    Mock(stdout="no crontab")]
        self.assertRaises(EnvironError, helper.get_hostname_cloud_deployment)

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.Command")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.run_local_cmd")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_documents_info_from_dit")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_document_content_from_dit")
    def test_get_hostname_in_cloud_native__success(self, mock_get_document_content_from_dit,
                                                   mock_get_documents_info_from_dit, mock_run_local_cmd, *_):
        mock_run_local_cmd.return_value.stdout = "the name of the deployment.cloud.native"
        mock_get_documents_info_from_dit.return_value = {"cENM_site_information": "ddp_document_number",
                                                         "cENM_integration_values": "deployment_doc_number"}
        mock_get_document_content_from_dit.side_effect = [{"global": {"ddp_hostname": "hostname_1"}},
                                                          {"eric-enm-ddc": {
                                                              "eric-oss-ddc": {"autoUpload": {"ddpid": "hostname_2"}}}}]
        self.assertEqual(helper.get_hostname_in_cloud_native(), ("hostname_1", "hostname_2"))

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.Command")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.run_local_cmd")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_documents_info_from_dit")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_document_content_from_dit")
    def test_get_hostname_in_cloud_native__raise_error(self, mock_get_document_content_from_dit, mock_get_documents_info_from_dit, mock_run_local_cmd, *_):
        mock_run_local_cmd.return_value.stdout = None
        self.assertRaises(EnvironError, helper.get_hostname_in_cloud_native)

    def test_get_historic_date_and_directory_of_ddp__return_date_and_dir(self):
        expected_historic_date = [str(datetime.datetime.today() - datetime.timedelta(days=13)).split()[0],
                                  str(datetime.datetime.today() - datetime.timedelta(days=14)).split()[0],
                                  str(datetime.datetime.today() - datetime.timedelta(days=15)).split()[0]]
        expected_directory_num = [(datetime.datetime.today() - datetime.timedelta(days=13)).strftime('%d%m%y'),
                                  (datetime.datetime.today() - datetime.timedelta(days=14)).strftime('%d%m%y'),
                                  (datetime.datetime.today() - datetime.timedelta(days=15)).strftime('%d%m%y')]
        actual_historic_date, actual_directory_num = helper.get_historic_date_and_directory_of_ddp()
        self.assertEqual(actual_historic_date, expected_historic_date)
        self.assertEqual(actual_directory_num, expected_directory_num)

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.log.logger")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.requests.get")
    def test_execute_ddp_url_and_fetch_cell_count__success(self, mock_get, _):
        mock_get.return_value = Mock(text=TEXT)
        helper.execute_ddp_url_and_fetch_cell_count("something")

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.log.logger")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.requests.get")
    def test_execute_ddp_url_and_fetch_cell_count__raise_error(self, mock_get, _):
        mock_get.return_value = Mock(text=TEXT_1)
        with self.assertRaises(EnvironError) as e:
            helper.execute_ddp_url_and_fetch_cell_count('url')
        self.assertEqual(e.exception.message, "Could not retrieve the cells_count_value from DDP, Check DDP page once.")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    def test_get_network_element_primary_types__returns_only_ne_types(self, mock_user):
        response = Mock()
        response.get_output.return_value = [u'FDN : NetworkElement=netsim_LTE05ERBS00016', u'neType : ERBS', u'',
                                            u'FDN : NetworkElement=netsim_LTE05ERBS00010', u'neType : ERBS', u'',
                                            u'FDN : NetworkElement=netsim_LTE05ERBS00029', u'neType : ERBS', u'',
                                            u'FDN : NetworkElement=netsim_LTE05ERBS00027', u'neType : ERBS', u'',
                                            u'FDN : NetworkElement=netsim_LTE05ERBS00023', u'neType : ERBS', u'',
                                            u'FDN : NetworkElement=netsim_LTE05ERBS00004', u'neType : ERBS', u'',
                                            u'FDN : NetworkElement=netsim_LTE05ERBS00007', u'neType : ERBS', u'',
                                            u'FDN : NetworkElement=netsim_LTE05ERBS00021', u'neType : ERBS', u'',
                                            u'FDN : NetworkElement=netsim_LTE05ERBS00019', u'neType : ERBS', u'',
                                            u'', u'10 instance(s)']
        mock_user.return_value.enm_execute.return_value = response
        result = helper.get_network_element_primary_types()
        expected = ["ERBS"] * 9
        self.assertEqual(result, expected)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    def test_get_network_element_primary_types__raises_script_engine_error(self, mock_user):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        mock_user.return_value.enm_execute.return_value = response
        self.assertRaises(helper.ScriptEngineResponseValidationError, helper.get_network_element_primary_types)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_network_element_primary_types')
    def test_sort_and_count_ne_types__correctly_sorts_and_total_ne_types(self, mock_get_nes):
        expected = {"ERBS": 3, "RadioNode": 5, "MGW": 2, "Router6672": 1}
        mock_get_nes.return_value = ["ERBS", "RadioNode", "RadioNode", "MGW", "ERBS", "ERBS", "MGW", "RadioNode",
                                     "RadioNode", "RadioNode", "Router6672"]
        result = helper.sort_and_count_ne_types()
        self.assertEqual(expected, result)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.sort_and_count_ne_types',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.info')
    def test_detect_transport_network_and_set_transport_size__logs_exception(self, mock_info, _):
        helper.detect_transport_network_and_set_transport_size()
        mock_info.assert_called_with("Could not determine network type, error encountered:: [Error].Load will be "
                                     "applied based upon the network cell count.")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.sort_and_count_ne_types')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.info')
    def test_detect_transport_network_and_set_transport_size__detects_ran_network(self, mock_info, mock_ne_types):
        mock_ne_types.return_value = {"RadioNode": 1, "TCU02": 5000}
        helper.detect_transport_network_and_set_transport_size()
        mock_info.assert_called_with("RAN NetworkElement(s) found, load will be applied based upon the network cell"
                                     " count.")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.sort_and_count_ne_types')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.info')
    def test_detect_transport_network_and_set_transport_size__cannot_determine_network(self, mock_info, mock_ne_types):
        mock_ne_types.return_value = {"MGW": 1}
        helper.detect_transport_network_and_set_transport_size()
        mock_info.assert_called_with("Could not determine network type, load will be applied based upon the network "
                                     "cell count.")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.determine_size_of_transport_network')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.sort_and_count_ne_types')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.info')
    def test_detect_transport_network_and_set_transport_size__transport_network(self, mock_info, mock_ne_types,
                                                                                mock_transport):
        mock_ne_types.return_value = {"TCU02": 1}
        helper.detect_transport_network_and_set_transport_size()
        mock_info.assert_called_with("Transport NetworkElement(s) found, determining transport configuration to be "
                                     "used.")
        self.assertEqual(1, mock_transport.call_count)

    def test_determine_size_of_transport_network__sets_correct_transport_size(self):
        ne_type_dict = {"SIU02": 5000, "MGW": 100}
        transport_key = helper.determine_size_of_transport_network(ne_type_dict)
        self.assertEqual("soem_five_k_network", transport_key)
        ne_type_dict.update({"TCU02": 5001})
        transport_key = helper.determine_size_of_transport_network(ne_type_dict)
        self.assertEqual("transport_twenty_k_network", transport_key)

    def test_determine_size_of_transport_network__sets_10k_transport_size(self):
        ne_type_dict = {"SIU02": 5001, "MGW": 100}
        transport_key = helper.determine_size_of_transport_network(ne_type_dict)
        self.assertEqual("transport_ten_k_network", transport_key)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_network_config',
           return_value=helper.SOEM_5K_NETWORK)
    def test_is_transport_network__true(self, _):
        self.assertTrue(helper.is_transport_network())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_network_config',
           return_value=helper.TRANSPORT_10K_NETWORK)
    def test_is_transport_network__ten_k_true(self, _):
        self.assertTrue(helper.is_transport_network())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_network_config',
           return_value=helper.FORTY_K_NETWORK)
    def test_is_transport_network__false(self, _):
        self.assertFalse(helper.is_transport_network())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value="key")
    def test_get_network_config__uses_persisted_value(self, _):
        self.assertEqual("key", helper.get_network_config())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value=helper.SOEM_5K_NETWORK)
    def test_get_network_config__uses_transport_key(self, *_):
        self.assertEqual(helper.SOEM_5K_NETWORK, helper.get_network_config())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_total_cell_count', return_value=1)
    def test_get_network_config__extra_small(self, *_):
        self.assertEqual(helper.EXTRA_SMALL_NETWORK, helper.get_network_config())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_total_cell_count', return_value=1001)
    def test_get_network_config__5k(self, *_):
        self.assertEqual(helper.FIVE_K_NETWORK, helper.get_network_config())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_total_cell_count', return_value=7501)
    def test_get_network_config__15k(self, *_):
        self.assertEqual(helper.FIFTEEN_K_NETWORK, helper.get_network_config())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_total_cell_count', side_effect=[0, 27501])
    def test_get_network_config__40k(self, *_):
        self.assertEqual(helper.FORTY_K_NETWORK, helper.get_network_config())
        self.assertEqual(helper.FORTY_K_NETWORK, helper.get_network_config())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_total_cell_count', return_value=70000)
    def test_get_network_config__60k(self, *_):
        self.assertEqual(helper.SIXTY_K_NETWORK, helper.get_network_config())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_total_cell_count', return_value=90000)
    def test_get_network_config__80k(self, *_):
        self.assertEqual(helper.EIGHTY_K_NETWORK, helper.get_network_config())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.detect_transport_network_and_set_transport_size',
           return_value=None)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_total_cell_count', return_value=90001)
    def test_get_network_config__100k(self, *_):
        self.assertEqual(helper.ONE_HUNDRED_K_NETWORK, helper.get_network_config())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_network_config',
           side_effect=[helper.SIXTY_K_NETWORK, helper.FORTY_K_NETWORK, helper.FIFTEEN_K_NETWORK])
    def test_get_robustness_configuration(self, _):
        self.assertDictEqual(helper.robustness_60k.get("robustness_60k"), helper.get_robustness_configuration())
        self.assertDictEqual(helper.robustness_60k.get("robustness_60k"), helper.get_robustness_configuration())
        self.assertDictEqual({}, helper.get_robustness_configuration())

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_all_enm_network_element_objects")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user")
    def test_build_poid_dict_from_enm_data__successful(
            self, mock_get_workload_admin_user, mock_get_all_enm_network_element_objects, mock_debug):
        enm_ne_poid_data = [{"id": "12345", "poId": "12345", "moType": "NetworkElement", "mibRootName": "node1"},
                            {"id": "23456", "poId": "23456", "moType": "NetworkElement", "mibRootName": "node2"}]
        mock_get_all_enm_network_element_objects.return_value.json.return_value = enm_ne_poid_data
        self.assertEqual(helper.build_poid_dict_from_enm_data(), {"node1": "12345", "node2": "23456"})
        mock_get_all_enm_network_element_objects.assert_called_with(mock_get_workload_admin_user.return_value)
        self.assertTrue(call("POID info from ENM has been read for 2 NetworkElements") in mock_debug.mock_calls)

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_all_enm_network_element_objects",
           side_effect=Exception("some error"))
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user")
    def test_build_poid_dict_from_enm_data__handles_error_while_fetching_data_from_enm(
            self, mock_get_workload_admin_user, mock_get_all_enm_network_element_objects, mock_debug):
        self.assertEqual(helper.build_poid_dict_from_enm_data(), None)
        mock_get_all_enm_network_element_objects.assert_called_with(mock_get_workload_admin_user.return_value)
        self.assertTrue(call("Error encountered while trying to fetch info from ENM: some error")
                        in mock_debug.mock_calls)

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_all_enm_network_element_objects")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user")
    def test_build_poid_dict_from_enm_data__handles_unexpected_data_from_enm(
            self, mock_get_workload_admin_user, mock_get_all_enm_network_element_objects, mock_debug):
        enm_ne_poid_data = [{"id": "12345", "moType": "NetworkElement", "mibRootName": "node1"},
                            {"id": "23456", "moType": "NetworkElement", "mibRootName": "node2"}]
        mock_get_all_enm_network_element_objects.return_value.json.return_value = enm_ne_poid_data
        self.assertEqual(helper.build_poid_dict_from_enm_data(), None)
        mock_get_all_enm_network_element_objects.assert_called_with(mock_get_workload_admin_user.return_value)
        self.assertTrue(call("Unexpected data received from ENM while processing POID info") in mock_debug.mock_calls)

    def test_get_all_enm_network_element_objects__successful(self):
        mock_user = Mock()
        response = Mock(ok=1)
        mock_user.get.return_value = response
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.assertEqual(response, helper.get_all_enm_network_element_objects(mock_user))
        mock_user.get.assert_called_with("/managedObjects/query?searchQuery=select%20NetworkElement",
                                         headers=headers)

    def test_get_all_enm_network_element_objects__raises_httperror(self):
        mock_user = Mock()
        mock_user.get.return_value = Mock(ok=0)
        with self.assertRaises(HTTPError) as e:
            helper.get_all_enm_network_element_objects(mock_user)
        self.assertEqual(e.exception.message, "Unable to get data from Network Explorer")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_local_ip', return_value=None)
    def test_is_eniq_server__no_hostname(self, _):
        self.assertEqual((False, []), helper.is_eniq_server(lms="ms_host"))

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_local_ip', return_value="ip")
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug')
    def test_is_eniq_server__no_lms_and_no_emp(self, mock_debug, _):
        self.assertEqual((False, []), helper.is_eniq_server())
        mock_debug.assert_called_with(ENIQ_SERVER_ERR_MSG)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.parse_eniq_ip_values', return_value=['unique'])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_local_ip', return_value="unique")
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput',
           return_value=(0, "output"))
    def test_is_eniq_server__success(self, mock_get, *_):
        self.assertTrue(helper.is_eniq_server(emp="emp"))
        mock_get.assert_called_with("ssh -q -i /var/tmp/enm_keypair.pem -o UserKnownHostsFile=/dev/null "
                                    "-o stricthostkeychecking=no cloud-user@emp "
                                    "'cat /ericsson/pmic1/eniq_integration_details.txt'")

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.parse_eniq_ip_values', return_value=['unique'])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_local_ip', return_value="not found")
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput',
           return_value=(0, "output"))
    def test_is_eniq_server__no_match(self, mock_get, *_):
        self.assertEqual((False, ['unique']), helper.is_eniq_server(lms="lms"))
        mock_get.assert_called_with("ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no lms "
                                    "'cat /var/log/eniq_integration_details.txt'")

    def test_parse_eniq_ip_values__returns_ips_found(self):
        output = "[eniq_oss_1]\neniq ip address = ['unique', 'unique1']\nlast updated = 2020-07-31 14:28:30\n"
        self.assertListEqual(['unique', 'unique1'], helper.parse_eniq_ip_values(output))

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput', return_value=(0, 'ip'))
    def test_get_local_ip__success(self, _):
        self.assertEqual('ip', helper.get_local_ip())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput', return_value=(256, ''))
    def test_get_local_ip__command_fails(self, _):
        self.assertIsNone(helper.get_local_ip())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    def test_check_if_password_ageing_enabled__success(self, mock_get_admin):
        response = Mock()
        mock_exception = Exception('some error')
        response.json.side_effect = [
            {u'passwordAgeing': {u'pwdExpireWarning': 7, u'graceLoginCount': 0, u'enabled': True, u'pwdMaxAge': 90}},
            {u'passwordAgeing': {u'enabled': False}}, mock_exception]
        mock_get_admin.return_value.get.return_value = response
        message = ("\nENM Password Ageing Policy is currently enabled. Password max age is currently: "
                   "[90] days and expiry warning is: [7] days. Password Ageing may impact workload created"
                   " user(s).\nRun SECUI_03 to disable password ageing policy (SECUI_03 runs at 12:00 am daily)"
                   " or change policy manually via ENM System Settings if the profile is not executable due "
                   "to password ageing.")
        self.assertEqual(message, helper.check_if_password_ageing_enabled())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_workload_admin_user')
    def test_check_if_password_ageing_enabled__does_not_return_message_if_policy_not_enabled(self, mock_get_admin):
        response = Mock()
        response.json.return_value = {u'passwordAgeing': {u'enabled': False}}
        mock_get_admin.return_value.get.return_value = response
        self.assertIsNone(helper.check_if_password_ageing_enabled())

    # output_network_basic test cases
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.config.has_prop', return_value=False)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get',
           side_effect=["five_k_network", 1000])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log')
    def test_output_network_basic__success(self, mock_log, *_):
        mock_log.cyan_text.side_effect = ['\x1b[96mWorkload Config\t/opt/ericsson/enmutils/nrm_default_configurations/'
                                          'five_network.py\x1b[0m',
                                          '\x1b[96mDetermined network size: 1000 Cells total.\x1b[0m']
        helper.output_network_basic()
        self.assertTrue(call(mock_log.cyan_text.side_effect in mock_log.logger.info.mock_calls))

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.config.has_prop', return_value=False)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get',
           side_effect=["transport_ten_k_network", 6000])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log')
    def test_output_network_basic__ten_k_network_success(self, mock_log, *_):
        mock_log.cyan_text.side_effect = ['\x1b[96mWorkload Config\t/opt/ericsson/enmutils/nrm_default_configurations/'
                                          'transport_ten_network.py\x1b[0m',
                                          '\x1b[96mDetermined network size: 6000 Cells total.\x1b[0m']
        helper.output_network_basic()
        self.assertTrue(call(mock_log.cyan_text.side_effect in mock_log.logger.info.mock_calls))

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.cyan_text', return_value=Mock())
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.persistence.get',
           side_effect=["sixty_k_network", 60000])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log')
    def test_output_network_basic__if_robustness_sixty_k_network(self, mock_log, *_):
        mock_log.cyan_text.side_effect = ['\x1b[96mWorkload Config\t/opt/ericsson/enmutils/nrm_default_configurations/'
                                          'robustness_60k.py\x1b[0m',
                                          '\x1b[96mDetermined network size: 60000 Cells total.\x1b[0m']
        helper.output_network_basic()
        self.assertTrue(call(mock_log.cyan_text.side_effect in mock_log.logger.info.mock_calls))

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput',
           return_value=(0, 'cnis.sero.gic.ericsson.se cnis.sero.gic.ericsson.se'))
    def test_get_uiserv_address__successful(self, mock_getstatusoutput):
        result = helper.get_uiserv_address()
        cmd = ("/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ingress -A "
               "-o=jsonpath='{.items[?(@.metadata.name==\"uiserv\")].spec.rules[0].host}' 2>/dev/null")
        mock_getstatusoutput.assert_called_with(cmd)
        self.assertEqual('cnis.sero.gic.ericsson.se', result[1])

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug')
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_enm_cloud_native_namespace",
           return_value="enm123")
    def test_get_cloud_native_service_ips__is_successful(
            self, mock_get_enm_cloud_native_namespace, mock_output, _):
        output = 'general-scripting-0   some_ip1:5020     ["ip:22"]\n' \
                 'general-scripting-1   some_ip2:5021     ["ip:22"]\n' \
                 'general-scripting-2   some_ip3:5022     ["ip:22"]\n'
        mock_output.return_value = 0, output
        expected_ips_with_ports = ['some_ip1 -p 5020', 'some_ip2 -p 5021', 'some_ip3 -p 5022']
        expected_ips_without_ports = ['some_ip1', 'some_ip2', 'some_ip3']
        ips_with_ports, ips_without_ports = helper.get_cloud_native_service_ips("general-scripting")
        self.assertListEqual(ips_with_ports, expected_ips_with_ports)
        self.assertListEqual(ips_without_ports, expected_ips_without_ports)
        self.assertEqual(mock_get_enm_cloud_native_namespace.called, 1)
        command = ("/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ericingress -n enm123 2>/dev/null | grep -P '(^|\\s)general-scripting-[0-9](?=\\s|$)'")
        mock_output.assert_called_with(command)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug')
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_enm_cloud_native_namespace",
           return_value="enm123")
    def test_get_cloud_native_service_ips__returns_2_epmty_lists_if_unsuccessful(
            self, mock_get_enm_cloud_native_namespace, mock_output, _):
        mock_output.return_value = 1, "error\n"
        self.assertEqual(helper.get_cloud_native_service_ips("general-scripting"), ([], []))
        self.assertEqual(mock_get_enm_cloud_native_namespace.called, 1)
        command = ("/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ericingress -n enm123 2>/dev/null | grep -P '(^|\\s)general-scripting-[0-9](?=\\s|$)'")
        mock_output.assert_called_with(command)

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_enm_cloud_native_namespace", return_value="enm123")
    def test_get_cloud_native_service_vip__is_successful(
            self, mock_get_enm_cloud_native_namespace, mock_output):
        output = "general-scripting   some_vip:9920    [some_ip1:9920 some_ip2:9920]\n"
        mock_output.return_value = 0, output
        self.assertEqual(helper.get_cloud_native_service_vip("general-scripting"), "some_vip")
        self.assertEqual(mock_get_enm_cloud_native_namespace.called, 1)
        command = ("/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ericingress -n enm123 2>/dev/null | "
                   "egrep general-scripting")
        mock_output.assert_called_with(command)

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput")
    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_enm_cloud_native_namespace", return_value="enm123")
    def test_get_cloud_native_service_vip__returns_epmty_string_if_unsuccessful(
            self, mock_get_enm_cloud_native_namespace, mock_output):
        mock_output.return_value = 1, "error\n"
        self.assertEqual(helper.get_cloud_native_service_vip("general-scripting"), "")
        self.assertEqual(mock_get_enm_cloud_native_namespace.called, 1)
        command = ("/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ericingress -n enm123 2>/dev/null | "
                   "egrep general-scripting")
        mock_output.assert_called_with(command)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.socket.gethostname', return_value=helper.VAPP_KEY)
    def test_is_host_vapp__success(self, _):
        self.assertTrue(helper.is_deployment_vapp())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.socket.gethostname', return_value="ieatwlvm")
    def test_is_host_vapp__no_host_match(self, _):
        self.assertFalse(helper.is_deployment_vapp())

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.is_transport_network', return_value=False)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.node_pool_mgr.get_all_nodes_from_redis',
           return_value=[Mock()])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput', return_value=(0, ""))
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.nss_mo_info.NssMoInfo.'
           'fetch_and_parse_netsim_simulation_files')
    def test_fetch_and_parse_nss_mo_files__removes_existing_files_updates_netsim_files(self, mock_fetch_and_parse, *_):
        helper.NODE_COUNT = 2
        helper.fetch_and_parse_nss_mo_files()
        self.assertEqual(1, mock_fetch_and_parse.call_count)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.is_transport_network', return_value=False)
    @patch('enmutils_int.lib.node_pool_mgr.get_all_nodes_from_redis',
           return_value=[Mock()])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput',
           side_effect=[(1, ""), RuntimeError("Error")])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.nss_mo_info.NssMoInfo.'
           'fetch_and_parse_netsim_simulation_files')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.log.logger.debug')
    def test_fetch_and_parse_nss_mo_files__logs_exception(self, mock_debug, mock_fetch_and_parse, *_):
        helper.NODE_COUNT = 2
        helper.fetch_and_parse_nss_mo_files()
        self.assertEqual(0, mock_fetch_and_parse.call_count)
        mock_debug.assert_called_with('Failed to generate one or more files, error encountered: Error.')

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.is_transport_network', return_value=False)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.node_pool_mgr.get_all_nodes_from_redis',
           return_value=[Mock()])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.nss_mo_info.NssMoInfo.'
           'fetch_and_parse_netsim_simulation_files')
    def test_fetch_and_parse_nss_mo_files__updates_netsim_files(self, mock_fetch_and_parse, mock_get_status, *_):
        helper.NODE_COUNT = 1
        helper.fetch_and_parse_nss_mo_files()
        self.assertEqual(1, mock_fetch_and_parse.call_count)
        self.assertEqual(0, mock_get_status.call_count)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.is_transport_network', return_value=True)
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.node_pool_mgr.get_all_nodes_from_redis',
           return_value=[Mock()])
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.commands.getstatusoutput')
    @patch('enmutils_int.lib.services.deployment_info_helper_methods.nss_mo_info.NssMoInfo.'
           'fetch_and_parse_netsim_simulation_files')
    def test_fetch_and_parse_nss_mo_files__skips_transport_network(self, mock_fetch_and_parse, mock_get_status, *_):
        helper.fetch_and_parse_nss_mo_files()
        self.assertEqual(0, mock_fetch_and_parse.call_count)
        self.assertEqual(0, mock_get_status.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
