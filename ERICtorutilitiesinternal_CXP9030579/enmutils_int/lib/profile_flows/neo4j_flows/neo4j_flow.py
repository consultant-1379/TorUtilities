from datetime import datetime, timedelta
import time
from functools import partial
from enmutils.lib import log, shell
from enmutils.lib.cache import is_enm_on_cloud_native, get_enm_cloud_native_namespace
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.exceptions import EnvironError, TimeOutError
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.enm_deployment import get_pod_hostnames_in_cloud_native
import pexpect

DISABLE_HEALTH_CHECK = "touch disable-neo4j-healthcheck"
STOP_LEADER = "/ericsson/3pp/neo4j/bin/neo4j stop"
START_NEO4J_NODE = "/ericsson/3pp/neo4j/bin/neo4j start"
ENABLE_HEALTH_CHECK = "rm -rf disable-neo4j-healthcheck"


def get_neo4j_leader_ip():
    """
    This method will run the command to get the list of DB clusters and then on each cluster runs a command to check if
    it is a neo4jleader
    :return:Neo4j system name
    :rtype:str
    :raises EnvironError: Exception raised run_cmd_on_ms gives exception
    """
    neo4j_leader = None
    response = shell.run_cmd_on_ms("sudo /opt/ericsson/enminst/bin/vcs.bsh --system -c db_cluster")
    log.logger.debug("Response after running command to get Neo4J DB clusters: {0}".format(response.stdout))
    if response.rc == 0:
        neo4j_system_ids = [i.strip(' ').split(' ')[0] for i in response.stdout.split("\n") if "ieat" in i]
        log.logger.debug("List of Neo4j DB clusters: {0}".format(neo4j_system_ids))
        for ip in neo4j_system_ids:
            response = shell.run_cmd_on_ms('/usr/bin/curl -s --user '
                                           'neo4j:Neo4jadmin123 '
                                           '"http://{0}:7474/db/manage/server/causalclustering/writable"'.format(ip))
            if response.stdout == "true":
                neo4j_leader = ip
                break
        log.logger.debug("Neo4J leader: {0}".format(neo4j_leader))
    else:
        raise EnvironError("Unable to get the neo4j leader ip due to {0}".format(response.stdout))

    return neo4j_leader


class Neo4JProfile01(GenericFlow):
    EXPIRE_TIME = 60

    def execute_flow(self):
        """
        Main flow for Neo4JProfile01
        """
        self.state = 'RUNNING'
        try:
            if hasattr(self, "SCHEDULED_DAYS"):
                while self.keep_running():
                    self.sleep_until_day()
                    self.neo4j_lock_unlock()
            else:
                self.neo4j_lock_unlock()
        except Exception as e:
            self.add_error_as_exception(e)

    def neo4j_lock_unlock(self):
        """
        This method is to execute the command to lock(freeze) or unlock (unfreeze) neo4j.
        """
        try:
            neo4j_leader = get_neo4j_leader_ip()
            if neo4j_leader:
                self.freeze_the_leader(neo4j_leader)
                self.teardown_list.append(partial(picklable_boundmethod(self.unfreeze_the_leader),
                                                  neo4j_leader))
                self.state = "SLEEPING"
                log.logger.debug("Sleeping for 5 Hours, before Un-locking neo4j leader")
                time.sleep(self.SLEEP_TIME)  # Sleep for specified hours
                self.state = "RUNNING"
                self.unfreeze_the_leader(neo4j_leader)
            else:
                raise EnvironError("Could not identify the Neo4J leader")
        except Exception as e:
            self.add_error_as_exception(e)

    def freeze_the_leader(self, neo4j_leader):
        """
        This method is to execute the command to lock(freeze) or unlock (unfreeze the DB cluster) based on the variable
        freeze and check if it got freeze or un-freeze properly
        :param neo4j_leader: system name for Neo4j leader
        :type neo4j_leader: str
        :raises TimeOutError: raises if there is timeout for more than defined 30 mins
        """
        try:
            result_code = "Result code: 0"
            cmd_lock = ("sudo mco rpc vcs_cmd_api lock nic_wait_timeout=60 switch_timeout=60 "
                        "sys={node} -I {node}").format(node=neo4j_leader)
            log.logger.debug("Attempting to execute the {0} command to lock the {1}".format(cmd_lock,
                                                                                            neo4j_leader))
            response = shell.run_cmd_on_ms(cmd_lock)
            log.logger.debug(response.stdout)
            if result_code in response.stdout:
                log.logger.debug("Successfully executed lock")
            else:
                log.logger.debug("Unable to lock the DB")

            expiry_time = datetime.now() + timedelta(minutes=self.EXPIRE_TIME)
            while datetime.now() < expiry_time:
                log.logger.debug("Sleeping for 200 secs before executing next command")
                time.sleep(200)
                log.logger.debug("Verifying if DB got locked")
                cmd_lock_check = ("sudo mco rpc vcs_cmd_api check_evacuated sys={node} "
                                  "-I {node}".format(node=neo4j_leader))
                log.logger.debug("Attempting to execute the {0} command to check the status".format(cmd_lock_check))
                response = shell.run_cmd_on_ms(cmd_lock_check)
                if result_code in response.stdout:
                    log.logger.debug("Successfully locked {0}".format(neo4j_leader))
                    break
                else:
                    log.logger.debug("Could not get proper response from executing the cmd to know if "
                                     "it is successfully locked")
            else:
                raise TimeOutError("Cannot identify if the DB got locked, got 30 mins time out and not able to get "
                                   "response 0 from check command")

        except Exception as e:
            self.add_error_as_exception(e)

    def unfreeze_the_leader(self, neo4j_leader):
        """
        This method is to execute the command to lock(freeze) or unlock (unfreeze the DB cluster) based on the variable
        freeze and check if it got freeze or un-freeze properly
        :param neo4j_leader: system name for Neo4j leader
        :type neo4j_leader: str
        :raises TimeOutError: raises if there is timeout for more than defined 30 mins
        """
        try:
            result_code = "Result code: 0"
            cmd_unlock = ("sudo mco rpc vcs_cmd_api unlock nic_wait_timeout=60 "
                          "sys={node} -I {node}").format(node=neo4j_leader)
            log.logger.debug("Attempting to execute the {0} command to un-lock the {1}".format(cmd_unlock, neo4j_leader))
            response = shell.run_cmd_on_ms(cmd_unlock)

            if result_code in response.stdout:
                log.logger.debug("Successfully executed unlock command")
            else:
                log.logger.debug("Unable to execute unlock command")

            expiry_time = datetime.now() + timedelta(minutes=self.EXPIRE_TIME)
            while datetime.now() < expiry_time:
                log.logger.debug("Sleeping for 200 secs before executing next command")
                time.sleep(200)
                log.logger.debug("Verifying if DB got un-locked")

                cmd_unlock_check = ("sudo mco rpc vcs_cmd_api check_cluster_online "
                                    "sys={node} -I {node}").format(node=neo4j_leader)
                log.logger.debug("Attempting to execute the {0} command to check the status".format(cmd_unlock_check))

                response = shell.run_cmd_on_ms(cmd_unlock_check)
                if result_code in response.stdout:
                    log.logger.debug("Successfully un-locked {0}".format(neo4j_leader))
                    break
                else:
                    log.logger.debug("Could not get proper response from executing the cmd to know if "
                                     "it is successfully un-locked")
            else:
                raise TimeOutError("Cannot identify if the DB got unlocked, got 30 mins time out and not able to get "
                                   "response 0 from check command")

        except Exception as e:
            self.add_error_as_exception(e)


class Neo4JProfile02(GenericFlow):
    EXPIRE_TIME = 60

    def execute_flow(self):
        """
        Main flow for Neo4JProfile02
        To turn down the Neo4j Leader for 6 hours and enable the neo4j node after 6 hours
        :raises EnvironError: If the pod is not available in cEnm
        """
        self.state = "RUNNING"
        try:
            if is_enm_on_cloud_native():
                while self.keep_running():
                    self.sleep_until_day()
                    vm_addresses = get_pod_hostnames_in_cloud_native('trouble')
                    if not vm_addresses:
                        raise EnvironError(" Failed to get the pod ip of Troubleshooting pod in cEnm")
                    else:
                        self.neo4j_flow(vm_addresses)
            else:
                raise EnvironError("Neo4j_02 profile will run in cenm deployments only.")
        except Exception as e:
            self.add_error_as_exception(e)

    def neo4j_flow(self, vm_addresses):
        """
        Flow To turn down the Neo4j Leader for 6 hours and enable the neo4j node after 6 hours
        :param vm_addresses: This is a troubleshooting pod vm address.
        :type vm_addresses: str
        :raises EnvironError: If one leader and two followers are not available in cEnm
        """
        cmd = '/opt/ericsson/neo4j/util/dps_db_admin.py cluster'
        command_response = shell.run_cmd_on_cloud_native_pod('troubleshooting-utils', vm_addresses[0], cmd)
        data = command_response.stdout
        if data.count('LEA') == 1 and data.count('FOL') == 2:
            log.logger.info('one leader and two followers are confirmed')
            leader = self.neo4j_leader_check()
            log.logger.info('Disabling the NEO4J health check')
            self.neo4j_command_execution(DISABLE_HEALTH_CHECK, leader)
            log.logger.info('Stopping the leader')
            self.neo4j_pexpect(STOP_LEADER, leader)
            self.teardown_list.append(partial(picklable_boundmethod(self.neo4j_command_execution), ENABLE_HEALTH_CHECK,
                                              leader))
            self.teardown_list.append(partial(picklable_boundmethod(self.neo4j_pexpect), START_NEO4J_NODE, leader))
            self.state = "SLEEPING"
            log.logger.info('The profile will sleep for six hours')
            time.sleep(self.SLEEP_TIME)  # Sleep for specified hours
            log.logger.info('starting the NEO4J node')
            log.logger.debug('Before starting time {0}'.format(datetime.now()))
            self.neo4j_pexpect(START_NEO4J_NODE, leader)
            self.check_dps_online(leader)
            log.logger.info('Enabling the NEO4J health check')
            self.neo4j_command_execution(ENABLE_HEALTH_CHECK, leader)
        elif data.count('LEA') == 0 and data.count('FOL') == 2:
            raise EnvironError("No leader available to continue the profile flow")
        else:
            raise EnvironError('less number of followers available to continue the profile flow')

    def neo4j_leader_check(self):
        """
        This method will run the command on the neo4j pods and consider the pod as leader if the command output is true
        :return:Neo4j leader system name
        :rtype:str
        :raises EnvironError: If vm addresses are not available in cEnm
        :raises EnvironError: If the command execution fails in cEnm
        """
        neo4j_leader = None
        vm_addresses = get_pod_hostnames_in_cloud_native('neo4j')
        if not vm_addresses:
            raise EnvironError(" Failed to get the pod ip of neo4j pod in cEnm")
        log.logger.debug("The neo4j pods are {0}".format(vm_addresses))
        for i in range(3):
            cmd = 'curl -s --user neo4j:Neo4jadmin123 -m 5 http://{0}:7474/db/dps/cluster/writable'.format(
                vm_addresses[i])
            command_response = shell.run_cmd_on_cloud_native_pod('neo4j', vm_addresses[i], cmd)
            if command_response.stdout == 'true':
                neo4j_leader = vm_addresses[i]
                log.logger.debug("The neo4j leader is {0}".format(neo4j_leader))
                break
            elif command_response.rc != 0:
                raise EnvironError("Unable to Execute the command {0} and the response {1}".
                                   format(cmd, command_response.stdout))
        return neo4j_leader

    def neo4j_command_execution(self, command, leader):
        """
        This method is to execute the commands as part Neo4j flow.
        :param command: command to execute on the pod
        :type command: str
        :param leader: leader pod of neo4j among all the neo4j pods
        :type leader: str
        :raises EnvironError: If the command execution fails in cEnm
        """
        log.logger.info('Executing the following command {0}'.format(command))
        command_response = shell.run_cmd_on_cloud_native_pod('neo4j', leader, command)
        if command_response.rc != 0:
            raise EnvironError("Unable to Execute the command {0} and the response {1}".
                               format(command, command_response.stdout))

    def neo4j_pexpect(self, command, leader):
        """
        This method is to execute the commands as part Neo4j flow using pexpect.
        :param command: command to execute on the pod
        :type command: str
        :param leader: leader pod of neo4j among all the neo4j pods
        :type leader: str
        :raises EnvironError: If the command execution fails in cEnm
        """
        child = pexpect.spawn(
            'kubectl -n {0} exec -it {1} -- bash'.format(get_enm_cloud_native_namespace(), leader, timeout=400))
        child.expect("neo4j")
        child.sendline(command)
        response = child.expect(['stopped', 'server is ready', pexpect.EOF, pexpect.TIMEOUT])
        log.logger.debug('The expect command output before {0} after {1}'.format(child.before, child.after))
        if response == 0:
            log.logger.info('The leader is stopped')
        elif response == 1:
            log.logger.info('started the NEO4J node')
            log.logger.debug('After starting time {0}'.format(datetime.now()))
        else:
            raise EnvironError("Unable to Execute the command {0} ".format(command))

    def check_dps_online(self, leader):
        """
        This method is to check the time it took to bring the pod online.
        :param leader: leader pod of neo4j among all the neo4j pods
        :type leader: str
        :raises TimeOutError: If the pod does not come to online
        """
        cmd = '''/opt/ericsson/neo4j/scripts/cluster_overview.py table  |sed "s/ \[[0-9;]*m//g" | grep "{0}" | grep "online"'''.format(leader)  # pylint: disable=W1401
        vm_addresses = get_pod_hostnames_in_cloud_native('trouble')
        count = -1
        try:
            expiry_time = datetime.now() + timedelta(minutes=self.EXPIRE_TIME)
            while datetime.now() < expiry_time:
                log.logger.debug("Verifying if {0} node is added to cluster and ready".format(leader))
                command_response = shell.run_cmd_on_cloud_native_pod('troubleshooting-utils', vm_addresses[0], cmd)
                count += 1
                if 'online' in command_response.stdout:
                    time_taken = count * 200
                    log.logger.debug("Successfully {0} is added to cluster and ready in {1} sec".format(leader,
                                                                                                        time_taken))
                    break
                else:
                    log.logger.debug("Could not get proper response from executing the cmd to know if "
                                     "it is successfully added to cluster")
                log.logger.debug("Sleeping for 200 secs before executing next command ")
                time.sleep(200)
            else:
                self.neo4j_command_execution(ENABLE_HEALTH_CHECK, leader)
                raise TimeOutError("Cannot identify if the node is added to cluster, got 30 mins time out and not able"
                                   "to get response 0 from check command")
        except Exception as e:
            self.add_error_as_exception(e)
