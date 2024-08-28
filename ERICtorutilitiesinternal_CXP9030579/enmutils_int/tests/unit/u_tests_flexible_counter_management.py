#!/usr/bin/env python

import unittest2
from requests.exceptions import HTTPError
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.flexible_counter_management import (verify_creation_or_deletion_flex_counters_status,
                                                          get_ebs_flex_counters, delete_flex_counters,
                                                          get_flex_counters, get_reserved_ebsn_flex_counters,
                                                          remove_any_existing_flexible_counters,
                                                          import_flex_counters_in_enm)
from mock import Mock, patch, mock_open
from testslib import unit_test_utils


class FlexibleCounterManagementUnitTests(unittest2.TestCase):

    flex_counters_json = [{"flexCounterName": "pmEbsMacTimeDlDrb_Qos98_QosType1",
                           "baseCounterName": "pmEbsMacTimeDlDrb",
                           "counterDescription": "Description: Aggregated time for HARQ initial transmission "
                                                 "scheduling downlink of DRB since DRB was last scheduled "
                                                 "(delta-time between scheduling occasions).",
                           "nodeType": "RadioNode", "deprecatedSince": None, "networkFunction": "DU",
                           "sourceObject": ["NRCellDU"], "status": "AVAILABLE", "createdBy": "EBSN_04_0917-20265045_u0",
                           "createdDate":1600370820157, "basedOnEvent":["DuPerUeRbTrafficRep"],
                           "flexFilters":[{"eventName": None, "eventParam": None, "filterName": "Qos",
                                           "filterValue": "98", "status": None},
                                          {"eventName": None, "eventParam": None, "filterName": "QosType",
                                           "filterValue": "1", "status": None}]},
                          {"flexCounterName": "pmEbsRrcInactLevelSum_mcc128mnc49",
                           "baseCounterName": "pmEbsMacTimeDlDrb",
                           "counterDescription": "Description: Aggregated time for HARQ initial transmission "
                                                 "scheduling downlink of DRB since DRB was last scheduled "
                                                 "(delta-time between scheduling occasions).",
                           "nodeType": "RadioNode", "deprecatedSince": None, "networkFunction": "DU",
                           "sourceObject": ["NRCellDU", "GNBCUCPFunction"], "status": "AVAILABLE",
                           "createdBy": "EBSN_04_0917-20265045_u0",
                           "createdDate": 1600370820157, "basedOnEvent": ["DuPerUeRbTrafficRep"],
                           "flexFilters": [{"eventName": None, "eventParam": None, "filterName": "Qos",
                                            "filterValue": "98", "status": None},
                                           {"eventName": None, "eventParam": None, "filterName": "QosType",
                                            "filterValue": "1", "status": None}]}]

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.SLEEP_TIME = 60

    def tearDown(self):
        unit_test_utils.tear_down()

    # get_flex_counters test cases
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_get_flex_counters__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = self.flex_counters_json
        self.user.get.return_value = response
        get_flex_counters(self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_get_flex_counters__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 500
        response.raise_for_status.side_effect = HTTPError({"description": "Internal server error"})
        self.user.get.return_value = response
        self.assertRaises(HTTPError, get_flex_counters, self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    # import_flex_counters_in_enm test cases
    @patch('__builtin__.open', new_callable=mock_open)
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_import_flex_counters_in_enm__is_successful_for_ebsn_04(self, mock_debug_log, mock_open_file):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"JobId": "cd767a8e-f348-11ea-8b99-a153311852cd", "Total Flex Counters": "1",
                                      "Total Failed Flex Counters": '0'}
        self.user.post.return_value = response
        import_flex_counters_in_enm(self.user, 'EBSN_04')
        self.assertTrue(response.raise_for_status.called)
        self.assertTrue(mock_open_file.return_value.read.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('__builtin__.open', new_callable=mock_open)
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_import_flex_counters_in_enm__is_successful_for_ebsn_05(self, mock_debug_log, mock_open_file):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"JobId": "cd767a8e-f348-11ea-8b99-a153311852cd", "Total Flex Counters": "1",
                                      "Total Failed Flex Counters": '0'}
        self.user.post.return_value = response
        import_flex_counters_in_enm(self.user, 'EBSN_05')
        self.assertTrue(response.raise_for_status.called)
        self.assertTrue(mock_open_file.return_value.read.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('__builtin__.open', new_callable=mock_open)
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_import_flex_counters_in_enm__is_successful_for_other_than_ebsn_04_and_ebsn_05(self, mock_debug_log,
                                                                                           mock_open_file):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"JobId": "cd767a8e-f348-11ea-8b99-a153311852cd", "Total Flex Counters": "1",
                                      "Total Failed Flex Counters": '0'}
        self.user.post.return_value = response
        import_flex_counters_in_enm(self.user, 'EBSN_01')
        self.assertTrue(response.raise_for_status.called)
        self.assertTrue(mock_open_file.return_value.read.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('__builtin__.open', new_callable=mock_open)
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_import_flex_counters_in_enm__raises_http_error(self, mock_debug_log, mock_open_file):
        response = Mock()
        response.ok = False
        response.status_code = 500
        response.raise_for_status.side_effect = HTTPError({"description": "Internal server error"})
        self.user.post.return_value = response
        self.assertRaises(HTTPError, import_flex_counters_in_enm, self.user, 'EBSN_04')
        self.assertTrue(response.raise_for_status.called)
        self.assertTrue(mock_open_file.return_value.read.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('__builtin__.open', new_callable=mock_open)
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_import_flex_counters_in_enm__raises_enm_application_error(self, mock_debug_log, mock_open_file):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {}
        self.user.post.return_value = response
        self.assertRaises(EnmApplicationError, import_flex_counters_in_enm, self.user, 'EBSN_04')
        self.assertTrue(response.raise_for_status.called)
        self.assertTrue(mock_open_file.return_value.read.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    # delete_flex_counters test cases
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_delete_flex_counters__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"jobId": "fa284106-ec67-11ea-92fc-9d909cf6623a", "totalFlexCounters": 1}
        self.user.delete_request.return_value = response
        delete_flex_counters(self.user, ["pmEbsMacTimeDlDrb_Qos98_QosType1"])
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_delete_flex_counters__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 500
        response.raise_for_status.side_effect = HTTPError({"description": "Internal server error"})
        self.user.delete_request.return_value = response
        self.assertRaises(HTTPError, delete_flex_counters, self.user, ["pmEbsMacTimeDlDrb_Qos98_QosType1"])
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    # verify_creation_or_deletion_flex_counters_status test cases
    @patch('enmutils_int.lib.flexible_counter_management.time.sleep', return_value=0)
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    @patch('enmutils_int.lib.flexible_counter_management.get_flex_counters')
    def test_verify_creation_or_deletion_flex_counters_status__if_flex_counters_created(self, mock_get_flex_counters,
                                                                                        mock_debug_log, *_):
        mock_get_flex_counters.return_value = self.flex_counters_json
        verify_creation_or_deletion_flex_counters_status(self.user, self.SLEEP_TIME, "create", 2)
        self.assertTrue(mock_get_flex_counters.called)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch('enmutils_int.lib.flexible_counter_management.time.sleep', return_value=0)
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    @patch('enmutils_int.lib.flexible_counter_management.get_flex_counters')
    def test_verify_creation_or_deletion_flex_counters_status__if_flex_counters_not_created(self,
                                                                                            mock_get_flex_counters,
                                                                                            mock_debug_log, *_):
        mock_get_flex_counters.return_value = []
        self.assertRaises(EnvironError, verify_creation_or_deletion_flex_counters_status, self.user, self.SLEEP_TIME,
                          "create", 2)
        self.assertTrue(mock_get_flex_counters.called)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.flexible_counter_management.time.sleep', return_value=0)
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    @patch('enmutils_int.lib.flexible_counter_management.get_flex_counters')
    def test_verify_creation_or_deletion_flex_counters_status__if_flex_counters_deleted(self, mock_get_flex_counters,
                                                                                        mock_debug_log, *_):
        mock_get_flex_counters.return_value = []
        verify_creation_or_deletion_flex_counters_status(self.user, self.SLEEP_TIME, "delete", 2)
        self.assertTrue(mock_get_flex_counters.called)
        self.assertEqual(2, mock_debug_log.call_count)

    # get_ebs_flex_counters test cases
    @patch('enmutils_int.lib.flexible_counter_management.get_flex_counters')
    def test_get_ebs_flex_counters__is_successful(self, mock_get_flex_counters):
        mock_get_flex_counters.return_value = self.flex_counters_json
        self.assertEqual([{'moClassType': 'NRCellDU', 'name': 'pmEbsMacTimeDlDrb_Qos98_QosType1'},
                          {'moClassType': 'NRCellDU', 'name': 'pmEbsRrcInactLevelSum_mcc128mnc49'},
                          {'moClassType': 'GNBCUCPFunction', 'name': 'pmEbsRrcInactLevelSum_mcc128mnc49'}],
                         get_ebs_flex_counters(self.user))
        self.assertTrue(mock_get_flex_counters.called)

    @patch('enmutils_int.lib.flexible_counter_management.get_flex_counters')
    def test_get_ebs_flex_counters___if_counters_not_existed_enm(self, mock_get_flex_counters):
        mock_get_flex_counters.return_value = []
        self.assertRaises(EnvironError, get_ebs_flex_counters, self.user)
        self.assertTrue(mock_get_flex_counters.called)

    # get_reserved_ebsn_flex_counters test cases
    @patch('enmutils_int.lib.flexible_counter_management.filesystem.read_json_data_from_file')
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_get_reserved_ebsn_flex_counters__is_successful(self, mock_debug_log, mock_read_json_data_from_file):
        mock_read_json_data_from_file.return_value = self.flex_counters_json
        self.assertEqual(['pmEbsMacTimeDlDrb_Qos98_QosType1', 'pmEbsRrcInactLevelSum_mcc128mnc49'],
                         get_reserved_ebsn_flex_counters('EBSN_04'))
        mock_read_json_data_from_file.assert_called("/tmp/file.json", raise_error=False)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.flexible_counter_management.filesystem.read_json_data_from_file')
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    def test_get_reserved_ebsn_flex_counters__if_file_not_existed(self, mock_debug_log, mock_read_json_data_from_file):
        mock_read_json_data_from_file.return_value = []
        self.assertEqual([], get_reserved_ebsn_flex_counters('EBSN_04'))
        mock_read_json_data_from_file.assert_called("/tmp/file.json", raise_error=False)
        self.assertEqual(mock_debug_log.call_count, 1)

    # remove_any_existing_flexible_counters test cases
    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    @patch('enmutils_int.lib.flexible_counter_management.verify_creation_or_deletion_flex_counters_status')
    @patch('enmutils_int.lib.flexible_counter_management.delete_flex_counters')
    @patch('enmutils_int.lib.flexible_counter_management.get_flex_counters')
    def test_remove_any_existing_flexible_counters__if_old_ebs_flexible_counters_existed(
            self, mock_get_flex_counters, mock_delete_flex_counters,
            mock_verify_creation_or_deletion_flex_counters_status, mock_debug_log):
        mock_get_flex_counters.return_value = self.flex_counters_json
        flex_counters_names = [counter['flexCounterName'] for counter in self.flex_counters_json]
        remove_any_existing_flexible_counters(self.user, self.SLEEP_TIME)
        mock_get_flex_counters.assert_called_with(self.user)
        mock_delete_flex_counters.assert_called_with(self.user, flex_counters_names)
        mock_verify_creation_or_deletion_flex_counters_status.assert_called_with(self.user, self.SLEEP_TIME, "delete",
                                                                                 len(flex_counters_names))
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.flexible_counter_management.log.logger.debug')
    @patch('enmutils_int.lib.flexible_counter_management.verify_creation_or_deletion_flex_counters_status')
    @patch('enmutils_int.lib.flexible_counter_management.delete_flex_counters')
    @patch('enmutils_int.lib.flexible_counter_management.get_flex_counters')
    def test_remove_any_existing_flexible_counters__if_old_ebs_flexible_counters_not_existed(
            self, mock_get_flex_counters, mock_delete_flex_counters,
            mock_verify_creation_or_deletion_flex_counters_status, mock_debug_log):
        mock_get_flex_counters.return_value = []
        remove_any_existing_flexible_counters(self.user, self.SLEEP_TIME)
        mock_get_flex_counters.assert_called_with(self.user)
        self.assertFalse(mock_delete_flex_counters.called)
        self.assertFalse(mock_verify_creation_or_deletion_flex_counters_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
