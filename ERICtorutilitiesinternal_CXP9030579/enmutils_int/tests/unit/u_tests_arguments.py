#!/usr/bin/env python
import string
import unittest2
from mock import patch, Mock

from enmutils.lib import arguments
from testslib import unit_test_utils
from parameterizedtestcase import ParameterizedTestCase


class ArgumentsUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils.lib.init.exit")
    @ParameterizedTestCase.parameterize(
        ('addresses', 'expected_result'),
        [
            ("one@yahoo.com", False),
            ("one@yahoo.com,two@gmail.com", False),
            ("one@yahoo.com, two@gmail.com", False),
            ("james@fail", True),
            ("one@yahoo.com, abc@nothing,two@gmail.com", True),
            ("f@f.f", True),
            ("f,j@ibm.com", True),
            ("123$@ericsson.se", True),
            ("james22@fail.org", False),
            (1234, True),
            ("foobar", True)
        ]
    )
    def test_get_email_addresses(self, addresses, expected_result, mock_exit):
        arguments.get_email_addresses(addresses)
        self.assertEqual(expected_result, mock_exit.called)

        # If we expect init.exit() to have been invoked, assert that he was called with rc = 2
        if expected_result:
            self.assertEqual((2,), mock_exit.call_args[0])

    @patch("enmutils.lib.init.exit")
    @ParameterizedTestCase.parameterize(
        ('numeric_range', 'expected_result'),
        [
            ("1-2", False),
            ("1", False),
            ("0-3", False),
            ("-2-5", True),
            ("-2", True),
            ("14-3", True),
            (5, True),
            ("00X00", True)
        ]
    )
    def test_get_numeric_range(self, numeric_range, expected_result, mock_exit):
        arguments.get_numeric_range(numeric_range)
        self.assertEqual(expected_result, mock_exit.called)
        # If we expect init.exit() to have been invoked, assert that he was called with rc = 2
        if expected_result:
            self.assertEqual((2,), mock_exit.call_args[0])

    def test_get_random_string_returns_correct_length(self):
        self.assertEqual(len(arguments.get_random_string(9)), 9)

    def test_get_random_string_excludes_correctly(self):
        exclude = string.ascii_letters
        self.assertNotIn(arguments.get_random_string(exclude=exclude), exclude)

    def test_get_random_string_returns_password_correctly(self):
        self.assertEqual(arguments.get_random_string(password=True)[-3:], ".8z")

    @ParameterizedTestCase.parameterize(
        ('email_address', 'expected_result'),
        [
            ("pass@yahoo.com", True),
            ("pass@T-mobile.com", True),
            ("james@fail", False),
            ("f@f.f", False),
            ("f,j@ibm.com", False),
            ("123$@ericsson.se", False),
            ("james22@fail.org", True),
            ("kevin@bbc.co.uk", True),
            (1234, False),
            ("foobar", False),
            ("a" * 245 + "@email.com", True),
            ("a" * 246 + "@email.com", False),
            ("ab@c.ie", True)
        ]
    )
    def test_is_valid_email_address(self, email_address, expected_result):
        self.assertEqual(expected_result, arguments.is_valid_email_address(email_address))

    @patch("enmutils.lib.arguments.exception.handle_invalid_argument")
    def test_validate_email_address_with_invalid_email_invokes_handle_invalid_exception(self,
                                                                                        mock_handle_invalid_argument):
        arguments.validate_email_address("john@foobar")
        self.assertTrue(mock_handle_invalid_argument.called)

    @ParameterizedTestCase.parameterize(
        ('version_number', 'expected_result'),
        [
            ("1234", True),
            ("-1.2.3", False),
            ("1.2.3", True),
            ("100.200.300", True),
            ("1.2.-3", False),
        ]
    )
    def test_is_valid_version_number(self, version_number, expected_result):
        self.assertEqual(expected_result, arguments.is_valid_version_number(version_number))

    @patch("enmutils.lib.arguments.re.match", side_effect=AttributeError)
    def test_is_valid_version_number__attribute_error(self, _):
        self.assertEqual(arguments.is_valid_version_number("none"), False)

    def test_is_valid_hostname__len_less_than_255(self):
        self.assertEqual(arguments.is_valid_hostname("host1-23.athtem.999.ericsson"), True)

    def test_is_valid_hostname__len_less_than_255_with_dot(self):
        self.assertEqual(arguments.is_valid_hostname("host1-23.athtem.999.ericsson."), True)

    def test_is_valid_hostname__len_more_than_255(self):
        mock_hostname = Mock()
        mock_hostname.__len__ = Mock(return_value=256)
        self.assertEqual(arguments.is_valid_hostname(mock_hostname), False)

    def test_grouper__return_correct(self):
        x = arguments.grouper("HELLO", 5)
        self.assertListEqual([("H", "E", "L", "L", "O")], x)

    def test_splits_list_into_chunks(self):
        x = arguments.split_list_into_chunks(["random", "stuff"], 5)
        self.assertListEqual([["random", "stuff"]], x)

    @patch("enmutils.lib.arguments.exception.handle_invalid_argument")
    def test_validate_version_number_with_invalid_version_invokes_handle_invalid_exception(self,
                                                                                           mock_handle_invalid_argument):
        arguments.validate_version_number("a.-1.z")
        self.assertTrue(mock_handle_invalid_argument.assert_called)

    @patch("enmutils.lib.arguments.is_valid_version_number", return_value=True)
    @patch("enmutils.lib.arguments.exception.handle_invalid_argument")
    def test_validate_version_number__correct(self, mock_handle_invalid_argument, *_):
        arguments.validate_version_number("1.2.3")
        self.assertTrue(mock_handle_invalid_argument.assert_called(0))

    @patch("enmutils.lib.exception.handle_invalid_argument")
    def test_validate_range_with_invalid_range_invokes_handle_invalid_exception(self, mock_handle_invalid_argument):
        arguments.validate_range(-5, -10)
        self.assertTrue(mock_handle_invalid_argument.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
