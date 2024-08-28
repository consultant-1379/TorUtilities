#!/usr/bin/env python
import datetime

import unittest2
from mock import patch, Mock
from enmutils_int.lib.assertions_utils import AssertionValues
from testslib import unit_test_utils


class AssertionUtilsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.a_time = datetime.datetime.now()
        self.an_existing_assertion_value_dict = AssertionValues("PROFILE_A")
        self.an_existing_assertion_value_dict.update(9999)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_assertion_values_persists_a_new_assertion_values(self):
        a_new_assertion_value_dict = AssertionValues("PROFILE_B")
        a_new_assertion_value_dict.update(9999, self.a_time)

        the_assertion_value_dict = AssertionValues("PROFILE_B")
        self.assertEqual(the_assertion_value_dict.values[self.a_time], 9999)

    def test_assertion_values_updates_an_existing_assertion_values(self):
        another_time = datetime.datetime.now() + datetime.timedelta(seconds=10)
        self.an_existing_assertion_value_dict.update(8888, another_time)
        val = self.an_existing_assertion_value_dict.values[another_time]
        self.assertEqual(val, 8888)

    def test_assertion_values_updates_with_mutilple_entries(self):
        a_new_assertion_value_dict = AssertionValues("PROFILE_C")
        for i in xrange(0, 60):
            a_new_assertion_value_dict.update(i, self.a_time.replace(minute=i))
        the_assertion_value_dict = AssertionValues("PROFILE_C")
        self.assertEqual(len(the_assertion_value_dict.values), 60)

    @patch("enmutils_int.lib.assertions_utils.AssertionValues.delete")
    def test_teardown__delete_called(self, mock_delete):
        AssertionValues._teardown(self.an_existing_assertion_value_dict)
        self.assertTrue(mock_delete.called)

    @patch("enmutils_int.lib.assertions_utils.persistence.remove")
    def test_delete(self, mock_remove):
        AssertionValues(Mock(), Mock()).delete()
        self.assertTrue(mock_remove.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
