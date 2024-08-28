import random
import json
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib.nhm_rest_nbi import KPI_ALL_REQUEST
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.nhm import sleep_until_profile_persisted, wait_for_nhm_setup_profile


class NhmRestNbiFlow(GenericFlow):

    def nhm_node_level_kpi(self, all_kpis):
        """
        :param all_kpis: list of all KPI's
        :type all_kpis : list
        :return: list of random 10 kpi id's
        :rtype: list
        :raises EnmApplicationError: No Node level kpi's available
        """
        node_level_kpis = [kpi for kpi in all_kpis if 'NHM SETUP' in kpi['name'] and kpi['active']
                           is True and 'ENodeBFunction' in kpi['reportingObject']]
        if len(node_level_kpis) < 10:
            raise EnmApplicationError("Node level KPIs available for this iteration are less than 10.")
        random_kpi = random.sample(node_level_kpis, 10)
        log.logger.debug('Random KPI picked for use case are {0}'.format(random_kpi))
        return random_kpi

    def nhm_rest_nbi_node_level_kpi(self, all_kpis):
        """
        Filtering all kpi data having kpi name is

       :param all_kpis: all_kpis filter kpis created by nhm rest nbi setup
       :type all_kpis: list of dictionary of kpis and id
       :return: list of 5 kpis
       :rtype: list
        """
        node_level_kpis = [kpi for kpi in all_kpis if 'NHM REST NBI SETUP' in kpi['name']]
        log.logger.debug("Node level kpi created by nhm rest nbi setup {0}".format(node_level_kpis))
        return node_level_kpis

    def nhm_rest_pre_defined_kpi(self, all_kpis):
        """
        Filtering all kpi data not having NHM in kpi name

       :param all_kpis: all_kpis filter kpis created by nhm rest nbi setup
       :type all_kpis: list of dictionary of kpis and id
       :return: list of kpis
       :rtype: list
        """
        pre_defined_kpis = [kpi for kpi in all_kpis if kpi['createdBy'] == 'Ericsson' and 'RadioNode' in kpi['neTypes'] and kpi['active'] is False][0:10]
        log.logger.debug("Pre defined kpi created are {0}".format(pre_defined_kpis))
        return pre_defined_kpis

    def fdn_format(self, nodes_verified_on_enm):
        """
        :params nodes_verified_on_enm: The List of node with correct POIDs to use for NHM
        :type nodes_verified_on_enm: list
        :return payload_value: Dictionary of request payload data
        :rtype payload_value: Dict
        """
        user_data = []
        for nodes in nodes_verified_on_enm:
            user_data.append(nodes.node_id)
        payload_value = {"neNames": user_data}
        log.logger.debug('payload for the post request {0}'.format(user_data))
        return payload_value

    def kpi_execution(self, user, node_level_kpi, fdn_values, rest_url):
        """
        :params user: user to make requests
        :type user: enm_user.User object
        :params node_level_kpi: the list of node_level_kpi
        :type node_level_kpi: list
        :params all_kpi: dictionary of all kpi and id
        :type all_kpi: dict
        :params fdn_values: dictionary of request payload data
        :type fdn_values: dict
        :params rest_url: end point of rest api
        :type rest_url: str
        """
        for kpi in node_level_kpi:
            log.logger.debug("KPI Name:{0}, Id: {1}, Reporting object: {2}".format(kpi['name'], kpi['id'], kpi['reportingObject']))
            response = user.post(rest_url.format(id=kpi['id']), data=json.dumps(fdn_values),
                                 headers=JSON_SECURITY_REQUEST)
            if not response.ok:
                raise EnvironError('Unable to fetch the values for the post request  response :{0}'.format
                                   (response.json()))

    def kpi_execution_nhm_rest_nbi(self, user, node_level_kpi, fdn_values, kpi_value):
        """
         Execute the rest call 5 times by taking five different kpi id

        :params user: user to make requests
        :type user: enm_user.User object
        :params node_level_kpi: the list of node_level_kpi
        :type node_level_kpi: list
        :params fdn_values: dictionary of request payload data
        :type fdn_values: dict
        :params kpi_value: end point of rest api
        :type kpi_value: str
        """
        for kpis in node_level_kpi:
            log.logger.debug("kpi name {0} and the kpi id {1}".format(kpis['name'], kpis['id']))
            response = user.post(kpi_value.format(id=kpis['id']), data=json.dumps(fdn_values),
                                 headers=JSON_SECURITY_REQUEST)
            log.logger.debug('request url {0}'.format(kpi_value.format(id=kpis['id'])))
            if not response.ok:
                raise EnvironError('Unable to fetch the values for the post request,  response :{0}'.format
                                   (response.json()))

    def kpi_execution_nhm_rest_pre_defined(self, user, fdn_values, pre_defined_kpis, kpi_value):
        """
        Execute the rest call 10 times by taking ten different kpi id

        :param user: enm_user.User object
        :type user: list
        :param fdn_values: dictionary of request payload data
        :type fdn_values: dict
        :param pre_defined_kpis: pre-defined kpi's
        :type pre_defined_kpis: list
        :param kpi_value: end point of rest api
        :type kpi_value: str
        :raises EnvironError: Unable to fetch the values for the post request
        """
        for kpis in pre_defined_kpis:
            log.logger.debug("kpi name {0} and the kpi id {1}".format(kpis['name'], kpis['id']))
            response = user.put(kpi_value.format(id=kpis['id']), data=json.dumps(fdn_values),
                                headers=JSON_SECURITY_REQUEST)
            log.logger.debug('request url {0}'.format(kpi_value.format(id=kpis['id'])))
            if not response.ok:
                raise EnvironError('Unable to fetch the values for the post request,  response :{0}'.format
                                   (response.json()))

    def setup_nhm_profile(self):
        """
        Setup the NHM profile. Wait for the SETUP_PROFILE to complete, create users, and get nodes for NHM use.
        :return operator_users: operator_users of the profile
        :rtype operator_users: list
        :return nodes_verified_on_enm: list of nodes with correct POIDs to use for NHM
        :rtype nodes_verified_on_enm: list
        """
        if self.NAME not in ['NHM_REST_NBI_03', 'NHM_REST_NBI_04']:
            setup_profile = "NHM_REST_NBI_SETUP"
        else:
            setup_profile = "NHM_SETUP"
        sleep_until_profile_persisted(setup_profile)
        wait_for_nhm_setup_profile(setup_profile)
        operator_users = self.create_users(self.NUM_OPERATORS, self.OPERATOR_ROLE, fail_fast=False, safe_request=True,
                                           retry=True)
        nodes_verified_on_enm = self.get_allocated_nodes(setup_profile)
        if len(nodes_verified_on_enm) > self.TOTAL_NODES:
            nodes_verified_on_enm = nodes_verified_on_enm[:self.TOTAL_NODES]
        return operator_users, nodes_verified_on_enm

    def get_list_all_kpis(self, user):
        """
         Execute the rest call for all the kpis object
        :param user: user
        :type user: enm_user.User object
        :return: list of all the kpis object
        :rtype: List
        :raises EnmApplicationError: No Node level kpi's available
        """
        response = user.get(KPI_ALL_REQUEST, headers=JSON_SECURITY_REQUEST)
        if response.status_code == 200:
            return response.json().get("items")
        else:
            raise EnmApplicationError("No kpi's available for this iteration")
