#!/usr/bin/env python
from datetime import datetime, timedelta

import unittest2
from enmutils.lib.exceptions import (ScriptEngineResponseValidationError, TimeOutError, ValidationError,
                                     EnvironError, DependencyException, EnmApplicationError)
from enmutils_int.lib.node_security import (NodeSecurity, NodeTrust, NodeSecurityLevel, NodeCredentials, NodeSSHKey,
                                            NodeCertificate, NodeSNMP, SecurityConfig, get_level, FTPES,
                                            get_nodes_not_at_required_level, generate_node_batches, check_sync,
                                            check_services_are_online, check_sync_and_remove, set_time_out,
                                            parse_tabular_output, check_job_status,
                                            get_required_services_status_on_cloud)
from mock import patch, Mock
from testslib import unit_test_utils


class NodeSecurityUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()

        self.nodes = [Mock() for _ in range(3)]
        self.nodes[0].node_id = 'netsim_LTE01ERBS00001'
        self.nodes[1].node_id = 'netsim_LTE01ERBS00002'
        self.nodes[2].node_id = 'netsim_LTE01ERBS00003'
        config = SecurityConfig()
        self.security = NodeSecurity(nodes=self.nodes, security_config=config, user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_is_algorithm_enabled_returns_true(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = \
            [u'Following is the list of algorithm(s) available in the system',
             u'Algorithm Name\tAlgorithm Type\tKey Size\tStatus', u'SHA224\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'SHA256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA384\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'SHA512\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA3-224\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'SHA3-256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA3-384\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'SHA3-512\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'HMAC_SHA256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'160-BIT_SHA-1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'0100-60-BIT_SHA-1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'', u'Command Executed Successfully']
        self.assertTrue(self.security._is_algorithm_enabled())

    def test_is_algorithm_enabled_returns_false(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = \
            [u'Following is the list of algorithm(s) available in the system',
             u'Algorithm Name\tAlgorithm Type\tKey Size\tStatus', u'SHA224\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'SHA256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA384\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'SHA512\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA3-224\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'SHA3-256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA3-384\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'SHA3-512\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'HMAC_SHA256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'160-BIT_SHA-1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
             u'0100-60-BIT_SHA-1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'', u'Command Executed Successfully']
        self.assertFalse(self.security._is_algorithm_enabled())

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_enable_algorithm_is_successful(self, mock_log_debug):
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Following is the list of algorithm(s) available in the system',
              u'Algorithm Name\tAlgorithm Type\tKey Size\tStatus', u'SHA224\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'SHA256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA384\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'SHA512\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA3-224\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'SHA3-256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA3-384\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'SHA3-512\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'HMAC_SHA256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'160-BIT_SHA-1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'0100-60-BIT_SHA-1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'', u'Command Executed Successfully'],
             [u'Algorithms updated Successfully']]
        self.security._enable_algorithm()
        self.assertTrue(mock_log_debug.called)

    def test_enable_algorithm_raises_validation_error_if_unsuccessful(self):
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Following is the list of algorithm(s) available in the system',
              u'Algorithm Name\tAlgorithm Type\tKey Size\tStatus', u'SHA224\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'SHA256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA384\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'SHA512\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA3-224\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'SHA3-256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'SHA3-384\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'SHA3-512\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'HMAC_SHA256\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'160-BIT_SHA-1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'0100-60-BIT_SHA-1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled', u'', u'Command Executed Successfully'],
             [u''],
             [u'Error: 11006 An error occurred while executing the PKI command on the '
              u'system. Consult the error and logs for more information.']]
        self.assertRaises(ScriptEngineResponseValidationError, self.security._enable_algorithm)

    @patch('enmutils_int.lib.enm_deployment.get_service_hosts')
    def test_get_number_of_workflows_is_successful(self, _):
        response = self.user.get.return_value
        response.iter_lines.return_value = \
            [u'Workflow [SSHKeyGeneration] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPActivateSL2] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [LdapConfigure] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPActivateIpSec] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [COMRemoveTrust] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [COMIssueCert] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [COMIssueTrustCert] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [LdapReconfigure] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPIssueTrustCertIpSec] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPInstallCertificatesIpSec] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPRemoveTrustOAM] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPIssueTrustCert] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPDeactivateIpSec] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [RevokeNodeCertificate] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPIssueCertIpSec] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPIssueCert] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPDeactivateSL2] - num. of running instances [0], instancesDetails [] ',
             u'Workflow [CPPRemoveTrustNewIPSEC] - num. of running instances [0], instancesDetails [] ',
             u'Total num. [3] ', u'']
        result = self.security._get_number_of_workflows()
        self.assertEqual(result, 3)

    def test_get_number_of_workflows_raises_validation_error_if_unsuccessful(self):
        response = self.user.get.return_value
        response.ok = False
        self.assertRaises(EnvironError, self.security._get_number_of_workflows)

    @patch('enmutils_int.lib.node_security.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.node_security.filesystem.delete_file')
    def test_delete_xml_file_success(self, mock_delete_file, _):
        self.security._delete_xml_file()
        self.assertEqual(mock_delete_file.call_count, 1)

    @patch('enmutils_int.lib.node_security.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.node_security.filesystem.delete_file')
    def test_delete_xml_file_when_file_not_present(self, mock_delete_file, _):
        self.security._delete_xml_file()
        self.assertEqual(mock_delete_file.call_count, 0)

    # check_services_are_online test cases
    @patch('enmutils_int.lib.node_security.get_required_services_status_on_cloud')
    @patch('enmutils_int.lib.node_security.is_emp', return_value=False)
    @patch('enmutils_int.lib.node_security.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.node_security.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    @patch('enmutils_int.lib.node_security.run_cmd_on_ms')
    def test_services_are_online__raises_environ_error(self, mock_run, mock_debug_log, *_):
        response = Mock(ok=False)
        mock_run.return_value = response
        self.assertRaises(EnvironError, check_services_are_online)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.node_security.get_required_services_status_on_cloud')
    @patch('enmutils_int.lib.node_security.is_emp', return_value=False)
    @patch('enmutils_int.lib.node_security.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.node_security.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    @patch('enmutils_int.lib.node_security.run_cmd_on_ms')
    def test_services_are_online__is_successful(self, mock_run_cmd, mock_debug_log, *_):
        response = Mock()
        response.ok.side_effect = [True, True, True, True, True, True]
        mock_run_cmd.return_value = response
        check_services_are_online()
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.node_security.get_required_services_status_on_cloud')
    @patch('enmutils_int.lib.node_security.is_emp', return_value=False)
    @patch('enmutils_int.lib.node_security.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.node_security.get_enm_cloud_native_namespace')
    @patch('enmutils.lib.shell.run_local_cmd', return_value=2)
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_services_are_online__on_cloud_native_raises_environ_error(self, mock_debug_log, *_):
        self.assertRaises(EnvironError, check_services_are_online)
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch('enmutils_int.lib.node_security.get_required_services_status_on_cloud')
    @patch('enmutils_int.lib.node_security.is_emp', return_value=False)
    @patch('enmutils_int.lib.node_security.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.node_security.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    @patch('enmutils_int.lib.node_security.run_local_cmd')
    def test_services_are_online__on_cloud_native_is_successful(self, mock_local_cmd, mock_debug_log, *_):
        response = Mock()
        response.ok.side_effect = [True, True, True, True, True, True]
        mock_local_cmd.return_value = response
        check_services_are_online()
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.node_security.is_emp', return_value=True)
    @patch('enmutils_int.lib.node_security.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.node_security.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.node_security.get_required_services_status_on_cloud')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_services_are_online__on_cloud_is_successful(self, mock_debug_log,
                                                         mock_get_required_services_status_on_cloud, *_):
        check_services_are_online()
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_get_required_services_status_on_cloud.call_count, 1)

    @patch('enmutils_int.lib.node_security.is_emp', return_value=True)
    @patch('enmutils_int.lib.node_security.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.node_security.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.node_security.get_required_services_status_on_cloud')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_services_are_online__on_cloud_raises_environ_error(self, mock_debug_log,
                                                                mock_get_required_services_status_on_cloud, *_):
        mock_get_required_services_status_on_cloud.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, check_services_are_online)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_get_required_services_status_on_cloud.call_count, 1)

    @patch('enmutils_int.lib.node_security.get_emp', return_value="1.1.1.1")
    @patch('enmutils_int.lib.node_security.run_cmd_on_vm')
    def test_get_required_services_status_on_cloud__is_successful(self, mock_run_cmd_on_vm, _):
        response = Mock()
        response.ok.side_effect = [True, True, True, True, True, True]
        mock_run_cmd_on_vm.return_value = response
        services = ["SPS", "PKIRASERV", "SECSERV", "MSCM", "MSFM", "FMALARMPROCESSING"]
        get_required_services_status_on_cloud(services)
        self.assertEqual(mock_run_cmd_on_vm.call_count, 6)

    @patch('enmutils_int.lib.node_security.get_emp', return_value="1.1.1.1")
    @patch('enmutils_int.lib.node_security.run_cmd_on_vm')
    def test_get_required_services_status_on_cloud__raises_environ_error(self, mock_run_cmd_on_vm, _):
        response = Mock(ok=False)
        mock_run_cmd_on_vm.return_value = response
        services = ["SPS", "PKIRASERV", "SECSERV", "MSCM", "MSFM", "FMALARMPROCESSING"]
        self.assertRaises(EnvironError, get_required_services_status_on_cloud, services)
        self.assertEqual(mock_run_cmd_on_vm.call_count, 1)

    def test_generate_node_batches_raises_runtime_error(self):
        self.security.nodes = []
        self.assertRaises(RuntimeError, generate_node_batches, self.security.nodes)

    def test_generate_node_batches_is_successful(self):
        self.security.nodes = [Mock() for _ in range(913)]
        node_batches = generate_node_batches(self.security.nodes)
        self.assertEqual(3, len(node_batches))
        self.assertEqual(450, len(node_batches[0]))
        self.assertEqual(450, len(node_batches[1]))
        self.assertEqual(13, len(node_batches[2]))

    def test_set_time_out(self):
        self.security.nodes = ['netsim_LTE01ERBS00001', 'netsim_LTE01ERBS00002', 'netsim_LTE01ERBS00003']
        self.assertEqual(set_time_out(self.security.nodes), 0)

    def test_check_sync_returns_false1(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'SYNCSTATUS : UNSYNCHRONIZED']
        self.assertFalse(check_sync(self.nodes[0].node_id, self.user))

    def test_check_sync_returns_false2(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'0 instance(s)']
        self.assertFalse(check_sync(self.nodes[0].node_id, self.user))

    def test_check_sync_returns_true(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'SYNCSTATUS : SYNCHRONIZED']
        self.assertTrue(check_sync(self.nodes[0].node_id, self.user))

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_check_sync_raises_exception(self, mock_log):
        self.user.enm_execute.side_effect = Exception
        self.assertRaises(Exception, check_sync, self.nodes[0].node_id, self.user)
        self.assertEqual(mock_log.call_count, 3)

    @patch("enmutils_int.lib.node_security.get_enm_network_element_sync_states")
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_sync_and_remove_remove__is_successful(self, mock_debug, mock_get_enm_network_element_sync_states):
        node1 = Mock(node_id="node1")
        node2 = Mock(node_id="node2")
        node3 = Mock(node_id="node3")
        mock_get_enm_network_element_sync_states.return_value = {"node1": "UNSYNCHRONIZED",
                                                                 "node2": "SYNCHRONIZED",
                                                                 "node3": "PENDING"}
        sync, unsynced = check_sync_and_remove([node1, node2, node3], self.user)
        self.assertTrue(mock_debug.called)
        self.assertEqual(1, len(sync))
        self.assertEqual(2, len(unsynced))
        self.assertEqual(1, mock_get_enm_network_element_sync_states.call_count)

    @patch("enmutils_int.lib.node_security.get_enm_network_element_sync_states")
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_check_sync_and_remove__is_successful_if_no_nodes_supplied(self, mock_debug, _):
        sync, unsynced = check_sync_and_remove([], self.user)
        self.assertEqual(0, len(sync))
        self.assertEqual(0, len(unsynced))
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.node_security.filesystem')
    def test_teardown_is_successful(self, _):
        self.security._teardown()

    @patch("enmutils_int.lib.node_security.log.logger.debug")
    def test_create_xml_file__raises_exception(self, mock_debug_log):
        self.security.xml_file_path = ''
        self.assertRaises(RuntimeError, self.security._create_xml_file, self.nodes)
        self.assertEqual(0, mock_debug_log.call_count)

    @patch("enmutils_int.lib.node_security.log.logger.debug")
    def test_create_xml_file__is_successful_if_profile_name_is_nodesec_11(self, mock_debug_log):
        self.security.xml_file_path = '/tmp/test.xml'
        self.security._create_xml_file(profile_name='NODESEC_11', nodes=self.nodes)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch("enmutils_int.lib.node_security.log.logger.debug")
    def test_check_job_status__if_status_completed(self, mock_log_debug, _):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = ['Job(s) Summary', ' ', 'Job Id : 5c74861d-6dd6-48d0-8472-8f237b76ac64',
                                            'Command Id : TRUST_DISTRIBUTE Job', 'User : NODESEC_13_0719-10505197_u0',
                                            'Job Status : COMPLETED',
                                            'Job Start Date : 2021-07-19 10:55:09', 'Job End Date : 2021-07-19 11:06:40',
                                            'Num Of Workflows : 1200', 'Num OfPending Workflows : 0',
                                            'Num Of Running Workflows : 0', 'Num OfSuccess Workflows : 1200',
                                            'Num Of Error Workflows : 0',
                                            'Min Duration Of Success Workflows : 00:00:02.871',
                                            'Max Duration Of Success Workflows : 00:01:28.560',
                                            'Avg Duration Of Success Workflows : 00:00:13.058']
        check_job_status(self.user, "secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0 --summary", "distribution")
        self.assertEqual(mock_log_debug.call_count, 4)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch("enmutils_int.lib.node_security.log.logger.debug")
    def test_check_job_status__if_status_running(self, mock_log_debug, _):
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = [['Job(s) Summary', ' ', 'Job Id : 5c74861d-6dd6-48d0-8472-8f237b76ac64',
                                            'Command Id : TRUST_DISTRIBUTE Job', 'User : NODESEC_13_0719-10505197_u0',
                                            'Job Status : RUNNING', 'Job Start Date : 2021-07-19 10:55:09',
                                            'Job End Date : 2021-07-19 11:06:40',
                                            'Num Of Workflows : 1200', 'Num OfPending Workflows : 1160',
                                            'Num Of Running Workflows : 0', 'Num OfSuccess Workflows : 40',
                                            'Num Of Error Workflows : 0',
                                            'Min Duration Of Success Workflows : 00:00:02.871',
                                            'Max Duration Of Success Workflows : 00:01:28.560',
                                            'Avg Duration Of Success Workflows : 00:00:13.058'],
                                           ['Job(s) Summary', ' ', 'Job Id : 5c74861d-6dd6-48d0-8472-8f237b76ac64',
                                            'Command Id : TRUST_DISTRIBUTE Job', 'User : NODESEC_13_0719-10505197_u0',
                                            'Job Status : COMPLETED', 'Job Start Date : 2021-07-19 10:55:09',
                                            'Job End Date : 2021-07-19 11:06:40',
                                            'Num Of Workflows : 1200', 'Num OfPending Workflows : 0',
                                            'Num Of Running Workflows : 0', 'Num OfSuccess Workflows : 1200',
                                            'Num Of Error Workflows : 0',
                                            'Min Duration Of Success Workflows : 00:00:02.871',
                                            'Max Duration Of Success Workflows : 00:01:28.560',
                                            'Avg Duration Of Success Workflows : 00:00:13.058']]
        check_job_status(self.user, "secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0 --summary", "distribution")
        self.assertEqual(mock_log_debug.call_count, 7)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch("enmutils_int.lib.node_security.log.logger.debug")
    def test_check_job_status__if_status_not_went_to_completed(self, mock_log_debug, _):
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = 10 * [['Job(s) Summary', ' ',
                                                 'Job Id : 5c74861d-6dd6-48d0-8472-8f237b76ac64',
                                                 'Command Id : TRUST_DISTRIBUTE Job',
                                                 'User : NODESEC_13_0719-10505197_u0',
                                                 'Job Status : RUNNING', 'Job Start Date : 2021-07-19 10:55:09',
                                                 'Job End Date : 2021-07-19 11:06:40',
                                                 'Num Of Workflows : 1200', 'Num OfPending Workflows : 1160',
                                                 'Num Of Running Workflows : 0', 'Num OfSuccess Workflows : 40',
                                                 'Num Of Error Workflows : 0',
                                                 'Min Duration Of Success Workflows : 00:00:02.871',
                                                 'Max Duration Of Success Workflows : 00:01:28.560',
                                                 'Avg Duration Of Success Workflows : 00:00:13.058']]
        self.assertRaises(EnvironError, check_job_status, self.user,
                          "secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0 --summary", "distribution")
        self.assertEqual(mock_log_debug.call_count, 31)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch("enmutils_int.lib.node_security.log.logger.debug")
    def test_check_job_status__raises_exception(self, mock_log_debug, _):
        self.user.enm_execute.return_value = Exception()
        check_job_status(self.user, "secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0 --summary", "distribution")
        self.assertEqual(mock_log_debug.call_count, 3)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch("enmutils_int.lib.node_security.log.logger.debug")
    def test_check_job_status__if_status_completed_when_trust_remove_job(self, mock_log_debug, _):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = ['Job(s) Summary', ' ', 'Job Id : 5c74861d-6dd6-48d0-8472-8f237b76ac64',
                                            'Command Id : TRUST_REMOVE Job', 'User : NODESEC_13_0719-10505197_u0',
                                            'Job Status : COMPLETED',
                                            'Job Start Date : 2021-07-19 10:55:09', 'Job End Date : 2021-07-19 11:06:40',
                                            'Num Of Workflows : 1200', 'Num OfPending Workflows : 0',
                                            'Num Of Running Workflows : 0', 'Num OfSuccess Workflows : 1200',
                                            'Num Of Error Workflows : 0',
                                            'Min Duration Of Success Workflows : 00:00:02.871',
                                            'Max Duration Of Success Workflows : 00:01:28.560',
                                            'Avg Duration Of Success Workflows : 00:00:13.058']
        check_job_status(self.user, "secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0 --summary", "distribution")
        self.assertEqual(mock_log_debug.call_count, 4)


class NodeTrustUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()

        self.nodes = [Mock() for _ in range(3)]
        self.nodes[0].node_id = 'netsim_LTE01DG200001'
        self.nodes[1].node_id = 'netsim_LTE01DG200002'
        self.nodes[2].node_id = 'netsim_LTE01DG200003'
        config = SecurityConfig()
        self.trust = NodeTrust(nodes=self.nodes, security_config=config, user=self.user)
        NodeTrust.CA_ENTITIES = {"ENM_E-mail_CA": ["CN=ENM_E-mail_CA,O=ERICSSON,C=SE,OU=BUCI_DUAC_NAM", "", 0]}
        self.trust.JOB_STATUS_CHECK_INTERVAL = 3 * 60
        self.ca_certificates = [u'List of Certificate(s)',
                                u'Entity Name\tEntity Type\tCertificate Serial No.\tSubject\tIssuer\tCertificate Status'
                                u'\tTDPS URL(s)',
                                u'ENM_NBI_CA\tCA_ENTITY\t462d26892703b2be\tSubject [subjectFields=[ [Type: COMMON_NAME '
                                u',Value: ENM_NBI_CA] ,'
                                u'  [Type: COUNTRY_NAME ,Value: SE] ,  [Type: ORGANIZATION ,Value: ERICSSON] , '
                                u' [Type: ORGANIZATION'
                                u'_UNIT ,Value: BUCI_DUAC_NAM] ], ]\tENM_Infrastructure_CA\tACTIVE\tIPv4: {http://'
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/ENM_NBI_CA/'
                                u'462d26892703b2be/active'
                                u'/ENM_Infrastructure_CA}',
                                u'ENM_Management_CA\tCA_ENTITY\t63df98a06666e99a\tSubject [subjectFields=[ '
                                u'[Type: COMMON_NAME ,Value:'
                                u' ENM_Management_CA] ,  [Type: COUNTRY_NAME ,Value: SE] , '
                                u' [Type: ORGANIZATION ,Value: ERICSSON] ,  '
                                u'[Type: ORGANIZATION_UNIT ,Value: BUCI_DUAC_NAM] ], ]\tENM_Infrastructure_CA\t'
                                u'ACTIVE\tIPv4: {http://'
                                u'192.168.0.155:8093/pki-ra-tdps/ca_entity/ENM_Management_CA/63df98a06666e99a/active/'
                                u'ENM_Infrastructure_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/ENM_Management_CA/'
                                u'63df98a06666e99a/'
                                u'active/ENM_Infrastructure_CA}',
                                u'ENM_OAM_CA\tCA_ENTITY\t4260f65d6be8e312\tSubject [subjectFields=[ '
                                u'[Type: COMMON_NAME ,Value:'
                                u' ENM_OAM_CA] ,  [Type: COUNTRY_NAME ,Value: SE] ,  [Type: ORGANIZATION ,'
                                u'Value: ERICSSON] ,  '
                                u'[Type: ORGANIZATION_UNIT ,Value: BUCI_DUAC_NAM] ], ]\tENM_Infrastructure_CA\t'
                                u'ACTIVE\tIPv4: {http://'
                                u'192.168.0.155:8093/pki-ra-tdps/ca_entity/ENM_OAM_CA/4260f65d6be8e312/active/'
                                u'ENM_Infrastructure_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/ENM_OAM_CA/'
                                u'4260f65d6be8e312/'
                                u'active/ENM_Infrastructure_CA}',
                                u'NE_IPsec_CA\tCA_ENTITY\t7816303dfaa6c9b6\tSubject [subjectFields=[ '
                                u'[Type: COMMON_NAME ,Value:'
                                u' NE_IPsec_CA] ,  [Type: COUNTRY_NAME ,Value: SE] ,  '
                                u'[Type: ORGANIZATION ,Value: ERICSSON] ,'
                                u'  [Type: ORGANIZATION_UNIT ,Value: BUCI_DUAC_NAM] ], '
                                u']\tENM_PKI_Root_CA\tACTIVE\tIPv4: {http://'
                                u'192.168.0.155:8093/pki-ra-tdps/ca_entity/NE_IPsec_CA/7816303dfaa6c9b6/active/'
                                u'ENM_PKI_Root_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/NE_IPsec_CA/'
                                u'7816303dfaa6c9b6'
                                u'/active/ENM_PKI_Root_CA}',
                                u'ENM_E-mail_CA\tCA_ENTITY\t21461f069ada96da\tSubject [subjectFields=['
                                u' [Type: COMMON_NAME ,Value: '
                                u'ENM_E-mail_CA] ,  [Type: COUNTRY_NAME ,Value: SE] ,  [Type: ORGANIZATION ,'
                                u'Value: ERICSSON] ,'
                                u'[Type: ORGANIZATION_UNIT ,Value: BUCI_DUAC_NAM] ], ]\tENM_PKI_Root_CA\tACTIVE\t'
                                u'IPv4: {http://'
                                u'192.168.0.155:8093/pki-ra-tdps/ca_entity/ENM_E-mail_CA/21461f069ada96da/active/'
                                u'ENM_PKI_Root_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/ENM_E-mail_CA/'
                                u'21461f069ada96da/'
                                u'active/ENM_PKI_Root_CA}',
                                u'NE_OAM_CA\tCA_ENTITY\t4b10c2aea9fa3aae\tSubject [subjectFields=['
                                u' [Type: COMMON_NAME ,Value: NE_OAM_CA],'
                                u'  [Type: COUNTRY_NAME ,Value: SE] ,  [Type: ORGANIZATION ,Value: ERICSSON] ,  '
                                u'[Type: ORGANIZATION_UNIT'
                                u' ,Value: BUCI_DUAC_NAM] ], ]\tENM_PKI_Root_CA\tACTIVE\tIPv4: '
                                u'{http://192.168.0.155:8093/pki-ra-tdps/'
                                u'ca_entity/NE_OAM_CA/4b10c2aea9fa3aae/active/ENM_PKI_Root_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/NE_OAM_CA/'
                                u'4b10c2aea9fa3aae/active'
                                u'/ENM_PKI_Root_CA}',
                                u'NE_External_CA\tCA_ENTITY\t309fb4a7a533c12a\tSubject [subjectFields=[ '
                                u'[Type: COMMON_NAME ,Value: '
                                u'NE_External_CA] ,  [Type: COUNTRY_NAME ,Value: SE] ,  '
                                u'[Type: ORGANIZATION ,Value: ERICSSON] ,  [Type: '
                                u'ORGANIZATION_UNIT ,Value: BUCI_DUAC_NAM] ], ]\tENM_PKI_Root_CA\tACTIVE\tIPv4: '
                                u'{http://'
                                u'192.168.0.155:8093/pki-ra-tdps/ca_entity/NE_External_CA/309fb4a7a533c12a/active/'
                                u'ENM_PKI_Root_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/NE_External_CA/'
                                u'309fb4a7a533c12a/'
                                u'active/ENM_PKI_Root_CA}',
                                u'ENM_External_Entity_CA\tCA_ENTITY\t14ee30afb899f9b2\tSubject '
                                u'[subjectFields=[ [Type: COMMON_NAME ,'
                                u'Value: ENM_External_Entity_CA], [Type: COUNTRY_NAME ,Value: SE] , '
                                u'[Type: ORGANIZATION ,Value: ERICSSON'
                                u'] ,  [Type: ORGANIZATION_UNIT ,Value: BUCI_DUAC_NAM] ], '
                                u']\tENM_PKI_Root_CA\tACTIVE\tIPv4: {http://192.'
                                u'168.0.155:8093/pki-ra-tdps/ca_entity/ENM_External_Entity_CA/14ee30afb899f9b2/'
                                u'active/ENM_PKI_Root_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/'
                                u'ENM_External_Entity_CA/'
                                u'14ee30afb899f9b2/active/ENM_PKI_Root_CA}',
                                u'ENM_PKI_Root_CA\tCA_ENTITY\t7f1b07c58bcf0d8a\tSubject [subjectFields=[ '
                                u'[Type: COMMON_NAME ,Value: '
                                u'ENM_PKI_Root_CA] ,  [Type: COUNTRY_NAME ,Value: SE] , '
                                u'[Type: ORGANIZATION ,Value: ERICSSON] ,  [Type: '
                                u'ORGANIZATION_UNIT ,Value: BUCI_DUAC_NAM] ], '
                                u']\tENM_PKI_Root_CA\tACTIVE\tIPv4: {http://'
                                u'192.168.0.155:8093/pki-ra-tdps/ca_entity/ENM_PKI_Root_CA/7f1b07c58bcf0d8a/'
                                u'active/ENM_PKI_Root_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/'
                                u'ENM_PKI_Root_CA/7f1b07c58bcf0d8a'
                                u'/active/ENM_PKI_Root_CA}',
                                u'ENM_UI_CA\tCA_ENTITY\t50e84bf2d11e8306\tSubject '
                                u'[subjectFields=[ [Type: COMMON_NAME ,Value: ENM_UI_CA],'
                                u'  [Type: COUNTRY_NAME ,Value: SE] ,  [Type: ORGANIZATION ,Value: ERICSSON] ,  '
                                u'[Type: ORGANIZATION_UNIT,'
                                u'Value: BUCI_DUAC_NAM] ], '
                                u']\tENM_Infrastructure_CA\tACTIVE\tIPv4: {http://'
                                u'192.168.0.155:8093/pki-ra-tdps/ca_entity/ENM_UI_CA/50e84bf2d11e8306/active/'
                                u'ENM_Infrastructure_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/ENM_UI_CA/'
                                u'50e84bf2d11e8306/active/'
                                u'ENM_Infrastructure_CA}',
                                u'VC_Root_CA_A1\tCA_ENTITY\t312d629535058d22\tSubject '
                                u'[subjectFields=[ [Type: COMMON_NAME ,Value: '
                                u'VC_Root_CA_A1] ,  [Type: ORGANIZATION ,Value: Ericsson] ,  '
                                u'[Type: COUNTRY_NAME ,Value: SE] ], ]\t'
                                u'VC_Root_CA_A1\tACTIVE\tIPv4: {http://192.168.0.155:8093/pki-ra-tdps/'
                                u'ca_entity/VC_Root_CA_A1/'
                                u'312d629535058d22/active/VC_Root_CA_A1}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/VC_Root_CA_A1/'
                                u'312d629535058d22/'
                                u'active/VC_Root_CA_A1}',
                                u'ENM_Infrastructure_CA\tCA_ENTITY\t7f5ba3211e88c1a2\tSubject '
                                u'[subjectFields=[ [Type: COMMON_NAME ,Value:'
                                u' ENM_Infrastructure_CA] ,  [Type: COUNTRY_NAME ,Value: SE] ,  '
                                u'[Type: ORGANIZATION ,Value: ERICSSON] ,  '
                                u'[Type: ORGANIZATION_UNIT ,Value: BUCI_DUAC_NAM] ], '
                                u']\tENM_PKI_Root_CA\tACTIVE\tIPv4: {http://192.'
                                u'168.0.155:8093/pki-ra-tdps/ca_entity/ENM_Infrastructure_CA/7f5ba3211e88c1a2/'
                                u'active/ENM_PKI_Root_CA}',
                                u'IPv6: {http://[2001:1b70:82a1:103::181]:8093/pki-ra-tdps/ca_entity/'
                                u'ENM_Infrastructure_CA/'
                                u'7f5ba3211e88c1a2/active/ENM_PKI_Root_CA}',
                                u'', u'Command Executed Successfully']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.node_security._get_values_from_row")
    def test_parse_tabular_output__is_successful(self, mock_get_values_from_row):
        mock_get_values_from_row.side_effect = [[u'Node Name', u'Install State', u'Install Error Message', u'Subject', u'Serial Number', u'Issuer'],
                                                [u'NetworkElement=netsim_LTE01ERBS00001', u'IDLE', u'Not Applicable',
                                                 u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
                                                 u'0', u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority'],
                                                [u'', u'', u'', u'CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
                                                 u'9177108028339044770', u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'],
                                                [u'', u'', u'', u'CN=ENM_OAM_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON', u'4783093685370282770',
                                                 u'CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'],
                                                [u'', u'', u'', u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
                                                 u'9158922812223589770', u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'],
                                                [u'NetworkElement=netsim_LTE01ERBS00002', u'IDLE', u'Not Applicable',
                                                 u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
                                                 u'0', u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority']]
        response = [u'Node Name\tInstall State\tInstall Error Message\tSubject\tSerial Number\tIssuer',
                    u'NetworkElement=netsim_LTE01ERBS00001\tIDLE\tNot Applicable\tC=SE,O=Ericsson,OU=EAB,CN=CPP Ericsson1 '
                    u'Root Certificate Authority\t0\tC=SE,O=Ericsson,OU=EAB,CN=CPP Ericsson1 Root Certificate Authority',
                    u'\t\t\tCN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t9177108028339044770\tCN=ENM_PKI_'
                    u'Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
                    u'\t\t\tCN=ENM_OAM_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t4783093685370282770\tCN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
                    u'NetworkElement=netsim_LTE01ERBS00002\tIDLE\tNot Applicable\tC=SE,O=Ericsson,OU=EAB,CN=CPP Ericsson1'
                    u' Root Certificate Authority\t0\tC=SE,O=Ericsson,OU=EAB,CN=CPP Ericsson1 Root Certificate Authority',
                    u'', u'Command Executed Successfully']
        self.assertEqual(4, len([tc for tc in parse_tabular_output(response, skip="Command Executed Successfully",
                                                                   multiline=True)]))
        self.assertEqual(mock_get_values_from_row.call_count, 5)

    def test_get_ca_trust_certificates_is_successful(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = self.ca_certificates
        self.trust._get_ca_certificates()
        self.assertEqual(self.trust.CA_ENTITIES["ENM_E-mail_CA"][2], 2397637964849649370)

    def test_get_ca_trust_certificates_raises_validation_error_if_unsuccessful(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = \
            [u'Error: 11202 No Entity found with given name. Please refer an existing entity and try again.']
        self.assertRaises(ScriptEngineResponseValidationError, self.trust._get_ca_certificates)

    @patch("enmutils_int.lib.node_security.parse_tabular_output")
    def test_get_nodes_trust_status__is_successful(self, mock_parse_tabular_output):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = \
            [u'Node Name\tInstall State\tInstall Error Message\tSubject\tSerial Number\tIssuer',
             u'NetworkElement=netsim_LTE01DG200001\tIDLE\tNot Applicable\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1'
             u' Root Certificate Authority\t0\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'\t\t\tCN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t9177108028339044770\tCN=ENM_PKI_Root_'
             u'CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'\t\t\tCN=ENM_OAM_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t4783093685370282770\tCN=ENM_Infrastructure_CA,'
             u'OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'\t\t\tCN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t9158922812223589770\tCN=ENM_PKI_Root_CA,'
             u'OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'NetworkElement=netsim_LTE01DG200002\tIDLE\tNot Applicable\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1'
             u' Root Certificate Authority\t0\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'', u'Command Executed Successfully']
        nodes_list = ['netsim_LTE01DG200001', 'netsim_LTE01DG200002']
        expected_output = {u'netsim_LTE01DG200001': 3, u'netsim_LTE01DG200002': 0}
        mock_parse_tabular_output.return_value = iter([
            {u'Serial Number': u'0', u'Install State': u'IDLE', u'Install Error Message': u'Not Applicable',
             u'Subject': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority'},
            {u'Serial Number': u'9177108028339044770', u'Install State': u'',
             u'Install Error Message': u'', u'Subject': u'CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'},
            {u'Serial Number': u'4783093685370282770', u'Install State': u'',
             u'Install Error Message': u'',
             u'Subject': u'CN=ENM_OAM_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'},
            {u'Serial Number': u'9158922812223589770', u'Install State': u'',
             u'Install Error Message': u'', u'Subject': u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'},
            {u'Serial Number': u'0', u'Install State': u'IDLE', u'Install Error Message': u'Not Applicable',
             u'Subject': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200002',
             u'Issuer': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority'}])
        NodeTrust.CA_ENTITIES = \
            {"ENM_PKI_Root_CA": ["CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON", "", 9158922812223589770],
             "ENM_Infrastructure_CA": ["CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON", "", 9177108028339044770],
             "ENM_OAM_CA": ["CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON", "", 4783093685370282770]}
        self.assertEqual(self.trust._get_trust_status(nodes_list), expected_output)
        mock_parse_tabular_output.assert_called_with(response.get_output.return_value,
                                                     skip="Command Executed Successfully", multiline=True)

    @patch("enmutils_int.lib.node_security.parse_tabular_output")
    def test_get_nodes_trust_status__if_nodes_trust_information_mismatch(self, mock_parse_tabular_output):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = \
            [u'Node Name\tInstall State\tInstall Error Message\tSubject\tSerial Number\tIssuer',
             u'NetworkElement=netsim_LTE01DG200001\tIDLE\tNot Applicable\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1'
             u' Root Certificate Authority\t0\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'\t\t\tCN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t9177108028339044770\tCN=ENM_PKI_Root_'
             u'CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'\t\t\tCN=ENM_OAM_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t4783093685370282770\tCN=ENM_Infrastructure_CA,'
             u'OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'\t\t\tCN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t9158922812223589770\tCN=ENM_PKI_Root_CA,'
             u'OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'NetworkElement=netsim_LTE01ERBS00002\tIDLE\tNot Applicable\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1'
             u' Root Certificate Authority\t0\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'', u'Command Executed Successfully']
        nodes_list = ['netsim_LTE01DG200001', 'netsim_LTE01DG200002']
        expected_output = {u'netsim_LTE01DG200001': 2, u'netsim_LTE01DG200002': 0}
        mock_parse_tabular_output.return_value = iter([
            {u'Serial Number': u'0', u'Install State': u'IDLE', u'Install Error Message': u'Not Applicable',
             u'Subject': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority'},
            {u'Serial Number': u'9177108028339044770', u'Install State': u'',
             u'Install Error Message': u'', u'Subject': u'CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'},
            {u'Serial Number': u'4783093685370282770', u'Install State': u'',
             u'Install Error Message': u'',
             u'Subject': u'CN=ENM_OAM_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'},
            {u'Serial Number': u'9158922812223589770',
             u'Install Error Message': u'', u'Subject': u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'},
            {u'Serial Number': u'0', u'Install State': u'IDLE', u'Install Error Message': u'Not Applicable',
             u'Subject': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200002',
             u'Issuer': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority'}])
        NodeTrust.CA_ENTITIES = \
            {"ENM_PKI_Root_CA": ["CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON", "", 9158922812223589770],
             "ENM_Infrastructure_CA": ["CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON", "", 9177108028339044770],
             "ENM_OAM_CA": ["CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON", "", 4783093685370282770]}
        self.assertEqual(self.trust._get_trust_status(nodes_list), expected_output)
        mock_parse_tabular_output.assert_called_with(response.get_output.return_value,
                                                     skip="Command Executed Successfully", multiline=True)

    @patch("enmutils_int.lib.node_security.parse_tabular_output")
    def test_get_nodes_trust_status__if_one_node_id_empty_in_trust_information(self, mock_parse_tabular_output):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = \
            [u'Node Name\tInstall State\tInstall Error Message\tSubject\tSerial Number\tIssuer',
             u'NetworkElement=netsim_LTE01DG200001\tIDLE\tNot Applicable\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1'
             u' Root Certificate Authority\t0\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'\t\t\tCN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t9177108028339044770\tCN=ENM_PKI_Root_'
             u'CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'\t\t\tCN=ENM_OAM_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t4783093685370282770\tCN=ENM_Infrastructure_CA,'
             u'OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'\t\t\tCN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON\t9158922812223589770\tCN=ENM_PKI_Root_CA,'
             u'OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'NetworkElement=netsim_LTE01DG200002\tIDLE\tNot Applicable\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1'
             u' Root Certificate Authority\t0\tC=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'', u'Command Executed Successfully']
        nodes_list = ['netsim_LTE01DG200001', 'netsim_LTE01DG200002']
        expected_output = {u'netsim_LTE01DG200001': 2, u'netsim_LTE01DG200002': 0}
        mock_parse_tabular_output.return_value = iter([
            {u'Serial Number': u'0', u'Install State': u'IDLE', u'Install Error Message': u'Not Applicable',
             u'Subject': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority'},
            {u'Serial Number': u'9177108028339044770', u'Install State': u'',
             u'Install Error Message': u'', u'Subject': u'CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'},
            {u'Serial Number': u'4783093685370282770', u'Install State': u'',
             u'Install Error Message': u'',
             u'Subject': u'CN=ENM_OAM_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'Node Name': '',
             u'Issuer': u'CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'},
            {u'Serial Number': u'9158922812223589770', u'Install State': u'',
             u'Install Error Message': u'', u'Subject': u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200001',
             u'Issuer': u'CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON'},
            {u'Serial Number': u'0', u'Install State': u'IDLE', u'Install Error Message': u'Not Applicable',
             u'Subject': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority',
             u'Node Name': u'NetworkElement=netsim_LTE01DG200002',
             u'Issuer': u'C=SE, O=Ericsson, OU=EAB, CN=CPP Ericsson1 Root Certificate Authority'}])
        NodeTrust.CA_ENTITIES = \
            {"ENM_PKI_Root_CA": ["CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON", "", 9158922812223589770],
             "ENM_Infrastructure_CA": ["CN=ENM_PKI_Root_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON", "", 9177108028339044770],
             "ENM_OAM_CA": ["CN=ENM_Infrastructure_CA,OU=BUCI_DUAC_NAM,C=SE,O=ERICSSON", "", 4783093685370282770]}
        self.assertEqual(self.trust._get_trust_status(nodes_list), expected_output)
        mock_parse_tabular_output.assert_called_with(response.get_output.return_value,
                                                     skip="Command Executed Successfully", multiline=True)

    def test_get_nodes_trust_status_raises_validation_error_if_unsuccessful(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = \
            [u'Node', u'NetworkElement=netsim__LTE01ERBS00001',
             u'Error 10004 : The MO specified does not exist - NetworkElement=netsim__LTE01ERBS00001',
             u'Suggested Solution : Please specify a valid MO that exists in the system.']
        nodes_list = ['netsim_LTE01DG200001', 'netsim_LTE01DG200002']
        self.assertRaises(ScriptEngineResponseValidationError, self.trust._get_trust_status, nodes_list=nodes_list)

    @patch('enmutils_int.lib.node_security.NodeTrust._get_trust_status')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_check_trust__successfully_trims_nodes_list(self, mock_debug_log, mock_get_trust_status):
        mock_get_trust_status.return_value = {'netsim_LTE01DG200002': 2, 'netsim_LTE01DG200001': 0}
        nodes_list = ['netsim_LTE01DG200001', 'netsim_LTE01DG200002']
        self.trust._check_trust(nodes_list, 3)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_get_trust_status.call_count)

    @patch('enmutils_int.lib.node_security.NodeTrust._get_trust_status')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_check_trust__successfully_if_num_trusts_certificate_check_value_is_two(self, mock_debug_log,
                                                                                    mock_get_trust_status):
        mock_get_trust_status.return_value = {'netsim_LTE01DG200002': 3, 'netsim_LTE01DG200001': 3}
        nodes_list = ['netsim_LTE01DG200001', 'netsim_LTE01DG200002']
        self.trust._check_trust(nodes_list, 3)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_get_trust_status.call_count)

    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_ca_certificates')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_distribution__is_successful(self, mock_log_debug, mock_get_ca_certificates,
                                                    mock_check_job_status):
        response = self.user.enm_execute.return_value
        mock_get_ca_certificates.return_value = self.ca_certificates
        response.get_output.return_value = ["Successfully started a job for trust distribution to nodes. "
                                            "Perform 'secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0' "
                                            "to get progress info."]
        self.trust.distribute("nodes.txt", "/tmp/nodes.txt")
        self.assertEqual(2, mock_log_debug.call_count)
        self.assertEqual(1, mock_get_ca_certificates.call_count)
        self.assertEqual(1, mock_check_job_status.call_count)

    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_ca_certificates')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_distribution__if_serial_number_already_existed(self, mock_log_debug, mock_get_ca_certificates,
                                                                       mock_check_job_status):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = ["Successfully started a job for trust distribution to nodes. "
                                            "Perform 'secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0' "
                                            "to get progress info."]
        NodeTrust.CA_ENTITIES = {"ENM_E-mail_CA": ["CN=ENM_E-mail_CA,O=ERICSSON,C=SE,OU=BUCI_DUAC_NAM", "",
                                                   2397637964849649370]}
        self.trust.distribute("nodes.txt", "/tmp/nodes.txt")
        self.assertEqual(2, mock_log_debug.call_count)
        self.assertEqual(0, mock_get_ca_certificates.call_count)
        self.assertEqual(1, mock_check_job_status.call_count)

    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_ca_certificates')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_distribution__is_successful_if_ca_is_not_included(self, mock_log_debug,
                                                                          mock_get_ca_certificates,
                                                                          mock_check_job_status):
        response = self.user.enm_execute.return_value
        mock_get_ca_certificates.return_value = self.ca_certificates
        response.get_output.return_value = ["Successfully started a job for trust distribution to nodes. "
                                            "Perform 'secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0' "
                                            "to get progress info."]
        self.trust.distribute("nodes.txt", "/tmp/nodes.txt", include_ca=False)
        self.assertEqual(2, mock_log_debug.call_count)
        self.assertEqual(1, mock_get_ca_certificates.call_count)
        self.assertEqual(1, mock_check_job_status.call_count)

    @patch('enmutils_int.lib.node_security.NodeTrust._get_ca_certificates')
    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_distribution__raises_validation_error_if_unsuccessful(self, mock_log_debug,
                                                                              mock_check_job_status, _):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Node', u'NetworkElement=netsim_LTE04DG200000',
                                            u'Error 10004 : The node specified does not exist',
                                            u'Suggested Solution : Please specify a valid MO that exists '
                                            u'in the system.']
        self.assertRaises(ScriptEngineResponseValidationError, self.trust.distribute, "nodes.txt", "/tmp/nodes.txt")
        self.assertEqual(0, mock_log_debug.call_count)
        self.assertEqual(0, mock_check_job_status.call_count)

    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_ca_certificates')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_removal__is_successful(self, mock_log_debug, mock_get_ca_certificates,
                                               mock_check_job_status):
        response = self.user.enm_execute.return_value
        mock_get_ca_certificates.return_value = self.ca_certificates
        response.get_output.return_value = ["Successfully started a job for trust removal from nodes. "
                                            "Perform 'secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0' "
                                            "to get progress info."]
        self.trust.remove("nodes.txt", "/tmp/nodes.txt")
        self.assertEqual(2, mock_log_debug.call_count)
        self.assertEqual(1, mock_get_ca_certificates.call_count)
        self.assertEqual(1, mock_check_job_status.call_count)

    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_ca_certificates')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_removal__if_serial_number_already_existed(self, mock_log_debug, mock_get_ca_certificates,
                                                                  mock_check_job_status):
        response = self.user.enm_execute.return_value
        mock_get_ca_certificates.return_value = self.ca_certificates
        response.get_output.return_value = ["Successfully started a job for trust removal from nodes. "
                                            "Perform 'secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0' "
                                            "to get progress info."]
        NodeTrust.CA_ENTITIES = {"ENM_E-mail_CA": ["CN=ENM_E-mail_CA,O=ERICSSON,C=SE,OU=BUCI_DUAC_NAM", "",
                                                   2397637964849649370]}
        self.trust.remove("nodes.txt", "/tmp/nodes.txt")
        self.assertEqual(2, mock_log_debug.call_count)
        self.assertEqual(0, mock_get_ca_certificates.call_count)
        self.assertEqual(1, mock_check_job_status.call_count)

    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_ca_certificates')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_removal__is_successful_if_check_job_status_on_teardown_true(self, mock_log_debug,
                                                                                    mock_get_ca_certificates,
                                                                                    mock_check_job_status):
        response = self.user.enm_execute.return_value
        mock_get_ca_certificates.return_value = self.ca_certificates
        response.get_output.return_value = ["Successfully started a job for trust removal from nodes. "
                                            "Perform 'secadm job get -j 5684fb8a-90e7-4b3a-9c2d-8409985a1aa0' "
                                            "to get progress info."]
        self.trust.remove("nodes.txt", "/tmp/nodes.txt", check_job_status_on_teardown=True)
        self.assertEqual(2, mock_log_debug.call_count)
        self.assertEqual(1, mock_get_ca_certificates.call_count)
        self.assertEqual(0, mock_check_job_status.call_count)

    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_ca_certificates')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_removal__raises_validation_error_if_unsuccessful(self, mock_log_debug,
                                                                         mock_get_ca_certificates,
                                                                         mock_check_job_status):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Node', u'NetworkElement=netsim_LTE04DG200000',
                                            u'Error 10004 : The node specified does not exist',
                                            u'Suggested Solution : Please specify a valid MO that exists in the system.']
        self.assertRaises(ScriptEngineResponseValidationError, self.trust.remove, "nodes.txt", "/tmp/nodes.txt")
        self.assertEqual(0, mock_log_debug.call_count)
        self.assertEqual(1, mock_get_ca_certificates.call_count)
        self.assertEqual(0, mock_check_job_status.call_count)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeTrust._check_trust')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_validation__is_successful(self, mock_log_debug, mock_get_number_of_workflows,
                                                  mock_check_trust, *_):
        mock_get_number_of_workflows.side_effect = [1, 0]
        self.trust.start_time = datetime.now()
        self.trust.verify_timeout = 4
        self.trust.validate(action='distribute', check_trusts=False)
        self.assertEqual(mock_log_debug.call_count, 6)
        self.assertEqual(mock_check_trust.call_count, 0)
        self.assertEqual(mock_get_number_of_workflows.call_count, 2)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeTrust._check_trust')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_validation__raises_timeout_error_if_timeout_expired(self, mock_log_debug,
                                                                            mock_get_number_of_workflows,
                                                                            mock_check_trust, *_):
        mock_get_number_of_workflows.side_effect = [1, 1, 1]
        self.trust.verify_timeout = 4 * 60 * 60
        self.trust.start_time = datetime.now() - timedelta(seconds=14401)
        self.assertRaises(TimeOutError, self.trust.validate, action='distribute', check_trusts=False)
        self.assertEqual(mock_log_debug.call_count, 0)
        self.assertEqual(mock_check_trust.call_count, 0)
        self.assertEqual(mock_get_number_of_workflows.call_count, 0)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeTrust._check_trust')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_validation__raises_validation_error_if_unsuccessful(self, mock_log_debug,
                                                                            mock_get_number_of_workflows,
                                                                            mock_check_trust, *_):
        mock_get_number_of_workflows.return_value = 0
        self.trust.start_time = datetime.now()
        self.assertRaises(ValidationError, self.trust.validate, action='remove', check_trusts=True, fail_fast=True)
        self.assertEqual(mock_log_debug.call_count, 2)
        self.assertEqual(mock_check_trust.call_count, 1)
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeTrust._check_trust')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_validation__successful_if_action_is_remove(self, mock_log_debug, mock_get_number_of_workflows,
                                                                   mock_check_trust, *_):
        mock_get_number_of_workflows.return_value = 0
        self.trust.verify_timeout = 0.001
        self.trust.start_time = datetime.now()
        self.assertRaises(TimeOutError, self.trust.validate, action='remove', check_trusts=True, fail_fast=False)
        self.assertTrue(mock_log_debug.called)
        self.assertTrue(mock_check_trust.called)
        self.assertEqual(1, mock_get_number_of_workflows.call_count)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeTrust._check_trust')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_validation__if_nodes_not_exist(self, mock_log_debug, mock_get_number_of_workflows,
                                                       mock_check_trust, *_):
        mock_get_number_of_workflows.return_value = 0
        self.trust.start_time = datetime.now()
        self.trust.verify_timeout = 10
        self.trust.nodes = []
        self.trust.validate(action='distribute', check_trusts=True)
        self.assertEqual(mock_log_debug.call_count, 3)
        self.assertEqual(mock_check_trust.call_count, 1)
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeTrust._check_trust')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_trust_validation__if_polling_time_is_expired(self, mock_log_debug, mock_get_number_of_workflows,
                                                               mock_check_trust, *_):
        mock_get_number_of_workflows.side_effect = [1, 1, 0]
        self.trust.start_time = datetime.now()
        self.trust.verify_timeout = 20
        self.trust.validate(action='distribute', check_trusts=False)
        self.assertEqual(mock_log_debug.call_count, 9)
        self.assertEqual(mock_check_trust.call_count, 0)
        self.assertEqual(mock_get_number_of_workflows.call_count, 3)

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeTrust._check_trust')
    @patch('enmutils_int.lib.node_security.NodeTrust._get_number_of_workflows')
    def test_node_trust_validation__if_check_workflows_false(self, mock_get_number_of_workflows, *_):
        self.trust.start_time = datetime.now()
        self.trust.verify_timeout = 0.1
        mock_get_number_of_workflows.side_effect = [0, 1]
        self.assertRaises(TimeOutError, self.trust.validate)


class NodeSecurityLevelUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()

        self.nodes = [Mock() for _ in range(3)]
        self.nodes[0].node_id = 'netsim_LTE01ERBS00001'
        self.nodes[1].node_id = 'netsim_LTE01ERBS00002'
        self.nodes[2].node_id = 'netsim_LTE01ERBS00003'
        config = SecurityConfig()
        self.security_level = NodeSecurityLevel(nodes=self.nodes, security_config=config, user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.get_nodes_not_at_required_level')
    @patch('enmutils_int.lib.node_security.NodeSecurityLevel._get_number_of_workflows')
    def test_node_security_level_validation__if_check_workflows(self, mock_get_number_of_workflows, *_):
        self.security_level.verify_timeout = 0.1
        self.security_level.cert_prev_status = {"test": "status"}
        mock_get_number_of_workflows.side_effect = [0, 1]
        self.security_level.start_time = datetime.now()
        self.assertRaises(TimeOutError, self.security_level.validate, self.nodes)

    def test_get_nodes_security_level_is_successful(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Node Name \tNode Security Level', u'netsim_LTE01ERBS00001\tlevel 2',
                                            u'netsim_LTE01ERBS00002\tlevel 1', u'netsim_LTE01ERBS00003\t ', u'',
                                            u'Command Executed Successfully']
        nodes_list = ['netsim_LTE01ERBS00001', 'netsim_LTE01ERBS00002', 'netsim_LTE01ERBS00003']
        expected_output = {u'netsim_LTE01ERBS00001': 2, u'netsim_LTE01ERBS00002': 1}
        self.assertEqual(get_level(nodes_list, self.user), expected_output)

    def test_get_nodes_security_level_raises_validation_error_if_unsuccessful(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = \
            [u'Node', u'NetworkElement=netsim__LTE01ERBS00001',
             u'Error 10004 : The MO specified does not exist - NetworkElement=netsim__LTE01ERBS00001',
             u'Suggested Solution : Please specify a valid MO that exists in the system.']
        nodes_list = ['netsim_LTE01ERBS00001', 'netsim_LTE01ERBS00002']
        self.assertRaises(ScriptEngineResponseValidationError, get_level, nodes_list=nodes_list, user=self.user)

    def test_get_nodes_security_level_raises_dependecny_error__if_unsuccessful(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Node Name \tNode Security Levell', u'netsim_LTE01ERBS00001\tlevel 2',
                                            u'Command Executed Successfully']
        nodes_list = ['netsim_LTE01ERBS00001', 'netsim_LTE01ERBS00002', 'netsim_LTE01ERBS00003']
        self.assertRaises(DependencyException, get_level, nodes_list, self.user)

    def test_check_number_of_nodes_without_security_level_enabled(self):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Node Name \tNode Security Level', u'netsim_LTE01ERBS00001\tlevel 2',
                                            u'netsim_LTE01ERBS00002\tlevel 1', u'netsim_LTE01ERBS00003\tlevel 1', u'',
                                            u'Command Executed Successfully']
        nodes_list = ['netsim_LTE01ERBS00001', 'netsim_LTE01ERBS00002', 'netsim_LTE01ERBS00003']
        get_nodes_not_at_required_level(nodes_list, self.user, required_security_level=2)
        self.assertEqual(len(nodes_list), 2)

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_set_node_security_level_is_successful(self, mock_log_debug, *_):
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Following is the list of algorithm(s) available in the system',
              u'SHA1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'', u'Command Executed Successfully'],
             [u'Security level change initiated']]
        self.security_level.file_name = 'NODESEC_03.xml'
        self.security_level.xml_file_path = '/tmp/enmutils/NODESEC_03.xml'
        self.security_level.set_level()
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.node_security.time.sleep')
    def test_set_node_security_level_raises_validation_error_if_unsuccessful(self, *_):
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Following is the list of algorithm(s) available in the system',
              u'SHA1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'', u'Command Executed Successfully'],
             [u'Error 10007 : The NetworkElement MO does not exist for the associated MeContext MO',
              u'Suggested Solution : Please create the NetworkElement MO and any other required MOs '
              u'or the associated MeContext MO.'], [u'']]
        self.security_level.file_name = 'NODESEC_03.xml'
        self.security_level.xml_file_path = '/tmp/enmutils/NODESEC_03.xml'
        self.assertRaises(ScriptEngineResponseValidationError, self.security_level.set_level)

    # validate test cases
    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeSecurityLevel._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_security_level_validation__is_successful(self, mock_log_debug, mock_get_number_of_workflows, *_):
        response = self.user.get.return_value
        response.iter_lines.side_effect = [[u'Total num. [1] '], [u'Total num. [0] ']]
        mock_get_number_of_workflows.side_effect = [1, 0]
        self.security_level.start_time = datetime.now()
        self.security_level.verify_timeout = 4
        self.security_level.validate(self.nodes, check_levels=False)
        self.assertEqual(mock_log_debug.call_count, 6)
        self.assertEqual(mock_get_number_of_workflows.call_count, 2)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeSecurityLevel._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_security_level_validation__raises_timeout_error_if_timeout_expired(self, mock_log_debug,
                                                                                     mock_get_number_of_workflows, *_):
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = [[u'Total num. [1] '], [u'Total num. [1] '], [u'Total num. [1] ']]
        self.security_level.verify_timeout = 15 * 60
        self.security_level.start_time = datetime.now() - timedelta(seconds=901)
        mock_get_number_of_workflows.side_effect = [1, 1, 1]
        self.assertRaises(TimeOutError, self.security_level.validate, self.nodes, self.security_level.start_time,
                          check_levels=False)
        self.assertEqual(mock_log_debug.call_count, 0)
        self.assertEqual(mock_get_number_of_workflows.call_count, 0)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeSecurityLevel._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_security_level_validation__raises_validation_error_when_check_level_is_true(
            self, mock_log_debug, mock_get_number_of_workflows, *_):
        response_workflows = self.user.get.return_value
        response_workflows.iter_lines.return_value = [u'Total num. [0] ']
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = [[u'Command Executed Successfully'],
                                           [u'Node Name \tNode Security Level', u'netsim_LTE01ERBS00001\tlevel 0',
                                            u'netsim_LTE01ERBS00002\tlevel 1', u'netsim_LTE01ERBS00003\tlevel 1', u'',
                                            u'Command Executed Successfully']]
        self.security_level.start_time = datetime.now()
        mock_get_number_of_workflows.side_effect = [0]
        self.assertRaises(ValidationError, self.security_level.validate, self.nodes, check_levels=True, fail_fast=True)
        self.assertEqual(mock_log_debug.call_count, 5)
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeSecurityLevel._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_security_level_validation__is_successful_when_check_level_is_true(self, mock_log_debug,
                                                                                    mock_get_number_of_workflows, *_):
        response_workflows = self.user.get.return_value
        response_workflows.iter_lines.return_value = [u'Total num. [0] ']
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = [[u'Command Executed Successfully'],
                                           [u'Node Name \tNode Security Level', u'netsim_LTE01ERBS00001\tlevel 1',
                                            u'netsim_LTE01ERBS00002\tlevel 1', u'netsim_LTE01ERBS00003\tlevel 1', u'',
                                            u'Command Executed Successfully']]
        self.security_level.start_time = datetime.now()
        mock_get_number_of_workflows.side_effect = [0]
        self.security_level.validate(self.nodes, check_levels=True, fail_fast=True)
        self.assertEqual(mock_log_debug.call_count, 6)
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeSecurityLevel._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_security_level_validation__raises_validation_error_if_unsuccessful(self, mock_log_debug,
                                                                                     mock_get_number_of_workflows, *_):
        response_workflows = self.user.get.return_value
        response_workflows.iter_lines.return_value = [u'Total num. [0] ']
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = [[u'Command Executed Successfully'],
                                           [u'Node Name \tNode Security Level', u'netsim_LTE01ERBS00001\tlevel 0',
                                            u'netsim_LTE01ERBS00002\tlevel 1', u'netsim_LTE01ERBS00003\tlevel 1', u'',
                                            u'Command Executed Successfully']]
        self.security_level.start_time = datetime.now()
        mock_get_number_of_workflows.side_effect = [0]
        self.assertRaises(ValidationError, self.security_level.validate, self.nodes, check_levels=True, fail_fast=True)
        self.assertEqual(mock_log_debug.call_count, 5)
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeSecurityLevel._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_security_level_validation__if_check_workflows_false(self, mock_log_debug,
                                                                      mock_get_number_of_workflows, *_):
        response = self.user.get.return_value
        response.iter_lines.side_effect = [[u'Total num. [0] '], [u'Total num. [1] ']]
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Node Name \tNode Security Level', u'netsim_LTE01ERBS00001\tlevel 0',
                                            u'netsim_LTE01ERBS00002\tlevel 1', u'netsim_LTE01ERBS00003\tlevel 1', u'',
                                            u'Command Executed Successfully']
        mock_get_number_of_workflows.side_effect = [0, 1]
        self.security_level.start_time = datetime.now()
        self.security_level.verify_timeout = 0.001
        self.assertRaises(TimeOutError, self.security_level.validate, self.nodes, check_levels=True)
        self.assertTrue(mock_log_debug.called)
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeSecurityLevel._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_node_security_level_validation__if_polling_time_is_expired(self, mock_log_debug,
                                                                        mock_get_number_of_workflows, *_):
        response_workflows = self.user.get.return_value
        response_workflows.iter_lines.return_value = [u'Total num. [1] ']
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Node Name \tNode Security Level', u'netsim_LTE01ERBS00001\tlevel 0',
                                            u'netsim_LTE01ERBS00002\tlevel 1', u'netsim_LTE01ERBS00003\tlevel 1', u'',
                                            u'Command Executed Successfully']
        mock_get_number_of_workflows.side_effect = [1, 1, 0]
        self.security_level.start_time = datetime.now()
        self.security_level.verify_timeout = 30
        self.security_level.validate(self.nodes, check_levels=False)
        self.assertTrue(mock_log_debug.called)
        self.assertEqual(mock_get_number_of_workflows.call_count, 3)

    def test_tear_down_is_successful(self):
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Following is the list of algorithm(s) available in the system',
              u'SHA1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'', u'Command Executed Successfully'],
             [u'Security level change initiated']]
        self.security_level._teardown()

    def test_tear_down_fails(self):
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Following is the list of algorithm(s) available in the system',
              u'SHA1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'', u'Command Executed Successfully'],
             [u'Error 10007 : The NetworkElement MO does not exist for the associated MeContext MO',
              u'Suggested Solution : Please create the NetworkElement MO and any other required MOs '
              u'or the associated MeContext MO.'], [u'']]
        self.security_level._teardown()


class NodeCredentialsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.nodes = Mock()
        self.nodes.node_id = "LTE07"
        self.nodes.primary_type = "ERBS"
        self.nodes._persist.return_value = None
        self.nodes.SET_NODE_SECURITY_CMD = "execute"
        self.nodes.UPDATE_NODE_SECURITY_CMD = "execute"
        self.nodes.secure_user = self.nodes.secure_password = "level"
        self.nodes.normal_user = self.nodes.normal_password = "level"
        self.mock_user = Mock()
        self.response = Mock()
        self.response.get_output.return_value = ['blah']
        self.mock_user.enm_execute.return_value = self.response
        self.node_credentials = NodeCredentials([self.nodes], user=self.mock_user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.node_security.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.node_security.persist_node')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_create__in_node_credentials_is_successful(self, mock_log_debug, *_):
        response = self.mock_user.enm_execute.return_value
        response.get_output.return_value = [u'All credentials were created successfully']
        self.node_credentials.create("secure_user", "secure_password", "normal_user", "normal_password")
        self.assertTrue(mock_log_debug.called)

    def test_update_raises_runtime_error(self):
        self.node_credentials._attribute_list_default = []
        self.assertRaises(RuntimeError, self.node_credentials.update, "a", "b", "c", "d")

    @patch('enmutils.lib.log.logger.debug')
    def test_update_is_successful(self, mock_log_debug):
        response = self.mock_user.enm_execute.return_value
        response.get_output.return_value = [u'All credentials updated successfully']
        self.node_credentials._attribute_list_default = ['secure_user', 'secure_password', 'normal_user',
                                                         'normal_password', 'secure_level']
        self.node_credentials.update()
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_remove_is_successful(self, mock_log_debug):
        response = self.mock_user.enm_execute.return_value
        response.get_output.return_value = [u'13 instance(s) deleted']
        self.node_credentials.remove()
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_restore_is_successful(self, mock_log_debug):
        response = self.mock_user.enm_execute.return_value
        response.get_output.return_value = [u'All credentials updated successfully']
        self.node_credentials.restore()
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.node_security.node_pool_mgr.mutex')
    def test_modify_raises_on_create(self, _):
        self.node_credentials._modify_cmd = self.node_credentials.credentials_create_cmd
        self.node_credentials._modify_verification = self.node_credentials.CREATED_VERIFICATION
        self.assertRaises(ScriptEngineResponseValidationError, self.node_credentials._modify, "create")

    @patch('enmutils_int.lib.node_security.node_pool_mgr.mutex')
    def test_modify_raises_on_update(self, _):
        self.node_credentials._modify_cmd = self.node_credentials.credentials_update_cmd
        self.node_credentials._modify_verification = self.node_credentials.UPDATED_VERIFICATION
        self.assertRaises(ScriptEngineResponseValidationError, self.node_credentials._modify, "update")

    @patch('enmutils_int.lib.node_security.node_pool_mgr.mutex')
    def test_modify_raises_on_create_remove(self, _):
        self.node_credentials._modify_cmd = self.node_credentials.credentials_remove_cmd
        self.node_credentials._modify_verification = self.node_credentials.REMOVED_VERIFICATION
        self.assertRaises(ScriptEngineResponseValidationError, self.node_credentials._modify, "remove")

    @patch('enmutils_int.lib.node_security.persist_node')
    @patch('enmutils_int.lib.node_security.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_modify_permanent_flag__is_successful_if_no_services_used(self, mock_log_debug, *_):
        response = self.mock_user.enm_execute.return_value
        response.get_output.return_value = [self.node_credentials.CREATED_VERIFICATION]
        self.node_credentials.user = self.mock_user
        self.node_credentials._modify_cmd = self.node_credentials.credentials_create_cmd
        self.node_credentials._modify_verification = self.node_credentials.CREATED_VERIFICATION
        self.node_credentials._modify("create", permanent=True)
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.node_security.time.sleep')
    def test_get_credentials_raises_script_engine_error(self, mock_sleep):
        nodes = [Mock(), Mock()]
        nodes[0].primary_type = "ERBS"
        nodes[1].primary_type = "RadioNode"
        self.node_credentials = NodeCredentials(nodes, user=self.mock_user)
        response_output = (u'Error 10004 : The NetworkElement specified does not exist '
                           u'Suggested Solution : Please specify a valid NetworkElement '
                           u'that exists in the system.')
        self.response.get_output.side_effect = [response_output, response_output]
        mock_profile = Mock()
        self.node_credentials.get_credentials_with_delay(mock_profile)
        self.assertEqual(mock_profile.add_error_as_exception.call_count, 2)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.node_security.time.sleep')
    def test_get_credentials_waits_between_nodes(self, mock_sleep):
        self.response.get_output.return_value = [u'Command Executed Successfully.']
        self.node_credentials.get_credentials_with_delay(profile=Mock())
        self.assertTrue(mock_sleep.called)

    def test_get_node_security_commands_based_on_node_type_if_node_type_is_RadioNode(self):
        nodes = [Mock()]
        nodes[0].primary_type = "RadioNode"
        self.node_credentials = NodeCredentials(nodes, user=self.mock_user)
        credentials_create_cmd = ('secadm credentials create --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"')
        credentials_update_cmd = ('secadm credentials update --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"')
        self.assertEqual(self.node_credentials.credentials_create_cmd, credentials_create_cmd)
        self.assertEqual(self.node_credentials.credentials_update_cmd, credentials_update_cmd)

    def test_get_node_security_commands_based_on_node_type_if_node_type_is_empty(self):
        nodes = [Mock()]
        nodes[0].primary_type = ""
        self.node_credentials = NodeCredentials(nodes, user=self.mock_user)
        self.assertEqual(self.node_credentials.credentials_create_cmd, "")
        self.assertEqual(self.node_credentials.credentials_update_cmd, "")


class FTPESUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.nodes = [Mock(), Mock()]
        self.user = Mock()
        self.job_id = 'TestId'
        self.ftpes = FTPES(self.user, nodes=self.nodes)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_activate_ftpes_on_nodes__is_successful(self, mock_debug):
        nodes = ['DG2', 'DG2']
        response = Mock()
        response.get_output.return_value = [u' \'secadm job get -j jobid\'']
        self.user.enm_execute.return_value = response
        self.ftpes.activate_ftpes_on_nodes(nodes)
        self.assertEqual(mock_debug.call_count, 2)
        mock_debug.assert_called_with('Successfully activated FTPES with Job ID: jobid')

    def test_activate_ftpes_on_nodes__raises_error(self):
        nodes = ['DG2', 'DG2']
        response = Mock()
        response.get_output.return_value = Exception
        self.user.enm_execute.return_value = response
        with self.assertRaises(EnmApplicationError):
            self.ftpes.activate_ftpes_on_nodes(nodes)

    def test_get_ftpes_status__is_successful(self):
        self.ftpes.get_ftpes_status(self.nodes)
        self.assertEqual(self.user.enm_execute.call_count, 1)

    def test_get_ftpes_status__raises_error(self):
        self.user.enm_execute.side_effect = Exception
        with self.assertRaises(EnmApplicationError):
            self.ftpes.get_ftpes_status(self.nodes)

    @patch('enmutils_int.lib.node_security.FmManagement')
    def test_enable_fm_supervsion_on_nodes_for_ftpes_activation__is_successful(self, mock_fm_management, *_):
        self.ftpes.enable_fm_supervsion_on_nodes_for_ftpes_activation(self.nodes)
        self.assertEqual(mock_fm_management.call_count, 1)

    @patch('enmutils_int.lib.node_security.FmManagement')
    @patch('enmutils_int.lib.node_security.FmManagement.supervise', side_effect="Error")
    def test_enable_fm_supervsion_on_nodes_for_ftpes_activation__raises_error(self, *_):
        self.ftpes.enable_fm_supervsion_on_nodes_for_ftpes_activation(self.nodes)
        self.assertRaises(EnvironError)

    @patch('enmutils_int.lib.node_security.FmManagement', side_effect=Exception)
    def test_enable_fm_supervsion_on_nodes_for_ftpes_activation__raises_environ_error(self, _):
        self.assertRaises(EnvironError, self.ftpes.enable_fm_supervsion_on_nodes_for_ftpes_activation, self.nodes)

    @patch("enmutils_int.lib.node_security.re.compile")
    @patch('enmutils_int.lib.node_security.FTPES.activate_ftpes_on_nodes')
    @patch('enmutils_int.lib.node_security.FTPES.get_ftpes_status')
    def test_check_ftpes_are_enabled_on_nodes_and_enable__doesnt_activate_when_fptes_are_enabled(self,
                                                                                                 mock_get_ftpes_status,
                                                                                                 mock_activate_ftpes,
                                                                                                 mock_compile):
        mock_get_ftpes_status.return_value = ['ON', 'ON', 'ON']
        mock_compile.return_value.search.return_value = False
        self.ftpes.check_ftpes_are_enabled_on_nodes_and_enable()
        self.assertEqual(mock_activate_ftpes.call_count, 0)

    @patch('enmutils_int.lib.node_security.time.sleep')
    @patch('enmutils_int.lib.node_security.FTPES.activate_ftpes_on_nodes')
    @patch('enmutils_int.lib.node_security.FTPES.enable_fm_supervsion_on_nodes_for_ftpes_activation')
    @patch('enmutils_int.lib.node_security.FTPES.get_ftpes_status')
    @patch("re.compile")
    def test_check_ftpes_are_enabled_on_nodes_and_enable__when_status_returns_off_is_successful(self,
                                                                                                mock_compile,
                                                                                                mock_get_ftpes_status,
                                                                                                mock_enable_fm_super,
                                                                                                mock_activate_ftpes, _):
        mock_get_ftpes_status.return_value = ['OFF', 'ON']
        mock_compile.return_value.search.return_value = None
        self.ftpes.check_ftpes_are_enabled_on_nodes_and_enable()
        self.assertEqual(mock_activate_ftpes.call_count, 1)
        self.assertEqual(mock_enable_fm_super.call_count, 1)

    @patch('enmutils_int.lib.node_security.time.sleep')
    @patch('enmutils_int.lib.node_security.FTPES.activate_ftpes_on_nodes')
    @patch('enmutils_int.lib.node_security.FTPES.enable_fm_supervsion_on_nodes_for_ftpes_activation')
    @patch('enmutils_int.lib.node_security.FTPES.get_ftpes_status')
    @patch("enmutils_int.lib.node_security.re.compile")
    def test_check_ftpes_are_enabled_on_nodes_and_enable__doesnt_enable_fm_on_teardown_successful(self,
                                                                                                  mock_compile,
                                                                                                  mock_get_ftpes_status,
                                                                                                  mock_enable_fm_super,
                                                                                                  mock_activate_ftpes,
                                                                                                  _):
        mock_get_ftpes_status.return_value = ['OFF', 'ON']
        mock_compile.return_value.search.return_value = None
        self.ftpes.check_ftpes_are_enabled_on_nodes_and_enable(teardown=True)
        self.assertEqual(mock_activate_ftpes.call_count, 1)
        self.assertEqual(mock_enable_fm_super.call_count, 0)

    @patch('enmutils_int.lib.node_security.time.sleep')
    @patch('enmutils_int.lib.node_security.FTPES.activate_ftpes_on_nodes')
    @patch('enmutils_int.lib.node_security.FTPES.enable_fm_supervsion_on_nodes_for_ftpes_activation')
    @patch('enmutils_int.lib.node_security.FTPES.get_ftpes_status')
    @patch("enmutils_int.lib.node_security.re.compile")
    def test_check_ftpes_are_enabled_on_nodes_and_enable__raises_exception_when_fptes_status_is_off(self,
                                                                                                    mock_compile,
                                                                                                    mock_get_ftpes_stat,
                                                                                                    *_):
        mock_get_ftpes_stat.return_value = ['OFF', 'OFF']
        mock_compile.return_value.search.return_value = None
        with self.assertRaises(Exception):
            self.ftpes.check_ftpes_are_enabled_on_nodes_and_enable()


class NodeSSHKeyUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        nodes = Mock()
        self.user = Mock()
        nodes.node_id = "LTE07"
        self.node_key = NodeSSHKey([nodes], user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_validate_algorithm_is_in_algorithm_list(self):
        self.node_key._validate_algorithm("RSA_2048")

    def test_validate_algorithm_raises(self):
        self.assertRaises(RuntimeError, self.node_key._validate_algorithm, "doesnt_exist")

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_create_is_successful(self, mock_log_debug):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Sshkey create command executed']
        self.node_key.create()
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_update_is_successful(self, mock_log_debug):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Sshkey update command executed"']
        self.node_key.update()
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_delete_is_successful(self, mock_log_debug):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'12 instance(s) updated']
        self.node_key.delete()
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_modify_is_successful(self, mock_log_debug):
        self.node_key._modify_cmd = "{node_id} {algorithm}"
        self.node_key._modify_verification = "search pattern"
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'search pattern']
        self.node_key._modify('cmd')
        self.assertTrue(mock_log_debug.called)

    def test_modify_raises_validation_error(self,):
        self.node_key._modify_cmd = "{node_id} {algorithm}"
        self.node_key._modify_verification = "script"
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'search pattern']
        self.assertRaises(ScriptEngineResponseValidationError, self.node_key._modify, "doesnt_exist")


class NodeCertificateUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.nodes = [Mock() for _ in range(3)]
        self.nodes[0].node_id = 'netsim_LTE01ERBS00001'
        self.nodes[1].node_id = 'netsim_LTE01ERBS00002'
        self.nodes[2].node_id = 'netsim_LTE01ERBS00003'
        self.mock_user = Mock()
        config = SecurityConfig()
        self.node_cert = NodeCertificate(nodes=self.nodes, security_config=config, user=self.mock_user)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_certificate_status__is_successful(self):
        response = self.mock_user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Dynamic errors:\t\t\t\t\t\t', u'Node Name\tError Code\tError Message\t\t\t\t',
              u'NetworkElement=ieatnetsimv6018-15_LTE07\t10005\tThe node specified is not synchronized\t\t\t\t',
              u'', u'Command Executed Successfully'],
             [u'Node Name\tEnroll State\tSerial Number\tone\ttwo\tthree\tfour',
              u'NetworkElement=LTE07\tenrolled\tLx7lkajs\t\t\t\t']]
        self.assertEqual(self.node_cert._get_certificate_status(["LTE07"]), {'LTE07': ("enrolled", "Lx7lkajs")})

    def test_get_certificate_status__raises(self):
        response = self.mock_user.enm_execute.return_value
        response.get_output.return_value = ['blah']
        self.assertRaises(ScriptEngineResponseValidationError, self.node_cert._get_certificate_status, ["LTE07"])

    def test_get_certificate_status__is_successful_with_invalid_entries(self):
        response = self.mock_user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Dynamic errors:\t\t\t\t\t\t', u'Node Name\tError Code\tError Message\t\t\t\t',
              u'NetworkElement=ieatnetsimv6018-15_LTE07\t10005\tThe node specified is not synchronized\t\t\t\t',
              u'', u'Command Executed Successfully'],
             [u'Node Name\tEnroll State\tSerial Number\tone\ttwo\tthree\tfour\tfive',
              u'NetworkElement=LTE07\tenrolled\tLx7lkajs\t\t\t\t\t']]
        self.assertEqual(self.node_cert._get_certificate_status(["LTE07"]), {})

    def test_check_certificates__is_successful(self):
        response = self.mock_user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Command Executed Successfully'],
             [u'Node Name\tEnroll State\tSerial Number\tone\ttwo\tthree\tfour',
              u'NetworkElement=netsim_LTE01ERBS00001\tenrolled\t7890\t\t\t\t',
              u'NetworkElement=netsim_LTE01ERBS00002\tenrolled\t1234\t\t\t\t',
              u'NetworkElement=netsim_LTE01ERBS00003\tenrolled\t4567\t\t\t\t']]
        self.node_cert.cert_prev_status = \
            {'netsim_LTE01ERBS00001': ('enrolled', "7899"), 'netsim_LTE01ERBS00002': ('enrolled', '1234'),
             'netsim_LTE01ERBS00003': ('enrolled', '4567')}
        nodes_list = ['netsim_LTE01ERBS00001', 'netsim_LTE01ERBS00002', 'netsim_LTE01ERBS00003']
        self.node_cert._check_certificates(nodes_list=nodes_list)
        self.assertEqual(len(nodes_list), 2)

    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.NodeSecurity._enable_algorithm')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_issue__is_successful(self, mock_log_debug, *_):
        response = self.mock_user.enm_execute.return_value
        response.get_output.return_value = ["Successfully started a job to issue certificates for nodes.Perform "
                                            "'secadm job get -j 300659b2-9b5e-4ac2-86a0-ff48a90d794a' to get progress "
                                            "info"]
        self.node_cert.issue(profile_name="NODESEC_11", selected_nodes=self.nodes)
        self.assertTrue(mock_log_debug.called)

    def test_issue__raises_validation_error(self):
        response = self.mock_user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Following is the list of algorithm(s) available in the system',
              u'SHA1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'', u'Command Executed Successfully'],
             [u'Command Executed Successfully'],
             [u'Node Name\tEnroll State\tSerial Number\tone\ttwo\tthree\tfour',
              u'NetworkElement=netsim_LTE01ERBS00001\tenrolled\t7890\t\t\t\t',
              u'NetworkElement=netsim_LTE01ERBS00002\tenrolled\t7891\t\t\t\t',
              u'NetworkElement=netsim_LTE01ERBS00003\tenrolled\t7892\t\t\t\t',
              u'NetworkElement=netsim_LTE01ERBS00003\tenrolled\t7892\t\t\t\t\t'
              u'Command Executed Successfully'],
             [u'blah'], [u'blah']]
        self.assertRaises(ScriptEngineResponseValidationError, self.node_cert.issue, profile_name="NODESEC_11",
                          selected_nodes=self.nodes)

    @patch('enmutils_int.lib.node_security.check_job_status')
    @patch('enmutils_int.lib.node_security.NodeSecurity._enable_algorithm')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_reissue__is_successful(self, mock_log_debug, *_):
        response = self.mock_user.enm_execute.return_value
        response.get_output.return_value = ["Successfully started a job to reissue certificates for nodes.Perform "
                                            "'secadm job get -j 300659b2-9b5e-4ac2-86a0-ff48a90d794a' to get progress "
                                            "info"]
        self.node_cert.reissue(selected_nodes=self.nodes)
        self.assertTrue(mock_log_debug.called)

    def test_reissue__raises_validation_error(self):
        response = self.mock_user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Following is the list of algorithm(s) available in the system',
              u'SHA1\tMESSAGE_DIGEST_ALGORITHM\t-\tenabled',
              u'', u'Command Executed Successfully'],
             [u'Command Executed Successfully'],
             [u'Node Name\tEnroll State\tSerial Number\tone\ttwo\tthree\tfour',
              u'NetworkElement=netsim_LTE01ERBS00001\tenrolled\t7890\t\t\t\t',
              u'NetworkElement=netsim_LTE01ERBS00002\tenrolled\t7891\t\t\t\t',
              u'NetworkElement=netsim_LTE01ERBS00003\tenrolled\t7892\t\t\t\t',
              u'NetworkElement=netsim_LTE01ERBS00003\tenrolled\t7892\t\t\t\t\t'
              u'Command Executed Successfully'],
             [u'blah'], [u'blah']]
        self.assertRaises(ScriptEngineResponseValidationError, self.node_cert.reissue, selected_nodes=self.nodes)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeCertificate._check_certificates')
    @patch('enmutils_int.lib.node_security.NodeCertificate._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_validate__raises_timeout_error(self, mock_log_debug, mock_get_number_of_workflows,
                                            mock_check_certificates, *_):
        self.node_cert.start_time = datetime.now()
        self.node_cert.verify_timeout = 0
        self.node_cert.cert_prev_status = {'sdjskdj': ''}
        self.assertRaises(TimeOutError, self.node_cert.validate)
        self.assertFalse(mock_log_debug.called)
        self.assertFalse(mock_get_number_of_workflows.called)
        self.assertFalse(mock_check_certificates.called)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeCertificate._check_certificates')
    @patch('enmutils_int.lib.node_security.NodeCertificate._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_validate__is_successful_check_workflows_true(self, mock_log_debug, mock_get_number_of_workflows,
                                                          mock_check_certificates, *_):
        response_workflows = self.mock_user.get.return_value
        response_workflows.iter_lines.return_value = [u'Total num. [0] ']
        mock_get_number_of_workflows.return_value = 0
        response = self.mock_user.enm_execute.return_value
        response.get_output.side_effect = [[u'Command Executed Successfully'], [u'Command Executed Successfully']]
        self.node_cert.verify_timeout = 20
        self.node_cert.cert_prev_status = {}
        self.node_cert.start_time = datetime.now()

        self.node_cert.validate()
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)
        self.assertEqual(mock_log_debug.call_count, 3)
        self.assertEqual(mock_check_certificates.call_count, 1)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeCertificate._check_certificates')
    @patch('enmutils_int.lib.node_security.NodeCertificate._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_validate__raises_validation_error(self, mock_log_debug, mock_get_number_of_workflows,
                                               mock_check_certificates, *_):
        self.node_cert.verify_timeout = 20
        self.node_cert.start_time = datetime.now()
        self.node_cert.cert_prev_status = {'sadfshdfjh': ('enrolled', 'Lx7lkdajs')}
        mock_get_number_of_workflows.return_value = 0
        self.assertRaises(ValidationError, self.node_cert.validate, fail_fast=True)
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)
        self.assertEqual(mock_log_debug.call_count, 2)
        self.assertEqual(mock_check_certificates.call_count, 1)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeCertificate._check_certificates')
    @patch('enmutils_int.lib.node_security.NodeCertificate._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_validate__is_successful_when_check_certs_is_false(self, mock_log_debug, mock_get_number_of_workflows,
                                                               mock_check_certificates, *_):
        response_workflows = self.mock_user.get.return_value
        response_workflows.iter_lines.return_value = [u'Total num. [0] ']
        mock_get_number_of_workflows.return_value = 0
        response = self.mock_user.enm_execute.return_value
        response.get_output.side_effect = [[u'Command Executed Successfully'], [u'Command Executed Successfully']]
        self.node_cert.start_time = datetime.now()
        self.node_cert.verify_timeout = 10
        self.node_cert.cert_prev_status = {'netsim_LTE01ERBS00001': ('enrolled', "7899"),
                                           'netsim_LTE01ERBS00002': ('enrolled', '1234'),
                                           'netsim_LTE01ERBS00003': ('enrolled', '4567')}

        self.node_cert.validate(check_certificates=False)
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)
        self.assertEqual(mock_log_debug.call_count, 3)
        self.assertEqual(mock_check_certificates.call_count, 0)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeCertificate._check_certificates')
    @patch('enmutils_int.lib.node_security.NodeCertificate._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_validate__if_polling_time_is_expired(self, mock_log_debug, mock_get_number_of_workflows,
                                                  mock_check_certificates, *_):
        response_workflows = self.mock_user.get.return_value
        response_workflows.iter_lines.return_value = [u'Total num. [1] ']
        mock_get_number_of_workflows.side_effect = [1, 1, 0]
        response = self.mock_user.enm_execute.return_value
        response.get_output.side_effect = [[u'Command Executed Successfully'], [u'Command Executed Successfully']]
        self.node_cert.start_time = datetime.now()
        self.node_cert.verify_timeout = 20
        self.node_cert.cert_prev_status = {'netsim_LTE01ERBS00001': ('enrolled', "7899"),
                                           'netsim_LTE01ERBS00002': ('enrolled', '1234'),
                                           'netsim_LTE01ERBS00003': ('enrolled', '4567')}

        self.node_cert.validate(check_certificates=False)
        self.assertEqual(mock_get_number_of_workflows.call_count, 3)
        self.assertEqual(mock_log_debug.call_count, 9)
        self.assertEqual(mock_check_certificates.call_count, 0)

    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeCertificate._check_certificates')
    @patch('enmutils_int.lib.node_security.NodeCertificate._get_number_of_workflows')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test__validate_is_successful_when_check_certs_is_true(self, mock_log_debug, mock_get_number_of_workflows,
                                                              mock_check_certificates, *_):
        response_workflows = self.mock_user.get.return_value
        response_workflows.iter_lines.return_value = [u'Total num. [0] ']
        mock_get_number_of_workflows.side_effect = [0, 1]
        response = self.mock_user.enm_execute.return_value
        response.get_output.side_effect = [[u'Command Executed Successfully'], [u'Command Executed Successfully']]
        self.node_cert.start_time = datetime.now()
        self.node_cert.verify_timeout = 0.001
        self.node_cert.cert_prev_status = {'netsim_LTE01ERBS00001': ('enrolled', "7899"),
                                           'netsim_LTE01ERBS00002': ('enrolled', '1234'),
                                           'netsim_LTE01ERBS00003': ('enrolled', '4567')}

        self.assertRaises(TimeOutError, self.node_cert.validate)
        self.assertEqual(mock_get_number_of_workflows.call_count, 1)
        self.assertTrue(mock_log_debug.called)
        self.assertTrue(mock_check_certificates.called)

    @patch('enmutils_int.lib.node_security.log.logger.debug')
    @patch('enmutils_int.lib.node_security.time.sleep', return_value=0)
    @patch('enmutils_int.lib.node_security.NodeCertificate._check_certificates')
    @patch('enmutils_int.lib.node_security.NodeCertificate._get_number_of_workflows')
    def test_node_certificate_validation__if_check_workflows_false(self, mock_get_number_of_workflows, *_):
        self.node_cert.start_time = datetime.now()
        self.node_cert.verify_timeout = 0.1
        self.node_cert.cert_prev_status = {"test": "status"}
        mock_get_number_of_workflows.side_effect = [0, 1]
        self.assertRaises(TimeOutError, self.node_cert.validate)


class NodeSNMPUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.node_snmp = ''
        self.create_connectivity_info_kwargs = {'snmp_version': 'SNMP_V3',
                                                'node_id': 'LTE04dg2ERBS00001',
                                                'snmp_security_level': 'AUTH_PRIV',
                                                'snmp_security_name': 'sampleuser'}
        self.set_snmp_cmd_kwargs = {'priv_password': 'privpass', 'node_id': 'LTE04dg2ERBS00001',
                                    'auth_password': 'authpass', 'auth_algo': 'MD5', 'priv_algo': 'DES'}
        self.SET_SNMP_CMD = ('secadm snmp authpriv --auth_algo {auth_algo} --auth_password "{auth_password}" --priv_algo {priv_algo} --priv_password "{priv_password}" -n "{node_id}"')
        self.SET_SNMP_CONNECTIVITY_INFO_CMD = ('cmedit set "{node_id}" "{connectivity_information}" snmpVersion="{snmp_version}", snmpSecurityLevel="{snmp_security_level}", snmpSecurityName="{snmp_security_name}"')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.node_security.config.set_prop')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_set_snmp_is_successful(self, mock_log_debug, _):
        nodes = Mock()
        nodes.node_id = "LTE04dg2ERBS00001"
        nodes.primary_type = "RadioNode"
        nodes.create_connectivity_cmd.return_value = None
        self.node_snmp = NodeSNMP(nodes=[nodes], user=self.user)
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = [[u'Snmp Authpriv Command OK'], [u'1 instance(s) updated']]
        self.node_snmp.set_version('SNMP_V3')
        self.assertEqual(mock_log_debug.call_count, 2)

    @patch('enmutils_int.lib.node_security.config.set_prop')
    @patch('enmutils_int.lib.node_security.log.logger.debug')
    def test_set_snmp_to_Router6675_nodes_are_successful(self, mock_log_debug, _):
        nodes = Mock()
        nodes.node_id = "CORE66Router667501"
        nodes.primary_type = "Router6675"
        self.create_connectivity_info_kwargs['node_id'] = nodes.node_id
        self.set_snmp_cmd_kwargs['node_id'] = nodes.node_id
        nodes.create_connectivity_cmd.return_value = None
        self.node_snmp = NodeSNMP(nodes=[nodes], user=self.user)
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = [[u'Snmp Authpriv Command OK'], [u'1 instance(s) updated']]
        self.node_snmp.set_version('SNMP_V3')
        self.assertEqual(mock_log_debug.call_count, 2)

    @patch('enmutils_int.lib.node_security.config.set_prop')
    def test_set_snmp_raises_validation_error_if_unsuccessful(self, _):
        nodes = Mock()
        nodes.node_id = "LTE04dg2ERBS00001"
        nodes.primary_type = "RadioNode"
        nodes.create_connectivity_cmd.return_value = None
        self.node_snmp = NodeSNMP(nodes=[nodes], user=self.user)
        response = self.user.enm_execute.return_value
        response.get_output.side_effect = \
            [[u'Snmp Authpriv Command OK'],
             [u'Error 10004 : The MO specified does not exist - NetworkElement=LTE04dg2ERBS00001'],
             [u'Error 10004 : The MO specified does not exist - NetworkElement=LTE04dg2ERBS00001']]
        self.assertRaises(ScriptEngineResponseValidationError, self.node_snmp.set_version, 'SNMP_V3')

    @patch('enmutils_int.lib.node_security.config.set_prop')
    def test_set_snmp_raises_validation_error_if_incorrect_parameter(self, _):
        nodes = Mock()
        nodes.node_id = "CORE66Router667501"
        nodes.primary_type = "Router6675"
        self.create_connectivity_info_kwargs['node_id'] = nodes.node_id
        self.set_snmp_cmd_kwargs['node_id'] = nodes.node_id
        nodes.create_connectivity_cmd.return_value = None
        self.node_snmp = NodeSNMP(nodes=[nodes], user=self.user)
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'Error 10091 : Invalid argument value']
        self.assertRaises(ScriptEngineResponseValidationError, self.node_snmp.set_version, 'SNMP_V4')


if __name__ == "__main__":
    unittest2.main(verbosity=2)
