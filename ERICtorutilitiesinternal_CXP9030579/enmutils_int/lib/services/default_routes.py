import threading
import time

from enmutils.lib import log
from enmutils_int.bin.wl_service import get_service_name_from_running_service, log_message
from flask import Blueprint, request

default_blueprint = Blueprint("default_blueprint", __name__)


@default_blueprint.before_app_request
def log_application_request():
    """
    Log details of request (excluding service status requests)

    This function will also update the name of the running thread based on:
    1) the epoch timestamp at the point in time when the request was received, and
    2) the remote port from where the request originated
    """
    request_env = request.environ
    if request_env["PATH_INFO"] != "/status":
        threading.current_thread().name = "{0}_{1}".format(request_env["REMOTE_PORT"], time.time())
        log.logger.debug("Request received: {0}".format(request_env))
        log.logger.debug("Data received in request: {0}".format(request.get_json()))


@default_blueprint.route("/status")
def server_status():
    """
    Route handling the status of the currently running web server
    :return: Message to say that server is running
    :rtype: str
    """
    server_port = request.environ.get('SERVER_PORT')
    service_name = get_service_name_from_running_service()
    message = ("Webserver for Workload Service {0} is running and listening on port: {1}"
               .format(service_name, server_port))
    return message


@default_blueprint.errorhandler(Exception)
def handle_error(error):
    """
    Route that handles web server errors

    :param error: Error that is encountered
    :type error: Exception
    :returns: Error message
    :rtype: str
    """
    log_message("ERROR: {0}".format(error))
    return "Error encountered: {0}".format(error)
