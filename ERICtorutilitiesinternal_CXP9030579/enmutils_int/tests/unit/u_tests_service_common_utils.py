#!/usr/bin/env python
import unittest2
from parameterizedtestcase import ParameterizedTestCase

from enmutils_int.lib.services import service_common_utils
from testslib import unit_test_utils
from mock import patch, Mock


JOB_SCHEDULED_STR = "Background scheduled job created."


class ServiceCommonUtilsUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @ParameterizedTestCase.parameterize(
        ("args", "expected"),
        [
            ((True, "Operation successful.", 200, "text/html"),
             ('{"message": "Operation successful.", "success": true}', 200, {'ContentType': 'text/html'})),
            ((None, "Operation successful.", 200, "text/html"),
             ('{"message": "Operation successful.", "success": true}', 200, {'ContentType': 'text/html'})),
            ((None, None, 200, "text/html"),
             ('{"message": "", "success": true}', 200, {'ContentType': 'text/html'})),
            ((None, None, None, "text/html"),
             ('{"message": "", "success": true}', 200, {'ContentType': 'text/html'})),
            ((None, None, None, None),
             ('{"message": "", "success": true}', 200, {'ContentType': 'application/json'})),
            ((False, "", 500, None),
             ('{"message": "", "success": false}', 500, {'ContentType': 'application/json'}))
        ]
    )
    def test_get_json_response__response(self, args, expected):
        success, message, rc, content_type = args
        self.assertEqual(service_common_utils.get_json_response(success=success, message=message, rc=rc,
                                                                content_type=content_type), expected)

    @patch('enmutils_int.lib.services.service_common_utils.traceback')
    @patch('enmutils_int.lib.services.service_common_utils.abort')
    def test_abort_with_message__is_successful_for_default_http_status_code(self, mock_abort, _):
        error = "some error"
        exception = Exception(error)
        message = "Could not do something"
        logger = Mock()
        service_common_utils.abort_with_message(message, logger, "nodemanager", "dir", exception)
        abort_message = ("{0} - error encountered :: {1} - see nodemanager service log for more details "
                         "(dir/nodemanager.log)".format(message, error))
        mock_abort.assert_called_with(500, abort_message)

    @patch('enmutils_int.lib.services.service_common_utils.traceback')
    @patch('enmutils_int.lib.services.service_common_utils.abort')
    def test_abort_with_message__is_successful_for_non_default_http_status_code(self, mock_abort, _):
        error = "some error"
        exception = Exception(error)
        message = "Could not do something"
        logger = Mock()
        service_common_utils.abort_with_message(message, logger, "nodemanager", "dir", exception, 400)
        abort_message = ("{0} - error encountered :: {1} - see nodemanager service log for more details "
                         "(dir/nodemanager.log)".format(message, error))
        mock_abort.assert_called_with(400, abort_message)

    @patch('enmutils_int.lib.services.service_common_utils.get_time_zone', return_value='Europe/Dublin')
    @patch('enmutils_int.lib.services.service_common_utils.BackgroundScheduler.__init__', return_value=None)
    @patch('enmutils_int.lib.services.service_common_utils.BackgroundScheduler.add_job')
    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.service_common_utils.BackgroundScheduler.start')
    def test_create_and_start_background_scheduled_job__starts_job(self, mock_start, mock_logger, mock_add_job, *_):
        mock_func = Mock()
        service_common_utils.create_and_start_background_scheduled_job(mock_func, 1, "id", mock_logger)
        self.assertEqual(1, mock_start.call_count)
        mock_logger.info.assert_called_with(JOB_SCHEDULED_STR)
        mock_add_job.assert_called_with(mock_func, 'interval', minutes=1, id="id")

    @patch('enmutils_int.lib.services.service_common_utils.get_time_zone', return_value='Europe/Dublin')
    @patch('enmutils_int.lib.services.service_common_utils.BackgroundScheduler.__init__', return_value=None)
    @patch('enmutils_int.lib.services.service_common_utils.BackgroundScheduler.add_job')
    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.service_common_utils.BackgroundScheduler.start')
    def test_create_and_start_once_off_background_scheduled_job__starts_job(
            self, mock_start, mock_logger, mock_add, *_):
        mock_func = Mock()
        service_common_utils.create_and_start_once_off_background_scheduled_job(mock_func, "id", mock_logger)
        self.assertEqual(1, mock_start.call_count)
        self.assertEqual(2, mock_add.call_count)
        mock_logger.info.assert_called_with(JOB_SCHEDULED_STR)

    @patch('enmutils.lib.log.logger')
    def test_shutdown_scheduled_job__calls_shutdown(self, mock_logger):
        scheduler = Mock()
        service_common_utils.shutdown_scheduled_job(scheduler, mock_logger)
        self.assertEqual(1, scheduler.shutdown.call_count)
        mock_logger.info.assert_called_with('Once off background scheduled job shutdown completed.')

    @patch('enmutils_int.lib.services.service_common_utils.commands.getstatusoutput', return_value=(0, 'ZONE="UTC"'))
    def test_get_time_zone__returns_system_time_zone(self, _):
        self.assertEqual('UTC', service_common_utils.get_time_zone())

    @patch('enmutils_int.lib.services.service_common_utils.commands.getstatusoutput', return_value=(1, 'ZONE="UTC"'))
    def test_get_time_zone__uses_europe_dublin(self, _):
        self.assertEqual('Europe/Dublin', service_common_utils.get_time_zone())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
