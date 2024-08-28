from datetime import datetime
from time import sleep
import json

from requests.exceptions import HTTPError, ConnectionError

from enmutils_int.lib.nhc import NHC_JOB_CREATE_URL
from enmutils_int.lib.nhc import get_time_from_enm_return_string_with_gtm_offset, create_nhc_request_body
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import JSON_SECURITY_REQUEST


class Nhc02(GenericFlow):

    def execute_nhc_02_flow(self):

        user, = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, retry=True)
        self.state = "RUNNING"
        ne_names = [{'name': node.node_id} for node in self.get_nodes_list_by_attribute()]
        scheduled_time = None

        while self.keep_running():
            self.sleep_until_day()
            if not scheduled_time:
                try:
                    scheduled_time = get_time_from_enm_return_string_with_gtm_offset(user, self.NHC_JOB_TIME)
                except (HTTPError, ConnectionError) as e:
                    self.add_error_as_exception(EnmApplicationError("Could not get time from the Server due to HTTP or "
                                                                    "connection error! Msg: {}".format(e)))
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError("Could not get time from the Server! "
                                                                    "Msg: {}".format(e)))
            if scheduled_time:
                report_name = self.NAME + "_Report_Administrator_" + datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                payload = create_nhc_request_body(name=report_name, time=scheduled_time, ne_elements=ne_names)
                try:
                    response = user.post(NHC_JOB_CREATE_URL, data=json.dumps(payload), headers=JSON_SECURITY_REQUEST)
                    if not response.ok:
                        response.raise_for_status()
                    log.logger.info("NHC job created successfully.")
                except (HTTPError, ConnectionError) as e:
                    self.add_error_as_exception(EnmApplicationError("Post Request Failed. NHC job not created. Msg: {}"
                                                                    .format(e.message)))
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))
                sleep(1)
