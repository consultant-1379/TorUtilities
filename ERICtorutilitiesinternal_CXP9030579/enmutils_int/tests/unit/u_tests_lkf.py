import datetime
import unittest2
from mock import Mock, patch, call
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib.exceptions import TimeOutError, EnmApplicationError, NetsimError
from enmutils_int.lib.lkf import LkfJob, INSTANTANEOUS_LICENSING_CMD
from enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow import Lkf01Flow
from testslib import unit_test_utils


class LkfJobUnitTests(ParameterizedTestCase):

    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()
        node = Mock(primary_type='RadioNode', node_id='testNode', ne_type='EnodeB')
        self.nodes = [node]
        current_time = "2020-12-11 00:00:00"
        self.job = LkfJob(self.user, self.nodes, job_type="LICENSE_REQUEST", name="CapacityExpansionLicenseJob",
                          current_time=current_time)
        self.profile = Lkf01Flow()
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.lkf.sleep', return_value=0)
    @patch('enmutils_int.lib.lkf.log.logger.debug')
    @patch('enmutils_int.lib.lkf.datetime')
    @patch('enmutils_int.lib.lkf.ShmJob.get_lkf_job')
    def test_check_lkf_job_status__success(self, mock_lkf_job, mock_datetime, mock_debug_log, _):
        time_now = datetime.datetime(2020, 12, 28, 9, 0, 0)
        expiry_time = datetime.datetime(2020, 12, 28, 9, 45, 0)
        mock_datetime.datetime.now.side_effect = [time_now, time_now]
        mock_datetime.timedelta.return_value = expiry_time - time_now
        mock_lkf_job.return_value = [{"status": "COMPLETED", "jobName": "LkfJob"}]
        self.job.check_lkf_job_status()
        self.assertTrue(mock_lkf_job.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.lkf.sleep', return_value=0)
    @patch('enmutils_int.lib.lkf.log.logger.debug')
    @patch('enmutils_int.lib.lkf.datetime')
    @patch('enmutils_int.lib.lkf.ShmJob.get_lkf_job')
    def test_check_lkf_job_status__raises_timeout_error(self, mock_lkf_job, mock_datetime, mock_debug_log, *_):
        time_now = datetime.datetime(2020, 12, 28, 9, 0, 0)
        expiry_time = datetime.datetime(2020, 12, 28, 9, 45, 0)
        mock_datetime.datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_datetime.timedelta.return_value = expiry_time - time_now
        mock_lkf_job.return_value = [{"status": "SLEEPING", "jobName": "CapacityExpansionLicenseJob_2019_12"},
                                     {"status": "RUNNING", "jobName": "CapacityExpansionLicenseJob_2020_12"}]
        self.assertRaises(TimeOutError, self.job.check_lkf_job_status)
        self.assertTrue(mock_lkf_job.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.lkf.sleep', return_value=0)
    @patch('enmutils_int.lib.lkf.log.logger.debug')
    @patch('enmutils_int.lib.lkf.datetime')
    @patch('enmutils_int.lib.lkf.ShmJob.get_lkf_job')
    def test_check_lkf_job_status__raises_enmapplication_error(self, mock_lkf_job, mock_datetime, mock_debug_log, *_):
        time_now = datetime.datetime(2020, 12, 28, 9, 0, 0)
        expiry_time = datetime.datetime(2020, 12, 28, 9, 45, 0)
        mock_datetime.datetime.now.side_effect = [time_now, time_now]
        mock_datetime.timedelta.return_value = expiry_time - time_now
        mock_lkf_job.return_value = [{"status": "COMPLETED", "jobName": "CapacityExpansionLicenseJob_2019_12"},
                                     {"status": "SYSTEM_CANCELLED", "jobName": "CapacityExpansionLicenseJob_2020_12"}]
        self.assertRaises(EnmApplicationError, self.job.check_lkf_job_status)
        self.assertTrue(mock_lkf_job.called)
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch('enmutils_int.lib.lkf.log.logger.debug')
    @patch('enmutils_int.lib.lkf.update_pib_parameter_on_enm')
    def test_update_pib_parameters__success(self, mock_update_pib, _):
        sas_ip = Mock()
        self.job.update_pib_parameters(sas_ip)
        self.assertEqual(mock_update_pib.call_count, 12)

    @patch('enmutils_int.lib.lkf.SimulationCommand')
    def test_construct_commands_on_nodes__success(self, mock_sim_cmd):
        netsim_operation_obj = [("ieatnetsimv110-01", 'NR19-Q4-V1x40-gNodeBRadio-NRAT-NR01', self.nodes)]
        cmd = "sequenceNumber=1"
        sim_list = []
        il_sim_list = []
        self.job.construct_commands_on_nodes(netsim_operation_obj, cmd, sim_list, il_sim_list)
        self.assertEqual(mock_sim_cmd.call_count, len(self.nodes) + 1)
        self.assertTrue(mock_sim_cmd.mock_calls == [call(netsim_operation_obj[0][0], netsim_operation_obj[0][1],
                                                         netsim_operation_obj[0][2], INSTANTANEOUS_LICENSING_CMD),
                                                    call(netsim_operation_obj[0][0], netsim_operation_obj[0][1],
                                                         [self.nodes[0]], cmd)])

    @patch('enmutils_int.lib.lkf.LkfJob.construct_commands_on_nodes')
    @patch('enmutils_int.lib.lkf.NetsimOperation')
    def test_execute_il_netsim_cmd_on_nodes__success(self, mock_netsim_operation, mock_construct_cmd):
        netsim_operation_obj = Mock()
        netsim_operation_obj.node_groups = {self.nodes[0].ne_type: [("ieatnetsimv110-01",
                                                                     'NR19-Q4-V1x40-gNodeBRadio-NRAT-NR01',
                                                                     self.nodes)]}
        mock_netsim_operation.return_value = netsim_operation_obj
        simulation_cmd_obj = [Mock()]
        il_simulation_cmd_obj = [Mock()]
        mock_construct_cmd.return_value = simulation_cmd_obj, il_simulation_cmd_obj
        self.job.execute_il_netsim_cmd_on_nodes(self.nodes)
        self.assertTrue(mock_construct_cmd.called)
        self.assertEqual(mock_netsim_operation.return_value.execute.call_count, 2)

    @patch('enmutils_int.lib.lkf.LkfJob.construct_commands_on_nodes')
    @patch('enmutils_int.lib.lkf.NetsimOperation')
    def test_execute_il_netsim_cmd_on_nodes__raises_netsim_error(self, mock_netsim_operation, mock_construct_cmd):
        netsim_operation_obj = Mock()
        netsim_operation_obj.node_groups = {self.nodes[0].ne_type: [("ieatnetsimv110-01",
                                                                     'NR19-Q4-V1x40-gNodeBRadio-NRAT-NR01',
                                                                     self.nodes)]}
        mock_netsim_operation.return_value = netsim_operation_obj
        simulation_cmd_obj = [Mock()]
        il_simulation_cmd_obj = [Mock()]
        mock_construct_cmd.return_value = simulation_cmd_obj, il_simulation_cmd_obj
        mock_netsim_operation.return_value.execute.side_effect = [NetsimError, NetsimError]
        self.assertRaises(NetsimError, self.job.execute_il_netsim_cmd_on_nodes, self.nodes)


if __name__ == '__main__':
    unittest2.main()
