#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils.lib import enm_user_2 as enm_user
from enmutils_int.lib.amos_cmd import MoBatchCmd, get_specific_scripting_iterator, MoBatchCommandReturnedError, \
    EnmApplicationError, delete_left_over_sessions
from testslib import unit_test_utils

NODE_OKAY_STR = "Node: OK"


class MoBatchCmdUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        nodes = [Mock(node_id="id")] * 5
        user = enm_user.User("TestUser2", "T3stP4ssw0rd")
        commands = ["lt all", "get", "get Upgradepackage"]
        self.mo_batch_cmd = MoBatchCmd(nodes, user, commands, num_in_parallel=5, timeout=10)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_delete_left_over_sessions_successful(self):
        mock_user = Mock()
        mock_user.session = True
        mock_session_deleter = Mock()
        delete_left_over_sessions(mock_user, mock_session_deleter)
        self.assertTrue(mock_user.remove_session.called)

    def test_delete_left_over_sessions_false(self):
        mock_user = Mock()
        mock_user.session = False
        mock_session_deleter = Mock()
        delete_left_over_sessions(mock_user, mock_session_deleter)
        self.assertFalse(mock_user.remove_session.called)

    def test_delete_left_over_sessions_raises_enm_application_error(self):
        mock_user = Mock()
        mock_session_deleter = Mock()
        mock_user.username = "1234"
        mock_session_deleter.delete_request.side_effect = EnmApplicationError("User session {0} could not be deleted "
                                                                              "from scripting cluster".format(mock_user.username))
        with self.assertRaises(EnmApplicationError):
            delete_left_over_sessions(mock_user, mock_session_deleter)

    @patch("enmutils_int.lib.amos_cmd.shell.run_remote_cmd")
    def test_execute___in_mo_batch_raises_error_if_run_remote_cmd_raises_exception(self, mock_run_remote_cmd):
        mock_run_remote_cmd.side_effect = Exception("blah")

        with self.assertRaises(Exception) as e:
            self.mo_batch_cmd.execute()
        self.assertEqual(e.exception.message, "blah")

    @patch("enmutils_int.lib.amos_cmd.shell.run_remote_cmd")
    def test_mo_batch_execute_does_not_raise_error_if_response_is_valid(self, mock_run_remote_cmd):
        response = Mock(rc=0, stdout=NODE_OKAY_STR * 15)
        mock_run_remote_cmd.return_value = response
        self.mo_batch_cmd.execute()

    @patch("enmutils_int.lib.amos_cmd.shell.run_remote_cmd")
    def test_mo_batch_execute_raises_error_if_less_than_expected_number_of_oks_in_response_stdout(self,
                                                                                                  mock_run_remote_cmd):
        response = Mock(rc=0, stdout=NODE_OKAY_STR * 9)
        mock_run_remote_cmd.return_value = response
        self.assertRaises(MoBatchCommandReturnedError, self.mo_batch_cmd.execute)

    @patch("enmutils_int.lib.amos_cmd.shell.run_remote_cmd")
    @patch("enmutils_int.lib.amos_cmd.log.logger.debug")
    def test_mo_batch_does_not_raise_error_if_execution_is_killed_after_ten_minutes_duration(self, mock_debug,
                                                                                             mock_run_remote_cmd):
        response = Mock(rc=177, stdout=NODE_OKAY_STR * 10)
        mock_run_remote_cmd.return_value = response
        self.mo_batch_cmd.execute()
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.get_list_of_scripting_service_ips')
    def test_get_specific_scripting_iterator(self, mock_vm, *_):
        mock_vm.return_value = ['scp-1-scripting', 'scp-2-scripting', 'scp-3-scripting', 'scp-4-scripting']
        scripting_iterator = get_specific_scripting_iterator()
        self.assertTrue(scripting_iterator.next() in ['scp-1-scripting', 'scp-2-scripting', 'scp-3-scripting',
                                                      'scp-4-scripting'])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
