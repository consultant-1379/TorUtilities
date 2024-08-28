# ********************************************************************
# Name    : CM Import Over NBI
# Summary : Primary module for interacting with CM Import NBI.
#           Allows user to create, delete, query, Undo Jobs,  NBI
#           Imports over API v1 or API v2.
# ********************************************************************

import time
import datetime

from retrying import retry
from requests import RequestException

from enmutils.lib import filesystem, log
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import (TimeOutError, EnmApplicationError, FileDoesNotExist, RemoveUndoConfigFilesError,
                                     ValidationWarning, RemoveUndoJobError)
from enmutils_int.lib.cm_import_export_nbi_common import get_download_file, get_download_job_details_by_id


class CmImportOverNbi(object):

    GET_UNDO_ENDPOINT = '/configuration/jobs/{undo_id}?type=UNDO_IMPORT_TO_LIVE'

    def __init__(self, timeout=90 * 60):
        self.id = None
        self.timeout = timeout

    def create_import_over_nbi(self, post_endpoint, file_in=None):
        """
        Create the import job with a POST request containing the file information

        :param post_endpoint: v1 or v2 REST endpoint to use
        :type post_endpoint: str
        :param file_in: file path passed in of the undo file, if the import is an undo iteration
        :type file_in: str
        :return: the response to the REST request in JSON format
        :rtype: dict

        :raises: HTTPError
        """

        template_name = None
        file_type = None

        if file_in:
            template_name = file_in.replace('/', '_')
            file_type = 'dynamic'

        template_name = self.template_name if not template_name else template_name
        log.logger.debug('Starting import with file {0}'.format(template_name))
        file_type = self.file_type if not file_type else file_type
        error_handling = self.error_handling if self.error_handling else "stop-on-error"

        post_request_body = {
            'type': 'IMPORT',
            'fileName': template_name,
            'configName': self.config_name or 'Live',
            'fileFormat': file_type,
        }
        if self.interface == 'NBIv2':
            post_request_body.update(
                {'executionPolicy': [error_handling] if isinstance(error_handling, str) else error_handling})
        response = self.user.post(post_endpoint, json=post_request_body,
                                  headers={'Content-Type': 'application/json'})
        raise_for_status(response, message_prefix='Could not initiate import: ')

        return response.json()


class CmImportOverNbiV1(CmImportOverNbi):

    POST_IMPORT_ENDPOINT_V1 = '/bulk/import/jobs'
    GET_IMPORT_ENDPOINT_V1 = '/bulk/import/jobs/{job_id}'

    def create_import_over_nbi_v1(self, file_in=None):
        """
        Create the import job with a POST request
        :param file_in: file path passed in of the undo file, if the import is an undo iteration
        :type file_in: str

        """
        create_response = super(CmImportOverNbiV1, self).create_import_over_nbi(self.POST_IMPORT_ENDPOINT_V1, file_in)
        file_uri = create_response.get('fileUri')
        self.add_file_to_import_job_v1(file_uri, file_in)

    def add_file_to_import_job_v1(self, file_uri, file_in=None):
        """
        Attach a file to the import job by carrying out a PUT request to the file URI
        :param file_uri: file URI to send the PUT request to
        :type file_uri: URI
        :param file_in: file path passed in of the undo file, if the import is an undo iteration
        :type file_in: str

        :raises: HTTPError
        """

        file_in = self.filepath if not file_in else file_in

        put_file_response = self.user.put(file_uri, headers={'Content-Type': 'application/octet-stream'}, data=open(file_in))
        raise_for_status(put_file_response, message_prefix='Could not update import job with file content')
        self.id = put_file_response.json().get('id')

        self.poll_until_completed(job_id=self.id)

    def poll_until_completed(self, job_id, undo=False):
        """
        Poll the import job until it is FAILED, COMPLETED, or times out

        :param job_id: id of the import job to poll
        :type job_id: int
        :param undo: if True the import job is an undo iteration
        :type undo: bool

        :raises EnmApplicationError: raised if the import job fails
        :raises TimeOutError: raised if the profile reaches its validation timeout
        """

        status = None
        timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=self.timeout)
        log.logger.debug('Waiting for the job to complete. Maximum wait time is {0} seconds'.format(self.timeout))
        log.logger.debug('To retrieve the details of the import job go to endpoint: /bulk/import/jobs/{job_id}'.format(job_id=self.id))

        while datetime.datetime.now() < timeout_time:
            if undo:
                job_details = get_download_job_details_by_id(self.user, job_id, end_point=self.GET_UNDO_ENDPOINT)
            else:
                job_details = self.get_job_details_by_id(job_id)
            status = job_details.get('status')

            if status == 'COMPLETED':
                log.logger.debug('Job id {0} has completed successfully'.format(job_id))
                break
            elif status == 'FAILED':
                status_reason = job_details.get('statusReason')
                raise EnmApplicationError('ERROR: Job id {0} failed. {1}'.format(job_id, status_reason))
            time.sleep(60)
        else:
            raise TimeOutError("Current status of the job {id} is '{status}' and not 'COMPLETED'."
                               "This profile has encountered a timeout error after {timeout} minutes."
                               .format(id=job_id, status=status, timeout=self.timeout / 60))

    def get_job_details_by_id(self, job_id):
        """
        Get the job details with a GET request
        :param job_id: id of the import job to retrieve details of
        :type job_id: int
        :return: the response to the REST request in JSON format
        :rtype: dict
        :raises: HTTPError
        """

        get_details_response = self.user.get(self.GET_IMPORT_ENDPOINT_V1.format(job_id=job_id))
        raise_for_status(get_details_response, message_prefix='Could not get details for job {0}: '.format(job_id))

        return get_details_response.json()


class CmImportOverNbiV2(CmImportOverNbi):
    """
    Carry out a CM import job over NBI version 2
    """

    POST_IMPORT_ENDPOINT = '/bulk-configuration/v1/import-jobs/jobs'
    EXECUTE_IMPORT_ENDPOINT = '/bulk-configuration/v1/import-jobs/jobs/{id}/invocations'
    GET_IMPORT_ENDPOINT = '/bulk-configuration/v1/import-jobs/jobs/{id}'
    FILE_UPLOAD_LINK = '/bulk-configuration/v1/import-jobs/jobs/{id}/files'
    SUMMARY_ENDPOINT = '/bulk-configuration/v1/import-jobs/jobs/{id}/?expand=summary&expand=failures'

    def create_import_over_nbi_v2(self, file_in=None):
        """
        Create the import job with a POST request

        :param file_in: file path passed in of the undo file, if the import is an undo iteration
        :type file_in: str

        """
        response_json = super(CmImportOverNbiV2, self).create_import_over_nbi(self.POST_IMPORT_ENDPOINT, file_in)
        self.id = response_json.get('id')
        self.add_file_to_import_job(file_in)

    def add_file_to_import_job(self, file_in=None):
        """
        Attach a file to the import job by carrying out a POST request to the file upload link

        :param file_in: file path passed in of the undo file, if the import is an undo iteration
        :type file_in: str

        :raises: HTTPError
        """

        template_name = None
        if file_in:
            template_name = file_in.replace('/', '_')
        template_name = self.template_name if not template_name else template_name

        file_in = self.filepath if not file_in else file_in

        file_to_import = open(file_in, 'r')
        file_body = {
            'file': (None, file_to_import),
            'filename': (None, template_name)
        }

        post_response = self.user.post(self.FILE_UPLOAD_LINK.format(id=self.id), files=file_body)
        raise_for_status(post_response, message_prefix='Could not add file to import job {0}: '.format(self.id))
        try:
            self.validation_flow()
        except ValidationWarning:
            setattr(self, 'skip_history_check', True)

    def validation_flow(self):
        """
        Carry out the validation of the import job with a POST request.
        The status of the job is polled until it is 'VALIDATED'.

        NOTE: An import job via NBI version 2 needs to complete two flows. Firstly, it must be validated, and then it
        can be executed.
        This is achieved by specifying the 'invocationFlow' in the REST request. The invocationFlow can be
        'validate' or 'execute'.

        :raises: HTTPError
        """

        validate_json = {'invocationFlow': 'validate'}
        validate_response = self.user.post(self.EXECUTE_IMPORT_ENDPOINT.format(id=self.id), json=validate_json,
                                           headers={'Content-Type': 'application/json'})
        raise_for_status(validate_response, message_prefix='Could not validate import job {0}: '.format(self.id))
        self.poll_until_flow_is_complete(end_status='VALIDATED')
        # Check if there are valid operations or raise warning
        if self.no_valid_operations():
            log.logger.debug("No valid operations, nothing to execute.")
            raise ValidationWarning("No valid operations found, no execute operation will be performed.")
        time.sleep(1)  # Sleep between validation and execution: See RTD-6645
        setattr(self, 'skip_history_check', False)
        self.execution_flow()

    def no_valid_operations(self):
        """
        Check the job summary for valid operations

        :return: Number of valid operations
        :rtype: int
        """
        log.logger.debug("Checking job summary for valid operations.")
        job_details, valid_operations = None, None
        try:
            job_details = self.get_import_job_summary_by_id()
            valid_operations = job_details.get("summary").get("total").get("valid")
            log.logger.debug("Check completed, found a total of [{0}] valid operations to complete."
                             .format(valid_operations))
        except AttributeError:
            log.logger.debug("Failed to retrieve valid operations from response: [{0}].\nFlow will continue and "
                             "attempt operations.".format(job_details))
        except Exception as e:
            log.logger.debug("Failed to retrieve valid operations from response: [{0}].".format(str(e)))
        return True if valid_operations == 0 else False

    def execution_flow(self):
        """
        Carry out the import job with a POST request.
        The status of the job is polled until it is 'EXECUTED'.

        NOTE: An import job via NBI version 2 needs to complete two flows. Firstly, it must be validated, and then it
        can be executed.
        This is achieved by specifying the 'invocationFlow' in the REST request. The invocationFlow can be
        'validate' or 'execute'.

        :raises: HTTPError
        """

        execute_json = {'invocationFlow': 'execute'}
        execute_response = self.user.post(self.EXECUTE_IMPORT_ENDPOINT.format(id=self.id), json=execute_json,
                                          headers={'Content-Type': 'application/json'})
        raise_for_status(execute_response, message_prefix='Could not execute import job {0}: '.format(self.id))
        self.poll_until_flow_is_complete(end_status='EXECUTED')

    @retry(retry_on_exception=lambda e: isinstance(e, RequestException), wait_fixed=500, stop_max_attempt_number=2)
    def poll_until_flow_is_complete(self, end_status):
        """
        Poll the import job by its ID, until it is 'VALIDATED' or 'EXECUTED', depending on the end_status specified.

        :param end_status: status to poll for - VALIDATED or EXECUTED
        :type end_status: str

        :raises EnmApplicationError: raised if the import job fails
        :raises TimeOutError: raised if the profile reaches its validation timeout
        """

        status = None
        timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=self.timeout)
        log.logger.debug('Waiting for the job to be {0}. Maximum wait time is {1} seconds'.format(end_status, self.timeout))
        log.logger.debug('To retrieve the details of the import job go to endpoint: /bulk-configuration/v1/import-jobs/'
                         'jobs/{job_id}/operations'.format(job_id=self.id))
        while datetime.datetime.now() < timeout_time:
            job_details = self.get_import_job_by_id()
            status = job_details.get('status')
            if status == end_status:
                failure_reason = job_details.get('failureReason')
                if failure_reason and end_status == "EXECUTED":
                    raise EnmApplicationError(
                        "ERROR: Job id {0} returned 'failureReason': {1}".format(self.id, failure_reason))
                log.logger.debug('Job {0} has {1} successfully'.format(self.id, end_status))
                break
            if self.name.startswith('cmimport_13') or self.name.startswith('cmimport_31') or self.name.startswith('cmimport_32') or self.name.startswith('cmimport_33'):
                time.sleep(0.5)
            else:
                time.sleep(60)
        else:
            status = status if status else 'no status available'
            raise TimeOutError("Current status of the job {id} is '{status}' and not {end_status}."
                               "This profile has encountered a timeout error after {timeout} minutes."
                               .format(id=self.id, status=status, end_status=end_status, timeout=self.timeout / 60))

    def get_import_job_by_id(self):
        """
        Carries out a GET request with the job id to find the status of the job
        :return: the response to the REST request in JSON format
        :rtype: dict
        :raises: HTTPError
        """

        response = self.user.get(self.GET_IMPORT_ENDPOINT.format(id=self.id),
                                 headers={'Content-Type': 'application/json'})
        raise_for_status(response, message_prefix='Could not retrieve import by id: ')

        return response.json()

    def get_import_job_summary_by_id(self, job_id=None):
        """
        Carries out a GET request with the job id to find the summary of the job

        :raises HTTPError: raised if the GET request fails

        :return: the response to the REST request in JSON format
        :rtype: dict
        """
        job_id = self.id if not job_id else job_id
        response = self.user.get(self.SUMMARY_ENDPOINT.format(id=job_id),
                                 headers={'Content-Type': 'application/json'})
        raise_for_status(response, message_prefix='Could not retrieve import summary by id: ')
        return response.json()


class UndoOverNbi(CmImportOverNbiV1):

    UNDO_CONFIGS_FILEPATH = '/tmp/wl_storage/profile_undo_configs/'
    UNDO_POST_ENDPOINT = '/configuration/jobs?type=UNDO_IMPORT_TO_LIVE'
    DELETE_UNDO_JOB = 'config undo --remove --job {0}'

    def __init__(self, user, name, file_type):
        super(UndoOverNbi, self).__init__()
        self.user = user
        self.file_type = file_type
        self.UNDO_CONFIGS_FILEPATH = self.UNDO_CONFIGS_FILEPATH + name
        self.id = None

    def undo_job_over_nbi(self, id_of_job_to_undo):
        """
        Carry out a POST request to initiate the undo job, then call the function to poll the job until completed.
        Finally, call the function to retrieve the undo file

        :param id_of_job_to_undo: id of the import job that the undo job is acting upon
        :type id_of_job_to_undo: int
        :raises: HTTPError
        :return: the id of the undo job read from POST response
        :rtype: int
        """

        log.logger.debug('Attempting to initiate the undo job for job id {0}'.format(id_of_job_to_undo))

        post_response = self.user.post(self.UNDO_POST_ENDPOINT, headers={'Content-Type': 'application/json'},
                                       json={'id': id_of_job_to_undo, 'type': 'UNDO_IMPORT_TO_LIVE'})
        raise_for_status(post_response, 'Error initiating the undo job for job id {0}'.format(id_of_job_to_undo))
        self.id = post_response.json().get('id')

        self.poll_until_completed(self.id, undo=True)

        get_download_file(self.user, self.id, operation="undo", end_point=self.GET_UNDO_ENDPOINT,
                          file_path=self.UNDO_CONFIGS_FILEPATH)

        return self.id

    def get_undo_config_file_path(self):
        """
        Retrieves the path of the undo configuration file

        :return: path of the undo file
        :rtype: str
        :raises FileDoesNotExist: raised if file does not exist in directory
        :raises Exception: raised if error encountered retrieving the file path
        """

        log.logger.debug(
            "Attempting to GET UNDO CONFIG FILE PATH from directory: '{0}'".format(self.UNDO_CONFIGS_FILEPATH))
        try:
            files = filesystem.get_files_in_directory(directory=self.UNDO_CONFIGS_FILEPATH, full_paths=True)
            for undo_file in files:
                self.id = str(self.id)
                if self.id == undo_file.split(".")[0][-len(self.id):]:
                    log.logger.debug("Successfully RETRIEVED UNDO CONFIG FILE PATH from directory: '{0}'".format(
                        self.UNDO_CONFIGS_FILEPATH))
                    undo_filepath = undo_file
                    break
            else:
                raise FileDoesNotExist(
                    "Undo file ending in: '{0}' does not exist in directory: '{1}'".format(
                        self.id, self.UNDO_CONFIGS_FILEPATH))
        except Exception:
            log.logger.debug(
                "ERROR RETRIEVING UNDO CONFIG FILE PATH FROM DIRECTORY: '{0}'".format(self.UNDO_CONFIGS_FILEPATH))
            raise

        return undo_filepath

    def remove_undo_config_files(self):
        """
        Call to remove the directory containing all associated files locally
        :raises RemoveUndoConfigFilesError
        """
        log.logger.debug('Attempting to remove undo config files')
        try:
            filesystem.remove_dir(self.UNDO_CONFIGS_FILEPATH)
        except Exception as e:
            log.logger.debug('ERROR REMOVING UNDO CONFIG FILES')
            raise RemoveUndoConfigFilesError(e)
        log.logger.debug('Successfully removed undo config files')

    def remove_undo_job(self, user, id_of_job_to_undo):
        """
        Call to remove the UNDO job created
        :param user: User who execute the command
        :type user: `enm_user_2.User`
        :param id_of_job_to_undo: the id of the undo job
        :type id_of_job_to_undo: int
        :raises RemoveUndoJobError: raised if it fails to delete undo job
        """
        try:
            log.logger.debug("Deleting the undo job")
            response = user.enm_execute(self.DELETE_UNDO_JOB.format(id_of_job_to_undo))
            log.logger.debug("Response of undo job remove command : {0}".format(response.get_output()))
        except Exception as e:
            log.logger.debug("ERROR DELETING UNDO JOB")
            raise RemoveUndoJobError(e)
        log.logger.debug("Successfully removed undo job")
