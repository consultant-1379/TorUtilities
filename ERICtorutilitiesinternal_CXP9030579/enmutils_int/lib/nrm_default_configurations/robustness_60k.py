from basic_network import (IMP_EXP_KEYS as IMP_EXP, USER_KEYS as USER, NODE_KEYS as NODE, TIME_KEYS as TIME,
                           TIMEOUT, LTE_CELL_CHECK, ERROR_HANDLING, CHECK_NODE_SYNC, NeTypesEnum as NODES, MAX_NODES)

from profile_cmds import (CMSYNC_AVC_BURST_MO_TYPE_SETTINGS)

SCHEDULED_DAYS, SCHEDULE_SLEEP, SCHEDULED_TIMES_STRINGS = TIME
NUM_USERS, USER_ROLES = USER
NUM_NODES, SUPPORTED_NODE_TYPES, TOTAL_NODES, EXCLUDE_NODES_FROM, NODE_FILTER = NODE
INTERFACE, FILETYPE, FLOW, IMPORT_TYPE, CREATE_DELETE_LIVE, CREATE_DELETE_CONFIG, UPDATE_LIVE, UPDATE_CONFIG = IMP_EXP

robustness_60k = {
    "robustness_60k": {
        "amos": {},
        "aid": {},
        "ap": {},
        "apt": {},
        "asr_l": {},
        "asr_n": {},
        "asu": {},
        "bur": {},
        "ca": {},
        'cbrs': {},
        "cellmgt": {},
        "cli_mon": {},
        "cmevents_nbi": {},
        "cmexport": {
            'CMEXPORT_01': {SCHEDULE_SLEEP: 60 * 60, 'FILETYPE': '3GPP', NUM_USERS: 1,
                            'ENM_NE_TYPES': [NODES.ERBS, NODES.RADIONODE, NODES.RBS], USER_ROLES: ['Cmedit_Operator'],
                            "MAX_RETENTION_TIME": "2", "RETENTION_ENABLED": "true"},
            'CMEXPORT_14': {SCHEDULED_TIMES_STRINGS: ["00:00:00", "01:00:00", "02:00:00", "03:00:00", "04:00:00",
                                                      "05:00:00", "06:00:00", "07:00:00", "08:00:00", "09:00:00",
                                                      "10:00:00", "11:00:00", "12:00:00", "13:00:00", "14:00:00",
                                                      "15:00:00", "16:00:00", "17:00:00", "18:00:00", "19:00:00",
                                                      "20:00:00", "21:00:00", "22:00:00", "23:00:00", ],
                            'FILETYPE': 'dynamic', NUM_USERS: 1, USER_ROLES: ['CM_REST_Administrator'],
                            INTERFACE: 'NBI',
                            "ENM_NE_TYPES": [NODES.ROUTER6274, NODES.ROUTER6672, NODES.ROUTER6675, NODES.FRONTHAUL_6020,
                                             NODES.FRONTHAUL_6080,
                                             NODES.MINI_LINK_Indoor, NODES.CISCO_ASR900, NODES.MINILINK_6352,
                                             NODES.MINI_LINK_669x, NODES.JUNIPER_MX],
                            "MAX_RETENTION_TIME": "2", "RETENTION_ENABLED": "true"}
        },
        "cmimport": {
            'CMIMPORT_13': {'MO_VALUES': {'UtranCellRelation': 5, 'EUtranCellRelation': 5},
                            'MOS_ATTRS': {'UtranCellRelation': ['isRemoveAllowed'],
                                          'EUtranCellRelation': ['isRemoveAllowed']},
                            USER_ROLES: ['Cmedit_Administrator', 'CM_REST_Administrator'], TOTAL_NODES: 10,
                            SUPPORTED_NODE_TYPES: [NODES.ERBS, NODES.RADIONODE, NODES.RBS], TIMEOUT: 30 * 60,
                            NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB', 'GNodeB']}},
                            'BATCH_MO_SIZE': 50, 'FILETYPE': '3GPP', 'TIMES_PER_DAY': 400,
                            EXCLUDE_NODES_FROM: ['CMSYNC_01', 'CMSYNC_02', 'CMSYNC_04', 'CMSYNC_06'],
                            ERROR_HANDLING: 'continue-on-error-node',
                            "MAPPING_FOR_5G_NODE_MO": {'UtranCellRelation': {'NRCellRelation': 5},
                                                       'EUtranCellRelation': {'EUtranCellRelation': 5}},
                            "MAPPING_FOR_5G_NODE_ATTRS": {'NRCellRelation': ['isHoAllowed'],
                                                          'EUtranCellRelation': ['isRemoveAllowed']},
                            'MOS_DEFAULT': {'UtranCellRelation': ('isRemoveAllowed', 'true'),
                                            'EUtranCellRelation': ('isRemoveAllowed', 'true'),
                                            'NRCellRelation': ('isHoAllowed', 'true')},
                            'MOS_MODIFY': {'UtranCellRelation': ('isRemoveAllowed', 'false'),
                                           'EUtranCellRelation': ('isRemoveAllowed', 'false'),
                                           'NRCellRelation': ('isHoAllowed', 'false')},
                            "POSTGRES_RETENTION_TIME_DAYS": '30'}
        },
        "cmsync": {
            'CMSYNC_23': {TOTAL_NODES: 50, NUM_NODES: {NODES.ERBS: 25, NODES.RADIONODE: -1},
                          'NOTIFICATION_PER_SECOND': 8000,
                          NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ['ENodeB']}},
                          SCHEDULE_SLEEP: 60 * 60 * 6, 'BURST_DURATION': 900, LTE_CELL_CHECK: True,
                          'NOTIFICATION_INFO': (CMSYNC_AVC_BURST_MO_TYPE_SETTINGS.get("ERBS")[:1] +
                                                CMSYNC_AVC_BURST_MO_TYPE_SETTINGS.get("RadioNode")[:1]),
                          'NODES_PER_HOST': 40, EXCLUDE_NODES_FROM: ["CMIMPORT_03", "TOP_01", "CMSYNC_02", "CMSYNC_04",
                                                                     "CMSYNC_06"]},
            'CMSYNC_25': {NUM_NODES: {NODES.RADIONODE: -1}, SCHEDULED_DAYS: ["SUNDAY"],
                          SCHEDULED_TIMES_STRINGS: ["20:00:00"],
                          NODE_FILTER: {NODES.RADIONODE: {"managed_element_type": ["ENodeB", "GNodeB", "NodeB"]}}},
            'CMSYNC_33': {TOTAL_NODES: 1000, SUPPORTED_NODE_TYPES: [NODES.ROUTER6672, NODES.ROUTER6675],
                          SCHEDULED_TIMES_STRINGS: ["17:30:00"]},
            'CMSYNC_34': {TOTAL_NODES: 1000, SUPPORTED_NODE_TYPES: [NODES.MINI_LINK_669x, NODES.MINI_LINK_Indoor],
                          SCHEDULED_TIMES_STRINGS: ["01:30:00"]},
            'CMSYNC_43': {NUM_NODES: {NODES.PCG: -1, NODES.EPG_OI: -1, NODES.CCDM: -1},
                          SCHEDULED_TIMES_STRINGS: ["04:05:00"], SCHEDULED_DAYS: ["TUESDAY"]}
        },
        "configuration_template": {},
        "doc": {},
        "dynamic_crud": {},
        "ebsl": {},
        "ebsn": {},
        "ebsm": {},
        "enmcli": {},
        "esm": {},
        "esm_nbi": {},
        "fm": {},
        "fmx": {},
        "ftpes": {},
        "fan": {},
        "fs_quotas": {},
        "geo_r": {},
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
        "neo4j": {
            'NEO4J_01': {SCHEDULED_DAYS: ["MONDAY"], SCHEDULED_TIMES_STRINGS: ["09:00:00"], "SLEEP_TIME": 5 * 60 * 60},
            'NEO4J_02': {SCHEDULED_DAYS: ["MONDAY"], SCHEDULED_TIMES_STRINGS: ["09:00:00"], "SLEEP_TIME": 6 * 60 * 60}
        },
        "nas_outage": {
            'NAS_OUTAGE_01': {"SLEEP_TIME": 8 * 60 * 60},
            'NAS_OUTAGE_02': {"SLEEP_TIME": 60 * 60, SCHEDULED_DAYS: ['THURSDAY'],
                              SCHEDULED_TIMES_STRINGS: ['11:30:00', '16:00:00']}
        },
        "netex": {},
        "netview": {},
        "network": {
            'NETWORK_01': {SCHEDULE_SLEEP: 7200, "TOTAL_RANDOM_NODES": 100},
            'NETWORK_02': {SCHEDULE_SLEEP: 7200, "TOTAL_RANDOM_SIMS": 5},
            'NETWORK_03': {SCHEDULE_SLEEP: 7200, NUM_NODES: {NODES.MINI_LINK_669x: -1, NODES.MINI_LINK_Indoor: -1}}
        },
        "nhc": {},
        "nhm": {},
        "nhm_rest_nbi": {},
        "nodecli": {},
        "nodesec": {},
        "npa": {},
        "nvs": {},
        "migration": {},
        "ops": {},
        "parmgt": {},
        "plm": {},
        "pkiadmin": {},
        "pm_rest_nbi": {},
        "pm": {
            'PM_26': {NUM_USERS: 1, USER_ROLES: ["PM_NBI_Operator", "Scripting_Operator", "ADMINISTRATOR"],
                      'ROP_INTERVAL': 15, 'SFTP_FETCH_TIME_IN_MINS': 13, 'N_SFTP_THREADS': 10,
                      SCHEDULED_TIMES_STRINGS: ["{0}:{1}:00".format(hour, minute) for hour in range(00, 24)
                                                for minute in range(0, 60, 15)],
                      'DATA_TYPES': ['PM_STATISTICAL', 'PM_STATISTICAL_1MIN', 'PM_STATISTICAL_5MIN',
                                     'PM_STATISTICAL_30MIN', 'PM_STATISTICAL_1HOUR', 'PM_STATISTICAL_12HOUR',
                                     'PM_STATISTICAL_24HOUR', 'PM_CELLTRACE', 'PM_CELLTRACE_CUCP', 'PM_CELLTRACE_CUUP',
                                     'PM_CELLTRACE_DU', 'PM_UETRACE', 'PM_UETRACE_CUCP', 'PM_UETRACE_CUUP',
                                     'PM_UETRACE_DU', 'PM_EBS', 'PM_EBM', 'PM_CTUM', 'PM_UETR', 'PM_CTR', 'PM_GPEH',
                                     'PM_CELLTRAFFIC', 'PM_EBSM_3GPP', 'PM_EBSM_ENIQ', 'PM_EBSL', 'PM_EBSN_DU',
                                     'PM_EBSN_CUCP', 'PM_EBSN_CUUP', 'PM_BSC_PERFORMANCE_EVENT',
                                     'PM_BSC_PERFORMANCE_CTRL', 'PM_BSC_RTT', 'PM_BSC_PERFORMANCE_EVENT_STATISTICS',
                                     'PM_BSC_PERFORMANCE_EVENT_RAW', 'PM_BSC_PERFORMANCE_EVENT_MONITORS',
                                     'TOPOLOGY_*'], "DATA_TYPES_UPDATE_TIME": "00:00"},
            'PM_28': {},
            'PM_101': {'CELLTRACE_AND_EBM_RETENTION':
                       {"pmicCelltraceFileRetentionPeriodInMinutes": [360, 300, 240],
                        "pmicEbmFileRetentionPeriodInMinutes": [300, 240, 180]}, SCHEDULED_TIMES_STRINGS: ["00:00:00"],
                       "SCHEDULE_SLEEP_DAYS": 15}
        },
        "reparenting": {},
        "secui": {},
        "sev": {
            'SEV_01': {NUM_USERS: 5, USER_ROLES: ["SEV_Administrator", "SEV_Operator"], NUM_NODES: {NODES.ESC: 5},
                       NODE_FILTER: {NODES.ESC: {"node_version": ["22.Q3"]}}, SCHEDULE_SLEEP: 60 * 15,
                       CHECK_NODE_SYNC: True},
            'SEV_02': {NUM_USERS: 5, USER_ROLES: ["SEV_Administrator", "SEV_Operator"], NUM_NODES: {NODES.ESC: 5},
                       SCHEDULE_SLEEP: 60 * 15}
        },
        "shm": {
            'SHM_46': {TOTAL_NODES: 5000, SCHEDULED_TIMES_STRINGS: ["06:00:00", "19:45:00"],
                       NUM_NODES: {NODES.RADIONODE: 5000},
                       NODE_FILTER: {NODES.RADIONODE: {'managed_element_type': ["ENodeB", "GNodeB", "NodeB", "Bts"]}},
                       "SHM_JOB_SCHEDULED_TIME_STRINGS": ["06:30:00", "20:15:00"], 'NUM_NODES_PER_BATCH': 5000, MAX_NODES: 5000},
        },
        "top": {}
    }
}
