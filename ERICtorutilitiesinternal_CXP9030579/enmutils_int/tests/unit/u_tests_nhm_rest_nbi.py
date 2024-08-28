#!/usr/bin/env python
import json
import unittest2
from mock import patch, Mock
from requests.exceptions import HTTPError
from enmutils_int.lib.nhm import wait_for_nhm_setup_profile
from enmutils_int.lib.nhm_rest_nbi import (CREATED_BY_DEFAULT, NhmRestNbiKpi)
from testslib import unit_test_utils


URL = 'http://localhost/'
KPI_INFO = {u'name': u'NHM REST NBI SETUP 1201 18490366 KPI 4', u'neFormulaList': {u'RadioNode': {u'reportingObjList': {u'ENodeBFunction': {u'formula': u'pmPagS1Discarded-pmPagS1Received'}}}},
            u'autoUpdateKpiScope': False, u'successNeNames': [u'LTE98dg2ERBS00002', u'LTE98dg2ERBS00001'],
            u'id': u'TkhNjYgS1BJIDQ', u'unit': u'No. of occurrences'}
KPI_INFO_TEST = {u'name': u'NHM REST NBI SETUP 1201 18490366 KPI 4', u'neFormulaList': {u'RadioNode': {u'reportingObjList': {u'ENodeBFunction': {u'formula': u'pmPagS1Discarded-pmPagS1Received'}}}},
                 u'autoUpdateKpiScope': False, u'successNeNames': [u'LTE98dg2ERBS00002', u'LTE98dg2ERBS00001'],
                 u'id': u'TkhNIFJFU1Q', u'unit': u'No. of occurrences'}
KPI_BODY = {'neNames': ['LTE98dg2ERBS00001', 'LTE98dg2ERBS00002'], 'neFormulaList': {'RadioNode': {'reportingObjList': {'ENodeBFunction': {'formula': {u'formula': u'pmPagS1Received-pmPagS1Discarded-pmLicConnectedUsersMax'}}}}},
            'name': 'unit_test_kpi', 'unit': 'No. of occurrences'}
PATTERN = 'NHM REST NBI SETUP'


class NhmRestNbiKpiUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser")
        self.mock_user = Mock()
        self.mock_response = Mock()
        self.NODE_IP_1 = unit_test_utils.generate_configurable_ip()
        self.NODE_IP_2 = unit_test_utils.generate_configurable_ip()
        self.nodes = [
            Mock(node_id='LTE98dg2ERBS00001', node_ip=self.NODE_IP_1, mim_version='F.1.101',
                 model_identity='5783-904-386', primary_type='RadioNode'),
            Mock(node_id='LTE98dg2ERBS00002', node_ip=self.NODE_IP_2, mim_version='F.1.101',
                 model_identity='5783-904-386', primary_type='RadioNode')
        ]
        self.kpi = NhmRestNbiKpi(user=self.user, kpi_id="unit_test_kpi_id", kpi_name="unit_test_kpi", nodes=self.nodes,
                                 created_by=self.user.username)
        self.kpi_id = 'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BJIDQ'
        self.counters = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr', 'pmLicConnectedUsersLicense',
                         'pmRrcConnBrEnbMax', 'pmMoFootprintMax', 'pmLicConnectedUsersMax', 'pmPagS1EdrxReceived']
        self.operators = ['+', '-', '*', '/']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi._create_kpi_equation")
    def test_create_node_level_body_success(self, mock_kpi_equation):
        self.kpi.name = "NHM_01_1017-16230557_KPI_3"
        self.kpi.counters = ['pmPagS1Received', 'pmRrcConnBrEnbMax', 'pmRimReportErr', 'pmMoFootprintMax']
        self.kpi.node_types = ['RadioNode']
        mock_kpi_equation.return_value = {u'formula': u'pmPagS1Received-pmPagS1Discarded-pmLicConnectedUsersMax'}
        self.kpi._create_node_level_body()
        self.assertEqual(self.kpi._create_node_level_body(), KPI_BODY)

    @patch('enmutils_int.lib.nhm_rest_nbi.log.logger.debug')
    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi._create_node_level_body")
    def test_kpi_create_success_node_success(self, mock_create_node_level_body, mock_logger_debug):
        response = Mock()
        self.user.post.return_value = response
        response.status_code = 200
        self.kpi.created_by = self.user.username
        mock_create_node_level_body.return_value = KPI_BODY
        response.json.return_value = {'id': 'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BJIDQ'}
        self.kpi.create()
        self.assertTrue(mock_create_node_level_body.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('time.sleep')
    @patch('enmutils_int.lib.nhm_rest_nbi.log.logger.debug')
    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi._create_node_level_body")
    def test_kpi_raise_http_error(self, mock_create_node_level_body, *_):
        response = Mock()
        response.raise_for_status.side_effect = [HTTPError, HTTPError, HTTPError, HTTPError]
        response.status_code = 405
        self.user.post.side_effect = [response, response, response, response]
        self.kpi.created_by = self.user.username
        mock_create_node_level_body.return_value = KPI_BODY
        self.assertRaises(HTTPError, self.kpi.create)

    def test_kpi_activate_success_for_else(self):
        response = Mock()
        response.status_code = 200
        self.user.put.return_value = response
        try:
            self.kpi.activate()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_kpi_activate_success_for_if(self):
        self.user.username = "NHM_13_0821-08385549_u0"
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        try:
            self.kpi.activate()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch("time.sleep")
    def test_kpi_activate_raises_http_error(self, *_):
        response = Mock()
        self.user.put.return_value = response
        try:
            self.kpi.activate()
        except Exception as e:
            raise HTTPError("Raised Http error: {}".format(str(e)))

    def test_kpi_deactivate_success(self):
        response = Mock(status_code=200)
        self.user.put.return_value = response
        try:
            self.kpi.deactivate()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch("time.sleep")
    def test_kpi_deactivate_raises_http_error(self, *_):
        response = Mock()
        self.user.put.return_value = response
        response.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, self.kpi.deactivate)

    def test_delete_kpi_success(self):
        response = Mock()
        response.status_code = 200
        self.user.delete_request.return_value = response
        self.kpi.created_by = self.user.username
        try:
            self.kpi.delete()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_delete_kpi_failure(self):
        self.kpi.created_by = CREATED_BY_DEFAULT
        try:
            self.kpi.delete()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_delete_kpi_exception(self):
        response = Mock()
        self.user.delete_request.return_value = response
        self.kpi.delete()
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.nhm.time.sleep")
    def test_delete_raises_http_error(self, *_):
        response = Mock()
        response.status_code = 305
        self.user.delete_request.return_value = response
        response.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, self.kpi.delete)

    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.delete")
    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.deactivate")
    def test_remove_kpis_by_pattern_success(self, mock_deactivate, mock_delete):
        response = Mock()
        user = Mock()
        response.status_code = 200
        response.json.return_value = {'items': [{u'name': u'NHM REST NBI SETUP 1201 18490366 KPI 4',
                                                 u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BJIDQ'},
                                                {u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BAIDQ',
                                                 u'name': u'NHM REST NBI SETUP 1201 18490366 KPI 3'}]}
        user.get.return_value = response
        NhmRestNbiKpi.remove_kpis_by_pattern(user=user)
        self.assertTrue(mock_deactivate.called)
        self.assertTrue(mock_delete.called)

    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.delete")
    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.deactivate")
    def test_remove_kpis_nhm_rest_nbi_05_by_pattern_success(self, mock_deactivate, mock_delete):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'items': [{u'name': u'NHM REST NBI 05 1201 18490366 KPI 4',
                                                 u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BJIDQ'},
                                                {u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BAIDQ',
                                                 u'name': u'NHM REST NBI 05 1201 18490366 KPI 3'}]}
        self.user.get.return_value = response
        NhmRestNbiKpi.remove_kpis_nhm_rest_nbi_05_by_pattern(user=self.user)
        self.assertTrue(mock_deactivate.called)
        self.assertTrue(mock_delete.called)

    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.delete")
    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.deactivate")
    def test_remove_kpis_nhm_rest_nbi_05_by_pattern_deactivate_exception(self, mock_delete, mock_deactivate):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'items': [{u'name': u'NHM REST NBI 05 1201 18490366 KPI 4',
                                                 u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BJIDQ'},
                                                {u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BAIDQ',
                                                 u'name': u'NHM REST NBI 05 1201 18490366 KPI 3'}]}
        self.user.get.return_value = response
        mock_deactivate.side_effect = Exception
        self.kpi.remove_kpis_nhm_rest_nbi_05_by_pattern(user=self.user)
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_deactivate.called)

    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.delete")
    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.deactivate")
    def test_remove_kpis_nhm_rest_nbi_05_by_pattern_new_delete_exception(self, mock_delete, mock_deactivate):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'items': [{u'name': u'NHM REST NBI 05 1201 18490366 KPI 4',
                                                 u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BJIDQ'},
                                                {u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BAIDQ',
                                                 u'name': u'NHM REST NBI 05 1201 18490366 KPI 3'}]}
        self.user.get.return_value = response
        mock_delete.side_effect = Exception
        self.kpi.remove_kpis_nhm_rest_nbi_05_by_pattern(user=self.user)
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_deactivate.called)

    def test_remove_kpis_nhm_rest_nbi_05_by_pattern_http_error(self):
        response = Mock()
        response.status_code = 305
        self.user.get.return_value = response
        response.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, self.kpi.remove_kpis_nhm_rest_nbi_05_by_pattern, user=self.user)

    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.delete")
    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.deactivate")
    def test_remove_kpis_by_pattern_deactivate_exception(self, mock_delete, mock_deactivate):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'items': [{u'name': u'NHM REST NBI SETUP 1201 18490366 KPI 4',
                                                 u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BJIDQ'},
                                                {u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BAIDQ',
                                                 u'name': u'NHM REST NBI SETUP 1201 18490366 KPI 3'}]}
        self.user.get.return_value = response
        mock_deactivate.side_effect = Exception
        self.kpi.remove_kpis_by_pattern(user=self.user)
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_deactivate.called)

    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.delete")
    @patch("enmutils_int.lib.nhm_rest_nbi.NhmRestNbiKpi.deactivate")
    def test_remove_kpis_by_pattern_new_delete_exception(self, mock_delete, mock_deactivate):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'items': [{u'name': u'NHM REST NBI SETUP 1201 18490366 KPI 4',
                                                 u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BJIDQ'},
                                                {u'id': u'TkhNIFJFU1QgTkJJIFNFVFVQIDEyMDEgMTg0OTAzNjYgS1BAIDQ',
                                                 u'name': u'NHM REST NBI SETUP 1201 18490366 KPI 3'}]}
        self.user.get.return_value = response
        mock_delete.side_effect = Exception
        self.kpi.remove_kpis_by_pattern(user=self.user)
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_deactivate.called)

    def test_remove_kpis_by_pattern_http_error(self):
        response = Mock()
        response.status_code = 305
        self.user.get.return_value = response
        response.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, self.kpi.remove_kpis_by_pattern, user=self.user)

    def test_create_kpi_equation_logic(self):
        self.kpi.counters = ["pmHwUtilDl", "pmHwUtilUl", "pmLic5MHzSectorCarrierActual", "pmLic5Plus5MHzScFddActual"]
        try:
            kpi_equation = self.kpi._create_kpi_equation()
            json.dumps(kpi_equation)
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_create_kpi_equation_division(self):
        self.kpi.counters = ["pmHwUtilDl", "pmHwUtilUl", "pmLic5MHzSectorCarrierActual", "pmLic5Plus5MHzScFddActual"]
        self.kpi.operators = ['/']
        try:
            kpi_equation = self.kpi._create_kpi_equation()
            json.dumps(kpi_equation)
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_create_kpi_equation_division__counter_greater_than_2(self):
        self.kpi.counters = ["pmHwUtilDl", "pmHwUtilUl", "pmLic5MHzSectorCarrierActual", "pmLic5Plus5MHzScFddActual",
                             "pmHwUtilDl", "pmHwUtilUl"]
        self.kpi.operators = ['/']
        try:
            kpi_equation = self.kpi._create_kpi_equation()
            json.dumps(kpi_equation)
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch("random.sample")
    def test_create_kpi_equation__not_division(self, mock_sample):
        self.kpi.counters = ["pmHwUtilDl", "pmHwUtilUl", "pmLic5MHzSectorCarrierActual", "pmLic5Plus5MHzScFddActual"]
        self.kpi.operators = ['*']
        self.kpi._create_kpi_equation()
        self.assertFalse(mock_sample.called)

    def test_activation_status__success(self):
        response = Mock()
        user = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = [{u'active': True, u'id': u'TkhNX1NFVFVQXzEwMDUtMTEyNzUzNDRfS1BJXzkw',
                                       u'name': u'NHM_SETUP_1005-11275344_KPI_90'}]
        user.get.return_value = response
        self.kpi.activation_status(user, ['kpi1', 'kpi2'])

    @patch('enmutils_int.lib.nhm_rest_nbi.log.logger.debug')
    def test_activation_status__failure(self, mock_logger_debug):
        response = Mock()
        user = Mock()
        response.ok = False
        response.status_code = 500
        user.get.return_value = response
        self.kpi.activation_status(user, ['kpi1'])
        self.assertTrue(mock_logger_debug.called)


class NhmUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.nhm_rest_nbi.log.logger')
    @patch('time.sleep')
    @patch('enmutils_int.lib.nhm.sleep_until_profile_persisted')
    @patch('enmutils_int.lib.nhm.persistence')
    def test_wait_for_nhm_rest_nbi_setup_profile_if_not_persistence(self, mock_persistence, *_):
        mock_persistence.has_key.side_effect = [False, True]
        mock_profile_with_flag = Mock()
        mock_profile_with_flag.FLAG = "COMPLETED"
        mock_persistence.get.side_effect = [mock_profile_with_flag, mock_profile_with_flag]
        wait_for_nhm_setup_profile()

    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm_rest_nbi.log.logger')
    @patch('enmutils_int.lib.nhm.sleep_until_profile_persisted')
    @patch('enmutils_int.lib.nhm.persistence')
    def test_wait_for_nhm_setup_profile__sleep_until_profile_persisted(self, mock_persistence, mock_profile_persisted,
                                                                       *_):
        mock_persistence.has_key.side_effect = [False, True]
        mock_profile_with_flag = Mock(FLAG="COMPLETED")
        mock_profile_with_out_flag = Mock(FLAG="RUNNING")
        mock_persistence.get.side_effect = [mock_profile_with_out_flag] * 18 + [False] + [mock_profile_with_flag]
        wait_for_nhm_setup_profile()
        self.assertTrue(mock_profile_persisted.called)

    @patch('enmutils_int.lib.nhm_rest_nbi.log.logger')
    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.persistence')
    def test_wait_for_nhm_setup_profile_start_with_flag_completed(self, mock_persistence, *_):
        mock_profile_with_flag = Mock()
        mock_profile_with_flag.FLAG = "COMPLETED"
        mock_persistence.get.side_effect = [mock_profile_with_flag, mock_profile_with_flag]
        wait_for_nhm_setup_profile()

    @patch('enmutils_int.lib.nhm_rest_nbi.log.logger')
    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.persistence')
    def test_wait_for_nhm_setup_profile_starts_and_wait_for_the_flag(self, mock_persistence, *_):
        mock_profile_with_flag = Mock()
        mock_profile_with_flag.FLAG = "COMPLETED"
        side_effects = [Mock() for _ in range(17)]
        side_effects.append(mock_profile_with_flag)
        mock_persistence.get.side_effect = side_effects
        wait_for_nhm_setup_profile()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
