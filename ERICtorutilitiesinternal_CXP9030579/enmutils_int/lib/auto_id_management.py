# ********************************************************************
# Name    : Auto Identity Management
# Summary : Primary module for interacting with Auto Identity
#           Management. Provides functionality for generating various
#           types of AID loops (open/manual).
#           Allows use to create, delete, profiles, along with
#           calculating the inconsistencies in the network and resolve
#           those consistencies using PCI scores.
# ********************************************************************

import sys
import time
from datetime import datetime, timedelta
from urlparse import urljoin

from requests.exceptions import HTTPError

from enmutils.lib import log, headers
from enmutils.lib.exceptions import TimeOutError, EnmApplicationError
from enmutils_int.lib.netex import Collection

HEADERS = headers.JSON_SECURITY_REQUEST
DEFAULT_DATA = {"toGenerateAlarm": False,
                "checkS": True,
                "checkEnodebDetected": True,
                "checkN": True,
                "checkNN": True,
                "checkD": False,
                "checkSS": False,
                "checkTopologyGroupRange": False,
                "checkNonPlannedPci": False,
                "checkRS": True,
                "checkRSAggregated": True,
                "checkRSNonShifted": False,
                "checkRSShifted": True,
                "checkSM30": False,
                "checkSCellsBlacklistedPciValues": False,
                "checkNM30": False,
                "checkNCellsBlacklistedPciValues": False,
                "checkNNM30": False,
                "checkNNCellsBlacklistedPciValues": False,
                "checkDM30": False,
                "checkDCellsBlacklistedPciValues": False,
                "checkDMinCellDistanceInKilometers": True,
                "checkDMinCellDistance": 5000,
                "checkDDistanceCost": 10,
                "checkSSM30": False,
                "checkSSCellsBlacklistedPciValues": False,
                "checkSSSignalStrength": 70,
                "checkTemporaryValues": False,
                "checkReservedValues": False,
                "checkM30Cost": 5,
                "checkBlacklistCost": 20,
                "networkTechnology": "LTE",
                "applied": 0,
                "hardLock": False,
                "maxRetries": 2,
                "referenceShiftCost": 0,
                "changeMultipleCellsToFixConflicts": False,
                "maximumNumberOfCellsToChange": 2,
                "multipleCellsToFixValue": 2,
                "alarmGeneration": False,
                "checkMultipleCellsToFix": False}


class AutoIdProfile(object):
    BASE_ENDPOINT = '/autocellid-services/pci/setting/conflict/'
    STATUS_ENDPOINT = '/autocellid-services/pci/reports/status/{0}'
    _POLL_ENDPOINT = '/autocellid-services/pci/reports/{0}'
    _REPORT_ENDPOINT = '/autocellid-services/pci/reports/{0}?networkTechnology={1}'
    _SETTINGS_ENDPOINT = '/autocellid-services/pci/systemsettings/'
    _GET_SETTINGS_ENDPOINT = '/autocellid-services/pci/systemsettings/getsystemsetting'

    def __init__(self, user, name, nodes=None, collection=None, **kwargs):
        """
        AutoIdProfile Constructor
        :param user: User object to be used for CRUD operations
        :type user: enmutils.lib.enm_user.User
        :param name: name of the subscription
        :type name: str
        :param nodes: List of nodes to be used in the profile
        :type nodes: list
        :param collection: Object to be used in the profile
        :type collection: Enm Collection
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict
        :raises Exception: When collection creation fails
        """
        self.name = name
        self.user = user

        # Build default profile attributes. Update them if kwargs are passed in
        options = kwargs.pop("options", {})
        self.profile_attributes = {attribute: options.pop(attribute, value)
                                   for attribute, value in DEFAULT_DATA.iteritems()}

        self.description = kwargs.pop("description", name + "_TERE_WORKLOAD")
        self.scheduled_times = kwargs.pop("scheduled_times", [])
        self.validation_timeout = kwargs.pop("validation_timeout", 5400)
        self.validation_interval = kwargs.pop("validation_interval", 30)
        self.schedule_type = "IMMEDIATE"

        self.schedule_epoch_times = self._get_epoch_schedule() if self.scheduled_times else []
        self.collection = None

        if nodes and not collection:
            self.collection = Collection(user=self.user, name=self.name, nodes=nodes)
            self.node_poids = {node.node_id: node.poid for node in nodes if node.poid}
            try:
                if self.collection.exists:
                    self.collection.delete()
                self.collection.create()
                self.collection_id = self.collection.id
            except Exception as e:
                raise e
        elif collection:
            self.collection_id = collection.id
            self.node_poids = {node.node_id: node.poid for node in collection.nodes if node.poid}

        self.profile_id = None
        self.check_id = None
        self.calculate_id = None
        self.resolve_id = None
        self.exceptions = []

        self.check_total_records = 0

    @property
    def node_poid_list(self):
        """
        Get a poid list of the nodes attached to the auto id profile

        :return: list of poids in the AutoId profile
        :rtype: list
        """
        return [node_poid for node_poid in self.node_poids.values()]

    @classmethod
    def get_all(cls, user):
        """
        Returns all AutoId profiles in ENM
        :param user: user to use for the REST request
        :type user: `enmutils.lib.enm_user.User` object

        :return: all AutoId profiles
        :rtype: dict
        :raises HTTPError:
        """
        response = user.get(cls.BASE_ENDPOINT, headers=HEADERS)
        if not response.ok:
            raise HTTPError('Cannot fetch profiles from ENM.', response=response)

        log.logger.debug("Successfully fetched all profiles from ENM.")
        return response.json()

    @classmethod
    def get_by_name(cls, name, user):
        """
        Returns the AutoId Profile object with the given name
        :param name: name of the profile object to get
        :type name: str
        :param user: User to use for REST request
        :type user: enmutils.lib.enm_user.User

        :return: AutoId Profile
        :rtype: Json
       :raises ValueError: If AID profile doesn't exist
        """
        for item in cls.get_all(user)["data"]:
            if item["name"] == name:
                return item

        raise ValueError("AutoIdManagement profile {0} does not exist on ENM.".format(name))

    @classmethod
    def change_settings(cls, user, reserved, temporary, remove=False):
        """
        Returns the AutoId Profile object with the given name
        :param user: user to use for the REST request
        :type user: enmutils.lib.enm_user.User
        :param reserved: Add to reserved list settings
        :type reserved: dict
        :param temporary: Add to temporary settings
        :type temporary: dict
        :param remove: Set to true to remove passed on values from AID reserved and temporary list
        :type remove: bool

        :raises HTTPError:
        """
        response = user.get(cls._GET_SETTINGS_ENDPOINT, headers=HEADERS)
        if not response.ok:
            raise HTTPError('Cannot get current AutoId settings from ENM.', response=response)

        reserved_list = response.json()["SystemSettings"][0]["reservedList"]
        temporary_list = response.json()["SystemSettings"][0]["temporaryList"]
        res = {"physicalLayerCellIdGroup": reserved.keys()[0], "physicalLayerSubCellId": reserved.values()[0]}
        temp = {"physicalLayerCellIdGroup": temporary.keys()[0], "physicalLayerSubCellId": temporary.values()[0]}
        if remove:
            if res in reserved_list:
                reserved_list.remove(res)
            if temp in temporary_list:
                temporary_list.remove(temp)
        else:
            reserved_list.append(res)
            temporary_list.append(temp)

        response = user.put(cls._SETTINGS_ENDPOINT, json={"reservedList": reserved_list,
                                                          "temporaryList": temporary_list,
                                                          "name": "PCISystemSettings"}, headers=HEADERS)
        if not response.ok:
            raise HTTPError('Failed to set AutoId settings.', response=response)

        log.logger.debug("Successfully updated settings for AutoId.")

    def create(self):
        """
        Creates an AutoId Profile
        """
        data = {
            "name": self.name,
            "conflictSettingType": self.conflict_setting_type,
            "autoIdTopologyInfo": [
                {'topologyId': self.collection_id,
                 'listOfPoIds': self.node_poid_list,
                 'networkExplorerState': '/networkexplorercollections'}],
            "scheduledTimes": self.schedule_epoch_times,
            "schedulerDataView": self.get_scheduler() if getattr(self, "get_scheduler", False) else None,
            "description": self.description,
            "scheduleType": self.schedule_type,
            "profileState": self.profile_state
        }

        for attribute, value in self.profile_attributes.items():
            data[attribute] = value

        response = self.user.post(self.BASE_ENDPOINT, json=data, headers=HEADERS)

        if not response.ok:
            raise HTTPError(
                "Could not create Profile: '{0}', rc = '{1}', Output = '{2}'".format(
                    self.name, response.status_code, response.text), response=response)
        log.logger.debug("Successfully created AutoIdManagement profile {0}".format(self.name))

        self.profile_id = self._extract_id(response)

    def delete(self):
        """
        Deletes an AutoId Profile
        """
        if not self.profile_id:
            self.profile_id = self.get_by_name(self.name, self.user)["id"]

        response = self.user.delete_request(url=urljoin(self.BASE_ENDPOINT, self.profile_id))
        if not response.ok:
            response.raise_for_status()
        log.logger.debug("AutoIdManagement profile '{0}' was successfully deleted".format(self.name))

        if self.collection:
            self._delete_collection()
            self.collection = None

    def check(self):
        """
        Run Check an AutoId Profile
        """
        # Method name builds subsequent rest requests
        method_name = sys._getframe().f_code.co_name

        data = {"conflictSettingName": self.name, "moIds": self.node_poid_list,
                "networkTechnology": self.profile_attributes["networkTechnology"]}

        log.logger.debug("Check payload: {0}".format(data))

        response = self.user.post(self._POLL_ENDPOINT.format(method_name), json=data, headers=HEADERS)
        if not response.ok:
            response.raise_for_status()

        self.check_id = self._extract_id(response)

        self._validate(self.check_id, method_name)

        check_report_response = self._get_report(self.check_id, method_name)
        self.check_total_records = self._extract_total_records(check_report_response)
        log.logger.debug("There are {0} conflicts detected in the check".format(self.check_total_records))

    def calculate(self):
        """
        Run Calculate an AutoId Profile
        """
        # Method name builds subsequent rest requests
        method_name = sys._getframe().f_code.co_name

        if not self.check_id:
            raise RuntimeError("Please run check before running calculate")
        elif self.check_total_records == 0:
            log.logger.debug("There are no conflicts to calculate at this time")
            return

        # profileConflicts is only populated in the UI if we only want to calculate a portion of the conflicts found.
        # [] means all conflicts will be resolved.
        data = {"profileConflicts": [],
                "networkTechnology": self.profile_attributes["networkTechnology"],
                "checkConflictsTaskId": self.check_id, "checkConflictsTaskType": "CHECK"}

        log.logger.debug("Calculate payload: {0}".format(data))

        response = self.user.post(self._POLL_ENDPOINT.format(method_name), json=data, headers=HEADERS)
        if not response.ok:
            response.raise_for_status()

        self.calculate_id = self._extract_id(response)
        self._validate(self.calculate_id, method_name)

    def resolve(self):
        """
        Run Resolve an AutoId Profile
        """
        # Method name builds subsequent rest requests
        method_name = sys._getframe().f_code.co_name

        if self.check_total_records == 0 and self.check_id:
            log.logger.debug("There are no conflicts to resolve at this time")
            return
        elif not self.calculate_id:
            raise RuntimeError("Please run calculate before running resolve")

        data = {"maxRetries": self.profile_attributes["maxRetries"], "hardLockSelected": True,
                "networkTechnology": self.profile_attributes["networkTechnology"],
                "proposedMoInfo": [str({"fdn": calculation["fdn"], "existingPci": calculation["existingPci"],
                                        "proposedPci": calculation["proposedPci"]}).replace('u\'', '\"').replace('\'', '\"')
                                   for calculation in self._get_report(self.calculate_id, "calculate").json()["data"]
                                   if not calculation["assignmentFailed"]]}

        log.logger.debug("Resolve payload: {0}".format(data))

        response = self.user.post(self._POLL_ENDPOINT.format(method_name), json=data, headers=HEADERS)
        if not response.ok:
            response.raise_for_status()

        self.resolve_id = self._extract_id(response)

        self._validate(self.resolve_id, method_name, excepted_results=["SUCCESS", "PARTIAL"])

        resolve_result = self._get_report(self.resolve_id, "resolve")
        if resolve_result:
            log.logger.debug("Resolve response: {0}".format(resolve_result.json()))

    def _validate(self, query_id, endpoint, excepted_results=None):
        """
        Validate that check, calculate and resolve completed successfully
        :param query_id: id of the action to validate
        :type query_id: str
        :param endpoint: Endpoint to query for result
        :type endpoint: str
        :param excepted_results: List of passing results for the resoponse
        :type excepted_results: list

        :raises TimeOutError:
        :raises EnmApplicationError:
        :raises RuntimeError:
        """
        excepted_results = excepted_results or ["SUCCESS"]

        start_time = datetime.now()
        while datetime.now() < start_time + timedelta(seconds=self.validation_timeout):
            response = self.user.get(self.STATUS_ENDPOINT.format(query_id), headers=HEADERS)
            if not response.ok:
                response.raise_for_status()

            if response.json()["data"][0]["complete"]:
                break
            time.sleep(self.validation_interval)
        else:
            raise TimeOutError(
                "Request for AutoIdManagement profile {0} for {1} action did not complete within the specified"
                "timeout {2} seconds.".format(self.name, endpoint, self.validation_timeout))

        final_status = response.json()["data"][0]["status"]
        log.logger.debug("Result validation of {0}. Found {1} status. Response: {2}".format(endpoint, final_status, response.json()))

        if final_status in excepted_results:
            log.logger.debug("Found status {0} in validation of {1}".format(final_status, endpoint))
        elif final_status == 'PARTIAL':
            log.logger.debug("Found status {0} in validation of {1}".format(final_status, endpoint))
        elif final_status == 'FAILURE':
            log.logger.debug(
                "Error in validation of {0}. Found {1} status. Response: {2}".format(endpoint, final_status, response.json()))
            raise EnmApplicationError("Error in validation of {0}. Found {1} status.".format(endpoint, final_status))
        elif final_status == 'FAILURE_WITH_REASON':
            log.logger.debug(
                "Error in validation of {0}. Found {1} status. Response: {2}".format(endpoint, final_status,
                                                                                     response.json()))
            raise EnmApplicationError("Error in validation of {0}. Found {1} status".format(endpoint, final_status))
        else:
            raise RuntimeError("Error in validation of {0}. Found {1} status".format(endpoint, final_status))
        log.logger.info("Validation completed with result: {0}".format(final_status))

    def _get_report(self, query_id, endpoint):
        """
        Get the report based on the endpoint and id passed in
        :param query_id: id of the action to validate
        :type query_id: str
        :param endpoint: Endpoint to query for result
        :type endpoint: str

        :return: Response
        :rtype: json dict
        """
        path = "?offset=0&limit=50&networkTechnology=" if endpoint == "check" else "?networkTechnology="
        response = self.user.get(self._POLL_ENDPOINT.format(endpoint + "/" + query_id + path + self.profile_attributes["networkTechnology"]),
                                 headers=HEADERS)
        if not response.ok:
            response.raise_for_status()
        return response

    def _get_epoch_schedule(self):
        """
        Converts the datetime objects into epoch times

        :return: list of epock times to in the schedule
        :rtype: list
        """
        epoch_times = []
        for scheduled_time in self.scheduled_times:
            total_time = scheduled_time - datetime.utcfromtimestamp(0)
            epoch_times.append(int(((total_time.microseconds +
                                     (total_time.seconds + total_time.days * 24 * 3600) * 10 ** 6) / 10 ** 6) / 0.001))
        return epoch_times

    def _delete_collection(self):
        """
        Wrapper for delete collection
        """
        try:
            self.collection.delete()
        except Exception as e:
            log.logger.debug("Collection deletion problem in AutoIdManagement: {0}\n "
                             "Exception: {1}".format(self.name, str(e)))

    def _delete_check(self, check_id):
        """
        Deletes the check cache
        """
        response = self.user.delete_request(self._REPORT_ENDPOINT.format("check" + "/" + check_id,
                                                                         self.profile_attributes["networkTechnology"]),
                                            headers=HEADERS)
        if not response.ok:
            response.raise_for_status()

    def _delete_conflicts(self, check_id):
        """
        Deletes the calculate cache
        """
        log.logger.info("Profile attributes: {0}".format(self.profile_attributes))
        response = self.user.delete_request(self._REPORT_ENDPOINT.format("conflicts" + "/" + check_id,
                                                                         self.profile_attributes["networkTechnology"]),
                                            headers=HEADERS)
        if not response.ok:
            response.raise_for_status()
        log.logger.info("Conflicts deleted")

    def profile_clean(self):
        """
        Resetting stateful variables after a run has complete
        """
        self.exceptions = []
        if self.check_id:
            try:
                self._delete_check(self.check_id)
            except Exception as e:
                self.exceptions.append(e)
            try:
                self._delete_conflicts(self.check_id)
            except Exception as e:
                self.exceptions.append(e)
        self.check_id = None
        self.calculate_id = None
        self.resolve_id = None
        self.check_total_records = 0

    def teardown(self):
        self._teardown()

    def _teardown(self):
        try:
            self.delete()
        except Exception as e:
            log.logger.warn(str(e))

        if self.collection:
            self._delete_collection()

    @staticmethod
    def _extract_id(response):
        """
        Get the id from the response object passed in
        :param response: Response object from which to extract the id
        :type response: Response object

        :return: data_id from the json response
        :rtype: str
        """
        return response.json()["data"][0]["id"]

    @staticmethod
    def _extract_total_records(response):
        """
        Get the totalRecords from the response object passed in
        :param response: Response object from which to extract the totalRecords
        :type response: Response object

        :return: totalRecords from the json response
        :rtype: str
        """
        return response.json()["totalRecords"]


class ManualAutoIdProfile(AutoIdProfile):
    def __init__(self, *args, **kwargs):
        """
        Manual AutoId Profile constructor
        """
        self.conflict_setting_type = "INACTIVE"
        self.profile_state = "NA"
        super(ManualAutoIdProfile, self).__init__(*args, **kwargs)


class OpenLoopAutoIdProfile(AutoIdProfile):
    def __init__(self, *args, **kwargs):
        """
        Closed Loop AutoId Profile constructor
        """
        self.conflict_setting_type = "OPEN_LOOP"
        self.profile_state = "ACTIVE"
        super(OpenLoopAutoIdProfile, self).__init__(*args, **kwargs)

    def get_scheduler(self):
        """
        Returns the scheduler json payload

        :return: scheduler dictionary fields
        :rtype: dict
        """
        return {"networkConflictSettingType": "LTE_{0}".format(self.conflict_setting_type),
                "conflictSettingType": self.conflict_setting_type,
                "networkTechnology": self.profile_attributes["networkTechnology"],
                "toGenerateAlarm": self.profile_attributes["toGenerateAlarm"],
                "profileName": self.name,
                "topologyMoIds": self.node_poid_list}


class ClosedLoopAutoIdProfile(AutoIdProfile):
    def __init__(self, *args, **kwargs):
        """
        Open Loop AutoId Profile constructor
        """
        self.conflict_setting_type = "CLOSED_LOOP"
        self.profile_state = "ACTIVE"
        super(ClosedLoopAutoIdProfile, self).__init__(*args, **kwargs)

    def get_scheduler(self):
        """
        Returns the scheduler json payload

        :return: scheduler
        :rtype: dict
        """
        data = None
        if self.schedule_epoch_times:
            data = {"networkConflictSettingType": "LTE_{0}".format(self.conflict_setting_type),
                    "conflictSettingType": self.conflict_setting_type,
                    "networkTechnology": self.profile_attributes["networkTechnology"],
                    "toGenerateAlarm": self.profile_attributes["toGenerateAlarm"], "profileName": self.name,
                    "hardLock": self.profile_attributes["hardLock"],
                    "maxRetries": self.profile_attributes["maxRetries"],
                    "scheduleType": self.schedule_type, "scheduleTimes": self.schedule_epoch_times,
                    "topologyMoIds": self.node_poid_list}
            if len(self.schedule_epoch_times) > 1:
                self.schedule_type = "RANGE"
                data["scheduleType"] = self.schedule_type

        return data


class TopologyGroupRange(object):
    CREATE = "/autocellid-services/pci/topologygrouprangesettings/"
    DELETE = "/autocellid-services/pci/topologygrouprangesettings/{0}"

    def __init__(self, user, name, first_pci_value_range=None, last_pci_value_range=None, nodes=None, collection=None):
        """
        Topology Group Range constructor
        """
        self.name = name
        self.first_pci_value_range = first_pci_value_range if first_pci_value_range else {0: 0}
        self.last_pci_value_range = last_pci_value_range if last_pci_value_range else {167: 2}

        self.user = user
        self.range_id = None
        self.collection = None if not collection else collection

        if nodes and not collection:
            self.collection = Collection(user=self.user, name=self.name, nodes=nodes)
            self.node_poids = {node.node_id: node.poid for node in nodes if node.poid}
            try:
                self.collection.create()
                self.collection_id = self.collection.id
            except Exception as e:
                raise e
        else:
            self.collection_id = collection.id
            self.node_poids = {node.node_id: node.poid for node in collection.nodes if node.poid}

    def create(self):
        """
        Creates Topology Group Range
        """
        data = {"topologyGroupRangeName": self.name,
                "listOfPciValues": [],
                "listOfPciRanges": [{"firstPciValueInRange": {"physicalLayerCellIdGroup": str(self.first_pci_value_range.keys()[0]),
                                                              "physicalLayerSubCellId": str(self.first_pci_value_range.values()[0])},
                                     "lastPciValueInRange":
                                         {"physicalLayerCellIdGroup": str(self.last_pci_value_range.keys()[0]),
                                          "physicalLayerSubCellId": str(self.last_pci_value_range.values()[0])}}],
                "autoIdTopologyInfo": [
                    {"topologyId": self.collection_id,
                     "listOfPoIds": [node_poid for node_poid in self.node_poids.values()],
                     "networkExplorerState": "/networkexplorer/"}]}

        response = self.user.post(self.CREATE, json=data, headers=HEADERS)
        if not response.ok:
            response.raise_for_status()

        self.range_id = response.json()["data"][0]["id"]

    def delete(self):
        """
        Deletes Topology Group Range
        """
        if self.range_id:
            response = self.user.delete_request(self.DELETE.format(self.range_id), headers=HEADERS)
            if not response.ok:
                response.raise_for_status()
            self.range_id = None
            if self.collection:
                self._delete_collection()
        else:
            log.logger.debug("No range id to create delete request with for Topology Group Range")

    def _delete_collection(self):
        """
        Wrapper for delete collection
        """
        try:
            self.collection.delete()
        except Exception as e:
            log.logger.debug("Collection deletion problem in Topology Group Range: {0}\n "
                             "Exception: {1}".format(self.name, str(e)))

    def _teardown(self):
        try:
            self.delete()
        except Exception as e:
            log.logger.warn(str(e))
        if self.collection:
            self._delete_collection()


class NonPlannedPCIRange(object):
    CREATE = "/autocellid-services/pci/system-settings/non-planned-pci-ranges"
    DELETE = "/autocellid-services/pci/system-settings/non-planned-pci-ranges/{0}"

    def __init__(self, user, frequency, pci_ranges):
        """
        Non-Planned PCI Range constructor
        """
        self.frequency = frequency
        self.pci_ranges = pci_ranges

        self.user = user
        self.range_id = None

    def create(self):
        """
        Creates Non-Planned PCI Range
        """
        data = {"id": None, "frequency": self.frequency,
                "pciRange": {"firstPciValueInRange": {"physicalLayerCellIdGroup": str(self.pci_ranges.keys()[0]),
                                                      "physicalLayerSubCellId": str(self.pci_ranges.values()[0])},
                             "lastPciValueInRange": None}, "networkTechnology": "LTE"}

        response = self.user.post(self.CREATE, json=data, headers=HEADERS)
        if not response.ok:
            response.raise_for_status()

        self.range_id = response.json()

    def delete(self):
        """
        Deletes Non-Planned PCI Range
        """
        if self.range_id:
            response = self.user.delete_request(self.DELETE.format(self.range_id), headers=HEADERS)
            if not response.ok:
                response.raise_for_status()
            self.range_id = None
        else:
            log.logger.debug("No range id to create delete request with for Non-Planned PCI Range")

    def _teardown(self):
        self.delete()


class AutoIdTearDownProfile(AutoIdProfile):

    def __init__(self, user, name, profile_id, collection_id):
        super(AutoIdTearDownProfile, self).__init__(user, name)
        self.profile_id = profile_id
        self.collection = Collection(user=self.user, name=self.name, nodes=[])
        self.collection.id = collection_id
