#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils.lib.enm_node import ERBSNode
from enmutils.lib.enm_user_2 import User
from enmutils.lib.exceptions import EnvironError, ScriptEngineResponseValidationError, EnmApplicationError
from enmutils_int.lib import cmcli
from testslib import unit_test_utils


@patch('enmutils.lib.enm_user_2.User.open_session')
class CmCliUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = User(username="enm_cli_unit")
        self.failed_output = [u'Error ']
        self.good_output = [u'1 instance(s) ']
        self.erbs_node1 = ERBSNode("netsim_LTE04ERBS00003", "255.255.255.255", "5.1.120", "1094-174-285",
                                   security_state='ON', normal_user='test', normal_password='test',
                                   secure_user='test',
                                   secure_password='test', subnetwork='SubNetwork=ERBS-SUBNW-1',
                                   netsim="netsimlin704",
                                   simulation="LTE01", user=self.user)
        self.cell_id = "LTE26ERBS00032-1"
        self.attribute = "acBarringInfoPresent"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_network_sync_status_raises_exception(self, mock_enm_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = self.failed_output
        mock_enm_execute.return_value = mock_response
        self.assertRaises(EnmApplicationError, cmcli.get_network_sync_status, self.user)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_network_sync_status(self, mock_enm_execute, *_):
        output = [u'FDN : NetworkElement=CORE11ESAPC0001,CmFunction=1',
                  u'syncStatus : UNSYNCHRONIZED', u'',
                  u'FDN : NetworkElement=netsim_LTE05ERBS00021,CmFunction=1',
                  u'syncStatus : SYNCHRONIZED', u'',
                  u'FDN : NetworkElement=netsim_LTE05ERBS00022,CmFunction=1',
                  u'syncStatus : SYNCHRONIZED', u'',
                  u'FDN : NetworkElement=netsim_LTE05ERBS00023,CmFunction=1',
                  u'syncStatus : SYNCHRONIZED', u'',
                  u'FDN : NetworkElement=netsim_LTE05ERBS00024,CmFunction=1',
                  u'syncStatus : SYNCHRONIZED', u'', u'', u'5 instance(s)']
        mock_response = Mock()
        mock_response.get_output.return_value = output
        mock_enm_execute.return_value = mock_response
        res = cmcli.get_network_sync_status(self.user)
        self.assertIsNotNone(res)

    @patch('time.sleep')
    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_cell_relations_fdd__use_provided_relation(self, mock_execute, *_):
        mock_node = Mock(node_id='node123', lte_cell_type='FDD')
        cmcli.get_cell_relations(self.user, mock_node, "EUtranCellFDD", "GeranFreqGroupRelation")
        expected_cmedit_cmd = "cmedit get {node_id} {cell_type}, {relation_type}".format(node_id=mock_node.node_id,
                                                                                         cell_type='EUtranCellFDD',
                                                                                         relation_type='GeranFreqGroupRelation')

        mock_execute.assert_called_with(self.user, expected_cmedit_cmd)

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_cell_relations_tdd__use_provided_relation(self, mock_execute, _):
        mock_node = Mock(node_id='node123', lte_cell_type='TDD')
        cmcli.get_cell_relations(self.user, mock_node, "EUtranCellTDD", "GeranFreqGroupRelation")
        expected_cmedit_cmd = "cmedit get {node_id} {cell_type}, {relation_type}".format(node_id=mock_node.node_id,
                                                                                         cell_type='EUtranCellTDD',
                                                                                         relation_type='GeranFreqGroupRelation')

        mock_execute.assert_called_with(self.user, expected_cmedit_cmd)

    @patch('enmutils_int.lib.cmcli.random.choice', return_value='EUtranCellRelation')
    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_cell_relations_fdd__no_relation_provided(self, mock_execute, *_):
        mock_node = Mock(node_id='node123', lte_cell_type='FDD')
        cmcli.get_cell_relations(self.user, mock_node, 'EUtranCellFDD')
        expected_cmedit_cmd = "cmedit get {node_id} {cell_type}, {relation_type}".format(node_id=mock_node.node_id,
                                                                                         cell_type='EUtranCellFDD',
                                                                                         relation_type='EUtranCellRelation')

        mock_execute.assert_called_with(self.user, expected_cmedit_cmd)

    @patch('enmutils_int.lib.cmcli.random.choice', return_value='EUtranCellRelation')
    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_cell_relations_tdd__no_relation_provided(self, mock_execute, *_):
        mock_node = Mock(node_id='node123', lte_cell_type='TDD')
        cmcli.get_cell_relations(self.user, mock_node, 'EUtranCellTDD')
        expected_cmedit_cmd = "cmedit get {node_id} {cell_type}, {relation_type}".format(node_id=mock_node.node_id,
                                                                                         cell_type='EUtranCellTDD',
                                                                                         relation_type='EUtranCellRelation')

        mock_execute.assert_called_with(self.user, expected_cmedit_cmd)

    @patch('time.sleep')
    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli', side_effect=ScriptEngineResponseValidationError('Error', Mock()))
    def test_get_cell_relations_fdd__raises_scripting_error(self, *_):
        self.assertRaises(ScriptEngineResponseValidationError, cmcli.get_cell_relations, self.user, Mock(), 'EUtranCellFDD')

    @patch('time.sleep')
    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli',
           side_effect=ScriptEngineResponseValidationError('Error', Mock()))
    def test_get_cell_relations_tdd__raises_scripting_error(self, *_):
        self.assertRaises(ScriptEngineResponseValidationError, cmcli.get_cell_relations, self.user, Mock(), 'EUtranCellTDD')

    @patch('time.sleep')
    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_cell_attributes__parses_the_correct_result(self, mock_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = [u">>cmedit get ieatnetsimv6018-07_LTE26ERBS00032 EUtranCellFDD."
                                                 u"EUtranCellFDDId==LTE26ERBS00032-1 EUtranCellFDD."
                                                 u"acBarringInfoPresent",
                                                 u"FDN : SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv6018-07_"
                                                 u"LTE26ERBS00032,ManagedElement=1,ENodeBFunction=1,"
                                                 u"EUtranCellFDD=LTE26ERBS00032-1",
                                                 u"acBarringInfoPresent : false", u"", u"", u"1 instance(s)"]
        mock_execute.return_value = mock_response
        results = cmcli.get_cell_attributes(self.user, self.erbs_node1, self.cell_id, [self.attribute])
        self.assertEqual(results, {self.attribute: 'false'})

    @patch('time.sleep')
    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli', side_effect=ScriptEngineResponseValidationError('Error', Mock()))
    def test_get_cell_attributes__raises_scripting_error(self, *_):

        self.assertRaises(ScriptEngineResponseValidationError, cmcli.get_cell_attributes, self.user, self.erbs_node1, self.cell_id, [self.attribute])

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_list_objects_in_network_that_match_specific_criteria(self, mock_execute_on_cli, *_):
        cmcli.list_objects_in_network_that_match_specific_criteria(self.user, 'ENodeBFunction', 'EUtranCellFDD')
        mock_execute_on_cli.assert_called_with(self.user, "cmedit get * ENodeBFunction,EUtranCellFDD.(administrativeState==LOCKED)")

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_bfd(self, mock_execute_on_cli, *_):
        mock_user = Mock()
        cmcli.get_bfd(mock_user)
        mock_execute_on_cli.assert_called_once_with(mock_user, "cmedit get * BFD.ipNetwork")

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_cells_zzztemporary34_csirsperiodicity__4g_fdd_command(self, mock_execute_on_cli, *_):
        mock_user = Mock()
        cmcli.get_cells_zzztemporary34_csirsperiodicity(mock_user, 'node123', 'ENodeB', 'EUtranCellFDD')
        mock_execute_on_cli.assert_called_once_with(mock_user, "cmedit get node1* EUtranCellFDD.zzzTemporary34")

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_cells_zzztemporary34_csirsperiodicity__4g_tdd_command(self, mock_execute_on_cli, *_):
        mock_user = Mock()
        cmcli.get_cells_zzztemporary34_csirsperiodicity(mock_user, 'node123', 'ENodeB', 'EUtranCellTDD')
        mock_execute_on_cli.assert_called_once_with(mock_user, "cmedit get node1* EUtranCellTDD.zzzTemporary34")

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_cells_zzztemporary34_csirsperiodicity__5g_command(self, mock_execute_command_on_enm_cli, *_):
        mock_user = Mock()
        cmcli.get_cells_zzztemporary34_csirsperiodicity(mock_user, 'node123', 'GNodeB', 'NRCellDU')
        mock_execute_command_on_enm_cli.assert_called_once_with(mock_user, "cmedit get node1* NRCellDU.csiRsPeriodicity")

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_process_get_administrator_state(self, mock_enm_execute, *_):
        output = [u"FDN : SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv6018-07_LTE26ERBS00014,ManagedElement=1,"
                  u"ENodeBFunction=1,EUtranCellFDD=LTE26ERBS00014-1",
                  u"administrativeState : UNLOCKED",
                  u"FDN : SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv6018-07_LTE26ERBS00014,ManagedElement=1,"
                  u"ENodeBFunction=1,EUtranCellFDD=LTE26ERBS00014-2",
                  u"administrativeState : UNLOCKED",
                  u"FDN : SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv6018-07_LTE26ERBS00014,ManagedElement=1,"
                  u"ENodeBFunction=1,EUtranCellFDD=LTE26ERBS00014-3",
                  u"administrativeState : UNLOCKED", u"", u"", u"3 instance(s)"]
        mock_response = Mock()
        mock_response.get_output.return_value = output
        mock_enm_execute.return_value = mock_response
        expected_result = [
            {'cell_id': 'LTE26ERBS00014-1', 'cell_state': 'UNLOCKED'},
            {'cell_id': 'LTE26ERBS00014-2', 'cell_state': 'UNLOCKED'},
            {'cell_id': 'LTE26ERBS00014-3', 'cell_state': 'UNLOCKED'}]
        self.assertEqual(expected_result, cmcli.get_administrator_state(self.user, self.erbs_node1, 'EUtranCellFDD')[0])

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_process_get_administrator_state_raises_exception_on_cell_mismatch(self, mock_enm_execute, *_):
        output = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE08ERBS00003,ManagedElement=1,ENodeBFunction=1,'
                  u'EUtranCellFDD=LTE08ERBS00003-1', u'', u'', u'1 instance(s)']
        mock_response = Mock()
        mock_response.get_output.return_value = output
        mock_enm_execute.return_value = mock_response
        self.assertRaises(ScriptEngineResponseValidationError, cmcli.get_administrator_state, self.user,
                          self.erbs_node1, 'EUtranCellFDD')

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_process_get_administrator_state_raises_exception(self, mock_enm_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = self.failed_output
        mock_enm_execute.return_value = mock_response
        self.assertRaises(EnmApplicationError, cmcli.get_administrator_state, self.user,
                          self.erbs_node1, 'EUtranCellFDD')

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_collection(self, mock_enm_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = self.good_output
        mock_enm_execute.return_value = mock_response
        res = cmcli.get_collection(self.user, "unit_collection")
        self.assertIsNotNone(res)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_collection_raises_exception(self, mock_enm_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = self.failed_output
        mock_enm_execute.return_value = mock_response
        self.assertRaises(EnmApplicationError, cmcli.get_collection, self.user, "unit_collection")

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.get')
    def test_get_url_and_log_result_on_exception(self, mock_get, mock_debug, _):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        cmcli.cm_cli_home(self.user)
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.enm_user_2.User.get')
    def test_get_url_and_log_result_success(self, mock_get, _):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        cmcli.cm_cli_home(self.user)

    @patch('enmutils.lib.enm_user_2.User.get')
    def test_get_url(self, mock_get, *_):
        cmcli.cm_cli_home(self.user)
        mock_get.assert_called_with('/#cliapp')

    @patch('enmutils.lib.enm_user_2.User.get')
    def test_get_cmcli_help_(self, mock_get, *_):
        cmcli.cm_cli_help(self.user)
        self.assertEqual(mock_get.call_count, 10)

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_node_cells__raises_exception_if_no_cell_information_returned(self, mock_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = ["", ""]
        mock_execute.return_value = mock_response
        self.assertRaises(EnmApplicationError, cmcli.get_node_cells, self.user, self.erbs_node1, 'EUtranCellFDD')

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_node_cells__raises_exception_due_to_error_in_response_text(self, mock_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = self.failed_output
        mock_execute.return_value = mock_response
        self.assertRaises(EnmApplicationError, cmcli.get_node_cells, self.user, self.erbs_node1, 'EUtranCellFDD')

    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_get_node_cells__success(self, mock_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = [
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00010,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD=LTE02ERBS00010-1', u'EUtranCellFDDId : LTE02ERBS00010-1',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00010,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD=LTE02ERBS00010-2', u'EUtranCellFDDId : LTE02ERBS00010-2',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00010,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD=LTE02ERBS00010-3', u'EUtranCellFDDId : LTE02ERBS00010-3']
        mock_execute.return_value = mock_response
        expected_result = ['LTE02ERBS00010-1', 'LTE02ERBS00010-2', 'LTE02ERBS00010-3']
        self.assertEqual(expected_result, cmcli.get_node_cells(self.user, self.erbs_node1, 'EUtranCellFDD'))

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.cmcli.execute_command_on_enm_cli')
    def test_set_cell_attributes(self, mock_enm_execute, *_):

        cmcli.set_cell_attributes(self.user, self.erbs_node1, 'EUtranCellFDD.EUtranCellFDDId==LTE02ERBS00028-1',
                                  {u'acBarringInfoPresent': 1, u'antennaUnit': 2})
        self.assertEqual(mock_enm_execute.call_count, 2)
        mock_enm_execute.assert_called_with(self.user,
                                            'cmedit set netsim_LTE04ERBS00003 EUtranCellFDD.EUtranCellFDDId==EUtranCellFDD.EUtranCellFDDId==LTE02ERBS00028-1 EUtranCellFDD.acBarringInfoPresent=1')

    def test_set_cell_attributes_no_attribute_raises_error(self, *_):
        self.assertRaises(EnvironError, cmcli.set_cell_attributes, self.user, self.erbs_node1,
                          'EUtranCellFDD.EUtranCellFDDId==LTE02ERBS00028-1', {None: u'false'})

    def test_set_cell_attributes_no_value_raises_error(self, *_):
        self.assertRaises(EnvironError, cmcli.set_cell_attributes, self.user, self.erbs_node1,
                          'EUtranCellFDD.EUtranCellFDDId==LTE02ERBS00028-1', {u'acBarringInfoPresent': None})

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_node_gerancell_value_success(self, mock_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = [
            u'FDN : SubNetwork=NETSimG,MeContext=GSM02BSC01,ManagedElement=GSM02BSC01,BscFunction=1,'
            u'BscM=1,GeranCellM=1,GeranCell=173027O']
        mock_execute.return_value = mock_response
        self.assertEqual([u'173027O'], cmcli.get_node_gerancell_value([self.user], [self.erbs_node1]))

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_node_gerancell_value_raises_ScriptEngineResponseValidationError(self, mock_execute, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = [u'FDN : SubNetwork=NETSimG,MeContext=GSM02BSC01,'
                                                 u'ManagedElement=GSM02BSC01,BscFunction=1']
        mock_execute.return_value = mock_response
        self.assertRaises(ScriptEngineResponseValidationError, cmcli.get_node_gerancell_value,
                          [self.user], [self.erbs_node1])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
