from random import sample

from requests.exceptions import HTTPError

from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.cellmgt import verify_nodes_on_enm_and_return_mo_cell_fdn_dict
from enmutils_int.lib.cellmgt import view_cell_relations
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class CellViewRelationsFlow(GenericFlow):

    relations_to_view = []
    mo_types = []

    def execute_cell_mgt_11_flow(self):
        """
        Executes the profile flow
        """
        self.state = 'RUNNING'
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        nodes = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'poid'])
        node_fdns = []

        try:
            node_fdns = verify_nodes_on_enm_and_return_mo_cell_fdn_dict(users[0], nodes, self.mo_types)
        except HTTPError:
            self.add_error_as_exception(EnvironError('Node Validation Failed'))
        except Exception as e:
            self.add_error_as_exception(e)

        if node_fdns:
            fdns_to_use = []
            for mo_type in self.mo_types:
                fdns = node_fdns.get(mo_type)
                if fdns:
                    fdns_to_use.extend(fdns)
            cell_per_user = self.NUM_CELLS_PER_USER if len(fdns_to_use) >= self.NUM_CELLS_PER_USER else len(fdns_to_use)
            user_node_data_lte = [(user, sample(fdns_to_use, cell_per_user)) for user in users]
            while self.keep_running():
                self.sleep_until_time()
                self.create_and_execute_threads(user_node_data_lte, 15, func_ref=view_cell_relations,
                                                args=[self.relations_to_view, self.THREAD_QUEUE_TIMEOUT],
                                                wait=self.THREAD_QUEUE_TIMEOUT, join=60)
        else:
            self.add_error_as_exception(EnvironError('Profile execution stopped due to failed node verification'))


class CellMgt11(CellViewRelationsFlow):

    relations_to_view = [('INCOMING', 'readRelations', 'LTE', 'EUtranCellRelation'),
                         ('OUTGOING', 'readRelations', 'LTE', 'EUtranFreqRelation'),
                         ('OUTGOING', 'readRelations', 'WCDMA', 'UtranCellRelation'),
                         ('OUTGOING', 'readRelations', 'GSM', 'GeranCellRelation')]

    mo_types = ['EUtranCellFDD', 'EUtranCellTDD']


class CellMgt12(CellViewRelationsFlow):

    relations_to_view = [('INCOMING', 'readRelations', 'LTE', 'UtranCellRelation'),
                         ('OUTGOING', 'readRelations', 'WCDMA', 'CoverageRelation'),
                         ('OUTGOING', 'readRelations', 'WCDMA', 'UtranRelation'),
                         ('OUTGOING', 'readRelations', 'LTE', 'EutranFreqRelation'),
                         ('OUTGOING', 'readRelations', 'GSM', 'GsmRelation')]

    mo_types = ['UtranCell']
