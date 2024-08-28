from time import sleep
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.plm import PhysicalLinkMgt


class Plm01Flow(GenericFlow):

    def __init__(self, *args, **kwargs):
        self.MAX_LINKS = kwargs.pop('MAX_LINKS', 0)
        self.FILE_FLAG = False
        self.imported_files_check = True
        self.delete_file = None
        super(Plm01Flow, self).__init__(*args, **kwargs)

    def execute_flow(self):
        """
        Executes the flow for PLM_01 use case
        """
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        plm = PhysicalLinkMgt(user, self.NODE_TYPES)
        self.teardown_list.append(plm)
        self.state = "RUNNING"
        import_files = self.perform_pre_startup_steps(plm)
        log.logger.debug("csv files to be imported : {0}".format(import_files))

        while self.keep_running():
            try:
                if not import_files:
                    raise EnmApplicationError("No files are generated to import. Please check the profile log for "
                                              "more details")
                if not self.FILE_FLAG and (len(plm.files_imported) == len(import_files)):
                    log.logger.info("All files imported, deleting links")
                    self.FILE_FLAG = True
                    plm.delete_links_using_id(self.delete_file)
                elif self.FILE_FLAG:
                    self.FILE_FLAG = False
                    plm.create_links([self.delete_file])
                else:
                    plm.create_links(import_files)
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()

    def perform_pre_startup_steps(self, plm):
        """
        Performs all the pre-requisites before importing the files to create/delete links
        :param plm : object of PhysicalLinkMgt class
        :type plm: enmutils_int.lib.plm.PhysicalLinkMgt
        :return: csv file paths which are to be imported in every iteration
        :rtype: list
        """
        import_files = None
        try:
            import_files = self.create_files_set_max_links(plm)
            # Cleaning up any links or files that might be left out during the last run of the profile
            log.logger.debug("Cleaning up!")
            plm.delete_links_on_nodes(import_files)
            log.logger.debug("Cleanup completed, sleeping for 300 sec before starting import of files")
            sleep(300)
        except Exception as e:
            self.add_error_as_exception(e)
        return import_files

    def create_files_set_max_links(self, plm):
        """
        Generates import files which contains the links to be created in Link Management
        If MAX_LINKS is greater than the sum of links present in the import files, will update MAX_LINKS with
        the new value
        :param plm: Object of PhysicalLinkMgt which has all the functions for generating/deleting import files and links
        :type plm: enmutils_int.lib.plm.PhysicalLinkMgt
        :return: csv file paths which are to be imported in every iteration
        :rtype: list
        :raises EnmApplicationError: raised if an error occurs while generating import files or fetching max links
        """
        try:
            normalized_nodes = plm.get_normalized_nodes_from_enm()
            nodes_to_import = plm.prepare_node_details_for_import_files(normalized_nodes)
            log.logger.debug("Max no.of links count : {0}".format(self.MAX_LINKS))
            import_dict = plm.validate_nodes_for_import(nodes_to_import, self.MAX_LINKS)
            import_files = plm.write_to_csv_file(import_dict)
            delete_dict = plm.prepare_delete_links_dict(import_files)
            self.delete_file = plm.write_to_csv_file(delete_dict)[0]
            updated_max_links = plm.get_max_links_limit(import_files)
            if updated_max_links < self.MAX_LINKS:
                self.MAX_LINKS = updated_max_links
            log.logger.info("Maximum number of links that can be created on the deployment : {0}".format(self.MAX_LINKS))
            return import_files
        except Exception as e:
            raise EnmApplicationError("Unable to generate import files. Please check profile log for more details \n"
                                      "Exception : {0}".format(e))
