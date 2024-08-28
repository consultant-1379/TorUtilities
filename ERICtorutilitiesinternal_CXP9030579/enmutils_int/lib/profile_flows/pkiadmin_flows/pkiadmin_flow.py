from enmutils.lib import log, multitasking
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class PkiAdmin01Flow(GenericFlow):

    def __init__(self, *args, **kwargs):
        super(PkiAdmin01Flow, self).__init__(*args, **kwargs)
        self.user = None

    def execute_flow(self):
        """
        Execute the flow
        """
        self.user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        self.state = "RUNNING"
        while self.keep_running():
            self.check_profile_memory_usage()
            try:
                multitasking.create_single_process_and_execute_task(execute_pkiadmin_commands, args=(self,),
                                                                    timeout=11 * 60 * 60)
            except Exception as e:
                self.add_error_as_exception(EnvironError(e))
            self.check_profile_memory_usage()
            self.sleep()


def execute_pkiadmin_commands(profile):
    """
    Function to be used to execute the 5000 pki admin commands.

    :param profile: Profile object to execute the functionality
    :type profile: `lib.profile.Profile`
    """
    failed_commands = 0
    log.logger.debug("Executing the 5000 pki admin commands")
    cmd_indexes = [cmd_index for cmd_index in xrange(19, 5000, 20)]
    for _ in xrange(0, 5000):
        try:
            if _ in cmd_indexes:
                command = "pkiadm entitymgmt --list --entitytype ee"
            else:
                command = "pkiadm entitymgmt --list --entitytype ca"

            profile.user.enm_execute(command)
        except Exception:
            failed_commands += 1
    log.logger.debug("{0} pki admin commands are executed successfully".format(5000 - failed_commands))
    if failed_commands:
        profile.add_error_as_exception(EnvironError("{0} pki admin commands execution was failed"
                                                    .format(failed_commands)))
    profile.check_profile_memory_usage()
