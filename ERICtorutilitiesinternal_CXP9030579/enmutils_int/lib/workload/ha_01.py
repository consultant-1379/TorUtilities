from enmutils.lib import log
from enmutils_int.lib.profile import Profile


class HA_01(Profile):
    """
    Use Case ID:        HA_01
    Slogan:             BladeRunners reserve 25 ERBS, 5 Router6672 or Router6675, and 3 BSC nodes.
    """
    NAME = 'HA_01'
    EXCLUSIVE = True

    def run(self):
        self.state = "RUNNING"
        log.logger.debug("Nodes used by HA: {0}".format([str(node.node_id) for node in self.get_nodes_list_by_attribute()]))


ha_01 = HA_01()
