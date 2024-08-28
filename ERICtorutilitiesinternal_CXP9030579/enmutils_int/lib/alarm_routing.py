# ********************************************************************
# Name    : Alarm Routing
# Summary : Allows creation, enabling, disabling and deletion of FM
#           alarm route policies.
# ********************************************************************

from enmutils.lib import log
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, AlarmRouteExistsError


class AlarmRoutePolicy(object):

    CREATE_ALARM_ROUTE_POLICY_ON_NODES = 'fmedit create name={name} description="{description}",fdn=' \
                                         '"{node_fqdns}",enablePolicy=true,outputType=Auto_Ack'
    CREATE_ALARM_ROUTE_POLICY_ON_NETWORK = "fmedit create name={name} description='{description}',enablePolicy=true," \
                                           "outputType=Auto_Ack"
    SET_ALARM_ROUTE_POLICY = "fmedit set * AlarmRoutePolicy.(name=={name}) enablePolicy='{is_policy_enabled}'"
    DELETE_ALARM_ROUTE_POLICY = "fmedit delete * AlarmRoutePolicy.(name=={name})"

    def __init__(self, user, name=None, nodes=None, description=None):
        """
        AlarmRoutePolicy Constructor

        :type name: string
        :param name: Name for AlarmRoutePolicy
        :type nodes: list
        :param nodes: list of enm_node.BaseNode objects to implement alarm route policy on
        :type description: string
        :param description: description of nodes
        :type user: enm_user.User instance
        :param user: User that will issue CRUD commands on the alarm route policy
        """
        self.name = name
        self.nodes = nodes
        self.description = description if description else "enmutils"
        self.user = user
        if nodes:
            self.nodes = []
            for node in nodes:
                node_name = "NetworkElement={0}".format(node.node_id)
                self.nodes.append(node_name)

    def _teardown(self):
        """
        Secret teardown method for Workload
        """
        try:
            self.disable()
            self.delete()
        except Exception as e:
            log.logger.debug(str(e))

    def create(self):
        """
        Creates AlarmRoutePolicy on ENM
        :raises ScriptEngineResponseValidationError: if issue with enm client scripting
        :raises AlarmRouteExistsError: if the alarm route with the same name already exists
        """
        command = (self.CREATE_ALARM_ROUTE_POLICY_ON_NETWORK.format(name=self.name, description=self.description) if not self.nodes
                   else self.CREATE_ALARM_ROUTE_POLICY_ON_NODES.format(name=self.name, node_fqdns=",".join(self.nodes),
                                                                       description=self.description))
        command_response = self.user.enm_execute(command)
        if "already exists" in " ".join(command_response.get_output()):
            raise AlarmRouteExistsError('"%s" already exists' % self.name)
        elif "successfully" not in " ".join(command_response.get_output()):
            raise ScriptEngineResponseValidationError(
                "Failed to Create AlarmRoutePolicy with name={name}\n"
                "RESPONSE: {response}".format(name=self.name, response="\n".join(command_response.get_output())),
                response=command_response)
        log.logger.debug("Successfully created AlarmRoutePolicy named {0}".format(self.name))

    def enable(self):
        """
        Enables AlarmRoutePolicy on ENM
        :raises ScriptEngineResponseValidationError: if issue with enm client scripting
        """
        command = self.SET_ALARM_ROUTE_POLICY.format(name=self.name, is_policy_enabled="true")
        command_response = self.user.enm_execute(command)

        if "successfully" not in " ".join(command_response.get_output()):
            raise ScriptEngineResponseValidationError(
                "Failed to Enable AlarmRoutePolicy with name={name}\n"
                "RESPONSE: {response}".format(name=self.name, response="\n".join(command_response.get_output())),
                response=command_response)
        log.logger.debug("Successfully enabled AlarmRoutePolicy named {0}".format(self.name))

    def disable(self):
        """
        Disables AlarmRoutePolicy on ENM
        :raises ScriptEngineResponseValidationError: if issue with enm client scripting
        """
        command = self.SET_ALARM_ROUTE_POLICY.format(name=self.name, is_policy_enabled="false")
        command_response = self.user.enm_execute(command)
        if "Already in Deactive state" in " ".join(command_response.get_output()):
            log.logger.info("The alarm route {0} is already disabled! \n"
                            "RESPONSE : {1}".format(self.name, "\n".join(command_response.get_output())))
        elif "successfully" not in " ".join(command_response.get_output()):
            raise ScriptEngineResponseValidationError(
                "Failed to Disable AlarmRoutePolicy with name={name}\n"
                "RESPONSE: {response}".format(name=self.name, response="\n".join(command_response.get_output())),
                response=command_response)
        else:
            log.logger.debug("Successfully disabled AlarmRoutePolicy named {0}".format(self.name))

    def delete(self):
        """
        Deletes AlarmRoutePolicy on ENM
        :raises ScriptEngineResponseValidationError: if issue with enm client scripting
        """
        command = self.DELETE_ALARM_ROUTE_POLICY.format(name=self.name)
        command_response = self.user.enm_execute(command)
        if "successfully" not in " ".join(command_response.get_output()):
            raise ScriptEngineResponseValidationError(
                "Failed to Delete AlarmRoutePolicy with name={name}\n"
                "RESPONSE: {response}".format(name=self.name, response="\n".join(command_response.get_output())),
                response=command_response)
        log.logger.debug("Successfully deleted AlarmRoutePolicy named {0}".format(self.name))
