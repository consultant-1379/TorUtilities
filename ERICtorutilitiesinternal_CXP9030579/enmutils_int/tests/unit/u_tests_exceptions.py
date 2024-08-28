import unittest2
from mock import Mock

from enmutils.lib.exceptions import (ScriptEngineResponseValidationError, FailedNetsimOperation,
                                     MoBatchCommandReturnedError, ShellCommandReturnedNonZero,
                                     NoOuputFromScriptEngineResponseError, JobExecutionError, JobValidationError,
                                     ProfileAlreadyRunning, DependencyException, InvalidSoftwarePackage,
                                     NetworkElementMigrationException, InvalidOpenapiFormat, SyncException,
                                     EnmUserRoleMissingException, NoRemainingNetworkElementsException)
from testslib import unit_test_utils


class FailedNetsimOperationUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.nodes = Mock()
        self.command = Mock()

        self.job = FailedNetsimOperation()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_failed_netsim_operation__success(self):
        FailedNetsimOperation()


class ExceptionsUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.response = Mock()
        self.msg = Mock()

        self.job = JobValidationError(msg=self.msg, response=self.response)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_job_validation_error__success(self):
        JobValidationError(msg=self.msg, response=self.response)

    def test_job_execution_error__success(self):
        JobExecutionError(msg=self.msg, response=self.response)

    def test_no_output_from_script_engine_response_error__success(self):
        NoOuputFromScriptEngineResponseError(msg=self.msg, response=self.response)

    def test_shell_command_returned_non_zero__success(self):
        ShellCommandReturnedNonZero(msg=self.msg, response=self.response)

    def test_mo_batch_command_returned_error__success(self):
        MoBatchCommandReturnedError(msg=self.msg, response=self.response)

    def test_script_engine_response_validation_error__success(self):
        ScriptEngineResponseValidationError(msg=self.msg, response=self.response)


class ProfileAlreadyRunningUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.host = Mock()
        self.msg = Mock()
        self.pid = Mock()

        self.job = ProfileAlreadyRunning(msg=self.msg, pid=self.pid, host=self.host)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_profile_already_running__success(self):
        ProfileAlreadyRunning(msg=self.msg, pid=self.pid, host=self.host)


class DependencyExceptionUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.host = Mock()
        self.msg = Mock()
        self.error = Mock()
        self.command = Mock()

        self.job = DependencyException(error=self.error, host=self.host, command=self.command)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_dependency_exception__success(self):
        DependencyException(error=self.error, host=self.host, command=self.command)

    def test_invalid_software_package__success(self):
        InvalidSoftwarePackage(error=self.error, host=self.host, command=self.command)

    def test_network_element_migration_exception__success(self):
        NetworkElementMigrationException(error=self.error, host=self.host)

    def test_sync_exception__success(self):
        SyncException(error=self.error, host=self.host)

    def test_enm_user_role_missing_exception__success(self):
        EnmUserRoleMissingException(error=self.error, host=self.host)

    def test_no_remaining_network_elements_exception__success(self):
        NoRemainingNetworkElementsException(error=self.error, host=self.host)


class InvalidOpenapiFormatUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.msg = Mock()
        self.service_name = Mock()

        self.job = InvalidOpenapiFormat(message=self.msg, service_name=self.service_name)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_invalid_open_api_format__success(self):
        InvalidOpenapiFormat(message=self.msg, service_name=self.service_name)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
