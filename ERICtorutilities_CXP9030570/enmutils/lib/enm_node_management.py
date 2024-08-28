# ********************************************************************
# Name    : ENM Node Management
# Summary : Provides FM, CM, PM, SHM supervise and synchronize
#           functionality - enable, disable, query.
# ********************************************************************

import re

from enmutils.lib import log, cache
from enmutils.lib.enm_user_2 import get_admin_user
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, EnmApplicationError


class Management(object):
    EXTRACT_INSTANCES_VALUE = r"\d+(?=\sinstance\(s\))"
    FAILED_GROUP_REGEX = r"\d+(?=\sout\sof\s\d+\sobjects)"
    EXTRACT_NODE_ID = r"(?<=NetworkElement=)(.*?)(?=,)"

    def __init__(self, node_ids="*", user=None, regex=None, ne_type=None, collections=None):
        """
        Management constructor.

        :type node_ids: list
        :param node_ids: A list of node_ids
        :type user: str or None
        :param user: The user that will be used for accessing ENM and issuing the commands.
        :type regex: str or None
        :param regex: regular expression to find node with
        :type ne_type: string or None
        :param ne_type: network element type ed. RadioNode
        :type collections: netex.Collection object
        :param collections: an enm collection of nodes
        """
        if not collections:
            self.node_ids = node_ids
            self.node_id = node_ids[0] if len(node_ids) == 1 and node_ids[0] != "*" else None
        if collections:
            self.node_ids = []
        self.collections = collections
        self.regex = regex
        self.user = user or get_admin_user()
        self.ne_type = ne_type

    @property
    def network_elements(self):
        node_ids = self.regex if self.regex else "*" if self.node_ids == "*" else ';'.join(node_id for node_id in self.node_ids)
        return node_ids

    @classmethod
    def get_management_obj(cls, nodes=None, user=None, collections=None):
        """
        Returns the enm node management object

        :type nodes: list
        :param nodes: List of nodes to perform the operation(s) upon
        :type user: `enm_user_2.User`
        :param user: Enm user user who will perform the operation(s)
        :type collections: list
        :param collections: List of `netex.Collections` objects, to perform the operation(s) upon

        :rtype: `enm_node_management.Management`
        :return: Management object that will perform the operation
        """
        if collections:
            return cls(user=user, collections=collections)
        if not nodes:
            return cls(user=user)
        return cls.get_management_obj_from_string([node.node_id for node in nodes], user=user)

    @classmethod
    def get_management_obj_from_string(cls, node_ids, user=None):
        return cls(node_ids=node_ids, user=user)

    @classmethod
    def get_status(cls, user, node_ids="*", regex=None):
        """
        Get status of responses

        :param user: user to execute command as
        :type user: enm_user_2.User
        :param node_ids: node_ids to get status of
        :type node_ids: list
        :param regex: regex to find node status with
        :type regex: str
        :return: a node status dictionary
        :rtype: dict(node_id: status)
        """
        if cls.APPLICATION == "Shm" and cache.has_key("SHM_CPP") and cache.get("SHM_CPP"):
            cls.SUPERVISION_STATUS_CMD = ('cmedit get {node_ids} NetworkElement.platformType==CPP, InventoryFunction.'
                                          'syncStatus').format(node_ids=node_ids)
        status_dict = {}
        node_ids = (regex if regex else node_ids if node_ids == "*" else ';'
                    .join("NetworkElement={0}".format(node_id) for node_id in node_ids))

        response = user.enm_execute(cls.SUPERVISION_STATUS_CMD.format(node_ids=node_ids))
        nodes_info = ",".join(response.get_output()).split("FDN")
        for node_info in nodes_info:
            match = re.search(cls.EXTRACT_SYNC_STATUS, node_info)
            node = re.search(cls.EXTRACT_NODE_ID, node_info)
            if node and match:
                status_dict[node.group(0)] = match.group(0)

        return status_dict

    def get_inventory_sync_nodes(self):
        """
        Checks the inventory sync status and returns the nodes which are synced.
        :return: list of synced nodes
        :rtype: list
        """

        sync_nodes = []
        response = self.__class__.get_status(self.user, node_ids=[node_id for node_id in self.node_ids])
        for node, status in response.iteritems():
            if re.match(r"\ASYNCHRONIZED+", status):
                sync_nodes.append(node)
        return sync_nodes

    def supervise(self, timeout_seconds=600):
        """
        Enables management in ENM on self.nodes
        """

        if self.node_id:
            response = self.user.enm_execute(self.SINGLE_SUPERVISION_CMD.format(node_ids="NetworkElement={0}".format(self.node_id), active="true"), timeout_seconds=timeout_seconds)
        elif self.ne_type:
            if self.ne_type == 'BSC':
                response = self.user.enm_execute(self.MULTIPLE_SUPERVISION_CMD_BSC.format(node_ids=self.network_elements, active="true", ne_type=self.ne_type), timeout_seconds=timeout_seconds)
            else:
                response = self.user.enm_execute(self.NETYPE_SUPERVISION_CMD.format(active="true", ne_type=self.ne_type), timeout_seconds=timeout_seconds)
        else:
            response = self.user.enm_execute(self.MULTIPLE_SUPERVISION_CMD.format(node_ids=self.network_elements, active="true"), timeout_seconds=timeout_seconds)

        self._verify_supervise_operation(response, "supervise")

    def unsupervise(self, timeout_seconds=600):
        """
        Disables management in ENM on self.nodes
        """

        if self.node_id:
            response = self.user.enm_execute(self.SINGLE_SUPERVISION_CMD.format(node_ids="NetworkElement={0}".format(self.node_id), active="false"), timeout_seconds=timeout_seconds)
        elif self.ne_type:
            if self.ne_type == 'BSC':
                response = self.user.enm_execute(self.MULTIPLE_SUPERVISION_CMD_BSC.format(node_ids=self.network_elements, active="false", ne_type=self.ne_type), timeout_seconds=timeout_seconds)
            else:
                response = self.user.enm_execute(self.NETYPE_SUPERVISION_CMD.format(active="false", ne_type=self.ne_type), timeout_seconds=timeout_seconds)
        else:
            response = self.user.enm_execute(self.MULTIPLE_SUPERVISION_CMD.format(node_ids=self.network_elements, active="false"), timeout_seconds=timeout_seconds)

        self._verify_supervise_operation(response, "unsupervise")

    def synchronize(self, netype=None, timeout=None):
        """
        Synchronizes all nodes in ENM on self.nodes

        :type netype: string or None
        :param netype: network element type ed. RadioNode
        :type timeout: int or None
        :param timeout: Command timeout. If none default of 10 minutes is selected

        :raises RuntimeError: raised if the supplied sync command is empty
        """

        msg = 'Unable to synchronize {0} as this functionality is not implemented in ENM.'.format(self.APPLICATION)
        response = None
        if not netype and not self.collections and getattr(self, 'SYNCHRONIZE_CMD', None):
            response = self.user.enm_execute(self.SYNCHRONIZE_CMD.format(node_ids=self.network_elements))
        elif self.collections and getattr(self, 'SYNCHRONIZE_COLLECTION_CMD', None):
            response = self.user.enm_execute(self.SYNCHRONIZE_COLLECTION_CMD
                                             .format(collections=";"
                                                     .join([collection.name for collection in self.collections])),
                                             timeout_seconds=timeout)
        else:
            if getattr(self, 'SYNCHRONIZE_CMD_WITH_NE_TYPE', None):
                response = self.user.enm_execute(self.SYNCHRONIZE_CMD_WITH_NE_TYPE.format(ne_type=netype))

        if response:
            self._verify_sync_operation(response, collections=self.collections)
        else:
            raise RuntimeError(msg)

    def _verify_supervise_operation(self, response, action):
        """
        Verify results of supervision commands

        :raises ScriptEngineResponseValidationError:
        """
        num_nodes = len(self.node_ids)
        cmd_output = ','.join(line for line in response.get_output())
        match = re.search(self.INSTANCE_VERIFICATION.format(num_nodes), cmd_output)
        instances_match = re.search(self.EXTRACT_INSTANCES_VALUE, cmd_output)

        if match:
            log.logger.debug(str('Successfully executed {0} {1} for {2} nodes.'
                                 .format(self.APPLICATION, action, ",".join(self.node_ids) if num_nodes < 20 else
                                         re.search(r"\d+", match.group(0)).group(0))))
        elif instances_match:
            instances_returned = int(instances_match.group(0))
            if self.network_elements == "*" or self.regex:
                search_value = self.regex if self.regex else "*"
                # Assuming there is an error in the regex passed in since no nodes have been supervised
                if instances_returned > 0:
                    log.logger.debug('Successfully executed {0} {1} for {2} nodes with {3}.'
                                     .format(self.APPLICATION, action, instances_returned, search_value))
                else:
                    raise ScriptEngineResponseValidationError('Failed {0} {1} on all nodes with regex {2}. '
                                                              'Output = {3}'
                                                              .format(action, self.APPLICATION, search_value,
                                                                      cmd_output), response)
            else:
                raise ScriptEngineResponseValidationError('Failed {0} {1} on {2}/{3}. Output = {4}'
                                                          .format(action, self.APPLICATION,
                                                                  num_nodes - instances_returned,
                                                                  num_nodes, response.get_output()), response)
        else:
            raise ScriptEngineResponseValidationError('Failed {0} {1} on specified nodes. Output = {2}'
                                                      .format(action, self.APPLICATION, cmd_output), response)

    def _verify_sync_operation(self, response, collections=None):
        """
        Verify results of synchronization commands

        :type collections: netex.Collection object
        :param collections: an enm collection of nodes
        :type response:
        :param response:
        :raises ScriptEngineResponseValidationError:
        """
        if collections:
            for collection in collections:
                self.node_ids.extend([node.node_id for node in collection.nodes])
        num_nodes = len(self.node_ids)
        cmd_output = ','.join(line for line in response.get_output())
        instances_match = re.findall(self.EXTRACT_INSTANCES_VALUE, cmd_output)
        error_match = re.search(self.FAILED_GROUP_REGEX, cmd_output)
        if instances_match:
            self._check_instance_match(instances_match, response, num_nodes)
        elif error_match:
            raise ScriptEngineResponseValidationError('Failed {0} synchronization on {1}/{2} nodes. Output = {3}'
                                                      .format(self.APPLICATION, num_nodes - int(error_match.group(0)),
                                                              num_nodes, response.get_output()), response)
        else:
            raise ScriptEngineResponseValidationError('Failed {0} synchronization. Output = {1}'
                                                      .format(self.APPLICATION, response.get_output()), response)

    def _check_instance_match(self, instances_match, response, num_nodes):
        """
        Executes instance match check

        :param instances_match: list of instances
        :type instances_match: list
        :param response: HTTP response returned by ENM
        :type response: HTTPResponse
        :param num_nodes: Number of expected nodes
        :type num_nodes: int

        :raises ScriptEngineResponseValidationError: raised if no successful instance count in response
        :raises EnvironmentError: raised if the response count does not match expected
        """

        success = bool(re.search("Successfully", str(response.get_output())))
        output = re.sub(r"[\[].*?[\]]", "", str(response.get_output()))
        if self.network_elements == "*" or self.regex:
            search_value = self.regex if self.regex else "*"
            # Assuming there is an error in the regex passed in since no nodes have been synchronized
            if success and len(instances_match) == 1:
                log.logger.debug(output)
            elif success and len(instances_match) == 2:
                raise ScriptEngineResponseValidationError("{0} synchronization initiation unsuccessful. From output: "
                                                          "'{1}'".format(self.APPLICATION, output), response)
            else:
                raise ScriptEngineResponseValidationError('Failed {0} synchronization on all nodes with regex {1}. '
                                                          'Output = {2}'.format(self.APPLICATION, search_value,
                                                                                response.get_output()), response)

        elif success and num_nodes == instances_match[-1]:
            log.logger.debug('Successfully executed {0} synchronize for {1} nodes.'
                             .format(self.APPLICATION, ",".join(self.node_ids) if len(self.node_ids) < 20 else
                                     instances_match[-1]))
        else:
            raise ScriptEngineResponseValidationError("{0} synchronization unsuccessful on {1}/{2} nodes. From Output:"
                                                      " '{3}'".format(self.APPLICATION, num_nodes - instances_match[0],
                                                                      num_nodes, output), response)


class CmManagement(Management):
    APPLICATION = "Cm"
    SINGLE_SUPERVISION_CMD = "cmedit set {node_ids},CmNodeHeartbeatSupervision=1 active={active}"
    MULTIPLE_SUPERVISION_CMD = "cmedit set {node_ids} CmNodeHeartbeatSupervision active={active}"
    NETYPE_SUPERVISION_CMD = "cmedit set * CmNodeHeartbeatSupervision active={active} -ne={ne_type}"
    SUPERVISION_STATUS_CMD = "cmedit get {node_ids} CmFunction.syncStatus"
    GENERATION_COUNTER_STATUS_CMD = "cmedit get {node_ids} CppConnectivityInformation.generationCounter"
    SYNCHRONIZE_CMD = "cmedit action {node_ids} CmFunction sync"
    SYNCHRONIZE_CMD_WITH_NE_TYPE = "cmedit action * CmFunction sync --force --neType={ne_type}"
    SYNCHRONIZE_COLLECTION_CMD = "cmedit action {collections} CmFunction=1 sync"
    INSTANCE_VERIFICATION = r"{0} instance\(s\) updated"
    EXTRACT_SYNC_STATUS = r"(?<=syncStatus\s:\s)(\w+)"
    CHECK_GENERATION_COUNTER = r"generationCounter : 0"

    def __init__(self, *args, **kwargs):
        """
        CmManagement constructor

        """
        super(CmManagement, self).__init__(*args, **kwargs)

    @classmethod
    def check_generation_counter(cls, node_id, user):
        """
        Class method to check the generation counter value

        :param node_id: Id of the node to be checked
        :type node_id: str
        :param user: User who will make the request to ENM
        :type user: `enm_user_2.User`

        :raises ScriptEngineResponseValidationError: raised the ENM request fails
        """
        response = user.enm_execute(cls.GENERATION_COUNTER_STATUS_CMD.format(node_ids="NetworkElement={0}".format(
            node_id)))

        if any(cls.CHECK_GENERATION_COUNTER in line for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Generation counter zero on node "%s". Response was "%s"' % (
                    node_id, ', '.join(response.get_output())), response=response)

    def _verify_sync_operation(self, response, collections=None):
        """
        Verify results of synchronization commands

        :param response: Response received from ENM command executed
        :type response: `response.HTTPResponse`
        :param collections: Name of the collection object to sync   #  Match overridden function
        :type collections: str

        :raises ScriptEngineResponseValidationError: raised if there is no response from ENM
        :raises EnmApplicationError: raised if not all of the nodes sync successfully
        """
        if not response or not response.get_output():
            raise ScriptEngineResponseValidationError("Cannot verify response sync operation, no response or output "
                                                      "from response.", response)
        total_nodes = len([line for line in response.get_output() if "FDN" in line])
        if any(re.search(r'(error|^[0]\sinstance)', line, re.I) for line in response.get_output()):
            failed_nodes = [line.split("NetworkElement=")[-1].split(',')[0] for line in response.get_output() if
                            "FDN" in line and "SUCCESS" not in line]
            raise EnmApplicationError('Failed {0} synchronization for {1}/{2} nodes. Failed nodes\n{3}.'.format(
                self.APPLICATION, len(failed_nodes), total_nodes, failed_nodes))
        log.logger.debug('Successfully executed {0} synchronize for {1} nodes.'.format(self.APPLICATION, total_nodes))


class FmManagement(Management):
    APPLICATION = "Fm"
    SINGLE_SUPERVISION_CMD = "cmedit set {node_ids},FmAlarmSupervision=1 active={active}"
    MULTIPLE_SUPERVISION_CMD = "cmedit set {node_ids} FmAlarmSupervision active={active}"
    NETYPE_SUPERVISION_CMD = "cmedit set * FmAlarmSupervision active={active} -ne={ne_type}"
    SUPERVISION_STATUS_CMD = "cmedit get {node_ids} FmFunction.currentServiceState"
    SYNCHRONIZE_CMD = "alarm sync {node_ids}"
    INSTANCE_VERIFICATION = r"{0} instance\(s\)"
    EXTRACT_SYNC_STATUS = r"(?<=currentServiceState\s:\s)(\w+)"

    def __init__(self, *args, **kwargs):
        """
        FmManagement constructor

        """
        super(FmManagement, self).__init__(*args, **kwargs)


class ShmManagement(Management):

    APPLICATION = "Shm"
    SINGLE_SUPERVISION_CMD = "cmedit set {node_ids},InventorySupervision=1 active={active}"
    MULTIPLE_SUPERVISION_CMD = "cmedit set {node_ids} InventorySupervision active={active}"
    MULTIPLE_SUPERVISION_CMD_BSC = "cmedit set {node_ids} InventorySupervision active={active} -neType={ne_type}"
    NETYPE_SUPERVISION_CMD = "cmedit set * InventorySupervision active={active} -ne={ne_type}"
    SUPERVISION_STATUS_CMD = "cmedit get {node_ids} InventoryFunction.syncStatus"
    SYNCHRONIZE_CMD = "cmedit action {node_ids},SHMFunction=1,InventoryFunction=1 synchronize.(invType=ALL)"
    INSTANCE_VERIFICATION = r"{0} instance\(s\) updated"
    EXTRACT_SYNC_STATUS = r"(?<=syncStatus\s:\s)(\w+)"

    def __init__(self, *args, **kwargs):
        """
        ShmManagement constructor

        """
        super(ShmManagement, self).__init__(*args, **kwargs)


class PmManagement(Management):
    APPLICATION = "Pm"
    SINGLE_SUPERVISION_CMD = "cmedit set {node_ids},PmFunction=1 pmEnabled={active}"
    MULTIPLE_SUPERVISION_CMD = "cmedit set {node_ids} PmFunction pmEnabled={active}"
    NETYPE_SUPERVISION_CMD = "cmedit set * PmFunction pmEnabled={active} -ne={ne_type}"
    SUPERVISION_STATUS_CMD = "cmedit get {node_ids} PmFunction.pmEnabled"
    INSTANCE_VERIFICATION = r"{0} instance\(s\) updated"
    EXTRACT_SYNC_STATUS = r"(?<=pmEnabled\s:\s)(\w+)"

    def __init__(self, *args, **kwargs):
        """
        PmManagement constructor

        """
        super(PmManagement, self).__init__(*args, **kwargs)
