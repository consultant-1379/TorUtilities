#!/usr/bin/env python
import unittest2
from mock import patch, PropertyMock
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib import config
from enmutils_int.lib.nrm_default_configurations.basic_network import NeTypesEnum as Nodes
from enmutils_int.lib.services.profilemanager_helper_methods import get_all_profile_names
from enmutils_int.lib.workload_network_manager import (InputData, map_synonym_to_network_size,
                                                       determine_size_of_transport_network,
                                                       detect_transport_network_and_set_transport_size,
                                                       NETWORK_TYPE)
from testslib import unit_test_utils

SAMPLE_CONFIG_DATA = {'secui': {"SECUI_03": {"SUPPORTED": True}}}
SAMPLE_EXPECTED = {'SUPPORTED': True}


class WorkloadNetworkManagerUnitTests(ParameterizedTestCase):

    @patch('enmutils_int.lib.workload_network_manager.node_pool_mgr.get_pool', return_value=None)
    def setUp(self, _):  # pylint: disable=arguments-differ
        unit_test_utils.setup()
        self.input_data = InputData()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.deployment_info_helper_methods.get_total_cell_count', return_value=68)
    def test_network_size__successfully_sets_key(self, mock_get_total_cell_count):
        self.assertEqual(self.input_data.network_size, 68)
        self.assertEqual(mock_get_total_cell_count.call_count, 1)

    @patch('enmutils_int.lib.workload_network_manager.persistence.get', return_value="key")
    @patch('enmutils_int.lib.workload_network_manager.config.set_prop')
    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=False)
    @patch('enmutils_int.lib.workload_network_manager.InputData.network_size', new_callable=PropertyMock)
    @ParameterizedTestCase.parameterize(
        ("network_size", "response"),
        [
            (0, InputData.FORTY_K),
            (1, InputData.EXTRA_K),
            (1000, InputData.EXTRA_K),
            (1200, InputData.EXTRA_K),
            (1201, InputData.FIVE_K),
            (7500, InputData.FIVE_K),
            (14000, InputData.FIFTEEN_K),
            (15000, InputData.FIFTEEN_K),
            (27500, InputData.FIFTEEN_K),
            (27501, InputData.FORTY_K),
            (40000, InputData.FORTY_K),
            (50000, InputData.FORTY_K),
            (50001, InputData.SIXTY_K),
        ]
    )
    def test_network_key__success(self, network_size, response, mock_network_size, *_):
        mock_network_size.return_value = network_size
        self.assertEqual(self.input_data.network_key, response)

    def test_netypesenum__returns_expected_netypes(self):
        self.assertEqual("ERBS", str(Nodes.ERBS))
        self.assertEqual("ERBS", repr(Nodes.ERBS))

    def test_profile_values_contains_all_profiles_in_workload_dir(self):
        profiles_in_workload_dir = list(set(get_all_profile_names()).difference(set(unit_test_utils.NON_PROFILES)))
        profiles = ["network_01", "network_02", "cmsync_23", "network_03", "neo4j_01", "neo4j_02", "shm_46",
                    "nas_outage_02", "cmsync_43"]
        for key in self.input_data.networks.get(self.input_data.FORTY_K).keys():
            for k in self.input_data.networks.get(self.input_data.FORTY_K).get(key).iterkeys():
                profiles.append(k.lower())
        for key in self.input_data.networks.get(self.input_data.SIXTY_K).keys():
            for k in self.input_data.networks.get(self.input_data.SIXTY_K).get(key).iterkeys():
                profiles.append(k.lower())
        for key in self.input_data.networks.get(self.input_data.FIVE_K).keys():
            for k in self.input_data.networks.get(self.input_data.FIVE_K).get(key).iterkeys():
                profiles.append(k.lower())
        for key in self.input_data.networks.get(self.input_data.TWENTY_K_TRANSPORT).keys():
            for k in self.input_data.networks.get(self.input_data.TWENTY_K_TRANSPORT).get(key).iterkeys():
                profiles.append(k.lower())

        self.assertEqual(len(set(profiles_in_workload_dir)), len(set(profiles)))
        self.assertEqual(set(profiles_in_workload_dir), set(profiles))

    def test_map_synonym_to_network_key_returns_none_when_not_mapped(self):
        self.assertIsNone(map_synonym_to_network_size('not_existing'))

    @ParameterizedTestCase.parameterize(
        ("key", "network_size"),
        [
            ('10k_transport', 'transport_ten_k_network'),
            ('transport_ten_k_network', 'transport_ten_k_network'),
            ('20k_transport', 'transport_twenty_k_network'),
            ('transport_twenty_k_network', 'transport_twenty_k_network'),
            ('1', 'extra_small_network'),
            ('1k', 'extra_small_network'),
            ('extra-small', 'extra_small_network'),
            ('soem', 'soem_five_k_network'),
            ('5k_soem', 'soem_five_k_network'),
            ('soem_five_k_network', 'soem_five_k_network'),
            ('5', 'five_k_network'),
            ('5k', 'five_k_network'),
            ('five_k_network', 'five_k_network'),
            ('15', 'fifteen_k_network'),
            ('15k', 'fifteen_k_network'),
            ('fifteen_k_network', 'fifteen_k_network'),
            ('40', 'forty_k_network'),
            ('40k', 'forty_k_network'),
            ('forty_k_network', 'forty_k_network'),
            ('60', 'sixty_k_network'),
            ('60k', 'sixty_k_network'),
            ('sixty_k_network', 'sixty_k_network')
        ]
    )
    def test_map_synonym_to_network_key_returns_valid_key_when_mapped(self, key, network_size):

        self.assertTrue(map_synonym_to_network_size(key) == network_size)

    @patch('enmutils_int.lib.workload_network_manager.get_all_networks')
    def test_all_network_sizes_have_all_applications(self, *_):
        five_keys = set(self.input_data.networks.get(self.input_data.FIVE_K).keys())
        fifteen_keys = set(self.input_data.networks.get(self.input_data.FIFTEEN_K).keys())
        forty_keys = set(self.input_data.networks.get(self.input_data.FORTY_K).keys())
        sixty_keys = set(self.input_data.networks.get(self.input_data.SIXTY_K).keys())
        five_keys_soem = set(self.input_data.networks.get(map_synonym_to_network_size('soem')).keys())
        self.assertEqual([], list(five_keys - sixty_keys))
        self.assertEqual([], list(fifteen_keys - forty_keys))
        self.assertEqual([], list(forty_keys - sixty_keys))
        self.assertEqual([], list(five_keys - five_keys_soem))
        self.assertTrue(fifteen_keys == forty_keys == sixty_keys == five_keys == five_keys_soem)

    @patch('enmutils_int.lib.workload_network_manager.get_all_networks')
    def test_all_networks_are_correct_format(self, *_):
        for network in self.input_data.networks.iterkeys():
            self.assertTrue(isinstance(self.input_data.networks.get(network), dict))
            for app in self.input_data.networks.get(network).iterkeys():
                self.assertTrue(isinstance(self.input_data.networks.get(network).get(app), dict))
                for profile in self.input_data.networks.get(network).get(app).iterkeys():
                    self.assertTrue(isinstance(self.input_data.networks.get(network).get(app).get(profile), dict))

    def test_network_config_keys_correct_syntax(self):
        for network in self.input_data.networks:
            self.assertFalse(' ' in network)

    @patch('enmutils_int.lib.workload_network_manager.InputData.network_size', return_value=1000)
    def test_soem_network_is_returned_for_soem_network(self, *_):
        config.set_prop('network_config', 'SOEM')
        self.assertTrue(config.has_prop('network_config'))
        self.assertEqual(self.input_data.network_key, 'soem_five_k_network')

    @patch('enmutils_int.lib.workload_network_manager.InputData.network_size')
    def test_soem_network__is_returned_when_there_is_0_cell_and_soem_config(self, mock_network_size):
        config.set_prop('network_config', 'SOEM')
        mock_network_size.return_value = 0
        self.assertTrue(config.has_prop('network_config'))
        self.assertEqual(self.input_data.network_key, 'soem_five_k_network')

    @patch('enmutils_int.lib.workload_network_manager.InputData.network_size', return_value=1000)
    def test_network_key__extra_small_key_returned(self, *_):
        config.set_prop('network_config', 'extra-small')
        self.assertTrue(config.has_prop('network_config'))
        self.assertEqual(self.input_data.network_key, 'extra_small_network')

    @patch('enmutils_int.lib.workload_network_manager.InputData.network_size', return_value=1000)
    def test_network_key__20k_transport_key_returned(self, *_):
        config.set_prop('network_config', '20k_transport')
        self.assertTrue(config.has_prop('network_config'))
        self.assertEqual(self.input_data.network_key, 'transport_twenty_k_network')

    @patch('enmutils_int.lib.workload_network_manager.InputData.network_size', return_value=1000)
    def test_network_key__10k_transport_key_returned(self, *_):
        config.set_prop('network_config', '10k_transport')
        self.assertTrue(config.has_prop('network_config'))
        self.assertEqual(self.input_data.network_key, 'transport_ten_k_network')

    @patch('enmutils_int.lib.workload_network_manager.InputData.get_profiles_values',
           return_value={'AP_01': 'profile values'})
    @patch('enmutils_int.lib.workload_network_manager.get_all_networks')
    @patch('enmutils_int.lib.workload_network_manager.InputData.basic_network', new_callable=PropertyMock)
    def test_get_all_exclusive_profiles(self, mock_basic_network, *_):
        mock_basic_network.return_value = {"ap": {'AP_01': {"EXCLUSIVE": True, "SUPPORTED": True}}}
        self.assertEqual(["AP_01"], self.input_data.get_all_exclusive_profiles)

    @patch('enmutils_int.lib.workload_network_manager.InputData.get_profiles_values',
           return_value={'AP_01': 'profile values'})
    @patch('enmutils_int.lib.workload_network_manager.get_all_networks')
    @patch('enmutils_int.lib.workload_network_manager.InputData.basic_network', new_callable=PropertyMock)
    def test_get_all_exclusive_profiles__exclusive(self, mock_basic_network, *_):
        self.input_data.ignore_warning = True
        mock_basic_network.return_value = {"ap": {'AP_01': {"EXCLUSIVE": True, "SUPPORTED": True}}}
        self.assertEqual(["AP_01"], self.input_data.get_all_exclusive_profiles)

    @patch('enmutils_int.lib.workload_network_manager.get_all_networks')
    @patch('enmutils_int.lib.workload_network_manager.InputData.basic_network', new_callable=PropertyMock)
    def test_get_all_exclusive_profiles_ignores_false(self, mock_basic_network, *_):
        mock_basic_network.return_value = {"ap": {'AP_01': {"EXCLUSIVE": False}}}
        self.assertEqual([], self.input_data.get_all_exclusive_profiles)

    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.helper.sort_and_count_ne_types',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.workload_network_manager.determine_size_of_transport_network')
    @patch('enmutils_int.lib.workload_network_manager.log.logger.info')
    def test_detect_transport_network_and_set_transport_size__cannot_determine_network(self, mock_info, mock_transport,
                                                                                       *_):
        detect_transport_network_and_set_transport_size()
        mock_info.assert_called_with("Could not determine network type, error encountered:: [Error].Load will be "
                                     "applied based upon the network cell count.")
        self.assertEqual(0, mock_transport.call_count)

    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.helper.sort_and_count_ne_types')
    @patch('enmutils_int.lib.workload_network_manager.determine_size_of_transport_network')
    @patch('enmutils_int.lib.workload_network_manager.log.logger.info')
    def test_detect_transport_network_and_set_transport_size__detects_ran_network(self, mock_info, mock_transport,
                                                                                  mock_ne_types, *_):
        mock_ne_types.return_value = {"RadioNode": 1, "TCU02": 5000}
        detect_transport_network_and_set_transport_size()
        mock_info.assert_called_with("RAN NetworkElement(s) found, load will be applied based upon the network cell "
                                     "count.")
        self.assertEqual(0, mock_transport.call_count)

    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.helper.sort_and_count_ne_types')
    @patch('enmutils_int.lib.workload_network_manager.determine_size_of_transport_network')
    @patch('enmutils_int.lib.workload_network_manager.log.logger.info')
    def test_detect_transport_network_and_set_transport_size__core_network(self, mock_info, mock_transport,
                                                                           mock_ne_types, *_):
        mock_ne_types.return_value = {"MGW": 1}
        detect_transport_network_and_set_transport_size()
        mock_info.assert_called_with("Could not determine network type, load will be applied based upon the network "
                                     "cell count.")
        self.assertEqual(0, mock_transport.call_count)

    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.helper.sort_and_count_ne_types')
    @patch('enmutils_int.lib.workload_network_manager.determine_size_of_transport_network')
    @patch('enmutils_int.lib.workload_network_manager.log.logger.info')
    def test_detect_transport_network_and_set_transport_size__transport_network(self, mock_info, mock_transport,
                                                                                mock_ne_types, *_):
        mock_ne_types.return_value = {"TCU02": 1}
        detect_transport_network_and_set_transport_size()
        mock_info.assert_called_with("Transport NetworkElement(s) found, determining transport configuration to be "
                                     "used.")
        self.assertEqual(1, mock_transport.call_count)

    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.config.get_prop', return_value=False)
    @patch('enmutils_int.lib.workload_network_manager.helper.sort_and_count_ne_types')
    @patch('enmutils_int.lib.workload_network_manager.determine_size_of_transport_network')
    @patch('enmutils_int.lib.workload_network_manager.log.logger.debug')
    def test_detect_transport_network_and_set_transport_size__does_nothing_if_default_value_disabled(self, mock_debug,
                                                                                                     mock_transport,
                                                                                                     mock_ne_types, *_):
        detect_transport_network_and_set_transport_size()
        mock_debug.assert_called_with("Default values disabled, configuration value already supplied.")
        self.assertEqual(0, mock_transport.call_count)
        self.assertEqual(0, mock_ne_types.call_count)

    @patch('enmutils_int.lib.workload_network_manager.config.set_prop')
    def test_determine_size_of_transport_network__sets_correct_transport_size(self, mock_set):
        ne_type_dict = {"SIU02": 5000, "MGW": 100}
        determine_size_of_transport_network(ne_type_dict)
        mock_set.assert_any_call('DEFAULT_VALUES', False)
        mock_set.assert_called_with('network_config', "soem_five_k_network")
        ne_type_dict.update({"TCU02": 5001})
        determine_size_of_transport_network(ne_type_dict)
        mock_set.assert_any_call('DEFAULT_VALUES', False)
        mock_set.assert_called_with('network_config', "transport_twenty_k_network")

    @patch('enmutils_int.lib.workload_network_manager.config.set_prop')
    def test_determine_size_of_transport_network__sets_10K_transport_size(self, mock_set):
        ne_type_dict = {"SIU02": 5001, "MGW": 100}
        determine_size_of_transport_network(ne_type_dict)
        mock_set.assert_any_call('DEFAULT_VALUES', False)
        mock_set.assert_called_with('network_config', "transport_ten_k_network")

    @patch('enmutils_int.lib.workload_network_manager.InputData.network_key', new_callable=PropertyMock,
           return_value="five_k_network")
    @patch('enmutils_int.lib.workload_network_manager.persistence.get_all_default_keys', return_value=[])
    @patch('enmutils_int.lib.workload_network_manager.persistence.set')
    def test_network_property__persists_the_network_type(self, mock_set, *_):
        _ = self.input_data.network
        mock_set.assert_called_with(NETWORK_TYPE, "five_k_network", 21600, log_values=False)

    @patch('enmutils_int.lib.workload_network_manager.InputData.network_key', new_callable=PropertyMock,
           return_value="five_k_network")
    @patch('enmutils_int.lib.workload_network_manager.persistence.has_key', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.persistence.set')
    def test_network_property__does_not_persist_the_network_type_if_key_set(self, mock_set, *_):
        _ = self.input_data.network
        self.assertEqual(0, mock_set.call_count)

    @patch('enmutils_int.lib.workload_network_manager.InputData.network_size', new_callable=PropertyMock,
           return_value=0)
    @patch('enmutils_int.lib.workload_network_manager.persistence.get', return_value=None)
    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=False)
    @patch('enmutils_int.lib.workload_network_manager.detect_transport_network_and_set_transport_size')
    def test_network_key__will_check_for_transport_network(self, mock_detect, *_):
        _ = self.input_data.network_key
        self.assertEqual(1, mock_detect.call_count)

    @patch('enmutils_int.lib.workload_network_manager.InputData.network_size', new_callable=PropertyMock,
           return_value=0)
    @patch('enmutils_int.lib.workload_network_manager.map_synonym_to_network_size', return_value="key")
    @patch('enmutils_int.lib.workload_network_manager.persistence.get', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.config.set_prop')
    @patch('enmutils_int.lib.workload_network_manager.config.get_prop')
    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.detect_transport_network_and_set_transport_size')
    def test_network_key__will_use_existing_key_if_set(self, mock_detect, *_):
        self.assertEqual("key", self.input_data.network_key)
        self.assertEqual(0, mock_detect.call_count)

    @patch('enmutils_int.lib.workload_network_manager.InputData.network', new_callable=PropertyMock, return_value={})
    @patch('enmutils_int.lib.workload_network_manager.InputData.robustness_check', return_value=SAMPLE_EXPECTED)
    @patch('enmutils_int.lib.workload_network_manager.InputData.update_basic_values')
    def test_get_profiles_values__no_checks_if_robustness(self, mock_update, *_):
        self.input_data.get_profiles_values('secui', "SECUI_03")
        mock_update.assert_called_with(SAMPLE_EXPECTED, 'SECUI_03', 'secui')

    @patch('enmutils_int.lib.workload_network_manager.InputData.network', new_callable=PropertyMock,
           return_value=SAMPLE_CONFIG_DATA)
    @patch('enmutils_int.lib.workload_network_manager.InputData.network_key', new_callable=PropertyMock,
           return_value="five_network")
    @patch('enmutils_int.lib.workload_network_manager.InputData.robustness_check', return_value=None)
    @patch('enmutils_int.lib.workload_network_manager.InputData.update_basic_values')
    def test_get_profiles_values__used_selected_network_values(self, mock_update, mock_robustness, *_):
        self.input_data.get_profiles_values('secui', "SECUI_03")
        mock_update.assert_called_with(SAMPLE_EXPECTED, 'SECUI_03', 'secui')
        self.assertEqual(1, mock_robustness.call_count)

    @patch('enmutils_int.lib.workload_network_manager.InputData.network', new_callable=PropertyMock,
           return_value={'secui': {}})
    @patch('enmutils_int.lib.workload_network_manager.InputData.network_key', new_callable=PropertyMock,
           return_value="five_network")
    @patch('enmutils_int.lib.workload_network_manager.InputData.default_config_values', new_callable=PropertyMock,
           return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.InputData.robustness_check', return_value=None)
    @patch('enmutils_int.lib.workload_network_manager.InputData.update_basic_values')
    def test_get_profiles_values__defaults_to_40k_values_if_not_restricted_config(self, mock_update, mock_robustness,
                                                                                  *_):
        self.input_data.get_profiles_values('secui', "SECUI_03")
        mock_update.assert_called_with({'SCHEDULED_TIMES_STRINGS': ["00:00:00"]}, 'SECUI_03', 'secui')
        self.assertEqual(1, mock_robustness.call_count)

    @patch('enmutils_int.lib.workload_network_manager.InputData.network', new_callable=PropertyMock,
           return_value={'secui': {"SECUI_03": {}}})
    @patch('enmutils_int.lib.workload_network_manager.InputData.network_key', new_callable=PropertyMock,
           return_value="five_network")
    @patch('enmutils_int.lib.workload_network_manager.InputData.default_config_values', new_callable=PropertyMock,
           return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.InputData.robustness_check', return_value=None)
    @patch('enmutils_int.lib.workload_network_manager.InputData.update_basic_values')
    def test_get_profiles_values__defaults_to_40k_values_if_not_restricted_config_value(self, mock_update, mock_robustness,
                                                                                        *_):
        self.input_data.get_profiles_values('secui', "SECUI_03")
        self.assertTrue(mock_robustness.called)

    @patch('enmutils_int.lib.workload_network_manager.InputData.network', new_callable=PropertyMock,
           return_value={'secui': {}})
    @patch('enmutils_int.lib.workload_network_manager.InputData.network_key', new_callable=PropertyMock,
           return_value="extra_small_network")
    @patch('enmutils_int.lib.workload_network_manager.InputData.default_config_values', new_callable=PropertyMock,
           return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.InputData.robustness_check', return_value=None)
    @patch('enmutils_int.lib.workload_network_manager.InputData.update_basic_values')
    def test_get_profiles_values__no_default_if_restricted_network(self, mock_update, mock_robustness, *_):
        self.input_data.get_profiles_values('secui', "SECUI_03")
        mock_update.assert_called_with(None, 'SECUI_03', 'secui')
        self.assertEqual(1, mock_robustness.call_count)

    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.helper.get_robustness_configuration',
           return_value=SAMPLE_CONFIG_DATA)
    def test_robustness_check__updates_values_if_config_set(self, *_):
        self.assertDictEqual(SAMPLE_EXPECTED, self.input_data.robustness_check("SECUI_03", "secui"))

    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.helper.get_robustness_configuration',
           return_value={})
    def test_robustness_check__returns_none_type_if_no_match(self, *_):
        self.assertIsNone(self.input_data.robustness_check("SECUI_03", "secui"))

    @patch('enmutils_int.lib.workload_network_manager.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_network_manager.config.get_prop', return_value=False)
    @patch('enmutils_int.lib.workload_network_manager.helper.get_robustness_configuration',
           return_value=SAMPLE_CONFIG_DATA)
    def test_robustness_check__returns_none_type_if_config_not_set(self, *_):
        self.assertIsNone(self.input_data.robustness_check("SECUI_03", "secui"))

    @patch('enmutils_int.lib.workload_network_manager.InputData.basic_network', new_callable=PropertyMock,
           return_value=SAMPLE_CONFIG_DATA)
    def test_update_basic_values__updates_if_values_are_dict(self, _):
        self.assertDictEqual(SAMPLE_EXPECTED, self.input_data.update_basic_values({}, "SECUI_03", "secui"))

    @patch('enmutils_int.lib.workload_network_manager.InputData.basic_network', new_callable=PropertyMock,
           return_value=SAMPLE_CONFIG_DATA)
    def test_update_basic_values__no_update_if_none_type(self, _):
        self.assertIsNone(self.input_data.update_basic_values(None, "SECUI_03", "secui"))

    def test_basic_network__property_return_basic_dictionary(self):
        self.assertIsInstance(self.input_data.basic_network, dict)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
