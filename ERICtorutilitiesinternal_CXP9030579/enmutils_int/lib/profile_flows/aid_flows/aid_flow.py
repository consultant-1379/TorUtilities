import time
from datetime import datetime, timedelta
from random import randint, sample

from enmutils.lib import log, timestamp
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import load_mgr
from enmutils_int.lib.auto_id_management import ClosedLoopAutoIdProfile, OpenLoopAutoIdProfile
from enmutils_int.lib.auto_id_management import (ManualAutoIdProfile, AutoIdTearDownProfile, TopologyGroupRange,
                                                 NonPlannedPCIRange)
from enmutils_int.lib.cellmgt import get_cell_name
from enmutils_int.lib.cellmgt import populate_node_cell_data
from enmutils_int.lib.common_utils import get_random_string
from enmutils_int.lib.load_node import annotate_fdn_poid_return_node_objects
from enmutils_int.lib.netex import Collection
from enmutils_int.lib.node_security import generate_node_batches
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


def parallel_executions(user, collection, identifier, loop, profile):
    frequencies = [2110.1, 2110.2, 2110.3, 2110.4]
    teardown = []
    log.logger.debug("Re-Connecting user session for {user}".format(user=user))
    user.open_session(reestablish=True)
    sleep_interval = profile.AID_PROFILE_SLEEP
    caught_exception = False
    if loop == 0:
        try:
            manual_loop_profile = ManualAutoIdProfile(user=user, name=identifier + get_random_string(6),
                                                      nodes=[], collection=collection)
            log.logger.debug(
                "Creating Manual AID profile {name} using user {user}".format(user=user, name=manual_loop_profile.name))
            manual_loop_profile.create()
            teardown_manual = ManualAutoIdProfile(user=user, name=manual_loop_profile.name, nodes=[],
                                                  collection=Collection(user=user, name=collection.name, nodes=[]))
            teardown_manual.profile_id = manual_loop_profile.profile_id
            teardown.append(teardown_manual)
            log.logger.debug(
                "Sleeping for {sleep_interval} seconds before deleting: {name} ".format(sleep_interval=sleep_interval,
                                                                                        name=manual_loop_profile.name))
            time.sleep(sleep_interval)
            log.logger.debug(
                "Deleting Manual AID profile {name} using user {user}".format(user=user, name=manual_loop_profile.name))
            manual_loop_profile.delete()
        except Exception as e:
            caught_exception = True
            profile.add_error_as_exception(e)
    if loop == 1:
        try:
            topology_group_range = TopologyGroupRange(user=user, name=identifier + get_random_string(6),
                                                      collection=collection, nodes=[])
            log.logger.debug(
                "Creating Topology Group Range profile {name} using user {user}".format(user=user,
                                                                                        name=topology_group_range.name))
            topology_group_range.create()
            teardown_topology = TopologyGroupRange(user=user, name=topology_group_range.name,
                                                   collection=Collection(user=user, name=collection.name, nodes=[]))
            teardown_topology.profile_id = topology_group_range.range_id
            teardown.append(teardown_topology)
            log.logger.debug(
                "Sleeping for {sleep_interval} seconds before deleting: {name} ".format(sleep_interval=sleep_interval,
                                                                                        name=topology_group_range.name))
            time.sleep(sleep_interval)
            log.logger.debug(
                "Deleting Topology Group Range profile {name} using user {user}".format(user=user,
                                                                                        name=topology_group_range.name))
            topology_group_range.delete()
        except Exception as e:
            caught_exception = True
            profile.add_error_as_exception(e)
    if loop == 2:
        try:
            non_planned_group_range = NonPlannedPCIRange(user=user, frequency=sample(frequencies, 1)[0],
                                                         pci_ranges={randint(2, 167): randint(0, 2)})
            log.logger.debug("Creating Non Planned PCI Range using user {user}".format(user=user))
            non_planned_group_range.create()
            teardown.append(non_planned_group_range)
            log.logger.debug("Sleeping for {sleep_interval} seconds before deleting "
                             "Non Planned PCI Range".format(sleep_interval=sleep_interval))

            time.sleep(sleep_interval)
            log.logger.debug("Deleting Non Planned PCI Range using user {user}".format(user=user))
            non_planned_group_range.delete()
        except Exception as e:
            caught_exception = True
            profile.add_error_as_exception(e)
    if caught_exception and teardown:
        sleep_time = randint(400, 600)
        log.logger.debug("Sleeping for {0} seconds before running teardown".format(sleep_time))
        time.sleep(sleep_time)
        for obj in teardown:
            obj._teardown()
        log.logger.debug("Error caught in the thread queue: {0}".format(str(e)))


def _wait_for_setup_profile(profile):
    """
    wait for AID_SETUP profile to go to COMPLETED state with OK status
    """
    try:

        load_mgr.wait_for_setup_profile("AID_SETUP", state_to_wait_for="COMPLETED", status="OK", timeout_mins=5,
                                        sleep_between=20)
    except Exception as e:
        profile.add_error_as_exception(EnvironError(e))
        return False


class Aid01Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the profiles flow

        """
        if _wait_for_setup_profile(self):
            users = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, safe_request=True, retry=True)
            nodes = self.get_nodes_list_by_attribute(['node_id', 'poid'])
            collection = Collection(user=users[0], name="AID_01_COLLECTION_{0}".format(self.identifier),
                                    nodes=nodes)
            collection_created = False
            try:
                collection.create()
                collection_created = True
            except Exception as e:
                self.add_error_as_exception(
                    EnmApplicationError("Unable to create a collection via NetworkExplorer in ENM - {0}".format(str(e))))

            if collection_created:
                self.teardown_list.append(picklable_boundmethod(collection.delete))
                self.state = "RUNNING"

                while self.keep_running():

                    for i in xrange(3):
                        self.sleep_until_time()
                        self.create_and_execute_threads(workers=users, thread_count=len(users),
                                                        func_ref=parallel_executions,
                                                        args=[collection, self.identifier, i, self],
                                                        wait=60 * 60, join=5 * 60)


class Aid02Flow(GenericFlow):

    def execute_flow(self):  # NOSONAR
        """
        Executes the profiles flow

        """
        if _wait_for_setup_profile(self):
            auto_id_objects = self.get_aid_profile_objects()
            if auto_id_objects:
                self.state = "RUNNING"
                while self.keep_running():
                    self.sleep_until_time()
                    for manual_profile in auto_id_objects:
                        try:
                            manual_profile.check()
                            manual_profile.calculate()
                            manual_profile.resolve()
                        except Exception as e:
                            self.add_error_as_exception(e)
                        finally:
                            manual_profile.profile_clean()
                            for exception in manual_profile.exceptions:
                                self.add_error_as_exception(exception)
            else:
                log.logger.debug("No aid profiles were created, refer profile log")

    def get_aid_profile_objects(self):
        """
        Get aid profile objects

        :return: list of aid profile objects
        :rtype: list
        """

        nodes = self.get_nodes_list_by_attribute(['node_id', 'poid'])
        nodes_verified_on_enm = None
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        self.set_schedule_time()
        try:
            nodes_verified_on_enm = annotate_fdn_poid_return_node_objects(nodes)
        except Exception as e:
            self.add_error_as_exception(EnvironError('Node verification Failed. Manual Auto ID profile not created. '
                                                     'The exception reason is {0}'.format(e)))
        if nodes_verified_on_enm:
            return self.create_manual_aid_profiles(nodes_verified_on_enm, user)
        else:
            log.logger.warning('No nodes verified on ENM available. Manual Auto ID profile not created.')

    def set_schedule_time(self):
        """
        Sets SCHEDULED_TIMES

        """
        start_time = datetime.strptime(self.SCHEDULED_TIMES_STRINGS[0], '%H:%M:%S').replace(year=datetime.now().year,
                                                                                            month=datetime.now().month,
                                                                                            day=datetime.now().day)
        setattr(self, 'SCHEDULED_TIMES', [start_time + timedelta(hours=hour) for hour in xrange(0, 23, self.FREQUENCY)])

    def return_grouping_list(self, nodes=None):
        """
        It gathers the number of nodes that should be run in each AutoID profile, the initial and last node and returns
        them in a list so AID_02 in all the nodes using different AutoID profiles

        :param nodes: list of nodes allocated to profile
        :type nodes: list
        :return: a list with the index of nodes for each profile
        :rtype: list
        """
        nodes_grouping = []
        nodes_group = len(nodes) / self.NUM_PROFILES
        for i in xrange(0, self.NUM_PROFILES):
            if i == self.NUM_PROFILES - 1:
                nodes_grouping.append(len(nodes))
            else:
                nodes_grouping.append((i + 1) * nodes_group)
        log.logger.debug(
            'Running profile with {0}, each profile will run with {1} nodes'.format(len(nodes), nodes_group))
        log.logger.debug('List {0}'.format(nodes_grouping))
        return nodes_grouping

    def create_manual_aid_profiles(self, nodes, user):
        """
        Creates auto id profile Objects

        :param nodes: list of node objects
        :type nodes: list
        :param user: user to create aid profile
        :type user: enm_user.User object
        :return: list of manual aid profile objects
        :rtype: list
        """

        auto_id_profiles = []
        nodes_grouping = self.return_grouping_list(nodes)
        validation_timeout = self.AID_PROFILE_TIMEOUT
        for i in range(self.NUM_PROFILES):
            begin = 0 if i == 0 else nodes_grouping[i - 1]
            end = nodes_grouping[i] if i == (self.NUM_PROFILES - 1) else nodes_grouping[i] - 1
            log.logger.debug('AID profile {0} using nodes from {1} to {2}'.format(i, begin, end))
            log.logger.debug('Begin: {0} to end {1}'.format(begin, end))
            try:
                auto_id_profiles.append(
                    ManualAutoIdProfile(user=user, name=self.identifier, nodes=nodes[begin:end],
                                        validation_timeout=validation_timeout,
                                        options={"checkTopologyGroupRange": True,
                                                 "checkNonPlannedPci": True,
                                                 "checkD": True,
                                                 "checkSM30": True,
                                                 "checkNNM30": True,
                                                 "checkNM30": True,
                                                 "checkTemporaryValues": True,
                                                 "checkReservedValues": True,
                                                 "checkRSShifted": False,
                                                 "checkRSNonShifted": True,
                                                 "checkRSAggregated": True,
                                                 "checkSCellsBlacklistedPciValues": True,
                                                 "checkNNCellsBlacklistedPciValues": True,
                                                 "checkNCellsBlacklistedPciValues": True,
                                                 "checkDMinCellDistanceInKilometers": True}))
            except Exception as e:
                self.add_error_as_exception(e)

        for profile in auto_id_profiles[:]:
            try:
                log.logger.debug("Creating AID profile {0}".format(profile.name))
                profile.create()
                teardown_profile = AutoIdTearDownProfile(profile.user, profile.name,
                                                         collection_id=profile.collection.id,
                                                         profile_id=profile.profile_id)
                self.teardown_list.append(picklable_boundmethod(teardown_profile.teardown))
            except Exception as e:
                log.logger.debug("Failed to create AID profile {0}".format(profile.name))
                self.add_error_as_exception(e)
                auto_id_profiles.remove(profile)

        return auto_id_profiles


class Aid03Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the profiles flow

        """
        if _wait_for_setup_profile(self):
            user = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, safe_request=True, retry=True)[0]
            self.state = "RUNNING"
            nodes = self.get_nodes_list_by_attribute(['node_id', 'poid'])
            nodes_verified_on_enm = annotate_fdn_poid_return_node_objects(nodes)
            try:
                open_loop_profile = OpenLoopAutoIdProfile(user=user, name=self.identifier, nodes=nodes_verified_on_enm,
                                                          options={"checkEnodebDetected": False,
                                                                   "checkD": False,
                                                                   "checkRS": False,
                                                                   "checkTemporaryValues": False,
                                                                   "checkReservedValues": False})
                open_loop_profile.create()
                self.teardown_list.append(picklable_boundmethod(open_loop_profile.teardown))
            except Exception as e:
                self.add_error_as_exception(e)


class Aid04Flow(GenericFlow):

    def execute_flow(self):  # NOSONAR
        """
        Executes the profiles flow
        """

        if _wait_for_setup_profile(self):

            self.state = "RUNNING"
            user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES, safe_request=True)[0]
            nodes = self.get_nodes_list_by_attribute(node_attributes=['poid', 'node_id', 'node_version', 'lte_cell_type'])
            nodes_verified_on_enm = None

            try:
                nodes_verified_on_enm = annotate_fdn_poid_return_node_objects(nodes)
            except Exception as e:
                self.add_error_as_exception(e)

            if nodes_verified_on_enm:
                tdd_nodes = [node for node in nodes_verified_on_enm if node.lte_cell_type == "TDD"]
                fdd_nodes = [node for node in nodes_verified_on_enm if node.lte_cell_type == "FDD"]
                node_cell_data = self.get_node_cell_data(user, [tdd_nodes, fdd_nodes])
                profile_time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 1, 0, 0)

                close_loop_profile = ClosedLoopAutoIdProfile(user=user, name=self.identifier, nodes=nodes_verified_on_enm,
                                                             scheduled_times=[profile_time])

                try:
                    close_loop_profile.create()
                    self.teardown_list.append(picklable_boundmethod(close_loop_profile.teardown))
                except Exception as e:
                    close_loop_profile = None
                    self.add_error_as_exception(EnmApplicationError("Failed creating AID profile. "
                                                                    "Message error: {0}".format(e.message)))

                if close_loop_profile:
                    while self.keep_running():
                        self.sleep_until_time()
                        try:
                            self.update_cells_attributes_via_netsim(node_cell_data, nodes_verified_on_enm)
                            log.logger.info('{0} Nodes injected with same PCI values.'.format(len(nodes_verified_on_enm)))
                        except Exception as e:
                            self.add_error_as_exception(EnmApplicationError(e))

    def get_node_cell_data(self, user, node_lists):
        """
        Query cell management application for cell information.

        :param user: ENM User who will perform the query
        :type user: `enm_user_2.user`
        :param node_lists: List containing cell type sorted lists of nodes
        :type node_lists: list

        :return: Dictionary containing the cell data for the respective nodes
        :rtype: dict
        """
        node_cell_data = {}
        for nodes in node_lists:
            if nodes:
                cell_type = nodes[0].lte_cell_type
                node_cell_data.update(populate_node_cell_data(user, 4, "EUtranCell{0}".format(cell_type), nodes,
                                                              self.MO_ATTRIBUTE_DATA.get(cell_type),
                                                              set_new_attributes_to_zero=True))
        return node_cell_data

    def update_cells_attributes_via_netsim(self, node_cell_data, nodes_for_injection):
        """
        Executing the netsim command to updating the node cell attributes.

        :param node_cell_data: dict containing nodes, cell_fdn's, attributes and corresponding new & default values
        :type node_cell_data: dict
        :param nodes_for_injection: list of nodes objects
        :type nodes_for_injection: list
        :raises EnmApplicationError: raised if modify cell request fails
        """
        node_batches = generate_node_batches(nodes_for_injection, batch_size=self.NUM_NODES_PER_BATCH)
        self.create_and_execute_threads(workers=node_batches, thread_count=len(node_batches),
                                        func_ref=self.set_aid_inconsistencies_on_nodes, args=[self, node_cell_data])

    @staticmethod
    def set_aid_inconsistencies_on_nodes(nodes, profile, node_cell_data):  # pylint: disable=arguments-differ
        """
        Executing the netsim command to updating the node cell attributes.

        :type nodes: list
        :param nodes: list of nodes objects.
        :type profile: `lib.profile.Profile`
        :param profile: Profile executing the threads to add exceptions to
        :param node_cell_data: dict containing nodes, cell_fdn's, attributes and corresponding new & default values
        :type node_cell_data: dict
        :raises EnmApplicationError: raised if modify cell request fails

        """
        run_type = profile.RUN_TYPE
        exceptions = []
        start = timestamp.get_current_time()
        node_counter = cell_counter = 1
        failed_cell_names = []
        for node in nodes:
            node_name = node.node_id
            for cell_fdn in node_cell_data[node_name]:
                cell_name = get_cell_name(cell_fdn)
                log.logger.debug(
                    "# {run_type} attribute values being set on node {node_counter}/{node_total_count}: "
                    "{node_name}, cell {cell_counter}: {cell_name} ".format(run_type=run_type,
                                                                            cell_counter=cell_counter,
                                                                            cell_name=cell_name,
                                                                            node_counter=node_counter,
                                                                            node_total_count=len(nodes),
                                                                            node_name=node_name))
                try:
                    netsim_node_command = ('setmoattribute:mo="{source_fdn}",attributes="physicalLayerCellIdGroup={'
                                           'physical_layer_cellid_group} ||physicalLayerSubCellId={'
                                           'physical_layer_sub_cellid}";')

                    netsim_node_command = netsim_node_command.format(source_fdn=','.join(cell_fdn.split(',')[-3:]),
                                                                     physical_layer_cellid_group=node_cell_data[node_name]
                                                                     [cell_fdn][run_type]['physicalLayerCellIdGroup'],
                                                                     physical_layer_sub_cellid=node_cell_data[node_name]
                                                                     [cell_fdn][run_type]['physicalLayerSubCellId'])

                    if not profile.execute_netsim_command_on_netsim_node([node], netsim_node_command):
                        raise Exception("Problems encountered while executing the netsim command to "
                                        "updating the cell attributes on {0} node".format(node_name))
                except Exception as e:
                    failed_cell_names.append(cell_name)
                    log.logger.debug(str(e))
                    exceptions.append(e)

                cell_counter += 1

            node_counter += 1

        finish = timestamp.get_current_time() - start
        time_taken = timestamp.get_string_elapsed_time(finish)
        log.logger.debug("# This iteration took {time_taken}s to complete".format(time_taken=time_taken))
        if exceptions:
            log.logger.debug(
                "Iteration failed to change PCI values for {0}/{1} cells - see logs for "
                "details".format(len(failed_cell_names), cell_counter))

            profile.add_error_as_exception(EnmApplicationError("Operation has encountered errors, "
                                                               "please check the logs for more information."))
