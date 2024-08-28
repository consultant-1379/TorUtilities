#!/usr/bin/env python
import sys
import unittest2

from enmutilsbin import cli_app
from enmutils_int.lib import common_utils
from enmutils_int.lib.auto_provision import AutoProvision
from testslib.func_test_utils import func_dec
from testslib import func_test_utils, test_fixture


class CliAppAcceptanceTests(unittest2.TestCase):
    FILE_PATH = None

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

    @func_dec("CLI APP", "Check if cmedit command executes successfully")
    def test_cmedit_commands_executes_successfully(self):
        cli_app._execute_cli_command("cmedit get * MeContext", None)

    @func_dec("CLI APP", "Check if shm import executes successfully with file path")
    def test_cli_command_with_file_executes_successfully(self):
        self.FILE_PATH = common_utils.get_internal_file_path_for_import("templates", "ap", AutoProvision.LICENCE)
        sys.argv = ['./cli_app.py', 'lcmadm install file:{0}'.format(AutoProvision.LICENCE)]
        try:
            cli_app._execute_cli_command('lcmadm install file:{0}'.format(AutoProvision.LICENCE), self.FILE_PATH)
        finally:
            cli_app._execute_cli_command('lcmadm remove name={0}'.format(AutoProvision.LICENCE), None)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
