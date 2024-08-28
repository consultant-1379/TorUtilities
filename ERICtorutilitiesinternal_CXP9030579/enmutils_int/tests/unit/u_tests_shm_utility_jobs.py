import unittest2
from mock import Mock, patch

from enmutils.lib.enm_node import BSCNode
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.shm_utility_jobs import RestartNodeJob, ShmBackUpCleanUpJob, ShmBSCBackUpCleanUpJob
from testslib import unit_test_utils


class RestartNodeJobUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()
        enode = Mock()
        enode.primary_type = 'ERBS'
        enode.node_id = 'testNode'
        self.job_SHM_28 = RestartNodeJob(user=self.user, nodes=[enode], name='SHMDeleteJobUnitTests',
                                         description='testDescription')
        self.job_SHM_47 = RestartNodeJob(user=self.user, nodes=[enode], name='SHMDeleteJobUnitTests',
                                         description='testDescription', profile_name="SHM_47")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.update_activities_schedule')
    @patch('enmutils_int.lib.shm_utility_jobs.RestartNodeJob._set_job_id')
    @patch('enmutils_int.lib.shm_utility_jobs.RestartNodeJob._wait_job_to_complete')
    def test_create__restart_node_job_success_SHM_28(self, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job_SHM_28.create()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.update_activities_schedule')
    @patch('enmutils_int.lib.shm_utility_jobs.RestartNodeJob._set_job_id')
    @patch('enmutils_int.lib.shm_utility_jobs.RestartNodeJob._wait_job_to_complete')
    def test_create__restart_node_job_success_SHM_47(self, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job_SHM_47.create()


class ShmBSCBackUpCleanUpJobUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()
        bsc_node = BSCNode(node_id='MSC22BSC43', primary_type="BSC")
        enode = Mock()
        enode.primary_type = 'ERBS'
        enode.node_id = 'testNode'

        self.bsc_job = ShmBSCBackUpCleanUpJob(self.user, nodes=[bsc_node], name='ShmBSCBackUpCleanUpJobUnitTests',
                                              description='testDescription', platform="AXE")
        self.job = ShmBSCBackUpCleanUpJob(self.user, nodes=[enode], name='ShmBSCBackUpCleanUpJobUnitTests')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob.update_activities_schedule')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob._set_job_id')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob._wait_job_to_complete')
    @patch("enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob.update_parent_ne_withcomponents")
    @patch('enmutils_int.lib.shm_utility_jobs.json.dumps')
    @patch('enmutils_int.lib.shm_utility_jobs.json.loads')
    @patch("enmutils_int.lib.shm_utility_jobs.ShmJob.fetch_job_status")
    def test_create__bsc_clean_up_job_success(self, mock_job_status, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.bsc_job.create()
        self.assertTrue(mock_job_status.called)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob.update_activities_schedule')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob._set_job_id')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob._wait_job_to_complete')
    @patch("enmutils_int.lib.shm_utility_jobs.ShmJob.update_configuration")
    @patch("enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob.update_parent_ne_withcomponents")
    @patch('enmutils_int.lib.shm_utility_jobs.json.dumps')
    @patch('enmutils_int.lib.shm_utility_jobs.json.loads')
    @patch("enmutils_int.lib.shm_utility_jobs.ShmJob.fetch_job_status")
    @patch("enmutils_int.lib.shm_utility_jobs.ShmJob.update_bsc_backup_deletebackup_housekeeping_in_payload")
    def test_create__not_success(self, mock_update, mock_job_status, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job.create()
        self.assertFalse(mock_update.called)
        self.assertTrue(mock_job_status.called)

    def test_collect_available_backup_ne_withcomponents__success(self):
        self.bsc_job.cv_names = {
            u'MSC22BSC43': {
                u'ap220-2021-01-20T18-27-10': {u'neType': u'BSC', 'node__component': 'MSC22BSC43__APG',
                                               u'nodeName': u'MSC22BSC43',
                                               u'name': u'ap220-2021-01-20T18-27-10',
                                               u'nodeFdn': u'NetworkElement=MSC22BSC43',
                                               u'date': u'1621287519896', u'componentName': u'APG',
                                               u'platformType': u'AXE',
                                               u'backupId': u'ap220-2021-01-20T18-27-10', u'location': u'NODE'},
                u'RELFSW9-MSC22BSC43': {u'nodeFdn': u'NetworkElement=MSC22BSC43', u'componentName': u'CP',
                                        u'neType': u'BSC',
                                        'node__component': 'MSC22BSC43__CP', u'date': u'1621287519542',
                                        u'backupId': u'RELFSW9-MSC22BSC43',
                                        u'platformType': u'AXE', u'name': u'RELFSW9-MSC22BSC43',
                                        u'nodeName': u'MSC22BSC43',
                                        u'awaitingConfirmation': u'False', u'location': u'NODE'}}}
        expected = {u'MSC22BSC43': ['MSC22BSC43__APG', 'MSC22BSC43__CP']}
        self.assertEqual(self.bsc_job.collect_available_backup_ne_withcomponents(), expected)

    def test_collect_available_backup_ne_withcomponents__when_cv_names_has_same_components(self):
        self.bsc_job.cv_names = {
            u'MSC22BSC43': {
                u'ap220-2021-01-20T18-27-10': {u'neType': u'BSC', 'node__component': 'MSC22BSC43__APG',
                                               u'nodeName': u'MSC22BSC43',
                                               u'name': u'ap220-2021-01-20T18-27-10',
                                               u'nodeFdn': u'NetworkElement=MSC22BSC43',
                                               u'date': u'1621287519896', u'componentName': u'APG',
                                               u'platformType': u'AXE',
                                               u'backupId': u'ap220-2021-01-20T18-27-10', u'location': u'NODE'},
                u'RELFSW9-MSC22BSC43': {u'nodeFdn': u'NetworkElement=MSC22BSC43', u'componentName': u'CP',
                                        u'neType': u'BSC',
                                        'node__component': 'MSC22BSC43__APG', u'date': u'1621287519542',
                                        u'backupId': u'RELFSW9-MSC22BSC43',
                                        u'platformType': u'AXE', u'name': u'RELFSW9-MSC22BSC43',
                                        u'nodeName': u'MSC22BSC43',
                                        u'awaitingConfirmation': u'False', u'location': u'NODE'}}}
        expected = {u'MSC22BSC43': ['MSC22BSC43__APG']}
        self.assertEqual(self.bsc_job.collect_available_backup_ne_withcomponents(), expected)

    def test_set_properties__success(self):
        bsc_properties = self.bsc_job.set_properties()
        self.assertEqual(len(bsc_properties), 2)

    def test_set_properties__not_success(self):
        bsc_properties = self.job.set_properties()
        self.assertEqual(bsc_properties, None)

    @patch("enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob.get_node_component",
           return_value=["MSC22BSC43__APG", "MSC22BSC43__CP"])
    def test_get_node_component_dict__success(self, _):
        self.bsc_job.get_node_component_dict()
        self.assertEqual(len(self.bsc_job.component_names), 1)

    @patch("enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob.get_node_component_dict")
    @patch("enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob.collect_available_backup_ne_withcomponents",
           return_value={"MSC22BSC43": ["MSC22BSC43__APG", "MSC22BSC43__CP"]})
    def test_update_parent_ne_withcomponents__success(self, *_):
        expected_output = [{'selectedComponents': ['MSC22BSC43__APG', 'MSC22BSC43__CP'], 'parentNeName': 'MSC22BSC43'}]
        self.assertEqual(self.bsc_job.update_parent_ne_withcomponents(), expected_output)

    @patch("enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob.collect_available_backup_ne_withcomponents",
           return_value=[])
    @patch("enmutils_int.lib.shm_utility_jobs.ShmBSCBackUpCleanUpJob.get_node_component_dict")
    def test_update_parent_ne_withcomponents__when_selected_components_empty(self, *_):
        self.bsc_job.component_names = {"MSC22BSC43": ["MSC22BSC43__APG", "MSC22BSC43__CP"]}
        expected_output = [{'selectedComponents': ['MSC22BSC43__APG', 'MSC22BSC43__CP'], 'parentNeName': 'MSC22BSC43'}]
        self.assertEqual(self.bsc_job.update_parent_ne_withcomponents(), expected_output)

    @patch('enmutils_int.lib.shm.json.dumps')
    @patch('enmutils_int.lib.shm.json.loads')
    def test_get_node_component__success(self, *_):
        response = Mock()
        response.ok = True
        response.json.return_value = {"nodeTopology": [{"nodeName": "MSC22BSC43", "neType": "BSC", "axeClusterName": "null",
                                                        "components": [{"name": "APG", "cpNames": ["APG"]},
                                                                       {"name": "CP", "cpNames": ["CP"]}],
                                                        "numberOfAPG": 1}]}
        response.text = {"nodeTopology": [{"nodeName": "MSC22BSC43", "neType": "BSC", "axeClusterName": "null",
                                           "components": [{"name": "APG", "cpNames": ["APG"]},
                                                          {"name": "CP", "cpNames": ["CP"]}], "numberOfAPG":1}],
                         "failureReason": [], "nodesWithoutComponents": []}
        self.user.post.return_value = response
        self.assertEqual(self.bsc_job.get_node_component(self.bsc_job.nodes), ['APG', 'CP'])

    @patch('enmutils_int.lib.shm_utility_jobs.json.dumps')
    @patch('enmutils_int.lib.shm_utility_jobs.json.loads')
    @patch('time.sleep', return_value=0)
    def test_get_node_component__raises_enm_application_error(self, *_):
        response = Mock()
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(EnmApplicationError, self.bsc_job.get_node_component, node_id=self.bsc_job.nodes)


class ShmBackUpCleanUpJobUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()
        enode, rnode = Mock(), Mock()
        enode.primary_type = 'ERBS'
        enode.node_id = 'testNode'
        rnode.primary_type = 'RadioNode'
        rnode.node_id = 'testNode'

        self.cpp_job = ShmBackUpCleanUpJob(self.user, nodes=[enode])
        self.ecim_job = ShmBackUpCleanUpJob(self.user, nodes=[rnode])

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.update_activities_schedule')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob._set_job_id')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob._wait_job_to_complete')
    def test_create__clean_up_job_success(self, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.cpp_job.create()

    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob._set_job_id')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob._wait_job_to_complete')
    def test_create_clean_up_properties_activities_updates_correctly(self, *_):
        cpp_properties = self.cpp_job.set_properties()
        ecim_properties = self.ecim_job.set_properties()
        cpp_activities = self.cpp_job.set_activities()
        ecim_activities = self.ecim_job.set_activities()
        self.assertNotEquals(cpp_properties, ecim_properties)
        self.assertNotEquals(cpp_activities, ecim_activities)
        self.assertEqual(len(cpp_properties), 3)
        self.assertEqual(len(ecim_properties), 1)
        self.assertEqual(cpp_activities[0].get("activityName"), "cleancv")
        self.assertEqual(ecim_activities[0].get("activityName"), "deletebackup")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
