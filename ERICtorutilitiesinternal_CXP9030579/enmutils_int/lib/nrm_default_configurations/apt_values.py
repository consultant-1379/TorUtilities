"""
The following attributes are for use by APT for a few assertions.
This file needs to be kept updated with the actual values in the framework.
Please inform APT team if something is being updated here.
"""

SHM_DATA = {
    "LOCAL_PATH": "/home/enmutils/shm",
    "EXISTING_PACKAGES": {
        "ERBS": ["CXPL16BCP1_G1283", "CXPL17BCP1_G1284", "CXP102051_26-R24BC"],
        "MLTN": ["R35F105_1"],
        "RadioNode": [
            "CXP2010174_R50J23", "CXP9024420_R2SM", "CXP9024418_6_R2CXS2", "CXP9024418_15-R31A209",
            "CXP9024418_R2SM"
        ],
        "Router_6672": ["CXP9027695_1-R17B138_108773_SF-RP-P1S_NMS"],
        "Router6672": ["CXP9027695_1-R17B138_108773_SF-RP-P1S_NMS"],
        "Router6675": ["CXP9060188_1-R17B138_108769_SF-RP-P1L"],
        "MINI-LINK-Indoor": ["R35F105_1"],
        "MINI-LINK-6352":
        ["CXP9026371_3_R10F110_2-8", "CXP9026371_3_R11A130_2-9"],
        "MINI-LINK-669x":
        ["CXP9036600_1_MINI-LINK_6600_6366_1.4_R5N107", "CXP9036600_1-R6S127"],
        "SIU02": ["R1H20_CXP102200_1"],
        "TCU02": ["R1H20_CXP102200_2"],
        "BSC": ["BSC_BRprofilePkg_A", "BSC_BRprofilePkg_B"],
        "SCU": ["CXP9017878_3_P24A"]
    }
}

FM_DATA = {
    "DELAYED_ACKNOWLEDGE_HRS": 24
}
