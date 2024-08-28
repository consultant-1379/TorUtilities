import re
import json
import logging
from threading import Lock

from bs4 import BeautifulSoup
from requests import Session, packages, HTTPError

logger = logging.getLogger(__name__)

RELEASE_FEM = "https://fem21s11-eiffel004.eiffel.gic.ericsson.se:8443/jenkins/job/TorUtilities_Release/"
FEM_URL = "https://fem21s11-eiffel004.eiffel.gic.ericsson.se:8443/jenkins/j_acegi_security_check"
FEM_HEADERS = {
    'Host': 'fem21s11-eiffel004.eiffel.gic.ericsson.se:8443',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Content-Length': '76',
    'Origin': 'https://fem21s11-eiffel004.eiffel.gic.ericsson.se:8443',
    'Connection': 'keep-alive',
    'Referer': 'https://fem21s11-eiffel004.eiffel.gic.ericsson.se:8443/jenkins/login?from=/jenkins/',
    'Upgrade-Insecure-Requests': 1
}
CIFWK_URL = "https://ci-portal.seli.wh.rnd.internal.ericsson.com/{0}"
USERNAME = None
PASSWORD = None
LOGIN = False


def _init_logger():
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler = logging.FileHandler('/var/log/enmutils/CIFWKSession.log')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


try:
    packages.urllib3.disable_warnings()
except AttributeError:
    pass  # requests 1.1.0 does not have this feature


class CIFWKSession(Session):
    """
    Session that uses the login / logout endpoints to authenticate
    """
    BASE_URL = CIFWK_URL
    URL = BASE_URL.format('login/')
    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': URL
    }

    def __init__(self, username, password, enm_drop=None, rpm_version=None):
        """
        Init method for session object

        :type username: str
        :param username: User to login
        :type password: str
        :param password: Password for the login
        :type enm_drop: str
        :param enm_drop: The ENM drop number of deliver to
        :type rpm_version: str
        :param rpm_version: The utils rpm version number e.g 4.49.8
        """
        super(CIFWKSession, self).__init__()
        self.username = username
        self.password = password
        global USERNAME, PASSWORD
        USERNAME = self.username
        PASSWORD = self.password
        _init_logger()
        self.enm_drop = enm_drop or get_enm_drop()
        self.rpm_version = rpm_version or get_last_rpm_version()
        self._request_lock = Lock()
        self.builds = get_all_previous_builds(self.rpm_version)

    def get_token(self):
        """
        Gets CSRF token to be used for the login
        """
        page = self.get(self.URL)
        soup = BeautifulSoup(page.content, "lxml")
        tag = soup.find('input', attrs={'type': 'hidden', 'name': 'csrfmiddlewaretoken'})
        return tag.encode('utf-8').split('value="')[1].split('"/>')[0]

    def open_session(self):
        """
        Opens a session.
        """
        login_data = {
            'username': self.username,
            'password': self.password,
            'csrfmiddlewaretoken': self.get_token(),
            'ciportal_login': ''
        }
        response = self.post(self.URL, data=login_data, headers=self.HEADERS)
        if response.status_code >= 400:
            raise HTTPError("Failed to complete login request, response: {0}".format(response.content))
        msg = 'Login to {0} successful.'.format(self.URL)
        logger.info(msg)

    def close_session(self):
        """
        Close the session
        """
        logger.info('Closing session: ' + str(self))
        self.get(''.join((self.BASE_URL, 'logout')), allow_redirects=True)
        self.cookies.clear_session_cookies()
        self.close()
        logger.info('Session is closed: ' + str(self))

    def post(self, url, data=None, **kwargs):  # pylint: disable=arguments-differ
        """
        Post request
        """
        logger.info('POST called [%s]', url)
        with self._request_lock:
            return super(CIFWKSession, self).post(url, data=data, **kwargs)

    def get(self, url, **kwargs):
        """
        Get request
        """
        logger.info('GET called [%s]', url)
        return super(CIFWKSession, self).get(url, **kwargs)

    def get_jiras_for_jenkins_build(self):
        """
        Filter all the returned 'jiras' and removes NO JIRA...

        :rtype: list
        :return: :List of updated jira references
        """
        rpm_url = self.BASE_URL.format("api/tools/jiravalidation/issue/{0}/")
        all_jiras = []
        for build in self.builds:
            all_jiras.extend(get_rpm_build_jira(build_num=str(build)))
        for jira in all_jiras[:]:
            response = self.get(rpm_url.format(jira))
            if 'invalid' in response.text or "(Support)" in response.text or "(Spike)" in response.text:
                all_jiras.remove(jira)
        return all_jiras

    def get_jira_details_for_email(self):
        """
        Filter all the returned 'jiras' and removes NO JIRA...

        :rtype: list
        :return: :List of updated jira references
        """
        all_jiras = []
        for build in self.builds:
            all_jiras.extend(get_rpm_build_jira(build_num=str(build), full_jira=True))
        return all_jiras

    def _generate_jira_list_of_dict(self):
        """
        Generate the list of jiras to be validated

        :rtype: list
        :return: List of jiras strings
        """
        jiras = self.get_jiras_for_jenkins_build()
        jira_dict_list = []
        for jira in jiras:
            jira_dict_list.append({"issue": jira})
        return jira_dict_list

    def deliver_rpm(self):
        """
        Build the payload and make the POST request to the delivery queue

        :raises HTTPError: raised if the Post command fails

        :return: Response code based on the success or failure of the operation
        :rtype: int
        """
        jiras = self._generate_jira_list_of_dict()
        if not jiras:
            logger.info('No valid jiras for specified rpm, cannot deliver rpm without valid jira reference.')
            return 0
        data = {
            "groupId": "",
            "drop": "ENM:{0}".format(self.enm_drop),
            "comment": "",
            "team": "BladeRunners",
            "missingDep": False,
            "warning": [""],
            "items": [{
                "packageName": "ERICtorutilities_CXP9030570",
                "version": self.rpm_version,
                "pkgTeams": "Fortress, BladeRunners"
            }],
            "jiraIssues": jiras,
            "kgb_published_reason": ""
        }
        response = self.post(CIFWK_URL.format('addDeliveryGroup/'), data=json.dumps(data))
        if response.status_code >= 400 or "ERROR" in response.content:
            raise HTTPError("Failed to complete POST request, response: {0}".format(response.content))
        if response.status_code == 302 and 'Login' in response.content:
            logger.info("Failed to complete POST request, redirected to login.")
            return 0
        logger.info("Successfully completed POST request, response: %s", response.content)
        return response.status_code


def get_url_content(url, login=False):
    """
    Parses the provided URL into a BeautifulSoup object


    :param url: Url to be scraped
    :type url: str
    :param login: Boolean indicating if the request needs to login into the FEM first
    :type login: bool

    :rtype: BeautifulSoup
    :return: Soup object created from parsing a url
    """
    logger.info("Attempting to retrieve content of {}.".format(url))
    session = Session()
    global LOGIN
    if login and not LOGIN:
        request_data = "j_username={username}&j_password={password}&from=%2Fjenkins%2F&Submit=Sign+in".format(
            username=USERNAME, password=PASSWORD)
        response = session.post(FEM_URL, data=request_data, headers=FEM_HEADERS)
        if response.status_code < 300:
            LOGIN = True
    page = session.get(url)
    soup = BeautifulSoup(page.content, "lxml")
    return soup


def get_jenkins_soup(rpm_build_num=""):
    """
    Parses the jenkins url and returns the soup object

    :type rpm_build_num: str
    :param rpm_build_num: Release job number to parse

    :rtype: BeautifulSoup object
    :return: Soup object created from parsing the specific url
    """
    release_url = ("{0}{1}".format(RELEASE_FEM, rpm_build_num))
    return get_url_content(release_url, login=True)


def get_last_rpm_version():
    """
    Parses the jenkins release build and retrieves the last rpm number

    :rtype: str
    :return: The last rpm version
    """
    soup = get_jenkins_soup()
    return soup.find_all("div", class_='pane desc indent-multiline')[0].text.split(':')[-1]


def get_last_build_number():
    """
    Parses the jenkins release build and retrieves the last jenkins number

    :rtype: str
    :return: The last jenkins release job number
    """
    soup = get_jenkins_soup()
    return soup.find_all(
        "a", class_="tip model-link inside build-link display-name")[0].text.replace("#", "").split("|")[0].strip()


def get_rpm_build_jira(build_num=None, full_jira=False):
    """
    Parses the jenkins release job for the list of JIRAS

    :type build_num: str
    :param build_num: Release job build number to query
    :type full_jira: bool
    :param full_jira: Option to toggle the returning the complete jira number and ticket title

    :rtype: list
    :return: List of jira string references
    """
    logger.info("Getting build jira details...")
    build_num = build_num or get_build_num_based_on_rpm_version(get_last_rpm_version())
    soup = get_jenkins_soup(build_num)
    list_items = soup.find_all("li", attrs={'class': None})
    valid_items = [item.text.encode('utf-8') for item in list_items if item.text.encode('utf-8').startswith('TORF-')]
    valid_items.extend([item.text.encode('utf-8') for item in list_items if
                        item.text.encode('utf-8').startswith('RTD-')])
    if full_jira:
        return [jira.replace("\n", "").replace("(detail)", "").strip() for jira in set(valid_items)]
    # Update to match tickets once the current range is exceeded
    return [re.match(r'RTD-[0-9]*|TORF-[0-9]*', _).group() for _ in set(valid_items)]


def get_enm_drop():
    """
    Queries CIFWK url for the latest drop number

    :rtype: str
    :return: ENM drop number
    """
    b = get_url_content(CIFWK_URL.format('api/product/ENM/latestdrop/'))
    return b.find('p').contents[0].split(':')[-1].replace('}', '').replace("\"", '')


def get_build_num_based_on_rpm_version(rpm_version):
    """
    Get the build number based on the supplied rpm version

    :type rpm_version: str
    :param rpm_version: The rpm version in format int.int.int to discover the build number of

    :raises RuntimeError: raised if supplied rpm number does not match jenkins

    :rtype: int
    :return: The build number matching the rpm
    """
    def _check_for_rpm(build_num):
        soup = get_jenkins_soup(build_num)
        soup_text = getattr(soup.find('h1', class_='build-caption page-headline'), 'text', None)
        return soup_text.split('|')[-1].split('(')[0].strip() if soup_text else None

    count = 0
    while count < 50:  # Jenkins job keeps up to 50
        last_build = int(get_last_build_number()) - count
        if rpm_version == _check_for_rpm(last_build):
            if not last_build:
                continue
            return last_build
        count += 1
    raise RuntimeError("Failed to determine build identity for rpm: {0}, please ensure rpm version is correct "
                       "and available.".format(rpm_version))


def get_all_previous_builds(rpm):
    """
    Retrieve a list the previous Rpm's still held by jenkins

    :type rpm: str
    :param rpm: Rpm number to start from

    :rtype: list
    :return: List of found rpm versions
    """
    undelivered_rpms = get_last_undelivered_rpms(rpm)
    builds = []
    for undelivered in undelivered_rpms:
        try:
            build = get_build_num_based_on_rpm_version(undelivered)
            builds.append(build)
        except RuntimeError:
            continue
    return builds


def check_if_undelivered_rpm(rpm):
    """
    Check if the rpm is already delivered

    :type rpm: str
    :param rpm: Rpm number to start from

    :rtype: str
    :return: Str value for undelivered rpms
    """
    soup = get_url_content(CIFWK_URL.format(
        "ENM/isoVersionList/ERICtorutilities_CXP9030570/{rpm}/None/rpm/".format(rpm=rpm)))
    soup_search = soup.find("div", attrs={'id': 'iso-text'})
    if soup_search and 'has not been included in any ISO Build' in soup_search.text:
        return soup_search.text


def check_if_delivered_rpm(rpm):
    """
    Check if the rpm is already delivered

    :type rpm: str
    :param rpm: Rpm number to start from

    :rtype: str
    :return: Str value for delivered rpm
    """
    soup = get_url_content(CIFWK_URL.format(
        "ENM/isoVersionList/ERICtorutilities_CXP9030570/{rpm}/None/rpm/".format(rpm=rpm)))
    soup_search = soup.findAll("table", class_="artifact-table")
    if soup_search:
        return soup_search[0].findAll('td')[2].text.encode('utf-8')


def get_last_undelivered_rpms(rpm):
    """
    Get the list of undelivered rpms

    :type rpm: str
    :param rpm: Rpm number to start from

    :rtype: list
    :return: List of the rpms that contain a not delivered div
    """
    undelivered_rpms, last_rpms = [], []
    while check_if_undelivered_rpm(rpm):
        undelivered_rpms.append(rpm)
        rpm, last_rpms = reduce_rpm_number_by_one(rpm, last_rpms)
    return undelivered_rpms


def get_last_delivered_rpm(rpm, username, password):
    """
    Get the last delivered rpm to check the sprint and rpm number


    :param rpm: Rpm number to start from
    :type rpm: str
    :param username: User who will login into the FEM
    :type username: str
    :param password: Password of the user who will login into the FEM
    :type password: str

    :rtype: tuple
    :return: Tuple of the rpm that was delivered, and the sprint
    """
    global USERNAME, PASSWORD
    USERNAME, PASSWORD = username, password
    delivered_rpm, last_rpms = [], []
    while not delivered_rpm:
        result = check_if_delivered_rpm(rpm)
        if result:
            value = (rpm, result)
            delivered_rpm.append(value)
        rpm, last_rpms = reduce_rpm_number_by_one(rpm, last_rpms)
    return delivered_rpm


def reduce_rpm_number_by_one(rpm, last_rpms=None):
    """
    Work the last rpm if straight forward reduction, or query for the previous based on all found


    :param rpm: Rpm number to start from
    :type rpm: str
    :param last_rpms: List of the last rpms built if available
    :type last_rpms: list

    :rtype: str
    :return: The rpm version number
    """
    start, middle, end = rpm.split('.')
    if int(end) > 1:
        end = int(end) - 1
        return '{0}.{1}.{2}'.format(start, middle, end), last_rpms
    else:
        recent_rpms = get_last_rpm_versions() if not last_rpms else last_rpms
        if rpm not in recent_rpms:
            recent_rpms = insert_missing_rpm_version(rpm, recent_rpms)
        for i, recent_rpm in enumerate(recent_rpms):
            if recent_rpm == rpm:
                return recent_rpms[i + 1], last_rpms


def get_last_rpm_versions():
    """
    Parses the jenkins release build and retrieves the last rpm numbers available

    :rtype: list
    :return: The list of the last rpm versions
    """
    soup = get_jenkins_soup()
    found_rpms_strings = soup.find_all("a", class_='build-link')
    found_rpms = []
    for _ in found_rpms_strings:
        link_text = str(_.text)
        if link_text[0].isdigit():
            found_rpms.append(link_text.split("|")[-1].strip())
    return found_rpms


def insert_missing_rpm_version(rpm, recent_rpms):
    """
    Add the rpm version, if the release did not build correctly and it is not included in the recent list

    :param rpm: RPM version we intend to deliver
    :type rpm: str
    :param recent_rpms: List of the recently built RPM
    :type recent_rpms: list

    :returns: List of recent rpm versions
    :rtype: list
    """
    start, middle, end = rpm.split('.')
    for i, recent_rpm in enumerate(recent_rpms):
        recent_start, recent_middle, recent_end = recent_rpm.split('.')
        if start == recent_start and middle == recent_middle and int(end) + 1 == int(recent_end):
            recent_rpms.insert(i + 1, rpm)
    return recent_rpms
