# ********************************************************************
# Name    : ALEX DOC
# Summary : Ericsson CPI Library (ELEX) functionality.
#           Visit documentation url specified.
# ********************************************************************

from enmutils.lib import log

# This is a list of some documentation pages user will randomly open.
# These do not need to change.
DOC_SERVICE = 'elex'
URLS_TO_VISIT = [
    '/{0}?id=870&fn=elexmain.html&ST=START'.format(DOC_SERVICE),
    '/{0}?ID=870&FN=1_1551-LXA1191929Uen.G.html'.format(DOC_SERVICE),
    '/{0}?ID=870&FN=1_1553-LXA1191929Uen.B.html'.format(DOC_SERVICE),
    '/{0}?ID=870&FN=1_15519-LXA1191929Uen.F.html'.format(DOC_SERVICE),
]


def get_doc_url(user, url, doc_service='ELEX'):
    """
    Visit documentation url specified
    :param user: `lib.enm_user.User` instance:
    :type user: `lib.enm_user_2.User`
    :param url: str page to visit:
    :type url: str
    :param doc_service: Current branding
    :type doc_service: str
    :return: response object
    :rtype: `enmscripting.Response`
    """
    response = user.get(url, verify=False)

    if '<title>{0} Error Message</title>'.format(doc_service.upper()) in response.text.encode('utf-8'):
        log.logger.debug('FAILED URL: {0}'.format(url))
        # First have to remove the response as from ui_responses as it will have been logged as a success
        request_key = (response.request.method, response.request.url)
        if request_key in user.ui_response_info:
            user.ui_response_info[request_key][True] -= 1
            response.status_code = 599
            response._content = 'ENMUtils response - URL: {0} not found in the {1} library'.format(url, doc_service.upper())
            user.ui_response_info[request_key][False] += 1
            user.ui_response_info[request_key]["ERRORS"] = {response.status_code: response}

    return response
