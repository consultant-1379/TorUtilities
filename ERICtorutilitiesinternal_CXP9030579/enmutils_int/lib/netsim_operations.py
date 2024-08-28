# ********************************************************************
# Name    : NetSim Operations
# Summary : Primarily used by FM and CmSync to create Burst instances.
#           Provides functionality to create Alarm/AVC/MCD/Burst burst
#           objects, all of which extend NetsimOperation class,
#           responsible for building the burst command, starting the
#           burst and stopping the burst. Also includes functionality
#           to execute a command on simulations and Power on nodes.
# ********************************************************************

import math
import random
from enmutils.lib import log
from enmutils.lib import thread_queue
from enmutils.lib.exceptions import NetsimError, FailedNetsimOperation
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib import netsim_executor


class NetsimOperation(object):

    def __init__(self, nodes):
        """
        NetsimOperation constructor.
        :type nodes: list
        :param nodes: list of enm_node.BaseNode objects on which to issue netsim command
        :raises AttributeError: If there are no elements in nodes
        """
        if not nodes:
            raise AttributeError("Nodes required to run a netsim operation on")

        self.nodes = nodes
        node_dict = node_pool_mgr.group_nodes_per_sim(nodes)
        self.node_groups = {}
        for host, sim_dict in node_dict.iteritems():
            for sim, nodes_info in sim_dict.iteritems():
                split_node_list_based_on_ne_type = {}
                for node in nodes_info:
                    ne_type = getattr(node, "NE_TYPE", node.primary_type)
                    if ne_type in split_node_list_based_on_ne_type.keys():
                        split_node_list_based_on_ne_type[ne_type].append(node)
                    else:
                        split_node_list_based_on_ne_type[ne_type] = [node]

                for ne_type in split_node_list_based_on_ne_type.keys():
                    if ne_type in self.node_groups.keys():
                        self.node_groups[ne_type].append((host, sim, split_node_list_based_on_ne_type[ne_type]))
                    else:
                        self.node_groups[ne_type] = [(host, sim, split_node_list_based_on_ne_type[ne_type])]

    def execute_command_string(self, command):
        """
        Executes the given netsim command on all self.nodes

        :type command: string
        :param command: netsim command to issue on all nodes

        :raises: FailedNetsimOperation if command fails on the node
        """
        sim_cmds = []

        for _, sim_info in self.node_groups.iteritems():
            for host, sim, nodes in sim_info:
                sim_cmds.append(SimulationCommand(host, sim, nodes, command))
        self.execute(sim_cmds)

    @staticmethod
    def taskset(sim_cmd):
        """
        Netsim Operation's task set

        :param sim_cmd: Command to be executed on the Netsim
        :type sim_cmd: `shell.Command`

        :return: Response object
        :rtype: `shell.Response`
        """
        return sim_cmd.execute()

    def execute(self, sim_cmds):
        """
        Executes the given netsim command on all self.nodes
        :type sim_cmds: List of SimulationCommand objects
        :param sim_cmds: list of SimulationCommand objects to issue on all nodes
        :raises FailedNetsimOperation: If netsim operation on the node is failed
        :raises NetsimError: If update on result_dict with the netsim result fails
        """
        if len(sim_cmds) > 1:
            result_dict = {}
            tq = thread_queue.ThreadQueue(work_items=sim_cmds, num_workers=5, func_ref=self.taskset,
                                          task_wait_timeout=60 * 15, task_join_timeout=60 * 15)

            tq.execute()
            if tq.exceptions_raised:
                raise FailedNetsimOperation("{0}/{1} threads raised exceptions for Netsim Operation '{2}'. "
                                            "Exception Messages: {3}".format(tq.exceptions_raised, len(self.nodes),
                                                                             sim_cmds[0].command[:30], "\n"
                                                                             .join(tq.exception_msgs), nodes=self.nodes,
                                                                             command=sim_cmds[0].command))

            for work_entry in tq.work_entries:
                if work_entry.result:
                    try:
                        result_dict.update(work_entry.result)
                    except Exception as e:
                        raise NetsimError(e.message)
        else:
            result_dict = sim_cmds[0].execute()

        failed_nodes = [node for node, result in result_dict.iteritems() if result == "FAIL"]
        if failed_nodes:
            log.logger.debug("The failed nodes are {0}".format(failed_nodes))
            nodes = [node for node in self.nodes if node.node_name in failed_nodes]
            raise FailedNetsimOperation("NetsimOperation operation '{0}' failed for {1}/{2} nodes, please refer to the "
                                        "profile logs for the nodes on which the netsim operations has failed"
                                        "".format(sim_cmds[0].command[:30], len(failed_nodes), len(self.nodes)),
                                        nodes=nodes, command=sim_cmds[0].command)
        log.logger.debug("Successfully ran netsim {0} operation on all nodes".format(sim_cmds[0].command[:30]))

    @staticmethod
    def _execute_on_simulation(host, simulation, nodes, command):
        """
        Executes the given command on nodes of the specified simulation
        :type host: string
        :param host: The Netsim box you want to access
        :type simulation: string
        :param simulation: The simulation you wish to use on the Netsim box
        :type nodes: list
        :param nodes: list of enm_node.BaseNode objects on which to issue netsim command
        :type command: string
        :param command: netsim command to issue on all the nodes
        :rtype: dict
        :returns: dict saying whether the operation on nodes PASSED or FAILED
        """

        node_names = [node.node_name for node in nodes]
        return netsim_executor.run_ne_cmd(command, host, simulation, node_names)


class Burst(NetsimOperation):

    STOP_BURST_COMMAND = "stopburst:id={burst_id};"

    def __init__(self, nodes, burst_id):
        """
        Burst Constructor
        :type nodes: list
        :param nodes: list of enm_node.BaseNode objects on which to issue the netsim command
        :type burst_id: string
        :param burst_id: The burst id for the string
        """

        super(Burst, self).__init__(nodes)
        self.burst_id = burst_id

    def stop(self):
        """
        Stops all bursts on the given nodes with the specified id
        :raises: FailedNetsimOperation
        """
        command = self.STOP_BURST_COMMAND.format(burst_id=self.burst_id)
        self.execute_command_string(command)

    def _teardown(self):
        """
        Teardown interface method
        """
        self.stop()


class AlarmBurst(Burst):

    ALARM_BURST_PROBLEM_1 = 'Nss Synchronization System Clock Status Change'
    ALARM_BURST_PROBLEM_2 = 'TU Synch Reference Loss of Signal'
    ALARM_BURST_PROBLEM_3 = 'Link Failure'
    START_BURST_COMMAND = 'alarmburst:{arguments};'
    SHARED_CNF_START_BURST_COMMAND = 'alarmburst_x:{arguments};'
    CCDM_START_BURST_COMMAND = 'alarmburst_x:{arguments};'
    BSC_MSC_START_BURST_COMMAND = 'axealarmburst_gsm:{arguments};'
    MSC_BC_START_BURST_COMMAND = 'axealarmburst:{arguments};'
    CPP = ["ERBS", "MGW", "RNC", "RBS"]
    COM_ECIM = ["RadioNode", "MSRBS_V2", "SGSN-MME", "SGSN"]
    SHARED_CNF = ["Shared-CNF"]
    GSM = ["BSC", "MSC-DB-BSP"]
    GSM_BLADE_CLUSTER = ["MSC-BC-BSP", "MSC-BC-IS"]
    ROUTER_CCDM_NODE_TYPES = ["Router_6672", "Router6672", "Router_6675", "Router6675", "CCDM"]
    TRANSPORT = ["SIU02", "TCU02"]
    MINI_LINK_INDOOR = ["MINI-LINK-Indoor", "MINI-LINK-669x", "MLTN"]
    BLADE_COUNT = 11

    def __init__(self, nodes, burst_id, burst_rate, duration, severity, text="", loop=False,
                 problem="", event_type="", probable_cause=""):
        """
        AlarmBurst Constructor
        :type nodes: list
        :param nodes: list of enm_node.BaseNode objects on which to issue netsim command
        :type burst_id: ste
        :param burst_id: the burst id for the command
        :type burst_rate: float
        :param burst_rate: the number of alarms per second you want generated by the sum of all nodes
        :type duration: int
        :param duration: the length of time you want the alarm burst to last
        :type severity: str
        :param severity: severity of alarm (i.e. critical, severe etc.)
        :type text: str
        :param text: bytes of text we want associated with alarm (usually used to increase package size of alarm)
        :type loop: bool
        :param loop: indicates whether the burst should or should not loop
        :type event_type: int
        :param event_type: event type attribute of the alarm
        :type problem: str
        :param problem: specific problem attribute of the alarm
        :type probable_cause: int
        :param probable_cause: probable cause attribute of the alarm
        """
        super(AlarmBurst, self).__init__(nodes=nodes, burst_id=burst_id)
        self.burst_rate = burst_rate
        self.duration = duration
        freq = round(float(self.burst_rate) / float(len(self.nodes)), 3)
        # To make total alarms a even number, so that equal number of alarms and clears would be generated by netsim
        num_alarms = int(round((self.duration * freq) / 2.) * 2)

        # Severity values for CPP nodes:
        # SEVERITY_CPP = {'1':'Indeterminate','2':'Critical','3':'Major','4':'Minor','5':'Warning','6':'Cleared'}
        # Severity values for COM_ECIM nodes:
        # SEVERITY_COM_ECIM = {'1': 'Cleared', '2': 'Indeterminate', '3': 'Critical', '4': 'Major', '5': 'Minor', '6': 'Warning'}

        self.problem = problem
        severity_cpp = 0
        if severity == 'indeterminate':
            severity_cpp = 1
        elif severity == 'critical':
            severity_cpp = 2
        elif severity == 'major':
            severity_cpp = 3
        elif severity == 'minor':
            severity_cpp = 4
        else:
            severity_cpp = 5

        self.kwargs_com_ecim = [
            ('id', str(burst_id)),
            ('freq', str(freq)),
            ('num_alarms', str(num_alarms)),
            ('severity', str(severity)),
            ('clear_after_burst', "false"),
            ('loop', "true" if loop else "false")
        ]

        self.kwargs_shared_cnf = [
            ('id', str(burst_id)),
            ('freq', str(freq)),
            ('num_alarms', str(num_alarms)),
            ('severity', str(severity)),
            ('clear_after_burst', "true"),
            ('loop', "true" if loop else "false")
        ]

        self.kwargs_siu_tcu = [
            ('id', str(burst_id)),
            ('freq', str(freq)),
            ('num_alarms', str(num_alarms)),
            ('severity', '3'),
            ('loop', "true" if loop else "false")
        ]

        self.kwargs_mltn = [
            ('id', str(burst_id)),
            ('freq', str(freq)),
            ('num_alarms', str(num_alarms)),
            ('severity', '3'),
            ('clear_after_burst', "false"),
            ('loop', "true" if loop else "false")
        ]

        self.kwargs_cpp = [
            ('id', str(burst_id)),
            ('freq', str(freq)),
            ('num_alarms', str(num_alarms)),
            ('severity', str(severity_cpp)),
            ('clear_after_burst', "false"),
            ('loop', "true" if loop else "false")
        ]

        self.kwargs_gsm = [
            ('NAME', 'GSMBURST'),
            ('ID', str(burst_id)),
            ('FREQ', str(freq)),
            ('BURST', str(num_alarms)),
            ('CLASS', str(1)),
            ('loop', "false")
        ]

        self.extra_cmd_kwargs = {'problem': problem, 'text': text, 'event_type': event_type, 'probable_cause': probable_cause}

    def burst_parameters(self, node_type):
        """
        Returns burst parameters for particular node_type
        :type node_type: str
        :param node_type: node type
        :rtype: list
        :returns: list of burst parameters based on the node platform/type
        """
        burst_params = []
        log.logger.info("Node Type to run alarmBurst: {0}".format(node_type))
        if node_type in self.COM_ECIM:
            c = ComECIMBurstParameters()
            burst_params = c.parameters()
        elif node_type in self.SHARED_CNF:
            c = SharedCNFBurstParameters()
            burst_params = c.parameters()
        elif node_type in self.ROUTER_CCDM_NODE_TYPES:
            c = RouterBurstParameters()
            burst_params = c.parameters()
        elif node_type in self.CPP:
            c = CppBurstParameters()
            burst_params = c.parameters()
        elif node_type in self.GSM or node_type in self.GSM_BLADE_CLUSTER:
            c = GsmBurstParameters()
            burst_params = c.parameters()
        elif node_type in self.TRANSPORT:
            c = SiuTcuBurstParameters()
            burst_params = c.parameters()
        elif node_type in self.MINI_LINK_INDOOR:
            c = MltnBurstParameters()
            burst_params = c.parameters()
        else:
            log.logger.debug('Node type "%s" is not supported' % node_type)
        return burst_params

    def start(self):
        """
        Starts an alarm burst on the given nodes
        """
        sim_cmds = []
        for node_type, sim_info in self.node_groups.iteritems():
            if node_type in self.CPP:
                command_params = self.kwargs_cpp + self.burst_parameters(node_type)
                log.logger.debug("Check node type {0}".format(node_type))
                start_command = self.START_BURST_COMMAND
            elif node_type in self.GSM:
                command_params = self.kwargs_gsm + self.burst_parameters(node_type)
                log.logger.debug("Check node type {0}".format(node_type))
                start_command = self.BSC_MSC_START_BURST_COMMAND
            elif node_type in self.GSM_BLADE_CLUSTER:
                self.alarm_rate_for_blade_clusters()
                command_params = self.kwargs_gsm + self.burst_parameters(node_type)
                log.logger.debug("Check node type {0}".format(node_type))
                start_command = self.MSC_BC_START_BURST_COMMAND
            elif node_type in self.TRANSPORT:
                command_params = self.kwargs_siu_tcu + self.burst_parameters(node_type)
                log.logger.debug("Check node type {0}".format(node_type))
                start_command = self.START_BURST_COMMAND
            elif node_type in self.MINI_LINK_INDOOR:
                command_params = self.kwargs_mltn + self.burst_parameters(node_type)
                log.logger.debug("Check node type {0}".format(node_type))
                start_command = self.START_BURST_COMMAND
            elif node_type in self.SHARED_CNF:
                command_params = self.kwargs_shared_cnf + self.burst_parameters(node_type)
                log.logger.debug("Check severity: node type {0}, severity {1} and problem '{2}'".format(node_type, str(
                    self.kwargs_shared_cnf[3]), self.problem))
                start_command = self.SHARED_CNF_START_BURST_COMMAND
            else:
                command_params = self.kwargs_com_ecim + self.burst_parameters(node_type)
                log.logger.debug("Check severity: node type {0}, severity {1} and problem '{2}'".format(node_type, str(self.kwargs_com_ecim[3]), self.problem))
                start_command = self.START_BURST_COMMAND if node_type != 'CCDM' else self.CCDM_START_BURST_COMMAND
            command = start_command.format(arguments=','.join(
                '%s=%s' % (k, v.format(**self.extra_cmd_kwargs)) for k, v in command_params if v is not None))

            for host, sim, nodes in sim_info:
                sim_cmds.append(SimulationCommand(host, sim, nodes, command))
        self.execute(sim_cmds)

    def start_aml(self):
        """
        Starts an alarm burst on the given nodes at interface level for AML
        """
        sim_cmds = []
        log.logger.debug("Starting alarm burst for AML nodes")
        for node_type, sim_info in self.node_groups.iteritems():
            log.logger.debug("Check node type {0}".format(node_type))
            if node_type in self.MINI_LINK_INDOOR:
                mo_name = '"MeContext={0},ManagedElement={0},Transport=1,Interfaces=1,Interface=CT-1/1"'
                cmd_args = self.kwargs_mltn
                burst_params = list(self.burst_parameters(node_type))
                cmds = self.construct_alarmburst_commands_for_aml_nodes(node_type, sim_info, mo_name, burst_params,
                                                                        cmd_args)
            else:
                mo_name = '"MeContext={0},ManagedElement=1,interfaces=1,interface=1/2"'
                cmd_args = self.kwargs_com_ecim
                burst_params = list(self.burst_parameters(node_type))
                cmds = self.construct_alarmburst_commands_for_aml_nodes(node_type, sim_info, mo_name, burst_params,
                                                                        cmd_args)
            sim_cmds.extend(cmds)
        self.execute(sim_cmds)

    def construct_alarmburst_commands_for_aml_nodes(self, node_type, sim_info, mo_name, burst_params, cmd_args):
        """
        constructs the alarm burst commands for nodes which are used for AML alarm load
        :return: alarm burst commands for each node
        :rtype: list
        """
        cmds = []
        log.logger.debug("constructing alamrburst commands for AML")
        for host, sim, nodes in sim_info:
            log.logger.debug("Nodes : {0}".format(nodes))
            for node in nodes:
                if node_type not in self.MINI_LINK_INDOOR:
                    burst_params[1] = ('managed_object', mo_name.format(node.node_name))
                command_params = cmd_args + burst_params
                command = self.START_BURST_COMMAND.format(arguments=','.join(
                    '%s=%s' % (k, v.format(**self.extra_cmd_kwargs)) for k, v in command_params if v is not None))
                cmds.append(SimulationCommand(host, sim, [node], command))
        log.logger.debug("Constructed alarmburst commands for AML, nodetype : {0}".format(node_type))
        return cmds

    def alarm_rate_for_blade_clusters(self):
        """
        This will calculate the rate freq and number of alarms to be generated for blade cluster nodes
        """
        rate = float(self.burst_rate) / float(self.BLADE_COUNT)
        freq = round(rate / float(len(self.nodes)), 3)
        # netsim is not accepting freq less than 0.005, it is taking it as 0
        if freq < 0.005:
            freq = 0.005
        # To make total alarms a even number, so that equal number of alarms and clears would be generated by netsim
        num_alarms = int(round((self.duration * freq) / 2.) * 2)
        self.kwargs_gsm[2] = ('FREQ', str(freq))
        self.kwargs_gsm[3] = ('BURST', str(num_alarms))
        log.logger.info("Blade cluster nodes alarm burst attributes = {}".format(self.kwargs_gsm))


class AVCBurst(Burst):

    START_BURST_COMMAND = 'avcburst:id={burst_id},freq={freq},num_events={num_events},avcdata="[{MO_Updates}]",' \
        'loop={loop},mode={mode},idle_time={idle_time};'

    def __init__(self, nodes, burst_id, duration, burst_rate, mo_path, mo_attribute, mo_values, notification_rate=None,
                 num_events=None):
        """
        AVCBurst Constructor

        :type nodes: list
        :param nodes: List of enm_node.BaseNode objects on which to issue the netsim command
        :type burst_id: string
        :param burst_id: the burst id for the command
        :type duration: int
        :param duration: the length of time in seconds you want the avc bursts to last
        :type burst_rate: float
        :param burst_rate: the number of avc events per second you want generated by the sum of all nodes
        :type mo_path: string
        :param mo_path: The different managed objects needed to drill down to get to the attributes and values
        :type mo_attribute: string
        :param mo_attribute: The attribute which will have its value changed
        :type mo_values: list
        :param mo_values: A list of the values to which the attribute will be changed to
        :type notification_rate: float
        :param notification_rate: Calculated notification rate per node
        :param num_events: Predefined number of events to be created
        :type num_events: int
        """

        super(AVCBurst, self).__init__(nodes=nodes, burst_id=burst_id)
        self.loop = "false"
        self.mode = "temp"
        self.idle_time = 0
        self.freq = round(float(burst_rate) / float(len(self.nodes)), 3) if not notification_rate else notification_rate
        self.num_events = int(math.ceil(duration * self.freq)) if not num_events else num_events

        mo_update_cmd = '{{\\"{mo_path}\\",[{{\\"{mo_attribute}\\",\\"{mo_values}\\"}}]}}'

        update_cmds = []

        if mo_attribute == 'None':
            for attr_values in mo_values:
                for attribute in attr_values.keys():
                    for value in attr_values[attribute]:
                        update_cmds.append(mo_update_cmd.format(mo_path=mo_path, mo_attribute=attribute,
                                                                mo_values=value))
        elif isinstance(mo_values, list):
            for value in mo_values:
                update_cmds.append(mo_update_cmd.format(
                    mo_path=mo_path, mo_attribute=mo_attribute, mo_values=value))
        else:
            update_cmds.append(mo_update_cmd.format(
                mo_path=mo_path, mo_attribute=mo_attribute, mo_values=mo_values))

        self.burst_data = ",".join(update_cmds)

    def start(self):
        """
        Starts avc bursts on the given nodes
        """
        command = self.START_BURST_COMMAND.format(
            burst_id=self.burst_id, freq=self.freq, num_events=self.num_events, MO_Updates=self.burst_data,
            loop=self.loop, mode=self.mode, idle_time=self.idle_time)
        self.execute_command_string(command)


class PowerNodes(NetsimOperation):

    START_NODES_COMMAND = ".start -parallel"
    NODES_IN_PARALLEL = 5
    START_NODES_COMMAND_VAPP = "{0} {1}".format(START_NODES_COMMAND, NODES_IN_PARALLEL)
    STOP_NODES_COMMAND = ".stop -parallel"
    NO_CALLBACK = ".selectnocallback {node_name}"

    def __init__(self, nodes):
        super(PowerNodes, self).__init__(nodes)

    def start(self):
        self.execute_command_string(self.START_NODES_COMMAND)

    def stop(self):
        self.execute_command_string(self.STOP_NODES_COMMAND)

    def start_nodes(self):
        hosts = node_pool_mgr.group_nodes_per_sim(self.nodes)
        for host, sim_dict in hosts.iteritems():
            start_command = self.START_NODES_COMMAND_VAPP if host == "netsim" else self.START_NODES_COMMAND
            for sim, nodes in sim_dict.iteritems():
                self._execute_on_simulation(host, sim, nodes, start_command)


class SimulationCommand(object):

    def __init__(self, host, simulation, nodes, command):
        self.host = host
        self.simulation = simulation
        self.nodes = nodes
        self.command = command
        self.keep_connection_open = False if 'burst' in command.split(":")[0] else True

    def execute(self):
        """
        Executes the supplied command on the designated simulation
        :returns: response of the command executed on the nodes
        :rtype: dict
        """
        node_names = [node.node_name for node in self.nodes]
        return netsim_executor.run_ne_cmd(self.command, self.host, self.simulation, node_names,
                                          keep_connection_open=self.keep_connection_open)


class CppBurstParameters(object):

    cpp_burst_parameters = [
        ('cease_after', '1'),
        ('mo_instance', "\"%mibprefix,ManagedElement=1,Equipment=1\""),
        ('cause', '"%unique"'),
        ('type', 'ET_COMMUNICATIONS_ALARM'),
        ('problem', '"{problem}"'),
        ('text', '"{text}"')
    ]

    def parameters(self):
        return self.cpp_burst_parameters


class ComECIMBurstParameters(object):
    com_ecim_burst_parameters = [
        ('cease_after', '1'),
        ('managed_object', '"ManagedElement=%nename,Equipment=1"'),
        ('probable_cause', '{probable_cause}'),
        ('event_type', '{event_type}'),
        ('specific_problem', '"{problem}"'),
        ('additional_text', '"NONE"')
    ]

    def parameters(self):
        return self.com_ecim_burst_parameters


class SharedCNFBurstParameters(object):
    shared_cnf_burst_parameters = [
        ('cease_after', '1'),
        ('managed_object', '"ManagedElement=%nename,SystemFunctions=1,SysM=1"'),
        ('probable_cause', '{probable_cause}'),
        ('event_type', '{event_type}'),
        ('specific_problem', '"{problem}"'),
        ('additional_text', '"NONE"')
    ]

    def parameters(self):
        return self.shared_cnf_burst_parameters


class RouterBurstParameters(object):
    router_burst_parameters = [
        ('cease_after', '1'),
        ('managed_object', '"ManagedElement=1,SystemFunctions=1,SysM=1"'),
        ('probable_cause', '{probable_cause}'),
        ('idle_time', '0'),
        ('event_type', '{event_type}'),
        ('specific_problem', '"{problem}"'),
        ('minor_type', '9175121'),
        ('major_type', '193'),
        ('additional_text', '"NONE"')
    ]

    def parameters(self):
        return self.router_burst_parameters


class SiuTcuBurstParameters(object):
    siu_tcu_burst_parameters = [
        ('cease_after', '1'),
        ('mo_class', '"Equipment"'),
        ('mo_instance', '"STN=0,Equipment=1"'),
        ('cause', '315'),
        ('type', '4'),
        ('problem', '"{problem}"'),
        ('text', '"FM Profile Alarm"')
    ]

    def parameters(self):
        return self.siu_tcu_burst_parameters


class MltnBurstParameters(object):
    lan_instances = ['"1/6/4"', '"1/6/5"', '"1/6/6"', '"1/6/7"', '"1/6/8"', '"1/2/1"', '"1/2/2"']
    wan_instances = ['"1/5/1"', '"1/4/1"']
    dict1 = {'"LAN"': lan_instances, '"WAN"': wan_instances}
    class_name = random.choice(list(dict1.keys()))
    instance_name = random.choice(dict1[class_name])
    mltn_burst_parameters = [
        ('cease_after', '1'),
        ('instance', instance_name),
        ('class', class_name),
        ('cause', '58'),
        ('type', '4'),
        ('problem', '"{problem}-%unique"'),
        ('text', '"FM Profile Alarm"')
    ]

    def parameters(self):
        return self.mltn_burst_parameters


class GsmBurstParameters(object):
    gsm_burst_parameters = [
        ('ACTIVE', '2'),
        ('CAT', '1'),
        ('PRCA', '40'),
        ('TEXT', '"unique 5"'),
        ('INFO1', '"{problem}"'),
        ('I_TIME', '0')
    ]

    def parameters(self):
        return self.gsm_burst_parameters


class MCDBurst(Burst):

    START_BURST_COMMAND = ('mcdburst:id={burst_id}, freq={freq}, num_events={num_events}, mode={mode}, loop={loop}, '
                           'idle_time={idle_time}, mcddata="[{mcd_data_info}]";')

    def __init__(self, nodes, burst_id, duration, burst_rate, new_mos_info, mcd_data_attrs=None):
        """

        :param nodes: List of enm_node.BaseNode objects on which to issue the netsim command
        :type nodes: list
        :param burst_id: the burst id to use in the command
        :type burst_id: str
        :param duration: the length of time in seconds the bursts should last
        :type duration: int
        :param burst_rate: the number of notifications per second to generated by all nodes
        :type burst_rate: int
        :param new_mos_info: List of information about the MOs to create on the specified nodes. Information should be provided in the following format:
            [{'mo_parent_path': <MO's parent FDB>, 'New_MO_Info': [(<MO Name>, <MO value>), (<MO Name>, <MO value>), ...]}] where
                <MO's parent FDB> is the full FDN of the parent MO, e.g. ManagedElement=1,ENodeBFunction=1,EUtraNetwork=1
                <MO Name> is the name of the MO to create.
                <MO value> is the ID of the MO to create
        :type new_mos_info: list
        :param mcd_data_attrs: List of strings in the format '{\"MoName=MoValue\"}}'
        :type mcd_data_attrs: list
        """

        super(MCDBurst, self).__init__(nodes=nodes, burst_id=burst_id)
        self.loop = "asym"  # asymmetrical burst so create/delete are executed if interrupted
        """
        mode: determines the way the burst shall be handled by the NE
            temp - The NE does not restart the burst at all
            persistent - The NE automatically starts the burst upon restart, if it was running when the NE was stopped
            permanent - Like persistent mode. Additionally, the NE tries to restart the burst immediately if it dies
        """
        self.mode = "temp"
        # idle_time = 16 == 16 seconds between delete and create
        self.idle_time = 16 if nodes[0].primary_type == "ERBS" else 2
        num_events = round(float(burst_rate) / float(len(self.nodes)), 3)
        self.num_events = int(math.ceil(duration * num_events))
        # freq = 0.03  == 33 seconds between create and delete
        self.freq = 0.03 if nodes[0].primary_type == "ERBS" else 0.125
        self.mcd_data_attrs = mcd_data_attrs if mcd_data_attrs else []

        mcd_data_cmd = '{{\\"{mo_parent_path}\\",[{new_mo_values}],[{mcd_data_attrs}]}}'
        new_mo_cmd = '{{\\"{mo_name}\\",\\"{mo_value}\\"}}'

        commands = []
        for mo_info in new_mos_info:
            new_mos = []
            for mo_name, mo_value in mo_info['New_MO_Info']:
                new_mos.append(new_mo_cmd.format(mo_name=mo_name, mo_value=mo_value))

                commands.append(mcd_data_cmd.format(mo_parent_path=mo_info['mo_parent_path'],
                                                    new_mo_values=",".join(new_mos),
                                                    mcd_data_attrs=",".join(self.mcd_data_attrs)))

        self.mcd_data_info = ",".join(commands)

    def start(self):
        """
        Starts mcd bursts on the given nodes
        """

        command = self.START_BURST_COMMAND.format(
            burst_id=self.burst_id, freq=self.freq, num_events=self.num_events, mcd_data_info=self.mcd_data_info,
            loop=self.loop, mode=self.mode, idle_time=self.idle_time)
        self.execute_command_string(command)
