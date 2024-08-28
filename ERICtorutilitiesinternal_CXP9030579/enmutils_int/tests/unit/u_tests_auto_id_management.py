#!/usr/bin/env python
from datetime import datetime, timedelta

import unittest2
from mock import patch, Mock, MagicMock, PropertyMock
from requests.exceptions import HTTPError

from enmutils.lib.enm_node import ERBSNode
from enmutils.lib.exceptions import EnmApplicationError, TimeOutError, EnvironError
from enmutils_int.lib.auto_id_management import (ManualAutoIdProfile, AutoIdProfile, TopologyGroupRange,
                                                 AutoIdTearDownProfile)
from enmutils_int.lib.auto_id_management import NonPlannedPCIRange, ClosedLoopAutoIdProfile, OpenLoopAutoIdProfile
from enmutils_int.lib.workload import aid_setup
from testslib import unit_test_utils

URL = 'http://locahost'


class AutoIdUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock()
        self.nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', 'ip', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', 'ip', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        self.collection = Mock(id="99999", nodes=self.nodes)
        self.auto_id = ManualAutoIdProfile(user=self.user, name="AutoIdManualProfileTest", nodes=self.nodes,
                                           collection=self.collection)
        self.topology_group_range = TopologyGroupRange(user=self.user, name="TopRangeUnitTest",
                                                       first_pci_value_range={12: 2}, nodes=self.nodes,
                                                       collection=self.collection)
        self.no_planned_pci_range = NonPlannedPCIRange(user=self.user, frequency=2110.1, pci_ranges={100: 0})

        start_time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 23, 15, 0)
        closed_loop_times = [start_time + timedelta(hours=hour) for hour in xrange(0, 23, 12)]
        self.closed_loop_profile = ClosedLoopAutoIdProfile(user=self.user, name="closed_unit_test", nodes=self.nodes,
                                                           scheduled_times=closed_loop_times,
                                                           collection=self.collection)
        self.closed_loop_profile.schedule_epoch_times = [1510269300000L, 1510312500000L]
        self.profile_attributes = {'checkN': True, 'checkRSAggregated': True, 'checkD': True,
                                   'changeMultipleCellsToFixConflicts': False, 'checkRSNonShifted': True,
                                   'checkEnodebDetected': True, 'checkNonPlannedPci': True,
                                   'checkNCellsBlacklistedPciValues': True,
                                   'checkTemporaryValues': True, 'maxRetries': 2, 'checkS': True, 'checkRS': True,
                                   'checkDMinCellDistance': 5000, 'checkRSShifted': False, 'checkReservedValues': True,
                                   'maximumNumberOfCellsToChange': 2, 'toGenerateAlarm': False,
                                   'multipleCellsToFixValue': 2,
                                   'checkNNCellsBlacklistedPciValues': True, 'checkSS': False,
                                   'checkSCellsBlacklistedPciValues': True,
                                   'checkSM30': True, 'checkSSM30': False, 'referenceShiftCost': 0,
                                   'checkSSCellsBlacklistedPciValues': False,
                                   'checkNNM30': True, 'checkSSSignalStrength': 70, 'checkNN': True, 'applied': 0,
                                   'checkDM30': False,
                                   'networkTechnology': 'LTE', 'checkMultipleCellsToFix': False, 'checkM30Cost': 5,
                                   'checkDMinCellDistanceInKilometers': True, 'checkDCellsBlacklistedPciValues': False,
                                   'alarmGeneration': False, 'checkDDistanceCost': 10, 'checkNM30': True,
                                   'checkTopologyGroupRange': True, 'hardLock': False, 'checkBlacklistCost': 20}
        self.open_loop_auto_id_profile = OpenLoopAutoIdProfile(user=self.user, name='unit test', nodes=self.nodes,
                                                               options={"checkEnodebDetected": False,
                                                                        "checkD": False,
                                                                        "checkRS": False,
                                                                        "checkTemporaryValues": False,
                                                                        "checkReservedValues": False},
                                                               collection=self.collection)
        self.auto_id.profile_attributes = self.profile_attributes

        self.AID_SETUP = aid_setup.AID_SETUP()

        self.data = {u'SystemSettings':
                     [{u'reservedList': [{u'physicalLayerSubCellId': 2, u'physicalLayerCellIdGroup': 0}],
                       u'temporaryList': [{u'physicalLayerSubCellId': 1, u'physicalLayerCellIdGroup': 0}],
                       u'poid': 281649241422715, u'name': u'PciSystemSettings'}]}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._get_epoch_schedule')
    @patch('enmutils_int.lib.auto_id_management.Collection')
    def test__init__deletes_collection_if_exists_and_creates_new(self, mock_collection, _):
        mock_collection.id = 1234
        user = Mock()
        name = "Test"
        profile = AutoIdProfile(user, name, nodes=self.nodes)
        self.assertTrue(profile.collection.delete.called)
        self.assertTrue(profile.collection.create.called)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._get_epoch_schedule')
    @patch('enmutils_int.lib.auto_id_management.Collection.exists', new_callable=PropertyMock, return_value=False)
    @patch('enmutils_int.lib.auto_id_management.Collection.create')
    @patch('enmutils_int.lib.auto_id_management.Collection.delete')
    def test__init__does_not_delete_collection(self, mock_delete, *_):
        user = Mock()
        name = "Test"
        AutoIdProfile(user, name, nodes=self.nodes)
        self.assertEqual(0, mock_delete.call_count)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._extract_total_records')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._get_report')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._extract_id')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._validate')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_check__raises_for_status(self, *_):
        profile = AutoIdProfile(Mock(), 'test')
        profile.user = Mock()
        response = profile.user.post.return_value = Mock(ok=False)
        response.json.return_value = {'data': [{'id': '1234'}]}
        profile.name = 'test'
        profile.profile_attributes = {"networkTechnology": ""}
        profile.node_poids = {}
        profile.check()
        self.assertEqual(1, response.raise_for_status.call_count)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_calculate__logs_no_conflict(self, mock_debug, *_):
        profile = AutoIdProfile(Mock(), 'test')
        profile.check_total_records = 0
        profile.profile_attributes = {"networkTechnology": "", "toGenerateAlarm": "", "hardLock": "", "maxRetries": ""}
        profile.user = profile.check_id = Mock()
        profile.calculate()
        mock_debug.assert_any_call("There are no conflicts to calculate at this time")

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._extract_id')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._validate')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_calculate__raises_for_status(self, mock_debug, *_):
        profile = AutoIdProfile(Mock(), 'test')
        profile.check_total_records = 1
        profile.profile_attributes = {"networkTechnology": "", "toGenerateAlarm": "", "hardLock": "", "maxRetries": ""}
        profile.user = profile.check_id = Mock()
        response = profile.user.post.return_value = Mock(ok=False)
        response.json.return_value = {'data': [{'id': '1234'}]}
        profile.calculate()
        self.assertEqual(1, response.raise_for_status.call_count)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._get_report',
           side_effect=[MagicMock(), None])
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._validate')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._extract_id')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_resolve__raises_for_status(self, *_):
        profile = AutoIdProfile(Mock(), 'test')
        profile.calculate_id = profile.check_total_records = 1
        profile.profile_attributes = {"networkTechnology": "", "toGenerateAlarm": "", "hardLock": "", "maxRetries": ""}
        profile.user = profile.check_id = Mock()
        response = profile.user.post.return_value = Mock(ok=False)
        profile.resolve()
        self.assertEqual(1, response.raise_for_status.call_count)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    def test_get_report__success(self, _):
        profile = AutoIdProfile(Mock(), 'test')
        profile.user = Mock()
        response_ok = Mock(ok=True)
        response_bad = Mock(ok=False)
        profile.profile_attributes = {"networkTechnology": "", "toGenerateAlarm": "", "hardLock": "", "maxRetries": ""}
        profile.user.get.side_effect = [response_ok, response_bad]
        self.assertEqual(response_ok, profile._get_report('test', 'check'))
        self.assertEqual(0, response_ok.call_count)
        profile._get_report('test', 'check')
        self.assertEqual(1, response_bad.raise_for_status.call_count)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    def test_delete_collection__success(self, _):
        profile = AutoIdProfile(Mock(), 'test')
        profile.collection = Mock()
        profile._delete_collection()
        self.assertEqual(1, profile.collection.delete.call_count)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_delete_collection__logs_exception(self, mock_debug, _):
        profile = AutoIdProfile(Mock(), 'test')
        profile.collection = Mock()
        profile.name = 'test'
        profile.collection.delete.side_effect = Exception('some error')
        profile._delete_collection()
        mock_debug.assert_called_once_with('Collection deletion problem in AutoIdManagement: test\n'
                                           ' Exception: some error')

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    def test_delete_check__raises_for_status(self, _):
        profile = AutoIdProfile(Mock(), 'test')
        profile.user = Mock()
        response = profile.user.delete_request.return_value = Mock(ok=False)
        profile.profile_attributes = {"networkTechnology": "", "toGenerateAlarm": "", "hardLock": "", "maxRetries": ""}
        profile._delete_check('1234')
        self.assertEqual(1, response.raise_for_status.call_count)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._delete_conflicts', side_effect=Exception('some_error'))
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._delete_check', side_effect=Exception('some_error'))
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    def test_profile_clean__add_exceptions_in_list(self, *_):
        profile = AutoIdProfile(Mock(), 'test')
        profile.check_id = Mock()
        profile.profile_clean()
        self.assertEqual(2, len(profile.exceptions))

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._delete_conflicts', side_effect=Exception('some_error'))
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._delete_check', side_effect=Exception('some_error'))
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    def test_profile_clean__does_not_add_exception(self, *_):
        profile = AutoIdProfile(Mock(), 'test')
        profile.check_id = None
        profile.profile_clean()
        self.assertEqual(0, len(profile.exceptions))

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.delete', side_effect=Exception('some error'))
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.auto_id_management.log.logger.warn')
    def test_teardown__logs_exception(self, mock_warn, *_):
        profile = AutoIdProfile(Mock(), 'test')
        profile.collection = None
        profile._teardown()
        mock_warn.assert_called_once_with('some error')

    def test__extract_total_records__returns_correct_response(self):
        response = MagicMock()
        AutoIdProfile._extract_total_records(response)
        self.assertEqual(1, response.json.call_count)

    @patch('enmutils_int.lib.netex.Collection.create', side_effect=HTTPError())
    def test_auto_id_profile_init_logic_raises_exception(self, _):
        self.assertRaises(Exception, AutoIdProfile, Mock(), 'test', [Mock()])

    def test_auto_id_profile_init_logic(self):
        user = Mock()
        name = "Test"
        collection = Mock()
        collection.id = "1234"
        collection.nodes = []
        profile = AutoIdProfile(user, name, [], collection)
        self.assertEqual("1234", profile.collection_id)
        profile1 = AutoIdProfile(user, name, [])
        self.assertEqual(None, profile1.collection)

    def test_auto_id_manual_profile_create_success(self):
        profile_id = "00001"
        response = Mock()
        response.json.return_value = {"data": [{"id": profile_id, "name": "Response check", "description": "Test"}]}
        self.user.post.return_value = response
        self.auto_id.create()
        self.assertEqual(self.auto_id.profile_id, profile_id)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    def test_get_all__raises_when_response_not_ok(self, _):
        user = Mock()
        user.get.return_value = Mock(ok=False)
        self.assertRaises(HTTPError, AutoIdProfile.get_all, user)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.get_all', return_value={"data": [{"name": ""}]})
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    def test_get_by_name__raises_valueerror(self, *_):
        user = Mock()
        name = "Test"
        self.assertRaises(ValueError, AutoIdProfile.get_by_name, name, user)

    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile.get_by_name')
    def test_auto_id_manual_profile_delete_success_without_id(self, mock_get_by_name):
        profile_id = "00002"
        mock_get_by_name.return_value = {"id": profile_id}
        response = Mock(ok=True)
        self.user.delete_request.return_value = response
        self.auto_id.delete()
        self.assertEqual(self.auto_id.profile_id, profile_id)

    def test_auto_id_manual_profile_delete_failure_without_id_response_not_ok_no_collection(self):
        profile_id = 'profile_01'
        self.auto_id.name = 'profile_name'
        self.auto_id.collection = None

        get_response = Mock()
        get_response.ok = True
        get_response.json.return_value = {'data': [{'name': 'profile_name', 'id': 'profile_01'}]}
        self.user.get.return_value = get_response
        response = Mock()
        response.ok = None
        self.user.delete_request.return_value = response

        self.auto_id.delete()
        self.assertEqual(self.auto_id.profile_id, profile_id)
        self.assertTrue(self.user.get.called)
        self.assertTrue(self.user.delete_request.called)
        self.assertTrue(response.raise_for_status.called)

    @patch('enmutils.lib.log.logger.debug')
    def test_auto_id_manual_profile_delete_success_with_id(self, mock_log_logger_debug):
        self.auto_id.profile_id = "00002"
        response = Mock(ok=True)
        self.user.delete_request = response
        self.auto_id.delete()

        self.assertTrue(mock_log_logger_debug.called)

    def test_delete_check(self):
        response = Mock(ok=True)
        self.user.delete_request = response
        self.auto_id._delete_check('1')

    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._extract_id', return_value="00003")
    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._validate')
    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._get_report')
    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._extract_total_records')
    def test_auto_id_manual_profile_check_success(self, *_):
        check_id = "00003"
        response = Mock(ok=True)
        response.json.return_value = {"data": [{"id": check_id}], "userAction": None, "totalRecords": 0}
        self.user.post.return_value = response
        self.auto_id.check()
        self.assertEqual(self.auto_id.check_id, check_id)

    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._extract_id', return_value="00004")
    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._validate')
    def test_auto_id_manual_profile_calculate_success(self, *_):
        calculate_id = "00004"
        self.auto_id.check_id = "60001"
        self.auto_id.check_total_records = 100
        response = Mock(status_code=200)
        response.json.return_value = {"data": [{"id": "281487883530747", "cellName": "LTE31ERBS00052-1",
                                                "cellENodeBName": "ieatnetsimv7004-14_LTE31ERBS00052",
                                                "currentPCI": "149/2", "conflictingCellName": "",
                                                "conflictingCellENodeBName": "",
                                                "checksFailedSummary": "RS",
                                                "cellCGI": "4852/1/353/57/2",
                                                "conflictingCellCGI": "",
                                                "conflictType": "ReferenceShift", "confusedCellNames": [],
                                                "confusedENodeBNames": [],
                                                "detectedType": "PCI_USER_DETECTED",
                                                "cellFdn": "SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv7004-14_"
                                                           "LTE31ERBS00052,ManagedElement=1,ENodeBFunction=1,EUtran"
                                                           "CellFDD=LTE31ERBS00052-1", "conflictingCellFdn": "",
                                                "confusedCellFdns": [], "timeOfDetection": 1476970298223}]}
        self.auto_id.check_report_response = response
        response = Mock(ok=True)
        response.json.return_value = {"data": [{"id": calculate_id}]}
        self.user.post.return_value = response
        self.auto_id.calculate()
        self.assertEqual(self.auto_id.calculate_id, calculate_id)

    def test_run_calculate_without_running_check_raises_runtime_exception(self):
        self.assertRaises(RuntimeError, self.auto_id.calculate)

    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._extract_id')
    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._validate')
    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._get_report')
    def test_auto_id_manual_profile_resolve_success(self, *_):
        resolve_id = "00005"
        self.auto_id.calculate_id = "40001"
        self.auto_id.calculate_total_records = 100
        response = Mock(ok=True)
        response.json.return_value = {"data": [{"id": resolve_id}]}
        self.user.post.return_value = response
        try:
            self.auto_id.resolve()
        except Exception as e:
            raise AssertionError("Should not have failed: {0}".format(str(e)))

    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_run_resolve_when_check_returns_no_conflicts(self, mock_log_debug):
        self.auto_id.check_id = "60001"
        self.auto_id.check_total_records = 0
        self.auto_id.resolve()
        self.assertEqual(1, mock_log_debug.call_count)

    def test_run_resolve_without_running_check_raises_runtime_exception(self):
        self.assertRaises(RuntimeError, self.auto_id.resolve)

    def test_run_resolve_without_running_calculate_raises_runtime_exception(self):
        self.auto_id.check_id = "60001"
        self.auto_id.check_total_records = 100
        self.assertRaises(RuntimeError, self.auto_id.resolve)

    def test_topology_group_range_create_success(self):
        group_range_id = "12345"
        response = Mock()
        response.json.return_value = {"data": [{"id": group_range_id,
                                                "topologyGroupRangeName": "TopRangeUnitTest", "listOfPciValues": [],
                                                "listOfPciRanges": [{
                                                    "firstPciValueInRange": {"physicalLayerCellIdGroup": 12,
                                                                             "physicalLayerSubCellId": 0},
                                                    "lastPciValueInRange": {"physicalLayerCellIdGroup": 15,
                                                                            "physicalLayerSubCellId": 1}}],
                                                "autoIdTopologyInfo": [{"topologyId": "281480744470951",
                                                                        "listOfPoIds": ["281474981106384"],
                                                                        "networkExplorerState": "/networkexplorer/"}],
                                                "lastUpdated": 1469609550895, "userName": "administrator",
                                                "updatedBy": "administrator"}], "userAction": None, "totalRecords": 0}
        self.user.post.return_value = response
        self.topology_group_range.create()
        self.assertEqual(self.topology_group_range.range_id, group_range_id)

    def test_topology_group_range_delete_success(self):
        self.topology_group_range.range_id = "54321"
        response = Mock(ok=True)
        response.json.return_value = {"code": 200, "description": "The request has succeeded. The response returns "
                                                                  "information on the message-body",
                                      "data": [{"id": self.topology_group_range.range_id,
                                                "topologyGroupRangeName": "Test", "listOfPciValues": [],
                                                "listOfPciRanges":[{
                                                    "firstPciValueInRange": {"physicalLayerCellIdGroup": 12,
                                                                             "physicalLayerSubCellId": 0},
                                                    "lastPciValueInRange": {"physicalLayerCellIdGroup": 15,
                                                                            "physicalLayerSubCellId": 1}}],
                                                "autoIdTopologyInfo": [{"topologyId": "281480744470951",
                                                                        "listOfPoIds": ["281474981106384"],
                                                                        "networkExplorerState": "/networkexplorer/"}],
                                                "lastUpdated":1469609550895, "userName": "administrator",
                                                "updatedBy": "administrator"}], "userAction": None, "totalRecords": 0}
        self.user.delete_request.return_value = response
        self.topology_group_range.delete()
        self.assertEqual(self.topology_group_range.range_id, None)

    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_topology_group_range_without_range_id(self, mock_log_debug):
        self.topology_group_range.delete()
        self.assertEqual(1, mock_log_debug.call_count)

    @patch('enmutils_int.lib.auto_id_management.TopologyGroupRange._delete_collection')
    @patch('enmutils_int.lib.auto_id_management.TopologyGroupRange.delete')
    def test_teardown_topology_group_range(self, mock_delete, mock_delete_collection):

        self.topology_group_range._teardown()

        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_delete_collection.called)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._teardown')
    def test_teardown_autoid_profile(self, mock_teardown):

        self.auto_id.teardown()

        self.assertTrue(mock_teardown.called)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._delete_collection')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.delete')
    def test_teardown_autoid_profile_no_collection(self, mock_delete, mock_delete_collection):
        self.auto_id.collection = None
        self.auto_id._teardown()

        self.assertTrue(mock_delete.called)
        self.assertFalse(mock_delete_collection.called)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._delete_collection')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.delete')
    def test_teardown_autoid_profile_with_collection(self, mock_delete, mock_delete_collection):
        self.auto_id.collection = 'collection_1'
        self.auto_id._teardown()

        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_delete_collection.called)

    def test_non_planned_pci_range_create_success(self):
        group_range_id = "67890"
        response = Mock(ok=True)
        response.json.return_value = group_range_id
        self.user.post.return_value = response
        self.no_planned_pci_range.create()

        self.assertEqual(self.no_planned_pci_range.range_id, group_range_id)

    def test_non_planned_pci_range_delete_success(self):
        self.no_planned_pci_range.range_id = "13579"
        response = Mock(ok=True)
        self.user.delete_request = response
        self.no_planned_pci_range.delete()
        self.assertEqual(self.no_planned_pci_range.range_id, None)

    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_non_planned_pci_range_delete_without_range_id(self, mock_log_debug):
        self.no_planned_pci_range.delete()
        self.assertEqual(1, mock_log_debug.call_count)

    def test_auto_id_closed_profile_create_success(self):
        profile_id = "00009"
        response = Mock(ok=True)
        response.json.return_value = {"code": 200, "description": "The request has succeeded. The response returns "
                                                                  "information on the message-body",
                                      "data": [{"id": profile_id, "name": "Response check", "description": "Test"}],
                                      "userAction": None, "totalRecords": 0}
        self.user.post.return_value = response
        self.closed_loop_profile.create()

        self.assertEqual(self.closed_loop_profile.profile_id, profile_id)

    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_change_settings__success(self, mock_log_logger_debug):
        response = Mock(ok=True)
        response.json.return_value = self.data
        self.user.get.side_effect = [response, Mock(ok=False)]
        self.user.put.return_value = response
        AutoIdProfile.change_settings(self.user, reserved={0: 2}, temporary={0: 1})
        mock_log_logger_debug.assert_called_with("Successfully updated settings for AutoId.")
        self.assertRaises(HTTPError, AutoIdProfile.change_settings, self.user, reserved={0: 2}, temporary={0: 1})

    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_change_settings__success_with_remove(self, mock_log_logger_debug):
        response = Mock(ok=True)
        response.json.return_value = self.data
        self.user.get.return_value = response
        self.user.put.side_effect = [response, Mock(ok=False)]
        AutoIdProfile.change_settings(self.user, reserved={0: 2}, temporary={0: 1}, remove=True)
        self.assertRaises(HTTPError, AutoIdProfile.change_settings, self.user, reserved={0: 2}, temporary={0: 1})

    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_change_settings__success_with_remove_no_reversed_temp_list_match(self, mock_log_logger_debug):
        data = {u'SystemSettings':
                [{u'reservedList': [{u'physicalLayerSubCellsdfId': 2, u'physicalLayesdfrCellIdGroup': 0}],
                  u'temporaryList': [{u'physicalLayerSubCesdfllId': 1, u'physicalLayerCsdfellIdGroup': 0}],
                  u'poid': 281649241422715, u'name': u'PciSystemSettings'}]}
        response = Mock(ok=True)
        response.json.return_value = data
        self.user.get.return_value = response
        self.user.put.side_effect = [response, Mock(ok=False)]
        AutoIdProfile.change_settings(self.user, reserved={0: 2}, temporary={0: 1}, remove=True)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    def test_create__raises_httperror(self, _):
        user = Mock()
        name = "Test"
        user.post.return_value = Mock(ok=False)
        profile = AutoIdProfile(user, name)
        profile.profile_attributes = profile.node_poids = {}
        profile.schedule_epoch_times = []
        profile.user = user
        profile.profile_state = profile.schedule_type = profile.description = profile.collection_id = name
        profile.conflict_setting_type = profile.name = name
        self.assertRaises(HTTPError, profile.create)

    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.get_by_name')
    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.auto_id_management.AutoIdProfile._delete_collection')
    def test_delete__deletes_collection(self, mock_delete_collection, *_):
        user = Mock()
        user.post.return_value = Mock(ok=True)
        name = "Test"
        profile = AutoIdProfile(user, name)
        profile.name = profile.profile_id = profile.collection = name
        profile.user = user
        profile.delete()
        self.assertTrue(mock_delete_collection.called)

    @patch('enmutils_int.lib.auto_id_management.log.logger.info')
    def test_validate_success(self, mock_log_logger_info):
        check_id = "00003"
        data = {u'totalRecords': 0, u'userAction': None, u'code': 200,
                u'data': [{u'status': u'SUCCESS', u'id': u'1972768761', u'complete': True}], u'description':
                    u'The request has succeeded. The response returns information on the message-body'}
        response = Mock(ok=True)
        response.json.return_value = data
        self.user.get.return_value = response
        self.auto_id._validate(query_id=check_id, endpoint="validate")
        self.assertTrue(mock_log_logger_info.called)

    @patch('enmutils_int.lib.auto_id_management.timedelta')
    @patch('enmutils_int.lib.auto_id_management.datetime')
    @patch('enmutils_int.lib.auto_id_management.log.logger.info')
    def test_validate_partial(self, mock_log_logger_info, mock_date_time, mock_delta):
        check_id = "00003"
        data = {u'totalRecords': 0, u'userAction': None, u'code': 200,
                u'data': [{u'status': u'PARTIAL', u'id': u'1972768761', u'complete': True}],
                u'description': u'The request has succeeded. The response returns information on the message-body'}
        mock_delta.return_value = -2
        mock_date_time.now.return_value = -2
        self.assertRaises(TimeOutError, self.auto_id._validate, query_id=check_id, endpoint="validate")
        mock_delta.return_value = 3
        mock_date_time.now.return_value = 5
        response = Mock(ok=True)
        response.json.return_value = data
        self.user.get.return_value = response
        self.auto_id._validate(query_id=check_id, endpoint="validate")
        self.assertTrue(mock_log_logger_info.called)

    def test_validate_failure(self):
        check_id = "00003"
        data = {u'data': [{u'status': u'FAILURE', u'id': u'1972768761', u'complete': True}]}
        response = Mock(ok=True)
        response.json.return_value = data
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.auto_id._validate, query_id=check_id, endpoint="validate")

    @patch('enmutils_int.lib.auto_id_management.timedelta')
    @patch('enmutils_int.lib.auto_id_management.datetime')
    @patch('enmutils_int.lib.auto_id_management.time.sleep')
    def test_validate__raises_for_status(self, mock_sleep, mock_datetime, mock_timedelta):
        check_id = "00003"
        data = {u'data': [{u'status': u'FAILURE', u'id': u'1972768761', u'complete': False}]}
        mock_timedelta.side_effect = [2, -2]
        mock_datetime.now.side_effect = [2, 2, 2, -2, -2, -2]
        response = Mock(ok=False)
        response.json.return_value = data
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.auto_id._validate, query_id=check_id, endpoint="validate")
        self.assertEqual(1, response.raise_for_status.call_count)
        self.assertEqual(1, mock_sleep.call_count)

    def test_validate__failure_with_reason(self):
        check_id = "00003"
        data = {u'totalRecords': 0, u'userAction': None, u'code': 200,
                u'data': [{u'status': u'FAILURE_WITH_REASON', u'id': u'1972768761', u'complete': True}],
                u'description': u'The request has not succeeded. The response returns information on the message-body'}
        response = Mock(ok=True)
        response.json.return_value = data
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.auto_id._validate, query_id=check_id, endpoint="validate")

    def test_validate__logs_if_no_status(self):
        check_id = "00003"
        data = {u'totalRecords': 0, u'userAction': None, u'code': 200,
                u'data': [{u'status': u'', u'id': u'1972768761', u'complete': True}],
                u'description': u'The request has not succeeded. The response returns information on the message-body'}
        response = Mock(ok=True)
        response.json.return_value = data
        self.user.get.return_value = response
        self.assertRaises(RuntimeError, self.auto_id._validate, query_id=check_id, endpoint="validate")

    @patch('enmutils_int.lib.auto_id_management.log.logger.info')
    def test_delete_conflicts_success(self, mock_log_logger_info):
        check_id = "00003"
        response = Mock(ok=True)
        response.json.return_value = {u'Success': u'True'}
        self.user.delete_request.return_value = response
        self.auto_id._delete_conflicts(check_id=check_id)

        self.assertTrue(mock_log_logger_info.called)

    def test_delete_conflicts_success_http_exception(self):
        check_id = "00003"
        response = Mock(ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.delete_request.return_value = response
        self.assertRaises(HTTPError, self.auto_id._delete_conflicts, check_id=check_id)

    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._get_epoch_schedule')
    def test_get_scheduler(self, mock_get_epoch_schedule):
        mock_get_epoch_schedule.return_value = [1510269300000L, 1510312500000L]
        return_value = {'scheduleTimes': [1510269300000L, 1510312500000L], 'networkTechnology': 'LTE',
                        'toGenerateAlarm': False, 'profileName': 'closed_unit_test', 'hardLock': False,
                        'conflictSettingType': 'CLOSED_LOOP', 'networkConflictSettingType': 'LTE_CLOSED_LOOP',
                        'scheduleType': 'RANGE', 'maxRetries': 2, 'topologyMoIds': []}

        self.assertEqual(self.closed_loop_profile.get_scheduler(), return_value)

    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._delete_conflicts')
    @patch('enmutils_int.lib.auto_id_management.ManualAutoIdProfile._delete_check')
    def test_profile_clean(self, mock_delete_check, mock_delete_conflicts):
        self.auto_id.check_id = "00003"

        self.auto_id.profile_clean()

        self.assertTrue(mock_delete_check.called)
        self.assertTrue(mock_delete_conflicts.called)
        self.assertEqual(self.auto_id.check_id, None)
        self.assertEqual(self.auto_id.calculate_id, None)
        self.assertEqual(self.auto_id.resolve_id, None)
        self.assertEqual(self.auto_id.check_total_records, 0)

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.workload.aid_setup.AID_SETUP.verify_node_versions_on_enm")
    @patch("enmutils_int.lib.workload.aid_setup.undo_settings_changes")
    @patch("enmutils_int.lib.workload.aid_setup.partial")
    @patch("enmutils_int.lib.workload.aid_setup.AutoIdProfile")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users")
    def test_run__in_aid_setup_is_successful(
            self, mock_create_profile_users, mock_autoidprofile, mock_partial, mock_undo_settings_changes, *_):
        profile = self.AID_SETUP
        profile.SUPPORTED_NODE_TYPES = ["abc", "def"]
        profile.NUM_USERS = 1
        profile.USER_ROLES = "blah"
        user = Mock()
        mock_create_profile_users.return_value = [user]
        profile.run()
        mock_autoidprofile.change_settings.assert_called_with(user, reserved={0: 2}, temporary={0: 1})
        mock_partial.assert_called_with(mock_undo_settings_changes, user)

    @patch("enmutils_int.lib.workload.aid_setup.undo_settings_changes")
    @patch("enmutils_int.lib.workload.aid_setup.partial")
    @patch("enmutils_int.lib.workload.aid_setup.AID_SETUP.verify_node_versions_on_enm")
    @patch("enmutils_int.lib.profile.Profile.add_error_as_exception")
    @patch("enmutils_int.lib.workload.aid_setup.AutoIdProfile")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users")
    def test_run__in_aid_setup_adds_error_if_aid_unavailable_on_enm(
            self, mock_create_profile_users, mock_autoidprofile, mock_add_error_as_exception, *_):
        profile = self.AID_SETUP
        profile.NUM_USERS = 1
        profile.SUPPORTED_NODE_TYPES = ["abc", "def"]
        profile.USER_ROLES = "blah"
        user = Mock()
        mock_create_profile_users.return_value = [user]
        mock_autoidprofile.change_settings.side_effect = Exception
        profile.run()
        self.assertTrue(mock_add_error_as_exception.called)

    def test_verify_node_versions_on_enm__sucessful(self):
        profile = self.AID_SETUP
        profile.SUPPORTED_NODE_TYPES = ["RadioNode"]
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'NetworkElement', u'NodeId\trelease', u'node_1\t19.Q3', u'node2\t19.Q3',
                                            u'', u'485 instance(s)']
        profile.verify_node_versions_on_enm(self.user, "RadioNode")

    def test_verify_node_versions_on_enm__raises_environerror_radionode(self):
        profile = self.AID_SETUP
        profile.SUPPORTED_NODE_TYPES = ["RadioNode"]
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'NetworkElement', u'NodeId\trelease', u'node_1\t19.Q2', u'node2\t19.Q3',
                                            u'', u'485 instance(s)']
        self.assertRaises(EnvironError, profile.verify_node_versions_on_enm, self.user, "RadioNode")

    def test_verify_node_versions_on_enm__raises_environerror_erbs(self):
        profile = self.AID_SETUP
        profile.SUPPORTED_NODE_TYPES = ["ERBS"]
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u'NetworkElement', u'NodeId\trelease', u'node_1\tJ.2.344', u'node2\tJ.4.332',
                                            u'', u'485 instance(s)']
        self.assertRaises(EnvironError, profile.verify_node_versions_on_enm, self.user, "ERBS")

    @patch("enmutils_int.lib.workload.aid_setup.AutoIdProfile")
    def test_undo_settings_changes__in_aid_setup_is_successful(self, mock_autoidprofile, *_):
        user = Mock()
        aid_setup.undo_settings_changes(user)
        mock_autoidprofile.change_settings.assert_called_with(user, reserved={0: 2}, temporary={0: 1}, remove=True)


class OpenLoopAutoIdProfileTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.auto_id_management.OpenLoopAutoIdProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.auto_id_management.AutoIdProfile")
    def test_get_scheduler__returns_correct_data(self, mock_auto_id, _):
        open_loop = OpenLoopAutoIdProfile()
        open_loop.name = open_loop.conflict_setting_type = 'test'
        open_loop.node_poids = {}
        open_loop.profile_attributes = {"networkTechnology": "", "toGenerateAlarm": "", "hardLock": "",
                                        "maxRetries": ""}
        expected_dict = {'networkTechnology': '', 'toGenerateAlarm': '', 'profileName': 'test',
                         'conflictSettingType': 'test', 'networkConflictSettingType': 'LTE_test', 'topologyMoIds': []}
        self.assertEqual(expected_dict, open_loop.get_scheduler())


class ClosedLoopAutoIdProfileTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.auto_id_management.ClosedLoopAutoIdProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.auto_id_management.AutoIdProfile")
    def test_get_scheduler__returns_none_when_not_schedule_epoch_times(self, mock_auto_id, _):
        closed_loop = ClosedLoopAutoIdProfile()
        closed_loop.schedule_epoch_times = None
        self.assertIsNone(closed_loop.get_scheduler())

    @patch("enmutils_int.lib.auto_id_management.ClosedLoopAutoIdProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.auto_id_management.AutoIdProfile")
    def test_get_scheduler__returns_data_when_len_epoch_times_lt_2(self, *_):
        closed_loop = ClosedLoopAutoIdProfile()
        closed_loop.schedule_epoch_times = [None]
        closed_loop.schedule_type = closed_loop.name = closed_loop.conflict_setting_type = 'test'
        closed_loop.node_poids = {}
        closed_loop.profile_attributes = {"networkTechnology": "", "toGenerateAlarm": "", "hardLock": "",
                                          "maxRetries": ""}
        expected_data = {'scheduleTimes': [None], 'networkTechnology': '', 'toGenerateAlarm': '',
                         'profileName': 'test', 'hardLock': '', 'conflictSettingType': 'test',
                         'networkConflictSettingType': 'LTE_test', 'scheduleType': 'test', 'maxRetries': '',
                         'topologyMoIds': []}
        self.assertEqual(expected_data, closed_loop.get_scheduler())


class TopologyGroupRangeTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.auto_id_management.Collection")
    def test__init__creates_new_collection(self, mock_collection):
        mock_collection.id = 1234
        topology_group_range = TopologyGroupRange(Mock(), 'test', nodes=[Mock()])
        self.assertTrue(topology_group_range.collection.create.called)

    @patch('enmutils_int.lib.netex.Collection.create', side_effect=HTTPError())
    def test__init__raises_exception(self, mock_collection):
        mock_collection.create.side_effect = Exception('some error')
        self.assertRaises(HTTPError, TopologyGroupRange, Mock(), 'test', nodes=[Mock()])

    @patch("enmutils_int.lib.auto_id_management.TopologyGroupRange.__init__", return_value=None)
    def test_create__raises_for_status(self, _):
        topology_group_range = TopologyGroupRange(Mock(), 'test')
        topology_group_range.name = 'test'
        topology_group_range.first_pci_value_range = {'test': Mock()}
        topology_group_range.node_poids = topology_group_range.last_pci_value_range = {'test': Mock()}
        topology_group_range.collection_id = 'test'
        response = Mock(ok=False)
        topology_group_range.user = topology_group_range.range_id = Mock()
        response.json.return_value = {'data': [{'id': 0}]}
        topology_group_range.user.post.return_value = response
        topology_group_range.create()
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.auto_id_management.TopologyGroupRange.__init__", return_value=None)
    def test_delete__raises_for_status(self, _):
        topology_group_range = TopologyGroupRange(Mock(), 'test')
        response = Mock(ok=False)
        topology_group_range.user = topology_group_range.range_id = Mock()
        topology_group_range.collection = None
        topology_group_range.user.delete_request.return_value = response
        topology_group_range.delete()
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.auto_id_management.TopologyGroupRange.__init__", return_value=None)
    @patch('enmutils_int.lib.auto_id_management.log.logger.debug')
    def test_delete_collection__logs_exception(self, mock_debug, _):
        topology_group_range = TopologyGroupRange(Mock(), 'test')
        topology_group_range.name = 'test'
        mock_collection = topology_group_range.collection = Mock()
        mock_collection.delete.side_effect = Exception('some error')
        topology_group_range._delete_collection()
        mock_debug.assert_called_once_with('Collection deletion problem in Topology Group Range: test\n'
                                           ' Exception: some error')

    @patch("enmutils_int.lib.auto_id_management.TopologyGroupRange.__init__", return_value=None)
    @patch("enmutils_int.lib.auto_id_management.TopologyGroupRange.delete")
    def test_teardown__success(self, mock_delete, _):
        topology_group_range = TopologyGroupRange(Mock(), 'test')
        topology_group_range.name = 'test'
        topology_group_range.collection = Mock()
        topology_group_range._teardown()
        self.assertEqual(1, mock_delete.call_count)

    @patch("enmutils_int.lib.auto_id_management.TopologyGroupRange.__init__", return_value=None)
    @patch("enmutils_int.lib.auto_id_management.TopologyGroupRange.delete", side_effect=Exception('some error'))
    @patch('enmutils_int.lib.auto_id_management.log.logger.warn')
    def test_teardown__logs_exception(self, mock_warn, mock_delete, _):
        topology_group_range = TopologyGroupRange(Mock(), 'test')
        topology_group_range.collection = None
        topology_group_range._teardown()
        self.assertEqual(1, mock_delete.call_count)
        mock_warn.assert_called_once_with('some error')


class NonPlannedPCIRangeTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_create__raises_for_status(self):
        non_palnned_pci_range = NonPlannedPCIRange(Mock(), Mock(), {100: 0})
        response = Mock(ok=False)
        non_palnned_pci_range.user.post.return_value = response
        non_palnned_pci_range.create()
        self.assertTrue(response.raise_for_status.called)

    def test_delete__raises_for_status(self):
        non_palnned_pci_range = NonPlannedPCIRange(Mock(), Mock(), {100: 0})
        response = Mock(ok=False)
        non_palnned_pci_range.user.delete_request.return_value = response
        non_palnned_pci_range.range_id = Mock()
        non_palnned_pci_range.delete()
        self.assertEqual(1, response.raise_for_status.call_count)

    @patch("enmutils_int.lib.auto_id_management.NonPlannedPCIRange.delete")
    def test_teardown__success(self, mock_delete):
        non_palnned_pci_range = NonPlannedPCIRange(Mock(), Mock(), {100: 0})
        non_palnned_pci_range._teardown()
        self.assertEqual(1, mock_delete.call_count)


class AutoIdTearDownProfileTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.auto_id_management.Collection.__init__", return_value=None)
    def test__init__success(self, _):
        user = name = profile_id = collection_id = 'test'
        profile_taerdown = AutoIdTearDownProfile(user, name, profile_id, collection_id)
        self.assertEqual('test', profile_taerdown.profile_id)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
