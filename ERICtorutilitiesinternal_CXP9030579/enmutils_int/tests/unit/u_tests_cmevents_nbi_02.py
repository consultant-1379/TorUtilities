#!/usr/bin/env python
import unittest2

from enmutils.lib.exceptions import EnvironError
from requests.exceptions import RequestException

from mock import patch, PropertyMock, Mock
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow import CmEventsNbi02


class CmEventsNbiUnitTests(unittest2.TestCase):
    data = [{"users": [{"username": "null", "password": "null", "type": "admin"}],
             "interfaces": [{"ports": {"ssh": 22}, "hostname": "null",
                             "type": "public", "ipv4": "141.137.232.23", "ipv6": "None"}],
             "hostname": "eventlistener", "type": "eventlistener", "nodes": [], "ports": {"ssh": 22}}]
    data_1 = [{'users': [{'username': 'null', 'password': 'null', 'type': 'admin'}],
               'interfaces': [{'ipv6': 'None', 'hostname': 'null', 'type': 'public', 'ports': {'ssh': 22},
                               'ipv4': '141.137.232.23'}],
               'hostname': None, 'nodes': [], 'type': 'eventlistener', 'ports': {'ssh': 22}}]
    data_2 = [{'users': [{'username': 'null', 'password': 'null'}],
               'interfaces': [
                   {'ipv6': 'None', 'hostname': 'null', 'type': None, 'ports': {'ssh': 22}, 'ipv4': '141.137.232.23'}],
               'hostname': 'eventlistener', 'nodes': [], 'type': 'eventlistener', 'ports': {'ssh': 22}}]

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.profile = CmEventsNbi02()
        self.profile.USER_ROLES = 'ADMINISTRATOR'
        self.profile.NUM_USERS = 1
        self.profile.NUM_SUBSCRIBERS = 2
        self.PAYLOAD = []
        self.SUBS_IDS = []

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.send_post_request')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.get_eventlistner_vm_ip')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.state',
           new_callable=PropertyMock)
    def test_execute_cmevent_flow__success(self, *_):
        self.profile.execute_flow()

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.send_post_request')
    @patch(
        'enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.read_existing_subscription',
        return_value='12')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.get_eventlistner_vm_ip')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.state',
           new_callable=PropertyMock)
    def test_execute_cmevent_flow__if_events_exists(self, *_):
        self.profile.execute_flow()

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.send_post_request',
           side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.get_eventlistner_vm_ip')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    def test_execute_cmevent_flow__raise_exception(self, mock_add_error_as_exception, *_):
        self.assertRaises(Exception, self.profile.execute_flow())

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_cloud_members_ip_address')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id',
           side_effect=[None, 'ip'])
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_emp')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.pexpect.spawn')
    def test_fetch_deployment_name_in_cloud_no_sid(self, mock_log, *_):
        self.profile.fetch_deployment_name_in_cloud()
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_cloud_members_ip_address')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id',
           side_effect=[None, None, None, None, None, None, None, None, None])
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_emp')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.pexpect.spawn')
    def test_fetch_deployment_name_in_cloud_for_retry(self, mock_log, *_):
        self.profile.fetch_deployment_name_in_cloud()
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_cloud_members_ip_address')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id',
           side_effect=[None, None, 'ip'])
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_emp')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.pexpect.spawn')
    def test_fetch_deployment_name_in_cloud_for_vio_name(self, mock_log, *_):
        self.profile.fetch_deployment_name_in_cloud()
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_cloud_members_ip_address')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id', return_value=["ip"])
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_emp')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.pexpect.spawn')
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.log.logger.debug")
    def test_fetch_deployment_name_in_cloud_success(self, *_):
        self.profile.fetch_deployment_name_in_cloud()

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_documents_info_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_document_content_from_dit")
    def test_fetch_eventlistener_vm_ip_in_cloud__raise_error_no_vm_ip(self, mock_get_document_content_from_dit,
                                                                      mock_get_documents_info_from_dit, *_):
        mock_get_document_content_from_dit.return_value = {"parameters": {"EVENTLISTENER": None}}
        with self.assertRaises(EnvironError) as e:
            self.profile.fetch_eventlistener_vm_ip_in_cloud("abc")
            self.assertEqual(e.exception.message, "EVENTLISTENER VM IP not available.")

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_documents_info_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_document_content_from_dit")
    def test_fetch_eventlistener_vm_ip_in_cloud__raise_error_no_vm_doc(self, mock_get_document_content_from_dit,
                                                                       mock_get_documents_info_from_dit, *_):
        mock_get_documents_info_from_dit.return_value = {u'cmevents': None}
        with self.assertRaises(EnvironError) as e:
            self.profile.fetch_eventlistener_vm_ip_in_cloud("abc")
            self.assertEqual(e.exception.message,
                             "CM_Subscribed_Events_Event_Listener document not attached to DIT to fetch 'eventlistener' IP.")

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_documents_info_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_document_content_from_dit")
    def test_fetch_eventlistener_vm_ip_in_cloud_success(self, *_):
        self.profile.fetch_eventlistener_vm_ip_in_cloud("abc")

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_documents_info_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_document_content_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id")
    def test_fetch_eventlistener_vm_ip_in_cloud_native__raise_error_no_vm_doc(self, mock_sid_id,
                                                                              mock_get_document_content_from_dit,
                                                                              mock_get_documents_info_from_dit, *_):
        mock_get_documents_info_from_dit.return_value = {u'cmevents': None}
        with self.assertRaises(EnvironError) as e:
            self.profile.fetch_eventlistener_vm_ip_in_cloud_native()
            self.assertEqual(e.exception.message,
                             "CM_Subscribed_Events_Event_Listener document not attached to DIT to fetch 'eventlistener' IP.")

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_documents_info_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_document_content_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id")
    def test_fetch_eventlistener_vm_ip_in_cloud_native__raise_error_no_vm_ip(self, mock_sid_id,
                                                                             mock_get_document_content_from_dit,
                                                                             mock_get_documents_info_from_dit, *_):
        mock_get_document_content_from_dit.return_value = {"parameters": {"EVENTLISTENER": None}}
        with self.assertRaises(EnvironError) as e:
            self.profile.fetch_eventlistener_vm_ip_in_cloud_native()
            self.assertEqual(e.exception.message, "EVENTLISTENER VM IP not available.")

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_documents_info_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_document_content_from_dit")
    def test_fetch_eventlistener_vm_ip_in_cloud_native__raise_error(self, mock_get_document_content_from_dit,
                                                                    mock_get_documents_info_from_dit,
                                                                    mock_run_local_cmd, _):
        mock_run_local_cmd.return_value.stdout = None
        with self.assertRaises(EnvironError) as e:
            self.profile.fetch_eventlistener_vm_ip_in_cloud_native()
            self.assertEqual(e.exception.message, "Issue occurred while fetching deployment name using kubectl "
                                                  "command.check maunally on wlvm by executing command /usr/local/bin/"
                                                  "kubectl --kubeconfig /root/.kube/config get ingress --all-namespaces"
                                                  " 2>/dev/null | egrep ui")

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_documents_info_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_document_content_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id")
    def test_fetch_eventlistener_vm_ip_in_cloud_native__success(self, mock_sid_id, mock_get_document_content_from_dit,
                                                                mock_get_documents_info_from_dit, mock_run_local_cmd,
                                                                *_):
        mock_sid_id.return_value = 'sed_id'
        mock_run_local_cmd.return_value.stdout = "the name of the deployment.cloud.native"
        mock_get_documents_info_from_dit.return_value = {"CM_Subscribed_Events_Event_Listener": "abc"}
        mock_get_document_content_from_dit.side_effect = [{"parameters": {"EVENTLISTENER": "ipv4_1"}}]
        self.assertEqual(self.profile.fetch_eventlistener_vm_ip_in_cloud_native(), "ipv4_1")

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_documents_info_from_dit")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_document_content_from_dit")
    @patch(
        "enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.fetch_deployment_name_cnis")
    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id")
    def test_fetch_eventlistener_vm_ip_in_cloud_native__success_no_sid_id(self, mock_sid_id, mock_cnis_dep,
                                                                          mock_get_document_content_from_dit,
                                                                          mock_get_documents_info_from_dit,
                                                                          mock_run_local_cmd, _):

        mock_run_local_cmd.return_value.stdout = "the name of the deployment.cloud.native"
        mock_sid_id.return_value = None
        mock_cnis_dep.return_value = 'cnisenm183'
        mock_get_documents_info_from_dit.return_value = {"CM_Subscribed_Events_Event_Listener": "abc"}
        mock_get_document_content_from_dit.side_effect = [{"parameters": {"EVENTLISTENER": "ipv4_1"}}]
        self.assertEqual(self.profile.fetch_eventlistener_vm_ip_in_cloud_native(), "ipv4_1")

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.requests.get')
    def test_fetch_eventlistener_vm_ip_in_physical__no_interface_public(self, mock_get, *_):
        response = Mock()
        response.status_code = 200
        response.json.return_value = self.data_2
        mock_get.return_value = response
        with self.assertRaises(EnvironError) as e:
            self.profile.fetch_eventlistener_vm_ip_in_physical(123)
            self.assertEqual(e.exception.message, "No 'public' interface found for 'eventlistener'.")

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.requests.get')
    def test_fetch_eventlistener_vm_ip_in_physical__no_event_data(self, mock_get, *_):
        response = Mock()
        response.status_code = 200
        response.json.return_value = self.data_1
        mock_get.return_value = response
        with self.assertRaises(EnvironError) as e:
            self.profile.fetch_eventlistener_vm_ip_in_physical(123)
            self.assertEqual(e.exception.message, "No block with hostname 'eventlistener' found.")

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.requests.get')
    def test_fetch_eventlistener_vm_ip_in_physical__if_responce_not_correct(self, mock_get, *_):
        response = Mock()
        response.status_code = 422
        mock_get.return_value = response
        with self.assertRaises(EnvironError) as e:
            self.profile.fetch_eventlistener_vm_ip_in_physical(123)
            self.assertEqual(e.exception.message, "Failed to retrieve data. Status code: 422")

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.requests.get')
    def test_fetch_eventlistener_vm_ip_in_physical__success(self, mock_get, *_):
        response = Mock()
        response.status_code = 200
        response.json.return_value = self.data
        mock_get.return_value = response
        self.profile.fetch_eventlistener_vm_ip_in_physical(123)

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_cmd_on_ms')
    def test_fetch_cluster_id_in_physical_no_enm_in_ouput(self, mock_run_local_cmd, *_):
        response = Mock()
        response.stdout = "-s"
        mock_run_local_cmd.return_value.stdout = "the name of the -s 123"
        self.assertEqual(self.profile.fetch_cluster_id_in_physical(), "123")

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_cmd_on_ms')
    def test_fetch_cluster_id_in_physical_if_enm_in_ouput(self, mock_run_local_cmd, *_):
        response = Mock()
        response.stdout = "-s"
        mock_run_local_cmd.return_value.stdout = "the name of the -s ENM123"
        self.assertEqual(self.profile.fetch_cluster_id_in_physical(), "123")

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_cmd_on_ms')
    def test_fetch_cluster_id_in_physical_if_s_in_ouput(self, mock_run_cmd, *_):
        response = Mock()
        response.stdout = "-s"
        mock_run_cmd.return_value = response
        self.profile.fetch_cluster_id_in_physical()

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_cmd_on_ms')
    def test_fetch_cluster_id_in_physical_raise_environ_error(self, mock_run_cmd, *_):
        response = Mock()
        response.stdout = "No such file or directory"
        mock_run_cmd.return_value = response
        self.profile.fetch_cluster_id_in_physical()

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.shell.run_cmd_on_ms')
    def test_fetch_cluster_id_in_physical_add_error_exception(self, mock_run_cmd, *_):
        mock_run_cmd.return_value.stdout = None
        with self.assertRaises(Exception) as e:
            self.profile.fetch_cluster_id_in_physical()
            self.assertEqual(e.exception.message, None)

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_enm_on_cloud_native',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.config.is_a_cloud_deployment',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_host_physical_deployment',
           return_value=True)
    @patch(
        'enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.fetch_eventlistener_vm_ip_in_physical',
        return_value=1234)
    @patch(
        'enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.fetch_cluster_id_in_physical',
        return_value=456)
    def test_get_eventlistner_vm_ip__success_in_physical(self, *_):
        self.profile.get_eventlistner_vm_ip()

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_enm_on_cloud_native',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.config.is_a_cloud_deployment',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_host_physical_deployment',
           return_value=False)
    @patch(
        'enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.fetch_eventlistener_vm_ip_in_cloud',
        return_value=1234)
    @patch(
        'enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.fetch_deployment_name_in_cloud',
        return_value="abc")
    def test_get_eventlistner_vm_ip__success_in_cloud(self, *_):
        self.profile.get_eventlistner_vm_ip()

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_enm_on_cloud_native',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.config.is_a_cloud_deployment',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_host_physical_deployment',
           return_value=False)
    @patch(
        'enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.fetch_eventlistener_vm_ip_in_cloud_native')
    def test_get_eventlistner_vm_ip__success_in_cloud_native(self, mock_cloud_native, *_):
        mock_cloud_native.return_value = 123
        cluster_ip = self.profile.get_eventlistner_vm_ip()
        self.assertEqual(cluster_ip, 123)

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_enm_on_cloud_native',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.config.is_a_cloud_deployment',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_host_physical_deployment',
           return_value=False)
    @patch(
        'enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.fetch_eventlistener_vm_ip_in_cloud_native')
    def test_get_eventlistner_vm_ip__not_able_to_get_cn(self, mock_cloud_native, *_):
        mock_cloud_native.return_value = 123
        with self.assertRaises(Exception) as e:
            self.profile.get_eventlistner_vm_ip()
            self.assertEqual(e.exception.message, "EVENTLISTENER VM are not available in ENM")

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_enm_on_cloud_native',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.config.is_a_cloud_deployment',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.is_host_physical_deployment',
           return_value=False)
    @patch(
        'enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.fetch_eventlistener_vm_ip_in_cloud_native')
    def test_get_eventlistner_vm_ip__raises_environ_error(self, mock_cloud_native, *_):
        mock_cloud_native.return_value = None
        with self.assertRaises(Exception) as e:
            self.profile.get_eventlistner_vm_ip()
            self.assertEqual(e.exception.message, "EVENTLISTENER VM are not available in ENM")

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.raise_for_status')
    def test_read_existing_subscription__add_error(self, *_):
        mock_exception = RequestException("mocked exception")
        self.user.get.side_effect = mock_exception
        self.profile.read_existing_subscription(self.user, 'test')

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.raise_for_status')
    def test_read_existing_subscription__if_code_return_unsuccess(self, *_):
        response = Mock()
        response.status_code = 204
        response.json.return_value = ""
        self.user.get.return_value = response
        self.assertEqual(self.profile.read_existing_subscription(self.user, 'test'), None)

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.raise_for_status')
    def test_read_existing_subscription__if_code_return_success(self, *_):
        response = Mock()
        response.status_code = 200
        response.json.return_value = [{u'ntfSubscriptionControl': {u'id': u'31'}}]
        self.user.get.return_value = response
        self.assertEqual(self.profile.read_existing_subscription(self.user, 'test'), [u'31'])

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.raise_for_status')
    def test_read_and_delete__for_delete_operation(self, *_):
        self.profile.read_and_delete(self.user, '123', "DELETE", {})

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.raise_for_status')
    def test_read_and_delete__success(self, *_):
        self.profile.read_and_delete(self.user, '123', "GET", {})

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.raise_for_status')
    def test_read_and_delete__add_error(self, *_):
        mock_exception = RequestException("mocked exception")
        self.user.get.side_effect = mock_exception
        self.profile.read_and_delete(self.user, '123', "GET", {})

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.raise_for_status')
    def test_send_post_request__exception(self, *_):
        mock_exception = RequestException("mocked exception")
        self.user.post.side_effect = mock_exception
        self.profile.send_post_request(self.user, 'test', {})

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.raise_for_status')
    def test_send_post_request__success(self, _):
        response = Mock()
        response.json.return_value = {u'ntfSubscriptionControl': {u'id': u'31'}}
        self.user.post.return_value = response
        self.assertEqual(self.profile.send_post_request(self.user, 'test', 'abc'), "31")

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_hostname_cloud_deployment')
    def test_get_hostname_of_cloud_having_sed_id(self, mock_cloud_deployment, mock_sed_id, _):
        mock_cloud_deployment.return_value = 'dp_hostname', 'deployment_hostname'
        mock_sed_id.return_value = 'sed_id'
        self.profile.get_hostname_of_cloud()

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.log.logger.debug")
    @patch(
        'enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.fetch_deployment_name_in_cloud',
        return_value="abc")
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_sed_id')
    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.get_hostname_cloud_deployment')
    def test_get_hostname_of_cloud_no_sed_id(self, mock_cloud_deployment, mock_sed_id, mock_cloud_name, _):
        mock_cloud_deployment.return_value = 'dp_hostname', 'deployment_hostname'
        mock_sed_id.return_value = ''
        self.profile.get_hostname_of_cloud()

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.log.logger.debug")
    def test_fetch_deployment_name_cnis(self, _):
        self.profile.fetch_deployment_name_cnis('enmcnis-n183p1.seli.gic.ericsson.se')

    @patch('enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.add_error_as_exception')
    def test_fetch_deployment_name_error(self, mock_error, *_):
        self.assertRaises(Exception, self.profile.fetch_deployment_name_cnis('enmcnis-np1.seli.gic.ericsson.se'))
        self.assertFalse(mock_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
