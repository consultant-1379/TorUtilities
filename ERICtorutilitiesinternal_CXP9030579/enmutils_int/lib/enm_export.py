# ********************************************************************
# Name    : ENM Export
# Summary : Primary module used by CM and SHM Exports.
#           Allows the user to set Export related PIB values, provides
#           classes and functionality for the creation, deletion,
#           verification and downloading of both CM and SHM Exports.
# ********************************************************************

import datetime
import random
import re
import time

from retrying import retry

from enmutils.lib import log, headers, shell
from enmutils.lib.enm_user_2 import raise_for_status, SessionTimeoutException
from enmutils.lib.exceptions import (ScriptEngineResponseValidationError, TimeOutError, EnmApplicationError)
from enmutils_int.lib import common_utils
from enmutils_int.lib import enm_deployment

GET_EXPORT_ENDPOINT = '/bulk/export/jobs/{id}'
CREATE_EXPORT_ENDPOINT = '/bulk/export/jobs'
GET_REPORT_ENPOINT = '/bulk/export/reports/{id}'


def toggle_pib_historicalcmexport(state):
    """
    :param state: Toggle turning on/off pib parameter for ENIQ Historical Export in cmexport_19 profile
    :type state: str
    :raises EnmApplicationError: if pip config script execution returns non zero return code
    """

    impexpserv_ip = enm_deployment.get_values_from_global_properties('impexpserv')
    response = shell.run_cmd_on_emp_or_ms("sudo /ericsson/pib-scripts/etc/config.py update "
                                          "--name=ETS_HistoricalCMExportEnabled "
                                          "--value={state} --app_server_address={vm_host}:8080 "
                                          "--scope=GLOBAL".format(state=state, vm_host=impexpserv_ip[0]))

    if response.rc != 0:
        raise EnmApplicationError("Setting Historical ENIQ Export PIB parameter failed with result: {0}"
                                  .format(response.stdout))
    elif state != 'true':
        log.logger.debug("ENIQ Historical CM Export is disabled. ")
    else:
        log.logger.debug("ENIQ Historical CM Export is enabled. ")


def create_and_validate_cm_export_over_nbi(cm_export_obj, profile):
    """
    Call the create and validate CM_NBI export methods for each parallel export job

    :type cm_export_obj: `CmExport`
    :param cm_export_obj: CM_NBI Export object to be executed in parallel by thread queue
    :type profile: `Profile`
    :param profile: Profile to add errors

    :raises Exception: when invalid job id e.g. None is returned from CM NBI json response
    """

    if profile.NAME == 'CMEXPORT_03':
        random_sleep = random.randint(0, 300)
        log.logger.debug("Sleeping randomly for {0} seconds".format(random_sleep))
        time.sleep(random_sleep)
    try:
        nbi_job_name = "{0}_{1}".format(profile.identifier, cm_export_obj.name)
        cm_export_obj.create_over_nbi(nbi_job_name)
        log.logger.debug(
            "{0} CM_NBI job is created with job id {1} ".format(nbi_job_name, cm_export_obj.job_id))
        cm_export_obj.validate_over_nbi()
    except Exception as e:
        profile.add_error_as_exception(e)


def create_and_validate_cm_export(cm_export_obj, profile):
    """
    Call the create and validate CM_CLI export methods for each parallel export job

    :type cm_export_obj: `CmExport`
    :param cm_export_obj: CM_CLI Export object to be executed in parallel by thread queue
    :type profile: `Profile`
    :param profile: Profile to add errors

    :raises Exception: when create/validation of export jobs fails
    """
    # Random sleep to stagger the parallel executions
    random_sleep = random.randint(0, 300)
    log.logger.debug("Sleeping randomly for {0} seconds".format(random_sleep))
    time.sleep(random_sleep)

    try:
        cm_export_obj.create()
        cm_export_obj.validate()
    except Exception as e:
        profile.add_error_as_exception(e)


class Export(object):
    DYNAMIC_EXPORT_LICENCE = "FAT1023443.txt"
    EXPORT_STATUS_CMD = "cmedit export -st -j {job_id}"
    EXPORT_DELETE_CMD = "cmedit export -rm -j {job_id}"
    CM_SERVICE_NAME = "-cmserv"

    def __init__(self, user, name=None, nodes=None, verify_timeout=124 * 60, node_regex='*', polling_interval=30):
        """
        Export constructor

        :type name: string
        :param name: Name for Export
        :type nodes: list
        :param nodes: list of enm_node.BaseNode objects to implement export policy on
        :type user: enm_user.User
        :param user: User Object
        :type verify_timeout: int
        :param verify_timeout: time for command to complete (in seconds)
        :type node_regex: str
        :param node_regex: String to represent the node type to use while creating export
        :param polling_interval: sleep interval to run command if fails
        :type polling_interval: int
        """

        self.name = name
        self.nodes = nodes
        self.user = user
        self.job_id = None
        self.verify_timeout = verify_timeout
        self.node_regex = node_regex
        self.polling_interval = polling_interval

    @property
    def node_names(self):
        return [self.node_regex] if not self.nodes else [node.node_id for node in self.nodes]

    def exists(self):
        """
        Method to check if export exists on ENM already

        :return: Boolean indicating if the export name is already present in ENM list of jobs
        :rtype: bool
        """
        all_job_names = []
        try:
            response = self.user.get(CREATE_EXPORT_ENDPOINT)
            if response.json():
                all_job_names = [job.get("jobName") for job in response.json().get("jobs")]
            if all_job_names and self.name in all_job_names:
                return True
        except Exception as e:
            log.logger.debug("Failed to confirm job exists, response: {0}".format(str(e)))

    def delete(self):
        """
        Deletes export job from both cli app, and .xml or .zip from cmserv

        :raises EnmApplicationError: raised if the job id is not set
        :raises ScriptEngineResponseValidationError: raised the delete command fails
        """

        if not self.job_id:
            raise EnmApplicationError('Job id not set, cannot delete job.')

        response = self.user.enm_execute(
            command=self.EXPORT_DELETE_CMD.format(job_id=self.job_id))
        output = response.get_output()

        log.logger.debug(
            'Script engine response for export delete command for {0} is {1}'.format(
                self.name, ','.join(output)))

        if not output or "Export job was successfully removed." not in output[0]:
            raise ScriptEngineResponseValidationError(
                "ScriptEngineResponse did not contain Export job was successfully removed"
                "Response was {0}".format(','.join(output)), response=response)

    @retry(retry_on_exception=lambda e: isinstance(e, (ScriptEngineResponseValidationError, IndexError)),
           wait_fixed=10000, stop_max_attempt_number=3)
    def _get_job_status_table(self):
        """
        Execute the script engine command to get the CMExport status and return the table output of the job status

        :raises ScriptEngineResponseValidationError: if error executing script engine command
        :raises IndexError: if error retrieving the job status table from the response output
        :return: job status table
        :rtype: enmscripting.common.element.ElementGroup
        """

        status_command = self.EXPORT_STATUS_CMD.format(job_id=self.job_id)
        try:
            response = self.user.enm_execute(command=status_command, on_terminal=False)
        except Exception as e:
            raise ScriptEngineResponseValidationError(
                "Error occurred executing the script engine command {0}".format(status_command), e)

        output = response.get_output()
        try:
            job_status_table = output.groups()[0][0]
        except IndexError:
            raise IndexError("Index Error occurred retrieving the Job Status Table - output: {0}".format(output))

        log.logger.debug("Job Status Table: {0}".format(job_status_table))

        return job_status_table

    def validate(self):
        """
        Validates the status of the CMExport job. If the status of the job is FAILED or ERROR, raise an
        EnmApplicationError. If the job is COMPLETED, it can be completed successfully or completed
        with nodes missing. Once completed, verify that the XML file exists.

        :raises EnmApplicationError: if export command failed or if job id is not set
        :raises TimeOutError: if export status command timed out
        """

        if not self.job_id:
            raise EnmApplicationError("Job id not set, cannot verify job.")
        timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=self.verify_timeout)
        log.logger.debug(
            "Waiting for the job to become complete. Maximum wait time is {0} seconds".format(str(self.verify_timeout)))

        while datetime.datetime.now() < timeout_time:
            try:
                job_status_table = self._get_job_status_table()
            except Exception as e:
                raise EnmApplicationError("Exception occurred retrieving the job status {0}".format(e))

            job_status = self._extract_table_value(job_status_table, "Status")
            if any([status in job_status for status in [u'FAILED', u'ERROR']]):
                raise EnmApplicationError(
                    "Job ID {0} returned status {1}. {2} of {3} nodes exported. "
                    "Check profile logs for full export status output.".format(
                        self.job_id, job_status, self._extract_table_value(job_status_table, "Nodes exported"),
                        self._extract_table_value(job_status_table, 'Expected nodes exported')))
            elif u'COMPLETED' in job_status:
                if job_status == u'COMPLETED':
                    log.logger.debug("Job ID {0} has completed successfully".format(self.job_id))
                else:
                    log.logger.debug(
                        "Job ID {0} has completed with nodes missing. Status: '{1}'.".format(self.job_id, job_status))
                xml_path = self._extract_table_value(job_status_table, "File name")
                log.logger.debug("CMExport is verified , XML file {0} exists ".format(xml_path))
                break

            log.logger.debug("Job has not yet finished, profile will re-check the job status in {0} seconds".format(
                self.polling_interval))
            time.sleep(self.polling_interval)
        else:
            response = self.user.enm_execute(command=self.EXPORT_STATUS_CMD.format(
                job_id=self.job_id), on_terminal=False)
            log.logger.debug("Last job Status table before timeout: {0}".format(response.get_output()))
            raise TimeOutError("Job ID {0} timed out after {1} while trying to validate export success.".format(
                self.job_id, str(self.verify_timeout)))

    @staticmethod
    def _extract_table_value(job_status_table, column_name):
        """
        Validates that xml file generated as a part of this export is a valid xml

        :type job_status_table: ElementGroup
        :param job_status_table: ElementGrop object to extract table data from
        :type column_name: str
        :param column_name: Column name you want to extract the
        :rtype: str
        :return: str
        """
        return job_status_table.find_by_label(column_name)[0].value()


class CmExport(Export):
    CM_EXPORT_CMD = "cmedit export -n {nodes_list} --filetype {file_type} {options}"
    CM_EXPORT_PREDEFINED_FILTER_OPTION = " --filtername {filter}"
    CM_EXPORT_BATCH_FILTER_OPTION = " --batchfilter {batch_filter}"
    CM_EXPORT_CONFIG_OPTION = " --source {config_name}"
    CM_EXPORT_FILE_IN = "-f file:{file_in}"
    CM_EXPORT_NAME_OPTION = " -jn {name}"
    CM_EXPORT_FILE_COMPRESSION_OPTION = " --filecompression {}"

    def __init__(self, *args, **kwargs):
        """
        CM_Export constructor

        filter=None, config_name=None
        :param args: The positional arguments to pass to the cmexport
        :param kwargs: The keyword arguments to pass to the cmexport
        """

        self.file_type = kwargs.pop('filetype', "3GPP")
        self.filter = kwargs.pop('filter', None)
        self.config_name = kwargs.pop('config_name', None)
        self.file_in = kwargs.pop('file_in', None)
        self.user_filter = kwargs.pop('user_filter', None)
        self.interface = kwargs.pop('interface', None)
        self.ne_types = kwargs.pop('ne_types', None)
        self.batch_filter = kwargs.pop('batch_filter', None)
        self.file_compression = kwargs.pop("file_compression", None)
        super(CmExport, self).__init__(*args, **kwargs)

    def _create(self):
        """
        Wrapper function for create function which performs the export
        """

        try:
            if self.interface:
                nbi_job_name = self.name
                log.logger.debug("Exporting {0} via NBI".format(nbi_job_name))
                self.create_over_nbi(job_name=nbi_job_name)
            else:
                log.logger.debug("Exporting via CLI")
                self.create()
        except Exception as e:
            log.logger.debug("ERROR during export {0}.".format(e.message))
            raise

        log.logger.debug("Successfully completed export {0}".format(self.job_id))

    def _validate(self):
        """Wrapper function for function to validate the export"""

        try:
            if self.interface:
                log.logger.debug("Validating export job via NBI")
                self.validate_over_nbi()
            else:
                self.validate()
        except Exception as e:
            log.logger.debug("ERROR during validation of export {0}.".format(e.message))
            raise

        log.logger.debug("Successfully completed validation of {0}".format(self.job_id))

    def construct_export_command(self):
        """
        Construct the command to be sent to the CmExport service

        :return: CmExport command string
        :rtype: str
        """
        export_options = self.CM_EXPORT_PREDEFINED_FILTER_OPTION.format(
            filter=self.filter.upper()) if self.filter else ""
        export_options += self.CM_EXPORT_CONFIG_OPTION.format(config_name=self.config_name) if self.config_name else ""
        export_options += self.CM_EXPORT_NAME_OPTION.format(name=self.name) if self.name else ""
        export_options += (self.CM_EXPORT_FILE_COMPRESSION_OPTION.format(self.file_compression) if
                           self.file_compression else "")
        export_options += self.CM_EXPORT_BATCH_FILTER_OPTION.format(batch_filter=self.batch_filter) if \
            self.batch_filter else ""

        if self.ne_types:
            command = self.CM_EXPORT_CMD.replace("-n {nodes_list}", "--netype {ne_types}").format(
                ne_types=";".join(self.ne_types), file_type=self.file_type,
                options=export_options)
        else:
            command = self.CM_EXPORT_CMD.format(nodes_list=";".join(self.node_names), file_type=self.file_type,
                                                options=export_options)
        return command

    @retry(retry_on_exception=lambda e: isinstance(e, (RuntimeError, SessionTimeoutException)), wait_fixed=5000,
           stop_max_attempt_number=3)
    def create(self):
        """
        Performs a cm export.
        """

        response = self.user.enm_execute(command=self.construct_export_command(), file_in=self.file_in)
        output = response.get_output()

        log.logger.debug(
            'Script engine response for export create command for "{0}" is "{1}"'.format(
                self.name, ','.join(output)))

        if not output or "job ID" not in output[0]:
            if "Error 8029 : License FAT1023443" in ','.join(output):
                common_utils.install_licence(user=self.user, licence_file_name=self.DYNAMIC_EXPORT_LICENCE)
                raise RuntimeError("License FAT1023443 is not available on the system.")
            else:
                raise ScriptEngineResponseValidationError(
                    "ScriptEngineResponse did not contain job ID for CM EXPORT. "
                    "Response was {0}".format(','.join(output)), response=response)

        self.job_id = re.search(r"ID\s(\d+)", output[0]).groups()[0]

    def create_over_nbi(self, job_name="export_name"):
        """
        Performs a cm export over the NBI

        :type job_name: string
        :param job_name: NBI Export job name
        :raises EnmApplicationError: when invalid job id e.g. None is returned from CM NBI json response
        """
        if "CMEXPORT_19" in job_name:
            log.logger.debug("started to read the body for job")
            body = {"jobName": job_name,
                    "type": "EXPORT",
                    "fileFormat": "3GPP",
                    "nodeSearchCriteria": {
                        "nodeSearchScopes": [{"scopeType": "UNSPECIFIED",
                                              "matchCondition": "NO_MATCH_REQUIRED"}]},
                    "enumTranslate": "false",
                    "compressionType": "GZIP"}
        else:
            body = {
                "type": "EXPORT",
                "jobName": job_name,
                "configName": self.config_name or "Live",
                "fileFormat": self.file_type
            }
        if self.user_filter:
            log.logger.debug("started to read the body for job")
            body.update({"userFilter": {"value": self.user_filter}})
        if self.nodes or self.ne_types or (self.node_regex and self.node_regex != '*'):
            log.logger.debug("started to read the body for job")
            search_criteria = self.set_nbi_search_criteria()
            body.update({"nodeSearchCriteria": {"nodeSearchScopes": search_criteria}})
        if self.filter:
            log.logger.debug("started to read the body for job")
            body.update({"exportFilter": {
                "namespace": "PredefinedExportFilter",
                "name": self.filter,
                "version": "1.0.0"}})
        response = self.user.post(CREATE_EXPORT_ENDPOINT, json=body, headers=headers.SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not create export: ")
        if not response or not response.text:
            raise EnmApplicationError("ENM service failed to return a valid response, "
                                      "unable to determine export status.")
        try:
            self.job_id = response.json().get('id')
        except (ValueError, TypeError):
            raise EnmApplicationError("Invalid job id: {0} has been retrieved from CM NBI json response: {1}."
                                      .format(self.job_id, response.txt))

    def set_nbi_search_criteria(self):
        """
        Sets search criteria of the NBI export job

        :return: List of node or regex matching scopes
        :rtype: list
        """
        search_criteria = []
        if self.node_regex and self.node_regex != '*':
            for pattern in self.node_regex.split(';'):
                search_criteria.append({"scopeType": "NODE_NAME", "matchCondition": "CONTAINS",
                                        "value": pattern.replace('*', '')})
        elif self.nodes:
            for node in self.nodes:
                search_criteria.append({"scopeType": "NODE_NAME", "matchCondition": "EQUALS", "value": node.node_id})
        else:
            for ne_type in self.ne_types:
                search_criteria.append({"scopeType": "UNSPECIFIED", "matchCondition": "NO_MATCH_REQUIRED",
                                        "neType": ne_type})
        return search_criteria

    def get_export_report_by_id(self):
        """
        Get the export report by the id
        :raises EnmApplicationError: when job id is invalid
        :rtype: dict
        :return: Response object dictionary
        """
        if not self.job_id or not isinstance(self.job_id, int):
            raise EnmApplicationError("Invalid job id returned from CM NBI: {0}".format(self.job_id))
        response = self.user.get(GET_REPORT_ENPOINT.format(id=self.job_id), headers=headers.SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not create export: ")
        return response.json()

    def get_export_job_by_id(self):
        """
        Get the export job details by the id

        :raises EnmApplicationError: when job id is invalid

        :rtype: dict
        :return: Response object dictionary
        """
        if not self.job_id or not isinstance(self.job_id, int):
            raise EnmApplicationError("Invalid job id returned by CM NBI: {0}".format(self.job_id))
        response = self.user.get(GET_EXPORT_ENDPOINT.format(id=self.job_id), headers=headers.SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not retrieve export by id: ")
        return response.json()

    def validate_over_nbi(self):
        if not self.job_id or not isinstance(self.job_id, int):
            raise EnmApplicationError("Invalid job id returned in response from CM NBI: {0}".format(self.job_id))
        timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=self.verify_timeout)

        log.logger.debug(
            'Waiting for the job to become complete. Maximum wait time is {0} seconds'.format(str(self.verify_timeout)))
        # Wait for export to complete
        while datetime.datetime.now() < timeout_time:
            job_json = self.get_export_job_by_id()
            if job_json.get('status') == 'STARTED':
                time.sleep(self.polling_interval)
                continue
            else:
                if job_json.get('status') in ['FAILED', 'ERROR']:
                    log.logger.debug("Job Status: {0}".format(job_json))
                    raise EnmApplicationError('Job ID "{0}" returned status "{1}".{2} of {3} nodes exported. Check '
                                              'profile logs for full export status output.'
                                              .format(self.job_id, job_json.get('status'),
                                                      job_json.get('nodesExported'),
                                                      job_json.get('expectedNodesExported')))
                else:
                    log.logger.debug('Job ID "{0}" returned status "{1}".Nodes export: {2} of {3}, Nodes not exported: '
                                     '{4}, Nodes not found: {5}.'
                                     .format(self.job_id, job_json.get('status'), job_json.get('nodesExported'),
                                             job_json.get('expectedNodesExported'), job_json.get('nodesNotExported'),
                                             job_json.get('nodesNoMatchFound')))
            report_json = self.get_export_report_by_id()
            if report_json.get('noMatchFoundResult'):
                log.logger.debug("Export job report location: {0}"
                                 .format(report_json.get('_links').get('self').get('href')))
            break


class ShmExport(Export):
    SHM_EXPORT_CMD = "shm export {options}"
    SHM_EXPORT_NODES_OPTION = " -n {nodes_list}"
    SHM_EXPORT_NAME_OPTION = " -jn {name}"
    SHM_EXPORT_TYPE = " -{export_type}"
    SHM_SAVED_SEARCH = " --savedsearch {name}"

    def __init__(self, export_type="", saved_search_name=None, *args, **kwargs):
        """
        SHM_Export constructor

        :param export_type: Type of export to be performed, software,hardware,licence
        :type export_type: str
        :param saved_search_name: Name of the saved search query to be used
        :type saved_search_name: str
        :param args: Optional positional arguments
        :type args: list
        :param kwargs: Keyword positional arguments
        :type kwargs: dict
        """

        super(ShmExport, self).__init__(*args, **kwargs)
        self.export_type = export_type
        self.saved_search_name = saved_search_name

    def create(self):
        """
        Performs a shm export.
        :raises ScriptEngineResponseValidationError: when job id is not in response output
        """

        export_options = self.SHM_EXPORT_NODES_OPTION.format(nodes_list=";".join(self.node_names)) if self.nodes else ""
        export_options += self.SHM_EXPORT_NAME_OPTION.format(name=self.name) if self.name else ""
        export_options += self.SHM_SAVED_SEARCH.format(name=self.saved_search_name) if self.saved_search_name else ""
        export_options += self.SHM_EXPORT_TYPE.format(export_type=self.export_type) if self.export_type else ""

        response = self.user.enm_execute(command=self.SHM_EXPORT_CMD.format(options=export_options))

        output = response.get_output()
        join_output = ','.join(output)

        log.logger.debug(
            'Script engine response for export create command for {0} is {1}'.format(self.name, join_output))

        if not output or "job ID" not in join_output:
            raise ScriptEngineResponseValidationError(
                "ScriptEngineResponse did not contain job ID for SHM EXPORT.\n"
                "Response was {0}".format(join_output), response=response)

        self.job_id = re.search(r"ID\s(\d+)", join_output).groups()[0]
