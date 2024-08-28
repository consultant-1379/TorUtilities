#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils.lib.exceptions import ScriptEngineResponseValidationError
from enmutils_int.lib.delete_network import DeleteNetwork
from testslib import unit_test_utils


class DocFlowUnitTest(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.delete_network = DeleteNetwork(user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_delete_network_element__success(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'', u'1 instance(s) deleted']
        self.delete_network.delete_network_element()

    def test_delete_network_element__raises_script_engine_error(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'', u'ERROR']
        self.assertRaises(ScriptEngineResponseValidationError, self.delete_network.delete_network_element)

    def test_delete_mecontext__success(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'', u'1 instance(s) deleted']
        self.delete_network.delete_mecontext()

    def test_delete_mecontext__raises_script_engine_error(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'', u'0 instance(s)']
        self.assertRaises(ScriptEngineResponseValidationError, self.delete_network.delete_mecontext)

    def test_delete_nrm_data_from_enm__success(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'', u'1 instance(s)']
        self.delete_network.delete_nrm_data_from_enm()

    def test_delete_nrm_data_from_enm__raises_script_engine_error(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'', u'ERROR']
        self.assertRaises(ScriptEngineResponseValidationError, self.delete_network.delete_nrm_data_from_enm)

    def test_delete_subnetwork__success(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'', u'1 instance(s) deleted']
        self.delete_network.delete_subnetwork()

    def test_delete_subnetwork__raises_script_engine_error(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'', u'ERROR']
        self.assertRaises(ScriptEngineResponseValidationError, self.delete_network.delete_subnetwork)

    def test_get_all_subnetworks__retrieves_all_subnetworks(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'', u'FDN: SubNetwork=Europe', u'',
                                                                      u'FDN: SubNetwork=Europe,SubNetwork=Ireland', u'',
                                                                      u'FDN: SubNetwork=Europe,SubNetwork=Ireland,'
                                                                      u'SubNetwork=ERBS', u'', u'3 instance(s)']
        networks = self.delete_network.get_all_subnetworks()
        self.assertEqual(3, len(networks))

    @patch('enmutils_int.lib.delete_network.DeleteNetwork.get_all_subnetworks', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.delete_network.DeleteNetwork.delete_subnetwork')
    @patch('enmutils_int.lib.delete_network.log.logger.debug')
    def test_delete_nested_subnetwork__defaults_to_using_wildcard_if_no_networks_found(self, mock_debug, mock_delete,
                                                                                       _):
        self.delete_network.delete_nested_subnetwork()
        mock_debug.assert_called_with("Unable to retrieve SubNetwork information, error encountered:: [Error]. "
                                      "Attempting to delete Subnetwork using default behaviour.")
        self.assertEqual(1, mock_delete.call_count)

    @patch('enmutils_int.lib.delete_network.DeleteNetwork.get_all_subnetworks')
    @patch('enmutils_int.lib.delete_network.DeleteNetwork.delete_subnetwork')
    @patch('enmutils_int.lib.delete_network.log.logger.debug')
    def test_delete_nested_subnetwork__deletes_nested_subnets_in_order(self, mock_debug, mock_delete, mock_get):
        mock_get.return_value = ["SubNetwork=Europe", "SubNetwork=Europe,SubNetwork=Ireland",
                                 "SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS"]
        self.delete_network.delete_nested_subnetwork()
        self.assertEqual(0, mock_debug.call_count)
        self.assertEqual(3, mock_delete.call_count)
        self.assertEqual(self.delete_network.subnetworks, ["SubNetwork=Europe"])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
