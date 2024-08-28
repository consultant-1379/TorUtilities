#!/usr/bin/env python
from datetime import datetime, date

import unittest2
from enmutils.lib.timestamp import (is_time_diff_greater_than_time_frame, get_int_time_in_secs_since_epoch,
                                    convert_time_to_ms_since_epoch, convert_datetime_to_str_format,
                                    convert_str_to_datetime_object)
from enmutils.lib import timestamp
from mock import patch
from testslib import unit_test_utils


class Timestamp(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_is_time_diff_greater_than_time_frame_returns_true_if_time_diff_exceeds_time_frame(self):
        now = datetime.now()
        start_time = now.replace(hour=12, minute=50, second=1)
        end_time = now.replace(hour=12, minute=50, second=42)
        time_frame = 40
        self.assertTrue(is_time_diff_greater_than_time_frame(start_time, end_time, time_frame))

    def test_is_time_diff_greater_than_time_frame_returns_false_if_time_diff_does_not_exceeds_time_frame(self):
        now = datetime.now()
        start_time = now.replace(hour=12, minute=50, second=1)
        end_time = now.replace(hour=12, minute=50, second=41)
        time_frame = 40
        self.assertFalse(is_time_diff_greater_than_time_frame(start_time, end_time, time_frame))

    @patch("time.time", return_value=1555612767.055923)
    def test_get_time_in_secs_since_epoch__is_successful(self, _):
        self.assertEqual(1555612767, get_int_time_in_secs_since_epoch())

    def test_convert_time_to_ms_since_epoch(self):
        convert_time = '12:00:00'
        convert_date = str(date(2019, 4, 30))
        epoch_return_value = convert_time_to_ms_since_epoch(convert_date, convert_time)
        self.assertEqual(epoch_return_value, 1556625600000)

    @patch('enmutils.lib.log.logger.debug')
    def test_convert_datetime_to_str_format__success(self, mock_debug):
        datetime_obj = datetime.now()
        self.assertIsInstance(convert_datetime_to_str_format(datetime_obj), str)
        mock_debug.assert_called_with("Returning datetime string format time object.")

    @patch('enmutils.lib.log.logger.debug')
    def test_convert_datetime_to_str_format__failure(self, mock_debug):
        self.assertIsInstance(convert_datetime_to_str_format([]), list)
        mock_debug.assert_called_with("Cannot convert object of type: [<type 'list'>] to datetime string format time.")

    @patch('enmutils.lib.log.logger.debug')
    def test_convert_str_to_datetime_object__success(self, mock_debug):
        self.assertIsInstance(convert_str_to_datetime_object("06-Feb, 13:20:38"), datetime)
        self.assertFalse(mock_debug.called)

    @patch('enmutils.lib.log.logger.debug')
    def test_convert_str_to_datetime_object__pattern_failue(self, mock_debug):
        convert_str_to_datetime_object("2020-02-06, 10:10")
        mock_debug.assert_called_with("Cannot convert object error encountered:: [time data '2020-02-06, 10:10' "
                                      "does not match format '%d-%b, %H:%M:%S'].")

    @patch('enmutils.lib.log.logger.debug')
    def test_convert_str_to_datetime_object__failure(self, mock_debug):
        convert_str_to_datetime_object([])
        self.assertIn("not list]", mock_debug.mock_calls[-1][1][0])

    def test_get_current_time__success(self):
        self.assertIsInstance(timestamp.get_current_time(), datetime)

    @patch("enmutils.lib.timestamp.datetime.datetime")
    @patch("enmutils.lib.timestamp.get_current_time")
    def test_is_time_current__success(self, mock_get_current_time, mock_datetime):
        mock_get_current_time.return_value = datetime(2020, 05, 12)
        test_res = datetime(2020, 05, 12)
        self.assertEqual(timestamp.is_time_current(test_res), True)

    def test_is_time_current__notsuccess(self):
        test_res = datetime(2020, 05, 12)
        self.assertEqual(timestamp.is_time_current(test_res), False)

    @patch("enmutils.lib.timestamp.datetime.datetime")
    @patch("enmutils.lib.timestamp.get_string_elapsed_time")
    def test_get_elapsed_time__sucess(self, mock_time, _):
        timestamp.get_elapsed_time(datetime.now())
        self.assertTrue(mock_time.called)

    @patch("enmutils.lib.timestamp.datetime.datetime")
    def test_get_elapsed_time_in_seconds__success(self, _):
        self.assertIsNotNone(timestamp.get_elapsed_time(datetime.now()))

    @patch("enmutils.lib.timestamp.datetime.datetime")
    def test_get_elapsed_time_in_duration_format__success(self, _):
        test_start = datetime(2020, 05, 8, 2, 05, 12)
        test_complete = datetime(2020, 05, 8, 2, 06, 15)
        res = timestamp.get_elapsed_time_in_duration_format(test_start, test_complete)
        self.assertEqual(res, "0h:1m:3s")

    @patch("enmutils.lib.timestamp.datetime.datetime")
    def test_get_human_readable_timestamp__success(self, _):
        test_res = timestamp.get_human_readable_timestamp(datetime(2020, 05, 8, 2, 05, 12))
        self.assertEqual(test_res, "2020/05/08 02:05:12")

    @patch("enmutils.lib.timestamp.datetime.datetime")
    def test_get_elapsed_time_in_duration_format__less_than_sixty(self, _):
        test_start = datetime(2020, 05, 8, 2, 05, 12)
        test_complete = datetime(2020, 05, 8, 2, 05, 15)
        self.assertEqual(timestamp.get_elapsed_time_in_duration_format(test_start, test_complete), "3 sec")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
