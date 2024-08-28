# ********************************************************************
# Name    : DDP Info Logging
# Summary : Module to log profile information to file(s) for upload to DDP.
# ********************************************************************
from enmutils.lib import filesystem, shell, log


LOG_FILES = {"CMIMPORT": "/home/enmutils/cm/cmimport_ddp_info.log", "CMSYNC": "/home/enmutils/cm/cmsync_ddp_info.log"}


def update_cm_ddp_info_log_entry(profile_name, data):
    """
    Update the CM information to be uploaded to DDP for APT assertions

    :param profile_name: Name of the profile to update the information of
    :type profile_name: str
    :param data: String to be written to text file
    :type data: str
    """
    try:
        log_file = LOG_FILES.get(profile_name.split('_')[0])
        cmd = "sed -i '/{0}/d' {1}".format(profile_name.upper(), log_file)
        shell.run_local_cmd(shell.Command(cmd))
        filesystem.write_data_to_file(data, log_file, append=True, log_to_log_file=False)
    except Exception as e:
        log.logger.debug(str(e))
