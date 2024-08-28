# ********************************************************************
# Name    : FMX Manager
# Summary : Primary module used by FM Extreme. Allows the user to
#           interact and manage all aspects of FMX modules.
# ********************************************************************

from datetime import datetime
import re
import time
from packaging.version import Version
from paramiko import SSHException
import pexpect
from retrying import retry
from requests.exceptions import HTTPError
from enmutils.lib import log, shell
from enmutils.lib.exceptions import (ShellCommandReturnedNonZero, ValidationError, FileNotUpdatedError, EnvironError)
from enmutils.lib.cache import (get_ms_host, get_emp, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP,
                                CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, is_enm_on_cloud_native,
                                is_emp, is_host_physical_deployment, get_enm_cloud_native_namespace)
from enmutils_int.lib import enm_deployment
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.services import nodemanager_adaptor

ACTIVE_SIMULATION_STATE = ['NotEnabled']
SIMULATION = '/fmxadminws/v1/module/setSimulation?simulationEnabled={0}'
SIMULATION_MODULE = 'CN_Signalling_Disturbances'


class FmxMgr(object):
    """
    Class for managing FMX functionality.
    For example, you can import, load, activate FMX modules.
    It can also set nodes into 'maintenance' for a specified period of time
    with the following attributes: MARK, NMS, NMSandOSS

    Additional alarm attributes generated, when processing nodes tagged as in maintenance (appended to an alarm: 'additionalInformation' field)
            FMX_Additional
            Maintenance

    Example of command to see alarm attributes
    fmedit get * OpenAlarm.(objectOfReference==*"LTE03ERBS00003"*,fdn=="NetworkElement="*) OpenAlarm.(fdn,processingType,fmxGenerated,additionalInformation,specificProblem)


    Possible fmx maintenance mode states of an alarms, displayed on a alarm in 'additionalInformation' field:
          ---Maintenance mode---    |            ---FMX additional attributes---            | ---Maintenance additional attributes---
    MARK 	                        | In maintenance mode. 	                                | MARK
    NMS 	                        | In maintenance mode. Blocked to NMS                   | NMS
    NMSandOSS 	                    | In maintenance mode. Hidden in OSS and blocked to NMS.| NMSandOSS
    After Maintenance window expired| Back after maintenance mode. 	                        | FALSE
    After module deactivation 	    | Shown due to module deactivation. 	                | FALSE
    """
    USER = 'cloud-user'
    child = None

    def __init__(self, user, all_modules=None, vm_addresses=None):
        """
        FmxMgr constructor

        :type all_modules: list
        :param all_modules: list of modules
        :type user: enm_user_2.User
        :param user: User executes UI commands
        :type vm_addresses: list
        :param vm_addresses: list of vm ips or hostnames

        :raises RuntimeError:
        """
        all_modules = all_modules or []
        self.user = user
        self.fmx_kvm_name = 'fmx'
        self.all_modules = all_modules
        self.fmxcli_path = '/opt/ericsson/fmx/cli/bin/fmxcli'
        self.execute_on_transport = self.CLOUD = False
        self.PHYSICAL = self.CLOUD = self.CLOUD_NATIVE = False
        self.check_deployment_type()
        self.index = 0

        # these, are used when setting nodes in different maintenance modes
        self.maintenance = False
        self.maintenance_script_path = '/ericsson/tor/data/fmx/etc/modules/nsx/ManageNodesInMaintenance.pl'
        self.remove_node_from_maintenance_cmd = 'sudo {0} -delete -node '.format(self.maintenance_script_path)
        self.clean_all_expired_maintenance_windows_cmd = 'sudo {0} -clean'.format(self.maintenance_script_path)
        self.list_nodes_in_maintenance = 'sudo {0} -list'.format(self.maintenance_script_path)

        # headers
        self.headers_application_json = {'Content-Type': 'application/json'}
        self.headers_application_url_encoded_utf8 = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        # fmx_01 file updates
        self.nsx_directory_path = '/var/opt/ericsson/fmx/etc/modules/nsx/'
        self.cnx_directory_path = '/var/opt/ericsson/fmx/etc/modules/cnx/'
        self.externalfilter_path = '{0}external_alarms_short_filter.txt'.format(self.cnx_directory_path)
        self.hardfilter_path = '{0}HardFilter.txt'.format(self.nsx_directory_path)
        self.node_type_for_hardfilter = ['Router6672', 'Router6675']
        self.update_eaf = ('if (grep -w "EXTERNAL ALARM" {0} | grep -v "#") && '
                           '(grep -w "CCITT7 SIGNALLING LINK FAILURE" {0}); then echo ""; '
                           'else echo -e "EXTERNAL ALARM\nCCITT7 SIGNALLING LINK FAILURE" >>{0}; fi'
                           .format(self.externalfilter_path))

        self.update_hf = [("grep -qw '{0};Nss Synchronization System Clock Status Change' {1} || printf "
                           "'%b\\n{0};Nss Synchronization System Clock Status Change'"
                           " >>{1}".format(node_type, self.hardfilter_path)) for node_type in self.node_type_for_hardfilter]

        self.update_hf_cn = [('grep -qw "{0};Nss Synchronization System Clock Status Change" {1} || printf \
                              "%b\\n{0};Nss Synchronization System Clock Status Change" \
                              >>{1}'.format(node_type, self.hardfilter_path)) for node_type in self.node_type_for_hardfilter]

        self.vm_addresses = vm_addresses

        if vm_addresses is None:
            try:
                if is_enm_on_cloud_native():
                    self.vm_addresses = enm_deployment.get_pod_hostnames_in_cloud_native('fmx-engine')
                else:
                    self.vm_addresses = enm_deployment.get_values_from_global_properties('fmx=')
            except Exception as e:
                log.logger.error("Failed to retrieve service host. Error: {response_out}".format(response_out=e))

    def get_export_dir_modules(self):
        """
        Get content of export directory, that holds all modules

        :rtype: Instance of Response class
        :returns: Response with all modules available in export directory

        :raises HTTPError:
        """
        url = '/fmxadminws/v1/exportmodules'
        response = self.user.get(url, headers=self.headers_application_json)
        if not response.ok:
            raise HTTPError('Cannot list modules in export dir at url: "{0}"'.format(str(url)), response=response)

        return response

    def _get_module_from_export_dir(self, module):
        """
        Get all versions available in the export dir of a particular module.

        :type module: str
        :param module: Name of a module

        :returns: List of all versions of a module found in the export dir
        :rtype: list
        """
        export_dir_modules_info = self.get_export_dir_modules().json()['localFiles']
        all_modules = [item['name'] for item in export_dir_modules_info]
        searched_module = [m for m in all_modules if m.startswith(module)]

        return searched_module

    def check_deployment_type(self):
        """
        Checks for the deployment type and modifies the class variables as required
        """
        if is_host_physical_deployment():
            self.PHYSICAL = True
        elif is_emp():
            self.CLOUD = True
        else:
            self.CLOUD_NATIVE = True

    def import_module(self, module):
        """
        Import all versions of fmx module into an archive from Export directory.

        :type module: str
        :param module: Name of a module

        :raises HTTPError:
        :raises ValidationError:
        """
        export_dir_modules = self._get_module_from_export_dir(module)
        if export_dir_modules:
            # import all available versions of a module
            log.logger.debug("IMPORTING FMX MODULE: {0}".format(export_dir_modules))

            for module in export_dir_modules:
                # url example:
                # https://enmapache.athtem.eei.ericsson.se/fmxadminws/v1/exportmodules?filename=baseblocks-module-15.74.fmx
                url = '/fmxadminws/v1/exportmodules?filename={0}'.format(module)

                response = self.user.put(url, headers=self.headers_application_json)
                if not response.ok:
                    if 'userMessage' in response.json() and "already been created" in response.json()['userMessage']:
                        continue
                    raise HTTPError('Cannot import module {0}'.format(module), response=response)
        else:
            log.logger.debug('Could not find module {0} in the export dir'.format(module))
            raise ValidationError('Could not find module {0} in the export dir'.format(module))

    def load_module(self, module, version):
        """
        Load fmx module from an archive

        :type module: str
        :param module: Name of a module
        :type version: str
        :param version: Version of a module

        :raises HTTPError:
        """

        log.logger.debug("LOADING FMX MODULE: {0}, version: {1}".format(module, version))

        #  load command seems to be idempotent. Can be executed over & over - with same result
        #  so we don't need any checks in stdout ... at least for now
        #  NOTE: every time 'load <module>' cmd is executed on FMX vm - <module> is deactivated in ENM.
        #  Reactivation of a <module>  this will have impact on ENM FM and FMX

        url = '/fmxadminws/v1/module/load'
        response = self.user.post(url, data='module={0}&version={1}'.format(module, version), headers=self.headers_application_url_encoded_utf8)

        if not response.ok:
            raise HTTPError('Cannot load module {0}'.format(module), response=response)

    def _unload_module(self, module):
        """
        Unload a module

        :type module: str
        :param module: Name of a module to be unloaded

        :rtype: Instance of Response class
        :returns: enm_user_2.requests.Response object
        """
        log.logger.debug('UNLOADING FMX MODULE: {0}'.format(module))

        url = '/fmxadminws/v1/module/unload'
        response = self.user.post(url, data='module={0}'.format(module), headers=self.headers_application_url_encoded_utf8)

        if not response.ok:
            log.logger.debug('Cannot unload module {0}. Response was: {1}'.format(module, response.json()))
        return response.ok

    def _activate_module(self, module):
        """
        Activate fmx module
        :type module: str
        :param module: Name of a module
        :raises HTTPError:  if response status is not ok
        """
        log.logger.debug('ACTIVATING FMX MODULE: {0}'.format(module))
        url = '/fmxadminws/v1/module/activate?module={0}'.format(module)
        response = self.user.get(url)
        if not response.ok:
            if 'userMessage' in response.json() and "already active" in response.json()['userMessage']:
                return
            raise HTTPError('Cannot activate module {0}'.format(module), response=response)

    def enable_simulation_module(self, module):
        """
        Enable simulation for fmx module
        :type module: str
        :param module: Name of a module
        :raises HTTPError:  if response status is not ok
        """
        log.logger.debug('Enable simulation for FMX MODULE: {0}'.format(module))
        url = SIMULATION.format('true')
        response = self.user.post(url, data='module={0}'.format(SIMULATION_MODULE),
                                  headers=self.headers_application_url_encoded_utf8)

        if not response.ok:
            raise HTTPError('Cannot enable simulation on module {0}'.format(module), response=response)

    def _disable_simulation_module(self, module):
        """
        Disable simulation for  a module
        :type module: str
        :param module: Name of a module
        :rtype: Instance of Response class
        :returns: Response with all modules available in export directory
        """
        log.logger.debug('Disabling simulation for FMX MODULE: {0}'.format(module))
        url = SIMULATION.format('false')
        response = self.user.post(url, data='module={0}'.format(SIMULATION_MODULE),
                                  headers=self.headers_application_url_encoded_utf8)

        if not response.ok:
            log.logger.debug('Cannot disable simulation on module {0}. Response was: {1}'
                             .format(module, response.json()))
        return response.ok

    def _deactivate_module(self, module):
        """
        Deactivate a module

        :type module: str
        :param module: Name of a module

        :rtype: Instance of Response class
        :returns: Response with all modules available in export directory
        """
        log.logger.debug('DEACTIVATING FMX MODULE: {0}'.format(module))
        url = '/fmxadminws/v1/module/deactivate?module={0}'.format(module)
        response = self.user.get(url)

        if not response.ok:
            log.logger.debug('Cannot deactivate module {0}. Response was: {1}'.format(module, response.json()))
        return response.ok

    def _get_archive_modules(self):
        """
        Get all modules (both utility & rule modules) imported into an archive

        :rtype: Response object
        :returns: All modules in the archive with all available versions
        :raises HTTPError:
        """
        url = '/fmxadminws/v1/module/listArchive'
        response = self.user.get(url)
        if not response.ok:
            raise HTTPError('Cannot get list of imported modules at url: {0}'.format(str(url)), response=response)
        return response

    def get_highest_version_for_modules_in_archive(self):
        """
        Get highest version of each module in the archive will be returned

        :type: Response object
        :param: All modules in the archive

        :rtype:  list
        :returns: A list of imported modules
        """

        archive_modules_response = self._get_archive_modules()
        imported_modules = {}
        for item in archive_modules_response.json()['modules']:
            module = item['moduleName']
            module_version = item['version']['version']
            if module not in imported_modules:
                imported_modules[module] = []
            imported_modules[module].append(Version(module_version))

        # there may be a case when more versions of the same modules are imported into archive
        # if so - get only highest one
        modules_highest_version = {}

        for module in imported_modules:
            max_ver = max(imported_modules[module])
            modules_highest_version[module] = [max_ver]

        # Ex: Modules in the archive:
        # {u'NSX_Shortlived_and_Frequent': [u'16.17'], u'NSX_Event_to_Alarm': [u'16.11']}
        return modules_highest_version

    def get_loaded_modules(self):
        """
        Get all loaded modules (both utility & rule modules)
        :raises HTTPError:
        :rtype: Instance of Response
        :returns: Response with all loaded modules
        """
        url = '/fmxadminws/v1/module/listLoaded'
        response = self.user.get(url)
        if not response.ok:
            raise HTTPError('Cannot get list of loaded modules at url: {0}'.format(str(url)), response=response)

        return response

    def _get_loaded_rule_active_modules(self, response):
        """
        Return grouped modules.
        Group by: loaded, rule, active rule modules

        :type response: Instance of Response
        :param response: Response with a list of all loaded modules

        :rtype: list, list, list
        :returns: list of loaded modules, list of rule modules, list of activated rule modules
        """
        loaded_modules = []
        rule_modules = []
        active_rule_modules = []

        for info_dict in response.json()['modules']:
            module_name = info_dict['module']['moduleInformation']['moduleName']
            module_type = info_dict['module']['moduleInformation']['type']
            active_state = info_dict['activationInformation']['activeState']
            cn_simulation = info_dict['simulation']
            if module_name == SIMULATION_MODULE and cn_simulation is True:
                log.logger.debug('module name {0} - simulation {1}'.format(module_name, cn_simulation))
                ACTIVE_SIMULATION_STATE[0] = 'Enabled'
            loaded_modules.append(module_name)
            if module_type == 'RULEMODULE':
                rule_modules.append(module_name)
                if active_state == 'ACTIVE' or active_state == 'ACTIVE_FOR':
                    active_rule_modules.append(module_name)

        return sorted(loaded_modules), sorted(rule_modules), sorted(active_rule_modules)

    def import_load(self):
        """
        Import, Load, Activate fmx modules
        """
        loaded_modules, _, _ = self._get_loaded_rule_active_modules(self.get_loaded_modules())
        imported_modules = self.get_highest_version_for_modules_in_archive()

        for fmx_module in self.all_modules:
            if fmx_module not in loaded_modules:
                if fmx_module not in imported_modules:
                    self.import_module(fmx_module)
                version = self.get_highest_version_for_modules_in_archive()[fmx_module][0]
                self.load_module(fmx_module, version)

    def activate_fmx_modules(self, nodes=None, entire_network=True):
        """
        Will activate the modules on entire network or provided nodes based on the entire_network flag
        :param nodes: nodes allocated to the profile
        :type nodes: list
        :param entire_network: flag to know if the modules are to be activated on entire network or not
        :type entire_network: bool
        """
        _, rule_modules, active_rule_modules = self._get_loaded_rule_active_modules(self.get_loaded_modules())
        for fmx_module in self.all_modules:
            if all([fmx_module in rule_modules, fmx_module not in active_rule_modules]):
                if entire_network:
                    self._activate_module(fmx_module)
                else:
                    self._activate_module_on_set_of_nodes(fmx_module, nodes)

    def _activate_module_on_set_of_nodes(self, fmx_module, nodes):
        """
        Activates FMX module on given set of nodes
        :param fmx_module: name of the fmx module to be activated
        :type fmx_module: str
        :param nodes: nodes allocated to the profile
        :type nodes: list
        :raises HTTPError: if response status is not ok
        """
        log.logger.debug('ACTIVATING FMX MODULE {0} ON {1} NODES'.format(fmx_module, len(nodes)))
        url = '/fmxadminws/v1/module/activateFor?module={0}'.format(fmx_module)
        data = {"fdn": ["NetworkElement=" + node.node_id for node in nodes if node]}

        response = self.user.post(url, data=data, headers=self.headers_application_url_encoded_utf8)
        if not response.ok:
            if 'userMessage' in response.json() and "already active" in response.json()['userMessage']:
                return
            raise HTTPError('Cannot activate module {0}'.format(fmx_module), response=response.text)

    def switch_to_ms(self):
        """
        Spawns a ssh session towards LMS or EMP based on the deployment
        :return: child with ssh terminal logged in as cloud-user
        :rtype: pexpect.spawn
        :raises EnvironError: if ssh connection fails towads the LMS or EMP
        """
        if self.CLOUD:
            log.logger.info("Executing ssh to EMP on CLOUD")
            child = pexpect.spawn('ssh -o StrictHostKeyChecking=no -i {2} {0}@{1}'.format(self.USER, get_emp(),
                                                                                          CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM,
                                                                                          timeout=30))
            child.expect('cloud-user@')
        if self.PHYSICAL:
            ms_host = get_ms_host()
            log.logger.info("the LMS host IP address is :{0}".format(ms_host))
            try:
                child = pexpect.spawn('ssh -o StrictHostKeyChecking=no root@{0}'.format(ms_host), timeout=30)
                child.expect("root@ieatlms")
            except Exception:
                raise EnvironError("The pexpect timedout! Please check if there is password-less connection setup"
                                   "between LMS and Workload VM.")
        child = self.switch_user_to_root_on_fmx_vm(child)
        return child

    @retry(retry_on_exception=lambda e: isinstance(e, EnvironError), wait_fixed=120000, stop_max_attempt_number=3)
    def switch_user_to_root_on_fmx_vm(self, child):
        """
        Switches the user from cloud-user to root on cloud or physical
        :param child: child of ssh terminal spawned
        :type child: pexpect.spawn
        :return: child with ssh terminal which has the user switched to root
        :rtype: pexpect.spawn
        :raises EnvironError: if ssh connection fails towads the fmx vm
        """
        ip = self.vm_addresses[self.index]
        log.logger.info("Connecting to FMX VM : {0}".format(ip))
        if self.CLOUD:
            try:
                child.sendline("ssh -o StrictHostKeyChecking=no -i {2} {0}@{1}".format(self.USER, ip, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP))
                child.expect("cloud-user@")
                child.sendline("sudo su - root")
                child.expect("root@")
                log.logger.info("User has root privileges on the fmx vm on cloud deployment")
            except Exception as e:
                self.index = 1 if len(self.vm_addresses) > 1 else 0
                raise EnvironError('Unable to connect to FMX vm {0}. Exception: {1}'.format(ip, e))
        else:
            try:
                child.sendline("ssh -t -o StrictHostKeyChecking=no -i /root/.ssh/vm_private_key {0}@{1} 'sudo su - root'".format(self.USER, ip))
                child.expect(["\\[root@svc-[1-9]-fmx ~\\]# ", pexpect.EOF], timeout=120, searchwindowsize=-1)
                log.logger.info("User has root privileges on the fmx vm on physical deployment")
            except Exception as e:
                self.index = 1 if len(self.vm_addresses) > 1 else 0
                raise EnvironError('Unable to connect to FMX vm {0}. Exception: {1}'.format(ip, e))
        return child

    def execute_maintenance_cmd(self, node_signature, put_node_in_maintenance_cmd):
        """
        Execute maintenance mode command on nodes
        :type node_signature: list
        :param node_signature: nodes to be set in maintenance
        :type put_node_in_maintenance_cmd: str
        :param put_node_in_maintenance_cmd: 1 of modes, ex.: 'MARK', 'NMS', 'NMSandOSS'.
        :raises ShellCommandReturnedNonZero: if the command rc code is not equal to 0
        """
        index = 0
        vm_address = None
        log.logger.debug("Executing maintenance mode command on nodes")
        while index < len(self.vm_addresses):
            try:
                vm_address = self.vm_addresses[index]
                command = 'sudo {0}'.format(put_node_in_maintenance_cmd)
                if self.CLOUD_NATIVE:
                    cmd_response = shell.run_cmd_on_cloud_native_pod('fmx-engine', vm_address, command)
                else:
                    cmd_response = shell.run_cmd_on_vm(command, vm_address)
                if cmd_response.rc == 0:
                    log.logger.debug("Successfully set the node {0} in maintenance mode".format(node_signature))
                    break
                else:
                    raise ShellCommandReturnedNonZero(
                        'Setting node {0} in maintenance mode - failed.'.format(node_signature), cmd_response)
            except (RuntimeError, SSHException) as e:
                log.logger.debug("Could not login into the FMX VM :{0} Exception: {1}".format(vm_address, e))
                index += 1

    def set_maintenance_mode_for_nodes(self, nodes, mode, start, end):
        """
        Set nodes into maintenance mode

        :type nodes: list
        :param nodes: nodes to be set in maintenance
        :type mode: str
        :param mode: 1 of modes, ex.: 'MARK', 'NMS', 'NMSandOSS'.
        :type start: str
        :param start: starting time of the maintenance mode for nodes
        :type end: str
        :param end: expire time of the maintenance mode for nodes
        :raises ShellCommandReturnedNonZero: if the command rc code is not equal to zero
        :raises ValidationError: if the parameter maintenace is not set to True
        """

        self.maintenance = all([nodes, mode, start, end, end > start])
        if self.maintenance:
            for node in nodes:
                node_signature = ''.join([node.subnetwork, ',MeContext=', node.node_id])

                put_node_in_maintenance_cmd = '{0} -add -node {1} -Start "{2}" -End "{3}" -mode {4} -override'.format(
                    self.maintenance_script_path, node_signature, start, end, mode)
                self.execute_maintenance_cmd(node_signature, put_node_in_maintenance_cmd)
        else:
            raise ValidationError('Parameters are either missing or are not correct.')

    def _deactivate_unload_modules(self):
        """Deactivate and unload modules"""
        if self.all_modules:
            loaded_modules, rule_modules, active_rule_modules = self._get_loaded_rule_active_modules(self.get_loaded_modules())

            for fmx_module in reversed(self.all_modules):
                if fmx_module in loaded_modules and all([fmx_module in rule_modules, fmx_module in active_rule_modules]):
                    self._deactivate_module(fmx_module)
                    time.sleep(10)
            log.logger.info("Sleeping for 60 sec before unloading all the loaded modules")
            time.sleep(60)
            for fmx_module in reversed(self.all_modules):
                if fmx_module in loaded_modules:
                    self._unload_module(fmx_module)
                    time.sleep(10)

    def _get_nodes_in_maintenance(self, vm_address):
        """
        List out nodes which are in maintenance
        :return: node FDNs which are in maintenance
        :rtype: list
        :raises ShellCommandReturnedNonZero: If the return code of the response is non-zero
        """
        cmd_response = shell.run_cmd_on_vm(self.list_nodes_in_maintenance, vm_address)
        if cmd_response.rc != 0:
            raise ShellCommandReturnedNonZero('Failed to fetch the nodes in maintenance', cmd_response)
        pattern = re.compile(r'-node=(.*) -Start')
        nodes_list = pattern.findall(cmd_response.stdout)
        return nodes_list

    def _remove_from_maintenance(self):
        """
        Remove entries for nodes with still in active maintenance
        Removes them one by one
        :raises ShellCommandReturnedNonZero: if the command rc code is not zero
        """
        if self.maintenance:
            vm_address = self.vm_addresses[0]
            node_fdn_list = self._get_nodes_in_maintenance(vm_address)
            for node_fdn in node_fdn_list:
                remove_node_from_maintenance_cmd = '{0} {1}'.format(self.remove_node_from_maintenance_cmd, node_fdn)
                cmd_response = shell.run_cmd_on_vm(remove_node_from_maintenance_cmd, vm_address)
                if cmd_response.rc != 0:
                    raise ShellCommandReturnedNonZero('Failed to remove nodes from maintenance', cmd_response)

    def check_hardfilter(self, child=None):
        """
        Checks and updates the Hardfilter file with node type and SP on FMX VM
        :param child: ssh terminal spawned using pexpect
        :type child: pexpect.spawn
        :return: child with ssh terminal which has the user switched to root
        :rtype: pexpect.spawn
        :raises FileNotUpdatedError: If an error is encoutered while updating the file
        """
        if self.CLOUD_NATIVE:
            for cmd in self.update_hf_cn:
                log.logger.debug("Updating the Filter file for Hard in cENM deployment")
                response = shell.run_cmd_on_cloud_native_pod('fmx-engine', self.vm_addresses[0], cmd)
                log.logger.debug("get command response {0} : {1}".format(response.stdout, response.rc))
        else:
            try:
                for cmd in self.update_hf:
                    log.logger.info("COMMAND : {0}".format(cmd))
                    child.sendline(cmd)
                    child.expect("root@")
                    time.sleep(20)
            except:
                raise FileNotUpdatedError("{0} file has not been updated".format(self.hardfilter_path).rsplit('/', 1)[-1])
            return child

    def check_externalalarmfilter(self, child=None):
        """
        Checks and updates the external alarm filter file with node type and SP on FMX VM
        :param child: ssh terminal spawned using pexpect
        :type child: pexpect.spawn
        :return: child with ssh terminal which has the user switched to root
        :rtype: pexpect.spawn
        :raises FileNotUpdatedError: If an error is encoutered while updating the file
        """
        if self.CLOUD_NATIVE:
            cmd = self.update_eaf
            log.logger.debug("Updating the Filter file for external in cENM deployment")
            value = shell.run_cmd_on_cloud_native_pod('fmx-engine', self.vm_addresses[0], cmd)
            return value
        else:
            try:
                if not self.execute_on_transport:
                    child.sendline("echo 'Updating External Alarm Filter {1}' >> {0}filter_update_log.txt"
                                   .format(self.cnx_directory_path, datetime.now()))
                    child.expect("root@")
                    child.sendline(self.update_eaf)
                    child.expect("root@")
                    child.sendline("echo $?")
                    child.expect("root@")
                    result = child.before
                    if '0' in result.strip():
                        log.logger.info("file has been updated with the specific problems, cmd output : {}".format(result))
                    else:
                        raise FileNotUpdatedError("{0} file has not been updated".format(self.externalfilter_path).rsplit('/', 1)[-1])
                else:
                    log.logger.info("CNX rules are not supported in Transport, hence not updating external alarm filter")
            except Exception as e:
                log.logger.info("Exception encountered while updating External alarm filter : {0}".format(e))
            return child

    def update_hardfilter(self):
        """
        Updates hardfilter file on FMX VM with relevant node type and SP
        """
        if self.CLOUD_NATIVE:
            self.check_hardfilter()
        else:
            child = self.switch_to_ms()
            self.check_hardfilter(child)

    def update_externalalarmsfilter(self):
        """
        Updates external alarms filter on FMX VM file with relevant node type and SP
        """
        if self.CLOUD_NATIVE:
            self.check_externalalarmfilter()
        else:
            child = self.switch_to_ms()
            self.check_externalalarmfilter(child)

    def execute_filter_file_updates(self, execute_on_transport=False, cloud=False):
        """
        Method which will update different filter files with Node type and SP
        :param execute_on_transport: Flag which indicates if the profile is being executed in a TN server
        :type execute_on_transport: bool
        :param cloud: Flag which indicates if the profile is being executed in a CLOUD env
        :type cloud: bool
        """
        if cloud:
            self.CLOUD = True
        if execute_on_transport:
            self.execute_on_transport = True
        self.update_hardfilter()
        self.update_externalalarmsfilter()

    def remove_expired_node_entries_from_maintenance(self):
        """
        Cleans up all entries that have passed
        :raises EnvironError: If the pod is not available in cEnm
        :raises ShellCommandReturnedNonZero: If the command rc value is not equal to zero
        """
        command = self.clean_all_expired_maintenance_windows_cmd
        if self.maintenance:
            if self.CLOUD_NATIVE:
                self.vm_addresses = enm_deployment.get_pod_hostnames_in_cloud_native('fmx-engine')
                if not self.vm_addresses:
                    raise EnvironError(" Failed to get the pod ip of fmx-engine in cEnm")
                cmd_response = shell.run_cmd_on_cloud_native_pod('fmx-engine', self.vm_addresses[0], command)
            else:
                if not self.vm_addresses:
                    raise EnvironError(" Failed to get vm_addresses ")
                cmd_response = shell.run_cmd_on_vm(command, self.vm_addresses[0])
            if cmd_response.rc != 0:
                raise ShellCommandReturnedNonZero('Failed to remove expired nodes entries from maintenance.', cmd_response)

    def _teardown(self, **kwargs):
        """
        Deactivate, unload all modules.
        Remove nodes from the maintenance mode
        :param kwargs: dictionary of key and value arguments
        :type kwargs: dict
        """
        if self.maintenance:
            try:
                profile = kwargs.pop('profile', None)
                self.remove_expired_node_entries_from_maintenance()
                self._remove_from_maintenance()
                self._disable_simulation_module(SIMULATION_MODULE)
                self._deactivate_unload_modules()
                nodemanager_service_can_be_used = getattr(profile, "nodemanager_service_can_be_used", False)
                node_mgr = nodemanager_adaptor if nodemanager_service_can_be_used else node_pool_mgr
                node_mgr.deallocate_nodes(profile)
            except Exception as e:
                log.logger.info("Error encountered during teardown, Exception : {0}".format(e))
        else:
            try:
                self._disable_simulation_module(SIMULATION_MODULE)
                self._deactivate_unload_modules()
            except Exception as e:
                log.logger.info("Error encountered during teardown, Exception : {0}".format(e))

    def execute_post_fmxenmcli_creation_steps(self, username, password):
        """
        Steps that are to be executed post fmxenmcli user creation
        :param username: username of the ENM user
        :type username: str
        :param password: password for given user
        :type password: str
        """
        log.logger.info("Starting post user creation steps")
        child = self.switch_to_ms()
        child.sendline("su nmxadm")
        child.expect("nmxadm@")
        child.sendline("/opt/ericsson/fmx/configEnmCliCredentials/bin/configEnmCliCredentials")
        child.expect("Enter username:")
        child.sendline(username)
        child.expect("Enter password:")
        child.sendline(password)
        index = child.expect(["Overwrite file", pexpect.TIMEOUT])
        if index == 0:
            child.sendline("yes")
        elif index == 1:
            child.expect("nmxadm@")
        child.sendline("sudo su")
        child.expect("root@")
        child.sendline("/opt/ericsson/fmx/cli/bin/fmxcli -c flush_topology")
        child.expect("root@")
        child.sendline("exit")
        child.close()

    def execute_post_fmxenmcli_creation_steps_cloudnative(self, username, password):
        """
        Steps that are to be executed post fmxenmcli user creation for cloud native
        :param username: username of the ENM user
        :raises EnvironError: If the pod is not available in cEnm
        :type username: str
        :param password: password for given user
        :type password: str
        """
        self.vm_addresses = enm_deployment.get_pod_hostnames_in_cloud_native('fmx-engine')
        if not self.vm_addresses:
            raise EnvironError(" Failed to get the pod ip of fmx-engine in cEnm")
        child = pexpect.spawn('kubectl -n {0} exec -it {1} -- bash'.format(get_enm_cloud_native_namespace(), self.vm_addresses[0]), timeout=30)
        child.expect("fmx-engine")
        child.sendline("su nmxadm")
        child.expect("nmxadm@fmx-engine")
        child.sendline("/opt/ericsson/fmx/configEnmCliCredentials/bin/configEnmCliCredentials")
        child.expect("Enter username:")
        child.sendline(username)
        child.expect("Enter password:")
        child.sendline(password)
        index = child.expect(["Overwrite file", pexpect.TIMEOUT])
        if index == 0:
            child.sendline("yes")
        elif index == 1:
            child.expect("nmxadm@")
        child.sendline("sudo su")
        child.expect("fmx-engine")
        child.sendline("/opt/ericsson/fmx/cli/bin/fmxcli -c flush_topology")
        child.expect("fmx-engine")
        child.sendline("exit")
        child.close()
