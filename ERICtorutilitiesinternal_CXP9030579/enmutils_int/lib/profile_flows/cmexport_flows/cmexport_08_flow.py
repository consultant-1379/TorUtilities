import random

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.enm_export import create_and_validate_cm_export_over_nbi, CmExport
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class CmExport08(GenericFlow):

    def create_export_object(self, user, three_cell_nodes):
        """
        Create a list of CMExport objects. Each export object will have one random 3 cell node.

        :param user: user to create the CMExport objects
        :type user: `enm_user_2.User`
        :param three_cell_nodes: list of nodes that have three cells
        :type three_cell_nodes: list

        :return: list of CMExport objects
        :rtype: list
        """
        cm_exports = []
        log.logger.debug("Creating {} export objects".format(self.NUMBER_OF_EXPORTS))
        for i in range(self.NUMBER_OF_EXPORTS):
            cm_export = CmExport(name="EXPORT_{0}".format(i + 1), user=user,
                                 nodes=random.sample(three_cell_nodes, 1), filetype=self.FILETYPE)
            cm_exports.append(cm_export)

        return cm_exports

    def execute_flow(self):
        """
        Executes the flow of the cmexport_08 profile
        """
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_time()
            three_cell_nodes = []
            try:
                log.logger.debug("Attempting to get nodes with {0} cells".format(self.NUMBER_OF_CELLS))
                three_cell_nodes = self.get_nodes_with_required_number_of_cells()
                log.logger.debug("Successfully obtained {0} cell nodes".format(self.NUMBER_OF_CELLS))
            except Exception as e:
                self.add_error_as_exception(e)

            if three_cell_nodes:
                log.logger.debug("Starting export threads for {0}".format(self.NAME))
                cm_export_object = self.create_export_object(user, three_cell_nodes)
                self.create_and_execute_threads(workers=cm_export_object, thread_count=self.NUMBER_OF_EXPORTS,
                                                func_ref=create_and_validate_cm_export_over_nbi, args=[self])
            else:
                self.add_error_as_exception(EnvironError('No three cell nodes found.'))
            self.exchange_nodes()
