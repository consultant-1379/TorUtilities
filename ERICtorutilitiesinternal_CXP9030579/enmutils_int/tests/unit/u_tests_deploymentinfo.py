#!/usr/bin/env python
import unittest2
from flask import Flask
from mock import patch, Mock

from enmutils.lib import log
from enmutils_int.lib.services import deploymentinfomanager as info
from testslib import unit_test_utils

app = Flask(__name__)

RSA_KEY_STR = '[{"enm":{"private_key":"-----BEGIN RSA PRIVATE KEY-----\\nM7\\nI==\\n-----END RSA PRIVATE KEY-----"}}]'
LMS_ROUTE = "deployment/lms/password"
SERVICE_IP_ROUTE = 'deployment/scripting_ips'


class DeploymentInfoManagerServiceUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.deploymentinfomanager.fetch_and_update_emp_key_if_no_longer_valid')
    @patch('enmutils_int.lib.services.deploymentinfomanager.copy_enm_keypair_to_emp')
    @patch('enmutils_int.lib.services.deploymentinfomanager.fetch_and_parse_cloud_native_pods')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_cloud_native_namespace')
    @patch('enmutils_int.lib.services.deploymentinfomanager.parse_global_properties')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_os_environ_keys')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger')
    @patch('enmutils_int.lib.services.deploymentinfomanager.create_and_start_once_off_background_scheduled_job')
    @patch('enmutils_int.lib.services.deploymentinfomanager.create_and_start_background_scheduled_job')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_haproxy_host')
    def test_at_startup__calls_functions_creates_background_jobs(
            self, mock_get_haproxy, mock_start, mock_once_off, *_):
        info.JOB, info.JOB1, info.JOB2 = None, None, None
        info.at_startup()
        self.assertEqual(1, mock_get_haproxy.call_count)
        self.assertEqual(2, mock_start.call_count)
        self.assertEqual(1, mock_once_off.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.fetch_and_update_emp_key_if_no_longer_valid')
    @patch('enmutils_int.lib.services.deploymentinfomanager.copy_enm_keypair_to_emp')
    @patch('enmutils_int.lib.services.deploymentinfomanager.fetch_and_parse_cloud_native_pods')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_cloud_native_namespace')
    @patch('enmutils_int.lib.services.deploymentinfomanager.parse_global_properties')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_os_environ_keys')
    @patch('enmutils_int.lib.services.deploymentinfomanager.create_and_start_once_off_background_scheduled_job')
    @patch('enmutils_int.lib.services.deploymentinfomanager.create_and_start_background_scheduled_job')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_haproxy_host')
    def test_at_startup__logs_exception(
            self, mock_get_haproxy, mock_debug,
            mock_create_and_start_background_scheduled_job, mock_create_and_start_once_off_background_scheduled_job,
            *_):
        mock_get_haproxy.func_name = "test"
        mock_get_haproxy.side_effect = [Exception("Error"), None]
        info.ENM_POID_DICT = {}
        info.JOB, info.JOB2, info.JOB1 = Mock(), Mock(), Mock()
        info.at_startup()
        self.assertEqual(1, mock_get_haproxy.call_count)
        mock_debug.assert_any_call('Failed to execute test, exception_encountered: [Error]')
        self.assertFalse(mock_create_and_start_background_scheduled_job.called)
        self.assertFalse(mock_create_and_start_once_off_background_scheduled_job.called)

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_json_response')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_haproxy_host')
    def test_get_apache_url__returns_hostname(self, mock_get_host, mock_response):
        mock_get_host.return_value = "hostname"
        with app.test_request_context('deployment/apache'):
            info.get_apache_url()
            mock_response.assert_called_with(message={'apache_url': 'https://hostname'})

    @patch('enmutils_int.lib.services.deploymentinfomanager.abort_with_message')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_haproxy_host')
    def test_get_apache_url__calls_abort_with_message_if_no_hostname(self, mock_get_host, mock_abort):
        mock_get_host.return_value = None
        with app.test_request_context('deployment/apache'):
            info.get_apache_url()
            self.assertEqual(1, mock_abort.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_cloud_native_service_vip')
    def test_get_general_scripting_ips_for_cloud_native__updates_enm_ip_dict_when_namespace_detected(self, mock_get_service_vip):
        mock_get_service_vip.return_value = 'some_ip'
        info.ENM_IP_DICT = {"cloud_native_namespace": "namespace"}
        info.get_general_scripting_ips_for_cloud_native()
        self.assertEqual(info.ENM_IP_DICT.get("scripting_service_IPs"), ['some_ip'])

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_cloud_native_service_vip')
    def test_get_general_scripting_ips_for_cloud_native__does_not_update_enm_ip_dict_when_namespace_not_detected(self, _):
        info.ENM_IP_DICT = {}
        info.get_general_scripting_ips_for_cloud_native()
        self.assertEqual(info.ENM_IP_DICT.get("scripting_service_IPs"), None)

    @patch('enmutils_int.lib.services.deploymentinfomanager.determine_ha_proxy')
    def test_get_haproxy_host__hostname_available(self, mock_determine):
        info.ENM_IP_DICT = {"haproxy": "hostname"}
        self.assertEqual('hostname', info.get_haproxy_host())
        self.assertEqual(0, mock_determine.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.mutexer.mutex')
    @patch('enmutils_int.lib.services.deploymentinfomanager.determine_ha_proxy')
    def test_get_haproxy_host__determines_host_name(self, mock_determine, _):
        info.ENM_IP_DICT = {}
        info.get_haproxy_host()
        self.assertEqual(1, mock_determine.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_ha_proxy_value_physical_or_venm')
    def test_determine_ha_proxy__physical(self, mock_physical):
        info.ENM_IP_DICT = {info.LMS_HOST_KEY: 'hostname'}
        info.determine_ha_proxy()
        self.assertEqual(1, mock_physical.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_ha_proxy_value_physical_or_venm')
    def test_determine_ha_proxy__virtual_enm(self, mock_venm):
        info.ENM_IP_DICT = {info.EMP_HOST_KEY: 'hostname'}
        info.determine_ha_proxy()
        self.assertEqual(1, mock_venm.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_ha_proxy_value_cloud_native')
    def test_determine_ha_proxy__cloud_native(self, mock_cloud):
        info.ENM_IP_DICT = {info.ENM_URL_KEY: 'hostname'}
        info.determine_ha_proxy()
        self.assertEqual(1, mock_cloud.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_deployment_vapp', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_ha_proxy_vapp')
    def test_determine_ha_proxy__vapp(self, mock_vapp, _):
        info.ENM_IP_DICT = {}
        info.determine_ha_proxy()
        self.assertEqual(1, mock_vapp.call_count)

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.is_deployment_vapp', return_value=False)
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_determine_ha_proxy__no_env_variables(self, mock_debug, _):
        info.ENM_IP_DICT = {}
        info.determine_ha_proxy()
        mock_debug.assert_called_with("Could not detect OS environ variables to identify deployment type.")

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput',
           return_value=(0, 'UI_PRES_SERVER=ieatENM5432-1.athtem.eei.ericsson.se'))
    def test_get_ha_proxy_value_physical_or_venm__success(self, _):
        info.ENM_IP_DICT = {}
        info.get_ha_proxy_value_physical_or_venm()
        self.assertEqual(info.ENM_IP_DICT.get('haproxy'), "ieatENM5432-1.athtem.eei.ericsson.se")

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(1, 'No hostname'))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_get_ha_proxy_value_physical_or_venm__failure(self, mock_debug, _):
        info.get_ha_proxy_value_physical_or_venm()
        mock_debug.assert_called_with("Could not retrieve LMS HA PROXY, response: [No hostname]")

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput',
           return_value=(0, 'UI_PRES_SERVER=ieatenmc5b03-16.athtem.eei.ericsson.se'))
    def test_get_ha_proxy_value_venm__success(self, _):
        info.ENM_IP_DICT = {}
        info.get_ha_proxy_value_physical_or_venm(venm=True)
        self.assertEqual(info.ENM_IP_DICT.get('haproxy'), "ieatenmc5b03-16.athtem.eei.ericsson.se")

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(1, 'No hostname'))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_get_ha_proxy_value_venm__failure(self, mock_debug, _):
        info.get_ha_proxy_value_physical_or_venm(venm=True)
        mock_debug.assert_called_with("Could not retrieve EMP UI PRES SERVER, response: [No hostname]")

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.get_uiserv_address',
           return_value=(0, 'ieatenmc11a003.athtem.eei.ericsson.se'))
    def test_get_ha_proxy_value_cloud_native__success(self, _):
        expected_host = "ieatenmc11a003.athtem.eei.ericsson.se"
        info.ENM_IP_DICT = {info.ENM_URL_KEY: expected_host}
        info.get_ha_proxy_value_cloud_native()
        self.assertEqual(info.ENM_IP_DICT.get('haproxy'), expected_host)

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.get_uiserv_address',
           return_value=(0, 'ieatenmc11a003.athtem.eei.ericsson.se'))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_get_ha_proxy_value_cloud_native__env_variable_doesnt_match(self, mock_debug, _):
        info.ENM_IP_DICT = {info.ENM_URL_KEY: "mismatch"}
        info.get_ha_proxy_value_cloud_native()
        mock_debug.assert_called_with("Could not retrieve or mismatch between ENV variable, ENM URL mismatch and Cloud "
                                      "Native UISERV address detected: [ieatenmc11a003.athtem.eei.ericsson.se]")

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.get_uiserv_address', return_value=(1, 'No hostname'))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_get_ha_proxy_value_cloud_native__failure(self, mock_debug, _):
        info.ENM_IP_DICT = {}
        info.get_ha_proxy_value_cloud_native()
        mock_debug.assert_called_with("Could not retrieve or mismatch between ENV variable, ENM URL None and Cloud "
                                      "Native UISERV address detected: [No hostname]")

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput',
           return_value=(0, 'UI_PRES_SERVER=ieatenmc5b03-16.athtem.eei.ericsson.se'))
    def test_get_ha_proxy_vapp__success(self, _):
        info.ENM_IP_DICT = {}
        info.get_ha_proxy_vapp()
        self.assertEqual(info.ENM_IP_DICT.get('haproxy'), "ieatenmc5b03-16.athtem.eei.ericsson.se")

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(1, 'No hostname'))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_get_ha_proxy_vapp__failure(self, mock_debug, _):
        info.get_ha_proxy_vapp()
        mock_debug.assert_called_with("Could not retrieve vApp HA PROXY, response: [No hostname]")

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput',
           side_effect=[(0, 'hostname'), (256, ''), (256, '')])
    def test_get_os_environ_keys__updates_service_dict_with_env_variables(self, _):
        info.ENM_IP_DICT = {}
        output = {'LMS_HOST': 'hostname'}
        info.get_os_environ_keys()
        self.assertDictEqual(output, info.ENM_IP_DICT)

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_haproxy_host', return_value='enm_url')
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput')
    def test_is_host_cloud_native__success(self, mock_output, _):
        mock_output.return_value = 0, "enm_url"
        self.assertTrue(info.is_deployment_cloud_native())

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_haproxy_host', return_value='enm_url')
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput')
    def test_is_host_cloud_native_false(self, mock_output, _):
        mock_output.return_value = 35112, "error"
        self.assertFalse(info.is_deployment_cloud_native())

    @patch('enmutils_int.lib.services.deploymentinfomanager.is_deployment_cloud_native', return_value=False)
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput')
    def test_fetch_and_parse_cloud_native_pods__no_cloud_native(self, mock_get_status, _):
        info.fetch_and_parse_cloud_native_pods()
        self.assertEqual(0, mock_get_status.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.is_deployment_cloud_native', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput')
    def test_fetch_and_parse_cloud_native_pods__success(self, mock_get_status, _):
        info.ENM_IP_DICT = {}
        mock_get_status.return_value = (0, "NAME                                                    READY   STATUS"
                                           "      RESTARTS   AGE\n"
                                           "accesscontrol-d8dd8788f-ddvr8                           3/3     Running"
                                           "     0          6d19h\n"
                                           "accesscontrol-d8dd8788f-lrgxl                           3/3     Running"
                                           "     0          6d19h\n"
                                           "amos-7bf55c8496-4xnrc                                   3/3     Running"
                                           "     0          6d19h\n"
                                           "amos-7bf55c8496-m9x6f                                   3/3     Running"
                                           "     0          6d19h\n"
                                           "apserv-7bbb547dc4-r8c28                                 3/3     Running"
                                           "     0          6d19h\n"
                                           "apserv-7bbb547dc4-xv57m                                 3/3     Running"
                                           "     0          6d19h\n"
                                           "autoidservice-7fcd94cbcf-twc6r                          3/3     Running"
                                           "     0          6d19h\n"
                                           "cmevents-5769798579-5qkg5                               3/3     Running"
                                           "     0          6d19h\n"
                                           "cmevents-5769798579-djhgg                               3/3     Running"
                                           "     0          6d19h\n"
                                           "cmserv-c7c678c75-2tq9g                                  3/3     Running"
                                           "     0          6d19h\n"
                                           "cmserv-c7c678c75-xp5qs                                  3/3     Running"
                                           "     0          6d19h")
        info.fetch_and_parse_cloud_native_pods()
        expected = {
            'cloud_native_pods': ['accesscontrol-d8dd8788f-ddvr8', 'accesscontrol-d8dd8788f-lrgxl',
                                  'amos-7bf55c8496-4xnrc', 'amos-7bf55c8496-m9x6f', 'apserv-7bbb547dc4-r8c28',
                                  'apserv-7bbb547dc4-xv57m', 'autoidservice-7fcd94cbcf-twc6r',
                                  'cmevents-5769798579-5qkg5', 'cmevents-5769798579-djhgg', 'cmserv-c7c678c75-2tq9g',
                                  'cmserv-c7c678c75-xp5qs']
        }
        self.assertEqual(1, mock_get_status.call_count)
        self.assertDictEqual(expected, info.ENM_IP_DICT)

    @patch('enmutils_int.lib.services.deploymentinfomanager.is_deployment_cloud_native', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(1, ""))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_fetch_and_parse_cloud_native_pods__no_output(self, mock_debug, *_):
        info.ENM_IP_DICT["cloud_native_namespace"] = "enm_url"
        info.fetch_and_parse_cloud_native_pods()
        mock_debug.assert_called_with("Failed to retrieve POD values with command: [/usr/local/bin/kubectl "
                                      "--kubeconfig /root/.kube/config get pods -n enm_url], output returned: [].")

    @patch('enmutils_int.lib.services.deploymentinfomanager.is_deployment_cloud_native', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput',
           return_value=(0, "NAME READY STATUS\n"))
    def test_fetch_and_parse_cloud_native_pods__no_pods_does_not_update_existing_value(self, *_):
        expected = ['cached pods']
        info.ENM_IP_DICT['cloud_native_pods'] = expected
        info.fetch_and_parse_cloud_native_pods()
        self.assertEqual(expected, info.ENM_IP_DICT.get('cloud_native_pods'))

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_lines_from_global_properties', return_value=[])
    def test_parse_global_properties__no_properties(self, _):
        info.ENM_IP_DICT = {}
        info.parse_global_properties()
        self.assertDictEqual({}, info.ENM_IP_DICT)

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_lines_from_global_properties',
           return_value=['key=ip,ip1,ip2', 'key1=somehash=', 'key2=""', ''])
    def test_parse_global_properties__adds_properties(self, _):
        info.ENM_IP_DICT = {}
        expected = {'key': ['ip', 'ip1', 'ip2'], 'key1': ['somehash=']}
        info.parse_global_properties()
        self.assertDictEqual(expected, info.ENM_IP_DICT)

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_deployment_vapp', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.get_lines_from_file')
    def test_get_lines_from_global_properties__vapp(self, mock_get_lines, _):
        info.get_lines_from_global_properties()
        self.assertEqual(1, mock_get_lines.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_deployment_vapp', return_value=False)
    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.get_lines_from_remote_file')
    def test_get_lines_from_global_properties__physical(self, mock_get_lines, _):
        info.ENM_IP_DICT[info.LMS_HOST_KEY] = "host"
        info.get_lines_from_global_properties()
        self.assertEqual(1, mock_get_lines.call_count)
        mock_get_lines.assert_called_with(info.GLOBAL_PROPERTIES, 'host', 'root')

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_deployment_vapp', return_value=False)
    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.get_lines_from_remote_file')
    def test_get_lines_from_global_properties__cloud(self, mock_get_lines, _):
        info.ENM_IP_DICT[info.LMS_HOST_KEY] = None
        info.ENM_IP_DICT[info.EMP_HOST_KEY] = 'cloud'
        info.get_lines_from_global_properties()
        self.assertEqual(1, mock_get_lines.call_count)
        mock_get_lines.assert_called_with(info.GLOBAL_PROPERTIES, 'cloud', 'cloud-user')

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_deployment_vapp', return_value=False)
    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.get_lines_from_file')
    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.get_lines_from_remote_file')
    def test_get_lines_from_global_properties__cloud_native(self, mock_remote_lines, mock_lines, _):
        info.ENM_IP_DICT = {}
        info.get_lines_from_global_properties()
        self.assertEqual(0, mock_lines.call_count)
        self.assertEqual(0, mock_remote_lines.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.is_deployment_cloud_native', return_value=False)
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput')
    def test_get_cloud_native_namespace__not_cloud_native(self, mock_status, _):
        info.get_cloud_native_namespace()
        self.assertEqual(0, mock_status.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.is_deployment_cloud_native', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(0, "enm_url"))
    def test_get_cloud_native_namespace__success(self, mock_status, _):
        info.get_cloud_native_namespace()
        self.assertEqual(1, mock_status.call_count)
        self.assertEqual("enm_url", info.ENM_IP_DICT.get("cloud_native_namespace"))

    @patch('enmutils_int.lib.services.deploymentinfomanager.is_deployment_cloud_native', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(256, ""))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_get_cloud_native_namespace__no_output(self, mock_debug, mock_status, _):
        info.get_cloud_native_namespace()
        self.assertEqual(1, mock_status.call_count)
        mock_debug.assert_called_with("Failed to retrieve Cloud Native namespace value with command: "
                                      "[/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ingress "
                                      "--all-namespaces 2>/dev/null | egrep uiserv], output returned: [].")

    @patch("enmutils_int.lib.services.deploymentinfomanager.get_pib_value_on_enm", return_value=5)
    @patch("enmutils_int.lib.services.deploymentinfomanager.get_json_response")
    def test_read_pib__is_successful(self, mock_get_json_response, _):
        request_data = {"enm_service_name": "cmserv",
                        "pib_parameter_name": "maxAmosSessions",
                        "service_identifier": "terminal-websocket"}

        with app.test_request_context('read_pib', json=request_data):
            pib_value = info.read_pib()

        self.assertEqual(mock_get_json_response.return_value, pib_value)
        mock_get_json_response.assert_called_with(message=5)

    @patch("enmutils_int.lib.services.deploymentinfomanager.log.logger")
    @patch("enmutils_int.lib.services.deploymentinfomanager.abort_with_message")
    @patch("enmutils_int.lib.services.deploymentinfomanager.get_pib_value_on_enm")
    @patch("enmutils_int.lib.services.deploymentinfomanager.get_json_response")
    def test_read_pib__results_in_abort_with_status_code_500_if_problem_occurred_trying_to_fetch_pib_value(
            self, mock_get_json_response, get_pib_value_on_enm, mock_abort_with_message, mock_logger):
        request_data = {"enm_service_name": "cmserv",
                        "pib_parameter_name": "maxAmosSessions",
                        "service_identifier": "terminal-websocket"}
        message = "Failure occurred during attempt to read PIB value"

        mock_exception = Exception()
        get_pib_value_on_enm.side_effect = mock_exception

        with app.test_request_context('read_pib', json=request_data):
            info.read_pib()

        self.assertFalse(mock_get_json_response.called)
        self.assertTrue(get_pib_value_on_enm.called)
        mock_abort_with_message.assert_called_with(message, mock_logger, info.SERVICE_NAME, log.SERVICES_LOG_DIR,
                                                   mock_exception)

    @patch("enmutils_int.lib.services.deploymentinfomanager.get_json_response")
    def test_get_deployment_info__is_successful(self, mock_get_json_response):
        request_data = {"enm_value": "cmserv"}
        info.ENM_IP_DICT["cmserv"] = ["ip", "ip1"]
        with app.test_request_context('get_deployment_info', json=request_data):
            enm_value = info.get_deployment_info()

        self.assertEqual(mock_get_json_response.return_value, enm_value)
        mock_get_json_response.assert_called_with(message={'service_info': ["ip", "ip1"]})

    @patch("enmutils_int.lib.services.deploymentinfomanager.log.logger")
    @patch("enmutils_int.lib.services.deploymentinfomanager.abort_with_message")
    def test_get_deployment_info__returns_404_if_no_value(self, mock_abort, mock_logger):
        request_data = {"enm_value": "cmserv"}
        info.ENM_IP_DICT = {}
        with app.test_request_context('get_deployment_info', json=request_data):
            info.get_deployment_info()

        message = ("No available information for: [cmserv], please ensure the deployment information requested is "
                   "correct.")
        mock_abort.assert_called_with(message, mock_logger, info.SERVICE_NAME, log.SERVICES_LOG_DIR,
                                      http_status_code=404)

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(0, ""))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_copy_enm_keypair_to_emp__success(self, mock_debug, _):
        info.ENM_IP_DICT[info.EMP_HOST_KEY] = "host"
        info.copy_enm_keypair_to_emp()
        mock_debug.assert_called_with("Successfully copied ENM key pair to EMP.")

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput',
           return_value=(1, "No such file."))
    def test_copy_enm_keypair_to_emp__raises_environ_error_if_copy_fails(self, _):
        info.ENM_IP_DICT[info.EMP_HOST_KEY] = "host"
        self.assertRaises(info.EnvironError, info.copy_enm_keypair_to_emp)

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput',
           side_effect=[(0, ""), (1, "No such file.")])
    def test_copy_enm_keypair_to_emp__raises_environ_error_if_move_fails(self, mock_get_status):
        info.ENM_IP_DICT[info.EMP_HOST_KEY] = "host"
        self.assertRaises(info.EnvironError, info.copy_enm_keypair_to_emp)
        self.assertEqual(2, mock_get_status.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_copy_enm_keypair_to_emp__no_emp_key(self, mock_debug, mock_get_output):
        info.ENM_IP_DICT[info.EMP_HOST_KEY] = None
        info.copy_enm_keypair_to_emp()
        self.assertEqual(1, mock_debug.call_count)
        self.assertEqual(0, mock_get_output.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.copy_enm_keypair_to_emp')
    @patch("enmutils_int.lib.services.deploymentinfomanager.get_json_response")
    def test_copy_emp_key__success(self, mock_response, _):
        with app.test_request_context('copy_emp'):
            info.copy_emp_key()
            mock_response.assert_called_with(message="Successfully copied ENM key pair to EMP.")

    @patch('enmutils_int.lib.services.deploymentinfomanager.copy_enm_keypair_to_emp',
           side_effect=info.EnvironError("Error"))
    @patch('enmutils_int.lib.services.deploymentinfomanager.abort_with_message')
    def test_copy_emp_key__failure(self, mock_abort, _):
        with app.test_request_context('copy_emp'):
            info.copy_emp_key()
            self.assertEqual(1, mock_abort.call_count)

    @patch("enmutils_int.lib.services.deploymentinfomanager.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.services.deploymentinfomanager.get_json_response")
    def test_update_pib__is_successful(self, mock_get_json_response, mock_update_pib_parameter_on_enm):
        request_data = {"enm_service_name": "cmserv",
                        "pib_parameter_name": "maxAmosSessions",
                        "pib_parameter_value": "150",
                        "service_identifier": "terminal-websocket",
                        "scope": "GLOBAL"}

        with app.test_request_context('update_pib', json=request_data):
            info.update_pib()

        self.assertTrue(mock_get_json_response.called)
        mock_update_pib_parameter_on_enm.assert_called_with("cmserv", "maxAmosSessions", "150",
                                                            service_identifier="terminal-websocket", scope="GLOBAL")

    @patch("enmutils_int.lib.services.deploymentinfomanager.log.logger")
    @patch("enmutils_int.lib.services.deploymentinfomanager.abort_with_message")
    @patch("enmutils_int.lib.services.deploymentinfomanager.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.services.deploymentinfomanager.get_json_response")
    def test_update_pib__results_in_abort_with_status_code_500_if_problem_occurred_trying_to_set_pib_value(
            self, mock_get_json_response, mock_update_pib_parameter_on_enm, mock_abort_with_message, mock_logger):
        request_data = {"enm_service_name": "cmserv",
                        "pib_parameter_name": "maxAmosSessions",
                        "pib_parameter_value": "150"}
        message = "Failure occurred during attempt to update PIB value"

        mock_exception = Exception()
        mock_update_pib_parameter_on_enm.side_effect = mock_exception

        with app.test_request_context('update_pib', json=request_data):
            info.update_pib()

        self.assertFalse(mock_get_json_response.called)
        mock_update_pib_parameter_on_enm.assert_called_with("cmserv", "maxAmosSessions", "150",
                                                            service_identifier=None, scope=None)
        mock_abort_with_message.assert_called_with(message, mock_logger, info.SERVICE_NAME, log.SERVICES_LOG_DIR,
                                                   mock_exception)

    @patch("enmutils_int.lib.services.deploymentinfomanager.abort_with_message")
    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.build_poid_dict_from_enm_data')
    @patch("enmutils_int.lib.services.deploymentinfomanager.get_json_response")
    def test_poid_refresh__is_successful(
            self, mock_get_json_response, mock_build_poid_dict_from_enm_data, mock_abort_with_message):
        with app.test_request_context('update_pib'):
            info.poid_refresh()
        self.assertFalse(mock_abort_with_message.called)
        mock_get_json_response.assert_called_with(message=mock_build_poid_dict_from_enm_data.return_value)
        self.assertTrue(mock_build_poid_dict_from_enm_data.called)

    @patch("enmutils_int.lib.services.deploymentinfomanager.abort_with_message")
    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.build_poid_dict_from_enm_data')
    @patch("enmutils_int.lib.services.deploymentinfomanager.get_json_response")
    def test_poid_refresh__calls_abort_if_error_occurs_while_removing_key(
            self, mock_get_json_response, mock_build_poid_dict_from_enm_data, mock_abort_with_message):
        error = Exception("error")
        mock_build_poid_dict_from_enm_data.side_effect = error
        with app.test_request_context('update_pib'):
            info.poid_refresh()
        mock_abort_with_message.assert_called_with("Failure occurred while fetching POID info from ENM", log.logger,
                                                   info.SERVICE_NAME, log.SERVICES_LOG_DIR, error)
        self.assertFalse(mock_get_json_response.called)

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_cloud_deployment_name', return_value="deployment")
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(0, RSA_KEY_STR))
    @patch('enmutils_int.lib.services.deploymentinfomanager.update_existing_emp_key')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_fetch_and_update_emp_key_if_no_longer_valid__updates_key(self, mock_debug, mock_update, *_):
        info.ENM_IP_DICT[info.EMP_HOST_KEY] = "host"
        info.fetch_and_update_emp_key_if_no_longer_valid()
        self.assertEqual(1, mock_update.call_count)
        mock_debug.assert_called_with("Requesting ENM key for deployment: [deployment].")

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_cloud_deployment_name', return_value="deployment")
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(0, ''))
    @patch('enmutils_int.lib.services.deploymentinfomanager.update_existing_emp_key')
    def test_fetch_and_update_emp_key_if_no_longer_valid__empty_key(self, mock_update, *_):
        info.ENM_IP_DICT[info.EMP_HOST_KEY] = "host"
        info.fetch_and_update_emp_key_if_no_longer_valid()
        self.assertEqual(0, mock_update.call_count)

    @patch('enmutils_int.lib.services.deploymentinfomanager.get_cloud_deployment_name', return_value=None)
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_fetch_and_update_emp_key_if_no_longer_valid__no_deployment_name(self, mock_debug, _):
        info.ENM_IP_DICT[info.EMP_HOST_KEY] = None
        info.fetch_and_update_emp_key_if_no_longer_valid()
        mock_debug.assert_called_with("Could not determine deployment name: [None] and EMP HOST value: [None].")

    def test_get_cloud_deployment_name__returns_ui_pres(self):
        info.ENM_IP_DICT = {info.EMP_HOST_KEY: "host", 'UI_PRES_SERVER': ['ieatenmc-16.se']}
        self.assertEqual('ieatenmc', info.get_cloud_deployment_name())

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(0, 'ieatenmc'))
    def test_get_cloud_deployment_name__returns_bashrc_entry(self, _):
        info.ENM_IP_DICT = {}
        self.assertEqual('ieatenmc', info.get_cloud_deployment_name())

    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(0, ''))
    def test_get_cloud_deployment_name__no_bashrc_entry(self, _):
        info.ENM_IP_DICT = {}
        self.assertIsNone(info.get_cloud_deployment_name())

    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.get_lines_from_file',
           return_value=['key'])
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_update_existing_emp_key__no_update_required(self, mock_debug, *_):
        info.update_existing_emp_key('key')
        mock_debug.assert_called_with("Key not available or no update required.")

    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.get_lines_from_file',
           return_value=['key1'])
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(1, 'Error'))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_update_existing_emp_key__update_required_fails(self, mock_debug, *_):
        info.update_existing_emp_key('key')
        mock_debug.assert_called_with("Failed to correctly update enm key pair, command output: [Error].")

    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.filesystem.get_lines_from_file',
           return_value=['key1'])
    @patch('enmutils_int.lib.services.deploymentinfomanager.commands.getstatusoutput', return_value=(0, 'key'))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_update_existing_emp_key__update_success(self, mock_debug, *_):
        info.update_existing_emp_key('key')
        mock_debug.assert_called_with("Successfully updated enm key pair.")

    @patch('enmutils_int.lib.services.deploymentinfomanager.pexpect.spawn')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_setup_lms_password_less_access__success(self, mock_debug, _):
        info.setup_lms_password_less_access("user", "pass", "host")
        mock_debug.assert_called_with("Completed password less access commands.")

    @patch('enmutils_int.lib.services.deploymentinfomanager.pexpect.spawn', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_setup_lms_password_less_access__raises_exception(self, mock_debug, _):
        self.assertRaises(info.EnvironError, info.setup_lms_password_less_access, "user", "pass", "host")
        mock_debug.assert_called_with("Failed to correctly create password less access to host: [host], error "
                                      "encountered: Error.")

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_deployment_vapp', return_value=False)
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_json_response')
    @patch('enmutils_int.lib.services.deploymentinfomanager.setup_lms_password_less_access')
    def test_lms_password_less_access__decodes_pass(self, mock_setup, *_):
        json_data = {'username': None, 'password': info.base64.encodestring('password'), 'ms_host': None}
        with app.test_request_context(LMS_ROUTE, json=json_data):
            info.lms_password_less_access()
            mock_setup.assert_called_with(username=None, password='password', ms_host=None)

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_deployment_vapp', return_value=False)
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger')
    @patch('enmutils_int.lib.services.deploymentinfomanager.abort_with_message')
    @patch('enmutils_int.lib.services.deploymentinfomanager.setup_lms_password_less_access')
    def test_lms_password_less_access__calls_abort_with_message(self, mock_setup, mock_abort, mock_logger, _):
        json_data = {'username': None, 'password': None, 'ms_host': None}
        exception = Exception("Error")
        mock_setup.side_effect = exception
        with app.test_request_context(LMS_ROUTE, json=json_data):
            info.lms_password_less_access()
            self.assertEqual(1, mock_abort.call_count)
            mock_abort.assert_called_with("Failure occurred attempting to setup password less access.", mock_logger,
                                          info.SERVICE_NAME, info.log.SERVICES_LOG_DIR, exception)

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_deployment_vapp', return_value=True)
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_json_response')
    def test_lms_password_less_access__returns_json_with_message_on_vapp(self, mock_get_json, mock_logger, _):
        json_data = {'username': None, 'password': None, 'ms_host': None}
        with app.test_request_context(LMS_ROUTE, json=json_data):
            info.lms_password_less_access()
            mock_logger.debug.assert_called_with("Already on LMS - No need for password-less access")
            mock_get_json.assert_called_with(message="Already on LMS - No need for password-less access")

    @patch('enmutils_int.lib.services.deploymentinfomanager.check_if_password_ageing_enabled')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_json_response')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger')
    def test_password_ageing__success(self, mock_logger, mock_get_json_response, mock_password_ageing):
        mock_password_ageing.return_value = "policy enabled"
        with app.test_request_context('deployment/password/ageing'):
            info.password_ageing()
            mock_logger.debug.assert_called_with('Establishing if ENM Password Ageing Policy is enabled')
            mock_get_json_response.assert_called_once_with(message='policy enabled')

    @patch('enmutils_int.lib.services.deploymentinfomanager.EnvironError', return_value=Exception('some error'))
    @patch('enmutils_int.lib.services.deploymentinfomanager.check_if_password_ageing_enabled')
    @patch('enmutils_int.lib.services.deploymentinfomanager.abort_with_message')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_json_response')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger')
    def test_password_ageing__failure(self, mock_logger, mock_get_json_response, mock_abort,
                                      mock_password_ageing, mock_exception):
        mock_password_ageing.side_effect = mock_exception.return_value
        with app.test_request_context('deployment/password/ageing'):
            info.password_ageing()
            self.assertFalse(mock_get_json_response.called)
            mock_abort.assert_called_once_with('Failure occured when checking if ENM Password Ageing Policy is enabled',
                                               mock_logger, 'deploymentinfomanager', '/home/enmutils/services',
                                               mock_exception.return_value)

    @patch('enmutils_int.lib.services.deploymentinfomanager.EnvironError', return_value=Exception('some error'))
    @patch('enmutils_int.lib.services.deploymentinfomanager.is_enm_accessible_to_workload')
    @patch('enmutils_int.lib.services.deploymentinfomanager.abort_with_message')
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_json_response')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger')
    def test_enm_access__success(self, mock_logger, mock_get_json_response, mock_abort,
                                 mock_is_enm_accessible_to_workload, mock_exception):
        mock_is_enm_accessible_to_workload.side_effect = [(False, 'no access'), mock_exception.return_value,
                                                          (True, 'enm accessible')]
        with app.test_request_context('deployment/enm/access'):
            info.enm_access()
            mock_logger.debug.assert_called_with('Establishing if ENM is accessible to workload')
            mock_get_json_response.assert_called_once_with(message={'log_info': 'no access', 'enm_access': False})
            info.enm_access()
            mock_abort.assert_called_once_with('Failure occured when checking if ENM is accessible to workload',
                                               mock_logger, 'deploymentinfomanager', '/home/enmutils/services',
                                               mock_exception.return_value)
            info.enm_access()
            mock_logger.debug.assert_called_with('Establishing if ENM is accessible to workload')
            mock_get_json_response.assert_called_with(message={'log_info': 'enm accessible', 'enm_access': True})

    @patch('enmutils_int.lib.services.deploymentinfomanager.run_cmd_on_different_deployment_types')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_is_enm_access_without_password__success_physical(self, mock_debug, mock_run_cmd):
        info.ENM_IP_DICT = {"LMS_HOST": "hostname"}
        info.is_enm_accessible_to_workload()
        mock_debug.assert_called_once_with("Establishing if workload VM has access to ENM")
        mock_run_cmd.assert_called_once_with('Establishing root ssh access to LMS',
                                             '/usr/bin/ssh -q $LMS_HOST hostname', 'Physical')

    @patch('enmutils_int.lib.services.deploymentinfomanager.run_cmd_on_different_deployment_types')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_is_enm_access_without_password__success_venm(self, mock_debug, mock_run_cmd):
        info.ENM_IP_DICT = {"EMP": "hostname"}
        info.is_enm_accessible_to_workload()
        mock_debug.assert_called_once_with("Establishing if workload VM has access to ENM")
        mock_run_cmd.assert_called_once_with('Establishing cloud-user access to EMP',
                                             '/usr/bin/ssh -i /var/tmp/enm_keypair.pem cloud-user@$EMP exit', 'vENM')

    @patch('enmutils_int.lib.services.deploymentinfomanager.run_cmd_on_different_deployment_types')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_is_enm_access_without_password__success_cenm(self, mock_debug, mock_run_cmd):
        info.ENM_IP_DICT = {"ENM_URL": "hostname"}
        info.is_enm_accessible_to_workload()
        mock_debug.assert_called_once_with("Establishing if workload VM has access to ENM")
        mock_run_cmd.assert_called_once_with('Checking that cluster is running and accessible',
                                             '/usr/local/bin/kubectl --kubeconfig /root/.kube/config cluster-info',
                                             'cENM')

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_deployment_vapp', side_effect=[True, False])
    @patch('enmutils_int.lib.services.deploymentinfomanager.run_cmd_on_different_deployment_types')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_is_enm_access_without_password__success_vapp_or_unknown(self, mock_debug, mock_run_cmd, _):
        info.ENM_IP_DICT = {}
        info.is_enm_accessible_to_workload()
        mock_debug.assert_called_once_with("Establishing if workload VM has access to ENM")
        mock_run_cmd.assert_called_once_with('Vapp detected - already on LMS', '', 'vApp')
        info.is_enm_accessible_to_workload()
        mock_run_cmd.assert_called_with('Unable to determine ENM type to establish if workload has access to ENM.'
                                        ' Please check Workload VM setup page: https://eteamspace.'
                                        'internal.ericsson.com/display/ERSD/Setting+up+a+Workload+VM+server',
                                        '', 'Unknown')

    @patch('enmutils_int.lib.services.deploymentinfomanager.shell.run_local_cmd', return_value=Mock(ok=True))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_run_cmd_on_different_deployment_types__enm_accessible(self, mock_debug, _):
        self.assertEqual((True, "Workload VM has access to venm"), info.run_cmd_on_different_deployment_types(
            'log statement', 'ls', 'venm'))
        mock_debug.assert_any_call('log statement')

    @patch('enmutils_int.lib.services.deploymentinfomanager.shell.run_local_cmd', return_value=Mock(ok=False))
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_run_cmd_on_different_deployment_types__enm_not_accessible(self, mock_debug, _):
        log_information = ("Workload VM does not have access to venm. Please check Workload VM setup page: "
                           "https://eteamspace.internal.ericsson.com/display/ERSD/"
                           "Setting+up+a+Workload+VM+server")
        self.assertEqual((False, log_information), info.run_cmd_on_different_deployment_types(
            'log statement', 'ls', 'venm'))
        mock_debug.assert_any_call('log statement')

    @patch('enmutils_int.lib.services.deploymentinfomanager.shell.run_local_cmd')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger.debug')
    def test_run_cmd_on_different_deployment_types__unknown_or_vapp_deployment(self, mock_debug, mock_run_cmd):
        self.assertEqual((False, 'log statement'), info.run_cmd_on_different_deployment_types(
            'log statement', '', 'venm'))
        self.assertFalse(mock_run_cmd.called)
        mock_debug.assert_called_once_with('log statement')
        self.assertEqual((True, 'log statement'), info.run_cmd_on_different_deployment_types(
            'log statement', '', 'vApp'))
        self.assertFalse(mock_run_cmd.called)
        mock_debug.assert_called_with('log statement')

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_eniq_server', return_value=(True, []))
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_json_response')
    def test_get_eniq__success(self, mock_get, _):
        with app.test_request_context('deployment/eniq'):
            info.get_eniq()
            mock_get.assert_called_with(message={'eniq_server': True, 'eniq_ip_list': []})

    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger')
    @patch('enmutils_int.lib.services.deploymentinfomanager.abort_with_message')
    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.is_eniq_server')
    def test_get_eniq__calls_abort_with_message(self, mock_eniq, mock_abort, mock_logger):
        exception = Exception("Error")
        mock_eniq.side_effect = exception
        with app.test_request_context('deployment/eniq'):
            info.get_eniq()
            self.assertEqual(1, mock_abort.call_count)
            mock_abort.assert_called_with("Failed to confirm if server is ENIQ server.", mock_logger, info.SERVICE_NAME,
                                          info.log.SERVICES_LOG_DIR, exception)

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.get_network_config', return_value="test_k_network")
    @patch('enmutils_int.lib.services.deploymentinfomanager.get_json_response')
    def test_deployment_config__success(self, mock_get_json_response, _):
        with app.test_request_context('deployment/type'):
            self.assertEqual(mock_get_json_response(), info.deployment_config())
            mock_get_json_response.assert_called_with(message='test_network')

    @patch('enmutils_int.lib.services.deploymentinfomanager.helper.get_network_config')
    @patch('enmutils_int.lib.services.deploymentinfomanager.log.logger')
    @patch('enmutils_int.lib.services.deploymentinfomanager.abort_with_message')
    def test_deployment_config__abort_response(self, mock_abort, mock_logger, mock_get_config):
        with app.test_request_context('deployment/type'):
            mock_exception = Exception("some_error")
            mock_get_config.side_effect = mock_exception
            info.deployment_config()
            message = 'Failure occured when checking deployment config'
            mock_abort.assert_called_with(message, mock_logger, 'deploymentinfomanager', '/home/enmutils/services',
                                          mock_exception)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
