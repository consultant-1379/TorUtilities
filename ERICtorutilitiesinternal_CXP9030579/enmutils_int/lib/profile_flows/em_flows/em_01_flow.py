import time
from enmutils.lib import log
from enmutils.lib.exceptions import ValidationError, NetsimError, EnvironError, EnmApplicationError
from enmutils_int.lib.enm_deployment import get_values_from_global_properties
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.em import get_poids
from enmutils_int.lib.em import pull_config_files_tarball, configure_assigned_nodes


class EM01Flow(GenericFlow):

    SUCCESSFUL_NODES = []
    POIDS = []

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        users, configured_nodes = self.get_profile_users_nodes()
        while self.keep_running():
            self.sleep_until_time()
            try:
                if len(self.POIDS) < len(users):
                    self.POIDS.extend(self.retrieve_poids(configured_nodes))
                user_nodes = zip(users, set(self.POIDS))
                if user_nodes:
                    for i in range(0, len(user_nodes), self.PARALLEL_SESSIONS_LAUNCH):
                        self.create_and_execute_threads(user_nodes[i:i + self.PARALLEL_SESSIONS_LAUNCH],
                                                        len(user_nodes), args=[self])
                        log.logger.debug("Completed opening {0} sessions".
                                         format(min(i + self.PARALLEL_SESSIONS_LAUNCH, len(user_nodes))))
                time.sleep(60 * 10)
                self.validate_sessions(users)
            except Exception as e:
                self.add_error_as_exception(e)
            finally:
                try:
                    for user in users:
                        user.remove_session()
                except Exception as e:
                    self.add_error_as_exception(e)

    def get_profile_users_nodes(self):
        """
        Returns the users and nodes to be used for the profile
        """
        try:
            nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "netsim", "simulation", "primary_type",
                                                                      "node_name", "poid", 'profiles'])
            if "Extra_Large_ENM_On_Rack_Servers" in get_values_from_global_properties("enm_deployment_type"):
                users = self.create_profile_users(self.NUM_USERS_RACK, self.USER_ROLES, safe_request=True)
                self.PARALLEL_SESSIONS_LAUNCH = 4  # pylint: disable=attribute-defined-outside-init
            else:
                self.update_profile_persistence_nodes_list(nodes[self.TOTAL_NODES_NON_RACK:])
                nodes = nodes[:self.TOTAL_NODES_NON_RACK]
                users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES, safe_request=True)
            configured_nodes = self.get_configured_nodes(users, nodes)
            return users, configured_nodes
        except Exception as e:
            self.add_error_as_exception(e)

    def get_configured_nodes(self, users, nodes):
        """
        Returns the list of configured nodes

        :param users: List of lib.enm_user_2.User instances
        :type users: list
        :param nodes: List of `load_node.Node` instances
        :type nodes: list

        :rtype: list
        :return: List of configured nodes
        """
        configured_nodes, unconfigured_nodes = self.configure_nodes(nodes[:])
        if len(nodes) >= len(users):
            while len(configured_nodes) < len(users):
                newly_configured_nodes, unconfigured_nodes = self.configure_nodes(unconfigured_nodes)
                configured_nodes.extend(newly_configured_nodes)
        else:
            while len(configured_nodes) < len(nodes):
                newly_configured_nodes, unconfigured_nodes = self.configure_nodes(unconfigured_nodes)
                configured_nodes.extend(newly_configured_nodes)
        if unconfigured_nodes:
            log.logger.debug("Configuration failed for {0} nodes.".format(len(unconfigured_nodes)))
        return configured_nodes

    def retrieve_poids(self, nodes):
        """
        Retrieve the poids to be used in the EM application

        :type nodes: list
        :param nodes: List of `load_node.Node` instances to be queried in network explorer

        :rtype: list
        :return: List of poids
        """
        poids = []

        while not poids:
            poids, completed_nodes = get_poids([node for node in nodes if node not in self.SUCCESSFUL_NODES])
            poids.extend(poids)
            self.SUCCESSFUL_NODES.extend(completed_nodes)
            if not poids:
                log.logger.debug("Failed to retrieve persisted objects ids, retrying in 5 minutes.")
                time.sleep(300)
                continue
        return poids

    def configure_nodes(self, nodes):
        """
        Configures the node to use EM application

        :type nodes: list
        :param nodes: List of `load_node.Node` instances to be configured for use with EM

        :rtype: tuple
        :return: Tuple containing configured nodes, and those nodes which failed to configure correctly.
        """
        unconfigured_nodes = nodes
        configured_nodes = []
        download_dir = '/tmp/enmutils'
        tarball_local_path = ''
        try:
            tarball_local_path = pull_config_files_tarball(download_dir)
        except ValidationError:
            error_msg = ('ERROR: Could not download configuration files. Looks like some environmental issue. '
                         'Check access to Nexus.')
            self.add_error_as_exception(EnvironError(error_msg))
        except Exception as e:
            self.add_error_as_exception(e)
        if tarball_local_path and unconfigured_nodes:
            for node in unconfigured_nodes[:]:
                try:
                    configure_assigned_nodes([node], tarball_path=tarball_local_path)
                    configured_nodes.append(node)
                    unconfigured_nodes.remove(node)
                except Exception as e:
                    log.logger.debug('ERROR: Could not apply configuration on the node: {0}. Exception was: {1}'
                                     .format(node.node_id, str(e)))

            if unconfigured_nodes:
                error_msg = ('ERROR: Could not configure some of the nodes. Running with: {0} node(s)'
                             .format(len(configured_nodes)))
                log.logger.debug(error_msg)
                self.add_error_as_exception(NetsimError(error_msg))
        return configured_nodes, unconfigured_nodes

    def validate_sessions(self, users):
        """
        Checks if the required number of EM sessions are launched
        :param users: List of `lib.enm_user_2.User` instances used to fetch the active EM sessions
        :type users: list
        :raises EnmApplicationError: raised if number of sessions required were not opened successfully
        """
        response = users[0].get('/element-manager-services/desktop/session')
        if response.status_code != 200:
            raise EnmApplicationError("Unable to get the active sessions details, response: {0}".format(response.text))
        active_users = {session['userId'] for session in response.json() if "userId" in session}
        em_users = {user.username for user in users}
        log.logger.debug("active_users - {0} \nem_users - {1}".format(active_users, em_users))
        if len(active_users.intersection(em_users)) != len(users):
            raise EnmApplicationError("Unable to open the required number of sessions,\nactive user count - {0} "
                                      "and em user count - {1}\nset difference - {2}".
                                      format(len(active_users), len(em_users), em_users.difference(active_users)))

    @staticmethod
    def task_set(worker, profile):
        """
        UI Flow to be used to run this profile
        :param worker: tuple, `lib.enm_user_2.User` instance to be used to perform the flow, str POID of the node
        :type worker: tuple
        :param profile: `profile.Profile` instance to pass exceptions to
        :type profile: `profile.Profile`
        """
        user_node = worker

        def launch_em(enm_user, node_poid):
            """
            Visit the element monitor home page

            :type enm_user: lib.enm_user_2.User
            :param enm_user: User who will perform the GET requests
            :type node_poid: str
            :param node_poid: POID of the node to be accessed through ElementManager
            """

            launch_elementmanager_url = '/element-manager-services/desktop/app/elementmanager/' + node_poid
            launch_thinlinc_url = ('/main/?username={0}&pamresponse={1}&submitbutton=Login&loginsubmit=1&screen_x_size='
                                   '800&screen_y_size=600').format(enm_user.username, enm_user.password)
            enm_user.get(launch_elementmanager_url)
            time.sleep(60)
            enm_user.get(launch_thinlinc_url)
            time.sleep(120)

        user, poid = user_node
        try:
            launch_em(user, poid)
        except Exception as e:
            profile.add_error_as_exception(e)
