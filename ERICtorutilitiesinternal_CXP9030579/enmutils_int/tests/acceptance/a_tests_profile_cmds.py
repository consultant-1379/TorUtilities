from datetime import date
import unittest2
from enmutils_int.lib.nrm_default_configurations.profile_cmds import ENMCLI_COMMANDS as enmcli_cmds
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec


class ProfileCmdsAcceptanceTests(unittest2.TestCase):
    NUM_NODES = {'RadioNode': 1}
    EXCLUSIVE = True
    current_date = date.today().strftime('%Y-%m-%d')

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ['Cmedit_Administrator', 'Network_Explorer_Administrator']

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        self.user = self.fixture.users[0]
        self.nodes = self.fixture.nodes

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("cmedit Basic Commands", "Evaluate cmedit basic commands syntactically with EnodeB nodes and verify "
                                       "result")
    def test_01_cmedit_basic_commands__enodeb(self):
        node_type = "eNodeB" if 'LTE' in self.nodes[0].node_id else 'gNodeB'
        cell_type = ('EUtranCellTDD' if self.nodes[0].lte_cell_type == 'TDD' else 'EUtranCellFDD') if node_type == 'eNodeB' else None
        for command in enmcli_cmds["cmedit_basic"]["eNodeB"]:
            command = command.format(node_id=self.nodes[0], primary_type="RadioNode", cell_type=cell_type)
            response = self.user.enm_execute(command)
            if "Error" in response.get_output():
                raise Exception

    @func_dec("cmedit Basic Commands", "Evaluate cmedit basic commands syntactically with GnodeB nodes and verify "
                                       "result")
    def test_02_cmedit_basic_commands__gnodeb(self):
        for command in enmcli_cmds["cmedit_basic"]["gNodeB"]:
            command = command.format(node_id=self.nodes[0], ten_node_id=self.nodes[0], primary_type="RadioNode")
            response = self.user.enm_execute(command)
            if "Error" in response.get_output():
                raise Exception

    @func_dec("cmedit Standard Commands", "Evaluate cmedit standard commands syntactically with EnodeB nodes and "
                                          "verify result")
    def test_03_cmedit_standard_commands__enodeb(self):
        node_type = "eNodeB" if 'LTE' in self.nodes[0].node_id else 'gNodeB'
        cell_type = ('EUtranCellTDD' if self.nodes[0].lte_cell_type == 'TDD' else 'EUtranCellFDD') if node_type == 'eNodeB' else None
        for command in enmcli_cmds["cmedit_standard"]["eNodeB"]:
            command = command.format(node_id=self.nodes[0], ten_node_id=self.nodes[0], primary_type="RadioNode",
                                     cell_type=cell_type)
            response = self.user.enm_execute(command)
            if "Error" in response.get_output():
                raise Exception

    @func_dec("cmedit Standard Commands",
              "Evaluate cmedit standard commands syntactically with GnodeB nodes and verify result")
    def test_04_cmedit_standard_commands__gnodeb(self):
        for command in enmcli_cmds["cmedit_standard"]["gNodeB"]:
            command = command.format(node_id=self.nodes[0], ten_node_id=self.nodes[0], primary_type="RadioNode")
            response = self.user.enm_execute(command)
            if "Error" in response.get_output():
                raise Exception

    @func_dec("cmedit Advanced Commands", "Evaluate cmedit advanced commands syntactically with EnodeB nodes and "
                                          "verify result")
    def test_05_cmedit_advanced_commands__enodeb(self):
        node_type = "eNodeB" if 'LTE' in self.nodes[0].node_id else 'gNodeB'
        cell_type = ('EUtranCellTDD' if self.nodes[0].lte_cell_type == 'TDD' else 'EUtranCellFDD') if node_type == 'eNodeB' else None
        for command in enmcli_cmds["cmedit_advanced"]["eNodeB"]:
            command = command.format(node_id=self.nodes[0], ten_node_id=self.nodes[0], ninetynine_node_id=self.nodes[0],
                                     cell_type=cell_type)
            response = self.user.enm_execute(command)
            if "Error" in response.get_output():
                raise Exception

    @func_dec("cmedit Advanced Commands",
              "Evaluate cmedit advanced commands syntactically with GnodeB nodes and verify result")
    def test_06_cmedit_advanced_commands__gnodeb(self):
        for command in enmcli_cmds["cmedit_advanced"]["gNodeB"]:
            command = command.format(node_id=self.nodes[0], ten_node_id=self.nodes[0], ninetynine_node_id=self.nodes[0])
            response = self.user.enm_execute(command)
            if "Error" in response.get_output():
                raise Exception

    @func_dec("Alarm Commands", "Evaluate alarm commands syntactically and verify result")
    def test_07_alarm_commands(self):
        for command in enmcli_cmds["alarm"]:
            command = command.format(node_id=self.nodes[0], ten_node_id=self.nodes[0], date=self.current_date)
            response = self.user.enm_execute(command)
            if "Error" in response.get_output():
                raise Exception

    @func_dec("secadm Commands", "Evaluate secadm commands syntactically and verify result")
    def test_08_secadm_commands(self):
        for command in enmcli_cmds["secadm"]:
            command = command.format(node_id=self.nodes[0])
            response = self.user.enm_execute(command)
            if "Error" in response.get_output():
                raise Exception


if __name__ == "__main__":
    unittest2.main(verbosity=2)
