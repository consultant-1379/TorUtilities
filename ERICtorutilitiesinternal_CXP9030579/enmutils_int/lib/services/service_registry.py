import json
import os.path
import pkgutil

from enmutils_int.lib.services.service_values import SERVICE_HOST_DEFAULT

ENMUTILS_INT_PATH = pkgutil.get_loader('enmutils_int').filename
SERVICE_REGISTRY_FILE = os.path.join(ENMUTILS_INT_PATH, 'etc', 'service_registry_data.json')
SERVICE_UNDER_TEST_FLAG_FILE = "/var/tmp/.{service_name}.service_under_test"


def get_registry_data():
    """
    Fetch service port from service registry

    :return: Service Data
    :rtype: dict
    """
    with open(SERVICE_REGISTRY_FILE) as registry_file:
        registry_data = json.load(registry_file)

    return registry_data


def can_service_be_used(service_name, priority=None):
    """
    Determine if service can be used

    :param service_name: Name of service
    :type service_name: str
    :param priority: Profile priority
    :type priority: int

    :return: Boolean to indicate if service can be used or not
    :rtype: bool
    """
    registry_data = get_registry_data()
    if service_name in registry_data.keys():
        if registry_data[service_name].get("test"):
            return True if os.path.isfile(SERVICE_UNDER_TEST_FLAG_FILE.format(service_name=service_name)) else False

        if ((priority and registry_data[service_name].get("P{0}".format(priority))) or
                registry_data[service_name].get("tool")):
            return True


def get_service_info_for_service_name(service_name):
    """
    Get Service info from registry for a particular service name

    :param service_name: Service Name
    :type service_name: str
    :return: Tuple of Service Port and Service Host, and thread count
    :rtype: tuple
    :raises RuntimeError: if service not defined in registry or port number is missing
    """
    service_info = get_registry_data().get(service_name)
    if not service_info:
        raise RuntimeError("Service {0} not defined in registry".format(service_name))

    service_host = service_info.get("host") or SERVICE_HOST_DEFAULT
    service_port = service_info.get("port")
    service_thread_count = service_info.get("threads")

    if not service_port:
        raise RuntimeError("Service Port not found not found in registry {0} for service {1}"
                           .format(SERVICE_REGISTRY_FILE, service_name))

    return service_port, service_host, service_thread_count


def get_service_name_for_service_port(service_port):
    """
    Get the service name for a given service port

    :param service_port: Service port
    :type service_port: int
    :return: Service Name
    :rtype: str
    :raises RuntimeError: is duplicate or no services are found matching service port number provided
    """
    service_names = [key for (key, value) in get_registry_data().items() if int(value.get('port')) == int(service_port)]

    if not service_names:
        raise RuntimeError("No service found for service port '{0}': {1}"
                           .format(service_port, service_names))

    if len(service_names) > 1:
        raise RuntimeError("Duplicate services found for same service port '{0}': {1}"
                           .format(service_port, service_names))

    return service_names[0]
