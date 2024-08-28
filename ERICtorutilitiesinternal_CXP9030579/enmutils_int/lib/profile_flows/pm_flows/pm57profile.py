import time
from enmutils.lib import log
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

ULSA_FILES_SUMMARY = "/pmul-service/rest/ulsa/files/summary"
ULSA_FILES_URL = "/pmul-service/rest/ulsa/files?nodeId={networkelement}&ruId={radiounit}&portId={port}"
ULSA_FILE_SAMPLES_URL = "/pmul-service/rest/sa/files/{filename}/spectrum/plottabledata"


def chunks(elements, n):
    """
    Divide a list in n-sized chunks
    """
    for i in xrange(0, len(elements), n):
        yield elements[i:i + n]


def get_files_summary_list(user):
    """
    Query the FLS to retrieve the files summary

    :param user: User to run GET request.
    :type user: enmutils.lib.enm_user_2.User

    :return: List of dictionaries. Each dictionary contains ULSA file metadata details for a specific NetworkElement
    :rtype: list

    :raises EnmApplicationError: if there is a problem fetching summary of files
    """
    log.logger.info("Fetching summary of ULSA information from ENM")
    summary_response = user.get(ULSA_FILES_SUMMARY, headers=JSON_SECURITY_REQUEST)
    if not summary_response.ok or not summary_response.json():
        raise EnmApplicationError('Error retrieving the files summary.')
    return summary_response.json()


def retrieve_ulsa_files(user, summary, max_number_of_files_to_be_fetched):
    """
    Using the provided files summary, find the required amount of ULSA files in the system.
    3 attempts allowed for each NetworkElement file search.

    :param user: User to run GET request.
    :type user: enmutils.lib.enm_user_2.User

    :param summary: List of dictionaries. Each dictionary contains ULSA file metadata details for a specific Node
    :type summary: list

    :param max_number_of_files_to_be_fetched: Maximum number of files to be fetched
    :type max_number_of_files_to_be_fetched: int

    :return: List of file paths
    :rtype: list
    """
    filepaths = []
    for file_summary in summary:
        attempt = 0
        response_state = False
        while not response_state and attempt < 3:
            attempt += 1
            try:
                log.logger.debug("Querying ENM to get list of files for NE '{0}'"
                                 .format(file_summary['networkelement']))
                response = user.get(ULSA_FILES_URL.format(networkelement=file_summary['networkelement'],
                                                          radiounit=file_summary['radiounit'],
                                                          port=file_summary['port']),
                                    headers=JSON_SECURITY_REQUEST)
                node_filepaths = [item.get('filepath') for item in response.json()]
                log.logger.debug("{0} files retrieved for NE '{1}'"
                                 .format(len(node_filepaths), file_summary['networkelement']))
                filepaths.extend(node_filepaths)
            except Exception as error:
                log.logger.error("Error retrieving the files list for NE '{0}': {1}."
                                 "Attempt {2}/3. Check profile logs. "
                                 "Sleeping 2 minutes before retrying..."
                                 .format(file_summary['networkelement'], error, attempt))
                time.sleep(120 if attempt < 3 else 1)
        if len(filepaths) >= max_number_of_files_to_be_fetched:
            break
    return filepaths[:max_number_of_files_to_be_fetched]


def get_spectrum_data(user_file_tuple):
    """
    Thread function.
    GET Spectrum sample data.

    :param user_file_tuple: Contains an User and a filename string.
    :type user_file_tuple: tuple

    :raises EnvironError: if there was an exception thrown fetching data from ENM
    :raises EnmApplicationError: if the response from ENM is NOK

    """
    user, ulsa_file = user_file_tuple
    log.logger.info("USER: {user}: retrieving Spectrum sample data for file '{filename}'."
                    .format(user=user.username, filename=ulsa_file))
    try:
        response = user.get(ULSA_FILE_SAMPLES_URL.format(filename=ulsa_file), headers=JSON_SECURITY_REQUEST)
    except Exception as e:
        raise EnvironError("USER {user}: Error retrieving Spectrum sample data for file: '{filename}' - {error}"
                           .format(user=user.username, filename=ulsa_file, error=e))
    if not response.ok:
        raise EnmApplicationError("USER {user}: Response NOK retrieving Spectrum sample data for file: '{filename}'"
                                  .format(user=user.username, filename=ulsa_file))
    elif not response.json():
        raise EnvironError("USER {user}: Empty output retrieving Spectrum sample data for file: '{filename}'"
                           .format(user=user.username, filename=ulsa_file))
    else:
        log.logger.info("USER {user}: Spectrum sample data for file '{filename}' successfully retrieved."
                        .format(user=user.username, filename=ulsa_file))


class Pm57Profile(GenericFlow):

    def get_users_filename_lists(self, users, sampling_periods):
        """
        Retrieves the ULSA files required by the users to get the required sample data

        :param users: List of User objects
        :type users: list
        :param sampling_periods: Number of Sampling periods
        :type sampling_periods: int

        :return: List. List of string lists.
        :rtype: list
        """
        try:
            summary_list = get_files_summary_list(users[0])
        except Exception as e:
            self.add_error_as_exception(
                EnmApplicationError('Cannot retrieve summary of ULSA files. '
                                    'Profile will retry in the next run, in 24 hours - {0}'.format(e)))
            return []
        max_number_of_files_to_be_fetched = len(users) * sampling_periods
        filepaths = retrieve_ulsa_files(users[0], summary_list, max_number_of_files_to_be_fetched)
        log.logger.debug("ULSA Files: ")

        if not filepaths:
            self.add_error_as_exception(
                EnvironError('No ULSA file available. Profile will retry in the next run, in 24 hours.'))
            return []

        # Get filenames from filepaths in the list
        filenames = [filepath.split('/')[-1] for filepath in filepaths]

        # If there aren't enough files for all the users, extend the filename list duplicating the retrieved ones
        if len(filenames) < max_number_of_files_to_be_fetched:
            while len(filenames) < max_number_of_files_to_be_fetched:
                filenames.extend(filenames)

        # Get first MAX_NUMBER_OF_FILES_TO_BE_FETCHED elements and divide them into groups.
        # Each group of filenames will be assigned to an user.
        return list(chunks(filenames[:max_number_of_files_to_be_fetched], len(users)))

    def process_ulsa_files(self, users, sampling_periods, time_between_sampling_periods):
        """
        Process ULSA files

        :param users: List of User objects
        :type users: list
        :param sampling_periods: Number of sampling periods
        :type sampling_periods: int
        :param time_between_sampling_periods: Time between Sampling periods (mins)
        :type  time_between_sampling_periods: int
        """

        log.logger.info('Starting Upload Spectrum file data sampling. The iteration will last 1 hour.')
        for i in xrange(sampling_periods):
            log.logger.info('Starting sampling period: {0}/{1}.'.format(i + 1, sampling_periods))

            log.logger.info("Retrieving Upload Spectrum file summary data")
            files_per_users = self.get_users_filename_lists(users, sampling_periods)

            if files_per_users:
                log.logger.debug("Assigning list of files to be fetched to each user")
                users_files = zip(users, files_per_users[i])

                log.logger.debug("Fetching ULSA sample data in parallel")
                self.create_and_execute_threads(users_files, len(users_files), func_ref=get_spectrum_data)

                log.logger.info('Completed sampling period: {0}/{1} ended'.format(i + 1, sampling_periods))

            if i < sampling_periods - 1:
                log.logger.info("Users are now waiting {0} mins before next file attempt..."
                                .format(time_between_sampling_periods))
                time.sleep(60 * time_between_sampling_periods)

            log.logger.info('All {0} data sampling periods are completed. '
                            'Profile will sleep until next iteration.'.format(sampling_periods))

    def execute_flow(self):
        """
        Main flow for PM_57

        """
        self.state = "RUNNING"

        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)

        while self.keep_running():
            try:
                log.logger.debug(
                    "Sleeping until Uplink Spectrum Analysis (ULSA) sampling period has been started by PM_52")
                self.sleep_until_time()

                self.process_ulsa_files(users, self.SAMPLING_PERIODS, self.TIME_BETWEEN_SAMPLING_PERIODS_MINS)
            except Exception as e:
                self.add_error_as_exception(e)
