import unittest2
from mock import patch, Mock

from enmutils_int.lib.reparenting import (send_post_request, get_status_request, build_cell_json,
                                          build_base_station_json, HTTPError,
                                          get_tg_mos, validate_response, check_status_code,
                                          poll_for_completed_status, get_bsc_network_elements, EnmApplicationError,
                                          remove_missing_cells, get_and_sort_geran_cells,
                                          set_inter_ran_mobility_attribute, set_channel_group_active)
from testslib import unit_test_utils

NODE_IDS = ["BSC01", "BSC02"]
CELLS = [u' FDN : GeranCell=1015102', u'FDN : GeranCell=1015110', u'', u'2 instance(s)']
G12TGS = [u' FDN : Bts=1,G12Tg=16',
          u' connectedChannelGroup : [GeranCellM=1,GeranCell=1015046,ChannelGroup=0, '
          u'GeranCell=1015047,ChannelGroup=0, GeranCell=1015048,ChannelGroup=0] ', u'', u'1 instance(s)']
MSCS = [u'FDN : NetworkElement=BSC01', u'connectedMsc : NetworkElement=MSC25']
CHANNEL = [u'conFact : 1', u'confMd : MINDIST',
           u'connectedChannelGroup : [GeranCell=1015073,ChannelGroup=0, GeranCell=1015074,ChannelGroup=0, '
           u'GeranCell=1015075,ChannelGroup=0]', u'csTma : ON', u'dAmrCr : OFF ', u'1 instance(s)']
BASE_STATIONS_WITH_CELLS = [{'G12Tg=23': ["GeranCell=1"]}, {'G12Tg=25': ["GeranCell=2"]}]
BASE_STATIONS = ['G12Tg=23', 'G12Tg=25']
GERAN_CELLS = ["GeranCell=1", "GeranCell=2"]
TARGET_NE = "BSC02"
TECHOLOGY_TYPE = "GSM"
CANDIDATES = [{'candidateFdn': GERAN_CELLS[0]}, {'candidateFdn': GERAN_CELLS[1]}]
BSCS = [u'FDN : NetworkElement=MSC01BSC01', u'FDN : NetworkElement=MSC01BSC02', u'', u'2 instance(s)']


class ReparentingUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.reparenting.raise_for_status')
    def test_send_post_request__success(self, _):
        user = Mock()
        user.post.return_value = Mock()
        send_post_request(user, 'test', {})
        self.assertEqual(1, user.post.call_count)

    @patch('enmutils_int.lib.reparenting.raise_for_status')
    def test_get_status_request__success(self, _):
        user = Mock()
        user.get.return_value = Mock()
        get_status_request(user, '1234')
        self.assertEqual(1, user.get.call_count)

    def test_build_base_station_json__success(self):
        result = build_base_station_json(BASE_STATIONS)
        self.assertDictEqual(result, {'baseStations': [{'fdn': BASE_STATIONS[0]}, {'fdn': BASE_STATIONS[1]}]})

    def test_build_base_station_json__adds_technology_type(self):
        result = build_base_station_json(BASE_STATIONS, technology_type=TECHOLOGY_TYPE)
        self.assertDictEqual(result, {'baseStations': [{'fdn': BASE_STATIONS[0]}, {'fdn': BASE_STATIONS[1]}],
                                      'technologyType': 'GSM'})

    def test_build_base_station_json__adds_target_ne(self):
        result = build_base_station_json(BASE_STATIONS, target_network_controller=TARGET_NE)
        self.assertDictEqual(result, {'baseStations': [{'fdn': BASE_STATIONS[0]}, {'fdn': BASE_STATIONS[1]}],
                                      'targetNetworkController': 'NetworkElement=BSC02'})

    def test_build_cell_json__success(self):
        result = build_cell_json(BASE_STATIONS_WITH_CELLS)
        self.assertDictEqual(result, {'baseStations': [{'cells': [CANDIDATES[0]], 'fdn': BASE_STATIONS[0]},
                                                       {'cells': [CANDIDATES[1]], 'fdn': BASE_STATIONS[1]}]})

    def test_build_cell_json__technology_type(self):
        result = build_cell_json(BASE_STATIONS_WITH_CELLS, technology_type=TECHOLOGY_TYPE)
        self.assertDictEqual(result, {'baseStations': [{'cells': [CANDIDATES[0]], 'fdn': BASE_STATIONS[0]},
                                                       {'cells': [CANDIDATES[1]], 'fdn': BASE_STATIONS[1]}],
                                      'technologyType': 'GSM'})

    def test_build_cell_json__target_ne(self):
        result = build_cell_json(BASE_STATIONS_WITH_CELLS, target_network_controller=TARGET_NE)
        self.assertDictEqual(result, {'targetNetworkController': 'NetworkElement=BSC02',
                                      'baseStations': [{'cells': [CANDIDATES[0]], 'fdn': BASE_STATIONS[0]},
                                                       {'cells': [CANDIDATES[1]], 'fdn': BASE_STATIONS[1]}]})

    def test_build_cell_json__msc_operations(self):
        result = build_cell_json(BASE_STATIONS_WITH_CELLS, include_mo_operations=False)
        self.assertDictEqual(result, {'baseStations': [{'cells': [CANDIDATES[0]], 'fdn': BASE_STATIONS[0]},
                                                       {'cells': [CANDIDATES[1]], 'fdn': BASE_STATIONS[1]}],
                                      'includeMscOperations': False})

    def test_build_cell_json__include_atrributes(self):
        result = build_cell_json(BASE_STATIONS_WITH_CELLS, include_attributes=True, target_cells=['REPARENTING=1', 'REPARENTING=2'])
        self.assertDictEqual(result, {'baseStations': [
            {'cells': [{'newName': '1', 'newLac': 100, 'candidateFdn': 'GeranCell=1'}], 'fdn': BASE_STATIONS[0]},
            {'cells': [{'newName': '2', 'newLac': 101, 'candidateFdn': 'GeranCell=2'}], 'fdn': BASE_STATIONS[1]}]})

    @patch('enmutils_int.lib.reparenting.validate_response', return_value=True)
    def test_get_bsc_network_elements__success(self, _):
        response, user = Mock(), Mock()
        response.get_output.return_value = BSCS
        user.enm_execute.return_value = response
        self.assertListEqual(['MSC01BSC01', 'MSC01BSC02'], get_bsc_network_elements(user))

    @patch('enmutils_int.lib.reparenting.validate_response', return_value=False)
    def test_get_bsc_network_elements__invalid_response(self, _):
        user = Mock()
        self.assertListEqual([], get_bsc_network_elements(user))

    @patch('enmutils_int.lib.reparenting.validate_response', side_effect=[True, True, True, False])
    def test_get_tg_mos__success(self, _):
        response, user = Mock(), Mock()
        response.get_output.return_value = G12TGS
        user.enm_execute.return_value = response
        g12tg_mos = get_tg_mos(user, NODE_IDS, {})
        self.assertDictEqual({u'Bts=1,G12Tg=16': [u'GeranCellM=1,GeranCell=1015046,ChannelGroup=0,',
                                                  u'GeranCell=1015047,ChannelGroup=0,',
                                                  u'GeranCell=1015048,ChannelGroup=0']}, g12tg_mos)

    @patch('enmutils_int.lib.reparenting.validate_response', return_value=True)
    def test_get_and_sort_geran_cells__success(self, _):
        user, response = Mock(), Mock()
        response.get_output.return_value = [u'FDN : ManagedElement=2,GeranCell=1',
                                            u'FDN : ManagedElement=2,GeranCell=2',
                                            u'FDN : ManagedElement=3,GeranCell=1',
                                            u'FDN : ManagedElement=4,GeranCell=1',
                                            u'', u'4 instance(s)']
        user.enm_execute.return_value = response
        self.assertDictEqual({u'2': [u'ManagedElement=2,GeranCell=1', u'ManagedElement=2,GeranCell=2'],
                              u'3': [u'ManagedElement=3,GeranCell=1'], u'4': [u'ManagedElement=4,GeranCell=1']},
                             get_and_sort_geran_cells(user))

    @patch('enmutils_int.lib.reparenting.validate_response', return_value=False)
    def test_get_and_sort_geran_cells__invalid_response(self, _):
        user = Mock()
        user.enm_execute.return_value = Mock()
        self.assertDictEqual({}, get_and_sort_geran_cells(user))

    def test_remove_missing_cells__success(self):
        result = remove_missing_cells(["ManagedElement=1,test=1,ChannelGroup=1",
                                       "ManagedElement=1,test=2,ChannelGroup=1"], {'1': ["ManagedElement=1,test=2"]})
        self.assertListEqual(['ManagedElement=1,test=2,ChannelGroup=1'], result)

    @patch('enmutils_int.lib.reparenting.validate_response', return_value=True)
    @patch('enmutils_int.lib.reparenting.log.logger.debug')
    def test_set_inter_ran_mobility_attribute__success(self, mock_debug, _):
        user = Mock()
        cells = ["Cell"] * 3
        set_inter_ran_mobility_attribute(user, cells, "on")
        user.enm_execute.assert_called_with("cmedit set Cell;Cell;Cell InterRanMobility prioCr:ON --force")
        mock_debug.assert_called_with("Set InterRanMobility prioCr for 3 cells to:: [ON] result:: True.")

    @patch('enmutils_int.lib.reparenting.log.logger.debug')
    def test_set_channel_group_active__success(self, mock_debug, *_):
        user = Mock()
        channel_groups = ["ManagedElement=1,test=1,ChannelGroup=0", "ManagedElement=1,test=2,ChannelGroup=0"]
        set_channel_group_active(user, channel_groups)
        user.enm_execute.assert_called_with("cmedit set ManagedElement=1,test=2,ChannelGroup=0 state=ACTIVE --force")
        mock_debug.assert_called_with("Successfully set the channelGroup to active state.")

    @patch('enmutils_int.lib.reparenting.log.logger.debug')
    def test_set_channel_group_active__log_error(self, *_):
        user = Mock()
        channel_groups = ["ManagedElement=1,test=1,ChannelGroup=0", "ManagedElement=1,test=2"]
        user.enm_execute.side_effect = Exception(EnmApplicationError)
        self.assertRaises(Exception, set_channel_group_active(user, channel_groups))

    def test_validate_response__valid(self):
        response = Mock()
        response.get_output.return_value = CHANNEL
        result = validate_response(response)
        self.assertEqual(result, True)

    def test_validate_response__zero_instance(self):
        response = Mock()
        response.get_output.return_value = [u'', u'0 instance(s)']
        result = validate_response(response)
        self.assertEqual(result, False)

    def test_validate_response__error(self):
        response = Mock()
        response.get_output.return_value = [u'Error: 4001']
        result = validate_response(response)
        self.assertEqual(result, False)

    def test_validate_response__no_response(self):
        result = validate_response(None)
        self.assertEqual(result, False)

    def test_validate_response__no_output(self):
        response = Mock()
        response.get_output.return_value = None
        result = validate_response(response)
        self.assertEqual(result, False)

    @patch('enmutils_int.lib.reparenting.time.sleep', return_value=0)
    @patch('enmutils_int.lib.reparenting.time.time', side_effect=[1, 2])
    @patch('enmutils_int.lib.reparenting.check_status_code', return_value=True)
    @patch('enmutils_int.lib.reparenting.get_status_request')
    def test_poll_for_completed_status__success(self, mock_get, *_):
        user, response = Mock(), Mock()
        response.status_code = 200
        response.json.return_value = {'cells': ['cell']}
        mock_get.return_value = response
        result = poll_for_completed_status(user, 'id', 3600)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(True, result)

    @patch('enmutils_int.lib.reparenting.time.sleep', return_value=0)
    @patch('enmutils_int.lib.reparenting.time.time', side_effect=[1, 2, 1799, 3700])
    @patch('enmutils_int.lib.reparenting.check_status_code', return_value=None)
    @patch('enmutils_int.lib.reparenting.get_status_request')
    def test_poll_for_completed_status__failure(self, mock_get, *_):
        user, response = Mock(), Mock()
        response.side_effect = Exception()
        response.status_code = 302
        mock_get.side_effect = [HTTPError(response=response), response]
        self.assertRaises(EnmApplicationError, poll_for_completed_status, user, 'id', 3600)
        self.assertEqual(2, mock_get.call_count)

    @patch('enmutils_int.lib.reparenting.time.sleep', return_value=0)
    @patch('enmutils_int.lib.reparenting.time.time', side_effect=[1, 2, 1799, 3700])
    @patch('enmutils_int.lib.reparenting.check_status_code', return_value=None)
    @patch('enmutils_int.lib.reparenting.get_status_request')
    def test_poll_for_completed_status__breaks_on_500_error(self, mock_get, *_):
        user, response = Mock(), Mock()
        response.side_effect = Exception()
        response.status_code = 500
        mock_get.side_effect = HTTPError(response=response)
        self.assertRaises(EnmApplicationError, poll_for_completed_status, user, 'id', 3600)
        self.assertEqual(1, mock_get.call_count)

    def test_check_status_code__success(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {}
        self.assertEqual(True, check_status_code(response))

    def test_check_status_code__raises_enm_application_error_empty_response(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'cells': [{}], 'operations': []}
        self.assertRaises(EnmApplicationError, check_status_code, response)

    def test_check_status_code__returns_none(self):
        response = Mock()
        response.status_code = 302
        response.json.return_value = {}
        self.assertIsNone(check_status_code(response))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
