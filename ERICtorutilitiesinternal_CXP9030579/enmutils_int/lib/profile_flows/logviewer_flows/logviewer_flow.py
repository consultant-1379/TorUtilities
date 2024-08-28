import time

from random import randint

from enmutils.lib import log
from enmutils.lib.thread_queue import ThreadQueue

from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.log_viewer import LogViewer


def tasks(log_viewer):
    """
    Performs a sequence of task on the LogViewer Object group

    :param log_viewer: list `lib.log_viewer.LogViewer` instance to be used to perform the flow
    :type log_viewer: log_viewer.LogViewer
    """

    time.sleep(randint(0, 900))
    log_viewer.get_log_viewer()
    log_viewer.get_log_viewer_by_search_term()
    log_viewer.get_log_viewer_help()


class LogViewerFlow(GenericFlow):

    log_viewer_list = list()

    def execute_flow(self):
        users = self.create_profile_users(getattr(self, 'NUM_USERS', 50),
                                          getattr(self, 'USER_ROLES', ['OPERATOR']))
        self.state = "RUNNING"
        for user in users:
            self.log_viewer_list.append(LogViewer(user=user, search_term=getattr(self, 'SEARCH_TERM', 'all errors')))

        while self.keep_running():
            try:
                # Add the threads to a single thread to execute all
                sleep_time = getattr(self, 'SCHEDULE_SLEEP', 1800)
                tq = ThreadQueue(self.log_viewer_list, num_workers=len(self.log_viewer_list), func_ref=tasks,
                                 task_join_timeout=sleep_time, task_wait_timeout=sleep_time)
                tq.execute()
            except Exception as e:
                log.logger.debug("Failed to execute threads correctly: {0}".format(e.message))

            self.sleep()
