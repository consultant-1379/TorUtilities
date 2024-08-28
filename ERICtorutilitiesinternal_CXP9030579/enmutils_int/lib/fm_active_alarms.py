# ********************************************************************
# Name    : FM Active Alarms
# Summary : Module for querying for Active alarms.
#           Allows the user the query ENM for active alarms count,
#           based on the alarm stage, Acknowledged, Unacknowledged,
#           Cleared.
# ********************************************************************


import re

from enmutils.lib import log


class FmActiveAlarmCheck(object):

    ALARMS = 'cmedit get * OpenAlarm.(alarmState=="{0}") --count'
    ACTIVE_ALARMS = 0

    OPEN_ALARMS_STEPS = ["ACTIVE_ACKNOWLEDGED", "ACTIVE_UNACKNOWLEDGED", "CLEARED_UNACKNOWLEDGED"]

    def __init__(self, user):
        self.user = user

    def check_active_alarms(self):
        """
        Calculates the number of active alarms: active ack and unack alarms plus cleared unack alarms
        :return: Number of active alarms
        """
        for alarm in self.OPEN_ALARMS_STEPS:
            command_response = self.user.enm_execute(self.ALARMS.format(alarm))
            if command_response.get_output()[0] != '':
                alarms = re.findall(r'\d+', command_response.get_output()[0])
                self.ACTIVE_ALARMS = self.ACTIVE_ALARMS + int(alarms[0])
                log.logger.debug("Number of {0}: {1} alarms".format(alarm, self.ACTIVE_ALARMS))

        return int(self.ACTIVE_ALARMS)
