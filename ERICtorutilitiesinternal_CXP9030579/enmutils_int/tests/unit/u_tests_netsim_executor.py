#!/usr/bin/env python
import os
import unittest2
from mock import patch, Mock
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils
import enmutils_int
from enmutils_int.lib import netsim_executor

ENMUTILS_INT_PATH = os.path.dirname(enmutils_int.__file__)


class NetsimExecutorUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    node_names = ["LTE05ERBS00005", "LTE05ERBS00006", "LTE05ERBS00007", "LTE05ERBS00008", "LTE05ERBS00009"]
    all_OK_response = {"LTE05ERBS00005": "OK", "LTE05ERBS00006": "OK", "LTE05ERBS00007": "OK", "LTE05ERBS00008": "OK", "LTE05ERBS00009": "OK"}

    # NE Commands
    start_already_in_progress_some_fail_response = ">> .start -parallel\n" \
        "Error starting NE(s)\n" \
        "LTE05ERBS00007: Start or stop already in progress\n" \
        "LTE05ERBS00008: Start or stop already in progress\n" \
        "LTE05ERBS00009: Start or stop already in progress\n" \
        "Please check section 15.4 in the System Administrator's Guide!\n"
    start_already_in_progress_some_fail_result = {"LTE05ERBS00005": "OK", "LTE05ERBS00006": "OK", "LTE05ERBS00007": "FAIL", "LTE05ERBS00008": "FAIL", "LTE05ERBS00009": "FAIL"}

    start_already_in_progress_different_fail_response = ">> .start -parallel\n" \
        ".stop -parallelError starting NE(s)\n" \
        "LTE05ERBS00005: Start or stop already in progress\n" \
        "LTE05ERBS00007: Problem when starting protocol (and internal error in error handling) iiop_prot on simulated NE LTE02ERBS00007:\n" \
        "   [{servicename,iiop},\n" \
        "{class,exit},\n"
    start_already_in_progress_different_fail_result = {"LTE05ERBS00005": "FAIL", "LTE05ERBS00006": "OK", "LTE05ERBS00007": "FAIL", "LTE05ERBS00008": "OK", "LTE05ERBS00009": "OK"}

    alarm_burst_cmd = "alarmburst:mode=temp,freq=1,num_alarms=20,loop=false,cause=1,severity=3,idle_time=0,clear_after_burst=true,id=500;"
    not_started_nodes_response = ">> .alarmburst:mode=temp,freq=1,num_alarms=20,loop=false,cause=1,severity=3,idle_time=0,clear_after_burst=true,id=500;\n" \
        "LTE05ERBS00005: Id: 1000\nOK\n\n" \
        "LTE05ERBS00006: Id: 1000\nOK\n\n" \
        "LTE05ERBS00007: Id: 1000\nOK\n\n" \
        "LTE05ERBS00009: Id: 1000\nOK\n\n" \
        "LTE05ERBS00008: Not started!\n"
    not_started_nodes_result = {"LTE05ERBS00005": "OK", "LTE05ERBS00006": "OK", "LTE05ERBS00007": "OK", "LTE05ERBS00008": "FAIL", "LTE05ERBS00009": "OK"}

    one_ok_in_all_fails_response = ">> .start -parallel\n" \
        "LTE05ERBS00005: Not started!\n\n" \
        "LTE05ERBS00006: Not started!\n\n" \
        "LTE05ERBS00007: Not started!\n\n" \
        "LTE05ERBS00009: Id: 1000\nOK\n\n" \
        "LTE05ERBS00008: Not started!\n"
    one_ok_in_all_fails_result = {"LTE05ERBS00005": "FAIL", "LTE05ERBS00006": "FAIL", "LTE05ERBS00007": "FAIL", "LTE05ERBS00008": "FAIL", "LTE05ERBS00009": "OK"}

    avc_command = 'avcburst:id=7, num_events=3, freq=3, mode=persistent, idle_time=0, avcdata = \"[ {\\\"ManagedElement=1\\\",[{\\\"userLabel\\\",\\\"ABC\\\"}]},{\\\"ManagedElement=1\\\",[{\\\"userLabel\\\",\\\"DEF\\\"}]},{\\\"ManagedElement=1\\\",[{\\\"userLabel\\\",\\\"GHI\\\"}]} ]\", loop=false;'
    avc_burst_ok_response = '>> avcburst:id=7, num_events=3, freq=3, mode=persistent, idle_time=0, avcdata = "[ ' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"ABC\"}]},' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"DEF\"}]},' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"GHI\"}]}' \
        ' ]";\nId: 7\nOK\n\n'
    avc_burst_ok_result = all_OK_response

    avc_burst_only_some_nodes_started_response = '>> avcburst:id=7, num_events=3, freq=3, mode=persistent, idle_time=0, avcdata = "[ ' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"ABC\"}]},' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"DEF\"}]},' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"GHI\"}]}' \
        ' ]";\nLTE05ERBS00005: Id: 7\nOK\n\nLTE05ERBS00006: Id: 7\nOK\n\n' \
        'LTE05ERBS00007: Not started!\n\n' \
        'LTE05ERBS00008: Id: 7\nOK\n\nLTE05ERBS00009: Id: 7\nOK\n\n'
    avc_burst_only_some_nodes_started_result = {"LTE05ERBS00005": "OK", "LTE05ERBS00006": "OK", "LTE05ERBS00007": "FAIL", "LTE05ERBS00008": "OK", "LTE05ERBS00009": "OK"}

    avc_burst_some_nodes_have_bursts_response = '>> avcburst:id=7, num_events=3, freq=3, mode=persistent, idle_time=0, avcdata = "[ ' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"ABC\"}]},' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"DEF\"}]},' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"GHI\"}]}' \
        ' ]";\nLTE05ERBS00008: Id: 7\nOK\n\nLTE05ERBS00009: Id: 7\nOK\n\n' \
        'LTE05ERBS00005: Error {id_already_in_use,7}\n\n' \
        'LTE05ERBS00006: Error {id_already_in_use,7}\n\nLTE05ERBS00007: Error {id_already_in_use,7}\n\n'
    avc_burst_some_nodes_have_bursts_result = {"LTE05ERBS00005": "FAIL", "LTE05ERBS00006": "FAIL", "LTE05ERBS00007": "FAIL", "LTE05ERBS00008": "OK", "LTE05ERBS00009": "OK"}

    avc_burst_all_nodes_have_bursts_response = '>> avcburst:id=7, num_events=3, freq=3, mode=persistent, idle_time=0, avcdata = "[ ' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"ABC\"}]},' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"DEF\"}]},' \
        '{\"ManagedElement=1,TransportNetwork=1,Scpt=1\",[{\"userLabel\",\"GHI\"}]}' \
        ' ]";\nError {id_already_in_use,7}\n\n'
    avc_burst_all_nodes_have_bursts_result = {"LTE05ERBS00005": "FAIL", "LTE05ERBS00006": "FAIL", "LTE05ERBS00007": "FAIL", "LTE05ERBS00008": "FAIL", "LTE05ERBS00009": "FAIL"}

    enable_pm_data_not_started_response = ">> .pmdata:enable;\n"  \
        "LTE05ERBS00007: OK\n\n" \
        "LTE05ERBS00008: OK\n\n" \
        "LTE05ERBS00005: Not started!\n\n" \
        "LTE05ERBS00006: OK\n\n" \
        "LTE05ERBS00009: OK\n"
    enable_pm_data_not_started_result = {"LTE05ERBS00005": "FAIL", "LTE05ERBS00006": "OK", "LTE05ERBS00007": "OK", "LTE05ERBS00008": "OK", "LTE05ERBS00009": "OK"}

    resume_pm_measurements_command = (
        "resumePMMeasurements Sftp://user:pass@ip_address/smrsroot/pm/sbg-is/CORE77SBG01/ 900 900")
    resume_pm_measurements_operation_succeeded_response = (
        ">> {0}\nOperationSucceeded\n\n".format(resume_pm_measurements_command))
    resume_pm_measurements_not_started_response = (
        ">> {0}\nNot started!\n\n".format(resume_pm_measurements_command))
    resume_pm_measurements_ok_result = {"CORE77SBG01": "OK"}
    resume_pm_measurements_fail_result = {"CORE77SBG01": "FAIL"}

    suspend_pm_measurements_command = "suspendPMMeasurements"
    suspend_pm_measurements_operation_succeeded_response = (
        ">> {0}\nOperationSucceeded\n\n".format(suspend_pm_measurements_command))
    suspend_pm_measurements_not_started_response = (
        ">> {0}\nNot started!\n\n".format(suspend_pm_measurements_command))
    suspend_pm_measurements_ok_result = {"CORE77SBG01": "OK"}
    suspend_pm_measurements_fail_result = {"CORE77SBG01": "FAIL"}

    enable_file_gen_set_ref_file_cmd = ".set addpmconn default stats enm_workload.STATS"
    enable_file_gen_set_ref_file_error_resp = '>> .set addpmconn default stats enm_workload.STATS\n' \
        'LTE05ERBS00005: OK\n' \
        'LTE05ERBS00006: OK\n' \
        'LTE05ERBS00007: Error {function_clause,\n' \
        '          [{simne,eval,\n' \
        '              [{error,{not_started,"NE not started"}},\n' \
        '               #Fun<set-addpmconn_simne.0.108345846>,infinity],\n' \
        '               [{file,"simne.erl"},{line,423}]},\n' \
        '          {\'set-addpmconn_simne\', insert_defaut_connection,4,\n' \
        '              etc...\n' \
        'LTE05ERBS00008: OK\n' \
        'LTE05ERBS00009: OK\n'
    enable_file_gen_set_ref_file_error_result = {"LTE05ERBS00005": "OK", "LTE05ERBS00006": "OK", "LTE05ERBS00007": "FAIL", "LTE05ERBS00008": "OK", "LTE05ERBS00009": "OK"}

    createmo_cmd = 'createmo:parentid="ManagedElement=1,ENodeBFunction=1,EUtraNetwork=1",type="ExternalENodeBFunction",name="CM_Sync_Load";'
    createmo_response = ' >> createmo:parentid="ManagedElement=1,ENodeBFunction=1,EUtraNetwork=1",type="ExternalENodeBFunction",name="CM_Sync_Load";\nOK'
    createmo_result = {"LTE05ERBS00005": "OK", "LTE05ERBS00006": "OK", "LTE05ERBS00007": "OK", "LTE05ERBS00008": "OK", "LTE05ERBS00009": "OK"}

    createmo_does_not_exist_response = '++++++++++++++++++++++++ ERROR! ++++++++++++++++++++++++\nAt least one of the NEs given as parameter does not exist\n++++++++++++++++++++++++ ERROR! ++++++++++++++++++++++++'
    createmo_does_not_exist_result = {"LTE05ERBS00005": "FAIL", "LTE05ERBS00006": "FAIL", "LTE05ERBS00007": "FAIL", "LTE05ERBS00008": "FAIL", "LTE05ERBS00009": "FAIL"}

    # Simulation Commands
    create_arne_cmd = '.createarne R12.2 LTEE1200-V2x160-RV-FDD-LTE05_fetcher NETSim %nename secret IP secure sites no_external_associations defaultgroups'
    create_arne_ok_response = ">> .createarne R12.2 LTEE1200-V2x160-RV-FDD-LTE05 fetcher NETSim %nename secret IP secure sites no_external_associations defaultgroups\n\n" \
        "XML generation finished in 4 s\n\nDTD validation result:\n\nstart parsing a grammar.\n\n" \
        "validating /netsim/netsimdir/exported_items/LTEE1200-V2x160-RV-FDD-LTE05_fetcher_create.xml\n\nthe document is valid.\n\nstart parsing a grammar.\n\n" \
        "validating /netsim/netsimdir/exported_items/LTEE1200-V2x160-RV-FDD-LTE05_fetcher_delete.xml\n\nthe document is valid.\n\n"
    create_arne_ok_result = {"LTEE1200-V2x160-RV-FDD-LTE05": "OK"}

    create_arne_fail_response = '>> .createarne R12.2 LTEE1200-V2x160-RV-FDD-LTE05 fetcher NETSim %nename secret IP secure sites no_external_associations defaultgroups\n\n' \
        'ERROR: {{case_clause,"R12.1"},\n' \
        '   [{arneversions,getDTD,1,[{file,"arneversions.erl"},{line,49}]},\n' \
        '   {createarnexml,getHeader,1,[{file,"createarnexml.erl"},{line,261}]},\n' \
        '   {createarnexml,create_xml_from_data,8,[{file,"createarnexml.erl"},{line,113}]},\n'
    create_arne_fail_result = {"LTEE1200-V2x160-RV-FDD-LTE05": "FAIL"}

    gen_ref_file_cmd = ".genreffilecpp lte enm_workload.STATS stats sizes no_value 50,150"
    gen_ref_file_ok_response = ">> .genreffilecpp lte enm_workload.STATS stats sizes no_value 50,150\nOK\n\n"
    gen_ref_file_ok_result = {"LTEE1200-V2x160-RV-FDD-LTE05": "OK"}

    gen_ref_file_already_exists_response = ">> .genreffilecpp lte enm_workload.STATS stats sizes no_value 50,150\nThe fileset name already exist\n\n"
    gen_ref_file_already_exists_result = {"LTEE1200-V2x160-RV-FDD-LTE05": "FAIL"}

    def _get_netsim_details(self):
        cmd = '.start -parallel'
        host = "netsimlin704.athtem.eei.ericsson.se"
        sim = "LTEE1200-V2x160-RV-FDD-LTE05"

        return cmd, host, sim

    # Tests
    @patch("enmutils_int.lib.netsim_executor.run_cmd")
    @ParameterizedTestCase.parameterize(
        ("run_cmd", "response_stdout", "expected_result"),
        [
            (".start -parallel", ">> .start -parallel\nOK\n", all_OK_response),
            (".start -parallel", start_already_in_progress_some_fail_response,
             start_already_in_progress_some_fail_result),
            (".start -parallel", start_already_in_progress_different_fail_response,
             start_already_in_progress_different_fail_result),
            (alarm_burst_cmd, not_started_nodes_response, not_started_nodes_result),
            (alarm_burst_cmd, one_ok_in_all_fails_response, one_ok_in_all_fails_result),
            (avc_command, avc_burst_ok_response, avc_burst_ok_result),
            (avc_command, avc_burst_only_some_nodes_started_response, avc_burst_only_some_nodes_started_result),
            (avc_command, avc_burst_some_nodes_have_bursts_response, avc_burst_some_nodes_have_bursts_result),
            (avc_command, avc_burst_all_nodes_have_bursts_response, avc_burst_all_nodes_have_bursts_result),
            (".pmdata:enable;", enable_pm_data_not_started_response, enable_pm_data_not_started_result),
            (enable_file_gen_set_ref_file_cmd, enable_file_gen_set_ref_file_error_resp,
             enable_file_gen_set_ref_file_error_result),
            (createmo_cmd, createmo_response, createmo_result),
            (createmo_cmd, createmo_does_not_exist_response, createmo_does_not_exist_result),
        ]
    )
    def test_run_ne_cmd_returns_correct_output_given_netsim_response(self, run_cmd, response_stdout, expected_result, mock_run_cmd):
        nodes = self.node_names
        _, host, sim = self._get_netsim_details()
        response = Mock()
        response.stdout = response_stdout
        mock_run_cmd.return_value = response
        self.assertEqual(expected_result, netsim_executor.run_ne_cmd(run_cmd, host, sim, nodes))

    @patch("enmutils_int.lib.netsim_executor.run_cmd")
    @ParameterizedTestCase.parameterize(
        ("run_cmd", "response_stdout", "expected_result"),
        [
            (resume_pm_measurements_command, resume_pm_measurements_operation_succeeded_response,
             resume_pm_measurements_ok_result),
            (resume_pm_measurements_command, resume_pm_measurements_not_started_response,
             resume_pm_measurements_fail_result),
        ]
    )
    def test_run_sim_cmd_returns_correct_output_for_resume_pm_measurements(self, run_cmd, response_stdout,
                                                                           expected_result, mock_run_cmd):
        _, host, sim = self._get_netsim_details()
        response = Mock()
        response.stdout = response_stdout
        mock_run_cmd.return_value = response
        self.assertEqual(expected_result, netsim_executor.run_ne_cmd(run_cmd, host, sim, ["CORE77SBG01"]))

    @patch("enmutils_int.lib.netsim_executor.run_cmd")
    @ParameterizedTestCase.parameterize(
        ("run_cmd", "response_stdout", "expected_result"),
        [
            (suspend_pm_measurements_command, suspend_pm_measurements_operation_succeeded_response,
             suspend_pm_measurements_ok_result),
            (suspend_pm_measurements_command, suspend_pm_measurements_not_started_response,
             suspend_pm_measurements_fail_result),
        ]
    )
    def test_run_sim_cmd_returns_correct_output_for_suspend_pm_measurements(self, run_cmd, response_stdout,
                                                                            expected_result, mock_run_cmd):
        _, host, sim = self._get_netsim_details()
        response = Mock()
        response.stdout = response_stdout
        mock_run_cmd.return_value = response
        self.assertEqual(expected_result, netsim_executor.run_ne_cmd(run_cmd, host, sim, ["CORE77SBG01"]))

    def test_parse_ne_response_returns_all_FAIL_when_rc_is_False(self):
        node_names = ['LTE05ERBS00013', 'LTE05ERBS00014']
        response = Mock()
        response.ok = False
        expected_result = {'all': 'FAIL'}
        self.assertEqual(expected_result, netsim_executor._parse_ne_response(response, node_names))

    def test_parse_ne_response_returns_all_OK_when_command_returns_ok_and_rc_is_True(self):
        node_names = ['LTE05ERBS00013', 'LTE05ERBS00014']
        response = Mock()
        response.stdout = "sample command\nId: 1000\nOK"
        response.rc = True
        expected_result = {'all': 'OK'}
        self.assertEqual(expected_result, netsim_executor._parse_ne_response(response, node_names))

    def test_parse_ne_response_returns_all_OK_when_command_returns_true_and_rc_is_True(self):
        node_names = ['LTE05ERBS00013', 'LTE05ERBS00014']
        response = Mock()
        response.stdout = "sample command\nId: 1000\ntrue"
        response.rc = True
        expected_result = {'all': 'OK'}
        self.assertEqual(expected_result, netsim_executor._parse_ne_response(response, node_names))

    @patch("enmutils_int.lib.netsim_executor._check_response_for_node_result")
    @patch("enmutils_int.lib.netsim_executor._prepare_response")
    @patch("enmutils_int.lib.netsim_executor.re")
    def test_parse_ne_response__returns_all_OK_when_pmdata_staus_command_returns_disabled(
            self, mock_re, mock__prepare_response, mock__check_response_for_node_result):
        node_names = ['CORE77SBG01']
        response = Mock()
        response.stdout = '>> pmdata:status;\ndisabled'
        response.rc = True
        mock__prepare_response.return_value = response.stdout
        mock_re.findall.return_value = ['disabled']
        expected_result = {'all': 'OK'}
        self.assertEqual(expected_result, netsim_executor._parse_ne_response(response, node_names))
        self.assertEqual(mock__check_response_for_node_result.call_count, 0)
        self.assertEqual(mock__prepare_response.call_count, 1)

    @patch("enmutils_int.lib.netsim_executor._check_response_for_node_result")
    @patch("enmutils_int.lib.netsim_executor._prepare_response")
    @patch("enmutils_int.lib.netsim_executor.re")
    def test_parse_ne_response__returns_all_OK_when_pmdata_staus_command_returns_enabled(
            self, mock_re, mock__prepare_response, mock__check_response_for_node_result):
        node_names = ['CORE77SBG01']
        response = Mock()
        response.stdout = '>> pmdata:status;\nenabled'
        response.rc = True
        mock__prepare_response.return_value = response.stdout
        mock_re.findall.return_value = ['enabled']
        expected_result = {'all': 'OK'}
        self.assertEqual(expected_result, netsim_executor._parse_ne_response(response, node_names))
        self.assertEqual(mock__check_response_for_node_result.call_count, 0)
        self.assertEqual(mock__prepare_response.call_count, 1)

    def test__check_response_for_node_result_returns_OK(self):
        response = Mock()
        response.stdout = "the document is valid hgdasfgfdocument is valid"
        resp_desc = '>> .set addpmconn default stats enm_workload.STATS \n' \
                    'LTE05ERBS0007: Error {function_clause,' \
                    '[{simne,eval,[{error,{not_started,"NE not started"}},' \
                    '[{file,"simne.erl"},{line,423}]},' \
                    '{\'set-addpmconn_simne\', insert_defaut_connection,4,etc... \n' \
                    'OK'
        result = netsim_executor._check_response_for_node_result("LTE05ERBS0007", resp_desc)
        self.assertEqual(result, 'OK')

    @patch("enmutils_int.lib.netsim_executor.re.sub")
    def test_prepare_response__returns_fail(self, mock_sub):
        node_names = None
        response = Mock()
        response.stdout = "Id: 234\nuxyznow"
        mock_sub.return_value = "uxyznow"
        self.assertEqual("uxyznow", netsim_executor._prepare_response(response, node_names))

    @patch("enmutils_int.lib.netsim_executor.persistence.has_key", return_value=False)
    @patch("enmutils_int.lib.netsim_executor.cache.has_key", return_value=False)
    @patch("enmutils_int.lib.netsim_executor.mutexer.mutex")
    @patch("enmutils_int.lib.netsim_executor.cache.set")
    @patch("enmutils_int.lib.netsim_executor.filesystem.get_remote_file_checksum", return_value=1)
    @patch("enmutils_int.lib.netsim_executor.filesystem.get_local_file_checksum", return_value=1)
    @patch("enmutils_int.lib.netsim_executor.filesystem.does_remote_file_exist", return_value=True)
    @patch("enmutils_int.lib.netsim_executor.persistence.set")
    @patch("enmutils_int.lib.netsim_executor.shell.run_remote_cmd")
    def test_run_cmd_without_the_executor_script_already_existing_on_the_host_deploys_the_script_successfully(
            self, mock_shell_run_remote_cmd, mock_persistence_set, *_):
        netsim_executor.run_cmd(".start -parallel", "netsimlin704")
        self.assertTrue(mock_persistence_set.called)
        self.assertTrue(mock_shell_run_remote_cmd.called)

    @patch("enmutils_int.lib.netsim_executor.filesystem.get_remote_file_checksum", return_value=0)
    @patch("enmutils_int.lib.netsim_executor.filesystem.get_local_file_checksum", return_value=1)
    @patch("enmutils_int.lib.netsim_executor.filesystem.does_remote_file_exist", side_effect=[False, False])
    def test_deploy_script_raisesRuntime_error_01(self, *_):
        self.assertRaises(RuntimeError, netsim_executor.deploy_script, "netsimlin704", "/tmp", "/tmp/command_executor.sh")

    @patch("enmutils_int.lib.netsim_executor.filesystem.get_remote_file_checksum", return_value=0)
    @patch("enmutils_int.lib.netsim_executor.filesystem.get_local_file_checksum", return_value=1)
    @patch("enmutils_int.lib.netsim_executor.filesystem.does_remote_file_exist", side_effect=[False, True])
    @patch("enmutils_int.lib.netsim_executor.shell.run_remote_cmd")
    def test_deploy_script_raisesRuntime_error_02(self, mock_shell_run_remote_cmd, *_):
        response = Mock()
        response.rc = 1
        mock_shell_run_remote_cmd.return_value = response
        self.assertRaises(RuntimeError, netsim_executor.deploy_script, "netsimlin704", "/tmp", "/tmp/command_executor.sh")

    @patch("enmutils_int.lib.netsim_executor.filesystem.get_remote_file_checksum", return_value=0)
    @patch("enmutils_int.lib.netsim_executor.filesystem.get_local_file_checksum", return_value=1)
    @patch("enmutils_int.lib.netsim_executor.filesystem.does_remote_file_exist", return_value=False)
    @patch("enmutils_int.lib.netsim_executor.upload")
    def test_deploy_script__is_successful(self, mock_upload, *_):
        netsim_executor.deploy_script("netsimlin704", "/tmp", "/tmp/command_executor.sh")
        self.assertEqual(1, mock_upload.call_count)

    @patch("enmutils_int.lib.netsim_executor.persistence.has_key", return_value=True)
    @patch("enmutils_int.lib.netsim_executor.cache.has_key", return_value=False)
    @patch("enmutils_int.lib.netsim_executor.mutexer.mutex")
    @patch("enmutils_int.lib.netsim_executor.shell.run_remote_cmd")
    @patch("enmutils_int.lib.netsim_executor.cache.set")
    def test_run_cmd_sets_the_executor_key_in_cache_when_the_script_is_already_deployed_on_the_host_as_the_key_is_stored_in_persistence(self, mock_cache_set, mock_shell_run_remote_cmd, *_):
        netsim_executor.run_cmd(".start -parallel", "netsimlin704")
        self.assertTrue(mock_cache_set.called)
        self.assertTrue(mock_shell_run_remote_cmd.called)

    @patch("enmutils_int.lib.netsim_executor.cache.has_key", return_value=True)
    @patch("enmutils_int.lib.netsim_executor.mutexer.mutex")
    @patch("enmutils_int.lib.netsim_executor.shell.run_remote_cmd")
    def test_run_cmd_executes_sussefully_when_the_executor_key_exists_in_cache(
            self, mock_shell_run_remote_cmd, mock_mutexer, *_):
        netsim_executor.run_cmd(".start -parallel", "netsimlin704")
        self.assertFalse(mock_mutexer.called)
        self.assertTrue(mock_shell_run_remote_cmd.called)

    @patch("enmutils_int.lib.netsim_executor.cache.has_key", return_value=True)
    @patch("enmutils_int.lib.netsim_executor.mutexer.mutex")
    @patch("enmutils_int.lib.netsim_executor.shell.run_remote_cmd")
    def test_run_cmd_successfully_builds_the_command_to_run_on_a_simulation_when_specified_even_if_no_password_is_specified(self, mock_shell_run_remote_cmd, *_):
        netsim_executor.run_cmd(".start -parallel", "netsimlin704", "sim1", password=None)
        self.assertTrue(mock_shell_run_remote_cmd.called)

    @patch("enmutils_int.lib.netsim_executor.cache.has_key", return_value=True)
    @patch("enmutils_int.lib.netsim_executor.mutexer.mutex")
    @patch("enmutils_int.lib.netsim_executor.shell.run_remote_cmd")
    def test_run_cmd_successfully_builds_the_command_to_run_on_a_string_of_node_names_in_a_simulation_when_specified(self, mock_shell_run_remote_cmd, *_):
        netsim_executor.run_cmd(".start -parallel", "netsimlin704", "sim1", "LTE05ERBS00005 LTE05ERBS00006")
        self.assertTrue(mock_shell_run_remote_cmd.called)

    @patch("enmutils_int.lib.netsim_executor.cache.has_key", return_value=True)
    @patch("enmutils_int.lib.netsim_executor.mutexer.mutex")
    @patch("enmutils_int.lib.netsim_executor.shell.run_remote_cmd")
    def test_run_cmd_successfully_builds_the_command_to_run_on_a_list_of_node_names_in_a_simulation_when_specified(self, mock_shell_run_remote_cmd, *_):
        netsim_executor.run_cmd(".start -parallel", "netsimlin704", "sim1", ["LTE05ERBS00005", "LTE05ERBS00006"])
        self.assertTrue(mock_shell_run_remote_cmd.called)

    @patch("enmutils_int.lib.netsim_executor.run_cmd")
    def test_check_nodes_started_returns_set_of_stopped_nodes(self, mock_run_cmd):
        node1 = Mock()
        node2 = Mock()
        node1.node_ip = '10.12.13.14'
        node1.netsim = "netsimlin123"
        node2.node_ip = '10.12.13.15'
        node2.netsim = "netsimlin123"
        nodes = [node1, node2]
        response = Mock()
        response.stdout = ('>> .show started \n'
                           '\'server_00212_LTE_ERBS_H1160-V2lim_-IPv6@netsim\' for LTE ERBS H1160-V2lim \n'
                           '================================================================= \n'
                           'NE                       Address          Simulation/Commands \n'
                           'LTE03ERBS00040           10.12.13.14  /netsim/netsimdir/LTEH1160-V2limx40-1.8K-FDD-LTE03 \n'
                           'MSC30BSC59               10.154.56.6,10.154.56.7,10.154.56.8 161  '
                           'GSM-FT-MSC-BC-IS-150cell_250cell_BSC_18-Q2_V7x9-GSM30_MSC30BSC59 \n'
                           'LTE03ERBS00039           10.12.13.25  /netsim/netsimdir/LTEH1160-V2limx40-1.8K-FDD-LTE03')
        mock_run_cmd.return_value = response
        result = netsim_executor.check_nodes_started(nodes)
        self.assertEqual(result.pop().node_ip, "10.12.13.15")

    @patch("enmutils_int.lib.netsim_executor.run_cmd")
    def test_check_nodes_started_raises_exception(self, mock_run_cmd):
        node = Mock()
        node.host = "netsimlin123"
        mock_run_cmd.side_effect = Exception
        self.assertRaises(Exception, netsim_executor.check_nodes_started, [node])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
