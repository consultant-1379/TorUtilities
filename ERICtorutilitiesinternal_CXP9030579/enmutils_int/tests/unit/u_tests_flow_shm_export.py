import unittest2
from mock import Mock, PropertyMock, patch
from requests.exceptions import HTTPError

from enmutils_int.lib.profile_flows.shm_flows.shm_export_flow import Shm19Flow, Shm20Flow, Shm21Flow
from enmutils_int.lib.workload.shm_19 import SHM_19
from enmutils_int.lib.workload.shm_20 import SHM_20
from enmutils_int.lib.workload.shm_21 import SHM_21
from testslib import unit_test_utils


class Shm19FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.nodes = [Mock()]
        self.flow = Shm19Flow()
        self.flow.SCHEDULED_TIMES_STRINGS = ["19:00:00"]
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.execute_flow")
    def test_shm_profile_shm_19_execute_flow__successful(self, mock_flow):
        SHM_19().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.create')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.get_nodes_list_by_attribute')
    def test_execute_flow_success(self, mock_nodes, mock_create, *_):
        mock_nodes.return_value = self.nodes
        self.flow.execute_flow()
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.create')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm19Flow.get_nodes_list_by_attribute')
    def test_execute_flow_add_error_as_exception(self, mock_nodes, mock_error, mock_create, *_):
        mock_nodes.return_value = self.nodes
        mock_create.side_effect = HTTPError
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)


class Shm20FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.nodes = [Mock()]
        self.flow = Shm20Flow()
        self.flow.SCHEDULED_TIMES_STRINGS = ["19:00:00"]
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.execute_flow")
    def test_shm_profile_shm_20_execute_flow__successful(self, mock_flow):
        SHM_20().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.create')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.get_nodes_list_by_attribute')
    def test_execute_flow_success(self, mock_nodes, mock_create, *_):
        mock_nodes.return_value = self.nodes
        self.flow.execute_flow()
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.create')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm20Flow.get_nodes_list_by_attribute')
    def test_execute_flow_add_error_as_exception(self, mock_nodes, mock_error, mock_create, *_):
        mock_nodes.return_value = self.nodes
        mock_create.side_effect = HTTPError
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)


class Shm21FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.nodes = [Mock()]
        self.flow = Shm21Flow()
        self.flow.SCHEDULED_TIMES_STRINGS = ["19:00:00"]
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.execute_flow")
    def test_shm_profile_shm_21_execute_flow__successful(self, mock_flow):
        SHM_21().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.create')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.get_nodes_list_by_attribute')
    def test_execute_flow_success(self, mock_nodes, mock_create, *_):
        mock_nodes.return_value = self.nodes
        self.flow.execute_flow()
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.SHMExport.create')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_export_flow.Shm21Flow.get_nodes_list_by_attribute')
    def test_execute_flow_add_error_as_exception(self, mock_nodes, mock_error, mock_create, *_):
        mock_nodes.return_value = self.nodes
        mock_create.side_effect = HTTPError
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
