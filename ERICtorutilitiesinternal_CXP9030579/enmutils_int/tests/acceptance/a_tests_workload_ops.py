#!/usr/bin/env python
import commands
import imp
import os
import pkgutil
import subprocess
import textwrap
import time

import unittest2
from enmutils.lib import persistence, shell, exceptions
from enmutils_int.lib import workload_ops, workload_ops_node_operations
from enmutils_int.lib.services import nodemanager_adaptor
from enmutils_int.lib.services.service_registry import SERVICE_UNDER_TEST_FLAG_FILE, SERVICE_REGISTRY_FILE
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec

ENMUTILS_INT_PATH = pkgutil.get_loader('enmutils_int').filename


class WorkloadOpsAcceptanceTest(unittest2.TestCase):
    NUM_NODES = {'RadioNode': 1}
    ARGUMENT_DICT = {}

    profile_template = textwrap.dedent(
        """
        import time
        from enmutils_int.lib.profile import Profile

        class {profile_name}(Profile):
            NAME = '{profile_name}'
            SUPPORTED = {supported}
            NUM_NODES = {{'RadioNode': 1}}
            RETAIN_NODES_AFTER_COMPLETED = True

            def run(self):
                pass

        {profile_name_lower} = {profile_name}()
        """)

    schedule_template = textwrap.dedent(
        """
        from collections import OrderedDict

        NON_EXCLUSIVE = OrderedDict()
        test_app = NON_EXCLUSIVE["TEST_APP"] = OrderedDict()
        {profile_schedule}
        WORKLOAD = [NON_EXCLUSIVE]
        """)

    profile_schedule = """test_app["{profile_name}"] = (1, 1)"""

    SUPPORTED_VALUES = [True, True, True, False, 'REL', 'RVB']

    @classmethod
    def _create_test_profile(cls, num_required=1, supported_values=None):
        # Create a test profile
        cls.profile_names = []
        cls.profile_file_paths = []
        for i in range(1, num_required + 1):
            profile_name = "TEST_PROFILE_{}".format(i)
            cls.profile_names.append(profile_name)
            profile_file_path = os.path.join(ENMUTILS_INT_PATH, "lib", "workload", profile_name.lower())
            cls.profile_file_paths.append(profile_file_path)
            supported_value = supported_values[i - 1] if supported_values else True
            with open("{}.py".format(profile_file_path), "w") as profile_file:
                profile_file.write(cls.profile_template
                                   .format(profile_name=profile_name,
                                           supported=supported_value if isinstance(supported_value, bool)
                                           else "'{0}'".format(supported_value),
                                           profile_name_lower=profile_name.lower()))

        # Create the schedule
        schedule = ""
        for profile_name in cls.profile_names:
            schedule = ("{existing_schedule}\n{new_schedule}"
                        .format(existing_schedule=schedule,
                                new_schedule=cls.profile_schedule.format(profile_name=profile_name)))
        cls.SCHEDULE_NAME = "test_schedule"
        cls.schedule_file_path = "{0}.py".format(os.path.join(ENMUTILS_INT_PATH, "lib", "schedules",
                                                              cls.SCHEDULE_NAME.lower()))
        with open(cls.schedule_file_path, "w") as schedule_file:
            schedule_file.write(cls.schedule_template.format(profile_schedule=schedule))

    @classmethod
    def _remove_test_profile(cls):
        # Remove the test profile
        for path in cls.profile_file_paths:
            os.remove("{}.py".format(path))
        for path in cls.schedule_file_path:
            if os.path.exists("{}.py".format(path)):
                os.remove("{}.py".format(path))
        for profile_file_path in cls.profile_file_paths:
            if os.path.exists("{}.pyc".format(profile_file_path)):
                os.remove("{}.pyc".format(profile_file_path))

    @classmethod
    def _remove_pid_files(cls):
        # Ensure the pid files are removed:
        for profile_name in cls.profile_names:
            pid_path = '/tmp/enmutils/daemon/{0}'.format(profile_name)
            if os.path.exists(pid_path):
                os.remove(pid_path)

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["ADMINISTRATOR"]
        cls.ARGUMENT_DICT = {"--conf": None, "--no-exclusive": True, "--network-check": False, "--schedule": None,
                             "--category": None, "--errors": None, "--warnings": None, "--force": False,
                             "--force-stop": False, "--errored-nodes": False, "--no-network-size-check": False,
                             "--initial-install-teardown": False, "--json": False, "--lastrun": False,
                             "--network-config": None, "--verbose": False, "--error-type": None, "--supported": False,
                             "--total": None, "--updated": False, "--validate": False, "--include": None,
                             "--release-exclusive-nodes": True, "--csv": False, 'IDENTIFIER': None, 'PROFILES': None,
                             'RANGE': None, "<profiles>": None, "--profiles": None, '--rpm-version': None,
                             '--network-size': None, '--network-type': None, '--priority': None, '--new-only': False,
                             "--list-format": False, '--no-sleep ': True, '--network-values': False}
        cls._create_test_profile(6, cls.SUPPORTED_VALUES)
        cls._remove_pid_files()
        cls.clear_nodes_from_database()
        cls.stop_nodemanager_service()
        cls.start_nodemanager_service()

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)
        cls._remove_test_profile()
        cls._remove_pid_files()
        cls.clear_nodes_from_database()
        cls.stop_nodemanager_service()
        cls.disable_nodemanager_service_in_test_mode()

    def setUp(self):
        func_test_utils.setup(self)
        module_name = os.path.basename(self.schedule_file_path)
        self.schedule = imp.load_source(module_name, self.schedule_file_path).WORKLOAD
        self.node = self.fixture.nodes[0]
        self.arguments = {}

    def tearDown(self):
        func_test_utils.tear_down(self)

    def get_parsed_node_information(self):
        virtual_env = os.environ['VIRTUAL_ENV']
        if "jenkins" in virtual_env:
            nodes_dir = "/opt/ericsson/nssutils/etc/nodes/"
        else:
            user = virtual_env.split("/")[4]
            nodes_dir = "/home/enmutils/bladerunners/{user}/int/nodes/".format(user=user)

        _ = commands.getoutput('rm -f {0}/*-failed'.format(nodes_dir))
        response = shell.run_local_cmd('egrep -nr  "{0}" {1}'.format(self.node.node_id, nodes_dir))
        if response.stdout:
            file_path = response.stdout.split(':')[0]
            node_range = response.stdout.split(':')[1]
            self.arguments = {"IDENTIFIER": file_path, "RANGE": str(int(node_range) - 1)}
        else:
            raise exceptions.EnvironError(response.stdout)

    @staticmethod
    def _poll_for_profile_started(profile_name='TEST_PROFILE_1'):
        iteration = 0
        while not persistence.has_key(profile_name) and iteration < 5:
            time.sleep(1)
            iteration += 1

    @staticmethod
    def _poll_for_profile_stop(profile_name='TEST_PROFILE_1'):
        iteration = 0
        while persistence.has_key("stop_{0}_lock".format(profile_name)) and iteration < 5:
            time.sleep(1)
            iteration += 1

    @staticmethod
    def _get_profile_state(profile_name):
        state = None
        if persistence.has_key(profile_name):
            profile = persistence.get(profile_name)
            state = profile.state if profile else None

        return state

    @staticmethod
    def enable_nodemanager_service_in_test_mode():
        sed_function = 's/"test": false/"test": true/'
        service_registry_file = SERVICE_REGISTRY_FILE.format(service_name=nodemanager_adaptor.SERVICE_NAME)

        command = "sed -i '{0}' {1}".format(sed_function, service_registry_file)
        commands.getoutput(command)

        command = 'touch {0}'.format(SERVICE_UNDER_TEST_FLAG_FILE.format(service_name=nodemanager_adaptor.SERVICE_NAME))
        commands.getoutput(command)

    @staticmethod
    def disable_nodemanager_service_in_test_mode():
        sed_function = 's/"test": true/"test": false/'
        service_registry_file = SERVICE_REGISTRY_FILE.format(service_name=nodemanager_adaptor.SERVICE_NAME)

        command = "sed -i '{0}' {1}".format(sed_function, service_registry_file)
        commands.getoutput(command)

        command = 'rm -f {0}'.format(SERVICE_UNDER_TEST_FLAG_FILE.format(service_name=nodemanager_adaptor.SERVICE_NAME))
        commands.getoutput(command)

    @staticmethod
    def start_nodemanager_service():
        print("Starting nodemanager service - with redis NODE_POOL_DB_INDEX: {0}"
              .format(persistence.NODE_POOL_DB_INDEX))

        command = "> /home/enmutils/services/nodemanager.log"
        commands.getoutput(command)

        shell_script_content = ("export REDIS_DB_INDEX={0}; wl_service {1} &"
                                .format(persistence.NODE_POOL_DB_INDEX, nodemanager_adaptor.SERVICE_NAME))
        acc_test_start_nodemanager_script = "/home/enmutils/.acc_test_start_nodemanager_script"

        command = "echo '{0}' > {1}".format(shell_script_content, acc_test_start_nodemanager_script)
        commands.getoutput(command)

        subprocess.Popen(["/bin/bash", acc_test_start_nodemanager_script], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
        time.sleep(5)

    @staticmethod
    def stop_nodemanager_service():
        command = 'pkill -f "{0} {0}"'.format(nodemanager_adaptor.SERVICE_NAME)
        commands.getoutput(command)

    @staticmethod
    def clear_nodes_from_database():
        command = 'curl -s "http://localhost:5002/api/v1/nodes/depopulate"'
        commands.getoutput(command)

    @func_dec("Workload Ops", "Start one profile")
    def test_01_simple_start_operation_of_one_profile(self):
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        operation = workload_ops.get_workload_operations("start", self.ARGUMENT_DICT,
                                                         profile_names=self.profile_names[:1])
        operation.execute()
        # Give the daemon a chance to kick off and persist profile
        self._poll_for_profile_started(profile_name='TEST_PROFILE_1')
        self.assertTrue(persistence.has_key('TEST_PROFILE_1'))
        # Just checking that the other profiles in the category were not started
        self.assertFalse(persistence.has_key('TEST_PROFILE_2'))

    @func_dec("Workload Ops", "Status operation")
    def test_02_status_operation(self):
        operation = workload_ops.get_workload_operations("status", self.ARGUMENT_DICT)
        operation.execute()
        self.assertEqual(self._get_profile_state("TEST_PROFILE_1"), "COMPLETED")

    @func_dec("Workload Ops", "Stop one profile")
    def test_03_simple_stop_operation(self):
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        operation = workload_ops.get_workload_operations("stop", self.ARGUMENT_DICT,
                                                         profile_names=self.profile_names[:1])
        operation.execute()
        self._poll_for_profile_stop(profile_name='TEST_PROFILE_1')
        self.assertFalse(persistence.has_key('TEST_PROFILE_1'))

    @func_dec("Workload Ops", "Start all profiles in category")
    def test_04_start_operation_for_all_profiles_in_a_category(self):
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        operation1 = workload_ops.get_workload_operations("stop", self.ARGUMENT_DICT, profile_names=self.profile_names)
        operation1.execute()
        operation = workload_ops.get_workload_operations("start", self.ARGUMENT_DICT, profile_names=self.profile_names)
        operation.execute()
        # Give the daemon a chance to kick off and persist profile
        for i in range(len(self.SUPPORTED_VALUES)):
            if self.SUPPORTED_VALUES[i] is True:
                self._poll_for_profile_started(profile_name=self.profile_names[i])
                self.assertTrue(persistence.has_key(self.profile_names[i]))

    @func_dec("Workload Ops", "Stop all started profiles")
    def test_05_stop_operation_stops_all_started_profiles(self):
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        operation = workload_ops.get_workload_operations("stop", self.ARGUMENT_DICT)
        operation.execute()

        for profile_name in self.profile_names:
            self._poll_for_profile_stop(profile_name=profile_name)
            self.assertFalse(persistence.has_key(profile_name))

    @func_dec("Workload Ops", "Start ignores specific profiles")
    def test_06_start_operation_ignores_specified_profiles(self):
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        operation = workload_ops.get_workload_operations(
            "start", self.ARGUMENT_DICT, ignored_profiles=[self.profile_names[0], self.profile_names[-1]],
            profile_names=self.profile_names)
        operation.execute()
        profile_name = self.profile_names[1]
        self._poll_for_profile_started(profile_name=profile_name)
        self.assertTrue(persistence.has_key(profile_name))

        # Check the others didn't start
        self.assertFalse(persistence.has_key(self.profile_names[0]))
        self.assertFalse(persistence.has_key(self.profile_names[-1]))

    @func_dec("Workload Ops", "Workload diff show profiles to be restarted")
    def test_07_workload_diff_show_restarted_operation_runs_without_errors(self):
        self.ARGUMENT_DICT["--updated"] = True
        self.ARGUMENT_DICT["--no-ansi"] = False
        operation = workload_ops.get_workload_operations("diff", self.ARGUMENT_DICT)
        operation.execute()

    @func_dec("Workload Ops", "Workload diff")
    def test_08_workload_diff_operation_runs_without_errors(self):
        self.ARGUMENT_DICT["--no-ansi"] = False
        operation = workload_ops.get_workload_operations("diff", self.ARGUMENT_DICT)
        operation.execute()

    @func_dec("Workload Ops", "Stop specific profiles")
    def test_09_stop_operation_stops_specific_started_profiles(self):
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        operation = workload_ops.get_workload_operations("stop", self.ARGUMENT_DICT)
        operation.execute()

        self._poll_for_profile_stop(profile_name='TEST_PROFILE_2')
        self.assertFalse(persistence.has_key('TEST_PROFILE_2'))

    @func_dec("Workload Ops", "Workload describe operation")
    def test_11_workload_describe_operation_runs_without_errors(self):
        operation = workload_ops.get_workload_operations('describe', self.ARGUMENT_DICT, profile_names=['CMIMPORT_01'])
        operation.execute()

    @func_dec("Workload Ops", "Workload profiles operation")
    def test_12_workload_profiles_operation_runs_without_errors(self):
        operation = workload_ops.get_workload_operations('profiles', self.ARGUMENT_DICT)
        operation.execute()

    @func_dec("Workload Ops", "Workload category operation")
    def test_13_workload_category_operation_runs_without_errors(self):
        operation = workload_ops.get_workload_operations("category", self.ARGUMENT_DICT)
        operation.execute()

    @func_dec("Workload Ops", "Workload start skips unsupported profiles")
    def test_14_workload_start_skips_unsupported_profile(self):
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        operation = workload_ops.get_workload_operations("start", self.ARGUMENT_DICT,
                                                         profile_names=[self.profile_names[3]])
        with self.assertRaises(RuntimeError):
            operation.execute()

    @func_dec("Workload Ops", "Workload start rvb supported profiles")
    def test_15_workload_start_rel_rvb_supported_profiles_with_correct_attributes(self):
        profile_names = ['TEST_PROFILE_5', 'TEST_PROFILE_6']
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        self.ARGUMENT_DICT["--include"] = 'REL,RVB'
        operation = workload_ops.get_workload_operations("start", self.ARGUMENT_DICT, profile_names=profile_names)
        operation.execute()
        # Give the daemon a chance to kick off and persist profile
        for profile_name in profile_names:
            self._poll_for_profile_started(profile_name=profile_name)
            self.assertTrue(persistence.has_key(profile_name))

    @func_dec("Workload Ops", "Start profile and dont allocate exclusive nodes")
    def test_17_nodemanager_service_start_profile_and_dont_allocate_exclusive_nodes(self):
        self.enable_nodemanager_service_in_test_mode()

        profile_name = "TEST_PROFILE_1"
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        self.ARGUMENT_DICT["--no-exclusive"] = True

        operation = workload_ops.get_workload_operations("start", self.ARGUMENT_DICT, profile_names=[profile_name])
        operation.execute()

        # Give the daemon a chance to kick off and persist profile
        self._poll_for_profile_started(profile_name=profile_name)

        self.assertTrue(persistence.has_key(profile_name))
        # Just checking that the other profiles in the category were not started
        self.assertFalse(persistence.has_key("TEST_PROFILE_2"))

        _, nodes_in_query, _ = nodemanager_adaptor.list_nodes(profile=profile_name)
        self.assertEqual(nodes_in_query, 1)

        _, nodes_in_query, _ = nodemanager_adaptor.list_nodes(profile="CMIMPORT_02")
        self.assertEqual(nodes_in_query, 0)

    @func_dec("Workload Ops", "Stop profile and deallocate nodes")
    def test_18_nodemanager_service_stop_profile_and_deallocate_nodes(self):

        profile_name = "TEST_PROFILE_1"
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        operation = workload_ops.get_workload_operations("stop", self.ARGUMENT_DICT, profile_names=[profile_name])
        operation.execute()

        self._poll_for_profile_stop(profile_name=profile_name)
        self.assertFalse(persistence.has_key(profile_name))

        _, nodes_in_query, _ = nodemanager_adaptor.list_nodes(profile=profile_name)
        self.assertEqual(nodes_in_query, 0)

    @func_dec("Workload Ops", "Reset nodes")
    def test_19_nodemanager_service_reset_nodes(self):

        profile_name = "TEST_PROFILE_1"

        command = ('curl -s -H \'Content-Type: application/json\' -X POST -d \'{"profile": "TEST_PROFILE_1", '
                   '"profile_values": {"NUM_NODES": {"ERBS": 1}, "EXCLUSIVE": "True"}}\' '
                   'http://localhost:5002/api/v1/nodes/allocate -H \'accept: application/json\'')
        commands.getoutput(command)

        _, nodes_in_query, _ = nodemanager_adaptor.list_nodes(profile=profile_name)
        self.assertEqual(nodes_in_query, 1)

        operation = workload_ops_node_operations.get_workload_operations("reset", self.ARGUMENT_DICT)
        operation.execute()

        _, nodes_in_query, _ = nodemanager_adaptor.list_nodes(profile=profile_name)
        self.assertEqual(nodes_in_query, 0)

    @func_dec("Workload Ops", "Start profiles and allocate exclusive nodes")
    def test_20_nodemanager_service_start_profile_and_allocate_exclusive_nodes(self):

        profile_name = "TEST_PROFILE_2"
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        self.ARGUMENT_DICT["--no-exclusive"] = False

        operation = workload_ops.get_workload_operations("start", self.ARGUMENT_DICT, profile_names=[profile_name])
        operation.execute()

        # Give the daemon a chance to kick off and persist profile
        self._poll_for_profile_started(profile_name=profile_name)

        self.assertTrue(persistence.has_key(profile_name))
        # Just checking that the other profiles in the category were not started
        self.assertFalse(persistence.has_key("TEST_PROFILE_1"))

        _, nodes_in_query, _ = nodemanager_adaptor.list_nodes(profile="CMIMPORT_02")
        self.assertNotEquals(nodes_in_query, 0)

    @func_dec("Workload Ops", "Stop profile and deallocate exclusive nodes")
    def test_21_nodemanager_service_stop_profile_and_deallocate_exclusive_nodes(self):

        profile_name = "TEST_PROFILE_2"
        self.ARGUMENT_DICT["--schedule"] = self.schedule_file_path
        self.ARGUMENT_DICT["--no-exclusive"] = True
        self.ARGUMENT_DICT["--release-exclusive_nodes"] = True
        operation = workload_ops.get_workload_operations("stop", self.ARGUMENT_DICT, profile_names=[profile_name])
        operation.execute()

        self._poll_for_profile_stop(profile_name=profile_name)
        self.assertFalse(persistence.has_key(profile_name))

        _, nodes_in_query, _ = nodemanager_adaptor.list_nodes(profile=profile_name)
        self.assertEqual(nodes_in_query, 0)

        _, nodes_in_query, _ = nodemanager_adaptor.list_nodes(profile="CMIMPORT_02")
        self.assertEqual(nodes_in_query, 0)

    @func_dec("Workload Ops", "Remove all nodes from workload pool")
    def test_22_nodemanager_service_remove_all_nodes_from_pool(self):
        self.get_parsed_node_information()
        nodemanager_adaptor.add_nodes(self.arguments)
        nodemanager_adaptor.remove_nodes({"RANGE": None, 'IDENTIFIER': 'all', 'force': True})
        _, _, nodes_in_query = nodemanager_adaptor.list_nodes()
        self.assertNotIn(self.node.node_id, [node.node_id for node in nodes_in_query])

    @func_dec("Workload Ops", "Add node to workload pool")
    def test_23_nodemanager_service_adds_node_to_pool(self):
        self.get_parsed_node_information()
        nodemanager_adaptor.add_nodes(self.arguments)
        _, _, nodes_in_query = nodemanager_adaptor.list_nodes()
        self.assertIn(self.node.node_id, [node.node_id for node in nodes_in_query])

    @func_dec("Workload Ops", "Remove node from workload pool")
    def test_24_nodemanager_service_removes_node_from_pool(self):
        self.get_parsed_node_information()
        nodemanager_adaptor.remove_nodes(self.arguments)
        _, _, nodes_in_query = nodemanager_adaptor.list_nodes()
        self.assertNotIn(self.node.node_id, [node.node_id for node in nodes_in_query])


if __name__ == '__main__':
    unittest2.main(verbosity=2)
