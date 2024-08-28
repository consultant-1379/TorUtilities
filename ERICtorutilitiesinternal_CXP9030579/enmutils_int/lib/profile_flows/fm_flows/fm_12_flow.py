import time
from functools import partial

import pexpect

from enmutils.lib import log
from enmutils.lib.cache import is_enm_on_cloud_native
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.fm_bnsi_nbi import FmBnsiNbi
from enmutils_int.lib.fm_nbi import FmNbi, IPv4
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile


class Fm12(FlowProfile):
    """
    Class to run the flow for FM_12 profile which test the FM NBI interface.
    """
    FM_NBI = None
    SNMP_NBI_IP = None
    BNSI_NBI = None
    CHILD = None
    CLOUD_NATIVE = False

    def _setting_fm_nbi_framework(self):
        """
        Creates the FM NBI framework getting all the required IP addresses and copying the required testclient files
        """
        try:
            self.FM_NBI.create_nbi_framework()
            log.logger.debug('Created NBI Framework')
            self.FM_NBI.print_info()
            try:
                self.FM_NBI.transfer_files_to_ms_or_emp()
                log.logger.debug('Files transferred to the MS/EMP')
                try:
                    self.FM_NBI.check_test_client_exist()
                    log.logger.debug('Testclient OK')
                except Exception as e:
                    self.add_error_as_exception(e)
            except Exception as e:
                self.add_error_as_exception(e)
        except Exception as e:
            self.add_error_as_exception(e)

    def _set_teardown_objects(self, fm_nbi):
        """
        Adds to the teardown list the fm_nbi.teardown method to run when profiles stops
        """
        self.teardown_list.append(partial(picklable_boundmethod(fm_nbi.teardown),
                                          self.NBI_filters))

    def _get_number_of_subscriptions_to_be_created(self, user):
        """
        This method will calculate the number of CPP and SNMP subscriptions to be created based on the number of CPP and
         SNMP type of nodes present in the deployment
        :param user: enm user to perform operations on the deployment
        :type user: enmutils.lib.enm_user_2.User
        :return: Number of CPP and SNMP subscriptions
        :rtype: dict
        :raises EnvironError: When total of cpp and snmp nodes is zero
        """
        subscriptions = {}
        if not self.CORBA_ENABLED:
            subscriptions["cpp_subscriptions"] = 0
            subscriptions["snmp_subscriptions"] = self.NUMBER_NBI_SUBSCRIPTIONS
        else:
            cpp_subs = 0
            snmp_subs = 0
            total_subscriptions = self.NUMBER_NBI_SUBSCRIPTIONS
            cpp_subs = total_subscriptions / 2
            snmp_subs = total_subscriptions / 2
            log.logger.debug("SNMP subscriptions to create : {0}, "
                             "CPP subscriptions to create : {1}".format(snmp_subs, cpp_subs))
            subscriptions["cpp_subscriptions"] = int(cpp_subs)
            subscriptions["snmp_subscriptions"] = int(snmp_subs)
        return subscriptions

    @staticmethod
    def corba_nbi_taskset(_, profile):
        profile.FM_NBI.subscribe_nbi(profile.TIMEOUT_SUBSCRIPTION, profile.NBI_filters)

    def setup_corba(self):
        """
        Setup prerequisites for CORBA NBI Subscriptions
        """
        if not self.FM_NBI.is_nbi_framework_ok or self.CLOUD_NATIVE:
            self._setting_fm_nbi_framework()
        try:
            self.FM_NBI.teardown(filters=self.NBI_filters)
            log.logger.debug("Old subscriptions were cleared. Sleeping for 30 sec before creating new subscriptions")
            time.sleep(30)
        except Exception as e:
            self.add_error_as_exception(e)
        self.FM_NBI.reset_ports()
        self.FM_NBI.reset_num_filters()

    def setup_snmp(self):
        """
        Setup prerequisites for SNMP NBI Subscriptions
        """
        try:
            log.logger.debug("Clean up any existing SNMP NBI subscriptions")
            self.FM_NBI.snmp_nbi_teardown()
            log.logger.debug("Get IP of workload VM")
            self.FM_NBI.get_workload_vm_ip()
        except Exception as e:
            self.add_error_as_exception(e)

    def create_corba_subs(self, cpp_subs_to_create):
        """
        Creates given number of CORBA subscriptions
        :param cpp_subs_to_create: number of CORBA subscriptions to be created
        :type cpp_subs_to_create: int
        :raises EnvironError: if the corba nbo framework is not setup properly
        """
        try:
            if self.CORBA_ENABLED:
                if not self.FM_NBI.is_nbi_framework_ok:
                    raise EnvironError("CORBA NBI services not available on the deployment, unable to create "
                                       "CORBA subscriptions")
                tq = ThreadQueue(work_items=range(cpp_subs_to_create), num_workers=cpp_subs_to_create,
                                 func_ref=self.corba_nbi_taskset, args=[self],
                                 task_join_timeout=60 * 5, task_wait_timeout=60 * 5)
                tq.execute()
                self.process_thread_queue_errors(tq)
                log.logger.debug("FM CORBA NBI Subscriptions have been created")
        except Exception as e:
            self.add_error_as_exception(e)

    def create_snmp_subs(self):
        """
        creates SNMP subscriptions
        """
        try:
            if not self.SNMP_NBI_IP:
                raise EnvironError("FM SNMP NBI service is not available on the deployment, unable to create "
                                   "SNMP subscriptions")
            self.FM_NBI.create_fm_snmp_nbi_subscriptions()
        except Exception as e:
            self.add_error_as_exception(e)

    def common_teardown(self):
        """
        Adds objects to the teardown
        """
        if self.CORBA_ENABLED:
            self._set_teardown_objects(self.FM_NBI)
        else:
            self.teardown_list.append(picklable_boundmethod(self.FM_NBI.snmp_nbi_teardown))

    def setup_bnsi_nbi(self):
        """
        Checks and creates bnsiman01 user and enables BNSI NBI by updating the PIB parameter
        """
        if self.BNSI:
            try:
                self.BNSI_NBI.create_bnsiman_user_and_enable_bnsi_nbi()
                self.teardown_list.append(self.BNSI_NBI)
                log.logger.info("Sleeping for 180 secs before opening the BNSI NBI SSH sesison towards FM VIP")
                time.sleep(180)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))
        else:
            log.logger.info("BNSI is currently not supported for soem deployments")

    def open_bnsi_nbi_session(self):
        """
        Steps that are to be executed post bnsiman user creation
        """
        log.logger.info("Opening an SSH session towards FM VIP")
        try:
            command = ("ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {0}@{1} -p 8345 "
                       "SendAlarms bnsitest -ver 3".format(self.BNSI_NBI.username, self.BNSI_NBI.fm_vip))
            log.logger.info("SSH command : {0}".format(command))
            child = pexpect.spawn(command)
            child.expect('password:', timeout=30)
            child.sendline(self.BNSI_NBI.password)
            child.expect(['#Version=3', '%a'], timeout=120)
            child.sendcontrol('c')
            child.sendline('exit')
            log.logger.info("BNSI NBI SSH session verified")
        except Exception as e:
            log.logger.debug('Unable to connect to FM VIP {0}, Exception encountered'.format(self.BNSI_NBI.fm_vip))
            self.add_error_as_exception(EnmApplicationError(e))

    def execute_flow(self):
        """
        Runs the flow of FM_12 profile which tests CORBA NBI and FM SNMP NBI
        """
        self.state = "RUNNING"
        user, = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, safe_request=True, retry=True)
        self.CLOUD_NATIVE = is_enm_on_cloud_native()
        subscriptions_to_create = self._get_number_of_subscriptions_to_be_created(user)
        cpp_subs_to_create = subscriptions_to_create["cpp_subscriptions"]
        snmp_subs_to_create = subscriptions_to_create["snmp_subscriptions"]
        self.BNSI_NBI = FmBnsiNbi()
        self.FM_NBI = FmNbi(user=user, timeout=self.TIMEOUT, ip=IPv4, ports=cpp_subs_to_create,
                            snmp_subs_count=snmp_subs_to_create)
        self.SNMP_NBI_IP = self.FM_NBI.fetch_snmp_nbi_service_ip()
        self.setup_bnsi_nbi()
        self.common_teardown()

        while self.keep_running():
            self.sleep_until_time()
            if self.CORBA_ENABLED:
                self.setup_corba()
            else:
                self.setup_snmp()
            time.sleep(60)
            self.create_snmp_subs()
            self.create_corba_subs(cpp_subs_to_create)
            if self.BNSI:
                self.open_bnsi_nbi_session()
