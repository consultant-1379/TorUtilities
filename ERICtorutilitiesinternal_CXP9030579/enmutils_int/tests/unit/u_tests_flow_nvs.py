#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock

from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.nvs_flows.nvs_flows import Nvs01Flow, NvsFlow, Nvs02Flow


class NvsFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = NvsFlow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.NvsFlow.create_profile_users')
    def test_create_nvs_object__no_wait(self, _):
        nvs = self.flow.create_nvs_object()
        self.assertTrue(hasattr(nvs, 'get_all_unsupported_version_ids'))


class Nvs01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = Nvs01Flow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.create_nvs_object')
    def test_execute_flow__success(self, mock_create_nvs_object, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_create_nvs_object.call_count)

    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.create_nvs_object')
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.add_error_as_exception')
    def test_execute_flow__adds_error(self, mock_add_error, mock_create_nvs_object, *_):
        mock_create_nvs_object.return_value.deploy_unsupported_models.side_effect = Exception("Error")
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)


class Nvs02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = Nvs02Flow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.create_nvs_object')
    def test_execute_flow__success(self, mock_create_nvs_object, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_create_nvs_object.call_count)

    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.create_nvs_object')
    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.add_error_as_exception')
    def test_execute_flow__adds_error(self, mock_add_error, mock_create_nvs_object, *_):
        mock_create_nvs_object.return_value.remove_supported_models.side_effect = Exception("Error")
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
