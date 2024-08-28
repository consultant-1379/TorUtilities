# ********************************************************************
# Name    : SHM Delete Jobs
# Summary : Primarily used in SHM profiles for constructing
#           back up delete jobs on the nodes.
# ********************************************************************

import ast
import json
from collections import defaultdict

from enmutils.lib import log
from enmutils.lib.headers import SHM_LONG_HEADER
from enmutils_int.lib.shm_backup_jobs import BackupJobCPP, BackupJobBSC
from enmutils_int.lib.shm_data import SHM_BACKUP_ITEMS
from enmutils_int.lib.shm_job import ShmJob
from requests.exceptions import HTTPError
from retrying import retry


class DeleteBackupOnNodeJob(BackupJobCPP, BackupJobBSC):

    def __init__(self, *args, **kwargs):
        """
        DeleteBackupOnNodeJob constructor
        :type args: list
        :param args: list of arguments
        :type kwargs: list
        :param kwargs: list of arguments
        """
        self.remove_from_rollback_list = kwargs.pop("remove_from_rollback_list", "FALSE")
        self.resolve_cv_name = kwargs.pop("resolve_cv_name", False)
        kwargs.setdefault("job_type", "DELETEBACKUP")
        super(DeleteBackupOnNodeJob, self).__init__(*args, **kwargs)
        self.platform = kwargs.pop("platform", None)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=60000, stop_max_attempt_number=3)
    def get_cvnames(self, node_id):
        """
        Queries SHM for list of CV related to the nodes in the payload

        :type node_id: str
        :param node_id: Node_id for which backup needs to be retrieved
        :raises HTTPError:  when shm backups are not retrieved correctly
        :rtype: str
        :returns: String representing stored CV name on the node(s)
        """
        payload = {
            "fdns": ["NetworkElement={0}".format(node_id)],
            "offset": 1,
            "limit": 50,
            "sortBy": "date",
            "ascending": False,
            "filterDetails": []
        }
        response = self.user.post(SHM_BACKUP_ITEMS, json=payload, headers=SHM_LONG_HEADER)
        if not response.ok:
            raise HTTPError('Failed to retrieve shm backups correctly. Check logs for details. Response was "{0}"'
                            .format(response.text), response=response)
        return json.loads(response.text)

    def get_node_backup_items(self, all_backups=False):
        """
        matches cvnames retrieved against the associated backup jobs name.

        :type all_backups: bool
        :param all_backups: Boolean indicating whether or not to retrieve all available cvs
        :rtype: str
        :returns: String representing stored CV name on the node(s)
        """

        cv_names = self.get_cvnames(self.nodes[0].node_id)
        if all_backups:
            return cv_names['backupItemList']
        elif cv_names['backupItemList']:
            for backup in cv_names['backupItemList']:
                if self.file_name in backup['name'] and backup['location'] == "NODE":
                    return backup['name']
        return []

    def set_properties(self):
        """
        Properties payload for DeleteBackupOnNodeJob

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        if self.resolve_cv_name:
            self.file_name = self.get_node_backup_items() if self.get_node_backup_items() else self.file_name
        ne_list_types = self._ne_list_types()
        payload = []
        for key, value in ne_list_types.iteritems():
            payload.append({"neType": key,
                            "properties": [{"key": "ROLL_BACK", "value": self.remove_from_rollback_list}],
                            "neProperties": ne_list_types[key]})
            log.logger.debug('neProperties key: {0} value: {1}'.format(key, value))
        return payload

    def set_multiple_activities(self):
        """
        Activities payload for CPP Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """

        activities = [
            {
                "platformType": self.platform,
                "value": [
                    {
                        "neType": node_type,
                        "value": self.set_activities()
                    } for node_type in self.node_types
                ]
            }
        ]
        return activities


class DeleteBackupOnNodeJobCPP(DeleteBackupOnNodeJob):

    def __init__(self, *args, **kwargs):
        """
        DeleteBackupOnNodeJob constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: list
        :param kwargs: list of arguments
        """
        kwargs.setdefault("job_type", "DELETEBACKUP")
        super(DeleteBackupOnNodeJobCPP, self).__init__(*args, **kwargs)

    def _ne_list_types(self):
        """
        Function to return network list types

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        ne_list_types = {}
        for node in self.nodes:
            tmp_type = node.primary_type
            ne_list_types[tmp_type] = [] if not ne_list_types.get(tmp_type) else ne_list_types[tmp_type]
            ne_list_types[tmp_type].append({"neNames": node.node_id,
                                            "properties": [
                                                {"key": "CV_NAME", "value": "{0}|NODE".format(self.file_name)}]})
        return ne_list_types

    def set_activities(self):
        """
        Activities payload for DeleteBackupOnNodeJob

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [
            {"activityName": "deletecv", "execMode": "IMMEDIATE", "order": 1}
        ]


class DeleteBackupOnNodeJobBSC(DeleteBackupOnNodeJob):

    def __init__(self, *args, **kwargs):
        """
        DeleteBackupOnNodeJobBSC constructor

        :type args: list
        :param args: arguments list
        :type kwargs: list
        :param kwargs: arguments list
        """
        kwargs.setdefault("job_type", "DELETEBACKUP")
        super(DeleteBackupOnNodeJobBSC, self).__init__(*args, **kwargs)
        self.ne_type = "BSC"
        self.platform = "AXE"

    def _ne_list_types(self):
        """
        Function to form two dicts ne_list_types, ne_list_node_component_backups with below format
        ne_list_node_component_backups = { 'n/w type of node' : {'node__component' : [ backup_name ]} ,
                                                             'node__component' : [ backup_name ]} }
        ne_list_types = { 'n/w type of node' : [ {neNames: '', properties: []}, {neNames: '', properties: []}] }
        :rtype: dict
        :returns: dict of neProperties for respective node_types(s)
        """
        log.logger.debug("Attempting to sort backup details according to NE names and few properties required "
                         "for payload..")
        ne_list_types = {}
        ne_list_node_component_backups = {}
        for node_name in self.cv_names.iterkeys():
            for backup_name in self.cv_names[node_name]:
                tmp_type = self.cv_names[node_name][backup_name]['neType']
                if tmp_type not in ne_list_node_component_backups:
                    ne_list_node_component_backups[tmp_type] = {}
                self.cv_names[node_name][backup_name][
                    'node__component'] = "{0}__{1}".format(
                        self.cv_names[node_name][backup_name]['nodeName'],
                        self.cv_names[node_name][backup_name]['componentName'])
                if self.cv_names[node_name][backup_name][
                        'node__component'] not in ne_list_node_component_backups[
                            tmp_type]:
                    ne_list_node_component_backups[tmp_type][self.cv_names[
                        node_name][backup_name]['node__component']] = []
                ne_list_node_component_backups[tmp_type][
                    self.cv_names[node_name][backup_name]
                    ['node__component']].append(backup_name)

        for network_type in ne_list_node_component_backups.iterkeys():
            ne_list_types[network_type] = []
            for component, backup_list in ne_list_node_component_backups[network_type].iteritems():
                backup_list_appended = [backup + "|NODE" for backup in backup_list]
                ne_list_types[network_type].append({"neNames": component,
                                                    "properties": [{"key": "BACKUP_NAME",
                                                                    "value": str(",".join(backup_list_appended))}]})
        log.logger.debug("Successfully sorted backup details according to NE names and few properties required "
                         "for payload..")
        return ne_list_types

    def get_node_backup_list(self, node_id):
        """
        Queries SHM for list of CV related to the nodes in the payload, filters the list backup creation date which is
        greater than backup_start_time
        is
        :type node_id: str
        :param node_id: node_id of node for which backup items should be collected and returned
        :rtype: dict
        :returns: dict representing key as stored CV name and values as respective backup details dict
        """
        log.logger.debug("Attempting to get node backup list..")
        node_component_backups_list = defaultdict(dict)

        cv_names = self.get_cvnames(node_id)
        if 'backupItemList' in cv_names:
            for backup in cv_names['backupItemList']:
                if ('name' in backup and backup['date'] is not None and
                        backup['location'] == "NODE" and int(backup['date']) > self.backup_start_time):
                    node_component_backups_list[backup['nodeName']].update({backup['name']: backup})
                    if backup['nodeName'] not in self.nodes_with_component_backups:
                        self.nodes_with_component_backups.append(str(backup['nodeName']))
            log.logger.debug("Successfully retrieved the backup list..")
        else:
            log.logger.error("Cannot retrieve the backup list.. Backup list json does not have backupItemList entry..")
        return node_component_backups_list

    def set_properties(self):
        """
        Properties payload for DeleteBackupOnNodeJobBSC

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        log.logger.debug("Attempting to set properties required for payload..")
        for node in self.nodes:
            self.cv_names.update(self.get_node_backup_list(node.node_id))
        ne_list_types = self._ne_list_types()
        payload = []
        for key, value in ne_list_types.iteritems():
            payload.append({"neType": str(key),
                            "properties": [{"key": "ROLL_BACK", "value": self.remove_from_rollback_list}],
                            "neProperties": value})
        log.logger.debug("Successfully completed setting properties required for payload..")
        return payload

    def set_activities(self):
        """
        Activities payload for DeleteBackupOnNodeJob

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        log.logger.debug("Fetching actvities required for payload..")
        return [
            {"activityName": "deletebackup", "execMode": "IMMEDIATE", "order": 1}
        ]

    def set_ne_names(self):
        """
        Method for building up the ne name dictionaries for BSC, which include only nodes with existing backups

        :rtype: list
        :return: List of containing dictionary(ies), of name -> "name", key -> values
        """
        log.logger.debug("Fetching nodes details which has backups required for payload..")
        return [{"name": node} for node in self.nodes_with_component_backups]

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


class DeleteSoftwarePackageOnNodeJob(ShmJob):

    def __init__(self, *args, **kwargs):
        """
        Delete Software Package from Node Job Constructor
        """
        kwargs.setdefault("job_type", "DELETE_UPGRADEPACKAGE")
        super(DeleteSoftwarePackageOnNodeJob, self).__init__(*args, **kwargs)
        self.package_list = kwargs.pop('upgrade_list', [])
        self.upgrade_list = "**|**".join([_ for _ in self.package_list])
        self.delete_from_rollback_list = kwargs.pop('delete_from_rollback_list', "true")
        self.delete_referred_ups = kwargs.pop('delete_referred_ups', "true")

    def set_configurations(self):
        """
        Configurations payload for Delete Software Upgrade Package Job

        :rtype: list
        :return: list of dictionary, key value pairs
        """

        properties = list()
        properties.append({
            "neType": self.ne_type,
            "properties": [{"key": "deleteFromRollbackList", "value": self.delete_from_rollback_list},
                           {"key": "deleteReferredUPs", "value": self.delete_referred_ups}],
            "neProperties": self.set_properties()
        })
        if not self.platform == "CPP":
            properties[0]["properties"] = [{"key": "deleteReferredUPs", "value": self.delete_referred_ups}]
        return properties

    def set_multiple_activities(self):
        """
        Activities payload for CPP Backup Job
        :rtype:  list
        :returns: list of dictionary, key value pairs
        """
        activities = [
            {
                "platformType": self.platform,
                "value": [
                    {
                        "neType": node_type,
                        "value": self.set_activities()
                    } for node_type in self.node_types
                ]
            }
        ]
        return activities

    def set_activities(self):
        """
        Activities for Delete Software Upgrade Package Job
        :rtype: list
        :return: list of activities
        """
        return [{"activityName": "deleteupgradepackage", "execMode": "IMMEDIATE", "order": 1}]

    def set_properties(self):
        """
        Properties for Delete Software Upgrade Package Job

        :rtype: list
        :return: List of dictionaries for each node
        """
        properties = []
        for node in self.nodes:
            properties.append({"neNames": node.node_id,
                               "properties": [{"key": "deleteUPList", "value": self.upgrade_list}]})
        return properties


class DeleteInactiveSoftwarePackageOnNodeJob(DeleteSoftwarePackageOnNodeJob):

    def __init__(self, *args, **kwargs):
        """
        Delete Inactive Software Package from Node Job Constructor
        """
        kwargs.setdefault("job_type", "DELETE_UPGRADEPACKAGE")
        super(DeleteInactiveSoftwarePackageOnNodeJob, self).__init__(*args, **kwargs)

    def set_configurations(self):
        """
        Configurations payload for Delete Inactive Software Upgrade Package Job

        :rtype: list
        :return: list of dictionary, key value pairs
        """

        properties = list()
        properties.append({
            "neType": self.ne_type,
            "properties": [{"key": "deleteReferredBackups", "value": "true"}],
            "neProperties": self.set_properties()
        })
        if self.platform == "CPP":
            properties[0]["properties"] = [{"key": "deleteReferredUPs", "value": "true"},
                                           {"key": "deleteFromRollbackList", "value": "true"}]
        return properties

    def set_properties(self):
        """
        Properties for Delete Inactive Software Upgrade Package Job

        :rtype: list
        :return: List of dictionaries for each node
        """
        properties = []
        for node in self.nodes:
            properties.append({"neNames": node.node_id,
                               "properties": [{"key": "deleteNonActiveUps",
                                               "value": "true"}]})
        return properties
