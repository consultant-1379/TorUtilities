# ********************************************************************
# Name    : SHM Utility Jobs
# Summary : Contains classes extracted from core SHM module. Allows
#           user to perform CRUD operations in relation to SHM restart
#           jobs and clean up jobs.
# ********************************************************************

import ast
import json

from retrying import retry

from enmutils.lib import log
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import SHM_LONG_HEADER
from enmutils_int.lib.shm import ShmJob
from enmutils_int.lib.shm_data import SHM_SOFTWARE_NODE_COMPONENTS_LIST_ENDPOINT


class RestartNodeJob(ShmJob):

    def __init__(self, *args, **kwargs):
        """
        RestartNodeJob constructor

        :type args: list
        :param args: list
        :type kwargs: list
        :param kwargs: list of arguments
        """
        kwargs.setdefault("job_type", "NODERESTART")
        super(RestartNodeJob, self).__init__(*args, **kwargs)

    def set_activities(self):
        """
        Set the job activities

        :return: List of activities to be performed by the job
        :rtype: list
        """
        return [{"activityName": "manualrestart", "execMode": "IMMEDIATE", "order": 1}]

    def set_properties(self):
        """
        Set the job properties

        :return: List of dictionaries, representing job key>value properties
        :rtype: list
        """
        properties = []
        keys = ["restartRank", "restartReason", "restartInfo"]
        values = ["RESTART_REFRESH", "PLANNED_RECONFIGURATION", "Manual Restart"]
        if self.profile_name == "SHM_47":
            values[0] = "RESTART_COLD"
        for key, value in zip(keys, values):
            d = {}
            d["key"], d["value"] = key, value
            properties.append(d)
        log.logger.debug(properties)
        return properties


class ShmBackUpCleanUpJob(ShmJob):

    def __init__(self, *args, **kwargs):
        """
        ShmBackUpCleanUpJob constructor

        :type args: list
        :param args: list
        :type kwargs: list
        :param kwargs: list of arguments
        """
        kwargs.setdefault("job_type", "BACKUP_HOUSEKEEPING")
        super(ShmBackUpCleanUpJob, self).__init__(*args, **kwargs)

    def set_activities(self):
        """
        Set the job activities

        :return: List of activities to be performed by the job
        :rtype: list
        """
        activities = [{"activityName": "deletebackup", "execMode": "IMMEDIATE", "order": 1}]
        if self.ne_type == "ERBS":
            activities[0]["activityName"] = "cleancv"
        return activities

    def set_properties(self):
        """
        Set the job properties

        :return: List of dictionaries, representing job key>value properties
        :rtype: list
        """
        properties = [{"key": "MAX_BACKUPS_TO_KEEP_ON_NODE", "value": "3"}]
        if self.ne_type == "ERBS":
            properties.extend([{"key": "CLEAR_ELIGIBLE_BACKUPS", "value": "TRUE"},
                               {"key": "BACKUPS_TO_KEEP_IN_ROLLBACK_LIST", "value": "1"}])
        return properties


class ShmBSCBackUpCleanUpJob(ShmBackUpCleanUpJob):

    def __init__(self, *args, **kwargs):
        """
        ShmBSCBackUpCleanUpJob constructor

        :type args: list
        :param args: list
        :type kwargs: list
        :param kwargs: list of arguments
        """
        self.component_names = {}
        super(ShmBSCBackUpCleanUpJob, self).__init__(*args, **kwargs)

    def set_properties(self):
        """
        Set the job properties

        :return: List of dictionaries, representing job key>value properties
        :rtype: list
        """
        if self.ne_type == "BSC":
            properties = [{"key": "MAX_BACKUPS_TO_KEEP_ON_COMPONENT_CP", "value": "20"},
                          {"key": "MAX_BACKUPS_TO_KEEP_ON_COMPONENT_APG", "value": "10"}]
            return properties

    def collect_available_backup_ne_withcomponents(self):
        """
        Function to create a dict named backup_dict, in which key
        will be nodename and value will be list of components for that node
        :rtype: dict
        :returns: dict of nodenames as keys and value as respective node components as a list
        """
        backup_dict = {}
        for node_name in self.cv_names.iterkeys():
            backup_dict[node_name] = []
            for backup_name in self.cv_names[node_name]:
                if self.cv_names[node_name][backup_name]['node__component'] not in backup_dict[node_name]:
                    backup_dict[node_name].append(self.cv_names[node_name][backup_name]['node__component'])
        return backup_dict

    @retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_fixed=60000,
           stop_max_attempt_number=3)
    def get_node_component(self, node_id):
        """
        Function to fetch the components list from a particular node using post command to url
        SHM_SOFTWARE_NODE_COMPONENTS_LIST_ENDPOINT

        :type node_id: str
        :param node_id: node_id for which the components needs to be fetched using url

        :rtype: list
        :returns: list of components in a node with given node_id
        :raises EnmApplicationError:  when shm fails to give correct response for
        POST url SHM_SOFTWARE_NODE_COMPONENTS_LIST_ENDPOINT
        """
        payload = {"neTypeToNodeNames": {"BSC": [node_id]}, "jobType": "BACKUP"}

        response = self.user.post(SHM_SOFTWARE_NODE_COMPONENTS_LIST_ENDPOINT, headers=SHM_LONG_HEADER,
                                  data=json.dumps(payload))
        raise_for_status(response)
        if response.ok and "nodeTopology" in response.text and response.json()['nodeTopology']:
            log.logger.debug('SHM job status: {0} status code: {1}'.format(response.text, response.status_code))
            index = 0
            json_components = response.json()['nodeTopology'][0]['components']
            component_names = []
            while index < len(json_components):
                component_names.extend(json_components[index]['cpNames'])
                index += 1
            return component_names
        raise EnmApplicationError("Failed to fetch node component details from {0}. Response is {1}".format(
            SHM_SOFTWARE_NODE_COMPONENTS_LIST_ENDPOINT, response.text))

    def get_node_component_dict(self):
        """
        Function to create a dictionary with node_id as key and components_list as value of it
        """
        for node in self.nodes:
            node_components = self.get_node_component(node.node_id)
            self.component_names.update(
                {node.node_id: ["{0}__{1}".format(node.node_id, x) for x in node_components]})

    def update_parent_ne_withcomponents(self):
        """
        Function to update the payload details to update the value for parentNeWithComponents
        :rtype: list
        :returns: list with dictionary of BSC payload details with keys  parentNeName, selectedComponents
        :raises EnmApplicationError:  when there exists no backups in the backup list
        """
        selected_components = []
        parent_ne_with_components = self.collect_available_backup_ne_withcomponents()
        if parent_ne_with_components:
            selected_components = [
                ast.literal_eval("{0}".format({
                    "parentNeName":
                        str(node_name),
                    "selectedComponents":
                        component_list
                })) for node_name, component_list in
                parent_ne_with_components.iteritems()
            ]
        else:
            log.logger.debug(
                "There are no list of backups present to delete after backup_start_time, considering "
                "selected node, component names of backup creation time  to delete backups further"
            )
            self.get_node_component_dict()
            selected_components = [
                ast.literal_eval("{0}".format({
                    "parentNeName":
                        node.node_id,
                    "selectedComponents":
                        self.component_names[node.node_id]
                })) for node in self.nodes
            ]
        return selected_components
