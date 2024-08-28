# ********************************************************************
# Name    : LDAP
# Summary : Module for LDAP configuration in ENM. Allows the user to
#           configure LDAP MOs in ENM, generate required XML
#           configuration files, and generate security certificates.
# ********************************************************************

import re
import string
import time
from collections import OrderedDict

import lxml.etree as et

from enmutils.lib import log, arguments, filesystem
from enmutils.lib.exceptions import EnvironError, EnmApplicationError


class LDAP(object):

    LDAP_AUTH_CMD = ('cmedit get {subnetwork},ManagedElement={node_id},SystemFunctions=1,SecM=1,'
                     'UserManagement=1,LdapAuthenticationMethod=1')
    LDAP_STATUS_CMD = "%s,%s" % (LDAP_AUTH_CMD, 'Ldap=1')
    LDAP_SET_CMD = ('cmedit set {subnetwork},ManagedElement={node_id},SystemFunctions=1,SecM=1,UserManagement=1,'
                    'LdapAuthenticationMethod=1,Ldap=1')
    LDAP_SET_FILTER_CMD = ('%s profileFilter=ERICSSON_FILTER' % LDAP_SET_CMD)
    LDAP_ENABLE_CMD = ('cmedit set {subnetwork},ManagedElement={node_id},SystemFunctions=1,'
                       'SecM=1,UserManagement=1,LdapAuthenticationMethod=1 administrativeState={state}')
    LDAP_STATUS_CMD_ON_ALL_NODES = 'cmedit get * LdapAuthenticationMethod'

    SECADM_LDAP_CONFIG_CMD = 'secadm ldap configure -xf file:{file_name}'
    SECADM_LDAP_ISSUE_CMD = 'secadm certificate issue -ct OAM -xf file:{file_name}'
    SECADM_JOB_STATUS_CMD = 'secadm job get -j {job_id}'
    SECADM_UPDATE_CREDENTIALS_CMD = 'secadm credentials update --secureusername notuse-netsim -n {node_id}'

    def __init__(self, user, nodes=None, xml_file_name=None, certificate_file_name=None):
        self.user = user
        self.nodes = nodes
        self.file_name = xml_file_name or "{0}.xml".format(arguments.get_random_string(size=6, exclude=string.digits))
        self.amos_directory = "/home/enmutils/amos"
        self.xml_file_path = "{0}/{1}".format(self.amos_directory, self.file_name)
        self.certificate_name = certificate_file_name or "{0}.xml".format(arguments.get_random_string(size=6))
        self.certificate_path = "{0}/{1}".format(self.amos_directory, self.certificate_name)
        self.job_id = None
        self.ldap_configuration_values = {}

    def configure_ldap_mo_from_enm(self):
        """
        Issue the command to ENM to configure ldap on the nodes provided in the generated file
        """
        if not filesystem.does_dir_exist(self.amos_directory):
            filesystem.create_dir(self.amos_directory)
        self.generate_xml_file(element_dict=OrderedDict([('tlsMode', 'LDAPS'), ('userLabel', 'prova'),
                                                         ('useTls', 'true')]), file_name=self.xml_file_path,
                               file_path=self.xml_file_path, use_fdn=True)
        self.execute_and_evaluate_command(self.SECADM_LDAP_CONFIG_CMD.format(file_name=self.file_name),
                                          file_in=self.xml_file_path,
                                          validation_string='failed')

    def get_ldap_status(self, node):
        """
        Retrieve the LDAP MO status of the supplied node

        :type node: `enm_node.Node`
        :param node: Node to query on enm for its ldap mo status
        """
        self.execute_and_evaluate_command(self.LDAP_STATUS_CMD.format(subnetwork=node.subnetwork, node_id=node.node_id))

    def set_filter_on_ldap_mo(self, node):
        """
        Set the Ericsson filter on the nodes ldap MO

        :type node: `enm_node.Node`
        :param node: Node to query on enm for its ldap mo status
        """
        self.execute_and_evaluate_command(self.LDAP_SET_FILTER_CMD.format(subnetwork=node.subnetwork,
                                                                          node_id=node.node_id))

    def create_and_issue_ldap_certificate(self):
        """
        Generate an xml certificate file, and issue the certificate via secadm command set
        """
        self.generate_xml_file(element_dict={'EntityProfileName': 'DUSGen2OAM_CHAIN_EP'},
                               file_name=self.certificate_name, file_path=self.certificate_path)
        response = self.execute_and_evaluate_command(self.SECADM_LDAP_ISSUE_CMD.format(file_name=self.certificate_name),
                                                     file_in=self.certificate_path)

        self.job_id = response[0].split(' -j ')[-1].split('\'')[0]

    def poll_until_job_complete(self, wait_time=60, timeout=1800):
        """
        Poll for the status of the job, until the job completes

        :type wait_time: int
        :param wait_time: Time in seconds to wait between polling
        :type timeout: int
        :param timeout: Integer of seconds setting the timeout of the polling action

        :raises EnvironError: raised if there is no job id supplied
        """
        if not self.job_id:
            raise EnvironError("Invalid job id provided: {0}".format(self.job_id))
        start = time.time()
        while time.time() <= start + timeout:
            response = self.execute_and_evaluate_command(self.SECADM_JOB_STATUS_CMD.format(job_id=self.job_id))
            if 'COMPLETED' in response[1].split('\t'):
                break
            log.logger.debug("Sleeping for {0} seconds before retrying job status.".format(wait_time))
            time.sleep(wait_time)

    def toggle_ldap_on_node(self, node, state="UNLOCKED"):
        """
        Set the Ericsson filter on the nodes ldap MO

        :type node: `enm_node.Node`
        :param node: Node to query on enm for its ldap mo status
        :type state: str
        :param state: Set the administrative state, UNLOCKED = enabled, LOCKED = disabled
        """
        self.execute_and_evaluate_command(self.LDAP_ENABLE_CMD.format(subnetwork=node.subnetwork, node_id=node.node_id,
                                                                      state=state))

    def update_credentials_on_node(self, node):
        """
        Update the credentials on the node to use the ldap credentials

        :type node: `enm_node.Node`
        :param node: Node to query on enm for its ldap mo status
        """
        self.execute_and_evaluate_command(self.SECADM_UPDATE_CREDENTIALS_CMD.format(node_id=node.node_id))

    def generate_xml_file(self, element_dict=None, file_name=None, file_path=None, use_fdn=False):
        """
        Generate an .xml file

        :type element_dict: dict
        :param element_dict: Dict with 1:1 of key:value of additional or unique elements to be included
        :type file_name: str
        :param file_name: Name of the .xml file to create or default to random name
        :type file_path: str
        :param file_path: Full path of the .xml file to create or default to random name
        :type use_fdn: bool
        :param use_fdn:

        :raises EnvironError: raised if the xml creation fails
        """
        file_name = file_name or arguments.get_random_string(size=8, exclude=string.digits)
        enmutils_dir = "/home/enmutils/amos"
        file_path = file_path or "{0}/{1}".format(enmutils_dir, file_name)
        node_fdn = 'NodeFdn'
        if use_fdn:
            node_fdn = 'nodeFdn'
        if not filesystem.does_dir_exist(enmutils_dir):
            filesystem.create_dir(enmutils_dir)
        root = et.Element('Nodes')
        for node in self.nodes:
            item = et.SubElement(root, 'Node')
            et.SubElement(item, node_fdn).text = node.node_id if not use_fdn else "NetworkElement={0}".format(node.node_id)
            for key, value in element_dict.iteritems():
                et.SubElement(item, key).text = value
        try:
            et.ElementTree(root).write(file_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')
            log.logger.debug('Successfully created {0} file.'.format(file_path))
        except Exception as e:
            raise EnvironError('Failed to create {0} file. Response: {1}'.format(file_name, e.message))

    def execute_and_evaluate_command(self, cmd, validation_string=None, file_in=None):
        """
        Executes the given command, and validates against the given string

        :type cmd: str
        :param cmd: Command to execute
        :type validation_string:
        :param validation_string: String to search for within the returned response
        :type file_in: str
        :param file_in: Path to the file to be attached to the command

        :raises EnvironError: raised if the command is not successful
         :raises EnmApplicationError: if there is no output from the command

        :rtype: list
        :return: List of values returned from the command execution
        """
        response = self.user.enm_execute(cmd, file_in=file_in)
        if not response.get_output():
            raise EnmApplicationError('Command Execution, returned no response.')
        if any(re.search(r'({0}|error|^[0]\sinstance)'.format(validation_string), line, re.I) for line in response.get_output()):
            raise EnvironError('Command [{0}] execution failed. Response: {1}'.format(cmd, response.get_output()))
        log.logger.debug('Successfully executed: [{0}].'.format(cmd))
        return response.get_output()
