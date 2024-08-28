import unittest2
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile


class FlowProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow_profile = FlowProfile()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_run__is_successful(self):
        self.flow_profile.run()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
