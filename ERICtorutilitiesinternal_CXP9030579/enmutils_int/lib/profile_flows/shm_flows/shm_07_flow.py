import random
import time

from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.services import nodemanager_adaptor
from enmutils_int.lib.shm_ui import shm_home, shm_backup_administration_home, shm_backup_go_to_topology_browser, \
    shm_license_inventory_home, shm_license_go_to_topology_browser, shm_software_administration_home, \
    shm_software_administration_upgrade_tab, shm_software_go_to_topology_browser, shm_hardware_administration_home, \
    shm_hardware_go_to_topology_browser, return_nodes_to_shm_app, shm_software_help


class Shm07Flow(ShmFlow):

    INITIAL_TASK = True

    @staticmethod
    def _taskset_return_nodes(user_to_app_tuple, nodes, profile):
        """
        UI Flow to be used to run this profile
        :param user_to_app_tuple: tuple with a user and shm app name
        :type user_to_app_tuple: tuple
        :param nodes: list of `lib.enm_node.Node` instances to be used to perform this flow
        :type nodes: list
        :param profile: profile object
        :type profile: `lib.profile.Profile`
        """
        time.sleep(random.randint(0, 3000))
        try:
            user, app = user_to_app_tuple
            shm_home(user=user)
            if "backup" in app:
                shm_backup_administration_home(user=user)
                shm_backup_go_to_topology_browser(user=user)
            elif "license" in app:
                shm_license_inventory_home(user=user)
                shm_license_go_to_topology_browser(user=user)
            elif "upgrade_pkg_list" in app:
                shm_software_administration_home(user=user)
                shm_software_administration_upgrade_tab(user=user)
                shm_software_go_to_topology_browser(user=user)
            elif "software" in app:
                shm_software_administration_home(user=user)
                shm_software_go_to_topology_browser(user=user)
            else:
                shm_hardware_administration_home(user=user)
                shm_hardware_go_to_topology_browser(user=user)

            return_nodes_to_shm_app(user=user, nodes=nodes)
        except Exception as e:
            profile.add_error_as_exception(e)

    @staticmethod
    def _taskset_software_help(user):
        """
        UI Flow to be used to keep the session alive
        :param user: `lib.enm_user.User` instance That executes the GET request
        :type user: str
        """
        shm_software_help(user)

    def create_app_list(self, user_count):
        """
        A list app_list is created with required actions backup, software, hardware, upgrade_pkg_list, license
        w.r.t number of users
        :return: list of actions to be taken
        :rtype: list
        """
        app_list = []

        for i in xrange(user_count):
            if i < user_count / 5:
                app_list.append('backup')
            elif user_count / 5 <= i < user_count * 2 / 5:
                app_list.append('software')
            elif user_count * 2 / 5 <= i < user_count * 3 / 5:
                app_list.append('hardware')
            elif user_count * 3 / 5 <= i < user_count * 4 / 5:
                app_list.append('upgrade_pkg_list')
            else:
                app_list.append('license')
        return app_list

    def execute_flow(self):
        """
        Executes the profile flow
        """
        self.state = "RUNNING"

        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False,
                                          safe_request=True, retry=True)
        user_count = len(users)
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "node_ip", "netsim", "poid",
                                                                       "simulation", "primary_type", "node_name"])
        nodes = self.get_started_annotated_nodes(user=users[0], nodes=nodes_list)

        app_list = self.create_app_list(user_count)
        # Match one user with one node
        user_to_app_tuple = zip(users, app_list)
        count = 0

        while self.keep_running():
            # Execute a number of tasksets for each user

            if not self.INITIAL_TASK and count is 0:
                # after the first iteration we no longer need the nodes, app tuple
                try:
                    node_mgr = nodemanager_adaptor if self.nodemanager_service_can_be_used else node_pool_mgr
                    node_mgr.deallocate_nodes(self)
                except Exception as e:
                    self.add_error_as_exception(e)

                nodes = []
                user_to_app_tuple = None
                count += 1

            if self.INITIAL_TASK:
                self.create_and_execute_threads(workers=user_to_app_tuple, thread_count=user_count,
                                                func_ref=self._taskset_return_nodes, args=[nodes, self],
                                                join=self.SCHEDULE_SLEEP, wait=self.SCHEDULE_SLEEP)
                self.INITIAL_TASK = False

            else:
                self.create_and_execute_threads(workers=users, thread_count=user_count,
                                                func_ref=self._taskset_software_help,
                                                join=self.SCHEDULE_SLEEP, wait=self.SCHEDULE_SLEEP)

            self.sleep()
