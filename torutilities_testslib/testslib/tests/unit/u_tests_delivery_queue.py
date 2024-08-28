#!/usr/bin/env python
import unittest2
from mock import patch
from parameterizedtestcase import ParameterizedTestCase

from testslib import unit_test_utils
from testslib.bin import delivery_queue


class DeliveryQueueUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('testslib.delivery_queue.get_last_delivered_rpm')
    @patch('testslib.delivery_queue.get_enm_drop')
    @ParameterizedTestCase.parameterize(
        ("rpm_drop", "response"),
        [
            (("4.63.12", "18.11"), True),
            (("5.65.1", "18.11"), False),
            (("4.100.1", "18.12"), True),
            (("5.0.1", "18.11"), True),
            (("5.1.2", "18.13"), False)
        ]
    )
    def test_sprint_validate(self, rpm_drop, response, mock_get_enm_drop, mock_get_last_delivered_rpm):
        rpm, drop = rpm_drop
        mock_get_enm_drop.return_value = drop if drop != "18.13" else "18.12"
        mock_get_last_delivered_rpm.return_value = [(rpm, drop)]
        self.assertEqual(response, delivery_queue._sprint_validate("5.1.1", "", ""))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
