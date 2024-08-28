from collections import defaultdict

import unittest2
from enmutils.lib.enm_node import BSCNode
from enmutils_int.lib.shm_delete_jobs import (DeleteBackupOnNodeJobCPP, DeleteBackupOnNodeJobBSC,
                                              DeleteSoftwarePackageOnNodeJob, DeleteInactiveSoftwarePackageOnNodeJob)
from mock import Mock, patch
from requests.exceptions import HTTPError
from testslib import unit_test_utils


class SHMDeleteJobUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        node = Mock()
        node.primary_type = 'ERBS'
        node.node_id = 'testNode'
        node.node_version = '16A'
        nodes = [node]

        bsc_node = Mock()
        bsc_node.primary_type = 'BSC'
        bsc_node.node_id = 'MSC07BSC14'
        radio_node = Mock()
        radio_node.primary_type = "RadioNode"
        sgsn_node = Mock()
        sgsn_node.primary_type = "SGSN-MME"
        self.job = DeleteBackupOnNodeJobCPP(user=self.user, nodes=nodes, description='testDescription',
                                            file_name='unitfilename')

        self.bsc_delete_job = DeleteBackupOnNodeJobBSC(user=self.user, nodes=[bsc_node, bsc_node],
                                                       remove_from_rollback_list="TRUE",
                                                       backup_start_time=1553600408324, platform="AXE")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm.json.loads')
    def test_get_node_backup_items_handles_single_cv_list(self, mock_json):
        response = Mock()
        response.status_code = 200
        response.ok = True
        mock_json.return_value = {u'unsupportedNodes': {}, u'backupItemList': [{u'location': 'NODE', u'name': 'unitfilename'}]}
        self.user.post.return_value = response
        self.assertEqual("unitfilename", self.job.get_node_backup_items())

    @patch('enmutils_int.lib.shm.json.loads')
    def test_get_node_backup_items_handles_full_cv_list(self, mock_json):
        response = Mock()
        response.status_code = 200
        response.ok = True
        mock_json.return_value = {u'unsupportedNodes': {},
                                  u'backupItemList': [{u'location': 'NODE', u'name': 'unitfilename'}]}
        self.user.post.return_value = response
        self.assertEqual([{u'location': 'NODE', u'name': 'unitfilename'}],
                         self.job.get_node_backup_items(all_backups=True))

    @patch('enmutils_int.lib.shm.json.loads')
    def test_get_node_backup_items_handles_no_cv_list(self, mock_json):
        response = Mock()
        response.status_code = 200
        response.ok = True
        mock_json.return_value = {u'unsupportedNodes': {},
                                  u'backupItemList': []}
        self.user.post.return_value = response
        self.assertEqual([], self.job.get_node_backup_items())

    @patch('enmutils_int.lib.shm.json.loads')
    def test_set_properties(self, mock_json):
        self.job.resolve_cv_name = True
        response = Mock()
        response.status_code = 200
        response.ok = True
        mock_json.return_value = {u'unsupportedNodes': {},
                                  u'backupItemList': [{u'location': 'no_node', u'name': 'no_file'}]}
        self.user.post.return_value = response
        self.assertEqual([], self.job.get_node_backup_items())
        self.job.set_properties()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobCPP._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobCPP._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_delete_cv_on_node_job_success(self, mock_log, mock_wait_job, mock_set_job, _):
        response = Mock()
        response.status_code = 200
        response.ok = True
        self.user.post.return_value = response
        self.job.create()
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_wait_job.called)
        self.assertTrue(mock_set_job.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobCPP._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobCPP._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_delete_cv_on_node_job_failure(self, *_):
        response = Mock()
        response.status_code = 200
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.create)

    @patch('time.sleep', return_value=lambda _: None)
    def test_get_backup_items_job_failure_raises_error(self, *_):
        response = Mock()
        response.status_code = 400
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.get_node_backup_items)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.json.dumps')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._wait_job_to_complete')
    @patch('enmutils_int.lib.shm.json.loads')
    def test_delete_backup_bsc_success(self, mock_json, *_):
        response = Mock()
        response.status_code = 200
        response.ok = True
        mock_json.return_value = {"totalCount": 14, "backupItemList": [{"nodeName": "MSC29BSC58",
                                                                        "name": "ap220-2019-03-14T05-01-10",
                                                                        "date": "1553600408326",
                                                                        "nodeFdn": "NetworkElement=MSC29BSC58",
                                                                        "location": "NODE", "platformType": "AXE",
                                                                        "neType": "BSC",
                                                                        "backupId": "ap220-2019-03-14T05-01-10",
                                                                        "fileName": "ap220-2019-03-14T05-01-10",
                                                                        "componentName": "APG"}]}
        self.user.post.return_value = response
        self.bsc_delete_job.create()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.json.dumps')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._wait_job_to_complete')
    @patch('enmutils_int.lib.shm.json.loads')
    def test_delete_backup_bsc_success_with_different_ne_types(self, mock_json, *_):
        response = Mock()
        response.status_code = 200
        response.ok = True
        mock_json.return_value = {"totalCount": 1,
                                  "backupItemList": [{"nodeName": "MSC29BSC58",
                                                      "name": "ap220-2019-03-14T05-01-10",
                                                      "date": "1553600408326",
                                                      "nodeFdn": "NetworkElement=MSC29BSC58",
                                                      "location": "NODE", "platformType": "AXE",
                                                      "neType": "BSC",
                                                      "backupId": "ap220-2019-03-14T05-01-10",
                                                      "fileName": "ap220-2019-03-14T05-01-10",
                                                      "componentName": "APG"},
                                                     {"nodeName": "MSC29BSC59",
                                                      "name": "ap220-2019-03-14T05-01-11",
                                                      "date": "1553600408326",
                                                      "nodeFdn": "NetworkElement=MSC29BSC58",
                                                      "location": "NODE", "platformType": "AXE",
                                                      "neType": "BSC",
                                                      "backupId": "ap220-2019-03-14T05-01-13",
                                                      "fileName": "ap220-2019-03-14T05-01-13",
                                                      "componentName": "CP"},
                                                     {"nodeName": "MSC29BSC59",
                                                      "name": "ap220-2019-03-14T05-01-12",
                                                      "date": "1553600408326",
                                                      "nodeFdn": "NetworkElement=MSC29BSC59",
                                                      "location": "NODE", "platformType": "AXE",
                                                      "neType": "BSC",
                                                      "backupId": "ap220-2019-03-14T05-01-12",
                                                      "fileName": "ap220-2019-03-14T05-01-12",
                                                      "componentName": "CP"}]}
        self.user.post.return_value = response

        self.bsc_delete_job.create()

    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobBSC.get_node_component_dict')
    @patch('enmutils_int.lib.shm_job.sleep')
    @patch('enmutils_int.lib.shm.json.dumps')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._wait_job_to_complete')
    @patch('enmutils_int.lib.shm.json.loads')
    def test_delete_backup_bsc_raises_EnmApplicationError_without_backupname(self, mock_json, mock_job_status, *_):
        response = Mock()
        response.status_code = 200
        response.ok = True
        mock_json.return_value = {"totalCount": 14,
                                  "backupItemList": [{"nodeName": "MSC29BSC58",
                                                      "date": "1553600408326", "nodeFdn": "NetworkElement=MSC29BSC58",
                                                      "location": "NODE", "platformType": "AXE", "neType": "BSC",
                                                      "backupId": "ap220-2019-03-14T05-01-10",
                                                      "fileName": "ap220-2019-03-14T05-01-10", "componentName": "APG"}]}
        self.user.post.return_value = response
        self.bsc_delete_job.component_names = {"MSC07BSC14": ["MSC07BSC14_APG", "MSC07BSC14_CP"]}
        self.bsc_delete_job.create()
        self.assertTrue(mock_job_status.called)

    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobBSC.get_node_component_dict')
    @patch('enmutils_int.lib.shm_job.sleep')
    @patch('enmutils_int.lib.shm.json.dumps')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._wait_job_to_complete')
    @patch('enmutils_int.lib.shm.json.loads')
    def test_delete_backup_bsc_raises_EnmApplicationError_without_backupitemlist(self, mock_json, mock_job_status, *_):

        response = Mock()
        response.status_code = 200
        response.ok = True
        mock_json.return_value = {"totalCount": 14}
        self.user.post.return_value = response
        self.bsc_delete_job.component_names = {"MSC07BSC14": ["MSC07BSC14_APG", "MSC07BSC14_CP"]}
        self.bsc_delete_job.create()
        self.assertTrue(mock_job_status.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm.json.dumps')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC._wait_job_to_complete')
    @patch('enmutils_int.lib.shm.json.loads')
    def test_delete_backup_bsc_raises_http_error_for_no_response(self, mock_json, *_):
        response = Mock()
        response.ok = False
        mock_json.return_value = {"totalCount": 14}
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.bsc_delete_job.create)


class DeleteBackupOnNodeJobUnitTests(unittest2.TestCase):
    CV_DATA1 = {
        u'backupItemsWithCustomColumns': [],
        u'unsupportedNodes': {},
        u'backupItemList': [{
            u'nodeFdn': u'NetworkElement=MSC22BSC43', u'neType': u'BSC', u'platformType': u'AXE', u'nodeName': u'MSC22BSC43', u'awaitingConfirmation': u'False', u'location': u'NODE',
            u'componentName': u'CP', u'date': u'1621287519542', u'backupId': u'RELFSW9-MSC22BSC43', u'name': u'RELFSW9-MSC22BSC43',
        }, {
            u'nodeFdn': u'NetworkElement=MSC22BSC43', u'neType': u'BSC', u'platformType': u'AXE', u'nodeName': u'MSC22BSC43', u'location': u'NODE', u'componentName': u'APG',
            u'date': u'1621287519896', u'backupId': u'ap220-2021-01-20T18-27-10', u'name': u'ap220-2021-01-20T18-27-10',
        }],
        u'responseMetadata': {u'totalCount': 2, u'clearOffset': False}}

    CV_DATA2 = {
        u'backupItemsWithCustomColumns': [],
        u'unsupportedNodes': {},
        u'backupItemList': [{
            u'nodeFdn': u'NetworkElement=MSC22BSC44', u'neType': u'BSC', u'platformType': u'AXE', u'nodeName': u'MSC22BSC44', u'awaitingConfirmation': u'False', u'location': u'NODE',
            u'componentName': u'CP', u'date': u'1621287519542', u'backupId': u'RELFSW9-MSC22BSC44', u'name': u'RELFSW9-MSC22BSC44',
        }, {
            u'nodeFdn': u'NetworkElement=MSC22BSC44', u'neType': u'BSC', u'platformType': u'AXE', u'nodeName': u'MSC22BSC44', u'location': u'NODE', u'componentName': u'APG',
            u'date': u'1621287519896', u'backupId': u'ap220-2021-01-20T18-27-10', u'name': u'ap220-2021-01-20T18-27-10',
        }],
        u'responseMetadata': {u'totalCount': 2, u'clearOffset': False}}

    def setUp(self):
        unit_test_utils.setup()
        bsc_nodes = [BSCNode(node_id='MSC22BSC43', primary_type="BSC"),
                     BSCNode(node_id='MSC22BSC44', primary_type="BSC")]
        self.tc = DeleteBackupOnNodeJobBSC(user=Mock(), nodes=bsc_nodes,
                                           remove_from_rollback_list="TRUE",
                                           backup_start_time=1621287516304,
                                           profile_name="SHM_39",
                                           shm_schedule_time_strings="shm_schedule_time_strings",
                                           schedule_time_strings="schedule_time_strings")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.shm_job.log")
    @patch("enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJob.get_cvnames")
    def test_generate_payload__generates_payload_as_expected(self, mock_cv_names, _):
        mock_cv_names.side_effect = [self.CV_DATA1, self.CV_DATA2] * 2
        self.tc.generate_payload()
        expected = {
            'mainSchedule': {'execMode': 'IMMEDIATE', 'scheduleAttributes': []},
            'name': 'SHM_39_DELETEBACKUP_BSC_0526115935',
            'activitySchedules': [{'platformType': 'AXE',
                                   'value': [{'neType': 'BSC', 'value': [{'execMode': 'IMMEDIATE', 'order': 1, 'activityName': 'deletebackup'}]}]}],
            'parentNeWithComponents': [{'selectedComponents': ['MSC22BSC43__APG', 'MSC22BSC43__CP'], 'parentNeName': 'MSC22BSC43'},
                                       {'selectedComponents': ['MSC22BSC44__APG', 'MSC22BSC44__CP'], 'parentNeName': 'MSC22BSC44'}],
            'neNames': [{'name': 'MSC22BSC43'}, {'name': 'MSC22BSC44'}],
            'configurations': [{'neProperties': [{'neNames': 'MSC22BSC43__APG', 'properties': [{'value': 'ap220-2021-01-20T18-27-10|NODE', 'key': 'BACKUP_NAME'}]},
                                                 {'neNames': 'MSC22BSC43__CP', 'properties': [{'value': 'RELFSW9-MSC22BSC43|NODE', 'key': 'BACKUP_NAME'}]},
                                                 {'neNames': 'MSC22BSC44__APG', 'properties': [{'value': 'ap220-2021-01-20T18-27-10|NODE', 'key': 'BACKUP_NAME'}]},
                                                 {'neNames': 'MSC22BSC44__CP', 'properties': [{'value': 'RELFSW10-MSC22BSC44|NODE', 'key': 'BACKUP_NAME'}]}],
                                'neType': 'BSC', 'properties': [{'value': 'FALSE', 'key': 'ROLL_BACK'}]}],
            'jobType': 'DELETEBACKUP',
            'description': 'SHM_39_DELETEBACKUP_IMMEDIATE_0526115935'}
        self.assertTrue(self.tc.payload, expected)

    @patch("enmutils_int.lib.shm.log")
    def test_ne_list_types__returns_as_expected(self, _):
        self.tc.cv_names = {
            u'MSC22BSC43': {
                u'ap220-2021-01-20T18-27-10': {
                    u'nodeFdn': u'NetworkElement=MSC22BSC43', u'neType': u'BSC', u'type': u'BRM_SYSTEM_DATA', u'date': u'1621287519896', u'backupId': u'ap220-2021-01-20T18-27-10',
                    u'platformType': u'AXE', u'nodeName': u'MSC22BSC43', u'name': u'ap220-2021-01-20T18-27-10', u'location': u'NODE', u'lastExportedBackup': None, u'componentName': u'APG'},
                u'RELFSW9-MSC22BSC43': {
                    u'nodeFdn': u'NetworkElement=MSC22BSC43', u'neType': u'BSC', u'date': u'1621287519542', u'backupId': u'RELFSW9-MSC22BSC43', u'platformType': u'AXE',
                    u'nodeName': u'MSC22BSC43', u'name': u'RELFSW9-MSC22BSC43', u'location': u'NODE', u'componentName': u'CP'}}}
        expected = {u'BSC': [{'neNames': 'MSC22BSC43__APG', 'properties': [{'value': 'ap220-2021-01-20T18-27-10|NODE', 'key': 'BACKUP_NAME'}]},
                             {'neNames': 'MSC22BSC43__CP', 'properties': [{'value': 'RELFSW9-MSC22BSC43|NODE', 'key': 'BACKUP_NAME'}]}]}
        self.assertEqual(self.tc._ne_list_types(), expected)

    @patch("enmutils_int.lib.shm.log")
    @patch("enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJob.get_cvnames")
    def test_get_node_backup_list__returns_as_expected(self, mock_get_cvs, _):
        mock_get_cvs.return_value = self.CV_DATA1
        expected = defaultdict(dict,
                               {u'MSC22BSC43': {u'ap220-2021-01-20T18-27-10': {u'neType': u'BSC', 'node__component': 'MSC22BSC43__APG',
                                                                               u'nodeName': u'MSC22BSC43', u'nodeFdn': u'NetworkElement=MSC22BSC43', u'date': u'1621287519896',
                                                                               u'componentName': u'APG', u'location': u'NODE', u'platformType': u'AXE',
                                                                               u'backupId': u'ap220-2021-01-20T18-27-10', u'name': u'ap220-2021-01-20T18-27-10'},
                                                u'RELFSW9-MSC22BSC43': {u'nodeFdn': u'NetworkElement=MSC22BSC43', u'componentName': u'CP', u'neType': u'BSC',
                                                                        'node__component': 'MSC22BSC43__CP', u'date': u'1621287519542', u'backupId': u'RELFSW9-MSC22BSC43',
                                                                        u'platformType': u'AXE', u'nodeName': u'MSC22BSC43', u'name': u'RELFSW9-MSC22BSC43',
                                                                        u'awaitingConfirmation': u'False', u'location': u'NODE'}}})
        self.assertEqual(self.tc.get_node_backup_list("MSC22BSC43"), expected)

    def test_collect_available_backup_ne_withcomponents__returns_as_expected(self):
        self.tc.cv_names = {
            u'MSC22BSC43': {
                u'ap220-2021-01-20T18-27-10': {u'neType': u'BSC', 'node__component': 'MSC22BSC43__APG', u'nodeName': u'MSC22BSC43',
                                               u'name': u'ap220-2021-01-20T18-27-10', u'nodeFdn': u'NetworkElement=MSC22BSC43',
                                               u'date': u'1621287519896', u'componentName': u'APG', u'platformType': u'AXE',
                                               u'backupId': u'ap220-2021-01-20T18-27-10', u'location': u'NODE'},
                u'RELFSW9-MSC22BSC43': {u'nodeFdn': u'NetworkElement=MSC22BSC43', u'componentName': u'CP', u'neType': u'BSC',
                                        'node__component': 'MSC22BSC43__CP', u'date': u'1621287519542', u'backupId': u'RELFSW9-MSC22BSC43',
                                        u'platformType': u'AXE', u'name': u'RELFSW9-MSC22BSC43', u'nodeName': u'MSC22BSC43',
                                        u'awaitingConfirmation': u'False', u'location': u'NODE'}}}
        expected = {u'MSC22BSC43': ['MSC22BSC43__APG', 'MSC22BSC43__CP']}
        self.assertEqual(self.tc.collect_available_backup_ne_withcomponents(), expected)

    @patch("enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC.collect_available_backup_ne_withcomponents")
    def test_update_parent_ne_withcomponents__returns_as_expected_for_parent_ne_components(self, mock_collect_ne):
        mock_collect_ne.return_value = {u'MSC22BSC43': ['MSC22BSC43__APG', 'MSC22BSC43__CP']}
        expected = [{'selectedComponents': ['MSC22BSC43__APG', 'MSC22BSC43__CP'], 'parentNeName': 'MSC22BSC43'}]
        self.assertEqual(self.tc.update_parent_ne_withcomponents(), expected)

    @patch("enmutils_int.lib.shm.log")
    @patch("enmutils_int.lib.shm_backup_jobs.BackupJobBSC.get_node_component_dict")
    @patch("enmutils_int.lib.shm_delete_jobs.DeleteBackupOnNodeJobBSC.collect_available_backup_ne_withcomponents")
    def test_update_parent_ne_withcomponents__returns_as_expected_without_parent_ne_components(self, mock_collect_ne, *_):
        mock_collect_ne.return_value = None
        self.tc.component_names = {"MSC22BSC43": ["MSC22BSC43__APG", "MSC22BSC43__CP"], "MSC22BSC44": ["MSC22BSC44__APG", "MSC22BSC44__CP"]}
        expected = [{'selectedComponents': ['MSC22BSC43__APG', 'MSC22BSC43__CP'], 'parentNeName': 'MSC22BSC43'},
                    {'selectedComponents': ['MSC22BSC44__APG', 'MSC22BSC44__CP'], 'parentNeName': 'MSC22BSC44'}]
        self.assertEqual(self.tc.update_parent_ne_withcomponents(), expected)


class SHMDeleteUpgradePackageJobUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        rnode = Mock()
        rnode.primary_type = "RadioNode"
        rnode.node_id = "1234"
        rnode.node_version = '16A'

        self.job3 = DeleteSoftwarePackageOnNodeJob(user=self.user, nodes=[rnode], description='test_radionode_delete',
                                                   upgrade_list=["PackageA", "PackageB"],
                                                   delete_from_rollback_list=True, delete_referred_ups=True)

        enode = Mock()
        enode.primary_type = 'ERBS'
        enode.node_version = '16A'
        enode.node_id = 'testNode'

        self.job = DeleteSoftwarePackageOnNodeJob(user=self.user, nodes=[enode], description='testDescription',
                                                  upgrade_list=["PackageA", "PackageB"],
                                                  delete_from_rollback_list=True, delete_referred_ups=True)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteSoftwarePackageOnNodeJob._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteSoftwarePackageOnNodeJob._wait_job_to_complete')
    def test_create__delete_package_on_node_job_success(self, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job.create()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteSoftwarePackageOnNodeJob._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteSoftwarePackageOnNodeJob._wait_job_to_complete')
    def test_create__delete_package_on_ecim_node_job_success(self, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job3.create()


class SHMDeleteUpgradeInactivePackageJobUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        enode = Mock()
        enode.primary_type = 'ERBS'
        enode.node_version = '16A'
        enode.node_id = 'testNode'
        self.erbs_job = DeleteInactiveSoftwarePackageOnNodeJob(user=self.user, nodes=[enode],
                                                               description='test_erbs_delete_inactive')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteInactiveSoftwarePackageOnNodeJob._set_job_id')
    @patch('enmutils_int.lib.shm_delete_jobs.DeleteInactiveSoftwarePackageOnNodeJob._wait_job_to_complete')
    def test_create__delete_inactive_package_on_node_job_success(self, mock_wait_job_to_complete, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.erbs_job.create()
        self.assertTrue(mock_wait_job_to_complete.called)

    def test_set_configurations_and_properties__verify_elements_count(self):
        self.erbs_job.platform = "CPP"
        properties = self.erbs_job.set_properties()
        configurations = self.erbs_job.set_configurations()
        self.assertEqual(len(properties), 1)
        self.assertIn("neNames", properties[0])
        self.assertEqual(len(properties[0]["properties"]), 1)
        self.assertEqual(len(properties[0]["properties"][0]), 2)
        self.assertEqual(len(configurations), 1)
        self.assertEqual(len(configurations[0]), 3)
        self.assertIn("neType", configurations[0])
        self.assertEqual(len(configurations[0]["neProperties"]), 1)
        self.assertEqual(len(configurations[0]["neProperties"][0]), 2)
        self.assertEqual(len(configurations[0]["neProperties"][0]["properties"]), 1)
        self.assertEqual(len(configurations[0]["neProperties"][0]["properties"][0]), 2)
        self.assertEqual(len(configurations[0]["properties"]), 2)
        self.assertEqual(len(configurations[0]["properties"][0]), 2)
        self.assertEqual(len(configurations[0]["properties"][1]), 2)

    def test_set_configurations__in_deleteinactivesoftwarepackageonnodejob_for_ecim_platform(self):
        radio_job = DeleteInactiveSoftwarePackageOnNodeJob(user=self.user, nodes=[Mock(primary_type="RadioNode")],
                                                           platform="ECIM", description='test_erbs_delete_inactive')
        config_values = radio_job.set_configurations()
        self.assertEqual(len(config_values), 1)
        self.assertEqual(len(config_values[0]), 3)
        self.assertEqual(len(config_values[0]["neProperties"]), 1)
        self.assertEqual(len(config_values[0]["neProperties"][0]), 2)
        self.assertEqual(len(config_values[0]["neProperties"][0]["properties"]), 1)
        self.assertEqual(len(config_values[0]["neProperties"][0]["properties"][0]), 2)
        self.assertEqual(len(config_values[0]["properties"]), 1)
        self.assertEqual(len(config_values[0]["properties"][0]), 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
