# ********************************************************************
# Name    : SHM JOB
# Summary : Primarily used by SHM profiles. Allows the user to manage
#           multiple operations within the SHM application area,
#           including but not limited all CRUD operations in relation
#           to Backup, Upgrade, Licence Key, Software Packages,
#           Restore, Deletion of generated content such as CVs and
#           Upgrade Package, and Exports.
# ********************************************************************

import abc
import datetime
import json
from time import sleep

from requests.exceptions import HTTPError
from retrying import retry

from enmutils.lib import log
from enmutils.lib.exceptions import (EnmApplicationError, JobExecutionError,
                                     JobValidationError, TimeOutError)
from enmutils.lib.headers import SHM_LONG_HEADER
from enmutils_int.lib.shm_data import (PLATFORM_TYPES, SHM_JOB_CREATE_ENDPOINT,
                                       SHM_JOB_DELETE_ENDPOINT,
                                       SHM_JOB_DETAILS,
                                       SHM_JOBS_CANCEL_ENDPOINT,
                                       SHM_JOBS_LIST_ENDPOINT)


def retry_if_job_validation_error(exception):
    """Return True if we should retry (in this case when it's an JobValidationError), False otherwise"""
    return isinstance(exception, JobValidationError)


class JobCreationError(Exception):
    pass


class ShmJob(object):

    def __init__(self, user, nodes, **kwargs):
        """
        Super class constructor for SHM jobs

        :type nodes: list
        :param nodes: List of Node objects
        :type user: `enm_user_2.User`
        :param user: user to use for the REST request
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary

        """
        self.user = user
        self.nodes = nodes
        self.schedule_time = self.fetch_schedule_time(kwargs.get('schedule_time'))
        self.exec_mode = "SCHEDULED" if self.schedule_time else "IMMEDIATE"
        self.job_type = kwargs.get('job_type')
        self.ne_type = self.nodes[0].primary_type.replace("_", "") if self.nodes else "ERBS"
        random_suffix = kwargs.get('random_suffix', datetime.datetime.now().strftime('%m%d%H%M%S'))
        self.profile_name = kwargs.get('profile_name', 'SHM')
        self.name = kwargs.get('name', '{0}_{1}_{2}_{3}'.format(self.profile_name, self.job_type,
                                                                self.ne_type, random_suffix))
        self.description = kwargs.get('description', '{0}_{1}_{2}_{3}'.format(self.profile_name, self.job_type,
                                                                              self.exec_mode, random_suffix))
        self.nodes[0].primary_type = 'SGSN-MME' if self.ne_type == 'SGSN' else self.ne_type
        self.platform = kwargs.get('platform', PLATFORM_TYPES[self.nodes[0].primary_type])
        self.repeat_count = kwargs.get('repeat_count', '1')
        self.collection_names = kwargs.get('collection_names', [])
        self.save_search_ids = kwargs.get('save_search_ids', [])
        self.job_id = None
        self.repeat_frequency = kwargs.pop('repeat_frequency', "Daily")  # Valid: Daily/Weekly/Monthly/Yearly
        self.occurrences = kwargs.pop('occurrences', "0")
        self.repeat_on_day = kwargs.pop('repeat_on', "1")  # Day of the week 1 = Monday
        self.file_name = kwargs.get('file_name', random_suffix)
        self.reboot_node = kwargs.pop('reboot_node', 'true')
        self.install_verify_only = kwargs.pop('install_verify_only', False)
        self.use_default_config = True
        self.set_as_startable = kwargs.get('set_as_startable')
        self.node_types = self.nodes_dictionary()
        self.package_list = kwargs.get('upgrade_list')
        self.delete_from_rollback_list = kwargs.get('delete_from_rollback_list')
        self.delete_referred_ups = kwargs.get('delete_referred_ups')
        self.upgrade_commit_only = kwargs.get("upgrade_commit_only")
        self.software_package = kwargs.get('software_package')
        self.backup_start_time = kwargs.get('backup_start_time')
        self.cv_names = {}
        self.nodes_with_component_backups = []
        if self.software_package:
            self.package_name = self.software_package.new_package
            self.zip_file_name = "{0}{1}".format(self.software_package.new_package, ".zip")
        self.payload = {}
        self.schedule_time_strings = kwargs.get('schedule_time_strings', [])
        self.shm_schedule_time_strings = kwargs.get('shm_schedule_time_strings', [])
        log.logger.debug('{0} Jobs running in the following Node Type {1}'.format(self.name, self.node_types))

    def fetch_schedule_time(self, schedule_time):
        """
        Fetch the scheduled time from the arguments provided and convert to datetime object.
        :type schedule_time: void
        :param schedule_time: schedule_time provided in kwargs
        :rtype: datetime.datetime
        :return: schedule time value in datetime.datetime format
        """
        if schedule_time:
            if isinstance(schedule_time, datetime.datetime):
                return schedule_time.strftime('%Y-%m-%d %H:%M:%S GMT+0000')
            else:
                current_time = datetime.datetime.now()
                st = datetime.datetime.strptime(schedule_time, "%H:%M:%S")
                job_schedule_time = current_time.replace(hour=st.hour, minute=st.minute, second=st.second)
                return job_schedule_time.strftime('%Y-%m-%d %H:%M:%S GMT+0000')
        else:
            return ""

    def nodes_dictionary(self):
        node_types = []
        for node in self.nodes:
            if node.primary_type not in node_types:
                node_types.append(node.primary_type)
        return node_types

    def set_schedule(self):
        """
        Schedule method

        :rtype void
        """
        if (self.job_type in ["DELETEBACKUP", "RESTORE", "DELETE_UPGRADEPACKAGE"] or
                (not self.schedule_time and self.job_type == "UPGRADE")):
            return []
        if not self.repeat_count == "1" or self.job_type == "UPGRADE":
            return [
                {"name": "START_DATE", "value": self.schedule_time}
            ]
        schedule = [
            {"name": "REPEAT_TYPE", "value": self.repeat_frequency},
            {"name": "REPEAT_COUNT", "value": self.repeat_count},
            {"name": "START_DATE", "value": self.schedule_time},
            {"name": "OCCURRENCES", "value": self.occurrences}
        ]
        if self.repeat_frequency == "Weekly":
            schedule.append({"name": "REPEAT_ON", "value": self.repeat_on_day})
        return schedule

    @abc.abstractmethod
    def set_properties(self):
        """
        Abstract Properties method
        """

    @abc.abstractmethod
    def set_activities(self):
        """
        Abstract Activities method
        """

    def update_configuration(self):
        """
        Updates the configuration dictionary values for the create functionality
        """
        if self.ne_type == "BSC" and self.job_type in ["UPGRADE", "BACKUP_HOUSEKEEPING"]:
            if self.job_type == "UPGRADE":
                self.payload.update({"configurations": [{"neType": self.ne_type, "properties": self.set_properties(),
                                                         "neProperties": self.set_neProperties(),
                                                         "neTypeActivityJobProperties": self.setActivityJobProperies()}]})
            if self.job_type == "BACKUP_HOUSEKEEPING":
                self.payload.update({"configurations": [{"neType": self.ne_type, "properties": self.set_properties()}]})
            self.payload["savedSearchIds"] = self.save_search_ids
            self.payload["collectionNames"] = self.collection_names
            self.payload["parentNeWithComponents"] = []
        else:
            self.payload.update({"configurations": [{"neType": self.ne_type, "properties": self.set_properties()}]})

    def update_activities_schedule(self):
        """
        Updates the activity schedule dictionary values for the create functionality
        """
        self.payload.update({"activitySchedules": [{"platformType": self.platform,
                                                    "value": [{"neType": self.ne_type,
                                                               "value": self.set_activities()}]}]})

    def set_ne_names(self):
        """
        Method for building up the ne name dictionaries based on primary_type

        :rtype: list
        :return: List of containing dictionary(ies), of name -> node_id, key -> values
        """
        ne_name_list = []
        for node_type in self.node_types:
            ne_name_list.extend([{'name': node.node_id} for node in self.nodes if node.primary_type == node_type])
        if not self.job_type == 'UPGRADE':
            return [{"name": node.node_id} for node in self.nodes]
        else:
            return ne_name_list

    def exists(self):
        """
        Check if job exists on ENM

        :rtype list
        """

        return self._get_jobs_results(self.get_shm_jobs(self.user), jobName=self.name)

    @staticmethod
    def convert_schedule_time_in_secs(scheduled_time):
        """
        Converts each index of passed scheduled time in seconds

        :type scheduled_time: list
        :param scheduled_time: scheduled time strings in list
        :rtype: list
        :return: each schedule time value in seconds
        """
        log.logger.debug("Converts scheduled time {0} in seconds".format(scheduled_time))
        scheduled_format_time = [60 * 60, 60, 1]
        try:
            for index_pos, each_time_string in enumerate(scheduled_time):
                if isinstance(each_time_string, datetime.datetime):
                    each_time_string = each_time_string.strftime("%H:%M:%S")
                if isinstance(each_time_string, str):
                    scheduled_time[index_pos] = each_time_string.split(":")
                    scheduled_time[index_pos] = sum([int(scheduled_time[index_pos][each_index]) *
                                                     scheduled_format_time[each_index] for each_index in range(3)])
        except Exception as e:
            log.logger.debug("{0} format is Invalid, cannot convert into seconds: {1}".format(scheduled_time, str(e)))
        log.logger.debug("scheduled time value after converting into seconds is {0}".format(scheduled_time))
        return scheduled_time

    def fetch_job_status(self):
        """
        This function is required to avoid the parallel execution of jobs.
        previously if the Job is scheduled then immediately delete activities are processed,
        so this function helps if the job activity is scheduled then it waits for certain amount of time and then
        checks the job status again.
        Upgrade Execution Order(Upgrade, DeleteInactive, DeleteUpgrade)
        Backup Execution Order(Backup, cleanup, housekeeping)
        """
        current_job_status = self._wait_job_to_complete()
        attribute_check_scheduled_time = all(
            hasattr(self, schedule_time) for schedule_time in ["schedule_time_strings", "shm_schedule_time_strings"])
        if current_job_status and current_job_status == "SCHEDULED" and attribute_check_scheduled_time:
            scheduled_times_in_secs = self.convert_schedule_time_in_secs(self.schedule_time_strings)
            shm_job_scheduled_time_in_secs = self.convert_schedule_time_in_secs(self.shm_schedule_time_strings)
            schedule_time_diff = (max(shm_job_scheduled_time_in_secs) - min(scheduled_times_in_secs) if
                                  (shm_job_scheduled_time_in_secs and scheduled_times_in_secs) else 0)
            log.logger.debug("Current Job was scheduled and it will be checked after {0} seconds".format(
                schedule_time_diff))
            sleep(schedule_time_diff)
            self._wait_job_to_complete()

    def update_config_and_schedules_in_payload(self):
        """
        Updates configurations and activitySchedules in payload based on platform type
        """
        if self.platform in ["CPP", "MINI_LINK_INDOOR"]:
            del self.payload["configurations"]
            self.payload["configurations"] = self.set_configurations()
            if self.job_type in ['BACKUP']:
                del self.payload["activitySchedules"]
                self.payload["activitySchedules"] = self.set_multiple_activities()
        if self.platform == "ECIM" and self.job_type in ['DELETE_UPGRADEPACKAGE']:
            del self.payload["configurations"]
            self.payload["configurations"] = self.set_configurations()
            del self.payload["activitySchedules"]
            self.payload["activitySchedules"] = self.set_multiple_activities()

    def update_bsc_backup_deletebackup_housekeeping_in_payload(self):
        """
        Updates configurations, neTypeComponentActivityDetails, parentNeWithComponents,
        neNames and configurations in payload based on job type for BSC Nodes
        """
        if self.job_type in ['BACKUP']:
            self.payload["neTypeComponentActivityDetails"] = self.update_neTypeComponentActivityDetails()
            self.payload["configurations"] = self.set_configurations()
        if self.job_type in ['BACKUP', 'DELETEBACKUP']:
            self.payload["parentNeWithComponents"] = self.update_parent_ne_withcomponents()
            self.payload["neNames"] = self.set_ne_names()
        if self.job_type in ['BACKUP_HOUSEKEEPING']:
            self.payload["parentNeWithComponents"] = self.update_parent_ne_withcomponents()

    def generate_payload(self):
        """
        Generates payload to create SHM Job.
        """
        self.payload = {
            "name": self.name,
            "description": self.description,
            "jobType": self.job_type,
            "neNames": self.set_ne_names(),
            "mainSchedule": {
                "scheduleAttributes": self.set_schedule(),
                "execMode": self.exec_mode
            },
        }
        self.update_configuration()
        self.update_activities_schedule()
        if not isinstance(self, MultiUpgrade):
            if self.ne_type in ['BSC']:
                self.update_bsc_backup_deletebackup_housekeeping_in_payload()
            if self.job_type in ['BACKUP', 'DELETE_UPGRADEPACKAGE'] and self.use_default_config is True:
                self.payload["savedSearchIds"] = self.save_search_ids
                self.payload["collectionNames"] = self.collection_names
                self.update_config_and_schedules_in_payload()
            elif self.job_type in ['DELETEBACKUP', 'RESTORE'] or self.use_default_config is False:
                del self.payload["configurations"]
                self.payload["configurations"] = self.set_properties()
                if self.job_type in ['DELETEBACKUP']:
                    del self.payload["activitySchedules"]
                    self.payload["activitySchedules"] = self.set_multiple_activities()
        log.logger.debug("Current Payload Data is : {0}".format(self.payload))

    def sleep_till_job_creation_time(self, job_creation_time, profile_object=None):
        """
        Calculates job creation time according to config values and sleeps till job creation time
        :type job_creation_time: str
        :param job_creation_time: Job creation time
        :param profile_object: profile object SHM_41
        :type profile_object: object
        """
        # Calculate and wait till job specified time in config file to create job request
        current_time = datetime.datetime.now()
        if not isinstance(job_creation_time, datetime.datetime):
            dt = datetime.datetime.strptime(job_creation_time, "%H:%M:%S")
            job_creation_time = current_time.replace(hour=dt.hour, minute=dt.minute, second=dt.second)

        log.logger.debug("Job creation time:{0}".format(job_creation_time))
        job_wait_time = (job_creation_time - current_time).total_seconds()
        if job_wait_time > 0:
            log.logger.debug("Sleeping for {0} seconds and thereafter job will be created as per the scheduled time "
                             "in config file".format(job_wait_time))
            if profile_object:
                profile_object.state = "SLEEPING"
            sleep(job_wait_time)
            if profile_object:
                profile_object.state = "RUNNING"

    def create(self, profile_object=None):
        """
        Creates an SHM job based on job schedule strings
        :param profile_object: profile object SHM_41
        :type profile_object: object
        :raises RuntimeError: when unable to create shm job
        """

        if self.job_type is None:
            log.logger.debug("Cannot create SHM Job with this {0} Job Type".format(self.job_type))
            raise RuntimeError('Cannot create SHM Job with Job Type: {0}'.format(self.job_type))

        if self.shm_schedule_time_strings == []:
            current_time = datetime.datetime.now()
            time = current_time.strftime("%H:%M:%S")
            self.create_job(time)
        else:
            self.if_schedule_time_strings_defined(profile_object)

    def if_schedule_time_strings_defined(self, profile_object=None):
        for time in self.shm_schedule_time_strings:
            log.logger.debug("JOB schedule time strings: {0}".format(time))
            self.name = 'name_{0}_{1}_{2}_{3}'.format(self.profile_name, self.job_type, self.ne_type,
                                                      datetime.datetime.now().strftime('%m%d%H%M%S'))
            if len(self.shm_schedule_time_strings) > 1:
                ct = datetime.datetime.now()
                jt = time
                if isinstance(time, str):
                    dt = datetime.datetime.strptime(time, "%H:%M:%S")
                    jt = ct.replace(hour=dt.hour, minute=dt.minute, second=dt.second)
                    log.logger.debug("Job creation time after changing to datetime :{0}".format(jt))
                if ct > jt:
                    log.logger.debug("Scheduled time has been passed for the day")
                    continue
                log.logger.debug("JOB creation time: {0}".format(time))
            self.create_job(time, profile_object)

    def create_job(self, time, profile_object=None):
        """
        Creates a SHM job
        :type time: str
        :param time: Job creation time
        :param profile_object: profile object SHM_41
        :type profile_object: object
        :raises HTTPError: when job response is not ok
        :raises JobCreationError: when job is not created correctly with unexpected status_code
        """
        self.generate_payload()
        self.sleep_till_job_creation_time(time, profile_object)
        # Create job request using payload to execute job activities
        response = self.user.post(SHM_JOB_CREATE_ENDPOINT, headers=SHM_LONG_HEADER, data=json.dumps(self.payload))
        if not (response.status_code in [200, 201] and response.ok):
            if response.status_code == 403:
                res = response.json() if response.json() else response.text
                raise JobCreationError("Failed to create job correctly, response: {}".format(res))
            else:
                raise HTTPError('Failed to create shm {0} job correctly. Check logs for details. Response was "{1}"'
                                .format(self.job_type, response.text), response=response)
        log.logger.debug('SHM job status: {0} status code: {1}'.format(response.text, response.status_code))
        log.logger.debug('Sleeping for 3 seconds after job creation.')
        sleep(3)
        self._set_job_id()
        self.fetch_job_status()

    @classmethod
    @retry(retry_on_exception=retry_if_job_validation_error, wait_fixed=60000, stop_max_attempt_number=3)
    def get_shm_jobs(cls, user, offset=1, limit=50, payload=None):
        """
        Get the list of jobs. Filters on name and status fields
        :type user: `enm_user_2.User`
        :param user: user to use for the REST request (EnmUser)
        :param offset:  Offset for SHM jobs list.
        :type offset:   int
        :param limit:   Limit for Number of SHM Jobs list.
        :type limit:    int
        :param payload: Payload to be sent as part of the POST request
        :type payload: dict
        :raises JobValidationError: when the attempt to get list of shm jobs fails
        :rtype: list
        :return: list of jobs
        """
        log.logger.debug("Fetching the list of shm jobs.")
        if not payload:
            payload = json.dumps(
                {"columns": [], "offset": offset, "limit": limit, "sortBy": "startTime", "orderBy": "desc"})
        response = user.post(SHM_JOBS_LIST_ENDPOINT, data=payload, headers=SHM_LONG_HEADER)
        if response.ok and int(response.json()["totalCount"]) != 0:
            log.logger.debug("Successfully fetched list of jobs.")
            return response
        else:
            log.logger.debug("POST request to {0} was failed, status code is {1} and response text is {2}"
                             .format(SHM_JOBS_LIST_ENDPOINT, response.status_code, response.text))
            log.logger.debug('Sleeping 60 seconds before re-trying.')
            raise JobValidationError("Max retries reached for post request {0}".format(SHM_JOBS_LIST_ENDPOINT),
                                     response=response)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=60000, stop_max_attempt_number=3)
    def delete(self):
        """
        Deletes a job in ENM
        :raises RuntimeError: when job id is not available to proceed for job deletion
        :raises HTTPError:  when job deletion fails with not success status
        """

        if not self.job_id:
            raise RuntimeError('No job id available for job "%s". Unable to delete.' % self.name)

        response = self.user.post(SHM_JOB_DELETE_ENDPOINT, headers=SHM_LONG_HEADER, data=json.dumps([self.job_id]))

        if not response.ok or not response.json()['status'] == 'success':
            raise HTTPError(
                'Could not delete the shm job with name %s. Rc is %d, output is %s' % (
                    self.name, response.status_code, response.text), response=response)

        log.logger.debug('Successfully deleted the shm job(s) with name %s' % self.name)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=60000, stop_max_attempt_number=3)
    def cancel(self, verify_cancelled=True):
        """
        Cancels a job in ENM
        :type verify_cancelled: bool
        :param verify_cancelled: verify job cancellation (boolean)
        :raises RuntimeError: when job id is not available to proceed for job cancellation
        :raises HTTPError:  when job cancellation fails with not success status
        """
        if not self.job_id:
            raise RuntimeError('No job id available for job "%s". Unable to cancel' % self.name)

        response = self.user.post(SHM_JOBS_CANCEL_ENDPOINT, headers=SHM_LONG_HEADER, data=json.dumps([self.job_id]))

        if response.ok:
            if verify_cancelled:
                self._verify_cancel()
        else:
            raise HTTPError(
                'Failed to cancel shm {0} job with ID {1}'.format(self.job_type, self.job_id), response=response)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=10000, stop_max_attempt_number=6)
    def _verify_cancel(self):
        response = self.get_shm_jobs(self.user)
        cancelled = self._get_jobs_results(response, jobId=self.job_id, status="CANCELLED")
        completed = self._get_jobs_results(response, jobId=self.job_id, status="COMPLETED")

        if cancelled:
            log.logger.debug('Successfully cancelled job with name: %s and id: %s' % (self.name, self.job_id))
        elif completed:
            log.logger.debug('Job with name: %s and id: %s has already completed. Unable to cancel.' %
                             (self.name, self.job_id))
        else:
            log.logger.debug('Job is not in cancelled or completed state. Sleeping 10 seconds before re-trying.')
            raise HTTPError('Could not verify that the job %s was cancelled. Max retries reached.' % self.name,
                            response=response)

    def validate(self):
        """
        Validate job success in ENM
        :raises JobExecutionError: when attempt to retrieve job results fails
        """
        response = self.get_shm_jobs(self.user)
        success = self._get_jobs_results(response, jobId=self.job_id, result="SUCCESS")

        if not success:
            raise JobExecutionError("Job {0} did not complete successfully, status: {1}."
                                    .format(self.name, response.json()['result'][0]['status']), response=response)
        log.logger.debug("Job {0} completed successfully.".format(self.name))

    @retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_fixed=60000,
           stop_max_attempt_number=10)
    def _set_job_id(self):
        """
        Sets the job id based on the name and status from the list of jobs, job id needed to validate against
        """
        response = self.get_shm_jobs(self.user)
        filter_job_result = self._get_jobs_results(response, jobName=self.name)
        log.logger.debug("List of SHM Jobs are: {0}".format(filter_job_result))
        if filter_job_result:
            self.job_id = filter_job_result[0]['jobId']
            log.logger.debug("Job Id chosen is: {0}".format(self.job_id))
        else:
            log.logger.debug("Re-trying retrieval 60s up to a max of 10 retries.")
            raise EnmApplicationError('Could not get the job ID for job {0}'.format(self.name))

    @staticmethod
    def _get_jobs_results(response, **kwargs):
        results = response.json()['result']
        matching_results = []
        if kwargs:
            for result in results:
                if all(True if str(result[key]) == str(value) else False for key, value in kwargs.iteritems()):
                    matching_results.append(result)
        return matching_results

    def _wait_job_to_complete(self):
        """
        Waits and checks for the job to be either "COMPLETED" or "SCHEDULED"
        :raises TimeOutError: when jon state cannot be verified within given time
        :raises EnmApplicationError: when job status not in RUNNING/CREATED state

        :rtype: str
        :return: SHM Job Status (COMPLETED or SCHEDULED)
        """
        log.logger.debug("Determining the current Status of the SHM Job")
        if self.job_type in ["UPGRADE", "DELETE_UPGRADEPACKAGE"] or self.nodes[0].primary_type == "BSC":
            job_time = 135
        elif self.nodes[0].primary_type in ["MLTN", "MINI-LINK-6352", "MINI-LINK-Indoor"]:
            job_time = 90
        elif self.nodes[0].primary_type == "MINI-LINK-669x":
            job_time = 180
        elif self.name == "SHM_35" and any(
                [True if _ in self.job_type else False for _ in ["Cleanup", "DELETEBACKUP", "BACKUP_HOUSEKEEPING"]]):
            delete_backup_per_node_time_minutes = {"ERBS": 1, "RadioNode": 1, "Router6672": 10,
                                                   "Router6675": 10, "BSC": 10}
            job_time_all_nodes = len(self.nodes) * delete_backup_per_node_time_minutes[self.nodes[0].primary_type]
            job_time = (job_time_all_nodes if hasattr(delete_backup_per_node_time_minutes, self.nodes[0].primary_type)
                        else 1)
        else:
            job_time = 45
        log.logger.debug("Maximum time considered for performing SHM Job activity is {0} minutes".format(job_time))
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=job_time)
        while datetime.datetime.now() < expiry_time:
            shm_job = self._get_job_response()
            if shm_job["status"] in ["COMPLETED", "SCHEDULED"]:
                log.logger.debug('Status of the SHM Job "{0}" is "{1}"'.format(self.name, shm_job["status"]))
                return shm_job["status"]
            elif shm_job["status"] not in ["RUNNING", "CREATED"]:
                raise EnmApplicationError("SHM Job changed to unexpected status. HTTPResponse was {0}"
                                          .format(str(shm_job)))
            log.logger.debug("Sleeping for {0} seconds before re-trying..".format(30))
            sleep(30)
        raise TimeOutError('Cannot verify the state "{0}" for job "{1}"'.format(shm_job["status"], self.name))

    def _teardown(self):
        """
        Teardown method to be used with workload profile teardown
        """
        try:
            self.cancel()
        except Exception as e:
            log.logger.debug(str(e))
        self.delete()

    def wait_time_for_job_to_complete(self, max_iterations=24, time_to_sleep=600):
        """
        Wait and see if the job validation is successful

        :type max_iterations: int
        :param max_iterations: number of iteration to wait
        :type time_to_sleep: int
        :param time_to_sleep: number of seconds to wait in each individual iteration
        :raises EnmApplicationError: when job_id is not present
        """

        def _validate_response(response):
            if not response:
                raise EnmApplicationError("It could not validate the response of the SHM job")

        iteration = 0
        if not self.job_id:
            raise EnmApplicationError('Cannot determine job id: {0}, exiting wait operation.'.format(self.job_id))
        try:
            shm_job = self._get_job_response()
        except Exception as e:
            raise EnmApplicationError(e.message)
        _validate_response(shm_job)
        while shm_job["status"] not in ["COMPLETED"] and iteration < max_iterations:
            log.logger.debug("SHM Backup Job Status is: {0}, Sleeping for {1} seconds until job execution completed."
                             .format(shm_job['status'], time_to_sleep))
            sleep(time_to_sleep)
            iteration += 1
            try:
                shm_job = self._get_job_response()
            except Exception as e:
                raise EnmApplicationError(e.message)
            _validate_response(shm_job)
        log.logger.debug("SHM Backup Job has completed, no completion to wait upon.")

    @retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_fixed=60000, stop_max_attempt_number=3)
    def get_skipped_count(self):
        """
        Returns the total number of SKIPPED nodes in an SHM Job
        :rtype: int
        :return: skipped nodes count
        :raises EnmApplicationError: when failed to fetch required attributes from json response
        """
        try:
            response = self.user.get(SHM_JOB_DETAILS.format(job_id=self.job_id))
            return len([node.get('neResult') for node in response.json().get('neDetails').get('result') if
                        node.get('neResult') == 'SKIPPED'])
        except ValueError:
            self._set_job_id()
        except Exception as e:
            raise EnmApplicationError(e.message)

    def construct_capacity_expansion_license_job_payload(self, limit):
        """
        Constructs capacity expansion license job payload used to fetch LKF Jobs from SHM UI
        """
        log.logger.debug("Constructing payload for fetching LKF Jobs from SHM UI")
        payload = json.dumps({"columns": [], "offset": 1, "limit": limit, "sortBy": "startTime", "orderBy": "desc",
                              "filterDetails": [{"columnName": "jobType", "filterOperator": "*",
                                                 "filterText": "LICENSE_REQUEST"},
                                                {"columnName": "startTime", "filterOperator": ">",
                                                 "filterText": self.current_time}]})
        return payload

    def _get_job_response(self):
        """
        Attempt to retrieve the job results, from the list of available jobs

        :return: response object
        :rtype: `requests.Response`
        :raises EnmApplicationError: when KeyError occurs
        :raises IndexError: when the shm job is not in the list of 50 SHM jobs.
        """
        retry = 0
        offset, limit = 1, 50
        while retry <= 60:
            try:
                if self.name == "CapacityExpansionLicenseJob":
                    payload = self.construct_capacity_expansion_license_job_payload(limit)
                    list_of_jobs = self.get_shm_jobs(self.user, 1, limit, payload)
                    if not list_of_jobs:
                        raise IndexError
                else:
                    list_of_jobs = self._get_jobs_results(self.get_shm_jobs(self.user, offset, limit),
                                                          jobName=self.name)[0]
                return list_of_jobs
            except IndexError as e:
                offset += 50
                limit += 50
                log.logger.debug("Unable to retrieve job list using {0}".format(SHM_JOBS_LIST_ENDPOINT))
            except Exception as e:
                log.logger.debug("Unable to retrieve job list using {0}".format(str(e)))
            retry += 1
            sleep(5)
        raise EnmApplicationError(e.message)

    def get_lkf_job(self):
        """
        Fetches LKF jobs from shm UI and returns those jobs to validate

        :rtype: list
        :return: list of jobs
        """
        log.logger.debug("Attempts to fetch the LKF Jobs from UI")
        response = self._get_job_response().json()['result']
        return response


class MultiUpgrade(ShmJob):

    def __init__(self, upgrade_jobs_to_merge, *args, **kwargs):
        """
        Multiple UpgradeJob constructor
        :type args: list
        :param args: list of arguments
        :type kwargs: list
        :param kwargs: list of arguments
        :type upgrade_jobs_to_merge: list
        :param upgrade_jobs_to_merge: List of SHM Upgrade job objects to merge into a single job
        """
        kwargs.setdefault("job_type", "UPGRADE")
        super(MultiUpgrade, self).__init__(*args, **kwargs)
        self.upgrade_jobs_to_merge = upgrade_jobs_to_merge

    def set_properties(self):
        """
        Properties payload for Upgrade Job
        """

    def set_activities(self):
        """
        Activities Schedule payload for Upgrade Job
        """

    def update_activities_schedule(self):
        """
        Activities Schedule payload for Upgrade Job
        """
        activities = {'activitySchedules': [{"platformType": self.upgrade_jobs_to_merge[0].platform, "value": []}]}
        for job in self.upgrade_jobs_to_merge:
            job_activity = {"neType": job.ne_type, "value": job.set_activities()}
            activities.get('activitySchedules')[0].get("value").append(job_activity)
        self.payload.update(activities)

    def update_configuration(self):
        configurations = {"configurations": []}
        for job in self.upgrade_jobs_to_merge:
            job_config = {"neType": job.ne_type, "properties": job.set_properties()}
            configurations.get('configurations').append(job_config)
        self.payload.update(configurations)
