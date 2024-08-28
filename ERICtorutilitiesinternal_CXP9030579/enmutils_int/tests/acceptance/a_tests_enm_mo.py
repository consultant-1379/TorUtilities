import unittest2
from testslib import test_fixture, func_test_utils
from nose.plugins.skip import SkipTest


@SkipTest
class NodeMoAcceptanceTests(unittest2.TestCase):

    create_delete_enm_mo = None
    NUM_NODES = {"ERBS": 1}
    MO_VALUES = {'EUtranCellRelation': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["ADMINISTRATOR"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)

    def tearDown(self):
        func_test_utils.tear_down(self)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
