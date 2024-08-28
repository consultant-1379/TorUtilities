import random
from itertools import cycle
from collections import Iterator
from functools import partial

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import common_utils
from enmutils_int.lib.enm_export import CmExport, create_and_validate_cm_export_over_nbi
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.helper_methods import generate_basic_dictionary_from_list_of_objects
from enmutils_int.lib.services.deploymentinfomanager_adaptor import update_pib_parameter_on_enm
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm


class CmExportFlow(GenericFlow):

    def execute_flow(self):
        """
        Executes the main profile flow
        """

        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        allocated_nodes = self.get_nodes_list_by_attribute()
        nodes = allocated_nodes if allocated_nodes else None

        file_type = self.FILETYPE
        if isinstance(file_type, list):
            file_type = cycle(self.FILETYPE)

        if hasattr(self, "MAX_RETENTION_TIME"):
            existing_schedule_cleanup_export, existing_schedule_cleanup_export_time = self.get_existing_pib_values()
            self.set_pib_parameters_to_required_values()
            self.teardown_list.append(partial(picklable_boundmethod(self.reset_pib_parameters), existing_schedule_cleanup_export, existing_schedule_cleanup_export_time))

        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            exports = self.create_export_objects(user, nodes, file_type)
            created_exports = self.create_exports(exports)
            self.validate_exports(created_exports)

    @staticmethod
    def get_existing_pib_values():
        """
        Get the existing pib parameter values

        :return: existing pib parameter values
        :rtype: tuple
        """
        existing_schedule_cleanup_export = get_pib_value_on_enm(enm_service_name="impexpserv",
                                                                pib_parameter_name="scheduledCleanupExportEnabled")
        existing_schedule_cleanup_export_time = get_pib_value_on_enm(enm_service_name="impexpserv",
                                                                     pib_parameter_name="scheduledCleanupExportTime")
        return existing_schedule_cleanup_export, existing_schedule_cleanup_export_time

    def update_pib_values(self, schedule_cleanup_export, schedule_cleanup_export_time):
        """"
        Update the pib parameter values

        :param schedule_cleanup_export: parameter value that is to be updated in the pib parameter
        :type schedule_cleanup_export: str
        :param schedule_cleanup_export_time: parameter value that is to be updated in the pib parameter
        :type schedule_cleanup_export_time: str
        """

        try:
            update_pib_parameter_on_enm(enm_service_name="impexpserv",
                                        pib_parameter_name="scheduledCleanupExportEnabled",
                                        pib_parameter_value=schedule_cleanup_export)
        except Exception as e:
            self.add_error_as_exception(e)
        try:
            update_pib_parameter_on_enm(enm_service_name="impexpserv",
                                        pib_parameter_name="scheduledCleanupExportTime",
                                        pib_parameter_value=schedule_cleanup_export_time)
        except Exception as e:
            self.add_error_as_exception(e)

    def set_pib_parameters_to_required_values(self):
        """
        Update the  pib parameter values to the required values
        """
        self.update_pib_values(schedule_cleanup_export=self.RETENTION_ENABLED,
                               schedule_cleanup_export_time=self.MAX_RETENTION_TIME)

    def reset_pib_parameters(self, existing_schedule_cleanup_export, existing_schedule_cleanup_export_time):
        """
        Update the  pib parameter values to the existing values

        :param existing_schedule_cleanup_export: existing parameter value of the pib parameter
        :type existing_schedule_cleanup_export: str
        :param existing_schedule_cleanup_export_time: existing parameter value of the pib parameter
        :type existing_schedule_cleanup_export_time: str
        """
        self.update_pib_values(schedule_cleanup_export=existing_schedule_cleanup_export,
                               schedule_cleanup_export_time=existing_schedule_cleanup_export_time)

    def create_export_objects(self, user, nodes, file_type, num_of_exports=1, verify_timeout=90 * 60):
        """
        Create the export object(s) required

        :param user: User who will create the export on ENM
        :type user: `enm_user_2.User`
        :param nodes: List of node(s) to be exported
        :type nodes: list
        :param file_type: type of file to be exported (3GPP or dynamic), or iterator object if both file types
                        are to be used in turn
        :type file_type: iterator or str
        :param num_of_exports: Integer
        :type num_of_exports: int
        :param verify_timeout: Timeout limit for validating the export
        :type verify_timeout: int

        :return: List of `enm_export.CmExport` objects
        :rtype: list
        """
        log.logger.debug("Starting export object instance creation.")
        exports = []
        node_regex = None
        if hasattr(self, "NODE_REGEX"):
            node_regex = self.NODE_REGEX
        user_filter = self.FILTER if hasattr(self, "FILTER") else None
        file_path = (common_utils.get_internal_file_path_for_import("etc", "data", self.FILE_IN) if
                     hasattr(self, "FILE_IN") else None)

        if isinstance(file_type, Iterator):
            file_type = file_type.next()

        interface = self.INTERFACE if hasattr(self, "INTERFACE") else None
        ne_types = self.ENM_NE_TYPES if hasattr(self, "ENM_NE_TYPES") else None
        batch_filter = self.BATCH_FILTER if hasattr(self, "BATCH_FILTER") else None

        for _ in xrange(num_of_exports):
            exports.append(CmExport(user=user, name="{0}_EXPORT".format(self.identifier), nodes=nodes,
                                    verify_timeout=verify_timeout, filetype=file_type, user_filter=user_filter,
                                    file_in=file_path, node_regex=node_regex, interface=interface, ne_types=ne_types,
                                    batch_filter=batch_filter))

        log.logger.debug("Successfully completed export object instance creation.")
        return exports

    def filter_cran_node(self, nodes):
        """
        Deprecated 24.09 and to be Deleted in 25.04 ENMRTD-25426

        """

    def create_exports(self, exports):
        """
        Create the export(s) job on ENM

        :param exports: List of CmExports to be created
        :type exports: list

        :returns: List of `enm_export.CmExport` objects
        :rtype: list
        """
        log.logger.debug("Starting export creation.")
        created_exports = []
        for export in exports:
            try:
                export._create()
                created_exports.append(export)
            except Exception as e:
                self.add_error_as_exception(e)
        if len(created_exports) != len(exports):
            log.logger.debug("Not all exports created successfully, please check the logs for more information.")
        log.logger.debug("Successfully created {0}/{1} export(s).".format(len(created_exports), len(exports)))
        return created_exports

    def validate_exports(self, exports):
        """
        Validate the export(s) job on ENM

        :param exports: List of CmExports to be validated
        :type exports: list
        """
        log.logger.debug("Starting export validation.")
        for export in exports:
            try:
                export._validate()
            except Exception as e:
                self.add_error_as_exception(e)
        log.logger.debug("Successfully completed export validation.")

    def execute_parallel_flow(self):
        """
        Executes the flow for exports to be run in parallel
        """
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        self.state = "RUNNING"

        while self.keep_running():
            self.sleep_until_time()
            cm_exports = []
            node_lists = self.generate_node_list_for_exports()
            if len(node_lists) < self.NUMBER_OF_EXPORTS:
                self.add_error_as_exception(EnmApplicationError("Unable to fulfil requirement of {0} cm exports of "
                                                                "various sizes".format(self.NUMBER_OF_EXPORTS)))
            else:
                for i in xrange(min([len(users), len(node_lists)])):
                    cm_export = CmExport(name="EXPORT_{0}".format(i), user=users[i], nodes=node_lists[i],
                                         filetype=self.FILETYPE)
                    cm_exports.append(cm_export)

                self.create_and_execute_threads(cm_exports, self.NUMBER_OF_EXPORTS,
                                                func_ref=create_and_validate_cm_export_over_nbi,
                                                join=self.THREAD_QUEUE_TIMEOUT,
                                                wait=self.THREAD_QUEUE_TIMEOUT, args=[self])

    def generate_node_list_for_exports(self):
        """
        Generates list of list of nodes from available nodes
        :rtype: list
        :return: List  of list of Nodes
        """
        node_lists = []

        nodes_dict = generate_basic_dictionary_from_list_of_objects(
            self.get_nodes_list_by_attribute(node_attributes=["node_id", "primary_type"]), "primary_type")
        for node_type, nodes in nodes_dict.items():
            number_nodes_available = len(nodes)
            while number_nodes_available > 0:
                number_of_nodes_per_list = random.randint(8, 90)
                number_nodes_available -= number_of_nodes_per_list
                if number_nodes_available < 0:
                    log.logger.debug("No more {0} nodes to fulfil requirement".format(node_type))
                    break

                node_lists.append(random.sample(nodes, number_of_nodes_per_list))
                if len(node_lists) >= self.NUMBER_OF_EXPORTS:
                    log.logger.debug("Successfully created {0} lists of nodes.".format(self.NUMBER_OF_EXPORTS))
                    return node_lists

        return node_lists
