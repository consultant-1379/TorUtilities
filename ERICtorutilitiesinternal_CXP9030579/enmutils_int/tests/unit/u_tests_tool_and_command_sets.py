import unittest2

from enmutils_int.lib.performance_commands import tool_and_command_sets
from testslib import unit_test_utils


class ToolAndCommandSets(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_tool_and_command(self):
        self.assertEqual(tool_and_command_sets.tool_and_commands, {
            "netsim": [
                "netsim stop netsim {simulations}", "netsim start netsim {simulations}",
                "netsim restart netsim {simulation}",
                "netsim list netsim {simulations}", "netsim info netsim {simulations}",
                "netsim fetch netsim {simulations} performance_nodes", "netsim activities netsim {simulation}",
                "netsim cli netsim {simulation} all showscanners"
            ]
        })


if __name__ == '__main__':
    unittest2.main(verbosity=2)
