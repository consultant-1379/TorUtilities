# ********************************************************************
# Name    : NHM UI
# Summary : Functional module used by NHM profiles. Provides some
#           basic URI navigation related to the NHM UI, home page,
#           widget views, mimics additional responses sent when an
#           end user would request the resource in the UI.
# ********************************************************************

import json
import time
from random import randint, shuffle, sample, choice
from retrying import retry
from requests.exceptions import HTTPError, ConnectionError
from enmutils.lib import log
from enmutils_int.lib.nhm_widget import (NhmWidget, NodesBreached, WorstPerforming, MostProblematic,
                                         NetworkOperationalState, CellStatus)

ALL_OPERATION_STATES = {"state": "OPERATIONAL", "filter": "count"}
NHA_TABLE_URL = "/oss/nhm/nha/nhaTable"
NETWORK_SCOPE_URL = "oss/nhm/networkscope"

KPI_ATTRIBUTES_URL = "kpi-specification-rest-api-war/kpi/attributes/"
LOAD_KPI_PAYLOAD = {"kpiNames": None, "attributes": ["ACTIVE", "UNIT", "THRESHOLD"]}


def create_nha_cell_tab_payload(scope_id, poids, kpi_name):
    """
    Creates a payload for the NHA cell tab request
    :param scope_id: Network scope id
    :type scope_id: str
    :param poids: List of poids to be used in the request
    :type poids: list
    :param kpi_name: Kpi to be used in the request
    :type kpi_name: str
    :return: payload body
    :rtype: dict
    """

    nha_cell_tab_payload = {"tableType": {"nhaFeature": "NHA_CELL", "moTypes": ["EUtranCellFDD", "EUtranCellTDD", "NbIotCell"]},
                            "export": False,
                            "dataSources": [{"type": "KPI", "query": {"nodeQuery": {"scopeId": scope_id,
                                                                                    "poIds": poids},
                                                                      "kpiValueQueries": [{
                                                                          "kpiName": kpi_name,
                                                                          "rops": 1,
                                                                          "columnName": kpi_name}]}},
                                            {"type": "CM", "query": {"nodeQuery": {"scopeId": scope_id,
                                                                                   "poIds": poids},
                                                                     "cmValueQueries": [
                                                                         {"stateType": "OPERATIONAL", "columnName": "operationalState"},
                                                                         {"stateType": "ADMINISTRATIVE", "columnName": "administrativeState"},
                                                                         {"stateType": "AVAILABILITY", "columnName": "availabilityStatus"}]}}],
                            "actions": [{"rowSortActionsList": [{"columnName": "nodeType", "sortDirection": "DESCENDING"},
                                                                {"columnName": "nodeName", "sortDirection": "DESCENDING"},
                                                                {"columnName": "moName", "sortDirection": "DESCENDING"}]}]}

    return nha_cell_tab_payload


def create_nha_node_tab_payload(scope_id, poids):
    """
    Creates a payload for the NHA node tab request
    :param scope_id: Network scope id
    :type scope_id: str
    :param poids: List of poids to be used in the request
    :type poids: list
    :return: payload body
    :rtype: dict
    """
    nha_node_tab_payload = {"tableType": {"nhaFeature": "NHA_NODE", "moTypes": ["ENodeBFunction"]}, "export": False,
                            "dataSources": [{"type": "CM", "query": {"nodeQuery": {"scopeId": scope_id,
                                                                                   "poIds": poids},
                                                                     "cmValueQueries": [{"stateType": "OPERATIONAL",
                                                                                         "columnName": "operationalState"},
                                                                                        {"stateType": "SYNCHRONIZED",
                                                                                         "columnName": "syncStatus"}]}},
                                            {"type": "FM", "query": {"nodeQuery": {"scopeId": poids,
                                                                                   "poIds": poids},
                                                                     "fmValueQueries": [{"severityLevel": "CRITICAL",
                                                                                         "columnName": "CRITICAL"},
                                                                                        {"severityLevel": "MAJOR",
                                                                                         "columnName": "MAJOR"},
                                                                                        {"severityLevel": "MINOR",
                                                                                         "columnName": "MINOR"},
                                                                                        {"severityLevel": "WARNING",
                                                                                         "columnName": "WARNING"},
                                                                                        {"severityLevel": "INDETERMINATE",
                                                                                         "columnName": "INDETERMINATE"},
                                                                                        {"severityLevel": "CLEARED",
                                                                                         "columnName": "CLEARED"}]}}],
                            "actions": [{"rowSortActionsList": [{"columnName": "nodeType", "sortDirection": "DESCENDING"},
                                                                {"columnName": "nodeName", "sortDirection": "DESCENDING"},
                                                                {"columnName": "moName", "sortDirection": "DESCENDING"}]}]}

    return nha_node_tab_payload


def create_widgets_taskset(widgets):
    """
    Create the widgets to be used in the UI flow
    :param widgets: Widgets on which to perform actions
    :type widgets: list

    """
    seconds = randint(1, 10)
    log.logger.debug("Widget create sleeping for {0}s".format(seconds))
    time.sleep(seconds)

    shuffle(widgets)
    for widget in widgets:
        widget.create()
        time.sleep(10)


@retry(retry_on_exception=lambda e: isinstance(e, TypeError), wait_fixed=1000, stop_max_attempt_number=5)
def nhm_widget_flows(widgets, number=None):
    """
    UI Flow to be used to run this profile
    :param widgets: Widgets on which to perform actions
    :type widgets: list
    :param number: Number of widgets to load
    :type number: int

    """
    number = number or len(widgets)
    widgets = sample(widgets, number)
    seconds = randint(1, 600)
    log.logger.debug("Widget flow sleeping for {0}s".format(seconds))
    time.sleep(seconds)
    user = widgets[0].user
    for widget in widgets:
        if isinstance(widget, NodesBreached):
            scope = str(time.time()).replace(".", "")
            nodes_breached_flow(widget, scope)
        elif isinstance(widget, NetworkOperationalState):
            scope = str(time.time()).replace(".", "")
            network_operational_state_flow(widget, scope)
        elif isinstance(widget, WorstPerforming):
            worst_performing_flow(widget)
        elif isinstance(widget, MostProblematic) and widget.polling_id:
            poll_alarm_widget(user=user, polling_id=widget.polling_id)
        elif isinstance(widget, CellStatus):
            cell_status_flow(widget)
        time.sleep(20)


@retry(retry_on_exception=lambda e: isinstance(e, TypeError), wait_fixed=1000, stop_max_attempt_number=5)
def call_widget_flow(widget):
    """
    Call to the UI Flow to be used to run this profile based on the widget type

    :param widget: widget whose flow to call
    :type widget: enmutils_int.lib.nhm_widget.NhmWidget

    """

    seconds = randint(1, 600)
    log.logger.debug("Widget flow sleeping for {0}s".format(seconds))
    time.sleep(seconds)
    user = widget.user

    if isinstance(widget, NodesBreached):
        scope = str(time.time()).replace(".", "")
        nodes_breached_flow(widget, scope)
    elif isinstance(widget, NetworkOperationalState):
        scope = str(time.time()).replace(".", "")
        network_operational_state_flow(widget, scope)
    elif isinstance(widget, WorstPerforming):
        worst_performing_flow(widget)
    elif isinstance(widget, MostProblematic) and widget.polling_id:
        poll_alarm_widget(user=user, polling_id=widget.polling_id)
    elif isinstance(widget, CellStatus):
        cell_status_flow(widget)
    time.sleep(20)


def get_nhm_kpi_home(user):
    """
    Visit the NHM kpi home page
    :param user: User
    :type user: enmutils.lib.enm_user_2.User instance

    """
    home_url = '/#kpimanagement'
    response = user.get(url=home_url, verify=False)
    if response.status_code != 200:
        response.raise_for_status()
    else:
        log.logger.debug("Successfully retrieved nhm kpi home")


def poll_alarm_widget(user, polling_id):
    """
    Poll the alarm widget to retrieve updated information on alarms
    :param user: User
    :type user: enmutils.lib.enm_user_2.User instance
    :param polling_id: The id of the alarm heartbeat subscription
    :type polling_id: str

    """
    log.logger.debug("Starting Poll Alarm Widget flow")
    user.post(url="/alarmcontroldisplayservice/alarmMonitoring/alarmoverviewdashboard/subscription/heartbeat/{polling_id}".format(polling_id=polling_id), verify=False)


def nodes_breached_flow(widget, random_scope_id):
    """
    Flow mimicking the UI load sent to the browser for Nodes Breached widget
    Navigation from Nodes Breached per KPI to Multi Node Health Monitor
    :param widget: Widget on which to perform the requests after navigation from main widget
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'
    :param random_scope_id: Widget network scope
    :type random_scope_id: str

    """
    log.logger.debug("Starting Nodes Breached flow")
    _nodes_breached_home(widget)
    _nodes_breached_node_view(widget, random_scope_id)
    log.logger.debug("Nodes Breached flow finished")


def _nodes_breached_home(widget):
    """
    Nodes breached rest requests loaded on NHM homepage
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'

    """
    nhm_landing_page_flow(widget.user)

    if widget.network_scope:
        widget.user.get(
            url="/oss/nhm/networkscope?scopeId={scope_id}".format(scope_id=widget.network_scope),
            headers=widget.headers_dict, verify=False)


def _nodes_breached_node_view(widget, random_scope_id):
    """
    Nodes breached rest requests
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'
    :param random_scope_id: Widget Network Scope
    :type random_scope_id: str

    """
    if widget.network_scope:
        network_scope_response = widget.user.post(
            "/oss/nhm/networkscope", data=json.dumps({"scopeId": widget.network_scope + "." + random_scope_id,
                                                      "poidList": [int(poid) for poid in widget.node_poids.values() if poid]}),
            headers=widget.headers_dict,
            verify=False)
        response = widget.get_kpis()
        if response:
            _nodes_breached_node_view_perform_main_request(response, widget, random_scope_id, network_scope_response)
        else:
            log.logger.debug("Failed to get kpi info")
    else:
        log.logger.debug("No network scope found for this widget")


def _nodes_breached_node_view_perform_main_request(kpis, widget, random_scope_id, network_scope_response):
    """
    Nodes breached rest requests
    :param kpis: Kpis of the widget
    :type kpis: list
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'
    :param random_scope_id: Widget Network Scope
    :type random_scope_id: str
    :param network_scope_response: response status of network scope request
    :type network_scope_response: int
    """
    log.logger.info("Starting the Nodes Breached Flow")
    kpis = [kpi for kpi in kpis.json() if kpi["numberOfNodes"] != "N/A"]
    if not kpis:
        log.logger.debug("None of the KPIs have breached the limit to view NHM")
    else:
        log.logger.debug(
            "The following KPIS have been breached: {0}".format(",".join([kpi["kpiName"] for kpi in kpis])))

    for kpi in kpis:
        kpi_type = "Nodes" if "ENodeBFunction" in kpi["measurementOn"] else "Cells"
        widget.user.post(
            url="#networkhealthanalysis?kpiName={kpi_name}&groupName={scope_id}.{random_scope}&type={kpi_type}&kpiUnit={kpi_unit}".format(
                kpi_name=kpi["kpiName"], scope_id=widget.network_scope, random_scope=random_scope_id,
                kpi_type=kpi_type, kpi_unit=kpi["kpiUnit"]), headers=widget.headers_dict, verify=False)
        if network_scope_response.status_code == 200:
            kpis_list = widget.get_kpi_names()
            log.logger.info("Requesting NHA table data for the :{}".format(widget.network_scope))
            widget.user.post(NHA_TABLE_URL, data=json.dumps(create_nha_node_tab_payload(widget.network_scope,
                                                                                        widget.node_poids)),
                             headers=widget.headers_dict, verify=False)
            log.logger.info("Sleeping for 10 secs before making request to NHA cell tab for :{0}".format(widget.network_scope))
            time.sleep(10)
            widget.user.post(NHA_TABLE_URL, data=json.dumps(create_nha_cell_tab_payload(widget.network_scope,
                                                                                        widget.node_poids,
                                                                                        kpis_list[0])),
                             headers=widget.headers_dict, verify=False)
        else:
            network_scope_response.raise_for_status()
        widget.user.get(
            url="/oss/nhm/networkscope/neTypes?scopeId={0}.{1}".format(widget.network_scope, random_scope_id),
            verify=False)


def network_operational_state_flow(widget, scope):
    """
    Flow mimicking the UI load sent to the browser for Operational State widget.
    Navigation from operational state widget to Multi Node Health Monitor
    :param widget: Widget on which to perform the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'
    :param scope: Widget network scope
    :type scope: str

    """

    log.logger.debug("Starting Network Operational State flow")
    nhm_landing_page_flow(widget.user)
    if widget.network_scope:
        response = widget.user.post(url="/network-status-rest-service/networkstatus/stateCount/{0}".format(widget.network_scope),
                                    data=json.dumps({"states": ["OPERATIONAL"]}),
                                    headers=widget.headers_dict, verify=False)
        if response.status_code == 200:
            ne_types = []
            operational_state = response.json()
            for state in operational_state:
                log.logger.debug("Monitoring {node_count} {ne_type} nodes".format(node_count=state["neCount"],
                                                                                  ne_type=state["neType"]))
                ne_types.append(state["neType"])
            if ne_types:
                widget.ne_type = choice(ne_types)
                _multi_node_health_monitor_page(widget)
        else:
            response.raise_for_status()
    else:
        log.logger.debug("No network scope found for this widget")


def nhm_landing_page_flow(user):
    """
    Flow mimicking the UI load sent to the browser for #networkhealthmonitor page
    :type user: enmutils.lib.enm_user_2.User instance

    """
    user.get(url="/#networkhealthmonitor", verify=False)
    user.get(url=NhmWidget.CURRENT_VIEW_URL, verify=False)


def worst_performing_flow(widget):
    """
    Flow mimicking the UI load sent to the browser for Worst Performing widget
    :param widget: Widget on which to perform the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'
    """
    log.logger.debug("Starting Worst Performing Widget Flow")
    response = _worst_performing_landing_page(widget)
    if response:
        log.logger.debug('response json {0}'.format(response.json()))
        if response.status_code == 200 and response.json():
            _worst_performing_node_page(widget, response)
        elif response.status_code == 200:
            old_kpi_name = widget.widget_kpi["name"]
            new_kpi_name = widget.get_kpi_with_results()
            log.logger.info("Worst Performing KPI widget returned no results. KPI used: {0}. New KPI to use: {1}. ".format(old_kpi_name, new_kpi_name))
        else:
            response.raise_for_status()


def _worst_performing_landing_page(widget):
    """
    Worst performing node rest requests loaded on NHM homepage
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'

    :return: response
    :rtype: Response object
    """
    kpi_name = None
    network_scope = None
    response = None
    if widget.widget_kpi:
        kpi_name = widget.widget_kpi["name"]
        network_scope = widget.network_scope

    if kpi_name and network_scope:
        if "Average_DRB_Latency" in kpi_name:
            response = widget.user.get(
                url="/oss/nhm/kpi/tenworstperformnode?groupname={scope_id}&kpi={kpi_name}&index=1".format(scope_id=network_scope,
                                                                                                          kpi_name=kpi_name),
                verify=False)
        else:
            response = widget.user.get(
                url="/oss/nhm/kpi/tenworstperformnode?groupname={scope_id}&kpi={kpi_name}".format(scope_id=network_scope,
                                                                                                  kpi_name=kpi_name),
                verify=False)
            if response.status_code != 200:
                response.raise_for_status()
    return response


def _worst_performing_node_page(widget, response):
    """
    Worst performing node rest request
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'
    :param response: json response
    :type response: json dict

    """
    node = choice(response.json())
    widget.poid = node.get('poID')
    _nodemonitor_poid(widget)
    _common_kpi_loading_endpoints(widget, node["poID"])
    widget.user.post(
        url="/network-status-rest-service/networkstatus/state/{scope_id}".format(scope_id=widget.network_scope),
        data=json.dumps({"states": ["OPERATIONAL"]}),
        headers=widget.headers_dict, verify=False)
    log.logger.debug("Worst Performing node page")


def cell_status_flow(widget):
    """
    Flow mimicking the UI load sent to the browser for Cell Status widget
    :param widget: Widget on which to perform the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'

    """
    log.logger.debug("Starting Cell Status flow")

    _network_status_landing_page(widget)
    _multi_node_health_monitor_page(widget)
    _cell_status_page(widget)


def _network_status_landing_page(widget):
    """
    Network status rest requests on NHM homepage
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'
    """
    nhm_landing_page_flow(user=widget.user)
    widget.user.post(url="/network-status-rest-service/networkstatus/stateCount/{0}".format(widget.network_scope),
                     data=json.dumps({"states": ["OPERATIONAL"]}), headers=widget.headers_dict, verify=False)


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)),
       wait_fixed=30000, stop_max_attempt_number=2)
def _multi_node_health_monitor_page(widget):
    """
    Node health monitor page rest requests
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'
    """
    if widget.network_scope:
        kpis_list = widget.get_kpi_names()
        log.logger.debug("Number of kpi's on the system {0}".format(len(kpis_list)))
        log.logger.info("Requesting NHA table data for the : {0}".format(widget.network_scope))
        widget.user.post(url=NETWORK_SCOPE_URL, data=json.dumps({"scopeId": widget.network_scope,
                                                                 "poidList": widget.poids}),
                         headers=widget.headers_dict)
        widget.user.post(NHA_TABLE_URL, data=json.dumps(create_nha_node_tab_payload(widget.network_scope,
                                                                                    widget.poids)),
                         headers=widget.headers_dict)
        log.logger.info("Sleeping for 20 secs before making request to NHA cell tab for : {0}".format(widget.network_scope))
        time.sleep(20)
        if kpis_list:
            widget.user.post(NHA_TABLE_URL, data=json.dumps(create_nha_cell_tab_payload(widget.network_scope,
                                                                                        widget.poids,
                                                                                        kpis_list[0])),
                             headers=widget.headers_dict)
        else:
            log.logger.debug("Unable to get the list of kpi's available on the system")
    else:
        log.logger.debug("No network scope found for this widget")


def _nodemonitor_poid(widget):
    """
    Targets the node monitor for the widget node poid
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'

    """
    response = widget.user.get(url="/#nodemonitor?poid={poid}".format(poid=widget.poid), verify=False)
    if response.status_code != 200:
        response.raise_for_status()


def _cell_status_page(widget):
    """
    Cell status page rest requests
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'

    """
    _nodemonitor_poid(widget)
    response = widget.user.get(url=NhmWidget.CURRENT_VIEW_URL, verify=False)
    if response.status_code != 200:
        response.raise_for_status()
    response = widget.user.post(url=KPI_ATTRIBUTES_URL, data=json.dumps(LOAD_KPI_PAYLOAD), headers=widget.headers_dict)
    if response.status_code != 200:
        response.raise_for_status()
    _common_kpi_loading_endpoints(widget, widget.poid)


def _common_kpi_loading_endpoints(widget, poid):
    """
    Some common endpoints hit to load kpi info in node views
    :param poid: object identifier
    :type poid: str
    :param widget: Widget from which to extract info to make the requests
    :type widget: 'enmutils_int.lib.nhm.NhmWidget'

    """
    if all([widget, poid, widget.widget_kpi]):
        if widget.widget_kpi.get('name'):
            LOAD_KPI_PAYLOAD['kpiNames'] = [widget.widget_kpi['name']]
            widget.user.post(url=KPI_ATTRIBUTES_URL, data=json.dumps(LOAD_KPI_PAYLOAD), headers=widget.headers_dict)
            widget.user.post("/oss/nhm/networkscope/nodemonitor",
                             data=json.dumps({"scopeId": widget.network_scope, "poId": int(poid)}),
                             headers=widget.headers_dict, verify=False)
            widget.user.get("/oss/nhm/kpi/cellstatus/{poid}?kpi={kpi_name}".format(poid=poid,
                                                                                   kpi_name=widget.widget_kpi["name"]),
                            headers=widget.headers_dict, verify=False)
        else:
            log.logger.debug("No KPI found to load the info into the widget: {0}".format(widget))
    else:
        log.logger.debug('WARNING: Wrong values found: widget: {0}, poid: {1}, widget.widget_kpi: {2}'.format(
            widget, poid, widget.widget_kpi))
