#!/usr/bin/env python
import time
import datetime
import unittest2
from pytz import timezone
from mock import Mock
from enmutils.lib import shell
from enmutils_int.lib.pm_subscriptions import (StatisticalSubscription, CelltraceSubscription, UETraceSubscription,
                                               EBMSubscription)
from enmutils_int.lib.pm_nbi import Fls
from enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile import PmFlsNbiProfile
from enmutils_int.lib.services.deployment_info_helper_methods import build_poid_dict_from_enm_data
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec, setup_verify
from requests.exceptions import RequestException

statistical_subscription = None
cell_trace_subscription = None
uetrace_subscription = None
statistical_subscription_cbs = None
cell_trace_subscription_cbs = None
ebm_subscription_cbs = None


class PmAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["PM_Operator"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def update_poids_on_nodes(self, nodes, node_poid_data):
        nodes_with_poid_updated = []
        for node in nodes:
            node.poid = node_poid_data.get(node.node_id)
            nodes_with_poid_updated.append(node)
        return nodes_with_poid_updated

    def setUp(self):
        func_test_utils.setup(self)
        global statistical_subscription, cell_trace_subscription, uetrace_subscription
        global statistical_subscription_cbs, cell_trace_subscription_cbs, ebm_subscription_cbs
        user = self.fixture.users[0]
        node_poid_data = build_poid_dict_from_enm_data()
        nodes = self.update_poids_on_nodes(self.fixture.nodes, node_poid_data)

        if not statistical_subscription:
            statistical_subscription = StatisticalSubscription(
                "AcceptanceStatisticalSubscription", nodes=nodes, user=self.fixture.users[0])

        if not cell_trace_subscription:
            cell_trace_subscription = CelltraceSubscription(
                "AcceptanceCellTraceSubscription", nodes=nodes, user=self.fixture.users[0])

        if not uetrace_subscription:
            UE_INFO = {"type": "IMSI", "value": "27208"}  # These values should exist on SGSN nodes
            uetrace_subscription = UETraceSubscription(UE_INFO, name="AcceptanceUetraceSubscription", user=user)

        if not statistical_subscription_cbs:
            statistical_subscription_cbs = StatisticalSubscription(
                "AcceptanceStatisticalSubscriptionCBS", nodes=nodes, user=self.fixture.users[0], cbs=True)

        if not cell_trace_subscription_cbs:
            cell_trace_subscription_cbs = CelltraceSubscription(
                "AcceptanceCellTraceSubscriptionCBS", nodes=nodes, user=self.fixture.users[0], cbs=True)

        if not ebm_subscription_cbs:
            ebm_subscription_cbs = EBMSubscription(
                "AcceptanceEBMSubscriptionCBS", nodes=nodes, user=self.fixture.users[0], cbs=True)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical", "Create Statistical Subscription")
    def test_001_create_statistical_subscription_success(self):
        statistical_subscription.create()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical", "Create Statistical Subscription Error")
    def test_002_create_statistical_subscription_raises_HTTPError(self):
        self.assertRaises(RequestException, statistical_subscription.create)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical", "Activate Statistical Subscription")
    def test_003_activate_statistical_subscription_success(self):
        statistical_subscription.activate()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical", "Activate Statistical Subscription Error")
    def test_004_activate_statistical_subscription_raises_HTTPError(self):
        self.assertRaises(RequestException, statistical_subscription.activate)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical", "Deactivate Statistical Subscription")
    def test_005_deactivate_statistical_subscription_success(self):
        statistical_subscription.deactivate()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical", "Deactivate Statistical Subscription Error")
    def test_006_deactivate_statistical_subscription_raises_HTTPError(self):
        self.assertRaises(RequestException, statistical_subscription.deactivate)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical", "Update Statistical Subscription")
    def test_007_update_statistical_subscription(self):
        statistical_subscription.update(counters=2)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace", "Create Cell Trace Subscription")
    def test_008_create_cell_trace_subscription_success(self):
        cell_trace_subscription.create()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace", "Create Cell Trace Subscription Error")
    def test_009_create_cell_trace_subscription_raises_HTTPError(self):
        self.assertRaises(RequestException, cell_trace_subscription.create)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace", "Activate Cell Trace Subscription")
    def test_010_activate_cell_trace_subscription_success(self):
        cell_trace_subscription.activate()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace", "Activate Cell Trace Subscription Error")
    def test_011_activate_cell_trace_subscription_raises_HTTPError(self):
        self.assertRaises(RequestException, cell_trace_subscription.activate)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace", "Deactivate Cell Trace Subscription")
    def test_012_deactivate_cell_trace_subscription_success(self):
        cell_trace_subscription.deactivate()

    @func_dec("PMIC Cell Trace", "Deactivate Cell Trace Subscription Error")
    def test_013_deactivate_cell_trace_subscription_raises_HTTPError(self):
        self.assertRaises(RequestException, cell_trace_subscription.deactivate)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Uetrace", "Create Uetrace Subscription")
    def test_014_create_uetrace_subscription(self):
        uetrace_subscription.create()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Uetrace", "Update Uetrace Subscription")
    def test_015_update_uetrace_subscription(self):
        uetrace_subscription.update(output_mode='FILE_AND_STREAMING', stream_info={"ipAddress": "1.2.3.4"})

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical", "Clean-up all Statistical Subscriptions from ENM")
    def test_016_clean_all_statistical_subscriptions_from_ENM(self):
        StatisticalSubscription.clean_subscriptions("Statistical")

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical", "Clean-up all Subscriptions from ENM")
    def test_017_clean_all_subscriptions_from_ENM(self):
        StatisticalSubscription.clean_subscriptions(delete_all=True)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical CBS", "Create Statistical Subscription for CBS")
    def test_018_create_statistical_subscription_for_CBS_success(self):
        statistical_subscription_cbs.create()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical CBS", "Create Statistical Subscription for CBS RequestException")
    def test_019_create_statistical_subscription_for_CBS_raises_RequestError(self):
        self.assertRaises(RequestException, statistical_subscription_cbs.create)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical CBS", "Update Statistical Subscription for CBS")
    def test_020_update_statistical_subscription(self):
        statistical_subscription_cbs.update(counters=2)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace CBS", "Create Cell Trace Subscription for CBS")
    def test_021_create_cell_trace_subscription_CBS_success(self):
        cell_trace_subscription_cbs.create()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace CBS", "Create Cell Trace Subscription for CBS RequestException")
    def test_022_create_cell_trace_subscription_CBS_raises_RequestError(self):
        self.assertRaises(RequestException, cell_trace_subscription_cbs.create)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace CBS", "Activate Cell Trace Subscription for CBS")
    def test_023_activate_cell_trace_subscription_CBS_success(self):
        cell_trace_subscription_cbs.activate()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace CBS", "Activate Cell Trace Subscription for CBS RequestException")
    def test_024_activate_cell_trace_subscription_CBS_raises_RequestError(self):
        self.assertRaises(RequestException, cell_trace_subscription_cbs.activate)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Cell Trace CBS", "Deactivate Cell Trace Subscription for CBS")
    def test_025_deactivate_cell_trace_subscription_CBS_success(self):
        cell_trace_subscription_cbs.deactivate()

    @func_dec("PMIC Cell Trace CBS", "Deactivate Cell Trace Subscription for CBS RequestException")
    def test_026_deactivate_cell_trace_subscription_CBS_raises_RequestError(self):
        self.assertRaises(RequestException, cell_trace_subscription_cbs.deactivate)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC EBM Subscription CBS", "Create EBM Subscription for CBS")
    def test_027_create_ebm_subscription_CBS_success(self):
        ebm_subscription_cbs.create()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC EBM Subscription CBS", "Create EBM Subscription for CBS RequestException")
    def test_028_create_ebm_subscription_CBS_raises_RequestError(self):
        self.assertRaises(RequestException, ebm_subscription_cbs.create)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC EBM Subscription CBS", "Activate EBM Subscription for CBS")
    def test_029_activate_ebm_subscription_CBS_success(self):
        ebm_subscription_cbs.activate()

    @setup_verify(available_nodes=1)
    @func_dec("PMIC EBM Subscription CBS", "Activate EBM Subscription for CBS RequestException")
    def test_030_activate_ebm_subscription_CBS_raises_RequestError(self):
        self.assertRaises(RequestException, ebm_subscription_cbs.activate)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC EBM Subscription CBS", "Update EBM Subscription for CBS")
    def test_031_deactivate_ebm_subscription_CBS_success(self):
        ebm_subscription_cbs.deactivate()

    @func_dec("PMIC EBM Subscription CBS", "Deactivate EBM Subscription for CBS RequestException")
    def test_032_deactivate_ebm_subscription_CBS_raises_RequestError(self):
        self.assertRaises(RequestException, ebm_subscription_cbs.deactivate)

    @setup_verify(available_nodes=1)
    @func_dec("PMIC Statistical CBS", "Clean-up all Subscriptions CBS from ENM")
    def test_033_clean_all_subscriptions_CBS_from_ENM(self):
        StatisticalSubscription.clean_subscriptions(delete_all=True)

    @func_dec("log_results_of_nbi_transfer", "Log to the rsyslogd messages file when PM_26 profile iteration is "
                                             "successful")
    def test_034_log_results_of_nbi_transfer__if_pm_26_profile_iteration_is_successful(self):
        pm_fls_nbi_profile = PmFlsNbiProfile()
        pm_fls_nbi_profile.SCHEDULE_SLEEP = 1
        pm_fls_nbi_profile.DATA_TYPES = ["PM_STATISTICAL", "PM_CELLTRACE", "PM_CTUM", 'PM_CTUM', 'PM_EBM',
                                         'PM_UETR', 'PM_EBSL', 'PM_GPEH', 'PM_UETRACE', 'PM_CTR', 'TOPOLOGY_*',
                                         'PM_CELLTRACE_CUCP', 'PM_CELLTRACE_CUUP', 'PM_CELLTRACE_DU']
        pm_fls_nbi_profile.N_SFTP_THREADS = 10
        pm_fls_nbi_profile.JOIN_QUEUE_TIMEOUT = 1
        pm_fls_nbi_profile.SFTP_FETCH_TIME_IN_MINS = 13
        pm_fls_nbi_profile.ROP_INTERVAL = 15
        pm_fls_nbi_profile.OFFSET = 1
        pm_fls_nbi_profile.FETCH_ROP_AGE_NUMBER = 1
        pm_fls_nbi_profile.user_roles = ["PM_NBI_Operator", "Scripting_Operator"]
        file_path = "/var/log/messages"
        local_time = time.time()
        start_time = (datetime.datetime.fromtimestamp(local_time)).strftime("%Y-%m-%dT%H:%M:00")
        end_time = (datetime.datetime.fromtimestamp(local_time) +
                    datetime.timedelta(minutes=pm_fls_nbi_profile.ROP_INTERVAL)).strftime("%Y-%m-%dT%H:%M:00")
        pm_fls_nbi_profile.time_now = time.time()
        pm_fls_nbi_profile.tz = timezone("Europe/Dublin")
        pm_fls_nbi_profile.collection_times = {"start_time_of_iteration": pm_fls_nbi_profile.time_now - 10,
                                               "start": start_time,
                                               "end": end_time,
                                               "time_range": (start_time, end_time),
                                               "rop_interval": pm_fls_nbi_profile.ROP_INTERVAL}
        pm_fls_nbi_profile.user = Mock(username="TestUser")
        pm_fls_nbi_profile.fls = Fls(user=pm_fls_nbi_profile.user)
        missed_file_count = {'1': 0, '0': 0, '3': 0, '2': 0, '5': 0, '4': 0, '7': 0, '6': 0, '9': 0, '8': 0}
        pm_fls_nbi_profile.nbi_transfer_stats[pm_fls_nbi_profile.user.username] = {"nbi_transfer_file_count": 240,
                                                                                   "nbi_transfer_time": 247.2,
                                                                                   "nbi_fls_file_count": 349,
                                                                                   "missed_file_count": missed_file_count}
        missed_files_count = 0
        for _, batch_file_count in missed_file_count.iteritems():
            missed_files_count += batch_file_count
        transfer_time_taken_text = ("{0:4.2f} min".format(float(pm_fls_nbi_profile.nbi_transfer_stats
                                                                [pm_fls_nbi_profile.user.username]
                                                                ["nbi_transfer_time"]) / 60))
        updated_excepted_output = ("PmFlsNbiProfile NBI File Transfer Results for user {username}:- "
                                   "COLLECTED_ROP: {start_time} -> {end_time}, STARTED_AT: {start_time_of_iteration}, "
                                   "FLS_FILE_COUNT: {fls_file_count}, TRANSFERRED_FILE_COUNT: {transferred_file_count}, "
                                   "MISSED_FILE_COUNT: {missed_file_count}, TIME_TAKEN: {time_taken}, "
                                   "SUCCESS: True".format(username=pm_fls_nbi_profile.user.username,
                                                          start_time=pm_fls_nbi_profile.collection_times['start'],
                                                          end_time=pm_fls_nbi_profile.collection_times['end'],
                                                          start_time_of_iteration=datetime.datetime.
                                                          fromtimestamp(pm_fls_nbi_profile.collection_times['start_time_of_iteration']),
                                                          fls_file_count=pm_fls_nbi_profile.nbi_transfer_stats[pm_fls_nbi_profile.user.username]['nbi_fls_file_count'],
                                                          transferred_file_count=pm_fls_nbi_profile.nbi_transfer_stats[pm_fls_nbi_profile.user.username]['nbi_fls_file_count'],
                                                          missed_file_count=missed_files_count, time_taken=transfer_time_taken_text))
        pm_fls_nbi_profile.log_results_of_nbi_transfer(True, pm_fls_nbi_profile.collection_times,
                                                       pm_fls_nbi_profile.user.username)
        response = shell.run_local_cmd('egrep "{0}" {1}'.format(updated_excepted_output, file_path))
        self.assertTrue(updated_excepted_output in response.stdout)
        response = shell.run_local_cmd('egrep -c "{0}" {1}'.format(updated_excepted_output, file_path))
        self.assertEqual(1, int((response.stdout).strip()))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
