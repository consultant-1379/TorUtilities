# ********************************************************************
# Name    : Configuration Template
# Summary : Primary module for ENM configuration application.
# ********************************************************************

import json
import os
import pkgutil
from enmutils.lib import log, shell
from enmutils.lib.headers import SECURITY_REQUEST_HEADERS

INT_PACKAGE = pkgutil.get_loader('enmutils_int').filename
IMPORT_EXPORT_CONFIGURATION_TEMPLATES_PATH = os.path.join(INT_PACKAGE, 'templates', 'import_export_configuration_templates')


class ConfigurationTemplate(object):
    CONFIGURATION_TEMPLATE_ENDPOINT = "/configuration-templates/v1/templates/"
    CONFIGURATION_TEMPLATES_PATH = os.path.join(INT_PACKAGE, 'templates', 'configuration_templates')
    TEMPLATE_FILES = [(_, (_, open(os.path.join(CONFIGURATION_TEMPLATES_PATH, _), 'rb'), 'text/xml'))
                      for _ in os.listdir(CONFIGURATION_TEMPLATES_PATH)]
    DEFAULT_METADATA = {"name": "CONFIGURATION_TEMPLATE_template",
                        "description": "Template created by the workload profile(s) of Configuration Templates application",
                        "type": "AutoIntegration",
                        "nodeTypes": ["RadioNode"]}

    def __init__(self, user, template_id=None):
        """
        Initializer for the ConfigurationTemplate class

        :param user:    Enm user who performs the operations
        :type user:     `enmutils.lib.enm_user_2.User`
        :param template_id: ID of the configuration template
        :type template_id:  str
        """
        self.user = user
        self.template_id = template_id

    def create(self, name="CONFIGURATION_TEMPLATE_template"):
        """
        Create configuration template

        :param name:    Name of the configuration template to be created
        :type name:     str
        :return:        ID of created template
        :rtype:         str
        """
        metadata_dict = dict(self.DEFAULT_METADATA)
        metadata_dict.update({"name": name})
        metadata = json.dumps(metadata_dict)

        files = [("template", ("metadata", metadata, "application/json"))] + self.TEMPLATE_FILES
        response = self.user.post(self.CONFIGURATION_TEMPLATE_ENDPOINT, files=files)
        response.raise_for_status()

        self.template_id = json.loads(response.content)["id"]

        log.logger.info("Configuration template with id - {0} and name - {1} "
                        "has been created successfully.".format(self.template_id, name))

        return self.template_id

    def export_template(self, template_id):
        """
        Export configuration template for a specific template ID

        :param template_id: ID of the configuration template to be exported
        :type template_id:  str
        """
        log.logger.info("Attempting to export configuration template with id - {0}".format(template_id))

        response = self.user.get(self.CONFIGURATION_TEMPLATE_ENDPOINT + template_id + "?attach=content&archive",
                                 headers=SECURITY_REQUEST_HEADERS)
        response.raise_for_status()

        zip_file_path = os.path.join(IMPORT_EXPORT_CONFIGURATION_TEMPLATES_PATH, template_id + ".zip")
        with open(zip_file_path, "wb") as f:
            f.write(response.content)
        # Remove first 5 lines in the response content which is metadata
        shell.run_local_cmd("sed -i 1,5d {0}".format(zip_file_path))

        log.logger.info("Configuration template with id - {0} "
                        "has been exported successfully.".format(template_id))

    def import_template(self, file_name):
        """
        Import configuration template for a specific template ID

        :param file_name: ID of the configuration template to be imported
        :type file_name:  str
        :return:        ID of imported template
        :rtype:         str
        """
        log.logger.info("Attempting to import configuration template with file name - {0}".format(file_name))

        files = [("archive", (file_name, open(os.path.join(IMPORT_EXPORT_CONFIGURATION_TEMPLATES_PATH, file_name), 'rb'),
                              'application/x-zip-compressed'))]

        response = self.user.post(self.CONFIGURATION_TEMPLATE_ENDPOINT, files=files, headers=SECURITY_REQUEST_HEADERS)
        response.raise_for_status()

        self.template_id = json.loads(response.content)["id"]

        log.logger.info("Configuration template with name - {0} "
                        "has been imported successfully.".format(file_name))
        return self.template_id

    def delete(self, template_id):
        """
        Delete configuration template for a specific template ID

        :param template_id: ID of the configuration template to be deleted
        :type template_id:  str
        """
        self.template_id = template_id
        response = self.user.delete_request(self.CONFIGURATION_TEMPLATE_ENDPOINT + template_id,
                                            headers=SECURITY_REQUEST_HEADERS)
        response.raise_for_status()
        log.logger.info("Configuration template with id - {0} "
                        "has been deleted successfully.".format(template_id))

    def _teardown(self):
        """
        Teardown method
        """
        self.delete(self.template_id)
