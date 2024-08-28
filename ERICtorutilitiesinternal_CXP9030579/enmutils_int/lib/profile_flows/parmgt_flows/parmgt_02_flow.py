import json
import time

from functools import partial
from random import choice
from requests import HTTPError, ConnectionError
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.parameter_management import (get_parameter_set, get_parameter_set_count,
                                                   create_parameter_set, delete_parameter_set,
                                                   TEST_DATA, PARAMETERS_4G, PARAMETERS_5G)
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib.mutexer import mutex
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib import log


class ParMgt02Flow(GenericFlow):
    def __init__(self, *args, **kwargs):
        self.parameter_set_count = 0
        self.max_limit = 0
        self.daily_limit = 0
        super(ParMgt02Flow, self).__init__(*args, **kwargs)

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        self.teardown_list.append(partial(picklable_boundmethod(self.clean_up), user=users[0]))
        # Calculate the limits for parameter sets to be created initially (maximum) and daily
        # depending on the number of users (threads), to be used in task set
        self.max_limit = self.MAX_NUM_PARAMETER_SETS - len(users) + 1
        self.daily_limit = self.NUM_PARAMETER_SETS - len(users) + 1
        sleep_times_for_retry = self.SLEEP_TIMES_FOR_RETRY
        while self.keep_running():
            for sleep_time in sleep_times_for_retry:
                try:
                    log.logger.info("Initial number of parameter sets in deployment "
                                    "before the iteration - {0}".format(get_parameter_set_count(users[0])))
                    self.parameter_set_count = 0
                    self.create_and_execute_threads(users, len(users), args=[self])
                    log.logger.info("Number of parameter sets in deployment "
                                    "after the iteration - {0}".format(get_parameter_set_count(users[0])))
                    log.logger.info("Number of parameter sets created "
                                    "as calculated by profile - {0}".format(self.parameter_set_count))
                except (HTTPError, ConnectionError) as e:
                    self.add_error_as_exception(
                        EnmApplicationError("Unable to get parameter set due to {}".format(str(e))))
                except Exception as e:
                    self.add_error_as_exception(EnvironError(e))
                else:
                    break
                log.logger.debug("Retrying after sleeping for {0} "
                                 "seconds".format(sleep_time))
                time.sleep(sleep_time)
            self.sleep()

    @staticmethod
    def task_set(worker, profile):
        """
        Task set for use with thread queue

        :type worker: list
        :param worker: list of tuples of user and corresponding persistent objects to be modified
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        :raises EnvironError: If there are no parameterSets
        """
        try:
            user = worker
            log.logger.info("Create up to {} parameter sets at the start of the iteration "
                            "if not present already".format(profile.MAX_NUM_PARAMETER_SETS))
            while profile.parameter_set_count < profile.max_limit:
                with mutex("parameter_set"):
                    ParMgt02Flow.create_parameter_sets_up_to_max(user, profile)
            log.logger.info("Wait 5 seconds for completion of creating parameter sets from other threads")
            time.sleep(5)
            log.logger.info("Number of parameter sets - {}".format(profile.parameter_set_count))
            parameter_set_json = get_parameter_set(user)
            if not parameter_set_json.get("parameterSets"):
                raise EnvironError("Unable to get parameterSets value from json response of parameter set data")
            parameter_set_data = [pset for pset in parameter_set_json["parameterSets"]
                                  if profile.NAME in pset["name"]]
            profile.counter = 0
            log.logger.info("Deleting parameter sets daily")
            while profile.counter < profile.daily_limit and parameter_set_data:
                with mutex("parameter_set"):
                    ParMgt02Flow.delete_parameter_set_and_update_profile_variables(user,
                                                                                   profile,
                                                                                   parameter_set_data)
            log.logger.info("Wait 5 seconds for completion of deleting parameter sets from other threads")
            time.sleep(5)
            log.logger.info("Number of parameter sets - {}".format(profile.parameter_set_count))
            log.logger.info("Creating parameter sets daily")
            while profile.parameter_set_count < profile.max_limit:
                with mutex("parameter_set"):
                    ParMgt02Flow.create_parameter_sets_up_to_max(user, profile)
        except (HTTPError, ConnectionError) as e:
            profile.add_error_as_exception(
                EnmApplicationError("Unable to get/create/delete parameter set due to {}".format(str(e))))
        except Exception as e:
            profile.add_error_as_exception(e)

    @staticmethod
    def delete_parameter_set_and_update_profile_variables(user, profile, parameter_set_data):
        """
        Delete parameter sets and update profile variables for
        parameter set count and number of parameter sets deleted

        :type user: `enm_user_2.User`
        :param user: User who will create the job
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        :param parameter_set_data: list of parameter sets created by the profile
        :type parameter_set_data: list
        """
        delete_parameter_set(user, parameter_set_data[profile.counter]["id"])
        profile.parameter_set_count -= 1
        profile.counter += 1

    @staticmethod
    def create_parameter_sets_up_to_max(user, profile):
        """
        Create parameter sets up to maximum number of parameter sets

        :type user: `enm_user_2.User`
        :param user: User who will create the job
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """
        TEST_DATA["name"] = profile.identifier + "_" + str(profile.parameter_set_count)
        TEST_DATA["parameterDetails"] = choice((PARAMETERS_4G, PARAMETERS_5G))
        create_parameter_set(user, data=json.dumps(TEST_DATA))
        profile.parameter_set_count += 1

    def clean_up(self, user):
        """
        Cleanup parameter sets created in the profile

        :type user: `enm_user_2.User`
        :param user: User who will create the job
        """
        try:
            response = get_parameter_set(user)
            parameter_sets = response["parameterSets"]
            parameter_set_ids = [parameter_set["id"] for parameter_set in parameter_sets
                                 if self.NAME in parameter_set["name"]]
            num_parameter_sets_deleted = 0
            for parameter_set_ids_chunk in chunks(parameter_set_ids, self.CHUNK_SIZE):
                delete_response = delete_parameter_set(user, parameter_set_ids_chunk)
                num_parameter_sets_deleted += len([_ for _ in delete_response.json()["data"] if _["errorCode"] == 0])
            log.logger.info("Number of parameter sets deleted successfully - {}".format(num_parameter_sets_deleted))
            self.parameter_set_count = get_parameter_set_count(user)
            log.logger.info("Number of parameter sets after teardown - {}".format(self.parameter_set_count))
        except (HTTPError, ConnectionError) as e:
            self.add_error_as_exception(
                EnmApplicationError("Unable to get/delete parameter set due to {}".format(str(e))))
        except Exception as e:
            self.add_error_as_exception(e)
