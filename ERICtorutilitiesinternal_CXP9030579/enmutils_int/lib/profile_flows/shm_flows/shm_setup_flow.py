import os
from collections import OrderedDict, defaultdict

from enmutils.lib import log, filesystem, config, cache
from enmutils.lib.command_execution import is_host_pingable
from enmutils_int.lib import simple_sftp_client
from enmutils_int.lib.helper_methods import generate_basic_dictionary_from_list_of_objects
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_data import EXISTING_PACKAGES
from enmutils_int.lib.shm_utilities import SHMUtils


class ShmSetupFlow(ShmFlow):

    # SFTP information
    HOST = None
    USER = None
    FILE_PATH = None
    PASS = None
    USE_PROXY = False

    NAME = "SHM_SETUP"
    PARAMS_CPP = ["setswinstallvariables:bandwidth=3072;", "setswinstallvariables:fileDl=sftp;",
                  "setswinstallvariables:confirmationDeadline=7800;", "setswinstallvariables:cvDbDatSize=512;"]
    PARAMS_ROUTER6672 = ["configure_async_action:backupload=true,backupfile_size=20M;"]
    PARAMS_COM_ECIM = ["configure_async_action:backupload=true,backupfile_size=5M;",
                       "ecim_configure_delay:event=activate,restart=no,delay=480;"]
    PARAMS_MLTN = ["backupcfg:file_size=200000;", "shmerror:ActionName=sbl_timer,OperationType=set,T0x=30;"]
    PARAMS_BSC = ["configure_async_action:backupload=true,backupfile_size=400M;"]
    PARAMS_ROUTER6675 = ["configure_async_action:backupload=true,backupfile_size=20M;"]
    PARAMS_MINI_LINK_669x = PARAMS_MLTN

    def set_sftp_values(self):
        """
        Setting SFTP server details, based upon whichever server is reachable
        """
        sftp_info = OrderedDict([
            ("gateway",
             {"host": config.get_prop("gateway_ftp"), "user": "root", "passwd": "shroot",
              "dir": "/proj/ENMLoggingServer/br_torutils", "use_proxy": False}),
            ("slow_ftp",
             {"host": "sfts.seli.gic.ericsson.se", "user": "APTUSER", "passwd": r"]~pR:'Aw6cwpJR4dDY$k85\t",
              "dir": "/enmcisftp/shm_packages", "use_proxy": True})
        ])
        if cache.is_enm_on_cloud_native():
            self.HOST = sftp_info.get("slow_ftp").get("host")
            self.USER = sftp_info.get("slow_ftp").get("user")
            self.PASS = sftp_info.get("slow_ftp").get("passwd")
            self.FILE_PATH = sftp_info.get("slow_ftp").get("dir")
            self.USE_PROXY = sftp_info.get("slow_ftp").get("use_proxy")
            return
        for server in sftp_info.values():
            if (self.HOST or (server.get("host") != sftp_info.get("slow_ftp").get("host") and
                              not is_host_pingable(server.get("host")))):
                continue
            self.HOST = server.get("host")
            self.USER = server.get("user")
            self.PASS = server.get("passwd")
            self.FILE_PATH = server.get("dir")
            self.USE_PROXY = server.get("use_proxy")

    def execute_flow(self):
        self.state = "RUNNING"
        self.set_sftp_values()
        self.download_software_packages()
        self.set_values()

    def get_software_package_details(self):
        """
        Get the list of software package archives from shm module

        :return: List of software package archive names
        :rtype: list
        """
        try:
            if self.LOCAL_PATH and not os.path.exists(self.LOCAL_PATH):
                os.makedirs(self.LOCAL_PATH)
                log.logger.debug("{0} directories were created to download SHM pkg's".format(self.LOCAL_PATH))
            else:
                log.logger.debug("Selected directory to download SHM pkg's is {0}".format(self.LOCAL_PATH))
        except Exception as e:
            self.add_error_as_exception(e)
        software_packages = []
        for key, values in EXISTING_PACKAGES.iteritems():
            for value in values:
                if key == "MLTN" or key == "MINI-LINK-669x":
                    software_packages.append("{0}.tgz".format(value))
                    continue
                software_packages.append("{0}.zip".format(value))
        return software_packages

    def download_software_packages(self):
        """
        Download the list of software packages
        """
        packages = self.get_software_package_details()
        for package in packages:
            try:
                if filesystem.does_file_exist("{0}/{1}".format(self.LOCAL_PATH, package)):
                    filesystem.delete_file("{0}/{1}".format(self.LOCAL_PATH, package))
                simple_sftp_client.download(self.HOST, self.USER, self.PASS, "{0}/{1}".format(self.FILE_PATH, package),
                                            "{0}/{1}".format(self.LOCAL_PATH, "{0}".format(package)),
                                            use_proxy=self.USE_PROXY)
            except Exception as e:
                log.logger.debug("Unable to download file from vAPP: {0}, Response: {1}.".format(package, str(e)))
                try:
                    sftp_server = {"host": "sfts.seli.gic.ericsson.se", "user": "APTUSER",
                                   "passwd": r"]~pR:'Aw6cwpJR4dDY$k85\t",
                                   "dir": "/enmcisftp/shm_packages", "use_proxy": True}
                    simple_sftp_client.download(sftp_server.get("host"), sftp_server.get("user"),
                                                sftp_server.get("passwd"), "{0}/{1}".format(sftp_server.get("dir"), package),
                                                "{0}/{1}".format(self.LOCAL_PATH, "{0}".format(package)),
                                                use_proxy=sftp_server.get("use_proxy"))
                except Exception as e:
                    log.logger.debug("Unable to download file either from vAPP or SFTP: {0}, Response: {1}."
                                     .format(package, str(e)))

    def set_values(self):
        """
        Set swinstall values on the netsim
        """
        node_attributes = ["node_id", "node_ip", "netsim", "primary_type", "simulation", "node_name", "poid"]
        nodes = generate_basic_dictionary_from_list_of_objects(
            self.get_nodes_list_by_attribute(node_attributes=node_attributes), "primary_type")
        nodes = defaultdict(list, nodes)
        node_types = [("CPP", nodes["ERBS"] + nodes["MGW"]), ("COM_ECIM", nodes["RadioNode"] + nodes["SCU"]),
                      ("MLTN", nodes["MLTN"]), ("ROUTER6672", nodes["Router6672"]),
                      ("ROUTER6675", nodes["Router6675"]), ("MINI_LINK_669x", nodes["MINI-LINK-669x"])]
        for node_type in node_types:
            platform, nodes = node_type
            if nodes:
                try:
                    SHMUtils.set_netsim_values(nodes, getattr(self, "PARAMS_{0}".format(platform)))
                except Exception as e:
                    self.add_error_as_exception(e)
                    continue
