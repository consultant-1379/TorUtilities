# ********************************************************************
# Name    : ENM Deployment
# Summary : Functional module for interacting with ENM deployment.
#           Allows the user to perform operations such as PIB commands,
#           read and update, can also retrieve deployment information,
#           such as VM information, global properties or the SSH key
#           for connecting in cloud or physical.
# ********************************************************************

import ast
import json
import os.path
import re

from enmutils.lib import log, shell
from enmutils.lib.cache import (get_emp, get_enm_cloud_native_namespace,
                                is_emp, is_enm_on_cloud_native)
from enmutils.lib.enm_user_2 import get_admin_user
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.services import deployment_info_helper_methods

LITP_HOST_CMD = ("/usr/bin/python /usr/bin/litp show -p /deployments/enm/clusters/{cluster}_cluster/services/"
                 "{service_name}/applications/vm-service_{service_name} --json")

ENM_LIST_LIBVIRT_INSTANCES = "ls -1 /var/lib/libvirt/instances | grep -v 'lost+found'"
ENM_INSTANCE_METADATA_FILE = "/var/lib/libvirt/instances/{service_instance}/meta-data"
ENM_LIST_INSTANCE_IP_ADDRESS = ("grep -A 2 'iface eth0' /var/lib/libvirt/instances/{service_instance}/meta-data | "
                                "grep address | awk '{{ print $2 }}'")
ENM_PROPERTIES_FILE = os.path.join("/ericsson", "tor", "data", "global.properties")


def get_service_ip(name, interface='internal', cluster='svc'):
    """
    Gets the ip addr of the service name given. It fetches from litp model
    :param name: name of the service
    :type name: str
    :param interface: IP address interface, public or private. Valid param options are: internal and services
    :type interface: str
    :param cluster: cluster name to use
    :type cluster: str
    :return: ip address
    :rtype: str
    :raises RuntimeError: when service ip address is not present in litp
    """
    litp_get_service = ("/usr/bin/python /usr/bin/litp show -p /deployments/enm/clusters/{cluster}_cluster/services/"
                        "{service_name}/applications/vm-service_{service_name}/vm_network_interfaces/{interface} "
                        "--json")
    response = shell.run_cmd_on_ms(litp_get_service.format(service_name=name, interface=interface, cluster=cluster))
    if response.rc != 0:
        log.logger.debug('Cannot get the ip of the vm for service: {0}'.format(name))
        raise RuntimeError('Cannot get the service IP address for service: {0}'.format(name))
    return json.loads(response.stdout)['properties']['ipaddresses']


def get_service_hosts(name, cluster='svc'):
    """
    Gets the ip addr of the service name given. It fetches from litp model
    :param name: name of the service
    :type name: str
    :type cluster: str
    :param cluster: The name of the cluster to query for litp
    :return: hostname
    :rtype: str
    :raises EnvironError: when service hosts is not present in litp
    """
    response = shell.run_cmd_on_ms(
        LITP_HOST_CMD.format(service_name=name, cluster=cluster))
    if response.rc != 0:
        raise EnvironError('Cannot get the service hosts service: {0}'.format(name))
    hostname_map_str = json.loads(response.stdout)['properties']['node_hostname_map']
    return ast.literal_eval(hostname_map_str).values()


def check_if_cluster_exists(cluster_type):
    """
    Checks the litp model to see there is a particular type of Cluster (e.g. evt etc) is defined for the deployment
    :param cluster_type: type of ENM cluster (e.g. evt)
    :type cluster_type: str
    :return: True or False, indicating whether cluster exists or not
    :rtype: bool
    :raises RuntimeError: when unable to check if cluster exits using litp
    """

    cluster = "{0}_cluster".format(cluster_type)

    command = "/usr/bin/python /usr/bin/litp show -p /deployments/enm/clusters/ | egrep {cluster} | cut -d'/' -f2"
    response = shell.run_cmd_on_ms(command.format(cluster=cluster))
    if response.rc != 0:
        raise RuntimeError('Cannot check with litp if cluster {0} exists'.format(cluster_type))
    command_response_lines = response.stdout.split("\n")

    return bool(cluster in command_response_lines)


def check_if_ebs_tag_exists(ebs_tag_name):
    """
    Checks the ebs tag (value_pack_ebs_ln, value_pack_ebs_m ebs tags values (true, false)) existed or not in
    CENM deployment.
    :param ebs_tag_name: Name of ebs tag (value_pack_ebs_ln, value_pack_ebs_m)
    :type ebs_tag_name: str
    :return: True or False, indicating whether ebs_tag (value_pack_ebs_ln or value_pack_ebs_m) exists or not
    :rtype: bool

    :raises EnvironError: When failed to get ebs tag values.
    """
    cmd = "/usr/local/bin/kubectl describe configmap value-pack-status -n {0} |grep -i {1}"
    cmd_response = shell.run_local_cmd(shell.Command(cmd.format(get_enm_cloud_native_namespace(), ebs_tag_name)))
    if cmd_response.rc != 0:
        raise EnvironError("Failed to get {0} Tag value due to {1}".format(ebs_tag_name, cmd_response.stdout))

    ebs_tag_exist = bool("true" in cmd_response.stdout.split("=")[1])
    log.logger.debug("{0} Tag is {1} in cENM deployment".format(ebs_tag_name,
                                                                "enabled" if ebs_tag_exist else "disabled"))
    return ebs_tag_exist


def get_service_ip_addresses_via_consul(service):
    """
    Returns the ip addresses of a given ENM service using consul command

    :raises EnvironError: When failed to correctly execute consul members command
    :param service: type of ENM Cloud service
    :type service: str
    :return: Service ip addresses for a given ENM Cloud service
    :rtype: list
    """
    cmd = shell.Command("sudo consul catalog nodes -service={0}".format(service))
    response = shell.run_cmd_on_vm(cmd, get_emp())
    if "No nodes match the given query" in response.stdout:
        raise EnvironError("Location of service {0} not found".format(service))
    if response.rc != 0 or not response.stdout:
        raise EnvironError('Failed to correctly execute consul members command, response: {0}'.format(response.stdout))
    service_ips = [line.split()[2] for line in response.stdout.split('\n') if line and "Address" not in line]
    log.logger.debug("{0} service IP's fetched : {1}".format(service, service_ips))
    return service_ips


def get_cloud_members_list_dict():
    """
    Returns a dict containing key,values pairs of service and their respective ip address

    :raises EnvironError: When failed to correctly execute consul members command

    :rtype: dict
    :return: Dictionary containing key,values pairs of service and their respective ip address
    """
    cmd = shell.Command("sudo consul members list")
    response = shell.run_cmd_on_vm(cmd, get_emp())
    if response.rc != 0 or not response.stdout:
        raise EnvironError('Failed to correctly execute consul members command, response: {0}'.format(response.stdout))
    all_ips = response.stdout.split('\n')
    return {line.split(' ')[0]: re.compile(r'\s+').split(line)[1].split(':')[0] for line in all_ips if line}


def get_cloud_members_ip_address(service):
    """
    Returns the ip addresses of a given ENM Cloud consul members service via partial pattern matching
    :param service: type of ENM Cloud service, can be partially matched e.g. (-amos-)
    :type service: str
    :rtype: list
    :return: Service ip addresses for a given ENM Cloud service e.g. (-cmserv-)
    """
    log.logger.debug("Getting IP address(es) for service: {0}".format(service))
    if service == 'visinamingnb':
        data = get_values_from_global_properties("{0}_service_IPs".format(service))

    else:
        consul_members = get_cloud_members_list_dict()
        data = [v for k, v in consul_members.iteritems() if service in k.lower()]

    log.logger.debug("IP address(es): {0}".format(data))
    return data


def get_values_from_global_properties(key, ipv6=False):
    """
    Given the key, retrieve the values from the global.properties file in ENM

    :param key: Key to be searched for
    :type key: str
    :param ipv6: Boolean to indicate if IPv6 version of the key is required
    :type ipv6: bool
    :return: Values for given key
    :rtype: list
    :raises EnvironError: When the key is not found in the global.properties file
    """

    log.logger.debug('Attempting to obtain the values for key: "{key}" from the file: "{properties_file_location}" in '
                     'ENM'.format(key=key, properties_file_location=ENM_PROPERTIES_FILE))

    command = ("egrep {key} {properties_file_location} | cut -f2 -d="
               .format(key=key, properties_file_location=ENM_PROPERTIES_FILE))

    response = shell.run_cmd_on_emp_or_ms(cmd=command, **{'timeout': 60})

    values = response.stdout.strip().split(',')

    if response.rc or values == ['']:
        raise EnvironError('Unable to obtain {KeyValues}: "{key}" from file: "{properties_file_location}" in ENM'
                           .format(KeyValues=("values from key" if values == [''] else "key"),
                                   key=key, properties_file_location=ENM_PROPERTIES_FILE))

    if "_IPs" in key and not any(item for item in values) and not ipv6:
        ipv6_key = key.replace("_IPs", "_IPv6_IPs")
        values = get_values_from_global_properties(ipv6_key, ipv6=True)

    log.logger.debug('Successfully obtained the values: "{values}" for key: "{key}" from the file: '
                     '"{properties_file_location}" in ENM'
                     .format(values=values, key=key, properties_file_location=ENM_PROPERTIES_FILE))

    return values


def get_list_of_scripting_service_ips():
    """
    Get the list of SCP services from the global properties list

    :return: List of scripting cluster ips
    :rtype: list
    """
    log.logger.debug("Fetching list of scripting service IP's")
    if is_enm_on_cloud_native():
        return [deployment_info_helper_methods.get_cloud_native_service_vip("general-scripting")]
    else:
        return get_values_from_global_properties("scripting_service_IPs")


def get_list_of_scripting_vms_host_names():
    """
    Get the list of host names of Scripting vms from /etc/hosts

    :return: List of scripting vms
    :rtype: list
    """
    command = r'egrep "scripting\-" /etc/hosts | cut -f2'
    response = shell.run_cmd_on_emp_or_ms(cmd=command, **{'timeout': 60})
    if response.rc == 0:
        values = response.stdout.strip().split('\n')
        log.logger.debug("List of Scripting VM host names are: {0}".format(values))
    else:
        values = []
        log.logger.debug("Unable to obtain list of scripting vms from /etc/hosts in ENM")
    return values


def get_pod_hostnames_in_cloud_native(service_name):
    """
    Fetch Pod hostnames (from Kubernetes cluster) for given service name

    :param service_name: ENM Service identifier, e.g. pmserv, fmserv etc
    :type service_name: str

    :return: List of hostnames in K8 Cluster
    :rtype: list

    :raises EnvironError: if problem encountered executing kubectl command
    """
    log.logger.debug("Fetching service hostnames from Kubernetes client for service '{0}'".format(service_name))
    cmd = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config get pods -n {enm_namespace} 2>/dev/null".format(
        enm_namespace=get_enm_cloud_native_namespace())
    response = shell.run_local_cmd(shell.Command(cmd))
    if response.rc or not response.stdout:
        raise EnvironError("Problem encountered running command: {0}".format(cmd))

    service_hostnames = []
    for line in response.stdout.split('\n'):
        if line.startswith(service_name):
            service_hostnames.append(line.split()[0])

    log.logger.debug("Service hostnames: {0}".format(service_hostnames))
    return service_hostnames


def get_enm_service_locations(enm_service, cluster='svc'):
    """
    Get ENM service locations (i.e. hostnames in cloud native otherwise IP addresses)

    :param enm_service: ENM service
    :type enm_service: str
    :param cluster: The name of the cluster to query for litp
    :type cluster: str
    :return: List of locations (strings)
    :rtype: list

    :raises EnvironError: if locations are not set in ENM
    """
    log.logger.debug("Get ENM service locations for {0}".format(enm_service))
    service_locations = []

    try:
        if is_enm_on_cloud_native():
            log.logger.debug("ENM on Cloud Native detected")
            service_locations = get_pod_hostnames_in_cloud_native(enm_service)

        elif is_emp():
            log.logger.debug("ENM on Cloud OpenStack detected")
            service_locations = get_service_ip_addresses_via_consul(enm_service)

        else:
            log.logger.debug("ENM on Physical detected")
            service_locations = get_service_hosts("{0}".format(enm_service), cluster)
    except Exception as e:
        log.logger.debug("Exception encountered while getting service location on enm: '{0}".format(e))

    if not service_locations:
        raise EnvironError("Location could not be determined for service: '{0}'".format(enm_service))

    log.logger.debug("ENM service locations for {0}: {1}".format(enm_service, service_locations))
    return service_locations


def update_pib_parameter_on_enm(enm_service_name, pib_parameter_name, pib_parameter_value,
                                enm_service_locations=None, service_identifier=None, scope=None):
    """
    Update PIB parameter on ENM by trying each service instance in turn until a successful response is obtained

    :param enm_service_name: Name of ENM service
    :type enm_service_name: str
    :param pib_parameter_name: Name of PIB Parameter
    :type pib_parameter_name: str
    :param pib_parameter_value: Value of PIB Paramater
    :type pib_parameter_value: str
    :param enm_service_locations: List of ENM service locations (hostnames or IP addresses)
    :type enm_service_locations: list
    :param service_identifier: Service Identifier
    :type service_identifier: str
    :param scope: Scope
    :type scope: str

    :return: Boolean to indicate that value was set
    :rtype: bool

    :raises EnmApplicationError: if could not set PIB value on ENM
    """
    log.logger.debug("Update PIB parameter '{0}' to '{1}'".format(pib_parameter_name, pib_parameter_value))

    enm_service_locations = (enm_service_locations if enm_service_locations
                             else get_enm_service_locations(enm_service_name))

    for enm_service_location in enm_service_locations:
        if set_pib_value_on_enm_service(enm_service_location,
                                        pib_parameter_name, pib_parameter_value,
                                        service_identifier=service_identifier):
            log.logger.debug("PIB parameter successfully updated on {0}".format(enm_service_location))
            return True

    raise EnmApplicationError("Unable to update PIB parameter {0} - see profile log for details"
                              .format(pib_parameter_name))


def set_pib_value_on_enm_service(enm_service_location, pib_parameter_name, pib_parameter_value,
                                 service_identifier=None):
    """
    Set PIB parameter value

    :param enm_service_location: Location of ENM service (hostname or IP address)
    :type enm_service_location: str
    :param pib_parameter_name: Name of PIB Parameter
    :type pib_parameter_name: str
    :param pib_parameter_value: Value of PIB Parameter
    :type pib_parameter_value: str
    :param service_identifier: The identity of the service. Required when setting scope SERVICE or JVM_AND_SERVICE
    :type service_identifier: str

    :return: Boolean to indicate if command was successful
    :rtype: bool
    """
    service_id = "" if not service_identifier else "--service_identifier {0}".format(service_identifier)
    log.logger.debug("Setting PIB parameter '{0}' to '{1}' on '{2}'"
                     .format(pib_parameter_name, pib_parameter_value, enm_service_location))
    pib_command_parameters = ("admin parameter modify --name {pib_parameter_name} --value {pib_parameter_value} "
                              "{service_identifier} "
                              "--app_server_identifier {hostname}:8080".format(pib_parameter_name=pib_parameter_name,
                                                                               pib_parameter_value=pib_parameter_value,
                                                                               service_identifier=service_id,
                                                                               hostname=enm_service_location))
    log.logger.debug("executing the pib command to set the pib value: {0}".format(pib_command_parameters))
    user = get_admin_user()

    try:
        user.enm_execute(pib_command_parameters)
        return True
    except Exception as e:
        log.logger.error("Unable to set PIB parameter: {0}".format(str(e)))


def get_pib_value_on_enm(enm_service_name, pib_parameter_name, service_identifier=None, enm_service_locations=None):
    """
    Get value of PIB parameter

    :param pib_parameter_name: Name of PIB Parameter
    :type pib_parameter_name: str
    :param enm_service_name: Name of enm service to get pib parameter value from.
    :type enm_service_name: str
    :param enm_service_locations: Locations of enm service (e.g. hostnames or IP's)
    :type enm_service_locations: list
    :return: Value of PIB parameter
    :param service_identifier: Identify a service
    :type service_identifier: str
    :rtype: str
    :raises EnmApplicationError: If value could not be read
    """

    log.logger.debug('Getting value of PIB parameter: {0}'.format(pib_parameter_name))
    enm_service_locations = (enm_service_locations if enm_service_locations
                             else get_enm_service_locations(enm_service_name))
    for enm_service_location in enm_service_locations:
        pib_parameter_value = get_pib_value_on_enm_service(enm_service_location, pib_parameter_name,
                                                           service_identifier)
        if pib_parameter_value:
            log.logger.debug('Successfully read {0} on {1} : Value = {2}'
                             .format(pib_parameter_name, enm_service_location, pib_parameter_value))
            return pib_parameter_value

    raise EnmApplicationError("Unable to get PIB parameter {0}. See profile log for details."
                              .format(pib_parameter_name))


def get_pib_value_on_enm_service(enm_service_location, pib_parameter_name, service_identifier=None):
    """
    Read pib value from an enm service.
    :param pib_parameter_name: Name of pib parameter
    :type pib_parameter_name: str
    :param enm_service_location: Hostname or Ip address of enm service.
    :type enm_service_location: str
    :param service_identifier: Identify a service
    :type service_identifier: str
    :return: pib value
    :rtype: str
    """

    service_identifier = ' --service_identifier {0}'.format(service_identifier) if service_identifier else ''
    pib_command_parameters = ("admin parameter view --name {pib_parameter_name}"
                              "{service_identifier} --app_server_identifier "
                              "{enm_service_location}:8080".format(pib_parameter_name=pib_parameter_name,
                                                                   service_identifier=service_identifier,
                                                                   enm_service_location=enm_service_location))
    log.logger.debug("Getting value of PIB parameter '{0}' on {1}".format(pib_parameter_name, enm_service_location))
    log.logger.debug("executing the pib command to get the pib value: {0}".format(pib_command_parameters))
    user = get_admin_user()
    try:
        response = user.enm_execute(pib_command_parameters)
        _, value = str(response.get_output()[1].strip('u')).split(': ')
        log.logger.debug('successfully fetched the pib value for {0} is {1}'.format(_, value))
        return value
    except Exception as e:
        log.logger.error("Unable to get PIB parameter: {0}".format(str(e)))


def run_pib_command_on_enm_service(enm_service_name, enm_service_location, pib_command_parameters):
    """
    Set PIB parameter value on VM by command

    :param enm_service_location: Location of ENM service (hostname or IP address)
    :type enm_service_location: str
    :param enm_service_name: Name of ENM service (e.g. pmserv, fmserv etc)
    :type enm_service_name: str
    :param pib_command_parameters: Parameters for PIB Command
    :type pib_command_parameters: str
    :return: Response output
    :rtype: str
    :raises Exception: if command cannot be run
    :raises e: if method throws error
    """
    log.logger.debug("Running PIB command on {0}".format(enm_service_location))
    pib_script_vm = "{0} /opt/ericsson/PlatformIntegrationBridge/etc/config.py"
    pib_script_lms = "python /ericsson/pib-scripts/etc/config.py"

    try:
        if is_enm_on_cloud_native():
            log.logger.debug("ENM on Cloud Native detected - running command on Pod")
            command_response = shell.run_cmd_on_cloud_native_pod(enm_service_name, enm_service_location, "python -V")
            log.logger.debug("Checking Python Version : {0} {1}".format(command_response.stdout, command_response.rc))
            cmd = pib_script_vm.format("python3" if command_response.rc else "python")
            command_response = shell.run_cmd_on_cloud_native_pod(
                enm_service_name, enm_service_location, "{0} {1}".format(cmd, pib_command_parameters))

        elif is_emp():
            log.logger.debug("ENM on Cloud OpenStack detected - running command on EMP")
            command_response = shell.run_cmd_on_vm(
                shell.Command("sudo {0} {1}".format(pib_script_lms, pib_command_parameters)), get_emp())
        else:
            log.logger.debug("ENM on Physical detected - running command on LMS")
            command_response = shell.run_cmd_on_ms(
                shell.Command("sudo {0} {1}".format(pib_script_lms, pib_command_parameters)))

        if not command_response.rc:
            log.logger.debug("Successfully ran PIB command: {0}".format(command_response.stdout))
            return command_response.stdout

        raise Exception("Command execution resulted in non-zero result code: {0}".format(command_response.stdout))

    except Exception as e:
        raise e


def get_pib_value_from_enm(service_ip, pib_parameter):
    """
    Gets the value of PIB Parameter set on ENM

    :param service_ip: the application service ip that will be queried
    :type service_ip: str
    :param pib_parameter: PIB Parameter
    :type pib_parameter: str

    :return: The output from issuing the command on ENM
    :rtype: str

    :raises EnmApplicationError: if there is a problem issuing command on ENM
    """
    log.logger.debug("Issuing command on ENM (via Application Service IP: '{0}') in order to read value of PIB "
                     "Parameter: {1}".format(service_ip, pib_parameter))

    command = ("admin parameter view --name {pib_parameter_name}"
               " --app_server_identifier "
               "{enm_service_location}:8080".format(pib_parameter_name=pib_parameter, enm_service_location=service_ip))
    user = get_admin_user()
    try:
        response = user.enm_execute(command)
    except Exception as e:
        raise EnmApplicationError("Problem encountered while executing command on Application Service IP '{0}': {1}"
                                  .format(service_ip, str(e)))

    if 'error' in response.get_output()[1].lower():
        raise EnmApplicationError("Error retrieving the value of PIB parameter '{0}' from Application Service IP: {1}"
                                  .format(pib_parameter, service_ip))

    _, command_output = str(response.get_output()[1].strip('u')).split(': ')
    log.logger.debug("Value of PIB Parameter '{0}': {1}".format(pib_parameter, command_output))
    return command_output


def fetch_pib_parameter_value(application_service, pib_parameter):
    """
    Fetch value of PIB parameter

    :param application_service: Application Service
    :type application_service: str
    :param pib_parameter: PIB Parameter
    :type pib_parameter: str
    :return: Value of PIB Parameter
    :rtype: str

    :raises EnvironError: if unable to get Application Service IP from Global Properties file in ENM
    """
    log.logger.debug("Fetching value of PIB Parameter: {0}".format(pib_parameter))

    app_service_ip_list = get_values_from_global_properties(application_service)
    if not app_service_ip_list:
        raise EnvironError("Unable to determine IP of application service from global properties file on ENM: {0}"
                           .format(application_service))

    pib_value = None
    for count, ip_address in enumerate(app_service_ip_list):
        if not pib_value:
            try:
                pib_value = get_pib_value_from_enm(service_ip=ip_address, pib_parameter=pib_parameter)
            except EnmApplicationError as e:
                log.logger.debug("Unable to retrieve value of PIB parameter from ENM: {0}".format(str(e)))

            if (count + 1) < len(app_service_ip_list):
                log.logger.debug("Retrying with the next available application service IP")

    log.logger.debug("Fetching value of PIB Parameter complete")
    return pib_value.strip() if pib_value else None


def get_fdn_list_from_enm(enm_user, mo_type, enm_scope="*"):
    """
    Get the list FDN's from ENM for a particular Managed Object type

    :param enm_user: User that will execute the ENM commands
    :type enm_user: enmutils.lib.enm_user_2.User
    :param mo_type: MO Type
    :type mo_type: str
    :param enm_scope: Scope of the ENM query (e.g. Network Element name), default: whole network
    :type enm_scope: str
    :return: List of MO FDN's found on ENM
    :rtype: list
    :raises EnmApplicationError: if command execution on ENM was unsuccessful or output was unexpected
    """

    log.logger.debug("Fetching list of MO's on ENM of type {0}".format(mo_type))
    cmd = "cmedit get {enm_scope} {mo_type}".format(enm_scope=enm_scope, mo_type=mo_type)
    try:
        response = enm_user.enm_execute(cmd)
        enm_output = response.get_output()
    except Exception as e:
        raise EnmApplicationError("ENM command execution unsuccessful: '{0}' - {1}".format(cmd, str(e)))

    fdn_list = []
    for line in enm_output:
        match = re.search("FDN : (.*)", line)
        if match:
            fdn_list.append(match.group(1))

    log.logger.debug("Number of {0} MO's found: {1}".format(mo_type, len(fdn_list)))

    return fdn_list


def get_mo_attributes_from_enm(enm_user, mo_type, mo_attributes, scope="*"):
    """
    Get the MO attributes for network elements in ENM

    :type enm_user: enmutils.lib.enm_user_2.User
    :param enm_user: User to run ENM CLI commands
    :type mo_type: str
    :param mo_type: mo type of node
    :type mo_attributes: list
    :param mo_attributes: list of MO attributes of node
    :type scope: list
    :param scope: to get particular node MO attributes or all nodes MO attributes. scope default value *

    :rtype: dict
    :return: The MO attribute value of all network elements in ENM
    :raises EnmApplicationError: if there is error in response from ENM

    """
    mo_attributes = ",".join(mo_attributes)
    scope = ";".join(scope) if scope != "*" else scope

    command = "cmedit get {scope} {mo_type}.({mo_attributes}) -t".format(scope=scope, mo_type=mo_type,
                                                                         mo_attributes=mo_attributes)
    log.logger.debug("Getting attribute ('{mo_attributes}') values for MO '{mo_type}' on ENM".format(
        mo_attributes=mo_attributes, mo_type=mo_type))
    response = enm_user.enm_execute(command)
    enm_output = response.get_output()
    if any(re.search(r'(error|^[0]\sinstance)', line, re.I) for line in enm_output):
        raise EnmApplicationError("Error occurred while getting NE {mo_type} status from ENM - {output}"
                                  .format(mo_type=mo_type, output=enm_output))
    mo_attribute_values_per_fdn = {}
    for line in enm_output[2:-2]:
        mo_attributes_values = line.split("\t")
        mo_attribute_values_per_fdn[mo_attributes_values[0]] = dict(zip(mo_attributes.split(','),
                                                                        mo_attributes_values[2:]))

    log.logger.debug("Finished getting {mo_type}.({mo_attributes}) values from ENM".format(mo_type=mo_type,
                                                                                           mo_attributes=mo_attributes))

    return mo_attribute_values_per_fdn


def get_pm_function_enabled_nodes(nodes, user):
    """
    Check if node Pm Function enabled or not

    :type nodes: list
    :param nodes: List of `enm_node.Node` to get PM Function enabled or not
    :type user: `enm_user_2.User`
    :param user: Instance of `enm_user_2.User` to execute the PM Function check

    :rtype: tuple
    :return: Tuple of two lists, containing PM Function Enabled and Disabled nodes
    """
    if nodes:
        enm_network_element_pm_status = get_mo_attributes_from_enm(enm_user=user, mo_type="PmFunction",
                                                                   mo_attributes=["pmEnabled"])
        pm_disabled_nodes = [node for node in nodes if enm_network_element_pm_status.get(node.node_id) and
                             enm_network_element_pm_status[node.node_id].get("pmEnabled") == "false"]
        pm_enabled_nodes = [node for node in nodes if node not in pm_disabled_nodes]
        log.logger.debug("Returning {0} PM Function enabled nodes, and {1}"
                         " disabled nodes.".format(len(pm_enabled_nodes), len(pm_disabled_nodes)))
        return pm_enabled_nodes, pm_disabled_nodes
    log.logger.debug("No nodes supplied so no PM Function will be checked")
    return [], []


def get_list_of_db_vms_host_names(db_vm_host_name=None):
    """
    Get the list of host names of db vms from /etc/hosts

    :return: List of db vms
    :rtype: list
    """
    command = "egrep {0} /etc/hosts|cut -f1 -d$'\\t'".format(db_vm_host_name if db_vm_host_name else 'db-')
    response = shell.run_cmd_on_emp_or_ms(cmd=command, **{'timeout': 60})
    if response.rc == 0:
        values = response.stdout.strip().split('\n')
        log.logger.debug("List of db vm host names are: {0}".format(values))
    else:
        values = []
        log.logger.debug("Unable to obtain list of db vms from /etc/hosts in ENM")
    return values
