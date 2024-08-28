# ********************************************************************
# Name    : Parameter Management
# Summary : Functional module for managing parameters on NE(s) in ENM.
#           Allows the user to create, delete, update parameters in
#           ENM using POID(s), also some basic Network Explorer
#           querying and matching FDN from supplied POID(s).
# ********************************************************************

import json
from datetime import datetime
from retrying import retry
from requests.exceptions import HTTPError, ConnectionError

from enmutils.lib import log
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib.netex import Search
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.netex import get_pos_by_poids

TEMPORARY_QUERY_ENDPOINT = "/managedObjects/temporaryQueryForMoClassMapping/v2/"
UPDATE_ATTRIBUTES_ENDPOINT = "/persistentObject/{0}"
PARAMETER_SET_ENDPOINT = "/parametermanagement/v1/parameterset/"
PARAMETER_SET_DELETE_ENDPOINT = "/parametermanagement/v1/parameterset/ids"
PARMGT_03_QUERY_TIMEOUT = 300

TEST_DATA = {"name": "parameter_set", "category": "Public", "readOnly": False, "type": "USER_DEFINED",
             "description": "created by PARMGT_02 workload profile",
             "parameterDetails": {}}

PARAMETERS_4G = {
    "EUtranCellFDD": [
        "acBarringForCsfb",
        "acBarringForCsfbPresent",
        "acBarringForEmergency",
        "acBarringForMoData",
        "acBarringForMoDataPresent",
        "acBarringForMoSignalling",
        "acBarringForMoSignallingPresent",
        "acBarringInfoPresent",
        "acBarringPresence",
        "acBarringSkipForMmtelVideo",
    ],
    "EUtranCellRelation": [
        "amoAllowed",
        "amoState",
        "cellIndividualOffsetEUtran",
        "coverageIndicator",
        "createdBy",
        "crsAssistanceInfoPriority",
        "eranExternalUICompGroupAvail",
        "eranUICompCoopCellAllowed",
        "EUtranCellRelationId",
        "hoSuccLevel",
    ],
    "EUtranFreqRelation": [
        "a5OffsetPerPC",
        "a5Thr1RsrpFreqOffset",
        "a5Thr1RsrqFreqOffset",
        "a5Thr2RsrpFreqOffset",
        "a5Thr2RsrqFreqOffset",
        "allowedMeasBandwidth",
        "allowedPlmnList",
        "amoAllowed",
        "anrMeason",
        "arpPrio",
    ],
    "ExternalEUtranCellFDD": [
        "activePlmnList",
        "activeServiceAreaId",
        "additionalFreqBandList",
        "createdBy",
        "csgPhysCellId",
        "csgPhysCellIdRange",
        "dlChannelBandwidth",
        "eutranFrequencyRef",
        "ExternalEUtranCellFDDId",
        "freqBand",
    ],
    "ExternalEUtranCellTDD": [
        "activePlmnList",
        "activeServiceAreaId",
        "additionalFreqBandList",
        "createdBy",
        "csgPhysCellId",
        "csgPhysCellIdRange",
        "dlChannelBandwidth",
        "eutranFrequencyRef",
        "ExternalEUtranCellTDDId",
        "freqBand",
    ],
    "EUtranCellTDD": [
        "acBarringForCsfb",
        "acBarringForEmergency",
        "acBarringForMoData",
        "acBarringForMoSignalling",
        "acBarringInfoPresent"
        "acBarringPresence",
        "acBarringSkipForMmtelVideo",
        "acBarringSkipForMmtelVoice",
        "activePlmnList",
        "activeServiceAreaId"
    ],
    "ExternalENodeBFunction": [
        "createdBy",
        "eNBId",
        "eNodeBPlmnId",
        "eranVlanPortRef",
        "eSCellCapacityScaling",
        "ExternalENodeBFunctionId",
        "gUGroupIdList",
        "interENodeBCAInteractionMode",
        "lastModification",
        "masterEnbFunction",
    ],
    "ExternalGeranCell": [
        "bcc",
        "cellIdentity",
        "dtmSupport",
        "ExternalGeranCellId",
        "greaFrequencyRef",
        "IsRemoveAllowed",
        "lac",
        "lastModification",
        "masterGeranCellId",
        "ncc",
    ],
    "ExternalUtrancellFDD": [
        "cellIdentity",
        "ExternalUtranCellFDDId",
        "isRemoveAllowed",
        "lac",
        "lastModification",
        "lbUtranCellOffloadCapacity",
        "masterUtranCellId",
        "physicalCellIdentity",
        "plmnIdentity",
        "rac",
    ],
    "ExternalUtrancellTDD": [
        "cellIdentity",
        "ExternalUtranCellTDDId",
        "isRemoveAllowed",
        "lac",
        "lastModification",
        "masterUtranCellId",
        "physicalCellIdentity",
        "plmnIdentity",
        "rac",
        "reservedBy",
    ],
}

PARAMETERS_5G = {
    "NRCellCU": [
        "absFrameStartOffset",
        "endcUlNrQualHyst",
        "cellState",
        "epsFallbackOperation",
        "nCI",
        "nRCellCUId",
        "nRFrequencyRef",
        "qHyst",
        "reservedBy",
        "serviceStatus",
    ],
    "NRCellRelation": [
        "cellIndividualOffsetNR",
        "coverageIndicator",
        "includeInSIB",
        "isHoAllowed",
        "nRCellRef",
        "nRCellRelationId",
        "nRFreqRelationRef",
        "sCellCandidate",
    ],
    "NRFreqRelation": [
        "cellReselectionPriority",
        "nRFreqRelationId",
        "nRFrequencyRef",
        "pMax",
        "qOffsetFreq",
        "qQualMin",
        "qRxLevMin",
        "reservedBy",
        "sIntraSearchQ",
        "threshXHighP",
    ],
    "ExternalNRCellCU": [
        "absFrameStartOffset",
        "externalNRCellCUId",
        "nCI",
        "nRFrequencyRef",
        "nRPCI",
        "nRTAC",
        "plmnIdList",
        "reservedBy",
        "sNSSAIList",
    ],
    "TermPointToGNodeB": [
        "administrativeState",
        "availabilityStatus",
        "ipsecEpAddress",
        "ipv4Address",
        "ipv6Address",
        "operationalState",
        "termPointToGNodeBId",
        "upIpAddress",
        "usedIpAddress",
    ],
    "CUCP5qi": [
        "cUCP5qiId",
        "packetErrorRateExp",
        "packetErrorRateScalar",
        "pdcpSnSize",
        "profile5qi",
        "resourceType",
        "rlcMode",
        "serviceType",
        "tPdcpDiscard",
        "tReorderingDl",
    ],
    "ExternalGNBCUCPFunction": ["externalGNBCUCPFunctionId", "gNBId",
                                "gNBIdLength", "pLMNId"],
    "TermPointToAmf": [
        "administrativeState",
        "amfName",
        "availabilityStatus",
        "domainName",
        "ipv4Address1",
        "ipv4Address2",
        "ipv6Address1",
        "ipv6Address2",
        "operationalState",
        "pLMNIdList",
    ],
    "TermPointToGNBCUUP": [
        "availabilityStatus",
        "gNBCUUPId",
        "gNBCUUPName",
        "operationalState",
        "termPointToGNBCUUPId",
        "usedIpAddress",
    ],
    "TermPointToGNBDU": [
        "administrativeState",
        "availabilityStatus",
        "gNBDUId",
        "gNBDUName",
        "reservedBy",
        "usedIpAddress",
    ],
}


def temporary_query_for_mo_class_mapping(user, query):
    """
    Temporary query for mo class mapping

    :type user: `enm_user_2.User`
    :param user: User who will create the job
    :type query: str
    :param query: Search query to be performed

    :rtype: json dict
    :return: json response
    """
    payload = {"query": query}
    response = user.get(TEMPORARY_QUERY_ENDPOINT, params=payload, verify=False)
    response.raise_for_status()
    return response.json()


def update_attributes(user, po_data, attributes):
    """
    Update MO attributes

    :type user: `enm_user_2.User`
    :param user: User who will create the job
    :type po_data: dict
    :param po_data: PO data with required attributes
    :type attributes: list
    :param attributes: List of attribute dictionaries with key, value and datatype to be updated
    """
    update_attribute_json = {"poId": po_data["poId"],
                             "fdn": po_data["fdn"],
                             "attributes": attributes}
    data = json.dumps(update_attribute_json)
    update_attribute_url = UPDATE_ATTRIBUTES_ENDPOINT.format(po_data["poId"])

    log.logger.debug("PUT with data: {0}".format(data))

    response = user.put(update_attribute_url, data=data, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()


def get_parameter_set(user):
    """
    Get parameter set data

    :type user: `enm_user_2.User`
    :param user: User who will create the job

    :rtype: dict
    :return: json response of parameter set data
    """
    response = user.get(PARAMETER_SET_ENDPOINT, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    return json.loads(response.text)


def get_parameter_set_count(user):
    """
    Get number of parameter sets

    :type user: `enm_user_2.User`
    :param user: User who will create the job

    :rtype: int
    :return: current number of parameter sets from get_parameter_set response
    """
    response = get_parameter_set(user)
    return response["resultSize"]


def create_parameter_set(user, data=None):
    """
    Create a parameter set with given data

    :type user: `enm_user_2.User`
    :param user: User who will create the job
    :type data: dict
    :param data: data to create parameter set
    """
    response = user.post(PARAMETER_SET_ENDPOINT, data=data, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()


def delete_parameter_set(user, parameter_set_ids):
    """
    Delete a parameter set for a given parameter set id

    :type user: `enm_user_2.User`
    :param user: User who will create the job
    :type parameter_set_ids: list
    :param parameter_set_ids: ids of parameter sets to be deleted

    :rtype: `requests.models.Response`
    :return: Response for the deletion of parameter set
    """
    response = user.delete_request(PARAMETER_SET_DELETE_ENDPOINT, params={"id": parameter_set_ids}, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    return response


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=30000,
       stop_max_attempt_number=3)
def perform_netex_search(user, search_query, search_name="PARMGT_03_"):
    """
    Performs netex search without saving and returns the result
    :param user: User to perform search
    :type user: enm_user_2.User
    :param search_query: Query to perform
    :type search_query: str
    :param search_name: Name of the search
    :type search_name: str
    :return: Search object
    :rtype: enmutils_int.lib.netex.Search
    """
    search_name = "_".join([search_name, datetime.now().strftime("%m%d-%H%M%S%f")[0:-4]])
    search = Search(user, search_query, search_name, version="v2")
    search.result = search.execute(timeout=PARMGT_03_QUERY_TIMEOUT)

    return search


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=30000,
       stop_max_attempt_number=3)
def get_fdns_from_poids(user, search, mo_type, parameter):
    """
    Requests the MO fdns of the given poid list
    :param user: User to perform request
    :type user: enm_user_2.User
    :param search: Return of Search object execute function
    :type search: dict
    :param mo_type: Mo_type to be mapped
    :type mo_type: str
    :param parameter: Attribute to be used
    :type parameter: str
    :return: List of fdns
    :rtype: list
    """
    fdns = []
    po_ids = [element["id"] for element in search["objects"]]
    for po_ids_chunk in chunks(po_ids, 250):
        pos_response = get_pos_by_poids(user, po_ids_chunk,
                                        attributeMappings=[
                                            {"moType": mo_type, "attributeNames": [parameter]}])
        fdns.extend(pos_response.json())
    fdns = [element["fdn"] for element in fdns]

    return fdns
