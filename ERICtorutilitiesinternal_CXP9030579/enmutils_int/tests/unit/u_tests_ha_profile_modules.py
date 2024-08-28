#!/usr/bin/env python
import unittest2

from mock import patch, PropertyMock
from testslib import unit_test_utils
from enmutils_int.lib.workload import ha_01
from enmutils_int.lib.load_node import ERBSNode


class Ha01ProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.workload.ha_01.HA_01.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.workload.ha_01.HA_01.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.workload.ha_01.log.logger.debug")
    def test_ha_01_profile__successful(self, mock_log, mock_get_nodes, _):
        mock_get_nodes.return_value = [ERBSNode(node_id=u"node1"), ERBSNode(node_id=u"node2")]
        ha_01.HA_01().run()
        mock_log.assert_called_with("Nodes used by HA: ['node1', 'node2']")
        self.assertEquals(mock_get_nodes.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
