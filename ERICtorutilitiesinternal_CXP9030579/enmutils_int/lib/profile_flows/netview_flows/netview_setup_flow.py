from random import uniform

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.netview import NodeLocation, get_existing_locations, delete_location_on_node
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class NetviewSetupFlow(GenericFlow):

    def __init__(self, *args, **kwargs):
        self.number_of_locations_created = 0
        self.user = None
        super(NetviewSetupFlow, self).__init__(*args, **kwargs)

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.user = self.create_profile_users(self.NUM_USERS, ["ADMINISTRATOR"])[0]
        self.state = "RUNNING"

        self._delete_existing_locations()

        for node in self.get_nodes_list_by_attribute():
            longitude = uniform(1, 37.91496)
            latitude = uniform(1, 37.91496)
            location = NodeLocation(self.user, node.node_id, longitude, latitude)
            try:
                location.create_geo_location()
                location.create_geo_point()
            except Exception as e:
                self.add_error_as_exception(EnvironError("Profile could not create location MO on {0} msg: {1}"
                                                         .format(node.node_id, e)))
            else:
                self.teardown_list.append(location)
                try:
                    location.create_latitude_and_longitude()
                    self.number_of_locations_created += 1
                except Exception as e:
                    self.add_error_as_exception(EnvironError("Profile could not set location on {0} msg: {1}"
                                                             .format(node.node_id, e)))

        log.logger.info("Successfully created coordinates on {0} out of {1} nodes"
                        .format(self.number_of_locations_created, self.TOTAL_NODES))

    def _delete_existing_locations(self):
        """
        Function to delete existing coordinates
        """
        nodes_with_locations = []
        try:
            nodes_with_locations = get_existing_locations(self.user)
        except Exception as e:
            self.add_error_as_exception(EnvironError("Could not retrieve a list of nodes with locations msg: {}"
                                                     .format(e)))
        if nodes_with_locations:
            for node_id in nodes_with_locations:
                try:
                    delete_location_on_node(self.user, node_id)
                except Exception as e:
                    self.add_error_as_exception(EnvironError("Could not delete location on {0} msg: {1}"
                                                             .format(node_id, e)))
        log.logger.info("Initial Clean Up finished.")
