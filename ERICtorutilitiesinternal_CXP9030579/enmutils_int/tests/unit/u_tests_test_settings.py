import unittest2

from enmutils_int.lib import test_settings
from testslib import unit_test_utils


class UpdateNexusUrlCommand(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_nexus_url_command(self):
        self.assertEqual(test_settings.UPDATE_NEXUS_URL_COMMAND, ("echo 'Update NEXUS URLs'; "
                                                                  "for FILE in $(egrep -r arm101-eiffel004.lmera "
                                                                  "/opt/ericsson/enmutils/ 2>/dev/null | "
                                                                  "egrep .py: | egrep -v test | awk -F':' '{print "
                                                                  "$1}'); do /bin/cp -p $FILE $FILE.orig; "
                                                                  "sed -i 's/arm101-eiffel004.lmera/arm1s11-eiffel004"
                                                                  ".eiffel.gic/' $FILE; done"))


if __name__ == '__main__':
    unittest2.main(verbosity=2)
