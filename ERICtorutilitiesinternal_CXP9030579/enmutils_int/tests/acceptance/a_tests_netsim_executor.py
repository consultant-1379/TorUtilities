#!/usr/bin/env python
import time
import unittest2

from enmutils_int.lib import netsim_executor
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec, setup_verify


def _run_ne_cmd_with_different_num_of_nodes(node_names, cmd, host, sim):
    return netsim_executor.run_ne_cmd(cmd, host, sim, node_names, password="netsim")


class NesimExecutorAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 6}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @property
    def nodes(self):
        return self._get_nodes_by_sim()

    @property
    def node_names(self):
        return [node.node_name for node in self.nodes]

    @property
    def sim(self):
        return self.nodes[0].simulation

    @property
    def host(self):
        return self.nodes[0].netsim

    @property
    def sims(self):
        return self._populate_simulations(self.fixture.nodes)

    def _populate_simulations(self, nodes):
        if nodes:
            return list(set([node.simulation for node in self.fixture.nodes]))

    def _get_nodes_by_sim(self):
        list_of_node_list_per_sim = list()
        if len(self.sims) != 1:
            for sim in self.sims:
                sim_nodes_list = list()
                for node in self.fixture.nodes:
                    if sim == node.simulation:
                        sim_nodes_list.append(node)
            list_of_node_list_per_sim.append(sim_nodes_list)

            return max(enumerate(list_of_node_list_per_sim), key=lambda tup: len(tup[1]))[1]
        else:
            return self.fixture.nodes

    def get_started_nodes(self):
        response = netsim_executor.run_cmd('.show started', self.host, self.sim)
        return response.stdout

    def _wait_for_nodes_to_stop(self, nodes):
        nodes_stopped = False
        loop_counter = 0

        while not nodes_stopped and loop_counter < 20:
            loop_counter += 1
            started_nodes = self.get_started_nodes()

            for node in nodes:
                if node in started_nodes:
                    time.sleep(3)

            nodes_stopped = True

        return nodes_stopped

    def _wait_for_nodes_to_start(self, nodes):
        nodes_started = False
        loop_counter = 0

        while not nodes_started and loop_counter < 20:
            loop_counter += 1
            started_nodes = self.get_started_nodes()

            for node in nodes:
                if node not in started_nodes:
                    time.sleep(3)

            nodes_started = True

        return nodes_started

    @setup_verify(available_nodes=6)
    @func_dec("Netsim Executor Library", "Nodes can be stopped in parallel")
    def test_001_successfully_stopping_nodes(self):
        cmd = ".stop -parallel"
        expected_result = {key: 'OK' for key in self.node_names}

        self.assertEqual(netsim_executor.run_ne_cmd(cmd, self.host, self.sim, self.node_names), expected_result)
        self.assertTrue(self._wait_for_nodes_to_stop(self.node_names))

    @setup_verify(available_nodes=6)
    @func_dec("Netsim Executor Library", "Nodes can be started in parallel")
    def test_002_successfully_starting_nodes(self):
        cmd = ".start -parallel"
        expected_result = {key: 'OK' for key in self.node_names}

        self.assertEqual(netsim_executor.run_ne_cmd(cmd, self.host, self.sim, self.node_names), expected_result)
        self.assertTrue(self._wait_for_nodes_to_start(self.node_names))

    @setup_verify(available_nodes=6)
    @func_dec("Netsim Executor Library", "Check if node is started")
    def test_013_check_node_started_on_netsim_box(self):
        stopped_nodes = netsim_executor.check_nodes_started([self.nodes[0]])
        self.assertFalse(stopped_nodes)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
