import unittest2
from enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow import ShmSetupFlow
from enmutils_int.lib.workload.shm_setup import SHM_SETUP
from testslib import unit_test_utils
from mock import Mock, PropertyMock, patch


class ShmSetupFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = ShmSetupFlow()
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmSetupFlow.execute_flow")
    def test_shm_profile_shm_setup_execute_flow__successful(self, mock_flow):
        SHM_SETUP().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmSetupFlow.nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmSetupFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmSetupFlow.set_sftp_values')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmSetupFlow.download_software_packages')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmSetupFlow.set_values')
    def test_execute_flow(self, mock_set_values, mock_download_software_packages, mock_nodes, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_set_values.called)
        self.assertEqual(1, mock_nodes.call_count)
        self.assertTrue(mock_download_software_packages.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.os.path.exists', return_value=False)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.os.makedirs', return_value=True)
    def test_get_software_package_details(self, *_):
        self.flow.LOCAL_PATH = True
        self.flow.get_software_package_details()

    def test_get_software_package_details__existing_directories(self, *_):
        self.flow.LOCAL_PATH = False
        self.flow.get_software_package_details()

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmFlow.add_error_as_exception')
    def test_get_software_package_details__adds_error_on_path_exception(self, mock_add_error_as_exception, *_):
        self.flow.LOCAL_PATH = True
        self.flow.get_software_package_details()
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.os.path.exists', return_value=False)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.os.makedirs', return_value=True)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.simple_sftp_client.download',
           side_effect=[None, None, Exception("exception")])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.filesystem.does_file_exist',
           side_effect=[True, False, True])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.filesystem.delete_file')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmSetupFlow.get_software_package_details')
    def test_download_software_packages__success(self, mock_packages, *_):
        self.flow.LOCAL_PATH = True
        mock_packages.return_value = ["pkg", "pkg1", "pkg2"]
        self.flow.download_software_packages()

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmSetupFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.SHMUtils.set_netsim_values')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.generate_basic_dictionary_from_list_of_objects')
    def test_set_values(self, mock_nodes_list, mock_set_values, mock_get_nodes_list_by_attribute):
        mock_nodes_list.return_value = {"ERBS": [Mock()], "RadioNode": [Mock()], "MGW": [Mock()], "MLTN": [Mock()],
                                        "Router_6672": [Mock()], "BSC": [Mock()], "Router6675": [Mock()],
                                        "SCU": [Mock()], "MINI-LINK-669x": [Mock()]}
        mock_set_values.side_effect = [self.exception, None]
        self.flow.set_values()
        mock_get_nodes_list_by_attribute.assert_called_with(
            node_attributes=["node_id", "node_ip", "netsim", "primary_type", "simulation", "node_name", "poid"])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.ShmSetupFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.SHMUtils.set_netsim_values')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.generate_basic_dictionary_from_list_of_objects')
    def test_set_values__runs_ignores_empty_list(self, mock_nodes_list, mock_set_values, _):
        mock_nodes_list.return_value = {"ERBS": [], "RadioNode": [], "MGW": [], "MLTN": [], "Router_6672": [],
                                        "BSC": [], "Router6675": [], "MINI-LINK-669x": []}
        self.flow.set_values()
        self.assertFalse(mock_set_values.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.config.get_prop', return_value="host")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.is_host_pingable', return_value=False)
    def test_set_sftp_values__uses_default_sftp(self, *_):
        self.flow.set_sftp_values()
        self.assertEqual(self.flow.USER, "APTUSER")

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.config.get_prop', return_value="host")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.is_host_pingable', return_value=True)
    def test_set_sftp_values__uses_gateway(self, *_):
        self.flow.set_sftp_values()
        self.assertEqual(self.flow.USER, "root")

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.config.get_prop', return_value="host")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow.is_host_pingable', return_value=True)
    def test_set_sftp_values__cloud_native_uses_default_sftp(self, *_):
        self.flow.set_sftp_values()
        self.assertEqual(self.flow.HOST, "sfts.seli.gic.ericsson.se")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
