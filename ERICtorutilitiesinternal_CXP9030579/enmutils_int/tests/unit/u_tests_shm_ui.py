#!/usr/bin/env python
import unittest2
from mock import Mock
from requests.exceptions import HTTPError

from enmutils.lib.enm_node import ERBSNode as erbs
from enmutils_int.lib import shm_ui
from enmutils_int.lib.shm_backup_jobs import BackupJobCPP
from testslib import unit_test_utils

URL = 'https://enmapache.athtem.eei.ericsson.se/'
HEADERS = {'Content-Type': 'application/json; charset=utf-8', 'Accept': 'application/json, text/javascript, */*; q=0.01'}
application_json = 'application/json'


class ShmUITestCase(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.shm_ui = shm_ui
        node = erbs(node_id='testNode', primary_type='ERBS')
        self.nodes = [node]
        time = "00:00:00"
        self.job = BackupJobCPP(user=self.user, nodes=self.nodes, name='testJob',
                                description='testDescription', schedule_time=time)
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_shm_home(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_home(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_view_inventory(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_view_inventory(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_license_inventory_home(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_license_inventory_home(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_license_go_to_topology_browser(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_license_go_to_topology_browser(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_import_license_keys(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_import_license_keys(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_software_administration_home(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_software_administration_home(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_software_administration_upgrade_tab(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_software_administration_upgrade_tab(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_import_software_package(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_import_software_package(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_software_go_to_topology_browser(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_software_go_to_topology_browser(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_software_help(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_software_help(user=self.user)
        self.assertEqual(self.user.get.call_count, 3)

    def test_shm_hardware_administration_home(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_hardware_administration_home(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_hardware_go_to_topology_browser(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_hardware_go_to_topology_browser(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_backup_administration_home(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_backup_administration_home(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_shm_backup_go_to_topology_browser(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.shm_backup_go_to_topology_browser(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_view_job_details(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.view_job_details(user=self.user, job=self.job)
        self.assertEqual(self.user.get.call_count, 1)

    def test_view_job_logs(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.view_job_logs(user=self.user, job=self.job)
        self.assertEqual(self.user.get.call_count, 1)

    def test_download_logs(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.shm_ui.download_logs(user=self.user)
        self.assertEqual(self.user.get.call_count, 1)

    def test_return_nodes_to_shm_app(self):
        response = Mock()
        response.ok = True
        self.user.post.return_value = response
        self.shm_ui.return_nodes_to_shm_app(user=self.user, nodes=self.nodes)
        self.assertEqual(self.user.post.call_count, 1)

    def test_return_nodes_to_shm_app_failure(self):
        response = Mock()
        response.ok = False
        response.text = 'nodes unavailable'
        self.user.post.side_effect = [response, HTTPError]
        self.assertRaises(HTTPError, self.shm_ui.return_nodes_to_shm_app, user=self.user, nodes=self.nodes)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
