# This a template for the config which can be used for starting APT_01
# There are 3 options provided below.
# NOTE: Only one option can be used - other two options must be removed!
# node_name should be replaced with desired node that need to be ringfenced for use by the profile
# To uncomment a configuration below, Remove the # at the start of the line
# For default template see:  https://eteamspace.internal.ericsson.com/display/ERSD/APT_01+Default+templates

APT_01 = {
    'SUPPORTED': True,
    # RAN_CORE only
    # 'DEFAULT_NODES': {"ERBS": ['node_name'],
    #                   "SGSN": ["node_name", "node_name", "node_name"],
    #                   "RadioNode": ['node_name']}

    # Transport only
    # 'DEFAULT_NODES': {'MINILINK_Indoor': ["node_name", "node_name", "node_name"],
    #                   'ROUTER_6000': ["node_name"]}

    # HYBRID only
    # 'DEFAULT_NODES': {"ERBS": ['node_name'],
    #                   "SGSN": ["node_name", "node_name", "node_name"],
    #                   'MINILINK_Indoor': ["node_name", "node_name", "node_name"],
    #                   'ROUTER_6000': ["node_name"],
    #                   "RadioNode": ['node_name']}
}
