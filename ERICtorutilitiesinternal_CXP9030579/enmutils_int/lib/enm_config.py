# ********************************************************************
# Name    : ENM Config
# Summary : Module which contains classes used by Cm Import
#           Configuration. Allows the user to create, delete and
#           query CM configurations, also provides classes to perform
#           a copy node or undo CM job.
# ********************************************************************

import re
import time
from datetime import datetime, timedelta

from enmscripting.exceptions import TimeoutException

from enmutils.lib import log
from enmutils.lib.exceptions import (ScriptEngineResponseValidationError, ENMJobStatusError,
                                     ENMJobDetailStatusError, TimeOutError)


class EnmJob(object):

    VALIDATION_TIMEOUT = 90 * 60

    def __init__(self, user, name=None, filepath=None, timeout=VALIDATION_TIMEOUT):
        self.id = None
        self.name = name
        self.user = user
        self.filepath = filepath
        self.timeout = self.VALIDATION_TIMEOUT if not timeout else timeout

    def create(self, validate=True, detailed_validation=False, file_in=None):
        """
        Creates the enm job and tries to validate if the creates becomes COMPLETED before
        it times out
        NOTE: The same user should not be used to run imports in parallel.
        :validate: bool indicating if we need to validate the creation of the job
        """
        self.id = None  # Reset the job id from previous profile run
        file_in = self.filepath if not file_in else file_in
        create_command = self.get_create_command()
        response = self.user.enm_execute(command=create_command, file_in=file_in)
        output = response.get_output()
        log.logger.debug("Script engine response for command {0} is {1}".format(
            create_command[:1000], ','.join(output)))

        for output_string in output:
            if 'job ID' in output_string:
                self.id = re.search(r"ID\s(\d+)", output_string).groups()[0]
                log.logger.debug('Job id identified: {0}'.format(self.id))
                break

        if not self.id:
            raise ScriptEngineResponseValidationError(
                "ScriptEngineResponse did not contain job ID for command '{0}'"
                "Response was '{1}'".format(create_command[:1000], ','.join(output)), response=response)

        log.logger.debug("Job {0} successfully created with id {1}".format(create_command[:1000], self.id))

        if validate:
            self.wait_for_finish(detailed_validation=detailed_validation)

    def get_status(self, status_command):
        """
        Reads the status of the create command
        """
        try:
            response = self.user.enm_execute(command=status_command, on_terminal=False)
        except TimeoutException as e:
            log.logger.debug(
                "A Timeout was encountered via enmscripting library while checking the status of the "
                "currently executing job: {0} via command '{1}'. "
                "This indicates a problem on ENM. "
                "Note: Use verbose option, e.g. -v (if available), for extra information. "
                "".format(self.id, status_command))
            raise e
        if not response.get_output().has_groups():
            raise ScriptEngineResponseValidationError(
                "ScriptEngineResponse did not contain table output for command: '{0}' "
                "Response was: '{1}'".format(self.get_status_command(),
                                             response.get_output()), response=response)
        return response

    def wait_for_finish(self, detailed_validation=False):
        """
        Waits for the script engine command status to become COMPLETED. This should only be used
        where we expect a table output for the status of the jobs running in ENM like cm imports
        and cm configs

        :raises TimeOutError: if timeout encountered when waiting for the import job to complete
        :raises TimeoutException: if timeout encountered when checking import job status
        :raises ENMJobStatusError: if the job status is 'FAILED', 'ERROR', 'STOPPED'
        :raises ENMJobDetailStatusError: if the detailed job status is not 'COMPLETED'

        """

        status = None
        create_job = self.get_create_command()
        status_command = self.get_status_command()
        log.logger.debug("Waiting for the job {0} to complete. Maximum wait time is {1} seconds"
                         .format(create_job[:1000], self.timeout))
        timeout_time = datetime.now() + timedelta(seconds=self.timeout)

        while datetime.now() < timeout_time:
            response = self.get_status(status_command)
            status_groups = response.get_output().groups()[0][0]
            status = status_groups.find_by_label('Status')[0].value()
            job_status_column = 'Status'
            error_message = ("The {column} of the ENM job, id:'{job_id}', is '{status}'. The reason was - '{reason}'. "
                             "This indicates that there is a problem on ENM while running command '{create_command}'. "
                             "The status of the command can be checked via '{status_command}'."
                             "Note: Use verbose option, e.g. -v (if available), for extra information."
                             .format(column="{column}", job_id=self.id, status="{status}", reason=response.get_output(),
                                     create_command=create_job[:1000], status_command=status_command))
            if status in [u'FAILED', u'ERROR', u'STOPPED']:
                raise ENMJobStatusError(error_message.format(column=job_status_column, status=status), response=response)
            elif status == u'COMPLETED':
                if detailed_validation:
                    detailed_status_column = 'Status detail'
                    detailed_status = status_groups.find_by_label('Status detail')[0].value()
                    if detailed_status != u'COMPLETED':
                        raise ENMJobDetailStatusError(
                            error_message.format(column=detailed_status_column, status=detailed_status),
                            response=response)
                log.logger.debug("Job {0} was completed successfully".format(create_job[:1000]))
                break
            time.sleep(20)
        else:
            status = status if status else "no status available"
            raise TimeOutError(
                "The current status of the ENM job, id:'{job_id}', is still not 'COMPLETED'. "
                "This profile will only wait {wait_time} minutes for the job to complete successfully. "
                "The current status is: '{status}' and therefore this indicates a problem on ENM. "
                "The status and execution time can be checked via '{status_command}'. "
                "Note: Use verbose option, e.g. -v (if available), for extra information"
                "".format(job_id=self.id, wait_time=self.timeout / 60, status=status, status_command=status_command))


class CopyNodes(object):
    CREATE_CMD = ''
    STATUS_CMD = ''


class Activate(object):
    CREATE_CMD = ''
    STATUS_CMD = ''


class Undo(object):
    UNDO_ACTIVATION = ''
    UNDO_IMPORT = ''
    STATUS = ''
    UNDO_DOWNLOAD = ''
    UNDO_CONFIGS_FILEPATH = ""
    REMOVE = ''


class Config(object):
    CREATE_CMD = ''


class ConfigDelete(object):
    CREATE_CMD = ''
    STATUS_CMD = ''
