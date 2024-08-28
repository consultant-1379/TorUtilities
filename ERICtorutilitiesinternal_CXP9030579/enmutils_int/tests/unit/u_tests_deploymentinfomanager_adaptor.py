#!/usr/bin/env python

import base64

import unittest2
from mock import patch, Mock

from enmutils_int.lib.services.deploymentinfomanager_adaptor import (POST_METHOD, READ_PIB_URL, SERVICE_NAME,
                                                                     send_request_to_service, can_service_be_used,
                                                                     read_pib_value, update_pib_value, get_apache_url,
                                                                     get_deployment_service_info, GET_METHOD,
                                                                     APACHE_URL, SERVICE_INFO_URL, UPDATE_PIB_URL,
                                                                     COPY_EMP_KEY_URL, copy_cloud_user_key_to_emp,
                                                                     get_pib_value_on_enm, update_pib_parameter_on_enm,
                                                                     poid_refresh, POID_REFRESH, LMS_PASS_URL,
                                                                     lms_password_less_access, check_deployment_config,
                                                                     get_eniq_ip_list_check_if_eniq_server,
                                                                     ENIQ_URL, check_enm_access,
                                                                     check_password_ageing_policy_status,
                                                                     get_list_of_scripting_service_ips)
from testslib import unit_test_utils


class DeploymentManagerAdaptorUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.can_service_be_used',
           return_value=True)
    def test_can_service_be_used__is_sucessful_for_profile(self, mock_can_service_be_used):
        profile = Mock()
        self.assertTrue(can_service_be_used(profile))
        mock_can_service_be_used.assert_called_with(SERVICE_NAME, profile)

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.can_service_be_used',
           return_value=True)
    def test_can_service_be_used__is_sucessful_for_tools(self, mock_can_service_be_used):
        self.assertTrue(can_service_be_used())
        mock_can_service_be_used.assert_called_with(SERVICE_NAME, None)

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.send_request_to_service')
    def test_send_request_to_service__success(self, mock_send_request):
        json_data = {"enm_service_name": "pmserv", "pib_parameter_name": "pmicSymbolicLinkCreationEnabled"}
        send_request_to_service(POST_METHOD, READ_PIB_URL, json_data)
        mock_send_request.assert_called_with(POST_METHOD, READ_PIB_URL, SERVICE_NAME, json_data=json_data, retry=True)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.can_service_be_used", return_value=True)
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.enm_deployment")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.read_pib_value")
    def test_get_pib_value_on_enm__is_successful_if_service_can_be_used(
            self, mock_read_pib_value, mock_enm_deployment, _):
        get_pib_value_on_enm("enm_service_name", "pib_parameter_name", "service_identifier")
        mock_read_pib_value.assert_called_with("enm_service_name", "pib_parameter_name", "service_identifier",)
        self.assertFalse(mock_enm_deployment.get_pib_value_on_enm.called)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.can_service_be_used", return_value=False)
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.enm_deployment")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.read_pib_value")
    def test_get_pib_value_on_enm__is_successful_if_service_can_not_be_used(
            self, mock_read_pib_value, mock_enm_deployment, _):
        get_pib_value_on_enm("enm_service_name", "pib_parameter_name", "service_identifier", ["service_locations"])
        mock_enm_deployment.get_pib_value_on_enm.assert_called_with("enm_service_name", "pib_parameter_name",
                                                                    "service_identifier", ["service_locations"])
        self.assertFalse(mock_read_pib_value.called)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_read_pib_value__is_successful(self, mock_send_request_to_service, mock_validate_response):
        json_data = {"enm_service_name": "pmserv", "pib_parameter_name": "pmicSymbolicLinkCreationEnabled"}
        mock_validate_response.return_value = "false"

        self.assertEqual("false", read_pib_value("pmserv", "pmicSymbolicLinkCreationEnabled"))
        mock_send_request_to_service.assert_called_with(POST_METHOD, READ_PIB_URL, json_data=json_data, retry=False)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_read_pib_value__is_successful_with_service_identifier(
            self, mock_send_request_to_service, mock_validate_response):
        json_data = {"enm_service_name": "cmserv", "pib_parameter_name": "maxAmosSessions",
                     "service_identifier": "terminal-websocket"}
        mock_validate_response.return_value = "120"

        self.assertEqual("120", read_pib_value("cmserv", "maxAmosSessions", service_identifier="terminal-websocket"))
        mock_send_request_to_service.assert_called_with(POST_METHOD, READ_PIB_URL, json_data=json_data, retry=False)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.can_service_be_used", return_value=True)
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.enm_deployment")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.update_pib_value")
    def test_update_pib_parameter_on_enm__is_successful_if_service_can_be_used(
            self, mock_update_pib_value, mock_enm_deployment, _):
        update_pib_parameter_on_enm("enm_service_name", "pib_parameter_name", "pib_parameter_value",
                                    ["enm_service_locations"], "service_identifier", "scope")
        mock_update_pib_value.assert_called_with("enm_service_name", "pib_parameter_name", "pib_parameter_value",
                                                 "service_identifier", "scope")
        self.assertFalse(mock_enm_deployment.update_pib_parameter_on_enm.called)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.can_service_be_used", return_value=False)
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.enm_deployment")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.update_pib_value")
    def test_update_pib_parameter_on_enm__is_successful_if_service_can_not_be_used(
            self, mock_update_pib_value, mock_enm_deployment, _):
        update_pib_parameter_on_enm("enm_service_name", "pib_parameter_name", "pib_parameter_value",
                                    ["enm_service_locations"], "service_identifier", "scope")
        mock_enm_deployment.update_pib_parameter_on_enm.assert_called_with(
            "enm_service_name", "pib_parameter_name", "pib_parameter_value", ["enm_service_locations"],
            "service_identifier", "scope")
        self.assertFalse(mock_update_pib_value.called)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_update_pib_value__is_successful(self, mock_send_request_to_service, _):
        json_data = {"enm_service_name": "pmserv", "pib_parameter_name": "pmicSymbolicLinkCreationEnabled",
                     "pib_parameter_value": "true"}
        update_pib_value("pmserv", "pmicSymbolicLinkCreationEnabled", "true")
        mock_send_request_to_service.assert_called_with(POST_METHOD, UPDATE_PIB_URL, json_data=json_data, retry=False)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_update_pib_value__is_successful_with_service_identifier_and_scope(self, mock_send_request_to_service, _):
        json_data = {"enm_service_name": "cmserv", "pib_parameter_name": "maxAmosSessions",
                     "pib_parameter_value": "150",
                     "service_identifier": "terminal-websocket", "scope": "GLOBAL"}
        update_pib_value("cmserv", "maxAmosSessions", "150", service_identifier="terminal-websocket", scope="GLOBAL")
        mock_send_request_to_service.assert_called_with(POST_METHOD, UPDATE_PIB_URL, json_data=json_data, retry=False)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_get_apache_url__success(self, mock_send_request_to_service, mock_validate_response):
        mock_validate_response.return_value = {'apache_url': "url"}
        self.assertEqual("url", get_apache_url())
        mock_send_request_to_service.assert_called_with(GET_METHOD, APACHE_URL, retry=False)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_deployment_service_info__success(self, mock_send_request_to_service, mock_validate_response):
        svc_ips = ["ip", "ip1"]
        mock_validate_response.return_value = {'service_info': svc_ips}
        service_name = "cmserv"
        json_data = {'enm_value': service_name}
        self.assertListEqual(svc_ips, get_deployment_service_info(service_name))
        mock_send_request_to_service.assert_called_with(POST_METHOD, SERVICE_INFO_URL, json_data=json_data, retry=False)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.print_service_operation_message")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_copy_cloud_user_key_to_emp__sends_request(self, mock_send_request_to_service, mock_print):
        copy_cloud_user_key_to_emp()
        mock_send_request_to_service.assert_called_with(GET_METHOD, COPY_EMP_KEY_URL, retry=False)
        self.assertEqual(1, mock_print.call_count)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_poid_refresh__sends_request(self, mock_send_request_to_service, mock_validate_response):
        self.assertEqual(mock_validate_response.return_value, poid_refresh())
        mock_validate_response.assert_called_with(mock_send_request_to_service.return_value)
        mock_send_request_to_service.assert_called_with(GET_METHOD, POID_REFRESH)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.print_service_operation_message")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_lms_password_less_access__no_password(self, mock_send_request_to_service,
                                                   mock_print_service_operation_message):
        json_data = {'username': 'user', 'password': None, 'ms_host': 'host'}
        lms_password_less_access(username='user', ms_host='host')
        mock_send_request_to_service.assert_called_with(POST_METHOD, LMS_PASS_URL, json_data=json_data, retry=False)
        self.assertEqual(1, mock_print_service_operation_message.call_count)

    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.print_service_operation_message")
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service")
    def test_lms_password_less_access__sends_request_encode_password(self, mock_send_request_to_service,
                                                                     mock_print_service_operation_message):
        json_data = {'username': None, 'password': base64.encodestring('password'), 'ms_host': None}
        lms_password_less_access(password='password')
        mock_send_request_to_service.assert_called_with(POST_METHOD, LMS_PASS_URL, json_data=json_data, retry=False)
        self.assertEqual(1, mock_print_service_operation_message.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response',
           return_value={'eniq_server': False, 'eniq_ip_list': []})
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service')
    def test_check_if_eniq_server__sends_request(self, mock_send_request_to_service, _):
        self.assertEqual((False, []), get_eniq_ip_list_check_if_eniq_server())
        mock_send_request_to_service.assert_called_with(GET_METHOD, ENIQ_URL, retry=False)

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.can_service_be_used',
           side_effect=[True, False])
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response',
           return_value={'enm_access': True, 'log_info': 'info message'})
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service')
    def test_check_enm_access__success(self, mock_send_request, *_):
        self.assertEqual((True, 'info message'), check_enm_access())
        mock_send_request.assert_called_once_with('GET', 'deployment/enm/access', retry=False)
        self.assertIsNone(check_enm_access())

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.can_service_be_used',
           side_effect=[True, False])
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response',
           return_value='policy')
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service')
    def test_check_password_ageing_policy_status__success(self, mock_send_request, *_):
        self.assertEqual('policy', check_password_ageing_policy_status())
        mock_send_request.assert_called_once_with('GET', 'deployment/password/ageing', retry=False)
        self.assertIsNone(check_password_ageing_policy_status())

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.can_service_be_used',
           return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response',
           return_value='test_network')
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service')
    def test_check_deployment_config__service_success(self, mock_send_request, *_):
        self.assertEqual('test_network', check_deployment_config())
        mock_send_request.assert_called_once_with('GET', 'deployment/config', retry=False)

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.can_service_be_used',
           return_value=False)
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.helper.get_network_config',
           return_value='test_network')
    def test_check_deployment_config__no_service(self, *_):
        self.assertEqual('test_network', check_deployment_config())

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.can_service_be_used',
           return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.validate_response',
           return_value={"service_info": ["some_ip1", "some_ip2"]})
    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.send_request_to_service')
    def test_get_list_of_scripting_service_ips__service_success(self, mock_send_request, *_):
        self.assertEqual(["some_ip1", "some_ip2"], get_list_of_scripting_service_ips())
        mock_send_request.assert_called_once_with('POST', 'deployment/info',
                                                  json_data={'enm_value': 'scripting_service_IPs'}, retry=False)

    @patch('enmutils_int.lib.services.deploymentinfomanager_adaptor.service_adaptor.can_service_be_used',
           return_value=False)
    @patch("enmutils_int.lib.services.deploymentinfomanager_adaptor.enm_deployment.get_list_of_scripting_service_ips",
           return_value=["some_ip1", "some_ip2"])
    def test_get_list_of_scripting_service_ips__no_service_success(self, *_):
        self.assertEqual(["some_ip1", "some_ip2"], get_list_of_scripting_service_ips())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
