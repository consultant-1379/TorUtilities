from enmutils_int.lib.node_version_support import NodeVersionSupport
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class NvsFlow(GenericFlow):

    def create_nvs_object(self):
        """
        Creates the Node Version Support object that will perform the tasks

        :rtype: `node_Version_support.NodeVersionSupport`
        :return: NVS object, which will perform the required actions
        """
        nvs_user = self.create_profile_users(1, getattr(self, 'USER_ROLES', ['ADMINISTRATOR']))[0]
        node_version = NodeVersionSupport(
            user=nvs_user, supported_ne_types=getattr(self, 'SUPPORTED_NE_TYPES', ['ERBS', 'RadioNode', 'BSC', 'RNC']))
        return node_version


class Nvs01Flow(NvsFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile

        """
        node_version = self.create_nvs_object()
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            try:
                node_version.deploy_unsupported_models()
            except Exception as e:
                self.add_error_as_exception(e)


class Nvs02Flow(NvsFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile

        """
        node_version = self.create_nvs_object()
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            try:
                node_version.remove_supported_models()
            except Exception as e:
                self.add_error_as_exception(e)
