#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.nss_mo_info import NssMoInfo
from enmutils_int.lib import nss_mo_info
from testslib import unit_test_utils


SUMMARY_SAMPLE = [("NodeName,EUtranCellFDD,EUtranCellRelation,EUtranFreqRelation,ExternalENodeBFunction,"
                   "ExternalEUtranCellFDD,UtranCellRelation,UtranFreqRelation,ExternalUtranCellFDD,GeranCellRelation,"
                   "GeranFreqGroupRelation,GeranFrequency,TermPointToENB,SectorCarrier,RetSubUnit,TotalMO"),
                  "LTE13ERBS00001,12,5081,108,512,722,792,72,36,380,20,320,512,12,24,14665",
                  "LTE13ERBS00001,12,5081,108,512,722,792,72,36,380,20,320,512,12,24,14665",
                  "Total,240,120518,2160,40960,49293,15840,1440,2880,2865,292,2737,40960,363,356,691633"]

TOPOLOGY_SAMPLE = ["#########################################################",
                   "# TOPOLOGY DATA FOR LTEJ2100-limx80-60K-FDD-LTE13",
                   "#########################################################",
                   "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE13ERBS00001-1",
                   "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE13ERBS00002-2",
                   ("ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE13ERBS00001-1,EUtranFreqRelation=7,"
                    "EUtranCellRelation=733"),
                   ("ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE13ERBS00001-1,EUtranFreqRelation=7,"
                    "EUtranCellRelation=733"), "ManagedElement=1,ENodeBFunction=1,TermPointToMme=8",
                   "ManagedElement=1,ENodeBFunction=1,TermPointToMme=9"]

DEFAULT_FILES = ['TopologyData.txt', 'UtranCell.txt', 'Summary_sim.csv', 'NetworkStats.csv']

MO_FILE_SAMPLE = [('parent "ComTop:ManagedElement=LTE07dg2ERBS00072,Lrat:ENodeBFunction=1,Lrat:EUtraNetwork=1,'
                   'Lrat:ExternalENodeBFunction=LTE10ERBS00002"'), 'identity "1"', 'moType Lrat:TermPointToENB',
                  'exception none', 'nrOfAttributes 20', '"administrativeState" Integer 0',
                  ('parent "ComTop:ManagedElement=LTE07dg2ERBS00072,Lrat:ENodeBFunction=1,Lrat:EUtraNetwork=1,Lrat:'
                   'ExternalENodeBFunction=LTE13ERBS00061"'), 'identity "1"', 'moType Lrat:TermPointToENB',
                  ('parent "ComTop:ManagedElement=LTE07dg2ERBS00072,Lrat:ENodeBFunction=1,Lrat:EUtraNetwork=1,'
                   'Lrat:ExternalENodeBFunction=LTE11dg2ERBS00046"'), 'identity "1"']

NETWORK_STATS_SAMPLE = ["NodeName=MSC07BSC13;NumOfGsmCells=200", "NodeName=MSC07BSC13;NumOfG1Bts=33",
                        "NodeName=MSC07BSC13;NumOfG2Bts=100", "NodeName=MSC07BSC13;GsmInternalCellRelations=204",
                        "NodeName=MSC07BSC13;GsmIntraCellRelations=2600", "NodeName=MSC07BSC13;ExternalUtranCells=200",
                        "NodeName=MSC07BSC13;UtranRelations=1000", "NodeName=MSC07BSC13;GsmExternalRelations=800",
                        "NodeName=MSC07BSC13;ExternalGsmRelations=600",
                        "NodeName=MSC07BSC14;GsmInternalCellRelations=204"]


class NSSMoInfoUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.nss_info = NssMoInfo({"netsim": ["Node1", "Node2"]})

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.nss_mo_info.ThreadQueue.execute')
    def test_fetch_and_parse_netsim_simulation_files__skips_fetch_if_files_exist(self, mock_execute, _):
        self.nss_info.fetch_and_parse_netsim_simulation_files()
        self.assertEqual(0, mock_execute.call_count)

    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_file_exist', side_effect=[True, False])
    @patch('enmutils_int.lib.nss_mo_info.ThreadQueue.__init__', return_value=None)
    @patch('enmutils_int.lib.nss_mo_info.ThreadQueue.execute')
    def test_fetch_and_parse_netsim_simulation_files__raises_environ_error(self, mock_execute, *_):
        mock_execute.side_effect = AttributeError("Error")
        self.assertRaises(EnvironError, self.nss_info.fetch_and_parse_netsim_simulation_files)

    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_file_exist', side_effect=[False, False])
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.write_data_to_json_file')
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.write_data_to_json_file')
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.parse_each_file_into_an_usable_format')
    @patch('enmutils_int.lib.nss_mo_info.ThreadQueue.__init__', return_value=None)
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.delete_download_files_directory')
    @patch('enmutils_int.lib.nss_mo_info.ThreadQueue.execute', return_value=None)
    def test_fetch_and_parse_netsim_simulation_files__success(self, mock_execute, mock_delete_directories, *_):
        self.nss_info.fetch_and_parse_netsim_simulation_files()
        self.assertEqual(2, mock_execute.call_count)
        self.assertEqual(1, mock_delete_directories.call_count)

    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.fetch_simulation_files_from_simulation',
           side_effect=Exception("error"))
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.build_file_path_dictionary')
    def test_get_netsim_simulation_files_raises_environ_error(self, *_):
        self.nss_info.data_dictionary = {"host": [], "host1": []}
        self.assertRaises(EnvironError, self.nss_info.fetch_and_parse_netsim_simulation_files)

    def test_get_base_path(self):
        expected = "/netsim/netsimdir/sim/SimNetRevision"
        self.assertEqual(expected, self.nss_info.get_base_path(sim="sim"))
        expected = "/netsim/netsimdir/sim/SimnetRevision"
        self.assertEqual(expected, self.nss_info.get_base_path(sim="sim", gsm_dir=True))

    def test_get_all_simulations(self):
        node, node1, node2 = Mock(), Mock(), Mock()
        node.simulation, node1.simulation, node2.simulation = "sim", "sim", "sim1"
        self.assertListEqual(sorted(["sim", "sim1"]), sorted(self.nss_info.get_all_simulations([node, node1, node2])))

    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_remote_dir_exist', return_value=False)
    @patch('enmutils_int.lib.nss_mo_info.log.logger.debug')
    def test_get_file_paths(self, *_):
        result = self.nss_info.get_file_paths("sim", "host")
        self.assertListEqual([], result)

    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_remote_dir_exist', return_value=True)
    @patch('enmutils_int.lib.nss_mo_info.filesystem.get_files_in_remote_directory', return_value=["LTE01", "LTE02"])
    @patch('enmutils_int.lib.nss_mo_info.log.logger.debug')
    def test_get_file_paths_uses_mo_data_directory(self, mock_debug, *_):
        result = self.nss_info.get_file_paths("sim", "host")
        expected = ['MoData/LTE01', 'MoData/LTE02']
        mock_debug.assert_any_call("MoData directory found, will use available files of type '.mo' .")
        self.assertListEqual(expected, result)

    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_dir_exist')
    def test_fetch_simulation_files_from_simulation_no_paths(self, mock_does_dir_exist):
        nss_mo_info.FILE_PATHS = {"host": {}}
        self.nss_info.fetch_simulation_files_from_simulation("host", self.nss_info)
        self.assertEqual(0, mock_does_dir_exist.call_count)

    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_dir_exist', side_effect=[False, True])
    @patch('enmutils_int.lib.nss_mo_info.filesystem.create_dir')
    @patch('enmutils_int.lib.nss_mo_info.simple_sftp_client.download_file')
    def test_fetch_simulation_files_from_simulation(self, mock_download, *_):
        nss_mo_info.FILE_PATHS = {"host": {"sim": ["/tmp/file"], "sim1": ["/tmp/file"]}}
        self.nss_info.fetch_simulation_files_from_simulation("host", self.nss_info)
        self.assertEqual(2, mock_download.call_count)

    @patch('enmutils_int.lib.nss_mo_info.filesystem.get_lines_from_file')
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.parse_node_mo_file')
    @patch('enmutils_int.lib.nss_mo_info.group_mos_by_node')
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.parse_network_summary_file')
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.parse_topology_file')
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.parse_summary_file')
    def test_parse_each_file_into_an_usable_format(self, mock_summary, mock_topology, mock_network_stats,
                                                   mock_group_mos, mock_parse_mo_file, *_):
        nss_mo_info.HOST_DATA = ["Summary.csv", "UtranCell.txt", "TopologyData.txt", "LTE01.mo", "NetworkStats.csv"]
        self.nss_info.parse_each_file_into_an_usable_format()
        self.assertEqual(1, mock_summary.call_count)
        self.assertEqual(1, mock_topology.call_count)
        self.assertEqual(1, mock_network_stats.call_count)
        self.assertEqual(1, mock_group_mos.call_count)
        self.assertEqual(1, mock_parse_mo_file.call_count)

    def test_parse_summary_file(self):
        self.nss_info.parse_summary_file(SUMMARY_SAMPLE)
        expected = {'LTE13ERBS00001': {'RetSubUnit': '24', 'ExternalEUtranCellFDD': '722', 'EUtranCellFDD': '12',
                                       'ExternalUtranCellFDD': '36', 'UtranCellRelation': '792',
                                       'EUtranFreqRelation': '108', 'SectorCarrier': '12', 'TermPointToENB': '512',
                                       'GeranFrequency': '320', 'UtranFreqRelation': '72', 'GeranCellRelation': '380',
                                       'EUtranCellRelation': '5081', 'GeranFreqGroupRelation': '20',
                                       'ExternalENodeBFunction': '512'}}
        self.assertDictEqual(self.nss_info.cardinality_values, expected)

    def test_parse_network_summary_file(self):
        self.nss_info.parse_network_summary_file(NETWORK_STATS_SAMPLE)
        expected = {'MSC07BSC14': {None: 204},
                    'MSC07BSC13': {'UtranCellRelation': 1000, 'G12Tg': 33, 'G31Tg': 100, None: 2600, 'GeranCell': 200,
                                   'ExternalUtranCell': 200, 'ExternalGeranCellRelation': 1400}}
        self.assertDictEqual(self.nss_info.cardinality_values, expected)

    def test_parse_topology_file(self):
        self.nss_info.parse_topology_file(TOPOLOGY_SAMPLE)
        expected_keys = ['LTE13ERBS00001', 'LTE13ERBS00002']
        expected_mos = ['EUtranCellFDD', 'EUtranCellRelation']
        returned_mos = [key for value in self.nss_info.parsed_mos.itervalues() for key in value.keys()]
        self.assertListEqual(self.nss_info.parsed_mos.keys(), expected_keys)
        self.assertTrue(set(returned_mos).issuperset(expected_mos))

    @patch('enmutils_int.lib.nss_mo_info.log.logger.debug')
    def test_parse_node_mo_file(self, mock_debug):
        expected = ('ComTop:ManagedElement=LTE07dg2ERBS00072,Lrat:ENodeBFunction=1,Lrat:EUtraNetwork=1,Lrat:'
                    'ExternalENodeBFunction=LTE10ERBS00002,Lrat:TermPointToENB=1')
        self.nss_info.parse_node_mo_file(MO_FILE_SAMPLE)
        mock_debug.assert_any_call("Index out range, not enough data to complete an MO from line parent"
                                   " \"ComTop:ManagedElement=LTE07dg2ERBS00072,Lrat:ENodeBFunction=1,"
                                   "Lrat:EUtraNetwork=1,Lrat:ExternalENodeBFunction=LTE11dg2ERBS00046\".")
        mo = list(self.nss_info.parsed_mos.get("LTE07dg2ERBS00072").get("Lrat:TermPointToENB"))[0]
        self.assertEqual(expected, mo)

    @patch('enmutils_int.lib.nss_mo_info.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.nss_mo_info.log.logger.debug')
    def test_write_data_to_json_file(self, mock_debug, _):
        data = {"Node1": {"Mo1": ["Id1", "Id2"]}}
        self.nss_info.write_data_to_json_file(data, "test1")
        mock_debug.assert_called_with("Completed writing data to json file.")

    @patch('enmutils_int.lib.nss_mo_info.filesystem.write_data_to_file', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.nss_mo_info.log.logger.debug')
    def test_write_data_to_json_file_logs_exception(self, mock_debug, _):
        data = {"Node1": {"Mo1": ["Id1", "Id2"]}}
        self.nss_info.write_data_to_json_file(data, "test1")
        mock_debug.assert_called_with("Failed to write to file test1, error encountered: Error.")

    @patch('enmutils_int.lib.nss_mo_info.filesystem.remove_dir')
    @patch('enmutils_int.lib.nss_mo_info.log.logger.debug')
    def test_delete_download_files_directory(self, mock_debug, _):
        self.nss_info.delete_download_files_directory()
        mock_debug.assert_called_with("Successfully deleted temporary directory.")

    @patch('enmutils_int.lib.nss_mo_info.filesystem.remove_dir', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.nss_mo_info.log.logger.debug')
    def test_delete_download_files_directory_logs_exception(self, mock_debug, _):
        self.nss_info.delete_download_files_directory()
        mock_debug.assert_called_with("Failed to delete temporary directory, error encountered: Error.")

    def test_add_file_to_file_path_dict__adds_correct_host_and_sim(self):
        paths_hosts_sims = [(["path1"], "host", "sim"), (["path2"], "host", "sim1"), (["path2"], "host", "sim")]
        for _ in paths_hosts_sims:
            self.nss_info.add_file_to_file_path_dict(_[0], _[1], _[2])
        self.assertDictEqual({'host': {'sim1': ['path2'], 'sim': ['path1', 'path2']}}, nss_mo_info.FILE_PATHS)

    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_remote_dir_exist', return_value=True)
    def test_check_if_netsim_directories_exists__only_checks_gsm(self, mock_dir_exist):
        self.assertFalse(all(self.nss_info.check_if_netsim_directories_exists("host", "sim")))
        self.assertEqual(1, mock_dir_exist.call_count)

    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_remote_dir_exist', side_effect=[False, True])
    def test_check_if_netsim_directories_exists__only_checks_lte(self, mock_dir_exist):
        self.assertFalse(all(self.nss_info.check_if_netsim_directories_exists("host", "sim")))
        self.assertEqual(2, mock_dir_exist.call_count)

    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.get_all_simulations', return_value=["sim"])
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.check_if_netsim_directories_exists',
           return_value=(False, False))
    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_remote_file_exist', side_effect=[False, True])
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.add_file_to_file_path_dict')
    def test_build_file_path_dictionary__skips_add_if_no_directories(self, mock_add_file_path, *_):
        self.nss_info.build_file_path_dictionary("host", self.nss_info)
        self.assertEqual(0, mock_add_file_path.call_count)

    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.get_all_simulations', return_value=["sim", "sim1"])
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.check_if_netsim_directories_exists',
           side_effect=[(False, True), (False, True)])
    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_remote_file_exist', side_effect=[False, True])
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.add_file_to_file_path_dict')
    def test_build_file_path_dictionary__skips_empty_gsm_directory(self, mock_add_file_path, *_):
        self.nss_info.build_file_path_dictionary("host", self.nss_info)
        self.assertEqual(1, mock_add_file_path.call_count)

    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.get_all_simulations', return_value=["sim"])
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.check_if_netsim_directories_exists',
           return_value=(True, False))
    @patch('enmutils_int.lib.nss_mo_info.filesystem.does_remote_file_exist', return_value=False)
    @patch('enmutils_int.lib.nss_mo_info.NssMoInfo.add_file_to_file_path_dict')
    def test_build_file_path_dictionary__adds_lte_file_paths_if_files_exist(self, mock_add_file_path, *_):
        self.nss_info.build_file_path_dictionary("host", self.nss_info)
        self.assertEqual(0, mock_add_file_path.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
