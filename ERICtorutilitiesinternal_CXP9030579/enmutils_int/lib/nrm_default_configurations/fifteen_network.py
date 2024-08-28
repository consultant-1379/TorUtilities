# ********************************************************************
# Name    : Fifteen Network
# Summary : If a profile is not listed here in this file, please refer to default values config file (forty_network.py) instead.
# ********************************************************************

from basic_network import (IMP_EXP_KEYS as IMP_EXP, USER_KEYS as USER, NODE_KEYS as NODE, TIME_KEYS as TIME,
                           NeTypesEnum as NODES, MAX_NODES, SKIP_SYNC_CHECK, ERROR_HANDLING, TIMEOUT, NUM_ITERATIONS,
                           COM_ROLES, OPS_USER_ROLES, CNX_RULEMODULES, NSX_RULEMODULES, GRX_RULEMODULES,
                           FMX_RULEMODULES, CHECK_NODE_SYNC,
                           LTE_CELL_CHECK, THREAD_QUEUE_TIMEOUT, GEO_USER_ROLES, NUM_EVENTS)
from profile_cmds import ROUTER_6000_AVC_BURST_MO_TYPE_SETTINGS

SCHEDULED_DAYS, SCHEDULE_SLEEP, SCHEDULED_TIMES_STRINGS = TIME
NUM_USERS, USER_ROLES = USER
NUM_NODES, SUPPORTED_NODE_TYPES, TOTAL_NODES, EXCLUDE_NODES_FROM, NODE_FILTER = NODE
INTERFACE, FILETYPE, FLOW, IMPORT_TYPE, CREATE_DELETE_LIVE, CREATE_DELETE_CONFIG, UPDATE_LIVE, UPDATE_CONFIG = IMP_EXP
TOTAL_TARGET_ALARMS = 2800000
FM_02_TOTAL_ALARMS = 4 * 5 * 60 * 24 * 40
FM_03_TOTAL_ALARMS = 4 * 60 * 8 * 200

fifteen_k_network = {
    "fifteen_k_network": {
        "amos": {},
        "aid": {
            'AID_02': {NUM_NODES: {NODES.ERBS: -1, NODES.RADIONODE: -1}, 'NUM_PROFILES': 2, 'FREQUENCY': 12,
                       NUM_USERS: 1,
                       NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB']}},
                       'AID_PROFILE_TIMEOUT': 10800,
                       USER_ROLES: ['AutoId_Administrator'], SCHEDULED_TIMES_STRINGS: ['06:00:00']},
            'AID_04': {SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE], TOTAL_NODES: 500, NUM_USERS: 1,
                       USER_ROLES: ['AutoId_Administrator', "ADMINISTRATOR"], 'NUM_NODES_PER_BATCH': 100,
                       SCHEDULED_TIMES_STRINGS: ['02:00:00'],
                       'MO_ATTRIBUTE_DATA': {
                           'FDD': {'EUtranCellFDD': [['physicalLayerCellIdGroup', 0, 167],
                                                     ['physicalLayerSubCellId', 0, 2]]},
                           'TDD': {'EUtranCellTDD': [['physicalLayerCellIdGroup', 0, 167],
                                                     ['physicalLayerSubCellId', 0, 2]]}},
                       'RUN_TYPE': 'NEW', EXCLUDE_NODES_FROM: ["AID_03"],
                       NODE_FILTER: {NODES.ERBS: {"lte_cell_type": ['FDD', 'TDD']},
                                     NODES.RADIONODE: {'managed_element_type': ['ENodeB'],
                                                       "lte_cell_type": ['FDD', 'TDD']}}}
        },
        "ap": {},
        "apt": {},
        "asr_l": {
            'ASR_L_01': {NUM_NODES: {NODES.ERBS: -1, NODES.RADIONODE: -1},
                         NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB']}},
                         USER_ROLES: ["ASR_Administrator", "ASR-L_Administrator", "Cmedit_Administrator"],
                         "SLEEP_TIME": 60, "NB_IP": "", "PORT": ""}
        },
        "asr_n": {
            'ASR_N_01': {NUM_NODES: {NODES.RADIONODE: -1},
                         NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['GNodeB']}},
                         USER_ROLES: ["ASR_Administrator", "ASR-L_Administrator", "Cmedit_Administrator"],
                         "SLEEP_TIME": 60, "NB_IP": "", "PORT": ""}
        },
        "asu": {
            'ASU_01': {},
        },
        "bur": {},
        "ca": {
            'CA_01': {}
        },
        'cbrs': {
            'CBRS_SETUP': {}
        },
        "cellmgt": {
            'CELLMGT_07': {},
            'CELLMGT_13': {},
            'CELLMGT_14': {},
            'CELLMGT_15': {}
        },
        "cli_mon": {},
        "cmevents_nbi": {},
        "cmexport": {
            'CMEXPORT_25': {}
        },
        "cmimport": {
            'CMIMPORT_01': {'TIMES_PER_DAY': 24, TOTAL_NODES: 3, SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE],
                            NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB', 'GNodeB']}},
                            'BATCH_MO_SIZE': 50, USER_ROLES: ['Cmedit_Administrator', 'CM_REST_Administrator'],
                            SCHEDULED_TIMES_STRINGS: ['03:00:01', '09:00:01', '17:00:01'],
                            'MO_VALUES': {'RetSubUnit': 1, 'AntennaSubunit': 1},
                            'MOS_ATTRS': {'RetSubUnit': ['userLabel'], 'AntennaSubunit': ['maxTotalTilt']},
                            EXCLUDE_NODES_FROM: ['CMSYNC_01', 'CMSYNC_02', 'CMSYNC_04', 'CMSYNC_06'],
                            TIMEOUT: 15 * 60, NUM_ITERATIONS: 24 / 3, FILETYPE: '3GPP', FLOW: 'live_config',
                            IMPORT_TYPE: UPDATE_LIVE,
                            'MOS_DEFAULT': {'RetSubUnit': ('userLabel', ""), 'AntennaSubunit': ('maxTotalTilt', 900)},
                            'MOS_MODIFY': {'RetSubUnit': ('userLabel', 'cmimport_01'),
                                           'AntennaSubunit': ('maxTotalTilt', 899)}},
            'CMIMPORT_02': {TOTAL_NODES: 1, SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE],
                            NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB', 'GNodeB']}},
                            'BATCH_MO_SIZE': 50, USER_ROLES: ['Cmedit_Administrator', 'CM_REST_Administrator'],
                            'MO_VALUES': {'EUtranCellRelation': 12, 'UtranCellRelation': 12, 'GeranCellRelation': 6},
                            'MOS_ATTRS': {'UtranCellRelation': ['externalUtranCellFDDRef', 'UtranCellRelationId'],
                                          'EUtranCellRelation': ['EUtranCellRelationId', 'neighborCellRef'],
                                          'GeranCellRelation': ['GeranCellRelationId']},
                            EXCLUDE_NODES_FROM: ['CMSYNC_02'],
                            SCHEDULED_TIMES_STRINGS: ['00:30:01', '01:30:01', '02:30:01', '03:30:01', '04:30:01',
                                                      '05:30:01', '06:30:01', '07:30:01', '08:30:01', '09:30:01'],
                            FILETYPE: 'dynamic', INTERFACE: 'NBIv2', FLOW: 'live_config',
                            IMPORT_TYPE: 'CreateDeleteLive', TIMEOUT: 15 * 60,
                            "MAPPING_FOR_5G_NODE_MO": {'UtranCellRelation': {'NRCellRelation': 15},
                                                       'EUtranCellRelation': {'EUtranCellRelation': 15}},
                            "MAPPING_FOR_5G_NODE_ATTRS": {'EUtranCellRelation': ['isRemoveAllowed',
                                                                                 'neighborCellRef',
                                                                                 'eUtranCellRelationId'],
                                                          'NRCellRelation': ['nRCellRelationId', 'nRCellRef',
                                                                             'nRFreqRelationRef']}},
            'CMIMPORT_03': {'MO_VALUES': {'TermPointToENB': 2},
                            'MOS_ATTRS': {'TermPointToENB': ['administrativeState']},
                            USER_ROLES: ['Cmedit_Administrator', 'CM_REST_Administrator'], 'BATCH_MO_SIZE': 100,
                            TOTAL_NODES: 10, SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE],
                            NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB', 'GNodeB']}},
                            EXCLUDE_NODES_FROM: ['CMSYNC_01', 'CMSYNC_02', 'CMSYNC_04', 'CMSYNC_06'],
                            SCHEDULED_TIMES_STRINGS: ['08:45:01', '09:45:01', '10:45:01', '11:45:01', '12:45:01',
                                                      '13:45:01', '14:45:01', '15:45:01', '16:45:01', '17:45:01',
                                                      '18:45:01', '19:45:01', '20:45:01', '21:45:01'],
                            FILETYPE: 'dynamic', IMPORT_TYPE: UPDATE_LIVE, FLOW: 'live_config',
                            'MOS_DEFAULT': {'TermPointToENB': ('administrativeState', 'UNLOCKED'),
                                            'TermPointToGNodeB': ('administrativeState', 'UNLOCKED')},
                            'MOS_MODIFY': {'TermPointToENB': ('administrativeState', 'LOCKED'),
                                           'TermPointToGNodeB': ('administrativeState', 'LOCKED')},
                            TIMEOUT: 60 * 60, 'UNDO_TIME': '09:45:01', INTERFACE: 'NBIv2',
                            "MAPPING_FOR_5G_NODE_MO": {'TermPointToENB': {'TermPointToGNodeB': 2}},
                            "MAPPING_FOR_5G_NODE_ATTRS": {'TermPointToGNodeB': ['administrativeState']}},
            'CMIMPORT_04': {'MO_VALUES': {'EUtranCellRelation': 2},
                            'MOS_ATTRS': {'EUtranCellRelation': ['EUtranCellRelationId', 'neighborCellRef']},
                            USER_ROLES: ['Cmedit_Administrator', 'CM_REST_Administrator'], TOTAL_NODES: 100,
                            SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE],
                            NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB']}},
                            SCHEDULED_TIMES_STRINGS: ['12:50:01', '13:50:01', '14:50:01', '15:50:01', '16:50:01',
                                                      '17:50:01'], 'BATCH_MO_SIZE': 100, FILETYPE: 'dynamic',
                            FLOW: 'live_config', IMPORT_TYPE: CREATE_DELETE_LIVE, TIMEOUT: 60 * 60},
            'CMIMPORT_05': {'MO_VALUES': {'UtranFreqRelation': 6, 'EUtranFreqRelation': 4},
                            'MOS_ATTRS': {'UtranFreqRelation': ['userLabel'], 'EUtranFreqRelation': ['userLabel']},
                            USER_ROLES: ['Cmedit_Administrator', 'CM_REST_Administrator'],
                            SCHEDULED_TIMES_STRINGS: ['02:20:01', '10:00:01'],
                            'BATCH_MO_SIZE': 100, TOTAL_NODES: 500, SUPPORTED_NODE_TYPES: [NODES.RADIONODE],
                            NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB']}},
                            FILETYPE: '3GPP', FLOW: 'live_config', INTERFACE: 'NBIv2', IMPORT_TYPE: UPDATE_LIVE,
                            'MOS_DEFAULT': {'UtranFreqRelation': ('userLabel', 'cmimport_05_default'),
                                            'EUtranFreqRelation': ('userLabel', 'cmimport_05_default')},
                            'MOS_MODIFY': {'UtranFreqRelation': ('userLabel', 'cmimport_05_changes'),
                                           'EUtranFreqRelation': ('userLabel', 'cmimport_05_changes')},
                            TIMEOUT: 45 * 60, EXCLUDE_NODES_FROM: ["NODESEC_13"]},
            'CMIMPORT_10': {SUPPORTED_NODE_TYPES: [NODES.ROUTER6672], TOTAL_NODES: 316, 'BATCH_MO_SIZE': 100,
                            USER_ROLES: ['Cmedit_Administrator', 'CM_REST_Administrator'],
                            SCHEDULED_TIMES_STRINGS: ['02:10:00'], INTERFACE: 'NBIv2',
                            'MO_VALUES': {'SwItem': 4}, 'MOS_ATTRS': {'SwItem': ['userLabel']},
                            FILETYPE: 'dynamic', EXCLUDE_NODES_FROM: ['CMSYNC_11', 'CMSYNC_15'],
                            FLOW: 'live_config', IMPORT_TYPE: UPDATE_LIVE,
                            'MOS_DEFAULT': {'SwItem': ('userLabel', 'default')},
                            'MOS_MODIFY': {'SwItem': ('userLabel', 'modify')},
                            ERROR_HANDLING: 'continue-on-error-node', TIMEOUT: 90 * 60},
            'CMIMPORT_15': {USER_ROLES: ['Cmedit_Administrator', 'CM_REST_Administrator'], NUM_USERS: 20,
                            SCHEDULED_TIMES_STRINGS: ['09:00:01']},
            'CMIMPORT_18': {},
            'CMIMPORT_19': {},
            'CMIMPORT_20': {},
            'CMIMPORT_21': {},
            'CMIMPORT_22': {},
            'CMIMPORT_23': {},
            'CMIMPORT_24': {},
            'CMIMPORT_26': {},
            'CMIMPORT_27': {},
            'CMIMPORT_28': {},
            'CMIMPORT_29': {},
            'CMIMPORT_30': {},
            'CMIMPORT_31': {},
            'CMIMPORT_32': {},
            'CMIMPORT_33': {}
        },
        "cmsync": {
            'CMSYNC_15': {TOTAL_NODES: 100, SUPPORTED_NODE_TYPES: [NODES.ROUTER6672, NODES.ROUTER6675],
                          SCHEDULE_SLEEP: 1800,
                          'NOTIFICATION_INFO': ROUTER_6000_AVC_BURST_MO_TYPE_SETTINGS, 'ROUTER_SUPPORT': 2000,
                          EXCLUDE_NODES_FROM: ['CMIMPORT_10'], 'BURST_DURATION': 1800},
            'CMSYNC_33': {TOTAL_NODES: 200, SUPPORTED_NODE_TYPES: [NODES.ROUTER6672],
                          SCHEDULED_DAYS: ["THURSDAY"],
                          SCHEDULED_TIMES_STRINGS: ["17:30:00"]},
            'CMSYNC_34': {TOTAL_NODES: 200, SUPPORTED_NODE_TYPES: [NODES.MINI_LINK_Indoor],
                          SCHEDULED_DAYS: ["THURSDAY"],
                          SCHEDULED_TIMES_STRINGS: ["01:30:00"]},
            'CMSYNC_35': {},
            'CMSYNC_39': {},
            'CMSYNC_40': {},
            'CMSYNC_41': {},
            'CMSYNC_42': {},
            'CMSYNC_44': {}
        },
        "configuration_template": {},
        "doc": {},
        "dynamic_crud": {
            'DYNAMIC_CRUD_01': {NUM_USERS: 1, USER_ROLES: ['ADMINISTRATOR'], NUM_NODES: {NODES.RADIONODE: 10},
                                NODE_FILTER: {NODES.RADIONODE: {"managed_element_type": ["ENodeB", "GNodeB"]}},
                                SCHEDULE_SLEEP: 30 * 60,
                                "REQ_COUNTS": {"REQ_1_2_3": 47, "REQ_4_5_6": 234,
                                               "REQ_7": 4, "REQ_8": 3, "REQ_9": 3, "REQ_10": 3}},
            'DYNAMIC_CRUD_03': {NUM_USERS: 1, USER_ROLES: ['ADMINISTRATOR'], NUM_NODES: {NODES.RADIONODE: 40},
                                NODE_FILTER: {NODES.RADIONODE: {"managed_element_type": ["ENodeB", "GNodeB"]}},
                                SCHEDULED_TIMES_STRINGS: ["09:30:00", "21:30:00"], "NUMBER_OF_THREADS": 20,
                                "REQ_COUNTS": {"REQ_1_2_3": 200}, EXCLUDE_NODES_FROM: ["DYNAMIC_CRUD_05"],
                                "NODES_PER_HOST": 10, MAX_NODES: 25},
            'DYNAMIC_CRUD_04': {NUM_USERS: 1, USER_ROLES: ['ADMINISTRATOR'], NUM_NODES: {NODES.RADIONODE: 10},
                                NODE_FILTER: {NODES.RADIONODE: {"managed_element_type": ["ENodeB", "GNodeB"]}},
                                SCHEDULED_TIMES_STRINGS: ["03:30:00", "07:30:00", "11:30:00", "15:30:00", "19:30:00",
                                                          "23:30:00"],
                                "NUMBER_OF_THREADS": 10, "REQ_COUNTS": {"REQ_1_2_3": 1875}},
            'DYNAMIC_CRUD_05': {NUM_USERS: 1, USER_ROLES: ['ADMINISTRATOR'], NUM_NODES: {NODES.RADIONODE: 6},
                                NODE_FILTER: {NODES.RADIONODE: {"managed_element_type": ["ENodeB", "GNodeB"]}},
                                "NUMBER_OF_THREADS": 2, SCHEDULED_TIMES_STRINGS: ["02:30:00", "14:30:00"],
                                "REQ_COUNTS": {"PATCH": 19}, EXCLUDE_NODES_FROM: ["DYNAMIC_CRUD_03"],
                                "NODES_PER_HOST": 3, MAX_NODES: 3}
        },
        "ebsl": {},
        "ebsn": {
            "EBSN_05": {NUM_NODES: {NODES.RADIONODE: -1}, NUM_EVENTS: 1.0, 'NUM_COUNTERS': 1.0, "EBS_EVENTS": True,
                        USER_ROLES: ["ADMINISTRATOR", 'Cmedit_Administrator', "PM_Operator"], 'POLL_SCANNERS': True,
                        NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ["GNodeB"]}},
                        'CELL_TRACE_CATEGORY': "CELLTRACE_NRAN_AND_EBSN_STREAM", "EVENT_FILTER": "cellTraceNRan",
                        'DEFINER': "CELLTRACENRAN_SubscriptionAttributes", 'SLEEP_TIME': 240}
        },
        "ebsm": {},
        "em": {
            'EM_01': {SUPPORTED_NODE_TYPES: [NODES.MINI_LINK_669x], TOTAL_NODES: 100, NUM_USERS: 50,
                      'TOTAL_NODES_NON_RACK': 50, 'NUM_USERS_RACK': 100,
                      SCHEDULED_TIMES_STRINGS: ["00:30:00", "06:30:00", "12:30:00", "18:30:00"],
                      "PARALLEL_SESSIONS_LAUNCH": 2,
                      USER_ROLES: ['Element_Manager_Operator', 'ENodeB_Application_Administrator',
                                   'GNodeB_Application_Administrator', 'Network_Explorer_Operator',
                                   'RemoteDesktop_Operator', 'DesktopSession_Administrator']}
        },
        "enmcli": {
            'ENMCLI_02': {SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE], TOTAL_NODES: 47, NUM_USERS: 47,
                          NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB', 'GNodeB']}},
                          USER_ROLES: ['Cmedit_Administrator', 'Network_Explorer_Administrator'],
                          SCHEDULE_SLEEP: 60 * 15, EXCLUDE_NODES_FROM: ["TOP_01"], LTE_CELL_CHECK: True},
            'ENMCLI_05': {TOTAL_NODES: 1500, SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE], NUM_USERS: 1,
                          USER_ROLES: ['Cmedit_Administrator', 'Network_Explorer_Administrator']},
            'ENMCLI_08': {},
        },
        "esm": {},
        "esm_nbi": {},
        "fm": {
            'FM_01': {
                SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE, NODES.MGW, NODES.RNC, NODES.RBS, NODES.ROUTER6672,
                                       NODES.BSC,
                                       NODES.MSC_DB_BSP, NODES.MSC_BC_BSP, NODES.MSC_BC_IS, NODES.SIU02, NODES.TCU02,
                                       NODES.SGSN_MME,
                                       NODES.MINI_LINK_Indoor, NODES.CCDM],
                NUM_USERS: 1, USER_ROLES: ["ADMINISTRATOR"], 'PLATFORM_TYPES': ['Cpp', 'Bsc', 'Msc'], 'AML_RATIO': 0.5,
                TOTAL_NODES: 17, 'BSC_BURST_RATE': 0.038, 'MSC_BURST_RATE': 0.038,
                'FM_01_TOTAL_ALARMS': TOTAL_TARGET_ALARMS - (FM_02_TOTAL_ALARMS + FM_03_TOTAL_ALARMS),
                'DURATION': 3660, SCHEDULE_SLEEP: 3600, EXCLUDE_NODES_FROM: ["FM_02", "FM_03"], 'AML_RATE': 1.0,
                'ALARM_SIZE_DISTRIBUTION': [1000, 1000, 1000, 1000, 2000, 2000, 2000, 2000, 3000, 4000],
                'ALARM_PROBLEM_DISTRIBUTION': [
                    ('Nss Synchronization System Clock Status Change', 'indeterminate'),
                    ('Nss Synchronization System Clock Status Change', 'indeterminate'),
                    ('EXTERNAL ALARM', 'major'),
                    ('CCITT7 SIGNALLING LINK FAILURE', 'major'),
                    ('TU Synch Reference Loss of Signal', 'major'),
                    ('TU Synch Reference Loss of Signal', 'major'),
                    ('TU Synch Reference Loss of Signal', 'major'), ('Link Failure', 'critical'),
                    ('Link Failure', 'critical'), ('Link Failure', 'critical'), ('', 'warning'),
                    ('', 'warning')]},
            'FM_02': {
                SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE, NODES.MGW, NODES.RNC, NODES.RBS, NODES.ROUTER6672,
                                       NODES.BSC,
                                       NODES.MSC_DB_BSP, NODES.MSC_BC_BSP, NODES.MSC_BC_IS, NODES.SIU02, NODES.TCU02,
                                       NODES.SGSN_MME,
                                       NODES.MINI_LINK_Indoor, NODES.CCDM],
                TOTAL_NODES: 225, 'BURST_RATE': 40, 'DURATION': 300, SCHEDULE_SLEEP: 900,
                NUM_USERS: 1, USER_ROLES: ["ADMINISTRATOR"], 'PLATFORM_TYPES': ['Cpp', 'Bsc', 'Msc'],
                EXCLUDE_NODES_FROM: ["FM_01", "FM_03"], 'AML_RATE': 2.0, 'AML_RATIO': 0.5,
                'ALARM_SIZE_DISTRIBUTION': [1000, 1000, 1000, 1000, 2000, 2000, 2000, 2000, 3000, 4000],
                'ALARM_PROBLEM_DISTRIBUTION': [
                    ('Nss Synchronization System Clock Status Change', 'indeterminate'),
                    ('Nss Synchronization System Clock Status Change', 'indeterminate'),
                    ('EXTERNAL ALARM', 'major'),
                    ('CCITT7 SIGNALLING LINK FAILURE', 'major'),
                    ('TU Synch Reference Loss of Signal', 'major'),
                    ('TU Synch Reference Loss of Signal', 'major'),
                    ('TU Synch Reference Loss of Signal', 'major'), ('Link Failure', 'critical'),
                    ('Link Failure', 'critical'), ('Link Failure', 'critical'), ('', 'warning'),
                    ('', 'warning')]},
            'FM_03': {
                SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE, NODES.MGW, NODES.RNC, NODES.RBS, NODES.ROUTER6672,
                                       NODES.BSC,
                                       NODES.MSC_DB_BSP, NODES.MSC_BC_BSP, NODES.MSC_BC_IS, NODES.SIU02, NODES.TCU02,
                                       NODES.SGSN_MME,
                                       NODES.MINI_LINK_Indoor, NODES.CCDM],
                NUM_USERS: 1, USER_ROLES: ["ADMINISTRATOR"], 'PLATFORM_TYPES': ['Cpp', 'Bsc', 'Msc'],
                TOTAL_NODES: 1000, 'BURST_RATE': 200, 'DURATION': 240,
                SCHEDULED_TIMES_STRINGS: ['00:00:00', '02:45:00', '06:00:00', '09:35:00', '12:10:00',
                                          '14:45:00', '18:00:00', '21:00:00'],
                EXCLUDE_NODES_FROM: ["FM_01", "FM_02"], 'AML_RATE': 10.0, 'AML_RATIO': 0.5,
                'ALARM_SIZE_DISTRIBUTION': [1000, 1000, 1000, 1000, 2000, 2000, 2000, 2000, 3000, 4000],
                'ALARM_PROBLEM_DISTRIBUTION': [
                    ('Nss Synchronization System Clock Status Change', 'indeterminate'),
                    ('Nss Synchronization System Clock Status Change', 'indeterminate'),
                    ('EXTERNAL ALARM', 'major'),
                    ('CCITT7 SIGNALLING LINK FAILURE', 'major'),
                    ('TU Synch Reference Loss of Signal', 'major'),
                    ('TU Synch Reference Loss of Signal', 'major'),
                    ('TU Synch Reference Loss of Signal', 'major'), ('Link Failure', 'critical'),
                    ('Link Failure', 'critical'), ('Link Failure', 'critical'), ('', 'warning'),
                    ('', 'warning')]},
            'FM_08': {TOTAL_NODES: 500, SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE, NODES.ROUTER6672,
                                                               NODES.CCDM],
                      NUM_USERS: 10, 'NUM_USERS_1': 7, 'NUM_USERS_2': 3,
                      USER_ROLES: ["FM_Operator"], 'ALARM_MONITOR_SLEEP': 5 * 60, SCHEDULE_SLEEP: 60 * 15},
            'FM_09': {TOTAL_NODES: 500, SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE, NODES.ROUTER6672,
                                                               NODES.CCDM],
                      NUM_USERS: 12,
                      USER_ROLES: ["FM_Operator"], 'ALARM_MONITOR_SLEEP': 60, SCHEDULE_SLEEP: 60 * 15},
            'FM_12': {NUM_USERS: 1, USER_ROLES: ["ADMINISTRATOR"], 'TIMEOUT_SUBSCRIPTION': 60 * 24,
                      'NUMBER_NBI_SUBSCRIPTIONS': 14, 'TIMEOUT': 2,
                      'NBI_filters': ["LTE0", "LTE1", "LTE2", "LTE3", "LTE4"],
                      'CORBA_ENABLED': True, 'BNSI': True, SCHEDULED_TIMES_STRINGS: ["07:00:00"]},
            'FM_14': {TOTAL_NODES: 1, SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE, NODES.CCDM], NUM_USERS: 2,
                      USER_ROLES: ["FM_Administrator"], SCHEDULED_TIMES_STRINGS: ["16:00:00"],
                      "TIME_SPAN": 90},
        },
        "fmx": {
            'FMX_01': {SCHEDULE_SLEEP: 60 * 60, USER_ROLES: ["FMX_Administrator"], 'execute_on_transport': False,
                       FMX_RULEMODULES: NSX_RULEMODULES + CNX_RULEMODULES + GRX_RULEMODULES},
            'FMX_05': {NUM_USERS: 1, 'NODE_COUNT': 12, 'NODE_TYPES': ['ERBS', 'RadioNode'],
                       USER_ROLES: ["ADMINISTRATOR"], SCHEDULE_SLEEP: 60 * 60, 'FETCH_NODES_FROM': ['FM_01', 'FM_02'],
                       'MAINTENANCE_MODES': ['MARK', 'NMS', 'NMSandOSS']}
        },
        "ftpes": {},
        "fan": {},
        "fs_quotas": {},
        "geo_r": {
            'GEO_R_01': {SCHEDULED_TIMES_STRINGS: ["05:00:00", "11:00:00", "17:00:00", "23:00:00"],
                         USER_ROLES: GEO_USER_ROLES, "EXPORT_SIZE": "1.5", "MAX_FM_HISTORY_SIZE": "1"}
        },
        "ha": {},
        "launcher": {},
        "lcm": {},
        "lkf": {},
        "logviewer": {},
        "lt_syslog_stream": {},
        "ncm_mef_lcm": {},
        "ncm_l3_vpn": {},
        "ncm_mef": {},
        "ncm_vpn_sd": {},
        "neo4j": {},
        "netex": {
            'NETEX_04': {},
            'NETEX_07': {},
        },
        "netview": {},
        "network": {},
        "nhc": {
            'NHC_01': {"NHC_SLEEP": 120, NUM_USERS: 1, USER_ROLES: ["Nhc_Operator"], "START_TIME": "19:55:00",
                       "STOP_TIME": "05:55:00", SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.MGW, NODES.RNC, NODES.RBS],
                       TOTAL_NODES: 500},
            'NHC_02': {NUM_USERS: 1, USER_ROLES: ["Nhc_Administrator"], SUPPORTED_NODE_TYPES: [NODES.RADIONODE],
                       TOTAL_NODES: 250,
                       NODE_FILTER: {NODES.RADIONODE: {"node_version": ["18.Q3", "18.Q4", "19.Q1", "19.Q2", "19.Q3",
                                                                        "19.Q4", "20.Q1", "20.Q2", "20.Q3", "20.Q4",
                                                                        "21.Q1", "21.Q2", "21.Q3", "21.Q4"]}},
                       SCHEDULED_TIMES_STRINGS: ['04:30:00'], SCHEDULED_DAYS: ['THURSDAY'],
                       "NHC_JOB_TIME": "05:00:00"},
            'NHC_04': {NUM_USERS: 1, USER_ROLES: ["Nhc_Administrator", "Shm_Administrator"],
                       SUPPORTED_NODE_TYPES: [NODES.RADIONODE], TOTAL_NODES: 250,
                       NODE_FILTER: {NODES.RADIONODE: {"node_version": ["20.Q1", "20.Q2", "20.Q3", "20.Q4",
                                                                        "21.Q1", "21.Q2", "21.Q3", "21.Q4"]}},
                       SCHEDULED_TIMES_STRINGS: ['08:20:00'],
                       SCHEDULED_DAYS: ['THURSDAY'], "NHC_JOB_TIME": "08:50:00"}
        },
        "nhm": {
            'NHM_SETUP': {TOTAL_NODES: 4000, SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE],
                          'TRANSPORT_SETUP': False,
                          'NUMBER_OF_INSTANCES_REQUIRED': 300000.0, 'INSTANCES_GENERATED_BY_NPA_01': 8000.0,
                          'MAX_NUMBER_OF_CUSTOM_KPIS': 100,
                          NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB']}},
                          'REPORTING_OBJECT_02': {'RNC': ['UtranCell'], 'ERBS': ['EUtranCellFDD', 'EUtranCellTDD'],
                                                  'RadioNode': ['EUtranCellFDD', 'EUtranCellTDD']},
                          'REPORTING_OBJECT_01': {'ERBS': 'ENodeBFunction', 'RadioNode': 'ENodeBFunction'},
                          'SUPPORTED_TYPES_CUSTOM_CELL_LEVEL_KPI': ['ERBS', 'RadioNode'],
                          'UNSUPPORTED_TYPES_NODE_LEVEL_KPI': ['RNC'],
                          USER_ROLES: ['NHM_Administrator', 'Cmedit_Administrator'], 'NUM_KPIS_01': 8,
                          'UNSUPPORTED_KPIS': [['Added_E-RAB_Establishment_Success_Rate_per_QCI'],
                                               ['Average_DL_MAC_DRB_Latency_per_QCI'],
                                               ['Average_DL_PDCP_UE_DRB_Throughput_per_QCI'],
                                               ['Average_DL_UE_PDCP_DRB_Latency_per_QCI'],
                                               ['E-RAB_Retainability_Percentage_Lost_per_QCI'],
                                               ['E-RAB_Retainability_Session_Time_Normalized_per_QCI_Loss_Rate'],
                                               ['Initial_E-RAB_Establishment_Success_Rate_per_QCI'],
                                               ['UL_Packet_Loss_Rate_per_QCI'],
                                               ['Added_E-RAB_Establishment_Success_Rate_for_Emergency_Calls'],
                                               ['E-RAB_Retainability_Percentage_Lost_for_Emergency_Calls'],
                                               ['Initial_E-RAB_Establishment_Success_Rate_for_Emergency_Calls'],
                                               ['Average_DRB_Latency_DRX_Active-State_UL_In-Sync'],
                                               ['Average_DRB_Latency_with_DRX_Active-State_UL_Out-of-Sync'],
                                               ['Average_DRB_Latency_with_DRX_Inactive-State_UL_In-Sync'],
                                               ['Average_UL_UE_Throughput_per_LCG'],
                                               ['Handover_Failure'],
                                               ['Downlink_PRB_Utilization'],
                                               ['PDCCH_Utilization'],
                                               ['Uplink_PRB_Utilization']]},
            'NHM_14': {NUM_NODES: {NODES.ERBS: -1, NODES.RADIONODE: -1}, 'OPERATOR_ROLE': ["NHM_Administrator"],
                       'NUM_OPERATORS': 1, 'NUMBER_OF_KPIS': 25,
                       NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB']}},
                       'REPORTING_OBJECT': ['EUtranCellFDD', 'EUtranCellTDD'],
                       'SUPPORTED_TYPES_CUSTOM_CELL_LEVEL_KPI': ['ERBS', 'RadioNode']}},
        "nhm_rest_nbi": {
            'NHM_REST_NBI_01': {},
            'NHM_REST_NBI_02': {},
            'NHM_REST_NBI_03': {},
            'NHM_REST_NBI_04': {},
            'NHM_REST_NBI_05': {},
            'NHM_REST_NBI_06': {},
            'NHM_REST_NBI_07': {},
            'NHM_REST_NBI_08': {},
            'NHM_REST_NBI_SETUP': {}
        },
        "nodecli": {},
        "nodesec": {
            'NODESEC_15': {TOTAL_NODES: 1000, SUPPORTED_NODE_TYPES: [NODES.RADIONODE, NODES.ERBS, NODES.RNC, NODES.RBS,
                                                                     NODES.MGW, NODES.DSC, NODES.EPG, NODES.MTAS,
                                                                     NODES.ROUTER6672, NODES.ROUTER6675,
                                                                     NODES.SGSN_MME],
                           NUM_USERS: 20, SCHEDULED_TIMES_STRINGS: ['08:00:00'], 'RUN_UNTIL': '18:00:00',
                           THREAD_QUEUE_TIMEOUT: 4 * 60 * 60, 'NODE_REQUEST_CREDENTIALS_TIME': 5},
            'NODESEC_16': {NUM_USERS: 1, "NUM_OF_NODES": 1000, USER_ROLES: ['ldaprenewer'],
                           "CAPABILITIES": {"ldap": ["update", "patch"], "cm_editor": ["read"]},
                           SCHEDULED_TIMES_STRINGS: ['05:00:00']},
            "NODESEC_17": {NUM_USERS: 1, USER_ROLES: ["proxycleanupper"],
                           "CAPABILITIES": {"nodesec_proxy": ["read", "update", "delete"]},
                           "INACTIVE_HOURS": 48, SCHEDULED_TIMES_STRINGS: ["22:30:00"], "SCHEDULE_SLEEP_DAYS": 2}
        },
        "npa": {
            'NPA_01': {NUM_USERS: 1, SCHEDULE_SLEEP: 60 * 60 * 24 * 7, 'NUMBER_OF_FLOWS': 5, 'NUMBER_OF_CELLS': 200,
                       USER_ROLES: ['Flowautomation_Operator', 'Cmedit_Operator', 'NHM_Operator', 'NHM_Administrator',
                                    'Nhc_Administrator', 'Shm_Administrator'],
                       'NODE_VERSION_FORMAT': ["20.Q1", "20.Q2", "20.Q3", "20.Q4", "21.Q1", "21.Q2", "21.Q3", "21.Q4"],
                       'CELL_TYPE': {'RadioNode': ['EUtranCellFDD', 'EUtranCellTDD']}, 'KPI_ADJUST': 2}
        },
        "nvs": {},
        "nas_outage": {},
        "ops": {
            'OPS_01': {'FILTERED_NODES_PER_HOST': 1, USER_ROLES: OPS_USER_ROLES + COM_ROLES, SUPPORTED_NODE_TYPES: [NODES.BSC],
                       TOTAL_NODES: 16, 'MAX_SESSION_COUNT_PER_NODE': 35,
                       SCHEDULED_TIMES_STRINGS: ["03:30:00", "09:30:00", "15:30:00", "21:30:00"], "SESSION_COUNT": 14,
                       THREAD_QUEUE_TIMEOUT: 2400, EXCLUDE_NODES_FROM: ["CELLMGT_15"]}
        },
        "migration": {},
        "parmgt": {
            'PARMGT_03': {NUM_USERS: 1, USER_ROLES: ["Parameter_Management_Administrator"], "NUMBER_OF_MOS": 15000,
                          SCHEDULED_TIMES_STRINGS: ["14:00:00"], SCHEDULED_DAYS: ["FRIDAY"]}
        },
        "plm": {
            'PLM_01': {NUM_USERS: 1, USER_ROLES: ["LinkManagement_Administrator", "LinkManagement_Operator",
                                                  "Cmedit_Administrator"], SCHEDULE_SLEEP: 60 * 60,
                       "NODE_TYPES": [NODES.SGSN_MME, NODES.RADIONODE, NODES.MINILINK_6352, NODES.ROUTER6672, NODES.ROUTER6675,
                                      NODES.MINI_LINK_669x],
                       'MAX_LINKS': 25000},
            'PLM_02': {NUM_USERS: 1, USER_ROLES: ["LinkManagement_Administrator", "LinkManagement_Operator",
                                                  "Cmedit_Administrator"], TOTAL_NODES: 20, SCHEDULE_SLEEP: 60 * 60,
                       SUPPORTED_NODE_TYPES: [NODES.MINI_LINK_669x]}
        },
        "pkiadmin": {},
        "pm_rest_nbi": {},
        "pm": {
            'PM_97': {},
            'PM_98': {},
            'PM_100': {},
            'PM_101': {}
        },
        "reparenting": {
            "REPARENTING_01": {},
            "REPARENTING_02": {},
            "REPARENTING_03": {},
            "REPARENTING_04": {},
            "REPARENTING_05": {},
            "REPARENTING_06": {},
            "REPARENTING_07": {},
            "REPARENTING_08": {},
            "REPARENTING_09": {},
            "REPARENTING_10": {},
            "REPARENTING_11": {},
            "REPARENTING_12": {}
        },
        "secui": {
            'SECUI_02': {'NUMBER_OF_USERS': 30, 'NUMBER_OF_ROLES': 5, SCHEDULE_SLEEP: 24 * 60 * 60},
            'SECUI_05': {NUM_USERS: 50, USER_ROLES: ["SECURITY_ADMIN"], 'CREATED_ROLE_COUNT': 6},
        },
        "sev": {
            'SEV_01': {NUM_USERS: 5, USER_ROLES: ["SEV_Administrator", "SEV_Operator"], NUM_NODES: {NODES.ESC: 5},
                       NODE_FILTER: {NODES.ESC: {"node_version": ["22.Q3"]}}, SCHEDULE_SLEEP: 60 * 15,
                       CHECK_NODE_SYNC: True},
            'SEV_02': {NUM_USERS: 5, USER_ROLES: ["SEV_Administrator", "SEV_Operator"], NUM_NODES: {NODES.ESC: 5},
                       SCHEDULE_SLEEP: 60 * 15}
        },
        "shm": {
            'SHM_04': {NUM_USERS: 1, USER_ROLES: ["Shm_Administrator", "Cmedit_Administrator"],
                       NUM_NODES: {NODES.ERBS: 1000}, SCHEDULED_TIMES_STRINGS: ["11:00:00"], 'TIMEOUT': 1800,
                       SCHEDULED_DAYS: ['WEDNESDAY']},
            'SHM_06': {NUM_USERS: 10, TOTAL_NODES: 10,
                       SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE, NODES.ROUTER6672, NODES.BSC],
                       SCHEDULE_SLEEP: 60 * 60, EXCLUDE_NODES_FROM: ['SHM_24', 'ASU_01', 'NPA_01'], "PIB_VALUES": {},
                       NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ["ENodeB"]}}, SKIP_SYNC_CHECK: False,
                       USER_ROLES: ["Shm_Administrator", "Cmedit_Administrator", "Ops_Operator", "WinFIOL_Operator",
                                    "Element_Manager_Operator", "FIELD_TECHNICIAN", "Scripting_Operator"] + COM_ROLES},
            'SHM_07': {NUM_USERS: 20, NUM_NODES: {NODES.ERBS: -1, NODES.RADIONODE: -1, NODES.MINI_LINK_Indoor: -1},
                       SCHEDULE_SLEEP: 3000,
                       USER_ROLES: ['Shm_Administrator', 'Network_Explorer_Administrator']},
            'SHM_23': {'NODES_PER_HOST': 100, NUM_NODES: {NODES.MINI_LINK_Indoor: 200}, MAX_NODES: 2,
                       SCHEDULED_TIMES_STRINGS: ["02:30:00"], "PIB_VALUES": {},
                       "SHM_JOB_SCHEDULED_TIME_STRINGS": ["03:00:00"]},
            'SHM_24': {'NODES_PER_HOST': 100, NUM_NODES: {NODES.MINI_LINK_Indoor: 200},
                       SCHEDULED_TIMES_STRINGS: ["06:30:00"],
                       EXCLUDE_NODES_FROM: ['SHM_06'], "MLTN_TIMEOUT": 90, NUM_USERS: 1,
                       USER_ROLES: ["Shm_Administrator", "Cmedit_Administrator"], SKIP_SYNC_CHECK: False,
                       SCHEDULED_DAYS: ['MONDAY'], 'MAX_NODES': 200, "SHM_JOB_SCHEDULED_TIME_STRINGS": ["07:00:00"],
                       "PKG_PIB_VALUES": {}},
            'SHM_31': {'NODES_PER_HOST': 84, NUM_NODES: {NODES.MINILINK_6352: -1}, "MAX_NODES_TO_ALLOCATE": 100,
                       SCHEDULED_TIMES_STRINGS: ["05:30:00"], NUM_USERS: 1, SCHEDULED_DAYS: ['TUESDAY'],
                       USER_ROLES: ["Shm_Administrator", "Cmedit_Administrator"], 'TIMEOUT': 1800,
                       'MAX_NODES': 100, "SHM_JOB_SCHEDULED_TIME_STRINGS": ["07:00:00"],
                       SKIP_SYNC_CHECK: False, "MINIMUM_ALLOWABLE_NODE_COUNT": 100, "PKG_PIB_VALUES": {}},
            'SHM_32': {'FILTERED_NODES_PER_HOST': 100, NUM_NODES: {NODES.MINILINK_6352: -1}, 'MAX_NODES': 100,
                       SCHEDULED_TIMES_STRINGS: ["02:00:00"], "SHM_JOB_SCHEDULED_TIME_STRINGS": ["02:30:00"],
                       'TIMEOUT': 1800, USER_ROLES: ["Shm_Administrator", "Cmedit_Administrator"], NUM_USERS: 1,
                       "MINIMUM_ALLOWABLE_NODE_COUNT": 100, "MAX_NODES_TO_ALLOCATE": 100, "PIB_VALUES": {}},
            'SHM_33': {'NODES_PER_HOST': 100, TOTAL_NODES: 200, SUPPORTED_NODE_TYPES: [NODES.ROUTER6672],
                       'MAX_NODES': 200, SCHEDULED_TIMES_STRINGS: ["06:30:00"], NUM_USERS: 1,
                       USER_ROLES: ["Shm_Administrator", "Cmedit_Administrator"],
                       SCHEDULED_DAYS: ['SUNDAY'], "SHM_JOB_SCHEDULED_TIME_STRINGS": ["07:00:00"],
                       SKIP_SYNC_CHECK: False, "PKG_PIB_VALUES": {}},
            'SHM_34': {'NODES_PER_HOST': 100, TOTAL_NODES: 200, MAX_NODES: 200,
                       SUPPORTED_NODE_TYPES: [NODES.ROUTER6672], "PIB_VALUES": {},
                       SCHEDULED_TIMES_STRINGS: ["23:00:00"], "SHM_JOB_SCHEDULED_TIME_STRINGS": ["23:30:00"]},
            'SHM_41': {'NODES_PER_HOST': 40, TOTAL_NODES: 200, MAX_NODES: 200,
                       SUPPORTED_NODE_TYPES: [NODES.ROUTER6675],
                       "PIB_VALUES": {"SMRS_Router6675_NoOf_BACKUP_FILES": "2"},
                       SCHEDULED_TIMES_STRINGS: ["23:00:00"], EXCLUDE_NODES_FROM: ['SHM_06'],
                       "SHM_JOB_SCHEDULED_TIME_STRINGS": ["23:30:00"]},
        },
        "top": {}
    }
}
