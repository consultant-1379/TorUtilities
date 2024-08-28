# *******************************************************************
# Name    : LKF (License Key File)
# Summary : Primarily used by LKF profiles. Allows the user to manage
#           instantaneous licensing operation within the SHM
#           application area.
# *******************************************************************

import datetime
from time import sleep

from enmutils.lib import log
from enmutils.lib.exceptions import TimeOutError, EnmApplicationError, NetsimError
from enmutils_int.lib.netsim_operations import NetsimOperation, SimulationCommand
from enmutils_int.lib.services.deploymentinfomanager_adaptor import update_pib_parameter_on_enm
from enmutils_int.lib.shm import ShmJob

INSTANTANEOUS_LICENSING_CMD = "capacity_expansion_request;"
SERVICE_NAME = "shmserv"
JOB_TIME = 165
JOB_RETRY_SLEEP_TIME = 4


class LkfJob(ShmJob):

    def __init__(self, user, nodes, **kwargs):
        """
        Constructor for LKF jobs

        :type nodes: list
        :param nodes: List of Node objects
        :type user: `enm_user_2.User`
        :param user: user to use for the REST request
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary

        """
        self.user = user
        self.nodes = nodes
        self.job_type = kwargs.get('job_type')
        self.name = kwargs.get('name')
        self.current_time = kwargs.get('current_time')
        super(LkfJob, self).__init__(user, nodes, **kwargs)

    def set_properties(self):
        """
        Properties payload for Licensing Job
        """

    def set_activities(self):
        """
        Activities Schedule payload for Licensing Job
        """

    def check_lkf_job_status(self):
        """
        Checks the Instantaneous Licensing job status by fetching the jobs from SHM UI

        :return: All jobs are completed or not
        :rtype: bool
        :raises EnmApplicationError: If we couldn't fetch and validate the job from SHM UI
        :raises TimeOutError: If jobs couldn't complete the usecase within time
        """
        log.logger.debug("Determines the current status of the LKF Job")
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=JOB_TIME)
        while datetime.datetime.now() < expiry_time:
            lkf_job_res = self.get_lkf_job()
            success_jobs = failed_jobs = 0
            failed_job_names = []
            for lkf_job in lkf_job_res:
                if lkf_job["status"] in ["COMPLETED"]:
                    log.logger.debug('Status of the LKF Job "{0}" is "{1}"'.format(lkf_job["jobName"],
                                                                                   lkf_job["status"]))
                    success_jobs += 1
                elif lkf_job["status"] not in ["RUNNING", "CREATED"]:
                    failed_jobs += 1
                    failed_job_names.append(lkf_job["jobName"])
                    log.logger.debug("LKF Job changed to unexpected status. HTTPResponse was {0}".format(str(lkf_job)))
            total_jobs = success_jobs + failed_jobs
            if total_jobs and total_jobs == len(lkf_job_res):
                log.logger.debug("All the LKF jobs are completed")
                if failed_jobs:
                    raise EnmApplicationError("These {0} LKF Jobs changed to unexpected status."
                                              .format(failed_job_names))
                return True
            log.logger.debug("Sleeping for {0} min before re-trying..".format(JOB_RETRY_SLEEP_TIME))
            sleep(JOB_RETRY_SLEEP_TIME * 60)
        raise TimeOutError('Cannot verify the status for job "{0}"'.format(self.name))

    @staticmethod
    def update_pib_parameters(sas_ip):
        """
        Updates all the pib parameters required for INSTANTANEOUS_LICENSE_SOFTWARE
        """
        pib_dict = {"INSTANTANEOUS_LICENSE_SENTINEL_PROXY_IP_ADDRESS": sas_ip,
                    "INSTANTANEOUS_LICENSE_SOFTWARE_DROPBOX_DIRECTORY_PATH": "/Store/LicenseFiles",
                    "INSTANTANEOUS_LICENSE_SENTINEL_PROXY_PORT_NUMBER": 443,
                    "INSTANTANEOUS_LICENSE_SOFTWARE_SUPPLY_ENDPOINT": "requestIdFromElis/api/v1/licenses",
                    "INSTANTANEOUS_LICENSE_GLOBAL_CUSTOMER_ID": 1234,
                    "INSTANTANEOUS_LICENSE_SOFTWARE_DROPBOX_ID": 1234,
                    "NE_SOFTWARE_STORE_IP_ADDRESS": sas_ip,
                    "NE_SOFTWARE_STORE_PORT_NUMBER": 22,
                    "NE_SOFTWARE_STORE_USERNAME": "enmuser",
                    "INSTANTANEOUS_LICENSE_ENABLED": "true",
                    "INSTANTANEOUS_LICENSE_BATCH_REQUEST_INTERVAL_IN_MINUTES": 15,
                    "INSTANTANEOUS_LICENSE_MAX_NUMBER_OF_REQUEST_PER_BATCH": 1000}
        log.logger.debug("Updating all the required pib values for Insatantaneous Licensing Usecase")
        for pib_param, pib_val in pib_dict.items():
            update_pib_parameter_on_enm(enm_service_name=SERVICE_NAME, pib_parameter_name=pib_param,
                                        pib_parameter_value=pib_val, enm_service_locations=None,
                                        service_identifier="shm-softwarepackagemanagement-ear", scope=None)
        log.logger.debug("Succesfully updated all the pib values")

    @staticmethod
    def construct_commands_on_nodes(sim_info, cmd, sim_cmd_list, il_sim_cmd_list):
        """
        Construct commands (SimulationCommand objects) using sim_info
        :type sim_info: tuple
        :param sim_info: tuple containing host, sim, and nodes
        :type cmd: str
        :param cmd: cmd passed to SimulationCommand object that executes in netsim
        :type sim_cmd_list: list
        :param sim_cmd_list: list of SimulationCommand objects
        :type il_sim_cmd_list: list
        :param il_sim_cmd_list: list of SimulationCommand objects

        :rtype: tuple
        :return: Tuple of two lists, containing SimulationCommand objects
        """
        for host, sim, nodes in sim_info:
            il_sim_cmd_list.append(SimulationCommand(host, sim, nodes, INSTANTANEOUS_LICENSING_CMD))
            for node in nodes:
                sim_cmd_list.append(SimulationCommand(host, sim, [node], cmd.format(node=node.node_id)))
        return sim_cmd_list, il_sim_cmd_list

    def execute_il_netsim_cmd_on_nodes(self, nodes_list):
        """
        Executes Instantaneous Licensing command on netsim for all the nodes

        :type nodes_list: list
        :param nodes_list: `lib.enm_node.Node` instance
        :raises NetsimError: If command execution fails
        """
        failed_nodes_list = []
        il_sim_cmd_list = []
        sim_cmd_list = []
        cmd = ('setmoattribute:mo="ManagedElement={node},SystemFunctions=1,Lm=1,KeyFileManagement=1,'
               'KeyFileInformation=1",attributes="sequenceNumber=1";')
        log.logger.debug("Attempts to execute {0} command on all nodes".format(INSTANTANEOUS_LICENSING_CMD))
        netsim_operation = NetsimOperation(nodes_list)
        for _, sim_info in netsim_operation.node_groups.iteritems():
            sim_cmd_list, il_sim_cmd_list = self.construct_commands_on_nodes(sim_info, cmd, sim_cmd_list, il_sim_cmd_list)
        try:
            netsim_operation.execute(sim_cmd_list)
        except Exception as e:
            failed_nodes_list.append(e)
        try:
            netsim_operation.execute(il_sim_cmd_list)
        except Exception as e:
            failed_nodes_list.append(e)
        if failed_nodes_list:
            raise NetsimError("Command execution failed. Reason: {0}".format(failed_nodes_list))
