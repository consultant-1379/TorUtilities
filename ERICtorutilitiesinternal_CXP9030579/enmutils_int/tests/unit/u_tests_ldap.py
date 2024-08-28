#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils.lib import filesystem
from enmutils.lib.enm_user_2 import User
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.ldap import LDAP
from testslib import unit_test_utils


@patch('enmutils.lib.enm_user_2.User.open_session')
class LDAPUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ldap_test_user")
        unit_test_utils.setup()
        self.nodes = [Mock()]
        self.nodes[0].node_id = 'netsim_LTE01ERBS00001'
        self.xml_file_name = 'test.xml'
        self.certificate_file = 'certificate.xml'
        self.ldap = LDAP(user=self.user, nodes=self.nodes, xml_file_name=self.xml_file_name,
                         certificate_file_name=self.certificate_file)

    def tearDown(self):
        unit_test_utils.tear_down()
        for test_file_path in [self.ldap.xml_file_path, self.ldap.certificate_path]:
            if filesystem.does_file_exist(test_file_path):
                filesystem.delete_file(test_file_path)

    @patch('enmutils_int.lib.ldap.LDAP.generate_xml_file')
    @patch('enmutils_int.lib.ldap.LDAP.execute_and_evaluate_command')
    @patch('enmutils_int.lib.ldap.filesystem')
    def test_configure_ldap_mo_from_enm_does_dir_exist(self, mock_filesystem, *_):
        mock_filesystem.does_dir_exist.return_value = True
        self.ldap.configure_ldap_mo_from_enm()

    @patch('enmutils_int.lib.ldap.LDAP.generate_xml_file')
    @patch('enmutils_int.lib.ldap.LDAP.execute_and_evaluate_command')
    @patch('enmutils_int.lib.ldap.filesystem')
    def test_configure_ldap_mo_from_enm_dir_exist(self, mock_filesystem, *_):
        mock_filesystem.does_dir_exist.return_value = False
        self.ldap.configure_ldap_mo_from_enm()
        mock_filesystem.create_dir.assert_called_once_with("/home/enmutils/amos")

    @patch('enmutils_int.lib.ldap.LDAP.generate_xml_file')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_configure_ldap_mo_from_enm_generates_xml(self, mock_enm_execute, mock_gen_xml, *_):
        response = Mock()
        response.get_output.return_value = [u'SUCCESS FDN']
        mock_enm_execute.return_value = response
        self.ldap.configure_ldap_mo_from_enm()
        self.assertEqual(1, mock_gen_xml.call_count)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_configure_ldap_mo_from_enm_raises_environ_error(self, mock_enm_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        mock_enm_execute.return_value = response
        self.assertRaises(EnvironError, self.ldap.configure_ldap_mo_from_enm)

    @patch('enmutils_int.lib.ldap.LDAP.generate_xml_file')
    @patch('enmutils_int.lib.ldap.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_configure_ldap_mo_from_enm_logs_on_success(self, mock_enm_execute, mock_debug, *_):
        response = Mock()
        response.get_output.return_value = [u'SUCCESS FDN']
        mock_enm_execute.return_value = response
        self.ldap.configure_ldap_mo_from_enm()
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_ldap_status_raises_environ_error(self, mock_enm_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'0 instance']
        mock_enm_execute.return_value = response
        self.assertRaises(EnvironError, self.ldap.get_ldap_status, self.nodes[0])

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_ldap_status(self, mock_enm_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'ldap', u'1']
        mock_enm_execute.return_value = response
        self.ldap.get_ldap_status(self.nodes[0])

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_set_filter_on_ldap_mo_raises_environ_error(self, mock_enm_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'0 instance']
        mock_enm_execute.return_value = response
        self.assertRaises(EnvironError, self.ldap.set_filter_on_ldap_mo, self.nodes[0])

    @patch('enmutils_int.lib.ldap.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_set_filter_on_ldap_mo(self, mock_enm_execute, mock_debug, *_):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s) updated']
        mock_enm_execute.return_value = response
        self.ldap.set_filter_on_ldap_mo(self.nodes[0])
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_create_and_issue_ldap_certificate_raises_environ_error(self, mock_enm_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'0 instance']
        mock_enm_execute.return_value = response
        self.assertRaises(EnvironError, self.ldap.create_and_issue_ldap_certificate)

    @patch('enmutils_int.lib.ldap.LDAP.generate_xml_file')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_create_and_issue_ldap_certificate_generates_xml(self, mock_enm_execute, mock_gen_xml, *_):
        response = Mock()
        response.get_output.return_value = [u'Executing ScriptEngine command \'secadm job get -j fea454c7-809b-4e4a-b22c-9ea3de85d6a6\'']
        mock_enm_execute.return_value = response
        self.ldap.create_and_issue_ldap_certificate()
        self.assertEqual(1, mock_gen_xml.call_count)

    @patch('enmutils_int.lib.ldap.LDAP.generate_xml_file')
    @patch('enmutils_int.lib.ldap.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_create_and_issue_ldap_certificate(self, mock_enm_execute, mock_debug, *_):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s) updated']
        mock_enm_execute.return_value = response
        self.ldap.create_and_issue_ldap_certificate()
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.ldap.et.ElementTree')
    @patch('enmutils_int.lib.ldap.filesystem.does_dir_exist', return_value=False)
    @patch('enmutils_int.lib.ldap.filesystem.create_dir')
    @patch('enmutils_int.lib.ldap.log.logger.debug')
    def test_generate_xml_file_creates_dir(self, mock_debug, mock_create_dir, *_):
        self.ldap.generate_xml_file(file_name=self.xml_file_name, element_dict={"useTls": "true"})
        self.assertTrue(mock_create_dir.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.ldap.log.logger.debug')
    @patch('enmutils_int.lib.ldap.filesystem.does_dir_exist', return_value=True)
    @patch('enmutils_int.lib.ldap.et.ElementTree')
    def test_generate_xml_file_raises_environ_error(self, mock_write, *_):
        mock_write.side_effect = Exception("Some Exception")
        self.assertRaises(EnvironError, self.ldap.generate_xml_file, file_name=self.xml_file_name,
                          element_dict={"useTls": "true"})

    def test_poll_until_job_complete_raises_environ_error(self, *_):
        self.assertRaises(EnvironError, self.ldap.poll_until_job_complete, timeout=0.0001)

    @patch('enmutils_int.lib.ldap.time.sleep')
    @patch('enmutils_int.lib.ldap.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_poll_until_job_complete_breaks(self, mock_enm_execute, mock_debug, mock_sleep, *_):
        response = Mock()
        response.get_output.return_value = ['blah', '\tCOMPLETED']
        mock_enm_execute.return_value = response
        self.ldap.job_id = '1234'
        self.ldap.poll_until_job_complete(wait_time=0.000025, timeout=0.0001)
        self.assertFalse(mock_sleep.called)

    @patch('enmutils_int.lib.ldap.time.sleep')
    @patch('enmutils_int.lib.ldap.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_poll_until_job_complete(self, mock_enm_execute, mock_debug, mock_sleep, *_):
        response = Mock()
        response.get_output.return_value = [u'Job Id\tCommand Id\tJob User\tJob Status\tJob Start Date\tJob End Date\tNode Name\tWorkflow Status\tWorkflow Start Date\tWorkflow Duration\tWorkflow Details', u'fea454c7-809b-4e4a-b22c-9ea3de85d6a6\tCERTIFICATE_ISSUE\tSECUI_10_0802-17480476_u0\tRUNNING\t2017-08-02 17:48:13\tN/A\tLTE01dg2ERBS00002\tRUNNING\t2017-08-02 17:48:13\tN/A\t[Check trustInstall: already installed][Perform action: startOnlineEnrollment performed. Polling progress][Check action ... ]', u'', u'Command Executed Successfully']
        mock_enm_execute.return_value = response
        self.ldap.job_id = '1234'
        self.ldap.poll_until_job_complete(wait_time=0.000025, timeout=0.0001)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_toggle_ldap_on_node_raises_environ_error(self, mock_enm_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'Error']
        mock_enm_execute.return_value = response
        self.assertRaises(EnvironError, self.ldap.toggle_ldap_on_node, self.nodes[0])

    @patch('enmutils_int.lib.ldap.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_toggle_ldap_on_node(self, mock_enm_execute, mock_debug, *_):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s) updated']
        mock_enm_execute.return_value = response
        self.ldap.toggle_ldap_on_node(self.nodes[0])
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_update_credentials_on_node_raises_environ_error(self, mock_enm_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'Error']
        mock_enm_execute.return_value = response
        self.assertRaises(EnvironError, self.ldap.update_credentials_on_node, self.nodes[0])

    @patch('enmutils_int.lib.ldap.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_update_credentials_on_node(self, mock_enm_execute, mock_debug, *_):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s) updated']
        mock_enm_execute.return_value = response
        self.ldap.update_credentials_on_node(self.nodes[0])
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_execute_and_evaluate_command_raises_error_if_no_output(self, mock_enm_execute, *_):
        response = Mock()
        response.get_output.return_value = None
        mock_enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, self.ldap.execute_and_evaluate_command, "cmd")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
