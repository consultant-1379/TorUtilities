import re
import time
from functools import partial
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib import log
from enmutils.lib.exceptions import (EnvironError, EnmApplicationError)
from enmutils_int.lib.profile_flows.secui_flows.secui_flow import SecuiFlow
from enmutils_int.lib.node_security import generate_node_batches
from enmutils_int.lib.node_pool_mgr import group_nodes_per_netsim_host

NODE_FTPES_CMD = "secadm ftpes {action} --nodelist {nodes_list}"
NODE_FTPES_STATUS_CMD = "secadm ftpes getstatus --nodelist {nodes_list}"
NODE_FTPES_ACTION_VERIFICATION = "Successfully started a job for FTPES {action} operation"


class Ftpes01Flow(SecuiFlow):
    MAX_POLL = 4

    def __init__(self, *args, **kwargs):
        super(Ftpes01Flow, self).__init__(*args, **kwargs)
        self.user = None

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        self.user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        self.state = "RUNNING"
        try:
            nodes = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'netsim', "profiles", "oss_prefix"])
            if nodes:
                nodes_list = self.ftpes_profile_prerequisites(nodes)
                self.toggle_ftpes(nodes_list)
            else:
                raise EnvironError("Profile is not allocated to any node")
        except Exception as e:
            self.add_error_as_exception(e)

    def toggle_ftpes(self, nodes_list):
        """
        Function to be used to generate the node batches and activate the ftpes on every node batches

        :param nodes_list: List of enm_node.Node objects
        :type nodes_list:  list
        :raises EnvironError: if any method throws error
        :raises Exception: if any method throws error
        """
        try:
            node_batches = generate_node_batches(nodes_list, batch_size=self.NUM_NODES_PER_BATCH)
            log.logger.debug("{0} node batches are generated".format(len(node_batches)))
            for node_batch in node_batches:
                self.toggle_ftpes_on_nodes(node_batch, "activate")
                self.teardown_list.append(partial(picklable_boundmethod(self.toggle_ftpes_on_nodes), node_batch,
                                                  "deactivate"))
                self.get_nodes_ftpes_status(node_batch, "activate")
        except Exception as e:
            raise EnvironError(e)

    def toggle_ftpes_on_nodes(self, nodes, action):
        """
        Function to be used to activate/deactivate the FTPES on nodes

        :param nodes: List of enm_node.Node objects
        :type nodes:  list
        :param action: activate or deactivate the ftpes on nodes
        :type action: str

        :raises EnmApplicationError: when node ftpes activation/deactivation command not executed.
        """
        try:
            node_ids = ','.join(node.node_id for node in nodes)
            log.logger.debug('Attempting to execute {0} FTPES command on {1} nodes'.format(action, len(nodes)))
            response = self.user.enm_execute(NODE_FTPES_CMD.format(action=action, nodes_list=node_ids))
            enm_output = response.get_output()
            if not re.search(NODE_FTPES_ACTION_VERIFICATION.format(action=action), enm_output[0]):
                raise EnmApplicationError(
                    "Cannot {0} the FTPES on {1} nodes due to {2}".format(action, len(nodes),
                                                                          response.get_output()))

            log.logger.debug(
                'Successfully initiated {0} FTPES command on {1} nodes'.format(action, len(nodes)))
            job_status_cmd = str(re.split("'*'", enm_output[0])[1])
            log.logger.debug("Command to get status for {0} FTPES job: '{1}'".format(action, job_status_cmd))
            if action == "activate":
                self.get_current_job_status(job_status_cmd)
                self.check_any_nodes_in_error_state(job_status_cmd)
        except Exception as e:
            self.add_error_as_exception(EnvironError(e))

    def check_any_nodes_in_error_state(self, job_status_cmd):
        """
        This function will verify if any nodes in error state

        :param job_status_cmd: command to execute job status
        :type job_status_cmd: str
        """
        job_status_response = self.user.enm_execute(job_status_cmd)
        enm_output = [line for line in job_status_response.get_output() if self.get_node_error_state(line)]
        if enm_output:
            enm_output = '\n'.join(enm_output)
            log.logger.debug('Checking the error status of secadm job using command {0} and encountered the error as follows {1}\n'.
                             format(job_status_cmd, enm_output))
        else:
            log.logger.debug('Successfully activated ftpes on all the, no nodes are in error state')

    def get_node_error_state(self, line):
        """
        This function will return if any nodes in error state

        :param line: job_status_cmd output line
        :type line: str
        :return: List of nodes in ERROR state
        :rtype: list
        """
        pattern = r'{}'.format('ERROR')
        matches = re.findall(pattern, line)
        return matches

    def get_current_job_status(self, job_status_cmd, job_type="FTPES"):
        """
        Function to be used to get activate/deactivate job status

        :param job_status_cmd: command to execute job status
        :type job_status_cmd: str
        :param job_type: type of job
        :type job_type: str

        :raises EnvironError: If job status has not been completed within expected time/Max_poll
        """
        job_complete_status = False
        poll = 1
        while not job_complete_status and poll <= self.MAX_POLL:
            log.logger.debug('POLL_COUNT: {0}, MAX_POLL: {1}'.format(poll, self.MAX_POLL))
            try:
                log.logger.debug("Execute {0} command to get current {1} job status".format(job_status_cmd, job_type))

                job_status_response = self.user.enm_execute(job_status_cmd)
                if (job_status_response and len(job_status_response.get_output()) > 2 and
                        job_status_response.get_output()[1].split('\t')[3] == 'COMPLETED'):
                    log.logger.debug("Job status has been successfully completed")
                    job_complete_status = True

                if not job_complete_status:
                    log.logger.debug("Sleeping for {0} seconds until {1} job status in COMPLETED "
                                     "state..".format(self.JOB_STATUS_CHECK_INTERVAL, job_type))
                    time.sleep(self.JOB_STATUS_CHECK_INTERVAL)
                    poll += 1
            except Exception as e:
                log.logger.debug("Failed to get current job status:{0}".format(e))
                self.add_error_as_exception(EnvironError(e))
                break
        if poll > self.MAX_POLL:
            log.logger.debug('MAX_POLL limit reached - {0} retries in {1} seconds'.format(self.MAX_POLL,
                                                                                          self.MAX_POLL * self.JOB_STATUS_CHECK_INTERVAL))
            raise EnvironError('FTPES Job status has not completed within expected retries: {0} '.format(self.MAX_POLL))

    def get_required_nodes(self, nodes, network_percent=0.5):
        """
        Function to be used to get the percentage of nodes from each netsim box from network.
        :param nodes: List of enm_node.Node objects
        :type nodes: list
        :param network_percent: percentage of nodes. The default network percent value is 0.5
        :type network_percent: float
        :return: List of `enm_node.Node` instances
        :rtype: list
        """
        nodes_list = []
        netsim_hosts_with_nodes = group_nodes_per_netsim_host(nodes)
        log.logger.debug("Successfully fetched {0} netsim boxes".format(len(netsim_hosts_with_nodes)))
        for _, nodes in netsim_hosts_with_nodes.iteritems():
            nodes_list += nodes[:int(round(network_percent * len(nodes)))]
        log.logger.debug("Successfully fetched {0} nodes from all netsim boxes".format(len(nodes_list)))
        return nodes_list

    def ftpes_profile_prerequisites(self, nodes):
        """
        Get the percentage of nodes takes from percentage of netsims and verifying these nodes are synced,
        configured with ldap or not
        :type nodes: list
        :param nodes: List of `enm_node.Node` instances
        :return: list of specific percentage of synced, ldap configured nodes
        :rtype: list
        :raises EnvironError: when nodes are not synced or not configured with ldap
        """
        netsim_nodes = []
        synced_nodes = self.get_synchronised_nodes(nodes, self.user)
        log.logger.debug("{0} synced radio nodes: {1}".format(len(synced_nodes),
                                                              [node.node_id for node in synced_nodes]))
        if synced_nodes:
            ldap_configured_nodes = self.check_ldap_is_configured_on_nodes(self.user, synced_nodes)
            if ldap_configured_nodes:
                netsim_nodes = self.get_required_nodes(ldap_configured_nodes, self.NETWORK_PERCENT)
                log.logger.debug("{0}% of nodes taken from network: {1} nodes".format(
                    int(self.NETWORK_PERCENT * 100), len(netsim_nodes)))
                unused_nodes = [node for node in nodes if node not in netsim_nodes]
                self.update_profile_persistence_nodes_list(list(unused_nodes))
            else:
                raise EnvironError("Nodes not LDAP configured")
        else:
            raise EnvironError("Synced nodes are not available")
        return netsim_nodes

    def get_nodes_ftpes_status(self, nodes, action):
        """
        Retrieve the FTPES status for supplied nodes

        :param nodes: List of enm_node.Node objects
        :type nodes:  list
        :param action: activate or deactivate the ftpes on nodes
        :type action: str

        :raises EnmApplicationError: when node get ftpes status command not executed.
        """
        try:
            log.logger.debug('Attempting to execute the get nodes FTPES status command')
            response = self.user.enm_execute("cmedit get * ComConnectivityinformation.fileTransferProtocol==FTPES")
            enm_output = response.get_output()
            if "Error" in "\n".join(enm_output):
                raise EnmApplicationError(
                    "Error occurred while getting FTPES status for {0} nodes due to {1}".format(len(nodes),
                                                                                                response.get_output()))
            if response and enm_output:
                self.get_success_and_failed_node_ftpes_status(action, enm_output, nodes)
        except Exception as e:
            self.add_error_as_exception(e)

    def get_success_and_failed_node_ftpes_status(self, action, enm_output, nodes):
        """
        Get success and failed node ftpes activate/deactivate status

        :param action: Activate or deactivate ftpes status on nodes
        :type action: str
        :param enm_output: Ftpes status command output
        :type enm_output: list
        :param nodes: List of enm_node.Node objects
        :type nodes: list
        """
        total_ftpes_enabled_nodes = [str(node).split(',')[0].split('=')[1]
                                     for node in enm_output if str(node).startswith("FDN")]
        log.logger.debug("Total ftpes enabled nodes : {0}".format(len(total_ftpes_enabled_nodes)))
        success_node_status = []
        failed_node_status = []
        for node in nodes:
            if node.node_id in total_ftpes_enabled_nodes:
                success_node_status.append(node)
            else:
                failed_node_status.append(node)

        if failed_node_status:
            self.add_error_as_exception(EnmApplicationError("Failed to {0} FTPES on {1} nodes out of {2} nodes"
                                                            .format(action, len(failed_node_status), len(nodes))))
        log.logger.debug('Successfully {0}d FTPES on {1} nodes out of {2} nodes'.format(
            action, len(success_node_status), len(nodes)))
