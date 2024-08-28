#!/usr/bin/env python
import pkgutil

import os
import unipath
import unittest2
from testslib import unit_test_utils
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename


class ServiceUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_validate_yaml_filess__success(self):
        _internal_data = pkgutil.get_loader('enmutils_int')
        _file_path = unipath.Path(_internal_data.filename)
        yml_files = os.listdir('/{0}/{1}/{2}'.format(_file_path, 'etc', 'openapi'))
        for yml_file in yml_files:
            file_name = get_internal_file_path_for_import('etc', 'openapi', yml_file)
            spec_dict, spec_url = read_from_filename(file_name)
            validate_spec(spec_dict, spec_url)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
