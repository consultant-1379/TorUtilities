import time

from enmutils.lib import log
from enmutils.lib.enm_node_management import ShmManagement
from enmutils_int.lib import load_mgr, node_pool_mgr
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_ui import shm_home, shm_import_license_keys, shm_license_inventory_home, \
    shm_software_administration_home, shm_import_software_package, view_job_details, view_job_logs, download_logs, \
    shm_software_help
from enmutils_int.lib.shm_utilities import SHMLicense


class Shm06Flow(ShmFlow):

    LICENCE_LIST = list()
    REBOOT_NODE = 'false'
    LOG_ONLY = True
    DEFAULT = False
    JOB_NAME_PREFIX = ""
    TLS_FLAG = False
    LICENSE_PRE_CHECK = False

    @staticmethod
    def tasksetlicense(user_node_sleep, profile):
        """
        Generates the license and assigns it to the profile

        :param user_node_sleep: Tuple with a one user, node and sleep time each
        :type user_node_sleep: tuple
        :param profile: Profile object
        :type profile: `lib.profile.Profile`
        """
        user, node, sleep = user_node_sleep
        time.sleep(sleep)
        licence = SHMLicense(user=user, node=node, fingerprint_id="{0}_fp".format(node.node_name))
        try:
            licence.generate()
            profile.teardown_list.append(licence)
            profile.LICENCE_LIST.append(licence)
        except Exception as e:
            profile.add_error_as_exception(e)

    @staticmethod
    def taskset_license_actions(license_key, user, profile):
        """
        # License actions

        :param license_key: License key generated as per node
        :type license_key: str
        :param user: User object to use to make requests
        :type user: `enm_user_2.User`
        :param profile: Profile object
        :type profile: `lib.profile.Profile`
        """
        shm_home(user)
        shm_license_inventory_home(user)
        shm_import_license_keys(user)
        if license_key.path_to_license_key:
            try:
                license_key.import_keys()
            except Exception as e:
                profile.add_error_as_exception(e)
            shm_license_inventory_home(user)
        shm_home(user)
        shm_software_administration_home(user)
        shm_import_software_package(user)
        shm_software_administration_home(user)

    @staticmethod
    def taskset_license_delete(license_key, user, profile):
        """
         # License actions

        :param license_key: License key generated as per node
        :type license_key: str
        :param user: User object to use to make requests
        :type user: `enm_user_2.User`
        :param profile: Profile object
        :type profile: `lib.profile.Profile`
        """
        if license_key.fingerprint_id in license_key.get_imported_keys(user=user):
            try:
                license_key.delete(delete_on_enm_only=True)
            except Exception as e:
                profile.add_error_as_exception(e)

    def set_job_name_prefix(self, node, job_type):
        """
        Function to set a job prefix name depending on the node primary type.
        :type node: `enm_node.Node`
        :param node: Node to get the primary type for assigning JOB_NAME_PREFIX variable
        :param job_type: The type of the job created by profile
        :type job_type: str
        """
        node_type = node.primary_type
        if node_type in ["ERBS", "BSC", "RadioNode", "Router6672", "Router_6672", "Router6675", "MINI-LINK-669x"]:
            self.JOB_NAME_PREFIX = "{0}_{1}_{2}".format(self.NAME, job_type, node_type)

    @staticmethod
    def taskset_create_and_delete_backup(user, node, file_name, profile):
        """
        # Function to create a backup job and delete the backup on node

        :param file_name: String used for upgrade and delete job names
        :type file_name: str
        :param user: User object to use to make requests
        :type user: `enm_user_2.User`
        :param node: Node object to create and delete backup
        :type node: `enm_node.Node`
        :param profile: Profile object
        :type profile: `lib.profile.Profile`
        """
        backup_job = None
        profile.set_job_name_prefix(node, job_type="BACKUP")
        backup_start_time = profile.get_current_epoch_time_in_milliseconds
        log.logger.debug("Time recorded before backup starts: {0}".format(backup_start_time))
        try:
            backup_job = profile.upgrade_backup_util.backup_setup(user=user, nodes=[node],
                                                                  file_name=profile.JOB_NAME_PREFIX + "_" + file_name,
                                                                  repeat_count="0")
        except Exception as e:
            profile.add_error_as_exception(e)

        if backup_job is not None and backup_job.exists():
            try:
                # View job logs and export them
                view_job_details(user, backup_job)
                view_job_logs(user, backup_job)
                download_logs(user)

                # Browse help
                shm_software_help(user)

                # Updating Cleanup JobName in JOB_NAME_PREFIX
                profile.set_job_name_prefix(node, job_type="CleanUp")

                # Delete all packages from run
                profile.backup_deletion_from_node(user=user, nodes=[node], backup_start_time=backup_start_time,
                                                  name=profile.JOB_NAME_PREFIX + "_" + file_name)
            except Exception as e:
                profile.add_error_as_exception(e)

    @staticmethod
    def taskset(user_node_profile, profile):
        """
        UI Flow to be used to run this profile
        :type profile: `lib.profile.Profile`
        :param profile: profile object
        :type user_node_profile: tuple
        :param user_node_profile: `lib.enm_user.User` & `lib.enm_node.Node` instances to be used to perform the flow
        """
        user, node, license_key = user_node_profile
        file_name = ("{0}_{1}".format(profile.timestamp_str, user.username.split("_")[3]))
        shm_management = ShmManagement(node_ids=[node.node_id], user=user)

        # Staggered sleep for the parallel executions
        time.sleep(int(user.username.split('_u')[-1]) * 150)
        shm_management.supervise()
        profile.taskset_license_actions(license_key, user, profile)

        # Execute backup job
        time.sleep(20)
        shm_home(user)
        profile.taskset_create_and_delete_backup(user, node, file_name, profile)

        # Browse help
        shm_software_help(user)
        profile.taskset_license_delete(license_key, user, profile)

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        load_mgr.wait_for_setup_profile("SHM_SETUP", state_to_wait_for="COMPLETED")
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES, safe_request=True)
        nodes_lic_gen = self.get_nodes_list_by_attribute(
            node_attributes=["node_id", "primary_type", "node_name", "node_ip", "netsim"])
        synced_nodes_lic_gen = self.get_synced_nodes(nodes_lic_gen, self.TOTAL_NODES, self.NAME)
        sleep_distribution = range(0, len(synced_nodes_lic_gen) * 6, 6)
        user_node_lic_gen = zip(users, synced_nodes_lic_gen, sleep_distribution)
        while self.keep_running():
            try:
                if not self.LICENSE_PRE_CHECK:
                    # Try to generate our SHM licence first
                    self.geneate_and_assign_license(user_node_lic_gen, synced_nodes_lic_gen, users)
                node_attributes = ["node_id", "primary_type", "node_name", "node_ip", "netsim", "poid", "simulation"]
                nodes_profile = self.get_nodes_list_by_attribute(node_attributes=node_attributes)
                nodes_started = self.get_started_annotated_nodes(users[0], nodes_profile)
                synced_nodes_profile = node_pool_mgr.filter_unsynchronised_nodes(nodes_started)
                user_node_profile = zip(users, synced_nodes_profile, self.LICENCE_LIST)
                self.check_and_update_pib_values_for_backups()
                if not self.TLS_FLAG:
                    self.download_tls_certs(users)
                    self.TLS_FLAG = True
                self.create_and_execute_threads(workers=user_node_profile, thread_count=len(synced_nodes_profile),
                                                func_ref=self.taskset, args=[self], join=self.SCHEDULE_SLEEP,
                                                wait=self.SCHEDULE_SLEEP)
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()
            self.exchange_nodes()

    def geneate_and_assign_license(self, user_node_lic_gen, synced_nodes_lic_gen, users):
        """
        Perform pre-requisite actions for generating licenses, generate and assign license
        """
        SHMLicense.install_license_script_dependencies()
        self.create_and_execute_threads(workers=user_node_lic_gen, thread_count=len(synced_nodes_lic_gen),
                                        func_ref=self.tasksetlicense, args=[self], join=60, wait=60 * 10)
        self.process_user_request_errors(users)
        self.LICENSE_PRE_CHECK = True
