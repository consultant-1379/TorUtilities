import time
from random import choice
import ssl
import copy
from urlparse import urlparse
import websocket
from websocket import WebSocketConnectionClosedException, WebSocketBadStatusException, WebSocketTimeoutException

from enmutils.lib import log, persistence
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.em import get_poids
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

NODECLI_WEBSOCKET_URL = "wss://%s/nodecli-websocket/%s?poid=%s"
WEB_SOCKET_CONNECTIONS = {}


class NodeCli01Flow(GenericFlow):

    poids, completed_nodes, profile_nodes, users, user_nodes = [], [], [], [], []

    def execute_flow(self):
        self.state = "RUNNING"
        self.users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        self.profile_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid"])
        while self.keep_running():
            self.teardown_list.append(persistence.picklable_boundmethod(self.close_web_socket_connections))
            try:
                if not self.poids:
                    poids, completed = self.get_node_poids(self.users[0])
                    self.poids.extend(poids)
                    self.completed_nodes.extend(completed)
                self.duplicate_poids_if_fewer_than_user_count()
            except Exception as e:
                self.add_error_as_exception(e)
                log.logger.debug("Failed to retrieve persisted objects ids, retrying in 120 seconds.")
                time.sleep(120)
                continue
            user_nodes = zip(self.users, self.poids, self.profile_nodes) * self.SESSION_MULTIPLIER
            self.create_and_execute_threads(user_nodes, thread_count=len(user_nodes), args=[self], join=1100, wait=1100)
            self.sleep()
            self.close_web_socket_connections()
            del self.teardown_list[:]

    def close_web_socket_connections(self):
        """
        Close any web socket connections which were successfully created
        """
        global WEB_SOCKET_CONNECTIONS
        for node_id in WEB_SOCKET_CONNECTIONS.keys():
            error_occurred, connection = WEB_SOCKET_CONNECTIONS.get(node_id)
            try:
                connection.close()
                log.logger.debug('Socket closed for node {0}'.format(node_id))
            except Exception as e:
                if not error_occurred:
                    self.add_error_as_exception(
                        WebSocketConnectionClosedException('Socket already closed for node {0}. {1}'.
                                                           format(node_id, str(e))))
        WEB_SOCKET_CONNECTIONS = {}

    def get_node_poids(self, user):
        """
        Get the persisted object ids from ENM for the provided nodes

        :rtype: list
        :return: List of poids, list of nodes that returned a poid
        """
        poids, completed_nodes = get_poids([node for node in self.profile_nodes if node not in self.completed_nodes])
        return poids, completed_nodes

    def duplicate_poids_if_fewer_than_user_count(self):
        """
        Reuse some persisted object ids if we have more users than ids available

        :raises EnmApplicationError: raised if there are no available poids

        :rtype: list
        :return: List of poids
        """
        if not self.poids:
            raise EnmApplicationError("No available poids to duplicate for usage.")
        if not len(self.poids) == len(self.users):
            while len(self.poids) < len(self.users):
                duplicate = choice(self.poids)
                self.poids.append(duplicate)
        return self.poids

    def websocket_connection(self, user, poid):
        """
        :param user: User object to be used to make requests
        :type user: enm_user_2.User object
        :param poid: poid associated with node
        :type poid: str
        :return: Websocket object that could be used to make websocket requests
        :rtype: object
        """
        user.get('/oss/idm/usermanagement/users/{0}'.format(user.username))
        time.sleep(1)
        parsed_url = urlparse(user.session.url())
        cookies = copy.copy(user.session.cookies)
        headers = copy.copy(user.session.headers)
        headers['Sec-WebSocket-Protocol'] = 'any-protocol'
        headers['Sec-WebSocket-Extensions'] = 'permessage-deflate; client_max_window_bits'
        cookies['TorUserID'] = user.username
        cookie = '; '.join('{0}={1}'.format(k, v) for k, v in cookies.items())
        header = [': '.join([k, v]) for k, v in cookies.items()]
        ws_url = NODECLI_WEBSOCKET_URL % (parsed_url.netloc, user.username, poid)
        time.sleep(1)
        return websocket.create_connection(ws_url, sslopt={'cert_reqs': ssl.CERT_NONE}, header=header, cookie=cookie,
                                           timeout=60 * 10)

    @staticmethod
    def task_set(worker, profile):
        """
        Task that will be executed by the thread queue
        :param worker: users, node poid, node object
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile object
        :type worker: tuple
        :raises WebSocketTimeoutException: if websocket times out
        :raises WebSocketBadStatusException: if the websocket does not have proper status
        :raises WebSocketConnectionClosedException: If connection is closed already
        :raises EnvironError: If websocket is not created
        """
        exception_occured, ws = False, None
        user, poid, node = worker
        initial_sleep_time = int(user.username.split('_u')[-1] * 1)
        log.logger.debug("USER: {username} with NODE POID: {poid} for NODE: {node} will connect after initial sleep of"
                         " {sleep} seconds.".format(username=user.username, poid=poid, node=node.node_id,
                                                    sleep=initial_sleep_time))
        time.sleep(initial_sleep_time)
        try:
            ws = profile.websocket_connection(user, poid)
            log.logger.debug('Socket created: {0}'.format(node.node_id))
        except WebSocketTimeoutException as e:
            profile.add_error_as_exception(WebSocketTimeoutException('WebSocketTimeoutException: Verify node {0} is '
                                                                     'started and is currently added to ENM correctly '
                                                                     'with its security credentials. %s'.format(node.node_id),
                                                                     str(e)))
            exception_occured = True
        except WebSocketBadStatusException as e:
            profile.add_error_as_exception(WebSocketBadStatusException(
                'Unsuccessfully created socket for user {0} using node {1}. %s %s'.format(user.username,
                                                                                          node.node_id), str(e)))
            exception_occured = True
        except Exception as e:
            profile.add_error_as_exception(EnvironError('Exception caused by {0}. {1}'.format(node.node_id, str(e))))
            exception_occured = True
        if ws:
            global WEB_SOCKET_CONNECTIONS
            WEB_SOCKET_CONNECTIONS[node.node_id] = [exception_occured, ws]
