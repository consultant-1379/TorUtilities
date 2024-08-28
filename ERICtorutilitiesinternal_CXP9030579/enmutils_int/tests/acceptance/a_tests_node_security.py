#!/usr/bin/env python
import pkgutil

import unittest2

from enmutils.lib import log, filesystem
from enmutils_int.lib.node_security import (NodeCredentials, NodeCertificate, NodeTrust, NodeSecurityLevel, NodeSNMP,
                                            get_level, SecurityConfig)
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec, setup_verify

INTERNAL = pkgutil.get_loader('enmutils_int').filename


class NodeCredentialsAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["ADMINISTRATOR"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        user = self.fixture.users[0]
        self.node_credentials = NodeCredentials(user=user, nodes=self.fixture.nodes)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("Node Security", "Remove, create and restore node credentials")
    def test_010_node_credentials_remove_create_and_restore(self):
        self.node_credentials.remove()
        self.node_credentials.create(secure_user='netsim', secure_password='netsim', normal_user='netsim',
                                     normal_password='netsim')
        self.node_credentials.restore()

    @setup_verify(users=1)
    @func_dec("Node Security", "Multiple update and restore node credentials")
    def test_020_node_credentials_multiple_update_and_restore(self):
        self.node_credentials.update(secure_user='DUMMY', secure_password='DUMMY')
        self.node_credentials.restore()
        self.node_credentials.update(normal_user='DUMMY')
        self.node_credentials.restore()
        self.node_credentials.update(normal_password='DUMMY')
        self.node_credentials.restore()


class NodeCertificateAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["ADMINISTRATOR"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        security_config = SecurityConfig(level=2)
        self.node_certificate = NodeCertificate(nodes=self.fixture.nodes, security_config=security_config,
                                                user=self.fixture.users[0])

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("Node Security", "Issue and reissue node certificate")
    def test_010_node_certificate_issue_and_reissue(self):
        self.node_certificate.issue(selected_nodes=self.fixture.nodes, profile_name="test")
        self.node_certificate.reissue(selected_nodes=self.fixture.nodes)


class NodeTrustAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["ADMINISTRATOR"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        security_config = SecurityConfig(level=1)
        self.node_trust = NodeTrust(nodes=self.fixture.nodes, security_config=security_config,
                                    user=self.fixture.users[0])
        self.node_trust.EXCLUSIVE = False
        node_ids = ';'.join(node.node_id for node in self.fixture.nodes)
        filesystem.write_data_to_file(node_ids, "/tmp/nodes.txt")

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("Node Security", "Remove trust certificates")
    def test_020_node_trust_removal(self):
        self.node_trust.remove("nodes.txt", "/tmp/nodes.txt")

    @setup_verify(users=1)
    @func_dec("Node Security", "Distribute trust certificates")
    def test_010_node_trust_distribution(self):
        self.node_trust.distribute("nodes.txt", "/tmp/nodes.txt")


class NodeSecurityLevelAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["ADMINISTRATOR"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        security_config = SecurityConfig(level=1)
        self.node_security_level = NodeSecurityLevel(nodes=self.fixture.nodes, security_config=security_config,
                                                     user=self.fixture.users[0], timeout=15 * 60)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("Node Security", "Deactivate security level")
    def test_010_node_security_set_level(self):
        try:
            security_level_dictionary = get_level([node.node_id for node in self.fixture.nodes], self.fixture.users[0])
        except Exception as e:
            log.logger.debug(str(e))
            security_level_dictionary = {}
        if security_level_dictionary and self.fixture.nodes[0].node_id in security_level_dictionary.keys():
            security_level = 1 if security_level_dictionary.get(self.fixture.nodes[0].node_id) != int(1) else 2
            self.node_security_level.set_level(security_level=security_level)
        else:
            log.logger.debug("Unable to determine existing security level.")

    def test_020_node_security_get_level(self):
        get_level([node.node_id for node in self.fixture.nodes], self.fixture.users[0])


class NodeSNMPAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'RadioNode': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["ADMINISTRATOR"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        self.node_snmp = NodeSNMP(nodes=self.fixture.nodes, user=self.fixture.users[0])

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("Node Security", "Set node SNMP version to SNMP_V3")
    def test_010_node_snmp_set_version_to_SNMP_V3(self):
        self.node_snmp.set_version(snmp_version='SNMP_V3')

    @setup_verify(users=1)
    @func_dec("Node Security", "Restore node SNMP version to SNMP_V2C")
    def test_020_node_snmp_restore_version_to_SNMP_V2C(self):
        self.node_snmp.set_version(snmp_version='SNMP_V2C')


if __name__ == "__main__":
    unittest2.main(verbosity=2)
