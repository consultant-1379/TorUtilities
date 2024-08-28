from itertools import cycle
from enmutils.lib import log

from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.cm_import import CmImportUpdateLive, get_different_nodes
from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class CmImport08Flow(CmImportFlowProfile, GenericFlow):

    IMPORT = cycle(['CHANGES', 'DEFAULTS'])

    @staticmethod
    def calculate_num_imports_in_parallel(num_nodes):
        """
        Calculate the number of imports to be carried out in parallel. The total nodes for this profile is 50, and the
        import jobs are using 5 nodes at a time so we should have 10 import jobs. However, if there are less than 50
        nodes allocated to the profile we need to run the profile with a reduced number of imports.

        :param num_nodes: Number of nodes assigned to the profile
        :type num_nodes: int
        :return: the number of imports
        :rtype: int
        """

        num_imports_in_parallel = num_nodes / 5
        log.logger.debug(
            'The number of imports to perform in parallel based on the number of nodes allocated to the profile: {0}'
            .format(num_imports_in_parallel))

        return num_imports_in_parallel

    def create_reset_job_and_set_default_values(self, user, nodes, expected_num_mo_changes):
        """
        Create the import job that will reset the MO values to the default userLabel, and then carry out that import job
        to ensure the MO userLabels are at their default values

        :param user: user to carry out the import
        :type user: enmutils.lib.enm_user_2.User
        :param nodes: list of nodes
        :type nodes: list
        :param expected_num_mo_changes: the number of MO changes expected to be carried out by the import job
        :type expected_num_mo_changes: int
        :return: method to carry out the reset import job
        :rtype: enmutils.lib.persistence.picklable_boundmethod
        """

        cmimport_08_reset = CmImportUpdateLive(
            name='cmimport_08_reset',
            user=user,
            nodes=nodes,
            mos={'UtranFreqRelation': ('userLabel', 'cmimport_08_default'),
                 'EUtranFreqRelation': ('userLabel', 'cmimport_08_default')},
            template_name='cmimport_08_reset.txt',
            flow='live_config',
            file_type=self.FILETYPE,
            expected_num_mo_changes=expected_num_mo_changes,
            timeout=self.TIMEOUT
        )

        cmimport_08_reset.prepare_dynamic_file()
        self.teardown_list.append(picklable_boundmethod(cmimport_08_reset.delete))
        reset_values = picklable_boundmethod(cmimport_08_reset.create)

        try:
            cmimport_08_reset.create()
        except Exception as e:
            self.add_error_as_exception(e)

        return reset_values

    def create_import_jobs(self, nodes, expected_num_mo_changes, users):
        """
        Create a list of the default import jobs, and a list of the modified ('changes') import jobs

        :param nodes: list of nodes
        :type nodes: list
        :param expected_num_mo_changes: the number of MO changes expected to be carried out by the import job
        :type expected_num_mo_changes: int
        :param users: List of users for each import job.
        :type users: list
        :return: two lists, a list of the default import jobs and a list of modified import jobs
        :rtype: list
        """

        nodes = get_different_nodes(nodes, 5)
        import_changes_jobs = []
        import_default_jobs = []

        for i, user in enumerate(users):
            modified_label = 'cmimport_08_{0}'.format(i)
            nodes_subset = next(nodes)

            cmimport_changes = CmImportUpdateLive(
                name='cmimport_08_changes',
                user=user,
                nodes=nodes_subset,
                mos={'UtranFreqRelation': ('userLabel', modified_label),
                     'EUtranFreqRelation': ('userLabel', modified_label)},
                template_name='cmimport_08_userLabel_changes_{i}.txt'.format(i=i),
                flow='live_config',
                file_type=self.FILETYPE,
                expected_num_mo_changes=expected_num_mo_changes,
                timeout=self.TIMEOUT

            )

            import_changes_jobs.append(cmimport_changes)
            cmimport_changes.prepare_dynamic_file()
            self.teardown_list.append(picklable_boundmethod(cmimport_changes.delete))

            cmimport_default = CmImportUpdateLive(
                name='cmimport_08_default',
                user=user,
                nodes=nodes_subset,
                mos={'UtranFreqRelation': ('userLabel', 'cmimport_08_default'),
                     'EUtranFreqRelation': ('userLabel', 'cmimport_08_default')},
                template_name='cmimport_08_userLabel_default_{i}.txt'.format(i=i),
                flow='live_config',
                file_type=self.FILETYPE,
                expected_num_mo_changes=expected_num_mo_changes,
                timeout=self.TIMEOUT

            )

            import_default_jobs.append(cmimport_default)
            cmimport_default.prepare_dynamic_file()
            self.teardown_list.append(picklable_boundmethod(cmimport_default.delete))

        return import_changes_jobs, import_default_jobs

    @staticmethod
    def import_func(imp):
        """
        Executes the import of updates to a live ENM system. This function is passed to the 'func_ref' parameter in
        the thread queue below for each parallel execution.
        """
        imp._create()

    def execute_flow(self):
        """
        Execute the flow for cmimport_08
        """
        nodes = self.nodes_list
        num_imports = self.calculate_num_imports_in_parallel(len(nodes))
        users = self.create_users(num_imports + 1, roles=self.USER_ROLES, fail_fast=False, retry=True)

        cmimport_setup_object = self.setup_flow(user=users[0], nodes=nodes)
        user = cmimport_setup_object.user
        expected_num_mo_changes = cmimport_setup_object.expected_num_mo_changes
        reset_values = self.create_reset_job_and_set_default_values(user, nodes, expected_num_mo_changes)
        import_changes_jobs, import_default_jobs = self.create_import_jobs(nodes, expected_num_mo_changes, users[1:])

        self.state = 'RUNNING'
        while self.keep_running():
            self.sleep_until_time()
            import_type = self.IMPORT.next()
            imports_list = import_changes_jobs if import_type == 'CHANGES' else import_default_jobs
            self.create_and_execute_threads(workers=imports_list, thread_count=len(imports_list),
                                            func_ref=self.import_func, wait=60 * 25, join=60 * 25)

            if import_type == 'CHANGES' and reset_values:
                self.teardown_list.append(reset_values)
                reset_values = None
