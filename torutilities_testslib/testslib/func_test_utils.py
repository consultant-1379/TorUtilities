#!/usr/bin/env python
import os
import pkgutil
from functools import wraps

import nose

from enmutils.lib import init, config, log, exception, persistence, cache, http, enm_user_2
from enmutils.lib.enm_node_management import CmManagement
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.node_pool_mgr import filter_unsynchronised_nodes
from testslib import test_utils

log_counter = 1

INTERNAL = pkgutil.get_loader('enmutils_int').filename


def setup(cls):
    """
    Sets up a functional test execution

    :type cls: unittest2.TestCase
    :param cls: Test class to be run

    :raises BaseException: raised if setup fails
    """

    global log_counter
    log_counter = 1

    try:
        init.global_init("func-test", "int", cls._testMethodName, simplified_logging=True)

        # Set environment variable to 'testing' so config picks up the test database index when calling default db
        log.logger.debug("func_test_utils setup - Setting ENVIRON=testing")
        config.set_prop("ENVIRON", "testing")

        # NOTE: The persistence object gets created here as session mgr is the first to persist something
        log.logger.debug("Establishing security admin session for test case {0}".format(cls._testMethodName))
        enm_user_2.get_or_create_admin_user()
        test_utils.setup()

        if hasattr(cls, "fixture"):
            cls.fixture.setup()

        log.logger.debug("Test setup has finished; executing test...")

    except BaseException as e:
        exception.process_exception("Exception raised during test setup: {0}".format(e.message))
        tear_down(cls)
        raise


def tear_down(cls):
    """
    Tears down after a functional test execution

    :type cls: unittest2.TestCase
    :param cls: Test class to be cleaned after test method execution has finished
    """

    log.logger.debug("Test has finished; tearing down...")

    test_name = cls._testMethodName
    log.shutdown_handlers(test_name)

    if test_name is not None and hasattr(nose, 'allure'):
        log_file_path = os.path.join(config.get_log_dir(), "test", "{0}.log".format(test_name))
        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as file_handle:
                nose.allure.attach("Test Log", file_handle.read())


def module_tear_down(cls):
    """
    Tears down after all functional tests have been executed in the specified test class

    :type cls: unittest2.TestCase
    :param cls: Test class to be cleaned up

    :raises BaseException: raised if tear down fails
    :raises RuntimeError: raised if fixture tear down fails
    """

    try:
        tear_down_result = True
        log_name = "{0}TearDown".format(cls.__name__)
        init.global_init("func-test", "int", log_name, simplified_logging=True)

        if hasattr(cls, "fixture"):
            tear_down_result = cls.fixture.teardown()

        cache.clear()
        if not persistence.default_db().clear_all():
            log.logger.info("DB not cleared")
        persistence.mutex_db().clear()
        log.shutdown_handlers(log_name)

        if hasattr(nose, 'allure'):
            log_file_path = os.path.join(config.get_log_dir(), "test", "{0}.log".format(log_name))
            if os.path.exists(log_file_path):
                with open(log_file_path, "r") as file_handle:
                    nose.allure.attach("Teardown Log", file_handle.read())

        if not tear_down_result:
            raise RuntimeError("Error occurred in teardown steps. Check logs for more details.")

    except BaseException as e:
        exception.process_exception("Exception raised during teardown of test module {0}: {1}".format(cls.__name__,
                                                                                                      e.args[0]))
        raise


def cm_sync_nodes(nodes):
    """
     Cm sync the node

    :param nodes: Node to enable supervision by ENM
    :type nodes: `enm_node.Node`
    """
    unsynced = list(set(nodes).difference(filter_unsynchronised_nodes(nodes, ne_type=nodes[0].primary_type)))
    if unsynced:
        log.logger.info("\nUnsynced nodes\t{0}\n".format(", ".join([node.node_id for node in unsynced])))
        cm_sync = CmManagement.get_management_obj(nodes=unsynced, user=get_workload_admin_user())
        try:
            cm_sync.synchronize()
        except Exception as e:
            log.logger.debug(str(e))
    log.logger.info("\nNo unsynced nodes.\n")


def func_dec(feature=None, story=None, issue=None, test_case_id=None):
    """
    Adds allure annotations to acceptance tests

    :type feature: str
    :param feature: Feature name for allure plugin
    :type story: str
    :param story: Story name for allure plugin
    :type issue: str
    :param issue: Issue for allure plugin
    :type test_case_id: string
    :param test_case_id: Taf TM test case Id

    :rtype: func
    :returns: Returns decorated function with allure annotations
    """

    def wrapper(func):
        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        if hasattr(nose, "allure"):
            wrapped = wraps(func)(wrapped)
            if test_case_id:
                wrapped = _send_get_request_taf_tm(wrapped, test_case_id)
            if issue:
                wrapped = nose.allure.issue(issue)(wrapped)
            if feature and story:
                wrapped = nose.allure.feature(feature)(wrapped)
                wrapped = nose.allure.story(story)(wrapped)

        return wrapped
    return wrapper


def _send_get_request_taf_tm(wrapped, test_case_id):
    taf_tm_fetch = "http://taftm.lmera.ericsson.se/tm-server/api/test-cases/{test_case_id}?version&view=detailed"
    taf_tm_view_tc = "http://taftm.lmera.ericsson.se/#tm/viewTC/{test_case_id}"
    taf_tm_create_new_tc = "http://taftm.lmera.ericsson.se/#tm/createTC/{test_case_id}"

    url = taf_tm_fetch.replace("{test_case_id}", test_case_id)
    response = http.get(url, verbose=False)

    if response.rc == 200:
        json_obj = response.json()
        wrapped = nose.allure.issue(taf_tm_view_tc.replace("{test_case_id}", test_case_id))(wrapped)
        wrapped = nose.allure.feature(json_obj['componentTitle'])(wrapped)
        wrapped = nose.allure.story(json_obj['title'])(wrapped)
    elif response.rc == 404:
        wrapped = nose.allure.issue(taf_tm_create_new_tc.replace("{test_case_id}", test_case_id))(wrapped)
        wrapped = nose.allure.feature("Test case not found in TAF TM.")(wrapped)
        wrapped = nose.allure.story("Test case not found in TAF TM. Use link provided to create test with current ID.")(wrapped)

    return wrapped


def setup_verify(users=0, available_nodes=0, managed_nodes=0, login=False, **kwargs):
    """
    Decorator function to check if test setup requirements are met before attempting to execute a test, if not a
    RuntimeError is raised and the test is skipped

    :type users: int
    :param users: The number of users required by a test
    :type available_nodes: int
    :param available_nodes: The number of nodes required to be available for the test
    :type managed_nodes: int
    :param managed_nodes: The number of nodes required to be managed/synced for the test
    :type login: boolean
    :param login: Indicates whether login is a prereq for running this test
    :type kwargs: dict
    :param kwargs: Keyword dictionary

    :raises RuntimeError: raised if the verify checks fail
    :returns: wrapper function
    :rtype: obj
    """

    def wrapper(func):

        def wrapped(cls, *args, **_):

            if login and not cls.fixture.ui_setup_done:
                raise RuntimeError("SetupFail - Login was not successful unable to run test")
            if users and len(cls.fixture.users) < users:
                raise RuntimeError("SetupFail - Only {0} users have been created out of the {1} users required to run this test".format(len(cls.fixture.users), users))
            if available_nodes and len(cls.fixture.nodes) < available_nodes:
                raise RuntimeError("SetupFail - Only {0} nodes are available out of the {1} nodes required to run this test".format(len(cls.fixture.nodes), available_nodes))
            if managed_nodes and len(cls.fixture.managed_nodes) < managed_nodes:
                raise RuntimeError("SetupFail - Only {0} nodes have been managed out of the {1} nodes required to run this test".format(len(cls.fixture.managed_nodes), managed_nodes))
            if kwargs:
                for attr, value in kwargs.items():
                    if not hasattr(cls.fixture, attr) or getattr(cls.fixture, attr) != value:
                        raise RuntimeError("SetupFail - Value for test fixture attribute '{0}' was '{1}'. The expected value was '{2}'".format(attr, value, getattr(cls.fixture, attr)))
            return func(cls, *args, **_)

        if hasattr(nose, "allure"):
            wrapped = wraps(func)(wrapped)

        return wrapped
    return wrapper
