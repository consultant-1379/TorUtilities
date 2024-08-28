import json
import random
import string
import time

from requests.exceptions import HTTPError, ConnectionError
from retrying import retry

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.headers import JSON_SECURITY_REQUEST as HEADERS
from enmutils_int.lib.parameter_management import perform_netex_search, get_fdns_from_poids
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class ParMgt03Flow(GenericFlow):
    IMPORT_FILE_URL = "/parametermanagement/v1/importFile"
    SEARCH_QUERIES = ["select GeranFreqGroupRelation with attr userLabel filter by radioAccessTechnology contains 4G",
                      "select EUtranFrequency with attr userLabel filter by radioAccessTechnology contains 5G"]
    MO_TYPES = ["GeranFreqGroupRelation", "EUtranFrequency"]
    PARAMETERS = ["userLabel", "userLabel"]
    PARAMETER_VALUE = ""

    def execute_flow(self):
        self.state = "RUNNING"
        user = self.create_profile_users(1, self.USER_ROLES)[0]
        while self.keep_running():
            self.sleep_until_day()
            self.PARAMETER_VALUE = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            fdns_per_mo_type = {}
            mo_type_query_parameters = dict(zip(self.MO_TYPES, zip(self.SEARCH_QUERIES, self.PARAMETERS)))
            max_number_of_mos = self.NUMBER_OF_MOS
            log.logger.debug("Profile attempts to generate import file with {0} attribute updates for each "
                             "type of MO - {1} based on number of search results. But the actual number of "
                             "attributes imported can be lesser than expected if there are less number of "
                             "results depending on the deployment.".format(max_number_of_mos, self.MO_TYPES))
            for (mo_type, (search_query, parameter)) in mo_type_query_parameters.items():
                try:
                    search = perform_netex_search(user, search_query)
                    fdns_per_mo_type[mo_type] = get_fdns_from_poids(
                        user, search.result, mo_type, parameter)[:max_number_of_mos]
                    time.sleep(10)
                except Exception as e:
                    self.add_error_as_exception(EnvironError("Netex search query failed request failed. Msg: {}. "
                                                             "Profile will not create the import file".format(e)))
                else:
                    try:
                        log.logger.debug("Attempting to create import file for MO type - {0}".format(mo_type))
                        response = self.import_file_request(user, fdns_per_mo_type[mo_type][:max_number_of_mos],
                                                            parameter, self.PARAMETER_VALUE)
                        self.verify_import_file(parameter, self.PARAMETER_VALUE, response,
                                                fdns_per_mo_type[mo_type][:max_number_of_mos])
                    except Exception as e:
                        self.add_error_as_exception(
                            EnvironError("Create Import File request failed. Msg: {}".format(e)))

    @retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=60000,
           stop_max_attempt_number=3)
    def import_file_request(self, user, fdns, attribute, value):
        """
        Function to request the import file
        :param user: User to perform the request
        :type user: enm_user_2.User object
        :param fdns: List of fdns
        :type fdns: list
        :param attribute: Attribute to change
        :type attribute: str
        :param value: Value to change for the attribute
        :type value: str
        :return: import file response
        :rtype: response
        """
        payload = {"fileType": "THREE_GPP", "importFileName": None, "operations": []}
        for fdn in fdns:
            payload["operations"].append({"fdn": fdn, "changeType": "UPDATE", "attributes": {attribute: value}})

        log.logger.info("Performing {} attribute updates.".format(len(payload["operations"])))

        response = user.post(self.IMPORT_FILE_URL, data=json.dumps(payload), headers=HEADERS)
        if response.status_code != 200:
            response.raise_for_status()
        return response

    def verify_import_file(self, parameter, value, import_file, fdns):
        """
        Function to verify contents of the import file. It will iterate through the response text and confirm that
        number of parameter changes is same as the number of fdns in the request
        :param parameter: Name of the parameter which was changed
        :type parameter: str
        :param value: New value of the parameter
        :type value: str
        :param import_file: Response form the import file request
        :type import_file: response
        :param fdns: Fdns list used
        :type fdns: list
        """
        search_phrase = "{}>{}".format(parameter, value)
        number_of_parameters_updated = 0
        if import_file.text:
            for line in import_file.text.splitlines():
                if search_phrase in line:
                    number_of_parameters_updated += 1

            if number_of_parameters_updated == len(fdns):
                log.logger.info("Import file successfully created with {} parameter changes."
                                .format(number_of_parameters_updated))
            else:
                log.logger.error("Import file created with {0} parameters changed. {1} parameter changes expected!"
                                 .format(number_of_parameters_updated, len(fdns)))
        else:
            self.add_error_as_exception(EnvironError("Import file request returned no file body."))
