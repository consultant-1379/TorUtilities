#!/usr/bin/env python

import unittest2
from enmutils_int.lib.services import service_registry
from mock import patch
from testslib import unit_test_utils

DEFAULT_REGISTRY_DATA = {"some_service": {"port": 5001, "P2": True, "threads": 1}}


class ServiceRegistryUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("__builtin__.open")
    @patch("json.load", return_value={"some_service": {"port": 5001}})
    def test_get_registry_data__is_successful(self, *_):
        self.assertEqual({"some_service": {"port": 5001}}, service_registry.get_registry_data())

    @patch("enmutils_int.lib.services.service_registry.get_registry_data", return_value=DEFAULT_REGISTRY_DATA)
    def test_can_service_be_used__returns_none_if_service_not_found(self, *_):
        self.assertEqual(None, service_registry.can_service_be_used("some_other_service", priority=2))

    @patch("enmutils_int.lib.services.service_registry.get_registry_data", return_value=DEFAULT_REGISTRY_DATA)
    def test_can_service_be_used__returns_service_info_if_p2_profile_is_requested_and_p2_profile_allowed(self, *_):
        self.assertTrue(service_registry.can_service_be_used("some_service", priority=2))

    @patch("enmutils_int.lib.services.service_registry.get_registry_data", return_value=DEFAULT_REGISTRY_DATA)
    def test_can_service_be_used__returns_none_if_p1_profile_is_requested_and_only_p2_profile_allowed(self, *_):
        self.assertFalse(service_registry.can_service_be_used("some_service", priority=1))

    @patch("enmutils_int.lib.services.service_registry.get_registry_data",
           return_value={"some_service": {"port": 5001, "tool": False, "test": True}})
    @patch("enmutils_int.lib.services.service_registry.os.path.isfile", return_value=True)
    def test_can_service_be_used__returns_true_if_test_mode_flag_is_set_and_test_mode_flag_file_exists(self, *_):
        self.assertTrue(service_registry.can_service_be_used("some_service"))

    @patch("enmutils_int.lib.services.service_registry.os.path.isfile", return_value=False)
    @patch("enmutils_int.lib.services.service_registry.get_registry_data",
           return_value={"some_service": {"port": 5001, "tool": False, "test": True}})
    def test_can_service_be_used__returns_False_if_test_mode_flag_is_set_but_test_mode_flag_file_doesnt_exist(
            self, * _):
        self.assertFalse(service_registry.can_service_be_used("some_service"))

    @patch("enmutils_int.lib.services.service_registry.get_registry_data",
           return_value={"some_service": {"port": 5001, "tool": False}})
    def test_can_service_be_used__returns_none_if_tool_not_allowed(self, *_):
        self.assertFalse(service_registry.can_service_be_used("some_service"))

    @patch("enmutils_int.lib.services.service_registry.get_registry_data", return_value=DEFAULT_REGISTRY_DATA)
    def test_get_service_info_for_service_name__is_successful(self, _):
        self.assertEqual((5001, "localhost", 1), service_registry.get_service_info_for_service_name("some_service"))

    @patch("enmutils_int.lib.services.service_registry.get_registry_data", return_value=DEFAULT_REGISTRY_DATA)
    def test_get_service_info_for_service_name__raises_runtimeerror_if_servicename_not_found_in_registry(self, _):
        self.assertRaises(RuntimeError, service_registry.get_service_info_for_service_name, "other_service")

    @patch("enmutils_int.lib.services.service_registry.get_registry_data",
           return_value={"some_service": {"port": None}})
    def test_get_service_info_for_service_name__raises_runtimeerror_if_no_port_defined_for_service_in_registry(self, _):
        self.assertRaises(RuntimeError, service_registry.get_service_info_for_service_name, "some_service")

    @patch("enmutils_int.lib.services.service_registry.get_registry_data", return_value=DEFAULT_REGISTRY_DATA)
    def test_get_service_name_for_service_port__is_successful(self, _):
        self.assertEqual("some_service", service_registry.get_service_name_for_service_port(5001))

    @patch("enmutils_int.lib.services.service_registry.get_registry_data", return_value=DEFAULT_REGISTRY_DATA)
    def test_get_service_name_for_service_port__raises_runtimeerror_if_servicename_not_found_in_registry(self, _):
        self.assertRaises(RuntimeError, service_registry.get_service_name_for_service_port, 5002)

    @patch("enmutils_int.lib.services.service_registry.get_registry_data",
           return_value={"some_service": {"port": 5001}, "other_service": {"port": 5001}})
    def test_get_service_name_for_service_port__raises_runtimeerror_if_port_used_more_than_once_in_registry(self, _):
        self.assertRaises(RuntimeError, service_registry.get_service_name_for_service_port, 5001)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
