# ********************************************************************
# Name    : Status Profile
# Summary : Module created for use by ProfileManager service. Mimics
#           the existing StatusProfile class but does not inherit from
#           core Profile class, used to set the status of profile in
#           REDIS, can then be queried by workload status operation.
# ********************************************************************

from enmutils.lib import persistence, process, log


UNWANTED_GLOBAL_ITEMS = {'PID_PATH', 'LOG_PATH', 'CURRENT_TIME', 'IMPORT_COUNT', 'BACKUP_SCHEDULE_TIME',
                         'LOG_AFTER_COMPLETED', 'THREADING_TEARDOWN_TIMER', 'ERROR_LIMIT', 'IDENT_FILE_DIR',
                         'KEEP_RUNNING', 'STARTED_NODES', 'NODES', 'CONFIGURED_RADIO_NODES', 'USER', 'FM_NBI', 'IMPORT'}


class StatusProfile(object):

    def __init__(self, **kwargs):
        self.NAME = kwargs.pop('name')
        self.pid = kwargs.pop('pid')
        self.start_time = kwargs.pop('start_time')
        self.num_nodes = kwargs.pop('num_nodes')
        self.schedule = kwargs.pop('schedule')
        self.state = kwargs.pop('state')
        self.priority = kwargs.pop('priority')
        self.last_run = kwargs.pop('last_run', None)
        self.user_count = kwargs.pop('user_count', 0)

    @property
    def running(self):
        return self.pid and process.is_pid_running(self.pid)

    @property
    def daemon_died(self):
        return self.state != "COMPLETED" and not self.running and not self.does_process_name_match_with_profile_name()

    @property
    def errors(self):
        return persistence.get("{0}-errors".format(self.NAME)) or []

    @property
    def warnings(self):
        return persistence.get("{0}-warnings".format(self.NAME)) or []

    @property
    def status(self):
        if self.daemon_died:
            return "DEAD"
        elif self.warnings and not self.errors:
            return "WARNING"
        elif self.errors:
            return "ERROR"
        return "OK"

    def run(self):
        pass

    def get_last_run_time(self):
        """
        Returns the last run time or defaults to start time

        :return: Last run time or str representation
        :rtype: datetime | str
        """
        return self.last_run if self.last_run else self.start_time

    def does_process_name_match_with_profile_name(self):
        """
        Checks the whether process name matched with profile name.
        If process name and profile name is same then returns True, otherwise returns False.

        :return: True or False
        :rtype: bool
        """

        log.logger.debug("Attempting to check whether profile name: {0} match with process name "
                         "given process id {1}.".format(self.NAME, self.pid))
        process_name = process.get_process_name(self.pid)
        log.logger.debug("Process name: {0} for process id: {1}".format(process_name, self.pid))
        if self.NAME == process_name:
            log.logger.debug("Profile name: {0} is  matched with Process name: {1} "
                             "given process id {2}.".format(self.NAME, process_name, self.pid))
            status = True
        else:
            status = False
            log.logger.debug("Profile name: {0} is not matched with Process name: {1} "
                             "given process id {2}.".format(self.NAME, process_name, self.pid))
        return status
