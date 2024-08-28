#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils_int.lib.helper_methods import (generate_basic_dictionary_from_list_of_objects, list_netsim_simulations,
                                             get_local_ip_and_hostname)
from testslib import unit_test_utils


class HelperMethodUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_generate_basic_dictionary_from_list_of_objects__returns_dict_baed_upon_key(self):
        list_obj, list_obj1, list_obj2 = Mock(), Mock(), Mock()
        list_obj.name = "A"
        list_obj1.name = "B"
        list_obj2.name = "C"
        list_to_be_converted = [list_obj, list_obj, list_obj1, list_obj2]
        gen_dict = generate_basic_dictionary_from_list_of_objects(list_to_be_converted, "name")
        self.assertEqual(len(gen_dict.get("A")), 2)
        self.assertEqual(len(gen_dict.get("B")), 1)
        self.assertEqual(len(gen_dict.get("C")), 1)
        self.assertIsNotNone(gen_dict.get("A"))
        self.assertIsNotNone(gen_dict.get("B"))
        self.assertIsNotNone(gen_dict.get("C"))

    @patch('enmutils_int.lib.helper_methods.commands.getstatusoutput', return_value=(1, "Error"))
    def test_list_netsim_simulations__does_not_retry_if_max_attempts_reached(self, mock_getoutput):
        list_netsim_simulations(max_retries=1, lte_match=False)
        self.assertEqual(1, mock_getoutput.call_count)

    @patch('enmutils_int.lib.helper_methods.time.sleep', return_value=0)
    @patch('enmutils_int.lib.helper_methods.commands.getstatusoutput',
           return_value=(0, "H1\nH2\nH3\nSim\n"))
    def test_list_netsim_simulations__success(self, mock_getoutput, _):
        sims = list_netsim_simulations(lte_match=False)
        self.assertEqual(1, mock_getoutput.call_count)
        self.assertListEqual(["Sim", ''], sims)

    @patch('enmutils_int.lib.helper_methods.time.sleep', return_value=0)
    @patch('enmutils_int.lib.helper_methods.commands.getstatusoutput',
           side_effect=[(1, "Error"), (0, "H1\nH2\nH3\nSim\n")])
    def test_list_netsim_simulations__retries(self, mock_getoutput, _):
        list_netsim_simulations(lte_match=False)
        self.assertEqual(2, mock_getoutput.call_count)

    @patch('enmutils_int.lib.helper_methods.time.sleep', return_value=0)
    @patch('enmutils_int.lib.helper_methods.commands.getstatusoutput',
           side_effect=[(0, "H1\nH2\nH3\nSim\n"), (0, "H1\nH2\nH3\nLTE-SIM-limx40\n")])
    def test_list_netsim_simulations__retries_if_no_lte_match(self, mock_getoutput, _):
        list_netsim_simulations()
        self.assertEqual(2, mock_getoutput.call_count)

    @patch('enmutils_int.lib.helper_methods.socket.gethostname')
    def test_get_local_ip_and_hostname__is_successful(self, mock_get_hostname):
        mock_get_hostname.return_value = "hostname"
        self.assertEqual(get_local_ip_and_hostname(get_ip=False), ('', 'hostname'))
        self.assertEqual(mock_get_hostname.call_count, 1)

    @patch('enmutils_int.lib.helper_methods.socket.gethostname')
    def test_get_local_ip_and_hostname__raises_runtime_error(self, mock_get_hostname):
        mock_get_hostname.return_value = None
        self.assertRaises(RuntimeError, get_local_ip_and_hostname, get_ip=False)

    @patch('enmutils_int.lib.helper_methods.socket.gethostbyname_ex')
    @patch('enmutils_int.lib.helper_methods.socket.gethostname')
    def test_get_local_ip_and_hostname__returns_ip(self, mock_get_hostname, mock_get_host_by_name_ex):
        mock_get_hostname.return_value = "hostname"
        mock_get_host_by_name_ex.return_value = ('ieatlms5742', ['localhost', 'localhost'], ['localhost', 'ip'])
        self.assertEqual(get_local_ip_and_hostname(), ('ip', 'hostname'))
        self.assertEqual(mock_get_host_by_name_ex.call_count, 1)

    @patch('enmutils_int.lib.helper_methods.socket.gethostbyname_ex')
    @patch('enmutils_int.lib.helper_methods.socket.gethostname')
    def test_get_local_ip_and_hostname_returns_ip__raises_runtime_error(self, mock_get_hostname,
                                                                        mock_get_host_by_name_ex):
        mock_get_hostname.return_value = "hostname"
        mock_get_host_by_name_ex.return_value = ('ieatlms5742', ['localhost', 'localhost'], [None])
        self.assertRaises(RuntimeError, get_local_ip_and_hostname)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
