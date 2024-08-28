# ***************************************************************************************************************
# Name    : Federated identity management (FDIM)
# Summary : Module for perform the federated identity management operations.
#            1. Import the federated identity synchronization advanced settings configuration.
#            2. Set the period of the federated identity synchronization.
#            3. Set the administrative state (enabled/disabled) of the federated identity synchronization.
#            4. Trigger the federated identity synchronization forced sync to forcefully execute synchronization.
#            5. Retrieve the federated identity last synchronization report.
#            6. Get period of federated identity synchronization.
#            7. Retrieve the state of the Federated Identity Synchronization
#            8. Trigger the federated identity synchronization forced delete to remove all federated users from
#               Local server.
#            9. Trigger the federated identity synchronization restore to defaults.
#            10. Waits and checks for force sync federated identity synchronization.
#            11. Waits and checks for force delete federated identity synchronization.
# ***************************************************************************************************************


import datetime
import json
import time

from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils.lib import log
from enmutils.lib.exceptions import TimeOutError, EnmApplicationError


class FIDM_interface(object):

    IMPORT_FEDERATED_IDENTITY_SYNCHRONIZATION = "/oss/fidm/sync/import"
    FEDERATED_IDENTITY_SYNCHRONIZATION_PERIOD = "/oss/fidm/sync/period"
    FEDERATED_IDENTITY_SYNCHRONIZATION_STATE = "/oss/fidm/sync/state"
    FEDERATED_IDENTITY_SYNCHRONIZATION_FORCED_SYNC = "/oss/fidm/sync/forced"
    FEDERATED_IDENTITY_SYNCHRONIZATION_FORCED_DELETE = "/oss/fidm/sync/delete"
    FEDERATED_IDENTITY_SYNCHRONIZATION_RESTORE_TO_DEFAULT = "/oss/fidm/sync/restore"
    FEDERATED_IDENTITY_SYNC_REPORT = "/oss/fidm/sync/report"
    SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS = 15

    def import_federated_identity_synchronization(self, user):
        """
        import the Federated Identity Synchronization Advanced Settings configuration.
        :type user: enm_user_2.User
        :param user: User instance

        :return: returns import the Federated Identity Synchronization status.
        :rtype: dict
        :raises HttpError: if response status is not ok
        :raises EnmApplicationError: if getting empty response
        """
        payload = {"name": "Opendj RV-local Endurance", "searchPageSize": 999,
                   "searchRequests": [
                       {"relativeBaseDn": "ou=acmeUsersIntranet,ou=acmeEndurance,ou=pdu nam", "scope": "sub",
                        "filter": "(&(objectClass=*)(acmeapplicationaut={network_type}@ACME*))".format(
                            network_type=self.NETWORK_TYPE),
                        "attributes": {"uid": {"valueRegex": "^([^\b]+)$", "valueMatchingGroups": {"username": [1]}},
                                       "acmeapplicationaut": {"valueRegex": "{network_type}@([^:]+)(?::(.+))?".format(
                                           network_type=self.NETWORK_TYPE), "valueMatchingGroups": {"role": [1],
                                                                                                    "tg": [2]}},
                                       "dn": {"valueRegex": "^(.+)$", "valueMatchingGroups": {"userDn": [1]}}}}],
                   "roleMapping": {"roleMappingType": "none", "roleFormat": None, "rolesMap": None}}
        log.logger.debug("Attempting to import federated identity synchronization")
        log.logger.debug("Import the federated identity Synchronization payload: {0}".format(payload))
        response = user.post(self.IMPORT_FEDERATED_IDENTITY_SYNCHRONIZATION, data=json.dumps(payload),
                             headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        json_response = response.json()
        log.logger.debug("Response of import the federated identity Synchronization: {0}".format(json_response))
        if not json_response:
            raise EnmApplicationError("Failed to import the Federated Identity Synchronization")
        log.logger.debug("Successfully imported federated identity synchronization : {0}".format(json_response))
        return json_response

    def set_federated_identity_synchronization_period(self, user):
        """
        Set the period of the Federated Identity Synchronization.
        The period is expressed in terms of interval duration (in hours) of periodic synchronization timer.
        It is possible to specify also the initial expiration time as a string whose format is "HH:mm"

        :type user: enm_user_2.User
        :param user: User instance

        :return: returns status of set period of the Federated Identity Synchronization.
        :rtype: dict

        :raises HttpError: if response status is not ok
        :raises EnmApplicationError: if getting empty response
        """
        log.logger.debug("Attempting to set period of the federated identity synchronization")
        payload = {"intervalDurationInHours": self.INTERVAL_DURATION, "initialExpiration": self.INITIAL_EXPIRATION}
        log.logger.debug("Set period of the federated identity synchronization payload: {0}".format(payload))
        response = user.put(self.FEDERATED_IDENTITY_SYNCHRONIZATION_PERIOD, data=json.dumps(payload),
                            headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        json_response = response.json()
        log.logger.debug("Response of set the period of the federated identity "
                         "synchronization: {0}".format(json_response))
        if not json_response:
            raise EnmApplicationError("Failed to set the period of the federated identity synchronization")
        log.logger.debug("Successfully set the period of the federated identity "
                         "synchronization: {0}".format(json_response))
        return json_response

    def set_federated_identity_synchronization_admin_state(self, user, admin_state):
        """
        Set the administrative state of the Federated Identity Synchronization.

        :type admin_state: str
        :param admin_state: administrative state of the synchronization. "enabled", "disabled"
        :type user: enm_user_2.User
        :param user: User instance

        :return: returns administrative state of the synchronization.
        :rtype: dict

        :raises HttpError: if response status is not ok
        :raises EnmApplicationError: if getting empty response
        """
        payload = {"adminState": admin_state}
        log.logger.debug("Attempting to {0} federated identity synchronization".format(admin_state.rstrip("d")))
        log.logger.debug("{0} federated identity synchronization payload: {1}".format(admin_state.rstrip("d"),
                                                                                      payload))
        response = user.put(self.FEDERATED_IDENTITY_SYNCHRONIZATION_STATE, data=json.dumps(payload),
                            headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        json_response = response.json()
        log.logger.debug("Response of {0} federated identity synchronization: {1}".format(admin_state.rstrip("d"),
                                                                                          json_response))
        if json_response and "adminState" in json_response.keys() and json_response["adminState"] == admin_state:
            log.logger.debug("Successfully {0} federated identity synchronization".format(admin_state))
        else:
            raise EnmApplicationError("Failed to {0} federated identity synchronization".format(
                admin_state.rstrip("d")))

        return json_response

    def force_sync_federated_identity_synchronization(self, user):
        """
        Trigger the Federated Identity Synchronization forced sync to forcefully execute synchronization.

        :type user: enm_user_2.User
        :param user: User instance

        :return: returns sync status of Federated Identity Synchronization.
        :rtype: dict

        :raises HttpError: if response status is not ok
        :raises EnmApplicationError: if getting empty response
        """
        log.logger.debug("Attempting to force sync federated identity synchronization")
        response = user.post(self.FEDERATED_IDENTITY_SYNCHRONIZATION_FORCED_SYNC, headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        json_response = response.json()
        log.logger.debug("Response of force sync federated identity synchronization: {0}".format(json_response))
        if not json_response:
            raise EnmApplicationError("Failed to force sync federated identity synchronization")
        log.logger.debug("Successfully initialized force sync federated identity "
                         "synchronization : {0}".format(json_response))
        return json_response

    def get_federated_identity_last_synchronization_report(self, user):
        """
        Retrieve the Federated Identity last synchronization report.

        :type user: enm_user_2.User
        :param user: User instance

        :return: returns Federated Identity last synchronization report.
        :rtype: dict

        :raises HttpError: if response status is not ok
        :raises EnmApplicationError: Failed to get the federated identity last synchronization report
        """
        log.logger.debug("Attempting to get the last federated identity synchronization report")
        response = user.get(self.FEDERATED_IDENTITY_SYNC_REPORT, headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        json_response = response.json()

        log.logger.debug("Response of last federated identity synchronization report : {0}".format(json_response))
        if ("actionReport" in json_response and "result" in json_response["actionReport"] and
                json_response["actionReport"]["result"] != "failed" and "taskReports" in json_response):
            log.logger.debug("Successfully fetched last federated identity synchronization report")
            perform_crud_task_report = [report for report in json_response["taskReports"]
                                        if report["task"] == u'performCrud']
            merge_task_report = [report for report in json_response["taskReports"] if report["task"] == u'merge']

            if not perform_crud_task_report:
                log.logger.debug("Failed to create {0} federated users in external LDAP".format(
                    merge_task_report[0]["counters"]["numExtFederatedUsers"]["value"]))
            else:
                log.logger.debug("{0} federated users already present into ENM".format(
                    merge_task_report[0]["counters"]["numEnmFederatedUsers"]["value"]))
                log.logger.debug("{0} federated users present into external LDAP".format(
                    merge_task_report[0]["counters"]["numExtFederatedUsers"]["value"]))
                log.logger.debug("Successfully {0} federated users created in ENM".format(
                    perform_crud_task_report[0]["counters"]["numUserCreateSuccess"]["value"]
                ))
        else:
            raise EnmApplicationError("Failed to get the last federated identity synchronization report")

        return json_response

    def get_period_of_federated_identity_synchronization(self, user):
        """
        Get period of federated identity synchronization.

        :type user: enm_user_2.User
        :param user: User instance

        :return: returns period of federated identity synchronization.
        :rtype: dict

        :raises HttpError: if response status is not ok
        """
        log.logger.debug("Attempting to get period of federated identity synchronization")
        response = user.get(self.FEDERATED_IDENTITY_SYNCHRONIZATION_PERIOD, headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        json_response = response.json()
        log.logger.debug("Successfully fetched period of federated identity synchronization")

        return json_response

    def get_federated_identity_synchronization_state(self, user):
        """
        Retrieve the state of the Federated Identity Synchronization. Both administrative and operational
        states are returned.

        :type user: enm_user_2.User
        :param user: User instance

        :return: returns state of federated identity synchronization
        :rtype: dict

        :raises HttpError: if response status is not ok
        """
        log.logger.debug("Attempting to get state of the federated identity synchronization")
        response = user.get(self.FEDERATED_IDENTITY_SYNCHRONIZATION_STATE, headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        json_response = response.json()
        log.logger.debug("Successfully fetched federated identity synchronization state : {0}".format(json_response))

        return json_response

    def force_delete_federated_identity_synchronization(self, user):
        """
        Trigger the Federated Identity Synchronization forced delete to remove all federated users from Local server.

        :type user: enm_user_2.User
        :param user: User instance

        :return: returns status of forced delete Federated identity synchronization.
        :rtype: dict

        :raises HttpError: if response status is not ok
        """
        log.logger.debug("Attempting to force delete federated identity synchronization")
        response = user.post(self.FEDERATED_IDENTITY_SYNCHRONIZATION_FORCED_DELETE, headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        json_response = response.json()
        log.logger.debug("Successfully initialized force delete federated identity "
                         "synchronization : {0}".format(json_response))
        return json_response

    def restore_to_defaults_federated_identity_synchronization(self, user):
        """
        Trigger the Federated Identity Synchronization restore to defaults.

        :type user: enm_user_2.User
        :param user: User instance

        :return: returns status of Federated Identity Synchronization.
        :rtype: dict

        :raises HttpError: if response status is not ok
        """
        log.logger.debug("Attempting to restore the federated identity synchronization to defaults")
        response = user.post(self.FEDERATED_IDENTITY_SYNCHRONIZATION_RESTORE_TO_DEFAULT,
                             headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        json_response = response.json()
        log.logger.debug("Successfully restore federated identity synchronization to "
                         "defaults : {0}".format(json_response))

        return json_response

    def wait_force_sync_federated_identity_synchronization_to_complete(self, user):
        """
        Waits and checks for force sync federated identity synchronization  adminState is 'enabled'
        and operState is "idle"

        :type user: enm_user_2.User
        :param user: User instance

        :raises TimeOutError: when jon state cannot be verified within given time
        :raises EnmApplicationError: when job status not in RUNNING/CREATED state

        :rtype: dict
        :return: federated_identity_synchronization status

        :raises TimeOutError: still fetched federated identity synchronization force sync
                              operState is forcedSyncInProgress with in given time
        """
        log.logger.debug("checking the status of force sync federated identity synchronization operation")
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=self.SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS)
        while datetime.datetime.now() < expiry_time:
            fidm_sync_state = self.get_federated_identity_synchronization_state(user)
            if fidm_sync_state["adminState"] == "enabled" and fidm_sync_state["operState"] == "idle":
                log.logger.debug("Federated identity force sync operation completed successfully")
                return fidm_sync_state
            log.logger.debug("Force sync operation is still in progress, "
                             "Sleeping for {0} seconds before re-trying..".format(90))
            time.sleep(90)

        raise TimeOutError("Cannot verify the sync state of federated identity synchronization")

    def wait_force_delete_federated_identity_synchronization_to_complete(self, user):
        """
        Waits and checks for force delete federated identity synchronization  adminState is 'disabled'
        and operState is "disabled"

        :type user: enm_user_2.User
        :param user: User instance

        :rtype: dict
        :return: federated identity synchronization status

        :raises TimeOutError: still fetched federated identity synchronization force sync
                              operState is forcedDeleteInProgress with in given time
        """
        log.logger.debug("checking the status of force delete federated identity synchronization operation")
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=self.SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS)
        while datetime.datetime.now() < expiry_time:
            fidm_sync_state = self.get_federated_identity_synchronization_state(user)
            if fidm_sync_state["adminState"] == "disabled" and fidm_sync_state["operState"] == "disabled":
                log.logger.debug("Federated identity force delete operation completed successfully")
                return fidm_sync_state
            log.logger.debug("Force delete operation is still in progress, "
                             "Sleeping for {0} seconds before re-trying..".format(90))
            time.sleep(90)

        raise TimeOutError("Cannot verify the sync state of federated identity synchronization")
