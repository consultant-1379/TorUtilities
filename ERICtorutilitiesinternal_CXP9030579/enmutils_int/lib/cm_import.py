# ********************************************************************
# Name    : CM Import
# Summary : Primary module for interacting with Cm Import/Activation
#           over the CLI and generating the importable files. Allows
#           for creation, query, download, activation, undo, and
#           deletion of CM Configurations and Imports.
# ********************************************************************

import collections
import datetime
import os
import re
import time
from itertools import cycle

import lxml.etree as et
from dateutil.parser import parse
from retrying import retry

from enmutils.lib import filesystem, log, timestamp
from enmutils.lib.exceptions import (UndoPreparationError, HistoryMismatch,
                                     CMImportError, GetTotalHistoryChangesError, CmeditCreateSuccessfulValidationError,
                                     EnmApplicationError, EnvironError)
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.cm_import_over_nbi import CmImportOverNbiV1, CmImportOverNbiV2, UndoOverNbi
from enmutils_int.lib.ddp_info_logging import update_cm_ddp_info_log_entry
from enmutils_int.lib.enm_config import EnmJob

FILE_BASE_LOCATION = os.path.join('/', 'home', 'enmutils', 'cmimport')
IMPORT_FILES_LOCATION = os.path.join(FILE_BASE_LOCATION, 'cmimport_data', 'import_profile_recoveries')
XN = 'xn'
UN = 'un'
GN = 'gn'
ES = 'es'
UTRAN_NRM_XSD = 'utranNrm.xsd'
GERAN_NRM_XSD = 'geranNrm.xsd'
CONFIG_DATA_XSD = 'configData.xsd'
GENERIC_NRM_XSD = 'genericNrm.xsd'
ERICSSON_SPECIFIC_ATTRIBUTES = 'EricssonSpecificAttributes.14.02.xsd'
VS_DATA_FORMAT_VERSION = 'vsDataFormatVersion'
VS_DATA = 'vsData'
VS_DATA_TYPE = 'vsDataType'
VS_DATA_CONTAINER = 'VsDataContainer'
ATTRIBUTES = 'attributes'
FILE_FORMAT_VERSION_VALUE = '32.615 V4.5'
FILE_HEADER = 'fileHeader'
FILE_FOOTER = 'fileFooter'
CONFIG_DATA = 'configData'
ERICSSON = 'Ericsson'
UNDEFINED = 'Undefined'
UPDATE = 'update'
DELETE = 'delete'
CREATE = 'create'
SET = 'set'
DYNAMIC = 'dynamic'
THREE_GPP = '3GPP'


class CMImportXml(object):
    """
    Creates the XML file to be used in CM import with 3GPP file type
    """

    NSMAP = {
        None: CONFIG_DATA_XSD,
        XN: GENERIC_NRM_XSD,
        GN: GERAN_NRM_XSD,
        UN: UTRAN_NRM_XSD,
        ES: ERICSSON_SPECIFIC_ATTRIBUTES
    }

    def __init__(self, mos, outfile_path):
        """
        :param mos: dict, tree structure of the managed objects
        :type mos: dict
        :param outfile_path: string, path to the xml file
        :type outfile_path: str
        """

        self.mos = mos
        self.outfile_path = outfile_path

    def save(self):
        """
        Writes the XML file to its outfile path
        """

        element_tree = et.ElementTree(self.build_xml())
        with open(self.outfile_path, 'w') as f:
            element_tree.write(f, encoding='utf-8', xml_declaration=True)

    def _sub_element(self, parent, tag, namespace=None, text=None, **kwargs):

        """
        Prepares the element of the XML file, based on the information passed to the method

        :param parent: the root element
        :type parent: xml.etree._Element
        :param tag: tag in the XML file
        :type tag: str
        :param namespace: namespace in the XML file
        :type namespace: str
        :param text: text to be written in the XML element
        :type text: str
        :param kwargs: list
        :type kwargs: any
        :return: element of the XML file
        :rtype: xml.etree._Element
        """

        tag = '{%s}%s' % (self.NSMAP[namespace], tag) if namespace else tag
        element = et.SubElement(parent, tag, **kwargs)
        if text is not None:
            element.text = str(text)
        return element

    def build_xml(self):
        """
        Builds the XML tree structure
        :return: root, the root of the XML file
        :rtype: str
        """

        root = et.Element('bulkCmConfigDataFile', nsmap=self.NSMAP)
        self._sub_element(
            root, FILE_HEADER, fileFormatVersion=FILE_FORMAT_VERSION_VALUE, vendorName=ERICSSON)
        config_data = self._sub_element(
            root, CONFIG_DATA, dnPrefix=UNDEFINED)

        for subnetwork, nodes in self.mos.iteritems():
            element_name, element_id = subnetwork
            sub_element = self._sub_element(
                config_data, element_name, namespace=XN, id=str(element_id))
            for node in nodes:
                self._build_node_xml(sub_element, node.mos)

        self._sub_element(root, FILE_FOOTER, dateTime=datetime.datetime.now().isoformat('T'))
        return root

    def _build_node_xml(self, parent, data, count=0):
        """
        Build the node information in the XMl file

        :param parent: lxml.etree._Element, the root element
        :type parent: lxml.etree._Element
        :param data: node information used to build the XML
        :type data: mapping
        :param count: int
        :type count: int

        """

        for element_key, remaining in data.iteritems():
            if isinstance(remaining, collections.Mapping):
                mo_name, mo_id = element_key
                if count < 1:
                    sub_element = self._build_xn_element(parent, mo_name, mo_id)
                    count += 1
                else:
                    sub_element = self._build_mo_data_container(parent, mo_name, mo_id)

                self._build_node_xml(sub_element, remaining, count=count)
            else:
                for mo_obj in remaining:
                    self._build_mo_data_container_with_attrs(parent, mo_obj)

    def _build_mo_data_container(self, parent, mo_name, mo_id):
        """
        Builds the data container of the XML for the MO

        :param parent: lxml.etree._Element, the root element
        :type parent: xml.etree._Element
        :param mo_name: string, name of the MO
        :type mo_name: str
        :param mo_id: string, id of the MO
        :type mo_id: str
        :return: data container for the MO in the XML file
        :rtype: xml.etree._Element
        """

        sub_element = self._build_element_datacontainer(parent, mo_id=mo_id)
        attributes_container = self._build_attributes(sub_element, mo_name=mo_name)
        self._build_es_data(attributes_container, mo_name=mo_name)
        return sub_element

    def _build_mo_data_container_with_attrs(self, parent, mo_obj):
        """
        Build the data container of the XML for the MO with its attributes

        :param parent: lxml.etree._Element, the root element
        :type parent: lxml.etree._Element
        :param mo_obj: enmutils_int.lib.enm_mo.EnmMo object
        :type mo_obj: enmutils_int.lib.enm_mo.EnmMo

        :return: MO data container with attributes
        :rtype: xml.etree._Element
        """

        data_container = self._build_element_datacontainer(parent, mo_id=mo_obj.mo_id, modifier=self.MODIFIER)
        mo_name = 'context' if mo_obj.name in ['context=local', 'context=mgmt'] else mo_obj.name
        attributes_container = self._build_attributes(data_container, mo_name=mo_name)
        es_data_container = self._build_es_data(attributes_container, mo_name=mo_name)
        self._build_mo_attrs(es_data_container, mo_obj)
        return data_container

    def _build_xn_element(self, parent, mo_name, mo_id):
        """
        Builds the XN element of the XML

        :param parent: lxml.etree._Element, the root element
        :type parent: xml.etree._Element
        :param mo_name: string, name of the MO
        :type mo_name: str
        :param mo_id: string, id of the MO
        :type mo_id: str
        :return: xn element, xn is defined in the namespace
        :rtype: xml.etree._Element
        """

        return self._sub_element(
            parent, mo_name, namespace=XN, id=mo_id)

    def _build_element_datacontainer(self, parent, mo_id, **kwargs):
        """
        Builds the data container of the XML for the element

        :param parent: lxml.etree._Element, the root element
        :type parent: xml.etree._Element
        :param mo_id: string, id of the MO
        :type mo_id: str
        :param kwargs: list
        :type kwargs: list
        :return: the data container in the XML element
        :rtype: xml.etree._Element
        """
        return self._sub_element(
            parent,
            VS_DATA_CONTAINER,
            namespace=XN,
            id=mo_id, **kwargs)

    def _build_attributes(self, parent, mo_name):
        """
        Builds the attributes for the element

        :param parent: lxml.etree._Element, the root element
        :type parent: xml.etree._Element
        :param mo_name: string, name of the MO
        :type mo_name: str
        :return: the attributes for the element in the XML file
        :rtype: xml.etree._Element
        """

        attributes = self._sub_element(parent, ATTRIBUTES, namespace=XN)
        self._sub_element(
            attributes, VS_DATA_TYPE,
            text=VS_DATA + mo_name,
            namespace=XN)
        self._sub_element(
            attributes, VS_DATA_FORMAT_VERSION,
            text='EricssonSpecificAttributes',
            namespace=XN)
        return attributes

    def _build_es_data(self, parent, mo_name):
        """
        Builds the ES data

        :param parent: lxml.etree._Element, the root element
        :type parent: xml.etree._Element
        :param mo_name: string, name of the MO
        :type mo_name: str
        :return: es data, es is defined in the namespace
        :rtype: xml.etree._Element
        """

        return self._sub_element(parent, 'vsData%s' % mo_name, namespace=ES)

    def _build_mo_attrs(self, parent, mo_obj):
        """
        Builds the XML element for the MO, for the MO name and value attributes

        :param parent: lxml.etree._Element, the root element
        :type parent: xml.etree._Element
        :param mo_obj: enmutils_int.lib.enm_mo.EnmMo object
        :type mo_obj: enmutils_int.lib.enm_mo.EnmMo
        """

        for attr_name, attr_value in self._get_mo_attrs(mo_obj).iteritems():
            self._sub_element(parent, attr_name, text=attr_value)


class CMImportUpdateXml(CMImportXml):
    """
    Creates the XML for a CM import with 'update' modifier
    """

    MODIFIER = UPDATE

    def __init__(self, mos, outfile_path, values):
        """
        :param mos: managed objects
        :type mos: dict
        :param outfile_path: path the XML file is saved to
        :type outfile_path: str
        :param values: dictionary containing MO and tuple of attribute name, attribute value to be modified
        :type values: dict
        """

        super(CMImportUpdateXml, self).__init__(mos, outfile_path)
        self.values = values

    def _get_mo_attrs(self, mo_obj):
        """
        :return: dictionary of MO attributes
        :rtype: dict
        """
        attributes = self.values[mo_obj.name]
        attr_dict = {}

        if isinstance(attributes, list):
            for attr_name, attr_value in attributes:
                attr_dict.update({attr_name: attr_value})
            return attr_dict

        else:
            attr_dict = dict([attributes])
            return attr_dict


class CmImportCreateDeleteXml(CMImportXml):
    """
    Create an XML with 'create' or 'delete' modifier
    """

    def _get_mo_attrs(self, mo_obj):
        return mo_obj.attrs


class CMImportDeleteXml(CmImportCreateDeleteXml):
    """
    Set the modifier to 'delete' to create the XML
    """

    MODIFIER = DELETE


class CMImportCreateXml(CmImportCreateDeleteXml):
    """
    Set the modifier to 'create' to create the XML
    """

    MODIFIER = CREATE


class CmImportLive(EnmJob, CmImportOverNbiV1, CmImportOverNbiV2):
    """
    Performs a Live Import through the CLI or over NBI, depending on the interface
    """

    IMPORT_CMD = 'cmedit import -f file:{file_name} {file_type} -t {config_name} {flow} {error_handling}'
    STATUS_CMD = 'cmedit import -st -j {id}'
    JOB_TEMP_FILE_PATH = None
    PREVIOUS_ACTIVATION_EXISTS = False
    IMPORT_HISTORY = 'config history -s Live --importjob {id}'
    ACTIVATION_HISTORY = 'config history -s Live --activationjob {id}'

    def __init__(self, nodes, template_name, flow, file_type, config_name=None,
                 expected_num_mo_changes=None, user=None, timeout=None, filepath=None, name=None, interface=None,
                 error_handling=None, undo_id=None):
        """
        :param nodes: nodes to use for the import
        :type nodes: dict or list
        :param template_name: string, name of the file
        :type template_name: str
        :param flow: import flow to follow
        :type flow: str
        :param file_type: type of file to import, can be 3GPP or Dynamic
        :type file_type: str
        :param config_name: name of config file to be used if Non-Live import
        :type config_name: str
        :type expected_num_mo_changes: int
        :param expected_num_mo_changes: total number of MO changes expected to be recorded in history
        :param user: user object
        :type user: enmutils.lib.enm_user_2.User
        :param timeout: time in seconds for the import to complete
        :type timeout: int
        :param filepath: path to the filesystem where the file will be written
        :type filepath: str
        :param name: string, name for CM import, config will be generated with the same name
        :type name: str
        :param interface: import can be carried out through the CLI or over NBI
        :type interface: str
        :param error_handling: The execution policy with which to start the import job
        :type error_handling: str
        :param undo_id: the id of the undo job
        :type undo_id: int
        """

        filepath = filepath or os.path.join(FILE_BASE_LOCATION, template_name)
        super(CmImportLive, self).__init__(user, filepath=filepath, timeout=timeout)
        self.nodes = nodes
        self.template_name = template_name
        self.flow = flow
        self.file_type = file_type
        self.interface = interface
        self.config_name = 'Live' if not config_name else config_name
        self.expected_num_mo_changes = expected_num_mo_changes
        self.name = name if name else config_name
        self.detailed_validation = True if isinstance(self, (CmImportDeleteLive, CmImportCreateLive)) else False
        self.undo_over_nbi = UndoOverNbi(user=self.user, name=self.name, file_type=self.file_type)
        self.error_handling = error_handling
        self.skip_history_check = False
        self.undo_id = undo_id

    @property
    def nodes_tree(self):
        """
        :return: tree: tree structure of the subnetwork and its nodes
        :rtype: dict
        """

        tree = {}
        for node in self.nodes:
            subnetwork = (node.subnetwork_id if "Europe" not in node.subnetwork else
                          "Europe,{0}".format(node.subnetwork.split("SubNetwork=Europe,")[-1]))
            tree.setdefault(('SubNetwork', subnetwork), []).append(node)
        return tree

    def prepare_xml_file(self, **kwargs):
        """
        Prepare the XML file to be imported

        """
        log.logger.debug("Attempting to CREATE XML file: {0}, kwargs: {1}".format(self.filepath, kwargs))
        self.XML_CLASS(mos=self.nodes_tree, outfile_path=self.filepath, **kwargs).save()
        log.logger.debug("Successfully CREATED XML file: {0}".format(self.filepath))

    def prepare_dynamic_file(self, mo_values=None):
        """
        Prepare the dynamic text file to be imported

        :param mo_values: dictionary with MO name and the attribute and its value
                            e.g. {'GeranCellRelation': ('isHoAllowed', 'false')}
        :type mo_values: dict
        :raises EnvironError: if mo has no attribute 'fdn'
        """
        nodes_tree = self.nodes_tree
        log.logger.debug("Attempting to CREATE dynamic text file: {0}".format(self.filepath))

        with open(self.filepath, 'w+') as f:
            for nodes in nodes_tree.itervalues():
                for node in nodes:
                    mo_objects = get_enm_mo_attrs(node)
                    log.logger.debug("Writing attributes to file....")
                    for mo in mo_objects:
                        if hasattr(mo, 'fdn'):
                            self._modify_mo_data(mo, f)
                        else:
                            raise EnvironError("Cannot fetch an attribute 'fdn' for mo : {0}".format(mo))
                        if self.FILE_OPERATION != DELETE:
                            self._write_attribute_values_to_file(mo_values, mo, f)
                    log.logger.debug("Successfully wrote attributes to import file.")

    def _modify_mo_data(self, mo, f):
        """
        Write the required FDN value in the set

        :param mo: EnmMo object
        :type mo: enmutils_int.lib.enm_mo.EnmMo
        :param f: File object to write to
        :type f: BinaryIO
        """
        if "rule-list" in mo.fdn:
            new_fdn = ",".join(mo.fdn.split(',')[0:5] +
                               ["rule-list=ericsson-admin-user-management-1-system-admin"] +
                               ["rule=ericsson-system-ext-1-system-admin"])
            f.write("{0}\nFDN: {1}\n".format(self.FILE_OPERATION, new_fdn))
        else:
            f.write("{0}\nFDN: {1}\n".format(self.FILE_OPERATION, mo.fdn))

    def _write_attribute_values_to_file(self, mo_values, mo, file_obj):
        """
        Set the attribute name and value in the text file

        :param mo_values: dictionary with MO name and the attribute and its value
                            e.g. {'GeranCellRelation': ('isHoAllowed', 'false')}
        :type mo_values: dict
        :param mo: EnmMo object
        :type mo: enmutils_int.lib.enm_mo.EnmMo
        :param file_obj: File object to write to
        :type file_obj: BinaryIO
        """
        line = "{0} : '{1}'\n"
        if self.FILE_OPERATION == SET:
            mo_attr_list = mo_values[mo.name]
            if isinstance(mo_attr_list, list):
                for attribute_value in mo_attr_list:
                    file_obj.write(line.format(attribute_value[0], str(attribute_value[1])))
            else:
                file_obj.write(line.format(mo_attr_list[0], str(mo_attr_list[1])))
        else:
            mo_attr_list = mo.attrs
            for attr_name, attr_value in mo_attr_list.iteritems():
                file_obj.write(line.format(attr_name, str(attr_value)))

    def import_flow(self, history_check=False, undo=False, file_path=None):
        """
        Carries out the import flow of the profile

        :param history_check: boolean, whether or not history check is needed
        :type history_check: bool
        :param undo: boolean, whether or not the profile needs to carry out the undo flow
        :type undo: bool
        :param file_path: path to the config file if needed
        :type file_path: str
        :raises UndoPreparationError: if error encountered during undo
        :return: the id of the undo job
        :rtype: int
        """
        if not history_check:
            log.logger.debug("Setup Import Flow - Best effort to set all attribute to their default"
                             " values - Contains no history check")

        log.logger.debug("Starting Import Flow")

        if undo and self.PREVIOUS_ACTIVATION_EXISTS:
            log.logger.debug("This is an undo import iteration")
            try:
                self.undo_iteration()
                file_path = self._get_undo_file_path()
            except Exception as e:
                raise UndoPreparationError(e)

        self._create(file_in=file_path)

        if history_check and not self.skip_history_check:
            self.PREVIOUS_ACTIVATION_EXISTS = True
            # max delay of 5 seconds to store data in config history RTD-5684
            if (self.name.startswith('cmimport_31') or self.name.startswith('cmimport_32') or
                    self.name.startswith('cmimport_33')):
                time.sleep(2)
            else:
                time.sleep(5)
            self.check_num_history_changes_match_expected(self.expected_num_mo_changes)

        if undo:
            self._remove_undo_config_files()
            self._remove_undo_job()

        log.logger.debug("Successfully completed import flow")

        return self.undo_id

    def _get_undo_file_path(self):
        """
        Call to function to retrieve the file path of the undo configuration file

        :return: path of the undo file
        :rtype: str
        """

        return self.undo_over_nbi.get_undo_config_file_path()

    def _remove_undo_config_files(self):
        """
        Remove all files associated with the undo
        """
        self.undo_over_nbi.remove_undo_config_files()

    def _remove_undo_job(self):
        """
        Remove the UNDO job created to download undo file.
        """
        id_to_undo = self.undo_id
        self.undo_over_nbi.remove_undo_job(self.user, id_to_undo)

    def undo_iteration(self):
        """
        Function called if the import is an undo iteration
        """

        id_to_undo = self.id
        self.undo_id = self.undo_over_nbi.undo_job_over_nbi(id_to_undo)

    def _create(self, file_in=None):
        """
        Wrapper function for create function which performs the import.

        :param file_in: file path passed in of the undo file, if the import is an undo iteration
        :type file_in: str
        :raises CMImportError: if error encountered during the import flow
        """

        log.logger.debug("IMPORTING into config: '{0}'.".format(self.config_name))
        try:
            ts = timestamp.get_human_readable_timestamp()
            profile_name = re.split(r'_[a-zA-z]*$', self.name)[0].upper()
            update_cm_ddp_info_log_entry(profile_name,
                                         "{0} {1} {2}\n".format(ts, profile_name, self.expected_num_mo_changes))
            if self.interface:
                log.logger.debug("IMPORTING via '{0}'.".format(self.interface))
                self.create_over_nbi(file_in=file_in)
            else:
                log.logger.debug("IMPORTING via CLI")
                self.create(file_in=file_in)
        except Exception as e:
            log.logger.debug("ERROR WHEN IMPORTING into {0} through {1}. {2}"
                             .format(self.config_name, self.interface if self.interface else "CLI", e))
            if "Size: 0" in str(e) or "Index: 0" in str(e):
                e = ("{0}.\nImport service has failed to correctly execute or validate import, please check the impexp "
                     "service logs for further information.").format(e)
            raise CMImportError(e)

        log.logger.debug("Successfully IMPORTED into '{0}'.".format(self.config_name))

    def create_over_nbi(self, file_in=None):
        """
        Call the function to begin import over NBI, depending on the interface.
        Interface can be NBIv1 or NBIv2

        :param file_in: file path passed in of the undo file, if the import is an undo iteration
        :type file_in: str

        """

        if self.interface == 'NBIv1':
            self.create_import_over_nbi_v1(file_in)

        else:
            self.create_import_over_nbi_v2(file_in)

    def get_create_command(self):
        """
        :return: the command to create the import
        :rtype: str
        """
        file_type = "--filetype {0}".format(self.file_type) if self.file_type else ""
        flow = '-nc' if self.flow == 'non_live_config1' else ""
        error_handling = "--error node" if self.error_handling else ""
        return self.IMPORT_CMD.format(
            file_name=os.path.basename(self.filepath), file_type=file_type, config_name=self.config_name, flow=flow,
            error_handling=error_handling)

    def get_status_command(self):
        """
        :return: the command to get the status of the import
        :rtype: str
        """
        return self.STATUS_CMD.format(id=self.id)

    def check_num_history_changes_match_expected(self, expected_num_mo_changes):
        """
        Checks that the total changes recorded in history - solar, meet the total number of changes expected.

        :param expected_num_mo_changes: int, total number of changes expected to be recorded in solar
        :type expected_num_mo_changes: int

        :raises HistoryMismatch: if mismatch between expected changes and number of changes retrieved during the history check
        """

        log.logger.debug("Attempting to check if the number of history changes applied to ENM matches the expected: {0}"
                         .format(expected_num_mo_changes))
        try:
            job_id = self.id

            if self.interface:
                total_mo_changes = self.get_total_operations_over_nbi(job_id)

            else:
                # max delay of 5 seconds to store data in config history RTD-5684
                time.sleep(5)
                total_mo_changes = self.get_total_history_changes(job_id)

            if total_mo_changes != expected_num_mo_changes:
                raise HistoryMismatch("HISTORY CHANGES ERROR: No. of actual changes made: '{0}' did not match the "
                                      "required No. of changes: '{1}'".format(total_mo_changes,
                                                                              expected_num_mo_changes))
            else:
                log.logger.debug("HISTORY CHECK successful: No. of changes made: '{0}' matched the required No. of "
                                 "changes: '{1}'".format(total_mo_changes, expected_num_mo_changes))
        except Exception as e:
            log.logger.debug("ERROR WHEN CHECKING IF THE NUMBER OF HISTORY CHANGES APPLIED MATCHED EXPECTED")
            raise HistoryMismatch(e)

        log.logger.debug("Successfully checked the number of history changes applied to ENM")

    def get_total_operations_over_nbi(self, job_id):
        """
        Gets the total number of changes via the NBI.
        Calls the relative function for v1 or v2, depending on the interface.

        :type job_id: int
        :param job_id: job id to be checked
        :rtype: int
        :return: number of changes applied during the import
        :rtype: int

        """
        if self.interface == 'NBIv1':
            changes = self.get_total_history_changes_over_nbi_v1(job_id)

        else:
            changes = self.get_total_history_changes_over_nbi_v2(job_id)

        return changes

    def get_total_history_changes_over_nbi_v2(self, job_id):
        """
        Gets the total number of changes via NBI version 2, by performing a GET request to the SUMMARY_ENDPOINT.

        :type job_id: int
        :param job_id: job id to be checked
        :raises GetTotalHistoryChangesError: if error encountering getting history changes
        :rtype: int
        :returns: number of changes applied
        """

        log.logger.debug("Requesting summary for job id: {id}".format(id=job_id))

        try:
            response_json = self.get_import_job_summary_by_id(job_id)

            total_operations = response_json.get('summary').get('total').get('parsed')
            valid_operations = response_json.get('summary').get('total').get('valid')
            executed_operations = response_json.get('summary').get('total').get('executed')

            log.logger.debug("Successfully retrieved the summary of operations for job id {0}. "
                             "TOTAL: {1}, VALID: {2}, EXECUTED: {3}"
                             .format(job_id, total_operations, valid_operations, executed_operations))

            return executed_operations

        except Exception as e:
            log.logger.debug("ERROR when retrieving history changes for job {0}. {1}".format(job_id, e))

    def get_total_history_changes_over_nbi_v1(self, job_id):
        """
        Gets the total number of changes via NBI version 1, by getting the count of the totalManagedObjects
        Created, Deleted, or Updated, depending on the type of import

        :type job_id: int
        :param job_id: job id to be checked
        :raises GetTotalHistoryChangesError: if error encountering getting history changes
        :rtype: int
        :returns: number of changes
        """

        log.logger.debug("Requesting details for job id: {id}".format(id=job_id))

        try:
            response = self.get_job_details_by_id(job_id)
            total_deleted = response.get('totalManagedObjectDeleted')
            total_created = response.get('totalManagedObjectCreated')
            total_updated = response.get('totalManagedObjectUpdated')
            total_changes = total_deleted + total_created + total_updated

            if total_changes > 0:
                log.logger.debug("Successfully retrieved total changes for job id: {id}".format(id=job_id))
                return total_changes
            else:
                raise GetTotalHistoryChangesError(
                    "ERROR: Could not identify total changes for job {id}".format(id=job_id))

        except Exception as e:
            log.logger.debug("ERROR when retrieving history changes for job {0}. {1}".format(job_id, e))

    def get_total_history_changes(self, job_id):
        """
        Gets the total number of changes actually applied to ENM.

        :type job_id: int
        :param job_id: job id to be checked
        :raises GetTotalHistoryChangesError: if error encountering getting history changes
        :raises Exception: if error encountered trying to retrieve history changes
        :rtype: int
        :returns: number of changes applied
        """

        log.logger.debug(
            "Attempting to get the HISTORY CHANGES for job id: '{0}' ".format(job_id))
        try:
            response_output = self.history(job_id).get_output()
            for entry in reversed(response_output):
                if 'change(s)' in entry:
                    changes = int(entry.split()[0])
                    log.logger.debug("Successfully retrieved HISTORY CHANGES for job id: '{0}' ".format(job_id))
                    return changes
        except Exception:
            log.logger.debug("ERROR WHEN RETRIEVING HISTORY CHANGES FOR JOB ID: '{0}'".format(job_id))
            raise
        else:
            raise GetTotalHistoryChangesError(
                "ERROR COULD NOT IDENTIFY TOTAL CHANGES FROM OUTPUT FOR JOB ID: {0}".format(job_id))

    def history(self, job_id):
        """
        Executes the history command on ENM.

        :type job_id: int
        :param job_id: job id to be checked
        :returns: `enmscripting.Response` object
        :rtype: enmscripting.Response
        :raises Exception: if error encountered when executing the history command
        """

        try:
            return self.user.enm_execute(self.IMPORT_HISTORY.format(id=job_id))
        except Exception as e:
            log.logger.debug(
                "ERROR WHEN EXECUTING THE HISTORY COMMAND ON ENM FOR  JOB ID: '{0}'. Error: '{1}'".format(job_id,
                                                                                                          e.message))
            raise

    def cm_import(self):
        """
        Performs a CM import

        :raises: CMImportError: if unknown file type specified
        """

        if self.file_type == THREE_GPP:
            self.prepare_xml_file()
        elif self.file_type == DYNAMIC:
            self.prepare_dynamic_file()
        else:
            raise CMImportError(
                "Unknown file type has been specified: '{0}'. File type must be 3GPP or dynamic.".format(
                    self.file_type))

        self._create()

    @retry(retry_on_exception=lambda e: isinstance(e, Exception), wait_fixed=60000, stop_max_attempt_number=2)
    def restore_default_configuration_via_import(self):
        """
        Executes the create functionality up to three times as part of recovery option

        :raises e: (Exception) raised if the create fails after the second attempt
        """
        try:
            self._create()
        except Exception as e:
            log.logger.debug("Failed to restore default configuration, error encountered: [{0}]".format(str(e)))
            raise e

    def delete(self):
        """
        Removes file locally
        :raises Exception: if exception when removing file

        """

        log.logger.debug("Attempting to REMOVE file: {0}".format(self.filepath))
        try:
            os.remove(self.filepath)
        except Exception:
            log.logger.debug("ERROR REMOVING FILE: {0}".format(self.filepath))
            raise
        log.logger.debug("Successfully REMOVED file: {0}".format(self.filepath))

    def _teardown(self):
        self.delete()


class CmImportUpdateLive(CmImportLive):
    """
    Perform a Live CM import which modifies the MO values
    """
    XML_CLASS = CMImportUpdateXml
    FILE_OPERATION = SET

    def __init__(self, mos, nodes, template_name, flow, file_type, expected_num_mo_changes=None, user=None,
                 timeout=None, filepath=None, name=None, interface=None, error_handling=None):
        """
        :param mos: dict with the mo_name as the keys to be modified to their corresponding value which is used in xml file
        :type mos: dict
        :param nodes: dictionary with the subnetwork as the key and a list of enm_node.BaseNode objects as the values
        :type nodes: dict
        :param template_name: string, name of the xml file
        :type template_name: str
        :param flow: import flow to follow
        :type flow: str
        :param file_type: type of file to import, can be 3GPP or Dynamic
        :type file_type: str
        :param expected_num_mo_changes: int, total number of MO changes expected to be recorded in history
        :type expected_num_mo_changes: int
        :param user: enm_user.User object
        :type user: enmutils.lib.enm_user_2.User
        :param timeout: time in seconds for the import
        :type timeout: int
        :param filepath: path to the filesystem where the xml file will be written
        :type filepath: str
        :param name: string, name for CM import, config will be generated with the same name
        :type name: str
        :param interface: import can be carried out through the CLI or over NBI
        :type interface: str
        :param error_handling: The execution policy with which to start the import job
        :type error_handling: str
        """

        super(CmImportUpdateLive, self).__init__(nodes=nodes, template_name=template_name, flow=flow,
                                                 file_type=file_type,
                                                 expected_num_mo_changes=expected_num_mo_changes, user=user,
                                                 timeout=timeout,
                                                 filepath=filepath, name=name, interface=interface,
                                                 error_handling=error_handling)
        self.mos = mos

    def prepare_xml_file(self):  # pylint: disable=arguments-differ
        """
        Prepare the XML file to be imported
        """
        super(CmImportUpdateLive, self).prepare_xml_file(values=self.mos)

    def prepare_dynamic_file(self, mo_values=None):
        """
        Prepare the dynamic text file to be imported
        """
        super(CmImportUpdateLive, self).prepare_dynamic_file(mo_values=self.mos)


class CmImportDeleteLive(CmImportLive):
    """
    Performs a Live CM import with 'delete' operation
    """

    XML_CLASS = CMImportDeleteXml
    FILE_OPERATION = DELETE


class CmImportCreateLive(CmImportLive):
    """
    Performs a Live CM import with 'create' operation
    """

    XML_CLASS = CMImportCreateXml
    FILE_OPERATION = CREATE


class ImportProfileContextManager(object):
    """
    Manages the execution of CM import profile
    """
    IMPORT = cycle(["MODIFICATIONS", "DEFAULTS"])
    IMPORT_TYPE = IMPORT.next()
    CLEANUP_REQUIRED = False
    RECOVERY_NODE_INFO = []
    RECOVERY_INFO_FILE_KEEP_TIME = 5184000  # 2 months in seconds

    def __init__(self, profile, default_obj, modify_obj, attempt_recovery=True, undo_job_id=None, user=None):
        """
        :param profile: profile object
        :type profile: enmutils_int.lib.profile.CmImportProfile
        :param default_obj: original information for file
        :type default_obj: CMImportLive
        :param modify_obj: changes to be made to the file for the import
        :type modify_obj: CMImportLive
        :param attempt_recovery: Boolean indicating whether or no the profile should attempt to recover the original MOs
        :type attempt_recovery: bool
        :param undo_job_id: the id of the undo job
        :type undo_job_id: int
        :param user: User who execute the command
        :type user: `enm_user_2.User`
        """
        self.profile = profile
        self.default_obj = default_obj
        self.modify_obj = modify_obj
        self.attempt_recovery = attempt_recovery
        self.setup_completed = self.setup()
        self.undo_profile = True if hasattr(profile, "UNDO_TIME") else False
        self.user = user
        self.undo_job_id = undo_job_id

    def setup(self):
        """
        Completes the necessary steps for setting up and tearing down a profile

        :return: A boolean value to indicate the status of completion setup method.
        :rtype: bool
        """
        log.logger.debug("Starting IMPORT Context Manager Setup Stage")
        try:
            self.prepare_file()
            self.profile.teardown_list.append(picklable_boundmethod(self.default_obj.delete))
            self.profile.teardown_list.append(picklable_boundmethod(self.modify_obj.delete))

            if self.attempt_recovery:
                self.write_profile_nodes_recovery_commands_to_file()
            if isinstance(self.default_obj, CmImportUpdateLive):
                if self.attempt_recovery:
                    self.profile.teardown_list.append(picklable_boundmethod(self.default_obj.import_flow))

                self._set_values_to_default()

            elif isinstance(self.default_obj, CmImportCreateLive) and self.attempt_recovery:
                self.profile.teardown_list.append(picklable_boundmethod(self.recreate_all_mos))
            self.setup_completed = True
        except Exception as e:
            log.logger.debug("ERROR DURING SETUP")
            self.setup_completed = False
            self.profile.add_error_as_exception(e)

        log.logger.debug("Finished IMPORT Context Manager Setup Stage")
        return self.setup_completed

    def _set_values_to_default(self):
        """
        Set the import MO values to their default values
        """
        log.logger.debug("Setting MO values to their default")
        try:
            self.default_obj.import_flow()
        except Exception as e:
            self.profile.add_error_as_exception(e)

        log.logger.debug("Successfully set MO values to their default")

    def prepare_file(self):
        """
        Calls the function to prepare a dynamic (.txt) or 3GPP (.xml) file, based on the profile's file type
        """

        if self.profile.FILETYPE == DYNAMIC:
            self.default_obj.prepare_dynamic_file()
            self.modify_obj.prepare_dynamic_file()
        else:
            self.default_obj.prepare_xml_file()
            self.modify_obj.prepare_xml_file()

    def write_profile_nodes_recovery_commands_to_file(self):
        """
        Writes each create command for all nodes assigned to the profile to a file containing the profile name and
        timestamp
        """

        log.logger.debug("Attempting to WRITE profile nodes recovery commands to file")
        self._check_directory_exists_and_remove_outdated_files()
        date_time = datetime.datetime.now().strftime('%Y_%m_%d-%H.%M.%S')
        recovery_filename = IMPORT_FILES_LOCATION + self.profile.NAME + "/" + self.profile.NAME + "_" + date_time
        log.logger.debug("File location: {}".format(recovery_filename))
        for node in self.profile.nodes_list:
            create_commands = get_fqdn_with_attrs_for_creation(get_enm_mo_attrs(node))
            for command in create_commands:
                self.RECOVERY_NODE_INFO.append(command)
                filesystem.write_data_to_file(data=command + "\n", output_file=recovery_filename, append=True,
                                              log_to_log_file=False)
        log.logger.debug("Finished WRITING profile nodes recovery commands to file")

    def _check_directory_exists_and_remove_outdated_files(self):
        """
        Check the profile directory exists and remove all outdated files
        """

        directory = IMPORT_FILES_LOCATION + self.profile.NAME
        filesystem.create_dir(directory)
        filesystem.remove_local_files_over_certain_age(directory, self.profile.NAME, self.RECOVERY_INFO_FILE_KEEP_TIME)

    def manage_sleep(self):
        """
        Sleep until the scheduled day or until next scheduled time
        """

        if any([hasattr(self.profile, "SCHEDULED_DAYS"), hasattr(self.profile, "SCHEDULED_TIMES_STRINGS"),
                hasattr(self.profile, "SCHEDULE_SLEEP")]):
            self.profile.sleep_until_next_scheduled_iteration()

    def run_import(self):
        """
        Executes the import flow
        """

        try:
            self.default_obj.user.open_session(reestablish=True)
        except Exception as e:
            self.profile.add_error_as_exception(EnmApplicationError(e))
            # As only milliseconds have passed after the sleep_until_time() method to get to this point once an
            # error arises, we need to sleep so it doesnt retry due to the time being in the same second.
            time.sleep(2)
            return

        import_object, undo_iter = self.get_import_object()
        self.execute_import_flow(import_object, undo_iter)

    def get_import_object(self):
        """
        Determines the import object to be executed

        :return: Tuple, containing the import object to run, and boolean indicating if undo required.
        :rtype: tuple
        """
        if not self.undo_profile:
            undo_iter = False
        else:
            undo_time = parse(self.profile.UNDO_TIME)
            undo_iter = True if self.modify_obj.PREVIOUS_ACTIVATION_EXISTS and timestamp.is_time_current(
                undo_time) else False

        if undo_iter:
            import_object = self.default_obj if self.IMPORT_TYPE == "MODIFICATIONS" else self.modify_obj
        else:
            import_object = self.modify_obj if self.IMPORT_TYPE == "MODIFICATIONS" else self.default_obj
        return import_object, undo_iter

    def execute_import_flow(self, import_object, undo_iter):
        """
        Starts the import flow of the supplied object

        :param import_object: Import instance object
        :type import_object: `enm_config.EnmJob`
        :param undo_iter: Boolean indicator to determine if an undo action is required
        :type undo_iter: bool
        """
        try:
            self.undo_job_id = import_object.import_flow(
                history_check=True, undo=undo_iter)
            self.IMPORT_TYPE = self.IMPORT.next()
        except Exception as e:
            self.exception_handling(e, import_object, undo_iter=undo_iter)

    def exception_handling(self, exception_caught, import_object, undo_iter=False):
        """
        Manages the exception thrown by completing the necessary actions and
        managing the positive and negative scenarios

        :param import_object: import object currently in use whilst the exception was raised
        :type import_object: CmImportLive
        :param exception_caught: exception thrown
        :type exception_caught: Exception
        :param undo_iter: boolean, determines if the iteration was performing an undo
        :type undo_iter: bool

        """

        self.profile.add_error_as_exception(exception_caught)

        if isinstance(exception_caught, UndoPreparationError):
            self._undo_and_config_cleanup(import_object, delete_undo_files=True, delete_config=False)
            self._undo_job_cleanup(import_object, delete_undo_job=True)
            return

        if isinstance(exception_caught, CMImportError):
            if undo_iter:
                self._cleanup_undo_files(import_object)
                self._cleanup_undo_job(import_object)

            self._exception_handling_cmimport_error(import_object)

        if isinstance(exception_caught, HistoryMismatch):
            delete_config = False
            self.IMPORT_TYPE = self.IMPORT.next()
            self._undo_and_config_cleanup(import_object, delete_undo_files=undo_iter, delete_config=delete_config)
            self._undo_job_cleanup(import_object, delete_undo_job=undo_iter)

    def _exception_handling_cmimport_error(self, import_object):
        """
        Exception handling if CmImportError occurred

        :param import_object: import object currently in use whilst the exception was raised
        :type import_object: enmutils_int.lib.cm_import.CmImportLive
        """
        if isinstance(import_object, CmImportUpdateLive):
            self.IMPORT_TYPE = self.IMPORT.next()
        else:
            self.import_activate_mo_cleanup()
            if not self.IMPORT_TYPE == "MODIFICATIONS":
                self.IMPORT_TYPE = self.IMPORT.next()

    def _undo_and_config_cleanup(self, import_object, delete_undo_files=False, delete_config=False):
        """
        Cleanup the undo and config files during exception handling
        :param import_object: import object currently in use whilst the exception was raised
        :type import_object: enmutils_int.lib.cm_import.CmImportLive
        :param delete_undo_files: whether to delete the undo files
        :type delete_undo_files: bool
        :param delete_config: whether to delete the config files
        :type delete_config: bool
        """
        if delete_undo_files:
            self._cleanup_undo_files(import_object)

    def _cleanup_undo_files(self, import_object):
        """
        Cleanup the undo files during exception handling
        :param import_object: import object currently in use whilst the exception was raised
        :type import_object: enmutils_int.lib.cm_import.CmImportLive
        """
        try:
            import_object.undo_over_nbi.remove_undo_config_files()
        except Exception as exception_caught:
            self.profile.add_error_as_exception(exception_caught)

    def _undo_job_cleanup(self, import_object, delete_undo_job=False):
        """
        Cleanup the undo job during exception handling
        :param import_object: import object currently in use whilst the exception was raised
        :type import_object: enmutils_int.lib.cm_import.CmImportLive
        :param delete_undo_job: whether to delete the undo job
        :type delete_undo_job: bool
        """
        if delete_undo_job:
            self._cleanup_undo_job(import_object)

    def _cleanup_undo_job(self, import_object):
        """
        Cleanup the undo job during exception handling
        :param import_object: import object currently in use whilst the exception was raised
        :type import_object: enmutils_int.lib.cm_import.CmImportLive
        """
        try:
            id_to_undo = self.undo_job_id
            import_object.undo_over_nbi.remove_undo_job(self.user, id_to_undo)
        except Exception as exception_caught:
            self.profile.add_error_as_exception(exception_caught)

    @staticmethod
    def _execute_cleanup_commands(commands_to_execute, cleanup_user):
        """
        Execute the cmedit cleanup commands to ensure that the MOs targeted by the import are either re-created
        or already exist

        :param commands_to_execute: list of cmedit commands to carry out to re-create the MOs
        :type commands_to_execute: list
        :param cleanup_user: user to carry out the cmedit cleanup commands
        :type cleanup_user: enmutils_int.lib.enm_user_2.User
        :raises CmeditCreateSuccessfulValidationError: if MO validation error
        :return: the commands to execute if there are commands remaining (as a result of unsuccessful execution)
        :rtype: list
        """
        successful_texts = ["already exists", "1 instance(s) updated", "children"]
        output = ''

        for command in commands_to_execute[:]:
            try:
                output = cleanup_user.enm_execute(command).get_output()
                if any(line for line in output if any(text in line for text in successful_texts)):
                    commands_to_execute.remove(command)
                else:
                    raise CmeditCreateSuccessfulValidationError(
                        "MO Validation error: 'already exists' or '1 instance(s) updated' was not found in the "
                        "response output.")
            except Exception as e:
                log.logger.debug("ERROR: {0}. Error executing the command '{1}'. Response from script engine: '{2}'"
                                 .format(e.message, command, output))

            # Including sleep here to avoid overloading cmserv (Erring on the side of caution)
            time.sleep(1)

        return commands_to_execute

    def import_activate_mo_cleanup(self, manual_intervention_warning_time=60 * 60):
        """
        Make sure all MOs that have been targeted exist via cmedit create commands

        """

        log.logger.debug("Attempting import/activate mo cleanup i.e. re-create any missing mo's")

        commands_to_execute = self.RECOVERY_NODE_INFO[:]
        cleanup_iteration = 1
        cleanup_start_time = datetime.datetime.now()
        sleep_time_per_unsuccessful_iterations = 60
        cleanup_user = self.profile.create_users(number=1, roles=['Cmedit_Administrator'], fail_fast=False, retry=True)[
            0]

        while commands_to_execute:
            if sleep_time_per_unsuccessful_iterations < manual_intervention_warning_time:
                sleep_time_per_unsuccessful_iterations *= 2
            else:
                sleep_time_per_unsuccessful_iterations = 7200

            log.logger.debug("ATTEMPT: {0} - TRYING TO RECREATE MOS".format(cleanup_iteration))
            commands_to_execute = self._execute_cleanup_commands(commands_to_execute, cleanup_user)
            if commands_to_execute:
                cleanup_iteration_finish_time = datetime.datetime.now()
                if timestamp.is_time_diff_greater_than_time_frame(cleanup_start_time, cleanup_iteration_finish_time,
                                                                  manual_intervention_warning_time):
                    self.profile.add_error_as_exception(
                        EnmApplicationError(
                            "Profile has attempted to cleanup {0} times but was unsuccessful. It is likely that "
                            "manual intervention is required. {1} MO(S) have still not created successfully".format(
                                cleanup_iteration, len(commands_to_execute))))

                log.logger.debug("AFTER ATTEMPT {0} OF TRYING TO RECREATE THE MISSING MO'S, {1} MO'S DID NOT GET "
                                 "CREATED SUCCESSFULLY".format(cleanup_iteration, len(commands_to_execute)))

                cleanup_iteration += 1
                time.sleep(sleep_time_per_unsuccessful_iterations)

        log.logger.debug(
            "Successfully completed import/activate mo cleanup after {0} attempts".format(cleanup_iteration))

    def recreate_all_mos(self):
        """
        Execute the commands in the recovery file to recreate all MOs during cleanup or teardown
        """
        cleanup_user = self.profile.create_users(number=1, roles=['Cmedit_Administrator'], fail_fast=False, retry=True)[
            0]
        for create_command in self.RECOVERY_NODE_INFO:
            log.logger.debug("Executing command: '{0}'".format(create_command))
            try:
                cleanup_user.enm_execute(create_command).get_output()
            except Exception as e:
                log.logger.debug("COMMAND: '{0}' FAILED. Response was: '{1}'".format(create_command, e.message))
            time.sleep(1)


def get_fqdn_with_attrs_for_creation(enm_mo_attrs):
    """
    Gets all the fqdn with mandatory attributes and makes up the create command necessary fo creating the MO

    :param enm_mo_attrs: list of `enmutils_int.lib.enm_mo.EnmMo` objects
    :type enm_mo_attrs: list

    :return: list of create commands
    :rtype: list
    """

    fqdns = []
    create_command = 'cmedit create '
    assignment = '='
    separator = ';'
    for enm_mo_obj in enm_mo_attrs:
        fqdn = enm_mo_obj.fdn
        attrs = enm_mo_obj.attrs
        mandatory_arguments = ' '
        for attribute_name, attribute_value in attrs.iteritems():
            mandatory_arguments = mandatory_arguments + attribute_name + assignment + '"' + attribute_value + '"' + separator

        if mandatory_arguments.endswith(separator):
            mandatory_arguments = mandatory_arguments[:-1]

        fqdns.append(create_command + fqdn + mandatory_arguments)

    return fqdns


def get_different_nodes(nodes, num_required_nodes):
    """
    Gets the specified amount of different nodes.
    Yields a generator object that once .next() is called on it will generate a dict with subnetwork as keys and
    `enmutils.lib.enm_node.nm_node.NodeWithMos` objects as values

    :param nodes: list of node objects
    :type nodes: list
    :param num_required_nodes: int declaring the total number of nodes you want returned
    :type num_required_nodes: int
    """
    for i in range(0, len(nodes), num_required_nodes):
        yield nodes[i: i + num_required_nodes]


def get_total_num_mo_changes(mo_values, total_nodes):
    """
    Calculates the total number of MOs

    :param total_nodes: int, number of nodes
    :type total_nodes: int
    :param mo_values: dict containing the MO names as the keys and the number of them as the value
    :type mo_values: dict

    :return: total number of MOs
    :rtype: int
    """

    total_mos = 0
    for mos in mo_values.values():
        total_mos += mos

    return total_mos * total_nodes


def get_enm_mo_attrs(node):
    """
    Gets a list of the 'enmutils_int.lib.enm_mo' MoAttrs objects that are attached as a list to the last MO key in
    the hierarchy within self.mos
    :param node: Node obj
    :type node: enmutils.lib.enm_node.Node
    :return: enm_mos: list of 'enmutils_int.lib.enm_mo' MoAttrs objects
    :rtype: list
    """

    enm_mos = []

    def recurse(mos):
        for _, remaining_mos in mos.iteritems():
            if isinstance(remaining_mos, dict):
                recurse(remaining_mos)
            elif isinstance(remaining_mos, list):
                enm_mos.extend(remaining_mos)

    recurse(node.mos)
    return enm_mos
