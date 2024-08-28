# ********************************************************************
# Name    : Network Connectivity Manager-Virtual Private Network
# Summary : It allows the user to discover VPN service details from
#           ML6691 NEs when the rest call is invoked.
# ********************************************************************
import json
from enmutils_int.lib.ncm_manager import ncm_rest_query, fetch_ncm_vm
from enmutils_int.lib.node_security import check_sync_and_remove
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib import log

VPN_SD_ENDPOINT = "/ncm/rest/management/realign-services"


class NcmVpnSd01Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "primary_type"])
        try:
            if fetch_ncm_vm() in ("1.1.1.1", None):
                raise EnvironError("NCM VM is not configured in this deployment")
            while self.keep_running():
                self.sleep_until_day()
                for user in users:
                    log.logger.debug("Executing {0} service discovery with user: {1}".format(self.NAME, user))
                    try:
                        synced_nodes, _ = check_sync_and_remove(nodes_list, user)
                        list_of_node_names = [node.node_id for node in synced_nodes]
                        update_json = {"serviceType": "L3_VPN", "nodes": list_of_node_names}
                        data = json.dumps(update_json)
                        ncm_rest_query(user, VPN_SD_ENDPOINT, data)
                    except Exception as e:
                        self.add_error_as_exception(EnmApplicationError("Unable to send post alignment to {0}: {1}"
                                                                        .format(self.NAME, str(e))))
        except EnvironError as e:
            self.add_error_as_exception(EnvironError(e))
