import re
from functools import partial
from enmutils.lib import log

from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.auto_id_management import AutoIdProfile
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class AID_SETUP(GenericFlow):
    """
    Use Case ID:        AID_SETUP
    Slogan:             Manual AutoID Management setup
    """

    NAME = "AID_SETUP"
    CMD = "cmedit get * NetworkElement.(release) -ne={} -t"

    def run(self):
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES, safe_request=True)[0]
        try:
            AutoIdProfile.change_settings(user, reserved={0: 2}, temporary={0: 1})
            for node_type in self.SUPPORTED_NODE_TYPES:
                self.verify_node_versions_on_enm(user, node_type)
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            self.teardown_list.append(partial(undo_settings_changes, user))

    def verify_node_versions_on_enm(self, user, node_type):
        """
        Verifies if all radio nodes have version greater than 19.Q2 and ERBS are of version greater than J.4
        :param user: user
        :type user: user object
        :param node_type: Node type
        :type node_type: str

        :raises EnvironError: when there nodes with versions less than 19.Q2 or J.4
        """
        log.logger.debug("Verifying node versions of following nodes: {} to check if all radio nodes have version "
                         "greater than 19.Q2 and ERBS are of version are equal to J.4".
                         format(self.SUPPORTED_NODE_TYPES))
        response = user.enm_execute(self.CMD.format(node_type))
        output = response.get_output()
        for i in range(2, len(output) - 2):
            if node_type == "RadioNode" and not re.search(r".*\t([2-9]\d{1,}...|19\.Q[3-9])", output[i]):
                raise EnvironError("Node(s) found with release version less than 19.Q2")
            elif node_type == "ERBS" and not re.search(r".*\t(J\.4)", output[i]):
                raise EnvironError("Node(s) found with release version not equal to J.4")


def undo_settings_changes(user):
    AutoIdProfile.change_settings(user, reserved={0: 2}, temporary={0: 1}, remove=True)

aid_setup = AID_SETUP()
