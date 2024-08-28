from functools import partial

from enmutils.lib import log
from enmutils.lib.cache import is_enm_on_cloud_native
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.shell import run_cmd_on_emp_or_ms, run_cmd_on_cloud_native_pod
from enmutils_int.lib.enm_deployment import get_values_from_global_properties, get_pod_hostnames_in_cloud_native
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile


class CmExport18(FlowProfile):
    EBSTOPOLOGY_PODS = []
    BASE_READ_CMD = ("/ericsson/pib-scripts/etc/config.py read --app_server_address=evt-1-ebstopology:8080 "
                     "--service_identifier=ebs-topology-service --name={0}")
    BASE_UPDATE_CMD = ("/ericsson/pib-scripts/etc/config.py update --app_server_address=evt-1-ebstopology:8080 "
                       "--service_identifier=ebs-topology-service --name={0} --value={1}")
    BASE_READ_CMD_CN = ("/opt/ericsson/PlatformIntegrationBridge/etc/config.py read "
                        "--app_server_address={0}:8080 --service_identifier=ebs-topology-service --name={1}")
    BASE_UPDATE_CMD_CN = ("/opt/ericsson/PlatformIntegrationBridge/etc/config.py update "
                          "--app_server_address={0}:8080 --service_identifier=ebs-topology-service "
                          "--name={1} --value={2}")

    def execute_flow(self):
        """
        Execute profile flow.
        """
        try:
            self.setup()
        except Exception as e:
            self.add_error_as_exception(e)
            log.logger.debug("Profile setup failed due to {0}. Profile will not continue.".format(str(e)))
            return
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_time()
            for attr, target_value in self.ATTRS.iteritems():
                try:
                    log.logger.debug("Checking value of {0}.".format(attr))
                    current_value = self.execute_config_cmd(attr)
                    log.logger.debug("The current value of {0} is {1}.".format(attr, current_value))
                    if target_value != current_value:
                        log.logger.debug("Attempting to set {0} to {1}.".format(attr, target_value))
                        self.execute_config_cmd(attr, target_value=target_value)
                    else:
                        log.logger.debug("Attribute {0} was already set to {1}.".format(attr, target_value))

                except Exception as e:
                    self.add_error_as_exception(e)

    def setup(self):
        """
        Carry out setup steps for profile. Detect EBS Cluster and read starting values.
        :raises EnvironError: if EBSTOPOLOGY_PODS were not available on server or if starting value not found.
        """
        log.logger.debug("Attempting profile set up.")
        if is_enm_on_cloud_native():
            self.EBSTOPOLOGY_PODS = get_pod_hostnames_in_cloud_native("ebstopology")
        else:
            get_values_from_global_properties("ebstopology")

        if not self.EBSTOPOLOGY_PODS:
            raise EnvironError("EBS cluster not available on this deployment. "
                               "This profile should only be ran on a deployment that has an EBS cluster")

        for attribute in self.ATTRS.keys():
            try:
                starting_value = self.execute_config_cmd(attribute)
                self.teardown_list.append(partial(picklable_boundmethod(self.execute_config_cmd),
                                                  attribute, target_value=starting_value))

            except Exception as e:
                log.logger.debug("Failed to find starting value of {0}.".format(attribute))
                raise EnvironError(e)
        log.logger.debug("Profile setup passed.")

    def execute_config_cmd(self, target_attr, target_value=None):
        """
        Checks the current value of the provided attribute and compares.
        :param target_attr: Target attribute to read/update operation.
        :type target_attr: str
        :param target_value: Target attribute value for update operation.
        :type target_value: str
        :return: Response.stdout
        :rtype: str
        :raises EnvironError: if rc is not 0.
        """
        if is_enm_on_cloud_native():
            self.EBSTOPOLOGY_PODS = get_pod_hostnames_in_cloud_native("ebstopology")
            cmd = (self.BASE_UPDATE_CMD_CN.format(self.EBSTOPOLOGY_PODS[0], target_attr, target_value)
                   if isinstance(target_value, str)
                   else self.BASE_READ_CMD_CN.format(self.EBSTOPOLOGY_PODS[0], target_attr))
            response = run_cmd_on_cloud_native_pod('ebstopology', self.EBSTOPOLOGY_PODS[0], cmd)
        else:
            cmd = (self.BASE_UPDATE_CMD.format(target_attr, target_value) if isinstance(target_value, str)
                   else self.BASE_READ_CMD.format(target_attr))

            response = run_cmd_on_emp_or_ms(cmd)
        if response.rc != 0:
            raise EnvironError("Issue executing {0}.\n"
                               "Response code {1} : stdout :{2}".format(cmd, response.rc, response.stdout))
        return response.stdout.strip()
