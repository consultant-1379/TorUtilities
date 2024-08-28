#!/usr/bin/env python

import unittest2

from enmutils_int.lib.services import deploymentinfomanager_adaptor
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec


class DeploymentInfoManagerAcceptanceTests(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("DeploymentInfoManager Service", "Confirm the Apache URL can be retrieved.")
    def test_01_apache_url(self):
        """
        APT team uses this endpoint to get apache url value. If there are any changes made to this endpoint API, please inform them before merging
        """
        apache_url = deploymentinfomanager_adaptor.get_apache_url()
        self.assertIn("https", apache_url)
        self.assertIn("ericsson", apache_url)

    @func_dec("DeploymentInfoManager Service", "Confirm the service can return requested service information.")
    def test_02_query_service_information(self):
        deployment_info = deploymentinfomanager_adaptor.get_deployment_service_info('dps_persistence_provider')
        self.assertIn("neo4j", deployment_info)

    @func_dec("DeploymentInfoManager Service", "Confirm the service can set PIB values.")
    def test_03_set_pib_value_on_enm(self):
        deploymentinfomanager_adaptor.update_pib_value('cmserv', 'maxAmosSessions', '150', 'terminal-websocket')

    @func_dec("DeploymentInfoManager Service", "Confirm the service can read PIB values.")
    def test_04_get_pib_value_on_enm(self):
        """
        APT team uses this endpoint to read pib values. If there are any changes made to this endpoint API, please inform them before merging
        """
        deployment_info = deploymentinfomanager_adaptor.read_pib_value('cmserv', 'maxAmosSessions',
                                                                       'terminal-websocket')
        self.assertEqual(int(deployment_info), 150)

    @func_dec("DeploymentInfoManager Service", "Confirm the service can reset PIB values.")
    def test_05_reset_pib_value_on_enm(self):
        deploymentinfomanager_adaptor.update_pib_value('cmserv', 'maxAmosSessions', '120', 'terminal-websocket')

    @func_dec("DeploymentInfoManager Service", "Confirm the service can read reset PIB values.")
    def test_06_get_reset_pid_value_on_enm(self):
        deployment_info = deploymentinfomanager_adaptor.read_pib_value('cmserv', 'maxAmosSessions',
                                                                       'terminal-websocket')
        self.assertEqual(int(deployment_info), 120)

    @func_dec("DeploymentInfoManager Service", "Confirm the service can copy EMP key if on vENM.")
    def test_07_copy_emp_key(self):
        deploymentinfomanager_adaptor.copy_cloud_user_key_to_emp()

    @func_dec("DeploymentInfoManager Service", "Confirm the service can refresh poids.")
    def test_08_poid_refresh(self):
        deploymentinfomanager_adaptor.poid_refresh()

    @func_dec("DeploymentInfoManager Service", "Confirm the service can setup password less access on lms.")
    def test_09_lms_password(self):
        deploymentinfomanager_adaptor.lms_password_less_access()

    @func_dec("DeploymentInfoManager Service", "Check if workload VM has access to ENM deployment")
    def test_10_check_enm_access(self):
        deploymentinfomanager_adaptor.check_enm_access()

    @func_dec("DeploymentInfoManager Service", "Check if ENM password ageing is enabled")
    def test_11_check_ageing_policy(self):
        deploymentinfomanager_adaptor.check_password_ageing_policy_status()

    @func_dec("DeploymentInfoManager Service", "Check deployment config type e.g. forty_network")
    def test_12_check_deployment_config(self):
        """
        APT team uses this endpoint to get network file values. If there are any changes made to this endpoint API, please inform them before merging
        """
        deploymentinfomanager_adaptor.check_deployment_config()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
