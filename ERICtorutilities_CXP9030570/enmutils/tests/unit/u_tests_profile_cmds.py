#!/usr/bin/env python
import string
import unittest2
from enmutils_int.lib.nrm_default_configurations import profile_cmds
from testslib import unit_test_utils


class ArgumentsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_random_string_returns_correct_length(self):
        self.assertEqual(len(profile_cmds.get_random_string(9)), 9)

    def test_get_random_string_excludes_correctly(self):
        exclude = string.ascii_letters
        self.assertNotIn(profile_cmds.get_random_string(exclude=exclude), exclude)

    def test_get_random_string_returns_password_correctly(self):
        self.assertEqual(profile_cmds.get_random_string(password=True)[-3:], ".8z")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
