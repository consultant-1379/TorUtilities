#!/usr/bin/env python
import unittest2

from enmutils_int.lib.netsim_operations import AVCBurst
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import setup_verify, func_dec
from enmutils.lib.exceptions import FailedNetsimOperation


class AVCBurstAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        mo_path = "ManagedElement=1,NodeManagementFunction=1,RbsConfiguration=1"
        mo_attribute = "ossCorbaNameServiceAddress"
        mo_values = ["abc.def.ghi", "jkl.mno.pqr", "stv.wxy.z"]
        self.avcburst = AVCBurst(nodes=self.fixture.nodes, burst_id="222", duration=120, burst_rate=10, mo_path=mo_path,
                                 mo_attribute=mo_attribute, mo_values=mo_values)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(available_nodes=1)
    @func_dec("AVC Burst", "Create an AVC Burst")
    def test_010_start_avc_bursts_raises_no_error_when_successfully_starting_the_burst(self):
        self.avcburst.start()

    @setup_verify(available_nodes=1)
    @func_dec("AVC Burst", "Exception expected when stating AVCBurst already started")
    def test_020_start_avc_bursts_raises_FailedNetsimOperation_error_exception(self):
        try:
            self.avcburst.start()
        except FailedNetsimOperation:
            pass
        else:
            self.fail("Failed to raise FailedNetsimOperation exception")

    @setup_verify(available_nodes=1)
    @func_dec("AVC Burst", "Stop the AVC burst")
    def test_030_stop_avc_bursts_raises_no_error_when_burst_is_running(self):
        self.avcburst.stop()

if __name__ == "__main__":
    unittest2.main(verbosity=2)
