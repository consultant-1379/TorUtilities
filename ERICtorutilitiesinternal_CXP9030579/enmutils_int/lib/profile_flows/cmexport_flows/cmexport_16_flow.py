import time
from requests.exceptions import HTTPError
from retrying import retry

from enmutils.lib import log
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.enm_export import ShmExport
from enmutils_int.lib.netex import Search
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class CmExport16(GenericFlow):

    SEARCH_QUERY = "select all objects of type NetworkElement where NetworkElement has attr platformType = CPP"
    SEARCH_NAME = "{0}_saved_search"

    def execute_flow(self):
        """
        Executes the flow of the cmexport_16 profile
        """

        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        search_created = False
        while search_created is not True:
            try:
                search_created = self.create_save_search(user)
            except HTTPError as e:
                log.logger.debug("Could not create saved search, error encountered:: {0}. "
                                 "Retrying in 300 seconds.".format(str(e)))
                time.sleep(300)
        export_objects = [ShmExport(user=user, export_type=export_type, name=self.identifier,
                                    saved_search_name=self.SEARCH_NAME.format(self.NAME).lower())
                          for export_type in ["hw", "sw", "lic"]]
        self.state = "RUNNING"
        while self.keep_running():
            for export in export_objects:
                self.sleep_until_time()
                try:
                    # Update the name here to avoid naming conflicts
                    export.name = self.identifier
                    export.create()
                    export.validate()
                except Exception as e:
                    self.add_error_as_exception(e)

    @retry(retry_on_exception=lambda e: isinstance(e, HTTPError), wait_exponential_multiplier=60000,
           stop_max_attempt_number=3)
    def create_save_search(self, user):
        """
        Create a save search instance to be used for the export

        :param user: ENM User who will create the saved search
        :type user: `enm_user_2.User`

        :raises HTTPError: raised if the search fails to save

        :returns: Boolean indicating the saved search was saved
        :rtype: bool
        """
        search = Search(user, self.SEARCH_QUERY, name=self.SEARCH_NAME.format(self.NAME))
        try:
            if search.exists:
                log.logger.debug("Saved search already exists, attempting to delete.")
                search.delete()
                del self.teardown_list[:]
        except HTTPError as e:
            log.logger.debug("Could not delete saved search, error encountered:: {0}.".format(str(e)))
        try:
            search.save()
            self.teardown_list.append(picklable_boundmethod(search.delete))
            return True
        except HTTPError as e:
            log.logger.debug("Could not create saved search, error encountered:: {0}. "
                             "Retrying in 60 seconds, for maximum 3 attempts.".format(str(e)))
            raise
