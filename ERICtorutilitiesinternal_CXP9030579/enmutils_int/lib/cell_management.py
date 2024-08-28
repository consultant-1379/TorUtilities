# ********************************************************************
# Name    : Cell Management
# Summary : This is a series of CellMgt profile flows.
# ********************************************************************

import time
from itertools import cycle
from enmutils_int.lib import cellmgt
from enmutils_int.lib.cellmgt import (IurLink)
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib import log
from enmutils.lib.persistence import picklable_boundmethod
from requests.exceptions import HTTPError

CMD_TO_LOCK_CELLS = "cmedit set {0} EUtranCellFDD.administrativeState=LOCKED"


class CreateDeleteCellsObject(object):

    def __init__(self, profile, user, node):
        self.profile = profile
        self.user = user
        self.node = node
        self.node_function = None
        self.node_name = node.node_id
        self.node_poid = None
        self.existing_cells = []
        self.cells_to_be_created = []
        self.external_cells = []
        self.created_cells = []
        self.relations_to_create = []
        self.created_relations = []
        self._setup_completed = False
        self.delete_count = 0
        self.lte_node_cell_type = node.lte_cell_type
        self.cell_type = (self.profile.CELL_TYPE.replace("FDD", self.lte_node_cell_type) if self.lte_node_cell_type else
                          self.profile.CELL_TYPE)

    @property
    def setup_completed(self):
        return self._setup_completed

    def setup(self):
        """
        Carry out setup operation for the object.
        """
        log.logger.debug('Attempting setup operations for {0}.'.format(self.node_name))
        try:
            self.node_poid = self.node.poid
            log.logger.debug('Got poid for node : {0} : {1}'.format(self.node_name, self.node_poid))
            self.existing_cells = self.fetch_existing_cells()
            self.clean_up_cells()
            self._setup_completed = True
        except Exception as e:
            e.message = "Profile failed setup due to: {0}".format(e.message)
            self.profile.add_error_as_exception(e)
            self._setup_completed = False

    def fetch_existing_cells(self):
        """
        Retrieves all existing cells of type profile.CELL_TYPE.

        :return: List of existing cells for node.
        :rtype: list

        :raises EnmApplicationError: if a list of existing could not be fetched.
        """
        log.logger.debug('Attempting fetch existing {0}s for node {1}.'.format(self.cell_type, self.node_name))

        try:
            return cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(self.user, [self.node_poid],
                                                                                self.profile.STANDARD,
                                                                                self.cell_type)
        except Exception as e:
            raise EnmApplicationError("Could not get list of {0}s for node {1} due to {2}".format(
                self.cell_type, self.node_name, e.message))

    def create_cells(self):
        """
        Creates a cell for each cell in self.cells_to_be_created.
        """
        created_cell_list, failed_creates = cellmgt.create_cell_via_rest(self.user, self.profile,
                                                                         self.cells_to_be_created,
                                                                         self.cell_type, self.lte_node_cell_type,
                                                                         node_name=self.node_name)
        self.created_cells.extend(created_cell_list)

        if failed_creates:
            for cell, failure_reason in failed_creates.items():
                if "already exists with id" in failure_reason:
                    try:
                        cellmgt.delete_cell_via_rest(self.user, cell)
                        log.logger.debug("Deleted existing cell. Profile will re-create cell after 60 second sleep.")
                        time.sleep(60)
                        created_cell_list, _ = cellmgt.create_cell_via_rest(self.user, self.profile, [cell],
                                                                            self.cell_type, self.lte_node_cell_type,
                                                                            node_name=self.node_name)
                        self.created_cells.extend(created_cell_list)
                    except Exception as e:
                        log.logger.debug("Failed to delete cell. Cell could not be cleaned up and will remain until "
                                         "next profile iteration")
                        self.profile.add_error_as_exception(e)

    def get_relations_to_create(self):
        """
        Creates a list of tuples containing relations to create.
        """

        for cell in self.created_cells:
            log.logger.debug("Generating relations to be created for {0}".format(cell))
            if hasattr(self.profile, "RELATIONS_TO_EXISTING_CELLS"):
                relations_to_existing_cells = [(cell, target_cell) for target_cell in
                                               self.existing_cells[:self.profile.RELATIONS_TO_EXISTING_CELLS]]
                self.relations_to_create.extend(relations_to_existing_cells)

            relations_between_newly_created_cells = [(cell, other_cell) for other_cell in self.created_cells if
                                                     cell != other_cell]
            self.relations_to_create.extend(relations_between_newly_created_cells)

            relations_to_external_cells = [(cell, external_cell) for external_cell in self.external_cells]
            self.relations_to_create.extend(relations_to_external_cells)

    def create_relations(self, **kwargs):
        """
        Creates relations between all cells in self.relations_to_create.
        """

        self.get_relations_to_create()

        for source_cell, target_cell in self.relations_to_create:
            log.logger.debug("Attempting to create relation of type {0} between {1} and {2}.".format(
                self.profile.RELATION_TYPE, source_cell, target_cell))
            try:
                created_relation = cellmgt.create_external_cell_relation(self.user, source_cell,
                                                                         {'targetFdn': target_cell},
                                                                         self.profile.RELATION_TYPE)
                self.created_relations.append(created_relation)
            except HTTPError as e:
                log.logger.debug('Could not create relation of type {0} between {1} and {2}.'.format(
                    self.profile.RELATION_TYPE, source_cell, target_cell))
                self.profile.add_error_as_exception(e)

    @staticmethod
    def cmedit_clean_up(fdn, user, delete_all=True):
        """
        Cleans up leftover cell relations from previous profile run.
        :param fdn: str of relation FDNs to delete.
        :type fdn: str
        :param user: User who will execute cmedit command
        :type user: `enm_user_2.User`
        :param delete_all: Flag to delete all children MOs
        :type delete_all: bool
        :return: Relation deleted successfully
        :rtype: bool
        """
        cmd = "cmedit delete {0} --all" if delete_all else "cmedit delete {0}"
        try:
            user.enm_execute(cmd.format(fdn))
            return True
        except Exception as e:
            log.logger.debug("Failed to delete {0}: {1}".format(fdn, e.message))

    def lock_cells_for_deletion(self, fdn, user):
        """
        This function will lock cells before the deletion process
        :param fdn: str of relation FDNs to lock.
        :type fdn: str
        :param user: User who will execute cmedit command
        :type user: `enm_user_2.User`
        :return: cell locked successfully
        :rtype: bool
        :raises EnmApplicationError: if locking the cell fails
        """
        try:
            user.enm_execute(CMD_TO_LOCK_CELLS.format(fdn))
            return True
        except Exception as e:
            self.profile.add_error_as_exception(EnmApplicationError(e))

    def delete_all_cells(self, attempts=1):
        """
        Deletes all cells attempted to be created.
        :param attempts: The number of deletion attempts.
        :type attempts: int
        """
        cells_to_delete = self.created_cells if self.created_cells else self.cells_to_be_created
        for cell in cells_to_delete:
            cell_deleted = False
            attempt = 1
            log.logger.debug("Locking cell before deletion")
            self.lock_cells_for_deletion(cell, self.user)
            log.logger.debug("Attempting to delete cell: {0}".format(cell))
            while not cell_deleted:
                try:
                    cellmgt.delete_cell_via_rest(self.user, cell)
                    cell_deleted = True
                    self.delete_count += 1
                except HTTPError as e:
                    log.logger.debug("Attempt: {0}/{1}. Could not delete cell: {2}.".format(attempt, attempts, cell))
                    attempt += 1
                    if "Invalid or non existing FDN" in str(e):
                        log.logger.debug('Cell was already deleted/never created: {0}'.format(cell))
                        break
                    elif attempt > attempts:
                        log.logger.debug("Max attempts to delete {0} via Cell Management reached.".format(cell))
                        self.profile.add_error_as_exception(e)
                        log.logger.debug("Profile will make one more attempt to delete via cmedit.")
                        self.cmedit_clean_up(cell, self.user)
                        break
                    log.logger.debug('Sleeping for 10s before next attempted delete.')
                    time.sleep(10)

    def get_available_cell_ids(self):
        """
        Generates list of unused cellIds.
        :return: List of unused cellIds
        :rtype: list
        """
        reserved_ids = [int(cell.split('-')[-1]) for cell in self.existing_cells if cell.split('-')[-1].isdigit()]
        cell_id_range = xrange(*self.profile.CELL_ID_RANGE)
        return [c_id for c_id in cell_id_range if c_id not in reserved_ids]

    def summary_report(self):
        """
        Logs the summary report of the jobs done
        """
        log.logger.debug("Summary for node:{0}".format(self.node_name))
        log.logger.debug("Cells successfully created:{0}/{1}".format(len(self.created_cells),
                                                                     len(self.cells_to_be_created)))
        log.logger.debug("Relations successfully created:{0}/{1}".format(len(self.created_relations),
                                                                         len(self.relations_to_create)))
        log.logger.debug("Cells successfully deleted:{0}/{1}".format(self.delete_count, len(self.created_cells)))

    def reset(self):
        """
        Resets the object back to a starting state.
        """
        self.external_cells = []
        self.created_cells = []
        self.relations_to_create = []
        self.created_relations = []
        self._setup_completed = False
        self.delete_count = 0

    def __ne__(self, other):
        return self.node_name != other.node_name

    def clean_up_cells(self):
        """
        Clean up left over cells at profile start up.
        """
        for cell in self.existing_cells:
            if self.profile.NAME in cell:
                log.logger.debug("Cell from previous profile run found. Profile will attempt to delete.")
                self.lock_cells_for_deletion(cell, self.user)
                log.logger.debug("Successfully locked the cell {0}".format(cell))
                cellmgt.delete_cell_via_rest(self.user, cell)
                self.existing_cells.remove(cell)


class RncCreateDeleteCells(CreateDeleteCellsObject):

    def __init__(self, profile, user, node):
        """
        init method.
        :param profile: Profile object.
        :type profile: 'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells'
        :param user: User object
        :type user: 'enm2.user'
        :param node: node object
        :type node: node
        """
        super(RncCreateDeleteCells, self).__init__(profile, user, node)
        self.rnc_id = self.node_name.split("RNC")[-1]
        self.utran_network = None

    def setup(self):
        """
        Carries out RNC specific setup steps.
        """
        super(RncCreateDeleteCells, self).setup()
        if self.setup_completed:
            try:
                self.utran_network = cellmgt.get_utran_network(self.user, self.node_name)[0]
                log.logger.debug('Got UtranNetwork FDN for node: {0} : {1}'.format(self.node_name, self.utran_network))
                self.node_function = self.utran_network.split('UtranNetwork')[0][:-1]

                for i in xrange(self.profile.NUM_CELLS_PER_NODE):
                    cell_fdn = self.node_function + ',{0}={1}-{2}'.format(self.cell_type, self.profile.NAME, i + 1)
                    self.cells_to_be_created.append(cell_fdn)

                self.profile.teardown_list.append(picklable_boundmethod(self.delete_all_cells))
                log.logger.debug("Setup completed for node: {0}".format(self.node_name))
            except Exception as e:
                e.message = "Profile failed setup due to: {0}".format(e.message)
                self.profile.add_error_as_exception(e)
                self._setup_completed = False

    def create_relations(self, **kwargs):
        """
        Creates relations for newly created cells. Overrides parent class.
        """
        target_obj = kwargs.pop("target_objs")
        for obj in target_obj:
            if self.check_if_iurlink_exists(obj):
                self.external_cells.extend(obj.created_cells)
            else:
                log.logger.debug("IurLink could not be created, external relations will not be created "
                                 "from {} to {}.".format(self.node_name, obj.node_name))
        super(RncCreateDeleteCells, self).create_relations()

    def check_if_iurlink_exists(self, destination):
        """
        Checks for an existing Iurlink to the destination object
        :param destination: RncCreateDeleteCells to check for Iurlink existing.
        :type destination: RncCreateDeleteCells
        :return: if iurlink exists
        :rtype: bool
        """

        iurlink = IurLink(self.profile, self.user, self.node_function, destination.rnc_id, self.utran_network)
        iurlink.execute()
        return iurlink.iurlink_exists


class ERBSCreateDeleteCells(CreateDeleteCellsObject):

    def __init__(self, profile, user, node):
        """
        init method.
        :param profile: Profile object.
        :type profile: 'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells'
        :param user: User object
        :type user: 'enm2.user'
        :param node: node object
        :type node: node
        """
        super(ERBSCreateDeleteCells, self).__init__(profile, user, node)
        self.created_eutran_relations = 0
        self.created_utran_relations = 0
        self.lte_node_cell_type = node.lte_cell_type
        self.cell_type = (self.profile.CELL_TYPE.replace('FDD', self.lte_node_cell_type) if self.lte_node_cell_type else
                          self.profile.CELL_TYPE)
        self.relations_created_on_cell = []

    def setup(self):
        """
        Carries out RadioNode specific setup steps.
        """
        super(ERBSCreateDeleteCells, self).setup()
        if self.setup_completed:
            try:
                retry = 1
                max_retries = 3
                while retry <= max_retries:
                    if self.existing_cells:
                        self.node_function = self.existing_cells[0].split(self.cell_type)[0][:-1]
                        break
                    else:
                        super(ERBSCreateDeleteCells, self).setup()
                        retry += 1
                else:
                    raise EnvironError("The existing_cells data is not present.")
                available_cell_ids = self.get_available_cell_ids()

                for i in xrange(self.profile.NUM_CELLS_PER_NODE):
                    cell_fdn = self.node_function + ',{0}={1}-{2}'.format(self.cell_type, self.profile.NAME,
                                                                          available_cell_ids[i])
                    self.cells_to_be_created.append(cell_fdn)

                self.profile.teardown_list.append(picklable_boundmethod(self.delete_all_cells))
                log.logger.debug("Cells to be created: {0}".format(self.cells_to_be_created))

                log.logger.debug("Setup completed for node: {0}".format(self.node_name))
            except Exception as e:
                self.profile.add_error_as_exception("Profile failed setup due to: {0}".format(e.message))
                self._setup_completed = False

    def create_relations(self, **kwargs):
        """
        Creates relations for newly created cells. Overrides parent class.
        """
        target_obj = kwargs.pop("target_objs")
        for obj in target_obj:
            self.external_cells.extend(obj.created_cells)
        self.create_eutran_relations()
        self.create_utran_relation()

        super(ERBSCreateDeleteCells, self).create_relations()

    @staticmethod
    def create_target_gsm_cgi_proxy_objects_for_lte_nodes(external_cell_type, frequency, freq_group_id, cell_id_start,
                                                          num_to_create=1):
        """
        Creates a list of proxy GSM cells for creating relations to LTE nodes.
        :param external_cell_type: External cell type.
        :type external_cell_type: str
        :param freq_group_id: Frequency group Id.
        :type freq_group_id: int
        :param frequency: External cell frequency.
        :type frequency: int
        :param cell_id_start: Cell Id starting value.
        :type cell_id_start: int
        :param num_to_create: Number of proxy objects to create
        :type num_to_create: int
        :return: List of gsm proxy objects.
        :rtype: list
        """
        gsm_proxy_objs = []

        for i in xrange(num_to_create):
            gsm_proxy_objs.append({
                "frequency": frequency,
                "frequencyGroupId": freq_group_id,
                "cellGlobalIdentity": {"mcc": "999", "mnc": "88", "lac": "7", "cellIdentity": str(cell_id_start + i)},
                "attributes": {external_cell_type: {"bcc": "5", "ncc": "7"}}
            })
        return gsm_proxy_objs

    @staticmethod
    def create_target_wcdma_cgi_proxy_objects_for_lte_nodes(external_cell_type, frequency, cell_id_start,
                                                            num_to_create=1):
        """
        Creates a list of proxy WCDMA cells for creating relations to LTE nodes.
        :param external_cell_type: External cell type.
        :type external_cell_type: str
        :param frequency: External cell frequency.
        :type frequency: int
        :param cell_id_start: Cell Id starting value.
        :type cell_id_start: int
        :param num_to_create: Number of proxy objects to create
        :type num_to_create: int
        :return: List of gsm proxy objects.
        :rtype: list
        """
        wcdma_proxy_objs = []

        for i in xrange(num_to_create):
            wcdma_proxy_objs.append({
                "frequency": frequency,
                "cellGlobalIdentity": {"mcc": "999", "mnc": "88", "rncId": "30", "cId": str(cell_id_start + i)},
                "externalCellType": external_cell_type,
                "attributes": {external_cell_type: {"physicalCellIdentity": 122 + i}}
            })
        return wcdma_proxy_objs

    def create_utran_relation(self):
        """
        Creates a UtranCellRelation to an external UtranCell.
        """
        utran_cell_relation = self.profile.UTRAN_RELATION
        utran_relations = self.create_target_wcdma_cgi_proxy_objects_for_lte_nodes(
            utran_cell_relation["external_cell_type".replace("FDD", self.lte_node_cell_type)],
            utran_cell_relation["frequency"], utran_cell_relation["cell_start_id"],
            num_to_create=utran_cell_relation["num_to_create"])
        log.logger.debug("Attempting to create UtranCellRelations to proxy cells.")
        for cell in self.created_cells:
            for relation in utran_relations:
                try:
                    self.relations_created_on_cell.append(cellmgt.create_external_cell_relation(
                        self.user, cell, relation, utran_cell_relation["relation_type"]))
                    self.created_utran_relations += 1
                except Exception as e:
                    log.logger.debug("Failed to create relation")
                    self.profile.add_error_as_exception(e)

    @staticmethod
    def create_target_lte_cgi_proxy_objects(external_cell_type, frequency_range, cell_id_start, num_to_create=1,
                                            enode_id=100):
        """
        Generates a list of proxy LTE cells for creation of externalEUtranCellRelations.
        NOTE: Max number of ExternalEUtranCellFDD that can be created under a ExternalENodeBFunction is 24.
        :param external_cell_type: Type of external cell. EUtranCellFDD or EUtranCellTDD
        :type external_cell_type: str
        :param frequency_range: Frequency range to spread relations over.
        :type frequency_range: tuple or int
        :param cell_id_start: External cellId start range.
        :type cell_id_start: int
        :param enode_id: enode_id to create proxy objects with. If the number of proxy objects exceeds 24 enode_id will
        be incremented to avoid cardinality issues. Max relation cardinality=24.
        :type enode_id: int
        :param num_to_create: Number of external relations to generate.
        :type num_to_create: int
        :return: list of lte cgi proxy objects.
        :rtype: list
        """

        frequency_range = cycle(frequency_range) if isinstance(frequency_range, tuple) else cycle([frequency_range])
        lte_proxy_objs = []
        log.logger.debug("Generating {0} LTE proxy objects.".format(num_to_create))
        for i in xrange(num_to_create):
            enode_id = enode_id + 1 if (i + 1) % 25 == 0 else enode_id  # Max Cardinality=24
            lte_proxy_objs.append({
                "frequency": str(frequency_range.next()),
                "cellGlobalIdentity": {"mcc": "999", "mnc": "90", "eNBId": str(enode_id),
                                       "cellId": str(cell_id_start + i)},
                "externalCellType": external_cell_type,
                "attributes": {
                    external_cell_type: {"physicalLayerCellIdGroup": "1", "physicalLayerSubCellId": "1", "tac": "1"}}
            })

        return lte_proxy_objs

    def create_eutran_relations(self):
        """
        Creates EUtranCellFDD  or EUtranCellTDD relations for each newly created cell to external EUtranCells.
        """
        eutran_cell_relation = self.profile.EUTRAN_RELATION
        relations = self.create_target_lte_cgi_proxy_objects(
            eutran_cell_relation["external_cell_type".replace("FDD", self.lte_node_cell_type)],
            eutran_cell_relation["frequencies"], eutran_cell_relation["cell_start_id"],
            eutran_cell_relation["num_to_create"], eutran_cell_relation['enode_id'])
        log.logger.debug("Attempting to create EUtranCellRelations to proxy cells.")
        for cell in self.created_cells:
            for relation in relations:
                try:
                    self.relations_created_on_cell.append(cellmgt.create_external_cell_relation(
                        self.user, cell, relation, eutran_cell_relation["relation_type"]))
                    self.created_eutran_relations += 1
                except Exception as e:
                    self.profile.add_error_as_exception(e)

    def reset(self):
        """
        Resets object back to starting state.
        """
        super(ERBSCreateDeleteCells, self).reset()
        self.created_eutran_relations = 0
        self.created_utran_relations = 0

    def summary_report(self):
        """
        Prints summary report for ERBS object.
        """

        super(ERBSCreateDeleteCells, self).summary_report()
        log.logger.debug("ExternalEUtranCellRelation(s) successfully created:{0}/{1}".format(
            self.created_eutran_relations, len(self.created_cells) * self.profile.EUTRAN_RELATION["num_to_create"]))
        log.logger.debug("ExternalUtranCellRelation(s) successfully created:{0}/{1}".format(
            self.created_utran_relations, len(self.created_cells) * self.profile.UTRAN_RELATION["num_to_create"]))
