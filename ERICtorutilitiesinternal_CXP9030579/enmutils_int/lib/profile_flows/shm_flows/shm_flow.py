import datetime
import os
import time
from enmutils.lib.enm_node_management import ShmManagement
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib import log
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.common_utils import start_stopped_nodes_or_remove
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.shm_utilities import SHMUtils
from enmutils_int.lib.shm import PLATFORM_TYPES
from enmutils_int.lib.shm_delete_jobs import DeleteBackupOnNodeJobBSC
from enmutils_int.lib.shm_utility_jobs import ShmBackUpCleanUpJob
from enmutils_int.lib.services import deploymentinfomanager_adaptor


class ShmFlow(GenericFlow):

    REBOOT_NODE = 'true'
    LOG_ONLY = False
    DEFAULT = True
    LOCAL_PATH = os.path.join("/home", "enmutils", "shm")  # Update value changes in enmutils_int/lib/nrm_default_configurations/apt_values.py SHM_DATA variable

    def __init__(self, *args, **kwargs):
        super(ShmFlow, self).__init__(*args, **kwargs)
        self.upgrade_backup_util = SHMUtils()

    @property
    def timestamp_str(self):
        return self.get_timestamp_str(timestamp_end_index=6)

    @property
    def get_current_epoch_time_in_milliseconds(self):
        return int(round(time.time() * 1000))

    def get_filtered_nodes_per_host(self, started_nodes, sync_check=True):
        """
        Groups the given nodes with respective to netsim box and
        takes FILTERED_NODES_PER_HOST nodes from each netsim box
        :type started_nodes: list
        :param started_nodes: list of all started nodes in the pool
        :type sync_check: boolean
        :param sync_check: ON/OFF the node_syn_check
        :rtype: list
        :return: synced_nodes
        """
        synced_nodes = []
        if started_nodes:
            log.logger.debug("Attempting to get the filtered nodes per each host netsim box")
            host_dict = node_pool_mgr.group_nodes_per_netsim_host(started_nodes)
            nodes_per_host = getattr(self, "FILTERED_NODES_PER_HOST", self.NODES_PER_HOST)
            host_balanced_nodes = [node for nodes in host_dict.itervalues() for node in nodes[:nodes_per_host]]
            log.logger.debug("The filtered_nodes_per_host filter completed with {0} nodes".
                             format(len(host_balanced_nodes)))
            synced_nodes = (self.get_synced_nodes(host_balanced_nodes, self.MAX_NODES) if sync_check else
                            host_balanced_nodes[:self.MAX_NODES])
            self.deallocate_unused_nodes_and_update_profile_persistence(synced_nodes)
            log.logger.debug("Completed fetching the filtered nodes per each host netsim box")
        else:
            log.logger.debug("Cannot check filtered nodes per each host, No nodes available")
        return synced_nodes

    def get_started_annotated_nodes(self, user, nodes):
        """
        Get the poids for provided nodes

        :type user: `enm_user_2.User`
        :param user: User who will query ENM
        :type nodes: list
        :param nodes: List of `enm_node.Node` objects

        :rtype: list
        :return: List of `enm_node.Node` objects
        """
        started_nodes = []
        try:
            annotated_nodes = SHMUtils.enm_annotate_method(user=user, nodes=nodes)
            started_nodes = start_stopped_nodes_or_remove(annotated_nodes)
        except Exception as e:
            self.add_error_as_exception(e)
        return started_nodes

    def inventory_sync_nodes(self, user, nodes=None):
        """
        Checks the inventory sync status of STARTED_NODES of respective profile and returns the nodes which are synced.
        :type user: enm_user_2.User object
        :param user: User object to check the inventory sync status
        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :return: list of synced nodes
        :rtype: list

        :raises EnmApplicationError: Exception raised when exception is raised in supervise function
        """
        try:
            nodes = nodes if nodes is not None else self.STARTED_NODES
            synced_nodes = []
            if nodes:
                shm_supervision_obj = ShmManagement(user=user, node_ids=[node.node_id for node in nodes])
                shm_supervision_obj.supervise(timeout_seconds=self.TIMEOUT)
                time.sleep(30)
                sync_node_ids = shm_supervision_obj.get_inventory_sync_nodes()
                synced_nodes = [node for node in nodes if node.node_id in sync_node_ids]
            else:
                log.logger.debug("Cannot check inventory sync, No nodes available")
            return synced_nodes
        except Exception as e:
            raise EnmApplicationError(e)

    def check_and_update_pib_values_for_backups(self):
        """
        Checks and updates pib values
        """
        pib_values = getattr(self, "PIB_VALUES", [])
        log.logger.debug("Pib values are : {0}".format(pib_values))
        deployment_config_value = deploymentinfomanager_adaptor.check_deployment_config()
        if deployment_config_value in ["extra_small_network", "five_network", "soem_five_network"]:
            log.logger.debug("{0} network detected. Attempting to update the required pib values!".format(
                deployment_config_value))
            try:
                for key in pib_values:
                    current_value = deploymentinfomanager_adaptor.get_pib_value_on_enm("shmserv", key)
                    if current_value == pib_values.get(key):
                        log.logger.debug("Pib value for {0} is already set required value - {1}".
                                         format(key, current_value))
                    else:
                        log.logger.debug("Pib updated needed for {0} to {1}".format(key, pib_values.get(key)))
                        deploymentinfomanager_adaptor.update_pib_parameter_on_enm(
                            "shmserv", key, pib_values.get(key))
            except Exception as e:
                raise EnvironError("Exception occured while trying to update required pib parameters - {0}".format(e))
        else:
            log.logger.debug("Pib updates not needed for {0}!".format(deployment_config_value))

    def cleanup_after_upgrade(self, user, synced_nodes, **kwargs):
        """
        Create a SHM cleanup job
        :type user: `enm_user_2.User`
        :param user: user object to create ShmBackUpCleanUpJob object
        :type synced_nodes: list
        :param synced_nodes: List of synced nodes objects
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary
        """
        try:
            primary_type = synced_nodes[0].primary_type
            description = "Initiating cleanup after upgrade"
            log.logger.debug("Starting SHMBackup cleanup Job after completing upgrade")
            cleanup_job = ShmBackUpCleanUpJob(user, nodes=synced_nodes,
                                              name="{0}_Cleanup_job_{1}_{2}".format(self.NAME, primary_type,
                                                                                    self.timestamp_str),
                                              description=description, platform=PLATFORM_TYPES[primary_type], **kwargs)
            cleanup_job.create()
        except Exception as e:
            self.add_error_as_exception(e)

    def create_upgrade_job(self, user, nodes, node_limit=None, **kwargs):
        """
        Create a SHM upgrade job

        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type user: `enm_user_2.User`
        :param user: User who will created the job
        :type node_limit: int
        :param node_limit: Upper limit of nodes to be used
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary

        :rtype: `shm.SoftwarePackage`
        :return: Software package object
        """
        try:
            pib_values = getattr(self, 'PKG_PIB_VALUES', {})
            synced_nodes = nodes if self.SKIP_SYNC_CHECK else node_pool_mgr.filter_unsynchronised_nodes(nodes)
            description = 'Performs upgrade on {0} nodes in a single job.'.format(len(synced_nodes))
            kwargs.update({"description": description, "use_default": self.DEFAULT, "reboot_node": self.REBOOT_NODE,
                           "log_only": self.LOG_ONLY, "profile_name": self.NAME})
            package = self.upgrade_backup_util.upgrade_setup(nodes=synced_nodes[:node_limit], user=user,
                                                             local_path=self.LOCAL_PATH, pib_values=pib_values, **kwargs)
            return package, synced_nodes
        except Exception as e:
            self.add_error_as_exception(e)

    def assign_nodes_based_on_profile_specification(self, user, nodes_list):
        """
        Returns list of required nodes based on profile name

        :type user: `enm_user_2.User`
        :param user: User who will created the job
        :param nodes_list: List of `enm_node.Node` instances
        :type nodes_list: list
        :return: List of nodes
        :rtype: list
        """
        log.logger.debug("Starting execution of function - assign_nodes_based_on_profile_specification")
        if self.NAME == "SHM_03":
            return SHMUtils.determine_highest_mim_count_nodes(nodes_list, self)
        elif self.NAME in ["SHM_05", "ASU_01"]:
            return SHMUtils.determine_highest_model_identity_count_nodes(self, nodes_list, user)
        elif self.NAME in ["SHM_24", "SHM_25", "SHM_27", "SHM_31", "SHM_33", "SHM_36", "SHM_40", "SHM_42"]:
            return nodes_list
        else:
            return self.get_nodes_list_by_attribute()

    def return_highest_mim_count_started_nodes(self, user, nodes_list):
        """
        Removes Upgrade Independent nodes and returns only started nodes

        :type user: `enm_user_2.User`
        :param user: User who will created the job
        :param nodes_list: List of `enm_node.Node` instances
        :type nodes_list: list
        :return: List of started nodes
        :rtype: list
        """
        started_nodes = []
        if nodes_list:
            log.logger.debug("Starting execution of function - return_highest_mim_count_started_nodes")
            nodes = self.assign_nodes_based_on_profile_specification(user, nodes_list)
            started_nodes = self.get_started_annotated_nodes(user, nodes)
        else:
            log.logger.debug("Cannot check highest_mim_count_started_nodes, No nodes available")

        return started_nodes

    def convert_shm_scheduled_times(self, scheduled_time):
        """
        Converts shm scheduled times from the network file to string format
        :type scheduled_time: list
        :param scheduled_time: scheduled time strings in list
        :return: List of scheduled times for profiles
        :rtype: list
        """
        scheduled_times = []
        for time_string in scheduled_time:
            if isinstance(time_string, int):
                time_string = self.convert_seconds_to_time_string(time_string)
            scheduled_times.append(time_string)

        return scheduled_times

    @staticmethod
    def convert_seconds_to_time_string(time_int):
        """
        Convert a time in seconds to a 24 hour string format

        :param time_int: Time in seconds, for example 58260 == 16:11:00
        :type time_int: int

        :return: Time in seconds in a 24 hour string format
        :rtype: str
        """
        hours = int(time_int / 3600)
        minutes = (time_int - (hours * 3600)) / 60
        seconds = time_int - (hours * 3600) - (60 * minutes)
        time_string = "{0}:{1}:{2}".format(hours if bool(len(str(hours)) == 2) else "0{0}".format(hours),
                                           minutes if bool(len(str(minutes)) == 2) else "0{0}".format(minutes),
                                           seconds if bool(len(str(seconds)) == 2) else "0{0}".format(seconds))
        return time_string

    def enable_shm_supervision(self, user, ne_type="BSC"):
        """
        Enables the shm supervision for all profile nodes
        """
        log.logger.debug("Starting to enable shm supervision on nodes")
        try:
            nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "node_ip"])
            shm_supervision_obj = ShmManagement(user=user, ne_type=ne_type,
                                                node_ids=[node.node_id for node in nodes_list])
            shm_supervision_obj.supervise(timeout_seconds=self.TIMEOUT)
        except Exception as e:
            log.logger.debug("Failed to set inventory supervise on one or more nodes.")
            self.add_error_as_exception(e)
        log.logger.debug("Successfully completed enabling shm supervision on nodes")

    def execute_backup_jobs(self, backup_job, delete_backup_job, user, enable_node_sync=False):
        """
        Executes the supplied backup related jobs

        :param backup_job: SHM backup job instance
        :type backup_job: `shm.ShmJob`
        :param delete_backup_job: SHM delete backup job instance
        :type delete_backup_job: `shm.ShmJob`
        :param user: User object that will be used to create the backup delete job
        :type user: `enm_user_2.User`
        :param enable_node_sync: Parameter to check if sync needs to be done before delete_backup
        :type enable_node_sync: bool
        """
        try:
            backup_job.create(self)
        except Exception as e:
            self.add_error_as_exception(e)
        try:
            backup_job.wait_time_for_job_to_complete(max_iterations=24, time_to_sleep=600)
        except Exception as e:
            self.add_error_as_exception(e)
        if enable_node_sync:
            self.enable_shm_supervision(user)
            log.logger.debug("Sleeping for 5 minutes to reflect the job status in backup inventory page")
            time.sleep(300)
        try:

            delete_backup_job.create(self)
        except Exception as e:
            self.add_error_as_exception(e)

    def backup_deletion_from_node(self, user, nodes, backup_start_time, name, platform="CPP"):
        """
        Creates a backup_delete job. This is a helper method for create/import software packages.
        :type name: str
        :param name: shm backup/cleanup job name
        :type nodes: `enm_node.Node`
        :param nodes: List of node(s) to be included in the backup delete job
        :param user: User object that will be used to create the backup delete job
        :type user: `enm_user_2.User`
        :param platform: Name of the node platform
        :type platform: str
        :type backup_start_time: int
        :param backup_start_time: delete backup job activity on node from this epoch time value after
        :raises EnmApplicationError: when there is issue in creating backup from node
        """
        log.logger.debug("Attempting to create a backup_housekeeping"
                         "job with user: {0} on platform: {1}".format(user, platform))
        try:
            if nodes[0].primary_type in ["ERBS", "RadioNode", "Router6672", "Router_6672", "Router6675"]:
                delete_backup_from_node = ShmBackUpCleanUpJob(user, nodes=nodes, platform=platform, name=name)
            elif nodes[0].primary_type == "BSC":
                # To consider backup files from backup inventory in payload.
                backup_start_time = backup_start_time - 60000
                delete_backup_from_node = DeleteBackupOnNodeJobBSC(user=user, nodes=nodes,
                                                                   remove_from_rollback_list="TRUE",
                                                                   backup_start_time=backup_start_time)
            else:
                log.logger.debug("Backup Deletion is not supported for the primary type {0} in this "
                                 "profile".format(nodes[0].primary_type))
                return
            delete_backup_from_node.create()
            log.logger.debug("Successfully created a backup_housekeeping"
                             "job with user: {0} on platform: {1}".format(user, platform))
        except Exception as err:
            raise EnmApplicationError("Backup Deletion from node encountered exception: {} ".format(err.message))

    def set_unset_mltn_timeout(self, timeout_cmd):
        try:
            SHMUtils.set_netsim_values(self.STARTED_NODES, [getattr(self, timeout_cmd).format(self.MLTN_TIMEOUT)])
        except Exception as e:
            self.add_error_as_exception(e)

    @staticmethod
    def get_synced_nodes(node_list, nodes_required, profile_name=None):
        """
        :param node_list: List of allocated nodes to profile
        :type node_list: list
        :param nodes_required: Count of required nodes (ERBS/RADIO)
        :type nodes_required: int
        :param profile_name: Profile name
        :type profile_name: str
        :return: Returns list of required number of synced nodes
        :rtype: list
        """
        if node_list:
            ne_type = node_list[0].primary_type if profile_name != "SHM_06" else None
            synced_nodes = node_pool_mgr.filter_unsynchronised_nodes(node_list, ne_type=ne_type)
            if synced_nodes:
                if len(synced_nodes) < nodes_required:
                    log.logger.debug("The profile will be running with {0} nodes,"
                                     "as remaining are unsynced.".format(len(synced_nodes)))
                    return synced_nodes
                elif len(synced_nodes) > nodes_required:
                    return synced_nodes[:nodes_required]
                else:
                    return synced_nodes
            else:
                log.logger.debug("No Available synced nodes")
                return []
        else:
            log.logger.debug("Cannot check sync status, No nodes available")
            return []

    def delete_inactive_upgrade_packages(self, user, nodes, **kwargs):
        """
        Create a job to delete inactive upgrade packages on a set of nodes

        :param user: User object to be used to make requests
        :type user: `enm_user_2.User`
        :param nodes: list of `lib.enm_node.Node` instances to be used to perform this flow
        :type nodes: list
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary
        """
        try:
            node_type = nodes[0].primary_type
            log.logger.debug("Attempting to create a job to "
                             "delete inactive upgrade packages on "
                             "{0} nodes".format(node_type))
            delete_name = "{0}_Delete_Upgrade_Inactive_{1}_{2}".format(self.NAME, node_type, self.timestamp_str)
            self.upgrade_backup_util.upgrade_delete_inactive(user=user, nodes=nodes,
                                                             job_name=delete_name, log_only=True, **kwargs)
        except IndexError as e:
            self.add_error_as_exception(EnvironError(
                "Nodes list is empty to create delete inactive upgrade package job."))
        except Exception as e:
            self.add_error_as_exception(e)

    def get_schedule_time_strings(self):
        """
        Assign empty list if the default values of SCHEDULED_TIMES_STRINGS and SHM_JOB_SCHEDULED_TIME_STRINGS
        does not exist in forty network file

        :return: Tuple containing the SCHEDULED_TIMES_STRINGS and SHM_JOB_SCHEDULED_TIME_STRINGS
        :rtype: tuple
        """
        log.logger.debug("Fetching the values of SCHEDULED_TIMES_STRINGS, SHM_JOB_SCHEDULED_TIME_STRINGS "
                         "from config file")
        schedule_time_strings = self.convert_shm_scheduled_times(getattr(self, "SCHEDULED_TIMES_STRINGS", []))
        shm_schedule_time_strings = self.convert_shm_scheduled_times(getattr(self, "SHM_JOB_SCHEDULED_TIME_STRINGS",
                                                                             []))
        log.logger.debug("Values picked for SCHEDULED_TIMES_STRINGS is {0} and SHM_JOB_SCHEDULED_TIME_STRINGS is {1}".
                         format(schedule_time_strings, shm_schedule_time_strings))
        shm_schedule_time_strings = self.convert_time_string_to_datetime_object(shm_schedule_time_strings)
        return schedule_time_strings, shm_schedule_time_strings

    def select_node_attributes_based_on_profile_name(self):
        """
        Selects list of nodes based on the profile_name and predefined node_attributes
        :return: List of `enm_node.Node` instances
        :rtype: list
        """
        default_shm_node_attribute = ["node_id", "node_ip", "netsim", "poid", "primary_type", "mim_version",
                                      "simulation", "node_name"]
        shm_node_attributes = {"SHM_01": default_shm_node_attribute,
                               "SHM_02": default_shm_node_attribute,
                               "SHM_03": default_shm_node_attribute + ["profiles"],
                               "SHM_05": default_shm_node_attribute + ["model_identity"],
                               "ASU_01": default_shm_node_attribute + ["model_identity"],
                               "SHM_18": default_shm_node_attribute,
                               "SHM_23": default_shm_node_attribute,
                               "SHM_24": default_shm_node_attribute,
                               "SHM_25": default_shm_node_attribute,
                               "SHM_26": default_shm_node_attribute,
                               "SHM_27": default_shm_node_attribute,
                               "SHM_28": default_shm_node_attribute,
                               "SHM_31": default_shm_node_attribute,
                               "SHM_32": default_shm_node_attribute,
                               "SHM_33": default_shm_node_attribute,
                               "SHM_34": default_shm_node_attribute,
                               "SHM_36": default_shm_node_attribute,
                               "SHM_39": default_shm_node_attribute,
                               "SHM_40": default_shm_node_attribute,
                               "SHM_41": default_shm_node_attribute,
                               "SHM_42": default_shm_node_attribute,
                               "SHM_43": default_shm_node_attribute,
                               "SHM_44": default_shm_node_attribute,
                               "SHM_46": default_shm_node_attribute,
                               "SHM_47": default_shm_node_attribute + ["oss_prefix"]}
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=shm_node_attributes[self.NAME])
        return nodes_list

    def select_nodes_based_on_profile_name(self, user):
        """
        Selects list of nodes based on the profile
        :param user: User object to be used to make requests
        :type user: `enm_user_2.User`
        :return: list of required synced_nodes
        :rtype: list
        :raises EnmApplicationError: when particular set of nodes unable to filter
        """
        self.check_and_update_pib_values_for_backups()
        nodes_list = self.select_node_attributes_based_on_profile_name()
        synced_nodes = []
        if nodes_list:
            try:
                if self.NAME in ["SHM_01", "SHM_02", "SHM_18", "SHM_23", "SHM_26", "SHM_28", "SHM_34", "SHM_39",
                                 "SHM_41", "SHM_43", "SHM_44"]:
                    started_nodes = self.get_started_annotated_nodes(user, nodes_list)
                    synced_nodes = self.get_synced_nodes(started_nodes, self.MAX_NODES)
                    self.deallocate_unused_nodes_and_update_profile_persistence(synced_nodes)
                elif self.NAME in ["SHM_03", "SHM_05", "SHM_24", "SHM_25", "SHM_33", "SHM_36", "SHM_40", "SHM_42",
                                   "ASU_01"]:
                    high_mim_nodes = self.return_highest_mim_count_started_nodes(user, nodes_list)
                    synced_nodes = self.get_filtered_nodes_per_host(high_mim_nodes)
                elif self.NAME == "SHM_27":
                    high_mim_nodes = self.return_highest_mim_count_started_nodes(user, nodes_list)
                    filtered_nodes = self.get_filtered_nodes_per_host(high_mim_nodes, sync_check=False)
                    synced_nodes = node_pool_mgr.filter_unsynchronised_nodes(filtered_nodes)
                elif self.NAME == "SHM_31":
                    high_mim_nodes = self.return_highest_mim_count_started_nodes(user, nodes_list)
                    synced_nodes = self.inventory_sync_nodes(user, nodes=high_mim_nodes)
                    self.deallocate_unused_nodes_and_update_profile_persistence(synced_nodes)
                elif self.NAME == "SHM_32":
                    started_nodes = self.get_started_annotated_nodes(user, nodes_list)
                    filtered_nodes = self.get_filtered_nodes_per_host(started_nodes, sync_check=False)
                    synced_nodes = self.inventory_sync_nodes(user, nodes=filtered_nodes)
                elif self.NAME == "SHM_47":
                    started_nodes = self.get_started_annotated_nodes(user, nodes_list)
                    synced_nodes = node_pool_mgr.filter_unsynchronised_nodes(started_nodes)
                    set_nodes = self.set_primary_core_baseband_FRU(user, synced_nodes)
                    unset_nodes = set(nodes_list) - set(set_nodes)
                    self.update_profile_persistence_nodes_list(unset_nodes)
                    synced_nodes = set_nodes
                else:
                    synced_nodes = nodes_list
            except Exception as e:
                raise EnmApplicationError("Failed to select specific type of nodes: {0}".format(str(e)))
        else:
            log.logger.debug("{0} Profile is not allocated to any node".format(self.NAME))
        return synced_nodes

    def set_primary_core_baseband_FRU(self, user, nodes_list):
        """
        Sets the primaryCoreRef attribute in Node's MpClusterHandling MO with the FDN of node's primary core
        Baseband FieldReplaceableUnit MO

        :param user: User who will execute the commands in ENM
        :type user: `enm_user_2.User`
        :param nodes_list: List of `enm_node.Node` instances
        :type nodes_list: list
        :return: List of set nodes
        :rtype: list
        """
        set_nodes = []
        SET_PRIMARY_CORE_BASEBAND_FRU_CMD = 'cmedit set {oss_prefix},ManagedElement={node_name},NodeSupport=1,' \
                                            'MpClusterHandling=1 primaryCoreRef="{oss_prefix},ManagedElement={node_name},Equipment=1,' \
                                            'FieldReplaceableUnit=1"'
        for node in nodes_list:
            cmd = SET_PRIMARY_CORE_BASEBAND_FRU_CMD.format(oss_prefix=node.oss_prefix, node_name=node.node_name)
            response = user.enm_execute(cmd)
            if 'SUCCESS' in str(response.get_output()[0]):
                log.logger.debug("Primary Core Baseband FRU set for node {0}".format(node.node_id))
                set_nodes.append(node)
                if len(set_nodes) == getattr(self, "MAX_NODES", 100):
                    break
            else:
                log.logger.debug("Response output - {0}".format(str(response.get_output())))
                self.add_error_as_exception(EnmApplicationError("Failed to set FRU for node {0}".format(node.node_id)))
        else:
            log.logger.debug("Couldn't get required number of nodes with FRU set to 1")
        log.logger.debug("Number of nodes with set primary core BaseBand FRU is {0} nodes".format(len(set_nodes)))
        return set_nodes

    def select_required_number_of_nodes_for_profile(self, user, sleep_param):
        """
        Select required number of synced nodes for a profile
        :param user: User object to be used to make requests
        :type user: `enm_user_2.User`
        :param sleep_param: Sleep parameter which is used to sleep until day/time
        :type sleep_param: str
        :return: list of required synced_nodes
        :rtype: list
        """
        try:
            selected_nodes = self.select_nodes_based_on_profile_name(user)
        except Exception as e:
            self.add_error_as_exception(e)
            selected_nodes = []
        if sleep_param == "day":
            self.sleep_until_day(delay_secs=1800)
        elif sleep_param == "time":
            self.sleep_until_time(delay_secs=1800)
        synced_nodes = node_pool_mgr.filter_unsynchronised_nodes(selected_nodes)
        if len(synced_nodes) != getattr(self, "MAX_NODES", 0):
            log.logger.debug("Allocated {0} nodes, required {1} nodes,"
                             " retrying node allocation".format(len(synced_nodes), getattr(self, "MAX_NODES", 0)))
            self.exchange_nodes()
            selected_nodes = self.select_nodes_based_on_profile_name(user)
            synced_nodes = node_pool_mgr.filter_unsynchronised_nodes(selected_nodes)
            if len(synced_nodes) == 0:
                self.add_error_as_exception(EnvironError('Profile is not allocated to any node'))
            elif len(synced_nodes) != self.MAX_NODES:
                log.logger.debug("Host doesn't have required number of synced nodes({0}), profile execution continues with"
                                 " available number of synced nodes({1})".format(self.MAX_NODES, len(synced_nodes)))
        return synced_nodes

    def convert_time_string_to_datetime_object(self, shm_schedule_time_strings):
        """
        Converts given time string to datetime object

        :param shm_schedule_time_strings: Job schedule time string
        :type shm_schedule_time_strings: str
        :return: List containing the SHM_JOB_SCHEDULED_TIME_STRINGS as datetime objects
        :rtype: list
        """
        new_datetime = []
        for time_str in shm_schedule_time_strings:
            time_data = [int(td) for td in time_str.split(":")]
            tmp_date = datetime.datetime.now().replace(hour=time_data[0], minute=time_data[1], second=time_data[2])
            new_datetime.append(tmp_date)
        log.logger.debug("SHM_JOB_SCHEDULED_TIME_STRINGS is {0}".format(new_datetime))
        return new_datetime


class Shm18Flow(object):

    BACKUP_DESCRIPTION = ""
    RESTORE_DESCRIPTION = ""


class Shm26Flow(object):

    BACKUP_DESCRIPTION = ""
    RESTORE_DESCRIPTION = ""
