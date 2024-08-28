#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils_int.lib.enm_ne_type_info import (ScriptEngineResponseValidationError, get_enm_supported_models,
                                               sorted_model_info, print_supported_node_info, describe_ne_type)
from testslib import unit_test_utils

RESPONSE_DATA = [u'Ne Type\tNe Release\tProduct Identity\tRevision (R-State)\tFunctional MIM Name\t'
                 u'Functional MIM Version\tModel ID',
                 u'RadioNode\t20.Q1\t-\t-\tRADIO_NODE_MODEL\t12345\t20.Q1-12345',
                 u'ERBS\t14A\tIdentity\tRevision\tERBS_NODE_MODEL\tE.1.63\t6824-690-779',
                 u'ERBS\t14A\t-\t-\tERBS_NODE_MODEL\tE.1.63\t4322-436-393', u'', u'', u'3 instance(s)']


class EnmNeTypeInfoUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.expected = {
            'RadioNode': [
                ['RadioNode', '20.Q1', '-', '-', 'RADIO_NODE_MODEL', '12345', '20.Q1-12345']
            ],
            'ERBS': [
                ['ERBS', '14A', 'Identity', 'Revision', 'ERBS_NODE_MODEL', 'E.1.63', '6824-690-779'],
                ['ERBS', '14A', '-', '-', 'ERBS_NODE_MODEL', 'E.1.63', '4322-436-393']
            ]}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.enm_ne_type_info.persistence.get', return_value=True)
    @patch('enmutils_int.lib.enm_ne_type_info.sorted_model_info')
    def test_get_enm_supported_models__uses_persisted_values_if_available(self, *_):
        get_enm_supported_models(self.user)
        self.assertEqual(0, self.user.enm_execute.call_count)

    @patch('enmutils_int.lib.enm_ne_type_info.persistence.get', return_value=False)
    @patch('enmutils_int.lib.enm_ne_type_info.persistence.set')
    @patch('enmutils_int.lib.enm_ne_type_info.sorted_model_info')
    def test_get_enm_supported_models__queries_enm(self, *_):
        response = Mock()
        response.get_output.return_value = RESPONSE_DATA
        self.user.enm_execute.return_value = response
        get_enm_supported_models(self.user)
        self.assertEqual(1, self.user.enm_execute.call_count)

    @patch('enmutils_int.lib.enm_ne_type_info.persistence.get', return_value=False)
    def test_get_enm_supported_models__raises_script_engine_error(self, _):
        response = Mock()
        response.get_output.return_value = [u'Error', u'', u'', u'0 instance(s)']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, get_enm_supported_models, self.user)

    def test_sorted_model_info__sorts_enm_info_correctly(self):
        self.assertDictEqual(self.expected, sorted_model_info(RESPONSE_DATA[1:-3]))

    @patch('enmutils_int.lib.enm_ne_type_info.get_enm_supported_models')
    def test_describe_ne_type__return_all_models(self, mock_get):
        mock_get.return_value = self.expected
        self.assertEqual((self.expected, []), describe_ne_type(self.user))

    @patch('enmutils_int.lib.enm_ne_type_info.get_enm_supported_models')
    def test_describe_ne_type__filters_models(self, mock_get):
        mock_get.return_value = self.expected
        expected = ({'ERBS': [['ERBS', '14A', 'Identity', 'Revision', 'ERBS_NODE_MODEL', 'E.1.63', '6824-690-779'],
                              ['ERBS', '14A', '-', '-', 'ERBS_NODE_MODEL', 'E.1.63', '4322-436-393']]}, ["NOTAMODEL"])
        self.assertEqual(expected, describe_ne_type(self.user, models=["ERBS", "NOTAMODEL"]))

    @patch('enmutils_int.lib.enm_ne_type_info.log.purple_text')
    @patch('enmutils_int.lib.enm_ne_type_info.describe_ne_type')
    def test_print_supported_node_info__logs_models(self, mock_describe, mock_purple):
        mock_describe.return_value = (self.expected, [])
        print_supported_node_info(self.user)
        mock_purple.assert_any_call("RadioNode")
        mock_purple.assert_any_call("ERBS")

    @patch('enmutils_int.lib.enm_ne_type_info.log.red_text')
    @patch('enmutils_int.lib.enm_ne_type_info.log.purple_text')
    @patch('enmutils_int.lib.enm_ne_type_info.describe_ne_type')
    def test_print_supported_node_info__logs_invalid_models(self, mock_describe, mock_purple, mock_red):
        mock_describe.return_value = (self.expected, ["NOTAMODEL"])
        print_supported_node_info(self.user)
        mock_purple.assert_any_call("RadioNode")
        mock_purple.assert_any_call("ERBS")
        inv = ("\t NO ENM SUPPORTED MODEL INFO FOR NE TYPES [{0}].\n\t Please confirm NE TYPE is supported by ENM, "
               "NE TYPES are case sensitive.\n".format(", ".join(["NOTAMODEL"])))
        mock_red.assert_called_with(inv)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
