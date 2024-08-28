import unittest2
from mock import patch, Mock, PropertyMock

from enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow import LogViewerFlow, tasks
from testslib import unit_test_utils


class LogViewerFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.flow = LogViewerFlow()
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewerFlow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewerFlow.sleep')
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewerFlow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewerFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewer.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.ThreadQueue.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.ThreadQueue.execute')
    def test_execute_flow__success(self, mock_execute, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewerFlow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewerFlow.sleep')
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewerFlow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewerFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewer.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.ThreadQueue.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.ThreadQueue.execute',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.log.logger.debug')
    def test_execute_flow__logs_exception(self, mock_debug, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_debug.call_count)

    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.time.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.randint', return_value=0)
    def test_tasks__successful(self, *_):
        mock_viewer = Mock()
        tasks(mock_viewer)
        self.assertEqual(1, mock_viewer.get_log_viewer.call_count)
        self.assertEqual(1, mock_viewer.get_log_viewer_by_search_term.call_count)
        self.assertEqual(1, mock_viewer.get_log_viewer_help.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
