import datetime
import random
from time import sleep
from functools import partial
from paramiko import SSHException
from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import load_mgr, node_pool_mgr
from enmutils_int.lib.fmx_mgr import FmxMgr
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services import nodemanager_adaptor


class FMX05(GenericFlow):
    fmx_mgr = None

    def execute_fmx_05_flow(self):
        """
        executes the fmx_05 profile flow
        """
        nsx_module = "NSX_Maintenance_filter"
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES, safe_request=True)[0]
        load_mgr.wait_for_setup_profile("FMX_01", state_to_wait_for='SLEEPING', sleep_between=60, timeout_mins=30)
        self.fmx_mgr = FmxMgr(user=user, all_modules=[nsx_module])
        self.teardown_list.append(partial(picklable_boundmethod(self.fmx_mgr._teardown), profile=self))
        initial_run = True
        self.state = "RUNNING"

        while self.keep_running():
            # STEP 1: Remove Old Entries
            self.remove_expired_old_entries()

            # STEP 2: Create New Entries
            self.fmx_mgr.nodes_signatures = []
            start_timestamp = datetime.datetime.now()
            end_timestamp = start_timestamp + datetime.timedelta(seconds=self.SCHEDULE_SLEEP)
            available_nodes = self.fetch_nodes_for_the_profile()
            if len(available_nodes) >= 3:
                total_nodes_per_mode = self.node_allocation_and_different_operations_on_nodes(
                    available_nodes, nsx_module, initial_run)
                initial_run = False
                self.set_available_nodes_into_maintenance_modes(available_nodes, total_nodes_per_mode, start_timestamp,
                                                                end_timestamp)
            else:
                log.logger.debug("Required Number of nodes are not available to continue the flow...")
            node_mgr = nodemanager_adaptor if self.nodemanager_service_can_be_used else node_pool_mgr
            node_mgr.deallocate_nodes(self)
            nodes_list = self.get_nodes_list_by_attribute()
            self.num_nodes = len(nodes_list)
            self.sleep()

    def node_allocation_and_different_operations_on_nodes(self, available_nodes, nsx_module, initial_run):
        """
        Allocate nodes to the profile, if it is initial run then profile will load and activate the FMX module
        or it will deactivate and activate the FMX module with the given set of nodes nodes
        :param available_nodes: list of nodes
        :type available_nodes: list
        :param nsx_module: FMX module
        :type nsx_module:str
        :param initial_run: Boolean True for initial run and False from next iterations
        :type initial_run: bool
        :return: Total number of nodes for each mode
        :rtype: int
        """
        log.logger.info("Nodes fetched from FM profiles are : {0}".format(available_nodes))
        self.allocate_specific_nodes_to_profile(available_nodes)
        self.num_nodes = len(available_nodes)
        log.logger.info("allocated {0} nodes to profile".format(self.num_nodes))
        self.persist()
        if initial_run:
            log.logger.info("Will load and activate {0}".format(nsx_module))
            self.load_and_activate_nsx_maintenance_filter(available_nodes)
        else:
            log.logger.info("Will de-activate and activate the module by updating the nodes")
            self.deactivate_and_activate_maintenance_filter_on_given_nodes(available_nodes, nsx_module)
        total_nodes_per_mode = len(available_nodes) / len(self.MAINTENANCE_MODES)
        return total_nodes_per_mode

    def set_available_nodes_into_maintenance_modes(self, available_nodes, total_nodes_per_mode, start_time, end_time):
        """
        Set nodes into respective maintenance modes ('MARK' , 'NMS', 'NSSandOSS')
        :param available_nodes: list of nodes
        :type available_nodes: list
        :param total_nodes_per_mode: no.of nodes per each mode
        :type total_nodes_per_mode: int
        :param start_time: starting time of the maintenance mode for nodes
        :type start_time: str
        :param end_time: expire time of the maintenance mode for nodes
        :type end_time: str
        """
        for mode in self.MAINTENANCE_MODES:
            try:
                assigned_nodes = available_nodes[:total_nodes_per_mode]
                log.logger.debug("setting maintenance mode {0} on {1} nodes".format(mode, len(assigned_nodes)))
                self.fmx_mgr.set_maintenance_mode_for_nodes(assigned_nodes, mode, start_time, end_time)
                del available_nodes[:total_nodes_per_mode]
            except Exception as e:
                self.add_error_as_exception(e)

    def fetch_nodes_for_the_profile(self):
        """
        Will fetch the nodes allocated to FM_01 profile and returns random nodes of given count
        :return: random nodes of given number
        :rtype: list
        """
        nodes_list = []
        required_nodes = []
        try:
            for profile in self.FETCH_NODES_FROM:
                nodes_list.extend(self.get_allocated_nodes(profile))
            log.logger.info("Total number of nodes fetched : {0}".format(len(nodes_list)))
            if len(nodes_list) > 0:
                new_nodes_list = [node for node in nodes_list if node.primary_type in self.NODE_TYPES]
                for node in new_nodes_list:
                    if node.primary_type == 'RadioNode' and node.managed_element_type != 'ENodeB':
                        continue
                    required_nodes.append(node)
                log.logger.info("Total nodes of required types : {0}".format(len(required_nodes)))
                if len(required_nodes) >= self.NODE_COUNT:
                    return random.sample(required_nodes, self.NODE_COUNT)
                else:
                    log.logger.info("Continuing with the available {} nodes".format(len(required_nodes)))
                    return required_nodes
            else:
                log.logger.info("The profile could not fetch nodes as the FM_01,FM_02 profiles are not running on the"
                                "deployment.Please start the above mentioned profiles and restart FMX_05 for the "
                                "nodes to be allocated to the FMX_05 profile")
                return required_nodes
        except Exception as e:
            self.add_error_as_exception(e)

    def remove_expired_old_entries(self):
        """
        removes old expired node entries from maintenance
        """
        try:
            # Speed up teardown by removing expired entries
            log.logger.debug("Removing expired node entries from maintenance")
            self.fmx_mgr.remove_expired_node_entries_from_maintenance()
        except (SSHException, RuntimeError) as e:
            error_msg = ('ERROR: Could not remove old maintenance entries due to environmental issue.'
                         'Check Workload FAQ page for known issues and limitations.')
            log.logger.debug('** ' + error_msg + ' Exception was: {0}'.format(str(e)))
            self.add_error_as_exception(EnvironError(error_msg))
        except Exception as e:
            self.add_error_as_exception(e)

    def load_and_activate_nsx_maintenance_filter(self, profile_nodes):
        """
        Loads and activated the module on given set of nodes
        :param profile_nodes: nodes on which the module is to be activated
        :type profile_nodes: list
        """
        try:
            self.fmx_mgr.import_load()
            self.fmx_mgr.activate_fmx_modules(nodes=profile_nodes, entire_network=False)
            log.logger.info("Loaded and activated the module successfully")
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))

    def deactivate_and_activate_maintenance_filter_on_given_nodes(self, profile_nodes, module):
        """
        De-activates and Activates the FMX module with the given set of nodes
        :param profile_nodes: nodes on which the module is to be activated
        :type profile_nodes: list
        :param module: name of the fmx module
        :type module: str
        """
        try:
            self.fmx_mgr._deactivate_module(module)
            log.logger.info("De-activated the module")
            log.logger.info("sleeping for 120 sec before re-activating the module with given nodes")
            sleep(120)
            self.fmx_mgr.activate_fmx_modules(nodes=profile_nodes, entire_network=False)
            log.logger.info("Activated the module")
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))
