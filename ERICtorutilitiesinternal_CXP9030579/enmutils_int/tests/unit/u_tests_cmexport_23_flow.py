import unittest2

from mock import Mock, patch

from enmutils.lib.exceptions import ScriptEngineResponseValidationError
from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow import CmExport23Flow
from testslib import unit_test_utils


class CmExport23UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = CmExport23Flow()
        self.flow.NAME = "CMEXPORT_23"
        self.flow.NUM_USERS = 1
        self.flow.TIMEOUT = 30
        self.flow.USER_ROLES = ['Cmedit_Operator', 'CM_REST_Administrator']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmExport23Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmManagement.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmExportFlow.execute_flow')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmExport23Flow.'
           'update_profile_persistence_nodes_list')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmManagement.supervise')
    def test_execute_flow__is_successful(self, mock_cm_export_flow, mock_update_profile_persistence_nodes_list,
                                         mock_execute_flow, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 1)
        self.assertEqual(mock_cm_export_flow.call_count, 1)
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmExport23Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmManagement.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmExportFlow.execute_flow')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmExport23Flow.'
           'update_profile_persistence_nodes_list')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmManagement.supervise')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmExport23Flow.add_error_as_exception')
    def test_execute_flow__add_error_as_exception(self, mock_add_error, mock_management, *_):
        mock_management.side_effect = ScriptEngineResponseValidationError("error", Mock())
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)


if __name__ == '__main__':
    unittest2.main(verbosity=2)
