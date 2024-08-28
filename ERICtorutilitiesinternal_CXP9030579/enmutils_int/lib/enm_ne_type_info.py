# ********************************************************************
# Name    : ENM NE Type Info
# Summary : Used by the NETWORK tool.
#           Replacement for functionality previously managed by
#           Production module, Model Info, queries ENM for the list
#           of ENM NEType models, can be filtered to specify particular
#           NETypes or all - information is cached in persistence.
# ********************************************************************

import re
from enmutils.lib import log, persistence
from enmutils.lib.exceptions import ScriptEngineResponseValidationError

MODEL_INFO_KEY = "enm-model-info-key"


def get_enm_supported_models(user):
    """
    Query ENM for the list of supported NE Types

    :param user: Enm user who will perform the query
    :type user: `enm_user_2.User`

    :raises ScriptEngineResponseValidationError: raised if the ENM CLI commands fails

    :return: Dictionary containing all ENM supported model info
    :rtype: dict
    """
    supported_models = persistence.get(MODEL_INFO_KEY)
    if not supported_models:
        cmd = "cmedit describe --netype --all -t"
        log.logger.debug("Querying ENM for list of supported NE Types.")
        response = user.enm_execute(cmd)
        if not response.get_output() or any(re.search(r'(error)', line, re.I) for line in response.get_output()):
            raise ScriptEngineResponseValidationError("Exception encountered: {0}".format(
                ','.join(response.get_output())), response=response)
        supported_models = response.get_output()[1:-3]
        persistence.set(MODEL_INFO_KEY, supported_models, 86400, log_values=False)
        log.logger.debug("Completed querying ENM for list of supported NE Types.")
    return sorted_model_info(supported_models)


def sorted_model_info(supported_models):
    """
    Sorted model response from ENM by NEType

    :param supported_models: List of ENM Supported models
    :type supported_models: list

    :return: Dictionary containing all ENM supported model info
    :rtype: dict
    """
    supported_models_dict = {}
    for _ in supported_models:
        values = _.encode('utf-8').split('\t')
        ne_type = values[0]
        if ne_type not in supported_models_dict.keys():
            supported_models_dict[ne_type] = []
        supported_models_dict[ne_type].append(values)
    return supported_models_dict


def describe_ne_type(user, models=None):
    """
    Returns all NE Type model info or filters upon those requested

    :param models: List of requested ENM models
    :type models: list
    :param user: Enm user who will perform the query
    :type user: `enm_user_2.User`

    :return: Tuple containing the dictionary of NE models, any invalid models supplied
    :rtype: tuple
    """
    supported_models_dict = get_enm_supported_models(user=user)
    invalid_models = []
    if not models:
        return supported_models_dict, invalid_models
    else:
        required_models = {}
        for model in models:
            if supported_models_dict.get(model):
                required_models[model] = supported_models_dict.get(model)
            else:
                invalid_models.append(model)
        return required_models, invalid_models


def print_supported_node_info(user, models=None):
    """
    Prints to the console information of all supported NE types on ENM

    :type: models: list
    :param: models: List of NeTypes to retrieve the Model information of
    """
    node_info_dict, invalid_models = describe_ne_type(user, models)
    log.logger.info(log.green_text(log.underline_text("\nENM SUPPORTED NETWORK ELEMENT INFO\n")))
    for ne_type in node_info_dict.keys():
        log.logger.info("\n\t{0}\n".format(log.purple_text(ne_type)))
        for _ in node_info_dict.get(ne_type):
            ne_type, ne_release, product_identity, revision, mim_name, mim_version, model_id = _
            log.logger.info("\t NE TYPE          : {0}".format(ne_type))
            log.logger.info("\t NE RELEASE       : {0}".format(ne_release))
            if product_identity and product_identity != '-':
                log.logger.info("\t SOFTWARE VERSION : {0}".format(product_identity))
            log.logger.info("\t MIM NAME         : {0}".format(mim_name))
            log.logger.info("\t MIM VERSION      : {0}".format(mim_version))
            log.logger.info("\t MODEL ID         : {0}".format(model_id))
            if revision and revision != '-':
                log.logger.info("\t REVISION         : {0}".format(revision))
            log.logger.info("")
    if invalid_models:
        log.logger.info(log.red_text("\t NO ENM SUPPORTED MODEL INFO FOR NE TYPES [{0}].\n\t Please confirm NE TYPE is "
                                     "supported by ENM, NE TYPES are case sensitive.\n"
                                     "".format(", ".join(invalid_models))))
