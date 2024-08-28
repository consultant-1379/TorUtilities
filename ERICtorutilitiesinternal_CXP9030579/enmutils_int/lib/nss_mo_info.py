# ********************************************************************
# Name    : NSS MO Info
# Summary : Used by node pool manager during node allocation. Used as
#           part of node allocation if the profile requesting nodes,
#           has a cell cardinality value attribute, some profiles
#           fetch node cardinality files from each Netsim Host,
#           parses the files by node and stores locally to be read
#           at allocation time to select specific cell cardinalities
#           on the required nodes, can also fetch MO files if they
#           are available, only newer simulations have these files.
# ********************************************************************

import json

from enmutils.lib import filesystem, log
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib import simple_sftp_client
from enmutils_int.lib.network_mo_info import CARDINALITY_FILE, MO_FILE, group_mos_by_node

FILE_PATHS = {}
HOST_DATA = []


class NssMoInfo(object):

    BASE_PATH = "/netsim/netsimdir/{sim_name}/SimNetRevision"
    SUMMARY_FILE = "Summary_{sim_name}.csv"
    NETWORK_STATS_FILE = "NetworkStats.csv"  # BSC version of summary
    TOPOLOGY_FILE = "TopologyData.txt"
    UTRANCELL_FILE = "UtranCell.txt"
    SUPPORTED_NODE_TYPES = ["ERBS", "RNC", "BSC", "RadioNode"]
    TEMP_DIR = "/home/enmutils/simulation_data"
    UTRANCELL_KEY = "UtranCell="
    EUTRANCELLFDD_KEY = "EUtranCellFDD="

    MO_DATA = "MoData"
    MO_DATA_DIR = "{0}/{1}".format(BASE_PATH, MO_DATA)

    def __init__(self, grouped_nodes):
        """
        Init method

        :param grouped_nodes: Dictionary containing Key/Value pairing of Netsim/Nodes
        :type grouped_nodes: dict
        """
        self.data_dictionary = grouped_nodes
        self.user = 'netsim'
        self.password = self.user
        self.cardinality_values = {}
        self.parsed_mos = {}
        self.utrancell_values = {}

    def fetch_and_parse_netsim_simulation_files(self):
        """
        Retrieves the required files
        """
        log.logger.debug("Checking if files from NetSim hosts exist.")
        if not filesystem.does_file_exist(MO_FILE) or not filesystem.does_file_exist(CARDINALITY_FILE):
            log.logger.warn(
                "Cardinality files not present on deployment. Retrieving files from Netsims can take several hours "
                "depending on number of simulations and retrievable files.. "
                "\nThis is a one time operation. Please wait...")
            try:
                tq = ThreadQueue(self.data_dictionary.keys(), num_workers=len(self.data_dictionary.keys()),
                                 func_ref=self.build_file_path_dictionary, args=[self],
                                 task_join_timeout=5 * 60, task_wait_timeout=60 * 60)
                tq.execute()
                tq = ThreadQueue(FILE_PATHS.keys(), num_workers=len(FILE_PATHS.keys()),
                                 func_ref=self.fetch_simulation_files_from_simulation,
                                 args=[self], task_join_timeout=5 * 60, task_wait_timeout=120 * 60)
                tq.execute()
            except Exception as e:
                raise EnvironError(str(e))
            log.logger.warn("Completed retrieving files from NetSim hosts. Starting parsing of files...")
            self.parse_each_file_into_an_usable_format()
            self.write_data_to_json_file(self.parsed_mos, MO_FILE)
            self.write_data_to_json_file(self.cardinality_values, CARDINALITY_FILE)
            self.delete_download_files_directory()
            log.logger.warn("Completed parsing files retrieved from NetSim hosts.")

    def check_if_netsim_directories_exists(self, host, sim):
        """
        Check if the SimNet directory exists for the simulation and whether it is GSM or LTE

        :param host: NetSim host name
        :type host: str
        :param sim: Simulation name to check
        :type sim: str

        :return: Tuple containing booleans indicating if the directories exist
        :rtype: tuple
        """
        gsm_dir, lte_dir = False, False
        gsm_base = self.BASE_PATH.format(sim_name=sim).replace('SimNet', 'Simnet')
        gsm_dir = filesystem.does_remote_dir_exist(dir_path=gsm_base, host=host, user=self.user,
                                                   password=self.password)
        if not gsm_dir:
            lte_dir = filesystem.does_remote_dir_exist(dir_path=self.BASE_PATH.format(sim_name=sim), host=host,
                                                       user=self.user, password=self.password)
        return lte_dir, gsm_dir

    @staticmethod
    def build_file_path_dictionary(host, worker):
        """
        Create or append file paths to the list of file paths to be retrieved

        :param host: NetSim host name
        :type host: str
        :param worker: Instance object which will perform the various tasks required
        :type worker: `nss_mo_info.NssMoInfo`
        """
        log.logger.debug("Getting file paths for NetSim host {0}.".format(host))

        simulations = worker.get_all_simulations(worker.data_dictionary.get(host))
        for sim in simulations:
            lte_dir, gsm_dir = worker.check_if_netsim_directories_exists(host, sim)
            if not any([lte_dir, gsm_dir]):
                log.logger.debug("SimNet revision directory not found for simulation {0}.".format(host))
                continue
            elif gsm_dir:
                file_paths = ["{0}/{1}".format(worker.get_base_path(sim, gsm_dir=gsm_dir),
                                               worker.NETWORK_STATS_FILE)]
                if not filesystem.does_remote_file_exist(file_path=file_paths[0], host=host, user=worker.user,
                                                         password=worker.password):
                    log.logger.debug("File does not exist\t{1} on host\t{0}.".format(host, file_paths[0]))
                    continue
            else:
                file_paths = ["{0}/{1}".format(worker.get_base_path(sim), _) for _ in
                              [worker.TOPOLOGY_FILE, worker.UTRANCELL_FILE, worker.SUMMARY_FILE.format(sim_name=sim)] if
                              filesystem.does_remote_file_exist(file_path="{0}/{1}".format(
                                  worker.get_base_path(sim), _), host=host, user=worker.user, password=worker.password)]
            if file_paths:
                worker.add_file_to_file_path_dict(file_paths, host, sim)
        log.logger.debug("Completed getting file paths for NetSim host {0}.".format(host))

    @staticmethod
    def add_file_to_file_path_dict(file_paths, host, sim):
        """
        Add found file paths to the global list of file paths

        :param file_paths: List of file paths found on the host
        :type file_paths: list
        :param host: Host name to add to the dictionary of hosts with fetchable files
        :type host: str
        :param sim: Simulation name to add to the dictionary for sorting
        :type sim: str
        """
        global FILE_PATHS
        log.logger.debug("Adding total count of file paths\t[{0}] for host\t{1} and sim\t{2}".format(len(file_paths),
                                                                                                     host, sim))
        for file_path in file_paths:
            if host not in FILE_PATHS.keys():
                FILE_PATHS[host] = {}
            if sim not in FILE_PATHS.get(host).keys():
                FILE_PATHS[host][sim] = []
            log.logger.debug("Adding file path {0}, to list of retrievable file paths.".format(file_path))
            FILE_PATHS[host][sim].append(file_path)

    def get_base_path(self, sim, gsm_dir=False):
        """
        Update the base path because GSM directories are inconsistent with LTE directories

        :param sim: Simulation name to append to file path
        :type sim: str
        :param gsm_dir: Boolean flag indicating if the dir is simnet
        :type gsm_dir: bool

        :return: Path to the SimNetRevision directory
        :rtype: str
        """
        if gsm_dir:
            return self.BASE_PATH.format(sim_name=sim).replace('SimNet', 'Simnet')
        return self.BASE_PATH.format(sim_name=sim)

    @staticmethod
    def get_all_simulations(nodes):
        """
        Get a list of all of the simulations on the supplied nodes

        :param nodes: List of `enm_node.Node` instances
        :type nodes: list

        :return: List of simulations
        :rtype: list
        """
        log.logger.debug("Getting list of all simulations for supplied nodes.")
        all_simulations = []
        for node in nodes:
            all_simulations.append(node.simulation)
        log.logger.debug("Completed getting list of all simulations for supplied nodes.")
        return list(set(all_simulations))

    def get_file_paths(self, sim, host):
        """
        Get the available file paths on the NetSim host

        :param sim: Simulation directory to check for available files
        :type sim: str
        :param host: Netsim host to connect to and query
        :type host: str

        :return: List of files to download
        :rtype: list
        """
        log.logger.debug("Determining file paths likely to be available on simulation.")
        lte_file_paths = []
        if filesystem.does_remote_dir_exist(self.MO_DATA_DIR.format(sim_name=sim), host=host, user=self.user,
                                            password=self.password):
            log.logger.debug("MoData directory found, will use available files of type '.mo' .")
            file_names = filesystem.get_files_in_remote_directory(self.MO_DATA_DIR.format(sim_name=sim), host=host,
                                                                  user=self.user, password=self.password,
                                                                  ends_with=".mo")
            lte_file_paths = ["{0}/{1}".format(self.MO_DATA, file_name) for file_name in file_names]
        log.logger.debug("Completed determining file paths likely to be available on simulation.")
        return lte_file_paths

    @staticmethod
    def fetch_simulation_files_from_simulation(host, worker):
        """
        Downloads the remote file(s) data to a local directory
        """
        log.logger.debug("Downloading remote file(s) to local directory from NetSim host:: [{0}].".format(host))
        global HOST_DATA
        for sim in FILE_PATHS.get(host).keys():
            local_dir = "{0}/{1}/{2}".format(worker.TEMP_DIR, host, sim)
            if not filesystem.does_dir_exist(local_dir):
                filesystem.create_dir(local_dir)
            for file_path in FILE_PATHS.get(host).get(sim):
                destination = "{0}/{1}".format(local_dir, file_path.split("/")[-1])
                simple_sftp_client.download_file(file_path, destination, host, worker.user, worker.password)
                HOST_DATA.append(destination)
        log.logger.debug("Completed downloading remote file(s) to local directory from NetSim host:: [{0}]."
                         .format(host))

    def parse_each_file_into_an_usable_format(self):
        """
        Reads each file into an usable format
        """
        log.logger.debug("Starting parse of files, into usable format.")
        for host_data_file in HOST_DATA:
            file_data = filesystem.get_lines_from_file(host_data_file)
            if host_data_file.endswith(".mo"):
                self.parse_node_mo_file(file_data)
            elif "Network" in host_data_file and host_data_file.endswith(".csv"):
                self.parse_network_summary_file(file_data)
            elif host_data_file.endswith(".csv"):
                self.parse_summary_file(file_data)
            elif "utrancell" in host_data_file.lower():
                self.utrancell_values.update(group_mos_by_node(file_data))
            else:
                self.parse_topology_file(file_data)
        log.logger.debug("Completed parsing of files, into usable format.")

    def parse_summary_file(self, lines):
        """
        Parses the .CSV summary files into a sorted dictionary

        :param lines: Lines read from the supplied file
        :type lines: list
        """
        log.logger.debug("Parsing summary file.")
        mos = lines[0].split(",")[1:-1]
        for line in lines[1:-1]:
            mo_count = line.split(",")[1:-1]
            node_name = line.split(",")[0]
            if node_name not in self.cardinality_values.keys():
                self.cardinality_values[node_name] = {}
            for index, mo in enumerate(mos):
                self.cardinality_values[node_name][mo] = mo_count[index]
        log.logger.debug("Completed parsing summary file.")

    def parse_network_summary_file(self, lines):
        """
        Parses the GSM .CSV summary files into a sorted dictionary

        :param lines: Lines read from the supplied file
        :type lines: list

        NumOfGsmCells = GeranCell
        GsmIntraCellRelations = GeranCellRelation
        UtranRelations = UtranCellRelation
        NumOfG2Bts = G31Tg
        NumOfG1Bts = G12Tg
        ExternalGsmRelations + GsmExternalRelations = ExternalGeranCellRelation
        """
        log.logger.debug("Parsing network summary file.")
        external_rel = "ExternalGeranCellRelation"
        mo_mappings = {
            "NumOfGsmCells": "GeranCell",
            "GsmIntraCellRelations ": "GeranCellRelation",
            "UtranRelations": "UtranCellRelation",
            "NumOfG2Bts": "G31Tg",
            "NumOfG1Bts": "G12Tg",
            "ExternalUtranCells": "ExternalUtranCell",
            "ExternalGsmRelations": external_rel,
            "GsmExternalRelations": external_rel
        }
        external_value = 0
        for line in lines:
            node_name = line.split("NodeName=")[-1].split(";")[0]
            mo_name = line.split(";")[-1].split("=")[0]
            mo_count = int(line.split(";")[-1].split("=")[-1])

            if node_name not in self.cardinality_values.keys():
                self.cardinality_values[node_name] = {}
            if mo_name in ["ExternalGsmRelations", "GsmExternalRelations"]:
                if not external_value:
                    external_value = mo_count
                    continue
                external_value += mo_count
                self.cardinality_values[node_name][mo_mappings.get(mo_name)] = external_value
                external_value = 0
            else:
                self.cardinality_values[node_name][mo_mappings.get(mo_name)] = mo_count
        log.logger.debug("Completed parsing network summary file.")

    def parse_topology_file(self, lines):
        """
        Parses the Topology file into a sorted dictionary

        :param lines: Lines read from the supplied file
        :type lines: list
        """
        log.logger.debug("Parsing topology file.")
        for line in lines:
            if self.EUTRANCELLFDD_KEY in line and not line.startswith("#"):
                node_name = line.split(self.EUTRANCELLFDD_KEY)[-1].split(",")[0].split('-')[0]
                mo_name = line.split("=")[-2].split(",")[-1]
                if node_name not in self.parsed_mos.iterkeys():
                    self.parsed_mos[node_name] = {}
                if mo_name not in self.parsed_mos.get(node_name).iterkeys():
                    self.parsed_mos[node_name][mo_name] = []
                self.parsed_mos[node_name][mo_name].append(line)
        log.logger.debug("Completed parsing topology file.")

    def parse_node_mo_file(self, lines):
        """
        Parse the node and MO values from the .mo files

        :param lines: Lines read from the supplied file
        :type lines: list
        """
        log.logger.debug("Parsing node MO file.")
        parent_key = "parent"
        identity_key = "identity"
        mo_type_key = "moType"
        for index, line in enumerate(lines):
            try:
                if parent_key in line and identity_key in lines[index + 1] and mo_type_key in lines[index + 2]:
                    # If the parent, identity and mo type are available, build the MO
                    parent_mo = line.split(parent_key)[-1].strip()
                    identity = lines[index + 1].split(identity_key)[-1].strip()
                    mo_name = lines[index + 2].split(mo_type_key)[-1].strip()
                    mo_value = "{0},{1}={2}".format(parent_mo, mo_name, identity).replace('\"', '')
                    node_name = parent_mo.split("ManagedElement=")[-1].split(",")[0]

                    if node_name not in self.parsed_mos.iterkeys():
                        self.parsed_mos[node_name] = {}
                    if mo_name not in self.parsed_mos.get(node_name).iterkeys():
                        self.parsed_mos[node_name][mo_name] = []
                    self.parsed_mos[node_name][mo_name].append(mo_value)
            except IndexError:
                log.logger.debug("Index out range, not enough data to complete an MO from line {0}.".format(line))
                continue
        log.logger.debug("Completed parsing node MO file.")

    @staticmethod
    def write_data_to_json_file(data, file_path):
        """
        Write the supplied data to the supplied file path as a JSON str

        :param data: Object to be converted to a JSON string and written to file
        :type data: object
        :param file_path: File path to write the data to
        :type file_path: str
        """
        log.logger.debug("Writing data to json file.")
        try:
            filesystem.write_data_to_file(data=json.dumps(data), output_file=file_path, log_to_log_file=False)
            log.logger.debug("Completed writing data to json file.")
        except Exception as e:
            log.logger.debug("Failed to write to file {0}, error encountered: {1}.".format(file_path, str(e)))

    def delete_download_files_directory(self):
        """
        Delete the temporary directory
        """
        log.logger.debug("Starting deletion of temporary directory.")
        try:
            filesystem.remove_dir(self.TEMP_DIR)
            log.logger.debug("Successfully deleted temporary directory.")
        except Exception as e:
            log.logger.debug("Failed to delete temporary directory, error encountered: {0}.".format(str(e)))
