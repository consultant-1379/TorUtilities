#!/usr/bin/env python
import unittest2

from mock import patch, Mock
from enmutils_int.lib.configuration_template import ConfigurationTemplate

from testslib import unit_test_utils


class ConfigurationTemplateUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.template = ConfigurationTemplate(self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.configuration_template.json.dumps")
    @patch("enmutils_int.lib.configuration_template.json.loads")
    def test_create(self, mock_loads, _):
        self.template.create(name="test")
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_loads.called)

    @patch("enmutils_int.lib.configuration_template.shell.run_local_cmd")
    @patch("__builtin__.open")
    @patch("enmutils_int.lib.configuration_template.log")
    def test_export(self, mock_log, *_):
        self.template.export_template(template_id="1")
        self.assertTrue(self.user.get.called)
        self.assertTrue(mock_log.logger.info.called)

    @patch("enmutils_int.lib.configuration_template.log")
    def test_delete(self, mock_log):
        self.template.delete(template_id="1")
        self.assertTrue(self.user.delete_request.called)
        self.assertTrue(mock_log.logger.info.called)

    @patch("enmutils_int.lib.configuration_template.json.loads")
    @patch("__builtin__.open")
    @patch("enmutils_int.lib.configuration_template.log")
    def test_import(self, mock_log, *_):
        self.template.import_template(file_name="1.zip")
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.logger.info.called)

    @patch("enmutils_int.lib.configuration_template.log")
    def test_teardown(self, mock_log):
        self.template.template_id = "1"
        self.template._teardown()
        self.assertTrue(self.user.delete_request.called)
        self.assertTrue(mock_log.logger.info.called)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
