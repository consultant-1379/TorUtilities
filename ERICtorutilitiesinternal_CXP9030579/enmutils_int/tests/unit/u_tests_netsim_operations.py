#!/usr/bin/env python
import unittest2

from enmutils_int.lib.netsim_operations import NetsimOperation, SimulationCommand
from enmutils_int.lib.netsim_operations import AlarmBurst, AVCBurst, MCDBurst, Burst, PowerNodes
from enmutils_int.lib.netsim_operations import FailedNetsimOperation, NetsimError

from testslib import unit_test_utils
from mock import patch, Mock
from parameterizedtestcase import ParameterizedTestCase


class NetsimOperationsUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.nodes = unit_test_utils.setup_test_node_objects(20)
        for i in range(len(self.nodes) - 10):
            if i < 10:
                self.nodes[i].simulation = "LTE08"
            else:
                self.nodes[i].netsim = "netsimlin123"

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_netsimoperation_constructor_groups_nodes_correctly(self):
        ne_type = self.nodes[0].NE_TYPE
        netsim_operation = NetsimOperation(self.nodes)
        self.assertEqual(len(netsim_operation.node_groups[ne_type]), 2)
        for group in netsim_operation.node_groups[ne_type]:
            self.assertEqual(len(group[2]), 10)

    def test_netsimoperation_constructor_raises_attribute_error(self):
        self.assertRaises(AttributeError, NetsimOperation, [])

    @patch('enmutils_int.lib.netsim_operations.NetsimOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.netsim_operations.log.logger.debug')
    def test_execute__single_sim_success(self, mock_debug, _):
        sim_cmd = Mock()
        sim_cmd.command = "cmd"
        sim_cmd.execute.return_value = {"NODE": "RESULT: SUCCESS"}
        netsim_operation = NetsimOperation([])
        netsim_operation.execute([sim_cmd])
        mock_debug.assert_called_with("Successfully ran netsim cmd operation on all nodes")

    @patch("enmutils_int.lib.netsim_operations.netsim_executor")
    def test_taskset_is_success(self, mock_netsim_executor, ):
        nodes = self.nodes[:5]
        expected_result = {'ERBS0001': 'OK', 'ERBS0002': 'OK', 'ERBS0003': 'OK', 'ERBS0004': 'OK', 'ERBS0005': 'OK'}
        mock_netsim_executor.run_ne_cmd.return_value = expected_result
        netsim_operation = NetsimOperation(nodes)
        simcmd = SimulationCommand(nodes[0].netsim, nodes[0].simulation, nodes, ".showburst;")
        result = netsim_operation.taskset(simcmd)
        self.assertEqual(result, expected_result)

    @patch("enmutils_int.lib.netsim_operations.node_pool_mgr.group_nodes_per_sim", return_value={})
    @patch("enmutils_int.lib.netsim_operations.thread_queue.ThreadQueue")
    def test_execute__raises_failed_netsim_operation(self, mock_queue, _):
        sim_cmd = Mock()
        sim_cmd.command = "cmd"
        nodes = [Mock()] * 2
        mock_queue.exceptions_raised = True
        netsim_operations = NetsimOperation(nodes)
        self.assertRaises(FailedNetsimOperation, netsim_operations.execute, [sim_cmd] * 2)

    @patch("enmutils_int.lib.netsim_operations.thread_queue")
    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_netsimoperation_execute_cmd_as_string_raises_correct_exception_with_nodes_attached(self,
                                                                                                mock_netsim_run_cmd,
                                                                                                mock_thread_queue):
        nodes = self.nodes[:5]
        netsim_operation = NetsimOperation(nodes)
        response = Mock()
        response.ok = True
        response.stdout = "Fail, invalid command"
        mock_netsim_run_cmd.return_value = response
        mock_thread_queue.ThreadQueue.return_value.exceptions_raised = 5
        try:
            netsim_operation.execute_command_string("invalid command")
        except FailedNetsimOperation as e:
            for node in nodes:
                self.assertTrue(node in e.nodes)
        else:
            self.fail("Failed to raise FailedNetsimOperation exception from execute method")

    @patch("enmutils_int.lib.netsim_operations.thread_queue")
    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_netsimoperation_execute_cmd_as_string_raises_netsim_error(self, mock_netsim_run_cmd, mock_thread_queue):
        netsim_operation = NetsimOperation(self.nodes)
        response = Mock()
        response.ok = True
        response.stdout = "OK"
        mock_netsim_run_cmd.return_value = response
        mock_thread_queue.ThreadQueue.return_value.exceptions_raised = 0
        mock_thread_queue.ThreadQueue.return_value.work_entries = [Mock(), Mock()]
        mock_thread_queue.work_entry.result.side_effect = NetsimError
        self.assertRaises(NetsimError, netsim_operation.execute_command_string, "showbursts;")

    @patch("enmutils_int.lib.netsim_operations.thread_queue")
    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_netsimoperation_execute_cmd_as_string_runs_successfully(self, mock_netsim_run_cmd, mock_thread_queue):
        work_entry = Mock()
        work_entry.result = None
        netsim_operation = NetsimOperation(self.nodes)
        response = Mock()
        response.ok = True
        response.stdout = "OK"
        mock_netsim_run_cmd.return_value = response
        mock_thread_queue.ThreadQueue.return_value.exceptions_raised = 0
        mock_thread_queue.ThreadQueue.return_value.work_entries = [work_entry]
        netsim_operation.execute_command_string("showbursts;")
        self.assertTrue(mock_thread_queue.ThreadQueue.called)

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_netsimoperation_execute_on_simulation_is_success(self, mock_netsim_run_cmd):
        netsim_operation = NetsimOperation(self.nodes)
        response = Mock()
        response.ok = True
        response.stdout = "OK"
        mock_netsim_run_cmd.return_value = response
        netsim_operation._execute_on_simulation(self.nodes[0].netsim, self.nodes[0].simulation, self.nodes[:5], "showbursts;")
        self.assertTrue(mock_netsim_run_cmd.called)

    @patch("enmutils_int.lib.netsim_operations.thread_queue")
    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_teardown(self, mock_netsim_run_cmd, mock_thread_queue):
        burst = Burst(self.nodes, "111")
        response = Mock()
        response.ok = True
        response.stdout = "OK"
        mock_netsim_run_cmd.return_value = response
        mock_thread_queue.ThreadQueue.return_value.exceptions_raised = 0
        mock_thread_queue.ThreadQueue.return_value.work_entries = []
        burst._teardown()
        self.assertTrue(mock_thread_queue.ThreadQueue.called)

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_cpp(self, mock_run_cmds):
        node_names_list = []
        burst = AlarmBurst(self.nodes[:5], burst_id="111", burst_rate=15, duration=30,
                           severity="indeterminate", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, host, simulation, node_names, _ = args
        self.assertEqual(command,
                         'alarmburst:id=111,freq=3.0,num_alarms=90,severity=1,clear_after_burst=false,loop=false,'
                         'cease_after=1,mo_instance="%mibprefix,ManagedElement=1,Equipment=1",'
                         'cause="%unique",type=ET_COMMUNICATIONS_ALARM,problem="",text="mock text";')
        for node in self.nodes[:5]:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)
        self.assertEqual(simulation, 'LTE08')
        self.assertEqual(host, 'netsimlin537')

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_bsc(self, mock_run_cmds):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='BSC')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30, problem="FM GSM Profile Test",
                           severity="critical", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, host, simulation, node_names, _ = args
        self.assertEqual(command,
                         'axealarmburst_gsm:NAME=GSMBURST,ID=111,FREQ=3.0,BURST=90,CLASS=1,loop=false,ACTIVE=2,CAT=1,'
                         'PRCA=40,TEXT="unique 5",INFO1="FM GSM Profile Test",I_TIME=0;')
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)
        self.assertEqual(simulation, 'LTE07')
        self.assertEqual(host, 'netsimlin537')

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_msc_bc_bsp(self, mock_run_cmds):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='MSC-BC-BSP')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=0.015, duration=60 * 60, problem="FM GSM Profile Test",
                           severity="critical", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, host, simulation, node_names, _ = args
        self.assertEqual(command,
                         'axealarmburst:NAME=GSMBURST,ID=111,FREQ=0.005,BURST=18,CLASS=1,loop=false,ACTIVE=2,CAT=1,'
                         'PRCA=40,TEXT="unique 5",INFO1="FM GSM Profile Test",I_TIME=0;')
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)
        self.assertEqual(simulation, 'LTE07')
        self.assertEqual(host, 'netsimlin537')

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_msc_bc_is(self, mock_run_cmds):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='MSC-BC-IS')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=60 * 60, problem="FM GSM Profile Test",
                           severity="critical", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, host, simulation, node_names, _ = args
        self.assertEqual(command,
                         'axealarmburst:NAME=GSMBURST,ID=111,FREQ=0.273,BURST=982,CLASS=1,loop=false,ACTIVE=2,CAT=1,'
                         'PRCA=40,TEXT="unique 5",INFO1="FM GSM Profile Test",I_TIME=0;')
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)
        self.assertEqual(simulation, 'LTE07')
        self.assertEqual(host, 'netsimlin537')

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_radio_node(self, mock_run_cmds):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='RadioNode')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30,
                           severity="major", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, host, simulation, node_names, _ = args
        self.assertEqual(command,
                         'alarmburst:id=111,freq=3.0,num_alarms=90,severity=major,clear_after_burst=false,loop=false,cease_after=1,'
                         'managed_object="ManagedElement=%nename,Equipment=1",probable_cause=,'
                         'event_type=,specific_problem="",additional_text="NONE";')
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)
        self.assertEqual(simulation, 'LTE07')
        self.assertEqual(host, 'netsimlin537')

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_shared_cnf(self, mock_run_cmds):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='Shared-CNF')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30,
                           severity="major", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, _, _, node_names, _ = args
        self.assertEqual(command,
                         'alarmburst_x:id=111,freq=3.0,num_alarms=90,severity=major,clear_after_burst=true,loop=false,'
                         'cease_after=1,managed_object="ManagedElement=%nename,SystemFunctions=1,SysM=1",'
                         'probable_cause=,event_type=,specific_problem="",additional_text="NONE";')
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_router(self, mock_run_cmds):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='Router_6672')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30,
                           severity="minor", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, host, simulation, node_names, _ = args
        self.assertEqual(command,
                         'alarmburst:id=111,freq=3.0,num_alarms=90,severity=minor,clear_after_burst=false,loop=false,'
                         'cease_after=1,managed_object="ManagedElement=1,SystemFunctions=1,SysM=1",'
                         'probable_cause=,idle_time=0,event_type=,specific_problem="",minor_type=9175121,major_type=193,'
                         'additional_text="NONE";')
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)
        self.assertEqual(simulation, 'LTE07')
        self.assertEqual(host, 'netsimlin537')

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_siu(self, mock_run_cmds):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='SIU02')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30, severity="minor", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, _, _, node_names, _ = args
        self.assertEqual(command,
                         'alarmburst:id=111,freq=3.0,num_alarms=90,severity=3,loop=false,cease_after=1,'
                         'mo_class="Equipment",mo_instance="STN=0,Equipment=1",cause=315,type=4,problem="",'
                         'text="FM Profile Alarm";')
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_tcu(self, mock_run_cmds):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='TCU02')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30, severity="minor", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, _, _, node_names, _ = args
        self.assertEqual(command,
                         'alarmburst:id=111,freq=3.0,num_alarms=90,severity=3,loop=false,cease_after=1,'
                         'mo_class="Equipment",mo_instance="STN=0,Equipment=1",cause=315,type=4,problem="",'
                         'text="FM Profile Alarm";')
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)

    @patch('enmutils_int.lib.netsim_operations.log.logger.debug')
    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_mini_link(self, mock_run_cmds, mock_logger, *_):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='MLTN')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30, severity="minor", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        _, _, _, node_names, _ = args
        self.assertTrue(mock_logger.called)
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_alarmburst_start_command_builds_up_the_correct_start_burst_command_for_ccdm(self, mock_run_cmds):
        node_names_list = []
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='CCDM')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30,
                           severity="minor", text="mock text")
        response = Mock()
        response.ok = True
        response.stdout = "Id: 111\nOK"
        mock_run_cmds.return_value = response
        burst.start()
        args, _ = mock_run_cmds.call_args
        command, host, simulation, node_names, _ = args
        self.assertEqual(command,
                         'alarmburst_x:id=111,freq=3.0,num_alarms=90,severity=minor,clear_after_burst=false,loop=false,'
                         'cease_after=1,managed_object="ManagedElement=1,SystemFunctions=1,SysM=1",'
                         'probable_cause=,idle_time=0,event_type=,specific_problem="",minor_type=9175121,major_type=193,'
                         'additional_text="NONE";')
        for node in nodes:
            node_names_list.append(node.node_name)
        self.assertEqual(node_names, node_names_list)
        self.assertEqual(simulation, 'LTE07')
        self.assertEqual(host, 'netsimlin537')

    @patch('enmutils_int.lib.netsim_operations.AlarmBurst.burst_parameters')
    @patch('enmutils_int.lib.netsim_operations.AlarmBurst.execute')
    @patch('enmutils_int.lib.netsim_operations.AlarmBurst.construct_alarmburst_commands_for_aml_nodes')
    def test_start_aml_is_successful_for_mini_link(self, mock_construct_cmd_for_aml, mock_execute, *_):
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='MINI-LINK-669x')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30,
                           severity="warning", text="mock text")
        mock_construct_cmd_for_aml.return_value = [Mock()]
        burst.start_aml()
        self.assertEqual(mock_execute.call_count, 1)

    @patch('enmutils_int.lib.netsim_operations.AlarmBurst.burst_parameters')
    @patch('enmutils_int.lib.netsim_operations.AlarmBurst.execute')
    @patch('enmutils_int.lib.netsim_operations.AlarmBurst.construct_alarmburst_commands_for_aml_nodes')
    def test_start_aml_is_successful_for_router(self, mock_construct_cmd_for_aml, mock_execute, *_):
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='Router6675')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30,
                           severity="warning", text="mock text")
        mock_construct_cmd_for_aml.return_value = [Mock()]
        burst.start_aml()
        self.assertEqual(mock_execute.call_count, 1)

    @patch('enmutils_int.lib.netsim_operations.SimulationCommand')
    def test_construct_alarmburst_commands_for_aml_nodes_returns_commands_for_mini_link(self, *_):
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='MINI-LINK-669x')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30,
                           severity="warning", text="mock text")
        mo_name = '"MeContext={0},ManagedElement={0},Transport=1,Interfaces=1,Interface=CT-1/1"'
        sim_info = [("ieatnetsimv7004-01", "CORE01-ML-669x-01", nodes)]
        burst_params = [('cease_after', '1'), ('instance', '"Transport=1,Interfaces=1"'),
                        ('class', '"MINI-LINK Traffic Node"'), ('cause', '58'), ('type', '4'), ('problem', '"Test"'),
                        ('text', '"FM Profile Alarm"')]
        cmd_args = [('id', "111"), ('freq', "2"), ('num_alarms', "120"), ('severity', '3'),
                    ('clear_after_burst', "false"), ('loop', "false")]
        cmds_list = burst.construct_alarmburst_commands_for_aml_nodes("MINI-LINK-669x", sim_info, mo_name, burst_params,
                                                                      cmd_args)
        self.assertEqual(len(cmds_list), 5)

    @patch('enmutils_int.lib.netsim_operations.SimulationCommand')
    def test_construct_alarmburst_commands_for_aml_nodes_returns_commands_for_router(self, *_):
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='Router6675')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30,
                           severity="warning", text="mock text")
        mo_name = '"MeContext={0},ManagedElement=1,interfaces=1,interface=1/2"'
        sim_info = [("ieatnetsimv7004-01", "CORE01-RR-6675-01", nodes)]
        burst_params = [('cease_after', '1'), ('managed_object', '"ManagedElement=1,SystemFunctions=1,SysM=1"'),
                        ('probable_cause', '{probable_cause}'), ('idle_time', '0'), ('event_type', '{event_type}'),
                        ('specific_problem', '"{problem}"'), ('minor_type', '9175121'), ('major_type', '193'),
                        ('additional_text', '"NONE"')]
        cmd_args = [('id', "111"), ('freq', "1"), ('num_alarms', "90"),
                    ('severity', "major"), ('clear_after_burst', "false"), ('loop', "false")]
        cmds_list = burst.construct_alarmburst_commands_for_aml_nodes("Router6675", sim_info, mo_name, burst_params,
                                                                      cmd_args)
        self.assertEqual(len(cmds_list), 5)

    def test_alarmburst_burst_parameters_returns_empty_list_for_not_supported_node_type(self):
        nodes = unit_test_utils.setup_test_node_objects(5, primary_type='SGSN')
        burst = AlarmBurst(nodes, burst_id="111", burst_rate=15, duration=30,
                           severity="warning", text="mock text")
        result = burst.burst_parameters("ABC")
        self.assertEqual(result, [])

    @patch("enmutils_int.lib.netsim_executor.run_cmd")
    def test_avcburst_start_builds_correct_start_burst_command_with_movalues_not_list(self, mock_netsim_run_cmd):
        self.nodes = unit_test_utils.setup_test_node_objects(20)
        mo_path = "ManagedElement=1,NodeManagementFunction=1,RbsConfiguration=1"
        mo_attribute = "ossCorbaNameServiceAddress"
        mo_values = "abc.def.ghi"
        burst = AVCBurst(self.nodes, burst_id="222", mo_path=mo_path, mo_attribute=mo_attribute, mo_values=mo_values,
                         duration=30, burst_rate=15)
        response = Mock()
        response.ok = True
        response.stdout = "Id: 222\nOK"
        mock_netsim_run_cmd.return_value = response
        burst.start()
        mock_netsim_run_cmd.assert_called_with(
            'avcburst:id=222,freq=0.75,num_events=23,avcdata="[{\\"ManagedElement=1,NodeManagementFunction=1,RbsConfig'
            'uration=1\\",[{\\"ossCorbaNameServiceAddress\\",\\"abc.def.ghi\\"}]}]",loop=false,'
            'mode=temp,idle_time=0;', 'netsimlin537', 'LTE07',
            ['ERBS0001', 'ERBS0002', 'ERBS0003', 'ERBS0004', 'ERBS0005', 'ERBS0006', 'ERBS0007', 'ERBS0008', 'ERBS0009',
             'ERBS0010', 'ERBS0011', 'ERBS0012', 'ERBS0013', 'ERBS0014', 'ERBS0015', 'ERBS0016', 'ERBS0017', 'ERBS0018',
             'ERBS0019', 'ERBS0020'], None, keep_connection_open=False)

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_avcburst_start_builds_correct_start_burst_command_with_movalues_as_list(self, mock_netsim_run_cmd):
        self.nodes = unit_test_utils.setup_test_node_objects(20)
        mo_path = "ManagedElement=1,NodeManagementFunction=1,RbsConfiguration=1"
        mo_attribute = "ossCorbaNameServiceAddress"
        mo_values = ["abc.def.ghi"]
        burst = AVCBurst(self.nodes, burst_id="222", mo_path=mo_path, mo_attribute=mo_attribute, mo_values=mo_values,
                         duration=30, burst_rate=15)
        response = Mock()
        response.ok = True
        response.stdout = "Id: 222\nOK"
        mock_netsim_run_cmd.return_value = response
        burst.start()
        mock_netsim_run_cmd.assert_called_with(
            'avcburst:id=222,freq=0.75,num_events=23,avcdata="[{\\"ManagedElement=1,NodeManagementFunction=1,RbsConfig'
            'uration=1\\",[{\\"ossCorbaNameServiceAddress\\",\\"abc.def.ghi\\"}]}]",loop=false,'
            'mode=temp,idle_time=0;', 'netsimlin537', 'LTE07',
            ['ERBS0001', 'ERBS0002', 'ERBS0003', 'ERBS0004', 'ERBS0005', 'ERBS0006', 'ERBS0007', 'ERBS0008', 'ERBS0009',
             'ERBS0010', 'ERBS0011', 'ERBS0012', 'ERBS0013', 'ERBS0014', 'ERBS0015', 'ERBS0016', 'ERBS0017', 'ERBS0018',
             'ERBS0019', 'ERBS0020'], None, keep_connection_open=False)

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_avcburst_start_builds_correct_start_burst_command_with_moattributes_as_list(self, mock_netsim_run_cmd):
        self.nodes = unit_test_utils.setup_test_node_objects(5, primary_type="BSC")
        mo_path = "ComTop:ManagedElement=%NENAME%"
        mo_attribute = "None"
        mo_values = [{"userLabel": ["CMSYNC_36_ENMUSA", "CMSYNC_36_ENMITALY"], "siteLocation": ["Sweden", "Ireland"]}]
        burst = AVCBurst(self.nodes, burst_id="222", mo_path=mo_path, mo_attribute=mo_attribute, mo_values=mo_values,
                         duration=60, burst_rate=17.4)
        response = Mock()
        response.ok = True
        response.stdout = "Id: 222\nOK"
        mock_netsim_run_cmd.return_value = response
        burst.start()
        mock_netsim_run_cmd.assert_called_with(
            'avcburst:id=222,freq=3.48,num_events=209,avcdata="[{\\"ComTop:ManagedElement=%NENAME%\\",'
            '[{\\"userLabel\\",\\"CMSYNC_36_ENMUSA\\"}]},{\\"ComTop:ManagedElement=%NENAME%\\",[{\\"userLabel\\",'
            '\\"CMSYNC_36_ENMITALY\\"}]},{\\"ComTop:ManagedElement=%NENAME%\\",[{\\"siteLocation\\",\\"Sweden\\"}]},'
            '{\\"ComTop:ManagedElement=%NENAME%\\",[{\\"siteLocation\\",\\"Ireland\\"}]}]",loop=false,mode=temp,'
            'idle_time=0;', 'netsimlin537', 'LTE07', ['BSC0001', 'BSC0002', 'BSC0003', 'BSC0004', 'BSC0005'], None,
            keep_connection_open=False)

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_mcdburst_creates_the_start_command_correctly(self, mock_netsim_run_cmd):
        self.nodes = unit_test_utils.setup_test_node_objects(10)
        burst = MCDBurst(self.nodes, burst_id='555', duration=10, burst_rate=10,
                         new_mos_info=[{'mo_parent_path': 'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1',
                                        'New_MO_Info': [('EUtranFreqRelation', 'Test')]}])

        response = Mock()
        response.ok = True
        response.stdout = "Id: 555\nOK"
        mock_netsim_run_cmd.return_value = response
        burst.start()
        mock_netsim_run_cmd.assert_called_with(
            'mcdburst:id=555, freq=0.03, num_events=10, mode=temp, loop=asym, idle_time=16, '
            'mcddata="[{\\"ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1\\",'
            '[{\\"EUtranFreqRelation\\",\\"Test\\"}],[]}]";', 'netsimlin537', 'LTE07',
            ['ERBS0001', 'ERBS0002', 'ERBS0003', 'ERBS0004', 'ERBS0005', 'ERBS0006', 'ERBS0007', 'ERBS0008', 'ERBS0009',
             'ERBS0010'], None, keep_connection_open=False)

    @patch("enmutils_int.lib.netsim_operations.netsim_executor.run_cmd")
    def test_mcdburst_resports_an_error_if_mo_already_exists(self, mock_netsim_run_cmd):
        burst = MCDBurst(self.nodes[:10], burst_id='555', duration=10, burst_rate=10,
                         new_mos_info=[
                             {'mo_parent_path': 'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1',
                              'New_MO_Info': [('EUtranFreqRelation', 'Test')]}])

        response = Mock()
        response.ok = True
        response.stdout = 'ERROR: {error,"MO EUtranFreqRelation already defined with name: Test"}'
        mock_netsim_run_cmd.return_value = response
        self.assertRaises(FailedNetsimOperation, burst.start)

    @patch("enmutils_int.lib.netsim_operations.thread_queue")
    def test_power_nodes_start_is_success(self, mock_thread_queue):
        power_nodes = PowerNodes(self.nodes)
        mock_thread_queue.ThreadQueue.return_value.exceptions_raised = 0
        mock_thread_queue.ThreadQueue.return_value.work_entries = []
        power_nodes.start()
        self.assertTrue(mock_thread_queue.ThreadQueue.called)

    @patch("enmutils_int.lib.netsim_operations.thread_queue")
    def test_power_nodes_stop_is_success(self, mock_thread_queue):
        power_nodes = PowerNodes(self.nodes)
        mock_thread_queue.ThreadQueue.return_value.exceptions_raised = 0
        mock_thread_queue.ThreadQueue.return_value.work_entries = []
        power_nodes.stop()
        self.assertTrue(mock_thread_queue.ThreadQueue.called)

    @patch("enmutils_int.lib.netsim_operations.NetsimOperation._execute_on_simulation")
    def test_start_nodes__in_power_nodes_is_successful_against_vapp_nodes(
            self, mock_execute_on_simulation):
        node1 = Mock(netsim="netsim", simulation="sim1")
        power_nodes = PowerNodes([node1])
        response = Mock()
        response.ok = True
        response.stdout = 'OK'
        mock_execute_on_simulation.return_value = response
        power_nodes.start_nodes()
        self.assertTrue(mock_execute_on_simulation.called)
        mock_execute_on_simulation.assert_called_with("netsim", "sim1", [node1], ".start -parallel 5")

    @patch("enmutils_int.lib.netsim_operations.NetsimOperation._execute_on_simulation")
    def test_start_nodes__in_power_nodes_is_successful_against_vfarm_nodes(
            self, mock_execute_on_simulation):
        node1 = Mock(netsim="ieatnetsimv7004-01", simulation="sim1")
        power_nodes = PowerNodes([node1])
        response = Mock()
        response.ok = True
        response.stdout = 'OK'
        mock_execute_on_simulation.return_value = response
        power_nodes.start_nodes()
        self.assertTrue(mock_execute_on_simulation.called)
        mock_execute_on_simulation.assert_called_with("ieatnetsimv7004-01", "sim1", [node1], ".start -parallel")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
