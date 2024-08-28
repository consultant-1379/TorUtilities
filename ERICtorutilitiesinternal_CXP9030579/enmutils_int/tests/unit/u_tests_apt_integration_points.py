import json
from time import sleep

import unittest2
from mock import patch, Mock, PropertyMock
from parameterizedtestcase import ParameterizedTestCase

import u_tests_fmx
from enmutils.lib import (config, cache, enm_node, enm_user_2, exception, exceptions, filesystem, mutexer,
                          persistence, shell, thread_queue)
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib import fmx_mgr
from enmutils_int.lib import profile, node_pool_mgr, pm_subscriptions
from enmutils_int.lib.nrm_default_configurations import profile_values
from enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow import Fm0506
from enmutils_int.lib.workload.doc_01 import DOC_01
from testslib import unit_test_utils

MESSAGE = "If there is a failing test-case you are about to push a change that will break the automated " \
          "performance testing framework (APT). \n Actions: \n1) Please let team APT know ASAP \n3) Skip the " \
          "failing test-case and continue with your push.\nIMPORTANT: Do not modify a test-case to get it passing " \
          "without notifying team APT"


class BaseIntegrationPointsTestCase(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()


class AptCacheIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_is_emp_method_is_available_and_returns_a_bool(self):
        self.assertTrue(isinstance(cache.is_emp(), bool), msg=MESSAGE)


class AptConfigIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_get_log_dir_method_is_available_and_returns_a_string(self):
        path = config.get_log_dir()
        self.assertTrue(isinstance(path, str), msg=MESSAGE)

    def test_set_prop_and_get_prop_methods_are_avaiable(self):
        key = "some_test_key"
        config.set_prop(key, 3)
        self.assertEqual(config.get_prop(key), 3, msg=MESSAGE)


class AptEnmNodeIntegrationPoint(BaseIntegrationPointsTestCase):

    def test_enm_node_module_has_a_base_node_class(self):
        self.assertTrue(hasattr(enm_node, "BaseNode"), msg=MESSAGE)


class AptEnmUserIntegrationPoint(BaseIntegrationPointsTestCase):

    @patch("enmutils.lib.enm_user_2.User.open_enmscripting_session")
    @patch("enmutils.lib.enm_user_2.User._execute_cmd")
    @patch("enmutils.lib.enm_user_2.log.logger.debug")
    def test_enm_execute_logs_expected_text_when_called(self, mock_debug, mock_execute_cmd, _):
        mock_execute_cmd.side_effect = RuntimeError()

        user = enm_user_2.User("test_user")
        user.enm_session = Mock()

        try:
            user.enm_execute("ls")
        except EnmApplicationError:
            pass
        except RuntimeError:
            pass
        self.assertTrue("Failed while executing ScriptEngine command" in mock_debug.call_args[0][0], MESSAGE)

    def test_get_or_create_admin_user_method_is_available(self):
        self.assertTrue(hasattr(enm_user_2, "get_or_create_admin_user"), msg=MESSAGE)


class AptExceptionIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_process_exception_method_is_available(self):
        self.assertTrue(hasattr(exception, "process_exception"), msg=MESSAGE)


class AptFileSystemIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_file_system_module_has_a_does_dir_exist_function(self):
        self.assertTrue(hasattr(filesystem, "does_dir_exist"))

    def test_file_system_module_has_a_does_file_exist_function(self):
        self.assertTrue(hasattr(filesystem, "does_file_exist"))


class AptFMLoadIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_fm_0506_nodes_assigned_parameter_is_still_available_in_flow_module(self):
        self.assertTrue(hasattr(Fm0506(), "PERCENTAGE_NODES_ASSIGNED_TO_POLICY"))


class AptMutexerIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_can_add_persisted_mutex_using_mutex_function(self):
        mutex_key = "apt-integration-test"
        with mutexer.mutex(mutex_key, persisted=True):
            self.assertTrue(persistence.mutex_db().has_key("mutex-{0}".format(mutex_key)))

        self.assertFalse(persistence.mutex_db().has_key("mutex-{0}".format(mutex_key)))


class AptPersistenceIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_get_db_method_is_available_and_returns_the_required_db_index(self):
        index = 0
        required_db = persistence.get_db(index)
        self.assertEqual(index, required_db.index, msg=MESSAGE)

    def test_persistence_has_a_index_db_function_which_returns_a_db_instance(self):
        self.assertTrue(isinstance(persistence.index_db(), persistence.Persistence))

    def test_setting_and_checking_for_a_key_in_persistence(self):
        key = "my_key"
        persistence.set(key, 1, 0.1)
        self.assertTrue(persistence.has_key(key), msg=MESSAGE)
        sleep(0.2)
        self.assertFalse(persistence.has_key(key), msg=MESSAGE)

    def test_removing_a_key_from_persistence_using_the_remove_function(self):
        key = "my_key"
        persistence.set(key, 1, 100)
        self.assertTrue(persistence.has_key(key), msg=MESSAGE)
        persistence.remove(key)
        self.assertFalse(persistence.has_key(key), msg=MESSAGE)


class AptPmSubscriptionsIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_system_configs_have_sys_defined_subscription_pattern_parameter_on_a_system_defined_subscription_profile(self):
        pm_04_values = profile_values.networks.get("forty_k_network").get("pm").get("PM_04")

        self.assertIn("SYS_DEF_SUB_PATTERN", pm_04_values, MESSAGE)

    def test_get_system_subscription_name_by_pattern_method_is_available_on_subscription_class(self):
        subscription_cls = pm_subscriptions.Subscription

        self.assertTrue(hasattr(subscription_cls, "get_system_subscription_name_by_pattern"), msg=MESSAGE)

    def test_get_subscription_method_is_available_on_subscription_object(self):
        subscription = pm_subscriptions.Subscription("Test Sub")

        self.assertTrue(hasattr(subscription, "get_subscription"), MESSAGE)


class AptProfileIntegrationPoints(BaseIntegrationPointsTestCase):

    def setUp(self):
        super(AptProfileIntegrationPoints, self).setUp()
        profile.Profile.NAME = "TEST"  # Allows us to set it once created
        self.prf = profile.Profile()

    def test_profile_errors_persistence_key_has_not_changed(self):
        profile_name = "XXX_01"
        self.prf.NAME = profile_name

        self.assertEqual(self.prf._profile_error_key, "{0}-errors".format(profile_name), MESSAGE)

    def test_profile_is_persisted_using_the_profiles_name(self):
        profile_name = "XXX_01"
        self.prf.NAME = profile_name

        self.prf.persist()
        self.assertTrue(persistence.has_key(profile_name), MESSAGE)

    def test_profile_is_running_parameters_have_not_changed(self):
        self.assertTrue(all([hasattr(self.prf, "daemon_died"), hasattr(self.prf, "run_profile")]), MESSAGE)

    def test_profile_state_parameter_is_still_available(self):
        self.assertTrue(hasattr(self.prf, "state"), MESSAGE)

    def test_profile_teardown_attribute_hasnt_changed(self):
        if hasattr(self.prf, "teardown_list"):
            self.assertTrue(isinstance(self.prf.teardown_list, list), MESSAGE)
        else:
            self.fail(MESSAGE)

    @ParameterizedTestCase.parameterize(
        ["expected_type", "error"],
        [("ProfileError", exceptions.ProfileError),
         ("EnmApplicationError", exceptions.EnmApplicationError),
         ("EnvironError", exceptions.EnvironError),
         ("NetsimError", exceptions.NetsimError)]
    )
    def test_profile_uses_error_class_names_as_keys_when_logging_errors(self, type_name, error):
        self.assertEqual(type_name, self.prf._process_error_for_type(error()), MESSAGE)

    @patch("enmutils_int.lib.profile.Profile.logger")
    def test_profile_persists_error_with_expected_error_type_as_key(self, _):
        profile_name = "XXX_01"
        self.prf.NAME = profile_name

        self.prf.add_error_as_exception(exceptions.ProfileError("Test Error"))

        err_list = persistence.get("{0}-errors".format(profile_name))
        self.assertTrue("REASON" in err_list[0].keys(), MESSAGE)
        self.assertTrue("TIMESTAMP" in err_list[0].keys(), MESSAGE)
        self.assertTrue("ProfileError" in err_list[0]["REASON"], MESSAGE)

    def test_amos_configuration_contain_a_commands_property_used_in_asserting_on_load_produced_by_the_profiles(self):
        amos_01_values = profile_values.networks.get("forty_k_network").get("amos").get("AMOS_01")

        self.assertIn("COMMANDS", amos_01_values, MESSAGE)

    def test_amos_05_configuration_contains_a_batch_commands_or_commands_property_used_in_asserting_on_load_produced_by_that_profile(self):
        amos_05_values = profile_values.networks.get("forty_k_network").get("amos").get("AMOS_05")

        try:
            self.assertIn("BATCH_COMMANDS", amos_05_values, MESSAGE)
        except AssertionError:
            self.assertIn("COMMANDS", amos_05_values, MESSAGE)


class AptShellIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_run_local_command_method_is_available_and_accepts_a_command_object(self):
        cmd = shell.Command("ls", log_cmd=False)
        resp = shell.run_local_cmd(cmd)

        self.assertTrue(isinstance(resp, shell.Response), msg=MESSAGE)
        self.assertEqual(resp.rc, 0, msg=MESSAGE)
        self.assertTrue(hasattr(resp, "stdout"))


class AptThreadQueueIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_thread_queue_module_has_threadqueue_class_with_execute_method(self):
        self.assertTrue(hasattr(thread_queue, "ThreadQueue"), msg=MESSAGE)
        self.assertTrue(hasattr(thread_queue.ThreadQueue([1, 2, 3], func_ref=unit_test_utils.setup), "execute"), msg=MESSAGE)

    def test_thread_queue_class_has_work_entries_property(self):
        self.assertTrue(hasattr(thread_queue.ThreadQueue([1, 2, 3], func_ref=unit_test_utils.setup), "work_entries"), msg=MESSAGE)


class AptWorkloadIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_workload_pool_uses_same_key_in_persistence(self):
        pl = node_pool_mgr.get_pool()
        pl.persist()

        self.assertTrue(persistence.has_key("workload_pool"), MESSAGE)

    @patch("enmutils_int.lib.profile.node_pool_mgr")
    @patch("enmutils_int.lib.profile.nodemanager_adaptor")
    @patch("enmutils_int.lib.profile.common_utils.terminate_user_sessions")
    @patch('enmutils_int.lib.workload.doc_01.DOC_01.cloud', new_callable=PropertyMock, return_value=False)
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch('enmutils_int.lib.workload.doc_01.DOC_01.kill_completed_pid')
    @patch('enmutils_int.lib.workload.doc_01.DOC_01.user_cleanup')
    @patch("enmutils_int.lib.workload.doc_01.DOC_01.run")
    def test_active_workload_profiles__uses_the_same_key_in_persistence(self, mock_run, *_):
        mock_run.return_value = None
        doc_profile = DOC_01()
        doc_profile.LOG_AFTER_COMPLETED = False
        doc_profile()
        self.assertTrue(persistence.get("active_workload_profiles"), msg=MESSAGE)
        doc_profile.teardown()


class AptNrmConfigIntegrationPoints(BaseIntegrationPointsTestCase):

    def test_loading_basic_network_module_doesnot_raise_import_error(self):
        try:
            from enmutils_int.lib.nrm_default_configurations import basic_network  # pylint: disable=unused-variable, locally-disabled
        except ImportError:
            self.assertTrue(False, MESSAGE)  # pylint: disable=redundant-unittest-assert, locally-disabled

    def test_priority_attribute_is_set_in_basic_network_module(self):
        from enmutils_int.lib.nrm_default_configurations import basic_network
        priority = basic_network.basic["basic"]["fm"]["FM_01"][basic_network.PRIORITY]
        self.assertEqual(priority, 1, MESSAGE)
        self.assertTrue(basic_network.SUPPORTED in basic_network.basic["basic"]["fm"]["FM_01"].keys(), MESSAGE)


class AptFmxProfileLoadIntegrationPoints(BaseIntegrationPointsTestCase):

    URL = 'http://locahost'
    fmx_url = '/fmxadminws/v1/module/listLoaded'
    modules = ['NSX_Configuration', 'baseblocks-module', 'enm-blocks-module', 'enmcli-blocks-module']
    application_json = 'application/json'
    vm_addresses = ["svc-3-fmx", "svc-4-fmx"]

    def setUp(self):

        self.user = Mock()
        self.fmx_mgr_obj = fmx_mgr.FmxMgr(user=self.user, all_modules=self.modules, vm_addresses=self.vm_addresses)

    def test_get_loaded_modules_is_available_on_FmxMgr_class(self):
        self.assertTrue(hasattr(self.fmx_mgr_obj, "get_loaded_modules"), MESSAGE)

    def test_get_loaded_rule_active_modules_is_available_on_FmxMgr_class(self):
        self.assertTrue(hasattr(self.fmx_mgr_obj, "_get_loaded_rule_active_modules"), MESSAGE)

    def test_get_loaded_rule_active_modules_returns_three_modules_list(self):
        response = Mock(ok=True)
        response.json.return_value = json.loads(u_tests_fmx.list_loaded_body_json)
        self.user.get.return_value = response
        fmx_modules_list = len(self.fmx_mgr_obj._get_loaded_rule_active_modules(self.fmx_mgr_obj.get_loaded_modules()))
        self.assertEqual(fmx_modules_list, 3, MESSAGE)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
