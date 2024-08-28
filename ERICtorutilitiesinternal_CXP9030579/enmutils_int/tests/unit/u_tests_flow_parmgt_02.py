#!/usr/bin/env python
import unittest2

from mock import patch, Mock
from requests import HTTPError, ConnectionError
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow import ParMgt02Flow


class ParMgt02UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = ParMgt02Flow()
        self.flow.NAME = "PARMGT_02"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]
        self.flow.MAX_NUM_PARAMETER_SETS = 5
        self.flow.NUM_PARAMETER_SETS = 2
        self.flow.CHUNK_SIZE = 1
        self.flow.SLEEP_TIMES_FOR_RETRY = [0]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("time.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile.Profile.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set_count")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.create_profile_users")
    def test_execute_flow_is_successful(self, mock_create_profile_users,
                                        mock_keep_running, mock_create_and_execute_threads,
                                        mock_get_parameter_set_count, mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_get_parameter_set_count.return_value = 0
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertTrue(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set_count")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.create_profile_users")
    def test_execute_flow_raises_http_error(self, mock_create_profile_users,
                                            mock_keep_running, mock_create_and_execute_threads,
                                            mock_get_parameter_set_count, mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_get_parameter_set_count.side_effect = HTTPError
        self.flow.execute_flow()
        self.assertFalse(mock_create_and_execute_threads.called)
        self.assertTrue(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set_count")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.create_profile_users")
    def test_execute_flow_raises_exception(self, mock_create_profile_users,
                                           mock_keep_running, mock_create_and_execute_threads,
                                           mock_get_parameter_set_count, mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_get_parameter_set_count.side_effect = Exception
        self.flow.execute_flow()
        self.assertFalse(mock_create_and_execute_threads.called)
        self.assertTrue(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.mutex")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.delete_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.create_parameter_set")
    def test_task_set_is_successful(self, mock_create_parameter_set,
                                    mock_delete_parameter_set, mock_get_parameter_set, *_):
        self.flow.max_limit = 2
        self.flow.daily_limit = 1
        mock_get_parameter_set.return_value = {u"errorCode": 0, u"resultSize": 1,
                                               u"parameterSets": [
                                                   {u"description": u"created by PARMGT_02 workload profile",
                                                    u"userId": u"parmgt_02_0514-13455223_u0",
                                                    u"lastUpdated": 1526301965065,
                                                    u"id": u"281475033979965", u"readOnly": False,
                                                    u"type": u"USER_DEFINED", u"parameterDetails": None,
                                                    u"name": u"PARMGT_02_0514-13460505_5"}], u"statusMessage": u"OK"}
        self.flow.task_set(self.user, self.flow)
        self.assertEqual(mock_create_parameter_set.call_count, 3)
        self.assertEqual(mock_delete_parameter_set.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.mutex")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.delete_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.create_parameter_set")
    def test_task_set_raises_connection_error(self, mock_create_parameter_set,
                                              mock_delete_parameter_set, *_):
        self.flow.max_limit = 1
        self.flow.daily_limit = 1
        mock_create_parameter_set.side_effect = ConnectionError
        self.flow.task_set(self.user, self.flow)
        self.assertEqual(mock_create_parameter_set.call_count, 1)
        self.assertEqual(mock_delete_parameter_set.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.mutex")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.delete_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.create_parameter_set")
    def test_task_set_raises_exception(self, mock_create_parameter_set,
                                       mock_delete_parameter_set, mock_get_parameter_set, *_):
        self.flow.max_limit = 1
        self.flow.daily_limit = 1
        mock_get_parameter_set.side_effect = Exception
        self.flow.task_set(self.user, self.flow)
        self.assertEqual(mock_create_parameter_set.call_count, 1)
        self.assertEqual(mock_delete_parameter_set.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.mutex")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.delete_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.create_parameter_set")
    def test_task_set__raises_exception_when_delete_raises_http_error(self, mock_create_parameter_set,
                                                                      mock_delete_parameter_set, mock_get_parameter_set,
                                                                      *_):
        self.flow.max_limit = 1
        self.flow.daily_limit = 1
        mock_get_parameter_set.return_value = {u"errorCode": 0, u"resultSize": 1,
                                               u"parameterSets": [
                                                   {u"description": u"created by PARMGT_02 workload profile",
                                                    u"userId": u"parmgt_02_0514-13455223_u0",
                                                    u"lastUpdated": 1526301965065,
                                                    u"id": u"281475033979965", u"readOnly": False,
                                                    u"type": u"USER_DEFINED", u"parameterDetails": None,
                                                    u"name": u"PARMGT_02_0514-13460505_5"}], u"statusMessage": u"OK"}
        mock_delete_parameter_set.side_effect = HTTPError
        self.flow.task_set(self.user, self.flow)
        self.assertEqual(mock_create_parameter_set.call_count, 1)
        self.assertEqual(mock_delete_parameter_set.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.mutex")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.delete_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.create_parameter_set")
    def test_task_set__raises_exception_when_create_raises_http_error(self, mock_create_parameter_set,
                                                                      mock_delete_parameter_set, mock_get_parameter_set,
                                                                      *_):
        self.flow.max_limit = 1
        self.flow.daily_limit = 1
        mock_get_parameter_set.return_value = {u"errorCode": 0, u"resultSize": 1,
                                               u"parameterSets": [
                                                   {u"description": u"created by PARMGT_02 workload profile",
                                                    u"userId": u"parmgt_02_0514-13455223_u0",
                                                    u"lastUpdated": 1526301965065,
                                                    u"id": u"281475033979965", u"readOnly": False,
                                                    u"type": u"USER_DEFINED", u"parameterDetails": None,
                                                    u"name": u"PARMGT_02_0514-13460505_5"}], u"statusMessage": u"OK"}
        mock_create_parameter_set.side_effect = [Mock(), HTTPError]
        self.flow.task_set(self.user, self.flow)
        self.assertEqual(mock_create_parameter_set.call_count, 2)
        self.assertEqual(mock_delete_parameter_set.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.delete_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.chunks")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set_count")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set")
    def test_clean_up_is_successful(self, mock_get_parameter_set,
                                    mock_get_parameter_set_count, mock_log, mock_chunks, *_):
        mock_get_parameter_set.return_value = {u"errorCode": 0, u"resultSize": 1,
                                               u"parameterSets": [
                                                   {u"description": u"created by PARMGT_02 workload profile",
                                                    u"userId": u"parmgt_02_0514-13455223_u0",
                                                    u"lastUpdated": 1526301965065,
                                                    u"id": u"281475033979965", u"readOnly": False,
                                                    u"type": u"USER_DEFINED", u"parameterDetails": None,
                                                    u"name": u"PARMGT_02_0514-13460505_5"}], u"statusMessage": u"OK"}
        mock_chunks.return_value = [{u"description": u"created by PARMGT_02 workload profile",
                                     u"userId": u"parmgt_02_0514-13455223_u0",
                                     u"lastUpdated": 1526301965065,
                                     u"id": u"281475033979965", u"readOnly": False,
                                     u"type": u"USER_DEFINED", u"parameterDetails": None,
                                     u"name": u"PARMGT_02_0514-13460505_5"}]
        mock_get_parameter_set_count.return_value = 0
        self.flow.clean_up(self.user)
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.delete_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set_count")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set")
    def test_clean_up_raises_http_error(self, mock_get_parameter_set,
                                        mock_get_parameter_set_count, mock_log, _):
        mock_get_parameter_set.side_effect = HTTPError
        self.flow.users = [self.user]
        mock_get_parameter_set_count.return_value = 0
        self.flow.clean_up(self.user)
        self.assertEqual(mock_log.logger.info.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.delete_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set_count")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set")
    def test_clean_up_raises_exception(self, mock_get_parameter_set,
                                       mock_get_parameter_set_count, mock_log, _):
        mock_get_parameter_set.side_effect = Exception
        self.flow.users = [self.user]
        mock_get_parameter_set_count.return_value = 0
        self.flow.clean_up(self.user)
        self.assertEqual(mock_log.logger.info.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.json.dumps")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.choice")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.create_parameter_set")
    def test_create_parameter_sets_up_to_max__is_success(self, mock_create_parameter_set, *_):
        self.flow.create_parameter_sets_up_to_max(self.user, self.flow)
        self.assertTrue(mock_create_parameter_set.called)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.log")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.mutex")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.get_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.delete_parameter_set")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.create_parameter_set")
    def test_task_set__raises_exception_when_parameter_set_None(self, mock_create_parameter_set,
                                                                mock_delete_parameter_set, mock_get_parameter_set, *_):
        self.flow.max_limit = 1
        self.flow.daily_limit = 1
        mock_get_parameter_set.return_value = {u"errorCode": 0, u"resultSize": 1,
                                               u"parameterSets": [], u"statusMessage": u"OK"}
        self.flow.task_set(self.user, self.flow)
        self.assertEqual(mock_create_parameter_set.call_count, 1)
        self.assertEqual(mock_delete_parameter_set.call_count, 0)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
