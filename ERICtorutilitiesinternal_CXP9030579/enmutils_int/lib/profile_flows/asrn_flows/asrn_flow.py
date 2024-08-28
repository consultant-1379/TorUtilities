from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib import enm_deployment
from enmutils_int.lib.services.deployment_info_helper_methods import output_network_basic
from enmutils_int.lib.asr_management import (get_asr_config_status, perform_asr_preconditions_and_postconditions,
                                             check_if_asr_record_nb_ip_port_configured)


class ASRN01Profile(GenericFlow):

    USER = None

    def execute_flow(self):
        """
        Main flow for ASR_N_01
        """
        self.state = 'RUNNING'
        try:

            self.USER = self.create_profile_users(1, roles=self.USER_ROLES, fail_fast=False, retry=True)[0]
            self.perform_asrn_operations()
        except Exception as e:
            self.add_error_as_exception(e)

    def perform_asrn_operations(self):
        """
        This method performs some set of operations such as checks str cluster exist or not, get asrn config status,
        checks NB IP, Port configured or not for ASR Record, get synced pm enabled nodes
        """
        if enm_deployment.check_if_cluster_exists("str") and get_asr_config_status(self.USER, "ASR-N"):
            if check_if_asr_record_nb_ip_port_configured(self, "ASR_N"):
                synced_pm_enabled_nodes = self.get_allocated_synced_pm_enabled_nodes(self.USER)
                perform_asr_preconditions_and_postconditions(self, synced_pm_enabled_nodes, "ASR_N")
            else:
                raise EnvironError("ASRN record NBI IP and port does not exist either in  ENM or network file, "
                                   "please set them in network file and restart the profile", output_network_basic())
        else:
            raise EnvironError("Required STR Clusters not found or ASRN not configured in ENM")
