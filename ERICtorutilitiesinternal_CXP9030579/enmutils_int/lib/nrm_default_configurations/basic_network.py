from enum import Enum, unique

SUPPORTED, PHYSICAL, CLOUD, CLOUD_NATIVE, INTRUSIVE, EXCLUSIVE, FOUNDATION, RETAIN_NODES_AFTER_COMPLETED = (
    'SUPPORTED', 'PHYSICAL_SUPPORTED', 'CLOUD_SUPPORTED', 'CLOUD_NATIVE_SUPPORTED', 'INTRUSIVE', 'EXCLUSIVE', 'FOUNDATION',
    'RETAIN_NODES_AFTER_COMPLETED')
NOTE = 'NOTE'
PRIORITY = 'PRIORITY'
UPDATE = 'UPDATE_VERSION'
MANUAL = 'USE CASE MUST BE EXECUTED MANUALLY'
NO_PLAN_SUPPORT = "No plan to set supported ({})"
OPTIONAL_UNSUPPORTED = "Optional Profile, to be started manually - {0}".format(NO_PLAN_SUPPORT)
CENM = "Support for cENM ({})"
CORBA_CENM = "CORBA Support for cENM ({})"
KTT = 'Owned by KTT'
DEPENDENT = "DEPENDENT_PROFILES"

# User Keys
NUM_USERS = 'NUM_USERS'
USER_ROLES = 'USER_ROLES'
USER_KEYS = [NUM_USERS, USER_ROLES]
# Node Keys
NUM_NODES = 'NUM_NODES'
SUPPORTED_NODE_TYPES = 'SUPPORTED_NODE_TYPES'
TOTAL_NODES = 'TOTAL_NODES'
EXCLUDE_NODES_FROM = 'EXCLUDE_NODES_FROM'
NODE_FILTER = 'NODE_FILTER'
NODE_KEYS = [NUM_NODES, SUPPORTED_NODE_TYPES, TOTAL_NODES, EXCLUDE_NODES_FROM, NODE_FILTER]
NODE_TYPES = ['ERBS', 'RadioNode', 'MGW', 'EPG', 'VEPG', 'RNC', 'RBS', 'SIU02', 'TCU02', 'MTAS', 'BSC',
              'MINI-LINK-6352', 'DSC', 'MSC-DB-BSP', 'MSC-BC-BSP', 'MSC-BC-IS', 'ESC', 'SBG-IS', 'Router6672',
              'Router6274', 'ERS-SupportNode', 'MINI-LINK-669x', 'Router6675', 'FRONTHAUL-6020', 'JUNIPER-MX',
              "SGSN-MME", "MINI-LINK-Indoor", "CISCO-ASR900", "FRONTHAUL-6080", "EPG-OI", "CCDM", "PCG", "SCU", "CUDB",
              'Shared-CNF']


@unique
class NeTypesEnum(str, Enum):
    (ERBS, RADIONODE, MGW, EPG, VEPG, RNC, RBS, SIU02, TCU02, MTAS, BSC, MINILINK_6352, DSC, MSC_DB_BSP, MSC_BC_BSP,
     MSC_BC_IS, ESC, SBG_IS, ROUTER6672, ROUTER6274, ERS_SUPPORTNODE, MINI_LINK_669x, ROUTER6675, FRONTHAUL_6020,
     JUNIPER_MX, SGSN_MME, MINI_LINK_Indoor, CISCO_ASR900, FRONTHAUL_6080, EPG_OI, CCDM, PCG, SCU, CUDB, Shared_CNF) = NODE_TYPES

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.__str__()


# Scheduling Keys
SCHEDULED_DAYS = 'SCHEDULED_DAYS'
SCHEDULE_SLEEP = 'SCHEDULE_SLEEP'
SCHEDULED_TIMES_STRINGS = 'SCHEDULED_TIMES_STRINGS'
TIME_KEYS = [SCHEDULED_DAYS, SCHEDULE_SLEEP, SCHEDULED_TIMES_STRINGS]
# Import/Export Keys
INTERFACE = 'INTERFACE'
FILETYPE = 'FILETYPE'
FLOW = 'FLOW'
IMPORT_TYPE = 'IMPORT_TYPE'
CREATE_DELETE_LIVE = 'CreateDeleteLive'
CREATE_DELETE_CONFIG = 'CreateDeleteConfig'
UPDATE_LIVE = 'UpdateLive'
UPDATE_CONFIG = 'UpdateFromConfig'
IMP_EXP_KEYS = [INTERFACE, FILETYPE, FLOW, IMPORT_TYPE, CREATE_DELETE_LIVE, CREATE_DELETE_CONFIG, UPDATE_LIVE,
                UPDATE_CONFIG]
NUM_EVENTS, LARGE_BSC_ONLY, SMALL_BSC_ONLY = "NUM_EVENTS", "LARGE_BSC_ONLY", "SMALL_BSC_ONLY",
MAX_NODES, ERROR_HANDLING = "MAX_NODES", "ERROR_HANDLING"
MAX_NODES_TO_ALLOCATE = "MAX_NODES_TO_ALLOCATE"
THREAD_QUEUE_TIMEOUT, SKIP_SYNC_CHECK, CHECK_NODE_SYNC = "THREAD_QUEUE_TIMEOUT", "SKIP_SYNC_CHECK", "CHECK_NODE_SYNC"
STANDARD, CELL_TYPE, NUM_CELLS_PER_USER, GSM, GERANCELL = ("STANDARD", "CELL_TYPE", "NUM_CELLS_PER_USER", "GSM",
                                                           "GeranCell")
FDD_ONLY, ATTEMPT_RECOVERY = "FDD_ONLY", "ATTEMPT_RECOVERY"
TIMEOUT = "TIMEOUT"
NUM_ITERATIONS = "NUM_ITERATIONS"
IGNORE_SOA = "IGNORE_SOA"  # Flag for use by any profile so it will avoid using Service-Oriented Architecture

APT_01_NOTE = ('https://eteamspace.internal.ericsson.com/display/ERSD/Starting+APT_01'
               '+profiles+for+KPI+nodes')
NCM_MEF_LCM_01_NOTE = ('https://eteamspace.internal.ericsson.com/pages/viewpage.action?pageId=2057399300')
NCM_L3_VPN_01_NOTE = ('{0} & {1}'.format(NCM_MEF_LCM_01_NOTE, 'https://eteamspace.internal.ericsson.com/display/BTT/How+to+create+L3+VPN+Service+on+NCM'))
HA_01_NOTE = "Dummy profile to ring-fence nodes for the HA testware."
PM_16_NOTE = "Requires MME with mobileCountryCode & MobileNetworkCode attributes set for PLMN MO"
PM_20_NOTE = ("Profile will only create EBM Subscription if the ENM deployment does NOT contain an "
              "Events Cluster/value_pack_ebs_m Tag")
AID_NOTE = "Unsupported till we have NRM with node version higher than or equal to 19.Q2 ({}, {}, {})".format(
    "RTD-12080", "HX27475", "RTD-12075")
CBRS_SETUP_NOTE = OPTIONAL_UNSUPPORTED.format("Requires manual configuration of SAS")
CLI_MON_01_NOTE = "Applicable to Physical ENM only"

AMOS_USER_ROLES = ['ADMINISTRATOR', 'Amos_Administrator', 'BscApplicationAdministrator',
                   'Bts_Application_Administrator',
                   'ENodeB_Application_Administrator', 'ENodeB_Application_SecurityAdministrator',
                   'ENodeB_Application_User', 'EricssonSupport', 'NodeB_Application_Administrator',
                   'NodeB_Application_User', 'RBS_Application_Operator', 'Support_Application_Administrator',
                   'SystemAdministrator', 'SystemReadOnly', 'SystemSecurityAdministrator', 'Amos_Operator']
GEO_USER_ROLES = ["Cmedit_Administrator", "FM_Administrator", "Lcm_Administrator", "Topology_Browser_Administrator",
                  "Network_Explorer_Operator", "PKI_Administrator", "Scripting_Operator", "FMX_Administrator",
                  "NodeSecurity_Administrator", "CM_REST_Administrator", "CM_REST_Operator", "SECURITY_ADMIN",
                  "PM_Operator", "Shm_Administrator", "Network_Explorer_Administrator",
                  "FlexCounterManagement_Administrator", "geo_r_role"]
COM_ROLES = ["SystemAdministrator", "SystemSecurityAdministrator", "BscApplicationAdministrator"]
OPS_USER_ROLES = ["Ops_Operator", "WinFIOL_Operator", "Element_Manager_Operator", "Scripting_Operator"]
SECUI_01_USER_ROLES = [u'Target_Group_Administrator', u'Topology_Browser_Administrator', u'FM_Administrator',
                       u'FM_BNSINBI_Operator', u'Network_Explorer_Administrator', u'Nodediscovery_Administrator',
                       u'Lcm_Administrator', u'PM_Operator', u'Cmedit_Administrator', u'Autoprovisioning_Administrator',
                       u'Autoprovisioning_Operator', u'Shm_Administrator']

# These are customised rule modules. Needs to be imported, loaded, activated. Order in the list is important
NSX_RULEMODULES = ['NSX_Configuration', 'NSX_Hard_filter']
CNX_RULEMODULES = ['CN_External_Alarm', 'CN_Signalling_Disturbances']
GRX_RULEMODULES = ['GRX_MO_FAULT', 'GRX_BTS_External']
FMX_RULEMODULES = 'FMX_RULEMODULES'
RENAMED_PROFILES = {"NHM_01_02": "NHM_SETUP"}
LTE_CELL_CHECK = "LTE_CELL_CHECK"


basic = {
    "basic": {
        "aid": {
            'AID_SETUP': {UPDATE: 12, FOUNDATION: False, SUPPORTED: False, NOTE: AID_NOTE, PRIORITY: 1},
            'AID_01': {UPDATE: 23, SUPPORTED: False, NOTE: AID_NOTE, PRIORITY: 2},
            'AID_02': {UPDATE: 32, SUPPORTED: False, NOTE: AID_NOTE, PRIORITY: 2},
            'AID_03': {UPDATE: 30, SUPPORTED: False, NOTE: AID_NOTE, PRIORITY: 2},
            'AID_04': {UPDATE: 19, SUPPORTED: False, NOTE: AID_NOTE, PRIORITY: 2}
        },
        "amos": {
            'AMOS_01': {UPDATE: 82, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'AMOS_02': {UPDATE: 80, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'AMOS_03': {UPDATE: 81, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'AMOS_04': {UPDATE: 81, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'AMOS_05': {UPDATE: 77, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'AMOS_08': {UPDATE: 42, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'AMOS_09': {UPDATE: 27, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1}
        },
        "ap": {
            'AP_SETUP': {UPDATE: 30, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2, FOUNDATION: True},
            'AP_01': {UPDATE: 104, SUPPORTED: True, EXCLUSIVE: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'AP_11': {UPDATE: 12, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'AP_12': {UPDATE: 13, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'AP_13': {UPDATE: 16, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'AP_14': {UPDATE: 15, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'AP_15': {UPDATE: 13, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'AP_16': {UPDATE: 17, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "apt": {
            'APT_01': {UPDATE: 13, SUPPORTED: True, CLOUD_NATIVE: True, EXCLUSIVE: True, NOTE: APT_01_NOTE, PRIORITY: 1},
        },
        "asr_l": {
            'ASR_L_01': {UPDATE: 2, SUPPORTED: True, CLOUD: False, NOTE: CENM.format('RTD-15937'), PRIORITY: 2}
        },
        "asr_n": {
            'ASR_N_01': {UPDATE: 2, SUPPORTED: True, CLOUD: False, NOTE: CENM.format('RTD-16048'), PRIORITY: 2}
        },
        "asu": {
            'ASU_01': {UPDATE: 54, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
        },
        "bur": {
            'BUR_02': {UPDATE: 0, SUPPORTED: False, NOTE: MANUAL, PRIORITY: 'M'}
        },
        "ca": {
            'CA_01': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
        },
        "cbrs": {
            'CBRS_SETUP': {UPDATE: 5, SUPPORTED: False, CLOUD_NATIVE: True, NOTE: CBRS_SETUP_NOTE,
                           PRIORITY: 2, RETAIN_NODES_AFTER_COMPLETED: True}
        },
        "cellmgt": {
            'CELLMGT_01': {UPDATE: 38, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_02': {UPDATE: 39, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_03': {UPDATE: 15, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_05': {UPDATE: 13, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_07': {UPDATE: 28, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_08': {UPDATE: 22, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_09': {UPDATE: 34, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_10': {UPDATE: 28, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_11': {UPDATE: 27, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_12': {UPDATE: 19, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_13': {UPDATE: 28, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_14': {UPDATE: 25, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CELLMGT_15': {UPDATE: 25, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True}
        },
        "cli_mon": {
            'CLI_MON_01': {UPDATE: 24, SUPPORTED: True, CLOUD: False, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CLI_MON_03': {UPDATE: 14, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True}
        },
        "cmevents_nbi": {
            'CMEVENTS_NBI_01': {UPDATE: 28, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEVENTS_NBI_02': {UPDATE: 3, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True}
        },
        "cmexport": {
            'CMEXPORT_01': {UPDATE: 35, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMEXPORT_02': {UPDATE: 31, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_03': {UPDATE: 31, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMEXPORT_05': {UPDATE: 32, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_07': {UPDATE: 28, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMEXPORT_08': {UPDATE: 38, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_11': {UPDATE: 53, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_12': {UPDATE: 31, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_13': {UPDATE: 31, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_14': {UPDATE: 40, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMEXPORT_16': {UPDATE: 24, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_17': {UPDATE: 31, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_18': {UPDATE: 20, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_19': {UPDATE: 35, SUPPORTED: True, NOTE: CENM.format('RTD-12743'), PRIORITY: 2},
            'CMEXPORT_20': {UPDATE: 24, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_21': {UPDATE: 17, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_22': {UPDATE: 18, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_23': {UPDATE: 11, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_25': {UPDATE: 9, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_26': {UPDATE: 5, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMEXPORT_27': {UPDATE: 0, SUPPORTED: False, NOTE: 'ENMRTD-25274', PRIORITY: 2, CLOUD_NATIVE: False}
        },
        "cmimport": {
            'CMIMPORT_01': {UPDATE: 50, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMIMPORT_02': {UPDATE: 75, SUPPORTED: True, EXCLUSIVE: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMIMPORT_03': {UPDATE: 58, SUPPORTED: True, NOTE: '', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMIMPORT_04': {UPDATE: 62, SUPPORTED: True, EXCLUSIVE: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMIMPORT_05': {UPDATE: 73, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMIMPORT_08': {UPDATE: 54, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMIMPORT_10': {UPDATE: 58, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMIMPORT_11': {UPDATE: 55, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMIMPORT_12': {UPDATE: 50, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_13': {UPDATE: 51, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_14': {UPDATE: 44, SUPPORTED: True, EXCLUSIVE: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_15': {UPDATE: 27, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_16': {UPDATE: 47, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_17': {UPDATE: 46, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_18': {UPDATE: 53, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_19': {UPDATE: 57, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_20': {UPDATE: 45, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_21': {UPDATE: 49, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_22': {UPDATE: 44, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_23': {UPDATE: 13, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_24': {UPDATE: 6, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_25': {UPDATE: 11, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_26': {UPDATE: 9, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_27': {UPDATE: 3, SUPPORTED: True, NOTE: CENM.format('RTD-15941'), PRIORITY: 2},
            'CMIMPORT_28': {UPDATE: 2, SUPPORTED: True, CLOUD: False, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_29': {UPDATE: 3, SUPPORTED: True, CLOUD: False, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_30': {UPDATE: 3, SUPPORTED: True, CLOUD: False, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_31': {UPDATE: 6, SUPPORTED: True, CLOUD: False, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_32': {UPDATE: 6, SUPPORTED: True, CLOUD: False, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_33': {UPDATE: 6, SUPPORTED: True, CLOUD: False, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMIMPORT_34': {UPDATE: 0, SUPPORTED: False, CLOUD: False, NOTE: 'ENMRTD-25326', PRIORITY: 2, CLOUD_NATIVE: False},
            'CMIMPORT_35': {UPDATE: 0, SUPPORTED: False, CLOUD: False, NOTE: 'ENMRTD-25607', PRIORITY: 2, CLOUD_NATIVE: False}
        },
        "cmsync": {
            'CMSYNC_SETUP': {UPDATE: 55, FOUNDATION: True, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMSYNC_01': {UPDATE: 72, SUPPORTED: True, NOTE: "-", PRIORITY: 1, CLOUD_NATIVE: True},
            'CMSYNC_02': {UPDATE: 106, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMSYNC_04': {UPDATE: 91, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMSYNC_06': {UPDATE: 93, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},

            'CMSYNC_11': {UPDATE: 33, SUPPORTED: False, NOTE: '{0}. RTD-17599'.format(KTT), PRIORITY: 'KTT',
                          CLOUD_NATIVE: True},
            'CMSYNC_15': {UPDATE: 37, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'CMSYNC_19': {UPDATE: 25, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_20': {UPDATE: 24, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_21': {UPDATE: 0, SUPPORTED: False, NOTE: KTT, PRIORITY: 'KTT'},
            'CMSYNC_22': {UPDATE: 0, SUPPORTED: False, NOTE: KTT, PRIORITY: 'KTT'},
            'CMSYNC_23': {UPDATE: 20, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_24': {UPDATE: 12, SUPPORTED: INTRUSIVE, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: INTRUSIVE},
            'CMSYNC_25': {UPDATE: 25, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_26': {UPDATE: 20, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_27': {UPDATE: 0, SUPPORTED: False, NOTE: KTT, PRIORITY: 'KTT'},
            'CMSYNC_28': {UPDATE: 23, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_29': {UPDATE: 28, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_30': {UPDATE: 18, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_32': {UPDATE: 25, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_33': {UPDATE: 14, SUPPORTED: INTRUSIVE, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: INTRUSIVE},
            'CMSYNC_34': {UPDATE: 12, SUPPORTED: INTRUSIVE, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: INTRUSIVE},
            'CMSYNC_35': {UPDATE: 20, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_37': {UPDATE: 16, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_38': {UPDATE: 15, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_39': {UPDATE: 4, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_40': {UPDATE: 5, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_41': {UPDATE: 5, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_42': {UPDATE: 5, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'CMSYNC_43': {UPDATE: 1, SUPPORTED: INTRUSIVE, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: INTRUSIVE},
            'CMSYNC_44': {UPDATE: 3, SUPPORTED: True, CLOUD: False, PHYSICAL: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'CMSYNC_45': {UPDATE: 0, SUPPORTED: False, CLOUD: False, NOTE: 'ENMRTD-25608', PRIORITY: 2}
        },
        "configuration_template": {},
        "doc": {
            'DOC_01': {UPDATE: 23, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "dynamic_crud": {
            'DYNAMIC_CRUD_01': {UPDATE: 2, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'DYNAMIC_CRUD_02': {UPDATE: 3, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'DYNAMIC_CRUD_03': {UPDATE: 3, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'DYNAMIC_CRUD_04': {UPDATE: 2, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'DYNAMIC_CRUD_05': {UPDATE: 2, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "ebsl": {
            'EBSL_05': {UPDATE: 18, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'EBSL_06': {UPDATE: 15, SUPPORTED: True, CLOUD: False, NOTE: CENM.format("RTD-15434"), PRIORITY: 2}
        },
        "ebsn": {
            'EBSN_01': {UPDATE: 13, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'EBSN_03': {UPDATE: 5, SUPPORTED: True, CLOUD: False, NOTE: CENM.format("RTD-15434"), PRIORITY: 2},
            'EBSN_04': {UPDATE: 17, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'EBSN_05': {UPDATE: 2, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: False, NOTE: CENM.format("RTD-22618"), PRIORITY: 2},
        },
        "ebsm": {
            'EBSM_04': {UPDATE: 16, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "em": {
            'EM_01': {UPDATE: 2, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "enmcli": {
            'ENMCLI_01': {UPDATE: 32, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'ENMCLI_02': {UPDATE: 40, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'ENMCLI_03': {UPDATE: 67, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'ENMCLI_04': {UPDATE: 5, SUPPORTED: False, NOTE: KTT, PRIORITY: 'KTT'},
            'ENMCLI_05': {UPDATE: 16, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'ENMCLI_06': {UPDATE: 14, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'ENMCLI_07': {UPDATE: 20, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'ENMCLI_08': {UPDATE: 8, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'ENMCLI_09': {UPDATE: 0, SUPPORTED: False, CLOUD_NATIVE: False, NOTE: 'ENMRTD-25422', PRIORITY: 2},
            'ENMCLI_10': {UPDATE: 0, SUPPORTED: False, CLOUD_NATIVE: False, NOTE: 'ENMRTD-25461', PRIORITY: 2},
        },
        "esm": {
            'ESM_01': {UPDATE: 32, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'ESM_02': {UPDATE: 0, SUPPORTED: False, NOTE: MANUAL, PRIORITY: 'M'}
        },
        "esm_nbi": {
            'ESM_NBI_01': {UPDATE: 1, SUPPORTED: True, PHYSICAL: False, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "fm": {
            'FM_0506': {UPDATE: 45, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'FM_01': {UPDATE: 85, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'FM_02': {UPDATE: 85, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'FM_03': {UPDATE: 85, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'FM_08': {UPDATE: 28, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_09': {UPDATE: 26, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_10': {UPDATE: 25, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_11': {UPDATE: 15, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_12': {UPDATE: 60, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: CORBA_CENM.format("TORF-516296"), PRIORITY: 1},
            'FM_14': {UPDATE: 26, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_15': {UPDATE: 27, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_17': {UPDATE: 21, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_20': {UPDATE: 20, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_21': {UPDATE: 22, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_23': {UPDATE: 1, SUPPORTED: False, NOTE: KTT, PRIORITY: 'KTT'},
            'FM_24': {UPDATE: 1, SUPPORTED: False, NOTE: KTT, PRIORITY: 'KTT'},
            'FM_25': {UPDATE: 32, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_26': {UPDATE: 23, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_27': {UPDATE: 9, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'FM_28': {UPDATE: 1, SUPPORTED: False, NOTE: KTT, PRIORITY: 'KTT'},
            'FM_29': {UPDATE: 1, SUPPORTED: False, NOTE: KTT, PRIORITY: 'KTT'},
            'FM_31': {UPDATE: 4, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'FM_32': {UPDATE: 11, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2}
        },
        "fmx": {
            'FMX_01': {UPDATE: 35, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'FMX_05': {UPDATE: 40, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "ftpes": {
            'FTPES_01': {UPDATE: 17, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "fan": {
            'FAN_01': {UPDATE: 1, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, PHYSICAL: False, NOTE: "ENMRTD-23897", PRIORITY: 2},
            'FAN_02': {UPDATE: 1, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, PHYSICAL: False, NOTE: "ENMRTD-23897", PRIORITY: 2},
            'FAN_03': {UPDATE: 1, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, PHYSICAL: False, NOTE: "ENMRTD-23897", PRIORITY: 2},
            'FAN_04': {UPDATE: 1, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, PHYSICAL: False, NOTE: "ENMRTD-23897", PRIORITY: 2},
            'FAN_11': {UPDATE: 1, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, PHYSICAL: False, NOTE: 'ENMRTD-20787', PRIORITY: 2},
            'FAN_12': {UPDATE: 5, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, PHYSICAL: False, NOTE: '-', PRIORITY: 2},
            'FAN_13': {UPDATE: 1, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, PHYSICAL: False, NOTE: 'ENMRTD-20789', PRIORITY: 2},
            'FAN_14': {UPDATE: 1, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, PHYSICAL: False, NOTE: 'ENMRTD-20790', PRIORITY: 2}
        },
        "fs_quotas": {
            'FS_QUOTAS_01': {UPDATE: 2, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, PHYSICAL: False, NOTE: '-', PRIORITY: 2}
        },
        "geo_r": {
            'GEO_R_01': {UPDATE: 10, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "ha": {
            'HA_01': {UPDATE: 16, SUPPORTED: True, CLOUD_NATIVE: True, EXCLUSIVE: True, PRIORITY: 1, NOTE: HA_01_NOTE}
        },
        "launcher": {
            'LAUNCHER_01': {UPDATE: 9, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'LAUNCHER_02': {UPDATE: 9, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'LAUNCHER_03': {UPDATE: 9, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "lcm": {
            'LCM_01': {UPDATE: 0, SUPPORTED: False, NOTE: MANUAL, PRIORITY: 'M'}
        },
        "lkf": {
            'LKF_01': {UPDATE: 0, SUPPORTED: False, NOTE: OPTIONAL_UNSUPPORTED.format("RTD-15881"), PRIORITY: 2},
        },
        "logviewer": {
            'LOGVIEWER_01': {UPDATE: 13, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "lt_syslog_stream": {
            'LT_SYSLOG_STREAM_01': {UPDATE: 3, SUPPORTED: True, PHYSICAL: False, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "migration": {
            'MIGRATION_01': {UPDATE: 0, SUPPORTED: False, NOTE: MANUAL, PRIORITY: 'M'},
            'MIGRATION_02': {UPDATE: 0, SUPPORTED: False, NOTE: MANUAL, PRIORITY: 'M'},
            'MIGRATION_03': {UPDATE: 0, SUPPORTED: False, NOTE: MANUAL, PRIORITY: 'M'}
        },
        "ncm_mef_lcm": {
            'NCM_MEF_LCM_01': {UPDATE: 5, SUPPORTED: True, NOTE: NCM_MEF_LCM_01_NOTE, PRIORITY: 2}
        },
        "ncm_l3_vpn": {
            'NCM_L3_VPN_01': {UPDATE: 6, SUPPORTED: True, NOTE: NCM_L3_VPN_01_NOTE, PRIORITY: 2}
        },
        "ncm_mef": {
            'NCM_MEF_01': {UPDATE: 3, SUPPORTED: True, NOTE: '-', PRIORITY: 2},
            'NCM_MEF_02': {UPDATE: 3, SUPPORTED: True, NOTE: '-', PRIORITY: 2},
            'NCM_MEF_03': {UPDATE: 0, SUPPORTED: False, NOTE: OPTIONAL_UNSUPPORTED.format("As per TERE"), PRIORITY: 2}
        },
        "ncm_vpn_sd": {
            'NCM_VPN_SD_01': {UPDATE: 2, SUPPORTED: True, NOTE: '-', PRIORITY: 2}
        },
        "neo4j": {
            'NEO4J_01': {UPDATE: 6, SUPPORTED: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'NEO4J_02': {UPDATE: 2, SUPPORTED: INTRUSIVE, NOTE: '-', PRIORITY: 2}
        },
        "netex": {
            'NETEX_01': {UPDATE: 46, SUPPORTED: True, NOTE: '-', PRIORITY: 1, CLOUD_NATIVE: True},
            'NETEX_02': {UPDATE: 47, SUPPORTED: True, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True},
            'NETEX_03': {UPDATE: 26, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: 'STKPI Profile.', PRIORITY: 1},
            'NETEX_04': {UPDATE: 32, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NETEX_05': {UPDATE: 24, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NETEX_07': {UPDATE: 27, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NETEX_08': {UPDATE: 0, SUPPORTED: False, CLOUD_NATIVE: False, NOTE: 'ENMRTD-25455', PRIORITY: 2}
        },
        "netview": {
            'NETVIEW_SETUP': {UPDATE: 13, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-',
                              RETAIN_NODES_AFTER_COMPLETED: True, PRIORITY: 2},
            'NETVIEW_01': {UPDATE: 13, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NETVIEW_02': {UPDATE: 18, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
        },
        "network": {
            'NETWORK_01': {UPDATE: 4, SUPPORTED: True, NOTE: OPTIONAL_UNSUPPORTED.format("Robustness"), PRIORITY: 2, CLOUD_NATIVE: True},
            'NETWORK_02': {UPDATE: 2, SUPPORTED: True, NOTE: OPTIONAL_UNSUPPORTED.format("Robustness"), PRIORITY: 2, CLOUD_NATIVE: True},
            'NETWORK_03': {UPDATE: 1, SUPPORTED: True, NOTE: OPTIONAL_UNSUPPORTED.format("Robustness"), PRIORITY: 2, CLOUD_NATIVE: True}
        },
        "nhc": {
            'NHC_01': {UPDATE: 38, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHC_02': {UPDATE: 20, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHC_04': {UPDATE: 13, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "nhm": {
            'NHM_SETUP': {UPDATE: 21, FOUNDATION: True, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2,
                          RETAIN_NODES_AFTER_COMPLETED: True, DEPENDENT: ["NHM_03", "NHM_04", "NHM_05", "NHM_06",
                                                                          "NHM_07", "NHM_08", "NHM_09", "NHM_10",
                                                                          "NHM_11", "NHM_12", "NHM_13", "NHM_14"]},
            'NHM_03': {UPDATE: 39, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_04': {UPDATE: 87, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_05': {UPDATE: 55, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_06': {UPDATE: 76, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_07': {UPDATE: 77, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_08': {UPDATE: 83, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_09': {UPDATE: 76, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_10': {UPDATE: 71, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_11': {UPDATE: 72, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_12': {UPDATE: 35, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_13': {UPDATE: 27, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_14': {UPDATE: 11, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "nhm_rest_nbi": {
            'NHM_REST_NBI_SETUP': {UPDATE: 1, FOUNDATION: True, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-',
                                   PRIORITY: 2, RETAIN_NODES_AFTER_COMPLETED: True, DEPENDENT: ["NHM_REST_NBI_01", "NHM_REST_NBI_02"]},
            'NHM_REST_NBI_01': {UPDATE: 2, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_REST_NBI_02': {UPDATE: 2, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_REST_NBI_03': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_REST_NBI_04': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_REST_NBI_05': {UPDATE: 1, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_REST_NBI_06': {UPDATE: 2, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_REST_NBI_07': {UPDATE: 1, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NHM_REST_NBI_08': {UPDATE: 1, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "nodecli": {
            'NODECLI_01': {UPDATE: 35, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "nodesec": {
            'NODESEC_01': {UPDATE: 6, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'NODESEC_02': {UPDATE: 6, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'NODESEC_03': {UPDATE: 11, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'NODESEC_04': {UPDATE: 8, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'NODESEC_08': {UPDATE: 11, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'NODESEC_11': {UPDATE: 16, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NODESEC_13': {UPDATE: 17, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NODESEC_15': {UPDATE: 22, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NODESEC_16': {UPDATE: 9, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NODESEC_17': {UPDATE: 1, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NODESEC_18': {UPDATE: 1, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "npa": {
            'NPA_01': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "nvs": {
            'NVS_01': {UPDATE: 11, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'NVS_02': {UPDATE: 12, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "nas_outage": {
            'NAS_OUTAGE_01': {UPDATE: 1, SUPPORTED: INTRUSIVE, CLOUD: False, CLOUD_NATIVE: False, NOTE: OPTIONAL_UNSUPPORTED.format("RTD-21052"), PRIORITY: 2},
            'NAS_OUTAGE_02': {UPDATE: 2, SUPPORTED: INTRUSIVE, CLOUD: False, CLOUD_NATIVE: False, NOTE: OPTIONAL_UNSUPPORTED.format("RTD-22235"), PRIORITY: 2}
        },
        "ops": {
            'OPS_01': {UPDATE: 57, SUPPORTED: True, CLOUD: False, NOTE: '-', PRIORITY: 2, CLOUD_NATIVE: True}
        },
        "parmgt": {
            'PARMGT_01': {UPDATE: 35, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PARMGT_02': {UPDATE: 15, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PARMGT_03': {UPDATE: 12, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PARMGT_04': {UPDATE: 7, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "plm": {
            'PLM_01': {UPDATE: 26, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PLM_02': {UPDATE: 0, SUPPORTED: False, CLOUD_NATIVE: False, NOTE: 'RTD-21715', PRIORITY: 2}
        },
        "pkiadmin": {
            'PKIADMIN_01': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "pm_rest_nbi": {
            "PM_REST_NBI_01": {UPDATE: 2, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            "PM_REST_NBI_02": {UPDATE: 2, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "pm": {
            'PM_02': {UPDATE: 20, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_03': {UPDATE: 23, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_04': {UPDATE: 8, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_06': {UPDATE: 38, SUPPORTED: False, NOTE: 'RTD-15443', PRIORITY: 2},
            'PM_11': {UPDATE: 37, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_15': {UPDATE: 17, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_16': {UPDATE: 15, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: PM_16_NOTE, PRIORITY: 2},
            'PM_17': {UPDATE: 19, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_19': {UPDATE: 14, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_20': {UPDATE: 30, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_24': {UPDATE: 15, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_25': {UPDATE: 21, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_26': {UPDATE: 82, SUPPORTED: True, CLOUD: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_27': {UPDATE: 11, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_28': {UPDATE: 13, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, NOTE: 'Deprecated (ENMRTD-25370)', PRIORITY: 2},
            'PM_29': {UPDATE: 14, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_30': {UPDATE: 15, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_31': {UPDATE: 13, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_32': {UPDATE: 21, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_35': {UPDATE: 1, SUPPORTED: False, NOTE: KTT, PRIORITY: 'KTT'},
            'PM_38': {UPDATE: 30, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_40': {UPDATE: 23, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_42': {UPDATE: 24, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_44': {UPDATE: 15, SUPPORTED: True, CLOUD: False, NOTE: CENM.format("RTD-12693"), PRIORITY: 2},
            'PM_45': {UPDATE: 34, SUPPORTED: False, CLOUD_NATIVE: False, NOTE: 'Deprecated (ENMRTD-25370)', PRIORITY: 2},
            'PM_46': {UPDATE: 18, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_47': {UPDATE: 12, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_48': {UPDATE: 27, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_49': {UPDATE: 12, SUPPORTED: INTRUSIVE, CLOUD: False, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'PM_50': {UPDATE: 21, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_51': {UPDATE: 19, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_52': {UPDATE: 46, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_53': {UPDATE: 16, SUPPORTED: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'PM_54': {UPDATE: 23, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_55': {UPDATE: 21, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_56': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_57': {UPDATE: 28, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_58': {UPDATE: 11, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_59': {UPDATE: 7, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_60': {UPDATE: 7, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_61': {UPDATE: 18, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_62': {UPDATE: 16, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_63': {UPDATE: 22, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_64': {UPDATE: 19, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_65': {UPDATE: 19, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_66': {UPDATE: 10, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_67': {UPDATE: 19, SUPPORTED: True, NOTE: CENM.format("RTD-15949"), PRIORITY: 1},
            'PM_68': {UPDATE: 9, SUPPORTED: True, NOTE: CENM.format("RTD-15949"), PRIORITY: 1},
            'PM_69': {UPDATE: 19, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_70': {UPDATE: 12, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_71': {UPDATE: 13, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_72': {UPDATE: 10, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_73': {UPDATE: 7, SUPPORTED: True, NOTE: CENM.format("RTD-15949"), PRIORITY: 1},
            'PM_74': {UPDATE: 17, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_75': {UPDATE: 19, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_76': {UPDATE: 16, SUPPORTED: True, NOTE: CENM.format("RTD-15949"), PRIORITY: 2},
            'PM_77': {UPDATE: 34, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_78': {UPDATE: 24, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_79': {UPDATE: 27, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_80': {UPDATE: 18, SUPPORTED: True, NOTE: CENM.format('RTD-12709'), PRIORITY: 2},
            'PM_81': {UPDATE: 13, SUPPORTED: True, NOTE: CENM.format('RTD-12709'), PRIORITY: 2},
            'PM_82': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_83': {UPDATE: 4, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_84': {UPDATE: 8, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_85': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_86': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_87': {UPDATE: 9, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_88': {UPDATE: 3, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_89': {UPDATE: 4, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_90': {UPDATE: 8, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_91': {UPDATE: 8, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_92': {UPDATE: 11, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_93': {UPDATE: 10, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_94': {UPDATE: 2, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'PM_95': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_96': {UPDATE: 7, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_97': {UPDATE: 4, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_98': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_99': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_100': {UPDATE: 2, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_101': {UPDATE: 2, SUPPORTED: True, CLOUD: False, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'PM_102': {UPDATE: 0, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, NOTE: 'ENMRTD-25084', PRIORITY: 2},
            'PM_103': {UPDATE: 0, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, NOTE: 'ENMRTD-25085', PRIORITY: 2},
            'PM_104': {UPDATE: 0, SUPPORTED: False, CLOUD: False, CLOUD_NATIVE: False, NOTE: 'ENMRTD-25086', PRIORITY: 2}
        },
        "reparenting": {
            'REPARENTING_01': {UPDATE: 4, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_02': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_03': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_04': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_05': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_06': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_07': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_08': {UPDATE: 2, SUPPORTED: False, NOTE: '-', PRIORITY: 2},
            'REPARENTING_09': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_10': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_11': {UPDATE: 5, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'REPARENTING_12': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "secui": {
            'SECUI_01': {UPDATE: 20, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'SECUI_02': {UPDATE: 15, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SECUI_03': {UPDATE: 8, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'SECUI_05': {UPDATE: 15, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SECUI_06': {UPDATE: 17, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SECUI_07': {UPDATE: 17, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SECUI_08': {UPDATE: 15, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SECUI_09': {UPDATE: 14, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SECUI_10': {UPDATE: 39, SUPPORTED: True, CLOUD: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SECUI_11': {UPDATE: 6, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SECUI_12': {UPDATE: 21, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
        },
        "sev": {
            'SEV_01': {UPDATE: 1, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SEV_02': {UPDATE: 1, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "shm": {
            'SHM_SETUP': {UPDATE: 54, FOUNDATION: True, SUPPORTED: True, CLOUD_NATIVE: True, PRIORITY: 1,
                          NOTE: ('Sets the bandwidth, SFTP, Confirmation and pulls down the software packages,'
                                 'used by SHM Upgrade profiles: '
                                 '(SHM_03, SHM_05, SHM_24, SHM_25, SHM_27, SHM_31, SHM_33, SHM_36, SHM_40, SHM_42, '
                                 'SHM_44)'
                                 'Sets the backup file sizes used by backup profiles: '
                                 '(SHM_01, SHM_02, SHM_06, SHM_18, SHM_23, SHM_26, SHM_32, SHM_34, SHM_39, '
                                 'SHM_41, SHM_43)')},
            'SHM_01': {UPDATE: 100, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'SHM_02': {UPDATE: 102, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'SHM_03': {UPDATE: 120, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'SHM_04': {UPDATE: 42, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'SHM_05': {UPDATE: 113, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'SHM_06': {UPDATE: 152, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_07': {UPDATE: 48, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_18': {UPDATE: 69, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'SHM_19': {UPDATE: 36, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_20': {UPDATE: 33, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_21': {UPDATE: 38, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_23': {UPDATE: 74, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_24': {UPDATE: 69, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_25': {UPDATE: 68, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'SHM_26': {UPDATE: 56, SUPPORTED: INTRUSIVE, CLOUD_NATIVE: INTRUSIVE, NOTE: '-', PRIORITY: 2},
            'SHM_27': {UPDATE: 70, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_28': {UPDATE: 54, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_31': {UPDATE: 80, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_32': {UPDATE: 72, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_33': {UPDATE: 90, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_34': {UPDATE: 68, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_35': {UPDATE: 65, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'SHM_36': {UPDATE: 97, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_37': {UPDATE: 42, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 1},
            'SHM_39': {UPDATE: 66, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_40': {UPDATE: 65, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_41': {UPDATE: 54, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_42': {UPDATE: 63, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_43': {UPDATE: 50, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_44': {UPDATE: 17, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_45': {UPDATE: 18, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2},
            'SHM_46': {UPDATE: 8, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: OPTIONAL_UNSUPPORTED.format("Robustness"), PRIORITY: 2},
            'SHM_47': {UPDATE: 2, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        },
        "top": {
            'TOP_01': {UPDATE: 54, SUPPORTED: True, CLOUD_NATIVE: True, NOTE: '-', PRIORITY: 2}
        }
    }
}
EXCLUSIVE_PROFILES = []
for app in basic:
    for profile in basic.get(app):
        for prof in basic.get(app).get(profile):
            if ("EXCLUSIVE" in basic.get(app).get(profile).get(prof) and
                    basic.get(app).get(profile).get(prof).get("SUPPORTED") and
                    basic.get(app).get(profile).get(prof).get('EXCLUSIVE')):
                EXCLUSIVE_PROFILES.append(prof)
