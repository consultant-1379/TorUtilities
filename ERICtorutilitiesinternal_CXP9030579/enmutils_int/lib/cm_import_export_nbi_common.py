# ********************************************************************
# Name    : CM Import/Export NBI Common
# Summary : Basic shared functionality for CM Bulk NBI.
#           Allows user to upload, download or create CM NBI files.
# ********************************************************************

import os

from enmutils.lib import filesystem, log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.enm_user_2 import raise_for_status


def get_download_file(user, job_id, operation="", end_point=None, file_path=None):

    """
    Retrieve the file by sending a GET request to the file URI
    :param user: user to carry out the request
    :type user: enm_user_2.User
    :param job_id: id of the job
    :type job_id: int
    :param operation: operation being carried out - whether it is a download operation or an undo operation
    :type operation: str
    :param end_point: file path where the jobs are stored
    :type end_point: file path
    :param file_path: location where the file will be stored
    :type file_path: file path
    :raises: HTTPError
    :raises EnmApplicationError: raised the File URI is not found
    """

    log.logger.debug('Attempting to retrieve the {0} file for job id: {1}'.format(operation, job_id))
    get_completed_job_response = get_download_job_details_by_id(user, job_id, end_point)
    file_uri = get_completed_job_response.get('fileUri')
    if not file_uri:
        raise EnmApplicationError("Unable to retrieve file URI, response\t[{0}].".format(get_completed_job_response))
    get_file_response = user.get(file_uri, stream=True)
    raise_for_status(get_file_response, 'Error retrieving {0} file for {0} job id {1}'.format(operation, job_id))

    write_to_file_location(file_uri, get_file_response, file_path, operation,
                           dev_null=True if user.username.startswith("CMEXPORT") else False)


def get_download_job_details_by_id(user, job_id, end_point):
    """
    Send a GET request to retrieve the job details with the job id.
    :param user: user to carry out the request.
    :type user: enm_user_2.User
    :param job_id: id of the job
    :type job_id: int
    :param end_point: file path where the jobs are stored
    :type end_point: file path
    :return: the response to the REST request in JSON format
    :rtype: dict
    :raises: HTTPError
    """

    get_response = user.get(end_point.format(undo_id=job_id))
    raise_for_status(get_response, message_prefix='Could not get details for job {0}: '.format(job_id))

    return get_response.json()


def write_to_file_location(file_uri, get_file_response, file_path, operation, dev_null=False):
    """
    Write the data of the file to a specific file location

    :param file_uri: fileUri of the file, as retrieved from get_download_file
    :type file_uri: URI
    :param get_file_response: the response from the GET request to the fileUri
    :type get_file_response: Response
    :param file_path: location where the file will be stored
    :type file_path: str
    :param operation: operation being carried out - whether it is a download operation or an undo operation
    :type operation: str
    :param dev_null: Boolean indicating if output should be written to /dev/null
    :type dev_null: bool
    :raises EnmApplicationError: raised if error encountered writing the file
    """
    if dev_null:
        try:
            filesystem.write_data_to_file(data=get_file_response.content, output_file=os.devnull)
            log.logger.debug('File has been successfully written to location {0}'.format(os.devnull))
            return
        except Exception as e:
            log.logger.debug('Error writing {0} file to location: {1}. Error encountered:: {2}.'
                             .format(operation, os.devnull, str(e)))
            return
    if operation == 'undo':
        file_name = file_uri.replace('/configuration', '')
    else:
        file_name = file_uri.replace('/bulk/export', '')

    file_location = file_path + file_name

    log.logger.debug('Attempting to write file to location: {0} .'.format(file_location))
    try:
        filesystem.create_dir(file_path)
        filesystem.touch_file(file_location)
        filesystem.write_data_to_file(data=get_file_response.content, output_file=file_location)
        log.logger.debug('File has been successfully written to location {0}'.format(file_location))

    except Exception as e:
        log.logger.debug('Error writing {0} file to location: {1} .'.format(operation, file_location))
        raise EnmApplicationError(e)
