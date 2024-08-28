import unittest2
from mock import Mock, patch
from parameterizedtestcase import ParameterizedTestCase
from requests import HTTPError

from testslib import unit_test_utils

from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.enm_node import ERBSNode as erbs
from enmutils.lib.enm_node import MiniLink6352Node as mltn6352
from enmutils.lib.enm_node import MiniLinkIndoorNode as mltn
from enmutils.lib.enm_node import RadioNode as radionode
from enmutils.lib.enm_node import SGSNNode as sgsn

from enmutils_int.lib.shm_backup_jobs import (BackupJobBSC, BackupJobCOMECIM, BackupJobCPP,
                                              BackupJobMiniLink, BackupJobMiniLink669x,
                                              BackupJobMiniLink6352, BackupJobRouter6675,
                                              BackupJobSGSN, BackupJobSpitFire)


class SHMBackupJobCPPUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        node = erbs(node_id='testNode', primary_type='ERBS')
        nodes = [node]
        time = "00:00:00"
        self.job = BackupJobCPP(user=self.user, nodes=nodes, description='testDescription', schedule_time=time)
        self.properties = self.job.set_properties()
        self.activities = self.job.set_activities()
        self.rollback_job = BackupJobCPP(user=self.user, nodes=nodes, description='testDescription',
                                         schedule_time=time, set_as_startable=True)
        self.rollback_properties = self.rollback_job.set_properties()
        self.rollback_activities = self.rollback_job.set_activities()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob.fetch_job_status')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobCPP._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobCPP._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create__erbs_backup_job_success(self, mock_log, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job.create()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    def test_set_schedule_returns_correct_data_type(self):
        self.assertEqual(type(self.job.set_schedule()), list)
        self.assertEqual(type(self.job.set_schedule()[0]), dict)

    def test_set_activities_returns_correct_data_type(self):
        self.assertEqual(type(self.activities), list)
        self.assertEqual(type(self.rollback_activities), list)
        self.assertEqual(type(self.activities[0]), dict)

    def test_set_properties_returns_correct_data_type(self, *_):
        self.assertEqual(type(self.properties), list)
        self.assertEqual(type(self.properties[0]), dict)

    def set_as_startable_alters_properties(self):
        self.assertEqual(len(self.properties[0]), 5)
        self.assertEqual(len(self.rollback_properties[0]), 6)
        self.assertNotEqual(self.properties[0], self.rollback_properties[0])

    def set_as_startable_alters_activities(self):
        self.assertEqual(len(self.activities[0]), 2)
        self.assertEqual(len(self.rollback_activities), 4)
        self.assertNotEqual(self.activities[0], self.activities[0])


class SHMBackupJobCOMECIMRadioUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        node = radionode(node_id='testNode', primary_type='RadioNode', platform="ECIM")
        nodes = [node]
        self.job = BackupJobCOMECIM(user=self.user, nodes=nodes, file_name="efgklm", repeat_count="0",
                                    platform="ECIM")
        self.properties = self.job.set_properties()
        self.activities = self.job.set_activities()
        self.rollback_job = BackupJobCOMECIM(user=self.user, nodes=nodes, file_name="asdklm", repeat_count="0",
                                             platform="ECIM", set_as_startable=True)
        self.rollback_properties = self.rollback_job.set_properties()
        self.rollback_activities = self.rollback_job.set_activities()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob.fetch_job_status')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobCOMECIM._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobCOMECIM._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create__radionode_backup_job_success(self, mock_log, *_):
        response = Mock(status_code=200, ok=True)
        self.user.post.return_value = response
        self.job.create()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    def test_set_radionode_activities_returns_correct_data_type(self):
        self.assertEqual(type(self.activities), list)
        self.assertEqual(type(self.activities[0]), dict)

    def test_set_radionode_properties_returns_correct_data_type(self, *_):
        self.assertEqual(type(self.properties), list)
        self.assertEqual(type(self.properties[0]), dict)

    def set_radionode_rollback_alters_properties(self):
        self.assertEqual(len(self.properties[0]), 5)
        self.assertEqual(len(self.rollback_properties[0]), 6)
        self.assertNotEqual(self.properties[0], self.rollback_properties[0])

    def set_radionode_rollback_alters_activities(self):
        self.assertEqual(len(self.activities[0]), 2)
        self.assertEqual(len(self.rollback_activities[0]), 4)
        self.assertNotEqual(self.activities[0], self.activities[0])


class SHMBackupJobSpitFireUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()
        nodes = [erbs(node_id='testNode', primary_type='Router6675')]
        self.job = BackupJobSpitFire(user=self.user, nodes=nodes, platform="ECIM")
        self.properties = self.job.set_properties()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_backupjob_router6672_properties(self):
        self.assertEqual(len(self.properties), 2)
        self.assertEqual(len(self.properties[0]), 2)
        self.assertEqual(len(self.properties[1]), 2)
        self.assertEqual(len(self.properties[1]["properties"]), 2)
        self.assertEqual(len(self.properties[1]["properties"][0]), 2)
        self.assertEqual(len(self.properties[1]["properties"][1]), 2)


class SHMBackupJobRouter6675UnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()
        nodes = [erbs(node_id='testNode', primary_type='Router6675')]
        self.job = BackupJobRouter6675(user=self.user, nodes=nodes, platform="ECIM")
        self.properties = self.job.set_properties()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_backupjob_router6675_properties(self):
        self.assertEqual(len(self.properties), 2)
        self.assertEqual(len(self.properties[0]), 2)
        self.assertEqual(len(self.properties[1]), 2)
        self.assertEqual(len(self.properties[1]["properties"]), 2)
        self.assertEqual(len(self.properties[1]["properties"][0]), 2)
        self.assertEqual(len(self.properties[1]["properties"][1]), 2)


class SHMBackupJobMiniLinkUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        node = mltn(node_id='testNode', primary_type='MLTN', platform="ECIM")
        nodes = [node]
        self.job = BackupJobMiniLink(user=self.user, nodes=nodes, file_name="efgklm", repeat_count="0",
                                     platform="ECIM")
        self.properties = self.job.set_properties()
        self.activities = self.job.set_activities()
        self.rollback_job = BackupJobMiniLink(user=self.user, nodes=nodes, file_name="asdklm", repeat_count="0",
                                              platform="ECIM", set_as_startable=True)
        self.rollback_properties = self.rollback_job.set_properties()
        self.rollback_activities = self.rollback_job.set_activities()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobMiniLink._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobMiniLink._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create__mini_link_backup_job_success(self, mock_log, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job.create()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobMiniLink._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobMiniLink._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_radionode_backup_job_failure(self, *_):
        response = Mock()
        response.status_code = 200
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.create)

    def test_set_radionode_activities_returns_correct_data_type(self):
        self.assertEqual(type(self.activities), list)
        self.assertEqual(type(self.activities[0]), dict)

    def test_set_radionode_properties_returns_correct_data_type(self, *_):
        self.assertEqual(type(self.properties), list)
        self.assertEqual(type(self.properties[0]), dict)

    def set_radionode_rollback_alters_properties(self):
        self.assertEqual(len(self.properties[0]), 5)
        self.assertEqual(len(self.rollback_properties[0]), 6)
        self.assertNotEqual(self.properties[0], self.rollback_properties[0])

    def set_radionode_rollback_alters_activities(self):
        self.assertEqual(len(self.activities[0]), 2)
        self.assertEqual(len(self.rollback_activities[0]), 4)
        self.assertNotEqual(self.activities[0], self.activities[0])


class SHMBackupJobMiniLink669xUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        nodes = [mltn6352(node_id='testNode', primary_type='MINI-LINK-669x', platform="MINI_LINK_INDOOR")]
        self.job = BackupJobMiniLink669x(user=self.user, nodes=nodes, platform="MINI_LINK_INDOOR")
        self.properties = self.job.set_properties()
        self.activities = self.job.set_activities()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_backupjob_miniLink669x_node_properties(self):
        self.assertEqual(len(self.properties), 2)
        self.assertEqual(len(self.properties[0]), 2)
        self.assertEqual(len(self.properties[1]), 2)
        self.assertEqual(len(self.properties[1]["properties"]), 1)
        self.assertEqual(len(self.properties[1]["properties"][0]), 2)

    def test_backupjob_miniLink669x_node_activities(self):
        self.assertEqual(len(self.activities), 1)
        self.assertEqual(len(self.activities[0]), 3)


class SHMBackupJobMiniLink6352UnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        node = mltn6352(node_id='testNode', primary_type='MINI-LINK-6352', platform="MINI_LINK_OUTDOOR")
        nodes = [node]
        self.job = BackupJobMiniLink6352(user=self.user, nodes=nodes, file_name="efgklm", repeat_count="0",
                                         platform="MINI_LINK_OUTDOOR")
        self.properties = self.job.set_properties()
        self.activities = self.job.set_activities()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobMiniLink6352._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobMiniLink6352._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create__mltn6352_backup_job_success(self, mock_log, *_):
        self.user.post.return_value = Mock(status_code=200, ok=True)
        self.job.create()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobMiniLink._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobMiniLink._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_mltn6352_backup_job_failure(self, *_):
        response = Mock()
        response.status_code = 200
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.create)

    def test_set_mltn6352_activities_returns_correct_data_type(self):
        self.assertEqual(type(self.activities), list)
        self.assertEqual(type(self.activities[0]), dict)

    def test_set_mltn6352_properties_returns_correct_data_type(self, *_):
        self.assertEqual(type(self.properties), list)
        self.assertEqual(type(self.properties[0]), dict)


class SHMBackupJobCOMECIMUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        node = sgsn(node_id='testNode', primary_type='SGSN', platform="ECIM")
        nodes = [node]
        time = "00:00:00"
        self.job = BackupJobCOMECIM(user=self.user, nodes=nodes, description='testDescription', schedule_time=time)
        self.properties = self.job.set_properties()
        self.activities = self.job.set_activities()
        self.rollback_job = BackupJobCOMECIM(user=self.user, nodes=nodes, description='testDescription',
                                             schedule_time=time, set_as_startable=True)
        self.rollback_properties = self.job.set_properties()
        self.rollback_activities = self.job.set_activities()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobCOMECIM._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobCOMECIM._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_sgsn_backup_job_failure(self, *_):
        response = Mock()
        response.status_code = 200
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.create)

    def test_set_sgsn_activities_returns_correct_data_type(self):
        self.assertEqual(type(self.activities), list)
        self.assertEqual(type(self.activities[0]), dict)

    def test_set_sgsn_properties_returns_correct_data_type(self, *_):
        self.assertEqual(type(self.properties), list)
        self.assertEqual(type(self.properties[0]), dict)

    def set_sgsn_rollback_alters_properties(self):
        self.assertEqual(len(self.properties[0]), 5)
        self.assertEqual(len(self.rollback_properties[0]), 6)
        self.assertNotEqual(self.properties[0], self.rollback_properties[0])

    def set_sgsn_rollback_alters_activities(self):
        self.assertEqual(len(self.activities[0]), 2)
        self.assertEqual(len(self.rollback_activities[0]), 4)
        self.assertNotEqual(self.activities[0], self.activities[0])


class SHMBackupJobSGSNUnitTests(ParameterizedTestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        node = sgsn(node_id='testNode', primary_type='SGSN', platform="ECIM")
        nodes = [node]
        time = "00:00:00"
        self.job = BackupJobSGSN(user=self.user, nodes=nodes, description='testDescription', schedule_time=time)
        self.properties = self.job.set_properties()
        self.activities = self.job.set_activities()
        self.rollback_job = BackupJobSGSN(user=self.user, nodes=nodes, description='testDescription',
                                          schedule_time=time, set_as_startable=True)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobSGSN._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobSGSN._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create__sgsn_backup_job_success(self, mock_log, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job.create()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobSGSN._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobSGSN._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_sgsn_backup_job_failure1(self, *_):
        response = Mock()
        response.status_code = 200
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.create)

    def test_set_sgsn_properties_returns_correct_data_type(self, *_):
        self.assertEqual(type(self.properties), list)
        self.assertEqual(type(self.properties[0]), dict)

    def set_sgsn_rollback_alters_properties(self):
        self.assertEqual(len(self.properties[0]), 5)
        self.assertEqual(len(self.rollback_properties[0]), 6)
        self.assertNotEqual(self.properties[0], self.rollback_properties[0])


class SHMBackupJobBSCUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        node = Mock()
        node.primary_type = 'BSC'
        node.platform = 'AXE'
        node.node_id = "MSC23BSC45"

        nodes = [node]
        time = "00:00:00"
        self.job = BackupJobBSC(user=self.user, nodes=nodes, description='testDescription', schedule_time=time)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobBSC._set_job_id')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobBSC._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_bsc_backup_job_success(self, mock_log, *_):
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.text = {"nodeTopology": [{"nodeName": "MSC23BSC45"}]}
        response.json.side_effect = [{"nodeTopology": [{"nodeName": "MSC23BSC45",
                                                        "neType": "BSC", "axeClusterName": "",
                                                        "components": [{"name": "APG", "cpNames": ["APG"]},
                                                                       {"name": "CP", "cpNames": ["CP"]}],
                                                        "numberOfAPG": 1}],
                                      "failureReason": [], "nodesWithoutComponents": []} for _ in range(4)]
        response_create = Mock()
        response_create.status_code = 201
        response_create.ok = True
        response_create.json.return_value = {"jobName": "shm_bsc_backup_DoxUwE",
                                             "jobConfigId": 281484158035992, "errorCode": "success"}

        self.user.post.side_effect = [response, response_create]
        self.job.create()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    @patch('time.sleep', return_value=lambda _: None)
    def test_create_bsc_backup_job_failure(self, *_):
        response = Mock()
        response.status_code = 200
        response.ok = False
        response.json.return_value = {"nodeTopology": [{"nodeName": "MSC23BSC45",
                                                        "neType": "BSC", "axeClusterName": "",
                                                        "components": [{"name": "APG", "cpNames": ["APG"]},
                                                                       {"name": "CP", "cpNames": ["CP"]}],
                                                        "numberOfAPG": 1}], "failureReason": [],
                                      "nodesWithoutComponents": []}
        self.user.post.side_effect = [response, response, response, response]
        self.assertRaises(EnmApplicationError, self.job.create)

    def test_update_parent_ne_withcomponents__returns_as_expected(self):
        self.job.component_names = {"MSC23BSC45": ["MSC23BSC45__APG", "MSC23BSC45__CP"]}
        expected = [{'selectedComponents': ['MSC23BSC45__APG', 'MSC23BSC45__CP'], 'parentNeName': 'MSC23BSC45'}]
        self.assertTrue(self.job.update_parent_ne_withcomponents(), expected)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
