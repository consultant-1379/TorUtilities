import unittest2
from testslib import unit_test_utils
from mock import patch, Mock, PropertyMock
from enmutils_int.lib.profile_flows.plm_flows.plm_02_flow import Plm02Flow, EnvironError
from enmutils_int.lib.workload import plm_02


class PLM02UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Plm02Flow()
        self.user = Mock()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = "PLM_Administrator"
        self.flow.NODE_TYPES = ["MINI-LINK-669x"]
        self.flow.SCHEDULE_SLEEP = 60 * 60

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.create_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.delete_discovered_links")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.rediscovery_of_links")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.get_nodes_list_by_attribute",
           return_value=[Mock(node_id=1), Mock(node_id=2)])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.log.logger.debug")
    def test_execute_flow__successful_flag_true(self, mock_debug_log, *_):
        self.flow.FLAG = True
        self.flow.RESET = 2
        self.flow.execute_flow()
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile.TeardownList.remove")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.create_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.delete_discovered_links")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.rediscovery_of_links")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.get_nodes_list_by_attribute",
           return_value=[Mock(node_id=1), Mock(node_id=2)])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.log.logger.debug")
    def test_execute_flow__successful_flag_false(self, mock_debug_log, *_):
        self.flow.FLAG = False
        self.flow.RESET = 1
        self.flow.execute_flow()
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.create_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.delete_discovered_links")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.rediscovery_of_links")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.get_nodes_list_by_attribute",
           return_value=[])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.log.logger.debug")
    def test_execute_flow__no_nodes(self, *_):
        self.assertRaises(EnvironError, self.flow.execute_flow())

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile.TeardownList.remove")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.create_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.delete_discovered_links")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.rediscovery_of_links")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.get_nodes_list_by_attribute",
           return_value=[Mock(node_id=1)])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.add_error_as_exception")
    def test_execute_flow__exception(self, mock_add_error_as_exception, *_):
        self.flow.execute_flow()
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.log.logger.debug")
    def test_rediscovery_of_links__successful(self, mock_debug_log):
        response = Mock(ok=True)
        self.user.post.return_value = response
        response.json.return_value = {"brand2": True}
        self.flow.rediscovery_of_links(self.user, node_list=["1", "2"])
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.log.logger.debug")
    def test_rediscovery_of_links__raises_error(self, mock_debug_log):
        response = Mock(ok=False)
        self.user.post.return_value = response
        response.json.return_value = {"brand2": True}
        self.assertRaises(EnvironError, self.flow.rediscovery_of_links, self.user, node_list=["1", "2"])
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.log.logger.debug")
    def test_delete_discovered_links__successful(self, mock_debug_log):
        response = Mock(ok=True)
        self.user.post.return_value = response
        response.json.return_value = {"brand2": True}
        self.flow.delete_discovered_links(self.user, node_list=["1", "2"])
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.log.logger.debug")
    def test_delete_discovered_links__raises_error(self, mock_debug_log):
        response = Mock(ok=False)
        self.user.post.return_value = response
        response.json.return_value = {"brand2": False}
        self.assertRaises(EnvironError, self.flow.delete_discovered_links, self.user, node_list=["1", "2"])
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.execute_flow")
    def test_run__is_successful(self, mock_execute_flow):
        plm_02.PLM_02().run()
        self.assertTrue(mock_execute_flow.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
