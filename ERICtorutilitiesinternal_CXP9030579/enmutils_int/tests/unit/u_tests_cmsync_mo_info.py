#!/usr/bin/env python
import unittest2
from mock import Mock, patch, PropertyMock
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib.exceptions import ScriptEngineResponseValidationError, DependencyException
from enmutils_int.lib import cmsync_mo_info
from testslib import unit_test_utils


class CmSyncMoInfoUnitTests(ParameterizedTestCase):
    maxDiff = None

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.get_network_notification_total', return_value=61230000)
    def setUp(self, _):  # pylint: disable=arguments-differ
        unit_test_utils.setup()
        self.user = Mock(username="cmsync_mo_info")
        network_mo_count = 61230
        mediator_dict = {
            "MSCM": {"EUtranCellFDD": 3840, "EUtranCellTDD": 0, "UtranCell": 14442, "GeranCell": 0, "NRCellCU": 0},
            "MSCMCE": {"EUtranCellFDD": 21390, "EUtranCellTDD": 1000, "UtranCell": 20558, "GeranCell": 10000,
                       "NRCellCU": 0}
        }
        kwargs = {"values_per_profile": {"cmsync_01": 0.0132, "CMSYNC_02": 0.6997, "CMSYNC_04": 0.1435, "CMSYNC_06": 0.1436}}
        self.cmsync_mo_info = cmsync_mo_info.CmSyncMoInfo(self.user, mediator_dict, network_mo_count, **kwargs)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_percentage_total(self):
        self.assertEqual(self.cmsync_mo_info.get_percentage_total(23267), 37.9993)

    def test_get_percentage_total_float_division_by_zero_avoided(self):
        self.cmsync_mo_info.network_mo_count = 0
        self.assertEqual(self.cmsync_mo_info.get_percentage_total(38), 0)

    def test_total_notifications_per_mediator(self):
        self.assertEqual(self.cmsync_mo_info.total_notifications_count_per_mediator_per_day("MSCM"), 18281992.17)

    @ParameterizedTestCase.parameterize(
        ("profile_mediator", "result"),
        [
            (("CMSYNC_01", "MSCM"), 0),
            (("CMSYNC_02", "MSCM"), 12791909),
            (("CMSYNC_04", "MSCM"), 2623465),
            (("CMSYNC_06", "MSCM"), 2625294),
            (("CMSYNC_01", "MSCMCE"), 0),
            (("CMSYNC_02", "MSCMCE"), 37047736),
            (("CMSYNC_04", "MSCMCE"), 7598042),
            (("CMSYNC_06", "MSCMCE"), 7603337)
        ]
    )
    def test_calculate_notification_per_profile_per_day_per_mediator(self, profile_mediator, result):
        profile, mediator = profile_mediator
        self.assertEqual(self.cmsync_mo_info.
                         calculate_notification_per_profile_per_day_per_mediator(profile, mediator), result)

    @patch('enmutils.lib.log.logger.debug')
    def test_get_network_percentage_for_mediator_logs_attribute_error(self, mock_debug):
        self.cmsync_mo_info.get_network_percentage_for_mediator("NoSuchKey")
        self.assertTrue(mock_debug.called)

    def test_get_network_percentage_for_mediator_hardcoded_value(self):
        self.cmsync_mo_info.mediator_ratio["MSCM"] = 0.75
        self.assertEqual(0.75, self.cmsync_mo_info.get_network_percentage_for_mediator("MSCM"))

    @ParameterizedTestCase.parameterize(
        ("profile_mediator_cell", "result"),
        [
            (("CMSYNC_02", "MSCM", "EUtranCellFDD"), 2686300.89),
            (("CMSYNC_02", "MSCM", "EUtranCellTDD"), 0),
            (("CMSYNC_02", "MSCM", "UtranCell"), 10105608.11),
            (("CMSYNC_02", "MSCMCE", "EUtranCellFDD"), 14967285.344),
            (("CMSYNC_02", "MSCMCE", "EUtranCellTDD"), 700202.2104),
            (("CMSYNC_02", "MSCMCE", "UtranCell"), 14385635.8888)
        ]
    )
    def test_calculate_notifications_per_profile_per_day_per_network(self, profile_mediator_cell, result):
        profile, mediator, cell = profile_mediator_cell
        self.assertEqual(self.cmsync_mo_info.
                         calculate_notifications_per_profile_per_day_per_mo(profile, mediator, cell), result)

    def test_get_network_percentage_for_mediator_per_cell(self):
        self.cmsync_mo_info.mediator_dict["MSCM"] = {}
        self.assertEqual(self.cmsync_mo_info.get_network_percentage_for_mediator_per_mo("MSCM", "EUtranCellFDD"),
                         0.00)

    def test_get_network_percentage_for_mediator_per_cell_handles_float_division(self):
        self.cmsync_mo_info.get_network_percentage_for_mediator_per_mo("MSCM", "EUtranCellFDD")

    @ParameterizedTestCase.parameterize(
        ("profile_mediator_cell_mo", "result"),
        [
            (("CMSYNC_02", "MSCM", "EUtranCellFDD", "EUtranCellFDD"), 1316287.4361),
            (("CMSYNC_02", "MSCM", "EUtranCellFDD", "TermPointToENB"), 402945.1335),
            (("CMSYNC_02", "MSCM", "EUtranCellFDD", "PmEventService"), 402945.1335),
            (("CMSYNC_02", "MSCM", "EUtranCellFDD", "UtranCellRelation"), 268630.089),
            (("CMSYNC_02", "MSCM", "EUtranCellFDD", "EUtranCellRelation"), 134315.0445),
            (("CMSYNC_02", "MSCM", "EUtranCellFDD", "ExternalEUtranCellFDD"), 134315.0445),
            (("CMSYNC_02", "MSCMCE", "UtranCell", "UtranCell"), 6167916.0147),
            (("CMSYNC_02", "MSCMCE", "UtranCell", "Rach"), 2055972.0049),
            (("CMSYNC_02", "MSCMCE", "UtranCell", "Pch"), 2055972.0049),
            (("CMSYNC_02", "MSCMCE", "UtranCell", "Hsdsch"), 2055972.0049),
            (("CMSYNC_02", "MSCMCE", "UtranCell", "Fach"), 2055972.0049),
            (("CMSYNC_02", "MSCMCE", "UtranCell", "GsmRelation"), 6167916.0147)
        ]
    )
    def test_calculate_notifications_per_day_per_mo_cmsync_02(self, profile_mediator_cell_mo, result):
        profile, mediator, cell, mo = profile_mediator_cell_mo
        self.assertEqual(self.cmsync_mo_info.
                         calculate_notifications_per_day_per_mo(profile, mediator, cell, mo), result)

    @ParameterizedTestCase.parameterize(
        ("profile_mediator_cell_mo", "result"),
        [
            (("CMSYNC_02", "MSCM", "EUtranCellFDD", "EUtranCellFDD"), 15.2348),
            (("CMSYNC_02", "MSCM", "UtranCell", "UtranCell"), 50.1485)
        ]
    )
    def test_calculate_notifications_per_mo_per_profile_cell_per_mediator_per_second(self, profile_mediator_cell_mo,
                                                                                     result):
        profile, mediator, cell, mo = profile_mediator_cell_mo
        self.assertEqual(self.cmsync_mo_info.
                         calculate_notification_rate_per_mo_per_profile_per_mo_type_per_mediator(profile, mediator,
                                                                                                 cell, mo), result)

    @ParameterizedTestCase.parameterize(
        ("profile_mediator_cell_mo_rate", "result"),
        [
            (("CMSYNC_02", "MSCM", "EUtranCellFDD", "EUtranCellFDD", 2), 7.6174),
            (("CMSYNC_02", "MSCM", "UtranCell", "UtranCell", 4), 12.537125)
        ]
    )
    def test_calculate_node_count_per_mo_per_profile(self, profile_mediator_cell_mo_rate, result):
        profile, mediator, cell, mo, rate = profile_mediator_cell_mo_rate
        self.assertEqual(self.cmsync_mo_info.
                         calculate_node_count_per_mo_per_profile(profile, mediator, cell, mo, rate), result)

    @ParameterizedTestCase.parameterize(
        ("profile_mediator_cell_mo", "result"),
        [
            (("CMSYNC_02", "MSCM", "EUtranCellFDD", "EUtranCellFDD"), (7, 2, 2, 0.6174)),
            (("CMSYNC_02", "MSCM", "UtranCell", "UtranCell"), (12, 4, 4, 0.5371249999999996)),
            (("CMSYNC_06", "MSCM", "UtranCell", "UtranCell"), (0, 32))
        ]
    )
    def test_calculate_adjusted_nodes_for_each_mo_per_profile(self, profile_mediator_cell_mo, result):
        profile, mediator, cell, mo = profile_mediator_cell_mo
        self.assertEqual(self.cmsync_mo_info.
                         calculate_adjusted_nodes_for_each_mo_per_profile(profile, mediator, cell, mo), result)

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.calculate_node_count_per_mo_per_profile',
           return_value=6.00)
    def test_calculate_adjusted_nodes_for_each_mo_per_profile_no_integer(self, *_):
        profile, mediator, cell, mo = "CMSYNC_02", "MSCM", "EUtranCellFDD", "EUtranCellFDD"
        self.assertEqual(self.cmsync_mo_info.
                         calculate_adjusted_nodes_for_each_mo_per_profile(profile, mediator, cell, mo), (6, 2))

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.calculate_node_count_per_mo_per_profile', return_value=1.00)
    def test_calculate_adjusted_nodes_for_each_mo_per_profile__updates_notification_rate_mcd_mscm(self, mock_count):
        profile, mediator, cell = "CMSYNC_01", "MSCM", "EUtranCellFDD"
        self.cmsync_mo_info.calculate_adjusted_nodes_for_each_mo_per_profile(profile, mediator, cell, cell)
        mock_count.assert_called_with(profile, mediator, cell, cell, 0.04)

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.calculate_node_count_per_mo_per_profile', return_value=1.00)
    def test_calculate_adjusted_nodes_for_each_mo_per_profile__updates_notification_rate_mcd_mscmce(self, mock_count):
        profile, mediator, cell = "CMSYNC_01", "MSCMCE", "EUtranCellFDD"
        self.cmsync_mo_info.calculate_adjusted_nodes_for_each_mo_per_profile(profile, mediator, cell, cell)
        mock_count.assert_called_with(profile, mediator, cell, cell, 0.5)

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.apply_mediation_limits')
    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.set_radio_node_managed_element_type', return_value="EPS")
    def test_set_values_for_all_profiles(self, *_):
        self.cmsync_mo_info.profile_notification_calculations = {"CMSYNC_02": []}
        self.cmsync_mo_info.set_values_for_all_profiles()
        self.assertEqual(len(self.cmsync_mo_info.profile_notification_calculations.get("CMSYNC_02")), 44)

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.apply_mediation_limits')
    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.set_radio_node_managed_element_type', return_value="EPS")
    def test_set_values_for_all_profiles_skips_empty(self, *_):
        self.cmsync_mo_info.profile_notification_calculations = {"CMSYNC_02": []}
        self.cmsync_mo_info.values_per_profile["CMSYNC_02"] = 0
        self.cmsync_mo_info.set_values_for_all_profiles()
        self.assertEqual(len(self.cmsync_mo_info.profile_notification_calculations.get("CMSYNC_02")), 0)

    @patch("enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.set_profile_values_for_each_mo_type")
    def test_set_profile_values_for_each_mediator_skips_empty_mediation(self, mock_each_mo_type):
        self.cmsync_mo_info.mediator_dict = {"MSCM": {"EUtranCell": 0, "UtranCell": 0}, "MSCMCE": {"EUtranCell": 0}}
        self.cmsync_mo_info.set_profile_values_for_each_mediator("CMSYNC_02")
        self.assertEqual(0, mock_each_mo_type.call_count)

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.set_radio_node_managed_element_type', return_value="EPS")
    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.calculate_adjusted_nodes_for_each_mo_per_profile',
           return_value=(8, 2))
    def test_set_profile_values_for_managed_object(self, *_):
        profile = "CMSYNC_02"
        expected = [
            ['RNC', 'Fach', 8, 2],
            ['RNC', 'GsmRelation', 8, 2],
            ['RNC', 'Hsdsch', 8, 2],
            ['RNC', 'UtranCell', 8, 2],
            ['RNC', 'Pch', 8, 2],
            ['RNC', 'Rach', 8, 2]
        ]
        self.cmsync_mo_info.set_profile_values_for_managed_object(profile, "MSCM", "UtranCell")
        self.assertListEqual(expected, self.cmsync_mo_info.profile_notification_calculations.get(profile))

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.set_radio_node_managed_element_type', return_value="EPS")
    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.calculate_adjusted_nodes_for_each_mo_per_profile',
           side_effect=[(0, 2, 0, 2), (0, 2)] * 6)
    def test_set_profile_values_for_managed_object_removes_none_types(self, *_):
        profile = "CMSYNC_02"
        expected = self.cmsync_mo_info.profile_notification_calculations.get(profile)
        self.cmsync_mo_info.set_profile_values_for_managed_object(profile, "MSCM", "UtranCell")
        self.cmsync_mo_info.set_profile_values_for_managed_object(profile, "MSCM", "UtranCell")
        self.assertListEqual(expected, self.cmsync_mo_info.profile_notification_calculations.get(profile))

    @ParameterizedTestCase.parameterize(
        ("domain", "result"),
        [
            ("[EPS]", "ENodeB"),
            ("[UMTS]", "WRAN"),
            ("[EPS,UMTS]", "ENodeB,WRAN")
        ]
    )
    def test_select_technology_domain_key(self, domain, result):
        self.assertEqual(self.cmsync_mo_info.select_technology_domain_key(domain), result)

    @patch('enmutils_int.lib.cmsync_mo_info.persistence.set')
    def test_persist_updated_radio_load_node(self, mock_set):
        node = Mock()
        node.managed_element_type = None
        self.cmsync_mo_info.persist_updated_radio_load_node(node, "ENodeB")
        self.assertTrue(mock_set.called)

    @patch('enmutils_int.lib.cmsync_mo_info.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.cmsync_mo_info.node_pool_mgr.Pool.persist')
    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.select_technology_domain_key',
           return_value="WRAN")
    @patch('enmutils_int.lib.cmsync_mo_info.node_pool_mgr.Pool.node_dict', new_callable=PropertyMock)
    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.persist_updated_radio_load_node')
    def test_set_radio_node_managed__element_type(self, mock_persist_updated_radio_load_node,
                                                  mock_node_dict, *_):
        response = Mock()
        response.get_output.return_value = [
            u'NetworkElement', u'NetworkElementId\tneType\ttechnologyDomain', u'LTE40dg2ERBS00002\tRadioNode\t[EPS]',
            u'NetworkElement', u'NetworkElementId\tneType\ttechnologyDomain', u'LTE40dg2ERBS00001\tRadioNode\t[EPS]',
            u'', u'2 instance(s)']
        self.user.enm_execute.return_value = response
        node, node1 = Mock(), Mock()
        node.managed_element_type = "ENodeB"
        node1.managed_element_type = ""
        node.node_id, node1.node_id = "LTE40dg2ERBS00001", "LTE40dg2ERBS00002"
        mock_node_dict.return_value = {"RadioNode": {"LTE40dg2ERBS00001": node, "LTE40dg2ERBS00002": node1}}
        self.cmsync_mo_info.set_radio_node_managed_element_type()
        self.assertTrue(mock_persist_updated_radio_load_node.called)

    def test_set_radio_node_managed_element_type__raises_script_engine_error(self):
        response = Mock()
        response.get_output.return_value = [u'ErRor']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.cmsync_mo_info.set_radio_node_managed_element_type)

    def test_set_radio_node_managed_element_type__raises_dependency_error(self):
        response = Mock()
        response.get_output.return_value = [
            u'NetworkElement', u'NetworkElementId\tneType\ttechnologyDomain', u'LTE40dg2ERBS00002\tERBS\t[EPS]',
            u'NetworkElement', u'NetworkElementId\tneType\ttechnologyDomain', u'LTE40dg2ERBS00001\tERBS\t[EPS]',
            u'', u'2 instance(s)']
        self.user.enm_execute.return_value = response
        self.assertRaises(DependencyException, self.cmsync_mo_info.set_radio_node_managed_element_type)

    def test_determine_node_allocation_for_profile(self):
        notification = [["ERBS", "Mo1", 10, 2], ["ERBS", "Mo1", 2, 0.5], ["ERBS", "Mo1", 10, 2], ["RNC", "Mo1", 10, 4],
                        ["RadioNode", "Mo1", 10, 0.5],
                        ["RadioNode", "Mo1", 10, 0.5]]
        self.assertDictEqual(self.cmsync_mo_info.determine_node_allocation_for_profile(notification),
                             {'ERBS': 22, 'RNC': 10, 'RadioNode': 20})

    def test_set_profile_node_allocations_values(self):
        notifications = [["ERBS", "Mo1", 10, 2], ["ERBS", "Mo1", 2, 0.5], ["ERBS", "Mo1", 10, 2], ["RNC", "Mo1", 10, 4],
                         ["RadioNode", "Mo1", 10, 0.5],
                         ["RadioNode", "Mo1", 10, 0.5]]
        for i in self.cmsync_mo_info.profile_notification_calculations.iterkeys():
            self.cmsync_mo_info.profile_notification_calculations[i] = notifications
        self.cmsync_mo_info.set_profile_node_allocations_values()
        self.assertDictEqual({'ERBS': 22, 'RNC': 10, 'RadioNode': 20},
                             self.cmsync_mo_info.profile_node_allocations.get("CMSYNC_02"))

    @patch('enmutils_int.lib.cmsync_mo_info.log.logger.debug')
    def test_calculate_notification_per_profile_per_day(self, mock_debug):
        total = self.cmsync_mo_info.total_notifications * self.cmsync_mo_info.values_per_profile.get("CMSYNC_04")
        expected = "Estimated daily notifications for CMSYNC_04 is {0}.".format(total)
        self.cmsync_mo_info.values_per_profile = {"CMSYNC_04": 0.1435}
        self.cmsync_mo_info.calculate_notification_per_profile_per_day()
        mock_debug.assert_called_with(expected)

    @patch('enmutils_int.lib.cmsync_mo_info.log.logger.debug')
    def test_calculate_notification_per_profile_per_day__cmsync_02_utrancell_warning(self, mock_debug):
        expected = ("Estimated daily notifications for CMSYNC_02 will be calculated more granularly as the profile "
                    "requires more UtranCell notifications.")
        self.cmsync_mo_info.values_per_profile = {"CMSYNC_02": 0.78}
        self.cmsync_mo_info.calculate_notification_per_profile_per_day()
        mock_debug.assert_called_with(expected)

    def test_get_network_percentage_for_mediator_returns_edited_value(self):
        self.cmsync_mo_info.mscm_total = 0.75
        self.cmsync_mo_info.get_network_percentage_for_mediator("MSCM")

    def test_all_mo_percentage_add_to_one(self):
        for value in self.cmsync_mo_info.notification_ratios_per_mo_per_profile_per_mediation.itervalues():
            for mo in [_.values() for _ in value.values()]:
                if sum(mo) == 0:
                    continue
                else:
                    self.assertAlmostEqual(1.0, sum(mo))

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.get_network_notification_total', return_value=1000)
    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.apply_limit_mscmce_cell_count', return_value=(1000, 1000, 10))
    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.get_total_rnc_count', return_value=4)
    @patch('enmutils_int.lib.cmsync_mo_info.log.logger.debug')
    def test_apply_mediation_limits__success(self, mock_debug, *_):
        call = ("Updated mediation dict: {"
                "'MSCMCE': {'NRCellCU': 0, 'GeranCell': 0, 'EUtranCellFDD': 1000, 'EUtranCellTDD': 1000, "
                "'UtranCell': 20558}, 'MSCM': {'NRCellCU': 0, 'GeranCell': 0, 'EUtranCellFDD': 16282, "
                "'EUtranCellTDD': 0, 'UtranCell': 2000}}")
        self.cmsync_mo_info.apply_mediation_limits()
        mock_debug.assert_called_with(call)
        self.assertEqual(self.cmsync_mo_info.total_notifications, 1000)

    def test_get_total_rnc_count__returns_zero_if_no_rncs_on_enm(self):
        response = Mock()
        response.get_output.return_value = [u"Error 1050 : All scope is incorrect or not associated with the "
                                            u"correct Node Type"]
        self.user.enm_execute.return_value = response
        self.assertEqual(0, self.cmsync_mo_info.get_total_rnc_count())

    @patch('enmutils_int.lib.cmsync_mo_info.log.logger.debug')
    def test_get_total_rnc_count__logs_exception(self, mock_debug):
        response = Mock()
        response.get_output.side_effect = Exception("504")
        self.user.enm_execute.return_value = response
        self.assertEqual(0, self.cmsync_mo_info.get_total_rnc_count())
        mock_debug.assert_called_with("Command failed, response was: 504")

    def test_get_total_rnc_count__success(self):
        response = Mock()
        response.get_output.return_value = [u"4 instance(s)"]
        self.user.enm_execute.return_value = response
        self.assertEqual(4, self.cmsync_mo_info.get_total_rnc_count())

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.get_network_notification_total', return_value=61230000)
    def test_apply_limit_mscmce_cell_count__no_change(self, _):
        med_dict = {"MSCMCE": {"EUtranCellFDD": 1000, "EUtranCellTDD": 100}}
        info_instance = cmsync_mo_info.CmSyncMoInfo(self.user, med_dict, 1100, max_mos_mscmce=1100)
        fdd_count, tdd_count, diff = info_instance.apply_limit_mscmce_cell_count()
        self.assertEqual(1000, fdd_count)
        self.assertEqual(100, tdd_count)
        self.assertEqual(0, diff)

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.get_network_notification_total', return_value=61230000)
    def test_apply_limit_mscmce_cell_count__reduced_evenly(self, _):
        med_dict = {"MSCMCE": {"EUtranCellFDD": 600, "EUtranCellTDD": 600}}
        info_instance = cmsync_mo_info.CmSyncMoInfo(self.user, med_dict, 1100, max_mos_mscmce=1000)
        fdd_count, tdd_count, diff = info_instance.apply_limit_mscmce_cell_count()
        self.assertEqual(500, fdd_count)
        self.assertEqual(500, tdd_count)
        self.assertEqual(200, diff)

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.get_network_notification_total', return_value=61230000)
    def test_apply_limit_mscmce_cell_count__tdd_reduced(self, _):
        med_dict = {"MSCMCE": {"EUtranCellFDD": 400, "EUtranCellTDD": 1600}}
        info_instance = cmsync_mo_info.CmSyncMoInfo(self.user, med_dict, 1100, max_mos_mscmce=800)
        fdd_count, tdd_count, diff = info_instance.apply_limit_mscmce_cell_count()
        self.assertEqual(400, fdd_count)
        self.assertEqual(400, tdd_count)
        self.assertEqual(1200, diff)

    @patch('enmutils_int.lib.cmsync_mo_info.CmSyncMoInfo.get_network_notification_total', return_value=61230000)
    def test_apply_limit_mscmce_cell_count__fdd_reduced(self, _):
        med_dict = {"MSCMCE": {"EUtranCellFDD": 1600, "EUtranCellTDD": 400}}
        info_instance = cmsync_mo_info.CmSyncMoInfo(self.user, med_dict, 1100, max_mos_mscmce=800)
        fdd_count, tdd_count, diff = info_instance.apply_limit_mscmce_cell_count()
        self.assertEqual(400, fdd_count)
        self.assertEqual(400, tdd_count)
        self.assertEqual(1200, diff)

    def test_get_network_notification_total__success(self):
        self.assertEqual(61230000, self.cmsync_mo_info.get_network_notification_total())
        self.assertEqual(60230000, self.cmsync_mo_info.get_network_notification_total(reduce_count_by=1000))

    def test_get_network_notification_total__success_for_small5K(self):
        self.cmsync_mo_info.network_mo_count = 6000
        self.assertEqual(7000000, self.cmsync_mo_info.get_network_notification_total())
        self.assertEqual(7000000, self.cmsync_mo_info.get_network_notification_total(reduce_count_by=1000))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
