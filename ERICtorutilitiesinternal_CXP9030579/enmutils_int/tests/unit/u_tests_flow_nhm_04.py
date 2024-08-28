#!/usr/bin/env python
import unittest2
from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.nhm_flows.nhm_04_flow import Nhm04


class Nhm04UnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.profile = Nhm04()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_04_flow.NhmConcurrentUsersFlow.execute_profile_flow')
    def test_execute_flow_is_successful(self, mock_execute_profile_flow):
        self.profile.execute_flow()
        mock_execute_profile_flow.assert_called()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
