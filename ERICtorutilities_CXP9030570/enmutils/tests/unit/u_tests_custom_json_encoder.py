#!/usr/bin/env python
from datetime import datetime
from mock import patch

import unittest2

from enmutils.lib.custom_json_encoder import CustomEncoder
from testslib import unit_test_utils


class CustomEncoderUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.tc = CustomEncoder()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_default__returns_list_for_set_data_type(self):
        self.assertTrue(isinstance(self.tc.default(set()), list))

    def test_default__returns_str_representation_for_datetime_data_type(self):
        date = datetime(2020, 12, 12)
        self.assertEqual(self.tc.default(date), "2020-12-12 00:00:00")

    @patch("enmutils.lib.custom_json_encoder.json.JSONEncoder.default")
    def test_default__calls_base_class_default_method_for_supported_type(self, mock_default):
        self.tc.default([])
        self.assertTrue(mock_default.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
