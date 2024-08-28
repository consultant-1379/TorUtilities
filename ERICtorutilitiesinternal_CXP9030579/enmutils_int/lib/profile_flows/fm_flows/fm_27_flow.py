from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib import load_mgr
from enmutils_int.lib.common_utils import split_list_into_sublists
from enmutils_int.lib.fm import FmAlarmRoute
from enmutils_int.lib.nhm import sleep_until_profile_persisted
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class Fm27(GenericFlow):
    """
    Class for FM_27. Alarm Routing Save To File.
    """

    def execute_flow(self):
        number_of_policies_sucessfuly_created = 0

        # sleep until fm_01 is started on the system, then wait until fm_0506 is completed
        log.logger.debug("Waiting for FM_01 to be started on the system.")
        sleep_until_profile_persisted("FM_01")
        log.logger.debug("Waiting for FM_0506 to be completed.")
        load_mgr.wait_for_setup_profile("FM_0506")

        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES, safe_request=True)[0]
        self.state = "RUNNING"
        profile_nodes = self.get_allocated_nodes("FM_01")

        # split nodes in to n lists to be added in to n routing polices
        node_lists = split_list_into_sublists(profile_nodes, self.NUMBER_OF_ROUTING_FILES)
        log.logger.info("Creating {} Routing Policies.".format(len(node_lists)))

        for sublist in node_lists:
            name = '_Routing_'.join([self.NAME, self.get_timestamp_str()])
            fm_route = FmAlarmRoute(user, sublist, name, name)
            try:
                fm_route.create()
                self.teardown_list.append(fm_route)
            except Exception as e:
                self.add_error_as_exception(EnvironError("Creation of Routing Policy {} failed with message: {}".
                                                         format(name, e.message)))
            else:
                log.logger.info("Successfully created Routing Policy {}".format(name))
                number_of_policies_sucessfuly_created += 1

        log.logger.info("Profile execution completed. Number of Routing Policies sucessfuly created: {}"
                        .format(number_of_policies_sucessfuly_created))
