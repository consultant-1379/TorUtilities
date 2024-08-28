import unittest2

from requests.exceptions import ChunkedEncodingError

from mock import patch, PropertyMock, Mock
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow import CmEventsNbi01


class CmEventsNbiUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.profile = CmEventsNbi01()
        self.profile.USER_ROLES = 'ADMINISTRATOR'
        self.profile.NUM_USERS = 1
        self.profile.EVENT_LIMIT = 10
        self.profile.URL = 'some_url'

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.sleep')
    @patch("enmutils.lib.persistence.get")
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.keep_running')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.'
           'create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.create_profile_users')
    def test_execute_cmevent_flow__success_cenm(self, mock_create_profile_users, mock_create_and_execute_threads,
                                                mock_keep_running, mock_persistence, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_persistence.return_value = "five_k_network"
        mock_keep_running.side_effect = [True, False]
        self.profile.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.is_enm_on_cloud_native')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.sleep')
    @patch("enmutils.lib.persistence.get")
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.keep_running')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.'
           'create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.create_profile_users')
    def test_execute_cmevent_flow__success(self, mock_create_profile_users, mock_create_and_execute_threads,
                                           mock_keep_running, mock_persistence, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        self.profile.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.raise_for_status')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.log.logger.debug')
    def test_get_events_is_successful(self, mock_debug, _):
        response = Mock()
        response.json.return_value = {"events": ["evts"] * 3}
        self.user.get.return_value = response
        self.profile.task_set(self.user, self.profile)
        mock_debug.assert_called_with("Successfully retrieved events from cm events nbi.")

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.raise_for_status')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_get_events_request__exception(self, mock_add_error, mock_raise_for_status):
        self.user.get.side_effect = ChunkedEncodingError("Chunked.")
        self.profile.task_set(self.user, self.profile)
        self.assertEqual(1, mock_add_error.call_count)
        self.assertEqual(0, mock_raise_for_status.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
