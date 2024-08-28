# ********************************************************************
# Name    : NHM Widget
# Summary : Primarily used by NHM profiles. Allows user to configure
#           and view widgets in the NHM application, a widget being
#           any component in the GUI, it can be something simple like
#           a button or more complex like a dynamically generated
#           graph.
# ********************************************************************

import ast
import json
import time
import random
from random import randint, sample, choice

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib.nhm import NhmKpi

CREATED_BY_DEFAULT = "Ericsson"
KPI_NAME_DEFAULT = u'NHM_01'
CREATE_NETWORK_SCOPE_URL = "oss/nhm/networkscope"
SELECTED_NETWORK_SCOPE_URL = "oss/nhm/networkscope/selected"
NETWORK_SCOPE_URL = "rest/ui/settings/networkhealthmonitor/nodescope"
DELETE_NETWORK_SCOPE_ALL = "oss/nhm/networkscope/delete/match"
GET_KPI_ATTRIBUTES_URL = "kpi-specification-rest-api-war/kpi/attributes/"
GET_KPI_ATTRIBUTES_PAYLOAD = {"kpiNames": None, "attributes": ["NAME", "ACTIVE", "UNIT", "THRESHOLD",
                                                               "IS_SMALLER_BETTER", "REPORTING_OBJECT_TYPES"]}


class NhmWidget(object):

    CURRENT_VIEW_URL = "/rest/ui/settings/networkhealthmonitor/dashboard"
    VALUE = '{"type": "Dashboard", "layout": "one-column", "items":[<items>]}'

    def __init__(self, user, nodes, kpi_type=None, kpi_present=True):
        self.user = user
        self.kpi_type = kpi_type
        self.kpi_present = kpi_present
        self.headers_dict = JSON_SECURITY_REQUEST
        self.node_poids = []

        if nodes:
            self.node_poids = {node.node_id: node.poid for node in nodes}
            self.poids = [int(node.poid) for node in nodes]
            self.node_ne_types = {node.poid: node.primary_type for node in nodes}
            self.ne_types = list(set(node.primary_type for node in nodes))
        else:
            log.logger.debug("Widget initialize with no nodes")

        self.network_scope = None
        self.selected_scope_id = None
        self.kpis = None
        self.created_configured = False

    @classmethod
    def number_created_configured_widgets(cls, widgets):
        """
        Returns the number of created and configured widgets

        :param widgets: List of NhmWidget objects
        :type widgets: list

        :return: Number of created and configured widgets
        :rtype: int
        """

        number_widgets = 0
        for widget in widgets:
            if widget.created_configured:
                number_widgets += 1

        return number_widgets

    def create(self):
        """
        Creates a NHM Widget
        """

        items = []
        self.get_network_element_scope()
        if not self.network_scope:
            self.create_network_element_scope()

        # Build widget payload for create based on widget type
        self.configure()
        log.logger.debug("Creating Widget")
        self.CREATE_PAYLOAD["config"]["groupName"] = self.network_scope

        # Get current widgets so we can add new widget to scope
        payload = self._get_widgets()

        if not payload:
            items.append(self.CREATE_PAYLOAD)
        else:
            value = payload[0]["value"].replace("false", "False").replace("true", "True")

            value = value.replace("null", "None")
            items = ast.literal_eval(value)["items"][0]
            items.append(self.CREATE_PAYLOAD)

        # Convert any python booleans to json booleans before casting items to string
        value = self.VALUE.replace("<items>", str(json.dumps(items))).replace("u\"", "\"")

        response = self.user.put(url=self.CURRENT_VIEW_URL, data=json.dumps({"id": self.user.workspace_id, "value": value}), headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()

    def delete(self):
        """
        Deletes all NHM Widgets associated with a user
        """

        data = {"id": self.user.workspace_id, "value": '{"type":"Dashboard","layout":"one-column","items":[[]]}'}

        response = self.user.put(url=self.CURRENT_VIEW_URL, data=json.dumps(data), headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()
        log.logger.debug("Deleted widget for user {0}".format(self.user.username))

    def _get_widgets(self):
        """
        Gets the current widgets associated with a user

        :return: Json response that contains all widgets
        :rtype: response.json
        """

        response = self.user.get(url=NhmWidget.CURRENT_VIEW_URL)
        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    def get_kpi_names(self):
        """
        Gets the list of KPI names available on the system

        :return: List of KPI names
        :rtype: list
        """
        return [kpi['kpiName'] for kpi in self._get_available_kpis()]

    def _get_available_kpis(self):
        """
        Gets the available KPIs on the system

        :return: List of available/activated KPIs
        :rtype: list
        :raises HTTPError: if post request to get attributes endpoint fails
        """
        response = self.user.post(url=GET_KPI_ATTRIBUTES_URL, data=json.dumps(GET_KPI_ATTRIBUTES_PAYLOAD),
                                  headers=self.headers_dict)
        kpis = []

        if response.status_code == 200 and response.json():
            for kpi in response.json():
                kpis.append({u'kpiName': kpi[0], u'active': kpi[1], u'kpiUnit': kpi[2], u'systemThreshold': None,
                             u'smallerBetter': kpi[4], u'measurementOn': kpi[5]})
        else:
            response.raise_for_status()

        return kpis

    def create_network_element_scope(self):
        """
        Creates the networkScope associated with the user
        """

        network_scope = "networkhealthmonitor:networkscope.{0}.{1}"\
            .format(time.time(), randint(1, 1000) * 1000000)

        response = self.user.post(url=CREATE_NETWORK_SCOPE_URL,
                                  data=json.dumps({"scopeId": network_scope,
                                                   "poidList": [int(poid) for poid in self.node_poids.values()]}),
                                  headers=self.headers_dict)

        if response.status_code != 200:
            self.network_scope = None
            response.raise_for_status()
        else:
            self.network_scope = network_scope

        log.logger.debug("Successfully created network element scope to: {0}".format(self.network_scope))

        self._set_selected_nodes()
        self._set_user_network_element_scope()
        self.get_network_element_scope()

    def get_network_element_scope(self):
        """
        Checks for existing networkScope associated with the user
        """

        response = self.user.get(url=NETWORK_SCOPE_URL, headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()
        if response.json():
            value_dict = ast.literal_eval(response.json()[0]["value"].replace("false", "False").replace("true", "True"))
            if "scopeId" in value_dict:
                self.network_scope = value_dict["scopeId"]
            if "selectedScopeId" in value_dict:
                self.selected_scope_id = value_dict["selectedScopeId"]
            log.logger.debug("User {0} using network scope: {1} with {2}".format(self.user.username, self.network_scope,
                                                                                 response.json()))

    def _set_selected_nodes(self):
        """
        Set the nodes selected for the widgets
        """

        data = {"scopeId": self.network_scope, "poidList": [int(poid) for poid in self.node_poids.values() if poid]}
        response = self.user.post(url=SELECTED_NETWORK_SCOPE_URL, data=json.dumps(data), headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()
        log.logger.debug("Successfully set selected nodes for {0}".format(self.user.username))

    def _set_user_network_element_scope(self):
        """
        Set the networkScope associated with the user
        """

        data = {"id": self.user.workspace_id,
                "value": str(json.dumps({"scopeId": self.network_scope,
                                         "selectedScopeId": self.network_scope,
                                         "selectedCount": len(self.node_poids),
                                         "isShown": True,
                                         "totalCount": len(self.node_poids)}))}

        response = self.user.put(url=NETWORK_SCOPE_URL, data=json.dumps(data), headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()
        log.logger.debug("Successfully set user network element scope for {0}".format(self.user.username))

    def _remove_network_scope(self):
        """
        Delete the networkScope associated with the user
        """

        body = {"partialScopeId": self.network_scope[21:]}
        response = self.user.put(url=DELETE_NETWORK_SCOPE_ALL, data=json.dumps(body), headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()
        log.logger.debug("Successfully deleted the network scope for {0}. Network scope {1}".format(self.user.username, self.network_scope))

    def configure(self):
        raise NotImplementedError("No configure method defined")

    def _teardown(self):
        log.logger.debug("Tearing down user's widget {0}".format(self.user.username))
        try:
            self.delete()
        except Exception as e:
            log.logger.debug(str(e))
        self._remove_network_scope()

    def teardown(self):
        self._teardown()


class NodesBreached(NhmWidget):

    SET_BREACH_SUMMARY = "oss/nhm/kpi/breachSummary?group={0}"
    CREATE_PAYLOAD = {"maximizeText": "Maximize", "minimizeText": "Minimize",
                      "config": {"selectedKpis": [], "groupName": "", "appTitle": "Nodes Breached per KPI"},
                      "settings": True, "header": "Nodes Breached per KPI", "maximizable": False, "closeText": "Close",
                      "closable": True, "type": "KpiBreachWidget"}

    def __init__(self, *args, **kwargs):
        self.number_of_kpis = kwargs.pop("number_of_kpis", 1)
        super(NodesBreached, self).__init__(*args, **kwargs)

    def configure(self):
        """
        Configuration needed to create a widget
        """

        log.logger.debug("Configure NodesBreached Widget")
        available_kpis = self._get_available_kpis()
        if available_kpis:
            self.kpis = [kpi for kpi in available_kpis if "NHM_14" not in kpi.get("kpiName")]
        if self.kpis:
            kpi_list = sample(self.kpis, self.number_of_kpis) if len(self.kpis) >= self.number_of_kpis else self.kpis

            self.CREATE_PAYLOAD["config"]["selectedKpis"] = kpi_list
            self.get_kpis()
        else:
            raise EnvironError("No active KPIs found to configure the widget")
        self.created_configured = True

    def get_kpis(self):
        """
        Set the KPI to be used in the widget
        """

        if self.kpis:
            data = {"kpiVo": self.kpis}
            response = self.user.post(url=self.SET_BREACH_SUMMARY.format(self.network_scope), data=json.dumps(data),
                                      headers=self.headers_dict)
            if response.status_code != 200:
                response.raise_for_status()
        else:
            log.logger.info("No KPIs available for Nodesbreached widget")
            response = None
        return response


class WorstPerforming(NhmWidget):

    SET_ATTRIBUTES = "kpi-specification-rest-api-war/kpi/attributes/"
    CREATE_PAYLOAD = {"header": "Worst Performing Nodes By KPI", "type": "TopWorstPerformers",
                      "maximizable": False, "closable": True, "maximizeText": "Maximize",
                      "minimizeText": "Minimize", "closeText": "Close", "settings": True,
                      "config": {"kpiName": "", "groupName": "",
                                 "appTitle": "Worst Performing Nodes By KPI",
                                 "smallerBetter": True, "linkOptions": [], "unit": "", "thresholdValue": ""}}

    def __init__(self, *args, **kwargs):
        self.kpi_name = kwargs.pop("kpi_name", None)
        self.widget_kpi = None
        super(WorstPerforming, self).__init__(*args, **kwargs)

    def configure(self):
        """
        Configuration needed to create a widget
        """
        available_kpis = self._get_available_kpis()
        if available_kpis:
            self.kpis = [kpi for kpi in available_kpis if "NHM_14" not in kpi.get("kpiName")]
        if self.kpis:
            if not self.kpi_name:
                self.widget_kpi = choice(self.kpis) if self.kpis else None
                self.kpi_name = self.widget_kpi["kpiName"]
            else:
                self.widget_kpi = NhmKpi.get_kpi_info(self.user, self.kpi_name)

            self.widget_kpi = NhmKpi.get_kpi_info(self.user, self.kpi_name)
            self.CREATE_PAYLOAD["config"]["kpiName"] = self.widget_kpi["name"]
            self.CREATE_PAYLOAD["config"]["unit"] = "%" if self.widget_kpi["kpiModel"]["unit"] == "PERCENTAGE" else "kbps"
            self.CREATE_PAYLOAD["config"]["thresholdValue"] = str(self.widget_kpi["kpiActivation"]["threshold"]["thresholdValue"])
            log.logger.debug("Configure WorstPerforming Widget")
        else:
            raise EnvironError("No active KPIs found to configure the widget")
        self.created_configured = True

    def get_kpi_with_results(self):
        """
        Retrieves a new valid active KPI from ENM to monitor and configure it to the widget discarding the monitoring of the current problematic KPI

        :return: kpi name
        :rtype: str
        :raises EnvironError: if no result found for the widget KPIs
        """
        kpi_with_no_results = []
        kpi_with_no_results.append(self.kpi_name)

        pattern_to_exclude = 'NHM_03'
        all_active_kpis = NhmKpi.get_all_kpi_names_active(self.user, exclude=pattern_to_exclude)

        if not all_active_kpis:
            raise EnvironError("There are no active KPI's on the system to assign to the Widget: '{0}'. Please check your ENM deployment.".format(self.__class__.__name__))
        else:
            log.logger.debug("Removing all KPI's deemed problematic: {0} from the list of active KPI's on ENM: {1}".format(kpi_with_no_results, all_active_kpis))
            for kpi in kpi_with_no_results:
                try:
                    all_active_kpis.remove([kpi])
                except ValueError:
                    log.logger.debug("ERROR - The KPI '{0}' either contains the pattern '{1}' or has been unexpectedly removed or deactivated from ENM. Please check your ENM deployment.".format(kpi, pattern_to_exclude))

            log.logger.debug("A new KPI will be picked from the new list of usuable active KPI's on ENM: '{0}'.".format(all_active_kpis))

            if len(all_active_kpis) > 0:
                index_kpi = random.randint(0, len(all_active_kpis) - 1)
                self.kpi_name = all_active_kpis[index_kpi][0]
                self.configure()
            else:
                raise EnvironError("There are currently no usuable active KPI's in ENM to select and assign to the Widget '{0}'. Please check your ENM deployment.".format(self.__class__.__name__))

        return self.kpi_name


class MostProblematic(NhmWidget):

    CREATE_SUBSCRIPTION_URL = "alarmcontroldisplayservice/alarmMonitoring/alarmoverviewdashboard/subscription"
    CREATE_PAYLOAD = {"header": "Most Problematic Node By Alarm Count", "type": "NodeRankingByAlarmCount",
                      "maximizable": False, "closable": True, "maximizeText ": "Maximize",
                      "minimizeText": "Minimize", "closeText": "Close", "settings": True,
                      "config": {"appTitle": "Most Problematic Node By Alarm Count", "isDashboard": True,
                                 "settings": True, "maximizable": True, "groupName": "",
                                 "linkOptions": [{"name": "Monitor this Node", "value": "#nodemonitor?poid=poID"}]}}

    def __init__(self, *args, **kwargs):
        super(MostProblematic, self).__init__(*args, **kwargs)
        self.polling_id = None

    def configure(self):
        """
        Configuration needed to create a widget
        """
        log.logger.debug("Configure MostProblematic Widget")
        self._create_alarm_polling()
        self.created_configured = True

    def _create_alarm_polling(self):
        """
        Create subscription to monitor alarms
        """

        data = {"groupName": self.network_scope, "widgetAttributes": {
            "widgetName": "Most Problematic Node By Alarm Count", "configuration":
            {"count": 10}}}
        response = self.user.post(url=self.CREATE_SUBSCRIPTION_URL, data=json.dumps(data), headers=self.headers_dict)
        if response.status_code != 200:
            response.raise_for_status()
        self.polling_id = response.json()
        log.logger.debug("Created alarm polling")


class NetworkOperationalState(NhmWidget):

    CREATE_PAYLOAD = {"header": "Network Operational State", "type": "NetworkStatusWidget", "maximizable": False,
                      "closable": True, "maximizeText": "Maximize", "minimizeText": "Minimize",
                      "closeText": "Close", "settings": False, "config": {"groupName": "",
                                                                          "baseURL": "network-status-rest-service"}}

    def __init__(self, *args, **kwargs):
        super(NetworkOperationalState, self).__init__(*args, **kwargs)

    def configure(self):
        """
        Configuration needed to create a widget
        """

        self.created_configured = True
        log.logger.debug("NetworkOperationalState widget configured")


class NetworkSyncStatus(NhmWidget):

    CREATE_PAYLOAD = {"header": "Network Sync Status", "type": "NetworkStatusWidget", "maximizable": False,
                      "closable": True, "maximizeText": "Maximize", "minimizeText": "Minimize",
                      "closeText": "Close", "settings": False, "config": {"groupName": "",
                                                                          "baseURL": "network-status-rest-service"}}

    def __init__(self, *args, **kwargs):
        super(NetworkSyncStatus, self).__init__(*args, **kwargs)

    def configure(self):
        """
        Configuration needed to create a widget
        """

        self.created_configured = True
        log.logger.debug("Configured the Network Sync Status Widget")


class CellStatus(NhmWidget):

    VALUE = '{"type": "Dashboard", "layout": "one-column", "items":[<items>], ' \
            '"showEmptyColumnPlaceholders": false, "poid": <poid>, "neType": "<ne_type>"}'
    CURRENT_VIEW_URL = "/rest/ui/settings/nodemonitor/dashboard"
    CELL_STATUS_URL = "/oss/nhm/kpi/cellstatus/{0}?kpi={1}"
    CREATE_PAYLOAD = {"header": "Cell Status", "type": "CellStatusWidget", "maximizable": False, "closable": True,
                      "maximizeText": "Maximize", "minimizeText": "Minimize", "closeText": "Close",
                      "settings": True, "config":
                          {"poid": "", "neType": "ERBS", "isDashboard": True,
                           "kpi": {"name": "", "value": "", "unit": "", "type": False, "status": True}}}

    def __init__(self, *args, **kwargs):
        super(CellStatus, self).__init__(*args, **kwargs)
        self.widget_kpi = None
        if self.node_poids:
            if len(self.node_poids) > 1:
                self.poid = self.node_poids.values()[randint(1, len(self.node_poids) - 1)]
            else:
                self.poid = self.node_poids.values()[0]

            self.ne_type = self.node_ne_types[self.poid]
        else:
            log.logger.debug("No poids associated to this widget")

    def configure(self):
        """
        Configuration needed to create a widget
        """

        if self.kpi_present:
            available_kpis = self._get_available_kpis()
            if available_kpis:
                self.kpis = [kpi for kpi in available_kpis if "NHM_14" not in kpi.get("kpiName")]
            if self.kpis:
                if len(self.kpis) > 1:
                    self.widget_kpi = sample(self.kpis, randint(1, len(self.kpis) - 1))
                    self.widget_kpi = self.widget_kpi[0]
                else:
                    self.widget_kpi = self.kpis[0]
            else:
                raise EnvironError("No active KPIs found to configure the widget")
            log.logger.debug("widget_kpi: {0}".format(self.widget_kpi))
            self.widget_kpi = NhmKpi.get_kpi_info(self.user, self.widget_kpi["kpiName"])
            log.logger.debug("widget_kpi: {0}".format(self.widget_kpi))
            self.VALUE = self.VALUE.replace("<poid>", self.poid)
            self.VALUE = self.VALUE.replace("<ne_type>", self.ne_type)
            self.CREATE_PAYLOAD["config"]["kpi"]["name"] = self.widget_kpi["name"]
            self.CREATE_PAYLOAD["config"]["kpi"]["value"] = str(self.widget_kpi["kpiActivation"]["threshold"]["thresholdValue"])
            self.CREATE_PAYLOAD["config"]["kpi"]["unit"] = "%" if self.widget_kpi["kpiModel"]["unit"] == "PERCENTAGE" else "kbps"
            self.CREATE_PAYLOAD["config"]["kpi"]["status"] = self.widget_kpi["kpiActivation"]["active"]
            self.CREATE_PAYLOAD["config"]["poid"] = self.poid
            self.CREATE_PAYLOAD["config"]["neType"] = self.ne_type
        else:
            log.logger.debug("CellStatusWidget with no KPI assigned")
        log.logger.debug("Configure CellStatus Widget")
        self.created_configured = True
