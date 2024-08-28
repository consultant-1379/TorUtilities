#!/usr/bin/env python
import unittest2
from mock import Mock, patch, PropertyMock
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib.enm_node import BaseNode
from enmutils.lib.enm_node import (Site, BaseNodeLite, ComEcimNode, RadioTNode, MTASNode, BSPNode, ER6000Node,
                                   Router6274Node, MINILink810R1Node, MINILink810R2Node, TspNode, TransportNode,
                                   JuniperMXNode, ESCNode, ERSSupportNode, StnNode, SnmpVersion, SnmpEncryptionMethod,
                                   SnmpAuthenticationMethod, get_nodes_by_cell_size,
                                   get_enm_network_element_sync_states, EnmApplicationError)
from testslib import unit_test_utils


class EnmNodeUnitTests(ParameterizedTestCase):
    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils.lib.enm_node.BaseNode.__init__", return_value=None)
    def test_snmp_security_level__returns_auth_priv(self, _):
        node = BaseNode()
        node.snmp_authentication_method = "some_auth_method"
        node.snmp_encryption_method = "some_encr_method"
        self.assertEqual(node.snmp_security_level, "AUTH_PRIV")

    @patch("enmutils.lib.enm_node.BaseNode.__init__", return_value=None)
    def test_snmp_security_level__returns_auth_no_priv(self, _):
        node = BaseNode()
        node.snmp_authentication_method = "some_auth_method"
        node.snmp_encryption_method = None
        self.assertEqual(node.snmp_security_level, "AUTH_NO_PRIV")

    @patch("enmutils.lib.enm_node.BaseNode.__init__", return_value=None)
    def test_snmp_security_level__returns_no_auth_no_priv(self, _):
        node = BaseNode()
        node.snmp_authentication_method = None
        node.snmp_encryption_method = None
        self.assertEqual(node.snmp_security_level, "NO_AUTH_NO_PRIV")

    def test_site__str__success(self):
        site = Site("name", "0", "0", "0", "0", "GMT")
        self.assertEqual("Site: name, TimeZone: GMT", str(site))

    def test_base_node_list__str__success(self):
        base_node = BaseNodeLite(node_id="Node")
        self.assertEqual("Node ID Node", str(base_node))

    def test_base_node_list__repr__success(self):
        base_node = BaseNodeLite(node_id="Node")
        self.assertEqual("<BaseNodeLite Node>", base_node.__repr__())

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.get_prop', return_value=False)
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=True)
    def test_base_node__init__success(self, *_):
        base_node = BaseNode(node_id="Node", oss_prefix="OSSPrefix")
        self.assertEqual("OSSPrefix,MeContext=Node", base_node.oss_prefix)

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test__str__success(self, *_):
        base_node = BaseNode(node_id="Node", node_ip="ip", model_identity="model", mim_version="mim",
                             security_state="OK")
        self.assertEqual("\nNode ID Node (ip) [Model Identity model; MIM version mim; security state OK]",
                         str(base_node))

    @patch('enmutils.lib.enm_node.BaseNode.node_name', new_callable=PropertyMock, return_value="Name")
    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test__repr__success(self, *_):
        base_node = BaseNode(node_id="Node")
        self.assertEqual("<BaseNode Name>", base_node.__repr__())

    @patch('enmutils.lib.enm_node.BaseNode.node_name', new_callable=PropertyMock, return_value="Name")
    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test__cmp__success(self, *_):
        base_node = BaseNode(node_id="Node")
        other_node = Mock(node_id="Node")
        self.assertEqual(0, base_node.__cmp__(other_node))

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_compare_with__value_error(self, *_):
        base_node = BaseNode(node_id="Node")
        self.assertTrue(isinstance(base_node.compare_with(Mock()), ValueError))

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_compare_with__no_value_error(self, *_):
        base_node = BaseNode(node_id="Node")
        self.assertEqual(base_node.compare_with(base_node), set([]))

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_node_name__epg_oi(self, *_):
        base_node = BaseNode(node_id="Node_100k", primary_type="EPG-OI")
        self.assertEqual(base_node.node_name, "Node_100k")

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_subnetwork_id__success(self, *_):
        base_node = BaseNode(node_id="Node_100k", subnetwork="Sub=Sub,Sub=Sub1")
        self.assertEqual(base_node.subnetwork_id, "Sub1")

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_mim__no_model_identity(self, *_):
        base_node = BaseNode(model_identity="")
        self.assertEqual(base_node.mim, "")

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_mim__model_identity(self, *_):
        base_node = BaseNode(model_identity="model", primary_type="ERBS")
        self.assertEqual(base_node.mim, "ERBS:model")

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    @patch('enmutils.lib.enm_node.security.encrypt')
    def test_to_dict__encryption(self, mock_encrypt, *_):
        base_node = BaseNode(model_identity="model", primary_type="ERBS", normal_password="normal",
                             secure_password="secure")
        base_node.to_dict(encryption_password="True")
        self.assertEqual(2, mock_encrypt.call_count)

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    @patch('enmutils.lib.enm_node.security.encrypt')
    def test_to_dict__encryption_no_password_or_username(self, mock_encrypt, *_):
        base_node = BaseNode(model_identity="model", primary_type="ERBS")
        base_node.to_dict(encryption_password="True")
        self.assertEqual(0, mock_encrypt.call_count)

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    @patch('enmutils.lib.enm_node.security.encrypt')
    def test_to_dict__no_encryption(self, mock_encrypt, *_):
        base_node = BaseNode(model_identity="model", primary_type="ERBS")
        base_node.to_dict()
        self.assertEqual(0, mock_encrypt.call_count)

    @patch('enmutils.lib.enm_node.BaseNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_comecim_node__init__no_transport_protocol(self, *_):
        ecim_node = ComEcimNode(transport_protocol={}, netconf_port="6513")
        self.assertEqual("LDAPS", ecim_node.tls_mode)

    @patch('enmutils.lib.enm_node.ComEcimNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_comecim_node__init__transport_protocol(self, *_):
        ecim_node = ComEcimNode(transport_protocol={"key": "value"}, netconf_port="6513")
        self.assertEqual("", ecim_node.tls_mode)

    @patch('enmutils.lib.enm_node.RadioTNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_radio_t_node__init__(self, *_):
        radio_t_node = RadioTNode(transport_protocol={})
        self.assertEqual(radio_t_node.transport_protocol, 'SSH')

    @patch('enmutils.lib.enm_node.MTASNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_mtas_node__init__(self, *_):
        mtas_node = MTASNode()
        self.assertEqual(mtas_node.snmp_port, 161)

    @patch('enmutils.lib.enm_node.BSPNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_bsp_node__init__(self, *_):
        bsp_node = BSPNode()
        self.assertEqual(bsp_node.transport_protocol, 'SSH')

    @patch('enmutils.lib.enm_node.ER6000Node._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_er6000_node__init__(self, *_):
        er6000_node = ER6000Node()
        self.assertEqual(er6000_node.transport_protocol, 'TLS')

    @patch('enmutils.lib.enm_node.Router6274Node._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_router_6274_node__init__(self, *_):
        router_6274_node = Router6274Node()
        self.assertEqual(router_6274_node.model_identity, 'R18Q2-GA')

    @patch('enmutils.lib.enm_node.MINILink810R1Node._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_ml_810r1_node__init__(self, *_):
        ml_810r1_node = MINILink810R1Node()
        self.assertEqual(ml_810r1_node.model_identity, 'M13B-CN810R1-1.0')

    @patch('enmutils.lib.enm_node.MINILink810R1Node._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_ml_810r2_node__init__(self, *_):
        ml_810r2_node = MINILink810R2Node()
        self.assertEqual(ml_810r2_node.model_identity, 'M16A-CN810R2-2.4FP')

    @patch('enmutils.lib.enm_node.TspNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_tsp_node__init__(self, *_):
        tsp_node = TspNode()
        self.assertEqual(tsp_node.transport_protocol, 'SSH')

    @patch('enmutils.lib.enm_node.TransportNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_transport_node__init__(self, *_):
        transport_node = TransportNode(primary_type="type", node_version="version")
        self.assertEqual(transport_node.NE_TYPE, 'type-version')

    @patch('enmutils.lib.enm_node.JuniperMXNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_juniper_node__init__18_3_version(self, *_):
        juniper_node = JuniperMXNode(node_version="18.3")
        self.assertEqual(juniper_node.NE_TYPE, 'JUNIPER-MX')
        self.assertEqual(juniper_node.model_identity, '18.3R1')

    @patch('enmutils.lib.enm_node.JuniperMXNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_juniper_node__init__(self, *_):
        juniper_node = JuniperMXNode(node_version="18")
        self.assertEqual(juniper_node.NE_TYPE, 'JUNIPER-MX')
        self.assertEqual(juniper_node.model_identity, '')

    @patch('enmutils.lib.enm_node.ESCNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_esc_node__init__(self, *_):
        esc_node = ESCNode()
        self.assertEqual(esc_node.NE_TYPE, 'ESC')
        self.assertEqual(esc_node.model_identity, '13A')

    @patch('enmutils.lib.enm_node.ERSSupportNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_ers_support_node__init__(self, *_):
        ers_support_node = ERSSupportNode()
        self.assertEqual(ers_support_node.NE_TYPE, 'ERS-SupportNode')
        self.assertEqual(ers_support_node.model_identity, '13A')

    @patch('enmutils.lib.enm_node.StnNode._get_snmp_version', return_value="")
    @patch('enmutils.lib.enm_node.config.has_prop', return_value=False)
    def test_stn_node__init__stn_ne_type(self, *_):
        stn_node = StnNode(simulation="SIM-TCU", NE_TYPE="STN")
        self.assertEqual(stn_node.NE_TYPE, 'TCU')

    def test_get_nodes_by_cell_size__success(self):
        user, response = Mock(), Mock()
        response.get_output.return_value = [u'netsim_LTE02ERBS00017	1	LTE02ERBS00017-1',
                                            u'netsim_LTE02ERBS00029	1	LTE02ERBS00029-2']
        user.enm_execute.return_value = response
        self.assertEqual(get_nodes_by_cell_size(1, user), [u'LTE02ERBS00017'])

    def test_get_enm_network_element_sync_states__success(self):
        user, response = Mock(), Mock()
        response.get_output.return_value = [u'', u'', u'Node\tvalue\tSYNCED', u'', u'']
        user.enm_execute.return_value = response
        self.assertDictEqual({u'Node': u'SYNCED'}, get_enm_network_element_sync_states(user))

    def test_get_enm_network_element_sync_states__raises_enm_application_error(self):
        user, response = Mock(), Mock()
        response.get_output.return_value = [u'Error']
        user.enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, get_enm_network_element_sync_states, user)

    @patch("enmutils.lib.enm_node.config.has_prop", return_value=True)
    @patch("enmutils.lib.enm_node.config.get_prop")
    def test_get_snmp_version__returns_version_value(self, *_):
        test_obj = BaseNode(node_id="Node")
        self.assertEqual(test_obj._get_snmp_version(), SnmpVersion.SNMP_V3)


class SNMPVersionUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.snmp_version = SnmpVersion(SnmpVersion.SNMP_V3)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_snmp_version__str__success(self):
        self.assertEqual(str(self.snmp_version), "SNMP_V3")

    def test_snmp_version__lt__success(self):
        self.assertFalse(self.snmp_version.__lt__(SnmpVersion(SnmpVersion.SNMP_V1)))

    def test_from_arne_value__success(self):
        self.assertEqual("SNMP_V3", str(self.snmp_version.from_arne_value("v3")))

    def test_from_arne_value__invalid_version(self):
        self.assertRaises(ValueError, self.snmp_version.from_arne_value, "v5")

    def test_from_enm_value__success(self):
        self.assertEqual("SNMP_V3", str(self.snmp_version.from_enm_value("SNMP_V3")))

    def test_from_enm_value__invalid_version(self):
        self.assertRaises(ValueError, self.snmp_version.from_enm_value, "v5")


class SnmpEncryptionMethodUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.snmp_encrypt = SnmpEncryptionMethod(SnmpEncryptionMethod.AES_128)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_snmp_encryption__str__success(self):
        self.assertEqual("AES128", str(self.snmp_encrypt))

    def test_from_enm_value__success(self):
        self.assertEqual("AES128", str(self.snmp_encrypt.from_enm_value("AES128")))

    def test_from_enm_value__invalid_version(self):
        self.assertRaises(ValueError, self.snmp_encrypt.from_enm_value, "AES256")

    def test_from_arne_value__success(self):
        self.assertEqual("AES128", str(self.snmp_encrypt.from_arne_value("AES-128")))

    def test_from_arne_value__invalid_version(self):
        self.assertRaises(ValueError, self.snmp_encrypt.from_arne_value, "AES256")


class SnmpAuthenticationMethodUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.snmp_auth = SnmpAuthenticationMethod(SnmpAuthenticationMethod.SHA)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_snmp_auth__str__success(self):
        self.assertEqual("SHA1", str(self.snmp_auth))

    def test_from_enm_value__success(self):
        self.assertEqual("SHA1", str(self.snmp_auth.from_enm_value("SHA1")))

    def test_from_enm_value__invalid_version(self):
        self.assertRaises(ValueError, self.snmp_auth.from_enm_value, "SHA2")

    def test_from_arne_value__success(self):
        self.assertEqual("SHA1", str(self.snmp_auth.from_arne_value("SHA")))

    def test_from_arne_value__invalid_version(self):
        self.assertRaises(ValueError, self.snmp_auth.from_arne_value, "SHA2")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
