#!/usr/bin/env python
import shutil
import sys
import unittest2

from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.nrm_default_configurations import basic_network
from testslib.func_test_utils import func_dec
from testslib.bin import basic_net_update
from testslib import func_test_utils, test_fixture

path = get_internal_file_path_for_import("lib", "nrm_default_configurations", "basic_network.py").strip()


class BasicNetUpdateAcceptanceTests(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        shutil.copy2(path, "backup.py")

    def tearDown(self):
        func_test_utils.tear_down(self)
        shutil.move("backup.py", path)

    @func_dec("BASIC NET UPDATE", "Check if update profiles executes successfully")
    def test_update_category_executes_successfully(self):
        sys.argv = ["./basic_net_update.py", "update", "amos"]
        basic_network.basic["basic"]["amos"]["AMOS_01"]["SUPPORTED"] = True
        pre_change = basic_network.basic.get("basic").get("amos").get("AMOS_01").get('UPDATE_VERSION')
        basic_net_update.cli()
        post_change = basic_network.basic.get("basic").get("amos").get("AMOS_01").get('UPDATE_VERSION')
        self.assertNotEqual(pre_change, post_change)

    @func_dec("BASIC NET UPDATE", "Check if update all executes successfully")
    def test_update_all_executes_successfully(self):
        sys.argv = ["./basic_net_update.py", "update"]
        basic_network.basic["basic"]["amos"]["AMOS_02"]["NOTE"] = True
        pre_change = basic_network.basic.get("basic").get("amos").get("AMOS_02").get('UPDATE_VERSION')
        basic_net_update.cli()
        post_change = basic_network.basic.get("basic").get("amos").get("AMOS_02").get('UPDATE_VERSION')
        self.assertNotEqual(pre_change, post_change)

    @func_dec("BASIC NET UPDATE", "Check if update profiles executes successfully")
    def test_update_inc_all_includes_unsupported_profiles(self):
        sys.argv = ["./basic_net_update.py", "update", "amos"]
        basic_network.basic["basic"]["amos"]["AMOS_01"]["SUPPORTED"] = False
        pre_change = basic_network.basic.get("basic").get("amos").get("AMOS_01").get('UPDATE_VERSION')
        basic_net_update.cli()
        post_change = basic_network.basic.get("basic").get("amos").get("AMOS_01").get('UPDATE_VERSION')
        self.assertNotEqual(pre_change, post_change)

    @func_dec("BASIC NET UPDATE", "Check if update all executes successfully")
    def test_update_all_ignores_manual_and_intrusive_profiles(self):
        sys.argv = ["./basic_net_update.py", "update"]
        basic_network.basic["basic"]["amos"]["AMOS_01"]["NOTE"] = "MANUAL"
        basic_network.basic["basic"]["nodesec"]["NODESEC_03"]["SUPPORTED"] = "INTRUSIVE"
        pre_change_1 = basic_network.basic.get("basic").get("amos").get("AMOS_01").get('UPDATE_VERSION')
        pre_change_2 = basic_network.basic.get("basic").get("nodesec").get("NODESEC_03").get('UPDATE_VERSION')
        basic_net_update.cli()
        post_change_1 = basic_network.basic.get("basic").get("amos").get("AMOS_01").get('UPDATE_VERSION')
        post_change_2 = basic_network.basic.get("basic").get("nodesec").get("NODESEC_03").get('UPDATE_VERSION')
        self.assertEqual(pre_change_1, post_change_1)
        self.assertEqual(pre_change_2, post_change_2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
