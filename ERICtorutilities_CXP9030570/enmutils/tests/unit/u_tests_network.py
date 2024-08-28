#!/usr/bin/env python
from enmutils.lib import network, persistence
from testslib import unit_test_utils

import unittest2
from mock import patch


class NetworkUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("socket.gethostbyaddr")
    @patch("socket.getfqdn")
    def test_that_fqdn_is_persisted_if_retrieved_successfully(self, mock_getfqdn, _):
        mock_getfqdn.return_value = "test-host.example.org"
        self.assertFalse(persistence.has_key("test-host-fqdn"))
        network.get_fqdn("test-host")
        self.assertTrue(persistence.has_key("test-host-fqdn"))

    @patch('enmutils.lib.network.socket.gethostbyaddr')
    @patch('enmutils.lib.network.socket.getfqdn')
    def test_get_fqdn__does_not_use_persistence_set(self, mock_getfqdn, _):
        mock_getfqdn.return_value = None
        network.get_fqdn("test-host")

    @patch("socket.gethostbyaddr")
    @patch("socket.getfqdn")
    def test_that_second_request_for_same_host_returns_persisted_value(self, mock_getfqdn, _):
        mock_getfqdn.return_value = "foobar987.blah.com"
        initial_fqdn = network.get_fqdn("test-host")
        mock_getfqdn.return_value = "foobar123.blah.com"
        self.assertEqual(initial_fqdn, network.get_fqdn("test-host"))

    @patch('enmutils.lib.network.is_valid_ip', return_value=False)
    def test_is_port_open__raises_exception_if_ip_invalid(self, _):
        self.assertRaises(RuntimeError, network.is_port_open, '172.258.45.233', 1234)

    @patch('enmutils.lib.network.is_valid_ip', return_value=True)
    @patch('enmutils.lib.network.closing')
    @patch('enmutils.lib.network.socket')
    def test_is_port_open__success(self, mock_socket, mock_closing, _):
        mock_socket.AF_INET = 1
        mock_socket.SOCK_STREAM = 1
        mock_socket.socket.connect_ex = 0
        self.assertEqual(0, network.is_port_open('172.258.45.233', 8080))
        self.assertTrue(mock_closing.called)
        self.assertTrue(mock_socket.socket.called)
        mock_socket.socket.assert_called_with(1, 1)

    @patch('enmutils.lib.network.is_valid_ipv6')
    def test_is_valid_ip__invokes_is_valid_ipv6(self, mock_ipv6):
        network.is_valid_ip('fe80:250:250:250:56ff:fe00:fe00:fe00:81')
        mock_ipv6.assert_called_with('fe80:250:250:250:56ff:fe00:fe00:fe00:81')

    @patch('enmutils.lib.network.is_valid_ipv4')
    def test_is_valid_ip__is_valid_ipv4(self, mock_ipv4):
        network.is_valid_ip('172.258.45.233')
        mock_ipv4.assert_called_with('172.258.45.233')

    @patch('enmutils.lib.network.is_valid_ipv4', return_value=True)
    def test_is_multicast_ipv4__raises_and_pass(self, *_):
        network.is_multicast_ipv4('test')

    def test_is_ipv4_address_private_returns_false_when_passed_an_invalid_ip_address_outside_the_172_range(self):
        self.assertFalse(network.is_ipv4_address_private('172.258.45.233'))

    def test_is_ipv4_address_private_returns_false_when_passed_an_valid_ip_address_outside_the_172_range(self):
        self.assertFalse(network.is_ipv4_address_private('172.10.45.233'))

    def test_is_ipv4_address_private_returns_true_when_passed_a_valid_ip_address_within_the_172_range(self):
        self.assertTrue(network.is_ipv4_address_private('172.20.45.233'))

    def test_is_ipv4_address_private_returns_true_when_passed_a_valid_ip_address_beginning_with_192_168(self):
        self.assertTrue(network.is_ipv4_address_private('192.168.2.67'))

    def test_is_ipv4_address_private_returns_false_when_passed_an_invalid_ip_address_beginning_with_127(self):
        self.assertFalse(network.is_ipv4_address_private('127.265.67.44'))

    def test_is_ipv4_address_private_returns_true_when_passed_a_valid_ip_address_beginning_with_127(self):
        self.assertTrue(network.is_ipv4_address_private('127.5.67.44'))

    def test_is_ipv4_address_private_returns_false_when_passed_an_invalid_private_ip_address(self):
        self.assertFalse(network.is_ipv4_address_private('253.32.225.222'))

    def test_is_valid_ip4_returns_false_when_passed_an_ip_starting_with_zero(self):
        self.assertFalse(network.is_valid_ipv4('0.329.225.25'))

    def test_is_valid_ip4_returns_false_when_passed_an_ip_outside_legit_addresses(self):
        self.assertFalse(network.is_valid_ipv4('256.32.225.300'))

    def test_is_valid_ip4_returns_true_when_passed_a_valid_ipv4_address(self):
        self.assertTrue(network.is_valid_ipv4('10.32.225.31'))

    def test_is_valid_ip4_returns_false_when_passed_an_empty_string(self):
        self.assertFalse(network.is_valid_ipv4(''))

    def test_is_valid_ip6_returns_false_when_passed_an_ip_outside_legit_addresses(self):
        self.assertFalse(network.is_valid_ipv6('fe80:250:250:250:56ff:fe00:fe00:fe00:81'))

    def test_is_valid_ip6_returns_true_when_passed_an_supported_ipv6_address(self):
        self.assertTrue(network.is_valid_ipv6('fe80::250:56ff:fe00:81'))

    def test_is_valid_ip6_returns_false_for_an_unsupported_ipv6_address_with_prefix_length(self):
        self.assertFalse(network.is_valid_ipv6('fe80::250:56ff:fe00:81/64'))

    def test_is_valid_ip6_returns_false_when_passed_an_empty_string(self):
        self.assertFalse(network.is_valid_ipv6(''))

    def test_is_multicast_ip4_returns_true_when_passed_a_valid_ipv4_address(self):
        self.assertTrue(network.is_multicast_ipv4('232.32.225.3'))

    def test_is_multicast_ip4_returns_false_when_passed_an_invalid_ipv4_address(self):
        self.assertFalse(network.is_multicast_ipv4('oct.32.225.3'))

    def test_is_multicast_ip4_returns_false_when_passed_an_inaccurate_ipv4_address(self):
        self.assertFalse(network.is_multicast_ipv4('222.32.225.3'))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
