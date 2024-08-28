import random
import time

from enmscripting.exceptions import TimeoutException
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.nhm import NhmKpi
from enmutils_int.lib.nhm_ui import get_nhm_kpi_home
from enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile import NhmFlowProfile
from requests.exceptions import HTTPError


class Nhm03(NhmFlowProfile):
    """
    Class to run the flow for NHM_03 profile
    """

    def _set_kpi(self, counters, admin_user, index_admin_user, nodes, ne_types):
        """
        Set the KPI values

        :param counters: A list of counters to use in the kpi
        :type counters: list
        :param admin_user: A administrator user
        :type admin_user: enmutils.lib.enm_user_2.User
        :param index_admin_user: index of the administrator user
        :type index_admin_user: int
        :param nodes: List of nodes
        :type nodes: list
        :param ne_types: List of node types
        :type ne_types: list

        :return: A kpi instance
        :rtype: enmutils_int.lib.nhm.NhmKpi
        """

        kpi = NhmKpi(name="{0}_KPI_{1}".format(self.identifier, index_admin_user),
                     reporting_objects=self.REPORTING_OBJECT, active=False,
                     nodes=nodes, node_types=ne_types, user=admin_user,
                     counters=random.sample(counters, random.randint(2, len(counters))))
        self.teardown_list.append(kpi)
        log.logger.debug("Process to set KPI initial values")
        return kpi

    def _create_update_activate_kpi(self, kpi, nodes):
        """
        Creates, updates and finally activates a KPI

        :param kpi: kpi to run CRUD operations
        :type kpi: enmutils_int.lib.nhm.NhmKpi
        :param nodes: list of nodes
        :type nodes: list
        """
        try:
            node_poids = [node.poid for node in nodes if node.poid]
            kpi.create()
            time.sleep(4)
            kpi.update(threshold_domain="GREATER_THAN", threshold_value=random.randint(1, 100))
            time.sleep(2)
            kpi.update(remove_nodes=node_poids)
            time.sleep(2)
            kpi.update(add_nodes=node_poids)
            time.sleep(2)
            kpi.update(replace_formula=True)
            time.sleep(2)
            kpi.activate()
        except Exception as e:
            self.add_error_as_exception(e)
        log.logger.debug("{0} KPI have been created, updated and activated".format(kpi))

    def _deactivate_delete_kpis(self, kpis):
        """
        Deactivates and deletes KPIs

        :param kpis: List of KPIs to deactivate and delete
        :type kpis: list
        """
        try:
            for kpi in kpis:
                kpi.deactivate()
                time.sleep(2)
                kpi.delete()
                self.teardown_list.remove(kpi)
        except Exception as e:
            self.add_error_as_exception(e)

    def _get_counters(self, ne_types, reporting_objects):
        """
        Returns the valid counters based on the node types and reporting object

        :param ne_types: Node types
        :type ne_types: list
        :param reporting_objects: list of reporting objects to create the KPI
        :type reporting_objects: list

        :return: List of counters
        :rtype: list
        """

        counters = []
        try:
            for ne_type in ne_types:
                for reporting_object in reporting_objects:
                    for counter in NhmKpi.get_counters_specified_by_nhm(reporting_object, ne_type):
                        counters.append(counter)
            log.logger.debug("List of counter: {0}".format(counters))
        except Exception as e:
            self.add_error_as_exception(e)
        return list(set(counters))

    def _clean_kpi_system(self, profile, user):
        """
        It removes all KPIs found created by previous runs of NHM_03 profile
        """
        try:
            NhmKpi.remove_kpis_by_pattern_new(user=user, pattern="NHM_03")
        except (HTTPError, TimeoutException, ValueError) as e:
            profile.add_error_as_exception(e)

    def _get_kpi_names(self, admin_user):
        """
        Return the names of all KPIs

        :param admin_user: Administrator user to run query
        :type admin_user: enmutils.lib.enm_user_2.User

        :return: List of kpi names
        :rtype: list

        """
        kpi_names = []
        try:
            kpi_names = [kpi_name for kpi_name in NhmKpi.get_all_kpi_names(admin_user)]
        except Exception as e:
            self.add_error_as_exception(e)
        return kpi_names

    def execute_flow(self):
        """
        Executes the flow of NHM_03 profile

        """
        operator_users, nodes_verified_on_enm = self.setup_nhm_profile()
        admin_users = self.create_users(self.NUM_ADMINS, self.ADMIN_ROLE, fail_fast=False, safe_request=True, retry=True)
        self._clean_kpi_system(self, admin_users[0])
        ne_types = list(set(node.primary_type for node in nodes_verified_on_enm))
        counters = self._get_counters(ne_types, self.REPORTING_OBJECT)
        self.state = "RUNNING"

        while self.keep_running():
            self.sleep_until_time()
            kpis = []

            for admin_user in admin_users:
                kpi = self._set_kpi(counters, admin_user, admin_users.index(admin_user), nodes_verified_on_enm,
                                    ne_types)
                kpis.append(kpi)
                self._create_update_activate_kpi(kpi, nodes_verified_on_enm)

            kpi_names = self._get_kpi_names(admin_users[0])
            if kpi_names:
                self.create_and_execute_threads(operator_users, thread_count=len(operator_users),
                                                args=[kpi_names, self])

            self._deactivate_delete_kpis(kpis)

    @staticmethod
    def task_set(operator_user, kpi_names, profile):  # pylint: disable=arguments-differ
        """
        UI Flow to be used to run this profile

        :param user: user instance to be used to perform the flow
        :type user: enmutils.lib.enm_user_2.User
        :param kpi_names: names of the KPIs to get
        :type kpi_names: list
        :param profile: profile object used for function calls
        :type profile: `lib.profile.Profile`
        """
        try:
            time.sleep(random.randint(1, 300))
            get_nhm_kpi_home(user=operator_user)
            kpi_index = random.randint(0, len(kpi_names) - 1)
            NhmKpi.get_kpi_info(user=operator_user, name=kpi_names[kpi_index][0])
        except Exception as e:
            profile.add_error_as_exception(EnmApplicationError(e))
