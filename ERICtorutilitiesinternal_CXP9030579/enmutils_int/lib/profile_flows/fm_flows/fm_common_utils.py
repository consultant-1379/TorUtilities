import re
import time
from datetime import datetime, timedelta
import random
from math import ceil
from enmscripting.exceptions import TimeoutException
from enmutils.lib import arguments
from enmutils.lib import log
from enmutils.lib.exceptions import FailedNetsimOperation, EnvironError
from enmutils_int.lib.fm import (alarmsearch_help, alarmviewer_help, add_nodes_to_given_workspace_for_a_user,
                                 delete_nodes_from_a_given_workspace_for_a_user, alarm_search_for_open_alarms,
                                 alarm_search_for_historical_alarms, OPEN)
from enmutils_int.lib.fm_specific_problems import get_specific_problem_iterator, map_nodes_for_profile
from enmutils_int.lib.fm_specific_problems import update_com_ecim_parameters
from enmutils_int.lib.netsim_operations import AlarmBurst, Burst


ALARM_VIEWER = "alarmviewer"
ALARM_SEARCH = "alarmsearch"


def execute_burst(profile, nodes_list, total_nodes, burst_id, burst_rate, duration, alarm_text_problem, alarm_text_size,
                  event_type, probable_cause, teardown_list, platform):
    """
    Execute the burst for the given profile
    :param profile: profile
    :type profile: enmutils_int.lib.profile.Profile
    :param nodes_list: list of nodes
    :type nodes_list: list
    :param total_nodes: total nodes used by profile
    :type total_nodes: int
    :param burst_id: the burst id for the command
    :type burst_id: str
    :param burst_rate: rate of alarms per sec
    :type burst_rate: float
    :param duration: duration of burst
    :type duration: int
    :param alarm_text_problem: list of alarm problem
    :type alarm_text_problem: list
    :param alarm_text_size: alarm size
    :type alarm_text_size: int
    :param event_type: event types
    :type event_type: int
    :param probable_cause: probable causes
    :type probable_cause: int
    :param teardown_list: teardown objects list
    :type teardown_list: list
    :param platform: platform of the nodes
    :type platform: str
    :raises TimeoutException: If burst command times out
    :return: alarm burst
    :rtype: enmutils_int.lib.netsim_operations.AlarmBurst
    """
    problem_iterator = get_specific_problem_iterator()
    profile_nodes = collect_nodes_for_profile(nodes_list, total_nodes)
    burst = AlarmBurst(profile_nodes, burst_id=burst_id, burst_rate=burst_rate, duration=duration,
                       severity=alarm_text_problem[1], text=arguments.get_random_string(alarm_text_size, exclude="oKkO"),
                       problem=alarm_text_problem[0] if alarm_text_problem[0] != '' else problem_iterator.next(),
                       event_type=event_type, probable_cause=probable_cause)
    set_teardown_list(burst, teardown_list)
    try:
        if platform == "AML":
            burst.start_aml()
        else:
            burst.start()
    except FailedNetsimOperation as e:
        profile.add_error_as_exception(FailedNetsimOperation(e))
    except Exception as e:
        raise TimeoutException(EnvironError("Timeout exception running start burst command : {0}".format(e)))
    return burst


def stop_burst(nodes, burst_id):
    """
    This will execute stopburst with the given burst ID on the given nodes
    :param nodes: ENM node instances
    :type nodes: list
    :param burst_id: Burt ID for stopping the corresponding alarm burst
    :type burst_id: str
    """
    try:
        burst = Burst(nodes, burst_id)
        burst.stop()
    except FailedNetsimOperation as e:
        log.logger.debug("Netsim operation failed. Exception: {0}".format(e))
    except Exception as e:
        log.logger.debug("Encountered an exception while stopping the burst: {0}".format(e))


def set_up_alarm_text_size_and_problem_distribution(alarm_size_distribution, alarm_problem_distribution):
    """
    Create a list of alarm sizes and problems
    :param alarm_size_distribution: list of alarm sizes
    :type alarm_size_distribution: list
    :param alarm_problem_distribution: list of alarm issues
    :type alarm_problem_distribution: list
    :return: a list of Alarm Sizes and Problems
    :rtype: list
    """
    alarm_distribution_list = []
    alarm_text_size = random.choice(alarm_size_distribution)
    alarm_text_problem = random.choice(alarm_problem_distribution)
    log.logger.debug("ALARM_PROBLEM_DISTRIBUTION" + str(alarm_problem_distribution))
    alarm_distribution_list.append(alarm_text_size)
    alarm_distribution_list.append(alarm_text_problem)
    return alarm_distribution_list


def set_up_event_type_and_probable_cause():
    """
    Sets the event type and probable cause to use from a list of all possible values
    :return: event type value , probable cause value
    :rtype: str
    """
    event_type = 1
    probable_cause = 0
    event_type, probable_cause = update_com_ecim_parameters(event_type, probable_cause)
    log.logger.debug("event_type and probable cause: [{0}, {1}]".format(event_type, probable_cause))
    return event_type, probable_cause


def collect_nodes_for_profile(nodes, total_nodes):
    """
    Collects nodes for profile
    :param nodes: Actual nodes used in profile
    :type nodes: list
    :param total_nodes: Total nodes required in profile
    :type total_nodes: int
    :return: nodes used in profile
    :rtype: list
    """
    log.logger.info('Nodes used in this burst cycle: {0}/{1}'.format(str(len(nodes)), str(total_nodes)))
    map_nodes_for_profile(nodes)
    return nodes


def set_teardown_list(burst, teardown_list):
    """
    Adds burst to the teardown list to run when profile stops
    :param burst: alarm burst
    :type burst: enmutils_int.lib.netsim_operations.AlarmBurst
    :param teardown_list: teardown objects list
    :type teardown_list: list
    """
    teardown_list.append(burst)


def execute_alarm_search_tasks(user, node_data, user_dict, nodes, search_type=OPEN, time_span=1):
    """
    A series of ui alarm search tasks to be executed
    :param user: enm user
    :type user: enmutils.lib.enm_user_2.User
    :param node_data: Dict of nodes with action type and uid
    :type node_data: dict
    :param user_dict: Dict containing workspace id and node group id
    :type user_dict: dict
    :param nodes: list of node instances to be used to perform this flow
    :type nodes: list
    :param search_type: Historical or Open alarms
    :type search_type: str
    :param time_span: time period for the search to span
    :type time_span: datetime
    """
    time.sleep(random.randint(1, 30))
    log.logger.debug("The Alarm Search user dict is {}".format(user_dict))
    node_count = len(nodes)
    time_now = datetime.now()
    old_time = time_now - timedelta(days=time_span)
    to_date = int(time.mktime(time_now.timetuple())) * 1000
    from_date = int(time.mktime(old_time.timetuple())) * 1000
    if user.username in user_dict.keys():
        workspace_id, node_group_id = user_dict.get(user.username)
        if workspace_id and node_group_id:
            # Add nodes to the workspace
            node_data['actionType'] = 'Create'
            add_nodes_to_given_workspace_for_a_user(user, node_data, workspace_id, node_group_id, node_count, ALARM_SEARCH)
            time.sleep(5)
            if search_type == OPEN:
                alarm_search_for_open_alarms(user, nodes, from_date, to_date, search_type, num_alarms=10)
            else:
                alarm_search_for_historical_alarms(user, nodes, from_date, to_date, search_type)
            time.sleep(10)
            # Remove nodes from workspace
            node_data['actionType'] = 'Delete'
            delete_nodes_from_a_given_workspace_for_a_user(user, node_data, workspace_id, node_group_id, ALARM_SEARCH)
            time.sleep(1)
            alarmsearch_help(user=user)
    else:
        log.logger.debug("User {0} not found in user dictionary ".format(user.username))


def execute_alarm_monitor_tasks(user, node_data, user_dict, node_count):
    """
    A series of ui alarm monitor tasks to be executed
    :param user: User to execute tasks
    :type user: `enmutils.lib.enm_user_2.User`
    :param node_data: Dict of nodes with action type and uid
    :type node_data: dict
    :param user_dict: Dict containing workspace id and node group id
    :type user_dict: dict
    :param node_count: Count of the nodes
    :type node_count: int
    """
    time.sleep(random.randint(1, 30))
    log.logger.debug("The Alarm Monitor user dict is {}".format(user_dict))
    if user.username in user_dict.keys():
        workspace_id, node_group_id = user_dict.get(user.username)
        if workspace_id and node_group_id:
            # Add nodes to the workspace
            node_data['actionType'] = 'Create'
            add_nodes_to_given_workspace_for_a_user(user, node_data, workspace_id, node_group_id, node_count, ALARM_VIEWER)
            time.sleep(10)
            # Remove nodes from the workspace
            node_data['actionType'] = 'Delete'
            delete_nodes_from_a_given_workspace_for_a_user(user, node_data, workspace_id, node_group_id, ALARM_VIEWER)
            time.sleep(1)
            alarmviewer_help(user=user)
    else:
        log.logger.debug("User {0} not found in user dictionary ".format(user.username))


def get_num_of_given_type_of_nodes_from_deployment(profile, user, platform_types):
    """
    Gets the number of SNMP type of nodes present on the deployment
    :param profile: workload profile instance
    :type profile: enmutils_int.lib.profile.Profile
    :param user: enm user to perform operations on the deployment
    :type user: enmutils.lib.enm_user_2.User
    :param platform_types: platform types of the nodes
    :type platform_types: list
    :return: Count of SNMP nodes present on the deployment
    :rtype: dict
    """
    cmedit_nodes_cmd = "cmedit get * {}ConnectivityInformation -cn"
    node_count_dict = {}
    for platform in platform_types:
        try:
            response = user.enm_execute(cmedit_nodes_cmd.format(platform))
            response_string = "\n".join(response.get_output())
            match_pattern = re.compile(r'{}ConnectivityInformation .* instance'.format(platform))
            second_pattern = re.compile(r'.* instance')
            if match_pattern.search(response_string) is not None:
                number_of_nodes = int(re.split('.*?{}ConnectivityInformation (.*?) instance.*'.format(platform),
                                               response_string)[1])
                node_count_dict[platform] = number_of_nodes
            elif second_pattern.search(response_string) is not None:
                number_of_nodes = int(re.split('(.*?) instance.*', response_string)[1])
                node_count_dict[platform] = number_of_nodes
            else:
                log.logger.debug("Unexpected response encountered, Response : {0}".format(response.get_output()))
                node_count_dict[platform] = 0
        except Exception as e:
            profile.add_error_as_exception(e)
    return node_count_dict


def get_total_number_of_nodes_on_deployment(profile, user):
    """
    Gets the total network elements count from the deployment
    :param profile: workload profile instance
    :type profile: enmutils_int.lib.profile.Profile
    :param user: enm user instance
    :type user: enmutils.lib.enm_user_2.User
    :return: count of total NE's
    :rtype: int
    """
    cmedit_command = "cmedit get * NetworkElement -cn"
    try:
        response = user.enm_execute(cmedit_command)
        response_string = "\n".join(response.get_output())
        match_pattern = re.compile(r'NetworkElement .* instance')
        second_pattern = re.compile(r'.* instance')
        if match_pattern.search(response_string) is not None:
            number_of_nodes = int(re.split('.*?NetworkElement (.*?) instance.*', response_string)[1])
            return number_of_nodes
        elif second_pattern.search(response_string) is not None:
            number_of_nodes = int(re.split('(.*?) instance.*', response_string)[1])
            return number_of_nodes
        else:
            log.logger.info("Unexpected response encountered, Response : {0}".format(response.get_output()))
            return 0
    except Exception as e:
        profile.add_error_as_exception(e)


def map_alarm_rate_with_nodes(profile_nodes, bsc_rate, msc_rate, cpp_rate, snmp_rate, aml_rate, aml_ratio):
    """
    Maps the overall burst frequency of a specific type with that type of nodes allocated to profile
    :param profile_nodes: nodes allocated to the profile
    :type profile_nodes: dict of enmutils.lib.enm_node.Node instances
    :param bsc_rate: overall burst frequency to be applied on BSC nodes
    :type bsc_rate: float
    :param msc_rate: overall burst frequency to be applied on MSC and MSC-BC nodes
    :type msc_rate: float
    :param cpp_rate: overall burst frequency to be applied on CPP nodes
    :type cpp_rate: float
    :param snmp_rate: overall burst frequency to be applied on SNMP nodes
    :type snmp_rate: float
    :param aml_rate: overall burst frequency to be applied on nodes for AML
    :type aml_rate: float
    :param aml_ratio: ratio of nodes to be set for AML
    :type aml_ratio: float
    :return: burst rate for each type and nodes on which it should be applied
    :rtype: dict
    """
    cpp_node_types = ['ERBS', 'RNC', 'RBS', 'MGW']
    aml_node_types = ['Router6672', 'Router6675', 'MINI-LINK-6352', 'MINI-LINK-669x']
    alarm_rate_dict = {}
    cpp_nodes = []
    snmp_nodes = []
    msc_nodes = []
    bsc_nodes = []
    aml_nodes = []
    for node_type, nodes_list in profile_nodes.iteritems():
        if 'BSC' in node_type:
            bsc_nodes.extend(nodes_list)
        elif 'MSC' in node_type:
            msc_nodes.extend(nodes_list)
        elif node_type in cpp_node_types:
            cpp_nodes.extend(nodes_list)
        elif node_type in aml_node_types:
            num_of_nodes = int(ceil(len(nodes_list) * aml_ratio))
            aml_nodes.extend(nodes_list[:num_of_nodes])
            snmp_nodes.extend(nodes_list[num_of_nodes:])
        else:
            snmp_nodes.extend(profile_nodes[node_type])
    alarm_rate_dict["CPP"] = (cpp_rate, cpp_nodes)
    if aml_nodes and snmp_rate > aml_rate:
        alarm_rate_dict["SNMP"] = ((snmp_rate - aml_rate), snmp_nodes)
    else:
        alarm_rate_dict["SNMP"] = (snmp_rate, snmp_nodes)
    alarm_rate_dict["MSC"] = (msc_rate, msc_nodes)
    alarm_rate_dict["BSC"] = (bsc_rate, bsc_nodes)
    alarm_rate_dict["AML"] = (aml_rate, aml_nodes)
    log.logger.debug("alarm rate dict : {0}".format(alarm_rate_dict))
    return alarm_rate_dict


def setup_alarm_burst(profile, alarm_dict, burst_id, alarm_size_and_sp, event_type, probable_cause, teardown_list):
    """
    setup the alarm burst for BSC, MSC, CPP and SNMP nodes
    :param profile: workload profile instance
    :type profile: enmutils_int.lib.profile.Profile
    :param alarm_dict: alarm dict which contains node type as key and a tuple of node objects and alarm rate as value
    :type alarm_dict: dict
    :param burst_id: burst id used to start burst on the node
    :type burst_id: str
    :param alarm_size_and_sp: alarm text size in bytes
    :type alarm_size_and_sp: list
    :param event_type: event type attribute  for the alarm burst
    :type event_type: int
    :param probable_cause: probable cause attribute for the alarm burst
    :type probable_cause: int
    :param teardown_list: teardown list of the profile
    :type teardown_list: list
    """
    duration = profile.DURATION
    for platform, (burst_rate, nodes) in alarm_dict.iteritems():
        if nodes and burst_rate > 0:
            log.logger.info("Burst rate for {0} nodes : {1} A/s".format(platform, burst_rate))
            try:
                execute_burst(profile, nodes, len(nodes), burst_id, burst_rate, duration, alarm_size_and_sp[1],
                              alarm_size_and_sp[0], event_type, probable_cause, teardown_list, platform)
                log.logger.info("Items in teardown list after burst : {}".format(teardown_list))
            except Exception as e:
                log.logger.debug("Encountered error executing burst, exception: {}".format(str(e)))
                profile.add_error_as_exception(EnvironError(e))
        else:
            log.logger.info("The burst rate for {} nodes is 0 or no nodes of that type are allocated".format(platform))


def calculate_alarm_rate_distribution(node_type_count, total_nodes, burst_rate):
    """
    calculates the alarm rates for different node types from a total burst rate
    :param node_type_count: node types and their respective count from the deployment
    :type node_type_count: dict
    :param total_nodes: total node count from the deployment
    :type total_nodes: int
    :param burst_rate: alarm burst frequency in alarms per second
    :type burst_rate: float
    :return: individual alarm rates for MSC, BSC, CPP and SNMP node types
    :rtype: float
    """
    alarm_load_dict = {}
    cpp_gsm_nodes = sum(node_type_count.values())
    if total_nodes > cpp_gsm_nodes:
        node_type_count['Snmp'] = total_nodes - cpp_gsm_nodes
    else:
        node_type_count['Snmp'] = 0
    log.logger.info("Node type count from deployment : {0}".format(node_type_count))
    for key, value in node_type_count.iteritems():
        if value > 0 and total_nodes > 0:
            ratio = float(value) / float(total_nodes)
            alarm_rate = ratio * burst_rate
            alarm_load_dict[key] = round(alarm_rate, 4)
        else:
            alarm_load_dict[key] = 0
            log.logger.warn("{0} type nodes are {1} in deployment".format(key, value))
    msc_rate = alarm_load_dict['Msc']
    bsc_rate = alarm_load_dict['Bsc']
    cpp_rate = alarm_load_dict['Cpp']
    snmp_rate = alarm_load_dict['Snmp']
    return msc_rate, bsc_rate, cpp_rate, snmp_rate


def put_profile_to_sleep(profile, sleep_time):
    """
    Puts profile to sleep for the given sleep time and updates last run and next run so that they will be seen in
    'workload status' output
    :param profile: workload profile object which needs to be put to sleep
    :type profile: enmutils_int.lib.profile.Profile
    :param sleep_time: number of seconds for the profile to sleep
    :type sleep_time: int
    """
    profile._last_run = datetime.now()
    profile._next_run = datetime.now() + timedelta(seconds=sleep_time)
    log.logger.info("Sleeping for {0} seconds until next iteration at {1}".format(sleep_time, profile._next_run))
    old_state = profile.state
    profile.state = "SLEEPING"
    time.sleep(sleep_time)
    profile.state = old_state
    log.logger.info("Profile is running its next iteration now")
