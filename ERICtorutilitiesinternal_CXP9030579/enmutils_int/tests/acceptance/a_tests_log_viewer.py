import unittest2

from enmutils_int.lib.log_viewer import LogViewer
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec


class LogViewerAcceptanceTests(unittest2.TestCase):

    SEARCH_TERM = "all errors"

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["OPERATOR"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        self.user = self.fixture.users[0]
        self.log_viewer = LogViewer(user=self.user, search_term=self.SEARCH_TERM)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("Log_Viewer", "Get app help")
    def test_log_viewer_rest_call_for_app_help_returns_200(self):
        self.assertLess(self.log_viewer.get_log_viewer_help(), 300)

    @func_dec("Log_Viewer", "Logviewer Search")
    def test_log_viewer_successfully_performs_rest_search(self):
        self.assertNotEqual(None, self.log_viewer.get_log_viewer_by_search_term())

    @func_dec("Log_Viewer", "Get Log viewer default")
    def test_log_view_successfully_gets_log_viewer_app_default(self):
        self.assertLess(self.log_viewer.get_log_viewer(), 300)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
