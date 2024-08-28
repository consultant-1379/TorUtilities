# ********************************************************************
# Name    : Delete Network
# Summary : Module is used by the Network tool,
#           e.g. /opt/ericsson/enmutils/bin/network clear
#           Allows the tool to delete the SubNetworks which do not
#           have child MOs, supports recursive SubNetwork deletion.
# ********************************************************************

from enmutils.lib import log
from enmutils.lib.exceptions import ScriptEngineResponseValidationError
from enmutils_int.lib.enm_user import get_workload_admin_user


class DeleteNetwork(object):

    DELETE_NETWORKELEMENT_CMD = "cmedit delete {node_ids} NetworkElement -ALL"
    DELETE_SUBNETWORK_CMD = "cmedit delete {subnetwork} -ALL"
    DELETE_MECONTEXT_CMD = "cmedit delete {node_ids} MeContext -ALL"
    DELETENRMDATAFROMENM_CMD = "cmedit action {node_ids} CmFunction deleteNrmDataFromEnm"
    GET_SUBNETWORKS_CMD = "cmedit get * SubNetwork"

    def __init__(self, node_ids="*", subnetworks="*", user=None):
        self.node_ids = node_ids
        self.subnetworks = subnetworks
        self.user = user or get_workload_admin_user()

    def delete_network_element(self):
        """
        Deletes NetworkElements on ENM
        """

        response = self.user.enm_execute(self.DELETE_NETWORKELEMENT_CMD.format(node_ids=";".join(self.node_ids)))
        output = response.get_output()
        if "ERROR" in " ".join(output) or ("instance(s) deleted" not in output[-1] and "found" not in output[-1]):
            raise ScriptEngineResponseValidationError("Failed to delete NetworkElement of nodes {0}"
                                                      "".format(";".join(self.node_ids)), response=response)

    def delete_mecontext(self):
        """
        Deletes MeContexts on ENM
        """

        response = self.user.enm_execute(self.DELETE_MECONTEXT_CMD.format(node_ids=";".join(self.node_ids)))
        output = response.get_output()
        if "ERROR" in " ".join(output) or ("instance(s) deleted" not in output[-1] and "found" not in output[-1]):
            raise ScriptEngineResponseValidationError("Failed to delete MeContext of nodes {0}"
                                                      "".format(";".join(self.node_ids)), response=response)

    def delete_nrm_data_from_enm(self):
        """
        Performs CmFunction deleteNrmDataFromEnm action on ENM
        """

        response = self.user.enm_execute(self.DELETENRMDATAFROMENM_CMD.format(node_ids=";".join(self.node_ids)))
        output = response.get_output()
        if "ERROR" in " ".join(output) or "instance(s)" not in output[-1]:
            raise ScriptEngineResponseValidationError("Failed action CmFunction for deleteNrmDataFromEnm of nodes {0}"
                                                      "".format(";".join(self.node_ids)), response=response)

    def delete_subnetwork(self):
        """
        Deletes SubNetworks from ENM
        """

        response = self.user.enm_execute(self.DELETE_SUBNETWORK_CMD.format(subnetwork=";".join(self.subnetworks)))
        output = response.get_output()
        if "ERROR" in " ".join(output) or ("instance(s) deleted" not in output[-1] and "found" not in output[-1]):
            raise ScriptEngineResponseValidationError("Failed delete Subnetwork for Subnetworks {0}"
                                                      "".format(";".join(self.subnetworks)), response=response)

    def get_all_subnetworks(self):
        """
        Get the list of SubNetworks from ENM

        :returns: List of SubNetworks strings
        :rtype: list
        """
        response = self.user.enm_execute(self.GET_SUBNETWORKS_CMD).get_output()
        return [line.split(":")[-1].strip().encode('utf-8') for line in response if "FDN" in line]

    def delete_nested_subnetwork(self):
        """
        Delete nested SubNetworks from ENM
        """
        try:
            networks = self.get_all_subnetworks()
        except Exception as e:
            log.logger.debug("Unable to retrieve SubNetwork information, error encountered:: [{0}]. "
                             "Attempting to delete Subnetwork using default behaviour.".format(str(e)))
            self.delete_subnetwork()
        else:
            for network in sorted(networks, key=len, reverse=True):
                self.subnetworks = [network]
                self.delete_subnetwork()
