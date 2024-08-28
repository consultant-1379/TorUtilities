#!/usr/bin/env python
import __builtin__

import sys
import unittest2
from mock import Mock, patch, mock_open

import enmutils_int.lib.py_json_html_converter as converter
from testslib import unit_test_utils


class PyJsonHtmlConverterUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.my_dict = {
            "forty_k_network": {
                "cpp": {
                    "cmcli": {
                        'CMCLI_02': {'NUM_USERS': 100, 'SUPPORTED': True, 'NUM_NODES': {'ERBS': 100}}
                    },
                    "cmexport": {
                        'CMEXPORT_01': {'SUPPORTED': True, 'NODE_REGEX': '*LTE*', 'NUM_NODES': {'ERBS': -1}},
                        'CMEXPORT_02': {'SUPPORTED': True, 'CM_EXPORT_FILTER': 'SON', 'NUM_NODES': {}, 'NUMBER_OF_NETWORK_EXPORTS': 3},
                        'CMEXPORT_03': {'NUM_USERS': 10, 'SUPPORTED': True, 'CM_EXPORT_FILTER': 'SON', 'NUM_NODES': {'ERBS': -1}},
                        'CMEXPORT_05': {'SUPPORTED': True, 'CM_EXPORT_FILTER': 'SON', 'NUM_NODES': {}},
                        'CMEXPORT_07': {'SUPPORTED': True, 'NUM_NODES': {'ERBS': 300}}, 'core': {'name': 'CMEXPORT_07'},
                        'CMEXPORT_08': {'NUMBER_OF_EXPORTS': 10, 'SUPPORTED': True, 'NUMBER_OF_CELLS': 3, 'NUM_NODES': {'ERBS': -1}},
                        'CMEXPORT_11': {'NUMBER_OF_EXPORTS': 500, 'SUPPORTED': True, 'NUMBER_OF_CELLS': 6, 'NUM_NODES': {'ERBS': -1}},
                        'CMEXPORT_12': {'SUPPORTED': False, 'NODE_BATCH_SIZE': 500, 'NUM_NODES': {'ERBS': -1, 'SGSN': -1, 'MGW': -1, 'RadioNode': -1}},
                        'CMEXPORT_13': {'SUPPORTED': True, 'NUM_NODES': {'RadioNode': -1, 'SGSN': -1, 'MGW': -1}},
                        'CMEXPORT_14': {'SUPPORTED': True, 'NUM_NODES': {'MLTN': -1, 'SpitFire': -1}},
                        'CMEXPORT_16': {'SUPPORTED': True, 'NUM_NODES': {}}
                    }
                }
            }
        }
        self.my_json = '{"forty_k_network": {"cpp": {"cmexport": {"core": {"name": "CMEXPORT_07"}, "CMEXPORT_16": {"SUPPORTED": true, "NUM_NODES": {}}, "CMEXPORT_12": {"SUPPORTED": false, "NODE_BATCH_SIZE": 500, "NUM_NODES": {"ERBS": -1, "SGSN": -1, "MGW": -1, "RadioNode": -1}}, "CMEXPORT_11": {"NUMBER_OF_EXPORTS": 500, "SUPPORTED": true, "NUMBER_OF_CELLS": 6, "NUM_NODES": {"ERBS": -1}}, "CMEXPORT_07": {"SUPPORTED": true, "NUM_NODES": {"ERBS": 300}}, "CMEXPORT_13": {"SUPPORTED": true, "NUM_NODES": {"RadioNode": -1, "SGSN": -1, "MGW": -1}}, "CMEXPORT_05": {"SUPPORTED": true, "CM_EXPORT_FILTER": "SON", "NUM_NODES": {}}, "CMEXPORT_02": {"NUMBER_OF_NETWORK_EXPORTS": 3, "SUPPORTED": true, "CM_EXPORT_FILTER": "SON", "NUM_NODES": {}}, "CMEXPORT_03": {"NUM_USERS": 10, "SUPPORTED": true, "CM_EXPORT_FILTER": "SON", "NUM_NODES": {"ERBS": -1}}, "CMEXPORT_01": {"SUPPORTED": true, "NODE_REGEX": "*LTE*", "NUM_NODES": {"ERBS": -1}}, "CMEXPORT_08": {"NUMBER_OF_EXPORTS": 10, "SUPPORTED": true, "NUMBER_OF_CELLS": 3, "NUM_NODES": {"ERBS": -1}}, "CMEXPORT_14": {"SUPPORTED": true, "NUM_NODES": {"MLTN": -1, "SpitFire": -1}}}, "cmcli": {"CMCLI_02": {"NUM_USERS": 100, "SUPPORTED": true, "NUM_NODES": {"ERBS": 100}}}}}}'
        self.my_html = '<caption><h2>WORKLOAD PROFILES - version: 1.2.3.4</h2></caption><style>table, th, td {border: 1px solid black; border-collapse: collapse;padding: 5px; background-color: #ffffff;}</style><table border="1"><tr><th>forty_k_network</th><td><table border="1"><tr><th>cpp</th><td><table border="1"><tr><th>cmexport</th><td><table border="1"><tr><th>core</th><td><table border="1"><tr><th>name</th><td>CMEXPORT_07</td></tr></table></td></tr><tr><th>CMEXPORT_14</th><td><table border="1"><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>NUM_NODES</th><td><table border="1"><tr><th>MLTN</th><td>-1</td></tr><tr><th>SpitFire</th><td>-1</td></tr></table></td></tr></table></td></tr><tr><th>CMEXPORT_01</th><td><table border="1"><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>NODE_REGEX</th><td>*LTE*</td></tr><tr><th>NUM_NODES</th><td><table border="1"><tr><th>ERBS</th><td>-1</td></tr></table></td></tr></table></td></tr><tr><th>CMEXPORT_11</th><td><table border="1"><tr><th>NUMBER_OF_EXPORTS</th><td>500</td></tr><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>NUMBER_OF_CELLS</th><td>6</td></tr><tr><th>NUM_NODES</th><td><table border="1"><tr><th>ERBS</th><td>-1</td></tr></table></td></tr></table></td></tr><tr><th>CMEXPORT_07</th><td><table border="1"><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>NUM_NODES</th><td><table border="1"><tr><th>ERBS</th><td>300</td></tr></table></td></tr></table></td></tr><tr><th>CMEXPORT_13</th><td><table border="1"><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>NUM_NODES</th><td><table border="1"><tr><th>RadioNode</th><td>-1</td></tr><tr><th>SGSN</th><td>-1</td></tr><tr><th>MGW</th><td>-1</td></tr></table></td></tr></table></td></tr><tr><th>CMEXPORT_12</th><td><table border="1"><tr><th>SUPPORTED</th><td>False</td></tr><tr><th>NODE_BATCH_SIZE</th><td>500</td></tr><tr><th>NUM_NODES</th><td><table border="1"><tr><th>ERBS</th><td>-1</td></tr><tr><th>SGSN</th><td>-1</td></tr><tr><th>MGW</th><td>-1</td></tr><tr><th>RadioNode</th><td>-1</td></tr></table></td></tr></table></td></tr><tr><th>CMEXPORT_02</th><td><table border="1"><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>NUM_NODES</th><td><table border="1"></table></td></tr><tr><th>CM_EXPORT_FILTER</th><td>SON</td></tr><tr><th>NUMBER_OF_NETWORK_EXPORTS</th><td>3</td></tr></table></td></tr><tr><th>CMEXPORT_03</th><td><table border="1"><tr><th>NUM_USERS</th><td>10</td></tr><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>CM_EXPORT_FILTER</th><td>SON</td></tr><tr><th>NUM_NODES</th><td><table border="1"><tr><th>ERBS</th><td>-1</td></tr></table></td></tr></table></td></tr><tr><th>CMEXPORT_16</th><td><table border="1"><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>NUM_NODES</th><td><table border="1"></table></td></tr></table></td></tr><tr><th>CMEXPORT_08</th><td><table border="1"><tr><th>NUMBER_OF_EXPORTS</th><td>10</td></tr><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>NUMBER_OF_CELLS</th><td>3</td></tr><tr><th>NUM_NODES</th><td><table border="1"><tr><th>ERBS</th><td>-1</td></tr></table></td></tr></table></td></tr><tr><th>CMEXPORT_05</th><td><table border="1"><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>CM_EXPORT_FILTER</th><td>SON</td></tr><tr><th>NUM_NODES</th><td><table border="1"></table></td></tr></table></td></tr></table></td></tr><tr><th>cmcli</th><td><table border="1"><tr><th>CMCLI_02</th><td><table border="1"><tr><th>NUM_USERS</th><td>100</td></tr><tr><th>SUPPORTED</th><td>True</td></tr><tr><th>NUM_NODES</th><td><table border="1"><tr><th>ERBS</th><td>100</td></tr></table></td></tr></table></td></tr></table></td></tr></table></td></tr></table></td></tr></table>'

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_html(self):
        converted = converter.get_html('1.2.3.4', self.my_dict)
        self.assertEqual(self.my_html, converted)

    def test_convert_from_dict_to_json(self):
        converted = converter.convert_from_dict_to_json(self.my_dict)
        self.assertEqual(self.my_json, converted)

    def test_convert_from_json_to_dict(self):
        converted = converter.convert_from_json_to_dict(self.my_json)
        self.assertEqual(self.my_dict, converted)

    def test_get_env_variable(self):
        converter._get_env_variable("")

    def test_create_python_module_from_file_raises_io_error(self):
        converter.create_python_module_from_file("networks_file")

    def test_get_json_from_a_file(self):
        open_ = mock_open()
        with patch.object(__builtin__, "open", open_):
            converter.get_json_from_a_file("networks_file")

    @patch("enmutils_int.lib.py_json_html_converter.imp.new_module")
    def test_create_python_module_from_file__success(self, mock_imp):
        mock_imp.return_value.__dict__.update({"data1": "data"})
        with patch("__builtin__.open", mock_open(read_data="data1")):
            with patch("__builtin__.compile", return_value="") as mock_compile:
                converter.create_python_module_from_file("/path/to/networks_file")
                mock_compile.assert_called_once_with('data1', '/path/to/networks_file', 'exec')

    def test_cli_calls_print_help(self):
        sys.argv = ['./u_tests_py_json_html_converter.py', '--help']
        converter.cli()

    @patch("enmutils_int.lib.py_json_html_converter.create_python_module_from_file")
    def test_cli_path_to_networks(self, mock_converter):
        mock_converter = Mock()
        mock_converter.networks = "networks"
        sys.argv = ['./u_tests_py_json_htmlconverter.py', '--path-to-networks=/tmp/blah']
        converter.cli()

    @patch("enmutils_int.lib.py_json_html_converter.get_html")
    def test_cli_html_option_extension(self, mock_html):
        open_ = mock_open()
        sys.argv = ['./u_tests_py_json_htmlconverter.py', '--html']
        mock_html.return_value = ""
        with patch.object(__builtin__, "open", open_):
            converter.cli()

    @patch("enmutils_int.lib.py_json_html_converter.convert_from_dict_to_json")
    def test_cli_json_option_extension(self, mock_json):
        open_ = mock_open()
        sys.argv = ['./u_tests_py_json_htmlconverter.py', '--json']
        mock_json.return_value = ""
        with patch.object(__builtin__, "open", open_):
            converter.cli()

if __name__ == "__main__":
    unittest2.main(verbosity=2)
