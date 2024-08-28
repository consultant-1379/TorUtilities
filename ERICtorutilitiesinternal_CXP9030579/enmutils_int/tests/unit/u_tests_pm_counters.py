#!/usr/bin/env python

import unittest2
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib import pm_counters
from mock import patch, Mock, call
from testslib import unit_test_utils


class PmCountersUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.counter1 = {"moClassType": "class1", "name": "counter1"}
        self.counter2 = {"moClassType": "class2", "name": "counter2"}
        self.counter3 = {"moClassType": "class3", "name": "counter3"}
        self.counter4 = {"moClassType": "class4", "name": "counter4"}
        self.counter5 = {"moClassType": "class5", "name": "counter5"}
        self.counter6 = {"moClassType": "class6", "name": "counter6"}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.pm_counters.filter_counters_for_pm38")
    @patch("enmutils_int.lib.pm_counters.get_reserved_pm_counters")
    @patch("enmutils_int.lib.pm_counters.get_counters_for_all_technology_domains")
    def test_get_tech_domain_counters_based_on_profile__successful_for_pm_48(
            self, mock_get_counters_for_all_technology_domains, mock_get_reserved_pm_counters,
            mock_filter_counters_for_pm38):
        subscription = Mock()
        subscription.name = "PM_48_012345"
        counter1 = Mock()
        all_counters = Mock()
        mock_get_counters_for_all_technology_domains.return_value = all_counters
        mock_get_reserved_pm_counters.return_value = [counter1]

        self.assertEqual(pm_counters.get_tech_domain_counters_based_on_profile(subscription), [counter1])
        mock_get_counters_for_all_technology_domains.assert_called_with(subscription)
        mock_get_reserved_pm_counters.assert_called_with(subscription, all_counters)
        self.assertFalse(mock_filter_counters_for_pm38.called)

    @patch("enmutils_int.lib.pm_counters.filter_counters_for_pm38")
    @patch("enmutils_int.lib.pm_counters.get_reserved_pm_counters")
    @patch("enmutils_int.lib.pm_counters.get_counters_for_all_technology_domains")
    def test_get_tech_domain_counters_based_on_profile__successful_for_pm_38(
            self, mock_get_counters_for_all_technology_domains, mock_get_reserved_pm_counters,
            mock_filter_counters_for_pm38):
        subscription = Mock()
        subscription.name = "PM_38_012345"
        counter1, counter2 = Mock(), Mock()
        all_counters = Mock()
        mock_get_counters_for_all_technology_domains.return_value = all_counters
        mock_get_reserved_pm_counters.return_value = [counter1]
        mock_filter_counters_for_pm38.return_value = [counter2]

        self.assertEqual(pm_counters.get_tech_domain_counters_based_on_profile(subscription), [counter2])
        mock_get_counters_for_all_technology_domains.assert_called_with(subscription)
        mock_get_reserved_pm_counters.assert_called_with(subscription, all_counters)
        mock_filter_counters_for_pm38.assert_called_with(subscription, all_counters, [counter1])

    def test_get_reserved_pm_counters__successful(self):
        subscription = Mock(reserved_counters={"EPS": 2})
        counter1, counter2, counter3 = {"name": "counter1"}, {"name": "counter2"}, {"name": "counter3"}
        all_counters = {"EPS": [counter2, counter3, counter1]}

        self.assertEqual([counter1, counter2], pm_counters.get_reserved_pm_counters(subscription, all_counters))

    def test_get_reserved_pm_counters__successful_if_no_counters_provided(self):
        subscription = Mock(reserved_counters={"EPS": 2})
        all_counters = {"EPS": []}

        self.assertEqual([], pm_counters.get_reserved_pm_counters(subscription, all_counters))

    @patch("enmutils_int.lib.pm_counters.filter_out_duplicate_counters")
    def test_filter_counters_for_pm38__successful(self, mock_filter_out_duplicate_counters):
        subscription = Mock(technology_domain_counter_limits={"EPS": 1, "UMTS": 1, "5GS": 1})
        all_counters = {"EPS": [self.counter2, self.counter3, self.counter1],
                        "UMTS": [self.counter6, self.counter4, self.counter5],
                        "5GS": []}
        reserved_pm_counters = [self.counter1, self.counter4]

        pm_counters.filter_counters_for_pm38(subscription, all_counters, reserved_pm_counters)
        limited_lists_of_counters = {"EPS": [self.counter2], "UMTS": [self.counter5]}
        mock_filter_out_duplicate_counters.assert_called_with(limited_lists_of_counters)

    def test_filter_out_duplicate_counters__successful(self):
        counters_for_all_tech_domains = {"EPS": [self.counter1, self.counter2], "UMTS": [self.counter1, self.counter3]}

        self.assertEqual(pm_counters.filter_out_duplicate_counters(counters_for_all_tech_domains),
                         [self.counter1, self.counter2, self.counter3])

    @patch("enmutils_int.lib.pm_counters.get_counters_for_tech_domain")
    def test_get_counters_for_all_technology_domains__successful(self, mock_get_counters_for_tech_domain):
        node1, node2 = {"name": "node1", "technologyDomain": ["EPS"]}, {"name": "node1", "technologyDomain": ["UMTS"]}
        subscription = Mock(parsed_nodes=[node1, node2], technology_domain_counter_limits={"EPS": 1})

        pm_counters.get_counters_for_all_technology_domains(subscription)
        mock_get_counters_for_tech_domain.assert_called_with(subscription, "EPS", [node1])

    @patch("enmutils_int.lib.pm_counters.get_counters_for_tech_domain")
    def test_get_counters_for_all_technology_domains__returns_no_counters_if_no_nodes_exist_with_tech_domain(
            self, mock_get_counters_for_tech_domain):
        node1, node2 = {"name": "node1", "technologyDomain": ["UMTS"]}, {"name": "node1", "technologyDomain": ["UMTS"]}
        subscription = Mock(parsed_nodes=[node1, node2], technology_domain_counter_limits={"EPS": 1})

        self.assertEqual(pm_counters.get_counters_for_all_technology_domains(subscription), {"EPS": []})
        self.assertFalse(mock_get_counters_for_tech_domain.called)

    @patch("enmutils_int.lib.pm_counters.filter_common_counters_for_model_ids")
    @patch("enmutils_int.lib.pm_counters.filter_counters")
    @patch("enmutils_int.lib.pm_counters.fetch_counters_from_enm_per_model_id")
    def test_get_counters_for_tech_domain__successful(
            self, mock_fetch_counters_from_enm_per_model_id, mock_filter_counters,
            mock_filter_common_counters_for_model_ids):
        nodes = [{"name": "node1", "ossModelIdentity": "123-456"}, {"name": "node2", "ossModelIdentity": "234-567"}]
        subscription = Mock()
        enm_counters1, enm_counters2 = Mock(), Mock()
        mock_fetch_counters_from_enm_per_model_id.side_effect = [enm_counters1, enm_counters2]
        filtered_counters1 = ["counter1", "counter2", "counter3"]
        filtered_counters2 = ["counter2", "counter3", "counter4"]
        mock_filter_counters.side_effect = [filtered_counters1, filtered_counters2]

        self.assertEqual(pm_counters.get_counters_for_tech_domain(subscription, "EPS", nodes),
                         mock_filter_common_counters_for_model_ids.return_value)
        self.assertEqual([call(subscription, "RadioNode", "123-456", "EPS"),
                          call(subscription, "RadioNode", "234-567", "EPS")],
                         mock_fetch_counters_from_enm_per_model_id.mock_calls)
        self.assertTrue(call(subscription, "EPS", enm_counters1) in mock_filter_counters.mock_calls)
        self.assertTrue(call(subscription, "EPS", enm_counters2) in mock_filter_counters.mock_calls)
        self.assertEqual(mock_filter_counters.call_count, 2)

    @patch("enmutils_int.lib.pm_counters.filter_common_counters_for_model_ids")
    @patch("enmutils_int.lib.pm_counters.filter_counters")
    @patch("enmutils_int.lib.pm_counters.fetch_counters_from_enm_per_model_id")
    def test_get_counters_for_tech_domain__successful_if_only_one_model_id(
            self, mock_fetch_counters_from_enm_per_model_id, mock_filter_counters,
            mock_filter_common_counters_for_model_ids):
        nodes = [{"name": "node1", "ossModelIdentity": "123-456"}, {"name": "node2", "ossModelIdentity": "123-456"}]
        subscription = Mock()
        enm_counters = Mock()
        mock_fetch_counters_from_enm_per_model_id.return_value = enm_counters
        filtered_counters = ["counter1", "counter2", "counter3"]
        mock_filter_counters.return_value = filtered_counters

        self.assertEqual(pm_counters.get_counters_for_tech_domain(subscription, "EPS", nodes), filtered_counters)
        self.assertEqual([call(subscription, "RadioNode", "123-456", "EPS")],
                         mock_fetch_counters_from_enm_per_model_id.mock_calls)
        self.assertTrue(call(subscription, "EPS", enm_counters) in mock_filter_counters.mock_calls)
        self.assertEqual(mock_filter_counters.call_count, 1)
        self.assertFalse(mock_filter_common_counters_for_model_ids.called)

    @patch("enmutils_int.lib.pm_counters.filter_common_counters_for_model_ids", return_value=[])
    @patch("enmutils_int.lib.pm_counters.filter_counters")
    @patch("enmutils_int.lib.pm_counters.fetch_counters_from_enm_per_model_id")
    def test_get_counters_for_tech_domain__returns_no_counters(
            self, mock_fetch_counters_from_enm_per_model_id, mock_filter_counters,
            mock_filter_common_counters_for_model_ids):
        nodes = [{"name": "node1", "ossModelIdentity": "123-456"}]
        subscription = Mock()
        mock_fetch_counters_from_enm_per_model_id.return_value = []

        self.assertEqual(pm_counters.get_counters_for_tech_domain(subscription, "EPS", nodes), [])
        self.assertEqual([call(subscription, "RadioNode", "123-456", "EPS")],
                         mock_fetch_counters_from_enm_per_model_id.mock_calls)
        self.assertFalse(mock_filter_common_counters_for_model_ids.called)
        self.assertFalse(mock_filter_counters.called)

    def test_fetch_counters_from_enm_per_model_id__successful(self):
        enm_counters = [Mock()]
        response = Mock()
        response.json.return_value = enm_counters
        subscription = Mock()
        subscription.user.get.return_value = response
        url = "/pm-service/rest/pmsubscription/counters?mim=RadioNode:123-456:EPS&definer=NE"

        self.assertEqual(pm_counters.fetch_counters_from_enm_per_model_id(subscription, "RadioNode", "123-456", "EPS"),
                         enm_counters)
        subscription.user.get.assert_called_with(url, headers=JSON_SECURITY_REQUEST)

    def test_filter_common_counters_for_model_ids__successful(self):
        user_defined_counters = {"123-2345": [self.counter1, self.counter2, self.counter3],
                                 "234-3456": [self.counter2, self.counter3, self.counter4]}

        self.assertEqual(pm_counters.filter_common_counters_for_model_ids(user_defined_counters),
                         [self.counter2, self.counter3])

    def test_filter_common_counters_for_model_ids__successful_if_only_one_type_of_model_id(self):
        user_defined_counters = {"123-2345": [self.counter1, self.counter2, self.counter3]}

        self.assertEqual(pm_counters.filter_common_counters_for_model_ids(user_defined_counters),
                         [self.counter1, self.counter2, self.counter3])

    def test_filter_common_counters_for_model_ids__returns_no_counters(self):
        self.assertEqual([], pm_counters.filter_common_counters_for_model_ids({}))

    @patch("enmutils_int.lib.pm_counters.filter_excluded_counters")
    @patch("enmutils_int.lib.pm_counters.filter_included_counters")
    @patch("enmutils_int.lib.pm_counters.filter_user_defined_counters")
    def test_filter_counters__successful(
            self, mock_filter_user_defined_counters, mock_filter_included_counters, mock_filter_excluded_counters):
        subscription = Mock()
        delattr(subscription, "mo_class_counters_included")
        delattr(subscription, "mo_class_counters_excluded")
        counters = [Mock()]

        self.assertEqual(pm_counters.filter_counters(subscription, "EPS", counters),
                         mock_filter_user_defined_counters.return_value)
        self.assertFalse(mock_filter_included_counters.called)
        self.assertFalse(mock_filter_excluded_counters.called)

    @patch("enmutils_int.lib.pm_counters.filter_excluded_counters")
    @patch("enmutils_int.lib.pm_counters.filter_included_counters")
    @patch("enmutils_int.lib.pm_counters.filter_user_defined_counters")
    def test_filter_counters__successful_if_mo_class_counters_included(
            self, mock_filter_user_defined_counters, mock_filter_included_counters, mock_filter_excluded_counters):
        subscription = Mock(mo_class_counters_included={"EPS": ["ClassA"]})
        delattr(subscription, "mo_class_counters_excluded")
        counters = [Mock()]

        self.assertEqual(pm_counters.filter_counters(subscription, "EPS", counters),
                         mock_filter_included_counters.return_value)
        self.assertTrue(mock_filter_user_defined_counters.called)
        self.assertFalse(mock_filter_excluded_counters.called)

    @patch("enmutils_int.lib.pm_counters.filter_excluded_counters")
    @patch("enmutils_int.lib.pm_counters.filter_included_counters")
    @patch("enmutils_int.lib.pm_counters.filter_user_defined_counters")
    def test_filter_counters__successful_if_mo_class_counters_excluded(
            self, mock_filter_user_defined_counters, mock_filter_included_counters, mock_filter_excluded_counters):
        subscription = Mock(mo_class_counters_excluded={"EPS": ["ClassA"]})
        delattr(subscription, "mo_class_counters_included")
        counters = [Mock()]

        self.assertEqual(pm_counters.filter_counters(subscription, "EPS", counters),
                         mock_filter_excluded_counters.return_value)
        self.assertTrue(mock_filter_user_defined_counters.called)
        self.assertFalse(mock_filter_included_counters.called)

    def test_filter_user_defined_counters__successful(self):
        counters = [{"sourceObject": "Class1", "counterName": "counter1", "scannerType": "USER_DEFINED"},
                    {"sourceObject": "Class2", "counterName": "counter2", "scannerType": "PREDEF"}]
        filtered_counters = [{"moClassType": "Class1", "name": "counter1"}]

        self.assertEqual(filtered_counters, pm_counters.filter_user_defined_counters(counters))

    def test_filter_excluded_counters__successful(self):
        counters = [{"moClassType": "Class1", "name": "counter1"},
                    {"moClassType": "Class2", "name": "counter2"}]
        filtered_counters = [{"moClassType": "Class1", "name": "counter1"}]

        self.assertEqual(filtered_counters, pm_counters.filter_excluded_counters(counters, ["Class2"]))

    def test_filter_included_counters__successful(self):
        counters = [{"moClassType": "Class1", "name": "counter1"},
                    {"moClassType": "Class2", "name": "counter2"}]
        filtered_counters = [{"moClassType": "Class2", "name": "counter2"}]

        self.assertEqual(filtered_counters, pm_counters.filter_included_counters(counters, ["Class2"]))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
