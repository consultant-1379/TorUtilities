#!/usr/bin/env python
import unittest2

from mock import patch, Mock

from testslib import unit_test_utils
from enmutils_int.lib.fm_specific_problems import (get_specific_problem_iterator, SPECIFIC_PROBLEMS, map_nodes_for_profile,
                                                   update_com_ecim_parameters)


class FMSpecificProblems(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.problem_iterator = get_specific_problem_iterator()
        self.next_fm_problem = self.problem_iterator.next()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_specific_problem(self):
        self.assertTrue(self.next_fm_problem in SPECIFIC_PROBLEMS)

    @patch('enmutils_int.lib.fm_specific_problems.log.logger.debug')
    def test_map_nodes_for_profile_calls_logger_on_success(self, mock_debug):
        node_types = ['ERBS', 'RBS', 'BSC', 'RNC', 'RadioNode', 'MGW', 'SGSN-MME', 'Router_6672', 'MSC-DB-BSP']
        nodes = []
        for ne_type in node_types:
            node = Mock()
            node.NE_TYPE = ne_type
            nodes.append(node)
        map_nodes_for_profile(nodes)
        self.assertFalse(mock_debug.called)

    def test_update_com_ecim_parameters(self):
        self.assertEqual((1, 0), update_com_ecim_parameters(11, 26))

    def test_update_com_ecim_parameters_with_other_probable_cause(self):
        self.assertEqual((56, 0), update_com_ecim_parameters(55, 26))

    def test_update_com_ecim_parameters_unknown_cause_and_type(self):
        self.assertEqual((55, 56), update_com_ecim_parameters(55, 55))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
