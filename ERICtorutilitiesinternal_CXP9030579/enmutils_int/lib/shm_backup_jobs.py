# ********************************************************************
# Name    : SHM Backup Jobs
# Summary : Primarily used in SHM profiles for constructing
#           back up jobs on the nodes.
# ********************************************************************

import ast
import json

from retrying import retry

from enmutils.lib import arguments, log
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import SHM_LONG_HEADER
from enmutils_int.lib.shm_data import SHM_SOFTWARE_NODE_COMPONENTS_LIST_ENDPOINT
from enmutils_int.lib.shm_job import ShmJob


class BackupJobCPP(ShmJob):

    def __init__(self, *args, **kwargs):
        """
        BackupJobCPP constructor

        :type args: list
        :param args: arguments list
        :type kwargs: list
        :param kwargs: arguments list
        """

        log.logger.debug(".........Entered into backup jobs file.......")
        random_suffix = arguments.get_random_string(4)
        kwargs.setdefault("job_type", "BACKUP")
        self.cv_id = kwargs.pop("cv_id", "{0}".format(random_suffix))
        self.cv_type = kwargs.pop("cv_type", "STANDARD")
        self.remove_from_rollback_list = kwargs.pop("remove_from_rollback_list", "FALSE")
        super(BackupJobCPP, self).__init__(*args, **kwargs)
        self.ne_type = "ERBS"
        self.platform = "CPP"

    def set_properties(self):
        """
        Properties payload for CPP Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        properties = [
            {"key": "CV_NAME", "value": self.file_name},
            {"key": "CV_IDENTITY", "value": self.cv_id},
            {"key": "CV_TYPE", "value": self.cv_type},
            {"key": "ROLLBACK_CV_NAME", "value": self.file_name},
            {"key": "UPLOAD_CV_NAME", "value": self.file_name},
            {"key": "STARTABLE_CV_NAME", "value": self.file_name},
        ]

        return properties

    def set_activities(self):
        """
        Properties payload for CPP Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        activities = [
            {"activityName": "createcv", "execMode": "IMMEDIATE", "order": 1},
            {"activityName": "exportcv", "execMode": "IMMEDIATE", "order": 4},
            {"activityName": "setcvasstartable", "execMode": "IMMEDIATE", "order": 2},
            {"activityName": "setcvfirstinrollbacklist", "execMode": "IMMEDIATE", "order": 3}
        ]
        if not self.set_as_startable:
            return activities[0:2]
        return activities

    def set_configurations(self):
        """
        Configurations payload for CPP Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """

        configurations = [
            {
                "neType": node_type,
                "properties": self.set_properties()
            } for node_type in self.node_types
        ]
        return configurations

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


class BackupJobCOMECIM(ShmJob):

    def __init__(self, *args, **kwargs):
        """
        BackupJobCOMECIM constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: list
        :param kwargs: list of arguments
        """
        kwargs.setdefault("job_type", "BACKUP")
        self.remove_from_rollback_list = kwargs.pop("remove_from_rollback_list", "FALSE")
        super(BackupJobCOMECIM, self).__init__(*args, **kwargs)
        self.platform = "ECIM"

    def set_properties(self):
        """
        Properties payload for COM/ECIM Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [
            {"value": self.name, "key": "BACKUP_NAME"},
            {"key": "UPLOAD_CV_NAME", "value": self.file_name},
            {"value": "System/Systemdata", "key": "BACKUP_DOMAIN_TYPE"}
        ]

    def set_activities(self):
        """
        Activities payload for COM/ECIM Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [
            {"activityName": "createbackup", "execMode": "IMMEDIATE", "order": 1},
            {"activityName": "uploadbackup", "execMode": "IMMEDIATE", "order": 2}
        ]


class BackupJobSGSN(BackupJobCOMECIM):

    def __init__(self, *args, **kwargs):
        """
        BackupJobSGSN constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: list
        :param kwargs: list of arguments
        """

        kwargs.setdefault("job_type", "BACKUP")
        self.remove_from_rollback_list = kwargs.pop("remove_from_rollback_list", "FALSE")
        super(BackupJobSGSN, self).__init__(*args, **kwargs)
        self.platform = "ECIM"

    def set_properties(self):
        """
        Properties payload for SGSN Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [
            {"key": "BACKUP_NAME", "value": self.name, },
            {"key": "BACKUP_DOMAIN_TYPE", "value": "System Local/System Local Data", }
        ]


class BackupJobBSC(BackupJobCOMECIM):

    def __init__(self, *args, **kwargs):
        """
        BackupJobBSC constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: list
        :param kwargs: list of arguments
        """
        kwargs.setdefault("job_type", "BACKUP")
        super(BackupJobBSC, self).__init__(*args, **kwargs)
        self.ne_type = "BSC"
        self.platform = "AXE"
        self.use_default_config = True
        self.component_names = {}

    def set_configurations(self):
        """
        Configurations payload for BSC Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [{"platform": self.platform, "properties": []}, {"neType": self.ne_type, "properties": []}]

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

    def update_neTypeComponentActivityDetails(self):
        """
        Function to update the payload details to update the value for neTypeComponentActivityDetails
        :rtype: list
        :returns: list with dictionary of BSC payload details with keys componentActivities, neType
        """
        self.get_node_component_dict()
        for component_name in self.component_names.values():
            component_json_data = [ast.literal_eval("{0}".format({"componentName": component,
                                                                  "activityNames": ["createbackup",
                                                                                    "uploadbackup"]}))
                                   for component in component_name]

        return [{"neType": "BSC", "componentActivities": component_json_data}]

    def update_parent_ne_withcomponents(self):
        """
        Function to update the payload details to update the value for parentNeWithComponents
        :rtype: list
        :returns: list with dictionary of BSC payload details with keys  parentNeName, selectedComponents
        :raises EnmApplicationError:  when there exists no backups in the backup list
        """
        selected_components = []
        selected_components = [
            ast.literal_eval("{0}".format({
                "parentNeName":
                node.node_id,
                "selectedComponents":
                self.component_names[node.node_id]
            })) for node in self.nodes
        ]
        return selected_components


class BackupJobSpitFire(BackupJobCOMECIM):

    def __init__(self, *args, **kwargs):
        """
        BackupJobSpitFire constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: list
        :param kwargs: list of arguments
        """
        kwargs.setdefault("job_type", "BACKUP")
        super(BackupJobSpitFire, self).__init__(*args, **kwargs)
        self.ne_type = "Router6672"
        self.platform = "ECIM"
        self.use_default_config = False

    def set_properties(self):
        """
        Properties payload for Spitfire Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [
            {"platform": self.platform, "properties": []},
            {"neType": self.ne_type, "properties": [
                {"key": "BACKUP_NAME", "value": self.name},
                {"key": "BACKUP_DOMAIN_TYPE", "value": "System/Configuration"}
            ]}
        ]


class BackupJobRouter6675(BackupJobCOMECIM):

    def __init__(self, *args, **kwargs):
        """
        BackupJobRouter6675 constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: dict
        :param kwargs: dict of arguments
        """

        kwargs.setdefault("job_type", "BACKUP")
        super(BackupJobRouter6675, self).__init__(*args, **kwargs)
        self.ne_type = "Router6675"
        self.platform = "ECIM"
        self.use_default_config = False

    def set_properties(self):
        """
        Properties payload for Router6675 Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [
            {"platform": self.platform, "properties": []},
            {"neType": self.ne_type, "properties": [
                {"key": "BACKUP_NAME", "value": self.name},
                {"key": "BACKUP_DOMAIN_TYPE", "value": "System/Configuration"}
            ]}
        ]


class BackupJobMiniLink(BackupJobSpitFire):

    def __init__(self, *args, **kwargs):
        """
        BackupJobMiniLink constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: list
        :param kwargs: list of arguments
        """
        super(BackupJobMiniLink, self).__init__(*args, **kwargs)
        self.ne_type = "MINI-LINK-Indoor"
        self.platform = "MINI_LINK_INDOOR"

    def set_properties(self):
        """
        Properties payload for MiniLink Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [
            {"platform": self.platform, "properties": []},
            {"neType": self.ne_type, "properties": [
                {"key": "BACKUP_NAME", "value": self.name}
            ]}
        ]

    def set_activities(self):
        """
        Activities payload for MiniLink Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [{"activityName": "backup", "execMode": "IMMEDIATE", "order": 1}]


class BackupJobMiniLink669x(BackupJobMiniLink):

    def __init__(self, *args, **kwargs):
        """
        BackupJobMiniLink669x constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: dict
        :param kwargs: dictionary of arguments
        """
        super(BackupJobMiniLink669x, self).__init__(*args, **kwargs)
        self.ne_type = "MINI-LINK-669x"
        self.platform = "MINI_LINK_INDOOR"


class BackupJobMiniLink6352(BackupJobSpitFire):

    def __init__(self, *args, **kwargs):
        """
        BackupJobMiniLink6352 constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: dict
        :param kwargs: dictionary of arguments
        """
        super(BackupJobMiniLink6352, self).__init__(*args, **kwargs)
        self.ne_type = "MINI-LINK-6352"
        self.platform = "MINI_LINK_OUTDOOR"

    def set_properties(self):
        """
        Properties payload for MiniLink Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [
            {"platform": self.platform, "properties": []},
            {"neType": self.ne_type, "properties": [
                {"key": "BACKUP_NAME", "value": self.name}
            ]}
        ]

    def set_activities(self):
        """
        Activities payload for MiniLink Backup Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [{"activityName": "backup", "execMode": "IMMEDIATE", "order": 1}]
