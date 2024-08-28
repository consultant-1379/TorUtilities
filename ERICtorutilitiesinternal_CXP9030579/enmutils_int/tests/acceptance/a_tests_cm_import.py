#!/usr/bin/env python
import unittest2

from enmutils.lib import filesystem
from enmutils_int.lib.cm_import import CmImportUpdateLive, CmImportCreateLive, CmImportDeleteLive
from enmutils_int.lib.cm_import_over_nbi import UndoOverNbi
from enmutils_int.lib.node_pool_mgr import get_nodes_mos
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec, setup_verify


class CmImportNbiAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'RadioNode': 1}
    EXCLUSIVE = True

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ['ADMINISTRATOR']
        cls.nbi_nodes = None

    @classmethod
    def tearDownClass(cls):
        test_files = ['a_tests_update_live_v1.txt', 'a_tests_delete_live_v1.xml', 'a_tests_create_live_v1.txt']
        for test_file in test_files:
            if filesystem.does_file_exist(test_file):
                filesystem.delete_file(test_file)
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        func_test_utils.cm_sync_nodes(self.fixture.nodes)
        if not self.nbi_nodes:
            self.user = self.fixture.users[0]
            if self.fixture.nodes:
                nbi_node = self.fixture.nodes[0]
                self.nbi_nodes = get_nodes_mos(user=self.user, mos_dict={'EUtranCellRelation': 3},
                                               attrs={'EUtranCellRelation': [
                                                   'EUtranCellRelationId', 'neighborCellRef']},
                                               nodes=[nbi_node], profile='cmimport_01')

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(available_nodes=1)
    @func_dec('Cm_Import', 'CmImport Update Live over NBIv1 with history check')
    def test_050_import_update_live_nbi_v1_and_history_check(self):

        update_live_over_nbi_job_v1 = CmImportUpdateLive(
            name='a_tests_update_live_v1',
            mos={'EUtranCellRelation': ('isHoAllowed', 'true')}, nodes=self.nbi_nodes,
            template_name='a_tests_update_live_v1.txt', flow='live_config', file_type='dynamic',
            interface='NBIv1', user=self.user, expected_num_mo_changes=3)

        update_live_over_nbi_job_v1.prepare_dynamic_file()
        update_live_over_nbi_job_v1.create_import_over_nbi_v1()

        actual_changes = update_live_over_nbi_job_v1.get_total_history_changes_over_nbi_v1(
            update_live_over_nbi_job_v1.id)
        self.assertEqual(actual_changes, update_live_over_nbi_job_v1.expected_num_mo_changes)

    @setup_verify(available_nodes=1)
    @func_dec('Cm_Import', 'CmImport Create/Delete Live over NBIv1 with history check')
    def test_060_import_delete_create_live_nbi_v1_and_history_check(self):

        delete_live_over_nbi_job_v1 = CmImportDeleteLive(
            name='a_tests_delete_live_v1',
            nodes=self.nbi_nodes,
            template_name='a_tests_delete_live_v1.xml', flow='live_config', file_type='3GPP',
            interface='NBIv1', user=self.user, expected_num_mo_changes=3)

        delete_live_over_nbi_job_v1.prepare_xml_file()
        delete_live_over_nbi_job_v1.create_import_over_nbi_v1()

        actual_changes = delete_live_over_nbi_job_v1.get_total_history_changes_over_nbi_v1(
            delete_live_over_nbi_job_v1.id)
        self.assertEqual(actual_changes, delete_live_over_nbi_job_v1.expected_num_mo_changes)

        create_live_over_nbi_job_v1 = CmImportCreateLive(
            name='a_tests_create_live_v1',
            nodes=self.nbi_nodes,
            template_name='a_tests_create_live_v1.txt', flow='live_config',
            file_type='dynamic',
            interface='NBIv1', user=self.user, expected_num_mo_changes=3)

        create_live_over_nbi_job_v1.prepare_dynamic_file()
        create_live_over_nbi_job_v1.create_import_over_nbi_v1()

        actual_changes = create_live_over_nbi_job_v1.get_total_history_changes_over_nbi_v1(
            create_live_over_nbi_job_v1.id)
        self.assertEqual(actual_changes, create_live_over_nbi_job_v1.expected_num_mo_changes)

    @setup_verify(available_nodes=1)
    @func_dec('Cm_Import', 'CmImport Undo Import to Live')
    def test_070_undo_import_to_live_job_over_nbi(self):

        job_to_undo = CmImportUpdateLive(
            name='a_tests_import_to_live', mos={'EUtranCellRelation': ('isHoAllowed', 'true')},
            nodes=self.nbi_nodes, template_name='a_tests_import_to_live.txt', flow='live_config',
            file_type='dynamic', interface='NBIv2', user=self.user, expected_num_mo_changes=3
        )

        job_to_undo.undo_over_nbi = UndoOverNbi(
            name='undo_import_to_live_nbi',
            user=self.user,
            file_type='dynamic',
        )

        job_to_undo.prepare_dynamic_file()
        job_to_undo.import_flow()
        job_to_undo.import_flow(undo=True)
        self.assertEqual(job_to_undo.expected_num_mo_changes, job_to_undo.get_total_operations_over_nbi(job_to_undo.id))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
