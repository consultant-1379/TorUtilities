# ********************************************************************
# Name    : Element Manager
# Summary : Functional module for Element Manager.
#           Allows the user the fetch, verify and apply the
#           configuration archive, to the supplied nodes, also
#           provides functionality for node POID discovery.
# ********************************************************************


from os import path, remove

from enmutils_int.lib import nexus, netsim_executor as nets_exec
from enmutils_int.lib.load_node import filter_nodes_having_poid_set
from enmutils.lib import log, shell, filesystem as fs
from enmutils.lib.exceptions import ShellCommandReturnedNonZero, ValidationError


ULIB_PATH = '/netsim/netsimdir/{0}/user_cmds/cppem'


def _untar_tarball_on_netsim(tarball_path, ulib_path=None, host=None, netsim_user='netsim', netsim_pass='netsim'):
    """
    Untar tarball to the specific location on specific netsim

    :param tarball_path: Path where tarball will be uploaded
    :type tarball_path: str
    :param ulib_path: Path to unpack configuration tarball
    :type ulib_path: str
    :param host: Netsim hostname
    :type host: str
    :param netsim_user: Netsim user
    :type netsim_user: str
    :param netsim_pass: Password for Netsim user
    :type netsim_pass: str
    :raises ShellCommandReturnedNonZero: if untarring file failed
    """
    unpack_cmd = '/bin/mkdir -p {0}; cd {0}; tar -xzf {1}'

    log.logger.debug('** Untarring file: {0} on netsim: {1} to: {2}'.format(tarball_path, host, ulib_path))
    cmd = unpack_cmd.format(ulib_path, tarball_path)
    cmd_response = shell.run_remote_cmd(shell.Command(cmd, timeout=600), host, netsim_user, netsim_pass)
    if cmd_response.rc != 0:
        raise ShellCommandReturnedNonZero('Untarring file: {0} on netsim: {1} to: {2} - failed. '
                                          'OUTPUT: {3}'.format(tarball_path, host, ulib_path,
                                                               cmd_response.stdout), cmd_response)


def _push_tarball_to_netsim(node_list, tarball_path, ulib_path=None):
    """
    Upload and unpack a tarball to netsims for specific nodes

    :param node_list: List of nodes to configure
    :type  node_list: list
    :param tarball_path: Path where tarball will be uploaded
    :type tarball_path: str
    :param ulib_path: Path to unpack configuration tarball
    :type ulib_path: str
    """
    tarball_remote_dir_path = '/'.join(tarball_path.split('/')[:-1])

    for node in node_list:
        host = node.netsim
        ulib_path = ulib_path or ULIB_PATH.format(node.simulation)
        log.logger.debug('** Uploading file: {0} to netsim: {1}:{2}'.format(tarball_path, host, tarball_remote_dir_path))
        nets_exec.deploy_script(host, tarball_path, tarball_path)
        _untar_tarball_on_netsim(tarball_path, ulib_path, host)


def _setup_user_cmds_on_nodes(node_list, ulib_path=None):
    """
    Configure nodes, so that they can use Element Manager application
    Configuration tarball will be downloaded if doesn't exist and deployed to netsims
    of profiles nodes.

    :param node_list:  List of nodes to configure
    :type node_list: list
    :param ulib_path: Path to unpack configuration tarball
    :type ulib_path: str

    :raises ShellCommandReturnedNonZero: if configuration of node failed
    """
    for node in node_list:
        host = node.netsim
        simulation = node.simulation

        ulib_path = ulib_path or ULIB_PATH.format(node.simulation)
        cmds = ['.stop', '.set ulib {0}'.format(ulib_path), '.set save', '.start']
        for cmd in cmds:
            response = nets_exec.run_cmd(cmd, host, simulation, node_names=[node.node_name])
            if response.rc != 0:
                raise ShellCommandReturnedNonZero('Configuration of node {0} failed, '
                                                  'when executing {1} command.'.format(node.node_id, cmd), response)


def _is_corrupted(tarball_path):
    """
    Verify tarball file
    :param tarball_path: path to the tarball
    :type tarball_path: str

    :return: True if file is ok, False otherwise
    :rtype: bool
    """
    cmd = '/bin/tar -tf {0}'.format(tarball_path)
    response = shell.run_local_cmd(shell.Command(cmd))

    # delete file if corrupted
    if response.rc != 0:
        try:
            remove(tarball_path)
        except OSError:
            pass

    return response.rc != 0


def _get_tarball_path(art, ver, ext, download_dir='/tmp/enmutils'):
    """
    Build abs path to a tarball
    :param art: Artifact name describing tarball on Nexus
    :type art: str
    :param ver: version of tarball
    :type ver: str
    :param ext: extension
    :type ext: str
    :param download_dir: Abs path to dir where tarball is to be stored
    :type download_dir: str

    :return: Abs path to the tarball
    :rtype: str
    """
    tarball_name = '{0}-{1}.{2}'.format(art, ver, ext)   # JIRA CIS-35882 to put to nexus
    return path.join(download_dir, tarball_name)


def pull_config_files_tarball(download_dir='/tmp/enmutils'):
    """
    Download configuration tarball(s) from Nexus to a local path
    Version 1.0.1 has only config files for ERBS nodes

    :param download_dir: Abs path to dir where tarball is to be stored
    :type download_dir: str

    :raises ValidationError: if tarball not downloaded
    :return: tarball local path
    :rtype: str
    """
    group = 'com.ericsson.oss.rv'
    artifact = 'workload-profiles'
    ver = '1.0.1'
    ext = 'tar.gz'

    tarball_local_path = _get_tarball_path(artifact, ver, ext, download_dir)

    if not fs.does_file_exist(tarball_local_path) or (fs.does_file_exist(tarball_local_path) and _is_corrupted(tarball_local_path)):
        tarball_downloaded = nexus.download_artifact_from_nexus(group, artifact, ver, ext, download_path=download_dir)
        if not tarball_downloaded:
            raise ValidationError

    return tarball_local_path


def configure_assigned_nodes(node_list, tarball_path=None):
    """
    Configure nodes for the Element Manager app.
    Steps include (based on https://eteamspace.internal.ericsson.com/display/SONV/Netsim+ERBS+configuration+for+Element+Manager):
        - upload tarball to specific location on netsim boxes(netsims are defined by the assigned nodes)
        - unltar tarball to predefined location on netsim boxes
        - apply new configuration (involves: stop, add new lib paths and start of assigned nodes)

    :param tarball_path: path to the tarball
    :type tarball_path: str
    :param node_list: List of nodes to configure
    :type node_list: list
    """
    if tarball_path and fs.does_file_exist(tarball_path):
        log.logger.debug('** Applying configuration on nodes: {0}'.format(', '.join([node.node_id for node in node_list])))
        _push_tarball_to_netsim(node_list, tarball_path)
        _setup_user_cmds_on_nodes(node_list)


def get_poids(nodes):
    """
    Get the POIDs for the provided nodes

    :param nodes: list of nodes to retrieve POIDs of
    :type nodes: list
    :return: all_poids, successful_nodes: list of all the POIDs,list of nodes for which a POID was successfully returned
    :rtype: list, list
    """

    successful_nodes = filter_nodes_having_poid_set(nodes)
    all_poids = [node.poid for node in successful_nodes]

    return all_poids, successful_nodes
