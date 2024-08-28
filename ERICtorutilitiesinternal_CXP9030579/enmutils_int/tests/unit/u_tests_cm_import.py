#!/usr/bin/env python
import unittest2
from mock import Mock, patch, mock_open, MagicMock, PropertyMock

from testslib import unit_test_utils
from testslib.unit_test_utils import get_nodes
from requests.exceptions import HTTPError
from enmutils_int.lib.enm_mo import EnmMo
from enmutils_int.lib.profile import CMImportProfile
from enmutils_int.lib.cm_import import (CMImportUpdateXml, get_different_nodes, get_total_num_mo_changes,
                                        CmImportLive, ImportProfileContextManager, CMImportDeleteXml,
                                        CmImportUpdateLive, CmImportCreateLive, get_fqdn_with_attrs_for_creation,
                                        get_enm_mo_attrs)
from enmutils.lib.exceptions import (GetTotalHistoryChangesError, UndoPreparationError,
                                     CMImportError, HistoryMismatch, EnmApplicationError, EnvironError)
import lxml.etree as etree


class CmImportUnitTests(unittest2.TestCase):

    @patch('enmutils_int.lib.cm_import.UndoOverNbi')
    def setUp(self, *_):  # pylint: disable=arguments-differ
        unit_test_utils.setup()
        self.user = Mock()

        mo_1 = EnmMo('EUtranFreqRelation', '1', 'SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE1-1,EUtranFreqRelation=4,EUtranCellRelation=7')
        mo_1.attrs = {'userLabel': 'default'}
        mo_2 = EnmMo('UtranFreqRelation', '1', 'SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE1-1,UtranFreqRelation=4,UtranCellRelation=7')
        mo_2.attrs = {'userLabel': 'changes'}
        self.mos = mo_1, mo_2

        node1 = get_nodes(1)[0]
        node1.mos = {(u'MeContext', u'netsimlin704_LTE1'): {(u'ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtranCellFDD', u'LTE1-1'): {u'EUtranFreqRelation': [mo_1], u'UtranFreqRelation': [mo_2]}}}}}
        node1.subnetwork = 'ERBS-SUBNW-1'
        node1.node_id = 'netsimlin704_LTE1'
        self.node1 = node1

        node2 = get_nodes(2)[1]
        node2.mos = {(u'MeContext', u'netsimlin704_LTE2'): {(u'ManagedElement', u'1'): {(u'ENodeBFunction', u'1'): {(u'EUtranCellFDD', u'LTE1-2'): {u'EUtranFreqRelation': [mo_1], u'UtranFreqRelation': [mo_2]}}}}}
        node2.subnetwork = 'ERBS-SUBNW-2'
        node2.node_id = 'netsimlin704_LTE2'
        self.node2 = node2

        self.nodes = {(u'SubNetwork', u'ERBS-SUBNW-1'): [node1, node2]}
        self.nodes_list = [node1, node2]

        self.import_live_job_v1 = CmImportLive(
            name='import_to_live_v1',
            user=self.user,
            nodes=self.nodes_list,
            template_name='cm_import_01.xml',
            flow='live_config',
            file_type='3GPP',
            interface='NBIv1',
            expected_num_mo_changes=1
        )
        self.import_live_job_v1.FILE_OPERATION = 'set'

    def tearDown(self):
        unit_test_utils.tear_down()

    def _get_profile(self, total_nodes=None):
        profile = CMImportProfile()
        if total_nodes:
            profile.TOTAL_NODES = total_nodes
            profile.SUPPORTED_NODE_TYPES = ['ERBS']
        return profile

    CMImportProfile.NAME = 'TEST_00'

    def test_cm_import_build_xml_success(self):
        xml = CMImportUpdateXml(self.nodes, '/tmp/test_update.xml', values={'UtranFreqRelation': [('ncc', 1), ('bcc', 3)], 'EUtranFreqRelation': ('userLabel', 'test2')}).build_xml()
        subnetworks = xml.getchildren()[1]
        mecontexts = subnetworks[0].getchildren()
        self.assertEqual(len(subnetworks), 1)
        self.assertEqual(len(mecontexts), 2)
        self.assertTrue('<ncc>1</ncc><bcc>3</bcc>' in etree.tostring(xml))

    @patch('enmutils_int.lib.cm_import.CmImportLive.nodes_tree', new_callable=PropertyMock)
    def test_prepare_dynamic_file_is_successful(self, mock_nodes_tree):
        mock_nodes_tree.return_value = {('SubNetwork', 'ERBS-SUBNW-1'): [self.node1, self.node2]}
        mo_values = {'EUtranFreqRelation': ('userLabel', 'default'), 'UtranFreqRelation': ('userLabel', 'default')}
        mock_open_file = mock_open()
        with patch('__builtin__.open', mock_open_file):
            self.import_live_job_v1.prepare_dynamic_file(mo_values=mo_values)

    @patch('enmutils_int.lib.cm_import.CmImportLive.nodes_tree', new_callable=PropertyMock)
    def test_prepare_dynamic_file_with_delete_operation_is_successful(self, mock_nodes_tree):
        self.import_live_job_v1.FILE_OPERATION = 'delete'
        mock_nodes_tree.return_value = {('SubNetwork', 'ERBS-SUBNW-1'): [self.node1, self.node2]}
        mock_open_file = mock_open()
        with patch('__builtin__.open', mock_open_file):
            self.import_live_job_v1.prepare_dynamic_file()

    @patch('enmutils_int.lib.cm_import.CmImportLive._write_attribute_values_to_file')
    @patch('__builtin__.open', new_callable=mock_open)
    @patch('enmutils_int.lib.cm_import.get_enm_mo_attrs')
    @patch('enmutils_int.lib.cm_import.CmImportLive.nodes_tree', new_callable=PropertyMock)
    def test_prepare_dynamic_file__raises_EnvironError(self, mock_nodes_tree, mock_get_enm, *_):
        mock_nodes_tree.return_value = {('SubNetwork', 'ERBS-SUBNW-1'): [self.node1, self.node2]}
        mo_values = {'EUtranFreqRelation': ('userLabel', 'default'), 'UtranFreqRelation': ('userLabel', 'default')}
        mock_get_enm.return_value = {'hi': ('fdn', 'hello')}
        delattr(mock_get_enm, 'fdn')
        self.assertRaises(EnvironError, self.import_live_job_v1.prepare_dynamic_file, mo_values)

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__')
    def test_modify_mo_data__is_successful(self, _):
        imp_obj = CmImportUpdateLive({}, {}, "test", "live_config", "dynamic")
        imp_obj.FILE_OPERATION = 'set'
        mo, f = Mock(), Mock()
        setattr(mo, 'fdn', 'rule-list')
        imp_obj._modify_mo_data(mo, f)

    @patch('enmutils_int.lib.cm_import.timestamp.get_human_readable_timestamp')
    @patch('enmutils_int.lib.cm_import.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.cm_import.CmImportLive.create_over_nbi')
    def test_import_flow_with_import_live_is_successful(self, mock_create_over_nbi, *_):

        self.import_live_job_v1.import_flow()
        self.assertTrue(mock_create_over_nbi.called)

    @patch('enmutils_int.lib.cm_import.timestamp.get_human_readable_timestamp')
    @patch('enmutils_int.lib.cm_import.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.cm_import.UndoOverNbi')
    @patch('enmutils_int.lib.cm_import.CmImportLive.create')
    @patch('enmutils_int.lib.cm_import.CmImportLive.undo_iteration')
    def test_import_flow_undo_iteration_is_successful(self, mock_undo_iteration, *_):

        import_job = CmImportLive(
            name='import_job',
            user=self.user,
            nodes=self.nodes,
            template_name='cm_import_00.xml',
            flow='live_config',
            file_type='3GPP',
            expected_num_mo_changes=1
        )
        import_job.PREVIOUS_ACTIVATION_EXISTS = True
        import_job.import_flow(undo=True)
        self.assertTrue(mock_undo_iteration.called)

    @patch('enmutils_int.lib.cm_import.timestamp.get_human_readable_timestamp')
    @patch('enmutils_int.lib.cm_import.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.cm_import.CmImportLive.create_over_nbi')
    @patch('enmutils_int.lib.cm_import.CmImportLive.undo_iteration')
    def test_import_flow_undo_iteration_with_interface_is_successful(self, mock_undo_iteration, *_):
        self.import_live_job_v1.PREVIOUS_ACTIVATION_EXISTS = True
        self.import_live_job_v1.import_flow(undo=True)
        self.assertTrue(mock_undo_iteration.called)
        self.assertTrue(self.import_live_job_v1.undo_over_nbi.get_undo_config_file_path.called)
        self.assertTrue(self.import_live_job_v1.undo_over_nbi.remove_undo_config_files.called)

    @patch('time.sleep')
    @patch('enmutils_int.lib.cm_import.timestamp.get_human_readable_timestamp')
    @patch('enmutils_int.lib.cm_import.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.cm_import.CmImportLive.check_num_history_changes_match_expected')
    @patch('enmutils_int.lib.cm_import.CmImportLive.create_over_nbi')
    def test_import_flow_with_history_check_is_successful(self, mock_create, mock_history_changes, *_):
        self.import_live_job_v1.import_flow(history_check=True)
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_history_changes.called)

    def test_undo_iteration_with_interface_is_successful(self):
        self.import_live_job_v1.undo_iteration()
        self.assertTrue(self.import_live_job_v1.undo_over_nbi.undo_job_over_nbi.called)

    @patch('enmutils_int.lib.cm_import.timestamp.get_human_readable_timestamp')
    @patch('enmutils_int.lib.cm_import.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.cm_import.CmImportLive.create_over_nbi')
    def test__create_raises_cmimporterror(self, mock_create, mock_log, _):
        mock_create.side_effect = Exception('Index: 0')
        with self.assertRaises(CMImportError):
            self.import_live_job_v1._create()
        mock_create.side_effect = Exception
        with self.assertRaises(CMImportError):
            self.import_live_job_v1._create()
        self.assertEqual(2, mock_log.call_count)

    @patch('enmutils_int.lib.cm_import.timestamp.get_human_readable_timestamp')
    @patch('enmutils_int.lib.cm_import.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.cm_import.CmImportOverNbiV1.create_import_over_nbi_v1')
    def test_create_over_nbi_calls_v1_success(self, mock_create_over_nbi_v1, *_):
        self.import_live_job_v1._create()
        self.assertTrue(mock_create_over_nbi_v1.called)

    @patch('enmutils_int.lib.cm_import.UndoOverNbi')
    @patch('enmutils_int.lib.cm_import.CmImportLive.create_import_over_nbi_v2')
    def test_create_over_nbi_calls_v2_success(self, mock_create_over_nbi_v2, *_):
        import_live_job_v2 = CmImportLive(
            name='import_live_job_v2',
            user=self.user,
            nodes=self.nodes,
            template_name='cm_import_00.xml',
            flow='live_config',
            file_type='3GPP',
            interface='NBIv2',
            expected_num_mo_changes=1
        )
        import_live_job_v2.create_over_nbi()
        self.assertTrue(mock_create_over_nbi_v2.called)

    @patch('enmutils_int.lib.cm_import.time.sleep', return_value=0)
    @patch('enmutils_int.lib.cm_import.CmImportLive.get_total_operations_over_nbi')
    def test_check_num_history_changes_match_expected__is_successful(self, mock_get_total, *_):
        mock_get_total.return_value = 1
        self.import_live_job_v1.check_num_history_changes_match_expected(expected_num_mo_changes=1)

    @patch('enmutils_int.lib.cm_import.time.sleep', return_value=0)
    @patch('enmutils_int.lib.cm_import.CmImportLive.get_total_operations_over_nbi')
    def test_check_num_history_changes_match_expected__raises_history_mismatch(self, mock_get_total, *_):
        mock_get_total.return_value = 1
        with self.assertRaises(HistoryMismatch):
            self.import_live_job_v1.check_num_history_changes_match_expected(expected_num_mo_changes=3)

    @patch('enmutils_int.lib.cm_import.CmImportLive.get_total_history_changes_over_nbi_v2')
    @patch('enmutils_int.lib.cm_import.CmImportLive.get_total_history_changes_over_nbi_v1')
    def test_get_total_operations_over_nbi_is_successful(self, mock_get_total_v1, mock_get_total_v2):
        self.import_live_job_v1.get_total_operations_over_nbi(job_id=1)
        self.assertTrue(mock_get_total_v1.called)
        self.import_live_job_v1.interface = 'NBIv2'
        self.import_live_job_v1.get_total_operations_over_nbi(job_id=1)
        self.assertTrue(mock_get_total_v2.called)

    @patch('enmutils_int.lib.cm_import.CmImportLive.get_import_job_summary_by_id')
    def test_get_total_history_changes_over_nbi_v2_is_successful(self, mock_summary):

        mock_summary.return_value = {'summary': {'total': {
            'type': 'total',
            'parsed': 8,
            'valid': 0,
            'invalid': 0,
            'executed': 8,
            'executionErrors': 0}}}
        self.assertEqual(self.import_live_job_v1.get_total_history_changes_over_nbi_v2(job_id=1), 8)

    @patch('enmutils_int.lib.cm_import.CmImportLive.get_import_job_summary_by_id', side_effect=HTTPError)
    @patch('enmutils_int.lib.cm_import.log.logger.debug')
    def test_get_total_history_changes_over_nbi_v2_excepts_exception(self, mock_debug, _):
        self.import_live_job_v1.get_total_history_changes_over_nbi_v2(job_id=1)
        mock_debug.assert_called_with("ERROR when retrieving history changes for job 1. ")

    @patch('enmutils_int.lib.cm_import.CmImportLive.get_job_details_by_id')
    def test_get_total_history_changes_over_nbi_v1_is_successful(self, mock_get_job_details_by_id):

        json_get_job_details_response_failed = {
            "id": 255,
            "status": "EXECUTED",
            "totalManagedObjectCreated": 5,
            "totalManagedObjectDeleted": 5,
            "totalManagedObjectUpdated": 0
        }

        self.import_live_job_v1.id = 255
        mock_get_job_details_by_id.return_value = json_get_job_details_response_failed
        self.assertEqual(self.import_live_job_v1.get_total_operations_over_nbi(self.import_live_job_v1.id), 10)

    @patch('enmutils_int.lib.cm_import.CmImportLive.get_job_details_by_id')
    def test_get_total_history_changes_over_nbi_v1_raises_get_total_history_changes_error(self, mock_get_job_details_by_id):

        json_get_job_details_response_failed = {
            "id": 255,
            "status": "FAILED",
            "statusReason": "Error 7042 : There are validation failures. Please consult the description of the errors reported in the import verbose job status.",
            "totalManagedObjectCreated": 0,
            "totalManagedObjectDeleted": 0,
            "totalManagedObjectUpdated": 0
        }

        self.import_live_job_v1.id = 255
        mock_get_job_details_by_id.return_value = json_get_job_details_response_failed
        self.assertRaises(GetTotalHistoryChangesError,
                          self.import_live_job_v1.get_total_operations_over_nbi(self.import_live_job_v1.id))

    @patch('enmutils_int.lib.cm_import.UndoOverNbi')
    @patch('enmutils_int.lib.cm_import.log.logger.debug')
    def test_history_command_with_live_job_is_successful(self, mock_debug_log, *_):
        import_live_job = CmImportLive(
            name='import_live_job',
            user=self.user,
            nodes=self.nodes,
            template_name='cm_import_00.xml',
            flow='live',
            file_type='3GPP',
            expected_num_mo_changes=2
        )
        import_live_job.history(job_id=123)
        self.assertFalse(mock_debug_log.called)
        self.assertTrue(self.user.enm_execute.called)

    @patch('enmutils_int.lib.cm_import.timestamp.get_human_readable_timestamp')
    @patch('enmutils_int.lib.cm_import.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.cm_import.CmImportLive.create_over_nbi')
    @patch('lxml.etree.ElementTree')
    def test_cm_import_prepare_xml_and_create_job_is_successful(self, mock_element_tree, mock_create, *_):
        self.import_live_job_v1.XML_CLASS = CMImportDeleteXml
        self.import_live_job_v1.nodes = self.nodes_list
        self.import_live_job_v1.filepath = '/tmp/filepath.xml'
        self.import_live_job_v1.cm_import()
        self.assertTrue(mock_element_tree.called)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.cm_import.timestamp.get_human_readable_timestamp')
    @patch('enmutils_int.lib.cm_import.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.cm_import.CmImportLive.prepare_dynamic_file')
    @patch('enmutils_int.lib.cm_import.CmImportLive.create_over_nbi')
    def test_cm_import_prepare_dynamic_file_and_create_job_is_successful(self, mock_create, mock_prepare_dynamic_file,
                                                                         *_):
        self.import_live_job_v1.file_type = 'dynamic'
        self.import_live_job_v1.cm_import()
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_prepare_dynamic_file.called)

    def test_cm_import_unknown_file_type_raises_cmimport_error(self):
        self.import_live_job_v1.file_type = 'unknown type'
        with self.assertRaises(CMImportError):
            self.import_live_job_v1.cm_import()

    @patch('enmutils_int.lib.cm_import.time.sleep', side_effect=lambda _: None)
    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.CmImportUpdateLive._create', side_effect=[Exception("Error"), None])
    def test_restore_default_configuration_via_import_is_successful(self, mock_create, *_):
        imp_obj = CmImportUpdateLive({}, {}, "test", "live_config", "dynamic")
        imp_obj.restore_default_configuration_via_import()
        self.assertEqual(2, mock_create.call_count)

    @patch('os.remove')
    def test_delete_file_is_successful(self, mock_os_remove,):
        self.import_live_job_v1.delete()
        self.assertTrue(mock_os_remove.called)

    def test_delete_file_raises_error(self):
        self.import_live_job_v1.filepath = '/tmp/does_not_exist.xml'
        with self.assertRaises(Exception):
            self.import_live_job_v1.delete()

    @patch('enmutils_int.lib.cm_import.CmImportLive.delete')
    def test_config_delete__teardown(self, mock_delete):
        self.import_live_job_v1._teardown()
        self.assertEqual(mock_delete.call_count, 1)

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.CmImportLive.prepare_xml_file')
    def test_cmimport_update_live_calls_prepare_xml(self, mock_super_call_to_prepare_xml_live, _):
        update_live_obj = CmImportUpdateLive(mos=self.mos, nodes={}, template_name="test", flow="live_config",
                                             file_type="3GPP")
        update_live_obj.prepare_xml_file()
        self.assertTrue(mock_super_call_to_prepare_xml_live.called)

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.CmImportLive.prepare_dynamic_file')
    def test_cmimport_update_live_calls_prepare_dynamic_file(self, mock_super_call_to_prepare_dynamic_live, _):
        update_live_obj = CmImportUpdateLive(mos=self.mos, nodes={}, template_name="test",
                                             flow="live_config", file_type="dynamic")
        update_live_obj.prepare_dynamic_file()
        self.assertTrue(mock_super_call_to_prepare_dynamic_live.called)

    @patch('enmutils_int.lib.cm_import.CmImportUpdateLive.__init__', return_value=None)
    def test_write_attribute_values_to_file__unpack_one_mo_attribute_when_updating_live(self, _):
        imp_obj = CmImportUpdateLive({}, {}, "test", "live_config", "dynamic")
        imp_obj.FILE_OPERATION = 'set'
        mo_values = {'BandwidthProfile': ('cir', 0)}
        mock_file_obj = Mock()
        mo = Mock()
        mo.name = "BandwidthProfile"
        imp_obj._write_attribute_values_to_file(mo_values, mo, mock_file_obj)
        mock_file_obj.write.assert_called_with("cir : '0'\n")

    @patch('enmutils_int.lib.cm_import.CmImportUpdateLive.__init__', return_value=None)
    def test_write_attribute_values_to_file__unpack_multiple_mo_attributes_when_updating_live(self, _):
        imp_obj = CmImportUpdateLive({}, {}, "test", "live_config", "dynamic")
        imp_obj.FILE_OPERATION = 'set'
        mo_values = {'BandwidthProfile': [('cir', 2), ('eir', 1), ('cbs', 0)]}
        mock_file_obj = Mock()
        mo = Mock()
        mo.name = "BandwidthProfile"
        imp_obj._write_attribute_values_to_file(mo_values, mo, mock_file_obj)
        mock_file_obj.write.assert_called_with("cbs : '0'\n")
        mock_file_obj.write.assert_any_call("eir : '1'\n")
        mock_file_obj.write.assert_any_call("cir : '2'\n")

    @patch('enmutils_int.lib.cm_import.CmImportUpdateLive.__init__', return_value=None)
    def test_write_attribute_values_to_file__unpack_mos_when_not_update_live(self, _):
        imp_obj = CmImportUpdateLive({}, {}, "test", "live_config", "dynamic")
        imp_obj.FILE_OPERATION = 'CreateDeleteLive'
        mo_values = {'BandwidthProfile': [('cir', 2), ('eir', 1), ('cbs', 0)]}
        mock_file_obj = Mock()
        mo = Mock()
        mo.name = "BandwidthProfile"
        mo.attrs = {'userLabel': 'default'}
        imp_obj._write_attribute_values_to_file(mo_values, mo, mock_file_obj)
        mock_file_obj.write.assert_called_with("userLabel : 'default'\n")

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.write_profile_nodes_recovery_commands_to_file')
    @patch('enmutils_int.lib.cm_import.CmImportCreateLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.prepare_file')
    def test_context_manager_setup_is_successful(self, *_):
        imp_obj = CmImportCreateLive({}, "test", "live_config", "dynamic")
        profile = Mock()
        ImportProfileContextManager(profile=profile, default_obj=imp_obj, modify_obj=imp_obj)
        self.assertFalse(profile.add_error_as_exception.called)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.write_profile_nodes_recovery_commands_to_file')
    @patch('enmutils_int.lib.cm_import.CmImportCreateLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.prepare_file')
    def test_context_manager_setup_adds_error(self, mock_prepare_file, *_):
        imp_obj = CmImportCreateLive({}, "test", "live_config", "dynamic")
        profile = Mock()
        mock_prepare_file.side_effect = CMImportError
        ImportProfileContextManager(profile=profile, default_obj=imp_obj, modify_obj=imp_obj)
        self.assertEqual(1, profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.prepare_file')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.write_profile_nodes_recovery_commands_to_file')
    @patch('enmutils_int.lib.cm_import.CmImportUpdateLive.__init__', return_value=None)
    def test_context_manager_setup_update_live_recovery_false_adds_error(self, *_):
        imp_obj = CmImportUpdateLive({}, {}, "test", "live_config", "dynamic")
        profile, import_flow = Mock(), Mock()
        import_flow.side_effect = CMImportError
        imp_obj.import_flow = import_flow
        ImportProfileContextManager(profile=profile, default_obj=imp_obj, modify_obj=imp_obj, attempt_recovery=False)
        self.assertEqual(1, profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cm_import.CmImportCreateLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.prepare_file')
    def test_context_manager_setup_create_live_recovery_false(self, *_):
        imp_obj = CmImportCreateLive({}, "test", "live_config", "dynamic")
        profile = Mock()
        ImportProfileContextManager(profile=profile, default_obj=imp_obj, modify_obj=imp_obj, attempt_recovery=False)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.CmImportUpdateLive.__init__', return_value=None)
    def test_prepare_file_is_successful_with_xml_file(self, *_):
        imp_obj = CmImportUpdateLive({}, {}, "test", "live_config", "3GPP")
        imp_obj.prepare_xml_file = Mock()
        profile = Mock()
        profile.FILETYPE = '3GPP'
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)
        context_mgr.prepare_file()
        self.assertEqual(imp_obj.prepare_xml_file.call_count, 2)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.CmImportUpdateLive.__init__', return_value=None)
    def test_prepare_file_is_successful_with_dynamic_file(self, *_):
        imp_obj = CmImportUpdateLive({}, {}, "test", "live_config", "dynamic")
        imp_obj.prepare_dynamic_file = Mock()
        profile = Mock()
        profile.FILETYPE = 'dynamic'
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)
        context_mgr.prepare_file()
        self.assertEqual(imp_obj.prepare_dynamic_file.call_count, 2)

    @patch('enmutils_int.lib.cm_import.get_enm_mo_attrs')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.datetime')
    @patch('enmutils_int.lib.cm_import.filesystem')
    @patch('enmutils_int.lib.cm_import.get_fqdn_with_attrs_for_creation')
    def test_write_profile_nodes_recovery_commands_to_file_is_successful(self, mock_get_fqdn, *_):
        mock_get_fqdn.return_value = ['cmedit command']
        profile = MagicMock()
        profile.nodes_list = [Mock()]
        profile.NAME = 'cmimport_profile'
        context_mgr = ImportProfileContextManager(profile, Mock(), Mock())
        context_mgr.write_profile_nodes_recovery_commands_to_file()

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    def test_manage_sleep_is_successful(self, _):
        profile = Mock()
        profile.SCHEDULED_DAYS = ["TUESDAY"]
        context_mgr = ImportProfileContextManager(profile=profile, default_obj=self.import_live_job_v1,
                                                  modify_obj=self.import_live_job_v1)
        context_mgr.manage_sleep()
        self.assertEqual(1, profile.sleep_until_next_scheduled_iteration.call_count)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.profile.Profile.sleep_until_next_scheduled_iteration')
    def test_manage_sleep_is_successful_does_not_call_sleep_until(self, mock_sleep_until, _):
        profile = self._get_profile()
        context_mgr = ImportProfileContextManager(profile=profile, default_obj=Mock(), modify_obj=Mock())
        context_mgr.manage_sleep()
        self.assertFalse(mock_sleep_until.called)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.get_import_object', return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.execute_import_flow')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    def test_run_import_manage_sleep_false_cleanup_required_is_successful(self, *_):
        imp_obj = Mock()
        context_mgr = ImportProfileContextManager(Mock(), imp_obj, imp_obj)
        context_mgr.CLEANUP_REQUIRED = True
        context_mgr.run_import()
        self.assertEqual(imp_obj.user.open_session.call_count, 1)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.get_import_object', return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.manage_sleep')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.execute_import_flow')
    def test_run_import_is_successful(self, mock_execute_import_flow, *_):
        imp_obj = Mock()
        profile = Mock()
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)
        context_mgr.run_import()
        self.assertTrue(imp_obj.user.open_session.called)
        self.assertTrue(mock_execute_import_flow.called)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.time.sleep')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.manage_sleep')
    def test_run_import_user_open_session_exception(self, *_):
        imp_obj = Mock()
        imp_obj.user.open_session.side_effect = HTTPError
        profile = Mock()
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)
        context_mgr.run_import()
        self.assertEqual(profile.add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.cm_import.parse')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    def test_get_import_object_is_successful(self, *_):
        imp_obj = Mock()
        profile = Mock()
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)
        context_mgr.undo_profile = False
        context_mgr.get_import_object()

    @patch('enmutils_int.lib.cm_import.parse')
    @patch('enmutils_int.lib.cm_import.timestamp.is_time_current', return_value=True)
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    def test_get_import_object_for_undo_iter_is_successful(self, *_):
        imp_obj = Mock()
        imp_obj.PREVIOUS_ACTIVATION_EXISTS = True
        profile = Mock()
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)
        context_mgr.undo_profile = True
        context_mgr.get_import_object()

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    def test_execute_import_flow_is_successful(self, _):
        imp_obj = Mock()
        imp_obj.id = 1
        profile = Mock()
        profile.NAME = 'CmImportProfile'
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)
        undo = Mock()
        context_mgr.execute_import_flow(imp_obj, undo)
        self.assertTrue(imp_obj.import_flow.called)
        imp_obj.import_flow.assert_called_with(history_check=True, undo=undo)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.exception_handling')
    def test_execute_import_flow_calls_exception_handling(self, mock_exception_handling, _):
        imp_obj = Mock()
        imp_obj.import_flow.side_effect = CMImportError
        context_mgr = ImportProfileContextManager(Mock(), imp_obj, imp_obj)
        context_mgr.execute_import_flow(imp_obj, Mock())
        self.assertTrue(mock_exception_handling.called)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    def test_exception_handling_is_successful(self, _):
        profile = Mock()
        imp_obj = Mock()
        imp_obj.interface = 'NBI'
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)

        context_mgr.exception_handling(exception_caught=UndoPreparationError(), import_object=imp_obj)
        self.assertEqual(imp_obj.undo_over_nbi.remove_undo_config_files.call_count, 1)
        context_mgr.exception_handling(exception_caught=HistoryMismatch(), import_object=imp_obj)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.CmImportUpdateLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.import_activate_mo_cleanup')
    def test_exception_handling_cmimport_error_live_is_successful(self, mock_mo_cleanup, *_):
        profile = Mock()
        update_imp_obj = CmImportUpdateLive(
            mos={}, flow='', file_type='', expected_num_mo_changes=1, nodes={}, template_name='')

        context_mgr = ImportProfileContextManager(profile, update_imp_obj, update_imp_obj)
        context_mgr.IMPORT_TYPE = 'DEFAULT'
        context_mgr.exception_handling(exception_caught=CMImportError(), import_object=update_imp_obj)
        self.assertEqual(mock_mo_cleanup.call_count, 0)

        imp_obj = CmImportLive(flow='', file_type='', expected_num_mo_changes=1, nodes={}, template_name='')
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)
        context_mgr.IMPORT_TYPE = 'DEFAULT'
        context_mgr.exception_handling(exception_caught=CMImportError(), import_object=imp_obj)
        self.assertEqual(mock_mo_cleanup.call_count, 1)

        context_mgr.IMPORT_TYPE = 'MODIFICATIONS'
        context_mgr.exception_handling(exception_caught=CMImportError(), import_object=imp_obj)
        self.assertTrue(mock_mo_cleanup.called)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    def test__cleanup_undo_files_adds_error(self, _):
        profile = Mock()
        imp_obj = Mock()
        imp_obj.interface = 'NBI'
        imp_obj.undo_over_nbi.remove_undo_config_files.side_effect = CMImportError
        context_mgr = ImportProfileContextManager(profile, imp_obj, imp_obj)
        context_mgr.exception_handling(exception_caught=UndoPreparationError(), import_object=imp_obj)

        self.assertTrue(profile.add_error_as_exception.called)

    @patch('enmutils_int.lib.cm_import.time.sleep')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    def test_import_activate_mo_cleanup_is_successful(self, *_):
        profile = Mock()
        profile.create_users.return_value = [self.user]
        context_mgr = ImportProfileContextManager(profile=profile, default_obj=Mock(),
                                                  modify_obj=Mock())
        context_mgr.RECOVERY_NODE_INFO = [
            'cmedit create SubNetwork=ERBS-SUBNW-2,MeContext=ieatnetsimv7004-15_LTE28ERBS00128,ManagedElement=1,'
            'Equipment=1,AntennaUnitGroup=1,AntennaUnit=1,AntennaSubunit=1 maxTotalTilt="900"']
        response = Mock()
        response.get_output.side_effect = [[u'already exists']]
        self.user.enm_execute.return_value = response
        context_mgr.import_activate_mo_cleanup(manual_intervention_warning_time=0.01)

    @patch('enmutils_int.lib.cm_import.time.sleep')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.timestamp.is_time_diff_greater_than_time_frame', return_value=False)
    @patch('enmutils_int.lib.profile.Profile.create_users')
    def test_import_activate_mo_cleanup_is_successful_time_diff_false(self, *_):
        profile = Mock()
        profile.create_users.return_value = [self.user]
        context_mgr = ImportProfileContextManager(profile=profile, default_obj=Mock(),
                                                  modify_obj=Mock())
        context_mgr.RECOVERY_NODE_INFO = [
            'cmedit create SubNetwork=ERBS-SUBNW-2,MeContext=ieatnetsimv7004-15_LTE28ERBS00128,ManagedElement=1,'
            'Equipment=1,AntennaUnitGroup=1,AntennaUnit=1,AntennaSubunit=1 maxTotalTilt="900"']
        response = Mock()
        response.get_output.side_effect = [[u'Error - MO not recognised'], [u'already exists']]
        self.user.enm_execute.return_value = response
        context_mgr.import_activate_mo_cleanup()

    @patch('enmutils_int.lib.cm_import.time.sleep')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.timestamp.is_time_diff_greater_than_time_frame')
    def test_import_activate_mo_cleanup_adds_errors_as_exception(self, mock_time_diff, *_):
        profile = Mock()
        profile.create_users.return_value = [self.user]
        context_mgr = ImportProfileContextManager(profile=profile, default_obj=Mock(), modify_obj=Mock())
        context_mgr.RECOVERY_NODE_INFO = [
            'cmedit create SubNetwork=ERBS-SUBNW-2,MeContext=ieatnetsimv7004-15_LTE28ERBS00128,ManagedElement=1,'
            'Equipment=1,AntennaUnitGroup=1,AntennaUnit=1,AntennaSubunit=1 maxTotalTilt="900"']
        mock_time_diff.side_effect = [True, False]
        response = Mock()
        response.get_output.side_effect = [[u'Error - MO not recognised'], [u'already exists']]
        self.user.enm_execute.return_value = response
        context_mgr.import_activate_mo_cleanup()
        self.assertTrue(profile.add_error_as_exception.called)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.time.sleep')
    def test_recreate_all_mos_is_successful(self, mock_sleep, _):
        profile = Mock()
        context_mgr = ImportProfileContextManager(profile=profile, default_obj=Mock(), modify_obj=Mock())
        context_mgr.RECOVERY_NODE_INFO = ['cmedit create SubNetwork=ERBS-SUBNW-2,MeContext=ieatnetsimv7004-15_LTE28ERBS00128,'
                                          'ManagedElement=1,Equipment=1,AntennaUnitGroup=1,AntennaUnit=1,AntennaSubunit=1'
                                          'maxTotalTilt="900"', 'cmedit create SubNetwork=ERBS-SUBNW-2,'
                                                                'MeContext=ieatnetsimv7004-15_LTE28ERBS00128,'
                                                                'ManagedElement=1,Equipment=1,AntennaUnitGroup=1,'
                                                                'AntennaUnit=1,AntennaSubunit=1 maxTotalTilt="900"']
        profile.create_users.return_value = [self.user]
        context_mgr.recreate_all_mos()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.cm_import.time.sleep')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils.lib.log.logger.debug')
    def test_recreate_all_mos_exception(self, mock_debug, *_):
        profile = Mock()
        context_mgr = ImportProfileContextManager(profile=profile, default_obj=Mock(), modify_obj=Mock())
        context_mgr.RECOVERY_NODE_INFO = ['cmedit create SubNetwork=ERBS-SUBNW-2,'
                                          'MeContext=ieatnetsimv7004-15_LTE28ERBS00128,ManagedElement=1,Equipment=1,'
                                          'AntennaUnitGroup=1,AntennaUnit=1,AntennaSubunit=1 maxTotalTilt="900"']
        profile.create_users.return_value = [self.user]
        self.user.enm_execute.side_effect = EnmApplicationError
        context_mgr.recreate_all_mos()
        self.assertTrue(mock_debug.called, 2)

    def test_get_fqdn_with_attrs_for_creation_is_successful(self):
        mo_1 = EnmMo('EUtranFreqRelation', '1', 'SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                                                'ENodeBFunction=1,EUtranCellFDD=LTE1-1,EUtranFreqRelation=4,'
                                                'EUtranCellRelation=7')
        mo_1.attrs = {'EUtranCellRelationId': '7'}
        mock_mo = Mock()
        mock_mo.attrs = {}
        mock_mo.fdn = 'FDN'
        self.assertEqual(get_fqdn_with_attrs_for_creation([mo_1, mock_mo]),
                         [
                             'cmedit create SubNetwork=ERBS-SUBNW-1,MeContext=netsimlin704_LTE1,ManagedElement=1,'
                             'ENodeBFunction=1,EUtranCellFDD=LTE1-1,EUtranFreqRelation=4,EUtranCellRelation=7 '
                             'EUtranCellRelationId="7"', 'cmedit create FDN '])

    def test_get_different_nodes_returns_correct_num_nodes(self):
        nodes = [Mock()] * 5
        result = list(get_different_nodes(nodes, 5))
        self.assertEqual(len(result), 1)

    def test_get_different_nodes_returns_remaining_nodes_even_if_num_required_nodes_are_not_met(self):
        nodes = [Mock()] * 18
        result = get_different_nodes(nodes, 10)
        first_results = result.next()
        self.assertEqual(len(first_results), 10)
        second_results = result.next()
        self.assertEqual(len(second_results), 8)

    def test_get_total_num_mo_changes_returns_correct_value_total_nodes(self):
        mo_values = {'RetSubUnit': 1, 'AntennaSubunit': 1}
        total_nodes = 5
        self.assertEqual(get_total_num_mo_changes(mo_values, total_nodes), 10)

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    def test_cm_import_nodes_tree__handles_nested_subnetwork(self, _):
        nodes = [Mock(subnetwork="SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=Sub1"),
                 Mock(subnetwork="SubNetwork=Sub1", subnetwork_id="Sub1")]
        import_obj = CmImportLive(file_type="3GPP", nodes=nodes, template_name="test", flow="live")
        import_obj.nodes = nodes
        expected = [('SubNetwork', 'Europe,SubNetwork=Ireland,SubNetwork=Sub1'), ('SubNetwork', 'Sub1')]
        self.assertListEqual(expected, sorted(import_obj.nodes_tree.keys()))

    def test_get_enm_mo_attrs(self):
        mos = {'MeContext': {'ManagedElement': {'ENodeBFunction': {'EUtranCellFDD': {'EUtranFreqRelation': {'EUtranCellRelation': [('isHoAllowed', 'false')]}, 'CellId': 5}}}}}
        node = Mock(mos=mos)
        self.assertEqual(get_enm_mo_attrs(node), [('isHoAllowed', 'false')])

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.CmImportLive.undo_iteration', side_effect=Exception("Error"))
    def test_import_flow__undo_error(self, *_):
        imp_object = CmImportLive([], "", "", "")
        imp_object.PREVIOUS_ACTIVATION_EXISTS = True
        self.assertRaises(UndoPreparationError, imp_object.import_flow, undo=True)

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    def test_get_create_command__success(self, _):
        imp_object = CmImportLive([], "", "", "")
        imp_object.file_type = ""
        imp_object.flow = ""
        imp_object.error_handling = ""
        imp_object.filepath = ""
        imp_object.config_name = ""
        self.assertIn('cmedit', imp_object.get_create_command())

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    def test_get_status_command__success(self, _):
        imp_object = CmImportLive([], "", "", "")
        imp_object.id = ""
        self.assertIn('cmedit', imp_object.get_status_command())

    @patch('enmutils_int.lib.cm_import.time.sleep', return_value=0)
    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.log.logger.debug')
    @patch('enmutils_int.lib.cm_import.CmImportLive.get_total_history_changes', return_value=10)
    def test_check_num_history_changes_match_expected__cli(self, mock_history, mock_debug, *_):
        imp_object = CmImportLive([], "", "", "")
        imp_object.id = ""
        imp_object.interface = None
        imp_object.check_num_history_changes_match_expected(10)
        self.assertEqual(1, mock_history.call_count)
        mock_debug.assert_called_with("Successfully checked the number of history changes applied to ENM")

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.log.logger.debug')
    @patch('enmutils_int.lib.cm_import.CmImportLive.history')
    def test_get_total_history_changes__success(self, mock_history, mock_debug, _):
        imp_object = CmImportLive([], "", "", "")
        response = Mock()
        response.get_output.return_value = [u'', u'1 change(s)']
        mock_history.return_value = response
        imp_object.get_total_history_changes(1)
        mock_debug.assert_called_with("Successfully retrieved HISTORY CHANGES for job id: '1' ")

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.CmImportLive.history')
    def test_get_total_history_changes__no_change_entry(self, mock_history, _):
        imp_object = CmImportLive([], "", "", "")
        response = Mock()
        response.get_output.return_value = [u'']
        mock_history.return_value = response
        self.assertRaises(GetTotalHistoryChangesError, imp_object.get_total_history_changes, 1)

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.log.logger.debug')
    @patch('enmutils_int.lib.cm_import.CmImportLive.history')
    def test_get_total_history_changes__raises_exception(self, mock_history, mock_debug, _):
        imp_object = CmImportLive([], "", "", "")
        response = Mock()
        response.get_output.side_effect = Exception("Err")
        mock_history.return_value = response
        self.assertRaises(Exception, imp_object.get_total_history_changes, 1)
        mock_debug.assert_called_with("ERROR WHEN RETRIEVING HISTORY CHANGES FOR JOB ID: '1'")

    @patch('enmutils_int.lib.cm_import.CmImportLive.__init__', return_value=None)
    def test_history__raise_exception(self, _):
        imp_object = CmImportLive([], "", "", "")
        user = Mock()
        imp_object.user = user
        user.enm_execute.side_effect = Exception("Error")
        self.assertRaises(Exception, imp_object.history, "id")

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.write_profile_nodes_recovery_commands_to_file')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.prepare_file')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager._set_values_to_default')
    @patch('enmutils_int.lib.cm_import.CmImportUpdateLive.__init__', return_value=None)
    def test_setup__attempt_recovery_update_live_success(self, *_):
        imp_mgr = ImportProfileContextManager("", "", "", "")
        imp_mgr.attempt_recovery = True
        imp_obj = CmImportUpdateLive({}, {}, "", "", "")
        imp_mgr.default_obj = imp_obj
        imp_mgr.modify_obj = Mock()
        profile = Mock()
        profile.teardown_list = []
        imp_mgr.profile = profile
        imp_mgr.setup()
        self.assertEqual(3, len(imp_mgr.profile.teardown_list))

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.__init__', return_value=None)
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager._exception_handling_cmimport_error')
    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager._cleanup_undo_files')
    def test_exception_handling__undo_iter(self, mock_clean_up, *_):
        imp_mgr = ImportProfileContextManager("", "", "")
        imp_mgr.profile = Mock()
        imp_mgr.exception_handling(CMImportError("Err"), Mock(), undo_iter=True)
        self.assertEqual(1, mock_clean_up.call_count)

    @patch('enmutils_int.lib.cm_import.ImportProfileContextManager.setup')
    @patch('enmutils_int.lib.cm_import.UndoOverNbi.remove_undo_job')
    def test_cleanup_undo_job__is_success(self, mock_remove, _):
        default_obj = Mock()
        default_obj.user = "user"
        imp_mgr = ImportProfileContextManager("", default_obj, "", undo_job_id=12)
        import_object = Mock()
        imp_mgr._cleanup_undo_job(import_object)
        self.assertEqual(0, import_object.mock_remove.call_count)

    @patch('time.sleep')
    @patch('enmutils_int.lib.cm_import.timestamp.get_human_readable_timestamp')
    @patch('enmutils_int.lib.cm_import.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.cm_import.CmImportLive.check_num_history_changes_match_expected')
    @patch('enmutils_int.lib.cm_import.CmImportLive.create_over_nbi')
    def test_import_flow_with_history_check__detects_cmimport_31(self, mock_create, mock_history_changes, *_):
        self.import_live_job_v1.name = "cmimport_31"
        self.import_live_job_v1.import_flow(history_check=True)
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_history_changes.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
