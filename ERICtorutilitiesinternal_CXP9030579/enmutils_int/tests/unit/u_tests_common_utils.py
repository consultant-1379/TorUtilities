#!/usr/bin/env python
from random import randint
import unittest2
from mock import patch, Mock
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib.enm_node import ERBSNode
from enmutils.lib.exceptions import EnvironError, NetsimError, ScriptEngineResponseValidationError, EnmApplicationError
from enmutils_int.lib import common_utils
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip


USERNAMES = ["CBRS_SETUP_0304-23132486_u0", "CMEVENTS_NBI_01_0304-23024972_u1"]


class CommonUtilsUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        node = ERBSNode(node_id="testNode", node_ip=generate_configurable_ip(), simulation="test_simulation",
                        netsim="test_host")
        self.nodes = [node]
        self.node2 = ERBSNode(node_id="testNode1", node_ip=generate_configurable_ip(), simulation="test_simulation",
                              netsim="test_host")
        self.tmp_dir = "/tmp/enmutils/"

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_random_string_include_numbers(self):
        self.assertFalse(all([_.isalpha() for _ in common_utils.get_random_string(36)]))

    def test_get_random_string_dont_include_numbers(self):
        self.assertTrue([_.isalpha() for _ in common_utils.get_random_string(16, include_numbers=False)])

    def test_merge_dict_initiate(self):
        dict1 = {'LTEG1220-V1limx3-5K-FDD-LTE103': {}}
        dict2 = {'LTEG1220-V1limx3-5K-FDD-LTE103': {'mim': '{"LTE","ERBS","G1220-V1lim",[]}', 'LTE103ERBS00001': {'status': 'stopped', 'ip': generate_configurable_ip()}, 'LTE103ERBS00002': {'status': 'stopped', 'ip': generate_configurable_ip()}, 'LTE103ERBS00003': {'status': 'stopped', 'ip': generate_configurable_ip()}}}
        common_utils.merge_dict(dict1, dict2)
        expected_dict1 = {'LTEG1220-V1limx3-5K-FDD-LTE103': {'mim': '{"LTE","ERBS","G1220-V1lim",[]}', 'LTE103ERBS00001': {'status': 'stopped', 'ip': generate_configurable_ip()}, 'LTE103ERBS00002': {'status': 'stopped', 'ip': generate_configurable_ip()}, 'LTE103ERBS00003': {'status': 'stopped', 'ip': generate_configurable_ip()}}}
        self.assertEqual(dict1, expected_dict1)

    def test_merge_dict_update(self):
        dict3 = {'LTEG1220-V1limx3-5K-FDD-LTE103': {'mim': '{"LTE","ERBS","G1220-V1lim",[]}', 'LTE103ERBS00001': {'status': 'stopped', 'ip': generate_configurable_ip()}, 'LTE103ERBS00002': {'status': 'stopped', 'ip': generate_configurable_ip()}, 'LTE103ERBS00003': {'status': 'stopped', 'ip': generate_configurable_ip()}}}
        dict4 = {'LTEG1220-V1limx3-5K-FDD-LTE103': {'LTE103ERBS00001': {'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}, 'LTE103ERBS00002': {'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}, 'LTE103ERBS00003': {'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}}}
        common_utils.merge_dict(dict3, dict4)
        expected_dict3 = {'LTEG1220-V1limx3-5K-FDD-LTE103': {'mim': '{"LTE","ERBS","G1220-V1lim",[]}', 'LTE103ERBS00001': {'status': 'stopped', 'ip': generate_configurable_ip(), 'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}, 'LTE103ERBS00002': {'status': 'stopped', 'ip': generate_configurable_ip(), 'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}, 'LTE103ERBS00003': {'status': 'stopped', 'ip': generate_configurable_ip(), 'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}}}
        self.assertEqual(dict3, expected_dict3)

    def test_merge_dict_final(self):
        dict5 = {'LTEG1220-V1limx3-5K-FDD-LTE103': {'mim': '{"LTE","ERBS","G1220-V1lim",[]}', 'LTE103ERBS00001': {'status': 'stopped', 'ip': generate_configurable_ip(), 'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}, 'LTE103ERBS00002': {'status': 'stopped', 'ip': generate_configurable_ip(), 'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}, 'LTE103ERBS00003': {'status': 'stopped', 'ip': generate_configurable_ip(), 'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}}}
        dict6 = {}
        common_utils.merge_dict(dict5, dict6)
        expected_dict5 = {'LTEG1220-V1limx3-5K-FDD-LTE103': {'mim': '{"LTE","ERBS","G1220-V1lim",[]}', 'LTE103ERBS00001': {'status': 'stopped', 'ip': generate_configurable_ip(), 'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}, 'LTE103ERBS00002': {'status': 'stopped', 'ip': generate_configurable_ip(), 'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}, 'LTE103ERBS00003': {'status': 'stopped', 'ip': generate_configurable_ip(), 'pm_sub': 'inactive', 'fm_sub': 'inactive', 'cm_sub': 'inactive'}}}
        self.assertEqual(dict5, expected_dict5)

    def test_merge_dict_extend(self):
        info_dict = {'key': {'value': {'inner_value'}}}
        database = {'key': {'value': ['inner_value']}}
        common_utils.merge_dict(database, info_dict)
        expected = {'key': {'value': ['inner_value', 'inner_value']}}
        self.assertEqual(database, expected)

    def test_merge_dict_new_val(self):
        info_dict = {'apple': {'value': {'inner_value'}}}
        database = {'key': {'value': {""}}}
        common_utils.merge_dict(database, info_dict)
        expected = {'apple': {'value': set(['inner_value'])}, 'key': {'value': set([''])}}
        self.assertEqual(expected, database)

    @patch("enmutils_int.lib.common_utils.shell.run_local_cmd")
    def test_get_installed_version__is_successful(self, mock_run):
        response = Mock()
        response.stdout = "1.1.1"
        mock_run.return_value = response
        ans = common_utils.get_installed_version("package")
        self.assertEqual(ans, "1.1.1")

    @patch("enmutils_int.lib.common_utils.installed_versions", {"package": "1.1.1"})
    @patch("enmutils_int.lib.common_utils.shell.run_local_cmd")
    def test_get_installed_version__returns_cached_info(self, mock_run, *_):
        ans = common_utils.get_installed_version("package")
        self.assertEqual(ans, "1.1.1")
        self.assertFalse(mock_run.called)

    @patch("enmutils_int.lib.common_utils.installed_versions", {})
    @patch("enmutils_int.lib.common_utils.shell.run_local_cmd")
    def test_get_installed_version__unknown_if_multiple_rpms_installed(self, mock_run, *_):
        response = Mock()
        response.stdout = "5.5.75.5.8"
        mock_run.return_value = response
        ans = common_utils.get_installed_version("package")
        self.assertEqual(ans, "Unknown")

    @patch("enmutils_int.lib.common_utils.installed_versions", {})
    @patch("enmutils_int.lib.common_utils.shell.run_local_cmd")
    def test_get_installed_version__returns_unknown_if_rpm_command_results_in_errors(self, mock_run):
        response = Mock()
        response.stdout = (
            """
            rpmdb: Thread/process 44204/140612492199840 failed: Thread died in Berkeley DB library
            error: db3 error(-30974) from dbenv->failchk: DB_RUNRECOVERY: Fatal error, run database recovery
            error: cannot open Packages index using db3 -  (-30974)
            error: cannot open Packages database in /var/lib/rpm
            """)
        mock_run.return_value = response
        ans = common_utils.get_installed_version("package")
        self.assertEqual(ans, "Unknown")

    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    def test_install_licence_raises_error(self, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = "ERROR"
        mock_user.enm_execute.return_value = mock_response
        with self.assertRaises(ScriptEngineResponseValidationError):
            common_utils.install_licence(mock_user, "name")

    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    def test_install_licence_success(self, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = "Success"
        mock_user.enm_execute.return_value = mock_response
        output = common_utils.install_licence(mock_user, "name")
        self.assertEqual(output, "Success")

    def test_get_directory_works(self):
        smo = "SMOinfo.xml"
        path = common_utils.get_internal_file_path_for_import("etc", "data", smo)
        self.assertIn("enmutils_int/etc/data/SMOinfo.xml", path)

    @patch('enmutils_int.lib.common_utils.unipath.Path', side_effect=Exception)
    def test_get_internal_file_path_for_import_raises_exception(self, *_):
        with self.assertRaises(RuntimeError):
            common_utils.get_internal_file_path_for_import("root", "child", "name")

    @patch('enmutils_int.lib.common_utils.PowerNodes')
    @patch("enmutils_int.lib.common_utils.check_nodes_started")
    def test_remove_stopped_nodes_raises_environ_error(self, mock_checked_nodes_started, *_):
        mock_checked_nodes_started.return_value = self.nodes
        self.assertRaises(EnvironError, common_utils.start_stopped_nodes_or_remove, self.nodes)

    @patch('enmutils_int.lib.common_utils.PowerNodes')
    @patch("enmutils_int.lib.common_utils.check_nodes_started")
    def test_remove_stopped_nodes_raises_exception(self, mock_checked_nodes_started, *_):
        mock_checked_nodes_started.side_effect = Exception("Exception")
        self.assertRaises(Exception, common_utils.start_stopped_nodes_or_remove, self.nodes)

    @patch('enmutils_int.lib.common_utils.PowerNodes')
    @patch("enmutils_int.lib.common_utils.check_nodes_started")
    def test_remove_stopped_nodes_raises_netsim_error(self, mock_checked_nodes_started, *_):
        mock_checked_nodes_started.side_effect = common_utils.NetsimError("Exception")
        self.assertRaises(NetsimError, common_utils.start_stopped_nodes_or_remove, self.nodes)

    @patch('enmutils_int.lib.common_utils.PowerNodes')
    @patch("enmutils_int.lib.common_utils.check_nodes_started")
    def test_remove_stopped_nodes_removes_nodes_correctly(self, mock_checked_nodes_started, *_):
        mock_checked_nodes_started.return_value = self.nodes
        self.nodes.append(self.node2)
        nodes = common_utils.start_stopped_nodes_or_remove(self.nodes)
        self.assertEqual(1, len(nodes))
        self.assertEqual(self.node2.node_id, nodes[0].node_id)

    @patch('enmutils_int.lib.common_utils.PowerNodes')
    @patch("enmutils_int.lib.common_utils.check_nodes_started")
    def test_remove_stopped_nodes_none_removed(self, mock_checked_nodes_started, *_):
        mock_checked_nodes_started.side_effect = [self.nodes, []]
        nodes = common_utils.start_stopped_nodes_or_remove(self.nodes)
        self.assertEqual(1, len(nodes))

    @patch("enmutils_int.lib.common_utils.check_nodes_started")
    def test_remove_stopped_nodes(self, mock_checked_nodes_started, *_):
        mock_checked_nodes_started.return_value = []
        common_utils.start_stopped_nodes_or_remove(self.nodes)

    def test_limited_size_dictionary_takes_no_more_than_size_limit(self):

        size_limit_dict = common_utils.LimitedSizeDict(size_limit=3)
        for i in xrange(0, 5):
            size_limit_dict[i] = i
        self.assertEqual(len(size_limit_dict), 3)

    def test_limited_size_dict_no_action_on_no_limit_given(self):
        size_limit_dict = common_utils.LimitedSizeDict(size_limit=None)
        self.assertEqual(size_limit_dict.size_limit, None)

    @patch("enmutils_int.lib.common_utils.download_artifact_from_nexus", return_value=None)
    def test_return_dict_from_json_artifact_raises_environ_error(self, *_):
        self.assertRaises(EnvironError, common_utils.return_dict_from_json_artifact, 'package')

    @patch('enmutils_int.lib.common_utils.get_json_from_a_file')
    @patch('enmutils_int.lib.common_utils.convert_from_json_to_dict')
    @patch('enmutils_int.lib.common_utils.download_artifact_from_nexus')
    def test_return_dict_from_json_artifact(self, mock_download, mock_convert, *_):
        common_utils.return_dict_from_json_artifact('4.1.2')
        self.assertTrue(mock_download.called)
        self.assertTrue(mock_convert.called)

    @patch('enmutils_int.lib.common_utils.return_dict_from_json_artifact')
    def test_filter_artifact_dict_for_profile_keys(self, mock_artifact_dict):
        mock_artifact_dict.side_effect = [{"basic": {"cmimport": {"CMIMPORT_SETUP": {"SUPPORTED": False},
                                                                  "CMIMPORT_10": {"SUPPORTED": False,
                                                                                  "NUM_NODES": {"Router6672": 500}}}}},
                                          {"basic": {"cmimport": {"CMIMPORT_SETUP": {"SUPPORTED": False},
                                                                  "CMIMPORT_10": {"SUPPORTED": False,
                                                                                  "NUM_NODES": {"Router6672": 500}},
                                                                  "CMIMPORT_11": {
                                                                      "NOTE": "Future development Jira: TORF-166127",
                                                                      "SUPPORTED": False}}}}]

        self.assertEqual(2, len(common_utils.filter_artifact_dict_for_profile_keys('4.1.1')))
        self.assertEqual(3, len(common_utils.filter_artifact_dict_for_profile_keys('4.1.2')))

    @patch("enmutils_int.lib.common_utils.return_dict_from_json_artifact", return_value="string")
    def test_filter_artifact_dict_for_profile_keys_raises_environ_error(self, *_):

        self.assertRaises(EnvironError, common_utils.filter_artifact_dict_for_profile_keys, '')

    def test_return_days_of_the_week(self):
        days = ["Monday", "Tuesday", "Friday", "Sunday"]
        self.assertTrue(set(days).issubset(common_utils.get_days_of_the_week()))
        self.assertEqual(7, len(common_utils.get_days_of_the_week()))
        self.assertNotEqual(days[0].upper(), common_utils.get_days_of_the_week()[0])
        self.assertEqual(days[0].upper(), common_utils.get_days_of_the_week(upper=True)[0])

    def test_chunks_generator(self):
        chunk_size = 250
        elements = [i for i in xrange(1400)]

        first = list(common_utils.chunks(elements, chunk_size))
        self.assertEqual(len(first), 6)
        self.assertEqual(len(first[0]), 250)
        self.assertEqual(len(first[4]), 250)
        self.assertEqual(len(first[5]), 150)

        chunk_size = 250
        elements2 = [i for i in xrange(500)]
        second = list(common_utils.chunks(elements2, chunk_size))
        self.assertEqual(len(second), 2)
        self.assertEqual(len(second[0]), 250)
        self.assertEqual(len(second[1]), 250)

    def test_chunks_generator_limits(self):
        chunk_size = 3
        elements = [i for i in xrange(40)]

        first = list(common_utils.chunks([], chunk_size))
        self.assertEqual(len(first), 0)

        chunk_size = 10
        second = list(common_utils.chunks(elements, chunk_size))
        self.assertEqual(len(second), 4)
        self.assertEqual(len(second[0]), 10)
        self.assertEqual(len(second[3]), 10)

        chunk_size = 1
        third = list(common_utils.chunks(elements, chunk_size))
        self.assertEqual(len(third), 40)
        self.assertEqual(len(third[0]), 1)
        self.assertEqual(len(third[39]), 1)

    @patch('enmutils_int.lib.common_utils.process.kill_process_id')
    @patch('enmutils_int.lib.common_utils.shell.run_local_cmd')
    def test_ensure_all_daemons_are_killed(self, mock_local_cmd, mock_os_kill):
        response = Mock()
        response.stdout = '13808\n21367\n'
        mock_local_cmd.return_value = response
        common_utils.ensure_all_daemons_are_killed()
        self.assertEqual(2, mock_os_kill.call_count)

    @patch('enmutils_int.lib.common_utils.process.kill_process_id')
    @patch('enmutils_int.lib.common_utils.shell.run_local_cmd')
    def test_ensure_all_daemons_are_killed__continues_on_failure(self, mock_local_cmd, mock_os_kill):
        response = Mock()
        response.stdout = '13808\n21367\n1234'
        mock_local_cmd.return_value = response
        mock_os_kill.side_effect = [None, Exception("Error"), None]
        common_utils.ensure_all_daemons_are_killed()
        self.assertEqual(3, mock_os_kill.call_count)

    def test_split_list_into_sublists_positive_n_value_and_number_of_items_in_input_list_higher_than_n(self):
        rand_input_lists_lengths = [randint(1000, 9999) for _ in range(20)]
        for rand_length in rand_input_lists_lengths:
            n = randint(1, 999)
            input_list = [i for i in range(rand_length)]
            lists = common_utils.split_list_into_sublists(input_list, n)
            self.assertTrue(len(lists) == n)
            number_of_items = 0
            for item in lists:
                number_of_items += len(item)
                self.assertTrue(isinstance(item, list))
                self.assertFalse(item == [])

            self.assertTrue(number_of_items == rand_length)

    def test_split_list_into_sublists_positive_n_value_and_number_of_items_in_input_list_lower_than_n(self):
        rand_input_lists_lengths = [randint(900, 999) for _ in range(20)]
        for rand_length in rand_input_lists_lengths:
            n = 2000
            input_list = [i for i in range(rand_length)]
            lists = common_utils.split_list_into_sublists(input_list, n)
            self.assertTrue(len(lists) == rand_length)
            number_of_items = 0
            for item in lists:
                number_of_items += len(item)
                self.assertTrue(isinstance(item, list))
                self.assertFalse(item == [])
            self.assertTrue(number_of_items == rand_length)

    def test_split_list_into_sublists_n_value_equals_zero(self):
        output_list = common_utils.split_list_into_sublists([1, 2, 3, 4, 5], 0)
        self.assertTrue(output_list == [])

    def test_split_list_into_sublists_n_value_less_than_zero(self):
        output_list = common_utils.split_list_into_sublists([1, 2, 3, 4, 5], -1)
        self.assertTrue(output_list == [])

    def test_split_list_into_sublists_test_list_is_an_empty_list(self):
        output_list = common_utils.split_list_into_sublists([], 6)
        self.assertTrue(output_list == [])

    @patch('enmutils_int.lib.common_utils.check_for_existing_process_on_ms')
    @patch('enmutils_int.lib.common_utils.filesystem.does_file_exist_on_ms', side_effect=[True, False])
    def test_check_if_upgrade_in_progress_physical_deployment(self, mock_file_exists, mock_existing_process):
        bad_response, good_response = Mock(), Mock()
        bad_response.ok = False
        good_response.ok = True
        mock_existing_process.side_effect = [bad_response, bad_response, good_response, bad_response, good_response,
                                             bad_response, bad_response]
        self.assertTrue(common_utils.check_if_upgrade_in_progress_physical_deployment())
        self.assertEqual(1, mock_file_exists.call_count)
        self.assertTrue(common_utils.check_if_upgrade_in_progress_physical_deployment())
        self.assertEqual(1, mock_file_exists.call_count)
        self.assertTrue(common_utils.check_if_upgrade_in_progress_physical_deployment())
        self.assertEqual(1, mock_file_exists.call_count)
        self.assertEqual(False, common_utils.check_if_upgrade_in_progress_physical_deployment())
        self.assertEqual(2, mock_file_exists.call_count)

    @patch('enmutils_int.lib.common_utils.shell.run_cmd_on_ms')
    def test_check_for_active_litp_plan(self, mock_run_cmd_on_ms):
        response = Mock()
        response.stdout = "successful"
        mock_run_cmd_on_ms.return_value = response
        self.assertFalse(common_utils.check_for_active_litp_plan())
        response.stdout = "Plan Status: Running"
        mock_run_cmd_on_ms.return_value = response
        self.assertTrue(common_utils.check_for_active_litp_plan())

    @patch('enmutils_int.lib.common_utils.shell.run_cmd_on_ms')
    def test_check_for_active_litp_plan__no_plan(self, mock_run_cmd_on_ms):
        response = Mock()
        response.stdout = "InvalidLocationError Plan does not exist"
        mock_run_cmd_on_ms.return_value = response
        self.assertFalse(common_utils.check_for_active_litp_plan())

    @patch('enmutils_int.lib.common_utils.check_for_existing_process_on_ms')
    @patch('enmutils_int.lib.common_utils.shell.run_cmd_on_ms')
    def test_check_for_backup_in_progress(self, mock_run_cmd_on_ms, mock_existing_process):
        response = Mock()
        response.stdout = "ombs_snapshot"
        mock_run_cmd_on_ms.return_value = response
        self.assertTrue(common_utils.check_for_backup_in_progress())
        self.assertEqual(1, mock_run_cmd_on_ms.call_count)
        response.stdout = "bos.log"
        mock_run_cmd_on_ms.side_effect = [response, response]
        self.assertTrue(common_utils.check_for_backup_in_progress())
        self.assertEqual(3, mock_run_cmd_on_ms.call_count)
        response.stdout = "Nothing to see here..."
        mock_run_cmd_on_ms.side_effect = [response, response]
        response.ok = True
        mock_existing_process.return_value = response
        self.assertTrue(common_utils.check_for_backup_in_progress())
        self.assertEqual(5, mock_run_cmd_on_ms.call_count)
        response.stdout = "Nothing to see here..."
        mock_run_cmd_on_ms.side_effect = [response, response]
        response.ok = False
        mock_existing_process.return_value = response
        self.assertFalse(common_utils.check_for_backup_in_progress())
        self.assertEqual(7, mock_run_cmd_on_ms.call_count)

    @patch('enmutils_int.lib.common_utils.log.logger.debug')
    @patch('enmutils_int.lib.common_utils.shell.run_cmd_on_ms')
    def test_check_for_existing_process_on_ms(self, mock_run_cmd_on_ms, mock_debug):
        common_utils.check_for_existing_process_on_ms("1234")
        self.assertEqual(1, mock_run_cmd_on_ms.call_count)
        mock_debug.assert_called_with("Completed check for process 1234")

    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    @patch('enmutils_int.lib.common_utils.log.logger.debug')
    @patch('enmutils_int.lib.common_utils.User.delete', side_effect=[None, Exception("Error"), None])
    @patch('enmutils_int.lib.common_utils.User.get_usernames')
    def test_user_cleanup(self, mock_get_usernames, mock_delete, mock_debug, _):
        mock_get_usernames.return_value = ["SECUI_01_", "SECUI_02_", "SECUI_01_", "SECUI_01_"]
        common_utils.delete_profile_users("SECUI_01")
        self.assertEqual(mock_delete.call_count, 3)
        self.assertEqual(mock_debug.call_count, 2)

    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    @patch('enmutils_int.lib.common_utils.log.logger.debug')
    @patch('enmutils_int.lib.common_utils.User.delete')
    @patch('enmutils_int.lib.common_utils.User.get_usernames', side_effect=Exception("Error"))
    def test_user_cleanup_user_list_failure(self, mock_get_usernames, mock_delete, mock_debug, _):
        mock_get_usernames.return_value = ["SECUI_01_", "SECUI_02_", "SECUI_01_", "SECUI_01_"]
        common_utils.delete_profile_users("SECUI_01")
        self.assertEqual(mock_delete.call_count, 0)
        self.assertEqual(mock_debug.call_count, 1)

    @patch('enmutils_int.lib.common_utils.User.__init__', return_value=None)
    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    @patch('enmutils_int.lib.common_utils.User.create', side_effect=[Exception("Exception"), Mock()])
    def test_create_users_operation(self, mock_user_create, mock_admin_user, _):
        common_utils.create_users_operation("Test_01", 4, ["Admin"], fail_fast=False)
        self.assertEqual(4, mock_user_create.call_count)
        self.assertEqual(1, mock_admin_user.call_count)

    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    @patch('enmutils_int.lib.common_utils.User.__init__', return_value=None)
    @patch('enmutils_int.lib.common_utils.User.create', side_effect=[Exception("Exception"), []])
    def test_create_users_operation_fail_fast_raises_enm_application_error(self, *_):
        self.assertRaises(EnmApplicationError, common_utils.create_users_operation, "Test_01", 2, ["Admin"],
                          fail_fast=True)

    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    @patch('enmutils_int.lib.common_utils.time.sleep', return_value=0)
    @patch('enmutils_int.lib.common_utils.User.__init__', return_value=None)
    @patch('enmutils_int.lib.common_utils.User.create', side_effect=[Exception("Exception")])
    def test_create_users_operation_exits_at_maximum_level(self, mock_create, *_):
        common_utils.create_users_operation("Test_01", 2, ["Admin"], fail_fast=False, level=9, retry=True)
        self.assertEqual(4, mock_create.call_count)

    @patch('enmutils_int.lib.common_utils.persistence.get', return_value={"TEST_02"})
    @patch('enmutils_int.lib.common_utils.mutexer')
    @patch('enmutils_int.lib.common_utils.persistence.set')
    def test_add_profile_to_active_workload_profiles(self, mock_persistence_set, *_):
        common_utils.add_profile_to_active_workload_profiles('TEST_01')
        mock_persistence_set.assert_called_with('active_workload_profiles', {"TEST_02", "TEST_01"}, -1)

    @patch('enmutils_int.lib.common_utils.persistence.get', return_value={"TEST_01", "TEST_02"})
    @patch('enmutils_int.lib.common_utils.mutexer')
    @patch('enmutils_int.lib.common_utils.persistence.set')
    def test_remove_profile_from_active_workload_profiles__profile_removed(self, mock_persistence_set, *_):
        common_utils.remove_profile_from_active_workload_profiles("TEST_01")
        mock_persistence_set.assert_called_with('active_workload_profiles', {"TEST_02"}, -1)

    @patch('enmutils_int.lib.common_utils.persistence.get', return_value={"TEST_02"})
    @patch('enmutils_int.lib.common_utils.mutexer')
    @patch('enmutils_int.lib.common_utils.persistence.set')
    def test_remove_profile_from_active_workload_profiles__not_in_active_list(self, mock_persistence_set, *_):
        common_utils.remove_profile_from_active_workload_profiles("TEST_01")
        self.assertEqual(0, mock_persistence_set.call_count)

    @patch('enmutils_int.lib.common_utils.persistence')
    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    def test_terminate_user_sessions__success(self, mock_user, mock_persistence):
        mock_user.return_value.get_usernames.return_value = USERNAMES
        mock_persistence.has_key.return_value = True
        mock_persistence.get.return_value = Mock()
        common_utils.terminate_user_sessions("CMEVENTS_NBI_01")
        self.assertEqual(1, mock_persistence.get.return_value.remove_session.call_count)

    @patch('enmutils_int.lib.common_utils.persistence')
    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    def test_terminate_user_sessions__matches_setup_profile(self, mock_user, mock_persistence):
        mock_user.return_value.get_usernames.return_value = USERNAMES
        mock_persistence.has_key.return_value = True
        mock_persistence.get.return_value = Mock()
        common_utils.terminate_user_sessions("CBRS_SETUP")
        self.assertEqual(1, mock_persistence.get.return_value.remove_session.call_count)

    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    def test_terminate_user_sessions__no_matching_users(self, mock_user):
        mock_user.return_value.get_usernames.return_value = USERNAMES
        common_utils.terminate_user_sessions("CMSYNC_01")
        self.assertEqual(0, mock_user.return_value.remove_session.call_count)

    @patch('enmutils_int.lib.common_utils.log.logger.debug')
    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    def test_terminate_user_sessions__logs_exception_with_workload_admin(self, mock_user, mock_debug):
        mock_user.return_value.get_usernames.side_effect = Exception("Error")
        common_utils.terminate_user_sessions("CMSYNC_01")
        self.assertEqual(0, mock_user.return_value.remove_session.call_count)
        mock_debug.assert_any_call("Failed to get ENM user session information, error encountered: Error.")

    @patch('enmutils_int.lib.common_utils.persistence')
    @patch('enmutils_int.lib.common_utils.log.logger.debug')
    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    def test_terminate_user_sessions__logs_exception_with_remove(self, mock_user, mock_debug, mock_persistence):
        mock_user.return_value.get_usernames.return_value = USERNAMES
        mock_persistence.has_key.return_value = True
        mock_persistence.get.return_value = Mock()
        mock_persistence.get.return_value.remove_session.side_effect = Exception("Error")
        common_utils.terminate_user_sessions("CBRS_SETUP")
        self.assertEqual(1, mock_persistence.get.return_value.remove_session.call_count)
        mock_debug.assert_any_call("Failed to remove ENM user session, error encountered: Error.")

    @patch('enmutils_int.lib.common_utils.log.logger.debug')
    def test_terminate_user_sessions__ignores_excluded_profiles(self, mock_debug):
        common_utils.terminate_user_sessions("GEO_R_01")
        self.assertEqual(0, mock_debug.return_value.remove_session.call_count)

    @patch('enmutils_int.lib.common_utils.persistence')
    @patch('enmutils_int.lib.common_utils.log.logger.debug')
    @patch('enmutils_int.lib.common_utils.get_workload_admin_user')
    def test_terminate_user_sessions__success_if_user_session_key_not_existed(self, mock_user, mock_debug,
                                                                              mock_persistence):
        mock_user.return_value.get_usernames.return_value = ["SECUI_01_0304-23132486_u0", "SECUI_01_0304-23132487_u1"]
        mock_persistence.has_key.return_value = False
        mock_persistence.get.return_value = Mock()
        common_utils.terminate_user_sessions("SECUI_01")
        self.assertEqual(0, mock_persistence.get.return_value.remove_session.call_count)
        self.assertEqual(3, mock_debug.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
