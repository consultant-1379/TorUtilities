import random
import time
from functools import partial

import pexpect

from enmutils.lib import log, shell
from enmutils.lib.exceptions import EnvironError, NetsimError
from enmutils.lib.filesystem import get_lines_from_remote_file, does_remote_file_exist
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import netsim_executor, node_pool_mgr
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class NetworkFlow(GenericFlow):
    RESTART_CMD = ".restart 120"
    START_CMD = ".start"
    STOP_CMD = ".stop"
    NETWORK_UNBLOCK = ("iptables -D INPUT -i ens192 -j DROP; iptables -D OUTPUT -o ens192 -j DROP; "
                       "iptables -D FORWARD -o ens192 -j DROP; ip6tables -D INPUT -i ens192 -j DROP; "
                       "ip6tables -D OUTPUT -o ens192 -j DROP; ip6tables -D FORWARD -o ens192 -j DROP")
    NETWORK_BLOCK = ("iptables -A INPUT -i ens192 -j DROP; iptables -A OUTPUT -o ens192 -j DROP; "
                     "iptables -A FORWARD -o ens192 -j DROP; ip6tables -A INPUT -i ens192 -j DROP; "
                     "ip6tables -A OUTPUT -o ens192 -j DROP; ip6tables -A FORWARD -o ens192 -j DROP")

    @staticmethod
    def execute_command_on_netsim_simulation(nodes_list, cmd):
        """
        Executes the supplied command on the supplied netsim host, targeting the supplied simulation and nodes
        if applicable.

        :param cmd: Netsim command to execute
        :type cmd: str
        :param nodes_list:node_user_info is the list of users and nodes.
        :type nodes_list: list
        :raises NetsimError: When issue occurred while executing commands on netsim fails
        """
        netsim, simulation, node_name = nodes_list
        log.logger.debug("Executing command: [{0}] on host: [{1}] targeting simulation: [{2}] and nodes("
                         "optional): [{3}]".format(cmd, netsim, simulation, node_name))
        try:
            netsim_executor.run_cmd(cmd, netsim, sim=simulation, node_names=[node_name])
        except Exception as e:
            raise NetsimError('Error: {0}'.format(e))
        log.logger.debug("Successfully executed command.")

    def select_random_node_or_simulation_attrs(self, required_node_count=None, required_simulations_count=None):
        """
        Select a sample of random nodes or simulations attributes to be execute netsim command against.

        :param required_node_count: Required number of random node attributes
        :type required_node_count: int
        :param required_simulations_count:  Required number of random simulation attributes
        :type required_simulations_count: int

        :return: List containing either sample of random nodes or simulations attributes
        :rtype: list
        """
        persisted_nodes = self.all_nodes_in_workload_pool(
            node_attributes=['netsim', 'simulation', 'node_ip', 'node_name'])
        if required_simulations_count:
            grouped_hosts = node_pool_mgr.group_nodes_per_sim(persisted_nodes)
            sims = [sim for sims in grouped_hosts.values() for sim in sims.keys()]
            sample_size = required_simulations_count if required_simulations_count <= len(sims) else len(sims)
            selected_sims = random.sample(sims, sample_size)
            node_attributes = [([key for key, value in grouped_hosts.items() if simulation in value][0],
                                simulation) for simulation in selected_sims]
        else:
            sample_size = required_node_count if required_node_count <= len(persisted_nodes) else len(persisted_nodes)
            selected_nodes = random.sample(persisted_nodes, sample_size)
            node_attributes = [(node.netsim, node.simulation, node.node_name) for node in selected_nodes]
        return node_attributes


class Network01Flow(NetworkFlow):

    def execute_flow(self):
        """
        Executes the flow
        """
        self.state = "RUNNING"
        while self.keep_running():
            try:
                nodes_list = self.select_random_node_or_simulation_attrs(
                    required_node_count=getattr(self, 'TOTAL_RANDOM_NODES', 100))
                log.logger.debug('The selected node : {0} \nThe number of nodes {1}'.format(nodes_list, len(nodes_list)))
                if not nodes_list:
                    raise EnvironError('Nodes are not available to continue the flow')
                teardown_object = partial(picklable_boundmethod(self.perform_netsim_operation_on_nodes), nodes_list,
                                          cmd=self.START_CMD)
                self.teardown_list.append(teardown_object)
                self.perform_netsim_operation_on_nodes(nodes_list, cmd=self.RESTART_CMD)
                self.teardown_list.remove(teardown_object)
            except Exception as e:
                self.add_error_as_exception(EnvironError(e))
            self.sleep()

    def perform_netsim_operation_on_nodes(self, nodes_list, cmd):
        """
        perform required operation( .start,.stop,.restart) on nodes
        :param nodes_list : List containing either sample of random nodes or simulations attributes
        :type nodes_list : list
        :param cmd : cmd to perform operation
        :type cmd : str
        """
        try:
            self.create_and_execute_threads(nodes_list, len(nodes_list),
                                            func_ref=self.execute_command_on_netsim_simulation, args=[cmd])
        except Exception as e:
            self.add_error_as_exception(EnvironError(e))


class Network02Flow(NetworkFlow):

    def execute_flow(self):
        """
        Executes the flow
        """
        self.state = "RUNNING"
        while self.keep_running():
            try:
                netsim_list = self.get_netsim_list()
                if not netsim_list:
                    raise EnvironError('Netsim VMs are not available to continue the flow')
                teardown_object = partial(picklable_boundmethod(self.perform_netsim_operations), netsim_list, up=True)
                self.teardown_list.append(teardown_object)
                self.perform_netsim_operations(netsim_list)
                sleep_time = 600
                log.logger.debug("Sleeping for {0} seconds before unblocking the network traffic.".format(sleep_time))
                time.sleep(sleep_time)
                self.perform_netsim_operations(netsim_list, up=True)
                self.teardown_list.remove(teardown_object)
            except Exception as e:
                self.add_error_as_exception(EnvironError(e))
            self.sleep()

    def get_netsim_list(self):
        """
        Returns the list of netsim hosts

        :return: List containing netsim hosts
        :rtype: list
        """
        netsim_limit = 3
        netsim_list = []
        simulation_list = self.select_random_node_or_simulation_attrs(
            required_simulations_count=getattr(self, 'TOTAL_RANDOM_SIMS', 5))
        netsim_vm_list = sorted(set([sim[0] for sim in simulation_list]))
        if len(netsim_vm_list) >= 3:
            for netsim in netsim_vm_list[:netsim_limit]:
                netsim_list.append(netsim)
            log.logger.debug("Netsim list: {0}".format(netsim_list))
        else:
            log.logger.debug("Netsim list: {0}".format(netsim_vm_list))
            netsim_list.extend(netsim_vm_list)
        return netsim_list

    def perform_netsim_operations(self, netsim_list, up=False):
        """
        Perform an up or down operation on the supplied simulations netsim host

        :param netsim_list: List of netsim, containing netsim host values
        :type netsim_list: list
        :param up: Boolean indicating if the operation is up or down of the simulation(s) netsim host
        :type up: bool
        """
        cmd = self.NETWORK_BLOCK if not up else self.NETWORK_UNBLOCK
        try:
            for netsim in netsim_list:
                self.execute_command_on_netsim_vm(cmd, netsim)
        except Exception as e:
            self.add_error_as_exception(e)

    def execute_command_on_netsim_vm(self, cmd, netsim):
        """
        Executes the supplied command on the supplied netsim host

        :param cmd: Netsim command to execute
        :type cmd: str
        :param netsim: Netsim host name
        :type netsim: str
        :raises EnvironError: When cannot connect to netsim vm
        :raises NetsimError: When netsim commands fails
        """
        log.logger.debug("The netsim VM is {0}".format(netsim))
        netsim_vm_cmd = "ssh -o stricthostkeychecking=no root@{0}".format(netsim)
        initial_expect = "root@"
        vm_password = "shroot"
        cmd_failed_message = "Command not executing properly on netsim vm because {0} \n Before:{1} \n After:{2}"
        with pexpect.spawn(netsim_vm_cmd) as child:
            rc = child.expect([initial_expect, "Password", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnvironError("Cannot connect to netsim vm because {0} \n Before:{1} \n After:{2}"
                                   .format(rc, child.before, child.after))
            child.sendline(vm_password)
            rc = child.expect([initial_expect, pexpect.EOF], timeout=10)
            if rc != 0:
                raise NetsimError(cmd_failed_message.format(rc, child.before, child.after))
            log.logger.debug("Logged into {0}".format(netsim))
            child.sendline(cmd)
            rc = child.expect([initial_expect, pexpect.EOF], timeout=60)
            if rc != 0:
                raise NetsimError(cmd_failed_message.format(rc, child.before, child.after))
            elif cmd == self.NETWORK_UNBLOCK:
                log.logger.debug("Successfully unblocked network traffic")
            else:
                log.logger.debug("Successfully blocked network traffic")
            child.sendline("exit")
            child.close()


class Network03Flow(NetworkFlow):

    NETSIM_CFG_FILE_PATH = "/netsim/netsim_cfg"
    NETSIM_USER = NETSIM_PWD = "netsim"
    REQUIRED_LATENCY = 60
    REQUIRED_BANDWIDTH = 12

    def execute_flow(self):
        """
        Executes the flow
        """
        append_teardown_once = True
        self.state = "RUNNING"
        while self.keep_running():
            nodes = self.select_nodes_to_use()
            if nodes:
                hosts = self.get_unique_netsim_host_to_be_changed(nodes)
                self.set_bandwidth_and_latency_on_netsims(hosts)
                if append_teardown_once:
                    self.teardown_list.append(partial(picklable_boundmethod(self.undo_changes), hosts))
                    append_teardown_once = False
            else:
                log.logger.debug('No MLTN nodes found to use. Going to sleep.')

            self.sleep()

    def select_nodes_to_use(self):
        """
        Selects all available minilink nodes with netsim attribute

        @return: list of nodes: nodes to be allocated for the profile
        @rtype: list
        """
        log.logger.debug("Selecting the minilink nodes available for profile.")
        persisted_nodes = self.all_nodes_in_workload_pool(
            node_attributes=["netsim"])
        log.logger.debug('Number of nodes selected: {0}'.format(len(persisted_nodes)))
        return persisted_nodes

    def set_bandwidth_and_latency_on_netsims(self, netsim_hosts):
        """
        Performs action on netsim: Changes values in netsim_cfg and make backup file of original netsim_cfg

        @param netsim_hosts: list of netsim hosts on which bandwidth and latency values need changes
        @type netsim_hosts: list
        """
        log.logger.debug("Using sed to change BANDWIDTH_ML and NETWORK_DELAY "
                         "values in {0} and creating backup: {0}bak".format(self.NETSIM_CFG_FILE_PATH))
        backup_change_values_cmd = ("sed -ribak -e 's/^(BANDWIDTH_ML\\=)(.*)$/\\1'{0}'/g' -e 's/^(NETWORK_DELAY\\=)(.*)"
                                    "$/\\1'{1}'/g' {2}".format(self.REQUIRED_BANDWIDTH, self.REQUIRED_LATENCY,
                                                               self.NETSIM_CFG_FILE_PATH))
        cmd = shell.Command("{0}".format(backup_change_values_cmd))
        for host in netsim_hosts:
            response = shell.run_remote_cmd(cmd, host, self.NETSIM_USER, self.NETSIM_PWD)
            if response.ok:
                log.logger.debug("Values changed in file: [{0}]"
                                 "and backup created [{0}bak on host [{1}]]".format(self.NETSIM_CFG_FILE_PATH, host))
                self.activate_changed_netsim_cfg(host)
            else:
                log.logger.debug("Unable to change values on host: [{0}]".format(host))

    def activate_changed_netsim_cfg(self, host):
        """
        Runs two commands on netsim to activate the new netsim_cfg configurations

        @param host: name of the host
        @type host: str
        """
        log.logger.debug("Activating the changed values in netsim_cfg file by using limitbw script")
        limitbw_path = "/netsim_users/pms/bin/limitbw"
        limitbw_logs_path = "/netsim_users/pms/logs/limitbw.log"
        bandwidth_limit_cmd = "{0} -n -c >> {1} 2>&1".format(limitbw_path, limitbw_logs_path)
        generate_band_report_cmd = "{0} -n -g >> {1} 2>&1".format(limitbw_path, limitbw_logs_path)
        cmd = "{0} && {1}".format(bandwidth_limit_cmd, generate_band_report_cmd)

        log.logger.debug("Executing command: [{0}] on host: [{1}]".format(cmd, host))
        response = netsim_executor.run_cmd(cmd, host)
        if response.ok:
            log.logger.debug("New limits applied to netsim host: [{0}]".format(host))
        else:
            self.add_error_as_exception(EnvironError("Unable to apply new limits on netsim host: [{0}]".format(host)))

    def get_unique_netsim_host_to_be_changed(self, nodes):
        """
        Performs checks on the host to ensure if changes could/should be made on host

        @param nodes: list of nodes to extract the host
        @type nodes: list
        @return: list of filtered hosts which need changes
        @rtype: list
        """
        netsim_hosts = set([node.netsim for node in nodes])
        modify_netsim_host_cfg = set()
        latency_bandwidth_values = ["BANDWIDTH_ML={0}".format(self.REQUIRED_BANDWIDTH),
                                    "NETWORK_DELAY={0}".format(self.REQUIRED_LATENCY)]
        for host in netsim_hosts:
            lines_in_netsim_cfg_file = get_lines_from_remote_file(self.NETSIM_CFG_FILE_PATH, host,
                                                                  self.NETSIM_USER, self.NETSIM_PWD)
            if any("BANDWIDTH_ML=" in line for line in lines_in_netsim_cfg_file):
                if all(line in lines_in_netsim_cfg_file for line in latency_bandwidth_values):
                    log.logger.debug(("Bandwidth and latency values correct on host: {0}".format(host)))
                else:
                    log.logger.debug(("netsim_cfg file on Host: {0} needs modification for bandwidth and latency"
                                      " values for mltn nodes".format(host)))
                    modify_netsim_host_cfg.add(host)
            else:
                log.logger.debug("BANDWIDTH_ML value does not exist in netsim_cfg file on host: [{0}]".format(host))

        return list(modify_netsim_host_cfg)

    def undo_changes(self, netsim_hosts):
        """
        Undo changes on the hosts which were modified by profile on teardown

        @param netsim_hosts: list of hosts
        @type netsim_hosts: list
        """
        log.logger.debug("Restoring the backup file on netsim and applying original values")
        delete_and_restore_netsim_cfg_cmd = "rm -f {0} && mv {0}bak {0}".format(self.NETSIM_CFG_FILE_PATH)
        cmd = shell.Command("{0}".format(delete_and_restore_netsim_cfg_cmd))
        remote_backup_file = "{0}bak".format(self.NETSIM_CFG_FILE_PATH)
        for host in netsim_hosts:
            if does_remote_file_exist(remote_backup_file, host, self.NETSIM_USER, self.NETSIM_PWD):
                log.logger.debug("Restoring the backup netsim_cfg file on host [{0}]".format(host))
                response = shell.run_remote_cmd(cmd, host, self.NETSIM_USER, self.NETSIM_PWD)
                if response.ok:
                    log.logger.debug("Backup file netsim_cfg restored successfully")
                    self.activate_changed_netsim_cfg(host)
                else:
                    log.logger.debug("Unable to restore the netsim_cfg file on [{0}].".format(host))
            else:
                log.logger.debug("backup file not found on host: [{0}]".format(host))
