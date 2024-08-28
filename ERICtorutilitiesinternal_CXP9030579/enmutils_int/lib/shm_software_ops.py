# ******************************************************************
# Name    : SHM SOFTWARE OPERATIONS
# Summary : Primarily used by SHM upgrade profiles. Allows the user
#           to manage package related operations within the
#           SHM application area that includes operations like
#           importing, verifying, deleting a package and
#           fetching the list of packages from smrs etc
# ******************************************************************

import re
from time import sleep

from requests_toolbelt.multipart.encoder import MultipartEncoder

from requests.exceptions import HTTPError
from retrying import retry

from enmutils.lib import filesystem, log
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import SHM_LONG_HEADER
from enmutils_int.lib.shm_data import (
    PLATFORM_TYPES, SHM_REFERRED_BACKUP_LIST_NODE_ENDPOINT,
    SHM_REFERRED_SOFTWARE_PACKAGE_LIST_NODE_ENDPOINT,
    SHM_SOFTWARE_PACKAGE_LIST_ENDPOINT,
    SHM_SOFTWARE_PACKAGE_LIST_NODE_ENDPOINT,
    SHM_SOFTWARE_PACKAGE_UPLOAD_ENDPOINT)


class SoftwareOperations(object):

    def __init__(self, user, package, ptype="ERBS"):
        """
        Imports a valid software package into ENM

        :type package: `SoftwarePackage`
        :param package: Instance of `enm_shm.SoftwarePackage`
        :type user: `enm_user_2.User`
        :param user: user to use for the REST request
        :type ptype: str
        :param ptype: Primary type of the node
        """
        file_format = ".tgz" if ptype in ["MLTN", "LH", "MINI-LINK-Indoor", "MINI-LINK-669x"] else ".zip"
        self.user = user
        self.zip_file_path = "{0}{1}".format(package.new_dir, file_format)
        self.package_name = package.new_package

    @retry(
        retry_on_exception=lambda e: isinstance(e, (HTTPError, EnmApplicationError)) or "Connection aborted" in str(e) or "Broken pipe" in str(e),
        wait_fixed=120000, stop_max_attempt_number=3)
    def import_package(self):
        """
        Upload the software upgrade package to ENM
        :raises HTTPError: when the rest call response is not ok, after upload and wait for certain time
        :raises EnmApplicationError: when the rest call failed to upload the upgrade package
        :raises EnvironmentError: when the package unable to find in directory /home/enmutils/shm
        """
        log.logger.debug("Checking if package exists in ENM, before attempting to import the software package {0} in "
                         "ENM".format(self.package_name))
        package_exists = self.package_exists(package_name=self.package_name, user=self.user,
                                             filter_text=self.package_name)
        log.logger.debug("Sleeping for 3secs before fetching package details")
        sleep(3)
        if not package_exists and filesystem.does_file_exist(self.zip_file_path):
            log.logger.debug("Package not found, attempting to import the software package")
            try:
                with open(self.zip_file_path, 'rb') as import_file:
                    response = self.user.post(SHM_SOFTWARE_PACKAGE_UPLOAD_ENDPOINT,
                                              files={'softwarePackage': import_file})
            except Exception as e:
                try:
                    log.logger.debug('Failed - {0}, trying to import with Multipart'.format(e))
                    multipart_data = MultipartEncoder(
                        fields={'file': (self.package_name + '.zip', open(self.zip_file_path, 'rb'), 'zip')})
                    response = self.user.post(SHM_SOFTWARE_PACKAGE_UPLOAD_ENDPOINT, data=multipart_data,
                                              headers={'Content-Type': multipart_data.content_type})
                except Exception as e:
                    raise EnmApplicationError("Software import encountered exception: {0} ".format(str(e)))
            else:
                sleep(3)
                log.logger.debug("Sleeping for 3secs after package upload")
            if response.ok:
                self.verify_upload_package()
            else:
                raise HTTPError('Cannot upload software package to ENM. Check logs for details. '
                                'Response was {0}'.format(response.text), response=response)
        elif package_exists:
            log.logger.debug("Software upgrade package {0} was already uploaded".format(self.package_name))
        else:
            raise EnvironmentError("Package import Failed, Software upgrade package {0} doesn't exist in shm "
                                   "directory to upload to ENM".format(self.package_name))

    def verify_upload_package(self):
        """
        Check the package upload status in ENM for every 30 secs
        :raises EnmApplicationError: when the rest call failed to upload the upgrade package in specified time (30 mnts)
        """
        sleep_time = 0
        while sleep_time < 30:
            package_exists = self.package_exists(package_name=self.package_name, user=self.user, filter_text=self.package_name)
            if package_exists:
                log.logger.debug("Software upgrade package {0} was successfully uploaded".format(self.package_name))
                break
            else:
                log.logger.debug("Sleeping for 60 seconds to allow SHM to update with the newly imported package")
                sleep(60)
                sleep_time += 1
        else:
            raise EnmApplicationError("Cannot upload software package to enm in estimated time")

    @classmethod
    def get_all_software_packages(cls, user, filter_text=None):
        """
        Get all imported software packages

        :type user: `enm_user_2.User`
        :param user: user to use for the REST request
        :type filter_text: str
        :param filter_text: String filter to use such as "CXP16BCP1" to identify software package

        :rtype: list
        :returns: list of imported software packages in the SHM application
        """
        cls.user = user
        cls.user.open_session()
        payload = {
            "offset": 1,
            "limit": 50,
            "sortBy": "importDate",
            "ascending": False,
            "nodePlatform": None,
            "filterDetails": [{"columnName": "name", "filterOperator": "*", "filterText": filter_text}]
        }
        response = cls.user.post(SHM_SOFTWARE_PACKAGE_LIST_ENDPOINT, json=payload, headers=SHM_LONG_HEADER)
        if filter_text:
            filter_package = r"\w*{0}\w*".format(filter_text)
            package_list = re.findall(filter_package, str(response.content))
        else:
            package_list = response.content
        return package_list

    def package_exists(self, package_name, user, filter_text=None):
        """
        Check whether exact package is present in the list of all imported software packages

        :type package_name: str
        :param package_name: validate the package name with the list of available imported packages
        :type user: `enm_user_2.User`
        :param user: user to use for the REST request
        :type filter_text: str
        :param filter_text: String filter to use such as "CXP16BCP1" to identify software package
        :rtype: bool
        :return: returns True if package exists in inventory and returns false if package won't present
        """
        check_package = any(each_package for each_package in
                            self.get_all_software_packages(user=user, filter_text=filter_text)
                            if package_name == each_package)
        return check_package

    @classmethod
    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=60000, stop_max_attempt_number=3)
    def get_packages_on_nodes(cls, nodes, user):
        """
        Get available software package from the provided nodes

        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type user: `enm_user_2.User`
        :param user: user to use for the REST request

        :rtype: dict
        :return: Response object json dict
        """
        fdns = ["NetworkElement={0}".format(node.node_id) for node in nodes]
        payload = {
            "fdns": fdns,
            "offset": 1,
            "limit": 50,
            "sortBy": "nodeName",
            "ascending": True,
            "filterDetails": []
        }
        response = user.post(SHM_SOFTWARE_PACKAGE_LIST_NODE_ENDPOINT, json=payload, headers=SHM_LONG_HEADER)
        raise_for_status(response, "Failed to get software packages on node.")
        return response.json()

    @classmethod
    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=60000, stop_max_attempt_number=3)
    def get_referred_packages_on_nodes(cls, node, user, package_fdn, product_revision, product_number):
        """
        Get referred software package from the provided nodes

        :type node: `enm_node.Node`
        :param node: Node object to view referred package of
        :type user: `enm_user_2.User`
        :param user: user to use for the REST request
        :type package_fdn: str
        :param package_fdn: The fdn of the UpgradePackage
        :type product_revision: str
        :param product_revision: The product revision of the package
        :type product_number: str
        :param product_number: The product number of the package

        :rtype: dict
        :return: Response object json dict
        """
        payload = {
            "nodeName": node.node_id,
            "platformType": PLATFORM_TYPES.get(node.primary_type),
            "upgradePackageFdn": package_fdn,
            "productRevision": product_revision,
            "productNumber": product_number
        }
        response = user.post(SHM_REFERRED_SOFTWARE_PACKAGE_LIST_NODE_ENDPOINT, json=payload,
                             headers=SHM_LONG_HEADER)
        raise_for_status(response, "Failed to get referred upgrades on node.")
        return response.json()

    @classmethod
    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_fixed=60000, stop_max_attempt_number=3)
    def get_referred_backups_on_nodes(cls, node, user, package_fdn, product_revision, product_number):
        """
        Get referred software package from the provided nodes

        :type node: list
        :param node: Node object to view referred package of
        :type user: `enm_user_2.User`
        :param user: user to use for the REST request
        :type package_fdn: str
        :param package_fdn: The fdn of the UpgradePackage
        :type product_revision: str
        :param product_revision: The product revision of the package
        :type product_number: str
        :param product_number: The product number of the package

        :rtype: dict
        :return: Response object json dict
        """
        payload = {
            "nodeName": node.node_id,
            "platformType": PLATFORM_TYPES.get(node.primary_type),
            "upgradePackageFdn": package_fdn,
            "productRevision": product_revision,
            "productNumber": product_number
        }
        response = user.post(SHM_REFERRED_BACKUP_LIST_NODE_ENDPOINT, json=payload, headers=SHM_LONG_HEADER)
        raise_for_status(response, "Failed to get referred backups on node.")
        return response.json()
