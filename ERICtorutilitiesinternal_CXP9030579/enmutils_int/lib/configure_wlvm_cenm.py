# ********************************************************************
# Name    : Configure WLVM Operations for cENM
# Summary : Functional module used by the workload configure tool
#           for cENM (Cloud Native ENM) deployment
# ********************************************************************

import commands
import inspect
import json
import socket

from enmutils.lib import log
from enmutils.lib.filesystem import create_dir, does_file_exist
from enmutils_int.lib.configure_wlvm_common import (update_bashrc_file_with_env_variable, create_ssh_keys,
                                                    SSH_PRIVATE_KEY, update_ssh_authorized_keys, execute_command)
from enmutils_int.lib.dit import (get_document_content_from_dit, get_sed_id, get_parameter_value_from_sed_document,
                                  get_deployment_namespace)

KUBECTL_DEFAULT_PATH = "/usr/local/bin/kubectl"
KUBE_CONFIG_DIR = "/root/.kube"
KUBE_CONFIG_FILE = "{0}/config".format(KUBE_CONFIG_DIR)
DDC_SERVER_TXT_FILE = "/tmp/ddc_server.txt"
DDC_CLUSTER_SECRET = "remote-servers"

KUBERNETES_URL = ("https://arm.sero.gic.ericsson.se/artifactory/"
                  "proj-iopensrc-dev-generic-local/com/storage.googleapis/kubernetes-release/release")
KUBECTL_DOWNLOAD_URL = "bin/linux/amd64/kubectl"
PROXY = "atproxy1.athtem.eei.ericsson.se:3128"


def create_kube_config_file(documents_info_dict, deployment_name):
    """
    Create Kube config file

    :param documents_info_dict: Documents Info Dict
    :type documents_info_dict: dict
    :param deployment_name: Deployment Name
    :type deployment_name: str
    :return: Boolean to indicate if file was created or not
    :rtype: bool
    """
    log.logger.debug("Attempting to create kube config file: {0}".format(KUBE_CONFIG_FILE))
    create_dir(KUBE_CONFIG_DIR, log_output=False)
    kube_config_doc_id = documents_info_dict.get("cloud_native_enm_kube_config")
    if kube_config_doc_id:
        content = get_document_content_from_dit(kube_config_doc_id)
        if content:
            try:
                with open(KUBE_CONFIG_FILE, "w") as f:
                    f.write(json.dumps(content))
                log.logger.debug("Content written to file: {0}".format(KUBE_CONFIG_FILE))
                return True
            except Exception as e:
                log.logger.debug("Error occurred while writing the content to file: {0}".format(e))
        else:
            log.logger.warn("The document 'cloud_native_enm_kube_config' from DIT contains no content")
    else:
        log.logger.warn("Unable to find document 'cloud_native_enm_kube_config' on DIT for deployment "
                        "{0}".format(deployment_name))

    log.logger.warn("Unable to create kube config file: {0}".format(KUBE_CONFIG_FILE))


def download_kubectl_client(is_proxy_required, version=None):
    """
    Download the kubectl client from proj-iopensrc-dev-generic-local repo

    :param is_proxy_required: proxy is used for download the kubectl, when it was True. Otherwise,
    it will not use proxy.
    :type is_proxy_required: bool
    :param version: version of kubectl
    :type version: str

    :return: Boolean to indicate if download was successful
    :rtype: bool
    """
    rc = 0
    log.logger.debug("Fetching the kubectl client")
    if not version:
        version = compare_kubectl_client_and_server_version("", "Updates local kubectl client version (cENM)")

    if not rc and version:
        log.logger.debug("kubectl version to be downloaded : {0}".format(version))
        curl_command = ("curl -s -o {0} -x {1} '{2}/{3}/{4}'".format(KUBECTL_DEFAULT_PATH, PROXY,
                                                                     KUBERNETES_URL, version,
                                                                     KUBECTL_DOWNLOAD_URL) if is_proxy_required
                        else "curl -s -o {0} '{1}/{2}/{3}'" .format(KUBECTL_DEFAULT_PATH, KUBERNETES_URL,
                                                                    version, KUBECTL_DOWNLOAD_URL))
        log.logger.debug("Downloading the executable: {0}".format(curl_command))
        rc, _ = commands.getstatusoutput(curl_command)
        if not rc or rc == 5888:
            log.logger.debug("Client downloaded")
            return True
        else:
            log.logger.warn("Problem encountered while downloading the kubectl client with version {0}".format(version))
            return False
    else:
        return True


def install_kubectl_client(is_proxy_required, version=None):
    """
    Download the kubectl client from the Internet with proxy, if is_proxy_required value is True,
    Otherwise downloads the file without proxy and Install kubectl client in default location on workload vm.

    :param is_proxy_required: proxy is used to install the kubectl client, when it was True. Otherwise,
    it will not use proxy.
    :type is_proxy_required: bool
    :param version: version of kubectl
    :type version: str
    :return: Boolean to indicate success of install
    :rtype: bool
    """

    log.logger.debug("Installing kubectl client to default path: {0}".format(KUBECTL_DEFAULT_PATH))
    if download_kubectl_client(is_proxy_required, version):

        command = "chmod +x {0}".format(KUBECTL_DEFAULT_PATH)
        log.logger.debug("Setting execute permissions on executable: '{0}'".format(command))
        rc, _ = commands.getstatusoutput(command)

        if not rc:
            log.logger.debug("Client installed")
            return True

    log.logger.warn("Failed to install kubectl client")


def check_kubectl_connection():
    """
    Check that Kubectl can be used to access the cluster

    :return: Boolean to indicate successful connection
    :rtype: bool
    """

    log.logger.debug("Checking that kubectl client can connect to cluster")
    command = "{0} --kubeconfig {1} cluster-info 2>/dev/null".format(KUBECTL_DEFAULT_PATH, KUBE_CONFIG_FILE)
    log.logger.debug("Executing command: '{0}'".format(command))
    rc, output = commands.getstatusoutput(command)
    if not rc:
        log.logger.debug("Execution return-code: 0 :: Output: {0}".format(output))
        log.logger.debug("Connection successful using kubectl client")
        return True

    log.logger.warn("Failed to connect to cluster with kubectl client: {0}".format(output))


def set_cenm_variables(deployment_name, slogan):
    """
    Set Bashrc variables on Workload VM for Cloud Native ENM

    :param deployment_name: Deployment Name
    :type deployment_name: str
    :param slogan: Configuration operation slogan
    :type slogan: str

    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    log.logger.info("Deployment: {0} - {1}".format(deployment_name, slogan))
    sed_id = get_sed_id(deployment_name)
    if sed_id:
        httpd_fqdn = get_parameter_value_from_sed_document(sed_id, "httpd_fqdn")
        if httpd_fqdn and update_bashrc_file_with_env_variable("ENM_URL", httpd_fqdn):
            log.logger.info("Bashrc updated")
            return True


def setup_cluster_connection(deployment_name, dit_document_info_dict, slogan, is_proxy_required):
    """
    Setup connection towards Kubernetes (ENM) cluster
    1. Create Kube config file on workload vm.
    2. Install kubectl client in default location on workload vm with proxy (if is_proxy_required is True)
    or without proxy, if is_proxy_required is False.
    3. Check that Kubectl can be used to access the cluster

    :param deployment_name: Deployment Name
    :type deployment_name: str
    :param dit_document_info_dict: Dictionary of DIT document info
    :type dit_document_info_dict: dict
    :param slogan: Configuration operation slogan
    :type slogan: str
    :param is_proxy_required: proxy is used for set up the kubectl, when it was True. Otherwise, it will not use proxy.
    :type is_proxy_required: bool

    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    log.logger.info("Deployment: {0}".format(deployment_name))
    log.logger.info("Option: {0} - {1}".format(inspect.stack()[0][3], slogan))

    if (create_kube_config_file(dit_document_info_dict, deployment_name) and install_kubectl_client(is_proxy_required) and
            check_kubectl_connection()):
        log.logger.info("Client installed and connection to cluster was successful")
        return True


def create_ddc_secret_on_cluster(deployment_name, slogan, dit_document_info_dict):
    """
    Create 'remote-servers' secret in kubernetes cluster to allow DDC to collect from Workload VM

    :param deployment_name: Deployment Name
    :type deployment_name: str
    :param dit_document_info_dict: Dictionary of DIT document info
    :type dit_document_info_dict: dict
    :param slogan: Configuration operation slogan
    :type slogan: str
    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    log.logger.info("Deployment: {0} - Option: {1}".format(deployment_name, slogan))
    log.logger.info("Creating '{0}' secret on the ENM cluster to allow DDC data on WLVM to be uploaded to DDP"
                    .format(DDC_CLUSTER_SECRET))

    deployment_namespace = get_deployment_namespace(deployment_name, dit_document_info_dict)

    if (deployment_namespace and create_server_txt_file() and create_ssh_keys() and
            update_ssh_authorized_keys() and add_secret_to_cluster(deployment_namespace)):
        log.logger.info("The secret was successfully created")
        return True

    log.logger.info("The secret was not created")


def create_server_txt_file():
    """
    Create server.txt file to be used to generate the 'remote-servers' secret
    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    log.logger.debug("Creating the server.txt file")

    command = "echo '{0}.athtem.eei.ericsson.se=WORKLOAD\n' > {1}".format(socket.gethostname(), DDC_SERVER_TXT_FILE)
    return execute_command(command)["result"]


def check_kubectl_can_be_used():
    """
    Check if kubectl can be used

    :return: Boolean to indicate that client can be used or not
    :rtype: bool
    """
    log.logger.debug("Checking if kubectl client can be used")
    if does_file_exist(KUBECTL_DEFAULT_PATH) and does_file_exist(KUBE_CONFIG_FILE) and check_kubectl_connection():
        return True

    log.logger.info("The kubectl client cannot connect to the ENM cluster - check if it is installed correctly")


def add_secret_to_cluster(deployment_namespace):
    """
    Adding secret to cluster

    :param deployment_namespace: Deployment Namespace
    :type deployment_namespace: str
    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    if not check_kubectl_can_be_used():
        return False

    if check_if_secret_exists(deployment_namespace) and not delete_secret_from_cluster(deployment_namespace):
        return False

    if create_secret_on_cluster(deployment_namespace) and verify_workload_entry_added_to_secret(deployment_namespace):
        return True


def check_if_secret_exists(deployment_namespace):
    """
    Check if secret exists

    :param deployment_namespace: Deployment Namespace
    :type deployment_namespace: str
    :return: Boolean to indicate if secret exists or not
    :rtype: bool
    """
    log.logger.debug("Check if ddc secret ({0}) exist".format(DDC_CLUSTER_SECRET))
    command = ("{0} --kubeconfig {1} get secret {2} -n {3} 2>/dev/null"
               .format(KUBECTL_DEFAULT_PATH, KUBE_CONFIG_FILE, DDC_CLUSTER_SECRET, deployment_namespace))
    if execute_command(command)["result"]:
        log.logger.debug("The ddc secret exists on cluster")
        return True

    log.logger.warn("The {0} secret does not exist for this cluster".format(DDC_CLUSTER_SECRET))


def delete_secret_from_cluster(deployment_namespace):
    """
    Delete secret from cluster

    :param deployment_namespace: Deployment Namespace
    :type deployment_namespace: str
    :return: Boolean to indicate if operation was successful
    :rtype: bool
    """
    log.logger.debug("Delete secret ({0})".format(DDC_CLUSTER_SECRET))
    command = ("{0} --kubeconfig {1} delete secret {2} -n {3} 2>/dev/null"
               .format(KUBECTL_DEFAULT_PATH, KUBE_CONFIG_FILE, DDC_CLUSTER_SECRET, deployment_namespace))
    return execute_command(command)["result"]


def create_secret_on_cluster(deployment_namespace):
    """
    Create secret on Cluster

    :param deployment_namespace: Deployment Namespace
    :type deployment_namespace: str
    :return: Boolean to indicate if operation was successful
    :rtype: bool
    """
    log.logger.debug("Creating secret: {0}".format(DDC_CLUSTER_SECRET))
    command = ("{0} --kubeconfig {1} create secret generic {2} "
               "-n {3} --from-file=server.txt={4} --from-file=ssh-key={5} 2>/dev/null"
               .format(KUBECTL_DEFAULT_PATH, KUBE_CONFIG_FILE, DDC_CLUSTER_SECRET,
                       deployment_namespace, DDC_SERVER_TXT_FILE, SSH_PRIVATE_KEY))
    return execute_command(command)["result"]


def verify_workload_entry_added_to_secret(deployment_namespace):
    """
    Verify that WORKLOAD entry added to secret

    :param deployment_namespace: Deployment Namespace
    :type deployment_namespace: str
    :return: Boolean to indicate is entry exists or not
    :rtype: bool
    """
    log.logger.debug("Verifying that the WORKLOAD entry has been added to the secret")
    command = ("{0} --kubeconfig {1} get secret {2} -n {3} -o yaml 2>/dev/null | egrep server.txt | awk '{{print $2}}' | "
               "base64 --decode | egrep {4}.*WORKLOAD"
               .format(KUBECTL_DEFAULT_PATH, KUBE_CONFIG_FILE, DDC_CLUSTER_SECRET, deployment_namespace,
                       socket.gethostname()))
    log.logger.debug("Executing command: '{0}'".format(command))
    if execute_command(command)["result"]:
        log.logger.debug("The correct WORKLOAD entry was detected within the secret")
        return True

    log.logger.warn("The WORKLOAD entry was not found within the {0} secret".format(DDC_CLUSTER_SECRET))


def compare_kubectl_client_and_server_version(deployment_name, slogan):
    """
    Compares the client and server versions of kubectl
    :param deployment_name: Deployment Name
    :type deployment_name: str
    :param slogan: Configuration operation slogan
    :type slogan: str
    :return: server version if it is different from client version
    :rtype: str
    """
    version_dict = {}
    log.logger.info("Deployment: {0} - Option: {1}".format(deployment_name, slogan))
    response = execute_command("{0} version --short 2>/dev/null".format(KUBECTL_DEFAULT_PATH))
    if response["result"]:
        versions_list = response["output"].split("\n")
        for entry in versions_list:
            host, version = entry.split(':')
            if 'client' in host.strip().lower():
                version_dict['client_version'] = version
            else:
                version_dict['server_version'] = version
        if not version_dict.get('client_version') == version_dict.get('server_version'):
            log.logger.debug("kubectl client and server versions are not the same")
            return version_dict.get('server_version').strip()
        else:
            log.logger.debug("Both server and client versions of kubectl are the same")
