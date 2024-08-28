# ********************************************************************
# Name    : PLM UI
# Summary : Functional module used by Physical Link Management.
#           Provides functionality to import the generated CSV file
#           into ENM.
# ********************************************************************

import random
import string
from retrying import retry
from requests.exceptions import HTTPError, ConnectionError
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.headers import PLM_IMPORT_REQUEST_HEADER


LINK_DELTE_URL = "/linkmanagerservice/linkmanager/delete"
FILE_IMPORT_URL = "/linkmanagerservice/linkmanager/import"
_BOUNDARY_CHARS = string.digits


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)),
       wait_fixed=300000, stop_max_attempt_number=3)
def import_multipart_file_to_plm(user, file_name, file_path):
    """
    Uses REST calls for creating links by importing the provided multipart format csv file name and its path
    :param user: ENM user with required access roles
    :type user: enmutils.lib.enm_user_2.User
    :param file_name: Name of the csv file which needs to be imported
    :type file_name: str
    :param file_path: Path of the csv file which is present on the deployment
    :type file_path: str
    :return: response of the REST call
    :rtype: `requests.Response`
    """
    lines = []
    content = open(file_path, "rb").read()
    boundary = ''.join(random.choice(_BOUNDARY_CHARS) for _ in range(15))
    lines.extend(('-----------------------------{}'.format(boundary),
                  'Content-Disposition: form-data; name="file"; filename=\"{}\"'.format(file_name),
                  'Content-Type: application/octet-stream',
                  '',
                  '{}'.format(content),
                  '-----------------------------{}--'.format(boundary)))
    body = '\r\n'.join(lines)
    PLM_IMPORT_REQUEST_HEADER["Content-Type"] = ("multipart/form-data; boundary=---------------------------{}".
                                                 format(boundary))
    response = user.post(FILE_IMPORT_URL, data=body, headers=PLM_IMPORT_REQUEST_HEADER)
    raise_for_status(response, message_prefix="Failed to import file : ")
    return response
