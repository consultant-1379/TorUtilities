#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow import CmExport11
from testslib import unit_test_utils


class Cmexport11UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(), Mock()]
        self.flow = CmExport11()
        self.flow.TOTAL_NODES = 5
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ['CM_REST_Administrator']
        self.flow.NUMBER_OF_EXPORTS = 2
        self.flow.FILETYPE = '3GPP'
        self.flow.TIMEOUT = 0.01
        self.flow.NUM_NODES_PER_BATCH = 30

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_calculate_the_number_of_sets_is_successful(self):
        self.assertEqual(1, self.flow.calculate_the_number_of_batches(self.nodes * 15))

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport')
    def test_create_export_objects_is_successful(self, mock_cm_export):
        self.flow.create_export_objects(user=self.user, nodes=self.nodes)
        self.assertEqual(mock_cm_export.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.log.logger.debug')
    def test_prepare_export_lists__success(self, mock_logger, *_):
        mock_export1, mock_export2 = Mock(), Mock()
        mock_export1.exists.return_value, mock_export2.exists.return_value = True, True
        mock_export1.nodes, mock_export2.nodes = ['node1', 'node2'], ['node3', 'node4']
        self.flow.prepare_export_lists([mock_export1, mock_export2])
        self.assertEquals(4, mock_logger.call_count)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.log.logger.debug')
    def test_prepare_export_lists__Exception(self, mock_logger, *_):
        mock_export1, mock_export2 = Mock(), Mock()
        mock_export1.create_over_nbi.side_effect, mock_export2.create_over_nbi.side_effect = Exception, Exception
        mock_export1.exists.return_value, mock_export2.exists.return_value = True, None
        mock_export1.nodes, mock_export2.nodes = ['node1', 'node2'], ['node3', 'node4']
        self.assertRaises(Exception, self.flow.prepare_export_lists([mock_export1, mock_export2]))
        self.assertEquals(2, mock_logger.call_count)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.prepare_export_lists',
           return_value=['mock_export1', 'mock_export2'])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.log.logger.debug')
    def test_create_export_jobs__continous_jobs(self, mock_logger, *_):
        self.flow.create_export_jobs([Mock(), Mock()])
        self.assertFalse(mock_logger.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.prepare_export_lists',
           return_value=['mock_export2', 'export'])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.add_error_as_exception')
    def test_create_export_jobs__sufficient_jobs(self, mock_add_error, mock_logger, *_):
        setattr(self.flow, "SCHEDULED_TIMES_STRINGS", True)
        self.flow.create_export_jobs([Mock(), Mock()])
        self.assertFalse(mock_add_error.called)
        self.assertFalse(mock_logger.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.prepare_export_lists',
           return_value=['mock_export2'])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.add_error_as_exception')
    def test_create_export_jobs__insufficient_jobs(self, mock_add_error, mock_logger, *_):
        setattr(self.flow, "SCHEDULED_TIMES_STRINGS", True)
        self.flow.create_export_jobs([Mock(), Mock()])
        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_logger.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.add_error_as_exception')
    def test_validate_export_jobs_is_successful(self, mock_add_error):
        cm_export_jobs = [Mock(), Mock()]
        self.flow.validate_export_jobs(cm_export_jobs)
        self.assertEqual(cm_export_jobs[0].validate_over_nbi.call_count, 1)
        self.assertEqual(cm_export_jobs[1].validate_over_nbi.call_count, 1)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.add_error_as_exception')
    def test_validate_export_jobs_adds_error_as_exception(self, mock_add_error, *_):
        cm_export_jobs = [Mock(), Mock()]
        cm_export_jobs[0].validate_over_nbi.side_effect = Exception
        self.flow.validate_export_jobs(cm_export_jobs)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.validate_export_jobs')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.create_export_objects')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.create_export_jobs')
    def test_execute_flow_is_successful(self, mock_create_jobs, mock_create_objects, mock_validate_jobs,
                                        mock_exchange_nodes, mock_nodes_list, *_):

        mock_nodes_list.return_value = self.nodes
        self.flow.execute_flow()
        self.assertTrue(mock_create_jobs.called)
        self.assertTrue(mock_create_objects.called)
        self.assertTrue(mock_validate_jobs.called)
        self.assertTrue(mock_exchange_nodes.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.validate_export_jobs')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.create_export_objects')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.create_export_jobs')
    def test_execute_flow__successful(self, *_):
        setattr(self.flow, 'SCHEDULED_TIMES_STRINGS', True)
        self.flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.create_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.get_nodes_list_by_attribute')
    def test_execute_flow_with_no_nodes_is_successful(self, mock_nodes_list, mock_exchange_nodes, *_):
        mock_nodes_list.return_value = []
        self.flow.execute_flow()
        self.assertTrue(mock_exchange_nodes.called)

    def test_calculate_the_number_of_batches(self):
        self.assertEqual(5, self.flow.calculate_the_number_of_batches([Mock()] * 150))
        self.assertEqual(5, self.flow.calculate_the_number_of_batches([Mock()] * 121))
        self.assertEqual(2, self.flow.calculate_the_number_of_batches([Mock()] * 31))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
