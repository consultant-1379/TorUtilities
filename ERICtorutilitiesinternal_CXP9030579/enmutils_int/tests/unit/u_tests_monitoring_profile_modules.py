#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (netview_01, netview_02, netview_setup, ftpes_01, lkf_01, nvs_01, nvs_02, geo_r_01,
                                       parmgt_01, parmgt_02, parmgt_03, parmgt_04, esm_01, plm_01, plm_02, logviewer_01, top_01,
                                       fmx_01, fmx_05, asu_01, doc_01, npa_01)


class MonitoringProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.Doc01Flow.execute_flow")
    def test_doc_01_profile_execute_flow__successful(self, mock_flow):
        doc_01.DOC_01().run()
        self.assertEqual(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.execute_flow")
    def test_asu_01_profile_execute_flow__successful(self, mock_execute_flow):
        asu_01.ASU_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.execute_flow")
    def test_npa_01_profile_execute_flow__successful(self, mock_flow):
        npa_01.NPA_01().run()
        self.assertEqual(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.execute_flow")
    def test_geo_r_01_profile_execute_flow__success(self, mock_flow):
        geo_r_01.GEO_R_01().run()
        self.assertEqual(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.execute_flow")
    def test_esm_profile_esm_01_execute_flow__successful(self, mock_flow):
        esm_01.ESM_01().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.execute_flow")
    def test_ftpes_profile_frpes_01_execute_flow__successful(self, mock_flow):
        ftpes_01.FTPES_01().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.execute_flow')
    def test_lf_profile_lkf_01_execute_flow__successful(self, mock_flow):
        lkf_01.LKF_01().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.execute_flow")
    def test_netview_profile_netview_01_execute_flow__successful(self, mock_flow):
        netview_01.NETVIEW_01().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.execute_flow")
    def test_netview_profile_netview_02_execute_flow__successful(self, mock_flow):
        netview_02.NETVIEW_02().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.execute_flow")
    def test_netview_profile_netview_setup_execute_flow__successful(self, mock_flow):
        netview_setup.NETVIEW_SETUP().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs01Flow.execute_flow')
    def test_nvs_profile_nvs_01_execute_flow_successful(self, mock_flow):
        nvs_01.NVS_01().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.nvs_flows.nvs_flows.Nvs02Flow.execute_flow')
    def test_nvs_profile_nvs_02_execute_flow_successful(self, mock_flow):
        nvs_02.NVS_02().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow.ParMgt01Flow.execute_flow")
    def test_parmgt_profile_parmgt_01_execute_flow__successful(self, mock_flow):
        parmgt_01.PARMGT_01().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow.ParMgt02Flow.execute_flow")
    def test_parmgt_profile_parmgt_02_execute_flow__successful(self, mock_flow):
        parmgt_02.PARMGT_02().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow.ParMgt03Flow.execute_flow")
    def test_parmgt_profile_parmgt_03_execute_flow__successful(self, mock_flow):
        parmgt_03.PARMGT_03().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow.ParMgt04Flow.execute_flow")
    def test_parmgt_profile_parmgt_04_execute_flow__successful(self, mock_flow):
        parmgt_04.PARMGT_04().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.execute_fmx_01_flow")
    def test_run_in_fmx_01__is_successful(self, mock_execute_flow):
        fmx_01.FMX_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.execute_fmx_05_flow")
    def test_run_in_fmx_05__is_successful(self, mock_execute_flow):
        fmx_05.FMX_05().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow.LogViewerFlow.execute_flow")
    def test_run_in_logviewer_01__is_successful(self, mock_execute_flow):
        logviewer_01.LOGVIEWER_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.execute_flow")
    def test_run_in_plm_01__is_successful(self, mock_execute_flow):
        plm_01.PLM_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_02_flow.Plm02Flow.execute_flow")
    def test_run_in_plm_02__is_successful(self, mock_execute_flow):
        plm_02.PLM_02().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.execute_flow")
    def test_run_in_top_01__is_successful(self, mock_execute_flow):
        top_01.TOP_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
