import datetime
from enmutils_int.lib.enm_export import CmExport, create_and_validate_cm_export
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class CmExport02(GenericFlow):

    def create_export_objects(self, users):
        """
        Create a list of CMExport objects. Create a total of 3 CMExport objects - the first two CmExport objects
        will be full network exports, and the third will be an export with a specified number of nodes.

        :param users: users to create the CMExport objects
        :type users: list
        :return: list of CMExport objects
        :rtype: list
        """

        file_type = self.FILETYPE[0] if datetime.date.today().strftime('%A') == 'Monday' else self.FILETYPE[1]
        cm_exports = []
        for i in xrange(self.NUMBER_OF_NETWORK_EXPORTS):
            cm_export = CmExport(name="{0}_FULL_NETWORK_EXPORT_{1}".format(self.identifier, i + 1), user=users[i],
                                 verify_timeout=self.VALIDATION_TIMEOUT, filetype=file_type,
                                 file_compression=self.FILE_COMPRESSION)
            cm_exports.append(cm_export)

        nodes = [node for node in self.get_nodes_list_by_attribute(node_attributes=['node_id', 'primary_type']) if
                 node.primary_type == self.SMALL_EXPORT_PRIMARY_TYPE]
        cm_export_specified_num_nodes = CmExport(name="{0}_EXPORT".format(self.identifier),
                                                 user=users[2], nodes=nodes[:self.NUM_NODES_FOR_EXPORT],
                                                 verify_timeout=self.VALIDATION_TIMEOUT, filetype=file_type,
                                                 file_compression=self.FILE_COMPRESSION)
        cm_exports.append(cm_export_specified_num_nodes)

        return cm_exports

    def execute_flow(self):
        """
        Executes the flow of the cmexport_02 profile
        """

        users = self.create_profile_users(1, self.ADMIN_ROLE) + self.create_profile_users(2, self.OPERATOR_ROLE)
        self.state = "RUNNING"

        while self.keep_running():
            self.sleep_until_day()
            cm_export_objects = self.create_export_objects(users)
            self.create_and_execute_threads(workers=cm_export_objects, thread_count=self.NUMBER_OF_EXPORTS,
                                            func_ref=create_and_validate_cm_export, args=[self],
                                            join=self.THREAD_QUEUE_TIMEOUT, wait=self.THREAD_QUEUE_TIMEOUT + 300)
