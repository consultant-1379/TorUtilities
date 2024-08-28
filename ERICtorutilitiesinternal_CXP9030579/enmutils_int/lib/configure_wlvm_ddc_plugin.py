# ********************************************************************
# Name    : configure_wlvm_ddc
# Summary : Functional module used by the workload configure_wlvm tool
#            to perform various tasks related to ddc
# ********************************************************************

from datetime import datetime
from enmutils.lib import log
from enmutils.lib.filesystem import does_dir_exist, get_files_in_directory
from enmutils_int.lib.configure_wlvm_common import execute_command

DDC_DATA_ROOT_DIR = "/var/tmp/ddc_data"
TODAY_DIR = None


def create_workload_log_file_increments():
    """
    Create workload log file increments

    :return: Boolean to indicate success or not
    :rtype: bool
    """
    log.logger.debug("Creating workload log file increments")

    global TODAY_DIR
    today = datetime.now().strftime("%d%m%y")
    TODAY_DIR = "{0}/{1}".format(DDC_DATA_ROOT_DIR, today)

    workload_dir = "{0}/plugin_data/workload".format(TODAY_DIR)

    if not does_dir_exist(workload_dir):
        return False

    try:
        return process_workload_files(workload_dir)
    except Exception as e:
        log.logger.debug("Error processing workload files - {0}".format(e))


def process_workload_files(workload_dir):
    """
    Process each workload log file in the workload directory, creating increment files if needed

    :param workload_dir: Directory where the plugin stores the workload output files (e.g. profiles.log)
    :type workload_dir: str
    :return: Boolean to indicate success or not
    :rtype: bool
    """
    log.logger.debug("Processing workload files in {0}".format(workload_dir))
    workload_files = get_files_in_directory(workload_dir, ends_with=".log")
    log.logger.debug("{0} File(s) detected (ending in .log) in workload dir: {1}".format(len(workload_files),
                                                                                         workload_files))
    result = True
    for workload_log_filename in workload_files:
        log.logger.debug("Processing file {0}".format(workload_log_filename))
        result = result and create_increment_file(workload_dir, workload_log_filename)

    return result


def create_increment_file(workload_dir, workload_log_filename):
    """
    Create increment file for a particular workload log file

    :param workload_dir: Plugin workload dir
    :type workload_dir: str
    :param workload_log_filename: Name of workload log file in plugin/workload dir (e.g. profiles.log)
    :type workload_log_filename: str

    :return: Boolean to indicate success or not
    :rtype: bool
    """
    log.logger.debug("Creating increment file for {0}/{1}".format(workload_dir, workload_log_filename))
    current_increment_files = get_list_of_increment_files(workload_dir, workload_log_filename)
    current_increment_increment = len(current_increment_files) + 1

    combined_increment_file = create_combined_increment_file(workload_dir, current_increment_files,
                                                             workload_log_filename)
    diff_file = create_diff_file(workload_dir, workload_log_filename, combined_increment_file)

    add_new_increment_file(workload_dir, workload_log_filename, diff_file, current_increment_increment)

    remove_temporary_files(workload_dir, workload_log_filename, diff_file, combined_increment_file)

    log.logger.debug("All actions completed")
    return True


def get_list_of_increment_files(workload_dir, workload_log_filename):
    """
    Get list of increment files given a particular workload log filename

    :param workload_dir: Plugin workload dir
    :type workload_dir: str
    :param workload_log_filename: Name of workload log file in plugin_data/workload dir (e.g. profiles.log)
    :type workload_log_filename: str

    :return: List of increment files
    :rtype: list
    """
    log.logger.debug("Getting list of increment files that already exist for: {0}".format(workload_log_filename))
    command = ("ls -rt {0} | egrep ^{1}.[1-9]".format(workload_dir, workload_log_filename))
    list_of_increment_files = execute_command(command, log_output=False)["output"].split()
    log.logger.debug("{0} increment file(s) found: {1}".format(len(list_of_increment_files), list_of_increment_files))
    return list_of_increment_files


def create_combined_increment_file(workload_dir, current_increment_files, workload_log_filename):
    """
    Create combined file containing contents of all increment files

    :param workload_dir: Plugin workload dir
    :type workload_dir: str
    :param current_increment_files: Current list of increment file names
    :type current_increment_files: list
    :param workload_log_filename: Name of workload log file
    :type workload_log_filename: str
    :returns: Combined file (contains contents of all increments files)
    :rtype: str
    """
    log.logger.debug("Creating combined increment file")
    combined_increment_file = "{0}/{1}.increment_files_combined".format(workload_dir, workload_log_filename)
    current_increment_files_full_paths = ["{0}/{1}".format(workload_dir, filename)
                                          for filename in current_increment_files]
    all_paths = " ".join(current_increment_files_full_paths)

    command = ("touch {0}".format(combined_increment_file) if not current_increment_files else
               "cat {0} > {1}".format(all_paths, combined_increment_file))
    execute_command(command)
    return combined_increment_file


def create_diff_file(workload_dir, workload_log_filename, combined_increment_file):
    """
    Create diff file, between workload log and combined increment file

    :param workload_dir: Plugin workload dir
    :type workload_dir: str
    :param workload_log_filename: Name of workload log file in plugin/workload dir (e.g. profiles.log)
    :type workload_log_filename: str
    :param combined_increment_file: Combined file containing contents of all increment files
    :type combined_increment_file: str
    :returns: Difference file, containing difference between workload log file and combined increment file
    :rtype: str
    """
    log.logger.debug("Creating a diff file")
    diff_file = "{0}/{1}.diff".format(workload_dir, workload_log_filename)

    command = ("diff --new-line-format='' --unchanged-line-format='' {0}/{1} {2} > {3}"
               .format(workload_dir, workload_log_filename, combined_increment_file, diff_file))
    execute_command(command, log_output=False)
    return diff_file


def add_new_increment_file(workload_dir, workload_log_filename, diff_file, current_increment_number):
    """
    Add new increment file, if new content exists

    :param workload_dir: Plugin workload dir
    :type workload_dir: str
    :param workload_log_filename: Name of workload log file in workload dir (e.g. profiles.log)
    :type workload_log_filename: str
    :param diff_file: Diff file containing differences between workload log file and combined increment file
    :type diff_file: str
    :param current_increment_number: Current increment number
    :type current_increment_number: int
    """
    log.logger.debug("Checking for content in diff file")

    command = "wc -l {0}".format(diff_file)
    lines_in_file = execute_command(command)["output"]

    if not lines_in_file.startswith("0 "):
        log.logger.debug("Content detected - creating new increment file")
        new_increment_file = "{0}/{1}.{2}".format(workload_dir, workload_log_filename, current_increment_number)
        command = "mv {0} {1}".format(diff_file, new_increment_file)
        execute_command(command)
        log.logger.debug("New increment file added to workload dir: {0}".format(new_increment_file))

        add_new_delta_file(new_increment_file, workload_log_filename)
    else:
        log.logger.debug("No increment file added as no content exists since last increment")


def add_new_delta_file(new_increment_file, workload_log_filename):
    """
    Add new delta file to the delta/workload directory

    :param new_increment_file: New Increment File (containing delta content since last increment file)
    :type new_increment_file: str
    :param workload_log_filename: Name of workload log file in workload dir (e.g. profiles.log)
    :type workload_log_filename: str
    """
    delta_dir = "{0}/delta".format(TODAY_DIR)

    if does_dir_exist(delta_dir):
        log.logger.debug("Delta directory detected - Creating workload sub-directory")
        delta_workload_dir = "{0}/workload".format(delta_dir)
        command = "mkdir -p {0}".format(delta_workload_dir)
        execute_command(command, log_output=False)

        log.logger.debug("Copying increment file to delta/workload directory")
        command = "cp {0} {1}".format(new_increment_file, delta_workload_dir)
        execute_command(command)
        log.logger.debug("New delta file added to delta dir: {0}".format(delta_dir))
    else:
        log.logger.debug("No Delta directory detected")


def remove_temporary_files(workload_dir, workload_log_filename, diff_file, combined_increment_file):
    """
    Remove temporary files

    :param workload_dir: Plugin workload dir
    :type workload_dir: str
    :param workload_log_filename: Name of workload log file in plugin/workload dir (e.g. profiles.log)
    :type workload_log_filename: str
    :param diff_file: Diff file containing differences between workload log file and combined delta data file
    :type diff_file: str
    :param combined_increment_file: File containing combined contents of all delta files
    :type combined_increment_file: str
    """
    log.logger.debug("Removing temporary files")
    command = ("rm -f {0}/{1} {2} {3}".format(workload_dir, workload_log_filename, diff_file, combined_increment_file))
    execute_command(command)
