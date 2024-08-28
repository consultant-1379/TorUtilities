# ********************************************************************
# Name    : PM NBI
# Summary : Used by PM profiles to interact with the PM NBI. Allows
#           user to interact with PM NBI(FLS), allows querying of
#           existing PM files and retrieval of files using SFTP.
# ********************************************************************

import random
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import FLS_HEADERS


class Fls(object):
    BASE_URL = '/file/v1/files/?filter=dataType=={data_type}'
    START_ROP_TIME = ";startRopTimeInOss=={start_rop_time}"
    TIME_SPAN = ";startRopTimeInOss=ge={start_time};startRopTimeInOss=lt={end_time}"
    FILE_CREATION_TIME = ";fileCreationTimeInOss=ge={file_creation_time}"
    FILE_ID = ";id=gt={file_id}"
    NODE_TYPE = ";nodeType=={node_type}"
    FILE_TYPE = ";fileType=={file_type}"
    SELECT = "&select=id,nodeName,fileLocation,nodeType,fileCreationTimeInOss,dataType"
    OFFSET = "&offset={offset}"
    LIMIT = "&limit={limit}"
    ORDER = "&orderBy={orderBy}"
    ROP_FILES_COUNT_LIMIT = 10000
    orderby = None
    limit_ = None
    offset_ = None
    fileid = None

    def __init__(self, user=None):
        """
        FLS (File lookup service) constructor
        :param user: ENM user
        :type user: enmutils.lib.enm_user_2.User
        """
        self.user = user

    def get_pmic_rop_files_location(self, profile_name, data_type, node_type=None, file_id=0, **kwargs):
        """
        Fetches all pm rop file locations based on start rop time
        :param node_type: Node type in ENM
        :type node_type: str
        :param data_type: To represent the file types like PM Data files Topology files. Based on subscription. e.g.PM_STATISTICAL
        :type profile_name: str
        :param profile_name: Profile name
        :type data_type: str
        :param file_id: The unique identifier/token of the file
        :type file_id: int
        :param kwargs: Dictionary of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :return: list of file locations, last file ID and file creation time in OSS of last file
        :rtype: tuple
        """
        file_creation_time = kwargs.pop("file_creation_time", None)

        self.SELECT = "&select=id,nodeName,fileCreationTimeInOss,fileLocation" if profile_name in ["PM_26", "PM_28", "PM_45"] else self.SELECT
        if not file_id:
            rop_file_locations = self.get_files(data_type, node_type, file_id, file_creation_time, **kwargs)
            last_file_id = rop_file_locations[-1]["id"] if rop_file_locations else 0
            filecreationtimeinoss = (rop_file_locations[-1]["fileCreationTimeInOss"]).split("+")[0] if rop_file_locations else None
        else:
            rop_file_locations = self.get_excess_files(profile_name, data_type, node_type, file_id, file_creation_time, **kwargs)

            last_file_id = rop_file_locations[-1]["id"] if rop_file_locations else file_id
            filecreationtimeinoss = str((rop_file_locations[-1]["fileCreationTimeInOss"]).split("+")[0]) if rop_file_locations else None
        file_locations = [item["fileLocation"] for item in rop_file_locations if rop_file_locations]

        return file_locations, last_file_id, filecreationtimeinoss

    def get_excess_files(self, profile_name, data_type, node_type, file_id, file_creation_time, **kwargs):
        """
        Get files from FLS, if total number of files is greater than 10000, it will request for the next batch of files

        :param node_type: Node type in ENM
        :type node_type: str
        :param data_type: To represent the file types like PM Data files Topology files. Based on subscription. e.g.PM_STATISTICAL
        :type profile_name: str
        :param profile_name: Profile name
        :type data_type: str
        :param file_id: The unique identifier/token of the file
        :type file_id: int
        :type file_creation_time: str
        :param file_creation_time: File creation time in OSS
        :param kwargs: Dictionary of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :return: list of file locations
        :rtype: list
        """
        rop_file_locations = self.get_files(data_type, node_type, file_id, file_creation_time, **kwargs)
        if rop_file_locations and profile_name in ["PM_26", "PM_28", "PM_45"]:
            for _ in range(5):

                if len(rop_file_locations) % self.ROP_FILES_COUNT_LIMIT == 0:
                    rop_file_locations_data = self.get_files(data_type, node_type, rop_file_locations[-1]["id"],
                                                             str((rop_file_locations[-1]["fileCreationTimeInOss"]).split("+")[0]), **kwargs)
                    if rop_file_locations_data:
                        rop_file_locations = rop_file_locations + rop_file_locations_data
                    else:
                        break
        return rop_file_locations

    def get_files(self, data_type, node_type, file_id, file_creation_time, **kwargs):
        """
        Fetches all pm rop file locations based on data type.

        :param data_type: To represent the file types like PM Data files Topology files.
                Based on subscription. e.g. PM_STATISTICAL
        :type data_type: str
        :param node_type: Node type in ENM
        :type node_type: str
        :param file_id: The unique identifier/token of the file
        :type file_id: int
        :type file_creation_time: str
        :param file_creation_time: File creation time in OSS
        :param kwargs: Dictionary of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :return: list of rop files with locations
        :rtype: list
        :raises EnmApplicationError: if getting empty response
        """
        self.orderby = kwargs.pop("orderby", None)
        self.limit_ = kwargs.pop("limit", None)
        self.offset_ = kwargs.pop("offset", 0)
        self.fileid = file_id
        raw_url_args = kwargs.pop('raw_url_args', "")
        self.check_topology_data_type(data_type)
        files = []
        url = self._url_builder(data_type, file_id=self.fileid, node_type=node_type, file_creation_time=file_creation_time,
                                orderby=self.orderby, limit=self.limit_, offset=self.offset_, raw_url_args=raw_url_args)

        response = self.user.get(url, headers=FLS_HEADERS)
        raise_for_status(response)
        if response.ok and response.json():
            files = response.json()["files"]
            file_id = files[-1]["id"] if files else file_id
            log_node_type = "for node type : {0},".format(node_type)
            log_id = "for file ID greater than : {0}".format(file_id)
            log.logger.info("FLS reports {0} files {1} data type : {2} {3}".format(len(files), log_node_type
                                                                                   if node_type else "for", data_type,
                                                                                   log_id))
            if files:
                last_file_creation_time = str((files[-1]["fileCreationTimeInOss"]).split("+")[0])
                log.logger.info("For datatype {0}, MAX_ID is {1} and File Creation Time is {2}".format(data_type, files[-1]["id"], last_file_creation_time))
            else:
                log.logger.debug("No files of datatype {0}. MAX_ID: None".format(data_type, ))
        else:
            raise EnmApplicationError("Failed to fetch information from FLS, response : {0}".format(response.text))

        return files

    def check_topology_data_type(self, data_type):
        """
        Checks if TOPOLOGY is present in data_type and updates the
        orderby, limit_, offset_, fileid values to None

        :param data_type: To represent the file types like PM Data files Topology files.
                Based on subscription. e.g. PM_STATISTICAL
        :type data_type: str
        """
        if "TOPOLOGY" in data_type:
            self.SELECT = ("&select=fileLocation,id,fileCreationTimeInOss,dataType,nodeType,"
                           "nodeName&orderBy=fileCreationTimeInOss asc")
            self.orderby = None
            self.limit_ = None
            self.offset_ = None
            self.fileid = None

    @staticmethod
    def create_sftp_batch_files(data, pm_nbi_dir, pm_nbi_batch_filename_prefix,
                                num_of_sftp_batch_files=5, shuffle_data=True):
        """
        Create the sftp batch files used for the nbi to sftp the files in batch mode.
        :param data: list of file locations
        :type data: list
        :param pm_nbi_dir: location of the pm_nbi directory
        :type pm_nbi_dir: str
        :param pm_nbi_batch_filename_prefix: batch file (full path)
        :type pm_nbi_batch_filename_prefix: str
        :param num_of_sftp_batch_files: number of batch files to created from the file_locations list
        :type num_of_sftp_batch_files: int
        :param shuffle_data: Option to shuffle the files before creating the batch files (file types are more equally
                             distributed over the batch files which increases performance)
        :type shuffle_data: bool
        """
        if shuffle_data:
            random.shuffle(data)

        # Equally distribute lines over batch files: int(total_lines + N - 1) / N, where N is the number of batch files
        break_point = int((len(data) + num_of_sftp_batch_files - 1) / num_of_sftp_batch_files)
        offset = 0

        for batch_id in range(num_of_sftp_batch_files):
            with open(pm_nbi_batch_filename_prefix.format(batch_id), "w") as batch_file:
                for count, file_path in enumerate(data[offset:]):
                    if break_point == count:
                        offset += count
                        break
                    batch_file.write("-get {file_path} {pm_nbi_dir}\n".format(file_path=file_path,
                                                                              pm_nbi_dir=pm_nbi_dir))

    def _url_builder(self, data_type, node_type=None, file_type=None, file_id=0, start_rop_time=None, time_span=None,
                     file_creation_time=None, raw_url_args="", offset=None, limit=None, orderby=None):
        """
        Builds the FLS url based on given Parameters. Parameters are parsed to FLS query string params
        :param data_type: Represents the file types like PM Data files Topology files. Based on subscription.
                e.g. PM_STATISTICAL.
        :type data_type: str
        :param node_type: Type of the node. Possible values: RNC, ERBS, RBS, MGW
        :type node_type: str
        :param file_type: The format of the file like compressed, decoded. Possible Values: XML, GZ, TXT
        :type file_type: str
        :param file_id: The unique identifier/token of the file
        :type file_id: int
        :param start_rop_time: It represents start ROP time of the file in ENM server time zone.
                Possible Formats: yyyy-MM-dd'T'HH:mm:ss , yyyy-MM-dd'T'HH:mm:ss(-|+)HHmm
        :type start_rop_time: str
        :param offset: (Mandatory when limit is given)
        :type offset: str
        :param time_span: Tuple containing 2 strings (in the form of "{year}-{month}-{day}T{hour}:{min}:00")
        :type time_span: tuple
        :param file_creation_time: It represents time when ENIQ is integrated with ENM
               Possible Formats: yyyy-MM-dd'T'HH:mm:ss , yyyy-MM-dd'T'HH:mm:ss(-|+)HHmm
        :type file_creation_time: str
        :param raw_url_args: Option for Raw url string arguments (formatted exactly as the url has them)
        :type raw_url_args: str
        :param limit: Limits the result records to any number smaller than 10000
        :type limit: int
        :param orderby: orders the result sets in ascending or descending
        :type orderby: str
        :return: FLS url query string
        :rtype: str
        """
        _node_type = self.NODE_TYPE.format(node_type=node_type) if node_type else ""
        _file_type = self.FILE_TYPE.format(file_type=file_type) if file_type else ""
        _file_id = self.FILE_ID.format(file_id=file_id) if file_id else ""
        _start_rop_time = self.START_ROP_TIME.format(start_rop_time=start_rop_time) if start_rop_time else ""
        _time_span = self.TIME_SPAN.format(start_time=time_span[0], end_time=time_span[1]) if time_span else ""
        _file_creation_time = self.FILE_CREATION_TIME.format(
            file_creation_time=file_creation_time) if file_creation_time else ""
        _offset = self.OFFSET.format(offset=offset) if offset else ""
        _limit = self.LIMIT.format(limit=limit) if limit else ""
        _orderby = self.ORDER.format(orderBy=orderby) if orderby else ""

        return (self.BASE_URL.format(data_type=data_type) + _node_type + _file_type + _file_id + _start_rop_time +
                _time_span + _file_creation_time + raw_url_args + _limit + _offset + _orderby + self.SELECT)
