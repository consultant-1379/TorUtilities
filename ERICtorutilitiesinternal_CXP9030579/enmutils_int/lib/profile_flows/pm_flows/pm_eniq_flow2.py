import re
from collections import deque
from datetime import date, datetime
from functools import partial
from time import sleep

import pexpect

from enmutils.lib import shell, log, filesystem
from enmutils.lib.cache import get_ms_host, get_workload_vm_credentials
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.filesystem import does_dir_exist, create_dir
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import pm_nbi
from enmutils_int.lib.common_utils import check_for_active_litp_plan
from enmutils_int.lib.helper_methods import get_local_ip_and_hostname
from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_common_utils import confirm_eniq_topology_export_enabled
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm, update_pib_parameter_on_enm

SHOW_EXPORT_TIMES = '{integration_script} showExportTimes'
ENIQ_INT_SCRIPT = '/usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_enm_integration.py'


def toggle_pib_inventory_export():
    """
    Function to set the inventory export to enabled.
    """
    log.logger.debug("Setting ENIQ export inventory pib values.")
    toggle_pib_inventorymoexport('true')
    log.logger.debug("ENIQ export values set.")


def set_pib_parameters_topology_export(value):
    """
    Set pib parameter values for ENIQ Stats Export
    :param value: Value to use when setting the PIB paramater value
    :type value: str
    """
    log.logger.debug("Setting PIB parameters for Topology Export")
    cmexport_type = ["topologyExportCreationEnabledStats", "topologyExportCreationEnabled"]
    for pib_parameter in cmexport_type:
        update_pib_parameter_on_enm(enm_service_name='impexpserv',
                                    pib_parameter_name=pib_parameter,
                                    pib_parameter_value=value,
                                    service_identifier="eniq-topology-service-impl")

    log.logger.debug("Setting PIB parameters complete")


def set_pib_parameters(value):
    """
    Set PIB parameters
    :param value: Value to set PIB parameters to
    :type value: str
    """

    set_pib_parameters_topology_export(value)
    toggle_pib_inventorymoexport(value)

    update_pib_parameter_on_enm("pmserv", "useStatsSymlinks", value)
    update_pib_parameter_on_enm("pmserv", "pmicSymbolicLinkCreationEnabled", value)


def toggle_pib_inventorymoexport(state):
    """
    Toggle turning on/off pib parameter for Inventory MO Export in PM_44 profile
    """

    update_pib_parameter_on_enm(enm_service_name='impexpserv',
                                pib_parameter_name='ETS_InventoryMoExportEnabled',
                                pib_parameter_value=state)
    state = "disabled" if state != "true" else "enabled"
    log.logger.debug("Inventory MO Export is {0}. ".format(state))


class PmEniqFlow(GenericFlow):
    COMMON_MOUNTPOINT = "/eniq/data/importdata"
    PMIC1_STATS_MOUNTPOINT = COMMON_MOUNTPOINT + "/eniq_oss_1/pmic1"
    PMIC2_STATS_MOUNTPOINT = COMMON_MOUNTPOINT + "/eniq_oss_1/pmic2"
    ES_MOUNT_POINT_LIST = [PMIC1_STATS_MOUNTPOINT, PMIC2_STATS_MOUNTPOINT]

    NFS_SHARES = ["nfsm-pm1", "nfsm-pm2"]
    LITP_PATH_TO_SHARES = ("/deployments/enm/clusters/svc_cluster/services/pmserv/applications/vm-service_pmserv/"
                           "vm_nfs_mounts/{nfs_share}")
    LITP = "/usr/bin/litp"
    ENIQ_STATS_SETUP_CMD = '{integration_script} eniq_oss_1 {workload_ip}\n'
    ENIQ_INT_SCRIPT = '/usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_enm_integration.py'
    ENIQ_INT_SCRIPT_FOR_CLOUD = 'sudo /usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_venm_integration.py'
    ENIQ_ACTIVATION_TIMEOUT = 1800

    def __init__(self):
        self.file_system_list = []
        self.fs_mounts = []
        self.mount_point_list = []
        self.check_time_file_interval = 100
        self.subdir_collection = deque()
        self.node_data_type_file_id_dict = None
        super(PmEniqFlow, self).__init__()

    def set_teardown_objects(self):
        """
        Add callable objects to the teardown list

        """
        self.teardown_list.append(partial(set_pib_parameters, "false"))
        self.teardown_list.append(picklable_boundmethod(self.umount_shared_file_system))

    def create_mount_points(self):
        """
        Creates directories present in self.mount_point_list

        :raises EnvironError: If creation of any directory fails

        """
        log.logger.debug("Creating Mount points on Workload VM")
        self.mount_point_list = self.ES_MOUNT_POINT_LIST
        for directory in self.mount_point_list:
            if not does_dir_exist(directory):
                create_dir(directory)

        log.logger.debug("Mount points created")

    def set_file_system_paths(self):
        """
        Sets PM file system paths obtained from litp commands

        :raises EnvironError: if failed to execute litp command

        """

        log.logger.debug("Fetching PM file system path information from LITP")

        litp_command = "{litp} show -p {path} -o device_path".format(litp=self.LITP, path=self.LITP_PATH_TO_SHARES)

        for nfs_share in self.NFS_SHARES:
            command = litp_command.format(nfs_share=nfs_share)
            output = self.run_litp_command(command)

            if output:
                log.logger.debug("NFS Share information for '{0}': {1}".format(nfs_share, output))
                self.file_system_list.append(output)
            else:
                raise EnvironError("Information not set in LITP for share: {0}".format(nfs_share))
            self.fs_mounts = dict(zip(self.mount_point_list, self.file_system_list))

        log.logger.debug("PM file system path information successfuly fetched from LITP")

    @staticmethod
    def run_litp_command(command):
        """
        Run LITP command and keep retrying command every 5 min in the event that LITP is unavailable,
        e.g. in the case of ENM upgrade

        :param command: LITP command to be run
        :type command:
        :return: Output from LITP command
        :rtype: str
        """

        log.logger.debug("Running LITP command: {0}".format(command))
        output = ""

        completed = False
        failure_count = 0
        while not completed:
            output = shell.run_cmd_on_ms(shell.Command(command, timeout=60)).stdout.split("\n")[0]

            if "ServerUnavailableError" in output:
                if failure_count == 12:  # log extra entry every time the function has been waiting for 1 hour
                    log.logger.debug("Unavailable to successfully query LITP for past hour as ServerUnavailableError "
                                     "is being returned from LITP command: {0}".format(command))
                    failure_count = 0

                log.logger.debug("LITP command not executed successfully - retrying in 5 min: {0}".format(output))
                failure_count += 1
                sleep(60 * 5)
                continue

            completed = True

        log.logger.debug("Output from LITP command: {0}".format(output))
        return output

    def umount_shared_file_system(self):
        """
        Unmounts ENIQ filesystems in Workload VM

        """
        log.logger.debug("Unmounting shared filesystems")

        for mount_point in self.mount_point_list:
            try:
                shell.run_local_cmd(
                    shell.Command('mount | grep {mount_point} && umount {mount_point}'.format(mount_point=mount_point)))
            except RuntimeError:
                log.logger.debug('Unable to unmount {mount_point}'.format(mount_point=mount_point))

        log.logger.debug("Share filesystems unmounted")

    def mount_file_systems(self):
        """
        Mounts PM filesystems in WLVM if does not exists
        """

        log.logger.debug("Mount File systems")

        for mount_point in self.mount_point_list:
            response = shell.run_local_cmd(shell.Command('mount | grep {mount_point}'.format(mount_point=mount_point)))
            if response.rc != 0:
                log.logger.debug(
                    "Mount point: {mount_point} does not exist, trying to mount".format(mount_point=mount_point))
                try:
                    shell.run_local_cmd(
                        shell.Command("mount -o nolock {0} {1}".format(self.fs_mounts[mount_point], mount_point),
                                      timeout=60, check_pass=True))
                except RuntimeError:
                    raise EnvironError(
                        'Unable to mount filesystem {0} to mount point {1}'.format(self.fs_mounts[mount_point],
                                                                                   mount_point))
        log.logger.debug("Mount File systems complete")

    def check_and_enable_pmic_symbolic_link_creation(self):
        """
        Deprecated in 20.16 and will be deleted in 21.11 RTD-14986
        """

    def check_and_toggle_pmic_symbolic_link_creation(self, action):
        """
        check and enable/disable the pmic symbolic link creation in ENIQ server
        """
        try:
            pib_value = get_pib_value_on_enm("pmserv", "pmicSymbolicLinkCreationEnabled")
            pmic_symbolic_link_creation_status = bool(pib_value == "true")
            action_state = bool(action == "enable")
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            try:
                if pmic_symbolic_link_creation_status == action_state:
                    log.logger.debug("PMIC symbolic link creation is currently {0}d".format(action))
                else:
                    update_pib_parameter_on_enm("pmserv", "pmicSymbolicLinkCreationEnabled",
                                                ("true" if action_state else "false"))
                    log.logger.debug("PMIC symbolic link creation is {0}d successfully".format(action))
            except Exception as e:
                self.add_error_as_exception(e)

    def check_eniq_exports_enabled(self):
        """
        Checks that ENIQ export is configured, once per day based on scheduled time
        """
        today = date.today()
        schedule_time = self.CHECK_EXPORT_TIME.split(':')
        time_to_check_export_enabled = self.start_time.replace(year=today.year,
                                                               month=today.month,
                                                               day=today.day,
                                                               hour=int(schedule_time[0]),
                                                               minute=int(schedule_time[1]),
                                                               second=int(schedule_time[2]))

        if 0 < (time_to_check_export_enabled - datetime.now()).total_seconds() < self.SCHEDULE_SLEEP:
            self.confirm_export_configured()

    def execute_flow(self):
        """
        Executes Profile Flow

        """
        file_id = 0
        filecreationtime = None
        pm_nbi_user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES, retry=True)[0]
        self.node_data_type_file_id_dict = {node_type: {data_type: [file_id, filecreationtime] for data_type in self.DATA_TYPES} for node_type in self.NODE_TYPES}
        # node_data_type_file_id_dict example : {'RadioNode': {'PM_STATISTICAL': 0, 'PM_STATISTICAL_1MIN': 0},
        #                                        'SGSN-MME': {'PM_STATISTICAL': 0, 'PM_STATISTICAL_1MIN': 0}}

        fls = pm_nbi.Fls(pm_nbi_user)

        self.perform_prechecks_and_execute_tasks()
        self.set_teardown_objects()

        self.state = 'RUNNING'
        while self.keep_running():
            self.sleep_until_time()
            self.periodic_fls_pm_query(fls)

    def perform_prechecks_and_execute_tasks(self):
        """
        Performs ENIQ integration checks and executes CMEXPORT_19 and PM_44 tasks
        """
        try:
            log.logger.debug("Performing ENIQ integration check and executing profile tasks")
            self.integrate_eniq()
            self.perform_cmexport19_tasks()
            self.perform_pm44_tasks()
        except Exception as e:
            self.add_error_as_exception(e)

    def perform_cmexport19_tasks(self):
        """
        Confirms if ENIQ export configured and checks & enables eniq exports
        """
        try:
            log.logger.debug("Performing CMEXPORT_19 tasks")
            self.confirm_export_configured()
            log.logger.debug("Checking if ENIQ exports is enabled")
            self.check_eniq_exports_enabled()
        except Exception as e:
            self.add_error_as_exception(e)

    def perform_pm44_tasks(self):
        """
        Performs PM_44 tasks such as updating useStatsSymlinks PIB parameter, creating mount points, setting PM file
        system paths and mounting file systems
        """
        try:
            log.logger.debug("Performing PM_44 profile prechecks and excuting tasks")
            update_pib_parameter_on_enm("pmserv", "useStatsSymlinks", "false")
            self.create_mount_points()
            self.set_file_system_paths()
            log.logger.debug("Performing tasks to mount file systems and disable symbolic link creation")
            self.check_and_toggle_pmic_symbolic_link_creation("disable")
            self.mount_file_systems()
        except Exception as e:
            self.add_error_as_exception(e)

    def sleep_for_wait_time(self, time, ref_time):
        """
        Sleep for a particular period of time until next iteration
        :param time: time interval of iteration
        :type time: int
        :param ref_time: current time to determine wait_time
        :type ref_time: int
        """
        old_state = self.state
        self.state = "SLEEPING"
        wait_time = (time - ref_time % time) * 60 - int(datetime.now().strftime("%S"))
        log.logger.debug("Sleeping for {0} second(s)".format(wait_time))
        sleep(wait_time)
        self.state = old_state

    def integrate_eniq(self):
        """
        Integrate ENIQ if not already integrated
        """
        if not self.check_if_eniq_integrated():
            self.wait_for_litp_plan_to_complete()
            self.execute_setup_commands()
            if not self.check_if_eniq_integrated():
                raise EnvironError("Unable to verify that ENIQ was integrated to ENM - cannot proceed")

    @staticmethod
    def create_status_file():
        """
        Create the  ENIQ status file to allow the integration script to run on a workloadVM
        """
        log.logger.debug("Creating status file.")
        eniq_dir = "/eniq/admin/version/"
        eniq_status_file = "{0}eniq_status".format(eniq_dir)
        filesystem.create_dir(eniq_dir)
        filesystem.touch_file(eniq_status_file)
        log.logger.debug("Status file created successfully")

    @staticmethod
    def manage_password_prompt(child, user, password):
        """
        Handle scenario where ENIQ script prompts for credentials

        :param child: Child of the spawned pexpect object
        :type child: `pty_spawn.spawn`
        :param user: Username to use when connecting to the dummy ENIQ server
        :type user: str
        :param password: Password to use when connecting to the dummy ENIQ server
        :type password: str

        :return: Child of the spawned pexpect object
        :rtype: `pty_spawn.spawn`
        """
        child.expect_exact("Please enter ENIQ server username:")
        child.send("{0}\r\n".format(user))
        log.logger.debug("\nENIQ server username sent.")
        password_prompt = child.expect_exact(["password :", pexpect.TIMEOUT, pexpect.EOF], timeout=30)
        if not password_prompt:
            child.send("{0}\r\n".format(password))
            log.logger.debug("\nENIQ server password sent.")
        return child

    def check_if_eniq_integrated(self):
        """
        Check if ENIQ has been integrated already
        :return: Boolean to indicate if ENIQ has been integrated or not
        :rtype: bool
        :raises EnvironError: if other Ips are found other than wlvm IP
        """
        log.logger.debug("Checking if ENIQ (i.e. Workload VM acts as ENIQ here) has already been integrated to ENM")
        cmd = "{0} list_eniqs".format(self.ENIQ_INT_SCRIPT)
        ip, _ = get_local_ip_and_hostname()
        log.logger.debug("IP Address of ENIQ: {0}".format(ip))
        remote_shell_options = {"get_pty": True}
        response = shell.run_cmd_on_ms(shell.Command(cmd, timeout=300), **remote_shell_options)
        if response.rc == 0 and response.stdout:
            output = response.stdout.split("\n")
            ips = len(output[2].split(','))
            for line in output:
                match = re.search(r"ENM has been integrated to eniq.*'{0}'.*".format(ip), line)
                if match and ips == 1:
                    return True
                if match and ips >= 2:
                    raise EnvironError(("Multiple IPs found:{0}\n"
                                        "Only wlvm IP is required to integrate ENIQ".format(output[2])))
            log.logger.debug("Unable to determine if ENIQ IP was integrated to ENM")
        else:
            raise EnvironError("Error occured while running command '{0}':".format(cmd))

    def execute_setup_commands(self):
        """
        Executes the setup commands for both ENIQ stats and events

        """
        log.logger.debug("Executing setup commands.")
        self.create_status_file()
        user, password = get_workload_vm_credentials()
        physical_ssh_cmd = 'ssh root@{0}'.format(get_ms_host())
        ip, _ = get_local_ip_and_hostname()
        cmd = self.ENIQ_STATS_SETUP_CMD.format(integration_script=self.ENIQ_INT_SCRIPT, workload_ip=ip)
        log.logger.debug("\n\nExecuting ENIQ configuration script command: {0}\n\n".format(cmd))
        with pexpect.spawn(physical_ssh_cmd, timeout=120) as child:
            initial_expect = "root@"
            child.expect([initial_expect, pexpect.EOF])
            child.send(cmd)
            child.expect_exact("Checking pmserv and impexpserv are available.")
            prompt = child.expect("Checking Provided IP address is ENIQ server or not .....")
            if not prompt:
                child = self.manage_password_prompt(child, user, password)
            result = child.expect(["ENIQ successfully activated!", "To view currently integrated ENIQ, use : "
                                                                   "/opt/ericsson/ENM_ENIQ_Integration/eniq_enm_"
                                                                   "integration.py list_eniqs", pexpect.EOF,
                                   pexpect.TIMEOUT], timeout=self.ENIQ_ACTIVATION_TIMEOUT)
            if result not in [0, 1]:
                log.logger.debug("\nBefore: {0}.".format(child.before))
                log.logger.debug("\nAfter: {0}.".format(child.after))
                self.add_error_as_exception(EnvironError("ENIQ configuration script has failed to correctly complete,"
                                                         " and may require manual intervention."))
            else:
                log.logger.debug("Script Output: {0}.".format(child.before))

        log.logger.debug("Setup commands completed.")

    def confirm_export_configured(self):
        """
        Confirm the ENIQ export has been configured
        """
        log.logger.debug("Confirming that ENIQ Topology exports are configured")
        try:
            if not confirm_eniq_topology_export_enabled():
                set_pib_parameters_topology_export("true")
            toggle_pib_inventory_export()
            log.logger.debug("ENIQ Topology exports configured & enabled")
        except Exception as e:
            self.add_error_as_exception(EnvironError("Failed to set ENIQ export parameters - {0}".format(e)))

    def wait_for_litp_plan_to_complete(self):
        """
        Waits for any active litp to complete
        """
        base_sleep_time = 1200
        while True:
            if not check_for_active_litp_plan():
                break
            log.logger.debug("Unable to run ENIQ integration script as active LITP plan exists. "
                             "Profile will sleep for {0} second(s) and check again for active LITP "
                             "plan.".format(base_sleep_time))
            sleep(base_sleep_time)

    def periodic_fls_pm_query(self, fls):
        """
        Performs periodic FLS query and reads files collected from each query

        :param fls: FLS object
        :type fls: FLS object
        """
        pm_files = []
        self.check_profile_memory_usage()
        log.logger.debug("Attempting to perform FLS query and read files")

        for node_type in self.node_data_type_file_id_dict.keys():
            for data_type, id_time_list in self.node_data_type_file_id_dict[node_type].iteritems():
                try:
                    file_locations, last_file_id, last_file_creation_time = fls.get_pmic_rop_files_location(
                        self.NAME, data_type, node_type=node_type, file_id=id_time_list[0],
                        file_creation_time=id_time_list[1])
                    pm_files.extend(file_locations)
                    self.node_data_type_file_id_dict[node_type][data_type][0] = last_file_id if last_file_id else id_time_list[0]
                    self.node_data_type_file_id_dict[node_type][data_type][1] = last_file_creation_time if last_file_creation_time else id_time_list[1]
                except Exception as e:
                    self.add_error_as_exception(e)

        log.logger.debug("node and data type file id dict : {}".format(self.node_data_type_file_id_dict))

        total_files = len(pm_files)
        log.logger.debug("Executed query, retrieved total: {0} files \n".format(total_files))

        latest_pm_files = pm_files if total_files < 10000 else pm_files[-10000:]
        self.read_files(latest_pm_files)
        self.check_profile_memory_usage()

    def read_files(self, files):
        """
        Read each file from list of files

        :param files: PM files
        :type files: list
        """

        common_dir_path = "/eniq/data/importdata/eniq_oss_1"
        running_totals = {"read_success": 0, "read_failure": 0}
        log.logger.debug("Reading files started")
        for line in files:
            file_path = line.replace("/ericsson", common_dir_path)
            try:
                with open(file_path, 'rb') as f:
                    f.read()
                    running_totals["read_success"] += 1
            except Exception:
                running_totals["read_failure"] += 1
        log.logger.debug("Total files read summary:{0}".format(running_totals))
