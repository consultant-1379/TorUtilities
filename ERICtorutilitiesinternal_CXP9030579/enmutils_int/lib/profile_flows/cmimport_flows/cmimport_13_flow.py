import datetime
import time
from itertools import cycle
from functools import partial

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.cm_import import CmImportUpdateLive
from enmutils_int.lib.enm_deployment import fetch_pib_parameter_value
from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile
from enmutils_int.lib.services.deploymentinfomanager_adaptor import update_pib_parameter_on_enm


class CmImport13Flow(CmImportFlowProfile):
    IMPORT = cycle(['CHANGES', 'DEFAULTS'])
    ITERATION_TIMEOUT = 30 * 60

    def set_default_values(self, nodes, user, expected_num_mo_changes):
        """
        Ensure the MO attributes are set to their default values

        :param nodes:list of nodes
        :type nodes: list
        :param user: user to carry out the import
        :type user: enmutils.lib.enm_user_2.User
        :param expected_num_mo_changes: the number of MO changes expected to be carried out by the import job
        :type expected_num_mo_changes: int

        """
        log.logger.debug('Attempting to set MOs to their default values.')

        cm_import_13_reset = CmImportUpdateLive(
            name='cmimport_13_reset',
            mos=self.MOS_DEFAULT,
            nodes=nodes,
            user=user,
            template_name='cmimport_13_reset.xml',
            flow='live_config',
            file_type=self.FILETYPE,
            interface='NBIv2',
            expected_num_mo_changes=expected_num_mo_changes,
            timeout=self.TIMEOUT
        )

        cm_import_13_reset.prepare_xml_file()
        self.teardown_list.append(picklable_boundmethod(cm_import_13_reset.create_over_nbi))

        try:
            cm_import_13_reset.create_over_nbi()
        except Exception as e:
            self.add_error_as_exception(e)

    def prepare_import_files(self, nodes, user, expected_num_mo_changes):
        """
        Create the import file for each node and add to an import jobs list

        :param nodes: list of nodes
        :type nodes: list
        :param user: user to carry out the import
        :type user: enmutils.lib.enm_user_2.User
        :param expected_num_mo_changes: the number of MO changes expected to be carried out by the import job
        :type expected_num_mo_changes: int
        :return: two lists, a list of the default import jobs and a list of modified import jobs
        :rtype: list
        """

        count = 0
        import_default_jobs = []
        import_changes_jobs = []

        for node in nodes:
            cm_import_13_default = CmImportUpdateLive(
                name='cmimport_13_default_{0}'.format(count),
                mos=self.MOS_DEFAULT,
                nodes=[node],
                user=user,
                template_name='cmimport_13_default_{0}.xml'.format(count),
                flow='live_config',
                file_type=self.FILETYPE,
                interface='NBIv2',
                expected_num_mo_changes=expected_num_mo_changes,
                timeout=self.TIMEOUT
            )

            import_default_jobs.append(cm_import_13_default)
            cm_import_13_default.prepare_xml_file()
            self.teardown_list.append(picklable_boundmethod(cm_import_13_default.delete))

            cm_import_13_changes = CmImportUpdateLive(
                name='cmimport_13_changes_{0}'.format(count),
                mos=self.MOS_MODIFY,
                nodes=[node],
                user=user,
                template_name='cmimport_13_changes_{0}.xml'.format(count),
                flow='live_config',
                file_type=self.FILETYPE,
                interface='NBIv2',
                expected_num_mo_changes=expected_num_mo_changes,
                timeout=self.TIMEOUT
            )

            import_changes_jobs.append(cm_import_13_changes)
            cm_import_13_changes.prepare_xml_file()
            self.teardown_list.append(picklable_boundmethod(cm_import_13_changes.delete))
            count += 1

        return import_default_jobs, import_changes_jobs

    def prepare_import_lists(self, import_default_jobs, import_changes_jobs, job_count, import_error_list,
                             expected_job_count=100):
        """
        Imports the lists of default and modified import files
        :param import_default_jobs: list of the default imports
        :type import_default_jobs: list
        :param import_changes_jobs: list of modified imports
        :type import_changes_jobs: list
        :param import_error_list: list of errors during imports
        :type import_error_list: list
        :param job_count: The initial job_count
        :type job_count: int
        :param expected_job_count: Expected total number of import jobs to be created
        :type expected_job_count: int

        :return: Number of Import Jobs created and List of Errors occured during creation of jobs
        :rtype: tuple
        """
        if job_count <= expected_job_count:
            import_type = self.IMPORT.next()
            imports_list = import_changes_jobs if import_type == 'CHANGES' else import_default_jobs
            job_count, import_error_list = self.create_list_of_imports(imports_list, job_count, import_error_list)
        return job_count, import_error_list

    def import_lists(self, nodes, user, expected_num_mo_changes, import_default_jobs, import_changes_jobs,
                     expected_job_count=100):
        """
        Imports the lists of default and modified import files

        :param nodes: list of nodes
        :type nodes: list
        :param user: user to carry out the import
        :type user: enmutils.lib.enm_user_2.User
        :param expected_num_mo_changes: the number of MO changes expected to be carried out by the import job
        :type expected_num_mo_changes: int
        :param import_default_jobs: list of the default imports
        :type import_default_jobs: list
        :param import_changes_jobs: list of modified imports
        :type import_changes_jobs: list
        :param expected_job_count: Expected total number of import jobs to be created
        :type expected_job_count: int
        """

        import_error_list = []
        job_count = 1
        if hasattr(self, "SCHEDULED_TIMES_STRINGS"):
            timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=self.ITERATION_TIMEOUT)
            while datetime.datetime.now() < timeout_time:
                job_count, import_error_list = self.prepare_import_lists(import_default_jobs, import_changes_jobs,
                                                                         job_count, import_error_list,
                                                                         expected_job_count=100)

            if job_count < expected_job_count:
                timeout_error = EnmApplicationError(
                    '{0} minute iteration has timed out before all jobs were successfully imported: {1} jobs completed '
                    'out of 100'.format(self.ITERATION_TIMEOUT / 60, job_count))
                self.add_error_as_exception(timeout_error)
                import_error_list.append(timeout_error)

            if import_error_list:
                log.logger.debug('{0} Error(s) encountered during iteration'.format(len(import_error_list)))
                log.logger.debug(
                    'Errors have occurred, therefore we will reset the MOs to their default values, to ensure '
                    'the MOs have the expected values for the beginning of the next iteration.')
                self.set_default_values(nodes, user, expected_num_mo_changes)
        else:
            while job_count <= expected_job_count:
                job_count, import_error_list = self.prepare_import_lists(import_default_jobs, import_changes_jobs,
                                                                         job_count, import_error_list,
                                                                         expected_job_count=100)

            if import_error_list:
                log.logger.debug('{0} Error(s) encountered during iteration'.format(len(import_error_list)))
                log.logger.debug(
                    'Errors have occurred, therefore we will reset the MOs to their default values, to ensure '
                    'the MOs have the expected values for the beginning of the next iteration.')
                self.set_default_values(nodes, user, expected_num_mo_changes)

    def create_list_of_imports(self, imports_list, job_count, import_error_list):
        """
        Create the list of supplied import instances over the NBI

        :param imports_list: List of import instances to be created
        :type imports_list: list
        :param job_count: Counter to track number of created jobs
        :type job_count: int
        :param import_error_list: List of errors encountered while creating the import instances
        :type import_error_list: list

        :return: Tuple containing the updated job count, and the updated import error list
        :rtype: tuple
        """
        for import_job in imports_list:
            try:
                time.sleep(7)
                log.logger.debug('Creating import job {0}, import number {1}/100'.format(import_job.name, job_count))
                job_count += 1
                import_job.create_over_nbi()
                time.sleep(1)
            except Exception as e:
                if isinstance(e, ValueError) and "json" in str(e).lower():
                    e = EnmApplicationError(str(e))
                self.add_error_as_exception(e)
                import_error_list.append(e)
        return job_count, import_error_list

    def execute_flow(self):
        """
        Execute the flow for CMImport_13 profile
        """

        cmimport_setup_object = self.setup_flow()
        user = cmimport_setup_object.user
        nodes = cmimport_setup_object.nodes
        expected_num_mo_changes = cmimport_setup_object.expected_num_mo_changes
        self.set_default_values(nodes, user, expected_num_mo_changes)
        import_default_jobs, import_changes_jobs = self.prepare_import_files(nodes, user, expected_num_mo_changes)
        if hasattr(self, "POSTGRES_RETENTION_TIME_DAYS"):
            existing_schedule_retention_time = fetch_pib_parameter_value(application_service="impexpserv",
                                                                         pib_parameter="bulkCmImport_importJobData"
                                                                                       "RetentionPeriod")
            update_pib_parameter_on_enm(enm_service_name="impexpserv",
                                        pib_parameter_name="bulkCmImport_importJobDataRetentionPeriod",
                                        pib_parameter_value=self.POSTGRES_RETENTION_TIME_DAYS)
            self.teardown_list.append(partial(update_pib_parameter_on_enm,
                                              enm_service_name="impexpserv",
                                              pib_parameter_name="bulkCmImport_importJobDataRetentionPeriod",
                                              pib_parameter_value=existing_schedule_retention_time))

        self.state = 'RUNNING'

        while self.keep_running():
            if hasattr(self, "SCHEDULED_TIMES_STRINGS"):
                self.sleep_until_next_scheduled_iteration()
            try:
                user.open_session(reestablish=True)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))
                continue

            self.import_lists(nodes, user, expected_num_mo_changes, import_default_jobs, import_changes_jobs)
