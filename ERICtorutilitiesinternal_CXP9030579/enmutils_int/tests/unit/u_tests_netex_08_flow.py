import unittest2
from mock import patch, Mock
from enmutils_int.lib.profile_flows.netex_flows.netex_08_flow import Netex08Flow
from enmutils_int.lib.workload.netex_08 import NETEX_08
from enmutils.lib.exceptions import EnmApplicationError
from testslib import unit_test_utils


class Netex08UnNitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.mock_user = [Mock()]
        self.mock_response = Mock()
        self.profile = NETEX_08()
        self.flow = Netex08Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["cmedit_operator", "cmedit_administrator"]
        self.READ_CMD = 'cmedit get 5G131vCUCPRI001 "modules-state$$module".*'

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.execute_flow")
    def test_netex_08_execute_flow__successful(self, mock_flow):
        NETEX_08().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.create_profile_users')
    def test_execute_flow__success(self, mock_create_profile, mock_nodes, mock_keep_running, *_):
        mock_create_profile.return_value = self.mock_user
        nodes = [Mock(node_id='5G131vCUCP001')]
        mock_nodes.return_value = nodes
        vcucp_node_names_user = [(nodes, self.mock_user)]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.flow.create_and_execute_threads(vcucp_node_names_user, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.create_profile_users')
    def test_execute_flow_no_nodes(self, mock_create_profile, mock_nodes):
        mock_create_profile.return_value = self.mock_user
        mock_nodes.return_value = []
        with self.assertRaises(EnmApplicationError) as context:
            self.flow.execute_flow()
        self.assertEqual(str(context.exception), "No Nodes of vCUCP type are available in this deployment")

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.create_profile_users')
    def test_execute_flow_exception(self, mock_create_profile, mock_nodes, mock_keep_running, mock_create_and_execute_threads, mock_add_error, *_):
        mock_create_profile.return_value = self.mock_user
        mock_nodes.return_value = [Mock(node_id='5G131vCUCP001')]
        mock_keep_running.side_effect = [True, False]
        mock_create_and_execute_threads.side_effect = [Exception, Exception]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.log.logger.debug')
    def test_task_set_successful(self, *_):
        out = ['FDN : SbNetwork=cRAN,MeContext=5G130vCPRI001,modles-state=1,modle=ietf-tls-client..2019-11-20',
               'conformance-type : implement', 'correction : nll', 'name : ietf-tls-client',
               'namespace : rn:ietf:params:xml:ns:yang:ietf-tls-client', 'release : nll', 'revision : 2019-11-20',
               'version : nll', '10 instances']
        response = Mock()
        response.get_output.return_value = out
        self.user.enm_execute.return_value = response
        self.flow.task_set(['CORE01SGSN001'], self.flow, self.user)
        self.assertTrue(self.user.enm_execute.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.log.logger.debug')
    def test_task_set__logs_exception(self, *_):
        self.user.enm_execute.side_effect = Exception
        self.flow.task_set(['CORE01SGSN001'], self.flow, self.user)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_08_flow.Netex08Flow.add_error_as_exception')
    def test_task_set_instance_zero(self, mock_error):
        out = ['FDN : SbNetwork=cRAN,MeContext=5G130vCPRI001,modles-state=1,modle=ietf-tls-client..2019-11-20',
               'conformance-type : implement', 'correction : nll', 'name : ietf-tls-client',
               'namespace : rn:ietf:params:xml:ns:yang:ietf-tls-client', 'release : nll', 'revision : 2019-11-20',
               'version : nll', '0 instances']
        response = Mock()
        response.get_output.return_value = out
        self.user.enm_execute.return_value = response
        self.flow.task_set(['CORE01SGSN001'], self.flow, self.user)
        self.assertTrue(self.user.enm_execute.called)
        self.assertEqual(mock_error.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
