import unittest2

from mock import patch, Mock
from requests import HTTPError
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow import ParMgt03Flow


class ParMgt03UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = ParMgt03Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]
        self.flow.NUMBER_OF_MOS = 40000
        self.flow.PARAMETERS = ["userLabel", "nRFreqRelationId"]
        self.flow.MO_TYPES = ["EUtranCellFDD", "NRCellCU"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.time.sleep')
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.perform_netex_search")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.get_fdns_from_poids")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.create_profile_users")
    def test_parmgt_03_flow_success(self, mock_create_users, mock_keep_running, mock_get_fdns, *_):
        mock_user = Mock()
        mock_import_file = Mock()
        mock_import_file_text = Mock()
        mock_import_file.status_code = 200
        mock_import_file_text.splitlines.return_value = ["some text /n text"]
        mock_import_file.text = mock_import_file_text
        mock_user.post.side_effect = [mock_import_file]
        mock_create_users.return_value = [mock_user]
        mock_keep_running.side_effect = [True, False]
        mock_get_fdns.return_value = ["some9458498549thing"]

        self.flow.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_get_fdns.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.time.sleep')
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.perform_netex_search")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.get_fdns_from_poids")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.create_profile_users")
    def test_parmgt_03_flow_no_parameters(self, mock_create_users, mock_keep_running, mock_get_fdns, *_):
        mock_user = Mock()
        mock_import_file = Mock()
        mock_import_file_text = Mock()
        mock_import_file.status_code = 200
        mock_import_file_text.splitlines.return_value = ["some text /n text"]
        self.flow.PARAMETERS = []
        mock_import_file.text = mock_import_file_text
        mock_user.post.side_effect = [mock_import_file]
        mock_create_users.return_value = [mock_user]
        mock_keep_running.side_effect = [True, False]
        mock_get_fdns.side_effect = Exception('error')

        self.flow.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertFalse(mock_get_fdns.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.time.sleep')
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.perform_netex_search")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.get_fdns_from_poids")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.create_profile_users")
    def test_parmgt_03_flow_get_fdns_throws_http_error(self, mock_create_users, mock_add_error,
                                                       mock_keep_running, mock_get_fdns, *_):
        mock_get_fdns.side_effect = HTTPError()
        mock_user = Mock()
        mock_create_users.return_value = [mock_user]
        mock_keep_running.side_effect = [True, False]

        self.flow.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_get_fdns.called)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.time.sleep')
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.perform_netex_search")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.get_fdns_from_poids")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.create_profile_users")
    def test_parmgt_03_flow_import_file_throws_http_error(self, mock_create_users, mock_add_error, mock_keep_running,
                                                          mock_get_fdns, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.staus_code = 420
        mock_response.raise_for_status.side_effect = HTTPError()
        mock_user.post.return_value = mock_response
        mock_create_users.return_value = [mock_user]
        mock_keep_running.side_effect = [True, False]
        mock_get_fdns.return_value = ["some9458498549thing"]

        self.flow.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_get_fdns.called)
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.log.logger")
    def test_verify_import_file_success(self, mock_log):
        import_file = Mock()
        import_file_text = Mock()
        import_file_text.splitlines.return_value = ["file one", "line>two"]
        import_file.text = import_file_text
        self.flow.verify_import_file("line", "two", import_file, [Mock()])

        self.assertTrue(mock_log.info.called)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.log.logger")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.add_error_as_exception")
    def test_verify_import_file_no_text_error(self, mock_add_error, *_):
        import_file = Mock()
        import_file.text = None
        self.flow.verify_import_file("line", "two", import_file, [Mock()])

        self.assertTrue(mock_add_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
