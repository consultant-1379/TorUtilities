import time

from requests.exceptions import HTTPError, ConnectionError

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib import load_mgr
from enmutils_int.lib.nhc import (get_time_from_enm_return_string_with_gtm_offset, create_nhc_profile, create_nhc_job,
                                  get_radio_node_package, NHC_PROFILE_LIST_URL, NHC_PROFILE_LIST_PAYLOAD)
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.shm_utilities import SoftwarePackage
from enmutils_int.lib.shm_software_ops import SoftwareOperations


class Nhc04(GenericFlow):

    def execute_nhc_04_flow(self):

        load_mgr.wait_for_setup_profile("SHM_SETUP", state_to_wait_for="COMPLETED", sleep_between=60, timeout_mins=45)
        user = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, retry=True)[0]
        nodes = self.get_nodes_list_by_attribute(
            node_attributes=["node_id", "primary_type", "mim_version", "node_name"])
        ne_names = [{'name': node.node_id} for node in nodes]
        health_check_profile_name = self.create_new_health_check_profile(user, nodes)
        scheduled_time = None

        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_day()
            if not scheduled_time:
                try:
                    scheduled_time = get_time_from_enm_return_string_with_gtm_offset(user, self.NHC_JOB_TIME)
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError("Could not) get time from the Server! "
                                                                    "Msg: {0}".format(e)))
            if scheduled_time:
                try:
                    if health_check_profile_name not in self.get_existing_health_check_profiles(user):
                        health_check_profile_name = self.create_new_health_check_profile(user, nodes)
                    log.logger.debug("Sleeping for 5 seconds before job creation")
                    time.sleep(5)
                    create_nhc_job(user=user, profile_name=health_check_profile_name, ne_elements=ne_names,
                                   scheduled_time=scheduled_time, ne_type=nodes[0].primary_type, name=self.NAME)
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))

    def create_new_health_check_profile(self, user, nodes):
        """
        Returns a new health check profile if required for the Node Health Check Job
        :param user: enm user instance to be used to perform post request
        :type user: `lib.enm_user.User`
        :param nodes: Nodes allocated to the profile
        :type nodes: list
        :return: Returns the health check profile name
        :rtype: str
        :raises EnmApplicationError: If the health check profile could not be created
        """
        profile_name = ''
        try:
            software_package = SoftwarePackage(nodes, user, use_default=True, profile_name=self.NAME)
            radio_node_package = SoftwareOperations(user=user, package=software_package, ptype=nodes[0].primary_type)
            radio_node_package.import_package()
            radio_node_package_dict = get_radio_node_package(user)
            profile_name = create_nhc_profile(user, nodes[0].primary_type, radio_node_package_dict, self.NAME)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError("Health check profile cannot be created due to - {0}".format(e.message)))
        return profile_name

    def get_existing_health_check_profiles(self, user):
        """
        Get profile name(s) for the NHC profiles which already exists
        :param user:    Enm user who performs the operations
        :type user:     `enmutils.lib.enm_user_2.User`
        :return:        list of existing NHC profile name(s)
        :rtype:         list
        """
        profile_names = []
        try:
            nhc_profiles_response = user.post(NHC_PROFILE_LIST_URL, json=NHC_PROFILE_LIST_PAYLOAD,
                                              headers=JSON_SECURITY_REQUEST)
            nhc_profiles_response.raise_for_status()
        except (ConnectionError, HTTPError) as e:
            self.add_error_as_exception(EnmApplicationError("Could not get the id(s) for NHC profile(s) "
                                                            " due to - {0}".format(e.message)))
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))
        else:
            nhc_profiles_dict = nhc_profiles_response.json()
            profile_names = [_['name'] for _ in nhc_profiles_dict['profileList'] if user.username[:6] in _['name']]
        log.logger.info("NHC profile(s) which already exist - {0}".format(profile_names))
        return profile_names
