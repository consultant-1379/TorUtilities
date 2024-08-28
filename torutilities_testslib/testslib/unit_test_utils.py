#!/usr/bin/env python
import os

import mock
from mock import Mock, patch

from enmutils.lib import config, init, log, persistence
from enmutils_int.lib.load_node import BaseLoadNode
from enmutils_int.lib.profile import Profile

import testslib as tests
from testslib import test_utils

ENMUTILS_TESTS_PATH = os.path.dirname(tests.__file__)
NON_PROFILES = ["stopped_nodes", "enm_checks"]

__config_dict = {}
__mock_config_file = os.path.join(ENMUTILS_TESTS_PATH, 'etc', 'mock_values.conf')


def setup():
    """ Called from the setup of each unit test case """
    # To prevent each unit test from pulling in the config from all files (I/O load), push a copy of the dict into the config module
    _push_config_dict()

    init.global_init("unit-test", "int", "unit-test")

    # Keep a local copy of the config dict so that we can push it into config for future unit tests
    if len(__config_dict) == 0:
        build_config_dict(__mock_config_file)

    # Setup mocks
    _setup_mocks()
    test_utils.setup()

    # Monkey patch mutex_push as FakeRedis does not have an eval function. Therefore mutexes are not deleted and simply
    # expire after 30 seconds. Therefore we need to delete them instead
    def mutex_push_delete(self, mutex):
        self.connection.delete(mutex[0])
    persistence.Persistence.mutex_push = mutex_push_delete


def tear_down():
    test_utils.tear_down()
    persistence.clear_all()


def _push_config_dict():
    config.set_config_dict(__config_dict)


def build_config_dict(file=None):  # pylint: disable=redefined-builtin
    global __config_dict

    if file is not None:
        config.load_config_from_file(file)

    __config_dict = config.get_config_dict()


def _setup_mocks():
    # Mock logging
    log.logger.info = mock.Mock(return_value=None)
    log.logger.debug = mock.Mock(return_value=None)
    log.logger.warn = mock.Mock(return_value=None)
    log.logger.error = mock.Mock(return_value=None)
    log.logger.syslog = mock.Mock(return_value=None)
    log.logger.rest = mock.Mock(return_value=None)
    log.logger.exception = mock.Mock(return_value=None)
    log.logger.log_cmd = mock.Mock(return_value=None)
    log.logger.workload = mock.Mock(return_value=None)
    persistence.publish = mock.Mock(return_value=None)
    persistence.subscribe = mock.Mock(return_value=None)


def setup_test_node_objects(range_end=100, primary_type="ERBS", node_version="16A", host_name="netsimlin537"):
    nodes = []
    range_end += 1

    for counter in range(1, range_end):
        if counter <= 9:
            name = "netsimlin537_{0}000{1}".format(primary_type, counter)
        elif counter <= 99:
            name = "netsimlin537_{0}00{1}".format(primary_type, counter)
        else:
            name = "netsimlin537_{0}0{1}".format(primary_type, counter)

        node_ip = "10.243.0.{0}".format(counter)
        mim_version = "4.1.189"
        netsim = host_name
        simulation = "LTE07"
        model_identity = "1094-174-285"
        node = BaseLoadNode(
            name, node_ip, mim_version, model_identity, security_state='ON', normal_user='test',
            primary_type=primary_type, normal_password='test', secure_user='test', secure_password='test',
            subnetwork='subnetwork', netsim=netsim, simulation=simulation, user=Mock(),
            node_version=node_version)

        nodes.append(node)
    return nodes


def add_nodes_to_pool(pool, num_nodes, primary_type="ERBS", node_version="16A"):
    with patch('enmutils_int.lib.node_pool_mgr.Pool.validate_nodes_against_enm') as mock_validate:
        with patch('enmutils_int.lib.node_pool_mgr.Pool._load_nodes_from_file') as mock_add_file:
            with patch('enmutils.lib.enm_node_management.CmManagement.get_status') as mock_sync_state:
                with patch('enmutils_int.lib.node_pool_mgr.Pool.nodes_to_be_allocated') as mock_lte:
                    with patch('testslib.unit_test_utils.BaseLoadNode.compare_and_update_persisted_node') as _:
                        nodes = setup_test_node_objects(num_nodes, primary_type=primary_type,
                                                        node_version=node_version)
                        mock_add_file.return_value = (nodes, [])
                        mock_validate.return_value = []
                        mock_lte.side_effect = [node for node in nodes]
                        mock_sync_state.return_value = {node.node_id: "SYNCHRONIZED" for node in nodes}
                        return pool.add('', 1, num_nodes)


class TestProfile(Profile):
    def __init__(self, **kwargs):

        for key, value in kwargs.iteritems():
            setattr(self, key.upper(), value)

        super(TestProfile, self).__init__()

    def run(self):
        pass


def get_profile(**kwargs):
    """
    Gets an instance of a profile

    :param kwargs: Arbitrary keyword arguments
    :return: An instance of a profile
    :rtype: `profile.Profile`

    """
    return TestProfile(**kwargs)


def get_nodes(num_nodes):
    """
    Gets an instance of a BaseLoadNode

    :param num_nodes: the number of node instances required
    :type num_nodes: int
    :return: load_node.BaseLoadNode
    :rtype: list
    """
    nodes = []
    for i in range(0, num_nodes):
        nodes.append(BaseLoadNode(
            "netsimlin704_LTE{0}".format(i + 1), "255.255.255.255", "5.1.120", "1094-174-285", security_state='ON',
            normal_user='test', normal_password='test', secure_user='test', secure_password='test',
            subnetwork='subnetwork', netsim="netsimlin704", simulation="LTE01", primary_type="ERBS"))

    return nodes


def generate_configurable_ip(start=1, end=8, step=2, ipversion=4):
    """
    Configurable ipv4 string, default return is "1.3.5.7"

    :param start: Start value of the ip
    :type start: int
    :param end: Last value of the ip
    :type end: int
    :param step: Step value between start and end
    :type step: int
    :param ipversion: Version of IP i.e., IPV4 or IPV6
    :type ipversion: int
    :return: String ip
    :rtype: str
    """
    min_end = start + (3 * step) + 1
    if end < min_end:
        end = min_end
    return (".".join([str(_) for _ in xrange(start, end, step)][:4]) if ipversion == 4
            else ":".join([str(_) * 4 for _ in xrange(start, end, step)][:4] * 2))
