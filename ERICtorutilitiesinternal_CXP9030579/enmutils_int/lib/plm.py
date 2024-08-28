# ********************************************************************
# Name    : (PLM) Physical Link Management
# Summary : Used by Physical Link Management profiles. Allows the
#           user to manage and generate link import files based upon
#           the supplied nodes(normalised), import files contain information on
#           the physical links between node, such as ethernet cables.
#           Allows management of the number of imported links,
#           deletion of links and querying of links in ENM.
# ********************************************************************

import os
import re
import json
from collections import OrderedDict
from enmutils.lib import log, filesystem, persistence, mutexer
from enmutils.lib.shell import run_local_cmd
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.plm_ui import import_multipart_file_to_plm

DYNAMIC_DIR = "/home/enmutils/dynamic_content/"
CMEDIT_GET_NORMALIZED_NODES = "cmedit get Network=1 Node.(neType=={node_type}, normalization-state==NORMALIZED)"
CMEDIT_GET_MIM = "cmedit get {node} NetworkElement.ossModelIdentity"
CMEDIT_GET_INTERFACES = "cmedit get * Node.node-id=={node},Interfaces.interfaces-id==1,*"
CMEDIT_GET_INTERFACE_DETAILS = "cmedit get Network=1,Node={node},Interfaces=1,Interface={interface}"
CMEDIT_GET_OSSIDENTITY = "cmedit get * NetworkElement.ossModelIdentity=={identity}"
LINK_DELETE_NODE_COMMAND = "link delete --node {}"
LINK_DELETE_COMMAND = "link delete --link {}"
PLM_FILES_IMPORTED_KEY = "PLM_FILES_IMPORTED"
LAN_LAG_HIERARCHY = ['LAN', 'LAG']
CT_RLT_HIERARCHY = ['CT', 'RLT', 'RLIME', 'WAN']
E1_HIERARCHY = ['STM', 'E1']


class PhysicalLinkMgt(object):

    def __init__(self, user, node_types):
        """
        PhysicalLinkMgt constructor
        :param user: ENM user with required access roles
        :type user: enmutils.lib.enm_user_2.User
        :param node_types: types of the nodes required for the profile
        :type node_types: list
        """
        self.user = user
        self.node_types = node_types
        self.num_lines = 300
        self.file_paths = []
        self.files_imported = []
        self.links_created = 0
        self.import_file_name = "PLMimport{0}.csv"
        self.deletable_links_file = "PLM_deletable_links1.csv"
        self.failed_links = {}

    @staticmethod
    def convert_string(value):
        """
        converts given value to integer
        :param value: string which is to be converted in to int
        :type value: str
        :return: integer equivalent of given value
        :rtype: int
        """
        return int(''.join(re.findall('([0-9]+)', value)))

    def get_normalized_nodes_from_enm(self):
        """
        Fetches the normalized nodes from ENM
        :return: normalized nodes of supported nodes types
        :rtype: OrderedDict
        :raises EnmApplicationError: If there are no normalized nodes present in the ENM system
        """
        normalized_nodes = OrderedDict()
        normalized_nodes_nonexclusive = []
        excluded_patterns = ['LTE', 'MSC', 'gNodeB']
        for node_type in self.node_types:
            nodes = self.execute_cmedit_cmd(CMEDIT_GET_NORMALIZED_NODES.format(node_type=node_type), '.*Node=(.*)')
            node_names_list = [node.strip() for node in nodes if not any(pattern in node for pattern in
                                                                         excluded_patterns) and not node.startswith('B')]
            for node in node_names_list:
                if persistence.has_key(node):
                    node_data = persistence.get(node)
                    if not node_data._is_exclusive:
                        normalized_nodes_nonexclusive.append(node)
                    else:
                        log.logger.debug("Node {0} allocated to exclusive profile".format(node))
            node_names_list = normalized_nodes_nonexclusive
            normalized_nodes_nonexclusive = []
            log.logger.info("Normalized nodes of type {0} : {1}".format(node_type, len(node_names_list)))
            if node_names_list:
                node_names_list.sort(key=self.convert_string)
                normalized_nodes[node_type] = node_names_list
        if not normalized_nodes:
            raise EnmApplicationError("No NORMALIZED nodes found in ENM, cannot proceed with creating links!")
        return normalized_nodes

    @staticmethod
    def prepare_model_id_and_node_names_dict(model_id_list):
        """
        Forms a dict with oss model id as key and value as nodes of that model id
        :param model_id_list:
        :type model_id_list: list
        :return: model id and corresponding nodes
        :rtype: OrderedDict
        """
        model_id_node_dict = OrderedDict()
        for node_name, model_id in model_id_list:
            if model_id in model_id_node_dict:
                model_id_node_dict[model_id].append(node_name)
            else:
                model_id_node_dict[model_id] = [node_name]
        log.logger.debug("Unique OSS model identities found : {0}".format(len(model_id_node_dict)))
        return model_id_node_dict

    def sort_interfaces_list_according_to_hierarchy(self, interfaces_list, infs_to_ignore):
        """
        sorts the interfaces as per the PLM interface hierarchy
        :param interfaces_list: interfaces present on the node
        :type interfaces_list: list
        :param infs_to_ignore: interfaces to ignore
        :type infs_to_ignore: list
        :return: sorted list of interfaces
        :rtype: list
        """
        log.logger.debug("inferfaces to ignore {0}".format(infs_to_ignore))
        result = [inf1 for inf1 in interfaces_list for inf2 in infs_to_ignore if inf2 in inf1]
        interfaces_list = list(set(interfaces_list) - set(result))
        sorted_inf_list = [inf2 for inf1 in CT_RLT_HIERARCHY for inf2 in interfaces_list if inf1 in inf2.upper()]
        sorted_inf_list.extend([inf2 for inf1 in LAN_LAG_HIERARCHY for inf2 in interfaces_list if inf1 in inf2.upper()])
        sorted_inf_list.extend([inf2 for inf1 in E1_HIERARCHY for inf2 in interfaces_list if inf1 in inf2.upper()])
        delta_list = list(set(interfaces_list) - set(sorted_inf_list))
        delta_list.sort(key=self.convert_string)
        sorted_inf_list.extend(delta_list)
        log.logger.debug("Sorted INF list : {0}".format(sorted_inf_list))
        return sorted_inf_list

    def get_interfaces_on_node(self, model_id_node_dict):
        """
        Fetches interfaces present on the node of a given model identity
        :param model_id_node_dict: contains model id as key and list of nodes as value
        :type model_id_node_dict: OrderedDict
        :return: dictionary containing model id as key and value as a tuple of list of interfaces and list of nodes
        :rtype: OrderedDict
        """
        model_id_inf_dict = OrderedDict()
        all_interfaces = []
        infs_to_ignore = ["management", "lag-"]
        infs_ignore_ml669 = ["LAN-1/2/1", "LAN-1/2/2", "LAN-1/5/1", "LAN-1/5/2", "LAG-3", "LAG-14", "LAN-1/6/4", "LAN-1/6/5", "LAN-1/6/6", "LAN-1/6/7", "LAN-1/6/8", "LAG-2", "LAG-10"]
        for model_id, nodes_list in model_id_node_dict.iteritems():
            nodes_list.sort(key=self.convert_string)
            node = nodes_list[0]
            interfaces_list = self.execute_cmedit_cmd(CMEDIT_GET_INTERFACES.format(node=node),
                                                      '.*Interface=(.*)')
            log.logger.debug("Node {0} interfaces_list : {1}".format(node, interfaces_list))
            if 'ML' in node:
                if 'ML669' in node:
                    log.logger.debug("Trying to extend for all interfaces for ML669x")
                    all_interfaces.extend((LAN_LAG_HIERARCHY + CT_RLT_HIERARCHY + E1_HIERARCHY))
                    infs_to_consider = [inf1 for inf1 in interfaces_list for inf2 in all_interfaces if inf2 in inf1]
                    infs_to_ignore = list(set(interfaces_list) - set(infs_to_consider)) + infs_to_ignore
                else:
                    log.logger.debug("Trying to extend for all interfaces of ML node type")
                    all_interfaces.extend((LAN_LAG_HIERARCHY + CT_RLT_HIERARCHY))
                    infs_to_consider = [inf1 for inf1 in interfaces_list for inf2 in all_interfaces if inf2 in inf1]
                    infs_to_ignore = list(set(interfaces_list) - set(infs_to_consider)) + infs_to_ignore
            if interfaces_list:
                if 'ML669' in node:
                    log.logger.debug("Trying to sort interfaces for ML669x nodes : {0}".format(node))
                    infs_to_ignore = infs_to_ignore + infs_ignore_ml669
                    sorted_inf_list = self.sort_interfaces_list_according_to_hierarchy(interfaces_list, infs_to_ignore)
                    model_id_inf_dict[model_id] = (sorted_inf_list, nodes_list)
                else:
                    log.logger.debug("Trying to sort interfaces for all nodes : {0}".format(node))
                    sorted_inf_list = self.sort_interfaces_list_according_to_hierarchy(interfaces_list, infs_to_ignore)
                    model_id_inf_dict[model_id] = (sorted_inf_list, nodes_list)
        return model_id_inf_dict

    def fetch_nodes_model_id(self, node_names_list):
        """
        Returns list of node names and their OSS model ID's
        :param node_names_list: node names
        :type node_names_list: list
        :return: list of node names and their oss model ID tuples
        :rtype: list
        """
        model_id_list = []
        temp_list = []
        num_of_nodes = len(node_names_list)
        for node in node_names_list:
            temp_list.append(node)
            num_of_nodes -= 1
            if len(temp_list) == 500 or num_of_nodes == 0:
                log.logger.debug("Executing command on batch of {0} nodes".format(len(temp_list)))
                model_id_list.extend(self.execute_cmedit_cmd(CMEDIT_GET_MIM.format(node=';'.join(temp_list)),
                                                             "FDN : NetworkElement=(.*)\nossModelIdentity : (.*)"))
                temp_list = []
        return model_id_list

    def prepare_node_details_for_import_files(self, normalized_nodes):
        """
        Prepares the node details that are required for generating the import files
        :return:  sorted list of tuples containing layer_rate, link_type, interface and node name
        :rtype: OrderedDict
        """
        nodes_to_import = {}
        for node_type, node_names_list in normalized_nodes.iteritems():
            if len(node_names_list) > 500:
                model_id_list = self.fetch_nodes_model_id(node_names_list)
            else:
                model_id_list = self.execute_cmedit_cmd(CMEDIT_GET_MIM.format(node=';'.join(node_names_list)),
                                                        "FDN : NetworkElement=(.*)\nossModelIdentity : (.*)")
            model_id_node_dict = self.prepare_model_id_and_node_names_dict(model_id_list)
            log.logger.debug("model_id_node_dict : {}".format(model_id_node_dict.keys()))
            model_id_inf_dict = self.get_interfaces_on_node(model_id_node_dict)
            log.logger.debug("Model ID and Interfaces dict : {0}".format(model_id_inf_dict))
            nodes_to_import[node_type] = self.consolidate_data_for_import(model_id_inf_dict)
        return nodes_to_import

    def execute_cmedit_cmd(self, cmd, regex):
        """
        Executes cmedit commands and looks for the given regex pattern in the response and returns the result
        :param cmd: cmedit command to be executed
        :type cmd: str
        :param regex: regular expression string for pattern matching
        :type regex: str
        :return: result acquired after doing a pattern match on the command output
        :rtype: list
        """
        try:
            response = self.user.enm_execute(cmd)
            response_string = "\n".join(response.get_output())
            pattern = re.compile(r'{}'.format(regex))
            return pattern.findall(str(response_string))
        except Exception as e:
            log.logger.debug("Exception caught while executing cmedit command : {}".format(e))

    def consolidate_data_for_import(self, model_id_inf_dict):
        """
        Consolidates all the details in to a list, required for creating import files
        :param model_id_inf_dict: contains model identity as key and tuple of list of interfaces and list of nodes as value
        :type model_id_inf_dict: OrderedDict
        :return: list of tuples with each tuple containing nodes and interface_name
        :rtype: list
        """
        node_pair_inf_list = []
        log.logger.debug("Consolidating node interface details")
        for _, (inf_list, nodes_list) in model_id_inf_dict.iteritems():
            nodes_list.sort(key=self.convert_string)
            if len(nodes_list) % 2 != 0:
                nodes_list.pop(len(nodes_list) - 1)
            node_pair_list = [nodes_list[n:n + 2] for n in range(0, len(nodes_list), 2)]
            for inf in inf_list:
                node_pair_inf_list.extend([(node_1, inf, node_2) for (node_1, node_2) in node_pair_list])
        log.logger.info("After consolidating, list of nodes to import :\n {0}".format(len(node_pair_inf_list)))
        return node_pair_inf_list

    def write_to_csv_file(self, import_dict):
        """
        Writes the content present in the given dict to a file
        :param import_dict: dict containing interface and node details
        :type import_dict: dict
        :return: sorted list of import file paths
        :rtype: list
        :raises EnmApplicationError: if the import dict is empty
        """
        csv_files = []
        if not filesystem.does_dir_exist(DYNAMIC_DIR):
            filesystem.create_dir(DYNAMIC_DIR)
        if import_dict:
            file_names = import_dict.keys()
            file_names.sort(key=self.convert_string)
            for file_name in file_names:
                file_path = DYNAMIC_DIR + file_name
                log.logger.info("Preparing to write to file : {0}".format(file_path))
                with open(file_path, "w") as new_file:
                    new_file.write('Link Name,A Node,A I/F,Z Node,Z I/F' + '\n')
                    for line in import_dict[file_name]:
                        new_file.write(line + '\n')
                csv_files.append(file_path)
                log.logger.info("File generated successfully!")
            self.file_paths.extend(csv_files)
            csv_files.sort(key=self.convert_string)
            return csv_files
        else:
            raise EnmApplicationError("There is no content to be written to the csv file")

    def validate_nodes_for_import(self, nodes_to_import, max_links):
        """
        Verifies the required conditions for creating the link between any 2 nodes
        :param nodes_to_import: dictionary with node type as key and list of tuples containing link-type, layer-rate,
                                interface and node name
        :type nodes_to_import: dict
        :param max_links: gives the maximum number of links in can create
        :type max_links: int
        :return: dict having import file name as key and the content to be written to the file as its value
        :rtype: tuple
        :raises EnmApplicationError: if there are no entries in nodes_to_import
        """
        import_dict = OrderedDict()
        link_num = file_num = 1
        line_num = 0
        total_link = 0
        csv_lines = []
        nodes_type_count = len(nodes_to_import.keys())
        log.logger.debug("the max number of links on deploy {0}".format(max_links))
        for _, node_pair_inf_list in nodes_to_import.iteritems():
            log.logger.debug("the total number of links created after node types {0}".format(total_link))
            for node_1, inf, node_2 in node_pair_inf_list:
                csv_lines.append(','.join(['link{}'.format(link_num), node_1, inf, node_2, inf]))
                link_num += 1
                line_num += 1
                total_link += 1
                if total_link >= max_links:
                    log.logger.debug("the total number of links created is {0}".format(total_link))
                    break
                if line_num == self.num_lines:
                    import_dict[self.import_file_name.format(file_num)] = csv_lines
                    file_num += 1
                    line_num = 0
                    csv_lines = []
            nodes_type_count = nodes_type_count - 1
            if nodes_type_count == 0 and csv_lines:
                import_dict[self.import_file_name.format(file_num)] = csv_lines
        return import_dict

    def prepare_delete_links_dict(self, import_files):
        """
        Returns links that are to be deleted every alternate iteration
        :param import_files: contains the imported file paths
        :type import_files: list
        :return: list of links IDs
        :rtype: list
        """
        links_dict = {}
        delete_dict = {}
        import_files.sort(key=self.convert_string)
        import_files.reverse()
        files_to_read = import_files[:2]
        log.logger.debug("Files to read : {0}".format(files_to_read))
        for file_path in files_to_read:
            with open(file_path, 'rb') as csv_file:
                csv_file.next()
                for line in csv_file:
                    link_id = line.strip().split(',')[0]
                    links_dict[link_id] = line.strip()
        links_id_list = links_dict.keys()
        links_id_list.sort(key=self.convert_string)
        links_id_list.reverse()
        links = [links_dict[link_id] for link_id in links_id_list[:self.num_lines]]
        links.reverse()
        delete_dict[self.deletable_links_file] = links
        log.logger.debug("Deletable links dict : {}".format(delete_dict))
        return delete_dict

    def create_links(self, import_files):
        """
        Imports files to the PLM UI and links will be seen on the UI
        :param import_files: csv file paths which have link data between the nodes
        :type import_files: list
        :raises EnmApplicationError: If any links are failed while importing the file
        """
        import_files.sort(key=self.convert_string)
        for file_path in import_files:
            file_name = file_path.split('/')[-1]
            if file_path not in self.files_imported:
                log.logger.debug("File to be imported : {0}".format(file_name))
                response = import_multipart_file_to_plm(self.user, file_name, file_path)
                failed_links = self.check_response_for_errors_after_file_import(response)
                if self.deletable_links_file not in file_name:
                    self.files_imported.append(file_path)
                    self.persist_files_imported(file_path)
                log.logger.info("Imported file : {0}".format(file_path))
                self.set_number_of_links_created(file_path, len(failed_links.keys()))
                if failed_links.keys():
                    log.logger.debug("Failed to import links : {0}".format(failed_links.keys()))
                    raise EnmApplicationError("Failed to import {0} links, check profile log for more "
                                              "details".format(len(failed_links)))
                return

    def check_response_for_errors_after_file_import(self, response):
        """
        Checks how many links were failed during the file import and return the failed links
        :param response: response object of multipart file import
        :type response: `requests.Response`
        :return: failed links and the coreesponding error messages
        :rtype: dict
        :raises EnmApplicationError: If the response from the ENM is not having json object
        """
        failed_links = {}
        try:
            json_response = response.json()
            for entry in json_response:
                if entry['importResult'] != 'Imported' and 'link' in entry['name']:
                    name = entry['name']
                    failed_links[name] = entry['errorMessage']
        except Exception as e:
            raise EnmApplicationError("Error occurred while reading the file import response {0}".format(str(e)))
        if failed_links:
            log.logger.debug("Failed links and their error messages after the "
                             "import : \n {0}".format(json.dumps(failed_links)))
            self.failed_links.update(failed_links)
        return failed_links

    def _teardown(self):
        """
        Teardown steps for deleting the links as well as the import files
        """
        try:
            self.delete_links_on_nodes(self.files_imported)
            self.remove_files()
            if persistence.has_key(PLM_FILES_IMPORTED_KEY):
                persistence.remove(PLM_FILES_IMPORTED_KEY)
        except Exception as e:
            log.logger.info("Error encountered while removing the key from persistence : \n {}".format(e))
            raise

    @staticmethod
    def fetch_content_from_files(imported_files, links=False):
        """
        Returns the content read from the given list of files as a list
        :param imported_files: files which are already imported to PLM
        :type imported_files: list
        :param links: Flag to read the link names or node names from the given files
        :type links: bool
        :return: content read from the given list of files
        :rtype: list
        """
        content = []
        for file_path in imported_files:
            log.logger.debug("Fetching the links from the file file : {}".format(file_path))
            with open(file_path, 'rb') as csv_file:
                csv_file.next()
                if links:
                    content.extend([(line.strip().split(',')[0]) for line in csv_file if line])
                else:
                    content.extend([node for line in csv_file for node in (line.split(',')[1::2]) if node])
        return content

    def delete_links_on_nodes(self, imported_files):
        """
        Deletes links on individual nodes which is called during teardown
        :param imported_files: csv file paths which are already imported to PLM UI
        :type imported_files: list
        """
        failed_nodes = []
        nodes = self.fetch_content_from_files(imported_files)
        for node in set(nodes):
            try:
                response = self.user.enm_execute(LINK_DELETE_NODE_COMMAND.format(node), timeout_seconds=300)
                response_output = "\n".join(response.get_output())
                if "successfully" not in str(response_output):
                    failed_nodes.append((node, str(response_output)))
            except Exception as e:
                log.logger.debug("Exception caught while deleting links on node {0} for teardown : {1}".format(node, e))
        if failed_nodes:
            for node, response in failed_nodes:
                log.logger.debug("Deletion of links failed on node {0} with response : {1}".format(node, response))

    def delete_links_using_id(self, file_path):
        """
        Delete links using the link names when the maximum number of links possible are created
        :param file_path: csv file path which is already imported to PLM UI
        :type file_path: str
        :raises EnmApplicationError: If the links were failed to get deleted
        """
        failed_links = []
        log.logger.debug("Fetching the links from the file : {0}".format(file_path))
        links_to_delete = self.fetch_content_from_files([file_path], links=True)
        links_to_delete.reverse()
        log.logger.debug("Links to be deleted list : \n {0}".format(links_to_delete))
        for link_id in links_to_delete:
            try:
                response = self.user.enm_execute(LINK_DELETE_COMMAND.format(link_id), timeout_seconds=600)
                response_output = "\n".join(response.get_output())
                if "successfully" not in str(response_output):
                    failed_links.append((link_id, str(response_output)))
            except Exception as e:
                log.logger.debug("Exception caught while deleting links using link ID {0} : {1}".format(link_id, e.message))
        num_of_links_deleted = len(links_to_delete) - len(failed_links)
        if self.links_created >= num_of_links_deleted:
            self.links_created = self.links_created - num_of_links_deleted
        else:
            self.links_created = 0
        log.logger.info("Number of links present after deleting : {0}".format(self.links_created))
        if file_path in self.files_imported:
            self.files_imported.remove(file_path)
        if failed_links:
            for link_id, response in failed_links:
                log.logger.debug("Deletion of links {0} failed with response : {1}".format(link_id, response))
            raise EnmApplicationError("Deletion of {0} links using their link IDs failed, please check profile logs for"
                                      " more details".format(len(failed_links)))

    def set_number_of_links_created(self, imported_file, num_of_failed_links):
        """
        Sets number of links created so far on the deployment
        :param imported_file: imported file path
        :type imported_file: str
        :param num_of_failed_links: number of links failed during file import
        :type num_of_failed_links: int
        """
        num_of_links = 300
        response = run_local_cmd("wc -l {}".format(imported_file))
        if not response.ok:
            log.logger.info("Execution of local command failed! : {}".format(response.stdout))
        else:
            num_of_links = (int(response.stdout.split()[0].strip()) - 1)
        self.links_created = self.links_created + (num_of_links - num_of_failed_links)
        log.logger.info("Links imported so far: {}".format(self.links_created))

    @staticmethod
    def get_max_links_limit(import_files):
        """
        Return the maximum number of links that can be created on the deployment
        :param import_files: csv file paths which have link data between the nodes
        :type import_files: list
        :return: sum of number of links present in the import files
        :rtype: int
        """
        max_links = []
        for import_file in import_files:
            with open(import_file, 'rb') as csv_file:
                csv_file.next()
                max_links.extend([(line.strip().split(',')[0]) for line in csv_file if line])
        log.logger.info("Max limit for links : {}".format(len(max_links)))
        return len(max_links)

    def remove_files(self):
        """
        Removes the import files present on the deployment
        """
        log.logger.info("Removing files : \n {}".format(self.file_paths))
        for file_path in self.file_paths:
            log.logger.info("Path of the file : {}".format(file_path))
            exists = os.path.isfile(file_path)
            if exists:
                os.remove(file_path)
                log.logger.info("File deleted successfully")
            else:
                log.logger.info("File not present in the given path!")

    def persist_files_imported(self, file_path, delete=False):
        """
        Persists the files which are imported so that Netview_02 can pick those files and visualize the nodes with links
        :param file_path: path of the files imported
        :type file_path: str
        :param delete: Flag which says whether a files needs to be appended or removed from imported files list
        :type delete: bool
        """
        log.logger.info("Persisting the imported file paths for NETVIEW_02")
        with mutexer.mutex("update-files-imported-by-plm", persisted=True):
            if persistence.has_key(PLM_FILES_IMPORTED_KEY):
                imported_files = persistence.get(PLM_FILES_IMPORTED_KEY)
                if not delete:
                    imported_files.append(file_path)
                else:
                    imported_files.remove(file_path)
                persistence.set(PLM_FILES_IMPORTED_KEY, imported_files, -1)
            else:
                persistence.set(PLM_FILES_IMPORTED_KEY, self.files_imported, -1)
        log.logger.info("Persisted the imported file paths")
