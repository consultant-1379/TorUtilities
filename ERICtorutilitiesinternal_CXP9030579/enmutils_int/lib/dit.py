# ********************************************************************
# Name    : DIT (Deployment Inventory Tool)
# Summary : Functional module used by the workload configure tool
#            to fetch information from DIT
# ********************************************************************

import commands
import json

from enmutils.lib import log

DIT_API_URL = "https://atvdit.athtem.eei.ericsson.se/api"
DEPLOYMENT_TYPE = None
DIT_DOCUMENTS_INFO_DICT = {}


def send_request_to_dit(content_url):
    """
    Sending request to DIT

    :param content_url: URL of DIT content
    :type content_url: str
    :return: output
    :rtype: str
    """

    log.logger.debug("Sending request to DIT using curl")
    curl_command = ("curl -s '{dit_api_base_url}/{content_url}'"
                    .format(dit_api_base_url=DIT_API_URL, content_url=content_url))
    log.logger.debug("Command: {0}".format(curl_command))
    rc, output = commands.getstatusoutput(curl_command)
    if not rc:
        if output:
            return output
        else:
            log.logger.debug("No data returned from DIT")
    else:
        log.logger.debug("Problem encountered while fetching data from DIT: '{0}'".format(output))


def get_documents_info_from_dit(deployment_name):
    """
    Fetch 'documents' info from DIT

    :param deployment_name: Deployment Name
    :type deployment_name: str
    :return: Dictionary of document info
    :rtype: dict
    """
    log.logger.debug("Fetching documents info from DIT related to deployment: [{0}]".format(deployment_name))
    url = (r"deployments/?q=name={deployment_name}&fields=documents".format(deployment_name=deployment_name))
    output = send_request_to_dit(url)
    if output:
        return parse_documents_data(output)


def parse_documents_data(output):
    """
    Parse output from DIT

    :param output: Output from curl request to DIT
    :type output: str
    :return: Dictionary of document info in the form of {schema_name: document_id}
    :rtype: dict
    """
    try:
        documents_data = [item for item in json.loads(output) if item.get("documents")][0]
        documents_list = documents_data.get("documents")
        document_info_dict = {item.get("schema_name"): item.get("document_id") for item in documents_list}
        log.logger.debug("Parsed data: {0}".format(document_info_dict))
        return document_info_dict

    except Exception as e:
        log.logger.debug("Data received from DIT in unexpected format:- Data: '{0}', Error: '{1}'".format(output, e))


def get_document_content_from_dit(document_id):
    """
    Fetch document content from DIT

    :param document_id: Document Id
    :type document_id: str
    :return: Content of document
    :rtype: dict
    """
    log.logger.debug("Fetching document content for document id: {0}".format(document_id))
    url = (r"documents/{document_id}?fields=content".format(document_id=document_id))
    output = send_request_to_dit(url)
    if output:
        return extract_document_content(output)


def extract_document_content(output):
    """
    Extract document content from output

    :param output: Output from curl command
    :type output: str
    :return: Content of document
    :rtype: dict
    """
    try:
        return json.loads(output).get("content")

    except Exception as e:
        log.logger.debug("Data received from DIT in unexpected format:- Data: '{0}', Error: '{1}'".format(output, e))


def determine_deployment_type(documents_info_dict):
    """
    Determine Deployment Type

    :param documents_info_dict: Documents Info Dict
    :type documents_info_dict: dict
    :return: Type of Deployment
    :rtype: str
    """
    cenm_indicator_document = "cENM_site_information"
    deployment_type = "cENM" if documents_info_dict.get(cenm_indicator_document) else "vENM"
    message = "no " if deployment_type == "vENM" else ""
    log.logger.info("Deployment type detected: {0} ({1}'{2}' document found on DIT)"
                    .format(deployment_type, message, cenm_indicator_document))
    return deployment_type


def get_sed_id(deployment_name):
    """
    Fetches SED ID from DIT

    :param deployment_name: Deployment Name
    :type deployment_name: str
    :return: SED ID
    :rtype: str
    """
    log.logger.debug("Fetching SED ID for deployment: {0}".format(deployment_name))
    url = r"deployments/?q=name={0}&fields=enm(sed_id)".format(deployment_name)
    output = send_request_to_dit(url)
    if output:
        sed_id = extract_sed_id_from_sed_document(output)
        log.logger.debug("SED ID: {0}".format(sed_id))
        return sed_id


def extract_sed_id_from_sed_document(output):
    """
    Extract SED Identifier from SED document

    :param output: Output returned by curl request
    :type output: str

    :return: SED Identifier
    :rtype: str
    """
    try:
        return json.loads(output)[0]["enm"]["sed_id"]
    except Exception as e:
        log.logger.debug("Data received from DIT in unexpected format:- Data: '{0}', Error: '{1}'".format(output, e))


def get_parameter_value_from_sed_document(sed_id, sed_parameter):
    """
    Fetches value of parameter from SED document

    :param sed_id: SED ID
    :type sed_id: str
    :param sed_parameter: SED Parameter
    :type sed_parameter: str
    :return: SED Parameter value
    :rtype: str
    """
    log.logger.debug("Fetching value from SED ({0}) for parameter {1}".format(sed_id, sed_parameter))
    url = r"documents/{0}?fields=content(parameters({1}))".format(sed_id, sed_parameter)
    output = send_request_to_dit(url)
    if output:
        sed_parameter_value = extract_parameter_value_from_sed_document(output, sed_parameter)
        log.logger.debug("Value: {0}".format(sed_parameter_value))
        return sed_parameter_value


def extract_parameter_value_from_sed_document(output, sed_parameter):
    """
    Extract value for particular SED Parameter

    :param output: Output returned by curl request
    :type output: str
    :param sed_parameter: SED Parameter
    :type sed_parameter: str

    :return: SED Parameter Value
    :rtype: str

    :return:
    """
    try:
        return json.loads(output)["content"]["parameters"][sed_parameter]
    except Exception as e:
        log.logger.debug("Data received from DIT in unexpected format:- Data: '{0}', Error: '{1}'".format(output, e))


def get_deployment_namespace(deployment_name, documents_info_dict):
    """
    Fetch Deployment namespace from cENM Site Info document

    :param deployment_name: Deployment Name
    :type deployment_name: str
    :param documents_info_dict: Documents Info Dict
    :type documents_info_dict: dict
    :return: Deployment Namespace
    :rtype: str
    """
    log.logger.debug("Getting the namespace for deployment: {0}".format(deployment_name))
    cenm_site_info_doc_id = documents_info_dict.get("cENM_site_information")
    if cenm_site_info_doc_id:
        content = get_document_content_from_dit(cenm_site_info_doc_id)
        deployment_namespace = content.get('global').get("namespace")
        if deployment_namespace:
            log.logger.debug("Deployment namespace: {0}".format(deployment_namespace))
            return deployment_namespace
        else:
            log.logger.warn("Unable to retrieve cENM_site_information document from DIT")
    else:
        log.logger.warn("The document 'cENM_site_information' was not found on DIT for deployment "
                        "{0}".format(deployment_name))

    log.logger.debug("Unable to get Deployment Namespace")


def get_dit_deployment_info(deployment_name):
    """
    Fetch Deployment type

    :param deployment_name: Deployment Name
    :type deployment_name: str

    :return: Tuple containing Deployment Type and Dictionary of DIT documents info
    :rtype: tuple

    :raises Exception: if unable to get documents data from DIT
    """
    global DEPLOYMENT_TYPE, DIT_DOCUMENTS_INFO_DICT

    if not DEPLOYMENT_TYPE or not DIT_DOCUMENTS_INFO_DICT:
        DIT_DOCUMENTS_INFO_DICT = get_documents_info_from_dit(deployment_name)
        if not DIT_DOCUMENTS_INFO_DICT:
            raise Exception("Unable to get documents info from DIT for this deployment")
        DEPLOYMENT_TYPE = determine_deployment_type(DIT_DOCUMENTS_INFO_DICT)

    return DEPLOYMENT_TYPE, DIT_DOCUMENTS_INFO_DICT
