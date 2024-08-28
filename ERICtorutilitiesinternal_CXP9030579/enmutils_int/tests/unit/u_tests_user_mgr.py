from requests.exceptions import HTTPError

import unittest2

from testslib import unit_test_utils
import enmutils_int.bin.user_mgr as mgr
from mock import patch, Mock


class UserMgrUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.mock_user = Mock()
        self.mock_user.username = 'test_user'
        mock_role = Mock()
        mock_role.name = 'test_role'
        self.mock_user.roles = [mock_role]
        self.users_list = [self.mock_user, self.mock_user]
        self.file_path = '/file_path'
        self.email = 'test@test'
        self.roles_list = "test_role1, test_role2"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.bin.user_mgr.log')
    def test_list_users__invalid_limit(self, mock_log):
        mgr.list_users(limit='test')
        mock_log.red_text.assert_called_once_with("Please enter a valid number or 'all' argument. "
                                                  "'test' is not a valid option for limit.")

    @patch('enmutils_int.bin.user_mgr.tabulate')
    @patch('enmutils_int.bin.user_mgr.enm_user.get_user_privileges')
    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user')
    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    def test_list_users__success_with_valid_limit(self, mock_user, mock_admin, *_):
        mock_user.get_usernames.return_value = self.users_list
        mgr.list_users(limit='0')
        mock_user.get_usernames.assert_called_with(user=mock_admin.return_value)

    @patch('enmutils_int.bin.user_mgr.tabulate')
    @patch('enmutils_int.bin.user_mgr.enm_user.get_user_privileges')
    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user')
    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    def test_list_users__success(self, mock_user, mock_admin, mock_previleges, _):
        mock_user.get_usernames.return_value = self.users_list
        mgr.list_users()
        mock_user.get_usernames.assert_called_with(user=mock_admin.return_value)
        self.assertEqual(2, mock_previleges.call_count)

    @patch('enmutils_int.bin.user_mgr.tabulate')
    @patch('enmutils_int.bin.user_mgr.log')
    @patch('enmutils_int.bin.user_mgr.enm_user.get_user_privileges')
    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user')
    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    def test_list_users__success_with_prefix(self, mock_user, mock_admin, mock_previleges, mock_log, _):
        mock_user.get_usernames.return_value = self.users_list
        mgr.list_users(prefix='test_prefix')
        mock_user.get_usernames.assert_called_with(user=mock_admin.return_value)
        self.assertEqual(2, mock_previleges.call_count)
        mock_log.purple_text.assert_any_call('USERS WITH PREFIX test_prefix')

    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    @patch('enmutils_int.bin.user_mgr._execute')
    @patch('enmutils_int.bin.user_mgr._remove_users_with_invalid_usernames')
    @patch('enmutils_int.bin.user_mgr._remove_users_with_invalid_roles')
    def test_create_users_with_username_and_password__success_with_no_range_start(
            self, mock_remove_users_roles, mock_remove_users_usernames, mock_execute, mock_user):
        mgr.create_users_with_username_and_password('test_user', 'testPassword', self.mock_user.roles)
        mock_remove_users_roles.assert_called_once_with(mock_remove_users_usernames.return_value)
        mock_remove_users_usernames.assert_called_once_with([mock_user.return_value], expected=False)
        mock_execute.assert_called_once_with(mock_remove_users_roles.return_value, 'create')

    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    @patch('enmutils_int.bin.user_mgr._execute')
    @patch('enmutils_int.bin.user_mgr._remove_users_with_invalid_usernames')
    @patch('enmutils_int.bin.user_mgr._remove_users_with_invalid_roles')
    def test_create_users_with_username_and_password__success_with_range_start(
            self, mock_remove_users_roles, mock_remove_users_usernames, mock_execute, mock_user):
        mgr.create_users_with_username_and_password('test_user', 'testPassword', self.mock_user.roles, range_start=1,
                                                    range_end=1)
        mock_remove_users_roles.assert_called_once_with(mock_remove_users_usernames.return_value)
        mock_remove_users_usernames.assert_called_once_with([mock_user.return_value], expected=False)
        mock_execute.assert_called_once_with(mock_remove_users_roles.return_value, 'create')

    @patch('enmutils_int.bin.user_mgr._execute')
    @patch('enmutils_int.bin.user_mgr._remove_users_with_invalid_roles')
    @patch('enmutils_int.bin.user_mgr._remove_users_with_invalid_usernames')
    @patch('enmutils_int.bin.user_mgr._parser_users_from_file')
    def test_create_users_with_file__success(self, mock_parser, mock_remove_users_with_invalid_usernames,
                                             mock_remove_users_with_invalid_roles, mock_execute):
        mgr.create_users_with_file(self.file_path, 'testPassword')
        mock_parser.assert_called_with(self.file_path, 'create', password='testPassword')
        mock_remove_users_with_invalid_usernames.assert_called_with(mock_parser.return_value, expected=False)
        mock_remove_users_with_invalid_roles.assert_called_with(mock_remove_users_with_invalid_usernames.return_value)
        mock_execute.assert_called_with(mock_remove_users_with_invalid_roles.return_value, 'create')

    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    @patch('enmutils_int.bin.user_mgr._execute')
    @patch('enmutils_int.bin.user_mgr._remove_users_with_invalid_usernames')
    def test_delete_users_with_username__success_with_no_start_range(self, mock_remove_users, mock_execute, mock_user):
        mgr.delete_users_with_username('test_user')
        mock_user.assert_called_once_with('test_user', 'UNUSED PASSWORD')
        mock_remove_users.assert_called_once_with([mock_user.return_value], expected=True)
        mock_execute.assert_called_once_with(mock_remove_users.return_value, 'delete')

    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    @patch('enmutils_int.bin.user_mgr._execute')
    @patch('enmutils_int.bin.user_mgr._remove_users_with_invalid_usernames')
    def test_delete_users_with_username__success_with_start_range(self, mock_remove_users, mock_execute, mock_user):
        mgr.delete_users_with_username('test_user', range_start=1, range_end=1)
        mock_user.assert_called_once_with('test_user1', 'UNUSED PASSWORD')
        mock_remove_users.assert_called_once_with([mock_user.return_value], expected=True)
        mock_execute.assert_called_once_with(mock_remove_users.return_value, 'delete')

    @patch('enmutils_int.bin.user_mgr._execute')
    @patch('enmutils_int.bin.user_mgr._remove_users_with_invalid_usernames')
    @patch('enmutils_int.bin.user_mgr._parser_users_from_file')
    def test_delete_users_with_file__success(self, mock_parser, mock_remove_users, mock_execute):
        mgr.delete_users_with_file(self.file_path)
        mock_parser.assert_called_once_with(self.file_path, 'delete')
        mock_remove_users.assert_called_once_with(mock_parser.return_value, expected=True)
        mock_execute.assert_called_once_with(mock_remove_users.return_value, 'delete')

    @patch('enmutils_int.bin.user_mgr.enm_user.User.get_usernames', return_value=['test_user'])
    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user')
    def test_remove_users_with_invalid_usernames__success_with_no_invalid_users(self, *_):
        self.assertEqual(self.users_list, mgr._remove_users_with_invalid_usernames(self.users_list, expected=True))

    @patch('enmutils_int.bin.user_mgr.enm_user.User.get_usernames', return_value=['test'])
    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user')
    def test_remove_users_with_invalid_usernames__success_with_invalid_users(self, *_):
        self.assertEqual([], mgr._remove_users_with_invalid_usernames(self.users_list, expected=True))

    @patch('enmutils_int.bin.user_mgr.enm_user.EnmRole.get_all_role_names', return_value=['test_role'])
    def test_remove_users_with_invalid_roles__success_no_invalid_roles(self, _):
        self.assertEqual([self.mock_user], mgr._remove_users_with_invalid_roles([self.mock_user]))

    @patch('enmutils_int.bin.user_mgr.enm_user.EnmRole.get_all_role_names', return_value=['test'])
    def test_remove_users_with_invalid_roles__success_with_invalid_roles(self, _):
        self.assertEqual([], mgr._remove_users_with_invalid_roles([self.mock_user]))

    @patch('enmutils_int.bin.user_mgr.csv.reader')
    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    def test_parser_users_from_file__success_with_create_operation(self, mock_user, mock_csv_reader):
        with patch('__builtin__.open') as mock_open:
            mock_csv_reader.return_value = ["", "{'roles':['role_test']}"]
            self.assertEqual([mock_user.return_value], mgr._parser_users_from_file(self.file_path, 'create'))
            mock_open.assert_called_once_with(self.file_path)
            self.assertEqual(1, mock_user.call_count)
            mock_csv_reader.assert_called_once_with(mock_open().__enter__.return_value)

    @patch('enmutils_int.bin.user_mgr.csv.reader')
    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    def test_parser_users_from_file__conditions_check(self, mock_user, mock_csv_reader):
        with patch('__builtin__.open') as mock_open:
            mock_csv_reader.return_value = ['""', {'roles': 'test_role', 'email': self.email}]
            self.assertEqual([], mgr._parser_users_from_file(self.file_path, 'create'))
            mock_open.assert_called_once_with(self.file_path)
            mock_csv_reader.assert_called_once_with(mock_open().__enter__.return_value)

    @patch('enmutils_int.bin.user_mgr.csv.reader')
    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    def test_parser_users_from_file__success_with_delete_operation(self, mock_user, mock_csv_reader):
        with patch('__builtin__.open') as mock_open:
            mock_csv_reader.return_value = ["", "{'roles':['role_test']}"]
            self.assertEqual([mock_user.return_value], mgr._parser_users_from_file(self.file_path, 'delete'))
            mock_open.assert_called_once_with(self.file_path)
            self.assertEqual(1, mock_user.call_count)
            mock_csv_reader.assert_called_once_with(mock_open().__enter__.return_value)

    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    def test_execute__success(self, mock_user):
        self.assertTrue(mgr._execute([self.mock_user], 'create'))
        mock_user.create.assert_called_once_with(self.mock_user)

    @patch('enmutils_int.bin.user_mgr.enm_user.User')
    @patch('enmutils_int.bin.user_mgr.log.logger.error')
    def test_execute__returns_false_when_no_user_provided(self, mock_error, _):
        self.assertFalse(mgr._execute([], 'create'))
        mock_error.assert_called_once_with('No users to perform create operation on.'
                                           ' Please try again with valid users...')

    @patch('enmutils_int.bin.user_mgr.enm_user.User.create', side_effect=HTTPError('some error'))
    @patch('enmutils_int.bin.user_mgr.enm_user.User.__init__', return_value=None)
    @patch('enmutils_int.bin.user_mgr.log.logger.error')
    def test_execute__logs_error(self, mock_error, *_):
        self.assertFalse(mgr._execute([self.mock_user], 'create'))
        mock_error.assert_called_once_with('some error')

    @patch('enmutils_int.bin.user_mgr.init.global_init')
    @patch('enmutils_int.bin.user_mgr.signal.signal')
    @patch('enmutils_int.bin.user_mgr.docopt', side_effect=[SystemExit, SystemExit('some error')])
    @patch('enmutils_int.bin.user_mgr.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.user_mgr.log.logger.info')
    def test_cli__docopt_error(self, mock_info, *_):
        self.assertRaises(SystemExit, mgr.cli)
        self.assertRaises(UnboundLocalError, mgr.cli)
        mock_info.assert_called_once_with('\n some error')

    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user')
    @patch('enmutils_int.bin.user_mgr.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.user_mgr.init.global_init')
    @patch('enmutils_int.bin.user_mgr.signal.signal')
    @patch('enmutils_int.bin.user_mgr.create_users_with_username_and_password', return_value=Mock())
    @patch('enmutils_int.bin.user_mgr.docopt')
    @patch('enmutils_int.bin.user_mgr.init.exit')
    def test_cli__create_success(self, mock_exit, mock_docopt, mock_create_user, *_):
        mock_docopt.return_value = {'USERNAME': 'test_user', 'PASSWORD': 'test', 'RANGE': (1, 3), 'create': True,
                                    'ROLES': "test_role1, test_role2", 'FIRSTNAME': 'test', 'LASTNAME': 'test',
                                    'EMAIL': self.email, '--file': False}
        mgr.cli()
        mock_exit.assert_called_with(0)
        mock_create_user.assert_called_once_with('test_user', 'test', ['test_role1', ' test_role2'], 'test', 'test',
                                                 self.email, range_end=None, range_start=None)

    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user')
    @patch('enmutils_int.bin.user_mgr.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.user_mgr.init.global_init')
    @patch('enmutils_int.bin.user_mgr.signal.signal')
    @patch('enmutils_int.bin.user_mgr.delete_users_with_username', return_value=Mock())
    @patch('enmutils_int.bin.user_mgr.docopt')
    @patch('enmutils_int.bin.user_mgr.init.exit')
    def test_cli__delete_success(self, mock_exit, mock_docopt, mock_delete_user, *_):
        mock_docopt.return_value = {'USERNAME': 'test_user', 'PASSWORD': 'test', 'RANGE': (1, 3), 'create': False,
                                    'ROLES': self.roles_list, 'FIRSTNAME': 'test', 'LASTNAME': 'test',
                                    'EMAIL': self.email, '--file': False, 'delete': True}
        mgr.cli()
        mock_exit.assert_called_with(0)
        mock_delete_user.assert_called_once_with('test_user', range_end=None, range_start=None)

    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user')
    @patch('enmutils_int.bin.user_mgr.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.user_mgr.init.global_init')
    @patch('enmutils_int.bin.user_mgr.signal.signal')
    @patch('enmutils_int.bin.user_mgr.list_users', return_value=Mock())
    @patch('enmutils_int.bin.user_mgr.docopt')
    @patch('enmutils_int.bin.user_mgr.init.exit')
    def test_cli__list_success(self, mock_exit, mock_docopt, mock_list, *_):
        mock_docopt.return_value = {'USERNAME': 'test_user', 'PASSWORD': 'test', 'RANGE': (1, 3), 'create': False,
                                    'ROLES': self.roles_list, 'FIRSTNAME': 'test', 'LASTNAME': 'test',
                                    'EMAIL': self.email, '--file': False, 'delete': False, 'list': True, '--limit': 0}
        mgr.cli()
        mock_exit.assert_called_with(0)
        mock_list.assert_called_once_with('test_user')

    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user')
    @patch('enmutils_int.bin.user_mgr.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.user_mgr.init.global_init')
    @patch('enmutils_int.bin.user_mgr.signal.signal')
    @patch('enmutils_int.bin.user_mgr.list_users', return_value=Mock())
    @patch('enmutils_int.bin.user_mgr.docopt')
    @patch('enmutils_int.bin.user_mgr.init.exit')
    def test_cli__list_with_limit_success(self, mock_exit, mock_docopt, mock_list, *_):
        mock_docopt.return_value = {'USERNAME': 'test_user', 'PASSWORD': 'test', 'RANGE': (1, 3), 'create': False,
                                    'ROLES': self.roles_list, 'FIRSTNAME': 'test', 'LASTNAME': 'test',
                                    'EMAIL': self.email, '--file': False, 'delete': False, 'list': True, '--limit': 1}
        mgr.cli()
        mock_exit.assert_called_with(0)
        mock_list.assert_called_once_with('test_user', limit=1)

    @patch('enmutils_int.bin.user_mgr.get_workload_admin_user', side_effect=Exception('some error'))
    @patch('enmutils_int.bin.user_mgr.exception.handle_exception')
    @patch('enmutils_int.bin.user_mgr.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.user_mgr.init.global_init')
    @patch('enmutils_int.bin.user_mgr.signal.signal')
    @patch('enmutils_int.bin.user_mgr.list_users', return_value=Mock())
    @patch('enmutils_int.bin.user_mgr.docopt')
    @patch('enmutils_int.bin.user_mgr.init.exit')
    def test_cli__exception_and_exit_with_code_1(self, mock_exit, mock_docopt, *_):
        mock_docopt.return_value = {'USERNAME': 'test_user', 'PASSWORD': 'test', 'RANGE': (1, 3), 'create': False,
                                    'ROLES': self.roles_list, 'FIRSTNAME': 'test', 'LASTNAME': 'test',
                                    'EMAIL': self.email, '--file': False, 'delete': False, 'list': True, '--limit': 1}
        mgr.cli()
        mock_exit.assert_called_with(1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
