from collections import OrderedDict

import unittest2

from enmutils_int.lib.schedules import schedule_template
from testslib import unit_test_utils


class ScheduleUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_variables(self):
        self.assertIsInstance(schedule_template.ONCE_OFF_BEFORE_STABILITY, OrderedDict)
        self.assertIsInstance(schedule_template.SETUP, OrderedDict)
        self.assertIsInstance(schedule_template.EXCLUSIVE, OrderedDict)
        self.assertIsInstance(schedule_template.NON_EXCLUSIVE, OrderedDict)
        self.assertIsInstance(schedule_template.PLACEHOLDERS, OrderedDict)


if __name__ == '__main__':
    unittest2.main(verbosity=2)
