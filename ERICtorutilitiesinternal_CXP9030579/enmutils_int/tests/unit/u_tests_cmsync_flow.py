#!/usr/bin/env python
import unittest2
from mock import Mock, PropertyMock, patch
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib.exceptions import FailedNetsimOperation, MOPathMisMatch, EnvironError
from enmutils_int.lib.netsim_operations import AVCBurst, MCDBurst, Burst
from enmutils_int.lib.nrm_default_configurations.profile_cmds import BSC_AVC_BURST_MO_TYPE_SETTINGS
from enmutils_int.lib.profile_flows.cmsync_flows import cmsync_flow
from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import (CMSyncProfile, CmSyncFlow, CmSyncSetupFlow,
                                                                     CollectionSyncFlow, CMSync15Flow,
                                                                     CMSync23Flow, CMSync32Flow, CMSync24Flow,
                                                                     PersistedNotificationException, CmSyncNodeManager,
                                                                     CmSyncNotificationManager, EnmApplicationError)
from testslib import unit_test_utils

RNC_PATH = {"RNC03": ["ManagedElement=1,RncFunction=1,UtranCell=RNC03-8-3,GsmRelation=128"],
            "RNC04": ["ManagedElement=1,RncFunction=1,UtranCell=RNC02-8-3,GsmRelation=128",
                      "ManagedElement=1,RncFunction=1,UtranCell=RNC04-8-3,GsmRelation=128",
                      "ManagedElement=1,RncFunction=1,UtranCell=RNC04-8-3,GsmRelation=129"],
            "RNC05": ["ManagedElement=1,RncFunction=1,UtranCell=RNC05-8-3,GsmRelation=128"],
            "RNC06": ["ManagedElement=1,RncFunction=1,UtranCell=RNC06-8-3,GsmRelation=128"],
            "RNC07": ["ManagedElement=1,RncFunction=1,UtranCell=RNC06-8-3,GsmRelation=128"]}


class CmSyncNotificationManagerUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        notifications = [["RNC", "UtranCell", 12, 4], ["RNC", "UtranCell", 4, 0.5], ["ERBS", "EUtranCell", 3, 1],
                         ["RadioNode", "EUtranCell", 2, 4], ["RadioNode", "EUtranCell", 2, 4],
                         ["RadioNode", "EUtranCell", 2, 4]]
        allocated_nodes = {"RNC": [Mock()], "ERBS": [Mock(), Mock(), Mock()], "RadioNode": []}
        num_nodes = {"RNC": 6, "ERBS": 2}
        self.flow = CmSyncNotificationManager(notifications, allocated_nodes, "CMSYNC_02", num_nodes)
        self.notifications = [['RNC', 'Fach', 4, 4], ['RNC', 'Fach', 4, 0.11165000000000003],
                              ['RNC', 'GsmRelation', 12, 4],
                              ['RNC', 'Hsdsch', 4, 0.11165000000000003], ['RNC', 'UtranCell', 12, 4],
                              ['RNC', 'UtranCell', 4, 0.3349499999999992], ['RNC', 'Pch', 4, 4],
                              ['RNC', 'Pch', 4, 0.11165000000000003], ['RNC', 'Rach', 4, 4],
                              ['RNC', 'Rach', 4, 0.11165000000000003], ['ERBS', 'PmEventService', 7, 2],
                              ['ERBS', 'PmEventService', 2, 0.5492999999999997],
                              ['ERBS', 'ExternalEUtranCellFDD', 2, 2],
                              ['ERBS', 'ExternalEUtranCellFDD', 2, 0.5164499999999999],
                              ['ERBS', 'EUtranCellFDD', 25, 2], ['ERBS', 'EUtranCellFDD', 2, 0.16440000000000055],
                              ['ERBS', 'UtranCellRelation', 5, 2],
                              ['ERBS', 'UtranCellRelation', 2, 0.03289999999999971], ['ERBS', 'TermPointToENB', 7, 2],
                              ['ERBS', 'TermPointToENB', 2, 0.5492999999999997], ['ERBS', 'EUtranCellRelation', 2, 2],
                              ['ERBS', 'EUtranCellRelation', 2, 0.5164499999999999], ['ERBS', 'PmEventService', 1, 2],
                              ['ERBS', 'PmEventService', 2, 0.7430000000000001], ['ERBS', 'EUtranCellTDD', 5, 2],
                              ['ERBS', 'EUtranCellTDD', 2, 0.8099499999999997], ['ERBS', 'UtranCellRelation', 1, 2],
                              ['ERBS', 'UtranCellRelation', 2, 0.16199999999999992],
                              ['ERBS', 'ExternalEUtranCellTDD', 2, 0.581], ['ERBS', 'TermPointToENB', 1, 2],
                              ['ERBS', 'TermPointToENB', 2, 0.7430000000000001],
                              ['ERBS', 'EUtranCellRelation', 2, 0.581], ['RadioNode', 'PmEventService', 5, 2],
                              ['RadioNode', 'PmEventService', 2, 0.8300999999999998],
                              ['RadioNode', 'ExternalEUtranCellFDD', 1, 2],
                              ['RadioNode', 'ExternalEUtranCellFDD', 2, 0.9433499999999999],
                              ['RadioNode', 'EUtranCellFDD', 19, 2],
                              ['RadioNode', 'EUtranCellFDD', 2, 0.43370000000000175],
                              ['RadioNode', 'UtranCellRelation', 3, 2],
                              ['RadioNode', 'UtranCellRelation', 2, 0.8867500000000001],
                              ['RadioNode', 'TermPointToENB', 5, 2],
                              ['RadioNode', 'TermPointToENB', 2, 0.8300999999999998],
                              ['RadioNode', 'EUtranCellRelation', 1, 2],
                              ['RadioNode', 'EUtranCellRelation', 2, 0.9433499999999999],
                              ['RadioNode', 'PmEventService', 1, 2], ['RadioNode', 'PmEventService', 2, 0.37825],
                              ['RadioNode', 'EUtranCellTDD', 4, 2],
                              ['RadioNode', 'EUtranCellTDD', 2, 0.5941000000000001],
                              ['RadioNode', 'UtranCellRelation', 2, 0.9188],
                              ['RadioNode', 'ExternalEUtranCellTDD', 2, 0.4594], ['RadioNode', 'TermPointToENB', 1, 2],
                              ['RadioNode', 'TermPointToENB', 2, 0.37825],
                              ['RadioNode', 'EUtranCellRelation', 2, 0.4594]]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncNotificationManager.'
           'reduce_nodes_required_by_notification')
    def test_alter_notifications_if_under_allocation_of_nodes__succsss(self, mock_reduce):
        self.flow.num_nodes = {"RadioNode": 10}
        self.flow.allocated_nodes_dict = {"RadioNode": ["Node"] * 8}
        self.flow.alter_notifications_if_under_allocation_of_nodes()
        self.assertEqual(1, mock_reduce.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncNotificationManager.'
           'reduce_nodes_required_by_notification')
    def test_alter_notifications_if_under_allocation_of_nodes__too_many_nodes_allocated(self, mock_reduce):
        self.flow.num_nodes = {"RadioNode": 10}
        self.flow.allocated_nodes_dict = {"RadioNode": ["Node"] * 80}
        self.flow.alter_notifications_if_under_allocation_of_nodes()
        self.assertEqual(0, mock_reduce.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncNotificationManager.'
           'remove_invalid_notifications')
    def test_alter_notifications_if_under_allocation_of_nodes__removes_invalid(self, mock_remove):
        notify_mgr = CmSyncNotificationManager([], {}, "CMSYNC_01", {})
        notify_mgr.alter_notifications_if_under_allocation_of_nodes()
        self.assertEqual(1, mock_remove.call_count)

    def test_reduce_nodes_required_by_notification(self):
        rnc_expected = ['RNC', 'UtranCell', 4, 12]
        rnc1_expected = ['RNC', 'UtranCell', 2, 1.0]
        erbs_expected = ['ERBS', 'EUtranCell', 3, 1]
        self.assertListEqual(rnc_expected, self.flow.
                             reduce_nodes_required_by_notification(4, self.flow.notifications[:1])[0])
        self.assertListEqual(rnc1_expected, self.flow.
                             reduce_nodes_required_by_notification(2, self.flow.notifications[:2])[1])
        self.assertListEqual(erbs_expected, self.flow.
                             reduce_nodes_required_by_notification(3, self.flow.notifications)[2])
        self.assertListEqual(self.flow.reduce_nodes_required_by_notification(3, self.flow.notifications[-1:]), [])

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    def test_notification_summary__success(self, mock_debug, _):
        expected = "\nExpected daily notification generation for profile: CMSYNC_02 is 1321685.28"
        self.flow.expected_notification_summary(300, 7200, self.notifications)
        mock_debug.assert_called_with(expected)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    def test_notification_summary_after_notification_alteration__rate_change(self, mock_debug, _):
        expected = "\nExpected daily notification generation for profile: CMSYNC_06 is 1375650.36"
        self.flow.notifications = self.notifications
        self.flow.allocated_nodes_dict = {"ERBS": [Mock()] * 80, "RadioNode": [Mock()] * 64, "RNC": [Mock()] * 24}
        self.flow.profile_name = "CMSYNC_06"
        self.flow.num_nodes = {"ERBS": 80, "RadioNode": 64, "RNC": 64}
        notifications = self.flow.alter_notifications_if_under_allocation_of_nodes()
        self.flow.expected_notification_summary(300, 7200, notifications)
        mock_debug.assert_called_with(expected)

    def test_remove_invalid_notifications__erbs_rate(self):
        expected = [['ERBS', 'MO', 76, 0.04], ['ERBS', 'MO', 1, 0.04]]
        notify_mgr = CmSyncNotificationManager([['ERBS', 'MO', 76, 0.04], ['ERBS', 'MO', 0.04, 0.875]],
                                               {}, "CMSYNC_01", {})
        self.assertListEqual(expected, notify_mgr.remove_invalid_notifications())

    def test_remove_invalid_notifications__radio_node_rate(self):
        expected = [['RadioNode', 'MO', 76, 0.5], ['RadioNode', 'MO', 1, 0.5]]
        notify_mgr = CmSyncNotificationManager([['RadioNode', 'MO', 76, 0.5], ['RadioNode', 'MO', 0.2, 0.875]],
                                               {}, "CMSYNC_01", {})
        self.assertListEqual(expected, notify_mgr.remove_invalid_notifications())


class CmSyncFlowUnitTests(ParameterizedTestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = CmSyncFlow()
        self.flow.BURST_TYPE = "AVC"
        self.flow.BURST_DURATION = 1800
        self.flow.SCHEDULE_SLEEP = 0
        self.notification_info = {
            "ERBS": [
                {"node_type": "ERBS", "mo_type_name": "UtranCellRelation",
                 "mo_path": "ComTop:ManagedElement=%NENAME%,Lrat:ENodeBFunction=1",
                 "parent_mo_names": None, "mo_attribute": "isRemoveAllowed", "mo_values": ["true", "false"]}
            ],
            "RNC": [
                {"node_type": "RNC", "mo_type_name": "UtranCell", "mo_path": None,
                 "parent_mo_names": ["ManagedElement", "RncFunction"],
                 "mo_attribute": "operationalState", "mo_values": ["ENABLED", "DISABLED"]}
            ],
            "RadioNode": [
                {"node_type": "RadioNode", "mo_type_name": "TermPointToENB",
                 "mo_path": "ComTop:ManagedElement=%NENAME%,Lrat:ENodeBFunction=1",
                 "parent_mo_names": None, "mo_attribute": "isRemoveAllowed", "mo_values": ["true", "false"]},

                {"node_type": "RadioNode", "mo_type_name": "GNBCUCP:NRCellRelation",
                 "mo_path": None,
                 "parent_mo_names": ["ComTop:ManagedElement", "GNBCUCP:GNBCUCPFunction", "GNBCUCP:NRCellCU"],
                 "mo_attribute": "includeInSIB", "mo_values": ["true", "false"]},

                {"node_type": "RadioNode", "mo_type_name": "GNBDU:NRSectorCarrier",
                 "mo_path": None, "parent_mo_names": ["ComTop:ManagedElement", "GNBDU:GNBDUFunction"],
                 "mo_attribute": "altitude", "mo_values": [10, 20, 30]},

                {"node_type": "RadioNode", "mo_type_name": "EUtranCellFDD", "mo_path": None,
                 "parent_mo_names": ["ComTop:ManagedElement", "Lrat:ENodeBFunction", "Lrat:EUtranCellFDD"],
                 "mo_attribute": "userLabel", "mo_values": [0, 1]},
                {
                    "mo_type_name": "GNBCUUP:S1ULink",
                    "parent_mo_names": ["ComTop:ManagedElement", "GNBCUUP:GNBCUUPFunction", "GNBCUUP:S1UTermination"],
                    "create_from_parent_type": None
                }
            ]
        }

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow."
           "CmSyncNotificationManager.expected_notification_summary")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow."
           "CmSyncFlow.get_notification_information_for_profile", return_value=[["ERBS", "EUtranCell", 1, 2]])
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow."
           "CmSyncNotificationManager.alter_notifications_if_under_allocation_of_nodes")
    def test_get_and_manage_notifications__successfully(self, mock_alter_notifications_if_under_allocated, *_):
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 1, "RadioNode": 0}
        self.flow.NAME = "CMSYNC_02"
        self.flow.get_and_manage_notifications()
        self.assertTrue(mock_alter_notifications_if_under_allocated.called)

    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow."
           "CmSyncNotificationManager.expected_notification_summary")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow."
           "CmSyncFlow.get_notification_information_for_profile", return_value=[])
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow."
           "CmSyncNotificationManager.alter_notifications_if_under_allocation_of_nodes")
    def test_get_and_manage_notifications__no_notifications(self, *_):
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 1, "RadioNode": 0}
        self.flow.NAME = "CMSYNC_02"
        self.assertRaises(EnvironError, self.flow.get_and_manage_notifications)

    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_and_execute_threads")
    def test_execute_threads_for_notifications__successfully_executes_threads(self, mock_create_and_execute, _):
        mock_notifications = [["ERBS", "EUtranCell", 1, 2]]
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 1, "RadioNode": 0}
        self.flow.NAME = "CMSYNC_02"
        self.flow.execute_threads_for_notifications(mock_notifications)
        self.assertTrue(mock_create_and_execute.call_count == 2)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.time', return_value=1)
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_and_execute_threads",
           side_effect=KeyboardInterrupt("Interrupt"))
    def test_execute_threads_for_notifications__execute_threads_raises_keyboard_interupt(self, *_):
        mock_notifications = [["ERBS", "EUtranCell", 1, 2]]
        self.flow.START_SLEEP_TIME = 0
        self.flow.BURST_DURATION = 1
        self.flow.TEARDOWN_OBJECTS = [Mock()]
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 1, "RadioNode": 0}
        self.flow.NAME = "CMSYNC_02"
        self.assertRaises(KeyboardInterrupt, self.flow.execute_threads_for_notifications, mock_notifications)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.time', return_value=100)
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_and_execute_threads",
           side_effect=KeyboardInterrupt("Interrupt"))
    def test_execute_threads_for_notifications__bursts_have_expired(self, *_):
        mock_notifications = [["ERBS", "EUtranCell", 1, 2]]
        self.flow.START_SLEEP_TIME = 1
        self.flow.BURST_DURATION = 100
        self.flow.TEARDOWN_OBJECTS = [Mock()]
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 1, "RadioNode": 0}
        self.flow.NAME = "CMSYNC_02"
        self.assertRaises(KeyboardInterrupt, self.flow.execute_threads_for_notifications, mock_notifications)

    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.distribute_large_notification_groups")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.execute_threads_for_notifications")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_and_manage_notifications")
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.read_gsm_relations_from_file_and_sort')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_and_set_num_nodes_from_persistence')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.sleep_until_next_scheduled_iteration')
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow._sleep_exchange_nodes_and_remove_bursts")
    def test_execute_flow__successfully_executes(self, mock_sleep_change_remove_nodes, mock_sleep_first_run, *_):
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 1, "RadioNode": 0}
        self.flow.SCHEDULED_TIMES_STRINGS = ['11:45:00']
        self.flow.NAME = "CMSYNC_01"
        self.flow.execute_flow()
        self.assertEqual(mock_sleep_first_run.call_count, 1)
        self.assertEqual(mock_sleep_change_remove_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.distribute_large_notification_groups")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.execute_threads_for_notifications")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_and_manage_notifications",
           side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.read_gsm_relations_from_file_and_sort')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_and_set_num_nodes_from_persistence')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.sleep_until_next_scheduled_iteration')
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.sleep")
    @patch("enmutils_int.lib.profile.Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow._sleep_exchange_nodes_and_remove_bursts")
    def test_execute_flow__exception_raised(self, mock_sleep_change_remove_nodes, mock_add_error_exception, *_):
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 1, "RadioNode": 0}
        self.flow.NAME = "CMSYNC_01"
        self.flow.execute_flow()
        self.assertEqual(mock_sleep_change_remove_nodes.call_count, 0)
        self.assertEqual(mock_add_error_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.distribute_large_notification_groups")
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.sleep_until_next_scheduled_iteration')
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.execute_threads_for_notifications")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_and_manage_notifications")
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_and_set_num_nodes_from_persistence')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.keep_running', side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow._sleep_exchange_nodes_and_remove_bursts")
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.read_gsm_relations_from_file_and_sort')
    def test_execute_flow__no_rnc_in_num_nodes(self, mock_read_gsm_relations, *_):
        self.flow.SCHEDULED_TIMES_STRINGS = ["time"]
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 0, "RadioNode": 0}
        self.flow.NAME = "CMSYNC_01"
        self.flow.execute_flow()
        self.assertEqual(mock_read_gsm_relations.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.chunks', return_value=[])
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_and_execute_threads")
    def test_threads_for_notifications__burst_size_is_zero(self, mock_execute_threads, *_):
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 1, "RadioNode": 0}
        self.flow.NAME = "CMSYNC_01"
        self.flow.execute_threads_for_notifications([[Mock()]])
        self.assertEqual(mock_execute_threads.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.chunks', return_value=[])
    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_and_execute_threads")
    def test_execute_threads_for_notifications__is_successful_when_burst_chunk_size_is_non_zero(
            self, mock_create_and_execute_threads, *_):
        def set_bursts_to_non_zero(*args, **kwargs):
            self.flow.BURSTS = [Mock()] * 12
        self.flow.NUM_NODES = {"ERBS": 1, "RNC": 1, "RadioNode": 0}
        self.flow.NAME = "CMSYNC_01"
        mock_create_and_execute_threads.side_effect = set_bursts_to_non_zero
        self.flow.execute_threads_for_notifications([[Mock()]])
        self.assertEqual(mock_create_and_execute_threads.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.persistence.get', return_value={"CMSYNC_01": [["RNC", "UtranCell", 4, 2]]})
    def test_get_notification_information_for_profile(self, *_):
        expected = [["RNC", "UtranCell", 4, 2]]
        self.flow.NAME = "CMSYNC_01"
        self.assertEqual(expected, self.flow.get_notification_information_for_profile())

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.persistence.get', return_value=False)
    def test_get_notification_information_for_profile_raises_exception(self, *_):
        self.assertRaises(PersistedNotificationException, self.flow.get_notification_information_for_profile)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_mo_types', return_value=[])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.update_radio_nodes_mo_name')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.create_bursts')
    def test_task_set__starts_bursts(self, mock_create_bursts, mock_get_nodes, mock_update, *_):
        mock_get_nodes.return_value = [Mock()]
        self.flow.task_set(['ERBS', "EUtranCellFDD", 2, 0.5], self.flow)
        self.assertEqual(1, mock_create_bursts.call_count)
        self.assertEqual(1, mock_update.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.start_bursts')
    def test_task_set__logs_no_nodes(self, mock_start_bursts, mock_get_nodes, mock_debug):
        mock_get_nodes.return_value = []
        self.flow.task_set(['ERBS', "EUtranCellFDD", 2, 0.5], self.flow)
        self.assertEqual(0, mock_start_bursts.call_count)
        mock_debug.assert_called_with("No available nodes, to generate Notification: NeType [ERBS], Mo [EUtranCellFDD],"
                                      " Number of nodes [2] Rate per second [0.5]. nothing to do.")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.start_bursts')
    def test_start_all_bursts__starts_bursts(self, mock_start_bursts):
        self.flow.start_all_bursts(['ERBS', "EUtranCellFDD", 2, 0.5], self.flow)
        self.assertEqual(1, mock_start_bursts.call_count)

    def test_update_radio_nodes_mo_name__updates_mo(self):
        self.assertEqual("Lrat:PmEventService", self.flow.update_radio_nodes_mo_name("RadioNode", "PmEventService"))

    def test_update_radio_nodes_mo_name__ignores_non_radionodes(self):
        self.assertEqual("PmEventService", self.flow.update_radio_nodes_mo_name("ERBS", "PmEventService"))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.build_mo_type_instances')
    def test_get_mo_type_instances__erbs_builds_mo(self, mock_build_mo):
        self.flow.get_mo_type_instances("ERBS", "mo", [], 0, self.notification_info)
        self.assertEqual(1, mock_build_mo.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_rnc_mo_type')
    def test_get_mo_type_instances__rnc_builds_mo(self, mock_get_rnc_mo_type, mock_add_error):
        cmsync_flow.GSM_PATHS = ["Path"]
        mock_get_rnc_mo_type.side_effect = [MOPathMisMatch("Error"), []]
        self.flow.get_mo_type_instances("RNC", "mo", ["node", "node1"], 0, self.notification_info)
        self.assertEqual(2, mock_get_rnc_mo_type.call_count)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.build_mo_type_instances')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_notification_info_for_5g_nodes')
    def test_get_mo_type_instances__is_successful_for_5g_radio_nodes(self, mock_get_notification_info, _):
        ne_type = 'RadioNode'
        mo = 'EUtranCellFDD'
        node, node1 = Mock(), Mock()
        node.node_id = "gNodeB01"
        node1.node_id = "gNodeB02"
        nodes = [node, node1]
        notification_rate = 0
        notification_info = self.notification_info
        self.flow.get_mo_type_instances(ne_type, mo, nodes, notification_rate, notification_info)
        self.assertEqual(2, mock_get_notification_info.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.build_mo_type_instances')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_notification_info_for_5g_nodes')
    def test_get_mo_type_instances__doesnt_call_5g_notification_info_for_4g_radio_nodes(self,
                                                                                        mock_get_notification_info, _):
        ne_type = 'RadioNode'
        mo = 'EUtranCellFDD'
        node = Mock()
        node.node_id = "dg201"
        nodes = [node]
        notification_rate = 0
        notification_info = self.notification_info
        self.flow.get_mo_type_instances(ne_type, mo, nodes, notification_rate, notification_info)
        self.assertEqual(0, mock_get_notification_info.call_count)

    def test_get_notification_info_for_5g_nodes__success(self):
        mo = 'Lrat:TermPointToENB'
        ne_type = 'RadioNode'
        self.flow.NOTIFICATION_INFO = self.notification_info
        expected = self.notification_info.get('RadioNode')[1]
        self.assertEqual(expected, self.flow.get_notification_info_for_5g_nodes(mo, ne_type))

    def test_get_notification_info_for_5g_nodes__returns_null(self):
        mo = 'ExternalEUtranCellFDD'
        ne_type = 'RadioNode'
        self.flow.NOTIFICATION_INFO = self.notification_info
        self.assertEqual(None, self.flow.get_notification_info_for_5g_nodes(mo, ne_type))

    @patch("enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.choice",
           return_value="GNBCUUP:S1ULink")
    def test_get_notification_info_for_5g_nodes__success_for_cmsync_01(self, _):
        mo = 'ExternalEUtranCellFDD'
        ne_type = 'RadioNode'
        self.flow.NAME = 'CMSYNC_01'
        self.flow.NOTIFICATION_INFO = self.notification_info
        expected = self.notification_info.get('RadioNode')[4]
        self.assertEqual(expected, self.flow.get_notification_info_for_5g_nodes(mo, ne_type))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_mo_type_instances')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.'
           'update_notification_values_for_tdd_cell_nodes')
    def test_get_mo_types__fdd_nodes(self, mock_tdd, mock_get_mo):
        ne = "RadioNode"
        mo = "EUtranCellFDD"
        nodes = [Mock(lte_cell_type="FDD", simulation="LTD-DG2-FDD")]
        notification_rate = 0
        mock_tdd.return_value = (mo, self.notification_info)
        self.flow.NOTIFICATION_INFO = self.notification_info
        self.flow.get_mo_types(ne, mo, nodes, notification_rate)
        self.assertEqual(0, mock_tdd.call_count)
        self.assertEqual(1, mock_get_mo.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_mo_type_instances')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.'
           'update_notification_values_for_tdd_cell_nodes')
    def test_get_mo_types__5g_nodes(self, mock_tdd, mock_get_mo):
        ne = "RadioNode"
        mo = "GNBCUCP:NRCellRelation"
        nodes = [Mock(lte_cell_type=None, simulation="NR")]
        notification_rate = 0
        mock_tdd.return_value = (mo, self.notification_info)
        self.flow.NOTIFICATION_INFO = self.notification_info
        self.flow.get_mo_types(ne, mo, nodes, notification_rate)
        self.assertEqual(0, mock_tdd.call_count)
        self.assertEqual(1, mock_get_mo.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_mo_type_instances')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.'
           'update_notification_values_for_tdd_cell_nodes')
    def test_get_mo_types__detects_tdd_nodes_no_fdd_nodes(self, mock_tdd, _):
        ne = "RadioNode"
        mo = "EUtranCellFDD"
        nodes = [Mock(lte_cell_type="TDD")]
        notification_rate = 0
        mock_tdd.return_value = (mo, self.notification_info)
        self.flow.NOTIFICATION_INFO = self.notification_info
        self.flow.get_mo_types(ne, mo, nodes, notification_rate)
        self.assertEqual(1, mock_tdd.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_mo_type_instances')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.'
           'update_notification_values_for_tdd_cell_nodes')
    def test_get_mo_types__detects_tdd_nodes_if_tdd_in_simulation(self, mock_tdd, _):
        ne = "RadioNode"
        mo = "EUtranCellFDD"
        nodes = [Mock(lte_cell_type=None, simulation="LTE-DG2-TDD")]
        notification_rate = 0
        mock_tdd.return_value = (mo, self.notification_info)
        self.flow.NOTIFICATION_INFO = self.notification_info
        self.flow.get_mo_types(ne, mo, nodes, notification_rate)
        self.assertEqual(1, mock_tdd.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_mo_type_instances')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.'
           'update_notification_values_for_tdd_cell_nodes')
    def test_get_mo_types__detects_tdd_and_fdd_nodes(self, mock_tdd, mock_get_mo):
        ne = "RadioNode"
        mo = "EUtranCellFDD"
        nodes = [Mock(lte_cell_type="TDD", simulation="LTE-DG2-TDD"),
                 Mock(lte_cell_type="FDD", simulation="LTE-DG2-FDD")]
        notification_rate = 0
        mock_tdd.return_value = (mo, self.notification_info)
        self.flow.NOTIFICATION_INFO = self.notification_info
        self.flow.get_mo_types(ne, mo, nodes, notification_rate)
        self.assertEqual(1, mock_tdd.call_count)
        self.assertEqual(2, mock_get_mo.call_count)

    def test_get_mo_types_handles__no_matching_mo(self, *_):
        ne = "ERBS"
        nodes = [Mock()]
        notification_rate = 0
        self.flow.NOTIFICATION_INFO = self.notification_info
        self.assertListEqual(self.flow.get_mo_types(ne, "NoMO", nodes, notification_rate), [])

    def test_update_notification_values_for_tdd_cell_nodes__updates_notifications_for_tdd_bursts(self):
        expected_mo = 'EUtranCellTDD'
        expected_notification_info = {'mo_values': [0, 1],
                                      'mo_attribute': 'userLabel',
                                      'node_type': 'RadioNode', 'mo_path': None,
                                      'parent_mo_names':
                                          ['ComTop:ManagedElement', 'Lrat:ENodeBFunction', 'Lrat:EUtranCellTDD'],
                                      'mo_type_name': 'EUtranCellTDD'}
        result = self.flow.update_notification_values_for_tdd_cell_nodes("EUtranCellFDD",
                                                                         self.notification_info.get('RadioNode')[-2])
        self.assertEqual(expected_mo, result[0])
        self.assertDictEqual(expected_notification_info, result[1])

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_mandatory_mcd_data_attributes',
           return_value={})
    def test_create_bursts_creates_correct_burst_types(self, *_):
        self.flow.NAME = "CMSYNC_02"
        self.flow.BURST_TYPE = "MCD"
        mo_type = Mock()
        mo_type.nodes = [Mock()]
        mo_type.mos = ["EUtranCellFDD"]
        bursts = self.flow.create_bursts([mo_type], 2)
        self.assertTrue(isinstance(bursts[0], MCDBurst))
        self.flow.BURST_TYPE = "AVC"
        mo_type.mo_path = "PathToMo"
        mo_type.mo_attribute = "Attr"
        mo_type.mo_values = "abc"
        bursts = self.flow.create_bursts([mo_type], 2)
        self.assertTrue(isinstance(bursts[0], AVCBurst))

    def test_create_bursts_handles_no_notifications(self):
        bursts = self.flow.create_bursts([], 2)
        self.assertListEqual([], bursts)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.add_error_as_exception')
    def test_start_bursts_adds_error_on_exception(self, mock_add_error_as_exception, mock_debug):
        burst = Mock()
        burst.start.side_effect = Exception("Some exception")
        burst.nodes = [Mock()]
        self.flow.BURST_TYPE = "MCD"
        self.flow.NAME = "CMSYNC_01"
        self.flow.start_bursts([burst])
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertEqual(mock_debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.add_error_as_exception')
    def test_start_bursts_adds_error_on_failed_netsim_operation(self, mock_add_error_as_exception, mock_debug):
        burst = Mock()
        burst.start.side_effect = FailedNetsimOperation(command="Command", nodes=[Mock()])
        burst.nodes = [Mock()]
        self.flow.BURST_TYPE = "MCD"
        self.flow.NAME = "CMSYNC_01"
        self.flow.start_bursts([burst])
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.add_error_as_exception')
    def test_start_burst__adds_netsim_error_no_failed_nodes(self, mock_add_error_as_exception, mock_debug):
        burst = Mock()
        burst.start.side_effect = FailedNetsimOperation(command="Command", nodes=[])
        burst.nodes = [Mock()]
        self.flow.BURST_TYPE = "AVC"
        self.flow.NAME = "CMSYNC_15"
        self.flow.start_bursts([burst])
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_debug.called)

    def test_start_bursts__adds_successful_burst_to_teardown(self):
        burst = Mock()
        burst.start.side_effect = None
        burst.nodes = [Mock()]
        self.flow.TEARDOWN_OBJECTS = []
        self.flow.NAME = "CMSYNC_01"
        self.assertEqual(0, len(self.flow.TEARDOWN_OBJECTS))
        self.flow.start_bursts([burst])
        self.assertEqual(1, len(self.flow.TEARDOWN_OBJECTS))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.add_error_as_exception')
    def test_start_bursts_handles_empty_bursts(self, mock_add_error_as_exception):
        self.flow.start_bursts([])
        self.assertFalse(mock_add_error_as_exception.called)

    def test_remove_unavailable_nodes(self):
        ne, nodes = "ERBS", ["node1", "node", "node2"]
        cmsync_flow.AVAILABLE_NODES_DICT = {ne: nodes}
        self.flow.remove_unavailable_nodes(ne, nodes[:2])
        self.assertListEqual(cmsync_flow.AVAILABLE_NODES_DICT.get(ne), [nodes[-1]])

    def test_remove_unavailable_nodes_not_called_if_under_allocated(self):
        ne, nodes = "ERBS", ["node1", "node", "node2"]
        cmsync_flow.AVAILABLE_NODES_DICT = {ne: nodes}
        self.flow.remove_unavailable_nodes(ne, nodes)
        self.assertDictEqual({ne: nodes}, cmsync_flow.AVAILABLE_NODES_DICT)

    def test_remove_unavailable_nodes_avoids_value_error(self):
        ne, nodes = "ERBS", ["node1", "node", "node2"]
        cmsync_flow.AVAILABLE_NODES_DICT = {ne: nodes}
        self.flow.remove_unavailable_nodes(ne, ["node1", "nodeNotPresent"])

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.MCDBurst.__init__')
    def test__sleep_exchange_nodes_and_remove_bursts__remove_bursts(self, *_):
        cmsync_flow.CREATED_EXTERNAL_ENODEB_FUNCTION_MOS = {}
        mcd = Burst([Mock()], "1234")
        self.flow.teardown_list = [Mock(), mcd]
        self.flow._sleep_exchange_nodes_and_remove_bursts()

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.'
           'delete_created_external_enodeb_function_mos')
    def test__sleep_exchange_nodes_and_remove_bursts__deletes_created_mos(self, mock_delete, *_):
        cmsync_flow.CREATED_EXTERNAL_ENODEB_FUNCTION_MOS = {"NODE": ["FDN"]}
        self.flow._sleep_exchange_nodes_and_remove_bursts()
        self.assertEqual(1, mock_delete.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.choice')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.mutexer')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.remove_unavailable_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    def test_get_nodes__returns_nodes(self, mock_debug, *_):
        cmsync_flow.AVAILABLE_NODES_DICT = {"ERBS": [Mock()] * 12}
        nodes = self.flow.get_nodes("ERBS", 10)
        self.assertEqual(len(nodes), 10)
        self.assertEqual(mock_debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.choice')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.mutexer')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.remove_unavailable_nodes')
    def test_get_nodes__returns_all_available_nodes_if_less_than_available(self, mock_remove, *_):
        cmsync_flow.AVAILABLE_NODES_DICT = {"ERBS": [Mock()] * 5}
        nodes = self.flow.get_nodes("ERBS", 10)
        self.assertEqual(len(nodes), 5)
        self.assertEqual(0, mock_remove.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.choice')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.mutexer')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.remove_unavailable_nodes')
    def test_get_nodes__removes_remaining_nodes_if_cmsync_01(self, mock_remove, *_):
        ne_type = "ERBS"
        cmsync_flow.AVAILABLE_NODES_DICT = {ne_type: [Mock()] * 5}
        self.flow.NAME = "CMSYNC_01"
        nodes = self.flow.get_nodes(ne_type, 10)
        self.assertEqual(len(nodes), 5)
        self.assertEqual(1, mock_remove.call_count)
        mock_remove.assert_called_with(ne_type, cmsync_flow.AVAILABLE_NODES_DICT.get(ne_type), empty_list=True)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.sample', side_effect=Exception("Exception"))
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.mutexer')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.remove_unavailable_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    def test_get_nodes_handles_exception(self, mock_debug, *_):
        cmsync_flow.AVAILABLE_NODES_DICT = {"ERBS": [Mock()] * 2}
        self.flow.get_nodes("ERBS", 1)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.filesystem.get_lines_from_file')
    def test_read_gsm_relations_from_file_and_sort(self, mock_get_lines_from_file):
        mock_get_lines_from_file.return_value = ["ManagedElement=1,RncFunction=1,UtranCell=RNC12-94-3",
                                                 "ManagedElement=1,RncFunction=1,UtranCell=RNC12-94-2",
                                                 "ManagedElement=1,RncFunction=1,UtranCell=RNC12-94-1",
                                                 "ManagedElement=1,RncFunction=1,UtranCell=RNC11-94-1",
                                                 "ManagedElement=1,RncFunction=1,UtranCell=RNC21-94-1",
                                                 "ManagedElement=1,RncFunction=1,UtranCell=RNC01-94-1",
                                                 "ManagedElement=1,RncFunction=1,UtranCell=RNC21-95-1"]

        expected = {'RNC01': ['ManagedElement=1,RncFunction=1,UtranCell=RNC01-94-1'],
                    'RNC11': ['ManagedElement=1,RncFunction=1,UtranCell=RNC11-94-1'],
                    'RNC21': ['ManagedElement=1,RncFunction=1,UtranCell=RNC21-94-1',
                              'ManagedElement=1,RncFunction=1,UtranCell=RNC21-95-1'],
                    'RNC12': ['ManagedElement=1,RncFunction=1,UtranCell=RNC12-94-3',
                              'ManagedElement=1,RncFunction=1,UtranCell=RNC12-94-2',
                              'ManagedElement=1,RncFunction=1,UtranCell=RNC12-94-1']}
        self.flow.read_gsm_relations_from_file_and_sort()
        self.assertDictEqual(expected, cmsync_flow.GSM_PATHS)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.persist')
    @patch('enmutils_int.lib.cmsync_mo_info.persistence.get',
           return_value={"CMSYNC_01": {"ERBS": 1, "RadioNode": 1, "RNC": 1}})
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncNodeManager.allocate_nodes_to_profile')
    def test_get_and_set_num_nodes_from_persistence__updates_num_nodes(self, *_):
        expected = {"ERBS": 1, "RadioNode": 1, "RNC": 1}
        self.flow.NAME = "CMSYNC_01"
        self.flow.get_and_set_num_nodes_from_persistence()
        self.assertEqual(expected, getattr(self.flow, 'NUM_NODES', {}))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.persist')
    @patch('enmutils_int.lib.cmsync_mo_info.persistence.get',
           return_value={"CMSYNC_01": {"ERBS": 1, "RadioNode": 1, "RNC": 1}})
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncNodeManager.allocate_nodes_to_profile')
    def test_get_and_set_num_nodes_from_persistence__calls_allocate(
            self, mock_allocate_nodes_to_profile, *_):
        self.flow.NAME = "CMSYNC_01"
        self.flow.get_and_set_num_nodes_from_persistence()
        self.assertEqual(1, mock_allocate_nodes_to_profile.call_count)

    @patch('enmutils_int.lib.cmsync_mo_info.persistence.get', return_value=False)
    def test_get_and_set_num_nodes_from_persistence__raises_exception(self, *_):
        self.assertRaises(PersistedNotificationException, self.flow.get_and_set_num_nodes_from_persistence)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.mutexer.mutex')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.validate_rnc_mo_path')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.sample')
    def test_get_rnc_path__rach(self, mock_sample, *_):
        cmsync_flow.GSM_PATHS = RNC_PATH
        cmsync_flow.RNC_MO_IDS = {"Rach": 1}
        mock_sample.return_value = RNC_PATH.get("RNC06")
        mo_info = {"mo_path": None, "parent_mo_names": ["RncFunction", "UtranCell"]}
        expected = "ManagedElement=1,RncFunction=1,UtranCell=RNC06-8-3,Rach=1"
        self.assertEqual(self.flow.get_rnc_path_avc_burst("RNC06", mo_info, "Rach").get('mo_path'), expected)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.mutexer.mutex')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.validate_rnc_mo_path')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.sample')
    def test_get_rnc_path_avc_burst__gsm_relation(self, mock_sample, *_):
        cmsync_flow.GSM_PATHS = RNC_PATH
        mock_sample.return_value = RNC_PATH.get("RNC03")
        mo_info = {"mo_path": None, "parent_mo_names": ["RncFunction", "UtranCell"]}
        expected = "ManagedElement=1,RncFunction=1,UtranCell=RNC03-8-3,GsmRelation=128"
        self.assertEqual(self.flow.get_rnc_path_avc_burst("RNC03", mo_info, "GsmRelation").get('mo_path'), expected)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.mutexer.mutex')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.validate_rnc_mo_path')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.sample')
    def test_get_rnc_path__utrancell(self, mock_sample, *_):
        cmsync_flow.GSM_PATHS = RNC_PATH
        mock_sample.return_value = RNC_PATH.get("RNC04")
        mo_info = {"mo_path": None, "parent_mo_names": ["RncFunction", "UtranCell"]}
        expected = "ManagedElement=1,RncFunction=1,UtranCell=RNC04-8-3"
        self.assertEqual(self.flow.get_rnc_path_avc_burst("RNC04", mo_info, "UtranCell").get('mo_path'), expected)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.mutexer.mutex')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.validate_rnc_mo_path')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.sample')
    def test_get_rnc_path_gsm_relation_path__raises_mo_path_mismatch(self, mock_sample, *_):
        cmsync_flow.GSM_PATHS = RNC_PATH
        mock_sample.return_value = RNC_PATH.get("RNC07")
        mo_info = {"mo_path": None, "parent_mo_names": ["RncFunction", "UtranCell"]}
        self.assertRaises(MOPathMisMatch, self.flow.get_rnc_path_avc_burst, "RNC07", mo_info, "GsmRelation")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.mutexer.mutex')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.validate_rnc_mo_path')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.random.sample')
    def test_get_rnc_path_gsm_relation_path__none_if_no_entry(self, mock_sample, *_):
        cmsync_flow.GSM_PATHS = RNC_PATH
        mo_info = {"mo_path": None, "parent_mo_names": ["RncFunction", "UtranCell"]}
        self.assertEqual(self.flow.get_rnc_path_avc_burst("RNC08", mo_info, "GsmRelation").get('mo_path'), None)
        self.assertEqual(0, mock_sample.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_rnc_path_avc_burst')
    def test_set_rnc_path__has_no_impact_mcd_bursts(self, mock_get_rnc_path_avc_burst):
        self.flow.BURST_TYPE = "MCD"
        mo_info = {"mo_path": None, "parent_mo_names": ["RncFunction", "UtranCell"]}
        self.flow.set_rnc_path("LTE01", "Rach", mo_info)
        self.assertEqual(0, mock_get_rnc_path_avc_burst.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.sleep', return_value=lambda: None)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_rnc_path_avc_burst',
           side_effect=[MOPathMisMatch, None])
    def test_set_rnc_path__retries_on_mismatch(self, mock_get_rnc_path_avc_burst, _):
        self.flow.BURST_TYPE = "AVC"
        mo_info = {"mo_path": None, "parent_mo_names": ["RncFunction", "UtranCell"]}
        self.flow.set_rnc_path("LTE01", "Rach", mo_info)
        self.assertEqual(2, mock_get_rnc_path_avc_burst.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.build_mo_type_instances')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.set_rnc_path')
    def test_get_rnc_mo_type__success(self, mock_rnc_path, mock_mo_types):
        node = Mock()
        self.flow.get_rnc_mo_type("RNC", "Fach", node, 4, {"mo_path": None})
        self.assertEqual(1, mock_rnc_path.call_count)
        self.assertEqual(1, mock_mo_types.call_count)

    def test_validate_rnc_mo_path__success(self):
        self.assertRaises(MOPathMisMatch, self.flow.validate_rnc_mo_path, "RNC06",
                          "ManagedElement=1,UtranCell=RNC21-345,Rach")
        self.flow.validate_rnc_mo_path("RNC06", "")
        self.flow.validate_rnc_mo_path("RNC06", "ManagedElement=1,UtranCell=RNC06-345,Rach")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_random_string')
    def test_random_mo_values__should_return_list_of_random_values(self, mock_random):
        mock_random.return_value = "str"
        self.assertEquals(self.flow.random_mo_values(mo_value=["mo1_abc", "mo2_cdf"]), ['mo1_str', 'mo2_str'])

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.AVCBurst')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.random_mo_values')
    def test_create_bursts__success(self, mock_random, _):
        self.flow.BURST_TYPE = "AVC"
        mo_type = Mock()
        mo1 = mo_type
        setattr(mo1, 'mo_attribute', 'userLabel')
        self.flow.NAME = "CMSYNC_02"
        self.flow.create_bursts(mo_types=[mo1], notification_rate=2)
        self.assertTrue(mock_random.called)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.netsim_mo.determine_mo_types_required')
    def test_build_mo_type_instances_mcd__success(self, mock_mo_type):
        self.flow.BURST_TYPE = "MCD"
        mo_type = Mock()
        mock_mo_type.return_value = [mo_type]
        self.flow.build_mo_type_instances("ERBS", {'mo_type_name': "MO"}, ["Node1"], 2)
        self.assertEqual(0, mo_type.add_avc_burst_info.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.netsim_mo.determine_mo_types_required')
    def test_build_mo_type_instances_avc__success(self, mock_mo_type):
        self.flow.BURST_TYPE = "AVC"
        mo_type = Mock()
        mock_mo_type.return_value = [mo_type]
        self.flow.build_mo_type_instances("ERBS", {'mo_type_name': "MO", "mo_values": "value", "mo_attribute": "attr"},
                                          ["Node1"], 2)
        self.assertEqual(1, mo_type.add_avc_burst_info.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.check_node_cardinality', return_value=4)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.update_created_mos')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    def test_create_external_enodeb_function__success(self, mock_user, mock_update, mock_add_error, _):
        nodes = [Mock(node_id="LTE01", subnetwork="SubNet")] * 3
        expected = ("cmedit create SubNet,MeContext=LTE01,ManagedElement=1,ENodeBFunction=1,EUtraNetwork=1,"
                    "ExternalENodeBFunction=CMSYNC-0-0 ExternalENodeBFunctionId=CMSYNC-0-0; eNBId=1000000; "
                    "eNodeBPlmnId=(mcc=272,mnc=7,mncLength=2)")
        self.flow.create_external_enodeb_function(nodes)
        mock_user.return_value.enm_execute.assert_called_with(expected)
        self.assertEqual(3, mock_update.call_count)
        self.assertEqual(0, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.check_node_cardinality',
           return_value=512)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.update_created_mos')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    def test_create_external_enodeb_function__mo_maximum_reached(self, mock_user, mock_update, mock_add_error, _):
        nodes = [Mock(node_id="LTE01", subnetwork="SubNet")]
        self.flow.create_external_enodeb_function(nodes)
        self.assertEqual(0, mock_user.return_value.enm_execute.call_count)
        self.assertEqual(0, mock_update.call_count)
        self.assertEqual(0, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.check_node_cardinality', return_value=4)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.update_created_mos')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    def test_create_external_enodeb_function__logs_exception(self, mock_user, mock_debug, *_):
        nodes = [Mock(node_id="LTE01", subnetwork="SubNet")] * 3
        mock_user.return_value.enm_execute.side_effect = Exception("Error")
        self.flow.create_external_enodeb_function(nodes)
        mock_debug.assert_any_call("\nFailed to create ExternalENodeBFunction for use by MCDBurst, error encountered:"
                                   " Error.")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    def test_update_created_mos__matches_1_instance_and_already_exists(self, mock_debug):
        for output in [[u'', u'1 instance(s)'], [u'Error: already exists', u'0 instance(s)'],
                       [u'Error: error', u'0 instance(s)']]:
            self.flow.update_created_mos(output, Mock(node_id="LTE01"), "CMSYNC-0-1")
        self.assertEqual(1, mock_debug.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.add_error_as_exception')
    def test_delete_created_external_enodeb_function_mos__error_handling(self, mock_add_error, mock_debug):
        user = Mock()
        node = Mock(node_id="Node")
        cmsync_flow.CREATED_EXTERNAL_ENODEB_FUNCTION_MOS = {"Node": node}
        user.enm_execute.side_effect = [None, Exception()]
        self.flow.delete_created_external_enodeb_function_mos(user, [node, node])
        self.assertEqual(1, mock_add_error.call_count)
        mock_debug.assert_any_call("Completed deleting ExternalENodeBFunction created for use by MCDBursts.")

    def test_delete_created_external_enodeb_function_mos__skips_node_not_in_created_dict(self):
        user = Mock()
        cmsync_flow.CREATED_EXTERNAL_ENODEB_FUNCTION_MOS = {"Node": None}
        self.flow.delete_created_external_enodeb_function_mos(user, [Mock(node_id="Node"), Mock(node_id="Node1")])
        self.assertEqual(0, user.enm_execute.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_matching_parent_mo')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.create_external_enodeb_function')
    def test_get_new_mo_info_for_mcd_burst__external_enodeb_function_mo(self, mock_create_mo, mock_match_mo, _):
        mo_type = Mock(mos=["ExternalENodeBFunction", "TermPointToENB"],
                       parent_mo_path=["ManagedElement", "ExternalENodeBFunction"],
                       nodes=[Mock(node_id="Node", primary_type="ERBS")])
        self.flow.get_new_mo_info_for_mcd_burst(mo_type)
        self.assertEqual(1, mock_create_mo.call_count)
        self.assertEqual(1, mock_match_mo.call_count)

    def test_get_matching_parent_mo__returns_common_mo_name(self):
        expected = "CELL-1--0"
        cmsync_flow.CREATED_EXTERNAL_ENODEB_FUNCTION_MOS = {"Node": ["CELL-1--0", "CELL-2--0"],
                                                            "Node1": ["CELL-1--0", "CELL-1--1"]}
        nodes = [Mock(node_id=_) for _ in ["Node", "Node1"]]
        self.assertEqual(self.flow.get_matching_parent_mo(nodes), expected)

    def test_get_matching_parent_mo__catches_no_mo_created(self):
        cmsync_flow.CREATED_EXTERNAL_ENODEB_FUNCTION_MOS = {"Node": ["CELL-1--0", "CELL-2--0"],
                                                            "Node1": ["CELL-1--0", "CELL-1--1"],
                                                            "Node2": [None]}
        nodes = [Mock(node_id=_) for _ in ["Node", "Node1", "Node2"]]
        self.assertEqual(self.flow.get_matching_parent_mo(nodes), None)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.build_fdn_reference_string',
           return_value='{\\"eutranFrequencyRef=1\\"}')
    def test_get_mandatory_mcd_data_attributes__returns_fdd_tdd_attrs_and_reference(self, mock_build):
        expected = ['{\\"ExternalEUtranCellTDDId=CMSYNC\\"}', '{\\"tac=60000\\"}', '{\\"physicalLayerSubCellId=1\\"}',
                    '{\\"physicalLayerCellIdGroup=100\\"}', '{\\"localCellId=200\\"}', '{\\"eutranFrequencyRef=1\\"}']
        self.assertListEqual(expected, self.flow.get_mandatory_mcd_data_attributes("ExternalEUtranCellFDD", "Node",
                                                                                   cell_type="TDD"))
        mock_build.assert_called_with('Node', 'ExternalEUtranCellFDD', 'TDD')

        self.assertListEqual(expected, self.flow.get_mandatory_mcd_data_attributes("ExternalEUtranCellTDD", "Node"))
        mock_build.assert_called_with('Node', 'ExternalEUtranCellTDD', 'TDD')

        expected = ['{\\"ExternalEUtranCellFDDId=CMSYNC\\"}', '{\\"tac=60000\\"}', '{\\"physicalLayerSubCellId=1\\"}',
                    '{\\"physicalLayerCellIdGroup=100\\"}', '{\\"localCellId=200\\"}', '{\\"eutranFrequencyRef=1\\"}']
        self.assertListEqual(expected, self.flow.get_mandatory_mcd_data_attributes("ExternalEUtranCellFDD", "Node"))
        mock_build.assert_called_with('Node', 'ExternalEUtranCellFDD', 'FDD')

        expected = ['{\\"bcc=1\\"}', '{\\"ncc=1\\"}', '{\\"lac=1\\"}']
        self.assertListEqual(expected, self.flow.get_mandatory_mcd_data_attributes("Lrat:ExternalGeranCell", "Node"))
        expected = ['{\\"eUtranCellRelationId=CMSYNC\\"}', '{\\"eutranFrequencyRef=1\\"}']
        self.assertListEqual(expected, self.flow.get_mandatory_mcd_data_attributes("Lrat:EUtranCellRelation", "Node"))
        self.assertEqual(4, mock_build.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncFlow.get_ref_mo_value', return_value="FDN")
    def test_build_fdn_reference_string__should_return_a_string_lets_see_if_it_returns_a_string(self, _):
        expected = '{\\"eutranFrequencyRef=FDN\\"}'
        self.assertEqual(expected, self.flow.build_fdn_reference_string("Node1", "ExternalEUtranCellTDD", "TDD"), "\n")
        expected = '{\\"neighborCellRef=FDN\\"}'
        self.assertEqual(expected, self.flow.build_fdn_reference_string("Node1", "EUtranCellRelation", "FDD"), "\n")
        expected = '{\\"externalUtranCellFDDRef=FDN\\"}'
        self.assertEqual(expected, self.flow.build_fdn_reference_string("Node1", "UtranCellRelation", "FDD"), "\n")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    def test_get_ref_mo_value__name_test_later(self, mock_get_admin_user):
        response = Mock()
        response.get_output.return_value = [u'', u'FDN : SubNetwork=ERBS,MeContext=1,ManagedElement=1,MO=1', u'', u'0']
        mock_get_admin_user.return_value.enm_execute.return_value = response
        self.flow.get_ref_mo_value("Node", "UtranCellRelation", "TDD")
        mock_get_admin_user.return_value.enm_execute.assert_called_with("cmedit get Node ExternalUtranCellTDD")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    def test_get_ref_mo_value__raises_enm_application_error_if_no_fdn(self, mock_get_admin_user):
        response = Mock()
        response.get_output.return_value = [u'', u'', u'0']
        mock_get_admin_user.return_value.enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, self.flow.get_ref_mo_value, "Node", "UtranCellRelation", "FDD")
        mock_get_admin_user.return_value.enm_execute.assert_called_with("cmedit get Node ExternalUtranCellFDD")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    def test_get_ref_mo_value__gets_the_neighborcellref_for_eutrancellrelation_mo(self, mock_get_admin_user):
        response = Mock()
        response.get_output.return_value = [u'', u'FDN : SubNetwork=ERBS,MeContext=1,ManagedElement=1,MO=1', u'', u'0',
                                            "neighborCellRef : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                            "ManagedElement=LTE45dg2ERBS00052,ENodeBFunction=1,EUtraNetwork=1,"
                                            "ExternalENodeBFunction=LTE46dg2ERBS00002,ExternalEUtranCellFDD="
                                            "LTE46dg2ERBS00002-6"]
        mock_get_admin_user.return_value.enm_execute.return_value = response
        expected_response = ("ManagedElement=LTE45dg2ERBS00052,ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction="
                             "LTE46dg2ERBS00002,ExternalEUtranCellFDD=LTE46dg2ERBS00002-6")
        self.assertEqual(expected_response, self.flow.get_ref_mo_value("Node", "EUtranCellRelation", "FDD"))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    def test_get_ref_mo_value__raises_enm_application_if_command_fails(self, mock_get_admin_user):
        mock_get_admin_user.return_value.enm_execute.side_effect = Exception("Error")
        self.assertRaises(EnmApplicationError, self.flow.get_ref_mo_value, "Node", "ExternalEUtranCellFDD", "FDD")

    def test_check_node_cardinality__success(self):
        user, response, node = Mock(), Mock(), Mock(node_id="Node")
        response.get_output.return_value = [u'', u'10 instance(s)']
        user.enm_execute.return_value = response
        self.assertEqual(10, self.flow.check_node_cardinality(user, node))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    def test_check_node_cardinality__return_none_if_cardinality_exceeded(self, mock_debug):
        user, response, node = Mock(), Mock(), Mock(node_id="Node")
        response.get_output.return_value = [u'', u'512 instance(s)']
        user.enm_execute.return_value = response
        self.assertIsNone(self.flow.check_node_cardinality(user, node))
        mock_debug.assert_called_with("Maximum MO Cardinality for node: Node, already reached, cannot create MO.")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    def test_check_node_cardinality__return_none_if_cmd_fails(self, mock_debug):
        user, response, node = Mock(), Mock(), Mock(node_id="Node")
        response.get_output.side_effect = Exception("Error")
        user.enm_execute.return_value = response
        self.assertIsNone(self.flow.check_node_cardinality(user, node))
        mock_debug.assert_called_with("Unable to determine MO Cardinality for node: Node, error encountered: [Error]")

    @ParameterizedTestCase.parameterize(
        ("input_notifications", "output_notifications"),
        [
            ([['RadioNode', 'EUtranCellFDD', 11, 2]], [['RadioNode', 'EUtranCellFDD', 11, 2]]),
            ([['RadioNode', 'EUtranCellFDD', 12, 2]], [['RadioNode', 'EUtranCellFDD', 12, 2]]),
            ([['RadioNode', 'EUtranCellFDD', 13, 2]], [['RadioNode', 'EUtranCellFDD', 12, 2],
                                                       ['RadioNode', 'EUtranCellFDD', 1, 2]]),
            ([['RadioNode', 'EUtranCellFDD', 23, 2]], [['RadioNode', 'EUtranCellFDD', 12, 2],
                                                       ['RadioNode', 'EUtranCellFDD', 11, 2]]),
            ([['RadioNode', 'EUtranCellFDD', 24, 2]], [['RadioNode', 'EUtranCellFDD', 12, 2],
                                                       ['RadioNode', 'EUtranCellFDD', 12, 2]]),
            ([['RadioNode', 'EUtranCellFDD', 25, 2]], [['RadioNode', 'EUtranCellFDD', 12, 2],
                                                       ['RadioNode', 'EUtranCellFDD', 12, 2],
                                                       ['RadioNode', 'EUtranCellFDD', 1, 2]]),
            ([['RadioNode', 'EUtranCellFDD', 35, 2]], [['RadioNode', 'EUtranCellFDD', 12, 2],
                                                       ['RadioNode', 'EUtranCellFDD', 12, 2],
                                                       ['RadioNode', 'EUtranCellFDD', 11, 2]]),
        ]
    )
    def test_distribute_large_notification_groups__is_successful(self, input_notifications, output_notifications):
        self.assertEqual(self.flow.distribute_large_notification_groups(input_notifications), output_notifications)


class CmSyncSetupFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = CmSyncSetupFlow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]
        self.flow.MSCM_RATIO = 0.50
        self.flow.MSCMCE_RATIO = 0.50
        self.flow.SCHEDULE_SLEEP = 0
        self.flow.VALUES_PER_PROFILE = {"cmsync_01": 0.0132, "CMSYNC_02": 0.6997, "CMSYNC_04": 0.1435, "CMSYNC_06": 0.1436}
        self.flow.MAX_MOS_PER_RNC = 500
        self.flow.MAX_MOS_MSCMCE = 20000

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncNodeManager.allocate_nodes_to_profile')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncMoInfo.'
           'set_profile_node_allocations_values')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncMoInfo.set_values_for_all_profiles')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.NetworkMoInfo.'
           'map_ne_types_to_mediator_and_update_mo_count')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncMoInfo.'
           'get_network_percentage_for_mediator')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.nodes', new_callable=PropertyMock,
           return_value={"RNC": []})
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.persistence.set')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.log_network_cell_info')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.sleep')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.add_error_as_exception')
    def test_execute_flow(self, mock_add_error, mock_sleep, mock_log, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 0)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncNodeManager.allocate_nodes_to_profile')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.NetworkMoInfo.'
           'map_ne_types_to_mediator_and_update_mo_count', side_effect=Exception("Exception"))
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncMoInfo.'
           'get_network_percentage_for_mediator')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.sleep')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmSyncSetupFlow.create_profile_users')
    def test_execute_flow_adds_error_on_exception(self, mock_create_profile_users, mock_add_error, mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_sleep.called)

    def test_log_network_cell_info__success(self):
        mo_info = Mock()
        mo_info.mediator_dict = {"MSCM": 1000, "MSCMCE": 1200}
        mo_info.network_mo_count = 4000
        mo_info.total_notifications = 40000
        mo_info.get_network_percentage_for_mediator.side_effect = ["50%", "50%"]
        mo_info.calculate_notification_per_profile_per_day.return_value = []
        mo_info.profile_node_allocations = {"P1": {"ERBS": 1}}
        mo_info.profile_notification_calculations = {"P1": ["mo", 1, 1]}
        self.flow.log_network_cell_info(mo_info)
        self.assertEqual(1, mo_info.calculate_notification_per_profile_per_day.call_count)


class CmSyncNodeManagerFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.profile = Mock()
        self.profile.num_nodes = 10
        self.profile.get_nodes_list_by_attribute.return_value = []
        self.profile.NUM_NODES = {"ERBS": 1, "RNC": 2}
        self.flow = CmSyncNodeManager(self.profile)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.node_pool_mgr.ProfilePool.allocate_nodes')
    def test_allocate_nodes_to_profile__updates_num_nodes(self, mock_allocate_nodes, *_):
        self.assertEqual(10, self.flow.profile.num_nodes)
        self.flow.allocate_nodes_to_profile()
        self.assertEqual(mock_allocate_nodes.call_count, 1)
        self.assertEqual(0, self.flow.profile.num_nodes)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.allocate_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.node_pool_mgr.ProfilePool.allocate_nodes')
    def test_allocate_nodes_to_profile__uses_service(self, mock_allocate_nodes, mock_service_allocate, *_):
        self.flow.allocate_nodes_to_profile()
        self.assertEqual(mock_allocate_nodes.call_count, 0)
        self.assertEqual(mock_service_allocate.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.node_pool_mgr.get_pool')
    def test_allocate_nodes_to_profile__logs_exception(self, mock_get_pool, mock_debug, *_):
        pool = Mock()
        pool.allocate_nodes.side_effect = Exception()
        mock_get_pool.return_value = pool
        self.flow.allocate_nodes_to_profile()
        self.assertEqual(mock_get_pool.call_count, 1)
        self.assertEqual(mock_debug.call_count, 4)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.allocate_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.node_pool_mgr.ProfilePool.allocate_nodes')
    def test_allocate_nodes_to_profile__skips_allocation_nodes_already_allocated(self, mock_allocate_nodes,
                                                                                 mock_service_allocate, *_):
        self.profile.get_nodes_list_by_attribute.return_value = ["Node", "Node1"]
        self.flow.allocate_nodes_to_profile()
        self.assertEqual(mock_allocate_nodes.call_count, 0)
        self.assertEqual(mock_service_allocate.call_count, 0)
        self.assertEqual(2, self.profile.num_nodes)


class CMSyncUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    # CMSyncProfile.execute_flow tests ###############################################################

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.persist')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.get_nodes_list_by_attribute')
    def test_execute_flow__adds_an_error_when_expected_nodes_are_not_available(
            self, mock_nodes_list, mock_add_error_as_exception, *_):
        mock_nodes_list.return_value = []

        sync_profile = CMSyncProfile()
        sync_profile.execute_flow()

        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.persist')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.create_cm_management_object')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.get_nodes_list_by_attribute')
    def test_execute_flow__adds_an_error_when_synchronisation_fails(
            self, mock_nodes_list, mock_add_error_as_exception, mock_get_management_obj, *_):
        mock_nodes_list.return_value = ["node1"]
        management_obj = mock_get_management_obj.return_value = Mock()
        management_obj.synchronize.side_effect = Exception

        sync_profile = CMSyncProfile()
        sync_profile.execute_flow()

        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.persist')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.create_cm_management_object')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSyncProfile.get_nodes_list_by_attribute')
    def test_execute_flow__adds_an_error_when_exchanging_nodes_fails(
            self, mock_nodes_list, mock_add_error_as_exception, *_):
        mock_nodes_list.side_effect = [["node1"], []]

        sync_profile = CMSyncProfile()
        sync_profile.execute_flow()

        self.assertEqual(mock_add_error_as_exception.call_count, 1)


class CmSync32FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = CMSync32Flow()
        self.flow.SCHEDULE_SLEEP = 0
        self.flow.NOTIFICATION_INFO = BSC_AVC_BURST_MO_TYPE_SETTINGS
        self.flow.AVG_PER_CELL_PER_SEC = 1
        self.flow.BURST_DURATION = 1800

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    def test_calculate_total_per_second__for_gerancells(self, mock_get_admin_user, mock_debug):
        response = Mock()
        response.get_output.return_value = [u"10 instance(s)"]
        mock_get_admin_user.return_value.enm_execute.return_value = response
        self.flow.calculate_total_per_second_for_gerancells(1)
        mock_debug.assert_called_with("Notification rate per second, per node, determined to be 10.0.")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.get_workload_admin_user')
    def test_calculate_total_per_second_for_gerancells__no_response(self, mock_get_admin_user, mock_debug):
        response = Mock()
        response.get_output.return_value = [u"Error"]
        mock_get_admin_user.return_value.enm_execute.return_value = response
        self.flow.calculate_total_per_second_for_gerancells(1)
        mock_debug.assert_called_with("Unable to determine total GeranCells on deployment continuing with basic load "
                                      "rate.")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.persist')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.calculated_daily_expected_load')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.generate_basic_dictionary_from_list_of_objects',
           return_value={"BSC": [Mock()]})
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.create_mo_types')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.sleep')
    def test_execute_flow__success(self, mock_sleep, mock_create_mo_types, *_):
        burst = Mock()
        mock_create_mo_types.return_value = [burst]
        self.flow.teardown_list.append(burst)
        self.flow.execute_flow()
        self.assertEqual(mock_create_mo_types.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.persist')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.calculated_daily_expected_load')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.generate_basic_dictionary_from_list_of_objects',
           return_value={"BSC": [Mock()]})
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.create_mo_types',
           side_effect=KeyboardInterrupt("Interrupt"))
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.sleep')
    def test_execute_flow__raises_keyboard_interrupt(self, mock_sleep, mock_create_mo_types, *_):
        burst = Mock()
        mock_create_mo_types.return_value = [burst]
        self.flow.teardown_list.append(burst)
        self.assertRaises(KeyboardInterrupt, self.flow.execute_flow)
        self.assertEqual(mock_create_mo_types.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 0)
        self.assertEqual(1, len(self.flow.teardown_list))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.persist')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.calculated_daily_expected_load')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.generate_basic_dictionary_from_list_of_objects',
           return_value={"BSC": [Mock()]})
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.'
           'calculate_total_per_second_for_gerancells')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.create_mo_types')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.sleep')
    def test_execute_flow__cmsync_32_calls_gerancell_calculate(self, mock_sleep, mock_create_mo_types, mock_calculate,
                                                               *_):
        burst = Mock()
        mock_create_mo_types.return_value = [burst]
        self.flow.NAME = "CMSYNC_32"
        self.flow.teardown_list.append(burst)
        self.flow.execute_flow()
        self.assertEqual(mock_create_mo_types.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertEqual(mock_calculate.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.persist')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.calculated_daily_expected_load')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.generate_basic_dictionary_from_list_of_objects',
           return_value={"BSC": [Mock()]})
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.'
           'calculate_total_per_second_for_gerancells', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.create_mo_types')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.sleep')
    def test_execute_flow__cmsync_32_adds_exception(self, mock_sleep, mock_create_mo_types, mock_add_error, *_):
        burst = Mock()
        mock_create_mo_types.return_value = [burst]
        self.flow.NAME = "CMSYNC_32"
        self.flow.teardown_list.append(burst)
        self.flow.execute_flow()
        self.assertEqual(mock_create_mo_types.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.create_burst_objects')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.netsim_mo.'
           'determine_mo_types_required_with_avc_burst_info')
    def test_create_mo_types__success(self, mock_determine_mo_types_required_with_avc_burst_info,
                                      mock_create_burst_objects):
        nodes = [Mock()]
        mock_determine_mo_types_required_with_avc_burst_info.return_value = nodes
        self.flow.create_mo_types({"BSC": nodes})
        self.assertEqual(mock_determine_mo_types_required_with_avc_burst_info.call_count, 1)
        self.assertEqual(mock_create_burst_objects.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.create_burst_objects')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.netsim_mo.'
           'determine_mo_types_required_with_avc_burst_info')
    def test_create_mo_types__no_nodes(self, mock_determine_mo_types_required_with_avc_burst_info,
                                       mock_create_burst_objects):
        nodes = [Mock()]
        mock_determine_mo_types_required_with_avc_burst_info.return_value = nodes
        self.flow.NOTIFCATION_INFO = {"node_type": "BSC"}
        self.flow.create_mo_types({"BSC": []})
        self.assertEqual(mock_determine_mo_types_required_with_avc_burst_info.call_count, 0)
        self.assertEqual(mock_create_burst_objects.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.AVCBurst.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync32Flow.start_bursts')
    def test_create_burst_objects__success(self, mock_start_avc_burst, *_):
        self.flow.create_burst_objects([Mock()])
        self.assertEqual(mock_start_avc_burst.call_count, 1)

    def test_calculated_daily_expected_load__gsm(self):
        self.flow.DURATION = 1800
        self.flow.SCHEDULE_SLEEP = 1800
        self.flow.UPDATED_AVG_PER_NODE = 0.072
        self.assertAlmostEqual(597196, int(self.flow.calculated_daily_expected_load(96)))


class CmSync23FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = CMSync23Flow()
        self.flow.BURST_DURATION = 900
        self.flow.SCHEDULE_SLEEP = 0
        self.flow.NOTIFICATION_INFO = [{"node_type": "RadioNode"}]
        self.flow.NOTIFICATION_PER_SECOND = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.persist')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.calculated_daily_expected_load')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.generate_basic_dictionary_from_list_of_objects',
           return_value={"BSC": [Mock()]})
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.modify_existing_notification_info')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.create_mo_types')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.sleep')
    def test_execute_flow__success(self, mock_sleep, mock_create_mo_types, *_):
        burst = Mock()
        mock_create_mo_types.return_value = [burst]
        self.flow.teardown_list.append(burst)
        self.flow.execute_flow()
        self.assertEqual(mock_create_mo_types.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 1)

    def test_modify_existing_notification_info__updates_to_dictionary(self):
        expected = {'RadioNode': [{'notification_percentage_rate': 0.5, 'node_type': 'RadioNode'}]}
        self.flow.modify_existing_notification_info()
        self.assertDictEqual(expected, getattr(self.flow, 'NOTIFICATION_INFO', {}))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.get_mo_types', return_value=[])
    def test_create_mo_types__success(self, mock_get_mo_types):
        nodes = [Mock()]
        self.flow.NOTIFICATION_INFO = {"RadioNode": [{"mo_type_name": "EUtranCellFDD"}]}
        self.flow.create_mo_types({"RadioNode": nodes})
        self.assertEqual(mock_get_mo_types.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync23Flow.get_mo_types', return_value=[])
    def test_create_mo_types__no_available_nodes(self, mock_get_mo_types):
        self.flow.NOTIFICATION_INFO = {"RadioNode": [{"mo_type_name": "EUtranCellFDD"}]}
        self.flow.create_mo_types({"RadioNode": []})
        self.assertEqual(mock_get_mo_types.call_count, 0)

    def test_calculated_daily_expected_load__megastorm(self):
        self.flow.DURATION = 900
        self.flow.SCHEDULE_SLEEP = 3600 * 6
        self.flow.UPDATED_AVG_PER_NODE = 8000 / 50
        self.assertEqual(28800000, self.flow.calculated_daily_expected_load(50))


class CmSync15FlowUnitTests(ParameterizedTestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = CMSync15Flow()
        self.flow.SCHEDULE_SLEEP = 0
        self.flow.BURST_DURATION = 1800

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync15Flow.persist')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync15Flow.calculated_daily_expected_load')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync15Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.generate_basic_dictionary_from_list_of_objects',
           return_value={"Router_6672": [Mock()]})
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync15Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync15Flow.calculate_avg_per_node')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync15Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync15Flow.create_mo_types')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync15Flow.sleep')
    def test_execute_flow__success(self, mock_sleep, mock_create_mo_types, *_):
        burst = Mock()
        mock_create_mo_types.return_value = [burst]
        self.flow.teardown_list.append(burst)
        self.flow.execute_flow()
        self.assertEqual(mock_create_mo_types.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync15Flow.get_nodes_list_by_attribute')
    @ParameterizedTestCase.parameterize(
        ("ROUTER_SUPPORT", "nodes", "result"),
        [
            (5000, [], 0.00),
            (300, range(50), 0.018),
            (2000, range(100), 0.06),
            (5000, range(500), 0.03)
        ]
    )
    def test_calculate_avg_per_node(self, router_support, nodes, result, mock_nodes_list):
        mock_nodes_list.return_value = nodes
        self.flow.ROUTER_SUPPORT = router_support
        self.assertEqual(result, self.flow.calculate_avg_per_node())

    def test_calculated_daily_expected_load__router_load(self):
        self.flow.DURATION = 1800
        self.flow.SCHEDULE_SLEEP = 1800
        self.flow.UPDATED_AVG_PER_NODE = 0.03
        self.assertEqual(1296000, self.flow.calculated_daily_expected_load(500))


class CollectionSyncFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = CollectionSyncFlow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmManagement.get_management_obj')
    def test_create_cm_management_object__success(self, mock_get_management_obj):
        self.flow.create_cm_management_object()
        self.assertEqual(1, mock_get_management_obj.call_count)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CmManagement.get_management_obj')
    def test_create_cm_management_object__raises_enm_application_error(self, mock_get_management_obj):
        mock_get_management_obj.side_effect = RuntimeError("Error")
        self.assertRaises(EnmApplicationError, self.flow.create_cm_management_object)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.arguments.get_random_string', return_value="1234")
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.check_if_collection_exists',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.create_cm_management_object')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.add_error_as_exception')
    def test_execute_flow__sync_fails(self, mock_add_error, mock_cm_object, *_):
        mock_cm_object.return_value.synchronize.side_effect = Exception("Error")
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.state',
           new_callable=PropertyMock, return_value=None)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.arguments.get_random_string', return_value="1234")
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.check_if_collection_exists',
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.create_cm_management_object')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.create_collection')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.add_error_as_exception')
    def test_execute_flow__retries_if_collection_create_fails(self, mock_add_error, mock_create, mock_cm_object, *_):
        mock_create.side_effect = [Exception("Error"), Mock()]
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)
        self.assertEqual(1, mock_cm_object.return_value.synchronize.call_count)

    def test_check_if_collection_exists__collection_found(self):
        user = Mock()
        response = Mock()
        response.get_output.return_value = [u'headers', u'collection1 user', u'collection2 user', u'', u'2 instance(s)']
        user.enm_execute.return_value = response
        self.flow.COLLECTION_NAME = "Collection2"
        self.assertTrue(self.flow.check_if_collection_exists(user))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    def test_check_if_collection_exists__logs_exception(self, mock_debug):
        user = Mock()
        response = Mock()
        response.get_output.side_effect = Exception("Error")
        user.enm_execute.return_value = response
        self.flow.COLLECTION_NAME = "Collection2"
        self.assertIsNone(self.flow.check_if_collection_exists(user))
        mock_debug.assert_called_with("Could not retrieve collection list from ENM CLI, error encountered: Error")

    def test_check_if_collection_exists__no_output(self):
        user = Mock()
        response = Mock()
        response.get_output.return_value = []
        user.enm_execute.return_value = response
        self.flow.COLLECTION_NAME = "Collection2"
        self.assertFalse(self.flow.check_if_collection_exists(user))

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.Collection.create')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.Collection.exists', new_callable=PropertyMock,
           side_effect=[False, True])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    def test_create_collection__success(self, mock_debug, mock_collection, *_):
        self.flow.COLLECTION_NAME = "Collection2"
        self.flow.teardown_list = []
        mock_collection.id = "1234"
        self.flow.create_collection(Mock(), [])
        mock_debug.assert_called_with("Collection not found, creating collection : Collection2.")

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.Collection.create', side_effect=Exception('Error'))
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.Collection.exists', new_callable=PropertyMock,
           side_effect=[False, True])
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CollectionSyncFlow.add_error_as_exception')
    def test_create_collection__adds_error_on_exception(self, mock_add_error, mock_collection, *_):
        self.flow.COLLECTION_NAME = "Collection2"
        self.flow.teardown_list = []
        mock_collection.id = "1234"
        self.flow.create_collection(Mock(), [])
        self.assertEqual(1, mock_add_error.call_count)


class CmSync24FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = CMSync24Flow()
        self.flow.MSG = "Successfully synchronised test nodes."

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync24Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync24Flow.create_cm_management_object')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync24Flow.add_error_as_exception')
    def test_execute_flow__success(self, mock_add_error_as_exception, mock_debug, *_):
        self.flow.teardown_list = Mock()
        self.flow.execute_flow()
        self.assertEqual(0, mock_add_error_as_exception.call_count)
        mock_debug.assert_called_with(self.flow.MSG)

    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync24Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync24Flow.create_cm_management_object')
    @patch('enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow.CMSync24Flow.add_error_as_exception')
    def test_execute_flow__adds_exception(self, mock_add_error_as_exception, mock_cm_management, *_):
        error = Exception("Error")
        mock_cm_management.return_value.synchronize.side_effect = error
        self.flow.teardown_list = Mock()
        self.flow.execute_flow()
        mock_add_error_as_exception.assert_called_with(error)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
