#!/usr/bin/env python
# ********************************************************************
# Name    : workload_service
# Purpose : Workload tool that runs an application service
# Team    : Blade Runners
# ********************************************************************

"""
wl_service - Starts basic service structure

Usage:
  wl_service SERVICE_NAME [ACTION]

Arguments:
   SERVICE_NAME     Service Name
   ACTION           status

Examples:
    ./wl_service usermanager
        Will start service called "usermanager"
    ./wl_service usermanager status
        Will get status of service called "usermanager"

Options:
  -h        Print this help text
"""

import commands
import importlib
import logging
import logging.handlers
import sys

from docopt import docopt
from flask import Flask, request
from waitress import serve

from enmutils.lib import log, config
from enmutils_int.lib.services import service_registry
from enmutils_int.lib.services.swagger_ui import register_swagger_blueprint, register_view_functions

app = None
service_logger = None

PATH_TO_SERVICES = "enmutils_int.lib.services"  # Location of application service code


def get_service_name_from_running_service():
    """
    Perform lookup of service name in registry using SERVER_PORT of currently running web server

    :return: Name of service
    :rtype: str
    """
    server_port = request.environ.get('SERVER_PORT')
    return service_registry.get_service_name_for_service_port(server_port)


def start(service_name):
    """
    Starts web service for application
    :param service_name: Name of service
    :type service_name: str

    :raises RuntimeError: if service is not registered
    """
    log_message("Starting {0} service".format(service_name))

    config.load_config("int", True)

    initialize_webserver(service_name)

    service_port, _, service_thread_count = service_registry.get_service_info_for_service_name(service_name)

    app.logger.addHandler(service_logger.handlers[0])
    app.logger.info("Logging is set up.")

    try:
        log_message("Starting web server, with {1} threads, listening for requests on port {0}"
                    .format(service_port, service_thread_count))
        initial_request(service_name)
        serve(app, port=service_port, threads=service_thread_count)
    except Exception as e:
        message = ("Service {service_name} already running" if "Address already in use" in str(e) else
                   "Error occurred during start of service {0}")
        raise RuntimeError(message.format(service_name=service_name))


def initial_request(service_name):
    """
    Check if the service has a start up function and trigger if True

    :param service_name: Service name
    :type service_name: str
    """
    module = importlib.import_module("{0}.{1}".format(PATH_TO_SERVICES, service_name))
    if getattr(module, 'at_startup', None):
        global app
        log_message("Calling start up function for service: [{0}].".format(service_name))
        app.before_first_request(getattr(module, 'at_startup'))
        app.try_trigger_before_first_request_functions()
        log_message("Start up function called for service: [{0}].".format(service_name))


def initialize_webserver(service_name):
    """
    Initialize webserver

    :param service_name: Service name
    :type service_name: str
    """
    initialize_application_logger(service_name)
    global app
    app = Flask(__name__)
    register_blueprints(service_name)


def initialize_application_logger(service_name):
    """
    Initialize application logger

    :param service_name: Service name
    :type service_name: str

    """
    if not log.logger:
        log.simplified_log_init(service_name, log_dir=log.SERVICES_LOG_DIR)


def status(service_name):
    """
    Gets application service status

    :param service_name: Name of service
    :type service_name: str
    :returns: Message regarding status
    :rtype: str
    :raises RuntimeError: if service is not running
    """
    service_port, service_host, _ = service_registry.get_service_info_for_service_name(service_name)
    url = "http://{0}:{1}/status".format(service_host, service_port)
    cmd = "curl -m5 -Ss \"{url}\" 2>&1".format(url=url)
    try:
        content = commands.getoutput(cmd)
        if "timed out" in content:
            raise RuntimeError(content)
    except Exception as e:
        raise RuntimeError("Problem encountered checking {0} status. Attempted to run command: '{1}'. "
                           "Result: {2}".format(service_name, cmd, str(e)))

    if "is running" not in str(content):
        raise RuntimeError("Service {0} not running".format(service_name))
    message = "{0}".format(content)
    log_message(message)
    return message


def log_message(message):
    """
    Wrapper for logging

    :param message: Message to be logged
    :type message: str
    """
    if not service_logger:
        initialize_logger(get_service_name_from_running_service())

    service_logger.debug(message)


def initialize_logger(service_name):
    """
    Initialize logging to file & stdout

    :return: logging instance
    :rtype: logging.Logger
    """
    global service_logger
    service_logger = logging.getLogger("service")

    commands.getoutput('mkdir -p {0}'.format(log.SERVICES_LOG_DIR))

    logfile_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler = logging.handlers.WatchedFileHandler('{0}/{1}.log'.format(log.SERVICES_LOG_DIR, service_name))
    file_handler.setFormatter(logfile_formatter)

    stdout_formatter = logging.Formatter('%(message)s')
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(stdout_formatter)

    service_logger.addHandler(file_handler)
    service_logger.addHandler(stdout_handler)
    service_logger.setLevel(logging.DEBUG)

    return service_logger


def get_arguments():
    """
    Process command line arguments

    :returns: Service Name and Action
    :rtype: tuple
    :raises SystemExit: if problems encountered parsing arguments
    """

    try:
        arguments = docopt(__doc__)
    except SystemExit as e:
        raise SystemExit(e)

    service_name = arguments['SERVICE_NAME']
    action = arguments['ACTION']
    if not action:
        action = "start"

    if action not in globals().iterkeys():
        raise SystemExit("Action not defined: {0}. See usage with option '-h'".format(action))

    if service_name not in service_registry.get_registry_data().iterkeys():
        raise SystemExit("Service name {0} not defined in registry".format(service_name))

    return service_name, action


def register_blueprints(service_name):
    """
    Register blueprints with the flask server

    :param service_name: Name of Service
    :type service_name: str
    :raises RuntimeError: if cannot register blueprint
    """
    global app
    try:
        # Import default routes blueprint
        module = importlib.import_module("{0}.{1}".format(PATH_TO_SERVICES, "default_routes"))

        # Register default routes blueprint with flask server app
        app.register_blueprint(module.__dict__["default_blueprint"])
    except Exception as e:
        raise RuntimeError("Error registering default blueprint: {0}".format(e))

    try:
        # Import application blueprint
        module = importlib.import_module("{0}.{1}".format(PATH_TO_SERVICES, service_name))

        # Register application routes blueprint with flask server app
        application_blueprint = module.__dict__["application_blueprint"]
        register_view_functions(application_blueprint, service_name, module.__dict__)
        app.register_blueprint(application_blueprint)
    except Exception as e:
        raise RuntimeError("Error registering application blueprint: {0}".format(e))

    # Add swagger ui to flask application
    register_swagger_blueprint(app, service_name)
    log.logger.debug('Service endpoints: {0}'.format(app.url_map))


def cli():
    """
    Main function to run when script is called from command line
    """
    service_name, action = get_arguments()

    rc = 0
    try:
        # Initialize logger
        initialize_logger(service_name)

        # Run the action on the running service
        globals()[action](service_name)
    except Exception as e:
        raise SystemExit("{0}".format(e))

    return rc


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cli())
