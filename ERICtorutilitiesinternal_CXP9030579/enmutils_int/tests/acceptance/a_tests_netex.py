#!/usr/bin/env python
import unittest2

from enmutils.lib.arguments import get_random_string
from enmutils_int.lib.netex import Search, Collection
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import setup_verify, func_dec


class NetexAcceptanceTests(unittest2.TestCase):

    collection = None
    NUM_NODES = {'ERBS': 5}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["Network_Explorer_Administrator"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        user = self.fixture.users[0]
        if not NetexAcceptanceTests.collection:
            NetexAcceptanceTests.collection = Collection(user=user, name="acceptance_collection", nodes=self.fixture.nodes)

        self.search = Search(user=user, query="NetworkElement", name="{}_acceptance_test".format(get_random_string(size=5)),
                             nodes=self.fixture.nodes)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("Netex Collection", "No exceptions on successfully creating a collection")
    def test_010_create_collection(self):
        self.collection.create()

    @setup_verify(users=1)
    @func_dec("Netex Collection", "No exceptions on successfully deleting a collection")
    def test_020_delete_collection(self):
        self.collection.delete()

    @setup_verify(users=1)
    @func_dec("Netex Collection", "No exceptions on successfully executing a search")
    def test_030_execute_search(self):
        nodes = self.search.execute().keys()
        for node in self.fixture.nodes:
            self.assertTrue(node.node_id in nodes)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
