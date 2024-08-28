#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock

from enmutils.lib.exceptions import EnvironError
from enmutils.lib.exceptions import NetsimError
from enmutils_int.lib.profile_flows.network_flows.network_flow import (NetworkFlow, Network01Flow,
                                                                       Network02Flow, Network03Flow)
from enmutils_int.lib.workload.network_01 import NETWORK_01
from enmutils_int.lib.workload.network_02 import NETWORK_02
from enmutils_int.lib.workload.network_03 import NETWORK_03
from testslib import unit_test_utils


class NetworkFlowUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.flow = NetworkFlow()
        node = Mock(node_name="Node", netsim="host", simulation="sim")
        node1 = Mock(node_name="Node1", netsim="host1", simulation="sim1")
        node3 = Mock(node_name="Node3", netsim="host3", simulation="sim3")
        self.nodes = [node, node1, node3]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.netsim_executor.run_cmd')
    def test_execute_command_on_netsim_simulation__success(self, mock_run, *_):
        nodes_list = "host", "sim", "Node"
        cmd = self.flow.RESTART_CMD
        self.flow.execute_command_on_netsim_simulation(nodes_list, cmd)
        self.assertEqual(mock_run.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.netsim_executor.run_cmd')
    def test_execute_command_on_netsim_simulation__raises_error(self, mock_run_cmd, *_):
        nodes_list = "host", "sim", "Node"
        cmd = self.flow.RESTART_CMD
        mock_run_cmd.side_effect = Exception
        self.assertRaises(NetsimError, self.flow.execute_command_on_netsim_simulation, nodes_list, cmd)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.NetworkFlow.all_nodes_in_workload_pool')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.node_pool_mgr.group_nodes_per_sim')
    def test_select_random_node_or_simulation_attrs__random_simulations(self, mock_group, _):
        mock_group.return_value = {node.netsim: {node.simulation: [node]} for node in self.nodes}
        result = self.flow.select_random_node_or_simulation_attrs(required_simulations_count=2)
        self.assertEqual(2, len(result))
        self.assertIn("sim", result[0][1])
        self.assertIn("host", result[0][0])
        result = self.flow.select_random_node_or_simulation_attrs(required_simulations_count=20)
        self.assertEqual(3, len(result))

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.NetworkFlow.all_nodes_in_workload_pool')
    def test_select_random_node_or_simulation_attrs__random_nodes(self, mock_nodes):
        mock_nodes.return_value = self.nodes
        result = self.flow.select_random_node_or_simulation_attrs(required_node_count=2)
        self.assertEqual(2, len(result))
        self.assertIn("sim", result[0][1])
        self.assertIn("host", result[0][0])
        self.assertIn("Node", result[0][2])


class Network01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Network01Flow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.execute_flow")
    def test_network_profile_network_01_execute_flow__successful(self, mock_flow):
        NETWORK_01().run()
        self.assertEqual(mock_flow.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.'
           'select_random_node_or_simulation_attrs')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.'
           'perform_netsim_operation_on_nodes')
    def test_execute__success(self, mock_perform_operations, mock_select, *_):
        mock_select.return_value = [("host", "sim", "Node"), ("host1", "sim1", "Node1")]
        self.flow.execute_flow()
        mock_perform_operations.assert_called_with([("host", "sim", "Node"), ("host1", "sim1", "Node1")], cmd=self.flow.RESTART_CMD)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.'
           'perform_netsim_operation_on_nodes')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.'
           'select_random_node_or_simulation_attrs')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.add_error_as_exception')
    def test_execute__raises_exception_when_no_nodes(self, mock_add_error, mock_select, *_):
        mock_select.return_value = []
        self.assertRaises(EnvironError, self.flow.execute_flow())
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.'
           'execute_command_on_netsim_simulation')
    def test_perform_netsim_operation_on_nodes__success_for_restart(self, mock_execute):
        nodes_list = [("host", "sim", "Node"), ("host1", "sim1", "Node1")]
        cmd = self.flow.RESTART_CMD
        self.flow.perform_netsim_operation_on_nodes(nodes_list, cmd)
        self.assertEqual(mock_execute.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.'
           'execute_command_on_netsim_simulation')
    def test_perform_netsim_operation_on_nodes__success_for_start(self, mock_execute):
        nodes_list = [("host", "sim", "Node"), ("host1", "sim1", "Node1")]
        cmd = self.flow.START_CMD
        self.flow.perform_netsim_operation_on_nodes(nodes_list, cmd)
        self.assertEqual(mock_execute.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network01Flow.'
           'execute_command_on_netsim_simulation')
    def test_perform_netsim_operation_on_nodes__exception(self, mock_execute, mock_add_error):
        nodes_list = [("host", "Node"), ("host1", "Node1")]
        cmd = self.flow.START_CMD
        self.flow.perform_netsim_operation_on_nodes(nodes_list, cmd)
        mock_execute.side_effect = Exception
        self.assertEqual(mock_add_error.call_count, 1)


class Network02UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Network02Flow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.execute_flow")
    def test_network_profile_network_02_execute_flow__successful(self, mock_flow):
        NETWORK_02().run()
        self.assertEqual(mock_flow.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.get_netsim_list')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.perform_netsim_operations')
    def test_execute__success(self, mock_netsim_ops, mock_netsim_list, *_):
        mock_netsim_list.return_value = ['host', 'host']
        self.flow.execute_flow()
        mock_netsim_ops.assert_any_call(mock_netsim_list.return_value)
        mock_netsim_ops.assert_called_with(mock_netsim_list.return_value, up=True)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.perform_netsim_operations')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.get_netsim_list')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.add_error_as_exception')
    def test_execute__raises_exception_when_no_netsim_vm(self, mock_add_error, mock_get_netsim_list, *_):
        mock_get_netsim_list.return_value = []
        self.assertRaises(EnvironError, self.flow.execute_flow())
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.'
           'execute_command_on_netsim_vm')
    def test_perform_netsim_operations__calls_network_block_and_unblock(self, mock_execute):
        netsim_list = ["host1", "host2"]
        self.flow.perform_netsim_operations(netsim_list)
        mock_execute.assert_any_call(self.flow.NETWORK_BLOCK, "host1")
        mock_execute.assert_any_call(self.flow.NETWORK_BLOCK, "host2")
        self.flow.perform_netsim_operations(netsim_list, up=True)
        mock_execute.assert_any_call(self.flow.NETWORK_UNBLOCK, "host1")
        mock_execute.assert_any_call(self.flow.NETWORK_UNBLOCK, "host2")

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.'
           'execute_command_on_netsim_vm', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.add_error_as_exception')
    def test_perform_netsim_operations__raises_exception(self, mock_add_error, *_):
        netsim_list = ["host1", "host2"]
        self.flow.perform_netsim_operations(netsim_list)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.'
           'select_random_node_or_simulation_attrs')
    def test_get_netsim_list__returns_netsim_list(self, mock_select, mock_log, *_):
        mock_select.return_value = [("host1", "sim1", "Node1"), ("host2", "sim2", "Node2"),
                                    ("host3", "sim3", "Node3"), ("host4", "sim4", "Node4")]
        result = self.flow.get_netsim_list()
        self.assertEqual(3, len(result))
        mock_log.assert_called_with("Netsim list: ['host1', 'host2', 'host3']")

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network02Flow.'
           'select_random_node_or_simulation_attrs')
    def test_get_netsim_list__else_condition_returns_netsim_list(self, mock_select, mock_log, *_):
        mock_select.return_value = [("host1", "sim1", "Node1"), ("host1", "sim1", "Node1")]
        result = self.flow.get_netsim_list()
        self.assertEqual(1, len(result))
        mock_log.assert_called_with("Netsim list: ['host1']")

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.pexpect.spawn.expect', return_value=0)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_execute_command_on_netsim_vm__success_network_block_and_unblock_command(self, mock_log, mock_send, *_):
        self.flow.execute_command_on_netsim_vm(self.flow.NETWORK_BLOCK, 'host')
        self.flow.execute_command_on_netsim_vm(self.flow.NETWORK_UNBLOCK, 'host')
        self.assertEqual(6, mock_send.call_count)
        self.assertEqual(6, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.pexpect.spawn.sendline')
    def test_execute_command_on_netsim_vm__fails_ssh_to_netsim_raises_environ_error(self, *_):
        self.assertRaises(EnvironError, self.flow.execute_command_on_netsim_vm, "cmd", "host")

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.pexpect.spawn.expect', side_effect=[0, 1])
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.pexpect.spawn.sendline')
    def test_execute_command_on_netsim_vm__fails_connect_to_netsim(self, *_):
        self.assertRaises(NetsimError, self.flow.execute_command_on_netsim_vm, "cmd", "host")

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.pexpect.spawn.expect', side_effect=[0, 0, 1, 0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.pexpect.spawn.sendline')
    def test_execute_command_on_netsim_vm__fails_to_block_or_unblock_network_traffic(self, *_):
        self.assertRaises(NetsimError, self.flow.execute_command_on_netsim_vm, self.flow.NETWORK_UNBLOCK, "host")
        self.assertRaises(NetsimError, self.flow.execute_command_on_netsim_vm, self.flow.NETWORK_BLOCK, "host")


@patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.__init__', return_value=None)
class Network03UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Network03Flow()
        self.flow.NAME = Network03Flow
        self.nodes = [Mock(netsim="host"), Mock(netsim="netsim"), Mock(netsim="netsim-01"), Mock(netsim="netsim-05"),
                      Mock(netsim="netsim-01"), Mock(netsim="host")]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.execute_flow")
    def test_network_profile_network_03_execute_flow__successful(self, mock_flow, _):
        NETWORK_03().run()
        self.assertEqual(mock_flow.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.partial')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.'
           'set_bandwidth_and_latency_on_netsims')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.'
           'get_unique_netsim_host_to_be_changed')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.select_nodes_to_use')
    def test_execute_flow__success(self, mock_nodes, mock_unique_hosts, mock_action_netsim, *_):
        mock_node_list = [Mock(netsim="host")]
        mock_nodes.return_value = mock_node_list
        mock_unique_hosts.return_value = host = ["host"]

        self.flow.execute_flow()

        mock_unique_hosts.assert_called_with(mock_node_list)
        mock_action_netsim.assert_called_with(host)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.'
           'set_bandwidth_and_latency_on_netsims')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.'
           'get_unique_netsim_host_to_be_changed')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.select_nodes_to_use')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_execute_flow__does_not_perform_actions_if_no_nodes(self, mock_debug, mock_nodes,
                                                                mock_unique_hosts, mock_action_netsim, *_):
        mock_node_list = []
        mock_nodes.return_value = mock_node_list

        self.flow.execute_flow()

        mock_debug.assert_called_with('No MLTN nodes found to use. Going to sleep.')
        self.assertEqual(mock_unique_hosts.call_count, 0)
        self.assertEqual(mock_action_netsim.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.all_nodes_in_workload_pool')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_select_nodes_to_use__success(self, mock_debug, mock_all_nodes, _):
        mock_all_nodes.return_value = self.nodes

        self.flow.select_nodes_to_use()

        mock_all_nodes.assert_called_with(node_attributes=['netsim'])
        self.assertEqual(mock_debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.activate_changed_netsim_cfg')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.Command')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_set_bandwidth_and_latency_on_netsims__success(self, mock_debug, mock_command, mock_run_cmd, *_):
        mock_hosts = ['host', 'host']
        mock_run_cmd.return_value = Mock(ok=True)

        self.flow.set_bandwidth_and_latency_on_netsims(mock_hosts)

        mock_debug.assert_called_with("Values changed in file: [/netsim/netsim_cfg]and backup created"
                                      " [/netsim/netsim_cfgbak on host [host]]")
        mock_run_cmd.assert_called_with(mock_command.return_value, 'host', 'netsim', 'netsim')

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.Command')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.activate_changed_netsim_cfg')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_set_bandwidth_and_latency_on_netsims__logs_if_no_success(self, mock_debug, mock_run_cmd, *_):
        mock_hosts = ['host', 'host']
        mock_run_cmd.return_value = Mock(ok=False)

        self.flow.set_bandwidth_and_latency_on_netsims(mock_hosts)

        mock_debug.assert_called_with("Unable to change values on host: [host]")
        self.assertEqual(mock_run_cmd.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.netsim_executor.run_cmd')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_activate_changed_netsim_cfg__success(self, mock_debug, mock_run_cmd, _):
        cmd = ("/netsim_users/pms/bin/limitbw -n -c >> /netsim_users/pms/logs/limitbw.log 2>&1 && "
               "/netsim_users/pms/bin/limitbw -n -g >> /netsim_users/pms/logs/limitbw.log 2>&1")
        host = 'host'
        mock_run_cmd.return_value = Mock(ok=True)

        self.flow.activate_changed_netsim_cfg(host)

        mock_debug.assert_called_with("New limits applied to netsim host: [host]")
        mock_run_cmd.assert_called_with(cmd, 'host')
        self.assertEqual(mock_debug.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.EnvironError')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.netsim_executor.run_cmd')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.add_error_as_exception')
    def test_activate_changed_netsim_cfg__logs_if_no_success(self, mock_error, mock_run_cmd, mock_environerror,
                                                             mock_debug, _):
        cmd = ("/netsim_users/pms/bin/limitbw -n -c >> /netsim_users/pms/logs/limitbw.log 2>&1 && "
               "/netsim_users/pms/bin/limitbw -n -g >> /netsim_users/pms/logs/limitbw.log 2>&1")
        host = 'host'
        mock_run_cmd.return_value = Mock(ok=False)

        self.flow.activate_changed_netsim_cfg(host)

        mock_run_cmd.assert_called_with(cmd, 'host')
        mock_error.assert_called_with(mock_environerror("Unable to apply new limits on netsim host: [host]"))
        self.assertEqual(mock_debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.get_lines_from_remote_file')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_get_unique_netsim_host_to_be_changed__success(self, mock_debug, mock_get_lines, _):
        mock_get_lines.return_value = ["BANDWIDTH_ML=128", "NETWORK_DELAY=30"]

        unique_hosts = self.flow.get_unique_netsim_host_to_be_changed(self.nodes)

        self.assertEqual(mock_debug.call_count, 4)
        self.assertListEqual(sorted(unique_hosts), sorted(["host", "netsim", "netsim-01", "netsim-05"]))

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.get_lines_from_remote_file')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_get_unique_netsim_host_to_be_changed__logs_if_ml_value_not_found(self, mock_debug, mock_get_lines, _):
        mock_node_list = [Mock(netsim="host")]
        mock_get_lines.return_value = ['BANDWIDTH_TCU02=128', 'BANDWIDTH_SIU02=128', 'BANDWIDTH_MSC=4096',
                                       'BANDWIDTH_HLR=512', "NETWORK_DELAY=30"]

        unique_hosts = self.flow.get_unique_netsim_host_to_be_changed(mock_node_list)

        mock_debug.assert_called_with("BANDWIDTH_ML value does not exist in netsim_cfg file on host: [host]")
        self.assertListEqual(unique_hosts, [])

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.get_lines_from_remote_file')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_get_unique_netsim_host_to_be_changed__host_not_added_if_values_exist(self, mock_debug, mock_get_lines, _):
        mock_node_list = [Mock(netsim="host")]
        mock_get_lines.return_value = ["BANDWIDTH_ML=12", "NETWORK_DELAY=60"]

        unique_hosts = self.flow.get_unique_netsim_host_to_be_changed(mock_node_list)

        mock_debug.assert_called_with("Bandwidth and latency values correct on host: host")
        self.assertListEqual(unique_hosts, [])

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.activate_changed_netsim_cfg')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.does_remote_file_exist',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.Command')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_undo_changes__success(self, mock_debug, mock_cmd, mock_run_cmd, *_):
        mock_hosts_list = ['host']
        mock_run_cmd.return_value = Mock(ok=True)

        self.flow.undo_changes(mock_hosts_list)

        mock_run_cmd.assert_called_with(mock_cmd.return_value, 'host', 'netsim', 'netsim')
        mock_debug.assert_called_with("Backup file netsim_cfg restored successfully")

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.Command')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.activate_changed_netsim_cfg')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.does_remote_file_exist',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_undo_changes__logs_if_no_backup_file(self, mock_debug, mock_run_cmd, *_):
        mock_hosts_list = ['host']
        mock_run_cmd.return_value = Mock(ok=True)

        self.flow.undo_changes(mock_hosts_list)

        self.assertEqual(mock_run_cmd.call_count, 0)
        mock_debug.assert_called_with("backup file not found on host: [host]")

    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.Network03Flow.activate_changed_netsim_cfg')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.does_remote_file_exist',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.shell.Command')
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.log.logger.debug')
    def test_undo_changes__logs_if_response_bad(self, mock_debug, mock_cmd, mock_run_cmd, *_):
        mock_hosts_list = ['host']
        mock_run_cmd.return_value = Mock(ok=False)

        self.flow.undo_changes(mock_hosts_list)

        mock_run_cmd.assert_called_with(mock_cmd.return_value, 'host', 'netsim', 'netsim')
        mock_debug.assert_called_with("Unable to restore the netsim_cfg file on [host].")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
