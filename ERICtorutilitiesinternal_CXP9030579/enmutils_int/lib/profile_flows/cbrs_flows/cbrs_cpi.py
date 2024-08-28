import re

import time
import random

import pexpect
from enmutils.lib import log, cache, filesystem
from enmutils.lib.exceptions import EnvironError, EnmApplicationError, NoOuputFromScriptEngineResponseError
from enmutils.lib.shell import run_local_cmd
from enmutils_int.lib.simple_sftp_client import download, upload
from enmutils_int.lib.services.deploymentinfomanager_adaptor import update_pib_value
from retrying import retry

CBRS_DEFAULT_DIR = "/home/enmutils/cbrs/"
PATH_CPI_CSV = CBRS_DEFAULT_DIR + "CpiSortedData.csv"
PRIVATE_KEY = "CPI_private_key.pem"
PATH_PRIVATE_KEY = CBRS_DEFAULT_DIR + PRIVATE_KEY
CBRS_JAR_DIR = "/home/enmutils/cbrs/opt/ericsson/ERICcpisigningtool_CXP9035592/"
NO_HOST_CHECK = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
CHECK_OLD_OR_NEW_6488 = "cmedit get * SectorCarrier.maxAllowedEirpPSD"
JAR_FILE_EXPECTED = "cpi-signing-tool-2.18.12.jar"
DEVICE_2208 = "2208"
DEVICE_4408 = "4408"
DEVICE_NR_4408 = "NR_4408"
DEVICE_6488 = "6488"
DEVICE_6488_NEW = "6488_NEW"
DEVICE_6488_OLD = "6488_OLD"
DEVICE_RADIODOT = "RadioDot"
DEVICE_PASSIVE_DAS_4408 = "PassiveDas_4408"

PRODUCT_ID_DICT = {DEVICE_6488: "KRD 901 160/11", DEVICE_4408: "KRC 161 746/1", DEVICE_NR_4408: "KRC 161 746/1",
                   DEVICE_2208: "KRC 161 711/1", DEVICE_RADIODOT: "KRY 901 385/1"}

ANTENNA_GAIN_DICT = {DEVICE_6488_NEW: ",0,AGL,FALSE,0,0,0,0,11,44.5,0,Ericsson_Antenna",
                     DEVICE_6488_OLD: ",0,AGL,FALSE,0,0,0,0,17,44.5,0,Ericsson_Antenna",
                     DEVICE_4408: ",0,AGL,FALSE,0,0,0,0,12.5,47,0,Ericsson_Antenna",
                     DEVICE_NR_4408: ",0,AGL,FALSE,0,0,0,0,12.5,47,0,Ericsson_Antenna",
                     DEVICE_2208: ",0,AGL,FALSE,0,0,0,0,12,47,0,Ericsson_Antenna",
                     DEVICE_RADIODOT: ",0,AGL,TRUE,0,0,0,0,3,25,0,Ericsson_Antenna"}
SERVER_SOURCE_IP = "sfts.seli.gic.ericsson.se"
PKG_SVR = {'uname': 'APTUSER', 'upass': r"]~pR:'Aw6cwpJR4dDY$k85\t", 'file_path': '/enmcisftp/Cbrs_private_key'}


@retry(retry_on_exception=lambda e: isinstance(e, EnvironError), wait_fixed=30000, stop_max_attempt_number=3)
def generic_pexpect_for_cpi_signing(child):
    """
    Generic pexpect operations for signing from Physical or Vio deployment
    :param child: pexpect.spawn
    :type child: pexpect.spawn
    :raises EnvironError: If any of the expected returns a non 0 integer an EnvironError will be raised
    """
    log.logger.debug("Inside Generic pexpect operations function")
    child.sendline("cd {0}".format(CBRS_JAR_DIR))
    child.sendline("cd {0}".format(CBRS_JAR_DIR))
    child.sendline("java -jar {0}".format(JAR_FILE_EXPECTED))
    return_1 = child.expect(["Enter", pexpect.EOF, pexpect.TIMEOUT], timeout=60)
    child.sendline("12345")
    return_2 = child.expect(["Enter your cpiName:", pexpect.EOF, pexpect.TIMEOUT])
    child.sendline("BladeRunner")
    return_3 = child.expect(["Enter the absolute path ", pexpect.EOF, pexpect.TIMEOUT])
    child.sendline(PATH_CPI_CSV)
    return_4 = child.expect(
        ["Enter the absolute path to your private key file:", pexpect.EOF, pexpect.TIMEOUT])
    child.sendline(PATH_PRIVATE_KEY)
    return_5 = child.expect(["Enter the absolute path", pexpect.EOF, pexpect.TIMEOUT])
    child.sendline("")
    return_6 = child.expect(["Enter a file name", pexpect.EOF, pexpect.TIMEOUT])
    child.sendline("CPI_SignedData")
    return_7 = child.expect(["Output CSV File:", pexpect.EOF, pexpect.TIMEOUT])
    child.sendline("y")
    time.sleep(20)
    return_8 = child.expect(["Output CSV file generated", pexpect.EOF, pexpect.TIMEOUT])
    return_list = [return_1, return_2, return_3, return_4, return_5, return_6, return_7, return_8]
    for return_value in return_list:
        if return_value != 0:
            raise EnvironError(
                "Failed to sign data, A return value did no return as expected. All values should be 0, "
                "Return values are {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}".format(return_1, return_2, return_3,
                                                                                  return_4, return_5, return_6,
                                                                                  return_7, return_8))
    log.logger.debug("Correctly signed data")


@retry(retry_on_exception=lambda e: isinstance(e, EnvironError), wait_fixed=30000, stop_max_attempt_number=3)
def rm_cpi_file_from_scripting_vm(child):
    """
    Removes the CPI_SignedData from the scripting vm on teardown
    :param child: pexpect.spawn instance
    :type child: Obj
    :raises EnvironError: If unexpected output when removing the CPI_SignedData file
    """
    log.logger.debug("Removing CPI_SignedData file on Teardown")
    child.sendline("rm -f CPI_SignedData")
    expected = child.expect(["administrator@", pexpect.EOF, pexpect.TIMEOUT])
    if expected == 0:
        log.logger.debug("Successfully cleaned up files and cleared cbrs_cpi db on scripting cluster")
    else:
        raise EnvironError("Expected to be prompted for 'administrator@' after cpi file has been deleted")


class CbrsCpi(object):

    def __init__(self):
        self.old_new_6488_dict = {DEVICE_6488_OLD: [], DEVICE_6488_NEW: []}
        self.long_lat_dict = {}
        self.serial_number_dict = {}
        self.fcc_id_dict = {}
        self.cpi_data_list = []

    def execute_cpi_flow(self, scripting_vms, device_type, product_data_dict, used_nodes, rf_branch_count_dict, user):
        """
        Creating a formated Data to Sign it for the cbrs profile
        :param scripting_vms: list of scripting vms for deployment
        :type scripting_vms: list
        :param device_type: Dictionary of device types and node ids as list of values
        :type device_type: Dict
        :param product_data_dict: node_ids are keys and corresponding product data are values
        :type product_data_dict: dict
        :param used_nodes: list of all used node ids
        :type used_nodes: list
        :param rf_branch_count_dict: dictionary of rf branches with nodes
        :type rf_branch_count_dict: dict
        :param user: user object
        :type user: `enmutils.enm_user_2`
        """
        scripting_vm = random.choice(scripting_vms)
        log.logger.debug("Starting the Creation of CPI signed Data")
        self.check_jar_file_exists()
        self.check_private_key_exists()
        self.replace_product_number_with_fcc_ids(product_data_dict)
        self.get_node_location(product_data_dict, used_nodes)
        self.get_node_serial_numbers(product_data_dict, used_nodes)
        self.cmedit_check_max_allowed_eirp_for_all_nodes(user, device_type)
        self.build_lines_for_cpi_file(used_nodes, device_type, rf_branch_count_dict)
        self.creating_unsigned_csv_file()
        self.sign_cpi_csv_file()
        self.put_signed_csv_file_to_scripting_cluster(scripting_vm)
        self.import_signed_csv_file_to_db(scripting_vm)
        if cache.is_enm_on_cloud_native():
            log.logger.debug("No pib values to be set on cENM")
        else:
            self.set_cpi_registration_pib_values()

    @staticmethod
    def check_jar_file_exists():
        """
        Checks if the jar files is present on the deployment.
        :raises EnvironError : raises an error if it encounters issues downloading the jar or extracting the rpm
        """
        log.logger.debug("Checking Jar file exists")
        if not filesystem.does_file_exist(CBRS_JAR_DIR + JAR_FILE_EXPECTED):
            log.logger.debug("Jar file not present on the deployment, Now Downloading it")
            run_local_cmd(
                "wget https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/content/repositories/releases/com/ericsson/oss/services/domainproxy/ERICcpisigningtool_CXP9035592/2.18.12/ERICcpisigningtool_CXP9035592-2.18.12.rpm -P {0} && rpm2cpio {0}ERICcpisigningtool_CXP9035592-2.18.12.rpm | (cd /home/enmutils/cbrs; cpio -idmv)".format(
                    CBRS_DEFAULT_DIR))
            if filesystem.does_file_exist(CBRS_JAR_DIR + JAR_FILE_EXPECTED):
                log.logger.debug("Jar downloaded and rpm extracted correctly")
            else:
                raise EnvironError("Jar failed to download and extract")
        else:
            log.logger.debug("Jar is present on the deployment")

    @staticmethod
    def check_private_key_exists():
        """
        Checks If private key is present at /home/enmutils/cbrs/  If not it will import
        :raises EnvironError: raises if it encounters issues downloading the private key from ftp server
        """
        log.logger.debug("Checking if Private key is present for cbrs cpi functionality")
        if not filesystem.does_file_exist(CBRS_DEFAULT_DIR + PRIVATE_KEY):
            log.logger.debug("Private key is not present for cbrs cpi functionality, Downloading NOW")
            try:
                download(SERVER_SOURCE_IP, PKG_SVR.get('uname'), PKG_SVR.get('upass'),
                         "{0}/{1}".format(PKG_SVR.get('file_path'), PRIVATE_KEY),
                         "{0}{1}".format(CBRS_DEFAULT_DIR, PRIVATE_KEY))
                log.logger.debug("Successfully downloaded private key")
            except Exception as e:
                raise EnvironError("Unable to download file: {0}.".format(e.message))
        else:
            log.logger.debug("Private key is present for cbrs cpi functionality")

    def replace_product_number_with_fcc_ids(self, product_data_dict):
        """
        Replacing the product number with serial numbers
        :param product_data_dict: dictionary of all product data split by FDN
        :type product_data_dict: dict
        """
        log.logger.debug("Getting the fccIds for each node id ")
        for key, value in product_data_dict.items():
            if PRODUCT_ID_DICT.get(DEVICE_6488) in str(value) and key not in self.fcc_id_dict.keys():
                self.fcc_id_dict[key] = 'TA8BKRD901160'
            elif PRODUCT_ID_DICT.get(DEVICE_RADIODOT) in str(value) and key not in self.fcc_id_dict.keys():
                self.fcc_id_dict[key] = 'TA8AKRY901385-1'
            elif "gNodeBRadio" in key and PRODUCT_ID_DICT.get(DEVICE_NR_4408) in str(
                    value) and key not in self.fcc_id_dict.keys():
                self.fcc_id_dict[key] = 'TA8AKRC161746-1'
            elif PRODUCT_ID_DICT.get(DEVICE_4408) in str(value) and key not in self.fcc_id_dict.keys():
                self.fcc_id_dict[key] = 'TA8AKRC161746-1'
            elif PRODUCT_ID_DICT.get(DEVICE_2208) in str(value) and key not in self.fcc_id_dict.keys():
                self.fcc_id_dict[key] = 'TA8AKRC161711-1'
            else:
                log.logger.debug("No product ID for {0} contained within {1}".format(key, value))
        log.logger.debug("Finished the fccIds for each node id ")

    def add_decimals_to_long_lat(self, latitude, longtitude, node_id):
        """
        Adds decimal points to latitude and longtitude
        :param latitude: value of the latitude that node_id
        :type latitude: str
        :param longtitude: value of the longtitude that node_id
        :type longtitude: str
        :param node_id: Node identidier
        :type node_id: str
        """
        if str(latitude[0]) == "-":
            decimal_latitude = str(latitude)[:3] + "." + str(latitude)[3:]
        else:
            decimal_latitude = str(latitude)[:2] + "." + str(latitude)[2:]
        if str(longtitude[0]) == "-":
            decimal_longtitude = str(longtitude)[:3] + "." + str(longtitude)[3:]
        else:
            decimal_longtitude = str(longtitude)[:2] + "." + str(longtitude)[2:]
        self.long_lat_dict[node_id] = (str(decimal_latitude) + ', ' + str(decimal_longtitude))

    def get_node_location(self, product_data_dict, used_nodes):
        """
        Getting the longtitude and Latitude replace_product_number_with_fcc_idse for each node Id and appending to dictionary
        :param used_nodes: list of all cbrs used nodes
        :type used_nodes: list
        :param product_data_dict: key is node_id and value is its product data as a string
        :type product_data_dict: dict creating_unsigned_csv_file
        """
        log.logger.debug("Getting longtitude and latitude for each node")
        for node in used_nodes:
            for node_id, product_data in product_data_dict.items():
                if node == node_id and node_id not in self.long_lat_dict.keys() and len(product_data) > 0:
                    latitude = re.findall(r"latitude=([-+]?[0-9]*[.]?[0-9]+)[,}]", product_data[0])[0]
                    longtitude = re.findall(r"longitude=([-+]?[0-9]*[.]?[0-9]+)[,}]", product_data[0])[0]
                    self.add_decimals_to_long_lat(latitude, longtitude, node_id)
        log.logger.debug("Finished getting longtitude and latitude for each node")

    def get_node_serial_numbers(self, product_data_dict, used_nodes):
        """
        :param used_nodes: list of all cbrs used nodes
        :type used_nodes: list
        Gets the serial numbers for each node
        :param product_data_dict: key is node_id and value is its product data as a string
        :type product_data_dict:  dict
        """
        log.logger.debug("Starting to get Serial numbers")
        for node in used_nodes:
            for node_id, product_data in product_data_dict.items():
                if node == node_id and node_id not in self.serial_number_dict.keys() and len(product_data) > 0:
                    serial_numbers_list = re.findall(r"serialNumber=(\S*),", str(product_data))
                    self.serial_number_dict[node_id] = serial_numbers_list
        log.logger.debug("Finished getting Serial numbers")

    def iterate_serial_numbers(self, node, device_type, rf_branch_count_dict):
        """
        Iterates through the serial number list of values and creates the first half of the command
        :param node: node_id ex.LTE08dg2ERBS0074
        :type node: str
        :param device_type: Dictionary of device types and node ids as list of values
        :type device_type: Dict
        :param rf_branch_count_dict: Dictionary of number of rf branches per node
        :type rf_branch_count_dict : dict
        :return: returns a list of partial commands
        :rtype: list
        """
        commands_list = []
        for node_id, serial_number_list in self.serial_number_dict.items():
            if node_id == node:
                if node in device_type.get(DEVICE_PASSIVE_DAS_4408) and rf_branch_count_dict[node] == 4:
                    self.passive_das_for_4408_4_rf_branch(node, rf_branch_count_dict, commands_list)
                elif node in device_type.get(DEVICE_PASSIVE_DAS_4408) and rf_branch_count_dict[node] == 2:
                    self.passive_das_for_4408_2_rf_branch(node, rf_branch_count_dict, commands_list)
                else:
                    for serial_number in serial_number_list:
                        command = str(self.fcc_id_dict.get(node_id)) + ',' + str(serial_number) + ',' + str(
                            self.long_lat_dict.get(node_id))
                        commands_list.append(command)
        return commands_list

    def passive_das_for_4408_4_rf_branch(self, node, rf_branch_count_dict, commands_list):
        """
        funtion used to enable the passive das feature for 4408 devices
        :param node: node_id ex.LTE08dg2ERBS0074
        :type node: str
        :param rf_branch_count_dict: rf branch dictionary
        :type rf_branch_count_dict: dict
        :param commands_list: list of commands
        :type commands_list: list
        """
        for node_id, serial_number_list in self.serial_number_dict.items():
            if node_id == node and rf_branch_count_dict[node] == 4:
                for serial_number in serial_number_list:
                    for transmission_point in range(1, 11):
                        command = str(self.fcc_id_dict.get(node_id)) + ',' + str(
                            serial_number) + ':' + "p1p2p3p4" + ':' + str(transmission_point) + ',' + str(self.long_lat_dict.get(node_id))
                        commands_list.append(command)

    def passive_das_for_4408_2_rf_branch(self, node, rf_branch_count_dict, commands_list):
        """
        function used to enable the passive das feature for 4408 devices
        :param node: node_id ex.LTE08dg2ERBS0074
        :type node: str
        :param rf_branch_count_dict: rf branch dictionary
        :type rf_branch_count_dict: dict
        :param commands_list: list of commands
        :type commands_list: list
        """
        for node_id, serial_number_list in self.serial_number_dict.items():
            if node_id == node and rf_branch_count_dict[node] == 2:
                for serial_number in serial_number_list:
                    for transmission_point in range(1, 11):
                        command = str(self.fcc_id_dict.get(node_id)) + ',' + str(
                            serial_number) + ':' + "p1p2" + ':' + str(transmission_point) + ',' + str(self.long_lat_dict.get(node_id))
                        commands_list.append(command)

    @retry(retry_on_exception=lambda e: isinstance(e, (EnvironError, EnmApplicationError, NoOuputFromScriptEngineResponseError)),
           wait_fixed=5000, stop_max_attempt_number=3)
    def cmedit_check_max_allowed_eirp_for_all_nodes(self, user, device_type):
        """
        Querying ENM get the value SectorCarrier.maxAllowedEirpPSD value, this is used to determine antenna gain for 6488 nodes
        :param user: user object
        :type user: `enmutils.enm_user_2`
        :param device_type: Dictionary of nodes separated by device type
        :type device_type: Dict
        :raises e: if any of the below is True
        :raises EnvironError: If no product number found
        :raises NoOuputFromScriptEngineResponseError: If no response from ENM
        :raises EnmApplicationError: If there is an error such as a timeout while executing command
        """
        log.logger.debug("Getting all node eirp values to evaluate 6488s being old or new")
        output = ""
        try:
            response = user.enm_execute(CHECK_OLD_OR_NEW_6488)
            output = response.get_output()
            if any(re.search(r'(error|^[0]\sinstance)', line, re.I) for line in output):
                raise EnvironError('Could not find any Eirp data to confirm 6488 new or old')
        except (EnvironError, EnmApplicationError, NoOuputFromScriptEngineResponseError) as e:
            log.logger.debug('Could not fetch data due as {0}'.format(e))
            raise e
        node_ids = re.findall('ManagedElement=(.*?),', str(output))
        self.determine_old_or_new_6488(device_type, node_ids)
        log.logger.debug("Finished getting  SectorCarrier.maxAllowedEirpPSD for all nodes and sorting")

    def determine_old_or_new_6488(self, device_type, node_ids):
        """
        Determines whether 6488 node is new or old based on node_ids gatherd in check_max_allowed_eirp_for_all_nodes
        :param device_type: Dictionary of nodes separated by device type
        :type device_type: Dict
        :param node_ids: List of all node ids which have eirp value
        :type node_ids: List
        """
        log.logger.debug("Differentiating between old and new 6488 nodes for cpi Antenna Gains")
        for node in device_type.get(DEVICE_6488):
            if node not in self.old_new_6488_dict.get(DEVICE_6488_NEW):
                if str(node) in node_ids:
                    self.old_new_6488_dict[DEVICE_6488_NEW].append(node)
                else:
                    self.old_new_6488_dict[DEVICE_6488_OLD].append(node)
        log.logger.debug("New and old 6488 nodes separated: {0}".format(self.old_new_6488_dict))

    def build_command(self, node, command, device_type):
        """
        Builds cpi commmands in the correct order
        :param node: node_id ex.LTE08dg2ERBS0074
        :type node: str
        :param command: Partial command
        :type command: str
        :param device_type: Dictionary with device type as key and list of node_ids of that device type for values
        :type device_type: dict
        """
        full_command = ""
        if node in device_type.get(DEVICE_RADIODOT):
            full_command = command + ANTENNA_GAIN_DICT[DEVICE_RADIODOT]
            my_device_type = DEVICE_RADIODOT
        elif node in device_type.get(DEVICE_2208):
            full_command = command + ANTENNA_GAIN_DICT[DEVICE_2208]
            my_device_type = DEVICE_2208
        elif "gNodeBRadio" in node and node in device_type.get(DEVICE_NR_4408):
            full_command = command + ANTENNA_GAIN_DICT[DEVICE_NR_4408]
            my_device_type = DEVICE_NR_4408
        elif node in device_type.get(DEVICE_4408):
            full_command = command + ANTENNA_GAIN_DICT[DEVICE_4408]
            my_device_type = DEVICE_4408
        elif node in device_type.get(DEVICE_6488) and node in self.old_new_6488_dict.get(DEVICE_6488_NEW):
            full_command = command + ANTENNA_GAIN_DICT[DEVICE_6488_NEW]
            my_device_type = DEVICE_6488_NEW
        elif node in device_type.get(DEVICE_6488) and node in self.old_new_6488_dict.get(DEVICE_6488_OLD):
            full_command = command + ANTENNA_GAIN_DICT[DEVICE_6488_OLD]
            my_device_type = DEVICE_6488_OLD
        else:
            log.logger.debug("Unable to identify device type for {0}: ".format(node))
        if len(full_command) > 0:
            full_command_no_spaces = full_command.replace(" ", "")
            self.cpi_data_list.append([full_command_no_spaces])
            log.logger.debug(
                "Device is {0} - Node is {1} - command is : {2}".format(my_device_type, node, full_command_no_spaces))

    def build_lines_for_cpi_file(self, used_nodes, device_type, rf_branch_count_dict):
        """
        Builds lines for signing the cpi data format"FccId, Serial_Number, Long, Lat, Device_type determines Antenna Gain"
        :param used_nodes: list of used nodes from cbrs_setup
        :type used_nodes: list
        :param device_type: Dictionary with device type as key and list of node_ids of that device type for values
        :type device_type: dict
        :param rf_branch_count_dict: Dictionary of number of rf branches per node
        :type rf_branch_count_dict : dict
        """
        log.logger.debug("Starting to build lines for cpi file")
        for node in used_nodes:
            if node in self.fcc_id_dict.keys() and node in self.serial_number_dict.keys() and node in self.long_lat_dict.keys():
                commands_list = self.iterate_serial_numbers(node, device_type, rf_branch_count_dict)
            for command in commands_list:
                self.build_command(node, command, device_type)
        log.logger.debug("Finished building lines for cpi file")

    def creating_unsigned_csv_file(self):
        """
        Creates a csv file at home/enmutils/cbrs
        """
        log.logger.debug("Starting the creation of cpi csv file")
        headers = ['FccId, Serial_Number,Long, Lat, height, heightType, indoorDeployment, horizontalAccuracy,'
                   ' verticalAccuracy,  antennaAzimuth, antennaDowntilt, antennaGain, eirpCapability, antennaBeamwidth,'
                   ' antennaModel']
        with open(PATH_CPI_CSV, "w") as csv_file:
            csv_file.write(",".join(x.strip() for x in headers[0].split(',')))
            csv_file.write("\n")
            for data in self.cpi_data_list:
                csv_file.write(",".join(x.strip() for x in data[0].split(',')))
                csv_file.write("\n")
        log.logger.debug("Finishing the creation of cpi csv file")

    def sign_cpi_csv_file(self):
        """
        Uses Jar file to sign csv data
        """
        log.logger.debug("Trying to Sign CBRS data")
        ms_host = cache.get_ms_host()
        with pexpect.spawn("ssh {0} root@{1}".format(NO_HOST_CHECK, ms_host)) as child:
            if ms_host == "localhost" and cache.is_enm_on_cloud_native():
                log.logger.debug("Local_Host cENM")
                generic_pexpect_for_cpi_signing(child)
            elif ms_host == "localhost":
                log.logger.debug("Local_Host")
                child.sendline("cd {0}".format(CBRS_JAR_DIR))
                generic_pexpect_for_cpi_signing(child)
            else:
                log.logger.debug("LMS")
                child.sendline("connect_to_vm")
                generic_pexpect_for_cpi_signing(child)
        log.logger.debug("Finished signing CBRS data")

    @staticmethod
    def put_signed_csv_file_to_scripting_cluster(scripting_vm):
        """
        Imports the csv file to the CPI DB on the scripting cluster
        :param scripting_vm: Scripting ip to which the CPI_SignedData file is uploaded too
        :type scripting_vm: str
        :raises RuntimeError: if there is an issue with upload to scripting cluster
        """
        log.logger.debug("Uploading CpiSignedData csv file to scripting cluster")
        try:
            scripting_vm = scripting_vm.split("-p")
            vm = scripting_vm[0].replace(" ", "")
            upload(vm, "administrator", "TestPassw0rd", local_file_path="/root/CPI_SignedData",
                   remote_file_path="/home/shared/administrator/CPI_SignedData", file_permissions=777)
        except IOError as e:
            raise RuntimeError(str(e))
        log.logger.debug("Uploaded CpiSignedData file to scripting cluster")

    @staticmethod
    def set_cpi_registration_pib_values():
        """
        Sets the cpi registration pib values on scripting cluster
        """
        log.logger.debug("Setting pib values for cbrs_cpi")
        try:
            update_pib_value(enm_service_name="cmserv",
                             pib_parameter_name="sasDomainProxy_registrationRequiresCpiSignedData",
                             pib_parameter_value="true", service_identifier="domain-proxy-service")
        except Exception as e:
            log.logger.debug(
                "Issue updating sasDomainProxy_registrationRequiresCpiSignedData pib to True, error message: {0}".format(e))
        try:
            update_pib_value(enm_service_name="cmserv", pib_parameter_name="sasDomainProxy_cpiDataMasterBoolean",
                             pib_parameter_value="true", service_identifier="domain-proxy-service")
        except Exception as e:
            log.logger.debug("Issue updating pip, error message: {0}".format(e))
        try:
            update_pib_value(enm_service_name="cmserv",
                             pib_parameter_name="sasDomainProxy_securityEndEntityRevocationCheckEnabled",
                             pib_parameter_value="false", service_identifier="domain-proxy-service")
        except Exception as e:
            log.logger.debug("Issue updating pip, error message: {0}".format(e))
        try:
            update_pib_value(enm_service_name="cmserv", pib_parameter_name="sasDomainProxy_securityRevocationCheckEnabled",
                             pib_parameter_value="false", service_identifier="domain-proxy-service")
        except Exception as e:
            log.logger.debug("Issue updating pip, error message: {0}".format(e))
        log.logger.debug("Finished setting pib values for cbrs_cpi")

    @staticmethod
    def import_signed_csv_file_to_db(scripting_vm):
        """
        Performs cbrscpi import on cvs file stored on scripting cluster
        :param scripting_vm: scripting Ip
        :type scripting_vm: unicode
        :raises EnvironError: If any issue with connecting to or umporting the cpi data to the scripting cluster
        """
        log.logger.debug("importing signed file to scripting db ")
        with pexpect.spawn("ssh {0} administrator@{1}".format(NO_HOST_CHECK, scripting_vm)) as child:
            time.sleep(2)
            expected = child.expect(["assword:", pexpect.EOF, pexpect.TIMEOUT])
            if expected == 0:
                child.sendline("TestPassw0rd")
                time.sleep(2)
                expected = child.expect(["administrator@", pexpect.EOF, pexpect.TIMEOUT])
                if expected == 0:
                    child.sendline("cbrscpi import")
                    time.sleep(2)
                    expected = child.expect(["Import file: ", pexpect.EOF, pexpect.TIMEOUT])
                    if expected == 0:
                        child.sendline("CPI_SignedData")
                        time.sleep(2)
                        expected = child.expect(["administrator@", pexpect.EOF, pexpect.TIMEOUT])
                        if expected == 0:
                            log.logger.debug("Completed import into scripting db")
                        else:
                            raise EnvironError("Expected to be prompted 'administrator@' after file imported")
                    else:
                        raise EnvironError("Expected to be prompted for 'Import file:'")
                else:
                    raise EnvironError("Expected to be prompted for 'administrator@' after successful login")
            else:
                raise EnvironError("Expected to be prompted for password")
        log.logger.debug("Finished importing signed file to scripting vm")


def cbrscpi_teardown(scripting_vms):
    """
    Cleans up the scripting cluster and wlvm of cbrs cpi data on teardown
    :param scripting_vms: list of Scripting Ip
    :type scripting_vms: list
    """
    cbrs_cpi_cleanup_import(scripting_vms)
    cleanup_wlvm_cpi_file()
    log.logger.debug("Finished Cbrs_cpi cleanup")


@retry(retry_on_exception=lambda e: isinstance(e, EnvironError), wait_fixed=30000, stop_max_attempt_number=3)
def cbrs_cpi_cleanup_import(scripting_vm):
    """
    Deletes the cbrs_cpi import data and deletes the file from the scripting cluster
    :param scripting_vm: Scripting Ip
    :type scripting_vm: Unicode
    :raises EnvironError: If there is any issue with clearing the cpi imported data, deleting the file or connecting to the scripting cluster
    """
    log.logger.debug("Cleaning up cpi data from scripting cluster on Teardown")
    with pexpect.spawn("ssh {0} administrator@{1}".format(NO_HOST_CHECK, scripting_vm)) as child:
        time.sleep(2)
        return1 = child.expect(["assword:", pexpect.EOF, pexpect.TIMEOUT])
        child.sendline("TestPassw0rd")
        time.sleep(2)
        return2 = child.expect(["administrator@", pexpect.EOF, pexpect.TIMEOUT])
        child.sendline("cbrscpi delete all --force")
        return3 = child.expect(["TRUNCATE", pexpect.EOF, pexpect.TIMEOUT])
        rm_cpi_file_from_scripting_vm(child)
        return_list = [return1, return2, return3]
        for return_value in return_list:
            if return_value != 0:
                raise EnvironError(
                    "Failed to teardown cpi data, A return value did no return as expected. All values should be 0, "
                    "Return values are {0}, {1}, {2}".format(return1, return2, return3))
    log.logger.debug("Finished Cleaning up cpi data from scripting cluster on Teardown")


def cleanup_wlvm_cpi_file():
    """
    Cleaning up cpiSortedData.csv for next iteration
    """
    log.logger.debug("Starting to cleanup csv file at /home/enmutils/cbrs")
    run_local_cmd("rm -f /home/enmutils/cbrs/CpiSortedData.csv")
    run_local_cmd("rm -f /root/CPI_SignedData")
    log.logger.debug("Finished cleanup of /home/enmutils/cbrs/CpiSortedData.csv and /root/CPI_SignedData")
