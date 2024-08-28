import pkgutil
import os
import unipath
from flask import jsonify, request, abort
from flask_swagger_ui import get_swaggerui_blueprint
import yaml

from enmutils.lib.exceptions import InvalidOpenapiFormat
from enmutils.lib import log
from enmutils.lib.filesystem import does_file_exist
from enmutils_int.lib.services.service_values import URL_PREFIX


SWAGGER_URL = os.path.join(URL_PREFIX, 'docs')
API_URL = os.path.join(SWAGGER_URL, "{service_name}.json")
OPENAPI_DIR = unipath.Path(pkgutil.get_loader('enmutils_int').filename).child("etc").child("openapi")


def load_openapi_specification(service_name):
    """
    Load Service Openapi specification if it exists.
    :param service_name: Name of service
    :type service_name: str
    :return: Openapi specification as dict
    :rtype: dict
    """

    openapi_specification_path = '{0}.yml'.format(os.path.join(OPENAPI_DIR, service_name))
    if does_file_exist(openapi_specification_path):
        with open(openapi_specification_path, 'r') as openapi:
            return yaml.safe_load(openapi)


def register_swagger_blueprint(app, service_name):
    """
    Register Swagger UI blueprint on the provided app if OpenApi spec exists for the service.
    :param app: flask app
    :type app: flask.Flask
    :param service_name: Service name
    :type service_name: string
    """

    if does_file_exist(os.path.join(OPENAPI_DIR, '{service_name}.yml'.format(service_name=service_name))):
        log.logger.debug('Registering Swagger blueprint on {0} service'.format(service_name))
        api_url = API_URL.format(service_name=service_name)
        swagger_ui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, api_url)
        swagger_ui_blueprint.add_url_rule('/{0}.json'.format(service_name), view_func=swagger_doc)
        app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
        log.logger.debug('View Swagger Ui at {0}'.format(SWAGGER_URL))
    else:
        log.logger.debug('No Swagger documentation found for {0} service. '
                         'Not registering Swagger UI blueprint.'.format(service_name))


def swagger_doc():
    """
    Swagger view function. Returns the requested service OpenApi spec yaml file contents as json.
    :return: Service OpenApi spec.
    :rtype: flask.Response
    """

    service_name = request.path.split('/')[-1].split('.')[0]
    open_api_file_path = os.path.join(OPENAPI_DIR, '{0}.yml'.format(service_name))
    if does_file_exist(open_api_file_path):
        with open(open_api_file_path) as open_api_spec:
            return jsonify(yaml.load(open_api_spec, Loader=yaml.FullLoader))
    else:
        return abort(404, 'Could not find Swagger documentation for service: {0}'.format(service_name))


def get_url_view_function_map(service_name):
    """
    Builds a url map from the service yml file.
    EXAMPLE:
        {
            '/enm/users': {'get': 'enm_users'},
            '/users': {'get': 'get_users'},
            '/users/create': {'post': 'create'},
            '/users/delete': {'delete': 'delete_users'}
        }
    :return: Map of url endpoint to view functions
    :rtype: dict
    :raises InvalidOpenapiFormat: If missing description attribute or view_function not specified in description.
    """
    paths = load_openapi_specification(service_name)['paths']
    url_map = {}
    for path, methods in paths.items():
        url_map[path] = {}
        for method_type, request_structure in methods.items():
            try:
                if 'view_function:' in request_structure['description']:
                    url_map[path][method_type.upper()] = request_structure['description'].strip('()').split('view_function: ')[-1]
                else:
                    raise InvalidOpenapiFormat('No view function found in description attribute: '
                                               '{0}: Endpoint:{1}:{2}'.format(request_structure['description'], path,
                                                                              method_type), service_name)
            except KeyError:
                raise InvalidOpenapiFormat('Description attribute not found: '
                                           'Endpoint:{0}:{1}'.format(path, method_type), service_name)
    return url_map


def register_view_functions(app, service_name, module_dict):
    """
    Registers view functions on a flask app or blueprint.
    View functions are defined in the associated OpenApi yml file
    :param app: Flask application/blueprint to register view functions on.
    :type app: flask.Flask or flask.Blueprint
    :param service_name: Name of service
    :type service_name: str
    :param module_dict: Module dict containing view functions
    :type module_dict: dict
    """

    if does_file_exist(os.path.join(OPENAPI_DIR, '{0}.yml'.format(service_name))):
        log.logger.debug('Parsing Openapi specification for view functions.')
        url_map = get_url_view_function_map(service_name)
        for endpoint, http_methods in url_map.items():
            for http_method, view_func in http_methods.items():
                log.logger.debug('Adding view function: {method}: {endpoint}'.format(method=http_method, endpoint=endpoint))
                app.add_url_rule(endpoint, view_func=module_dict[view_func], methods=[http_method])
    else:
        log.logger.debug('No Openapi specification found for service: {0}. No view functions to register.'.format(service_name))
