# ********************************************************************
# Name    : SHM DATA
# Summary : Primarily used by SHM profiles. Allows the user to store
#           common data within the SHM application area
# ********************************************************************

# PLATFORM_TYPES dictionary with primary type and platform type values
PLATFORM_TYPES = {'RadioNode': 'ECIM', 'ERBS': 'CPP', "Router6672": "ECIM", 'Router6675': 'ECIM',
                  'MLTN': 'MINI_LINK_INDOOR', 'LH': 'MINI_LINK_INDOOR', "MINI-LINK-Indoor": 'MINI_LINK_INDOOR',
                  'SGSN-MME': 'SGSN-MME', 'MINI-LINK-669x': 'MINI_LINK_INDOOR', 'SCU': 'ECIM',
                  'TCU02': 'STN', 'SIU02': 'STN', 'MINI-LINK-6352': 'MINI_LINK_OUTDOOR', 'BSC': 'AXE'}
HEADERS_DICT = {'Content-Type': 'application/json', 'Accept': 'application/json'}
# SHM Software
SHM_SOFTWARE_PACKAGE_UPLOAD_ENDPOINT = "/oss/shm/rest/softwarePackage/import"
SHM_SOFTWARE_PACKAGE_DELETE_ENDPOINT = "/oss/shm/rest/softwarePackage/delete"
SHM_SOFTWARE_PACKAGE_LIST_ENDPOINT = "/oss/shm/rest/softwarePackage/list"
SHM_SOFTWARE_ACTIVE_PACKAGE = "/oss/shm/rest/inventory/activeSoftware/"
SHM_SOFTWARE_VALIDATE_PACKAGE = "/oss/shm/rest/softwarePackage/validate"
SHM_SOFTWARE_PACKAGE_LIST_NODE_ENDPOINT = "/oss/shm/rest/inventory/v1/upgradepackage/list"
SHM_SOFTWARE_NODE_COMPONENTS_LIST_ENDPOINT = "/oss/shm/rest/inventory/v1/axe-node-topology"
SHM_REFERRED_SOFTWARE_PACKAGE_LIST_NODE_ENDPOINT = "/oss/shm/rest/inventory/v1/upgradepackage/referred-upgradepackages"
SHM_REFERRED_BACKUP_LIST_NODE_ENDPOINT = "/oss/shm/rest/inventory/v1/upgradepackage/referred-backups"
# SHM Licenses
SHM_LICENSE_UPLOAD_ENDPOINT = "/oss/shm/rest/licensekeyfiles/upload"
SHM_LICENSE_DELETE_ENDPOINT = "/oss/shm/rest/licensekeyfiles/delete"
NODE_FINGERPRINT_COMMAND = "cmedit get {node_id} Licensing.fingerprint"
GET_FINGERPRINT_REGEX = r"(?<=fingerprint\s:\s)\w+"
LICENSE_GENERATION_SCRIPT_NAME = "Multiple_FPs_Licensing.sh"
LICENSE_GENERATION_SCRIPT_FOLDER = "/tmp/MultiLIC_Script_updated/"
LICENSE_GENERATION_SCRIPT = LICENSE_GENERATION_SCRIPT_FOLDER + LICENSE_GENERATION_SCRIPT_NAME
SHM_LICENSE_LIST_ENDPOINT = "/oss/shm/rest/license/importedFiles"
# SHM job
SHM_JOBS_LIST_ENDPOINT = "/oss/shm/rest/job/v2/jobs"
SHM_JOBS_CANCEL_ENDPOINT = "/oss/shm/rest/job/cancelJobs"
SHM_JOB_DELETE_ENDPOINT = "/oss/shm/rest/job/delete"
SHM_JOB_CREATE_ENDPOINT = "/oss/shm/rest/job"
SHM_BACKUP_ITEMS = "/oss/shm/rest/inventory/backupItems"
SHM_JOB_DETAILS = '/oss/shm/rest/job/jobdetails?offset=1&limit=50&sortBy=neStartDate&orderBy=desc&jobId={job_id}'
# SHM Export
SHM_EXPORT_ENDPOINT = "/oss/shm/rest/inventory/exportInventory"
SHM_EXPORT_CSV_ENDPOINT = "/oss/shm/rest/inventory/inventoryExportProgress/{export_id}"
# Default SW PACKAGE Details
# Update value changes in enmutils_int/lib/nrm_default_configurations/apt_values.py SHM_DATA variable
EXISTING_PACKAGES = {
    "ERBS": ["CXPL16BCP1_G1283", "CXPL17BCP1_G1284", "CXP102051_26-R24BC"],
    "MLTN": ["R35F105_1"],
    "RadioNode": ["CXP2010174_R50J23", "CXP9024420_R2SM", "CXP9024418_6_R2CXS2", "CXP9024418_15-R31A209",
                  "CXP9024418_R2SM"],
    "Router_6672": ["CXP9027695_1-R17B138_108773_SF-RP-P1S_NMS"],
    "Router6672": ["CXP9027695_1-R17B138_108773_SF-RP-P1S_NMS"],
    "Router6675": ["CXP9060188_1-R17B138_108769_SF-RP-P1L"],
    "MINI-LINK-Indoor": ["R35F105_1"],
    "MINI-LINK-6352": ["CXP9026371_3_R10F110_2-8", "CXP9026371_3_R11A130_2-9"],
    "MINI-LINK-669x": ["CXP9036600_1_MINI-LINK_6600_6366_1.4_R5N107", "CXP9036600_1-R6S127"],
    "SIU02": ["R1H20_CXP102200_1"],
    "TCU02": ["R1H20_CXP102200_2"],
    "BSC": ["BSC_BRprofilePkg_A", "BSC_BRprofilePkg_B"],
    "SCU": ["CXP9017878_3_P24A"]
}

NODE_IDENTITY_MIMS = {
    "MLTN": ["CXP9010021_1_MINI-LINK_TN_6.1_LH_2.1_R35F105", "CXP 901 0021/1", "R35F105"],
    "MINI-LINK-Indoor": ["CXP9010021_1_MINI-LINK_TN_6.1_LH_2.1_R35F105", "CXP 901 0021/1", "R35F105"],
    "MINI-LINK-6352_0": ["CXP9026371_3_R10F110_2-8", "CXP9026371_3", "R10F110"],
    "MINI-LINK-6352_1": ["CXP9026371_3_R11A130_2-9", "CXP9026371_3", "R11A130"],
    "MINI-LINK-669x_0": ["CXP9036600_1_MINI-LINK_6600_6366_1.4_R5N107", "CXP9036600_1", "R5N107"],
    "MINI-LINK-669x_1": ["CXP9036600_1-R6S127", "CXP9036600_1", "R6S127"],
    "Router6672_0": ["CXP9027695_1-R7D44_9999_SF-RP-P1S_NMS", "CXP9027695_1", "R7D44_9999"],
    "Router6675_0": ["CXP9060188_1-R7D44_9999_SF-RP-P1L_NMS", "CXP9060188_1", "R7D44_9999"],
    "SIU02": ["CXP102200_1_R1H20", "CXP102200_1", "R1H20"],
    "TCU02": ["CXP102200_2_R1H20", "CXP102200_2", "R1H20"],
    "BSC_01": ["BSC_BRProfileTesting__A", "BSC_BRProfileTesting", "A"],
    "BSC_02": ["BSC_BRProfileTesting__B", "BSC_BRProfileTesting", "B"],
    "SCU_0": ["CXP9017878_3_P24A", "CXP9017878_3", "P24A"]
}
