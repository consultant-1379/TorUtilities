#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from parameterizedtestcase import ParameterizedTestCase

from testslib import unit_test_utils, test_node_mgr


class TestNodeManagerUnitTests(ParameterizedTestCase):
    NUM_NODES = {'ERBS': 10}

    def setUp(self):
        self.nodes = ['netsim_LTE02ERBS00001', 'netsim_LTE02ERBS00002', 'netsim_LTE02ERBS00003',
                      'netsim_LTE02ERBS00004', 'netsim_LTE02ERBS00005', 'netsim_LTE02ERBS00006',
                      'netsim_LTE02ERBS00007', 'netsim_LTE02ERBS00008', 'netsim_LTE02ERBS00009',
                      'netsim_LTE02ERBS00010']
        self.node_status = {node: "SYNCHRONIZED" for node in self.nodes}
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('testslib.test_node_mgr.TestPool.__init__', return_value=None)
    @patch('testslib.test_node_mgr.TestPool.mutex')
    @patch('testslib.test_node_mgr.TestPool.get_available_nodes')
    def test_test_pool_allocate_nodes__adds_test_to_node(self, mock_get_nodes, *_):
        pool = test_node_mgr.TestPool("acceptance")
        node = Mock()
        mock_get_nodes.return_value = [node]
        pool.allocate_nodes("test_class")
        self.assertEqual(1, mock_get_nodes.call_count)
        self.assertEqual(1, node.add_test.call_count)

    @patch('testslib.test_node_mgr.TestPool.mutex')
    @patch('testslib.test_node_mgr.TestPool.__init__', return_value=None)
    @patch('testslib.test_node_mgr.TestPool.get_available_nodes')
    def test_allocate_nodes__success(self, mock_get_available, *_):
        mock_get_available.return_value = [Mock(), Mock()]
        pool = test_node_mgr.TestPool("acceptance")
        pool.allocate_nodes(self.__class__)
        self.assertEqual(1, mock_get_available.call_count)

    @patch('testslib.test_node_mgr.TestPool.__init__', return_value=None)
    def test_return_nodes__removes_test_from_node(self, *_):
        node = Mock()
        nodes = [node]
        pool = test_node_mgr.TestPool("acceptance")
        pool.return_nodes(nodes)
        self.assertEqual(1, node.remove_test.call_count)

    @patch('testslib.test_node_mgr.TestPool.__init__', return_value=None)
    @patch('testslib.test_node_mgr.TestPool.db', new_callable=PropertyMock)
    def test_clear__removes_pool_from_persistence(self, mock_db, *_):
        pool = test_node_mgr.TestPool("acceptance")
        pool.key = "TestPool"
        mock_db.return_value = Mock()
        pool.clear()
        self.assertEqual(1, pool.db.remove.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
