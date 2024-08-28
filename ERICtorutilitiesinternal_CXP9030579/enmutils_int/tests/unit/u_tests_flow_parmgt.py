#!/usr/bin/env python

from datetime import datetime
from mock import patch, Mock
from requests import HTTPError, ConnectionError
import unittest2

from enmutils_int.lib.load_node import ERBSLoadNode
from enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow import ParMgt01Flow
from testslib import unit_test_utils


class ParMgt01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.user.username = "User_u0"
        self.flow = ParMgt01Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]
        self.flow.DAILY_SLEEP = 0
        self.flow.SCHEDULED_TIMES_STRINGS = ["06:00:00"]
        self.flow.NUMBER_OF_ITERATIONS = 1
        self.flow.TIME_IN_MINUTES_BETWEEN_ITERATIONS = 1
        self.nodes_list = [ERBSLoadNode(id='LTE01', node_id='LTE01', simulation='LTE-120', model_identity='1-2-34')]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    def test_process_po_data_returns_expected_result(self, mock_get_pos_by_poids,
                                                     mock_temporary_query_for_mo_class_mapping,
                                                     mock_chunks):
        mock_chunks.return_value = self.nodes_list
        users = [self.user]
        mock_temporary_query_for_mo_class_mapping.return_value = {
            'moDetails': [{'moTypes': {'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
        mock_get_pos_by_poids.return_value.json.return_value = \
            [{'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
              'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
              'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
              'poId': '281475024838824', 'id': '281475024838824',
              'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}]
        expected_result = {"4g": {self.user: [({'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
                                                'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
                                                'attributes': {'combCellSectorSelectThreshTx': 300,
                                                               'combCellSectorSelectThreshRx': 300},
                                                'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
                                                'poId': '281475024838824', 'id': '281475024838824'}, "4g")]}}
        self.assertEqual(self.flow.process_po_data(users=users, synced=self.nodes_list), expected_result)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    def test_process_po_data_returns_blank_list_when_po_ids_not_present(self, mock_get_pos_by_poids,
                                                                        mock_temporary_query_for_mo_class_mapping, _):
        users = [self.user]
        mock_temporary_query_for_mo_class_mapping.return_value = {}
        mock_get_pos_by_poids.return_value.json.return_value = \
            [{'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
              'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
              'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
              'poId': '281475024838824', 'id': '281475024838824',
              'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}]
        self.assertEqual(self.flow.process_po_data(users=users, synced=self.nodes_list), {})

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    def test_process_po_data_returns_blank_dict_when_get_pos_by_poids_raises_http_error(self, mock_get_pos_by_poids,
                                                                                        mock_temporary_query_for_mo_class_mapping,
                                                                                        _):
        users = [self.user]
        mock_temporary_query_for_mo_class_mapping.return_value = {
            'moDetails': [{'moTypes': {'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
        mock_get_pos_by_poids.side_effect = HTTPError
        self.assertEqual(self.flow.process_po_data(users=users, synced=self.nodes_list), {})

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    def test_process_po_data_returns_blank_list_when_get_pos_by_poids_raises_exception(self, mock_get_pos_by_poids,
                                                                                       mock_temporary_query_for_mo_class_mapping,
                                                                                       _):
        users = [self.user]
        mock_temporary_query_for_mo_class_mapping.return_value = {
            'moDetails': [{'moTypes': {'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
        mock_get_pos_by_poids.side_effect = Exception
        self.assertEqual(self.flow.process_po_data(users=users, synced=self.nodes_list), {})

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    def test_get_po_ids_for_selected_nodes_returns_expected_po_ids(self, mock_temporary_query_for_mo_class_mapping):
        mock_temporary_query_for_mo_class_mapping.return_value = {
            'moDetails': [{'moTypes': {'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}},
                          {'moTypes': {'ENodeBFunction': [{'poId': '281475024838825', 'nodeName': 'LTE02'}]}}]}
        expected_result = ["281475024838824"]
        self.assertEqual(self.flow.get_po_ids_for_selected_nodes(self.user, "query", ["LTE01"], '4g'), expected_result)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    def test_get_po_ids_for_selected_nodes_raises_http_error(self, mock_temporary_query_for_mo_class_mapping,
                                                             mock_add_error_as_exception):
        mock_temporary_query_for_mo_class_mapping.side_effect = HTTPError
        self.flow.get_po_ids_for_selected_nodes(self.user, "query", ["LTE01"], '4g')
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    def test_get_po_ids_for_selected_nodes_raises_exception(self, mock_temporary_query_for_mo_class_mapping,
                                                            mock_add_error_as_exception):
        mock_temporary_query_for_mo_class_mapping.side_effect = Exception
        self.flow.get_po_ids_for_selected_nodes(self.user, "query", ["LTE01"], '4g')
        self.assertTrue(mock_add_error_as_exception.called)

    def test_get_user_node_data_returns_user_node_data(self):
        po_list = \
            [{'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
              'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
              'attributes': {'combCellSectorSelectThreshTx': 300,
                             'combCellSectorSelectThreshRx': 300},
              'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
              'poId': '281475024838824', 'id': '281475024838824'}]
        expected_result = {self.user: [({'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
                                         'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
                                         'attributes': {'combCellSectorSelectThreshTx': 300,
                                                        'combCellSectorSelectThreshRx': 300},
                                         'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
                                         'poId': '281475024838824', 'id': '281475024838824'}, "4g")]}
        self.assertEqual(self.flow.get_user_node_data([self.user], po_list, "4g"), expected_result)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_task_set_is_successful(self, mock_update_attributes, mock_add_error_as_exception, _):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]

        self.flow.task_set(user_node_data[0], self.flow)
        self.assertTrue(mock_update_attributes.called)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_task_set_raises_http_error_as_enm_applcation_error(self, mock_update_attributes,
                                                                mock_add_error_as_exception, _):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = HTTPError
        self.flow.task_set(user_node_data[0], self.flow)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_task_set_raises_http_error_as_environ_error(self, mock_update_attributes, mock_add_error_as_exception, _):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = HTTPError
        self.flow.task_set(user_node_data[0], self.flow)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_task_set_raises_connection_error(self, mock_update_attributes, mock_add_error_as_exception, _):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = ConnectionError

        self.flow.task_set(user_node_data[0], self.flow)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_task_set_raises_key_error(self, mock_update_attributes, mock_add_error_as_exception, _):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = KeyError

        self.flow.task_set(user_node_data[0], self.flow)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_task_set_raises_exception(self, mock_update_attributes, mock_add_error_as_exception, _):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = Exception

        self.flow.task_set(user_node_data[0], self.flow)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_reset_attributes_is_successful(self, mock_update_attributes, mock_add_error_as_exception):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]

        self.flow.reset_attributes(self.user, user_node_data)
        self.assertTrue(mock_update_attributes.called)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_reset_attributes_raises_http_error_as_enm_application_error(self, mock_update_attributes,
                                                                         mock_add_error_as_exception):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = HTTPError

        self.flow.reset_attributes(self.user, user_node_data)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_reset_attributes_raises_http_error_as_environ_error(self, mock_update_attributes,
                                                                 mock_add_error_as_exception):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = HTTPError

        self.flow.reset_attributes(self.user, user_node_data)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_reset_attributes_raises_connection_error(self, mock_update_attributes, mock_add_error_as_exception):
        user_node_data = [(self.user, [
            ({'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
              'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
              'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
              'poId': '281475024838824', 'id': '281475024838824',
              'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = ConnectionError
        self.flow.reset_attributes(self.user, user_node_data)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_reset_attributes_raises_key_error(self, mock_update_attributes, mock_add_error_as_exception):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = KeyError

        self.flow.reset_attributes(self.user, user_node_data)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.update_attributes')
    def test_reset_attributes_raises_exception(self, mock_update_attributes, mock_add_error_as_exception):
        user_node_data = [(self.user, [(
            {'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
             'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
             'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
             'poId': '281475024838824', 'id': '281475024838824',
             'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}, "4g")])]
        mock_update_attributes.side_effect = Exception

        self.flow.reset_attributes(self.user, user_node_data)
        self.assertTrue(mock_update_attributes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.set_schedule_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_profile_users')
    def test_execute_flow_is_successful(self, mock_create_profile_users, mock_get_pos_by_poids,
                                        mock_temporary_query_for_mo_class_mapping, mock_check_sync_and_remove,
                                        mock_keep_running, *_):
        with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                   'create_and_execute_threads') as mock_create_and_execute_threads:
            with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.datetime') as mock_datetime:
                with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks') as mock_chunks:
                    with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                               'remove_partial_items_from_teardown_list') as \
                            mock_remove_partial_items_from_teardown_list:
                        mock_chunks.return_value = self.nodes_list
                        mock_create_profile_users.return_value = [self.user]
                        mock_check_sync_and_remove.return_value = (self.nodes_list, [])
                        mock_temporary_query_for_mo_class_mapping.return_value = {
                            'moDetails': [
                                {'moTypes': {'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
                        mock_get_pos_by_poids.return_value.json.return_value = \
                            [{'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
                              'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
                              'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
                              'poId': '281475024838824', 'id': '281475024838824',
                              'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}]
                        mock_keep_running.side_effect = [True, True, False]
                        self.flow.teardown_list = [self.user]
                        mock_datetime.now.return_value.__rsub__.return_value.total_seconds.return_value = 100
                        self.flow.execute_flow()
                        self.assertTrue(mock_create_and_execute_threads.called)
                        self.assertTrue(mock_remove_partial_items_from_teardown_list.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
           'remove_partial_items_from_teardown_list')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.set_schedule_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_profile_users')
    def test_execute_flow_raises_exception__when_check_sync_is_not_successful(self,
                                                                              mock_create_profile_users,
                                                                              mock_get_pos_by_poids,
                                                                              mock_temporary_query_for_mo_class_mapping,
                                                                              mock_check_sync_and_remove,
                                                                              mock_keep_running, *_):
        with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.'
                   'ParMgt01Flow.add_error_as_exception') as mock_add_error_as_exception:
            with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                       'create_and_execute_threads') as mock_create_and_execute_threads:
                with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.datetime') as mock_datetime:
                    with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks') as mock_chunks:
                        mock_chunks.return_value = self.nodes_list
                        mock_create_profile_users.return_value = [self.user]
                        mock_check_sync_and_remove.side_effect = (Exception, [])
                        mock_temporary_query_for_mo_class_mapping.return_value = {
                            'moDetails': [
                                {'moTypes': {
                                    'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
                        mock_get_pos_by_poids.return_value.json.return_value = \
                            [{'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
                              'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
                              'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
                              'poId': '281475024838824', 'id': '281475024838824',
                              'attributes': {'combCellSectorSelectThreshTx': 300,
                                             'combCellSectorSelectThreshRx': 300}}]
                        mock_keep_running.side_effect = [True, True, False]
                        self.flow.teardown_list = [self.user]
                        mock_datetime.now.return_value.__rsub__.return_value.total_seconds.return_value = 100
                        self.flow.execute_flow()
                        self.assertFalse(mock_create_and_execute_threads.called)
                        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
           'remove_partial_items_from_teardown_list')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.set_schedule_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.exchange_nodes_and_check_sync')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_profile_users')
    def test_execute_flow_raises_exception__when_exchange_is_not_successful(self,
                                                                            mock_create_profile_users,
                                                                            mock_get_pos_by_poids,
                                                                            mock_temporary_query_for_mo_class_mapping,
                                                                            mock_exchange_nodes_and_check_sync,
                                                                            mock_keep_running, *_):
        with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.'
                   'ParMgt01Flow.add_error_as_exception') as mock_add_error_as_exception:
            with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                       'create_and_execute_threads') as mock_create_and_execute_threads:
                with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.datetime') as mock_datetime:
                    with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks') as mock_chunks:
                        mock_chunks.return_value = self.nodes_list
                        mock_create_profile_users.return_value = [self.user]
                        mock_exchange_nodes_and_check_sync.side_effect = Exception
                        mock_temporary_query_for_mo_class_mapping.return_value = {
                            'moDetails': [
                                {'moTypes': {
                                    'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
                        mock_get_pos_by_poids.return_value.json.return_value = \
                            [{'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
                              'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
                              'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
                              'poId': '281475024838824', 'id': '281475024838824',
                              'attributes': {'combCellSectorSelectThreshTx': 300,
                                             'combCellSectorSelectThreshRx': 300}}]
                        mock_keep_running.side_effect = [True, True, False]
                        self.flow.teardown_list = [self.user]
                        mock_datetime.now.return_value.__rsub__.return_value.total_seconds.return_value = 100
                        self.flow.execute_flow()
                        self.assertFalse(mock_create_and_execute_threads.called)
                        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch(
        'enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_and_execute_threads')
    @patch(
        'enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.remove_partial_items_from_teardown_list')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.partial')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.process_po_data',
           return_value=[Mock(), [Mock()]])
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.set_schedule_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_profile_users')
    def test_execute_flow_is_successful_when_no_synced_nodes_and_exchanges_nodes_first_iteration_next_day(
            self, mock_create_profile_users, mock_get_pos_by_poids, mock_temporary_query_for_mo_class_mapping,
            mock_check_sync_and_remove, mock_keep_running, *_):
        with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                   'exchange_nodes') as mock_exchange_nodes:
            with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.datetime') as mock_datetime:
                with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks') as mock_chunks:
                    mock_chunks.return_value = self.nodes_list
                    mock_create_profile_users.return_value = [self.user]
                    mock_check_sync_and_remove.return_value = ([], [])
                    mock_temporary_query_for_mo_class_mapping.return_value = {
                        'moDetails': [
                            {'moTypes': {'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
                    mock_get_pos_by_poids.return_value.json.return_value = \
                        [{'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
                          'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
                          'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
                          'poId': '281475024838824', 'id': '281475024838824',
                          'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}]
                    mock_keep_running.side_effect = [True, True, False]
                    self.flow.teardown_list = [self.user]
                    mock_datetime.now.return_value.__rsub__.return_value.total_seconds.return_value = 10
                    self.flow.execute_flow()
                    self.assertTrue(mock_exchange_nodes.called)
                    self.assertTrue(mock_check_sync_and_remove.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch(
        'enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_and_execute_threads')
    @patch(
        'enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.remove_partial_items_from_teardown_list')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.partial')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.process_po_data',
           return_value={"4g": {Mock(): [({}, "4g")]}})
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.set_schedule_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_profile_users')
    def test_execute_flow_is_successful_when_synced_nodes_and_exchanges_nodes_first_iteration_next_day(
            self, mock_create_profile_users, mock_get_pos_by_poids, mock_temporary_query_for_mo_class_mapping,
            mock_check_sync_and_remove, mock_keep_running, *_):
        with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                   'exchange_nodes') as mock_exchange_nodes:
            with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.datetime') as mock_datetime:
                with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks') as mock_chunks:
                    mock_chunks.return_value = self.nodes_list
                    mock_create_profile_users.return_value = [self.user]
                    mock_check_sync_and_remove.return_value = (self.nodes_list, [])
                    mock_temporary_query_for_mo_class_mapping.return_value = {
                        'moDetails': [
                            {'moTypes': {'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
                    mock_get_pos_by_poids.return_value.json.return_value = \
                        [{'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
                          'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
                          'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
                          'poId': '281475024838824', 'id': '281475024838824',
                          'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}]
                    mock_keep_running.side_effect = [True, True, False]
                    self.flow.teardown_list = [self.user]
                    mock_datetime.now.return_value.__rsub__.return_value.total_seconds.return_value = 10
                    self.flow.execute_flow()
                    self.assertFalse(mock_exchange_nodes.called)
                    self.assertTrue(mock_check_sync_and_remove.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.set_schedule_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_profile_users')
    def test_execute_flow_raises_environ_error(self, mock_create_profile_users, mock_get_pos_by_poids,
                                               mock_check_sync_and_remove, mock_keep_running,
                                               mock_add_error_as_exception, *_):
        with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                   'create_and_execute_threads') as mock_create_and_execute_threads:
            with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks') as mock_chunks:
                mock_chunks.return_value = self.nodes_list
                mock_create_profile_users.return_value = [self.user]
                mock_check_sync_and_remove.return_value = ([], [])
                mock_keep_running.side_effect = [True, False]
                mock_get_pos_by_poids.return_value.json.return_value = \
                    [{'mibRootName': 'LTE01', 'moName': '1', 'parentRDN': 'ManagedElement=1',
                      'fullMoType': 'ENodeBFunction', 'moType': 'ENodeBFunction',
                      'fdn': 'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1',
                      'poId': '281475024838824', 'id': '281475024838824',
                      'attributes': {'combCellSectorSelectThreshTx': 300, 'combCellSectorSelectThreshRx': 300}}]

                self.flow.execute_flow()
                self.assertFalse(mock_create_and_execute_threads.called)
                self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.set_schedule_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_profile_users')
    def test_execute_flow_raises_http_error_from_get_po_ids_for_selected_nodes(self, mock_create_profile_users,
                                                                               mock_temporary_query_for_mo_class_mapping,
                                                                               mock_check_sync_and_remove,
                                                                               mock_keep_running,
                                                                               mock_add_error_as_exception, *_):
        with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                   'create_and_execute_threads') as mock_create_and_execute_threads:
            with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks') as mock_chunks:
                mock_chunks.return_value = self.nodes_list
                mock_create_profile_users.return_value = [self.user]
                mock_check_sync_and_remove.return_value = (self.nodes_list, [])
                mock_temporary_query_for_mo_class_mapping.side_effect = HTTPError
                mock_keep_running.side_effect = [True, False]

                self.flow.execute_flow()
                self.assertFalse(mock_create_and_execute_threads.called)
                self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.set_schedule_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_profile_users')
    def test_execute_flow_raises_http_error_from_get_pos_by_poids(self, mock_create_profile_users,
                                                                  mock_get_pos_by_poids,
                                                                  mock_temporary_query_for_mo_class_mapping,
                                                                  mock_check_sync_and_remove,
                                                                  mock_keep_running, *_):
        with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                   'add_error_as_exception') as mock_add_error_as_exception:
            with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                       'create_and_execute_threads') as mock_create_and_execute_threads:
                with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks') as mock_chunks:
                    mock_chunks.return_value = self.nodes_list
                    mock_create_profile_users.return_value = [self.user]
                    mock_check_sync_and_remove.return_value = (self.nodes_list, [])
                    mock_temporary_query_for_mo_class_mapping.return_value = {
                        'moDetails': [
                            {'moTypes': {'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
                    mock_get_pos_by_poids.side_effect = HTTPError
                    mock_keep_running.side_effect = [True, False]

                    self.flow.execute_flow()
                    self.assertFalse(mock_create_and_execute_threads.called)
                    self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.set_schedule_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.check_sync_and_remove')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.temporary_query_for_mo_class_mapping')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.get_pos_by_poids')
    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.create_profile_users')
    def test_execute_flow_raises_exception_from_get_pos_by_poids(self, mock_create_profile_users, mock_get_pos_by_poids,
                                                                 mock_temporary_query_for_mo_class_mapping,
                                                                 mock_check_sync_and_remove,
                                                                 mock_keep_running, *_):
        with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                   'add_error_as_exception') as mock_add_error_as_exception:
            with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.'
                       'create_and_execute_threads') as mock_create_and_execute_threads:
                with patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.chunks') as mock_chunks:
                    mock_chunks.return_value = self.nodes_list
                    mock_create_profile_users.return_value = [self.user]
                    mock_check_sync_and_remove.return_value = (self.nodes_list, [])
                    mock_temporary_query_for_mo_class_mapping.return_value = {
                        'moDetails': [
                            {'moTypes': {'ENodeBFunction': [{'poId': '281475024838824', 'nodeName': 'LTE01'}]}}]}
                    mock_get_pos_by_poids.side_effect = Exception
                    mock_keep_running.side_effect = [True, False]

                    self.flow.execute_flow()
                    self.assertFalse(mock_create_and_execute_threads.called)
                    self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.datetime')
    def test_set_schedule_time_is_successful(self, mock_datetime):
        mock_datetime.strptime.return_value = datetime(2019, 1, 1, 6, 0, 0, 0)
        mock_datetime.now.return_value.year = 2019
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.day = 1
        self.flow.NUMBER_OF_ITERATIONS = 3
        self.flow.TIME_IN_MINUTES_BETWEEN_ITERATIONS = 15
        self.flow.set_schedule_time()
        self.assertEqual(self.flow.SCHEDULED_TIMES, [datetime(2019, 1, 1, 6, 0, 0, 0),
                                                     datetime(2019, 1, 1, 6, 15, 0, 0),
                                                     datetime(2019, 1, 1, 6, 30, 0, 0)])

    def test_get_expected_po_data_with_more_po_data(self):
        po_id_dict = {
            'cran': [1, 2, 3, 4, 5, 66] * 100,
            '5g': [11, 22, 33, 44, 55, 66] * 100,
            '4g': [1, 2, 2] * 100
        }
        self.flow.get_expected_po_data(po_id_dict)

    def test_get_expected_po_data_with_less_podata(self):
        po_id_dict = {
            'cran': [1, 2, 3, 5] * 100,
            '5g': [11, 22, 33, 44] * 100,
            '4g': [1, 2] * 100
        }
        self.flow.get_expected_po_data(po_id_dict)

    def test_get_expected_po_data_with_more_data_remaining(self):
        po_id_dict = {
            'cran': [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14] * 100,
            '5g': [1] * 100,
            '4g': [1] * 100
        }
        self.flow.get_expected_po_data(po_id_dict)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
