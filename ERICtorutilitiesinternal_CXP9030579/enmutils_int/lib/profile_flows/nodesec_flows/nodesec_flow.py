import os
import time
import re
from datetime import datetime
from functools import partial
from enmutils.lib import log, filesystem
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import load_mgr
from enmutils_int.lib.common_utils import split_list_into_sublists
from enmutils_int.lib.helper_methods import generate_basic_dictionary_from_list_of_objects
from enmutils_int.lib.load_node import annotate_fdn_poid_return_node_objects
from enmutils_int.lib.node_security import (SecurityConfig, NodeSecurityLevel, generate_node_batches,
                                            get_nodes_not_at_required_level, check_services_are_online, NodeCredentials,
                                            NodeSNMP, NodeCertificate, NodeTrust)
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow import create_custom_user_role


DEFAULT_DIR = "/home/enmutils/nodesec/"
NODES_FILE_NAME = "nodes.txt"
NODES_FILE_PATH = os.path.join("{0}{1}".format(DEFAULT_DIR, NODES_FILE_NAME))
NODESEC_11_UNSYNCED_NODES_FILE_NAME = "nodesec_11_unsynced_nodes.txt"

# This file used to save the profile allocated unsynced nodes id's for nodesec_13
NODESEC_13_UNSYNCED_NODES_FILE_NAME = "nodesec_13_allocated_unsynced_nodes.txt"


class NodeSecFlow(GenericFlow):
    @staticmethod
    def wait_for_profile(nodes, profile_name="NODESEC_03", state="COMPLETED"):
        default_timeout = (len(nodes) * 4) / 60
        load_mgr.wait_for_setup_profile(profile_name=profile_name, state_to_wait_for=state,
                                        timeout_mins=default_timeout if default_timeout > 20 else 20)


class NodeSec01Flow(NodeSecFlow):

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        users = self.create_profile_users(self.NUM_BATCHES, roles=["ADMINISTRATOR"])
        self.state = "RUNNING"
        node_credentials_list = self.create_batches_credential_objects(users)
        self.create_and_execute_threads(node_credentials_list, self.NUM_BATCHES, args=[self])

    def create_batches_credential_objects(self, users):
        """
        Create batches of nodes to be allocated to each NodeCredential instance

        :type users: list
        :param users: List of `enm_user_2.User` instances

        :raises EnvironError: if nodes are not available on the deployment
        :rtype: list
        :return: List of `node_security.NodeCredential` instances
        """
        node_dict = generate_basic_dictionary_from_list_of_objects(
            self.get_nodes_list_by_attribute(
                node_attributes=['primary_type', 'node_id', 'secure_user', 'secure_password',
                                 'normal_user', 'normal_password']), "primary_type")
        node_credentials_list = []
        error_node_types = []
        for node_type in node_dict.keys():
            try:
                node_batches = generate_node_batches(node_dict[node_type], batch_size=self.NUM_BATCHES)
                node_user_tuple = zip(node_batches, users)
                for batch, user in node_user_tuple:
                    node_credentials_list.append(NodeCredentials(nodes=batch, user=user))
            except Exception:
                error_node_types.append(node_type)
        if error_node_types:
            self.add_error_as_exception(EnvironError("Error generating node batches, please ensure {0} nodes are "
                                                     "created on the deployment.".format(','.join(error_node_types))))
        return node_credentials_list

    @staticmethod
    def task_set(node_credentials_obj, profile):  # pylint: disable=arguments-differ
        """
        Task set for use with thread queue

        :type node_credentials_obj: `node_security.NodeCredential`
        :param node_credentials_obj: Object to be the worker
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """
        secure_user = secure_password = normal_user = normal_password = 'netsim'
        try:
            node_credentials_obj.remove()
            node_credentials_obj.create(secure_user=secure_user, secure_password=secure_password,
                                        normal_user=normal_user, normal_password=normal_password, permanent=False)
            node_credentials_obj.restore()
        except Exception as e:
            profile.add_error_as_exception(e)


class NodeSec02Flow(NodeSec01Flow):

    @staticmethod
    def task_set(node_credentials_obj, profile):  # pylint: disable=arguments-differ
        """
        Task set for use with thread queue

        :type node_credentials_obj: `node_security.NodeCredential`
        :param node_credentials_obj: Object to be the worker
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """
        try:
            node_credentials_obj.update(secure_user=profile.NAME, secure_password=profile.NAME)
            node_credentials_obj.restore()
        except Exception as ex:
            profile.add_error_as_exception(ex)


class NodeSec03Flow(NodeSecFlow):

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        users = self.create_profile_users(1, roles=["ADMINISTRATOR"])
        self.state = "RUNNING"
        self.check_services_are_online()
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid", "primary_type"])
        nodes = annotate_fdn_poid_return_node_objects(nodes_list)
        while nodes:
            nodes = self.get_nodes_at_correct_security_level(nodes, users[0])
            if nodes:
                try:
                    node_batches = generate_node_batches(nodes)
                except Exception as e:
                    raise EnvironError("{0}, please ensure nodes are created on the deployment.".format(e.message))
                start_time = int(time.time())
                self.create_and_execute_security_objects(node_batches, users[0], start_time, nodes)

    def create_and_execute_security_objects(self, node_batches, user, start_time, nodes, level=2):
        """
        Create the NodeSecurityLevel instances for each batch and calls the relevant security level

        :type node_batches: list
        :param node_batches: List of `enm_node.Node` objects allocated in equal sized batches
        :type user: `enm_user_2.user`
        :param user: User who will query ENM for ids
        :type start_time: int
        :param start_time: Integer representing start time of operation
        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type level: int
        :param level: Security level, to which the given nodes are requested to change to
        """
        for batch in node_batches:
            security_config = SecurityConfig(level=level)
            security = NodeSecurityLevel(batch, security_config, user)
            if self.TEARDOWN:
                self.teardown_list.append(security)
            try:
                security.set_level(security_config.level)
            except Exception as e:
                self.add_error_as_exception(e)
        self.calculate_and_perform_sleep(start_time, nodes)

    def get_nodes_at_correct_security_level(self, nodes, user, security_level=2):
        """
        Annotates, filters synced nodes based upon the required security level

        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type user: `enm_user_2.user`
        :param user: User who will query ENM for ids
        :type security_level: int
        :param security_level: The required security level

        :rtype: list
        :return: List of `enm_node.Node` objects
        """
        required_security_level_nodes = []
        synced = self.get_synchronised_nodes(nodes, user)
        if synced:
            incorrect_level_nodes = get_nodes_not_at_required_level([node.node_id for node in synced],
                                                                    required_security_level=security_level, user=user)
            required_security_level_nodes = [node for node in synced if node.node_id in incorrect_level_nodes]
        return required_security_level_nodes

    def check_services_are_online(self):
        """
        Check if the required service are online
        """
        try:
            check_services_are_online()
        except Exception as e:
            self.add_error_as_exception(EnvironError("Not all services could be determined as ONLINE, this may impact "
                                                     "performance.Response: {0}".format(e.message)))

    @staticmethod
    def calculate_and_perform_sleep(start_time, nodes):
        """
        Sleep for 10 minutes per 450 nodes or 4 seconds per node

        :type start_time: int
        :param start_time: Integer representing start time of operation
        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        """
        sleep = (start_time + (len(nodes) * 4)) - int(time.time())
        sleep = sleep if sleep > 60 else 60
        log.logger.debug("Sleeping for {0} seconds, before next iteration.".format(sleep))
        time.sleep(sleep)


class NodeSec04Flow(NodeSec03Flow):

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        users = self.create_profile_users(1, roles=["ADMINISTRATOR"])
        self.state = "RUNNING"
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid", "primary_type"])
        nodes = annotate_fdn_poid_return_node_objects(nodes_list)
        while nodes:
            self.wait_for_profile(nodes)
            nodes = self.get_nodes_at_correct_security_level(nodes, users[0], security_level=1)
            if nodes:
                try:
                    node_batches = generate_node_batches(nodes)
                except Exception as e:
                    raise EnvironError("{0}, please ensure nodes are created on the deployment.".format(e.message))
                start_time = int(time.time())
                self.create_and_execute_security_objects(node_batches, users[0], start_time, nodes, level=1)


class NodeSec08Flow(NodeSecFlow):

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        node_batches = []
        users = self.create_profile_users(self.NUM_USERS, roles=["ADMINISTRATOR"])
        self.state = "RUNNING"
        nodes_list = self.get_nodes_list_by_attribute(
            node_attributes=["node_id", "primary_type", "snmp_authentication_method", "snmp_auth_password",
                             "snmp_encryption_method", "snmp_priv_password", "snmp_security_level",
                             "snmp_security_name"])
        try:
            node_batches = generate_node_batches(nodes_list, batch_size=self.NUM_BATCHES)
        except Exception as e:
            raise EnvironError("{0}, please ensure nodes are created on the deployment.".format(e.message))
        node_user_tuple = zip(node_batches, users)
        node_snmp_list = self.create_snmp_instances(node_user_tuple)
        self.create_and_execute_threads(node_snmp_list, len(users), args=[self])

    @staticmethod
    def create_snmp_instances(node_user_tuple):
        """
        Create SNMP instances based upon the provided node/user tuple

        :type node_user_tuple: list
        :param node_user_tuple: Tuple containing list of `enm_node.Node` instance, list of `enm_user_2.User` instances

        :rtype: list
        :return: List of `node_security.NodeSNMP` instances
        """
        node_snmp_list = []
        for batch, user in node_user_tuple:
            node_snmp_list.append(NodeSNMP(nodes=batch, user=user))
        return node_snmp_list

    @staticmethod
    def task_set(node_snmp, profile):  # pylint: disable=arguments-differ
        """
        Task set for use with thread queue

        :type node_snmp: `node_security.SNMP`
        :param node_snmp: Object to be the worker
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """
        try:
            node_snmp.set_version(snmp_version=profile.SNMP_VERSION)
        except Exception as e:
            profile.add_error_as_exception(e)


class NodeSec11Flow(NodeSecFlow):

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        is_first_run = True
        try:
            users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
            self.state = "RUNNING"
            nodes = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'primary_type', 'profiles'])
            if nodes:
                synced_nodes = self.perform_prerequisites(nodes, users[0])
            else:
                raise EnvironError("No nodes are allocated to current profile")
            security_config = SecurityConfig(cert_type=self.CERTS[0])
            node_certificate = NodeCertificate(synced_nodes, security_config, user=users[0])
            self.teardown_list.append(partial(filesystem.delete_file,
                                              os.path.join("{0}{1}".format(DEFAULT_DIR,
                                                                           NODESEC_11_UNSYNCED_NODES_FILE_NAME))))
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))
        else:
            while self.keep_running():
                self.sleep_until_day()

                if is_first_run:
                    is_first_run = False
                    self.certificate_issue_tasks(node_certificate)
                else:
                    self.certificate_reissue_tasks(node_certificate)

    def verify_allocated_nodes_sync_status(self, nodes, user):
        """
        Verifies if profile allocated nodes are in synced state or not and returns list of synchronized nodes.

        :type nodes: list
        :param nodes: List of `enm_node.Node` instances
        :type user: `enm_user_2.User`
        :param user: User who will query the sync status
        :rtype: list
        :return: List of `enm_node.Node` instances
        """
        try:
            synced_nodes = self.get_synchronised_nodes(nodes, user)
            log.logger.debug("{0} synced nodes found from {1} nodes".format(len(synced_nodes), len(nodes)))
            unsynced_nodes = [node for node in nodes if
                              node.node_id not in [sync_node.node_id for sync_node in synced_nodes]]

            unsynced_nodes_file_path = os.path.join("{0}{1}".format(DEFAULT_DIR, NODESEC_11_UNSYNCED_NODES_FILE_NAME))
            node_ids = ';'.join(node.node_id for node in unsynced_nodes)
            filesystem.write_data_to_file(node_ids, unsynced_nodes_file_path)
            if unsynced_nodes:
                log.logger.debug("{0} allocated nodes are in Unsynchronized state. Unsynchronized Node IDs can be found in "
                                 "{1} file".format(len(unsynced_nodes), unsynced_nodes_file_path))
            return synced_nodes
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))

    def certificate_issue_tasks(self, node_certificate):
        """
        Performs the NodeCertificate issue operation.

        :type node_certificate: `node_security.NodeCertificate`
        :param node_certificate:
        """
        try:
            nodes = self.verify_allocated_nodes_sync_status(node_certificate.nodes, node_certificate.user)
            node_certificate.issue(self.NAME, nodes)
        except Exception as e:
            self.add_error_as_exception(e)
        finally:
            self.teardown_list.append(picklable_boundmethod(node_certificate._delete_xml_file))

    def certificate_reissue_tasks(self, node_certificate):
        """
        Performs the NodeCertificate reissue operation

        :type node_certificate: `node_security.NodeCertificate`
        :param node_certificate:
        """
        try:
            nodes = self.verify_allocated_nodes_sync_status(node_certificate.nodes, node_certificate.user)
            node_certificate.reissue(nodes)
        except Exception as e:
            self.add_error_as_exception(e)

    def perform_prerequisites(self, nodes, user):
        """
        This method performs following operations. i.e.; get synced nodes from profile allocated nodes,
        and deallocate unused nodes

        :param nodes: List of enm_node.Node objects
        :type nodes: list
        :param user: User object to be used to create the NodeTrust
        :type user: enmutils.lib.enm_user.User
        :return: synced nodes
        :rtype: list

        :raises EnvironError: if no synced nodes are available
        """
        synced_nodes = self.get_synchronised_nodes(nodes, user)
        if synced_nodes:
            profile_required_nodes = synced_nodes[:self.MAX_NODES]
            log.logger.debug("Profile took {0} nodes out of {1} from {2} "
                             "synced nodes".format(len(profile_required_nodes), self.MAX_NODES, len(synced_nodes)))
            profile_required_nodes_ids = [node.node_id for node in profile_required_nodes]
            unused_nodes = [node for node in nodes if node.node_id not in profile_required_nodes_ids]
            if unused_nodes:
                log.logger.debug("Deallocating the unused nodes from {} profile".format(self.NAME))
                self.update_profile_persistence_nodes_list(unused_nodes)
            return profile_required_nodes
        else:
            raise EnvironError("No synced nodes are available")


class NodeSec13Flow(NodeSecFlow):

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        try:
            users = self.create_profile_users(1, roles=["ADMINISTRATOR"])
            self.state = "RUNNING"
            nodes = self.get_nodes_list_by_attribute()
            if nodes:
                node_trust = self.trust_prerequisites(nodes, users[0])
                self.teardown_list.append(partial(filesystem.delete_file,
                                                  os.path.join("{0}{1}".format(DEFAULT_DIR,
                                                                               NODESEC_13_UNSYNCED_NODES_FILE_NAME))))
                self.teardown_list.append(partial(filesystem.delete_file, NODES_FILE_PATH))
                self.teardown_list.append(partial(picklable_boundmethod(self.nodes_trust_remove), node_trust,
                                                  check_job_status_on_teardown=True))
            else:
                raise EnvironError("Profile is not allocated to any node")
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            self.nodes_trust_distribute(node_trust, include_ca=False)
            while self.keep_running():
                self.sleep_until_day()
                try:
                    # check the synced nodes, unsynced nodes from node_trust.nodes for every run and
                    # skip the nodesec secadm commands execution on unsync nodes.
                    self.check_sync_and_unsync_nodes_and_save_to_files(node_trust, users[0])
                    self.nodes_trust_distribute(node_trust)
                    log.logger.debug("Sleep for 60 seconds before execute the trust remove command.")
                    time.sleep(60)
                    self.nodes_trust_remove(node_trust)
                except Exception as e:
                    self.add_error_as_exception(e)

    def nodes_trust_distribute(self, node_trust, include_ca=True):
        """
        Performs the NodeTrust distribute operation required by this profile

        :type node_trust: `node_security.NodeTrust`
        :param node_trust: NodeTrust instance responsible for performing the task
        :param include_ca: Boolean indicating if need to include ca in trust distribute command or not.
        :type include_ca: bool
        """
        try:
            node_trust.distribute(NODES_FILE_NAME, NODES_FILE_PATH, include_ca=include_ca)
        except Exception as e:
            self.add_error_as_exception(e)

    def nodes_trust_remove(self, node_trust, check_job_status_on_teardown=False):
        """
        Performs the NodeTrust remove operation required by this profile

        :type node_trust: `node_security.NodeTrust`
        :param node_trust: NodeTrust instance responsible for performing the task
        :type check_job_status_on_teardown: bool
        :param check_job_status_on_teardown: Boolean indicating if need to check remove trust job status
                                             on teardown or not.
        """
        try:
            node_trust.remove(NODES_FILE_NAME, NODES_FILE_PATH, check_job_status_on_teardown)
        except Exception as e:
            self.add_error_as_exception(e)

    def trust_prerequisites(self, nodes, user):
        """
        This method performs following operations. i.e.; get synced nodes from profile allocated nodes,
        creates the NodeTrust object, store the nodes id's in nodes file.

        :param nodes: List of enm_node.Node objects
        :type nodes: list
        :param user: User object to be used to create the NodeTrust
        :type user: enmutils.lib.enm_user.User
        :return: object of node_trust (NodeTrust)
        :rtype: NodeTrust object

        :raises EnvironError: if synced nodes not existed
        """
        synced_nodes = self.get_synchronised_nodes(nodes, user)
        if synced_nodes:
            profile_required_nodes = synced_nodes[:self.MAX_NODES]
            log.logger.debug("Profile took {0} nodes out of {1} from {2} "
                             "synced nodes".format(len(profile_required_nodes), self.MAX_NODES, len(synced_nodes)))
            profile_required_nodes_ids = [node.node_id for node in profile_required_nodes]
            unused_nodes = [node for node in nodes if node.node_id not in profile_required_nodes_ids]
            if unused_nodes:
                log.logger.debug("Deallocating the unused nodes from {} profile".format(self.NAME))
                self.update_profile_persistence_nodes_list(unused_nodes)
            security_config = SecurityConfig(cert_type=self.CERTS[0])
            node_trust = NodeTrust(profile_required_nodes, security_config, user=user)
            node_ids = ';'.join(node.node_id for node in node_trust.nodes)
            filesystem.write_data_to_file(node_ids, NODES_FILE_PATH)
            return node_trust
        else:
            raise EnvironError("Synced nodes are not existed")

    def check_sync_and_unsync_nodes_and_save_to_files(self, node_trust, user):
        """
        This methods checks the synced and un-synced nodes from node_trust nodes object.
        Synced nodes id's are saved in NODES_FILE_PATH file (nodes.txt) and
        un-synced nodes id's are saved in unsynced_nodes_file_path file (nodesec_13_allocated_unsynced_nodes.txt)

        :type node_trust: `node_security.NodeTrust`
        :param node_trust: NodeTrust instance responsible for performing the task
        :param user: User object to be used to create the NodeTrust
        :type user: enmutils.lib.enm_user.User

        :raises EnvironError: if Profile allocated nodes are not in synced state.
        """
        unsynced_nodes_file_path = os.path.join("{0}{1}".format(DEFAULT_DIR, NODESEC_13_UNSYNCED_NODES_FILE_NAME))

        # Checking node_trust.nodes are synced nodes or not
        synced_nodes = self.get_synchronised_nodes(node_trust.nodes, user)
        log.logger.debug("{0} synced nodes found from {1} nodes".format(len(synced_nodes),
                                                                        len(node_trust.nodes)))

        # Checking the unsynced nodes from node_trust.nodes
        unsynced_nodes = [node for node in node_trust.nodes if node not in synced_nodes]
        # Unsynced nodes id's are saved in nodesec_13_allocated_unsynced_nodes.txt (unsynced_nodes_file_path)
        node_ids = ';'.join(node.node_id for node in unsynced_nodes)
        filesystem.write_data_to_file(node_ids, unsynced_nodes_file_path)
        if unsynced_nodes:
            log.logger.debug("{0} unsynced nodes found from {1} nodes and "
                             "unsynced nodes id's are saved to {2} file".format(len(unsynced_nodes),
                                                                                len(node_trust.nodes),
                                                                                unsynced_nodes_file_path))
        if synced_nodes:
            # Synced nodes id's are saved in nodes.txt (/home/enmutils/nodesec/nodes.txt) file.
            node_ids = ';'.join(node.node_id for node in synced_nodes)
            filesystem.write_data_to_file(node_ids, NODES_FILE_PATH)
        else:
            raise EnvironError("Profile allocated nodes ({0}) are unsynced state. "
                               "So, Profile skipping the current iteration.".format(len(node_trust.nodes)))


class NodeSec15Flow(NodeSecFlow):
    def __init__(self, *args, **kwargs):
        self.end_time = None
        self.next_iteration_time = None
        self.total_iterations_for_day = 0
        super(NodeSec15Flow, self).__init__(*args, **kwargs)

    def execute_flow(self):
        """
        Executes the profiles flow.
        """
        users = self.create_profile_users(self.NUM_USERS, roles=["ADMINISTRATOR"])
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_time()
            try:
                nodes = self.get_nodes_list_by_attribute(node_attributes=['primary_type', 'node_id'])
                if nodes:
                    credentials = self.get_credentials_instances(users, nodes)
                    self.end_time = self.get_end_time()
                    self.next_iteration_time = datetime.now().replace(hour=0, minute=0, second=0)
                    while True:
                        if self.next_iteration_time < self.end_time:
                            self.next_iteration_time = self.execute_threads_for_profile(credentials)
                            self.total_iterations_for_day += 1
                        else:
                            self.last_iteration_if_minimum_time_exists(credentials)
                            log.logger.debug("Completed required iterations in given time period")
                            break
                    log.logger.debug("Total completed iterations for today: {0}".format(self.total_iterations_for_day))
                    self.total_iterations_for_day = 0
                else:
                    raise EnvironError("Profile is not allocated to any node")
            except Exception as e:
                self.add_error_as_exception(e)

    def execute_threads_for_profile(self, credentials):
        """
        Create and Execute threads and returns next iteration time
        :param credentials: List of `node_security.NodeCredential` instances
        :type credentials: list
        :return: next iteration time
        :rtype: datetime
        """
        present_time = datetime.now()
        self.create_and_execute_threads(credentials, len(credentials),
                                        wait=self.THREAD_QUEUE_TIMEOUT, args=[self])
        last_iteration_run_time = datetime.now() - present_time
        log.logger.debug("Time taken to run last iteration {0}".format(last_iteration_run_time))
        self.next_iteration_time = datetime.now() + last_iteration_run_time
        log.logger.debug("Next iteration time {0}".format(self.next_iteration_time))
        return self.next_iteration_time

    def last_iteration_if_minimum_time_exists(self, credentials):
        """
        Executes one last iteration if difference between next iteration and end time is less than or equal to 30 min
        :param credentials: List of `node_security.NodeCredential` instances
        :type credentials: list
        """
        access_time = 1800
        delta = self.next_iteration_time - self.end_time
        if delta.seconds <= access_time:
            log.logger.debug("Executing one last iteration taking extra {0} seconds to complete ".format(delta.seconds))
            self.create_and_execute_threads(credentials, len(credentials),
                                            wait=self.THREAD_QUEUE_TIMEOUT, args=[self])
            self.total_iterations_for_day += 1

    def get_credentials_instances(self, users, nodes):
        """
        Creates, and returns a list of `node_security.NodeCredential` instances

        :type users: list
        :param users: of `enm_user_2.User` instances who will query ENM
        :type nodes: list
        :param nodes: list of profile allocate nodes.

        :rtype: list
        :return: List of `node_security.NodeCredential` instances
        """
        nodes_per_user = split_list_into_sublists(nodes, self.NUM_USERS)
        return [NodeCredentials(nodes=nodes_per_user[users.index(user)], user=user) for user in users]

    @staticmethod
    def task_set(credential, profile):  # pylint: disable=arguments-differ
        """
        Function to be used by threads to retrieve the node credentials

        :type credential: `node_security.NodeCredentials`
        :param credential: Worker object to perform the function
        :type profile: `lib.profile.Profile`
        :param profile: Profile executing the threads to add exceptions to
        """
        if datetime.now() < profile.end_time:
            user_name = credential.user.username
            wait = (int(user_name.split('_u')[-1]) + 1) * profile.NODE_REQUEST_CREDENTIALS_TIME
            log.logger.info("Sleeping for {0} seconds for user - {1}".format(wait, user_name))
            time.sleep(wait)
            credential.get_credentials_with_delay(profile=profile)


class NodeSec18Flow(GenericFlow):
    MAX_POLL = 3
    SSHKEY_CREATE_CMD = "secadm sshkey create --algorithm-type-size RSA_4096 --nodelist {nodes_list}"
    SSHKEY_DELETE_CMD = "secadm sshkey delete --nodelist {nodes_list}"

    def execute_flow(self):
        """
        Executes the profiles flow
        """
        self.state = "RUNNING"
        is_first_run = True
        try:
            custom_role, teardown_role = create_custom_user_role(self, self.USER_ROLES[0],
                                                                 "Nodesec_18 profile custom user role")
            self.teardown_list.append(picklable_boundmethod(teardown_role.delete))
            log.logger.debug("Sleeping for 120 seconds to allow the UAC table update with {0} "
                             "custom role.".format(custom_role.name))
            time.sleep(120)
            # Creates user with sshkeymaker custom user role.
            user = self.create_profile_users(1, roles=[custom_role.name])[0]
            self.teardown_list.append(picklable_boundmethod(user.delete))

            while self.keep_running():
                self.sleep_until_day()
                try:
                    synced_nodes = self.get_profile_required_nodes(user)
                    self.perform_sshkey_create_and_delete_operations(user, synced_nodes, is_first_run=is_first_run)
                    is_first_run = False
                except Exception as e:
                    self.add_error_as_exception(e)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))

    def get_profile_required_nodes(self, user):
        """
        Allocate profile nodes and get synchronised nodes and 90% nodes are required for all deployments.
        :rtype: list
        :return: list of synced nodes
        :raises EnvironError: If synced nodes are not found or SGSN-MME nodes are not exist or
                              profile allocated node percentage version is less than 90%
        """
        nodes = self.all_nodes_in_workload_pool(node_attributes=["node_id", "poid", "primary_type"])
        synced_nodes = self.get_synchronised_nodes(nodes, user)
        log.logger.debug("{0} synced nodes: {1}".format(len(synced_nodes),
                                                        [node.node_id for node in synced_nodes]))
        if synced_nodes:
            unused_nodes = [node for node in nodes if node not in synced_nodes]
            if not unused_nodes and self.num_nodes != len(synced_nodes):
                self.num_nodes = len(synced_nodes)
                self.persist()
            else:
                self.update_profile_persistence_nodes_list(list(unused_nodes))
            exists = any(isinstance(item, partial) for item in self.teardown_list)
            if not exists:
                self.teardown_list.append(partial(picklable_boundmethod(self.delete_sshkey_on_nodes), user,
                                                  synced_nodes, is_teardown=True))
            total_nodes_count = self.get_total_number_of_sgsn_mme_nodes_on_deployment(user)
            if total_nodes_count:
                nodes_count_percentage = round((float(len(synced_nodes)) / total_nodes_count) * 100, 2)
                log.logger.debug("Profile allocate nodes percentage: {0}".format(nodes_count_percentage))
                if nodes_count_percentage < 90:
                    raise EnvironError("Profile should be allocate with minimum 90% nodes in deployment.")
            else:
                raise EnvironError("SGSN-MME nodes are not found in this deployment.")
            return synced_nodes
        else:
            raise EnvironError("Synced nodes are not available.")

    def perform_sshkey_create_and_delete_operations(self, user, nodes, is_first_run=False):
        """
        Perform sshkey create, delete operations on nodes.

        :param nodes: List of enm_node.Node objects
        :type nodes:  list
        :param user: User who will query ENM and run cli commands
        :type user: `enm_user_2.User`
        :param is_first_run: it skips to raise EnvironError if delete command is failed on more than 90% nodes, when it is true
        :type is_first_run:  bool
        """
        self.delete_sshkey_on_nodes(user, nodes, is_first_run=is_first_run)
        self.delete_sshkey_on_nodes(user, nodes, is_first_run=is_first_run)
        self.create_sshkey_on_nodes(user, nodes)

    def delete_sshkey_on_nodes(self, user, nodes, is_first_run=False, is_teardown=False):
        """
        Delete sshkey on nodes
        :param user: User who will query ENM and run cli commands
        :type user: `enm_user_2.User`
        :param nodes: List of enm_node.Node objects
        :type nodes:  list
        :param is_first_run: it skips to raise EnvironError if delete command is failed on more than 90% nodes, when it is true
        :type is_first_run:  bool
        :param is_teardown: it skips job status checkm when it is True, otherwise it waits for until job is completed.
        :type is_teardown:  bool
        :raises EnvironError: Unable to execute delete sshkey command on profile allocated nodes due to some issues.
        """
        try:
            node_ids = ','.join(node.node_id for node in nodes)
            log.logger.debug('Attempting to execute sshkey delete command on {0} nodes'.format(len(nodes)))
            cmd = self.SSHKEY_DELETE_CMD.format(nodes_list=node_ids)
            response = user.enm_execute(cmd)
            enm_output = response.get_output()
            log.logger.debug("output: {0}".format(enm_output))
            if "Successfully started a job" in str(enm_output):
                job_status_cmd = str(re.split("'*'", enm_output[0])[1])
                log.logger.debug(
                    "Command to get status for sshkey delete job on nodes: '{0}'".format(job_status_cmd))
                if not is_teardown:
                    self.get_current_job_status(user, "{0} --summary".format(job_status_cmd), "delete",
                                                len(nodes), is_first_run)
                    self.check_any_nodes_in_error_state(user, job_status_cmd, "delete")
            else:
                raise EnvironError("Unable to execute sshkey delete command({0}) on "
                                   "nodes due to {1}".format(cmd, enm_output))
        except Exception as e:
            self.add_error_as_exception(e)
        self.check_profile_memory_usage()

    def create_sshkey_on_nodes(self, user, nodes):
        """
        Create sshkey on nodes
        :param nodes: List of enm_node.Node objects
        :type nodes:  list
        :param user: User who will query ENM and run cli commands
        :type user: `enm_user_2.User`
        :raises EnvironError: Unable to execute create sshkey command on profile allocated nodes due to some issues
        """
        try:
            node_ids = ','.join(node.node_id for node in nodes)
            log.logger.debug('Attempting to execute sshkey create command on {0} nodes'.format(len(nodes)))
            cmd = self.SSHKEY_CREATE_CMD.format(nodes_list=node_ids)
            response = user.enm_execute(cmd)
            enm_output = response.get_output()
            log.logger.debug("output: {0}".format(enm_output))
            if "Successfully started a job" in str(enm_output):
                job_status_cmd = str(re.split("'*'", enm_output[0])[1])
                log.logger.debug(
                    "Command to get status for ssh create job on nodes: '{0}'".format(job_status_cmd))
                self.get_current_job_status(user, "{0} --summary".format(job_status_cmd), "create", len(nodes))
                self.check_any_nodes_in_error_state(user, job_status_cmd, "create")
            else:
                raise EnvironError("Unable to execute command({0}) on nodes due to {1}".format(cmd, enm_output))
        except Exception as e:
            self.add_error_as_exception(e)
        self.check_profile_memory_usage()

    def get_current_job_status(self, user, job_status_cmd, action, num_of_nodes, is_first_run=False):
        """
        Function to be used to get current job status
        :param user: User who will query ENM and run cli commands
        :type user: `enm_user_2.User`
        :param job_status_cmd: command to execute job status
        :type job_status_cmd: str
        :param action: sshkey create or delete
        :type action: str
        :param num_of_nodes: nodes count
        :type num_of_nodes: int
        :param is_first_run: it skips to raise EnvironError if delete command is failed on more than 90% nodes, when it is true
        :type is_first_run:  bool

        :raises EnvironError: If job status has not been completed within expected time/Max_poll
        """
        job_complete_status = False
        job_status_response = ''
        poll = 1
        while not job_complete_status and poll <= self.MAX_POLL:
            log.logger.debug('POLL_COUNT: {0}, MAX_POLL: {1}'.format(poll, self.MAX_POLL))
            try:
                log.logger.debug("Execute {0} command to get current job status".format(job_status_cmd))
                job_status_response = user.enm_execute(job_status_cmd)
                job_status_output = [job_status for job_status in job_status_response.get_output() if 'Status' in
                                     job_status]
                if job_status_response and job_status_output and 'COMPLETED' in job_status_output[0]:
                    log.logger.debug("Job status has been successfully completed")
                    job_complete_status = True
                    self.get_sshkey_create_and_delete_commands_fail_percentage_on_nodes(job_status_response, action,
                                                                                        num_of_nodes, is_first_run)
                if not job_complete_status:
                    log.logger.debug("Sleeping for 60 seconds until job status in COMPLETED state..")
                    time.sleep(60)
                    poll += 1
            except Exception as e:
                log.logger.debug("Failed to get current job status:{0}".format(e))
                self.add_error_as_exception(EnvironError(e))
                break
        if poll > self.MAX_POLL:
            log.logger.debug('MAX_POLL limit reached - {0} retries in 180 seconds'.format(self.MAX_POLL))
            msg = 'Job status has not completed within expected retries: {0} '.format(self.MAX_POLL)
            raise EnvironError(msg)

    def check_any_nodes_in_error_state(self, user, job_status_cmd, action):
        """
        This function will verify if any nodes in error state
        :param user: User who will query ENM and run cli commands
        :type user: `enm_user_2.User`
        :param job_status_cmd: command to execute job status
        :type job_status_cmd: str
        :param action: sshkey create or delete
        :type action: str
        """
        job_status_response = user.enm_execute(job_status_cmd)
        enm_output = [line for line in job_status_response.get_output()
                      if self.get_matched_line_based_on_specific_string(line)]
        if enm_output:
            enm_output = '\n'.join(enm_output)
            log.logger.debug('Checking the error status of secadm job using command {0} and encountered the error as follows {1}\n'.
                             format(job_status_cmd, enm_output))
        else:
            log.logger.debug('Successfully executed sshkey {0} command on profile allocated nodes, '
                             'no nodes are in error state'.format(action))

    def get_matched_line_based_on_specific_string(self, line, key="ERROR"):
        """
        This function will return if any matched content with specific key

        :param line: job_status_cmd output line
        :type line: str
        :param key: specific string to get the matched line, default value is ERROR.
        :type key: str
        :return: List of nodes in ERROR state
        :rtype: list
        """
        pattern = r'{}'.format(key)
        matches = re.findall(pattern, line)
        return matches

    def get_sshkey_create_and_delete_commands_fail_percentage_on_nodes(self, job_status_response, action,
                                                                       num_of_nodes, is_first_run=False):
        """
        This function will calculate the sshkey create/delete command fail percentage on nodes.

        :param job_status_response: response of job status
        :type job_status_response: str
        :param action: sshkey create or delete
        :type action: str
        :param num_of_nodes: nodes count
        :type num_of_nodes: int
        :param is_first_run: it skips to raise EnvironError if delete command is failed on more than 90% nodes, when it is true
        :type is_first_run:  bool

        :raises EnvironError: If ssh key create/delete commands is failed on more than 50% nodes.
        """
        log.logger.debug('Job Status Summary: {0}'.format(job_status_response))
        try:
            enm_output = [line for line in job_status_response.get_output()
                          if self.get_matched_line_based_on_specific_string(line, key="Num Of Error Workflows")]
            log.logger.debug("enm_output: {0}".format(enm_output))
            if enm_output:
                fail_percentage = round((float(enm_output[0].split(":")[1].strip()) / num_of_nodes) * 100, 2)
                log.logger.debug("sshkey {0} command is failed on nodes percentage: {1}".format(action,
                                                                                                fail_percentage))
                if fail_percentage > 50:
                    if not is_first_run:
                        raise EnvironError("sshkey {0} command is failed on more than 50% nodes.".format(action))
                    else:
                        log.logger.debug("sshkey {0} command is failed on more than 50% nodes.".format(action))
        except Exception as e:
            self.add_error_as_exception(e)

    def get_total_number_of_sgsn_mme_nodes_on_deployment(self, user):
        """
        Gets the total GGSN-MME network elements count from the deployment
        :param user: enm user instance
        :type user: enmutils.lib.enm_user_2.User
        :return: count of total SGSN-MME NE's
        :rtype: int
        """
        cmedit_command = "cmedit get * NetworkElement -cn -ne=SGSN-MME"
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
            self.add_error_as_exception(e)
