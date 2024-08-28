# ********************************************************************
# Name    : Node Parse
# Summary : Replacement file for the deprecated node parse module in
#           production package. Used by node pool manager when nodes
#           are added or removed from the pool. Responsible for
#           locating, reading the parsed node files, will use the node
#           id, netsim and simulation information from the arne.xml,
#           will query ENM directly for the ne type, oss prefix,
#           release, model identity and ne product version.
# ********************************************************************

import base64
import csv

from enmutils.lib import filesystem, log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.enm_user import get_workload_admin_user

FDN_KEY = "FDN"


def update_row_with_enm_values(node_ids):
    """
    Query ENM for the created node values

    :param node_ids: List of node ids created on ENM, based upon the nodes to be added
    :type node_ids: list

    :returns: Dictionary containing the ENM values for node(s)
    :rtype: dict
    """
    cmd = "cmedit get {0} NetworkElement.(neType, ossPrefix, ossModelIdentity, neProductVersion, release)".format(
        ";".join(node_ids))
    node_values = {}
    try:
        user = get_workload_admin_user()
        response = user.enm_execute(cmd).get_output()
        output = [_.encode('utf-8') for _ in response if _ and "instance" not in _]
        for index, line in enumerate(output):
            if FDN_KEY in line:
                node_values = parse_command_result_for_ne_values(output[index: index + 6], node_values)
        return node_values
    except Exception as e:
        log.logger.debug("Could not retrieve ENM node information, error encountered: {0}. "
                         "Information available in the supplied .csv file will be used.".format(str(e)))


def parse_command_result_for_ne_values(ne_values, node_values):
    """
    Parse the Node values from the ENM response

    :param ne_values: List containing the output of the ENM command starting with an FDN
    :type ne_values: list
    :param node_values: Dictionary to store the matched values in
    :type node_values: dict

    :returns: Dictionary containing the matched values
    :rtype: dict
    """
    node_id = ne_values[0].split("=")[-1].strip()
    node_values[node_id] = {}

    ne_product_version = (ne_values[1].split(':')[-1].strip() if "neProductVersion" in ne_values[1] else "null")

    revision = ne_product_version.split('revision=')[-1].split('}')[0].strip() if ne_product_version != '-' else "null"
    node_values[node_id]['revision'] = revision

    identity = (ne_product_version.split('identity=')[-1].split(',')[0].strip() if ne_product_version != '-' else
                "null")
    node_values[node_id]['identity'] = identity

    primary_type = ne_values[2].split(":")[-1].strip() if "neType" in ne_values[2] else "null"
    node_values[node_id]['primary_type'] = primary_type

    oss_model_id = ne_values[3].split(":")[-1].strip() if "ossModelIdentity" in ne_values[3] else "null"
    node_values[node_id]['model_identity'] = oss_model_id

    mim_version = oss_model_id.split('-')[-1] if oss_model_id != "null" else "null"
    node_values[node_id]['mim_version'] = mim_version

    oss_prefix = ne_values[4].split(":")[-1].strip() if "ossPrefix" in ne_values[4] else "null"
    node_values[node_id]['oss_prefix'] = oss_prefix

    sub_network = oss_prefix.split(",MeContext=")[0] if oss_prefix != "null" else "null"
    node_values[node_id]['subnetwork'] = sub_network

    node_version = ne_values[5].split(":")[-1].strip() if "release" in ne_values[5] else "null"
    node_values[node_id]['node_version'] = node_version
    return node_values


def get_node_data(input_file, start_range=None, end_range=None):
    """
    Get node data based on the value returned from CSV and ENM

    :param input_file: File path to the .csv file to be parsed
    :type input_file: str
    :param start_range: The start index of the nodes to be added
    :type start_range: int
    :param end_range: The end index of the nodes to be added
    :type end_range: int

    :return: Tuple containing a list of node dictionaries, node ids which are not created on ENM
    :rtype: tuple
    """
    enm_node_values = {}
    data = get_node_data_from_xml(input_file)
    start_range, end_range = set_nodes_ranges(len(data), start_range, end_range)
    row_ids = [row['node_id'] for row in data[start_range:end_range]]
    node_ids = verify_nodes_on_enm(row_ids)
    for node_chunk in (node_ids[i: i + 160] for i in range(0, len(node_ids), 160)):
        enm_node_values.update(update_row_with_enm_values(node_chunk))
    not_created = list(set(row_ids).difference(node_ids))
    found_nodes = []
    for row in data:
        if row['node_id'] in enm_node_values.keys():
            found_nodes.append(update_row_values(row, enm_node_values.get(row['node_id'])))
    return found_nodes, not_created


def update_row_values(row, node_values):
    """
    Update the .csv values with those found on ENM

    :param row: The matching row read in from the .csv
    :type row: dict
    :param node_values: The dictionary containing node id >> ENM values
    :type node_values: dict

    :returns: The updated row dictionary
    :rtype: dict
    """
    keys = ['oss_prefix', 'primary_type', 'model_identity', 'subnetwork', 'mim_version', 'revision', 'identity',
            'node_version']
    for key in keys:
        if node_values.get(key) and node_values.get(key) != "null":
            row[key] = node_values.get(key)
    return row


def set_nodes_ranges(row_count, start_range=None, end_range=None):
    """
    Determine if any range of nodes to be added needs to be applied

    :param row_count: Total number of rows found in the .csv file
    :type row_count: int
    :param start_range: The index of the first node if applicable
    :type start_range: int
    :param end_range: The final consecutive node index
    :type end_range: int

    :returns: Tuple containing the range of the nodes to be added
    :rtype: tuple
    """
    if start_range:
        start_range -= 1
        end_range = end_range if end_range else start_range + 1
    else:
        start_range = 0
        end_range = row_count
    return start_range, end_range


def verify_nodes_on_enm(node_ids):
    """
    Verify the list of supplied node ids exist on ENM

    :param node_ids: List of node ids to confirm if they are created on ENM
    :type node_ids: list

    :raises EnmApplicationError: raised if the command fails to execute correctly

    :returns: List of nodes created in ENM
    :rtype: list
    """
    cmd = "cmedit get * NetworkElement"
    nes_on_enm = []
    try:
        user = get_workload_admin_user()
        response = user.enm_execute(cmd).get_output()
        for line in response:
            if FDN_KEY in line:
                nes_on_enm.append(line.split("=")[-1].strip().encode('utf-8'))
        return list(set(nes_on_enm).intersection(node_ids))
    except Exception as e:
        raise EnmApplicationError(str(e))


def get_node_data_from_xml(input_file):
    """
    Gets the node data from the csv file

    :param input_file: File with node data
    :type input_file: string

    :returns: List of lists. Each list has node data
    :rtype: list
    :raises RuntimeError: raises if TypeError occurs and if file doesn't exist
    """
    if not filesystem.does_file_exist(input_file):
        raise RuntimeError("Could not find specified input file {0}".format(input_file))

    data = []
    with open(input_file) as node_file:
        reader = csv.DictReader(node_file, skipinitialspace=True)
        for row in reader:
            data.append(dict(
                node_id=row['node_name'],
                node_ip=row['node_ip'],
                mim_version=row['mim_version'],
                model_identity=row['oss_model_identity'],
                subnetwork=row['subnetwork'],
                revision=row.get('revision', None),
                identity=row.get('identity', None),
                primary_type=row.get('primary_type', None),
                node_version=row.get('node_version', None),
                netsim=row.get('netsim_fqdn', None),
                simulation=row.get('simulation', None),
                managed_element_type=row.get('managed_element_type', None),
                network_function=row.get('network_function', None),
                normal_user=base64.b64decode(row['normal_user']),
                normal_password=base64.b64decode(row['normal_password']),
                secure_user=base64.b64decode(row['secure_user']),
                secure_password=base64.b64decode(row['secure_password']),
            ))
    return data


def get_node_names_from_xml(input_file, start_range=None, end_range=None):
    """
    Gets the node data from the csv file

    :param input_file: File with node data
    :type input_file: string
    :param start_range: The start index of the node names to be returned
    :type start_range: int
    :param end_range: The end index of the nodes names to be returned
    :type end_range: int

    :returns: List of lists. Each list has node data
    :rtype: list
    :raises RuntimeError: raises if TypeError occurs and if file doesn't exists
    """
    if not filesystem.does_file_exist(input_file):
        raise RuntimeError("Could not find specified input file {0}".format(input_file))

    node_names = []
    with open(input_file) as node_file:
        reader = csv.DictReader(node_file, skipinitialspace=True)
        for row in reader:
            node_names.append(row['node_name'])
    start_range, end_range = set_nodes_ranges(len(node_names), start_range, end_range)
    return node_names[start_range:end_range]
