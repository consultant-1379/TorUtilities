import os
import re
from datetime import datetime, timedelta

from enmutils.lib import log
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, RequestException, EnmApplicationError
from enmutils_int.lib.cm_import_export_nbi_common import get_download_file
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class CmExport17(GenericFlow):

    GET_ALL_NBI_CMEXPORT_JOBS_ENDPOINT = "/bulk/export/jobs"
    GET_NBI_CMEXPORT_JOB_ENDPOINT = "/bulk/export/jobs/{0}"
    CMEXPORT_ALL_JOBS = "cmedit export -st"
    CMEXPORT_DOWNLOAD = "cmedit export -dl -j {0}"
    NBI_CMEXPORT_PROFILES = ['CMEXPORT_03', 'CMEXPORT_08', 'CMEXPORT_11', 'CMEXPORT_12', 'CMEXPORT_20']
    CLI_CMEXPORT_PROFILES = ['CMEXPORT_01', 'CMEXPORT_02', 'CMEXPORT_05', 'CMEXPORT_07', 'CMEXPORT_13', 'CMEXPORT_14',
                             'CMEXPORT_16', 'CMEXPORT_18', 'CMEXPORT_19', 'CMEXPORT_21', 'CMEXPORT_22']

    def execute_flow(self):
        """
        Execute the profile flow
        """
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep()
            log.logger.debug(
                "Checking for CMExport jobs that have occurred via the CLI. CLI profiles : {0}".format(
                    self.CLI_CMEXPORT_PROFILES))
            self.download_files_over_cli(user)
            log.logger.debug(
                "Checking for CMExport jobs that have occurred via the NBI. NBI profiles: {0}".format(
                    self.NBI_CMEXPORT_PROFILES))
            self.download_files_over_nbi(user)

    def download_files_over_cli(self, user):
        """
        Download cmexport file(s) via CLI.
        All files exported via CLI in the last 15 minutes will be downloaded via CLI.

        :param user: user to carry out the requests
        :type user: enm_user_2.User
        """

        try:
            job_ids = self.get_job_ids(user)
            if job_ids:
                for job_id in job_ids:
                    response = user.enm_execute(self.CMEXPORT_DOWNLOAD.format(job_id), outfile=os.devnull)
                    if response.http_response_code() not in [200, 201]:
                        self.add_error_as_exception(ScriptEngineResponseValidationError(
                            "Export download command failed.", response=response))
            else:
                log.logger.debug("No CMExports completed via CLI in the last 15 minutes. Nothing to download.")
        except Exception as e:
            self.add_error_as_exception(e)

    def download_files_over_nbi(self, user):
        """
        Download cmexport file(s) via NBI.
        All files exported via NBI in the last 15 minutes will be downloaded via NBI.

        :param user: user to carry out the requests
        :type user: enm_user_2.User
        """
        try:
            nbi_job_ids = self.get_nbi_job_ids_in_last_fifteen_mins(user)
            if nbi_job_ids:
                log.logger.debug(
                    "CMExport NBI job IDs to download that occurred in the previous 15 minutes: {0}".format(
                        nbi_job_ids))
                for nbi_id in nbi_job_ids:
                    log.logger.debug("Downloading file with id: {0}".format(nbi_id))
                    try:
                        get_download_file(user, nbi_id, operation="download",
                                          end_point=self.GET_NBI_CMEXPORT_JOB_ENDPOINT.format(nbi_id))
                    except Exception as e:
                        self.add_error_as_exception(e)
            else:
                log.logger.debug("No CMExports completed via NBI in the last 15 minutes. Nothing to download.")
        except Exception as e:
            self.add_error_as_exception(e)

    def get_job_ids(self, user):
        """
        Retrieve the list of job IDs for the cmexport jobs that occurred in the previous 15 minutes.
        Exclude ENIQ files as these files are moved to the PM filesystems after the export
        :param user: user to carry out the requests
        :type user: enm_user_2.User
        :return: list of IDs of the cmexport jobs carried out in the previous 15 minutes
        :rtype: list
        :raises ScriptEngineResponseValidationError: if error retrieving all cmexport jobs
        """
        job_ids = []
        time_match_found = False

        response = user.enm_execute(self.CMEXPORT_ALL_JOBS)
        if response.http_response_code() not in [200, 201]:
            raise ScriptEngineResponseValidationError("Unable to retrieve all cmexport jobs.", response=response)

        time_now = datetime.now()
        time_fifteen_mins_ago = time_now - timedelta(minutes=15)
        log.logger.debug("Checking for COMPLETED CMExport jobs between {0} and {1}".format(
            time_fifteen_mins_ago, time_now))
        regex_to_match_date_time_format = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'

        for response_line in response.get_output():
            if any(cli_profile in response_line for cli_profile in self.CLI_CMEXPORT_PROFILES):
                match_with_date_time_format = re.findall(regex_to_match_date_time_format, response_line)
                if match_with_date_time_format:
                    time_to_check = datetime.strptime(match_with_date_time_format[-1], '%Y-%m-%dT%H:%M:%S')
                    time_match_found = (time_fifteen_mins_ago <= time_to_check <= time_now)

                if (time_match_found and "COMPLETED" in response_line and "ENIQ" not in response_line and ".xml" not in
                        response_line):
                    log.logger.debug("Match found - extracting CMExport job ID")
                    extract_id_match = re.search(r"(\A\d+\s)", response_line)

                    if extract_id_match:
                        job_ids.append(extract_id_match.group(0).strip())

        log.logger.debug("CMExport CLI job IDs to download that occurred in the previous 15 minutes: {0}"
                         .format(job_ids))
        return job_ids

    def get_nbi_job_ids_in_last_fifteen_mins(self, user):
        """
        Retrieve the list of job IDs for the cmexport over NBI jobs that occurred in the previous 15 minutes

        :return: list of IDs of the cmexport NBI jobs carried out in the previous 15 minutes
        :rtype: list
        :raises ScriptEngineResponseValidationError: if error retrieving all cmexport jobs
        """

        try:
            log.logger.debug("Checking for COMPLETED NBI CMExport jobs in the previous 15 minutes.")
            time_now = datetime.now()
            time_fifteen_mins_ago = time_now - timedelta(minutes=15)

            get_all_jobs = user.get(self.GET_ALL_NBI_CMEXPORT_JOBS_ENDPOINT,
                                    headers={'Content-Type': 'application/json'})
            raise_for_status(get_all_jobs)
            jobs = get_all_jobs.json().get("jobs")
            if jobs:
                return self._get_nbi_job_ids(jobs, time_fifteen_mins_ago, time_now)
            else:
                log.logger.debug("There are no CMExport over NBI jobs. Nothing to download")
        except RequestException as e:
            self.add_error_as_exception(EnmApplicationError(e.message))
        except Exception as e:
            log.logger.debug("Failed to retrieve all jobs:  {0}".format(str(e)))
            self.add_error_as_exception(e)

    def _get_nbi_job_ids(self, jobs, time_fifteen_mins_ago, time_now):
        """
        Return the job ids of the exports that were executed via the NBI in the previous 15 minutes

        :param jobs: all jobs that have executed via NBI
        :type jobs: list
        :param time_fifteen_mins_ago: time 15 minutes ago
        :type time_fifteen_mins_ago: datetime.datetime
        :param time_now: current time
        :type time_now: datetime.datetime
        :return: the ids of the exports that were executed via the NBI in the previous 15 minutes
        :rtype: list
        """
        nbi_job_ids = []

        for job in jobs:
            job_name = job.get("jobName")
            if any(nbi_profile in job_name.upper() for nbi_profile in self.NBI_CMEXPORT_PROFILES):
                job_status = job.get("status")
                if job_status == "COMPLETED":
                    job_time = datetime.strptime(job.get("endTime"), '%Y-%m-%dT%H:%M:%S.%f')
                    if (time_fifteen_mins_ago <= job_time <= time_now) and "ENIQ" not in job_name:
                        nbi_job_ids.append(job.get("id"))
        return nbi_job_ids
