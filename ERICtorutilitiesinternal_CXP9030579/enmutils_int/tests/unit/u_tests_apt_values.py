"""  Unit tests for apt_values.py """

import unittest2

from enmutils_int.lib.nrm_default_configurations import apt_values
from enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow import Fm0506
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_utilities import EXISTING_PACKAGES


class AptValuesUnitTests(unittest2.TestCase):

    MSG = "Data mismatch between apt_values and actual values. Please update!"

    def test_shm_data__is_as_expected(self):
        self.assertEqual(apt_values.SHM_DATA["LOCAL_PATH"], ShmFlow.LOCAL_PATH, msg=self.MSG)
        self.assertEqual(apt_values.SHM_DATA["EXISTING_PACKAGES"], EXISTING_PACKAGES, msg=self.MSG)

    def test_fm_data__is_as_expected(self):
        self.assertEqual(apt_values.FM_DATA["DELAYED_ACKNOWLEDGE_HRS"], Fm0506.DELAYED_ACKNOWLEDGE_HRS, msg=self.MSG)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
