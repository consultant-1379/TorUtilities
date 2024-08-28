import time
import random
from itertools import cycle
from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.thread_queue import ThreadQueue
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import nhm_ui
from enmutils_int.lib.nhm import NhmKpi
from enmutils_int.lib.nhm_widget import (NodesBreached, WorstPerforming, MostProblematic, NetworkOperationalState,
                                         NetworkSyncStatus)
from enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile import NhmFlowProfile


class NhmConcurrentUsersFlow(NhmFlowProfile):

    @staticmethod
    def get_widget_iterator(widgets):
        """
        Returns iterator for widgets

        :param widgets: list of widget names
        :type widgets: list

        :return: A widget iterator
        :rtype: itertools.cycle
        """

        random.shuffle(widgets)
        return cycle(widgets)

    @staticmethod
    def create_widget_to_add_to_widget_list(widget_type, user, nodes, available_kpis):
        """
        Construct the widget to be added to the list of widgets used in the profile

        :param widget_type: name of the type of widget to create
        :type widget_type: str
        :param user: user to create the widgets
        :type user: enmutils.lib.enm_user_2.User object
        :param nodes: list of nodes to be used to create the widgets
        :type nodes: list
        :param available_kpis: names of the available KPIs
        :type available_kpis: list
        :return: widget created
        :rtype: enmutils_int.lib.nhm.NhmWidget object
        """

        if widget_type == "NodesBreached":
            widget = NodesBreached(user=user, nodes=nodes, number_of_kpis=1)
            log.logger.debug("Created a NodesBreached widget")
        elif widget_type == "WorstPerforming":
            selected_kpi = random.choice(available_kpis)
            widget = WorstPerforming(user=user, nodes=nodes, kpi_name=selected_kpi[0])
            log.logger.debug("Created a WorstPerforming widget with kpi: {0}".format(selected_kpi[0]))
        elif widget_type == "MostProblematic":
            widget = MostProblematic(user=user, nodes=nodes)
            log.logger.debug("Created a MostProblematic widget")
        elif widget_type == "NetworkOperationalState":
            widget = NetworkOperationalState(user=user, nodes=nodes)
            log.logger.debug("Created a NetworkOperationalState widget")
        else:
            widget = NetworkSyncStatus(user=user, nodes=nodes)
            log.logger.debug("Created a NetworkSyncStatus widget")

        return widget

    def init_widgets(self, users, nodes, widgets_to_use):
        """
        Creates the list of widgets to be used in the profile flow

        :param widgets_to_use: list of widget names to be created
        :type widgets_to_use: list
        :param users: users to create the widgets
        :type users: list
        :param nodes: list of nodes to be used to create the widgets
        :type nodes: list

        :raises EnvironError: enmutils.lib.exceptions.EnvironError
        :return: list of lists of created widgets
        :rtype: list
        """

        widgets = []
        num_exceptions = 0
        widget_iterator = self.get_widget_iterator(widgets_to_use)

        while not widgets:
            try:
                for user in users:
                    widget_type = widget_iterator.next()
                    available_kpis = NhmKpi.get_all_kpi_names_active(user, exclude="NHM_03")
                    if available_kpis:
                        widget = self.create_widget_to_add_to_widget_list(widget_type, user, nodes, available_kpis)
                        widgets.append(widget)
                    else:
                        raise EnvironError("No available active KPIs for the widget")
            except Exception as e:
                num_exceptions += 1
                if num_exceptions < 5 or num_exceptions % 20 == 0:
                    self.add_error_as_exception(e)
                log.logger.debug("Profile could not create widgets, retrying in 5 minutes")
                time.sleep(60 * 5)

        for widget in widgets:
            self.teardown_list.append(picklable_boundmethod(widget.teardown))
        return widgets

    def execute_profile_flow(self):
        """
        Execute the flow of the NHM profile

        """
        operator_users, nodes_verified_on_enm = self.setup_nhm_profile()
        widgets = self.init_widgets(operator_users, nodes_verified_on_enm, widgets_to_use=self.WIDGETS)
        self.create_and_configure_widgets(widgets)

        self.state = "RUNNING"
        while self.keep_running():
            tq = ThreadQueue(widgets, num_workers=len(widgets), func_ref=nhm_ui.call_widget_flow)
            tq.execute()
            num_exceptions = self.process_thread_queue_errors(tq, last_error_only=True)
            log.logger.debug("{0} has encountered {1} thread queue exceptions. Please see log errors for more details"
                             .format(self.NAME, num_exceptions))
            self.sleep()
