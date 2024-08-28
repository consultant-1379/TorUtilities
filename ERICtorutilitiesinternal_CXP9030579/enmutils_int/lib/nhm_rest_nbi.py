import json
from random import (randint, randrange, sample)

from requests import HTTPError, ConnectionError
from retrying import retry

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import JSON_SECURITY_REQUEST


KPI_ALL_REQUEST = "kpi-management/v1/kpis"
LAST_ROP_REQUEST = "enm/kpi-values/v1/{id}"
LAST_FOUR_ROP_REQUEST = "enm/kpi-values/v1/history/{id}"
NHM_REST_NBI_KPI_OPERATION = "kpi-management/v1/kpis/{id}"
NHM_REST_NBI_KPI_ACTIVATE = "kpi-management/v1/kpis/{id}/active"
NHM_REST_NBI_KPI_METRICS = "kpi-management/v1/metrics"
CREATED_BY_DEFAULT = "Ericsson"
KPI_PATTERN = "NHM REST NBI SETUP"
KPI_NAME = 'name'
KPI_ID = 'id'
SETUP_PROFILE = "NHM_REST_NBI_SETUP"

KPI_BODY = {
    "name": "",
    "unit": "",
    "neNames": [],
    "neFormulaList": {
        "RadioNode": {
            "reportingObjList": {
                "ENodeBFunction": {
                    "formula": ""
                }
            }
        }
    }
}

SET_ACTIVATION = {
    "active": True
}


class NhmRestNbiKpi(object):

    def __init__(self, user=None, kpi_id=None, kpi_name=None, nodes=None, **kwargs):
        """
        NHM KPI Constructor
        :param user: user to make requests
        :type user: enmutils.lib.enm_user_2.User
        :param kpi_id: string representing the id of the created kpi
        :type kpi_id: str
        :param kpi_name: string representing the name of the KPI
        :type kpi_name: str
        :param nodes: list of nodes to be used with the KPI
        :type nodes: list
        :type kwargs: dict
        :param kwargs: __builtin__ dictionary
        """
        self.user = user
        self.kpi_id = kpi_id
        self.kpi_name = kpi_name
        if nodes:
            self.node_ids = [node.node_id for node in nodes]
        self.counters = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr', 'pmLicConnectedUsersLicense',
                         'pmRrcConnBrEnbMax', 'pmMoFootprintMax', 'pmLicConnectedUsersMax', 'pmPagS1EdrxReceived']
        self.operators = kwargs.get('operators') if kwargs.get('operators') else ['+', '-', '*', '/']
        self.headers_dict = JSON_SECURITY_REQUEST
        self.created_by = kwargs.get('created_by')
        if user and not self.created_by:
            self.created_by = self.user.username

    @classmethod
    def remove_kpis_by_pattern(cls, user):
        response = user.get(KPI_ALL_REQUEST, headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            response.raise_for_status()
        all_kpis = response.json().get('items')
        node_level_kpis = [kpi for kpi in all_kpis if KPI_PATTERN in kpi[KPI_NAME]]
        for kpi in node_level_kpis:
            kpi_object = cls(kpi_id=kpi[KPI_ID], kpi_name=kpi[KPI_NAME], user=user)
            try:
                kpi_object.deactivate()
            except Exception as e:
                log.logger.debug(
                    "Exception raised while trying to deactivate KPI with name {0}: {1}".format(kpi[KPI_NAME],
                                                                                                str(e)))
            try:
                kpi_object.delete()
            except Exception as e:
                log.logger.debug(
                    "Exception raised while trying to delete KPI with name {0}: {1}".format(kpi[KPI_NAME], str(e)))
            log.logger.debug("KPI name: {0} deactivated and deleted".format(kpi[KPI_NAME]))

    @classmethod
    def remove_kpis_nhm_rest_nbi_05_by_pattern(cls, user):
        response = user.get(KPI_ALL_REQUEST, headers=JSON_SECURITY_REQUEST)
        if response.status_code != 200:
            response.raise_for_status()
        all_kpis = response.json().get('items')
        node_level_kpis = [kpi for kpi in all_kpis if 'NHM REST NBI 05' in kpi[KPI_NAME]]
        for kpi in node_level_kpis:
            kpi_object = cls(kpi_id=kpi[KPI_ID], kpi_name=kpi[KPI_NAME], user=user)
            try:
                kpi_object.deactivate()
            except Exception as e:
                log.logger.debug(
                    "Exception raised while trying to deactivate KPI with name {0}: {1}".format(kpi[KPI_NAME],
                                                                                                str(e)))
            try:
                kpi_object.delete()
            except Exception as e:
                log.logger.debug(
                    "Exception raised while trying to delete KPI with name {0}: {1}".format(kpi[KPI_NAME], str(e)))
            log.logger.debug("KPI name: {0} deactivated and deleted".format(kpi[KPI_NAME]))

    def _create_kpi_equation(self):
        for _ in xrange(randint(1, 4)):
            counters = [counter for counter in sample(self.counters, randint(2, len(self.counters)))]
        operator = self.operators[randrange(0, len(self.operators))]
        if operator == "/" and len(counters) > 2:
            counters = sample(counters, 2)
        equation = operator.join(counters)
        return equation

    def _create_node_level_body(self):
        """
        Returns the body used to create a node level KPI for all node types in KPI
        :return: KPI node level body values
        :rtype: json dictionary
        """
        log.logger.debug('Creating Node Level KPI body')
        kpi_body = KPI_BODY
        kpi_body["name"] = self.kpi_name
        kpi_body["unit"] = "No. of occurrences"
        kpi_body["neNames"] = self.node_ids
        kpi_body["neFormulaList"]["RadioNode"]["reportingObjList"]["ENodeBFunction"][
            "formula"] = self._create_kpi_equation()
        return kpi_body

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=30000, stop_max_attempt_number=3)
    def create(self):
        kpi_body = self._create_node_level_body()
        response = self.user.post(url=KPI_ALL_REQUEST, data=json.dumps(kpi_body),
                                  headers=self.headers_dict)
        if response.status_code != 201:
            response.raise_for_status()
        self.kpi_id = response.json()['id']
        log.logger.debug("KPI : '{0}' was successfully created id is : {1}".format(self.kpi_name, self.kpi_id))

    def activate(self):
        """
        Activates a NHM REST NBI KPI
        """

        self._set_activation(True)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=30000, stop_max_attempt_number=3)
    def deactivate(self):
        """
        Deactivates a NHM KPI
        """

        self._set_activation(False)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=30000, stop_max_attempt_number=3)
    def delete(self):
        """
        Deletes a NHM REST NBI KPI
        """

        if self.created_by != CREATED_BY_DEFAULT:
            response = self.user.delete_request(url=NHM_REST_NBI_KPI_OPERATION.format(id=self.kpi_id))
            if response.status_code != 200:
                log.logger.debug('Failed try delete KPI. Retry: {0}'.format(self.kpi_name))
                response.raise_for_status()
            log.logger.debug("KPI '{0}' was successfully deleted".format(self.kpi_name))
        else:
            log.logger.info("KPI profile created by default, it can't be deleted")

    @retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=30000,
           stop_max_attempt_number=3)
    def _set_activation(self, status):
        SET_ACTIVATION["active"] = status
        response = self.user.put(url=NHM_REST_NBI_KPI_ACTIVATE.format(id=self.kpi_id),
                                 data=json.dumps(SET_ACTIVATION),
                                 headers=self.headers_dict)
        if response.status_code != 200:
            log.logger.debug('Failed to deactivate KPI to {0}. Retry: {1}'.format(status, self.kpi_name))
            response.raise_for_status()
        log.logger.debug("Activation status of KPI {0} was set to {1}".format(self.kpi_name, status))

    def activation_status(self, user, random_kpi):
        """

        This method is to execute the Rest request as part nhm nbi 08 profile flow.
        :param user: username to send the rest call.
        :type user: list
        :param random_kpi : kpi id used in the rest call.
        :type random_kpi : list
        :raises EnmApplicationError: if there is error in response from ENM
        """
        try:
            for value in random_kpi:
                response = user.get(NHM_REST_NBI_KPI_ACTIVATE.format(id=value), headers=JSON_SECURITY_REQUEST)
                if response.status_code != 200:
                    raise EnmApplicationError("Unexpected response received {0}".format(response.json()))
                log.logger.debug("Response : {0}".format(response.json()))
        except Exception as e:
            log.logger.debug("Exception is : {0}".format(e))
