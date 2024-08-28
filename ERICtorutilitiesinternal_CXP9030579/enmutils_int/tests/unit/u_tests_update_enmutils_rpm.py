#!/usr/bin/env python
from os import path

import unittest2
from enmutils.lib import http
from enmutils.lib.exceptions import RpmMisMatch
from enmutils_int.bin import update_enmutils_rpm
from mock import patch, Mock, call
from testslib import unit_test_utils


MOCK_PACKAGE_METADATA = """<metadata>
  <groupId>com.ericsson.dms.torutility</groupId>
  <artifactId>ERICtorutilities_CXP9030570</artifactId>
  <versioning>
    <latest>4.2.38</latest>
    <release>4.16.38</release>
    <versions>
      <version>1.0.1</version>
      <version>1.1.74</version>
      <version>1.8.19</version>
      <version>2.3.4</version>
      <version>4.3.25</version>
      <version>4.10.3</version>
      <version>4.16.38</version>
    </versions>
    <lastUpdated>20150820182642</lastUpdated>
  </versioning>
</metadata>"""


class RpmUpgradeUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.bin.update_enmutils_rpm.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.bin.update_enmutils_rpm.http.get")
    def test_check_nexus_version__returns_none_if_nexus_is_not_available(self, mock_http_get,
                                                                         mock_check_deployment_to_disable_proxy):
        mock_check_deployment_to_disable_proxy.return_value = True
        mock_http_get.side_effect = http.requests.exceptions.ConnectionError("YIKES")
        self.assertIsNone(update_enmutils_rpm.check_nexus_version("prod"))

    @patch("enmutils_int.bin.update_enmutils_rpm.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.bin.update_enmutils_rpm.http.get")
    def test_check_nexus_version__proxy_is_not_required(self, mock_http_get, mock_check_deployment_to_disable_proxy):
        mock_check_deployment_to_disable_proxy.return_value = False
        mock_http_get.side_effect = http.requests.exceptions.ConnectionError("YIKES")
        self.assertIsNone(update_enmutils_rpm.check_nexus_version("prod"))

    @patch("enmutils_int.bin.update_enmutils_rpm.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.bin.update_enmutils_rpm.http.get")
    def test_check_nexus_version__returns_latest_version_if_no_desired_version_specified(self, mock_http_get, _):
        response = Mock()
        response.rc = True
        response.content = MOCK_PACKAGE_METADATA
        mock_http_get.return_value = response

        self.assertEqual("4.16.38", update_enmutils_rpm.check_nexus_version("prod"))

    @patch("enmutils_int.bin.update_enmutils_rpm.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.bin.update_enmutils_rpm.http.get")
    def test_check_nexus_version__returns_none_if_desired_version_not_found_on_nexus(self, mock_http_get, _):
        response = Mock()
        response.rc = True
        response.content = MOCK_PACKAGE_METADATA
        mock_http_get.return_value = response

        self.assertIsNone(update_enmutils_rpm.check_nexus_version("prod", "5.7.20"))

    @patch("enmutils_int.bin.update_enmutils_rpm.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.bin.update_enmutils_rpm.http.get")
    def test_check_nexus_version__returns_desired_version_if_desired_version_found_on_nexus(self, mock_http_get, _):
        response = Mock()
        response.rc = True
        response.content = MOCK_PACKAGE_METADATA
        mock_http_get.return_value = response

        self.assertEqual("4.3.25", update_enmutils_rpm.check_nexus_version("prod", "4.3.25"))

    @patch("enmutils_int.bin.update_enmutils_rpm._is_installed")
    def test_get_installed_version_of_package__returns_none_if_first_rpm_command_returns_non_zero_return_code(
            self, mock_is_installed):
        response = Mock()
        response.ok = False
        mock_is_installed.return_value = response

        self.assertIsNone(update_enmutils_rpm._get_installed_version_of_package("int"))

    @patch("enmutils_int.bin.update_enmutils_rpm._is_installed")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_get_installed_version_of_package__returns_none_if_second_rpm_command_returns_non_zero_return_code(
            self, mock_run_local_cmd, mock_is_installed):
        response1 = Mock()
        response1.ok = True
        mock_is_installed.return_value = response1

        response2 = Mock()
        response2.ok = False
        mock_run_local_cmd.side_effect = [response2]

        self.assertIsNone(update_enmutils_rpm._get_installed_version_of_package("int"))

    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_get_installed_version_of_package__returns_correct_version_if_commands_execute_successfully(
            self, mock_run_local_cmd):
        response1 = Mock()
        response1.ok = True
        response1.stdout = "int"
        response2 = Mock()
        response2.ok = True
        response2.stdout = "3.19.127"
        mock_run_local_cmd.side_effect = [response1, response2]

        self.assertEqual("3.19.127", update_enmutils_rpm._get_installed_version_of_package("int"))

    @patch("os.path.exists", return_value=False)
    def test_update_enmutils_rpm__raises_error(self, _):
        self.assertRaises(RuntimeError, update_enmutils_rpm.update_enmutils_rpm)

    @patch("enmutils_int.bin.update_enmutils_rpm._check_package_versions_match",
           side_effect=RuntimeError("error"))
    @patch("enmutils_int.bin.update_enmutils_rpm._verify_packages_installed")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_available_versions_from_nexus")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_installed_versions")
    def test_get_package_update_list__fails_validation_for_any_version_mismatches(
            self, mock_get_installed_versions, mock_get_available_versions, *_):
        mock_get_available_versions.return_value = {'int': None, 'prod': '1.2.3'}
        mock_get_installed_versions.return_value = {'prod': '1.2.1', 'int': None}

        self.assertRaises(RuntimeError, update_enmutils_rpm._get_package_update_list, ["prod", "int"], "2.34.5")

    @patch("enmutils_int.bin.update_enmutils_rpm._check_package_versions_match")
    @patch("enmutils_int.bin.update_enmutils_rpm._verify_packages_installed")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_available_versions_from_nexus")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_installed_versions")
    def test_get_package_update_list__returns_versions_of_all_packages(self, mock_get_installed_versions,
                                                                       mock_get_available_versions, *_):
        mock_get_available_versions.return_value = {'int': '1.2.3', 'prod': '1.2.3'}
        mock_get_installed_versions.return_value = {'prod': '1.2.1', 'int': None}

        (package_update_list, returned_version) = update_enmutils_rpm._get_package_update_list(["prod", "int"], "1.2.3")
        self.assertTrue("prod" in package_update_list)
        self.assertTrue("int" in package_update_list)
        self.assertEqual("1.2.3", returned_version)

    @patch("enmutils_int.bin.update_enmutils_rpm._check_package_versions_match")
    @patch("enmutils_int.bin.update_enmutils_rpm._verify_packages_installed")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_available_versions_from_nexus")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_installed_versions")
    def test_get_package_update_list__returns_versions_of_all_uninstalled_packages(
            self, mock_get_installed_versions, mock_get_available_versions, *_):
        mock_get_available_versions.return_value = {'int': '1.2.3', 'prod': '1.2.3'}
        mock_get_installed_versions.return_value = {'prod': '1.2.3', 'int': None}

        (package_update_list, _) = update_enmutils_rpm._get_package_update_list(["prod", "int"], "1.2.3")
        self.assertTrue("prod" not in package_update_list)
        self.assertTrue("int" in package_update_list)

    @patch("enmutils_int.bin.update_enmutils_rpm._check_package_versions_match")
    @patch("enmutils_int.bin.update_enmutils_rpm._verify_packages_installed")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_available_versions_from_nexus")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_installed_versions")
    def test_get_package_update_list__if_available_versions_are_old(
            self, mock_get_installed_versions, mock_get_available_versions, *_):
        mock_get_available_versions.return_value = {'int': "1.2.2", 'prod': '1.2.2'}
        mock_get_installed_versions.return_value = {'int': None, 'prod': '1.2.3'}

        _, _ = update_enmutils_rpm._get_package_update_list(["prod", "int"], "1.2.3")

    @patch("enmutils_int.bin.update_enmutils_rpm._check_package_versions_match")
    @patch("enmutils_int.bin.update_enmutils_rpm._verify_packages_installed")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_available_versions_from_nexus")
    @patch("enmutils_int.bin.update_enmutils_rpm._get_installed_versions")
    def test_get_package_update_list__if_available_one_version_is_none(
            self, mock_get_installed_versions, mock_get_available_versions, *_):
        mock_get_available_versions.return_value = {'int': None, 'prod': '1.2.5'}
        mock_get_installed_versions.return_value = {'int': '1.2.3', 'prod': '1.2.3'}

        update_enmutils_rpm._get_package_update_list(["prod", "int"], "1.2.5")

    @patch("enmutils_int.bin.update_enmutils_rpm.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.bin.update_enmutils_rpm.thread_queue.ThreadQueue.execute")
    @patch("enmutils_int.bin.update_enmutils_rpm.filesystem.does_file_exist")
    def test_download_packages__raises_exception_if_any_package_not_downloaded(
            self, mock_does_file_exist, mock_thread_queue_execute, _):
        mock_thread_queue_execute.return_value = None
        mock_does_file_exist.side_effect = [True, False, True]
        self.assertRaises(RuntimeError, update_enmutils_rpm._download_packages, ["prod", "int"], "7.23.14")

    @patch("enmutils_int.bin.update_enmutils_rpm.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.bin.update_enmutils_rpm.thread_queue.ThreadQueue.execute")
    @patch("enmutils_int.bin.update_enmutils_rpm.filesystem.does_file_exist")
    def test_download_packages__if_proxy_(
            self, mock_does_file_exist, mock_thread_queue_execute, _):
        mock_thread_queue_execute.return_value = None
        mock_does_file_exist.side_effect = [True, True, False]
        update_enmutils_rpm._download_packages(["prod", "int"], "7.23.14")

    @patch("enmutils_int.bin.update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version", return_value=False)
    @patch("enmutils_int.bin.update_enmutils_rpm.filesystem.delete_file")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.Command")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_install_packages__returns_false_if_rpm_command_returns_non_zero_return_code(
            self, mock_run_local_cmd, mock_command, *_):
        response = Mock()
        response.ok = False
        response.stdout = "FAIL"
        mock_run_local_cmd.return_value = response

        version = "7.23.14"
        snapped_version = "4.65.12"
        cmd = ('rpm -qa | grep ERICtoru')
        self.assertEqual(1, update_enmutils_rpm._install_packages(["prod", "int"], version, snapped_version))
        mock_command.assert_called_with(cmd)

    @patch("enmutils_int.bin.update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version", return_value=False)
    @patch("enmutils_int.bin.update_enmutils_rpm.filesystem.delete_file")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.Command")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_install_packages__returns_false_if_rpm_command_returns_zero_return_code_but_scriptlet_failures_occurred(
            self, mock_run_local_cmd, mock_command, *_):
        response = Mock()
        response.ok = True
        response.stdout = ("blah"
                           "warning: blah-blah scriptlet failed, exit status 2")
        mock_run_local_cmd.return_value = response

        version = "7.23.14"
        snapped_version = "4.65.12"
        cmd = 'rpm -qa | grep ERICtoru'
        self.assertEqual(1, update_enmutils_rpm._install_packages(["prod", "int"], version, snapped_version))
        mock_command.assert_called_with(cmd)

    @patch("enmutils_int.bin.update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version", return_value=True)
    @patch("enmutils_int.bin.update_enmutils_rpm.filesystem.delete_file")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.Command")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_install_packages__returns_false_if_rpm_command_returns_zero_return_code_but_syntax_error_occurred(
            self, mock_run_local_cmd, mock_command, *_):
        response = Mock()
        response.ok = True
        response.stdout = ("blah"
                           "/var/tmp/rpm-tmp.2TL0OI: line 59: syntax error: unexpected end of file")
        mock_run_local_cmd.return_value = response

        version = "7.23.14"
        snapped_version = "4.65.12"
        cmd = ("rpm -Uvh --replacepkgs --oldpackage "
               "/tmp/enmutils/ERICtorutilities_CXP9030570-{0}.rpm "
               "/tmp/enmutils/ERICtorutilitiesinternal_CXP9030579-{0}.rpm"
               .format(version))
        self.assertEqual(1, update_enmutils_rpm._install_packages(["prod", "int"], version, snapped_version))
        self.assertTrue(call(cmd, timeout=600, allow_retries=False) in mock_command.mock_calls)

    def test_get_enm_iso__pathname_regex(self):
        iso_path = path.join(update_enmutils_rpm.ENM_ISO_LOCATION, update_enmutils_rpm.ENM_ISO_MATCH_REGEX)
        self.assertEqual("/var/tmp/ERICenm_CXP9027091-*iso", iso_path)

    @patch("glob.glob")
    def test_get_latest_iso_version__when_iso_exists(self, mock_glob):
        mock_glob.return_value = ["/var/tmp/ERICenm_CXP9027091-1.13.50.iso", "/var/tmp/ERICenm_CXP9027091-1.13.55.iso"]
        self.assertEqual("/var/tmp/ERICenm_CXP9027091-1.13.55.iso",
                         update_enmutils_rpm.get_latest_iso_version("/var/tmp/ERICenm_CXP9027091-*iso"))

    @patch("glob.glob")
    def test_get_latest_iso_version__when_iso_doesnt_exists(self, mock_glob):
        mock_glob.return_value = []
        self.assertEqual("", update_enmutils_rpm.get_latest_iso_version("/var/tmp/ERICenm_CXP9027091-*iso"))

    @patch("glob.glob")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_get_package_version_from__iso_when_exists(self, mock_local_cmd, mock_glob):
        mock_glob.return_value = ["/var/tmp/ERICenm_CXP9027091-1.13.50.iso", "/var/tmp/ERICenm_CXP9027091-1.13.55.iso"]

        response = Mock()
        response.ok = True
        response.stdout = "4.20.47"
        mock_local_cmd.return_value = response

        package_alias = "prod"
        self.assertEqual("4.20.47", update_enmutils_rpm.get_package_version_from_iso(
            "/var/tmp/ERICenm_CXP9027091-*iso", package_alias))

    @patch("glob.glob")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_get_package_version_from_iso__when_exists_but_issue_with_rpm_version(self, mock_local_cmd, mock_glob):
        mock_glob.return_value = ["/var/tmp/ERICenm_CXP9027091-1.13.55.iso"]

        response = Mock()
        response.ok = False
        mock_local_cmd.return_value = response

        package_alias = "prod"
        self.assertEqual("", update_enmutils_rpm.get_package_version_from_iso("/var/tmp/ERICenm_CXP9027091-*iso",
                                                                              package_alias))

    @patch("glob.glob")
    def test_get_package_version_from_iso__when_no_iso(self, mock_glob):
        mock_glob.return_value = []
        package_alias = "prod"
        self.assertEqual("", update_enmutils_rpm.get_package_version_from_iso("/var/tmp/ERICenm_CXP9027091-*iso",
                                                                              package_alias))

    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_get_package_version_from_yum_repo__when_exist(self, mock_local_cmd):
        response = Mock()
        response.ok = True
        response.stdout = "4.20.47"
        mock_local_cmd.return_value = response

        package_alias = "prod"
        repo = update_enmutils_rpm.MS_REPO_NAME
        self.assertEqual("4.20.47", update_enmutils_rpm.get_package_version_from_yum_repo(repo, package_alias))

    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_get_package_version_from_yum_repo__no_rpm(self, mock_local_cmd):
        response = Mock()
        response.ok = False
        mock_local_cmd.return_value = response

        package_alias = "prod"
        repo = update_enmutils_rpm.MS_REPO_NAME
        self.assertEqual("", update_enmutils_rpm.get_package_version_from_yum_repo(repo, package_alias))

    @patch("enmutils_int.bin.update_enmutils_rpm._get_installed_version_of_package")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_remove_not_needed_packages__when_package_installed(
            self, mock_local_cmd, mock_get_installed_version_of_package):
        mock_get_installed_version_of_package.return_value = "4.20.21"

        response2 = Mock()
        response2.ok = True
        mock_local_cmd.return_value = response2

        packages = ['int']
        update_enmutils_rpm._remove_unneeded_packages(packages)
        self.assertTrue(mock_get_installed_version_of_package.calledwith(packages))

    @patch("enmutils_int.bin.update_enmutils_rpm._get_installed_version_of_package")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_remove_not_needed_packages__raises_exception_when_rpm_not_uninstalled(
            self, mock_local_cmd, mock_get_installed_version_of_package):
        response1 = Mock()
        response1.return_value = "4.20.21"
        mock_get_installed_version_of_package.return_value = response1

        response2 = Mock()
        response2.ok = False
        mock_local_cmd.return_value = response2

        packages = ['int']
        self.assertRaises(RuntimeError, update_enmutils_rpm._remove_unneeded_packages, packages)

    @patch("enmutils_int.bin.update_enmutils_rpm._get_installed_version_of_package")
    @patch("enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd")
    def test_remove_not_needed_packages__if_packages_version_are_not_found(
            self, mock_local_cmd, mock_get_installed_version_of_package):
        mock_get_installed_version_of_package.return_value = None

        response2 = Mock()
        response2.ok = True
        mock_local_cmd.return_value = response2

        packages = ['int']
        update_enmutils_rpm._remove_unneeded_packages(packages)
        self.assertTrue(mock_get_installed_version_of_package.calledwith(packages))

    @patch('subprocess.Popen')
    def test_display_updated_profiles_after_rpm_upgrade__success_when_upgrade(self, mock_subproc_popen):
        snapped_ver = '4.38.3'  # installed, lower version recorded
        target_ver = '4.38.33'  # higher ver. for the upgrade
        result = update_enmutils_rpm._display_updated_profiles_after_rpm_upgrade(snapped_ver, target_ver)
        self.assertTrue(mock_subproc_popen.called)
        self.assertTrue(str(mock_subproc_popen.call_args_list) == "[call(['/opt/ericsson/enmutils/bin/workload', "
                                                                  "'diff', '--updated'])]")
        self.assertTrue(result)

    @patch("subprocess.Popen")
    def test_display_updated_profiles_after_rpm_upgrade__false_when_downgrade(self, mock_subproc_popen):
        snapped_ver = '4.38.20'
        target_ver = '4.36.33'
        result = update_enmutils_rpm._display_updated_profiles_after_rpm_upgrade(snapped_ver, target_ver)
        self.assertFalse(mock_subproc_popen.called)
        self.assertFalse(result)

    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.does_dir_exist', return_value=False)
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.does_file_exist')
    @patch('enmutils_int.bin.update_enmutils_rpm.log.logger.error')
    def test_update_enmscripting_library__no_virtualenv(self, mock_error, mock_does_file_exist, *_):
        update_enmutils_rpm._update_enmscripting_library("/tmp", "test.whl")
        self.assertEqual(mock_error.call_count, 1)
        self.assertEqual(mock_does_file_exist.call_count, 0)

    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.does_dir_exist', return_value=True)
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd')
    @patch('enmutils_int.bin.update_enmutils_rpm.log.logger.error')
    def test_update_enmscripting_library__no_whl(self, mock_error, mock_run_local_cmd, *_):
        update_enmutils_rpm._update_enmscripting_library("/tmp", "test.whl")
        self.assertEqual(mock_error.call_count, 1)
        self.assertEqual(mock_run_local_cmd.call_count, 0)

    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.does_dir_exist', return_value=True)
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd')
    @patch('enmutils_int.bin.update_enmutils_rpm.log.logger.error')
    def test_update_enmscripting_library__is_success(self, mock_error, mock_run_local_cmd, *_):
        update_enmutils_rpm._update_enmscripting_library("/tmp", "test.whl")
        self.assertEqual(mock_error.call_count, 0)
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    def test_is_downgrade_of_rpm_below_particular_version__true_if_target_below_particular_version(self):
        self.assertTrue(update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version("4.65.10", "4.65.13",
                                                                                          "4.65.12"))

    def test_is_downgrade_of_rpm_below_particular_version__false_if_target_same_as_particular_version(self):
        self.assertFalse(update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version("4.65.12", "4.65.13",
                                                                                           "4.65.12"))

    def test_is_downgrade_of_rpm_below_particular_version__false_if_target_above_particular_version(self):
        self.assertFalse(update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version("4.65.14", "4.65.11",
                                                                                           "4.65.12"))

    def test_is_downgrade_of_rpm_below_particular_version__false_if_target_and_current_below_particular_version(self):
        self.assertFalse(update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version("4.65.10", "4.65.11",
                                                                                           "4.65.12"))

    def test_is_downgrade_of_rpm_below_particular_version__false_if_current_not_set(self):
        self.assertFalse(update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version("4.65.10", "",
                                                                                           "4.65.12"))

    @patch('os.path.join', return_value='/tmp/ERICtoru')
    @patch('enmutils_int.bin.update_enmutils_rpm._get_rpm_name', return_value="ERICtoru")
    @patch('enmutils_int.bin.update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version',
           side_effect=[True, False])
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.copy')
    @patch('enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd')
    @patch('enmutils_int.bin.update_enmutils_rpm._update_enmscripting_library')
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.delete_file')
    def test_install_packages__successful_with_enmscripting_library_change(self, mock_delete, *_):
        update_enmutils_rpm._install_packages(["ERICtoru"], "4.65.12", "4.65.11")
        self.assertEqual(1, mock_delete.call_count)

    @patch('os.path.join', return_value='/tmp/ERICtoru')
    @patch('enmutils_int.bin.update_enmutils_rpm._get_rpm_name', return_value="ERICtoru")
    @patch('enmutils_int.bin.update_enmutils_rpm._is_downgrade_of_rpm_below_particular_version', return_value=False)
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.copy')
    @patch('enmutils_int.bin.update_enmutils_rpm.shell.run_local_cmd')
    @patch('enmutils_int.bin.update_enmutils_rpm._update_enmscripting_library')
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.delete_file')
    def test_install_packages__successful_with_no_enmscripting_library_change(
            self, mock_delete, mock_update_enmscripting_library, *_):
        update_enmutils_rpm._install_packages(["ERICtoru"], "4.65.12", "4.65.11")
        self.assertEqual(1, mock_delete.call_count)
        self.assertEqual(0, mock_update_enmscripting_library.call_count)

    @patch('enmutils_int.bin.update_enmutils_rpm._get_installed_version_of_package')
    def test_get_installed_versions__is_successful(self, mock_get_installed_version_of_package):
        mock_get_installed_version_of_package.side_effect = ["1.2.0", "1.4.0"]
        update_enmutils_rpm._get_installed_versions(["eric", "test"])
        self.assertEqual(mock_get_installed_version_of_package.call_count, 2)

    @patch('enmutils_int.bin.update_enmutils_rpm.check_nexus_version')
    def test_get_available_versions_from_nexus__is_successful(self, mock_check_nexus_version):
        mock_check_nexus_version.return_value = "1.3"
        update_enmutils_rpm._get_available_versions_from_nexus(["eric", "test"], "1.2")
        self.assertEqual(mock_check_nexus_version.call_count, 2)

    def test_check_package_versions_match__is_successful(self):
        self.assertRaises(RuntimeError, update_enmutils_rpm._check_package_versions_match,
                          {'test': '1.2', 'eric': '1.4'}, ["eric", "test"], "1.2")

    def test_check_package_versions_match__raises_run_time_error(self):
        self.assertRaises(RuntimeError, update_enmutils_rpm._check_package_versions_match,
                          {'test': None, 'eric': None}, ["eric", "test"], "1.5")

    def test_check_package_versions_match__raises_run_time_error_if_version_is_None(self):
        update_enmutils_rpm._check_package_versions_match({'test': None, 'eric': None},
                                                          ["eric", "test"], None)

    def test_verify_packages_installed__is_successful(self):
        update_enmutils_rpm._verify_packages_installed([], {"int": "1.2", "prod": "1.2"},
                                                       {"int": "1.2", "prod": "1.2"}, ["int", "prod"])

    def test_verify_packages_installed__raises_run_time_error(self):
        self.assertRaises(RuntimeError, update_enmutils_rpm._verify_packages_installed, [],
                          {"int": "1.2", "prod": "1.2"}, {"int": "1.4", "prod": "1.4"}, ["int", "prod"])

    def test_verify_packages_installed__if_packages_to_update_is_not_empty(self):
        update_enmutils_rpm._verify_packages_installed(["int"],
                                                       {"int": "1.2", "prod": "1.2"},
                                                       {"int": "1.4", "prod": "1.4"},
                                                       ["int", "prod"])

    @patch('enmutils_int.bin.update_enmutils_rpm._get_installed_version_of_package')
    @patch('enmutils_int.bin.update_enmutils_rpm.get_package_version_from_yum_repo')
    @patch('enmutils_int.bin.update_enmutils_rpm.check_nexus_version')
    def test_get_status__is_successful(self, *_):
        update_enmutils_rpm.get_status()

    @patch('enmutils_int.bin.update_enmutils_rpm.os.path.join')
    def test_get_enm_iso_pathname_regex__is_successful(self, _):
        update_enmutils_rpm.get_enm_iso_pathname_regex()

    @patch('enmutils_int.bin.update_enmutils_rpm.http.get',
           side_effect=[Mock(ok=True, iter_content=Mock(return_value=iter(["aaaa", "Bbb"])))])
    @patch('enmutils_int.bin.update_enmutils_rpm.check_deployment_to_disable_proxy')
    @patch('enmutils_int.bin.update_enmutils_rpm.log.logger.debug')
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.delete_file')
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.bin.update_enmutils_rpm.os.path.join', return_value="testpath.txt")
    @patch('enmutils_int.bin.update_enmutils_rpm._get_rpm_name')
    def test__download_package__is_successful(self, *_):
        update_enmutils_rpm._download_package("eric", "1.1")

    @patch('enmutils_int.bin.update_enmutils_rpm.http.get',
           side_effect=[Mock(ok=False)])
    @patch('enmutils_int.bin.update_enmutils_rpm.check_deployment_to_disable_proxy')
    @patch('enmutils_int.bin.update_enmutils_rpm.log.logger.debug')
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.delete_file')
    @patch('enmutils_int.bin.update_enmutils_rpm.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.bin.update_enmutils_rpm.os.path.join', return_value="testpath.txt")
    @patch('enmutils_int.bin.update_enmutils_rpm._get_rpm_name')
    def test__download_package__if_file_is_not_existed(self, *_):
        update_enmutils_rpm._download_package("eric", "1.1")

    @patch('enmutils_int.bin.update_enmutils_rpm._get_package_update_list',
           return_value=(["int", "prod"], "1.2.0"))
    @patch('enmutils_int.bin.update_enmutils_rpm._install_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm._download_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm.stop_deleted_or_renamed_profiles')
    @patch('enmutils_int.bin.update_enmutils_rpm._remove_unneeded_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm.os.path.exists', return_value=True)
    def test_update_enmutils_rpm__is_successful(self, *_):
        update_enmutils_rpm.update_enmutils_rpm(("prod", "int"))

    @patch('enmutils_int.bin.update_enmutils_rpm._get_package_update_list',
           return_value=([], "1.2.0"))
    @patch('enmutils_int.bin.update_enmutils_rpm._install_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm._download_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm.stop_deleted_or_renamed_profiles')
    @patch('enmutils_int.bin.update_enmutils_rpm._remove_unneeded_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm.os.path.exists', return_value=True)
    def test_update_enmutils_rpm__if_no_packages_to_update(self, *_):
        update_enmutils_rpm.update_enmutils_rpm(("prod", "int"))

    @patch('enmutils_int.bin.update_enmutils_rpm._get_package_update_list', side_effect=Exception("error"))
    @patch('enmutils_int.bin.update_enmutils_rpm._install_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm._download_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm.stop_deleted_or_renamed_profiles')
    @patch('enmutils_int.bin.update_enmutils_rpm._remove_unneeded_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm.os.path.exists', return_value=True)
    def test_update_enmutils_rpm__raises_exception(self, *_):
        self.assertEqual(2, update_enmutils_rpm.update_enmutils_rpm(("prod", "int")))

    @patch('enmutils_int.bin.update_enmutils_rpm._get_package_update_list',
           return_value=(["int", "prod"], "1.2.0"))
    @patch('enmutils_int.bin.update_enmutils_rpm._install_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm._download_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm.stop_deleted_or_renamed_profiles',
           side_effect=RpmMisMatch("error"))
    @patch('enmutils_int.bin.update_enmutils_rpm._remove_unneeded_packages')
    @patch('enmutils_int.bin.update_enmutils_rpm.os.path.exists', return_value=True)
    def test_update_enmutils_rpm__if_stop_deleted_or_renamed_profiles_raises_exception(self, *_):
        self.assertEqual(2, update_enmutils_rpm.update_enmutils_rpm(("prod", "int")))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
