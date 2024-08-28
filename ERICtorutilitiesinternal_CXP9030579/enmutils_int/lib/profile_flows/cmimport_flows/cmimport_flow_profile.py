import os
import pkgutil
import re
import time
from itertools import cycle

import unipath

from enmutils.lib import log, persistence, filesystem
from enmutils.lib.exceptions import EnvironWarning
from enmutils.lib.timestamp import get_human_readable_timestamp
from enmutils_int.lib import common_utils
from enmutils_int.lib.cm_import import (get_total_num_mo_changes, CmImportDeleteLive, CmImportCreateLive,
                                        ImportProfileContextManager, CmImportUpdateLive, CmImportLive,
                                        FILE_BASE_LOCATION)
from enmutils_int.lib.ddp_info_logging import update_cm_ddp_info_log_entry
from enmutils_int.lib.profile import CMImportProfile
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

SLEEP_TIME = 3600


class CmImportFlowProfile(CMImportProfile, GenericFlow):

    def run(self):
        """
        Run method inherited from CMImportProfile
        """

    def __init__(self, *args, **kwargs):
        self.NAME = self.__class__.__name__
        super(CmImportFlowProfile, self).__init__(*args, **kwargs)
        self.NEW_VERSION = False

    def setup_flow(self, user=None, nodes=None):
        """
        Carry out the setup required to execute the flows of the CM Import profiles

        :param user: Optional previously created user object
        :type user: `enmutils.lib.enm_user_2.User`
        :param nodes: Already fetched node objects
        :type nodes: list
        :return: CmImportSetupObject containing the nodes, user, and expected_num_mo_changes of the cmimport object
        :rtype: CmImportSetupObject
        """

        nodes = nodes or self.nodes_list
        user = user or self.create_users(number=1, roles=self.USER_ROLES, fail_fast=False, retry=True)[0]
        expected_num_mo_changes = get_total_num_mo_changes(self.MO_VALUES, len(nodes))
        ts = get_human_readable_timestamp()
        update_cm_ddp_info_log_entry(self.NAME, "{0} {1} {2}\n".format(ts, self.NAME, expected_num_mo_changes))
        cmimport_setup_object = CmImportSetupObject(nodes, user, expected_num_mo_changes)
        if self.NAME == "CMIMPORT_26":
            self.NEW_VERSION = any(node.node_version == '1-17' for node in nodes)

        return cmimport_setup_object

    def cmimport_create_delete_live_objects(self, cmimport_setup_object, name, interface, file_ending, timeout):
        """
        Creates the CmImportCreateLive and CmImportDeleteLive objects

        :param name: import name
        :type name: str
        :param cmimport_setup_object: an object containing the nodes, user, and expected_num_mo_changes of the cmimport object
        :type cmimport_setup_object: CmImportSetupObject
        :param interface: interface can be NBI or CLI. If the interface is NBIv1 or NBIv2 it is specified,
                          interface=None leaves the interface as the default route through the CLI
        :type interface: str or None
        :param file_ending: .xml or .txt depending on whether the file type is 3GPP or dynamic, respectively
        :type file_ending: str
        :param timeout: timeout for the import job
        :type timeout: int

        :return: create_live_obj, delete_live_obj: CmImportCreateLive object, CmImportDeleteLive object
        :rtype: create_live_obj, delete_live_obj: cm_import.CmImportCreateLive, cm_import.CmImportDeleteLive
        """

        create_live_obj = CmImportCreateLive(
            name='{0}_create'.format(name),
            user=cmimport_setup_object.user,
            nodes=cmimport_setup_object.nodes,
            template_name='{0}_create{1}'.format(name, file_ending),
            flow=self.FLOW,
            file_type=self.FILETYPE,
            interface=interface,
            expected_num_mo_changes=cmimport_setup_object.expected_num_mo_changes,
            error_handling=self.ERROR_HANDLING if hasattr(self, "ERROR_HANDLING") and self.ERROR_HANDLING else None,
            timeout=timeout
        )

        delete_live_obj = CmImportDeleteLive(
            name='{0}_delete'.format(name),
            user=cmimport_setup_object.user,
            nodes=cmimport_setup_object.nodes,
            template_name='{0}_delete{1}'.format(name, file_ending),
            flow=self.FLOW,
            file_type=self.FILETYPE,
            interface=interface,
            expected_num_mo_changes=cmimport_setup_object.expected_num_mo_changes,
            error_handling=self.ERROR_HANDLING if hasattr(self, "ERROR_HANDLING") and self.ERROR_HANDLING else None,
            timeout=timeout
        )

        return create_live_obj, delete_live_obj

    def cmimport_update_live_objects(self, cmimport_setup_object, name, interface, file_ending, timeout):
        """
        Creates the CmImportUpdateLive default and modify objects

        :param name: import name
        :type name: str
        :param cmimport_setup_object: an object containing the nodes, user, and expected_num_mo_changes of the cmimport object
        :type cmimport_setup_object: CmImportSetupObject
        :param interface: interface can be NBI or CLI. If the interface is NBIv1 or NBIv2 it is specified,
                          interface=None leaves the interface as the default route through the CLI
        :type interface: str or None
        :param file_ending: .xml or .txt depending on whether the file type is 3GPP or dynamic, respectively
        :type file_ending: str
        :param timeout: timeout for the import job
        :type timeout: int
        :return: default_obj, modify_obj: CmImportUpdateLive objects
        :rtype: default_obj, modify_obj: cm_import.CmImportUpdateLive, cm_import.CmImportUpdateLive
        """
        default_obj = CmImportUpdateLive(
            user=cmimport_setup_object.user,
            name='{0}_default'.format(name),
            mos=self.MOS_DEFAULT_NEW if self.NEW_VERSION else self.MOS_DEFAULT,
            nodes=cmimport_setup_object.nodes,
            template_name='{0}_default{1}'.format(name, file_ending),
            flow=self.FLOW,
            file_type=self.FILETYPE,
            expected_num_mo_changes=cmimport_setup_object.expected_num_mo_changes,
            timeout=timeout,
            interface=interface,
            error_handling=self.ERROR_HANDLING if hasattr(self, 'ERROR_HANDLING') else None
        )

        modify_obj = CmImportUpdateLive(
            user=cmimport_setup_object.user,
            name='{0}_modify'.format(name),
            mos=self.MOS_MODIFY_NEW if self.NEW_VERSION else self.MOS_MODIFY,
            nodes=cmimport_setup_object.nodes,
            template_name='{0}_modify{1}'.format(name, file_ending),
            flow=self.FLOW,
            file_type=self.FILETYPE,
            expected_num_mo_changes=cmimport_setup_object.expected_num_mo_changes,
            timeout=timeout,
            interface=interface,
            error_handling=self.ERROR_HANDLING if hasattr(self, 'ERROR_HANDLING') else None
        )

        return default_obj, modify_obj

    def get_cmimport_objects(self, cmimport_setup_object):
        """
        Return the default and modify cmimport objects to be used in the import flow

        :param cmimport_setup_object: an object containing the nodes, user, and expected_num_mo_changes of the cmimport object
        :type cmimport_setup_object: CmImportSetupObject

        :return: CmImportCreateLive and CmImportDeleteLive objects
        :rtype: cm_import.CmImportCreateLive, cm_import.CmImportDeleteLive
        """

        name = self.NAME.lower()
        file_ending = '.txt' if self.FILETYPE == 'dynamic' else '.xml'
        interface = self.INTERFACE if hasattr(self, 'INTERFACE') else None
        timeout = self.TIMEOUT if hasattr(self, 'TIMEOUT') else None

        log.logger.debug(
            'Creating cmimport objects for profile: {0}, import type: {1}'.format(self.NAME, self.IMPORT_TYPE))

        if self.IMPORT_TYPE == 'CreateDeleteLive':
            return self.cmimport_create_delete_live_objects(cmimport_setup_object, name, interface, file_ending,
                                                            timeout)

        else:
            return self.cmimport_update_live_objects(cmimport_setup_object, name, interface, file_ending, timeout)

    def initial_setup(self):
        """
        Initial setup for import flow.

        :return: context_mgr: ImportProfileContextManager, recovery: bool, default_obj: CmImportUpdateLive objects
        :rtype: context_mgr, recovery, default_obj
        """
        cmimport_setup_object = self.setup_flow()
        default_obj, modify_obj = self.get_cmimport_objects(cmimport_setup_object)
        recovery = self.ATTEMPT_RECOVERY if hasattr(self, 'ATTEMPT_RECOVERY') else True
        context_mgr = ImportProfileContextManager(self, default_obj=default_obj, modify_obj=modify_obj,
                                                  attempt_recovery=recovery)
        return context_mgr, recovery, default_obj

    def setup(self):
        """
        The funtionality responsible for setup Retry Mechanism.

        :return: context_mgr: ImportProfileContextManager, recovery: bool, default_obj: CmImportUpdateLive objects,
        context_mgr.setup_completed: bool
        :rtype: context_mgr, recovery, default_obj, context_mgr.setup_completed
        """
        log.logger.debug("Attempting to retry initial setup")
        log.logger.debug("The profile is sleeping for {0}".format(SLEEP_TIME))
        time.sleep(SLEEP_TIME)
        log.logger.debug("Start of retry attempt for setup.")
        self.exchange_nodes()
        context_mgr, recovery, default_obj = self.initial_setup()
        return context_mgr, recovery, default_obj, context_mgr.setup_completed

    def retry_initial_setup(self, context_mgr):
        """
        Retry Initial setup for import flow if it encounters any error

        :param context_mgr: ImportProfileContextManager object
        :type context_mgr: object

        :return: context_mgr: ImportProfileContextManager, recovery: bool, default_obj: CmImportUpdateLive objects
        :rtype: context_mgr, recovery, default_obj
        """
        retry = True
        while retry:
            log.logger.debug("The status of setup_completed : {0}".format(context_mgr.setup_completed))
            context_mgr, recovery, default_obj, context_mgr.setup_completed = self.setup()
            if context_mgr.setup_completed:
                retry = False
        return context_mgr, recovery, default_obj

    def execute_cmimport_common_flow(self):
        """
        Execute the part of the cmimport flow common to all import profiles. Create the ImportProfileContextManager then
        run the import flow.

        """
        context_mgr, recovery, default_obj = self.initial_setup()

        if not context_mgr.setup_completed:
            context_mgr, recovery, default_obj = self.retry_initial_setup(context_mgr)

        self.state = "RUNNING"
        iterations = self.NUM_ITERATIONS if hasattr(self, "NUM_ITERATIONS") else 1
        if not recovery:
            self.teardown_list.append(persistence.picklable_boundmethod(
                default_obj.restore_default_configuration_via_import))
        while self.keep_running():
            context_mgr.manage_sleep()
            for i in range(0, iterations):
                try:
                    log.logger.debug('Attempting import: {0}/{1}'.format(i + 1, iterations))
                    context_mgr.run_import()
                except Exception as e:
                    self.add_error_as_exception(e)
                if self.NAME == 'CMIMPORT_01':
                    log.logger.debug('Sleeping until next import attempt')
                    time.sleep(8)


class SimplifiedParallelCmImportFlow(GenericFlow):
    CGI_VALUES = []

    def execute_flow(self):
        """
        Executes the profile flow
        """
        self.state = "RUNNING"

        user = self.create_profile_users(1, self.USER_ROLES)[0]
        import_nodes = self.get_nodes_list_by_attribute(['node_id', 'subnetwork_id', 'subnetwork', 'mos'])
        self.CGI_VALUES = ["{0}-{1}".format(self.CGI_ROOT_VALUE, _) for _ in
                           xrange(self.MO_ATTRS.get("cgi"), len(import_nodes) * self.MOS_PER_NODE)]
        node_chunks = common_utils.chunks(import_nodes, self.NODES_PER_JOB)
        create_objects, delete_objects = [], []

        for nodes in node_chunks:
            operation = "create"
            timestamp = self.get_timestamp_str()
            parent_mos = self.get_parent_fdns(user, nodes)
            if not parent_mos:
                log.logger.debug("Failed to retrieve FDN information for {0}."
                                 .format(", ".join([node.node_id for node in nodes])))
                continue
            self.create_import_file(parent_mos, operation, timestamp)
            create_objects.append(self.create_import_object(user, nodes, operation, timestamp))
            operation = "delete"
            self.create_import_file(parent_mos, operation, timestamp)
            delete_objects.append(self.create_import_object(user, nodes, operation, timestamp))
            self.teardown_list.extend(
                [persistence.picklable_boundmethod(delete_object.restore_default_configuration_via_import) for
                 delete_object in delete_objects])

        import_objects = cycle([create_objects, delete_objects])

        while self.keep_running():
            if not create_objects or not delete_objects or (len(create_objects) != len(delete_objects)):
                log.logger.debug("Cannot continue, import objects did not create correctly, found {0} create objects "
                                 "and {1} delete objects.".format(len(create_objects), len(delete_objects)))
                break
            self.sleep_until_time()
            current_import_objects = import_objects.next()
            self.create_and_execute_threads(current_import_objects, len(current_import_objects), args=[self])
            log.logger.debug('Sleeping for 60s to ensure sufficient time has passed for '
                             'sleep_until_time() to sleep until next iteration.')
            time.sleep(60)

    def get_parent_fdns(self, user, nodes):
        """
        Query enm for the list of FDN strings for the supplied nodes

        :param user: User who will perform the query
        :type user: `enm_user_2.User`
        :param nodes: Nodes to retrieve the FDN
        :type nodes: `enm_node.Node`

        :return: List of FDN strings for the supplied nodes
        :rtype: list
        """
        cmd = "cmedit get {0} {1}".format(";".join(node.node_id for node in nodes), self.PARENT_MO)
        list_of_fdns = []
        log.logger.debug("Querying ENM for list of FDNS.")
        try:
            response = user.enm_execute(cmd)
            for line in response.get_output():
                if "FDN" in line:
                    list_of_fdns.append(line)
            log.logger.debug("Successfully queried ENM for list of FDNS.")
        except Exception as e:
            self.add_error_as_exception(e)
        return list_of_fdns

    def create_import_file(self, parent_fdns, operation, timestamp):
        """
        Create the basic file to used by the import object

        :param parent_fdns: List of parent FDNs, to act as the source for the operation
        :type parent_fdns: list
        :param operation: The type of import operation to perform, create/delete/set
        :type operation: str
        :param timestamp: Unique str timestamp to distinguish file paths
        :type timestamp: str
        """
        setattr(self, 'file_path', "{0}.txt".format(os.path.join(FILE_BASE_LOCATION, '{0}_{1}_{2}'.format(
            self.NAME.lower(), operation, timestamp))))
        log.logger.debug("Creating import file: {0}".format(self.file_path))
        with open(self.file_path, 'w+') as f:
            for parent_fdn in parent_fdns:
                for _ in xrange(self.MOS_PER_NODE):
                    mo_id = self.MO_ID_START_RANGE + _
                    f.write("{0}\n{1},{2}={3}\n".format(operation, parent_fdn, self.TARGET_MO, mo_id))
                    if operation != "delete":
                        self.write_attributes_file(f, mo_id)
        log.logger.debug("Import file: {0} created.".format(self.file_path))

    def write_attributes_file(self, file_obj, mo_id):
        """
        Write the profile attributes to the supplied file object

        :param file_obj: File object to write to
        :type file_obj: BinaryIO
        :param mo_id: Id to use if necessary
        :type mo_id: int
        """
        log.logger.debug("Writing attributes to file.")
        for key, value in self.MO_ATTRS.iteritems():
            if key in ["geranCellId", "cgi"]:
                value = self.CGI_VALUES.pop() if key == "cgi" else mo_id
                log.logger.debug("Attribute {1} found in list of generated MOs, updating value to {0}"
                                 .format(value, key))
            file_obj.write("{0} : {1}\n".format(
                key, value if isinstance(value, list) else '\"' + str(value) + '\"'))
        log.logger.debug("Successfully wrote attribute to import file.")

    def create_import_object(self, user, nodes, import_operation, timestamp):
        """
        Create import object to be used by the task set

        :param user: User who will perform the import
        :type user: `enm_user_2.User`
        :param nodes: Nodes to perform the import upon
        :type nodes: `enm_node.Node`
        :param import_operation: The type of import operation to perform, create/delete/set
        :type import_operation: str
        :param timestamp: Unique str timestamp to distinguish file paths
        :type timestamp: str

        :return: Instance of  CmImportLive
        :rtype: `CmImportLive`
        """
        name = self.NAME.lower()
        interface = self.INTERFACE if hasattr(self, 'INTERFACE') else None
        log.logger.debug('Creating cmimport objects for profile: {0}'.format(name))
        expected_number_mo_changes = len(nodes) * self.MOS_PER_NODE
        import_object = CmImportLive(
            name='{0}_{1}'.format(name, import_operation),
            user=user,
            nodes=nodes,
            template_name='{0}_{1}_{2}.txt'.format(name, import_operation, timestamp),
            flow=self.FLOW,
            file_type="dynamic",
            interface=interface,
            expected_num_mo_changes=expected_number_mo_changes,
            error_handling=self.ERROR_HANDLING if hasattr(self, "ERROR_HANDLING") and self.ERROR_HANDLING else None,
            timeout=self.TIMEOUT if hasattr(self, "TIMEOUT") else None)
        ts = get_human_readable_timestamp()
        update_cm_ddp_info_log_entry(self.NAME, "{0} {1} {2}\n".format(ts, self.NAME, expected_number_mo_changes))
        # Reduce the persisted size of the object(s)
        import_object.undo = None
        import_object.undo_over_nbi = None
        log.logger.debug('Created cmimport objects for profile: {0}, for operation {1}'.format(name, import_operation))
        return import_object

    @staticmethod
    def task_set(worker, profile):
        """
        Task set for use with thread queue

        :type worker: `cm_import.CmImportLive` instance
        :param worker: CmImportLive instance used to perform the import
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """
        try:
            worker.import_flow(history_check=True)
        except Exception as e:
            profile.add_error_as_exception(e)


class ReparentingCmImportFlow(GenericFlow):
    BASE_FILE_PATH = '/home/enmutils/cmimport/{0}'

    def execute_flow(self):
        """
        Executes the flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, getattr(self, 'USER_ROLES', ['ADMINISTRATOR']))[0]
        create_file = '{0}_create.txt'.format(self.NAME.lower())
        delete_file = '{0}_delete.txt'.format(self.NAME.lower())
        try:
            self.copy_files()
            self.get_required_bsc(user, getattr(self, 'BSC_ID', 'M47B94'))
        except Exception as e:
            self.add_error_as_exception(e)
            return
        import_files = cycle([self.BASE_FILE_PATH.format(create_file), self.BASE_FILE_PATH.format(delete_file)])
        self.teardown_list.append(persistence.picklable_boundmethod(
            self.create_import_object(
                user, 'delete', self.BASE_FILE_PATH.format(delete_file)).restore_default_configuration_via_import))
        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            try:
                file_path = import_files.next()
                import_obj = self.create_import_object(user, file_path.split('_')[-1].split('.')[0], file_path)
                import_obj.import_flow(history_check=True, file_path=file_path)
            except Exception as e:
                self.add_error_as_exception(e)

    @staticmethod
    def get_required_bsc(user, bsc_id):
        """
        Function to set the BSC child creation value

        :param user: User who execute the ENM command
        :type user: `enm_user_2.User`
        :param bsc_id: Id of the BSC node to verify exists in ENM
        :type bsc_id: str

        :raises EnvironWarning: raised if the required node is not available.
        """
        log.logger.debug("Querying ENM for node:: {0}.".format(bsc_id))
        cmd = "cmedit get {0}".format(bsc_id)
        response = user.enm_execute(cmd)
        if (not response or not response.get_output() or
                any(re.search(r'(error|^[0]\sinstance)', line, re.I) for line in response.get_output())):
            raise EnvironWarning("Required BSC:: [{0}] not found.".format(bsc_id))
        log.logger.debug("Completed querying ENM for node:: {0}.".format(bsc_id))

    def copy_files(self):
        """
        Function to copy the pre-created import files to the common directory
        """
        data_path = unipath.Path(pkgutil.get_loader('enmutils_int').filename).child("etc").child("data")
        for file_path in ["{0}/{1}".format(data_path, '{0}_create.txt'.format(self.NAME.lower())),
                          "{0}/{1}".format(data_path, '{0}_delete.txt'.format(self.NAME.lower()))]:
            filesystem.copy(file_path, self.BASE_FILE_PATH.format(file_path.split('/')[-1]))

    def create_import_object(self, user, import_operation, template_name):
        """
        Create import object to be used by the task set

        :param user: User who will perform the import
        :type user: `enm_user_2.User`
        :param import_operation: The type of import operation to perform, create/delete/set
        :type import_operation: str
        :param template_name: Unique str to distinguish file paths
        :type template_name: str

        :return: Instance of  CmImportLive
        :rtype: `CmImportLive`
        """
        name = self.NAME.lower()
        interface = getattr(self, 'INTERFACE', 'NBIv2')
        log.logger.debug('Creating cmimport objects for profile: {0}.'.format(name))
        expected_number_mo_changes = getattr(
            self, 'EXPECTED_NUM_CHANGES', {'delete': 0, 'create': 0}).get(import_operation)
        import_object = CmImportLive(
            name='{0}_{1}'.format(name, import_operation),
            user=user,
            nodes={},
            template_name=template_name,
            flow=getattr(self, 'FLOW', 'live_config'),
            file_type="dynamic",
            interface=interface,
            expected_num_mo_changes=expected_number_mo_changes,
            error_handling=getattr(self, "ERROR_HANDLING", 'continue-on-error-node'),
            timeout=getattr(self, "TIMEOUT", None))
        # Reduce the persisted size of the object(s)
        import_object.undo = None
        import_object.undo_over_nbi = None
        log.logger.debug('Created cmimport objects for profile: {0}, for operation {1}.'.format(name, import_operation))
        return import_object


class CmImport23Flow(GenericFlow):
    BASE_FILE_PATH = '/home/enmutils/cmimport/{0}'

    def execute_flow(self):
        """
        Executes the flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, self.USER_ROLES)[0]
        nodes = self.get_nodes_list_by_attribute()
        create_path, delete_path = self.flow_setup(user, nodes)
        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            self.create_delete_obj(user, nodes, create_path, delete_path)

    def flow_setup(self, user, nodes):
        """
        Carry out the setup required to execute the flow of the CMIMPORT_23

        :param user: User who will perform the import
        :type user: 'enm_user_2.User`
        :param nodes: Nodes to perform the import upon
        :type nodes: list

        :return: Paths of create and delete files
        :rtype: `Str`
        """
        log.logger.debug("Setting up the setup required for files creation")
        create_file = '{0}_create.txt'.format(self.NAME.lower())
        delete_file = '{0}_delete.txt'.format(self.NAME.lower())
        create_path = self.BASE_FILE_PATH.format(create_file)
        delete_path = self.BASE_FILE_PATH.format(delete_file)
        create_cmd = "create\nFDN:SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimI,MeContext={0}," \
                     "ManagedElement={0},nacm=1,groups=1,group={1}_{2}\nname:{1}_{2}\n\n"
        delete_cmd = "delete\nFDN:SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimI,MeContext={0}," \
                     "ManagedElement={0},nacm=1,groups=1,group={1}_{2}\n\n\n"
        log.logger.debug("Setup completed")
        self.create_file(create_path, create_cmd, nodes)
        self.create_file(delete_path, delete_cmd, nodes)
        self.teardown_list.append(persistence.picklable_boundmethod(
            self.create_import_object(
                user, nodes, 'delete',
                self.BASE_FILE_PATH.format(delete_file)).restore_default_configuration_via_import))

        return create_path, delete_path

    def create_file(self, file_path, cmd, nodes):
        """
        Generate files with create and delete commands

        :param file_path: file path
        :type file_path: `str`
        :param cmd: command to be executed in import job
        :type cmd:  'str'
        :param nodes: Nodes to perform the import upon
        :type nodes: list
        """
        try:
            log.logger.debug("Creating import file: {0}".format(file_path))
            with open(file_path, 'w+') as f:
                for node in nodes:
                    for mo_count in range(1, self.MOS_PER_NODE + 1):
                        f.write(cmd.format(node.node_id, self.NAME.lower(), mo_count))
            log.logger.debug("Import file: {0} created.".format(file_path))
        except Exception as e:
            log.logger.debug("Exception in creating a file: {0}".format(str(e)))

    def create_delete_obj(self, user, nodes, create_path, delete_path):
        """
        Create import object to be used by the task set

        :param user: User who will perform the import
        :type user: 'enm_user_2.User`
        :param nodes: Nodes to perform the import upon
        :type nodes: list
        :param create_path: path of create file
        :type create_path: `str`
        :param delete_path: path of delete file
        :type delete_path: `str`
        """
        try:
            name = self.NAME.lower()
            log.logger.debug('Creating cmimport objects for profile: {0}.'.format(name))
            create_import_obj = self.create_import_object(user, nodes, 'create', create_path)
            create_import_obj.import_flow(history_check=True, file_path=create_path)
            log.logger.debug('Sleeping for 5s before delete')
            time.sleep(5)
            delete_import_obj = self.create_import_object(user, nodes, 'delete', delete_path)
            delete_import_obj.import_flow(history_check=True, file_path=delete_path)
        except Exception as e:
            self.add_error_as_exception(e)

    def create_import_object(self, user, nodes, import_operation, template_name):
        """
        Create import object to be used by the task set

        :param user: User who will perform the import
        :type user: `enm_user_2.User`
        :param nodes: Nodes to perform the import upon
        :type nodes: list
        :param import_operation: The type of import operation to perform, create/delete/set
        :type import_operation: str
        :param template_name: Unique str to distinguish file paths
        :type template_name: str

        :return: Instance of  CmImportLive
        :rtype: `CmImportLive`
        """
        name = self.NAME.lower()
        interface = self.INTERFACE if hasattr(self, 'INTERFACE') else None
        log.logger.debug('Creating cmimport object for profile: {0}, for operation {1}.'.format(name, import_operation))
        expected_number_mo_changes = len(nodes) * self.MOS_PER_NODE
        import_object = CmImportLive(
            name='{0}_{1}'.format(name, import_operation),
            user=user,
            nodes=nodes,
            template_name=template_name,
            flow=self.FLOW,
            file_type=self.FILETYPE,
            interface=interface,
            expected_num_mo_changes=expected_number_mo_changes,
            error_handling=getattr(self, "ERROR_HANDLING", 'continue-on-error-node'),
            timeout=getattr(self, "TIMEOUT", None))
        # Reduce the persisted size of the object(s)
        import_object.undo = None
        import_object.undo_over_nbi = None
        log.logger.debug('Created cmimport object for profile: {0}, for operation {1}.'.format(name, import_operation))
        return import_object


class CmImportSetupObject(object):
    def __init__(self, nodes, user, expected_num_mo_changes):
        self.nodes = nodes
        self.user = user
        self.expected_num_mo_changes = expected_num_mo_changes
