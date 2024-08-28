# ********************************************************************
# Name    : SHM
# Summary : Primarily used by SHM profiles. Allows the user to manage
#           multiple operations within the SHM application area,
#           including but not limited all CRUD operations in relation
#           to Backup, Upgrade, Licence Key, Software Packages,
#           Restore, Deletion of generated content such as CVs and
#           Upgrade Package, and Exports.
# ********************************************************************

import json

from requests.exceptions import HTTPError
from retrying import retry

from enmutils.lib import log
from enmutils.lib.enm_user_2 import raise_for_status, verify_json_response
from enmutils.lib.exceptions import EnmApplicationError, JobValidationError
from enmutils.lib.headers import SHM_LONG_HEADER
from enmutils_int.lib.shm_data import (PLATFORM_TYPES, SHM_EXPORT_CSV_ENDPOINT, SHM_EXPORT_ENDPOINT)
from enmutils_int.lib.shm_job import ShmJob


class RestoreJob(ShmJob):

    def __init__(self, *args, **kwargs):
        """
        RestoreJob constructor

        :type args: list
        :param args: list of arguments
        :type kwargs: list
        :param kwargs: list of arguments
        """
        kwargs.setdefault("job_type", "RESTORE")
        super(RestoreJob, self).__init__(*args, **kwargs)

    def set_properties(self):
        """
        Properties payload for RestoreJob

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        ne_list = list()
        for node in self.nodes:
            ne_list.append({"neNames": node.node_id,
                            "properties": [
                                {"key": "CV_LOCATION", "value": "ENM"},
                                {"key": "CV_NAME", "value": self.file_name},
                                {"key": "CV_TYPE", "value": "STANDARD"},
                                {"key": "CV_FILE_NAME", "value": "{0}.zip".format(self.file_name)}
                            ]})
        payload = [{"neType": self.ne_type,
                    "properties": [{"key": "INSTALL_MISSING_UPGRADE_PACKAGES", "value": "false"},
                                   {"key": "REPLACE_CORRUPTED_UPGRADE_PACKAGES", "value": "false"},
                                   {"key": "AUTO_CONFIGURATION", "value": "AS_CONFIGURED"},
                                   {"key": "FORCED_RESTORE", "value": "true"}],
                    "neProperties": ne_list}]
        return payload

    def set_activities(self):
        """
        Activities payload for RestoreJob

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        return [
            {"activityName": "download", "execMode": "IMMEDIATE", "order": 1, "scheduleAttributes": []},
            {"activityName": "verify", "execMode": "IMMEDIATE", "order": 2, "scheduleAttributes": []},
            {"activityName": "restore", "execMode": "IMMEDIATE", "order": 4, "scheduleAttributes": []},
            {"activityName": "confirm", "execMode": "IMMEDIATE", "order": 5, "scheduleAttributes": []}
        ]


class UpgradeJob(ShmJob):

    def __init__(self, *args, **kwargs):
        """
        UpgradeJob constructor
        """
        kwargs.setdefault("job_type", "UPGRADE")
        super(UpgradeJob, self).__init__(*args, **kwargs)
        self.software_identity = None
        self.software_revision = None
        self.set_software_values()
        self.update_ne_type_and_platform()

    def update_ne_type_and_platform(self):
        """
        Update to the supported SHM ne types and platform if needed
        """
        if self.ne_type in ["MLTN", "LH", "MINI-LINK-Indoor"]:
            self.ne_type = 'MINI-LINK-Indoor'
            self.platform = 'MINI_LINK_INDOOR'
        elif self.ne_type in ["MINI-LINK-669x"]:
            self.platform = PLATFORM_TYPES.get(self.ne_type)
        elif self.ne_type in ["MINI-LINK-6352"]:
            self.platform = "MINI_LINK_OUTDOOR"
        elif self.ne_type in ["Router6672", "Router6675", "SCU"]:
            self.platform = 'ECIM'
        elif self.ne_type in ["TCU02", "SIU02"]:
            self.platform = 'STN'
        elif self.ne_type in ["BSC"]:
            self.platform = 'AXE'

    def set_software_values(self):
        """
        Update to the correct software values if needed
        """
        if self.ne_type in ["MLTN", "LH", "Router6672", "Router6675", "SCU",
                            "TCU02", "SIU02", "BSC", "MINI-LINK-6352", "MINI-LINK-Indoor", "MINI-LINK-669x"] and self.software_package:
            self.software_identity = self.software_package.node_identity
            self.software_revision = self.software_package.node_mim

    def set_properties(self):
        """
        Properties payload for Upgrade Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        if self.ne_type == "ERBS":
            properties = [
                {"key": "SWP_NAME", "value": self.package_name},
                {"key": "UCF", "value": "{0}.xml".format(self.package_name)},
                {"key": "FORCEINSTALL", "value": "full"},
                {"key": "SELECTIVEINSTALL", "value": "not selective"},
                {"key": "REBOOTNODEUPGRADE", "value": self.reboot_node}
            ]
            if self.install_verify_only:
                properties = properties[:4]
        elif self.ne_type == "RadioNode":
            properties = [{"key": "SWP_NAME", "value": self.package_name}]
        elif self.ne_type == "BSC":
            properties = [
                {"key": "SWP_NAME", "value": self.package_name},
                {"key": "productNumber", "value": ""},
                {"key": "productRevision", "value": self.software_revision},
                {"key": "productName", "value": self.software_identity},
                {"key": "network_element", "value": ""}
            ]
        else:
            properties = [
                {"key": "SWP_NAME", "value": self.package_name},
                {"key": "productNumber", "value": self.software_identity},
                {"key": "productRevision", "value": self.software_revision}
            ]
        return properties

    def set_activities(self):
        """
        Activities payload for Upgrade Job

        :rtype: list
        :returns: list of dictionary, key value pairs
        """
        if self.ne_type in ["MINI-LINK-Indoor", "MINI-LINK-6352", "MINI-LINK-669x"]:
            activities = [
                {"activityName": "download", "execMode": "IMMEDIATE", "order": 1, "scheduleAttributes": []},
                {"activityName": "activate", "execMode": "IMMEDIATE", "order": 2, "scheduleAttributes": []},
                {"activityName": "confirm", "execMode": "IMMEDIATE", "order": 3, "scheduleAttributes": []}
            ]
        elif self.ne_type in ["RadioNode", "Router6672", "Router6675"]:
            activities = [
                {"activityName": "prepare", "execMode": "IMMEDIATE", "order": 1},
                {"activityName": "verify", "execMode": "IMMEDIATE", "order": 2},
                {"activityName": "activate", "execMode": "IMMEDIATE", "order": 3},
                {"activityName": "confirm", "execMode": "IMMEDIATE", "order": 4}
            ]
        elif self.ne_type in ["TCU02", "SIU02"]:
            activities = [
                {"activityName": "install", "execMode": "IMMEDIATE", "order": 1, "scheduleAttributes": []},
                {"activityName": "upgrade", "execMode": "IMMEDIATE", "order": 2, "scheduleAttributes": []},
                {"activityName": "approvesw", "execMode": "IMMEDIATE", "order": 3, "scheduleAttributes": []},
                {"activityName": "swadjust", "execMode": "IMMEDIATE", "order": 4, "scheduleAttributes": []}
            ]
        elif self.ne_type in ["BSC"]:
            activities = [
                {"activityName": "Test script", "execMode": "IMMEDIATE", "order": 1, "scheduleAttributes": []},
            ]
        elif self.ne_type in ["SCU"]:
            activities = [
                {"activityName": "prepare", "execMode": "IMMEDIATE", "order": 1, "scheduleAttributes": []},
                {"activityName": "activate", "execMode": "IMMEDIATE", "order": 2, "scheduleAttributes": []},
                {"activityName": "confirm", "execMode": "IMMEDIATE", "order": 3, "scheduleAttributes": []}
            ]
        else:
            activities = [
                {"activityName": "install", "execMode": "IMMEDIATE", "order": 1},
                {"activityName": "verify", "execMode": "IMMEDIATE", "order": 2},
                {"activityName": "upgrade", "execMode": "IMMEDIATE", "order": 3},
                {"activityName": "confirm", "execMode": "IMMEDIATE", "order": 4}
            ]
        return self.filter_activities(activities)

    def set_neProperties(self):
        properties = []
        for node in self.nodes:
            properties.append({"neNames": node.node_id,
                               "properties": []})
        return properties

    def setActivityJobProperies(self):
        return [{"activityName": "Test script",
                 "properties": [{"key": "_POPUP_WINDOWS", "value": "N"},
                                {"key": "Script", "value": "OPS/enm_test.ccf"}]}]

    def filter_activities(self, activities):
        """
        Update the list of activities based on whether or not all steps are to be completed

        :param activities: List of Shm Upgrade activities
        :type activities: list

        :return: Filtered list of dictionary, key value pairs
        :rtype: list
        """
        if self.install_verify_only:
            if self.ne_type == "MINI-LINK-Indoor":
                activities = activities[:1]
            else:
                activities = activities[:2]
        elif self.upgrade_commit_only:
            activities = activities[-2:]
        return activities


class SHMExport(object):

    def __init__(self, user, nodes, export_type="SOFTWARE"):
        """
        Constructor for SHM Exports
        :type nodes: list
        :param nodes: List of nodes to export
        :type export_type: str
        :param export_type: Type of export to perform, Hardware/Software/Licence
        :type user: `enm_user_2.User`
        :param user: User to perform the REST request
        """
        self.nodes = ["NetworkElement=%s" % node.node_id for node in nodes]
        self.export_type = export_type
        self.user = user
        self.export_id = None

    def verify_csv_created(self, response):
        """
        Update the wait fixed time and number of attempts for progress check of export job
        EXPORT TYPE: HARDWARE, WAIT_TIME: 5hours, RETRY_VALUE: 15min.
        EXPORT TYPE: LICENSE/SOFTWARE, WAIT_TIME: 1 hour, RETRY_VALUE: 1 min.

        :type response: `requests.Response`
        :param response: Response object

        :rtype: func
        :returns: Returns decorated function
        """
        time_wait = 900000 if self.export_type == "HARDWARE" else 60000
        retry_value = 20 if self.export_type == "HARDWARE" else 60
        log.logger.debug("Updated wait time is {0} in milliseconds and retry value is {1} reattempts".
                         format(time_wait, retry_value))
        check_job_progress = retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError),
                                   wait_fixed=time_wait, stop_max_attempt_number=retry_value)(self._verify_csv_created)
        return check_job_progress(response)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=60000, stop_max_attempt_number=3)
    def create(self):
        """
        Creates an SHM export

        :raises HTTPError: when failed to export shm correctly
        """
        payload = {
            "offset": 1,
            "limit": 50,
            "sortBy": "fdn",
            "ascending": True,
            "neFdns": self.nodes,
            "inventoryType": self.export_type,
            "fileFormat": "csv",
            "isNewExport": False,
            "filterDetails": []
        }
        response = self.user.post(SHM_EXPORT_ENDPOINT, headers=SHM_LONG_HEADER, data=json.dumps(payload))
        if not response.ok:
            log.logger.debug("Export failed, Response was: {0}".format(response.text))
            raise HTTPError('Failed to export shm {0} correctly. Check logs for details.'
                            .format(self.export_type), response=response)
        self.verify_csv_created(response)

    def _verify_csv_created(self, response):
        """
        Request the SHM export resource
        :type response: `requests.Response`
        :param response: Response object
        :raises EnmApplicationError: when shm export did not complete successfully
        :raises JobValidationError: when there is no value for request if in json

        :rtype: bool
        :return: Boolean
        """
        verify_json_response(response)
        self.export_id = response.json()['requestId']
        if self.export_id is not None:
            response = self.user.get(SHM_EXPORT_CSV_ENDPOINT.format(export_id=self.export_id))
            raise_for_status(response, message_prefix="Could not get SHM export details: ")
            if "progressPercentage" in response.json() and response.json()['progressPercentage'] == 100:
                log.logger.debug("\n Export Completed Successfully with {0} "
                                 "percentage \n".format(response.json()['progressPercentage']))
                return True
            else:
                raise EnmApplicationError("\n\n Export did not complete fully, PercentageCompleted: %s \n"
                                          % response.json()['progressPercentage'])
        else:
            raise JobValidationError("No export id set, unable to verify export csv created.", response=response)
