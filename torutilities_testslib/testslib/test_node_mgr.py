#!/usr/bin/env python
import os
import pkgutil

from contextlib import contextmanager

from enmutils_int.lib.node_pool_mgr import Pool
from enmutils_int.lib.load_node import LoadNodeMixin
from enmutils.lib import log, persistence, mutexer, filesystem
from enmutils.lib.enm_node import (ERBSNode, SGSNNode, RadioNode, MGWNode, Router6672Node, PICONode, EPGNode, VEPGNode,
                                   RNCNode, SAPCNode, RBSNode, BaseNode)


TESTS = pkgutil.get_loader('testslib').filename


class TestNodeMixin(object):

    def __init__(self, *args, **kwargs):
        super(TestNodeMixin, self).__init__(*args, **kwargs)
        self.test_cls = None
        self.exclusive = False

    def add_test(self, test_cls):
        self.test_cls = test_cls.__name__
        self.exclusive = getattr(self.test_cls, 'EXCLUSIVE', False)
        self._persist()

    def remove_test(self):
        self.test_cls = None
        self.exclusive = False
        self._persist()

    @property
    def used(self):
        if getattr(self.test_cls, 'EXCLUSIVE', False) and not self.exclusive:
            return True
        return bool(self.test_cls)

    @property
    def is_available(self):
        return not self.used

    def is_available_for(self, _):
        return not self.used

    def _persist(self):
        persistence.node_pool_db().set(self.node_id, self, -1, log_values=False)


class TestBaseNode(TestNodeMixin, LoadNodeMixin, BaseNode):  # pylint: disable=too-many-ancestors
    pass


class TestERBSNode(TestNodeMixin, LoadNodeMixin, ERBSNode):  # pylint: disable=too-many-ancestors
    pass


class TestSGSNNode(TestNodeMixin, LoadNodeMixin, SGSNNode):  # pylint: disable=too-many-ancestors
    pass


class TestRadioNode(TestNodeMixin, LoadNodeMixin, RadioNode):  # pylint: disable=too-many-ancestors
    pass


class TestMGWNode(TestNodeMixin, LoadNodeMixin, MGWNode):  # pylint: disable=too-many-ancestors
    pass


class TestSpitFireNode(TestNodeMixin, LoadNodeMixin, Router6672Node):  # pylint: disable=too-many-ancestors
    pass


class TestPICOLoadNode(TestNodeMixin, LoadNodeMixin, PICONode):  # pylint: disable=too-many-ancestors
    pass


class TestEPGLoadNode(TestNodeMixin, LoadNodeMixin, EPGNode):  # pylint: disable=too-many-ancestors
    pass


class TestVEPGLoadNode(TestNodeMixin, LoadNodeMixin, VEPGNode):  # pylint: disable=too-many-ancestors
    pass


class TestRNCLoadNode(TestNodeMixin, LoadNodeMixin, RNCNode):  # pylint: disable=too-many-ancestors
    pass


class TestSAPCLoadNode(TestNodeMixin, LoadNodeMixin, SAPCNode):  # pylint: disable=too-many-ancestors
    pass


class TestRBSLoadNode(TestNodeMixin, LoadNodeMixin, RBSNode):  # pylint: disable=too-many-ancestors
    pass


NODE_CLASS_MAP = {
    'ERBS': TestERBSNode,
    'SGSN': TestSGSNNode,
    'MSRBS_V2': TestRadioNode,
    'RadioNode': TestRadioNode,
    'MGW': TestMGWNode,
    'SpitFire': TestSpitFireNode,
    'MSRBS_V1': TestPICOLoadNode,
    'EPG': TestEPGLoadNode,
    'EPG-SSR': TestEPGLoadNode,
    'VEPG': TestVEPGLoadNode,
    'RNC': TestRNCLoadNode,
    'SAPC': TestSAPCLoadNode,
    'RBS': TestRBSLoadNode,
    'BaseLoadNode': TestBaseNode

}


class TestPool(Pool):

    PERSISTENCE_KEY = 'acceptance-node-pool'

    def __init__(self, pool_type="acceptance"):
        super(TestPool, self).__init__()
        self.pool_type = pool_type

        if pool_type == "acceptance":
            if filesystem.does_file_exist('/var/enmutils/acceptance_list'):
                node_file_path = os.path.join('/var/enmutils/acceptance_list')
            else:
                node_file_path = os.path.join(
                    TESTS, 'etc', 'network_nodes', 'acceptance_list')
            self.key = "acceptance-node-pool"
        else:
            raise ValueError("Unknown pool type {0} is not supported".format(pool_type))

        log.logger.info("Populating node pool with nodes from file {0}".format(node_file_path))
        self.add(node_file_path, node_map=NODE_CLASS_MAP)

    @property
    def db(self):
        return persistence.node_pool_db()

    def _node_is_used_by(self, node, _):
        return node.test_cls is not None

    def persist(self):
        with self.mutex():
            self.db.set(self.key, self, -1)

    def allocate_nodes(self, test_cls):
        """
        Given the test_cls, adds the nodes to the test_cls, raising error if it can't

        :param test_cls: Instance object which may be a test class or instance of test.UnavailableNodes
        :type test_cls: object

        :return: List of available nodes
        :rtype: list
        """
        with self.mutex():
            available_nodes = self.get_available_nodes(test_cls)
            for node in available_nodes:
                node.add_test(test_cls)
        return available_nodes

    def return_nodes(self, nodes):
        with self.mutex():
            for node in nodes:
                node.remove_test()

    @contextmanager
    def mutex(self):
        with mutexer.mutex('test-node-pool-operation', persisted=True):
            yield
