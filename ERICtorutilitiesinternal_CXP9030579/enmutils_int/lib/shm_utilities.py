# ********************************************************************
# Name    : SHM Utilities
# Summary : Primarily used by SHM profiles. Allows the user to manage
#           multiple operations within the SHM application area,
#           including but not limited all CRUD operations in relation
#           to SHM Utilities, Licence Key, Software Packages
# ********************************************************************

import datetime
import json
import os
import pkgutil
import re
from time import sleep
from xml.dom import minidom

import unipath
from requests.exceptions import HTTPError
from retrying import retry

from enmutils.lib import arguments, filesystem, log, mutexer
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import (EnmApplicationError,
                                     FailedNetsimOperation, NetsimError,
                                     ScriptEngineResponseValidationError,
                                     ShellCommandReturnedNonZero, EnvironError)
from enmutils.lib.headers import JSON_SECURITY_REQUEST, SHM_LONG_HEADER
from enmutils.lib.shell import Command, run_local_cmd
from enmutils_int.lib import netsim_operations, node_pool_mgr
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.load_node import annotate_fdn_poid_return_node_objects
from enmutils_int.lib.services import deploymentinfomanager_adaptor, nodemanager_adaptor
from enmutils_int.lib.shm_backup_jobs import (BackupJobBSC, BackupJobCOMECIM, BackupJobCPP,
                                              BackupJobMiniLink, BackupJobMiniLink669x,
                                              BackupJobMiniLink6352, BackupJobRouter6675,
                                              BackupJobSpitFire)
from enmutils_int.lib.shm import UpgradeJob
from enmutils_int.lib.shm_delete_jobs import DeleteSoftwarePackageOnNodeJob, DeleteInactiveSoftwarePackageOnNodeJob
from enmutils_int.lib.shm_data import (EXISTING_PACKAGES,
                                       GET_FINGERPRINT_REGEX,
                                       LICENSE_GENERATION_SCRIPT_FOLDER,
                                       LICENSE_GENERATION_SCRIPT_NAME,
                                       NODE_FINGERPRINT_COMMAND,
                                       NODE_IDENTITY_MIMS,
                                       SHM_LICENSE_DELETE_ENDPOINT,
                                       SHM_LICENSE_LIST_ENDPOINT,
                                       SHM_LICENSE_UPLOAD_ENDPOINT)
from enmutils_int.lib.shm_job import MultiUpgrade
from enmutils_int.lib.shm_software_ops import SoftwareOperations


class SHMUtils(object):

    def __init__(self):
        """
        Init method for helper class for shm generic actions
        """
        self.job = None

    @classmethod
    def retry_when_below_skipped_tolerance(cls, tolerance=40, skipped=None, total=None):
        """
        Util method to determine if skipped nodes, is above the threshold and to reschedule the job
        :type tolerance: int
        :param tolerance: Threshold of skipped nodes before we schedule the second run
        :type skipped: int
        :param skipped: Number of skipped nodes
        :type total: int
        :param total: Total number of nodes in the job
        :rtype: bool
        :return: Boolean
        """
        if skipped and not float(skipped) / (float(total) / 100) >= tolerance:
            return False
        return True

    def backup_setup(self, user, nodes, file_name, platform="CPP", repeat_count="0"):
        """
        Helper method to create/import software package, and create an backup job

        :type nodes: list
        :param nodes: List of node(s) to be determine the package, and be included in the backup job
        :param user: User object that will be used to create the backup job
        :type user: `enm_user_2.User`
        :param file_name: Filename which should be considered as the job name
        :type file_name: str
        :param platform: Name of the node platform
        :type platform: str
        :param repeat_count: str String representation of an integer indicating whether or not to repeat the job
        :type repeat_count: str
        :rtype: backup object
        :returns: object
        :raises EnmApplicationError: when there is error in creating backup job
        """
        try:
            if nodes[0].primary_type == "ERBS":
                backup_job = BackupJobCPP(user=user, nodes=nodes, name=file_name, platform=platform,
                                          repeat_count=repeat_count)
            elif nodes[0].primary_type == "RadioNode":
                backup_job = BackupJobCOMECIM(user=user, nodes=nodes, name=file_name, repeat_count=repeat_count,
                                              platform="ECIM", random_suffix=file_name)
            elif nodes[0].primary_type == "MINI-LINK-6352":
                backup_job = BackupJobMiniLink6352(user=user, nodes=nodes, name=file_name,
                                                   repeat_count=repeat_count, platform=platform)
            elif nodes[0].primary_type in ["Router6672", "Router_6672"]:
                description = 'Performs backup on Router_6672 nodes'
                backup_job = BackupJobSpitFire(user=user, nodes=nodes, name=file_name, repeat_count=repeat_count,
                                               description=description, random_suffix=file_name)
            elif nodes[0].primary_type in ["Router6675"]:
                description = 'Performs backup on Router6675 nodes'
                backup_job = BackupJobRouter6675(user=user, nodes=nodes, name=file_name, repeat_count=repeat_count,
                                                 description=description, random_suffix=file_name)
            elif nodes[0].primary_type == "MINI-LINK-669x":
                description = 'Performs backup on MINI-LINK-669x nodes'
                backup_job = BackupJobMiniLink669x(user=user, nodes=nodes, name=file_name, repeat_count=repeat_count,
                                                   description=description, random_suffix=file_name)
            elif nodes[0].primary_type == "BSC":
                description = "Performs backup on BSC nodes in a single job"
                backup_job = BackupJobBSC(user=user, nodes=nodes, repeat_count=repeat_count, description=description,
                                          name=file_name)
            else:
                backup_job = BackupJobMiniLink(user=user, nodes=nodes, repeat_count=repeat_count,
                                               name=file_name, platform=platform)
            backup_job.create()
        except Exception as err:
            raise EnmApplicationError("Backup Job Creation encountered exception: {} ".format(err.message))
        return backup_job

    @staticmethod
    def package_upgrade_list(nodes, package, node_type):
        """
        Helper method to fetch upgrade list for software package

        :type nodes: list
        :param nodes: List of node(s) to be determine the package, and be included in the upgrade job
        :type package: `SoftwarePackage` object
        :param package: Instance of `enm_shm.SoftwarePackage`
        :type node_type: str
        :param node_type: type of node used to query against primary node type
        :rtype: list
        :return: upgrade_list which contains Product Identity and Revision Number
        """
        if nodes[0].primary_type == node_type:
            ps = package.new_package.split('_')
            upgrade_list = ["{0}_{1}_".format(ps[0], ps[1]), ps[2]] if ps[1].isdigit() else ["{0}_".format(ps[0]),
                                                                                             ps[1]]
        else:
            upgrade_list = package.new_package.split('_')
        return upgrade_list

    def upgrade_delete(self, user, nodes, package, job_name=None, log_only=False):
        """
        Helper method to delete software package

        :type nodes: list
        :param nodes: List of node(s) to be determine the package, and be included in the upgrade job
        :type package: `lib.shm.SoftwarePackage`
        :param package: Instance of `enm_shm.SoftwarePackage`
        :type user: `enm_user_2.User`
        :param user: User object that will be used to create the upgrade job
        :type log_only: bool
        :param log_only: Indicates whether or not to log specific issues
        :type job_name: str
        :param job_name: Name of the upgrade job

        :raises e: Exception when there is exception while forming an upgrade list
        :raises EnvironmentError: when there are no nodes to delete upgrade
        :raises HTTPError: when there is http issue while forming an upgrade_list
        """
        if nodes and package:
            upgrade_list = self.package_upgrade_list(nodes=nodes, package=package, node_type="RadioNode")
            if nodes[0].primary_type in ["ERBS", "MGW", "RNC", "RBS"]:
                self.job = DeleteSoftwarePackageOnNodeJob(user=user, nodes=nodes, name=job_name, platform="CPP",
                                                          upgrade_list=upgrade_list)
            elif nodes[0].primary_type in ["MLTN", "LH", "Router6672", "Router_6672", "Router6675", "MINI-LINK-Indoor"]:
                log.logger.debug("Upgrade Deletion is not supported for {0}".format(nodes[0].primary_type))
                return
            else:
                self.job = DeleteSoftwarePackageOnNodeJob(user=user, nodes=nodes, name=job_name, platform="ECIM",
                                                          upgrade_list=upgrade_list)
            try:
                self.job.create()
            except Exception as e:
                if not log_only:
                    raise e
        else:
            raise EnvironmentError('No nodes available to delete upgrade package on node')

    def upgrade_delete_inactive(self, user, nodes, job_name=None, log_only=False, **kwargs):
        """
        Helper method to delete inactive software package

        :type user: `enm_user_2.User`
        :param user: User object that will be used to create the upgrade job
        :type nodes: list
        :param nodes: List of node(s) to be determine the package, and be included in the upgrade job
        :type job_name: str
        :param job_name: Name of the upgrade job
        :type log_only: bool
        :param log_only: Indicates whether or not to log specific issues
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary
        :raises EnvironmentError: when there are no nodes to delete upgrade
        :raises HTTPError: when there is http issue while creating job
        :raises Exception: when there is exception while creating job
        :raises e: when there is exception while creating job
        """
        if nodes:
            platform = "CPP" if nodes[0].primary_type == "ERBS" else "ECIM"
            self.job = DeleteInactiveSoftwarePackageOnNodeJob(user=user, nodes=nodes, name=job_name, platform=platform,
                                                              **kwargs)
            try:
                self.job.create()
                log.logger.debug("Successfully created a job to delete inactive upgrade packages on {0} "
                                 "nodes".format(nodes[0].primary_type))
            except Exception as e:
                if not log_only:
                    raise e
                else:
                    log.logger.debug("Error encountered while creating "
                                     "delete inactive upgrade package job : {0}".format(e))
        else:
            raise EnvironmentError('No nodes available to delete inactive upgrade package on node')

    def get_node_list(self, node_type, nodes):
        """
        Helper method to return the nodes list of specific node type

            :param node_type: Type of the node to be filtered
            :type node_type: str
            :param nodes: list of all nodes
            :type nodes: list

            :rtype: list
            :return: list of filtered nodes as per node type
        """
        return [node for node in nodes if node.primary_type == node_type]

    def upgrade_trigger(self, job_list, user, siu_nodes, tcu_nodes, log_only, **kwargs):
        """
        method to trigger the single or multi upgrade according to the job_list count

            :param job_list: list of the jobs to trigger upgrade
            :type job_list: list
            :param user: User object that will be used to create the upgrade job
            :type user: `enm_user_2.User`
            :param siu_nodes: list of siu02 nodes
            :type siu_nodes: list
            :param tcu_nodes: list of tcu nodes
            :type tcu_nodes: list
            :param log_only: Indicates whether or not to log specific issues
            :type log_only: bool
            :type kwargs: list
            :param kwargs: list of arguments

            :raises e: Exception raised if creation of Shm job fails
        """
        if len(job_list) > 1:
            multi_job = MultiUpgrade(user=user, nodes=siu_nodes + tcu_nodes, upgrade_jobs_to_merge=job_list, **kwargs)
            self.job = multi_job
        try:
            self.job.create()
        except Exception as e:
            if not log_only:
                raise e

    def get_nodes_for_shm_27(self, nodes):
        """
        Helper method to get nodes and required information for SHM_27 profile
        :type nodes: list
        :param nodes: List of node(s) to be determine the package, and be included in the upgrade job

        :rtype: tuple
        :return: siu_nodes, tcu_nodes, nodes, loop_count
        """
        siu_nodes = self.get_node_list("SIU02", nodes)
        tcu_nodes = self.get_node_list("TCU02", nodes)
        loop_count = 2 if (siu_nodes and tcu_nodes) else 1
        if loop_count == 1:
            nodes = siu_nodes if siu_nodes else tcu_nodes
        return siu_nodes, tcu_nodes, nodes, loop_count

    def upgrade_setup(self, user, nodes, log_only=False, use_default=False, pib_values=None, **kwargs):
        """
        Helper method to create/import software package, and create an upgrade job

        :type nodes: list
        :param nodes: List of node(s) to be determine the package, and be included in the upgrade job
        :type user: `enm_user_2.User`
        :param user: User object that will be used to create the upgrade job
        :type log_only: bool
        :param log_only: Indicates whether or not to log specific issues
        :type use_default: bool
        :param use_default: Flag indicating whether or not to edit the default package
        :type kwargs: list
        :param kwargs: list of arguments
        :param pib_values: PIB values to be updated
        :type pib_values: dict

        :raises EnvironError: when nodes are empty
        :raises Exception: raised if creation of Shm job fails

        :rtype: `lib.shm.SoftwarePackage`
        :return: Software package object
        """
        job_list = []
        siu_nodes = []
        tcu_nodes = []
        loop_count = 1
        profile_name = kwargs.get("profile_name")
        if profile_name == "SHM_27":
            siu_nodes, tcu_nodes, nodes, loop_count = self.get_nodes_for_shm_27(nodes)
        if nodes:
            for i in range(loop_count):
                if profile_name == "SHM_27" and loop_count == 2:
                    nodes = siu_nodes if i == 0 else tcu_nodes
                software_package = self.create_and_import_software_package(user, nodes, use_default, pib_values, **kwargs)
                kwargs.update(software_package)
                self.job = UpgradeJob(user=user, nodes=nodes, **kwargs)
                job_list.append(self.job)
            self.upgrade_trigger(job_list, user, siu_nodes, tcu_nodes, log_only, **kwargs)
            return software_package.get('software_package')
        else:
            raise EnvironError('No synced nodes available to create upgrade job')

    @staticmethod
    def create_and_import_software_package(user, nodes, use_default=False, pib_values=None, **kwargs):
        """
        Create a SoftwarePackage object based upon the provided inputs

        :type nodes: list
        :param nodes: List of node(s) to be determine the package, and be included in the upgrade job
        :type user: `enm_user_2.User`
        :param user: User object that will be used to create the upgrade job
        :type use_default: bool
        :param use_default: Flag indicating whether or not to edit the default package
        :type pib_values: dict
        :param pib_values: PIB values to be updated
        :type kwargs: list
        :param kwargs: list of arguments

        :raises Exception: when generating software package object
        :raises HTTPError: when importing package to software pkg list
        :raises EnmApplicationError: when there is issue in retrieving node pkg details using cmedit

        :return: Dictionary containing a software package object
        :rtype: dict
        """
        use_default = (True if nodes[0].primary_type in ["MLTN", "LH", "MINI-LINK-Indoor", "MINI-LINK-669x"] else
                       use_default)
        software_package = SoftwarePackage(nodes=nodes, user=user, use_default=use_default, pib_values=pib_values, **kwargs)
        try:
            if not use_default:
                software_package.update_file_details_and_create_archive()
            software_operation = SoftwareOperations(user=user, package=software_package, ptype=nodes[0].primary_type)
            software_operation.import_package()
            if filesystem.does_file_exist(software_operation.zip_file_path) and not use_default:
                filesystem.delete_file(software_operation.zip_file_path)
        except Exception as e:
            raise EnmApplicationError(e.message)
        return {"software_package": software_package}

    @classmethod
    def enm_annotate_method(cls, user, nodes):
        """
        Wrapper method for enm_annotate, using the default admin

        :type nodes: list
        :param nodes: List of `enm_node.Node` instances
        :type user: `enm_user_2.User`
        :param user: Enm user instance who will query netex for poids
        :rtype: list
        :return: List of `enm_node.Node` instances
        """
        return annotate_fdn_poid_return_node_objects(nodes)

    @classmethod
    def execute_restart_delay(cls, nodes, delay=20 * 60):
        """
        Sets a delay on the nodes provided

        :type nodes: list
        :param nodes: List of `enm_node.Node` instances to set the delay upon
        :type delay: int
        :param delay: Value to delay set the delayed restart to in seconds

        :raises NetsimError: when executing netsim operation
        """
        cmd = 'setswinstallvariables:restartDelay={0};'.format(delay)
        if nodes:
            net_op = netsim_operations.NetsimOperation(nodes)
            try:
                net_op.execute_command_string(cmd)
            except Exception as e:
                raise NetsimError(e.message)

    def verify_unzip(self):
        """
        Verify is zip/unzip executables are already installed

        :return: True, if executables are installed else False
        :rtype: bool
        :raises ShellCommandReturnedNonZero: when unable to install zip or unzip
        """
        return self.cmd_exists("zip") and self.cmd_exists("unzip")

    @staticmethod
    def cmd_exists(cmd):
        """
        Check if path contains an executable file with given name
        :param cmd: Command to be checked
        :type cmd: str
        :return: True, if executable file exists else False
        :rtype: bool
        """
        path = os.environ["PATH"].split(os.pathsep)

        for prefix in path:
            filename = os.path.join(prefix, cmd)
            executable = os.access(filename, os.X_OK)
            is_not_directory = os.path.isfile(filename)
            if executable and is_not_directory:
                return True
        return False

    def install_unzip(self):
        """
        Verifies if zip/unzip executables are already installed, else installs them

        :raises ShellCommandReturnedNonZero: when unable to install zip or unzip
        """
        if self.verify_unzip():
            log.logger.debug("Zip/Unzip executables are already available in PATH! Skipping installation.")
        else:
            response = run_local_cmd(Command("yum -y install unzip zip"))
            if response.rc:
                raise ShellCommandReturnedNonZero("Unable to install zip or unzip from yum repository", response=response)

    @classmethod
    def determine_highest_mim_count_nodes(cls, nodes, profile, allocate=False):
        """
        Return the highest count of nodes based on the respective mim version

        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type profile: `enmutils_int.lib.profile.Profile`
        :param profile: Profile to deallocated from the node(s)
        :param allocate: Boolean to indicate if in allocation phase
        :type allocate: bool
        :rtype: list
        :return: List of `enm_node.Node` objects
        """
        log.logger.debug("Starting execution of function - determine_highest_mim_count_nodes")
        mim_grouping = {}
        mim_list = []
        for node in nodes:
            if node.mim_version not in mim_grouping.keys():
                mim_grouping[node.mim_version] = []
            mim_grouping.get(node.mim_version).append(node)
        for key in mim_grouping.iterkeys():
            if len(mim_grouping.get(key)) > len(mim_list):
                mim_list = mim_grouping.get(key)
        cls.deallocate_unused_nodes(list(set(nodes) - set(mim_list)), profile, allocate)
        log.logger.debug("Completed execution of function - determine_highest_mim_count_nodes")
        return mim_list

    @classmethod
    def determine_highest_model_identity_count_nodes(cls, profile_object, nodes, user):
        """
        Return the highest count of nodes based on the respective mim version

        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type profile_object: `lib.profile.Profile`
        :param profile_object: profile object
        :type user: `enm_user_2.User`
        :param user: user object
        :rtype: list
        :return: List of `enm_node.Node` objects
        :raises EnmApplicationError: when models are not availalble for the profile allocated nodes
        """
        log.logger.debug("Attempting to filter the nodes which are high in number with same model identity.....")
        available_models = cls.check_availability_of_identity_revision(user, nodes[0].primary_type)
        if available_models:
            nodes_with_same_omi_nmi = cls.get_nodes_same_omi_nmi(user, nodes)
            model_list = cls.get_model_list(nodes_with_same_omi_nmi)
            profile_object.deallocate_unused_nodes_and_update_profile_persistence(model_list)
            log.logger.debug("Completed filtering the nodes which are high in number with same model identity")
            if model_list:
                return model_list
            else:
                raise EnmApplicationError("Node model identities do not match with ENM model identities")
        else:
            raise EnmApplicationError("There are no matching models available")

    @staticmethod
    def validate_omi_equals_nmi(output):
        """
        Filters output and extracts valid nodes with same node and oss model identity
        :param output: List of output strings
        :type output: list

        :rtype: list
        :return: List of valid nodes
        """
        nodes_with_same_omi_nmi = []
        lines_to_exclude = ["NetworkElement", "NodeId", "nodeModelIdentity", "ossModelIdentity",
                            "instance(s)"]
        for line in output:
            if not any(word in line for word in lines_to_exclude) and len(line.strip()) != 0 and len(line.split()) == 3:
                node_id, oss_model_id, node_model_id = line.split()
                if oss_model_id == node_model_id:
                    nodes_with_same_omi_nmi.append(node_id)
        return nodes_with_same_omi_nmi

    @classmethod
    def filter_nodes_with_same_omi_nmi(cls, user, nodes):
        """
        Filters and returns the nodes list which have same OMI and NMI.

        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type user: `enm_user_2.User`
        :param user: user object
        :rtype: list
        :return: List of `enm_node.Node` objects which have same OMI and NMI
        """
        nodes_with_same_omi_nmi = []
        cmd = 'cmedit get {0} networkelement.(nodeModelIdentity,ossModelIdentity) -t'
        log.logger.debug("Attempting to filter nodes with same OMI and NMI")
        node_ids = [node.node_id for node in nodes]
        for chunk_nodes in chunks(node_ids, 500):
            filter_output = []
            response = user.enm_execute(cmd.format(";".join(chunk_nodes)))
            output = response.get_output()
            for each_word in output:
                if not("Error" in each_word or str(each_word) == "0 instance(s)"):
                    filter_output.append(each_word)
            if filter_output:
                nodes_with_same_omi_nmi.extend(cls.validate_omi_equals_nmi(filter_output))
        if not nodes_with_same_omi_nmi:
            log.logger.error("Failed to get the Same OSS Model Identity-Node model identity for profile assigned nodes")
        return nodes_with_same_omi_nmi

    @classmethod
    def get_nodes_same_omi_nmi(cls, user, nodes):
        """
        Validates and returns the nodes objects list which have same OMI and NMI.

        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type user: `enm_user_2.User`
        :param user: user object
        :rtype: list
        :return: List of `enm_node.Node` objects which have same OMI and NMI
        :raises EnmApplicationError: when there are no nodes with the same OMI and NMI.
        """
        nodes_with_same_omi_nmi = cls.filter_nodes_with_same_omi_nmi(user, nodes)
        if nodes_with_same_omi_nmi:
            log.logger.debug("Completed filtering {0} nodes which "
                             "have the same OMI and NMI".format(len(nodes_with_same_omi_nmi)))
        else:
            raise EnmApplicationError("There are no nodes with the same OMI and NMI")
        node_objects = [node for node in nodes if node.node_id in nodes_with_same_omi_nmi]
        return node_objects

    @staticmethod
    def get_model_list(nodes):
        """
        Return the nodes which have same model identity and are high in number.

        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :rtype: list
        :return: List of `enm_node.Node` objects which have same model identity and are high in number.
        """
        model_grouping = {}
        model_list = []
        list_node_id = []
        list_model_identity = []
        for node in nodes:
            node_id = node.node_id
            model_identity = node.model_identity
            list_node_id.append(node_id)
            list_model_identity.append(model_identity)
            if model_identity not in model_grouping.keys():
                model_grouping[model_identity] = []
            model_grouping.get(model_identity).append(node)
        dict_model_identity = dict(zip(list_node_id, list_model_identity))
        log.logger.debug("Model Identity of Nodes are {0}".format(dict_model_identity))
        for key in model_grouping.iterkeys():
            if len(model_grouping.get(key)) > len(model_list):
                model_list = model_grouping.get(key)
                log.logger.debug("Model chosen is {0} with {1} number of nodes".format(key, len(model_list)))
        return model_list

    @staticmethod
    def check_availability_of_identity_revision(user, node_type):
        """
        Create a copy of an existing file under a new name

        :param user: ENM user who will perform the query
        :type user: `enm_user_2.User`
        :param node_type: primary type of node
        :type node_type: str

        :return: list of available model identities
        :rtype: list
        :raises EnmApplicationError: when failed to retrieve NetworkElement product version MO describe information
        """
        log.logger.debug("Started checking the availability of identity revisions in ENM.....")
        available_models = []
        cmd = 'cmedit describe -neType={netype} -t'
        response = user.enm_execute(cmd.format(netype=node_type))
        if "0 instance(s)" in response.get_output():
            raise EnmApplicationError("Failed to retrieve NetworkElement product version information.")
        for line in response.get_output():
            if len(line.split('\t')) >= 4 and line.split('\t')[2] != '-' and line.split('\t')[3] != '-':
                available_models.append(str(line.split('\t')[6]))
        return available_models

    @staticmethod
    def deallocate_unused_nodes(unused_nodes, profile, allocate=False):
        """
        Deallocate the unused nodes

        :type unused_nodes: list
        :param unused_nodes: List of unused `enm_node.Node` objects, to be deallocated
        :type profile: `enmutils_int.lib.profile.Profile`
        :param profile: Name of the profile to remove from the node(s)
        :param allocate: Boolean to indicate if in allocation phase
        :type allocate: bool
        """
        if unused_nodes:
            if nodemanager_adaptor.can_service_be_used(profile=profile):
                nodemanager_adaptor.deallocate_nodes(profile, unused_nodes=unused_nodes)
            else:
                if allocate:
                    node_pool_mgr.remove_profile_from_nodes(unused_nodes, profile.NAME)
                else:
                    node_pool_mgr.deallocate_unused_nodes(unused_nodes, profile.NAME)
        else:
            log.logger.debug("No unused nodes to be deallocated")

    @staticmethod
    @retry(retry_on_exception=lambda err: isinstance(err, FailedNetsimOperation), wait_fixed=10000,
           stop_max_attempt_number=4)
    def set_netsim_values(nodes_list, nodes_param):
        """
        Runs the list of commands in a list of nodes

        :param nodes_list: A list of nodes
        :type nodes_list: list
        :param nodes_param: A list of netsim commands
        :type nodes_param: list

        :raises FailedNetsimOperation: when there is issue in executing netsim operation
        """
        if nodes_list:
            net_op = netsim_operations.NetsimOperation(nodes_list)
            for param in nodes_param:
                net_op.execute_command_string(param)

    @staticmethod
    def check_and_update_pib_values_for_packages(pib_values):
        """
        Checks and updates pib values

        :param pib_values: PIB values to be updated
        :type pib_values: bool
        """
        deployment_config_value = deploymentinfomanager_adaptor.check_deployment_config()
        if deployment_config_value in ["extra_small_network", "five_network", "soem_five_network"]:
            log.logger.debug("{0} network detected. Attempting to update the required pib values!".format(deployment_config_value))
            try:
                for key in pib_values:
                    current_value = deploymentinfomanager_adaptor.get_pib_value_on_enm(
                        "shmserv", key, service_identifier="shm-softwarepackagemanagement-ear")
                    if current_value == pib_values.get(key):
                        log.logger.debug(
                            "Pib value for {0} is already set required value - {1}".
                            format(key, current_value))
                    else:
                        log.logger.debug("Pib updated needed for {0} to {1}".format(key, pib_values.get(key)))
                        deploymentinfomanager_adaptor.update_pib_parameter_on_enm(
                            "shmserv", key, pib_values.get(key), service_identifier="shm-softwarepackagemanagement-ear")
            except Exception as e:
                log.logger.error("Exception occured while trying to update required pib parameters - {0}".format(e))
        else:
            log.logger.debug("Pib updates not needed for {0}!".format(deployment_config_value))


class SoftwarePackage(object):

    def __init__(self, nodes, user, pib_values=None, **kwargs):

        """
        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type user: `enm_user_2.User`
        :param user: User who will perform any ENM queries
        :type pib_values: dict
        :param pib_values: PIB values to be updated
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary
        """
        self.package_selector = EXISTING_PACKAGES.get(nodes[0].primary_type)
        self.user = user
        self.nodes = nodes
        self.additional = kwargs.pop('additional', False)
        self.LOCAL_PATH = kwargs.pop('local_path', "Error")
        self.profile_name = kwargs.get('profile_name', None)
        if not kwargs.get('use_default'):
            self.existing_package = kwargs.get('existing_package')
            self.file_paths = kwargs.get('file_paths')
            self.node_variants = []
            # Mim to be replaced
            self.mim_version = kwargs.get('mim_version')
            self.identity = kwargs.get('identity')
            # New and existing archives to be created or edited
            self.node_mim = None
            self.mim_version_last_digit_count = len(self.nodes[0].mim_version.split('.')[-1])
            self.node_identity = None
            self.new_package = None
            self.new_dir = None
            self.existing_dir = None
            self.revision_number = None
            # Files to update
            self.smo_info = None
            self.existing_ucf = None
            self.new_ucf = None
            self.admin_data = None
            self.package = None

        else:
            if self.profile_name in ["NPA_01", "NHC_04"]:
                self.new_package = self.package_selector[2]
            elif self.profile_name in ["ASU_01"]:
                self.new_package = self.package_selector[3]
            else:
                self.new_package = self.package_selector[1] if self.additional else self.package_selector[0]
            self.new_dir = os.path.join("/home", "enmutils", "shm", self.new_package)
            self.update_node_details()
        if pib_values:
            SHMUtils.check_and_update_pib_values_for_packages(pib_values)

    def update_node_identity_and_mim(self, node_data):
        """
            Helper function to update node details identity and mim
            :param node_data: Primary type details of node as in NODE_IDENTITY_MIMS
            :type node_data: str
        """
        self.new_package = NODE_IDENTITY_MIMS.get(node_data)[0]
        self.node_identity = NODE_IDENTITY_MIMS.get(node_data)[1]
        self.node_mim = NODE_IDENTITY_MIMS.get(node_data)[2]

    def update_node_details(self):
        """
            Function to update node details according to package details
        """
        if self.new_package == EXISTING_PACKAGES.get("MLTN")[0] and self.nodes[0].primary_type == "MLTN":
            self.update_node_identity_and_mim("MLTN")
        elif self.new_package == EXISTING_PACKAGES.get("MINI-LINK-Indoor")[0]:
            self.update_node_identity_and_mim("MINI-LINK-Indoor")
        elif self.new_package == EXISTING_PACKAGES.get("MINI-LINK-6352")[0]:
            self.update_node_identity_and_mim("MINI-LINK-6352_0")
        elif self.new_package == EXISTING_PACKAGES.get("MINI-LINK-6352")[1]:
            self.update_node_identity_and_mim("MINI-LINK-6352_1")
        elif self.new_package == EXISTING_PACKAGES.get("SIU02")[0]:
            self.update_node_identity_and_mim("SIU02")
        elif self.new_package == EXISTING_PACKAGES.get("TCU02")[0]:
            self.update_node_identity_and_mim("TCU02")
        elif self.new_package == EXISTING_PACKAGES.get("BSC")[0]:
            self.update_node_identity_and_mim("BSC_01")
        elif self.new_package == EXISTING_PACKAGES.get("BSC")[1]:
            self.update_node_identity_and_mim("BSC_02")
        elif self.new_package == EXISTING_PACKAGES.get("MINI-LINK-669x")[0]:
            self.update_node_identity_and_mim("MINI-LINK-669x_0")
        elif self.new_package == EXISTING_PACKAGES.get("MINI-LINK-669x")[1]:
            self.update_node_identity_and_mim("MINI-LINK-669x_1")

    def set_file_paths(self, primary_type):
        """
        Helper function to update file_path_details
        :param primary_type: Primary type details of node
        :type primary_type: str
        """
        log.logger.debug("Attempting to set the file paths according to node type....")
        if self.file_paths:
            self.file_paths = [os.path.join("/home", "enmutils", "shm", self.new_package, file_path)
                               for file_path in self.file_paths]
        elif primary_type in ["Router_6672", "Router6672", "Router6675"]:
            self.file_paths = [self.smo_info, self.admin_data]
        elif primary_type in ["MINI-LINK-6352"]:
            self.file_paths = [self.package]
        else:
            self.file_paths = [self.smo_info, self.new_ucf]
        log.logger.debug("Completed setting the file paths according to node type.")

    def get_package_xml_files(self, primary_type):
        """
        Helper function to update package file path details
        :param primary_type: Primary type details of node
        :type primary_type: str
        """
        if primary_type in ["MINI-LINK-6352"]:
            self.package = os.path.join("/home", "enmutils", "shm", self.new_package,
                                        "{0}{1}".format('package', '.xml'))

    def get_ucf_files(self, primary_type):
        """
        Helper function to update ucf file path details
        :param primary_type: Primary type details of node
        :type primary_type: str
        """
        log.logger.debug("Attempting to get the ucf file paths according to node type....")
        if primary_type in ["Router_6672", "Router6672", "Router6675"]:
            self.admin_data = os.path.join("/home", "enmutils", "shm", self.new_package,
                                           "{0}{1}".format('admin_data', '.xml'))
        else:
            exiting_ucf_value = self.existing_package if primary_type == "ERBS" else self.identity + "-up"
            new_ucf_value = self.new_package if primary_type == "ERBS" else self.node_identity.replace('/', '_') + "-up"
            self.existing_ucf = os.path.join("/home", "enmutils", "shm", self.new_package,
                                             "{0}{1}".format(exiting_ucf_value, '.xml'))
            self.new_ucf = os.path.join("/home", "enmutils", "shm", self.new_package,
                                        "{0}{1}".format(new_ucf_value, '.xml'))
        log.logger.debug("Completed getting the ucf file paths according to node type.")

    def get_smo_nmsinfo_files(self, primary_type):
        """
        Helper function to update smo or nmsinfo file path details
        :param primary_type: Primary type details of node
        :type primary_type: str
        """
        log.logger.debug("Attempting to set the smo nms info file paths according to node type....")
        info_file = 'SMOinfo.xml' if primary_type == "ERBS" else "nmsinfo.xml"
        self.smo_info = os.path.join("/home", "enmutils", "shm", self.new_package, info_file)
        log.logger.debug("Completed setting the smo nms info file paths according to node type.")

    def get_exact_identity(self, pkg):
        """
        Helper function to update ucf file path details
        :param pkg: package name containing identity and revision
        :type pkg: str
        :rtype: str
        :return: returns identity details fetched from package name details
        """
        log.logger.debug("Attempting to fetch the exact identity from package name....")
        count_delimiter = pkg.count('_')
        radio_pkg = pkg.count('-')
        if count_delimiter == 1 and radio_pkg == 1:
            return pkg.split('-')[0]
        elif count_delimiter != 0:
            return pkg.split('_')[0] if count_delimiter == 1 else "_".join(pkg.split('_', 2)[:2])
        else:
            return pkg

    def get_mim_version(self, primary_type):
        """
        Helper function to get the current mim version use to update the revision value with timestamp in
        upgrade package xml files
        For example R7D44_9999 is for Router6672/Router6675
        :param primary_type: Primary type details of node
        :type primary_type: str
        :rtype: str
        :return: returns mim version fetched from package name
        """
        return (self.existing_package.split('-', 1)[-1].split("_SF")[0] if primary_type in ["Router6672", "Router_6672", "Router6675"]
                else self.existing_package.split('_')[-1])

    def set_package_values(self, primary_type="ERBS"):
        """
        Sets the file and directory details for the upgrade package
        :param primary_type: Primary type details of node
        :type primary_type: str
        """
        log.logger.debug("Attempting to set the package values.....")
        if not self.existing_package:
            if self.profile_name in ["ASU_01"]:
                self.existing_package = self.package_selector[3]
            else:
                self.existing_package = self.package_selector[1] if self.additional else self.package_selector[0]

        # Mim and identity to be replaced
        self.mim_version = self.mim_version if self.mim_version else self.get_mim_version(primary_type)
        self.identity = self.identity if self.identity else self.get_exact_identity(self.existing_package)
        # New and existing archives to be created or edited
        if primary_type in ["Router6672", "Router_6672", "Router6675"]:
            self.node_identity = self.existing_package.split("-")[0]
            current_revision = self.existing_package.split("-")[1].strip("_SF")
            self.node_mim = self.update_mim_version(current_revision)
        elif primary_type in ["SCU"]:
            self.node_identity = "_".join(self.existing_package.split('_', 2)[:2])
            self.node_mim = self.get_revision_from_ne_product_version()
        else:
            self.node_identity = self.get_identity_from_ne_describe()
            self.node_mim = self.get_revision_from_ne_product_version()

        if primary_type in ["MINI-LINK-6352"]:
            self.revision_number = self.existing_package.split('_')[2]
            self.new_package = self.existing_package.replace(self.revision_number, self.node_mim)
            self.get_package_xml_files(primary_type)
        else:
            self.new_package = "{0}_{1}".format(self.node_identity, self.node_mim).replace('/', '_')
        self.existing_dir = os.path.join("/home", "enmutils", "shm", self.existing_package)
        self.new_dir = os.path.join("/home", "enmutils", "shm", self.new_package)
        log.logger.debug("Shm Package details are: \n Existing package is: {0} \n New package is: {1}".format(
            self.existing_package, self.new_package))
        # Files to update
        self.get_smo_nmsinfo_files(primary_type)
        self.get_ucf_files(primary_type)
        self.set_file_paths(primary_type)
        log.logger.debug("Completed updating package values.....")

    def edit_file_values(self, primary_type="ERBS"):
        """
        Method for substitute existing mim values with the required mim version
        :param primary_type: Primary type details of node
        :type primary_type: str
        """
        if self.node_mim:
            for file_path in self.file_paths:
                if primary_type in ["MINI-LINK-6352"]:
                    cmd = "/bin/sed -i -e 's/{0}/{1}/g' {2}".format(self.revision_number, self.node_mim, file_path)
                else:
                    cmd = "/bin/sed -i -e 's/{0}/{1}/g' {2}".format(self.mim_version, self.node_mim, file_path)
                self.run_cmd_and_evaluate_rc(cmd, "Failed to correctly edit revision in files: ")
        if self.node_identity:
            for file_path in self.file_paths:
                cmd = "/bin/sed -i -e 's/{0}/{1}/g' {2}".format(self.identity.replace('/', '_'),
                                                                self.node_identity.replace('/', '_'), file_path)
                self.run_cmd_and_evaluate_rc(cmd, "Failed to correctly edit identity in files: ")
        if primary_type in ["Router6672", "Router_6672", "Router6675", "SCU"]:
            xml_file = minidom.parse(self.smo_info)
            file_items = xml_file.getElementsByTagName('UpgradePackage')
            name_value = file_items[0].attributes['name'].value
            cmd = "/bin/sed -i -e 's/{0}/{1}/g' {2}".format(name_value.encode(), self.new_package, self.smo_info)
            self.run_cmd_and_evaluate_rc(cmd, "Failed to correctly edit name field in nmsinfo.xml")

    def edit_file_values_for_asu(self):
        """
        Method for substitute existing mim values with the required mim version for ASU01 profile
        """
        if self.node_mim:
            for file_path in self.file_paths:
                if file_path in self.smo_info:
                    name_value = self.parse_values_in_xml_file(file_path, 'ProductData', 'productRevision')
                    cmd = "/bin/sed -i -e 's@{0}@{1}@g' {2}".format(name_value.encode(), self.node_mim, file_path)
                    self.run_cmd_and_evaluate_rc(cmd, "Failed to correctly edit revision in files: ")
                else:
                    cmd = "/bin/sed -i -e 's/{0}/{1}/g' {2}".format(self.existing_package.split('-')[-1], self.node_mim,
                                                                    file_path)
                    self.run_cmd_and_evaluate_rc(cmd, "Failed to correctly edit revision in files: ")
        if self.node_identity:
            for file_path in self.file_paths:
                if file_path in self.smo_info:
                    name_value = self.parse_values_in_xml_file(file_path, 'ProductData', 'productNumber')
                    cmd = "/bin/sed -i -e 's@{0}@{1}@g' {2}".format(name_value.encode(),
                                                                    self.node_identity.replace('/', '_'), file_path)
                    self.run_cmd_and_evaluate_rc(cmd, "Failed to correctly edit identity in files: ")
                else:
                    cmd = "/bin/sed -i -e 's/{0}/{1}/g' {2}".format(self.identity.replace('/', '_'),
                                                                    self.node_identity.replace('/', '_'), file_path)
                    self.run_cmd_and_evaluate_rc(cmd, "Failed to correctly edit identity in files: ")
        name_value = self.parse_values_in_xml_file(self.smo_info, 'UpgradePackage', 'name')
        cmd = "/bin/sed -i -e 's@{0}@{1}@g' {2}".format(name_value.encode(), self.new_package, self.smo_info)
        self.run_cmd_and_evaluate_rc(cmd, "Failed to correctly edit name field in nmsinfo.xml")

    def parse_values_in_xml_file(self, file_name, tag_name, name_value):
        """
        Method for pasring values in xml file and return the value of required name
        :rtype: str
        :return: returns the expected value of name in xml file
        """
        xml_file = minidom.parse(file_name)
        file_items = xml_file.getElementsByTagName(tag_name)
        name_value = file_items[0].attributes[name_value].value
        return name_value

    def update_file_details_and_create_archive(self):
        """
        Extract the files, update and recreate the archive
        :raises EnvironmentError: when the directory /home/enmutils/shm unable to find
        """
        if os.path.exists(self.LOCAL_PATH):
            self.set_package_values(primary_type=self.nodes[0].primary_type)
            SHMUtils().install_unzip()
            for directory in [self.new_dir, self.existing_dir]:
                if filesystem.does_dir_exist(directory):
                    filesystem.remove_dir(directory)
            self.run_cmd_and_evaluate_rc(Command("/usr/bin/unzip -o {0}.zip -d {1}".format(self.existing_dir, self.new_dir)),
                                         "Unable to unzip archive: ")
            if self.new_ucf in self.file_paths:
                filesystem.move_file_or_dir(self.existing_ucf, self.new_ucf)
            if self.profile_name in ["ASU_01"]:
                self.edit_file_values_for_asu()
            else:
                self.edit_file_values(primary_type=self.nodes[0].primary_type)
            self.run_cmd_and_evaluate_rc(Command("/usr/bin/zip -rj {0} {0}/*".format(self.new_dir), timeout=180),
                                         "Unable to zip archive: ")
            filesystem.remove_dir(self.new_dir)
        else:
            raise EnvironmentError("SHM package location path /home/enmutils/shm was not found, "
                                   "cannot proceed package installation further")

    @staticmethod
    def run_cmd_and_evaluate_rc(cmd, msg):
        """
        Run the given command and raise an exception if the rc is not 0

        :type cmd: `shell.Command`
        :param cmd: Command to be executed locally
        :type msg: str
        :param msg: Message to output if the command fails
        :raises ShellCommandReturnedNonZero: when response was not a success
        """
        response = run_local_cmd(cmd)
        if response.rc is not 0:
            raise ShellCommandReturnedNonZero(msg, response=response)

    def get_ne_product_version(self):
        """
        Retrieve the product version from the provided node.
        """
        cmd = 'cmedit get {node_ids} NetworkElement.neProductVersion'
        response = self.user.enm_execute(cmd.format(node_ids=";".join([node.node_id for node in self.nodes])))
        if "0 instance(s)" in response.get_output():
            raise EnmApplicationError("Failed to retrieve NetworkElement product version MO.")
        return response

    def get_netype_describe(self):
        """
        Retrieve the product version from the provided node.
        :raises EnmApplicationError: When there are no instances for the network available
        :rtype: str
        :return: returns response output for cmedit command
        """
        cmd = 'cmedit describe -neType={netype} -t'
        response = self.user.enm_execute(cmd.format(netype=self.nodes[0].primary_type))
        if "0 instance(s)" in response.get_output():
            raise EnmApplicationError("Failed to retrieve NetworkElement product version MOdescribe information.")
        return response.get_output()

    @staticmethod
    def identity_filter_special_chars(identities):
        """
        Filter the identities and returns a valid identity
        :type identities: list
        :param identities: list of identities availalble in ENM for profile nodes
        :rtype: str
        :return: valid identity
        :raises EnmApplicationError: when failed to retrieve network identity information
        """
        log.logger.debug("Attempting to filter the identities based on product identity and revision value:")
        for id_line in identities:
            id_temp = id_line.split('\t')[2]
            id_temp = re.sub("_+", "_", id_temp)
            id_temp = id_temp.strip("_")
            id_rev = id_line.split('\t')[3]
            id_rev = re.sub("_+", "_", id_rev)
            id_rev = id_rev.strip("_")
            if id_temp not in ['-', '-_'] and id_rev != '-':
                return str(id_temp)
        log.logger.debug("NO valid identity is available for package creation")
        raise EnmApplicationError("Failed to retrieve NetworkElement product identity information.")

    def get_identity_from_ne_describe(self):
        """
        Retrieve the product revision from the provided nodes.

        :rtype: str
        :return: The incremented revision number
        :raises EnmApplicationError: when failed to retrieve network identity information
        """
        log.logger.debug("Attempting to get available product identity details from ENM ")
        identities = []
        all_mim_or_model = []
        all_ne_version = []
        response = self.get_netype_describe()
        model_ids = self.get_node_model_identities()
        for line in response:
            for node in self.nodes:
                mim_or_model, ne_version = self.select_node_version_and_model_info(node, model_ids)
                all_mim_or_model.append(mim_or_model)
                all_ne_version.append(ne_version)
                if mim_or_model in line and ne_version in line:
                    identities.append(line)
                    break
        unique_mim_or_model = dict([(each_mim, all_mim_or_model.count(each_mim)) for each_mim in set(all_mim_or_model)])
        log.logger.debug("Using mim_or_model {0}".format(unique_mim_or_model))
        unique_all_ne_version = dict([(each_ne, all_ne_version.count(each_ne)) for each_ne in set(all_ne_version)])
        log.logger.debug("Using ne version {0}".format(unique_all_ne_version))
        log.logger.debug("The identities are : {0}".format(identities))
        if not identities:
            raise EnmApplicationError("Failed to retrieve NetworkElement product identity information.")
        return self.identity_filter_special_chars(identities)

    @staticmethod
    def select_node_version_and_model_info(node, model_ids):
        """
        Determine if there is a matching value available from ENM or if the stored information should be used

        :param node: Load node instance to be used in the upgrade
        :type node: `load_node.Node`
        :param model_ids: Dictioanry containing oss-model-id information
        :type model_ids: dict

        :return: Tuple containing the mim or model id, the node version
        :rtype: tuple
        """
        mim_or_model, ne_version = None, None
        if model_ids.get(node.node_id):
            try:
                mim_or_model = model_ids.get(node.node_id).split('-')[-1]
                ne_version = model_ids.get(node.node_id).split('-')[0]
            except Exception as e:
                log.logger.debug("Could not retrieve model information, error encountered {0} for model_id {1}"
                                 .format(str(e), model_ids.get(node.node_id)))
        if not mim_or_model or not ne_version:
            mim_or_model = node.mim_version if node.primary_type == "ERBS" else node.model_identity
            ne_version = node.node_version
        return mim_or_model, ne_version

    @staticmethod
    def sorted_alphanumeric(sort_list):
        """
        Sorts the given alphanumeric list.
        :rtype: list
        :return: List of sorted alphanumeric elements
        """

        def convert(text):
            return int(text) if text.isdigit() else text

        def alphanum_key(key):
            return [convert(character) for character in re.split('([0-9]+)', key)]

        return sorted(sort_list, key=alphanum_key)

    def get_revision_from_ne_product_version(self):
        """
        Retrieve the product revision from the provided nodes.

        :rtype: str
        :return: The incremented revision number
        :raises EnmApplicationError: when failed to retrieve network element revision information
        """
        revisions = []
        numbers = []
        response = self.get_ne_product_version()
        for line in response.get_output():
            if 'revision=' in line:
                revisions.append(line.split('revision=')[-1].split(',')[0])
            if 'identity=' in line:
                numbers.append(line.split('identity=')[-1].split(',')[0])
        if not revisions and not numbers:
            raise EnmApplicationError("Failed to retrieve NetworkElement product version information.")
        self.node_variants = list(set(numbers))
        revisions_without_time_stamp = [rev.split('-')[0] for rev in revisions]
        highest_revision = self.sorted_alphanumeric(set(revisions_without_time_stamp))[-1]
        current_highest_revision_on_chosen_nodes = highest_revision.split('}')[0]
        log.logger.debug("Highest available mim_version from all the allocated nodes without including time stamp is : "
                         "{0}".format(current_highest_revision_on_chosen_nodes))
        return self.update_mim_version(current_highest_revision_on_chosen_nodes)

    def update_mim_version(self, mim_version):
        """
        Increments the mim version if digits contained

        :type mim_version: str
        :param mim_version: String mim version of the node group

        :rtype: str
        :return: Incremented String mim version of the node group
        :raises EnvironmentError: when mim_version is not in correct format or null
        """
        log.logger.debug("Attempting to update mim version....")
        if mim_version:
            mim_time_stamp = datetime.datetime.now().strftime('%m%d%H%M')
            node_type = self.nodes[0].primary_type
            if node_type in ["ERBS", "RadioNode", "SCU"]:
                mim = mim_version[:4] + mim_time_stamp
            elif node_type in ["Router_6672", "Router6672", "Router6675"]:
                mim = (mim_version.split('_')[0] + "_" + mim_time_stamp)
            else:
                mim_digit_count = (self.mim_version_last_digit_count if self.mim_version_last_digit_count != 0
                                   else len(mim_version))
                mim = mim_version[:mim_digit_count] + mim_time_stamp
            log.logger.debug("Revision selected for {1} is: {0}".format(mim, node_type))
            return mim
        else:
            raise EnvironmentError("Cannot increment mim version, mim_version is empty: {0}".format(mim_version))

    def get_node_model_identities(self):
        """
        Query ENM for the ossModeIdentities of the instance nodes

        :return: Dictionary containing the ossModeIdentities of the instance nodes
        :rtype: dict
        """
        cmd = "cmedit get {0} NetworkElement.ossModelIdentity -ne={1} -t".format(
            ";".join([node.node_id for node in self.nodes]), self.nodes[0].primary_type)
        model_ids = {}
        response = self.user.enm_execute(cmd)
        if "0 instance(s)" in response.get_output():
            log.logger.debug("Failed to retrieve NetworkElement ossModelIdentities from ENM.")
            return model_ids
        for line in response.get_output()[2:-2]:
            values = line.strip().split("\t")
            try:
                model_ids[values[0]] = values[1]
            except IndexError:
                log.logger.debug("Unable to correctly parse values, supplied values:: {0}".format(values))
        return model_ids


class SHMLicense(object):
    def __init__(self, user, node, same_id_for_all_licenses="y",
                 same_sequence_for_all_licenses="y", fingerprint_id=None, **kwargs):
        """
        SHMLicense constructor

        :type node: `enm_node.Node`
        :param node: node object to generate license on (Node)
        :type same_id_for_all_licenses: str
        :param same_id_for_all_licenses: arg for shm gen_license script (string)
        :type same_sequence_for_all_licenses: str
        :param same_sequence_for_all_licenses: arg for shm gen_license script (y or n) (string)
        :type user: `enm_user_2.User`
        :param user: user to use for the REST request (EnmUser)
        :type fingerprint_id: str
        :param fingerprint_id: fingerprint_id
        :param kwargs: A dictionary of optional keyword arguments
        :type kwargs: dict
        """
        self.node = node
        self.random_suffix = arguments.get_random_string(4)
        self.number_of_licenses = str(kwargs.get("number_of_licenses", 1))  # the number of licenses to generate on given node
        self.same_id_for_all_licenses = same_id_for_all_licenses
        self.sequence_number = kwargs.get("sequence_number", "9000")  # arg for shm gen_license script
        self.same_sequence_for_all_licenses = same_sequence_for_all_licenses
        self.elsn_id = kwargs.get("elsn_id") if kwargs.get("elsn_id") else "elsn_id_{0}".format(self.random_suffix)  # arg for shm gen_license script
        self.user = user
        self.fingerprint_id = fingerprint_id
        self.node_ptype = self.node.primary_type
        self.nid = self.node.node_id
        self.headers_dict = JSON_SECURITY_REQUEST
        self.file_name = None
        self.path_to_license_key = None
        self._license_script_path = None
        self.network = "LTE"

    def generate(self):
        """
        Generate valid license key
        :raises RuntimeError: when failed to generate valid shm license key
        """
        new_dir = '/tmp/' + self.random_suffix
        gen_script = LICENSE_GENERATION_SCRIPT_FOLDER + '/*'
        if not self.fingerprint_id:
            self._get_fingerprint()
        str_cmd = "mkdir %s ; cp %s %s" % (new_dir, gen_script, new_dir)
        run_local_cmd(Command(str_cmd))
        sleep(0.2)
        filesystem.assert_dir_exists(new_dir)
        licence_script = new_dir + '/' + LICENSE_GENERATION_SCRIPT_NAME
        shm_script_path = "{0} {1} {2} {3}".format(
            licence_script, self.fingerprint_id, self.sequence_number, self.network)
        with mutexer.mutex("generate_licence"):
            if "has been created under your home folder" not in run_local_cmd(Command(shm_script_path)).stdout:
                raise RuntimeError("Failed to generate a valid shm license key zip.")

        self.file_name = "license_{0}_{1}_{2}.zip".format(self.fingerprint_id, self.sequence_number, self.network)
        self.path_to_license_key = "/root/{0}".format(self.file_name)

        log.logger.debug("License key file generated: {0}".format(self.path_to_license_key))
        run_local_cmd(Command('rm -rf %s' % new_dir))

    @retry(retry_on_exception=lambda e: isinstance(e, (EnvironmentError, HTTPError)), wait_fixed=60000,
           stop_max_attempt_number=3)
    def import_keys(self):
        """
        Import license key to SHM

        :raises Exception: when the attempt to delete the license key on enm fails
        :raises EnvironmentError: when there is no license key available
        """
        if not self.path_to_license_key:
            raise EnvironmentError("There is no available license key.")
        if self.fingerprint_id in self.get_imported_keys(user=self.user):
            self.delete(delete_on_enm_only=True)
        response = self.user.post(SHM_LICENSE_UPLOAD_ENDPOINT, files={'uploadfile': open(self.path_to_license_key)})
        raise_for_status(response, message_prefix="Unable to import license key {0}. Response status:")
        log.logger.debug("Successfully uploaded license {0}.".format(self.file_name))

    @retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_fixed=60000, stop_max_attempt_number=3)
    def delete(self, delete_on_enm_only=False):
        """
        Delete license key from SHM

        :type delete_on_enm_only: bool
        :param delete_on_enm_only: Boolean flag indicating, whether to delete from both the local storage and ENM
        :raises HTTPError:  when the attempt to delete the license key was not a success
        :raises EnmApplicationError: when the finger_print is not generated properly



        """
        log.logger.debug("Starting deletion of the license key..")
        try:
            if not delete_on_enm_only and self.path_to_license_key is not None and filesystem.does_file_exist(self.path_to_license_key):
                filesystem.delete_file(self.path_to_license_key)
            if not self.fingerprint_id:
                self._get_fingerprint()

            data = {'deleteKeyFiles': [{'fingerPrint': self.fingerprint_id, 'sequenceNumber': self.sequence_number}]}

            response = self.user.post(SHM_LICENSE_DELETE_ENDPOINT, data=json.dumps(data), headers=self.headers_dict)
            raise_for_status(response, message_prefix="Unable to delete license key {0}. Response status:")
            if response.json()["status"] != "success":
                raise HTTPError("Unable to delete license key {0}. Response status: {1}".format(self.file_name,
                                                                                                response.json()[
                                                                                                    "status"]),
                                response=response)
            else:
                log.logger.debug("Successfully deleted license. Node: {0}, Fingerprint: {1},"
                                 " Sequence Number: {2}".format(self.node.node_id,
                                                                self.fingerprint_id,
                                                                self.sequence_number))
        except Exception as e:
            raise EnmApplicationError(str(e))

    def _get_fingerprint(self):
        """
        Get fingerprint associated with node for license
        :raises AttributeError: when the finger_print_id is missing in response
        :raises ScriptEngineResponseValidationError: when fingerprint key is not available in response
        """

        response = self.user.enm_execute(NODE_FINGERPRINT_COMMAND.format(node_id=self.node.node_id))
        if "fingerprint :" not in " ".join(response.get_output()):
            raise ScriptEngineResponseValidationError(
                "Failed to get fingerprint of node={0}\n"
                "RESPONSE: {1}".format(self.node.node_id, "\n".join(response.get_output())), response=response)

        try:
            self.fingerprint_id = re.search(GET_FINGERPRINT_REGEX, " ".join(response.get_output())).group(0)
        except AttributeError:
            raise AttributeError("Unable to find nodes fingerprint in response: {0}"
                                 " using regex {1}".format(response.get_output(), GET_FINGERPRINT_REGEX))

        log.logger.debug("The fingerprint returned for node {0} is {1}".format(self.node.node_id, self.fingerprint_id))

    def _teardown(self):
        """
        Teardown method to be used with workload profile teardown
        """
        self.delete()

    @classmethod
    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=60000, stop_max_attempt_number=3)
    def get_imported_keys(cls, user):
        """
        Get all imported license keys

        :type user: `enm_user_2.User`
        :param user: user to use for the REST request

        :rtype: list
        :returns: list of imported license keys in the SHM application
        """
        cls.user = user
        payload = {
            "offset": 1,
            "limit": 50,
            "sortBy": "importedOn",
            "orderBy": "asc"
        }
        response = cls.user.post(SHM_LICENSE_LIST_ENDPOINT, json=payload, headers=SHM_LONG_HEADER)
        raise_for_status(response, message_prefix="Unable to retrieve license keys. Response status: ")
        return [str(res.get('fingerPrint')) for res in response.json().get('result')]

    @classmethod
    def install_license_script_dependencies(cls):
        """
        Install dependencies needed for License key generation
        """
        SHMUtils().install_unzip()

        _license_script_path = os.path.join(unipath.Path(pkgutil.get_loader('enmutils_int').filename),
                                            "external_sources", "scripts")
        run_local_cmd(Command("rm -rf " + LICENSE_GENERATION_SCRIPT_FOLDER))
        run_local_cmd(
            Command("unzip -o {0}/MultiLIC_Script_updated.zip -d /tmp/".format(_license_script_path), timeout=5 * 60))
        run_local_cmd(Command("chmod 755 " + LICENSE_GENERATION_SCRIPT_FOLDER + "*.sh"))
        log.logger.debug("Successfully unzipped License key generation scripts to /tmp directory on the server.")
