# ********************************************************************
# Name    : Node Version Support
# Summary : Currently only used by NVS profiles. Provides two basic
#           functionality in relation the Release Independence
#           application. Retrieving the list of unsupported NE models
#           and deploying those same models, retrieving the list of
#           supported models (those which have been deployed) and
#           removing support of those models. Supporting/Un-supporting
#           models is performed by NeType.
# ********************************************************************

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError


BASE_URL = "/upgrade-independence-service/rest/v5/"
GET_UNSUPPORTED_MODEL_URL = "{0}unsupported".format(BASE_URL)
GET_SUPPORTED_MODEL_URL = "{0}supported".format(BASE_URL)
POST_ADD_MODEL_URL = "{0}addsupport".format(BASE_URL)
DELETE_MODEL_URL = "{supported_url}/{ne_type}/{model_id}"


class NodeVersionSupport(object):

    def __init__(self, user, supported_ne_types):
        """
        Init method for node version support

        :param user: Instance of `enm_user_2.User`
        :type user: `enm_user_2.User`
        :param supported_ne_types: List of NeType models to be deploy or remove
        :type supported_ne_types: list
        """
        self.user = user
        self.supported_ne_types = supported_ne_types

    def get_all_unsupported_version_ids(self):
        """
        Retrieve the list of currently unsupported models from Release Information application

        :return: List of unsupported model version ids
        :rtype: list
        """
        log.logger.debug("Querying ENM for list of unsupported models.")
        response = self.user.get(GET_UNSUPPORTED_MODEL_URL)
        response.raise_for_status()
        log.logger.debug("Completed querying ENM for list of unsupported models.")
        return [unsupported.get('versionId') for unsupported in response.json() if unsupported.get('neType') in
                self.supported_ne_types]

    def get_all_supported_version_ids(self):
        """
        Retrieve dict of currently supported models, and NeTypes from Release Information application

        :return: Dictionary containing key, value pairs of model Identity and NeType
        :rtype: dict
        """
        log.logger.debug("Querying ENM for list of supported models.")
        response = self.user.get(GET_SUPPORTED_MODEL_URL)
        response.raise_for_status()
        log.logger.debug("Completed querying ENM for list of supported models.")
        return {supported.get('modelIdentity'): supported.get('neType') for supported in response.json() if
                supported.get('neType') in self.supported_ne_types}

    def deploy_unsupported_models(self):
        """
        Post the model version id for unsupported models to ENM
        """
        unsupported_models = self.get_all_unsupported_version_ids()
        if unsupported_models:
            log.logger.debug("Making deploy request to ENM, total of {0} unsupported models."
                             .format(len(unsupported_models)))
            response = self.user.post(POST_ADD_MODEL_URL, json=unsupported_models)
            response.raise_for_status()
            log.logger.debug("Completed deploy model(s) request to ENM for list of unsupported models.")
        else:
            log.logger.debug("No unsupported models available to deploy.")

    def remove_supported_models(self):
        """
        Delete the supported models from ENM

        :raises EnmApplicationError: raised if the delete model fails
        """
        supported_models = self.get_all_supported_version_ids()
        failed_deletes = 0
        if supported_models:
            log.logger.debug("Making delete request to ENM for list of supported models.")
            for model_id, ne_type in supported_models.items():
                try:
                    response = self.user.delete_request(DELETE_MODEL_URL.format(supported_url=GET_SUPPORTED_MODEL_URL,
                                                                                ne_type=ne_type, model_id=model_id))
                    response.raise_for_status()
                except Exception as e:
                    log.logger.debug("Failed to remove model [{0}] for NeType [{1}], exception encountered:: {2}".
                                     format(model_id, ne_type, str(e)))
                    failed_deletes += 1
            if failed_deletes:
                raise EnmApplicationError("Failed to successfully delete {0}/{1} model(s). Please check profile log for"
                                          " further information.".format(failed_deletes, len(supported_models.keys())))
            log.logger.debug("Completed delete model request(s) to ENM, of supported models.")
        else:
            log.logger.debug("No supported models available to delete.")
