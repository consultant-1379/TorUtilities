# ********************************************************************
# Name    : ENM Node
# Summary : Base class of LoadNode, also includes functionality to
#           retrieve and set the Persisted Object Identity(POID)
#           value of ENM nodes. Functionality should be moved
#           to LoadNode module.
# ********************************************************************

import re
from enum import Enum

from enmutils.lib import log, config, security
from enmutils.lib.exceptions import EnmApplicationError

ONE_INSTANCE_UPDATED_VERIFICATION = "1 instance(s) updated"
DELETED_INSTANCE_VERIFICATION = 'instance(s) deleted'
ZERO_INSTANCE_VERIFICATION = r"(?<=\D)(0 instance\(s\))"
ONE_INSTANCE_VERIFICATION = "1 instance(s)"
MULTIPLE_INSTANCES_DELETE_VERIFICATION = r"[1-9][0-9]* instance\(s\) deleted"
MULTIPLE_INSTANCES_VERIFICATION = r"[1-9][0-9]* instance\(s\)"

SSH = "SSH"
TLS = "TLS"


class Site(object):
    _valid_time_zones = None

    def __init__(self, site_name, altitude, location, longitude, latitude, world_time_zone):
        """
        Site Constructor

        :type site_name: string
        :param site_name: site name
        :type altitude: string
        :param altitude: site altitude
        :type location: string
        :param location: site location
        :type longitude: string
        :param longitude: site longitude
        :type latitude: string
        :param latitude: site latitude
        :type world_time_zone: string
        :param world_time_zone: site time zone
        """

        self.site_name = site_name
        self.altitude = altitude
        self.location = location
        self.longitude = longitude
        self.latitude = latitude
        self.world_time_zone = world_time_zone

    def __str__(self):
        return "Site: {site_name}, TimeZone: {timeZone}".format(site_name=self.site_name, timeZone=self.world_time_zone)


class BaseNodeLite(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return "Node ID {0}".format(self.node_id)

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self.node_id)


class BaseNode(object):
    _ignore_attrs = []
    _new_attrs = {'mos': {},
                  'managed_element_type': ''}
    root_elements = {'CCDM': 'ManagedElement', 'PCG': 'ManagedElement', 'MINI-LINK-669x': 'ManagedElement'}
    NE_TYPE = None

    def __init__(self, node_id='', node_ip='', mim_version='', model_identity='',
                 security_state='', normal_user='', normal_password='', secure_user='',
                 secure_password='', subnetwork='', isite_node_ip=None, netsim=None,
                 simulation=None, revision=None, identity=None, primary_type=None,
                 node_version=None, user=None, invalid_fields='', netconf_port='', snmp_port='', snmp_version=None,
                 snmp_community='', snmp_security_name='', snmp_authentication_method=None,
                 snmp_encryption_method=None, snmp_auth_password=None, snmp_priv_password=None, time_zone='',
                 controlling_rnc=None, connected_msc=None, transport_protocol=None, oss_prefix='', apnodeAIpAddress="",
                 apnode_bipaddress="", isnode_aipaddress="", isnode_bipaddress="", apgcluster_ipaddress="",
                 apgnode_aipaddress="",
                 apgnode_bipaddress="", bspnode_aipaddress="", bspnode_bipaddress="", bspapgcluster_ipaddress="",
                 bspapgnode_aipaddress="", bspapgnode_bipaddress="", base_file="", insight_ipaddress="",
                 connectivity_info_port='',
                 **kwargs):
        """
        Node Constructor

        :param node_id: Node ID (unique across all nodes)
        :type node_id: str
        :param node_ip: IP address of the node (unique across all nodes)
        :type node_ip: str
        :param mim_version: The node MIM version (in the format x.y.zzz)
        :type mim_version: str
        :param model_identity: The node model identity (in the format xxxx-yyy-zzz)
        :type model_identity: str
        :param security_state: The security state of the node
        :type security_state: str
        :param normal_user: The non secure username
        :type normal_user: str
        :param normal_password: The non secure username password
        :type normal_password: str
        :param secure_user: The secure username
        :type secure_user: str
        :param secure_password: The secure username password
        :type secure_password: str
        :param subnetwork: The node subnetwork
        :type subnetwork: str
        :param netsim: Netsim host
        :type netsim: str
        :param simulation: Netsim simulation
        :type simulation: str
        :param revision: Node revision
        :type revision: str
        :param identity: Node identity
        :type identity: str
        :param primary_type: The node's primary type
        :type primary_type: str
        :param node_version: Version of Node
        :type node_version: int
        :param user: User object
        :type user: enm_user_2.User
        :param invalid_fields:
        :type invalid_fields:
        :param netconf_port: Netconf Port to access on
        :type netconf_port: int
        :param snmp_port: Snmp Port to access on
        :type snmp_port: int
        :param snmp_version: Version of the SNMP protocol used
        :type snmp_version: SnmpVersion
        :param snmp_community: Community name
        :type snmp_community: str
        :param snmp_security_name: Security name
        :type snmp_security_name: str
        :param snmp_authentication_method: Algorithm used for authentication
        :type snmp_authentication_method: SnmpAuthenticationMethod
        :param snmp_encryption_method: Algorithm used for encryption
        :type snmp_encryption_method: SnmpEncryptionMethod
        :param snmp_auth_password: Authorization password for snmp V3
        :type snmp_auth_password: str
        :param snmp_priv_password: privacy password for snmp V3
        :type snmp_priv_password: str
        :param time_zone: node time zone
        :type time_zone: str
        :param controlling_rnc: The controlling RNC
        :type controlling_rnc: str
        :param connected_msc: The connected MSC
        :type connected_msc: str
        :param transport_protocol: Transport Protocol used by the Node
        :type transport_protocol: str
        :param oss_prefix: Oss Prefix of the node
        :type oss_prefix: str
        :param apnodeAIpAddress: IP address for apnodeA
        :type apnodeAIpAddress: str
        :param apnode_bipaddress: IP address for apnodeB
        :type apnode_bipaddress: str
        :param connectivity_info_port: port
        :type connectivity_info_port: str
        :param isite_node_ip: IP address of ISBlade
        :type isite_node_ip: str
        :param isnode_aipaddress: IP address of nodeA
        :type isnode_aipaddress: str
        :param isnode_bipaddress: IP address of nodeB
        :type isnode_bipaddress: str
        :param apgcluster_ipaddress: IP address of ap2clusterIP
        :type apgcluster_ipaddress: str
        :param apgnode_aipaddress: IP address of ap2nodeeA
        :type apgnode_aipaddress: str
        :param apgnode_bipaddress: IP address of ap2nodeeB
        :type apgnode_bipaddress: str
        :param bspnode_aipaddress: IP address of nodeA
        :type bspnode_aipaddress: str
        :param bspnode_bipaddress: IP address of nodeB
        :type bspnode_bipaddress: str
        :param bspapgcluster_ipaddress: IP address of bspcluster
        :type bspapgcluster_ipaddress: str
        :param bspapgnode_aipaddress: IP address of bspap2nodeA
        :type bspapgnode_aipaddress: str
        :param bspapgnode_bipaddress: IP address of bspap2nodeB
        :type bspapgnode_bipaddress: str
        :param base_file: path of csv file
        :type base_file: str
        :param insight_ipaddress: IP address of insight
        :type insight_ipaddress: str
        :param kwargs: A dictionary of optional keyword arguments
        :type kwargs: dict
        """

        self.node_id = node_id
        self.node_ip = node_ip
        self.mim_version = mim_version
        self.model_identity = model_identity
        self.security_state = security_state
        self.normal_user = normal_user
        self.normal_password = normal_password
        self.secure_user = secure_user
        self.secure_password = secure_password
        self.subnetwork = subnetwork if subnetwork != 'None' else ''
        self.netsim = netsim
        self.simulation = simulation
        self.time_zone = time_zone
        self.controlling_rnc = controlling_rnc
        self.connected_msc = connected_msc
        self.oss_prefix = oss_prefix or self.subnetwork_str
        self.isite_node_ip = isite_node_ip
        if config.has_prop("create_mecontext") and "MeContext" not in self.oss_prefix:
            self.oss_prefix = "{},MeContext={}".format(self.oss_prefix, self.node_id).lstrip(',')

        # Required to differentiate node types
        self.revision = revision
        self.identity = identity
        self.primary_type = primary_type
        self.node_version = node_version
        self.netconf_port = netconf_port
        self.transport_protocol = transport_protocol
        self.tls_mode = "LDAPS" if self.transport_protocol == TLS else ""
        self.snmp_port = snmp_port
        self.snmp_version = self._get_snmp_version() or snmp_version
        self.snmp_community = snmp_community
        self.snmp_security_name = snmp_security_name
        self.snmp_authentication_method = snmp_authentication_method
        self.snmp_encryption_method = snmp_encryption_method
        self.snmp_auth_password = snmp_auth_password
        self.snmp_priv_password = snmp_priv_password
        self.managed_element_type = kwargs.pop('managed_element_type', '')

        self.invalid_fields = invalid_fields
        self.user = ""
        self.fdn = kwargs.pop('fdn', '')
        self.poid = kwargs.pop('poid', '')
        self.mos = kwargs.pop('mos', {})
        self.network_function = kwargs.pop('network_function', '')
        self.apnodeAIpAddress = apnodeAIpAddress
        self.apnode_bipaddress = apnode_bipaddress
        self.isnode_aipaddress = isnode_aipaddress
        self.isnode_bipaddress = isnode_bipaddress
        self.apgcluster_ipaddress = apgcluster_ipaddress
        self.apgnode_aipaddress = apgnode_aipaddress
        self.apgnode_bipaddress = apgnode_bipaddress
        self.bspnode_aipaddress = bspnode_aipaddress
        self.bspnode_bipaddress = bspnode_bipaddress
        self.bspapgcluster_ipaddress = bspapgcluster_ipaddress
        self.bspapgnode_aipaddress = bspapgnode_aipaddress
        self.bspapgnode_bipaddress = bspapgnode_bipaddress
        self.base_file = base_file
        self.insight_ipaddress = insight_ipaddress
        self.connectivity_info_port = connectivity_info_port
        self.add_model_identity = config.get_prop("add_model_identity") if config.has_prop(
            "add_model_identity") else False
        if not hasattr(self, 'ROOT_ELEMENT'):
            self.ROOT_ELEMENT = (self.root_elements.get(self.primary_type) if
                                 self.root_elements.get(self.primary_type) else "MeContext")

        if not self.NE_TYPE:
            self.NE_TYPE = self.primary_type

    def _get_snmp_version(self):
        """
        Temporary method to get the snmp version if it exists
        To be removed when we are sure all node objects in persistence have this attribute 29-11-2016
        Original code in __init__: self.snmp_version = SnmpVersion.SNMP_V3 if config.has_prop("use_snmp_v3") else snmp_version

        :return: Snmp Version
        :rtype: str or None
        """

        version = None
        snmp_instance = None

        try:
            snmp_instance = SnmpVersion
        except (NameError, AttributeError) as e:  # pragma:no cover
            log.logger.debug(str("Exception trying to load SnmpVersion: {0}".format(str(e))))

        if config.has_prop("use_snmp_v3") and hasattr(snmp_instance, "SNMP_V3"):
            version = getattr(snmp_instance, "SNMP_V3")

        return version

    def __str__(self):
        return "\nNode ID {0} ({1}) [Model Identity {2}; MIM version {3}; security state {4}]".format(
            self.node_id, self.node_ip, self.model_identity, self.mim_version, self.security_state)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.node_name)

    def __cmp__(self, other):
        return cmp(self.node_id, other.node_id)

    def compare_with(self, other_node, ignore_attributes=("user")):
        if not isinstance(other_node, type(self)):
            return ValueError(
                "Argument should be of type {}, but got {}".format(self.__class__.__name__,
                                                                   other_node.__class__.__name__))
        return set(attr for attr in vars(self) if
                   attr not in ignore_attributes and getattr(self, attr) != getattr(other_node, attr))

    @property
    def node_name(self):
        """
        Returns the node name removing .*_ from id, except EPG-OI node IDs which are expected to contain underscores

        :return: node name
        :rtype: str
        """

        return re.sub(r".*_", "", self.node_id) if self.NE_TYPE not in ["EPG-OI"] else self.node_id

    @property
    def subnetwork_str(self):
        """
        Name of the subnetwork

        :return: subnetwork name
        :rtype: str
        """

        return "%s" % self.subnetwork.replace("|", ",") if self.subnetwork else ''

    @property
    def subnetwork_id(self):
        return self.subnetwork.split(",")[-1].split("=")[-1] if self.subnetwork else ''

    @property
    def mim(self):
        if not self.model_identity:
            return ''
        return "%s:%s" % (self.NE_TYPE, self.model_identity)

    @property
    def snmp_security_level(self):
        """

        :return: snmp security level
        :rtype: str
        """

        if self.snmp_authentication_method and self.snmp_encryption_method:
            return str(SnmpSecurityLevel.AUTH_PRIV)
        elif self.snmp_authentication_method:
            return str(SnmpSecurityLevel.AUTH_NO_PRIV)
        else:
            return str(SnmpSecurityLevel.NO_AUTH_NO_PRIV)

    def to_dict(self, encryption_password=None):
        """

        :type encryption_password: string
        :param encryption_password: If provided, passwords are encrypted
        :return: node in dictionary
        :rtype: dict[string]
        """

        normal_password = self.normal_password
        secure_password = self.secure_password
        if encryption_password:
            if normal_password:
                normal_password = "".join(security.encrypt(normal_password, encryption_password))
            if secure_password:
                secure_password = "".join(security.encrypt(secure_password, encryption_password))

        return {
            "connected_msc": self.connected_msc,
            "controlling_rnc": self.controlling_rnc,
            "identity": self.identity,
            "isite_node_ip": self.isite_node_ip,
            "mim_version": self.mim_version,
            "model_identity": self.model_identity,
            "netconf_port": self.netconf_port,
            "netsim": self.netsim,
            "node_id": self.node_id,
            "node_ip": self.node_ip,
            "node_version": self.node_version,
            "normal_user": self.normal_user,
            "normal_password": normal_password,
            "oss_prefix": self.oss_prefix,
            "poid": self.poid,
            "primary_type": self.primary_type,
            "revision": self.revision,
            "secure_user": self.secure_user,
            "secure_password": secure_password,
            "security_state": self.security_state,
            "simulation": self.simulation,
            "snmp_auth_password": self.snmp_auth_password,
            "snmp_authentication_method": self.snmp_authentication_method,
            "snmp_community": self.snmp_community,
            "snmp_encryption_method": self.snmp_encryption_method,
            "snmp_security_name": self.snmp_security_name,
            "snmp_port": self.snmp_port,
            "snmp_priv_password": self.snmp_priv_password,
            "snmp_version": self.snmp_version.enm_representation if self.snmp_version else None,
            "subnetwork": self.subnetwork,
            "time_zone": self.time_zone,
            "tls_mode": self.tls_mode,
            "transport_protocol": self.transport_protocol,
        }


class Node(BaseNode):
    MECONTEXT_NAMESPACE = "OSS_TOP"
    MECONTEXT_VERSION = "3.0.0"
    NETWORK_ELEMENT_NAMESPACE = "OSS_NE_DEF"
    NETWORK_ELEMENT_VERSION = "2.0.0"


class CppNode(Node):
    PLATFORM_TYPE = 'CPP'
    CONNECTIVITY_INFO_NAMESPACE = "CPP_MED"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    CONNECTIVITY_INFO_PORT = 80

    # Create Commands
    SET_NODE_SECURITY_CMD = 'secadm credentials create --rootusername root --rootuserpassword dummy --secureusername "{secure_user}" --secureuserpassword "{secure_password}" --normalusername "{normal_user}" --normaluserpassword "{normal_password}" -n "{node_id}"'
    UPDATE_NODE_SECURITY_CMD = 'secadm credentials update --rootusername root --rootuserpassword dummy --secureusername "{secure_user}" --secureuserpassword "{secure_password}" --normalusername "{normal_user}" --normaluserpassword "{normal_password}" -n "{node_id}"'

    ROOT_ELEMENT = 'MeContext'


class MGWNode(CppNode):
    NE_TYPE = 'MGW'
    NETWORK_TYPE = 'CORE'


class ERBSNode(CppNode):
    NE_TYPE = 'ERBS'
    NETWORK_TYPE = 'LRAN'


class RNCNode(CppNode):
    NE_TYPE = 'RNC'
    NETWORK_TYPE = 'WRAN'


class RBSNode(CppNode):
    NE_TYPE = 'RBS'
    NETWORK_TYPE = 'WRAN'


class ComEcimNode(Node):
    CONNECTIVITY_INFO_NAMESPACE = "COM_MED"
    CONNECTIVITY_INFO_VERSION = "1.1.0"
    CONNECTIVITY_INFO_PORT = 0
    SNMP_AGENT_PORT = 0
    SET_NODE_SECURITY_CMD = 'secadm credentials create --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'
    UPDATE_NODE_SECURITY_CMD = 'secadm credentials update --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'

    ROOT_ELEMENT = 'NetworkElement'

    def __init__(self, *args, **kwargs):
        super(ComEcimNode, self).__init__(*args, **kwargs)
        self.netconf_port = self.netconf_port or "830"
        if not self.transport_protocol:
            if self.netconf_port == "6513" and not config.has_prop("use_ssh"):
                self.transport_protocol = TLS
                self.tls_mode = "LDAPS"
            else:
                self.transport_protocol = SSH
                self.tls_mode = ""

        self.CERTM_MO = 'ManagedElement={node_id},SystemFunctions=1,SecM=1,CertM=1'.format(node_id=self.node_id)
        self.LDAP_MO = 'ManagedElement={node_id},SystemFunctions=1,SecM=1,UserManagement=1,LdapAuthenticationMethod=1,Ldap=1'.format(
            node_id=self.node_id)
        self.SYSM_MO = 'ManagedElement={node_id},SystemFunctions=1,SysM=1'.format(node_id=self.node_id)
        self.CLITLS_MO = self.SYSM_MO + ',CliTls=1'
        self.HTTPS_MO = self.SYSM_MO + ',HttpM=1,Https=1'
        self.NETCONFTLS_MO = self.SYSM_MO + ',NetconfTls=1'

        self.enrollment_authority_mo_name = 'EnrollmentAuthority'
        self.enrollment_server_group_mo_name = 'EnrollmentServerGroup'
        self.enrollment_server_mo_name = 'EnrollmentServer'
        self.node_credential_mo_name = 'NodeCredential'
        self.chain_certificate_mo_name = 'ChainCertificate'
        self.trust_category_mo_name = 'TrustCategory'


class IsNode(Node):
    CONNECTIVITY_INFO_NAMESPACE = "IS_MED"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    SET_NODE_SECURITY_CMD = 'secadm credentials create --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'
    UPDATE_NODE_SECURITY_CMD = 'secadm credentials update --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'
    ROOT_ELEMENT = 'NetworkElement'


class SbgIsNode(IsNode):
    NE_TYPE = 'SBG-IS'
    PLATFORM_TYPE = 'IS'


class SGSNNode(ComEcimNode):
    NE_TYPE = 'SGSN-MME'
    PLATFORM_TYPE = 'SGSN_MME'
    NETWORK_TYPE = 'CORE'


class VBGFNode(ComEcimNode):
    NE_TYPE = 'vBGF'
    PLATFORM_TYPE = 'ECIM'
    CONNECTIVITY_INFO_PORT = 22
    SNMP_AGENT_PORT = 1161


class WCGNode(ComEcimNode):
    NE_TYPE = 'vWCG'
    PLATFORM_TYPE = 'CBA'
    NETWORK_TYPE = 'CORE'


class VEMENode(ComEcimNode):
    NE_TYPE = 'vEME'


class EMENode(VEMENode):
    NE_TYPE = 'EME'


class RadioNode(ComEcimNode):
    NE_TYPE = 'RadioNode'
    PLATFORM_TYPE = 'CBA'
    ROOT_ELEMENT = 'ManagedElement'
    NETWORK_TYPE = 'LRAN,WRAN'


class PICONode(ComEcimNode):
    NE_TYPE = 'MSRBS_V1'
    PLATFORM_TYPE = 'CBA'
    NETWORK_TYPE = 'LRAN'


class EPGNode(ComEcimNode):
    NE_TYPE = 'EPG'
    PLATFORM_TYPE = 'CBA'
    NETWORK_TYPE = 'CORE'


class VEPGNode(ComEcimNode):
    NE_TYPE = 'VEPG'
    PLATFORM_TYPE = 'CBA'
    NETWORK_TYPE = 'CORE'


class SAPCNode(ComEcimNode):
    NE_TYPE = 'SAPC'
    PLATFORM_TYPE = 'CBA'
    NETWORK_TYPE = 'LRAN'


class SBGNode(ComEcimNode):
    NE_TYPE = 'SBG'
    PLATFORM_TYPE = 'CBA'


class RadioTNode(ComEcimNode):
    NE_TYPE = 'RadioTNode'
    PLATFORM_TYPE = ''

    def __init__(self, *args, **kwargs):
        super(RadioTNode, self).__init__(*args, **kwargs)
        self.transport_protocol = self.transport_protocol or TLS


class TCU04Node(RadioTNode):
    NE_TYPE = 'RadioTNode'
    PLATFORM_TYPE = ''


class C608Node(RadioTNode):
    NE_TYPE = 'RadioTNode'
    PLATFORM_TYPE = ''


class MTASNode(ComEcimNode):
    NE_TYPE = 'MTAS'
    PLATFORM_TYPE = ''

    def __init__(self, *args, **kwargs):
        kwargs["snmp_port"] = 161
        super(MTASNode, self).__init__(*args, **kwargs)


class CSCFNode(ComEcimNode):
    NE_TYPE = 'CSCF'
    PLATFORM_TYPE = ''


class WMGNode(ComEcimNode):
    NE_TYPE = 'WMG'
    PLATFORM_TYPE = ''


class VWMGNode(ComEcimNode):
    NE_TYPE = 'vWMG'
    PLATFORM_TYPE = ''


class DSCNode(ComEcimNode):
    NE_TYPE = 'DSC'
    PLATFORM_TYPE = ''


class BSCNode(ComEcimNode):
    NE_TYPE = 'BSC'
    PLATFORM_TYPE = 'ECIM'
    CONNECTIVITY_INFO_NAMESPACE = "BSC_MED"
    CONNECTIVITY_INFO_PORT = "830"
    APNODEAIPADDRESS = "172.168.16.46"
    APNODEBIPADDRESS = "172.168.16.35"
    CREATE_CONNECTIVITY_INFO_CMD = ""
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    SET_NODE_SECURITY_CMD = ('secadm credentials create '
                             '--secureusername "{secure_user}" --secureuserpassword "{secure_password}" '
                             '--nwieasecureusername "{secure_user}" --nwieasecureuserpassword {secure_password} '
                             '--nwiebsecureusername "{secure_user}" --nwiebsecureuserpassword {secure_password} -n {node_id}')

    ROOT_ELEMENT = "MeContext"


class BSPNode(Node):
    MECONTEXT_NAMESPACE = "OSS_TOP"
    MECONTEXT_VERSION = "3.0.0"
    NETWORK_ELEMENT_NAMESPACE = "OSS_NE_DEF"
    NETWORK_ELEMENT_VERSION = "2.0.0"
    CONNECTIVITY_INFO_NAMESPACE = "COM_MED"
    CONNECTIVITY_INFO_VERSION = "1.1.0"
    CONNECTIVITY_INFO_PORT = 22
    NE_TYPE = 'BSP'
    PLATFORM_TYPE = 'ECIM'

    SET_NODE_SECURITY_CMD = 'secadm credentials create --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'
    UPDATE_NODE_SECURITY_CMD = 'secadm credentials update --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'

    def __init__(self, *args, **kwargs):
        super(BSPNode, self).__init__(*args, **kwargs)
        self.transport_protocol = self.transport_protocol or SSH


class ER6000Node(Node):
    CONNECTIVITY_INFO_NAMESPACE = "ER6000_MED"
    CONNECTIVITY_INFO_VERSION = "1.2.0"
    CONNECTIVITY_INFO_PORT = 830
    SNMP_AGENT_PORT = 161

    SET_NODE_SECURITY_CMD = 'secadm credentials create --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'
    UPDATE_NODE_SECURITY_CMD = 'secadm credentials update --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'

    ROOT_ELEMENT = 'MeContext'

    def __init__(self, *args, **kwargs):
        super(ER6000Node, self).__init__(*args, **kwargs)
        self.transport_protocol = self.transport_protocol or TLS


class Router6274Node(ER6000Node):
    NE_TYPE = 'Router6274'
    PLATFORM_TYPE = 'ER6000'
    SET_NODE_SECURITY_CMD = ('secadm credentials create --secureusername "{secure_user}" --secureuserpassword '
                             '"{secure_password}" --ldapuser disable -n "{node_id}"')

    def __init__(self, *args, **kwargs):
        super(Router6274Node, self).__init__(*args, **kwargs)
        self.model_identity = self.model_identity if self.model_identity else "R18Q2-GA"


class Router6672Node(Router6274Node):
    NE_TYPE = 'Router6672'
    PLATFORM_TYPE = 'ER6000'


class MiniLinkNode(Node):
    CONNECTIVITY_INFO_NAMESPACE = ""
    CONNECTIVITY_INFO_VERSION = "3.0.0"
    SNMP_AGENT_PORT = 161
    CONNECTIVITY_LOCATION_VALUE = ''

    SET_NODE_SECURITY_CMD = ('secadm credentials create --rootusername "{secure_user}" --rootuserpassword '
                             '"{secure_password}" --secureusername "{secure_user}" --secureuserpassword '
                             '"{secure_password}" --normalusername "{normal_user}" --normaluserpassword '
                             '"{normal_password}" -n "{node_id}"')
    UPDATE_NODE_SECURITY_CMD = ('secadm credentials update --rootusername ericsson --rootuserpassword ericsson '
                                '--secureusername "{secure_user}" --secureuserpassword "{secure_password}" '
                                '--normalusername "{normal_user}" --normaluserpassword "{normal_password}" '
                                '-n "{node_id}"')


class MiniLinkIndoorNode(MiniLinkNode):
    NE_TYPE = 'MINI-LINK-Indoor'
    PLATFORM_TYPE = 'MINI-LINK-Indoor'
    CONNECTIVITY_INFO_NAMESPACE = "MINI-LINK-Indoor_MED"
    CONNECTIVITY_LOCATION_VALUE = 'Indoor'


class MINILink510R2Node(MiniLinkIndoorNode):
    NE_TYPE = 'MINI-LINK-CN510R2'


class MINILink810R1Node(MiniLinkIndoorNode):
    NE_TYPE = 'MINI-LINK-CN810R1'

    def __init__(self, *args, **kwargs):
        super(MINILink810R1Node, self).__init__(*args, **kwargs)
        self.NE_TYPE = 'MINI-LINK-CN810R1'
        self.model_identity = self.model_identity if self.model_identity else "M13B-CN810R1-1.0"


class MINILink810R2Node(MiniLinkIndoorNode):
    NE_TYPE = 'MINI-LINK-CN810R2'

    def __init__(self, *args, **kwargs):
        super(MINILink810R2Node, self).__init__(*args, **kwargs)
        self.NE_TYPE = 'MINI-LINK-CN810R2'
        self.model_identity = self.model_identity if self.model_identity else "M16A-CN810R2-2.4FP"


class MiniLinkOutdoorNode(MiniLinkNode):
    NE_TYPE = 'MINI-LINK-Outdoor'
    PLATFORM_TYPE = 'MINI-LINK-Outdoor'
    CONNECTIVITY_INFO_NAMESPACE = "MINI-LINK-Outdoor_MED"
    CONNECTIVITY_LOCATION_VALUE = 'Outdoor'


class MiniLink6352Node(MiniLinkOutdoorNode):
    NE_TYPE = 'MINI-LINK-6352'
    CONNECTIVITY_INFO_VERSION = "1.1.0"
    SET_NODE_SECURITY_CMD = ('secadm credentials create --rootusername {snmp_security_name} --rootuserpassword ericsson'
                             ' --secureusername {snmp_security_name} --secureuserpassword ericsson --normalusername '
                             '{snmp_security_name} --normaluserpassword ericsson -n "{node_id}"')


class MiniLink2020Node(MiniLinkOutdoorNode):
    CONNECTIVITY_INFO_VERSION = "1.1.0"
    SET_NODE_SECURITY_CMD = ('secadm credentials create --rootusername admin --rootuserpassword authpassword '
                             '--secureusername admin --secureuserpassword authpassword --normalusername admin '
                             '--normaluserpassword authpassword -n "{node_id}"')


class TspNode(Node):
    CONNECTIVITY_INFO_NAMESPACE = "TSP_MED"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    SNMP_AGENT_PORT = 161

    # Create Commands
    SET_NODE_SECURITY_CMD = 'secadm credentials create --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'
    UPDATE_NODE_SECURITY_CMD = 'secadm credentials update --secureusername "{secure_user}" --secureuserpassword "{secure_password}" -n "{node_id}"'

    ROOT_ELEMENT = 'NetworkElement'

    def __init__(self, *args, **kwargs):
        super(TspNode, self).__init__(*args, **kwargs)
        self.transport_protocol = self.transport_protocol or SSH


class CSCFTspNode(TspNode):
    NE_TYPE = 'CSCF-TSP'
    PLATFORM_TYPE = 'TSP'


class MTASTspNode(TspNode):
    NE_TYPE = 'MTAS-TSP'
    PLATFORM_TYPE = 'TSP'


class HSSFETspNode(TspNode):
    NE_TYPE = 'HSS-FE-TSP'
    PLATFORM_TYPE = 'TSP'


class CSAPCTspNode(TspNode):
    NE_TYPE = 'cSAPC-TSP'
    PLATFORM_TYPE = 'TSP'


class CCNTspNode(TspNode):
    NE_TYPE = 'CCN-TSP'
    PLATFORM_TYPE = 'TSP'


class VPNTspNode(TspNode):
    NE_TYPE = 'VPN-TSP'
    PLATFORM_TYPE = 'TSP'


class PT2020Node(MiniLink2020Node):
    NE_TYPE = 'MINI-LINK-PT2020'


class Fronthaul6392Node(MiniLink2020Node):
    NE_TYPE = 'Fronthaul-6392'


class Switch6391Node(MiniLink2020Node):
    NE_TYPE = 'Switch-6391'


class MiniLink6351Node(MiniLink2020Node):
    NE_TYPE = 'MINI-LINK-6351'


class TransportNode(Node):
    CONNECTIVITY_INFO_NAMESPACE = "GEN_FM_MED"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    PLATFORM_TYPE = ''
    NE_TYPE = ''
    SET_NODE_SECURITY_CMD = ('secadm credentials create --secureusername {secure_user} --secureuserpassword '
                             '{secure_password}  --nodelist "{node_id}"')
    UPDATE_NODE_SECURITY_CMD = ('secadm credentials update --secureusername {secure_user} --secureuserpassword '
                                '{secure_password} --nodelist "{node_id}"')

    def __init__(self, *args, **kwargs):
        self.NE_TYPE = "{0}-{1}".format(kwargs.get('primary_type'), kwargs.get('node_version'))
        super(TransportNode, self).__init__(*args, **kwargs)


class LanswitchNode(Node):
    NE_TYPE = "EXTREME-EOS"
    MECONTEXT_VERSION = "3.0.0"
    MECONTEXT_NAMESPACE = "OSS_TOP"
    NETWORK_ELEMENT_NAMESPACE = "OSS_NE_DEF"
    NETWORK_ELEMENT_VERSION = "2.0.0"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    CONNECTIVITY_INFO_NAMESPACE = "EOS_MED"
    SET_NODE_SECURITY_CMD = 'secadm credentials create --secureusername netsim --secureuserpassword netsim -n {node_id}'


class JuniperNode(TransportNode):
    pass


class JuniperMXNode(TransportNode):
    NE_TYPE = "JUNIPER-MX"

    def __init__(self, *args, **kwargs):
        super(JuniperMXNode, self).__init__(*args, **kwargs)
        self.NE_TYPE = 'JUNIPER-MX'
        if self.node_version == '18.3':
            self.model_identity = self.model_identity if self.model_identity else "18.3R1"
        else:
            self.model_identity = self.model_identity if self.model_identity else ""


class CiscoNode(TransportNode):
    pass


class ExtremeNode(LanswitchNode):
    PLATFORM_TYPE = 'EXTREME'


class ECILightSoftNode(TransportNode):
    NE_TYPE = "ECI-LightSoft"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    NETWORK_ELEMENT_NAMESPACE = "OSS_NE_DEF"
    CONNECTIVITY_INFO_NAMESPACE = "ECI_MED"
    CONNECTIVITY_INFO_PORT = 22
    NETWORK_ELEMENT_VERSION = "1.0.0"
    BASEFILE = "/netsim/netsimdir/CORE-ST-ECI-LightSoft-18.4x1/ECI-LightSoft01/ECI-LightSoft01.csv"
    SET_NODE_SECURITY_CMD = 'secadm credentials create --secureusername netsim --secureuserpassword netsim -n ManagementSystem={node_id}'


class ESCNode(TransportNode):
    CONNECTIVITY_INFO_NAMESPACE = "ESC_MED"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    PLATFORM_TYPE = 'ERS-SN'
    CONNECTIVITY_INFO_PORT = 830

    def __init__(self, *args, **kwargs):
        super(ESCNode, self).__init__(*args, **kwargs)
        self.NE_TYPE = "ESC"
        self.model_identity = self.model_identity if self.model_identity else "13A"


class ERSSupportNode(ESCNode):
    PLATFORM_TYPE = 'ERS-SN'
    NE_TYPE = 'ERS-SupportNode'
    CONNECTIVITY_INFO_NAMESPACE = "ESC_MED"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    SET_NODE_SECURITY_CMD = ('secadm credentials create --secureusername netsim --secureuserpassword '
                             'netsim  --nodelist "{node_id}"')

    def __init__(self, *args, **kwargs):
        super(ERSSupportNode, self).__init__(*args, **kwargs)
        self.NE_TYPE = 'ERS-SupportNode'
        self.model_identity = self.model_identity if self.model_identity else "13A"


class StnNode(Node):
    PLATFORM_TYPE = 'STN'
    NE_TYPE = 'STN'
    CONNECTIVITY_INFO_NAMESPACE = "STN_MED"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    CONNECTIVITY_INFO_PORT = 161

    # Create Commands
    SET_NODE_SECURITY_CMD = ('secadm credentials create --secureusername {secure_user} --secureuserpassword '
                             '{secure_password}  --nodelist "{node_id}"')
    UPDATE_NODE_SECURITY_CMD = ('secadm credentials update --secureusername {secure_user} --secureuserpassword '
                                '{secure_password} --nodelist "{node_id}"')
    ROOT_ELEMENT = 'MeContext'

    def __init__(self, *args, **kwargs):
        self.NE_TYPE = kwargs.get('simulation').split('-')[1] if self.NE_TYPE == 'STN' else self.NE_TYPE
        super(StnNode, self).__init__(*args, **kwargs)
        self.transport_protocol = self.transport_protocol or SSH


class SIU02Node(StnNode):
    NE_TYPE = 'SIU02'
    PLATFORM_TYPE = 'STN'


class TCU02Node(StnNode):
    NE_TYPE = 'TCU02'
    PLATFORM_TYPE = 'STN'


class Fronthaul6080Node(Node):
    NE_TYPE = 'FRONTHAUL-6080'
    CONNECTIVITY_INFO_NAMESPACE = "FRONT-HAUL-6080_MED"
    CONNECTIVITY_INFO_VERSION = "2.0.0"
    PLATFORM_TYPE = ''
    SNMP_PORT = '161'

    SET_NODE_SECURITY_CMD = ('secadm credentials create --rootusername admin --rootuserpassword admin '
                             '--secureusername admin --secureuserpassword admin --normalusername admin '
                             '--normaluserpassword admin -n "{node_id}"')
    UPDATE_NODE_SECURITY_CMD = ('secadm credentials update --rootusername "{root_user}" --rootuserpassword '
                                '"{root_password}" --secureusername "{secure_user}" --secureuserpassword '
                                '"{secure_password}" --normalusername "{normal_user}" --normaluserpassword "'
                                '{normal_password}" -n "{node_id}"')


class Fronthaul6020Node(Node):
    NE_TYPE = 'FRONTHAUL-6020'
    CONNECTIVITY_INFO_NAMESPACE = "FRONT-HAUL-6000_MED"
    CONNECTIVITY_INFO_VERSION = "1.0.0"
    PLATFORM_TYPE = ''
    SNMP_PORT = '161'
    SET_NODE_SECURITY_CMD = ('secadm credentials create --rootusername admin --rootuserpassword admin '
                             '--secureusername admin --secureuserpassword admin --normalusername admin '
                             '--normaluserpassword admin -n "{node_id}"')


class APGNode(CppNode):
    NE_TYPE = ''
    PLATFORM_TYPE = 'ECIM'
    APNODEAIPADDRESS = ""
    APNODEBIPADDRESS = ""
    CONNECTIVITY_INFO_NAMESPACE = "MSC_MED"
    SET_NODE_SECURITY_CMD = ('secadm credentials create --secureusername "{secure_user}" --secureuserpassword '
                             '"{secure_password}" -n "{node_id}"')


class APGISNode(CppNode):
    NE_TYPE = ''
    PLATFORM_TYPE = 'ECIM'
    APNODEAIPADDRESS = ""
    APNODEBIPADDRESS = ""
    CONNECTIVITY_INFO_NAMESPACE = "MSC_MED"
    SET_NODE_SECURITY_CMD = ('secadm credentials create --secureusername "{secure_user}" --secureuserpassword '
                             '"{secure_password}" -n "{node_id}"')


class APGISBladeNode(CppNode):
    """
    Inheriting from anything lower down the inheritance tree, causes too-many-ancestors to be raised
    """
    NE_TYPE = ''
    PLATFORM_TYPE = 'ECIM'
    ISNODEAIPADDRESS = ""
    ISNODEBIPADDRESS = ""
    APGCLUSTERIPADDRESS = ""
    APGNODEAIPADDRESS = ""
    APGNODEBIPADDRESS = ""
    CONNECTIVITY_INFO_NAMESPACE = "MSC_MED"
    SET_NODE_SECURITY_CMD = ('secadm credentials create --secureusername "{secure_user}" --secureuserpassword '
                             '"{secure_password}" -n "{node_id}"')


class VMSCNode(APGNode):
    NE_TYPE = 'vMSC'


class MSCDBNode(APGISNode):
    NE_TYPE = 'MSC-DB-BSP'
    NETWORK_TYPE = 'CORE'


class MSCBCNode(APGISNode):
    NE_TYPE = 'MSC-BC-BSP'
    NETWORK_TYPE = 'CORE'
    BSPNODEAIPADDRESS = ""
    BSPNODEBIPADDRESS = ""
    BSPAPGCLUSTERIPADDRESS = ""
    BSPAPGNODEAIPADDRESS = ""
    BSPAPGNODEBIPADDRESS = ""


class MSCISNode(APGISBladeNode):
    NE_TYPE = 'MSC-BC-IS'
    NETWORK_TYPE = 'CORE'


class IPSTPNode(APGNode):
    NE_TYPE = 'IP-STP'


class VIPSTPNode(APGNode):
    NE_TYPE = 'vIP-STP'


NODE_CLASS_MAP = {
    'vBGF': VBGFNode,
    'BSC': BSCNode,
    'BSP': BSPNode,
    'C608': C608Node,
    'CCN-TSP': CCNTspNode,
    'CISCO': CiscoNode,
    'cSAPC-TSP': CSAPCTspNode,
    'CSCF': CSCFNode,
    'CSCF-TSP': CSCFTspNode,
    'DSC': DSCNode,
    'ECI-LightSoft': ECILightSoftNode,
    'ECM': VMSCNode,
    'EME': EMENode,
    'vEME': VEMENode,
    'EPDG': WMGNode,
    'EPG': EPGNode,
    'VEPG': VEPGNode,
    'EPG-SSR': EPGNode,
    'ERBS': ERBSNode,
    'ESC': ESCNode,
    'ERS-SupportNode': ERSSupportNode,
    'EXTREME-EOS': ExtremeNode,
    'Fronthaul-6080': Fronthaul6080Node,
    'FRONTHAUL-6020': Fronthaul6020Node,
    'Fronthaul-6392': Fronthaul6392Node,
    'HSS-FE-TSP': HSSFETspNode,
    'JUNIPER': JuniperNode,
    'JUNIPER-MX': JuniperMXNode,
    'IP-STP': IPSTPNode,
    'vIP-STP': VIPSTPNode,
    'LH': MiniLinkIndoorNode,
    'MGW': MGWNode,
    'MINI-LINK-CN510R2': MINILink510R2Node,
    'MINI-LINK-CN810R1': MINILink810R1Node,
    'MINI-LINK-CN810R2': MINILink810R2Node,
    'MINI-LINK-6352': MiniLink6352Node,
    'MINI-LINK-6351': MiniLink6351Node,
    'MINI-LINK-PT2020': PT2020Node,
    'MLTN': MiniLinkIndoorNode,
    'MTAS': MTASNode,
    'MTAS-TSP': MTASTspNode,
    'MSC-BC-BSP': MSCBCNode,
    'MSC-DB-BSP': MSCDBNode,
    'MSC-BC-IS': MSCISNode,
    'MSC-DB': MSCDBNode,
    'vMSC': VMSCNode,
    'MSRBS_V1': PICONode,
    'PT': MiniLink6352Node,
    'RadioNode': RadioNode,
    'RadioTNode': RadioTNode,
    'RBS': RBSNode,
    'RNC': RNCNode,
    'Router_6672': Router6672Node,
    'Router6672': Router6672Node,
    'SpitFire': Router6672Node,
    'Router_6274': Router6274Node,
    'Router6274': Router6274Node,
    'SAPC': SAPCNode,
    'SBG': SBGNode,
    'SBG-IS': SbgIsNode,
    'STN': StnNode,
    'SIU02': SIU02Node,
    'SGSN': SGSNNode,
    'STP': IPSTPNode,
    'Switch-6391': Switch6391Node,
    'TCU02': TCU02Node,
    'TCU04': TCU04Node,
    'VPN-TSP': VPNTspNode,
    'WCG': WCGNode,
    'vWCG': WCGNode,
    'WMG': WMGNode,
    'vWMG': VWMGNode
}


def get_nodes_by_cell_size(cells, user):
    """
    Returns a list of nodes of with the specified number of cells

    :param cells: Create a list of nodes with the corresponding number of cells
    :type cells: list
    :param user: User object to be used to make http requests
    :type user: enm_user_2.User
    :return: list of nodes name
    :rtype: list
    """

    node_cells_cmd = "cmedit get * EUtranCellFDD.EUtranCellFDDId -t"
    cell_regex = r"\s+\d+\s+([a-zA-Z0-9_-]+)"
    cell_size_regex = r"([a-zA-Z0-9_]+)-{0}"

    response = user.enm_execute(node_cells_cmd)

    matches = re.findall(cell_regex, ','.join(line for line in response.get_output()))
    matching_cells = re.findall(cell_size_regex.format(cells), ','.join(match for match in matches))
    matching_cells_plus_one = re.findall(cell_size_regex.format(cells + 1), ','.join(match for match in matches))

    return list(set(matching_cells) - (set(matching_cells_plus_one)))


def get_enm_network_element_sync_states(enm_user):
    """
    To get the synchronization status of network elements in ENM

    :type enm_user: enmutils.lib.enm_user_2.User
    :param enm_user: User to run ENM CLI commands
    :rtype: dict[str, str]
    :return: The sync status of all network elements in ENM
    :raises EnmApplicationError: if there is error in response from ENM
    """
    log.logger.debug("Getting synchronization states of all Network Elements that exist in ENM")

    response = enm_user.enm_execute("cmedit get * CmFunction.syncStatus -t")
    enm_output = response.get_output()
    if "Error" in "\n".join(enm_output):
        raise EnmApplicationError("Error occurred while getting NE sync status from ENM - {output}"
                                  .format(output=enm_output))
    enm_network_element_sync_states = {}
    for line in enm_output[2:-2]:
        node_id, _, sync_status = line.split("\t")
        enm_network_element_sync_states[node_id.strip()] = sync_status.strip()

    log.logger.debug("Finished getting sync states of NE's that exist in ENM")
    return enm_network_element_sync_states


class SnmpVersion(Enum):
    SNMP_V1 = ("SNMP_V1", ["v1"])
    SNMP_V2C = ("SNMP_V2C", ["v2c", "v2"])
    SNMP_V3 = ("SNMP_V3", ["v3"])

    def __str__(self):
        return self.enm_representation

    def __lt__(self, other):
        return self.enm_representation < other.enm_representation

    @property
    def enm_representation(self):
        return self.value[0]

    @property
    def arne_representations(self):
        return self.value[1]

    @classmethod
    def from_arne_value(cls, value):
        """
        Returns the SNMP version enum that the value refers to. If the value contains more than one version (e.g. 'v1+v2+v3'), the highest version is returned

        :type value: str
        :param value: The string representation used by ARNE to refer to a version of SNMP. Can refer to multiple version (e.g. v1+v2)
        :return: Snmp Version
        :rtype: dict[str]
        """

        return sorted(cls._from_arne_value(version) for version in value.split("+"))[-1]

    @classmethod
    def _from_arne_value(cls, value):
        """
        Returns the SNMP version enum that the value refers to

        :type value: str
        :param value: The string representation used by ARNE to refer to a version of SNMP (e.g. v3). Can only refer to a single version
        :return: Snmp Version
        :rtype: str
        :raises ValueError: if there is StopIteration exception
        """

        try:
            return next(
                snmp_version for snmp_version in SnmpVersion if value.lower() in snmp_version.arne_representations)
        except StopIteration:
            raise ValueError("'{}' is not a valid SNMP version".format(value))

    @classmethod
    def from_enm_value(cls, value):
        """
        Returns the SNMP version enum that the value refers to

        :type value: str
        :param value: The string representation used by ENM to refer to a version of SNMP (e.g. SNMP_V3)
        :return: Snmp Version
        :rtype: str
        :raises ValueError: if there is StopIteration exception
        """

        try:
            return next(snmp_version for snmp_version in SnmpVersion if value in snmp_version.enm_representation)
        except StopIteration:
            raise ValueError("'{}' is not a valid SNMP version".format(value))


class SnmpEncryptionMethod(Enum):
    AES_128 = ("AES128", "AES-128")
    CBC_DES = ("DES", "CBC-DES")

    def __str__(self):
        return self.value[0]

    @property
    def enm_representation(self):
        return self.value[0]

    @property
    def arne_representation(self):
        return self.value[1]

    @classmethod
    def from_enm_value(cls, value):
        """
        Returns the appropriate SNMP encryption algorithm based on a value from an ARNE XML

        :type value: str
        :param value: The value of SNMP encryptionMethod retrieved from ARNE
        :return: Snmp Encryption Method
        :rtype: str
        :raises ValueError: if there is StopIteration exception
        """

        try:
            return next(method for method in cls if method.enm_representation == value)
        except StopIteration:
            raise ValueError("'{}' is not a valid SNMP encryption method".format(value))

    @classmethod
    def from_arne_value(cls, value):
        """
        Returns the appropriate SNMP encryption algorithm based on a value from ENM

        :type value: str
        :param value: The value of SNMP encryptionMethod retrieved from ENM
        :return: Snmp Encryption Method
        :rtype: str
        :raises ValueError: if there is StopIteration exception
        """

        try:
            return next(method for method in cls if method.arne_representation == value)
        except StopIteration:
            raise ValueError("'{}' is not a valid SNMP encryption method".format(value))


class SnmpAuthenticationMethod(Enum):
    MD5 = ["MD5", "MD5"]
    SHA = ["SHA1", "SHA"]

    def __str__(self):
        return self.value[0]

    @property
    def enm_representation(self):
        return self.value[0]

    @property
    def arne_representation(self):
        return self.value[1]

    @classmethod
    def from_arne_value(cls, value):
        """
        Returns the appropriate SNMP authentication algorithm based on a value from an ARNE XML

        :type value: str
        :param value: The value of SNMP authenticationMethod retrieved from ARNE
        :return: Snmp Authentication Method
        :rtype: str
        :raises ValueError: if there is StopIteration exception
        """

        try:
            return next(method for method in cls if method.arne_representation == value)
        except StopIteration:
            raise ValueError("'{}' is not a valid SNMP authentication method".format(value))

    @classmethod
    def from_enm_value(cls, value):
        """
        Returns the appropriate SNMP authentication algorithm based on a value from ENM

        :type value: str
        :param value: The value of SNMP authenticationMethod retrieved from ENM
        :return: Snmp Authentication Method
        :rtype: str
        :raises ValueError: if there is StopIteration exception
        """

        try:
            return next(method for method in cls if method.enm_representation == value)
        except StopIteration:
            raise ValueError("'{}' is not a valid SNMP authentication method".format(value))


class SnmpSecurityLevel(Enum):
    NO_AUTH_NO_PRIV = "NO_AUTH_NO_PRIV"
    AUTH_NO_PRIV = "AUTH_NO_PRIV"
    AUTH_PRIV = "AUTH_PRIV"

    def __str__(self):
        return self.value
