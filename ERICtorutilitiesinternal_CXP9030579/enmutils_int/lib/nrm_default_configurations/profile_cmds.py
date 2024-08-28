"""
The following defines managed object (MO) settings for AVC Burst profiles.

AVC Burst MO Info notes:
 - 'node_type': Must define the Node Type that these setting apply to.
 - 'mo_type_name': The MO to create the avc burst against
 - 'mo_path': The full path to the MO to create the avc burst against. Must be generic to multiple nodes. We can use
   '%NENAME%' as the name of the node. If no generic path available then specify as None
 - 'parent_mo_names': If no generic path may be specified, specify all the MO's parent MOs, but not the MO to create the
   avc burst on. If a generic path may be specified, this should be se to None, i.e. either 'mo_path' or
   'parent_mo_names' is None
 - 'mo_attribute': the attribute on the MO to change
 - 'mo_values': A list of the values to change the attribute to.
"""
import copy
import random
import string


def get_random_string(size=8, exclude=None, password=False, include_punctuation=False):
    """
    Generates a random string of the specified size (defaults to 8 characters)

    :param size: Number of characters to include in random string
    :type size: int
    :param exclude: Characters that are to be excluded from selection
    :type exclude: str
    :param password: Checks if its password
    :type password: bool
    :param include_punctuation: Include punctuation characters
    :type include_punctuation: bool

    :return: chars
    :rtype: str
    """

    characters = (string.ascii_letters + string.digits + string.punctuation if include_punctuation
                  else string.ascii_letters + string.digits)
    if exclude is not None:
        for char in exclude:
            characters = characters.replace(char, "")

    chars = ''.join(random.choice(characters) for _ in range(size))
    if password:
        chars = chars[:-4] + "H.8z"

    return chars


mo_values = ["cmsync_" + get_random_string(size=8, exclude='ok' + string.ascii_uppercase + string.digits),
             "cmsync_" + get_random_string(size=8, exclude='ok' + string.ascii_uppercase + string.digits),
             "cmsync_" + get_random_string(size=8, exclude='ok' + string.ascii_uppercase + string.digits)]
mo_values_numbers = random.randint(10000000, 99999999)

CPP_AVC_BURST_MO_TYPE_SETTINGS = [
    {"notification_percentage_rate": 0.35, "node_type": "ERBS",
     "mo_type_name": "EUtranCellFDD",
     "mo_path": None,
     "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtranCellFDD"],
     "mo_attribute": "userLabel",
     "mo_values": mo_values},

    {"notification_percentage_rate": 0.15, "node_type": "RadioNode",
     "mo_type_name": "EUtranCellFDD",
     "mo_path": None,
     "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtranCellFDD"],
     "mo_attribute": "userLabel",
     "mo_values": mo_values},

    {"notification_percentage_rate": 0.1, "node_type": "ERBS",
     "mo_type_name": "TermPointToENB",
     "mo_path": None,
     "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtraNetwork", "ExternalENodeBFunction"],
     "mo_attribute": "domainName",
     "mo_values": ["cmsync_02.abc", "cmsync_02.def", ""]},

    {"notification_percentage_rate": 0.05, "node_type": "RadioNode",
     "mo_type_name": "Lrat:TermPointToENB",
     "mo_path": None,
     "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtraNetwork",
                         "Lrat:ExternalENodeBFunction"],
     "mo_attribute": "domainName",
     "mo_values": ["cmsync_02.abc", "cmsync_02.def", ""]},

    {"notification_percentage_rate": 0.1, "node_type": "ERBS",
     "mo_type_name": "PmEventService",
     "mo_path": "ManagedElement=1,ENodeBFunction=1,PmEventService=1",
     "parent_mo_names": None,
     "mo_attribute": "cellTraceFileSize",
     "mo_values": [mo_values_numbers, mo_values_numbers + 20, mo_values_numbers + 10]},

    {"notification_percentage_rate": 0.05, "node_type": "RadioNode",
     "mo_type_name": "Lrat:PmEventService",
     "mo_path": "ComTop:ManagedElement=%NENAME%,Lrat:ENodeBFunction=1,Lrat:PmEventService=1",
     "parent_mo_names": None,
     "mo_attribute": "cellTraceFileSize",
     "mo_values": [mo_values_numbers, mo_values_numbers + 20, mo_values_numbers + 10]},

    {"notification_percentage_rate": 0.1, "node_type": "ERBS",
     "mo_type_name": "UtranCellRelation",
     "mo_path": None,
     "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtranCellFDD", "UtranFreqRelation",
                         "UtranCellRelation"],
     "mo_attribute": "isRemoveAllowed",
     "mo_values": ["true", "false"]},


    {"notification_percentage_rate": 0.05, "node_type": "ERBS",
     "mo_type_name": "EUtranCellRelation",
     "mo_path": None,
     "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtranCellFDD", "EUtranFreqRelation",
                         "EUtranCellRelation"],
     "mo_attribute": "includeInSystemInformation",
     "mo_values": ["true", "false"]},

    {"notification_percentage_rate": 0.05, "node_type": "ERBS",
     "mo_type_name": "ExternalEUtranCellFDD",
     "mo_path": None,
     "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtraNetwork", "ExternalENodeBFunction",
                         "ExternalEUtranCellFDD"],
     "mo_attribute": "userLabel",
     "mo_values": mo_values},
]

ROUTER_6000_AVC_BURST_MO_TYPE_SETTINGS = [
    {"notification_percentage_rate": 1, "node_type": "Router_6672",
     "mo_type_name": "Shelf",
     "mo_path": "ManagedElement=1,Equipment=1,Shelf=1",
     "parent_mo_names": None,
     "mo_attribute": "userLabel",
     "mo_values": ["CMSYNC_15_ENMUSA", "CMSYNC_15_ENMITALY"]},
    {"notification_percentage_rate": 1, "node_type": "Router6672",
     "mo_type_name": "Shelf",
     "mo_path": "ManagedElement=1,Equipment=1,Shelf=1",
     "parent_mo_names": None,
     "mo_attribute": "userLabel",
     "mo_values": ["CMSYNC_15_ENMUSA", "CMSYNC_15_ENMITALY"]},
    {"notification_percentage_rate": 1, "node_type": "Router6675",
     "mo_type_name": "Shelf",
     "mo_path": "ManagedElement=1,Equipment=1,Shelf=1",
     "parent_mo_names": None,
     "mo_attribute": "userLabel",
     "mo_values": ["CMSYNC_15_ENMUSA", "CMSYNC_15_ENMITALY"]}
]

BSC_AVC_BURST_MO_TYPE_SETTINGS = [
    {"notification_percentage_rate": 1, "node_type": "BSC",
     "mo_type_name": "ComTop:ManagedElement",
     "mo_path": "ComTop:ManagedElement=%NENAME%",
     "parent_mo_names": None,
     "mo_attribute": "userLabel",
     "mo_values": ["CMSYNC_32_ENMUSA", "CMSYNC_32_ENMITALY"]}
]

EPGOI_AVC_BURST_MO_TYPE_SETTINGS = [
    {"notification_percentage_rate": 1, "node_type": "EPG-OI",
     "mo_type_name": "card",
     "mo_path": "cardipr:card=1",
     "parent_mo_names": None,
     "mo_attribute": "speed",
     "mo_values": [mo_values_numbers, mo_values_numbers + 10]}
]

PCG_AVC_BURST_MO_TYPE_SETTINGS = [
    {"notification_percentage_rate": 1, "node_type": "PCG",
     "mo_type_name": "network-instances",
     "mo_path": "ni:network-instances=,ni:network-instance=media-1",
     "parent_mo_names": None,
     "mo_attribute": "enabled",
     "mo_values": ["false", "true"]}
]

CMSYNC_45_AVC_BURST_MO_TYPE_SETTINGS = [
    {"notification_percentage_rate": 1, "node_type": "Shared-CNF",
     "mo_type_name": "gnbcucp3gpp:attributes",
     "mo_path": None,
     "parent_mo_names": ["me3gpp:ManagedElement", "gnbcucp3gpp:GNBCUCPFunction"],
     "mo_attribute": "gNBIdLength",
     "mo_values": [33, 34]},
    {"notification_percentage_rate": 1, "node_type": "Shared-CNF",
     "mo_type_name": "nrcellcu3gpp:attributes",
     "mo_path": None,
     "parent_mo_names": ["me3gpp:ManagedElement", "gnbcucp3gpp:GNBCUCPFunction", "nrcellcu3gpp:NRCellCU"],
     "mo_attribute": "mdtEnabled",
     "mo_values": ['false', 'true']},
    {"notification_percentage_rate": 1, "node_type": "Shared-CNF",
     "mo_type_name": "eutranfreqrel3gpp:attributes",
     "mo_path": None,
     "parent_mo_names": ["me3gpp:ManagedElement", "gnbcucp3gpp:GNBCUCPFunction", "nrcellcu3gpp:NRCellCU", "eutranfreqrel3gpp:EUtranFreqRelation"],
     "mo_attribute": "threshXHighP",
     "mo_values": [60, 61]}
]

"""
The following define what MOs are created and deleted on nodes and provides information required to build the
mcd burst commands.

Create Delete Notification Info notes:
 - 'mo_type_name': Is the name of the MO to create / delete on a node
 - 'parent_mo_types': specify all parent MOs of the MO to create/delete. Do not include the mo to create / delete.
 - 'create_from_parent_type': Where only one MO is allowed under a specfic MO type, we need to create this parent MO
   first before the specified MO. Only specify one MO here, the MO highest in the MO tree that requires creation.

Note:
 - '%NENAME%' is not an available option for mcd burst commands so need to perform a dumpmotree command on all
    nodes
"""

CMSYNC_AVC_BURST_MO_TYPE_SETTINGS = {
    "ERBS": [
        {"node_type": "ERBS",
         "mo_type_name": "EUtranCellFDD",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtranCellFDD"],
         "mo_attribute": "userLabel",
         "mo_values": mo_values},

        {"node_type": "ERBS",
         "mo_type_name": "EUtranCellRelation",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtranCellFDD", "EUtranFreqRelation",
                             "EUtranCellRelation"],
         "mo_attribute": "includeInSystemInformation",
         "mo_values": ["true", "false"]},

        {"node_type": "ERBS",
         "mo_type_name": "ExternalEUtranCellFDD",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtraNetwork", "ExternalENodeBFunction",
                             "ExternalEUtranCellFDD"],
         "mo_attribute": "userLabel",
         "mo_values": mo_values},

        {"node_type": "ERBS",
         "mo_type_name": "PmEventService",
         "mo_path": "ManagedElement=1,ENodeBFunction=1,PmEventService=1",
         "parent_mo_names": None,
         "mo_attribute": "cellTraceFileSize",
         "mo_values": [mo_values_numbers, mo_values_numbers + 20, mo_values_numbers]},

        {"node_type": "ERBS",
         "mo_type_name": "TermPointToENB",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtraNetwork", "ExternalENodeBFunction"],
         "mo_attribute": "domainName",
         "mo_values": [mo_values[0], mo_values[1], ""]},

        {"node_type": "ERBS",
         "mo_type_name": "UtranCellRelation",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtranCellFDD", "UtranFreqRelation",
                             "UtranCellRelation"],
         "mo_attribute": "isRemoveAllowed",
         "mo_values": ["true", "false"]}
    ],
    "RadioNode": [
        {"node_type": "RadioNode",
         "mo_type_name": "EUtranCellFDD",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtranCellFDD"],
         "mo_attribute": "userLabel",
         "mo_values": mo_values},

        {"node_type": "RadioNode",
         "mo_type_name": "EUtranCellRelation",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtranCellFDD",
                             "Lrat:EUtranFreqRelation", "Lrat:EUtranCellRelation"],
         "mo_attribute": "includeInSystemInformation",
         "mo_values": ["true", "false"]},

        {"node_type": "RadioNode",
         "mo_type_name": "ExternalEUtranCellFDD",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtraNetwork",
                             "Lrat:ExternalENodeBFunction", "Lrat:ExternalEUtranCellFDD"],
         "mo_attribute": "userLabel",
         "mo_values": mo_values},

        {"node_type": "RadioNode",
         "mo_type_name": "Lrat:PmEventService",
         "mo_path": "ComTop:ManagedElement=%NENAME%,Lrat:ENodeBFunction=1,Lrat:PmEventService=1",
         "parent_mo_names": None,
         "mo_attribute": "cellTraceFileSize",
         "mo_values": [mo_values_numbers, mo_values_numbers + 20, mo_values_numbers + 10]},

        {"node_type": "RadioNode",
         "mo_type_name": "Lrat:TermPointToENB",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtraNetwork",
                             "Lrat:ExternalENodeBFunction"],
         "mo_attribute": "domainName",
         "mo_values": mo_values},

        {"node_type": "RadioNode",
         "mo_type_name": "UtranCellRelation",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtranCellFDD",
                             "Lrat:UtranFreqRelation", "Lrat:UtranCellRelation"],
         "mo_attribute": "isRemoveAllowed",
         "mo_values": ["true", "false"]},

        {"node_type": "RadioNode",
         "mo_type_name": "GNBDU:NRCellDU",
         "mo_path": "ComTop:ManagedElement=%NENAME%,GNBDU:GNBDUFunction=1,GNBDU:NRCellDU=%NENAME%-1",
         "parent_mo_names": None,
         "mo_attribute": "userLabel",
         "mo_values": mo_values},

        {"node_type": "RadioNode",
         "mo_type_name": "GNBCUCP:NRCellRelation",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement", "GNBCUCP:GNBCUCPFunction", "GNBCUCP:NRCellCU"],
         "mo_attribute": "includeInSIB",
         "mo_values": ["true", "false"]},

        {"node_type": "RadioNode",
         "mo_type_name": "GNBCUCP:NRCellCU",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement", "GNBCUCP:GNBCUCPFunction"],
         "mo_attribute": "qHyst",
         "mo_values": [mo_values_numbers, mo_values_numbers - 5, mo_values_numbers + 1]},

        {"node_type": "RadioNode",
         "mo_type_name": "GNBDU:NRSectorCarrier",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement", "GNBDU:GNBDUFunction"],
         "mo_attribute": "altitude",
         "mo_values": [mo_values_numbers, mo_values_numbers - 5, mo_values_numbers + 1]},

        {"node_type": "RadioNode",
         "mo_type_name": "GNBCUCP:EUtranCellRelation",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement", "GNBCUCP:GNBCUCPFunction", "GNBCUCP:NRCellCU"],
         "mo_attribute": "isRemoveAllowed",
         "mo_values": ["true", "false"]},

        {"node_type": "RadioNode",
         "mo_type_name": "GNBCUCP:GNBCUCPFunction",
         "mo_path": None,
         "parent_mo_names": ["ComTop:ManagedElement"],
         "mo_attribute": "userLabel",
         "mo_values": mo_values},
    ],
    "RNC": [
        {"node_type": "RNC",
         "mo_type_name": "Fach",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
         "mo_attribute": "operationalState",
         "mo_values": ["ENABLED", "DISABLED"]},

        {"node_type": "RNC",
         "mo_type_name": "Hsdsch",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
         "mo_attribute": "operationalState",
         "mo_values": ["ENABLED", "DISABLED"]},

        {"node_type": "RNC",
         "mo_type_name": "UtranCell",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
         "mo_attribute": "operationalState",
         "mo_values": ["ENABLED", "DISABLED"]},

        {"node_type": "RNC",
         "mo_type_name": "GsmRelation",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
         "mo_attribute": "qOffset1sn",
         "mo_values": [mo_values_numbers, mo_values_numbers - 5]},

        {"node_type": "RNC",
         "mo_type_name": "Pch",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
         "mo_attribute": "availabilityStatus",
         "mo_values": [mo_values_numbers, mo_values_numbers - 5]},

        {"node_type": "RNC",
         "mo_type_name": "Rach",
         "mo_path": None,
         "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
         "mo_attribute": "availabilityStatus",
         "mo_values": [mo_values_numbers, mo_values_numbers - 5]},
    ],
}

CMSYNC_02_AVC_BURST_MO_TYPE_SETTINGS = copy.deepcopy(CMSYNC_AVC_BURST_MO_TYPE_SETTINGS)
CDT_NOTIFICATION_INFO_4G = {"node_type": "RadioNode",
                            "mo_type_name": "EUtranFreqRelation",
                            "mo_path": None,
                            "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction",
                                                "Lrat:EUtranCellFDD", "Lrat:EUtranFreqRelation"],
                            "mo_attribute": "candNeighborRel",
                            "mo_values": [[[1, random.randint(000, 167),
                                            random.randint(000, 167), random.randint(000, 167),
                                            random.randint(000, 167), random.randint(000, 167),
                                            1, random.randint(000, 167),
                                            0] for i in range(18)],
                                          [[1, random.randint(000, 167),
                                            random.randint(000, 167), random.randint(000, 167),
                                            random.randint(000, 167), random.randint(000, 167),
                                            1, random.randint(000, 167),
                                            0] for j in range(19)]]}
CDT_NOTIFICATION_INFO_5G = {"node_type": "RadioNode",
                            "mo_type_name": "GNBCUCP:EUtranFreqRelation",
                            "mo_path": None,
                            "parent_mo_names": ["ComTop:ManagedElement", "GNBCUCP:GNBCUCPFunction",
                                                "GNBCUCP:NRCellCU"],
                            "mo_attribute": "allowedPlmnList",
                            "mo_values": [[[random.randint(000, 999), random.randint(000, 9999)] for l in range(14)],
                                          [[random.randint(000, 999), random.randint(000, 9999)] for k in range(15)]]}
CMSYNC_02_AVC_BURST_MO_TYPE_SETTINGS["RadioNode"].append(CDT_NOTIFICATION_INFO_4G)
CMSYNC_02_AVC_BURST_MO_TYPE_SETTINGS["RadioNode"].append(CDT_NOTIFICATION_INFO_5G)

CMSYNC_MCD_BURST_MO_TYPE_SETTINGS = {
    "ERBS": [{
        "mo_type_name": "UtranCellRelation",
        "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtranCellFDD", "UtranFreqRelation"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "ExternalEUtranCellFDD",
        "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtraNetwork", "ExternalENodeBFunction"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "EUtranCellRelation",
        "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtranCellFDD", "EUtranFreqRelation"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "GeranCellRelation",
        "parent_mo_names": ["ManagedElement", "ENodeBFunction", "EUtranCellFDD", "GeranFreqGroupRelation"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "ExternalUtranCellFDD",
        "parent_mo_names": ["ManagedElement", "ENodeBFunction", "UtraNetwork", "UtranFrequency"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "ExternalGeranCell",
        "parent_mo_names": ["ManagedElement", "ENodeBFunction", "GeraNetwork"],
        "create_from_parent_type": None
    }],
    "RadioNode": [{
        "mo_type_name": "Lrat:UtranCellRelation",
        "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtranCellFDD",
                            "Lrat:UtranFreqRelation"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "Lrat:ExternalEUtranCellFDD",
        "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtraNetwork",
                            "Lrat:ExternalENodeBFunction"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "Lrat:EUtranCellRelation",
        "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtranCellFDD",
                            "Lrat:EUtranFreqRelation"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "Lrat:GeranCellRelation",
        "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtranCellFDD",
                            "Lrat:GeranFreqGroupRelation"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "Lrat:ExternalUtranCellFDD",
        "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:UtraNetwork",
                            "Lrat:UtranFrequency"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "Lrat:ExternalUtranCellTDD",
        "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:UtraNetwork",
                            "Lrat:UtranFrequency"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "Lrat:ExternalGeranCell",
        "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:GeraNetwork"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "GNBCUUP:S1ULink",
        "parent_mo_names": ["ComTop:ManagedElement", "GNBCUUP:GNBCUUPFunction", "GNBCUUP:S1UTermination"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "GNBCUUP:X2ULink",
        "parent_mo_names": ["ComTop:ManagedElement", "GNBCUUP:GNBCUUPFunction", "GNBCUUP:X2UTermination"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "GNBCUUP:EP_NgU",
        "parent_mo_names": ["ComTop:ManagedElement", "GNBCUUP:GNBCUUPFunction"],
        "create_from_parent_type": None
    }, {
        "mo_type_name": "GNBCUUP:EP_XnU",
        "parent_mo_names": ["ComTop:ManagedElement", "GNBCUUP:GNBCUUPFunction"],
        "create_from_parent_type": None
    }],
    "RNC": [{
        "mo_type_name": "Hsdsch",
        "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
        "mo_path": "RemovingWillTriggerDumpMOTree",
        "create_from_parent_type": None
    }, {
        "mo_type_name": "Rach",
        "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
        "mo_path": "RemovingWillTriggerDumpMOTree",
        "create_from_parent_type": None
    }, {
        "mo_type_name": "Pch",
        "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
        "mo_path": "RemovingWillTriggerDumpMOTree",
        "create_from_parent_type": None
    }, {
        "mo_type_name": "Fach",
        "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
        "mo_path": "RemovingWillTriggerDumpMOTree",
        "create_from_parent_type": None
    }, {
        "mo_type_name": "GsmRelation",
        "parent_mo_names": ["ManagedElement", "RncFunction", "UtranCell"],
        "mo_path": "RemovingWillTriggerDumpMOTree",
        "create_from_parent_type": None
    }]
}

CELLMGT_MO_ATTRIBUTE_DATA = {
    'EUtranCellFDD': [
        # Each list below consists of items as follows: "attribute_name", attribute_min_value, attribute_max_value
        # MO Attribute ranges below have been taken from the MOM for LTE Node (CPI)
        ["physicalLayerCellIdGroup", 0, 167],
        ["tac", 0, 65535],
        ["physicalLayerSubCellId", 0, 2],
        ["lbEUtranCellOffloadCapacity", 0, 1000000]
    ],
    'EUtranCellTDD': [
        # Each list below consists of items as follows: "attribute_name", attribute_min_value, attribute_max_value
        # MO Attribute ranges below have been taken from the MOM for LTE Node (CPI)
        ["physicalLayerCellIdGroup", 0, 167],
        ["tac", 0, 65535],
        ["physicalLayerSubCellId", 0, 2],
        ["lbEUtranCellOffloadCapacity", 0, 1000000]
    ],
    'UtranCell': [
        # Each list below consists of items as follows: "attribute_name", attribute_min_value, attribute_max_value
        # MO Attribute ranges below have been taken from the MOM for RNC Node (CPI)
        ["maxTxPowerUl", -50, 33],
        ["primaryCpichPower", -99, 500],
        ["primaryScramblingCode", 0, 127],
        ["uarfcnDl", 0, 16383]
    ]

}

ENMCLI_COMMANDS = {
    "cmedit_basic": {
        "eNodeB": [
            "cmedit get {node_id} MeContext",
            "cmedit get {node_id} MeContext.neType=={primary_type}",
            "cmedit get {node_id} {cell_type}.*",
            "cmedit get {node_id} {cell_type}.(administrativeState, operationalState) -t",
            "cmedit get {node_id} {cell_type}.(altitude>0, tac==1)",
            "cmedit get {node_id} {cell_type}.(administrativeState==LOCKED, tac==1)",
            "cmedit get {node_id} SubNetwork, MeContext, ManagedElement, ENodeBFunction, {cell_type}.tac==1, EUtranFreqRelation",
            "cmedit get {node_id} NetworkElement, CmFunction.syncStatus==UNSYNCHRONIZED",
            "cmedit get {node_id} ENodeBFunction.eNodeBPlmnId"
        ],
        "gNodeB": [
            "cmedit get {ten_node_id} NRCellDU.(administrativeState, operationalState) -t",
            "cmedit get {ten_node_id} RetSubUnit.(maxTilt>-1500, iuantAntennaOperatingBand==-1000)",
            "cmedit get {ten_node_id} NRCellCU.*",
            "cmedit get {node_id} NRCellRelation.*",
            "cmedit get {ten_node_id} NRCellDU.(administrativeState==LOCKED, nrtac==1)",
            "cmedit get {ten_node_id} SubNetwork, ManagedElement, GNBCUCPFunction, NRCellDU.nrtac==1, NRFreqRelation",
            "cmedit get {ten_node_id} NetworkElement, CmFunction.syncStatus==UNSYNCHRONIZED",
            "cmedit get {ten_node_id} GNBCUCPFunction.pLMNId"
        ]
    },
    "cmedit_standard": {
        "eNodeB": [
            "cmedit get {ten_node_id} MeContext",
            "cmedit get {ten_node_id} MeContext.neType=={primary_type}",
            "cmedit get {ten_node_id} {cell_type}.(administrativeState, operationalState) -t",
            "cmedit get {ten_node_id} {cell_type}.(altitude>0, tac==1)",
            "cmedit get {ten_node_id} {cell_type}.*",
            "cmedit get {node_id} EUtranCellRelation.*",
            "cmedit get {ten_node_id} {cell_type}.(administrativeState==LOCKED, tac==1)",
            "cmedit get {ten_node_id} SubNetwork, MeContext, ManagedElement, ENodeBFunction, {cell_type}.tac==1, EUtranFreqRelation",
            "cmedit get {ten_node_id} NetworkElement, CmFunction.syncStatus==UNSYNCHRONIZED",
            "cmedit get {ten_node_id} ENodeBFunction.eNodeBPlmnId"
        ],
        "gNodeB": [
            "cmedit get {ten_node_id} NRCellDU.(administrativeState, operationalState) -t",
            "cmedit get {ten_node_id} RetSubUnit.(maxTilt>-1500, iuantAntennaOperatingBand==-1000)",
            "cmedit get {ten_node_id} NRCellCU.*",
            "cmedit get {node_id} NRCellRelation.*",
            "cmedit get {ten_node_id} NRCellDU.(administrativeState==LOCKED, nrtac==1)",
            "cmedit get {ten_node_id} SubNetwork, ManagedElement, GNBCUCPFunction, NRCellDU.nrtac==1, NRFreqRelation",
            "cmedit get {ten_node_id} NetworkElement, CmFunction.syncStatus==UNSYNCHRONIZED",
            "cmedit get {ten_node_id} GNBCUCPFunction.pLMNId"
        ]
    },
    "cmedit_advanced": {
        "eNodeB": [
            "cmedit get {ninetynine_node_id} {cell_type}.(altitude>0, tac==1)",
            "cmedit get {ninetynine_node_id} ENodeBFunction, {cell_type}.(administrativeState==LOCKED)",
            "cmedit get * ManagedElement -neType=SGSN-MME",
            "cmedit get {ten_node_id} AntennaUnitGroup, AntennaNearUnit.administrativeState",
            "cmedit get * MeContext"
        ],
        "gNodeB": [
            "cmedit get {ninetynine_node_id} RetSubUnit.(maxTilt>-1500, iuantAntennaOperatingBand==-1000)",
            "cmedit get {ninetynine_node_id} GNBDUFunction, NRCellDU.(administrativeState==LOCKED)",
            "cmedit get * ManagedElement -neType=SGSN-MME",
            "cmedit get {ten_node_id} AntennaUnitGroup, AntennaNearUnit.administrativeState"
        ]
    },
    "alarm": [
        "alarm get {node_id} --critical --warning",
        "alarm get {ten_node_id} --critical --warning",
        "alarm get {node_id} -war -unack",
        "alarm get {ten_node_id} -war -unack",
        "alarm get {node_id} --begin {date}",
        "alarm get {ten_node_id} --begin {date}",
        "alarm get {node_id}",
        "alarm get {ten_node_id} --begin {date}",
        "alarm hist {node_id} -cri --begin {date}",
        "alarm hist {node_id} -maj --begin {date}",
        "alarm hist {ten_node_id} -war --begin {date}"
    ],
    "secadm": [
        "secadm cert get -ct OAM -n {node_id}",
        "secadm get ciphers --protocol SSL/HTTPS/TLS -n {node_id}",
        "secadm credentials get -n {node_id}",
        "secadm get ciphers --protocol SSH/SFTP -n {node_id}",
        "secadm trust get -ct OAM -n {node_id}"
    ]
}
