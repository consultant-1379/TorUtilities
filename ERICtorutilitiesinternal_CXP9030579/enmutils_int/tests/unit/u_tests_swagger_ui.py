#!/usr/bin/env python

import importlib
import unittest2
from flask import Flask
from mock import patch, Mock, mock_open
from testslib import unit_test_utils

from enmutils.lib.exceptions import InvalidOpenapiFormat
from enmutils_int.lib.services.swagger_ui import (register_swagger_blueprint, swagger_doc, get_url_view_function_map, load_openapi_specification,
                                                  register_view_functions)


OPENAPI_PATH_JSON = {'paths': {'/enm/users': {'get': {'description': 'Returns a list of usernames for all users that exist on ENM (view_function: enm_users)', 'tags': ['User'], 'responses': {'200': {'$ref': '#/components/responses/getAllUsernames'}, '404': {'$ref': '#/components/responses/404Abort'}}, 'summary': 'Get list of usernames for existing users'}}, '/users/delete': {'delete': {'description': 'Warning: passing no query parameters deletes all users. (view_function: delete_users)', 'tags': ['User'], 'responses': {'200': {'$ref': '#/components/responses/successJson'}, '404': {'$ref': '#/components/responses/404Abort'}}, 'parameters': [{'$ref': '#/components/parameters/deleteData'}], 'summary': 'Delete User(s) from ENM'}}, '/users/create': {'post': {'requestBody': {'$ref': '#/components/requestBodies/createUsers'}, 'description': 'Create a specified number of ENM users. (view_function: create)', 'tags': ['User'], 'responses': {'200': {'$ref': '#/components/responses/successJson'}, '500': {'$ref': '#/components/responses/500Abort'}}, 'summary': 'Create ENM User(s)'}}, '/users': {'get': {'description': 'Get list of ENM Users that exist. (view_function: get_users)', 'tags': ['User'], 'responses': {'200': {'$ref': '#/components/responses/getUsers'}, '404': {'$ref': '#/components/responses/404Abort'}}, 'parameters': [{'$ref': '#/components/parameters/username'}, {'$ref': '#/components/parameters/profile'}], 'summary': 'Returns a list of ENM Users.'}}}}
OPENAPI_PATH_JSON_MISSING_DESCRIPTION = {'paths': {'/some/endpoint': {'get': {'tags': ['NoDescription']}}}}
OPENAPI_PATH_JSON_MISSING_DESCRIPTION_VIEW_FUNCTION = {'paths': {'/some/endpoint': {'get': {'description': 'No view function mapping'}}}}

URL_METHOD_MAP = url_method_map = {'/enm/users': {'GET': 'enm_users'}, '/users/delete': {'DELETE': 'delete_users'},
                                   '/users/create': {'POST': 'create'}, '/users': {'GET': 'get_users'}}


class SwaggerUiTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.app = Flask(__name__)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.swagger_ui.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.services.swagger_ui.get_swaggerui_blueprint')
    def test_register_swagger_blueprint__open_api_spec_exists(self, mock_swagger_blueprint, _):
        register_swagger_blueprint(Mock(), 'usermanager')
        mock_swagger_blueprint.assert_called_once_with('/api/v1/docs', '/api/v1/docs/usermanager.json')

    @patch('enmutils_int.lib.services.swagger_ui.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.services.swagger_ui.log.logger.debug')
    def test_register_swagger_blueprint__open_api_spec_does_not_exist(self, mock_debug, *_):
        service_name = 'usermanager'
        register_swagger_blueprint(Mock(), service_name)
        mock_debug.assert_called_once_with('No Swagger documentation found for {0} service. '
                                           'Not registering Swagger UI blueprint.'.format(service_name))

    @patch('enmutils_int.lib.services.swagger_ui.yaml')
    @patch('enmutils_int.lib.services.swagger_ui.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.services.swagger_ui.jsonify')
    def test_swagger_doc_open_api_spec_exists(self, mock_jsonify, *_):
        with self.app.test_request_context(path='/usermanager.json'):
            with patch('__builtin__.open', mock_open()):
                swagger_doc()
                self.assertEqual(mock_jsonify.call_count, 1)

    @patch('enmutils_int.lib.services.swagger_ui.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.services.swagger_ui.abort')
    def test_swagger_doc_open_api_spec_does_not_exist(self, mock_abort, _):
        with self.app.test_request_context(path='/some_service.json'):
            swagger_doc()
            mock_abort.assert_called_once_with(404, 'Could not find Swagger documentation for service: some_service')

    @patch('enmutils_int.lib.services.swagger_ui.load_openapi_specification', return_value=OPENAPI_PATH_JSON)
    def test_get_url_method_map__correctly_formated_openapi_spec(self, *_):

        self.assertEqual(get_url_view_function_map('usermanager'), url_method_map)

    @patch('enmutils_int.lib.services.swagger_ui.load_openapi_specification', return_value=OPENAPI_PATH_JSON_MISSING_DESCRIPTION)
    def test_get_url_method_map__missing_description_attribute(self, _):

        with self.assertRaises(InvalidOpenapiFormat) as e:

            get_url_view_function_map('someservice')
        self.assertTrue(e.exception.message == 'Description attribute not found: Endpoint:/some/endpoint:get. '
                                               'Update Openapi specification for someservice')

    @patch('enmutils_int.lib.services.swagger_ui.load_openapi_specification', return_value=OPENAPI_PATH_JSON_MISSING_DESCRIPTION_VIEW_FUNCTION)
    def test_get_url_method_map__missing_view_function_from_description(self, _):
        with self.assertRaises(InvalidOpenapiFormat) as e:
            get_url_view_function_map('someservice')
        self.assertTrue(
            e.exception.message == 'No view function found in description attribute: No view function mapping: '
                                   'Endpoint:/some/endpoint:get. Update Openapi specification for someservice')

    @patch('enmutils_int.lib.services.swagger_ui.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.services.swagger_ui.yaml.safe_load')
    def test_load_openapi_specification_file_exists(self, mock_load, *_):
        with patch('__builtin__.open', mock_open()):
            load_openapi_specification('usermanager')
            self.assertTrue(mock_load.call_count == 1)

    @patch('enmutils_int.lib.services.swagger_ui.does_file_exist', return_value=False)
    def test_load_openapi_specification_file_does_not_exist(self, *_):
        self.assertIsNone(load_openapi_specification('usermanager'))

    @patch('enmutils_int.lib.services.swagger_ui.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.services.swagger_ui.get_url_view_function_map', return_value=URL_METHOD_MAP)
    def test_register_view_functions__register_using_openapi_spec(self, *_):
        module = importlib.import_module("{0}.{1}".format('enmutils_int.lib.services', 'usermanager'))
        register_view_functions(self.app, 'usermanager', module.__dict__)
        for rule in self.app.url_map._rules:
            if rule.rule == '/static/<path:filename>':
                continue
            self.assertTrue(rule.rule in URL_METHOD_MAP.keys())
            for method in URL_METHOD_MAP[rule.rule]:
                self.assertTrue(method in rule.methods)

    @patch('enmutils_int.lib.services.swagger_ui.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.services.swagger_ui.log.logger.debug')
    def test_register_view_functions__no_existing_openapi_spec(self, mock_debug, _):
        register_view_functions(Mock(), 'somemanager', Mock())
        mock_debug.assert_called_once_with('No Openapi specification found for service: somemanager. No view functions to register.')


if __name__ == "__main__":
    unittest2.main(verbosity=2)
