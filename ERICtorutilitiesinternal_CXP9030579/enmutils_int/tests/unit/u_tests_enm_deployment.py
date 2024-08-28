#!/usr/bin/env python
import unittest2
from mock import patch, Mock, call
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib import enm_deployment
from testslib import unit_test_utils


class ENMDeploymentUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.libvirt_instances_dir_list = ("cmserv\nfmserv\nkpiserv\nmedrouter\nmspm\nnbalarmirp\nnetex\nsecserv\nsolr"
                                           "\nsupervc\nvisinamingnb\nwpserv")
        self.svc_vm_list = ('{"_embedded": {"item": [{"properties": {"hostname": "svc-1"}}, {"properties": '
                            '{"hostname": "svc-2"}}]}}')
        self.db_vm_list = ('{"_embedded": {"item": [{"properties": {"hostname": "db-44"}}, {"properties": '
                           '{"hostname": "db-91"}}]}}')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.enm_deployment.json.loads")
    def test_get_service_ip__is_successful(self, mock_loads, mock_run_cmd_on_ms):
        mock_loads.return_value = {
            "some_key": "some_value",
            "properties": {
                "host_device": "br1",
                "node_ip_map": "{'svc-1': {'ipv4': '10.247.246.130'}}",
                "device_name": "eth0",
                "ipaddresses": "some_ip_address",
                "network_name": "internal",
                "gateway": "some_gateway_ip",
                "node_mac_address_map": "{'31130cloud-svc-1-fmserveth0': '52:54:00:88:c3:77'}"
            }
        }

        mock_run_cmd_on_ms.return_value = Mock(rc=0)
        self.assertEqual("some_ip_address", enm_deployment.get_service_ip("fmserv"))
        litp_command = ("/usr/bin/python /usr/bin/litp show -p /deployments/enm/clusters/svc_cluster/services/fmserv/"
                        "applications/vm-service_fmserv/vm_network_interfaces/internal --json")
        mock_run_cmd_on_ms.assert_called_with(litp_command)

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.enm_deployment.json.loads")
    def test_get_service_ip__raises_runtimeerror_if_litp_command_is_unsuccessful(self, mock_loads, mock_run_cmd_on_ms):
        mock_run_cmd_on_ms.return_value = Mock(rc=1)
        self.assertRaises(RuntimeError, enm_deployment.get_service_ip, "fmserv")
        self.assertTrue(mock_run_cmd_on_ms.called)
        self.assertFalse(mock_loads.called)

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_ms")
    def test_get_service_hosts(self, mock_run_cmd_on_ms):
        response = Mock()
        response.rc = 0
        response.stdout = '{\n    "_embedded": {\n        "item": [\n            {\n                "item-type-name": "reference-to-collection-of-vm-ssh-key", \n                "applied_properties_determinable": true, \n                "state": "Applied", \n                "_links": {\n                    "inherited-from": {\n                        "href": "https://localhost:9999/litp/rest/v1/software/services/scripting/vm_ssh_keys"\n                    }, \n                    "self": {\n                        "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting/vm_ssh_keys"\n                    }, \n                    "collection-of": {\n                        "href": "https://localhost:9999/litp/rest/v1/item-types/vm-ssh-key"\n                    }\n                }, \n                "id": "vm_ssh_keys"\n            }, \n            {\n                "item-type-name": "reference-to-collection-of-vm-ram-mount", \n                "applied_properties_determinable": true, \n                "state": "Applied", \n                "_links": {\n                    "inherited-from": {\n                        "href": "https://localhost:9999/litp/rest/v1/software/services/scripting/vm_ram_mounts"\n                    }, \n                    "self": {\n                        "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting/vm_ram_mounts"\n                    }, \n                    "collection-of": {\n                        "href": "https://localhost:9999/litp/rest/v1/item-types/vm-ram-mount"\n                    }\n                }, \n                "id": "vm_ram_mounts"\n            }, \n            {\n                "item-type-name": "reference-to-collection-of-vm-nfs-mount", \n                "applied_properties_determinable": true, \n                "state": "Applied", \n                "_links": {\n                    "inherited-from": {\n                        "href": "https://localhost:9999/litp/rest/v1/software/services/scripting/vm_nfs_mounts"\n                    }, \n                    "self": {\n                        "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting/vm_nfs_mounts"\n                    }, \n                    "collection-of": {\n                        "href": "https://localhost:9999/litp/rest/v1/item-types/vm-nfs-mount"\n                    }\n                }, \n                "id": "vm_nfs_mounts"\n            }, \n            {\n                "item-type-name": "reference-to-collection-of-vm-network-interface", \n                "applied_properties_determinable": true, \n                "state": "Applied", \n                "_links": {\n                    "inherited-from": {\n                        "href": "https://localhost:9999/litp/rest/v1/software/services/scripting/vm_network_interfaces"\n                    }, \n                    "self": {\n                        "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting/vm_network_interfaces"\n                    }, \n                    "collection-of": {\n                        "href": "https://localhost:9999/litp/rest/v1/item-types/vm-network-interface"\n                    }\n                }, \n                "id": "vm_network_interfaces"\n            }, \n            {\n                "item-type-name": "reference-to-collection-of-vm-alias", \n                "applied_properties_determinable": true, \n                "state": "Applied", \n                "_links": {\n                    "inherited-from": {\n                        "href": "https://localhost:9999/litp/rest/v1/software/services/scripting/vm_aliases"\n                    }, \n                    "self": {\n                        "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting/vm_aliases"\n                    }, \n                    "collection-of": {\n                        "href": "https://localhost:9999/litp/rest/v1/item-types/vm-alias"\n                    }\n                }, \n                "id": "vm_aliases"\n            }, \n            {\n                "item-type-name": "reference-to-collection-of-vm-yum-repo", \n                "applied_properties_determinable": true, \n                "state": "Applied", \n                "_links": {\n                    "inherited-from": {\n                        "href": "https://localhost:9999/litp/rest/v1/software/services/scripting/vm_yum_repos"\n                    }, \n                    "self": {\n                        "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting/vm_yum_repos"\n                    }, \n                    "collection-of": {\n                        "href": "https://localhost:9999/litp/rest/v1/item-types/vm-yum-repo"\n                    }\n                }, \n                "id": "vm_yum_repos"\n            }, \n            {\n                "item-type-name": "reference-to-collection-of-vm-disk", \n                "applied_properties_determinable": true, \n                "state": "Applied", \n                "_links": {\n                    "inherited-from": {\n                        "href": "https://localhost:9999/litp/rest/v1/software/services/scripting/vm_disks"\n                    }, \n                    "self": {\n                        "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting/vm_disks"\n                    }, \n                    "collection-of": {\n                        "href": "https://localhost:9999/litp/rest/v1/item-types/vm-disk"\n                    }\n                }, \n                "id": "vm_disks"\n            }, \n            {\n                "item-type-name": "reference-to-collection-of-software-item", \n                "applied_properties_determinable": true, \n                "state": "Applied", \n                "_links": {\n                    "inherited-from": {\n                        "href": "https://localhost:9999/litp/rest/v1/software/services/scripting/packages"\n                    }, \n                    "self": {\n                        "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting/packages"\n                    }, \n                    "ref-collection-of": {\n                        "href": "https://localhost:9999/litp/rest/v1/item-types/software-item"\n                    }\n                }, \n                "id": "packages"\n            }, \n            {\n                "item-type-name": "reference-to-collection-of-vm-package", \n                "applied_properties_determinable": true, \n                "state": "Applied", \n                "_links": {\n                    "inherited-from": {\n                        "href": "https://localhost:9999/litp/rest/v1/software/services/scripting/vm_packages"\n                    }, \n                    "self": {\n                        "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting/vm_packages"\n                    }, \n                    "collection-of": {\n                        "href": "https://localhost:9999/litp/rest/v1/item-types/vm-package"\n                    }\n                }, \n                "id": "vm_packages"\n            }\n        ]\n    }, \n    "properties-overwritten": [\n        "adaptor_version", \n        "node_hostname_map", \n        "image_checksum"\n    ], \n    "id": "vm-service_scripting", \n    "item-type-name": "reference-to-vm-service", \n    "applied_properties_determinable": true, \n    "state": "Applied", \n    "_links": {\n        "inherited-from": {\n            "href": "https://localhost:9999/litp/rest/v1/software/services/scripting"\n        }, \n        "self": {\n            "href": "https://localhost:9999/litp/rest/v1/deployments/enm/clusters/scp_cluster/services/scripting/applications/vm-service_scripting"\n        }, \n        "item-type": {\n            "href": "https://localhost:9999/litp/rest/v1/item-types/vm-service"\n        }\n    }, \n    "properties": {\n        "adaptor_version": "1.15.1-1", \n        "internal_status_check": "on", \n        "service_name": "scripting", \n        "node_hostname_map": "{\'scp-1\': \'scp-1-scripting\', \'scp-2\': \'scp-2-scripting\'}", \n        "ram": "102400M", \n        "cpus": "16", \n        "image_name": "lsb-image", \n        "cleanup_command": "/sbin/service scripting stop-undefine --stop-timeout=300", \n        "image_checksum": "54773cb08b4b25b25506685e9fbc23e7"\n    }\n}\n'
        mock_run_cmd_on_ms.return_value = response
        res = enm_deployment.get_service_hosts('scripting', 'scp')
        self.assertEqual(res, ['scp-1-scripting', 'scp-2-scripting'])

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_ms")
    def test_get_service_hosts_raises_runtime_on_wrong_rc(self, mock_run_cmd_on_ms):
        response = Mock()
        response.rc = 2
        response.stdout = ''
        mock_run_cmd_on_ms.return_value = response
        self.assertRaises(EnvironError, enm_deployment.get_service_hosts, 'scripting', 'scp')

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_ms")
    def test_check_if_cluster_exists(self, mock_run_cmd_on_ms):
        response = Mock()
        response.rc = 0
        response.stdout = 'evt_cluster'
        mock_run_cmd_on_ms.return_value = response
        res = enm_deployment.check_if_cluster_exists('evt')
        self.assertEqual(res, True)

        response.stdout = ''
        mock_run_cmd_on_ms.return_value = response
        res = enm_deployment.check_if_cluster_exists('evt')
        self.assertEqual(res, False)

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_ms")
    def test_check_if_cluster_exists_raises_runtime_on_wrong_rc(self, mock_run_cmd_on_ms):
        response = Mock()
        response.rc = 2
        response.stdout = ''
        mock_run_cmd_on_ms.return_value = response
        self.assertRaises(RuntimeError, enm_deployment.check_if_cluster_exists, 'evt')

    # check_if_ebs_tag_exists test cases
    @patch("enmutils_int.lib.enm_deployment.shell.Command")
    @patch("enmutils_int.lib.enm_deployment.get_enm_cloud_native_namespace", return_value="en   m200")
    @patch("enmutils_int.lib.enm_deployment.log.logger.debug")
    @patch("enmutils_int.lib.enm_deployment.shell.run_local_cmd")
    def test_check_if_ebs_tag_exists__if_tag_name_is_value_pack_ebs_m(self, mock_run_local_cmd, mock_debug_log,
                                                                      mock_get_enm_cloud_native_namespace, _):
        response = Mock(rc=0, stdout="value_pack_ebs_m=true\n")
        mock_run_local_cmd.return_value = response
        self.assertEqual(enm_deployment.check_if_ebs_tag_exists("value_pack_ebs_m"), True)
        self.assertTrue(mock_debug_log.called)
        self.assertTrue(mock_get_enm_cloud_native_namespace.called)

    @patch("enmutils_int.lib.enm_deployment.shell.Command")
    @patch("enmutils_int.lib.enm_deployment.get_enm_cloud_native_namespace", return_value="enm200")
    @patch("enmutils_int.lib.enm_deployment.log.logger.debug")
    @patch("enmutils_int.lib.enm_deployment.shell.run_local_cmd")
    def test_check_if_ebs_tag_exists__if_value_pack_ebs_m_is_false(self, mock_run_local_cmd, mock_debug_log,
                                                                   mock_get_enm_cloud_native_namespace, _):
        response = Mock(rc=0, stdout="value_pack_ebs_m=false\n")
        mock_run_local_cmd.return_value = response
        self.assertEqual(enm_deployment.check_if_ebs_tag_exists("value_pack_ebs_m"), False)
        self.assertTrue(mock_debug_log.called)
        self.assertTrue(mock_get_enm_cloud_native_namespace.called)

    @patch("enmutils_int.lib.enm_deployment.shell.Command")
    @patch("enmutils_int.lib.enm_deployment.get_enm_cloud_native_namespace", return_value="enm200")
    @patch("enmutils_int.lib.enm_deployment.log.logger.debug")
    @patch("enmutils_int.lib.enm_deployment.shell.run_local_cmd")
    def test_check_if_ebs_tag_exists__raises_env_error(self, mock_run_local_cmd, mock_debug_log,
                                                       mock_get_enm_cloud_native_namespace, _):
        response = Mock(rc=1, stdout="error")
        mock_run_local_cmd.return_value = response
        self.assertRaises(EnvironError, enm_deployment.check_if_ebs_tag_exists, "value_pack_ebs_m")
        self.assertFalse(mock_debug_log.called)
        self.assertTrue(mock_get_enm_cloud_native_namespace.called)

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_vm")
    def test_get_service_ip_addresses_via_consul(self, mock_run_cmd_on_vm):
        response = Mock()
        response.rc = 0
        response.stdout = ('ieatenmc5a01-cmserv-0   f367a855   ip_1\n'
                           'ieatenmc5a01-cmserv-1   f367a855   ip_2\n'
                           'ieatenmc5a01-mspm-4     f367a855   ip_3')
        mock_run_cmd_on_vm.return_value = response
        result = enm_deployment.get_service_ip_addresses_via_consul("cmserv")
        self.assertEqual(result, ['ip_1', 'ip_2', 'ip_3'])

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_vm")
    def test_get_service_ip_addresses_via_consul_raises_environ_error(self, mock_run_cmd_on_vm):
        mock_run_cmd_on_vm.return_value = Mock(rc=5, stdout="Error")
        self.assertRaises(EnvironError, enm_deployment.get_service_ip_addresses_via_consul, "zx")

    @patch("enmutils.lib.shell.run_cmd_on_vm")
    def test_get_service_ip_addresses_via_consul_raises_environ_error_2(self, mock_run_cmd_on_vm):
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout="No nodes match the given query")
        self.assertRaises(EnvironError, enm_deployment.get_service_ip_addresses_via_consul, "zx")

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_vm")
    def test_get_cloud_members_list_dict_raises_environ_error(self, mock_run_cmd_on_vm):
        mock_run_cmd_on_vm.return_value = Mock(rc=5, stdout="Error")
        self.assertRaises(EnvironError, enm_deployment.get_cloud_members_list_dict)

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_vm")
    def test_get_cloud_members_list_dict(self, mock_run_cmd_on_vm):
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout="ms  ip_1\ncm    ip_2\npm    ip_3")
        cloud_dict = enm_deployment.get_cloud_members_list_dict()
        self.assertTrue(len(cloud_dict.keys()) is 3)
        for _ in ["ip_1", "ip_2", "ip_3"]:
            self.assertIn(_, cloud_dict.values())

    @patch("enmutils_int.lib.enm_deployment.get_values_from_global_properties")
    @patch("enmutils_int.lib.enm_deployment.get_cloud_members_list_dict")
    def test_get_cloud_members_ip_addresses_returns_list_of_requested_service_ips(
            self, mock_get_cloud_members_list_dict, mock_get_values_from_global_properties):
        consul_members = {"ieatenmc5a01-cmserv-0": "ip_1",
                          "ieatenmc5a01-cmserv-1": "ip_2",
                          "ieatenmc5a01-mspm-4": "ip_3"}
        mock_get_cloud_members_list_dict.return_value = consul_members
        self.assertEqual(['ip_1', 'ip_2'], enm_deployment.get_cloud_members_ip_address("cmserv"))
        self.assertFalse(mock_get_values_from_global_properties.called)

    @patch("enmutils_int.lib.enm_deployment.get_values_from_global_properties", return_value=["naming_ip"])
    @patch("enmutils_int.lib.enm_deployment.get_cloud_members_list_dict")
    def test_get_cloud_members_ip_addresses__returns_ip_of_visinamingnb(
            self, mock_get_cloud_members_list_dict, *_):
        self.assertEqual(["naming_ip"], enm_deployment.get_cloud_members_ip_address("visinamingnb"))
        self.assertFalse(mock_get_cloud_members_list_dict.called)

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms")
    def test_get_values_from_global_properties__is_successful(self, mock_run_cmd_on_emp_or_ms):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=0, stdout='ip_1,ip_2')
        expected_output = ['ip_1', 'ip_2']
        self.assertEqual(enm_deployment.get_values_from_global_properties('server'), expected_output)

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms")
    def test_get_values_from_global_properties__is_successful_for_ipv6(self, mock_run_cmd_on_emp_or_ms):
        mock_run_cmd_on_emp_or_ms.side_effect = [Mock(rc=0, stdout=','), Mock(rc=0, stdout='ipv6_1,ipv6_2')]
        expected_output = ['ipv6_1', 'ipv6_2']
        self.assertEqual(enm_deployment.get_values_from_global_properties('server_IPs'), expected_output)

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms")
    def test_get_values_from_global_properties__raises_environerror(
            self, mock_run_cmd_on_emp_or_ms):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=1, stdout='')
        self.assertRaises(EnvironError, enm_deployment.get_values_from_global_properties, 'server')

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms")
    def test_get_values_from_global_properties__raises_environerror_while_getting_empty_response(
            self, mock_run_cmd_on_emp_or_ms):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=0, stdout='')
        self.assertRaises(EnvironError, enm_deployment.get_values_from_global_properties, 'server')

    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.enm_deployment.deployment_info_helper_methods.get_cloud_native_service_vip")
    @patch("enmutils_int.lib.enm_deployment.get_values_from_global_properties")
    def test_get_list_of_scripting_service_ips__is_successful_for_physical_or_cloud(
            self, mock_get_values_from_global_properties, mock_get_cloud_native_service_vip, _):
        enm_deployment.get_list_of_scripting_service_ips()
        self.assertEqual(mock_get_values_from_global_properties.call_count, 1)
        self.assertFalse(mock_get_cloud_native_service_vip.called)
        mock_get_values_from_global_properties.assert_called_with("scripting_service_IPs")

    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.enm_deployment.deployment_info_helper_methods.get_cloud_native_service_vip")
    @patch("enmutils_int.lib.enm_deployment.get_values_from_global_properties")
    def test_get_list_of_scripting_service_ips__is_successful_on_cloud_native(
            self, mock_get_values_from_global_properties, mock_get_cloud_native_service_vip, _):
        enm_deployment.get_list_of_scripting_service_ips()
        self.assertFalse(mock_get_values_from_global_properties.called)
        self.assertEqual(mock_get_cloud_native_service_vip.call_count, 1)
        mock_get_cloud_native_service_vip.assert_called_with("general-scripting")

    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    def test_get_pib_value__is_successful(self, mock_admin):
        response = Mock()
        response.get_output.return_value = ["ABDD", "u: 555"]
        mock_admin.return_value.enm_execute.return_value = response
        self.assertEqual(enm_deployment.get_pib_value_from_enm("pmserv", "some_pib_parameter"), "555")

    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    def test_get_pib_value__returns_none_if_command_execution_throws_exception(self, mock_admin, *_):
        mock_admin.return_value.enm_execute.side_effect = Exception
        self.assertRaises(EnmApplicationError, enm_deployment.get_pib_value_from_enm, "pmserv", "some_pib_parameter")

    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms", return_value=Mock(rc=1, stdout="Problem\n"))
    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    def test_get_pib_value__returns_none_if_command_output_result_in_non_zero_result_code(self, mock_admin, _):
        response = Mock()
        response.get_output.return_value = ["ABDD", "error"]
        mock_admin.return_value.enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, enm_deployment.get_pib_value_from_enm, "pmserv", "some_pib_parameter")

    @patch("enmutils_int.lib.enm_deployment.get_values_from_global_properties", return_value=["ip_a", "ip_b"])
    @patch("enmutils_int.lib.enm_deployment.get_pib_value_from_enm", return_value="555")
    def test_fetch_pib_parameter_value__is_successful(self, *_):
        self.assertEqual(enm_deployment.fetch_pib_parameter_value("pmserv", "some_pib_parameter"), "555")

    @patch("enmutils_int.lib.enm_deployment.get_values_from_global_properties", return_value=["ip_a", "ip_b"])
    @patch("enmutils_int.lib.enm_deployment.get_pib_value_from_enm", return_value="555 ")
    def test_fetch_pib_parameter_value__is_successful_with_spaces(self, *_):
        self.assertEqual(enm_deployment.fetch_pib_parameter_value("pmserv", "some_pib_parameter"), "555")

    @patch("enmutils_int.lib.enm_deployment.get_values_from_global_properties", return_value=[])
    def test_fetch_pib_parameter_value__returns_none_if_no_application_ip_not_set_in_global_properties(self, _):
        self.assertRaises(EnvironError, enm_deployment.fetch_pib_parameter_value, "pmserv", "some_pib_parameter")

    @patch("enmutils_int.lib.enm_deployment.get_values_from_global_properties", return_value=["ip_a", "ip_b"])
    @patch("enmutils_int.lib.enm_deployment.get_pib_value_from_enm", return_value=None)
    def test_fetch_pib_parameter_value__returns_none_if_cant_get_pib_value(self, *_):
        self.assertEqual(enm_deployment.fetch_pib_parameter_value("pmserv", "some_pib_parameter"), None)

    @patch("enmutils_int.lib.enm_deployment.get_values_from_global_properties", return_value=["ip_a", "ip_b"])
    @patch("enmutils_int.lib.enm_deployment.get_pib_value_from_enm", side_effect=EnmApplicationError)
    def test_fetch_pib_parameter_value__returns_none_if_get_pib_returns_enmapplicationerror(self, *_):
        self.assertEqual(enm_deployment.fetch_pib_parameter_value("pmserv", "some_pib_parameter"), None)

    @patch("enmutils_int.lib.enm_deployment.get_enm_cloud_native_namespace", return_value="my_enm")
    @patch("enmutils_int.lib.enm_deployment.shell.Command")
    @patch("enmutils_int.lib.enm_deployment.shell.run_local_cmd")
    def test_get_service_hostnames_in_cloud_native__is_successful(self, mock_run_local_cmd, mock_command, _):
        output = "NAME                                               READY   STATUS      RESTARTS   AGE\n" \
                 "accesscontrol-5bb88f5ff8-zjp29                     1/1     Running     0          10h\n" \
                 "cmserv-f5d9d94bd-rb4f8                             1/1     Running     0          10h\n" \
                 "consul-0                                           1/1     Running     0          10h\n"
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=output)
        self.assertEqual(["cmserv-f5d9d94bd-rb4f8"], enm_deployment.get_pod_hostnames_in_cloud_native("cmserv"))
        mock_command.assert_called_with("/usr/local/bin/kubectl --kubeconfig /root/.kube/config get pods -n my_enm 2>/dev/null")

    @patch("enmutils_int.lib.enm_deployment.shell.Command")
    @patch("enmutils_int.lib.enm_deployment.get_enm_cloud_native_namespace")
    @patch("enmutils_int.lib.enm_deployment.shell.run_local_cmd")
    def test_get_service_hostnames_in_cloud_native__raises_environerror_if_kubectl_cmd_execution_has_problems(
            self, mock_run_local_cmd, *_):
        mock_run_local_cmd.return_value = Mock(rc=1, stdout="some_error\n")
        self.assertRaises(EnvironError, enm_deployment.get_pod_hostnames_in_cloud_native, "cmserv")

    @patch("enmutils_int.lib.enm_deployment.get_pod_hostnames_in_cloud_native", return_value=["A", "B"])
    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=True)
    def test_get_enm_service_locations__is_successful_for_cloud_native(self, *_):
        self.assertEqual(["A", "B"], enm_deployment.get_enm_service_locations("some_service"))

    @patch("enmutils_int.lib.enm_deployment.get_service_ip_addresses_via_consul", return_value=["A", "B"])
    @patch("enmutils_int.lib.enm_deployment.is_emp", return_value=True)
    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=False)
    def test_get_enm_service_locations__is_successful_for_cloud_openstack(self, *_):
        self.assertEqual(["A", "B"], enm_deployment.get_enm_service_locations("some_service"))

    @patch("enmutils_int.lib.enm_deployment.get_service_hosts", return_value=["A", "B"])
    @patch("enmutils_int.lib.enm_deployment.is_emp", return_value=False)
    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=False)
    def test_get_enm_service_locations__is_successful_for_physical(self, *_):
        self.assertEqual(["A", "B"], enm_deployment.get_enm_service_locations("some_service"))

    @patch("enmutils_int.lib.enm_deployment.get_service_hosts", side_effect=Exception)
    @patch("enmutils_int.lib.enm_deployment.is_emp", return_value=False)
    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=False)
    def test_get_enm_service_locations__raises_environerror_if_cannot_get_service_locations(self, *_):
        self.assertRaises(EnvironError, enm_deployment.get_enm_service_locations, "some_service")

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    @patch('enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms')
    def test_get_list_of_scripting_vms_host_names__successful_fetch(self, mock_run_cmd_on_emp_or_ms, _):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=0, stdout='scp-2-scripting\nscp-1-scripting')
        self.assertEqual(2, len(enm_deployment.get_list_of_scripting_vms_host_names()))

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    @patch('enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms')
    def test_get_list_of_scripting_vms_host_names__unsuccessful_fetch(self, mock_run_cmd_on_emp_or_ms, _):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=1, stdout='')
        self.assertEqual(0, len(enm_deployment.get_list_of_scripting_vms_host_names()))

    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    @patch("enmutils_int.lib.enm_deployment.get_enm_service_locations", return_value=["A", "B"])
    @patch("enmutils_int.lib.enm_deployment.set_pib_value_on_enm_service", side_effect=[False, True])
    def test_update_pib_parameter_on_enm__is_successful(self, mock_set_pib_value_on_enm_service, *_):
        self.assertTrue(enm_deployment.update_pib_parameter_on_enm("some_service", "some_name", "some_value",
                                                                   service_identifier="some_id", scope="some_scope"))
        self.assertEqual(2, mock_set_pib_value_on_enm_service.call_count)
        self.assertFalse(call("some_service", "A", "some_name", "some_value", service_identifier="some_id",
                              scope="some_scope") in mock_set_pib_value_on_enm_service.mock_calls)
        self.assertFalse(call("some_service", "B", "some_name", "some_value", service_identifier="some_id",
                              scope="some_scope") in mock_set_pib_value_on_enm_service.mock_calls)

    @patch("enmutils_int.lib.enm_deployment.set_pib_value_on_enm_service", side_effect=[False, False])
    def test_update_pib_parameter_on_enm__raises_enmapplicationerror(self, mock_set_pib_value_on_enm_service, *_):
        self.assertRaises(EnmApplicationError, enm_deployment.update_pib_parameter_on_enm,
                          "some_service", "some_name", "some_value", enm_service_locations=["A", "B"])
        self.assertEqual(2, mock_set_pib_value_on_enm_service.call_count)
        self.assertFalse(call("some_service", "A", "some_name", "some_value", service_identifier=None, scope=None)
                         in mock_set_pib_value_on_enm_service.mock_calls)
        self.assertFalse(call("some_service", "B", "some_name", "some_value", service_identifier=None, scope=None)
                         in mock_set_pib_value_on_enm_service.mock_calls)

    @patch("enmutils_int.lib.enm_deployment.get_enm_service_locations", return_value=[])
    @patch("enmutils_int.lib.enm_deployment.set_pib_value_on_enm_service", side_effect=[False, False])
    def test_update_pib_parameter_on_enm__raises_enmapplicationerror_if_no_locations_passed(
            self, mock_set_pib_value_on_enm_service, *_):
        self.assertRaises(EnmApplicationError, enm_deployment.update_pib_parameter_on_enm,
                          "some_service", "some_name", "some_value")
        self.assertEqual(0, mock_set_pib_value_on_enm_service.call_count)

    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    def test_set_pib_value_on_enm_service__returns_true_when_pib_update_is_successful(
            self, _):
        self.assertTrue(enm_deployment.set_pib_value_on_enm_service("some_service", "some_location", "some_name",
                                                                    "some_value"))

    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    def test_set_pib_value_on_enm_service__returns_false_when_pib_update_is_unsuccessful(self, _):
        self.assertTrue(enm_deployment.set_pib_value_on_enm_service("some_service", "some_location",
                                                                    "some_name", "some_value"))

    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    def test_set_pib_value_on_enm_service__throws_exception_when_pib_update_is_unsuccessful(self, mock_admin):
        mock_admin.return_value.enm_execute.side_effect = Exception
        self.assertEqual(None, enm_deployment.set_pib_value_on_enm_service("some_service", "some_location", "some_name",
                                                                           "some_value"))

    @patch("enmutils_int.lib.enm_deployment.get_enm_service_locations", return_value=['some_ip'])
    @patch("enmutils_int.lib.enm_deployment.get_pib_value_on_enm_service", return_value="5")
    def test_get_pib_value_on_enm__returns_value_when_pib_read_is_successful(
            self, mock_get_pib_value_on_enm_service, _):
        self.assertEqual("5", enm_deployment.get_pib_value_on_enm("some_service", "some_pib"))
        mock_get_pib_value_on_enm_service.assert_called_with('some_ip', "some_pib", None, )

    @patch("enmutils_int.lib.enm_deployment.get_enm_service_locations", return_value=[])
    @patch("enmutils_int.lib.enm_deployment.get_pib_value_on_enm_service")
    def test_get_pib_value_on_enm__raises_enm_application_error_due_to_no_enm_service_locations(
            self, mock_get_pib_value_on_enm_service, *_):
        self.assertRaises(EnmApplicationError, enm_deployment.get_pib_value_on_enm, "some_service", "some_name")
        self.assertFalse(mock_get_pib_value_on_enm_service.called)

    @patch("enmutils_int.lib.enm_deployment.get_enm_service_locations", side_effect=EnvironError('Error'))
    def test_get_pib_value_on_enm__get_enm_service_locations_raises_environ_error(self, _):
        self.assertRaises(EnvironError, enm_deployment.get_pib_value_on_enm, 'fmhistory', 'some_pib')

    @patch("enmutils_int.lib.enm_deployment.get_enm_service_locations",
           return_value=['first_location', 'second_location'])
    @patch("enmutils_int.lib.enm_deployment.get_pib_value_on_enm_service", side_effect=[None, '50'])
    def test_get_pib_value_on_enm__run_get_pib_value_on_enm_service_multiple_times(self, mock_get_pib_on_service, _):
        self.assertEqual('50', enm_deployment.get_pib_value_on_enm("some_service", 'some_pib'))
        self.assertEqual(2, mock_get_pib_on_service.call_count)

    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    @patch("enmutils_int.lib.enm_deployment.log.logger.error")
    def test_get_pib_value_on_enm_service__returns_none(self, mock_error, _):
        self.assertIsNone(enm_deployment.get_pib_value_on_enm_service("some_service", 'some_ip', "some_pib"))
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    @patch("enmutils_int.lib.enm_deployment.log.logger.error")
    def test_get_pib_value_on_enm_service__returns_value(self, mock_error, mock_admin):
        response = Mock()
        response.get_output.return_value = ["ABDD", "u: 555"]
        mock_admin.return_value.enm_execute.return_value = response
        self.assertEqual('555', enm_deployment.get_pib_value_on_enm_service("some_service", 'some_ip', "some_pib"))

    @patch('enmutils_int.lib.enm_deployment.run_pib_command_on_enm_service', return_value='5\n')
    @patch('enmutils_int.lib.enm_deployment.get_admin_user')
    def test_get_pin_value_on_enm_service__successful(self, mock_admin, _):
        self.assertEqual(None, enm_deployment.get_pib_value_on_enm_service("some_service", 'some_ip', 'some_pib'))

    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils.lib.shell.run_cmd_on_cloud_native_pod")
    def test_run_pib_command_on_enm_service__is_successful_on_cloud_native(self, mock_run_cmd_on_cloud_native_pod, *_):
        cmd = "python /opt/ericsson/PlatformIntegrationBridge/etc/config.py some_pip_parameters"
        mock_run_cmd_on_cloud_native_pod.return_value = Mock(rc=0)
        self.assertTrue(enm_deployment.run_pib_command_on_enm_service("some_service", "some_location",
                                                                      "some_pip_parameters"))
        mock_run_cmd_on_cloud_native_pod.assert_called_with("some_service", "some_location", cmd)

    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils.lib.shell.run_cmd_on_cloud_native_pod", side_effect=[Mock(rc=1), Mock(rc=0)])
    def test_run_pib_command_on_enm_service__is_successful_on_cloud_native_python3(self, mock_run_cmd_on_cloud_native_pod, *_):
        cmd = "python3 /opt/ericsson/PlatformIntegrationBridge/etc/config.py some_pip_parameters"
        self.assertTrue(enm_deployment.run_pib_command_on_enm_service("some_service", "some_location",
                                                                      "some_pip_parameters"))
        mock_run_cmd_on_cloud_native_pod.assert_called_with("some_service", "some_location", cmd)
        self.assertEqual(mock_run_cmd_on_cloud_native_pod.call_count, 2)

    @patch("enmutils_int.lib.enm_deployment.is_emp", return_value=True)
    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.enm_deployment.get_emp", return_value="EMP")
    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.enm_deployment.shell.Command")
    def test_run_pib_command_on_enm_service__is_successful_on_cloud_openstack(
            self, mock_command, mock_run_cmd_on_vm, *_):
        cmd = "sudo python /ericsson/pib-scripts/etc/config.py some_pip_parameters"
        mock_command.return_value = Mock()
        mock_run_cmd_on_vm.return_value = Mock(rc=0)
        self.assertTrue(enm_deployment.run_pib_command_on_enm_service("some_service", "some_location",
                                                                      "some_pip_parameters"))
        mock_command.assert_called_with(cmd)
        mock_run_cmd_on_vm.assert_called_with(mock_command.return_value, "EMP")

    @patch("enmutils_int.lib.enm_deployment.is_emp", return_value=False)
    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.enm_deployment.shell.Command")
    def test_run_pib_command_on_enm_service__is_successful_on_physical(self, mock_command, mock_run_cmd_on_ms, *_):
        cmd = "sudo python /ericsson/pib-scripts/etc/config.py some_pip_parameters"
        mock_run_cmd_on_ms.return_value = Mock(rc=0)
        self.assertTrue(enm_deployment.run_pib_command_on_enm_service("some_service", "some_location",
                                                                      "some_pip_parameters"))
        mock_command.assert_called_with(cmd)
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value)

    @patch("enmutils_int.lib.enm_deployment.is_emp", return_value=True)
    @patch("enmutils_int.lib.enm_deployment.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.enm_deployment.get_emp", return_value="EMP")
    @patch("enmutils_int.lib.enm_deployment.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.enm_deployment.shell.Command")
    def test_run_pib_command_on_enm_service__raises_exception_if_command_result_is_non_zero(
            self, mock_command, mock_run_cmd_on_vm, *_):
        cmd = "sudo python /ericsson/pib-scripts/etc/config.py some_pip_parameters"
        mock_command.return_value = Mock()
        mock_run_cmd_on_vm.return_value = Mock(rc=1)
        self.assertRaises(Exception, enm_deployment.run_pib_command_on_enm_service, "some_service", "some_location",
                          "some_pip_parameters")
        mock_command.assert_called_with(cmd)
        mock_run_cmd_on_vm.assert_called_with(mock_command.return_value, "EMP")

    def test_get_fdn_list_from_enm__is_successful(self):
        enm_user = Mock()

        parent_fdn = "SubNetwork=A,ManagedElement=node1,Equipment=1,FieldReplaceableUnit=1"
        fdn1 = "{0},RfPort=A".format(parent_fdn)
        fdn2 = "{0},RfPort=A".format(parent_fdn)
        fdn3 = "{0},RfPort=A".format(parent_fdn)

        fdn1_line = u'FDN : {0}'.format(fdn1)
        fdn2_line = u'FDN : {0}'.format(fdn2)
        fdn3_line = u'FDN : {0}'.format(fdn3)

        enm_output = [fdn1_line, u'', fdn2_line, u'', fdn3_line, u'', u'', u'3 instance(s)']
        expected_fdn_list = [fdn1, fdn2, fdn3]

        enm_user.enm_execute.return_value.get_output.return_value = enm_output
        fdn_list = enm_deployment.get_fdn_list_from_enm(enm_user, "RfPort")

        enm_user.enm_execute.assert_called_with("cmedit get * RfPort")
        self.assertEqual(fdn_list, expected_fdn_list)

    def test_get_fdn_list_from_enm__raises_enmapplicationerror_if_enm_returns_error(self):
        enm_user = Mock()

        enm_user.enm_execute.side_effect = EnmApplicationError("No response from ENM")
        with self.assertRaises(EnmApplicationError) as e:
            enm_deployment.get_fdn_list_from_enm(enm_user, "RfPort", enm_scope="Node1")

        msg = "ENM command execution unsuccessful: 'cmedit get Node1 RfPort' - No response from ENM"
        self.assertEqual(e.exception.message, msg)
        enm_user.enm_execute.assert_called_with("cmedit get Node1 RfPort")

    @patch("enmutils_int.lib.enm_deployment.get_mo_attributes_from_enm")
    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_pm_function_enabled_nodes__is_successful(self, mock_debug, mock_get_mo_attributes_from_enm):
        node1 = Mock(node_id="node1")
        node2 = Mock(node_id="node2")
        node3 = Mock(node_id="node3")
        mock_get_mo_attributes_from_enm.return_value = {"node1": {"pmEnabled": "false"},
                                                        "node2": {"pmEnabled": "true"},
                                                        "node3": {"pmEnabled": "false"}}
        pm_enabled_nodes, pm_disabled_nodes = enm_deployment.get_pm_function_enabled_nodes([node1, node2, node3],
                                                                                           Mock())
        self.assertTrue(mock_debug.called)
        self.assertEqual(1, len(pm_enabled_nodes))
        self.assertEqual(2, len(pm_disabled_nodes))
        self.assertTrue(mock_get_mo_attributes_from_enm.called)

    @patch("enmutils_int.lib.enm_deployment.get_mo_attributes_from_enm")
    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_pm_function_enabled_nodes__if_no_nodes_supplied(self, mock_debug, mock_get_mo_attributes_from_enm):
        pm_enabled_nodes, pm_disabled_nodes = enm_deployment.get_pm_function_enabled_nodes([], Mock())
        self.assertTrue(mock_debug.called)
        self.assertEqual(0, len(pm_enabled_nodes))
        self.assertEqual(0, len(pm_disabled_nodes))
        self.assertFalse(mock_get_mo_attributes_from_enm.called)

    @patch("enmutils_int.lib.enm_deployment.get_mo_attributes_from_enm")
    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_pm_function_enabled_nodes__raises_enm_application_error(self, mock_debug,
                                                                         mock_get_mo_attributes_from_enm):
        node1 = Mock(node_id="node1")
        node2 = Mock(node_id="node2")
        node3 = Mock(node_id="node3")
        mock_get_mo_attributes_from_enm.side_effect = EnmApplicationError("Error occurred while getting NE PmFunction"
                                                                          " status from ENM - Error")
        self.assertRaises(EnmApplicationError, enm_deployment.get_pm_function_enabled_nodes, [node1, node2, node3],
                          Mock())
        self.assertFalse(mock_debug.called)
        self.assertTrue(mock_get_mo_attributes_from_enm.called)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_mo_attributes_from_enm__getting_single_mo_attribute_value(self, mock_debug_log):
        enm_user = Mock()
        enm_output = [u'NetworkElement,PmFunction', u'NodeId\tPmFunctionId\tpmEnabled',
                      u'netsim_LTE02ERBS00007\t1\ttrue', u'netsim_LTE02ERBS00008\t1\ttrue',
                      u'netsim_LTE02ERBS00040\t1\ttrue', u'netsim_LTE02ERBS00025\t1\tfalse', u'', u'4 instance(s)']
        enm_user.enm_execute.return_value.get_output.return_value = enm_output
        excepted_output = {u'netsim_LTE02ERBS00008': {'pmEnabled': u'true'},
                           u'netsim_LTE02ERBS00025': {'pmEnabled': u'false'},
                           u'netsim_LTE02ERBS00040': {'pmEnabled': u'true'},
                           u'netsim_LTE02ERBS00007': {'pmEnabled': u'true'}}
        response = enm_deployment.get_mo_attributes_from_enm(enm_user=enm_user, mo_type="PmFunction",
                                                             mo_attributes=["pmEnabled"])
        self.assertTrue(mock_debug_log.called)
        self.assertEqual(response, excepted_output)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_mo_attributes_from_enm__getting_multiple_mo_attributes_values(self, mock_debug_log):
        enm_user = Mock()
        enm_output = [u'NetworkElement,PmFunction',
                      u'NodeId\tPmFunctionId\tfileCollectionState\tpmEnabled\tscannerMasterState',
                      u'netsim_LTE02ERBS00007\t1\tENABLED\ttrue\tENABLED',
                      u'netsim_LTE02ERBS00008\t1\tENABLED\ttrue\tENABLED', u'', u'2 instance(s)']
        enm_user.enm_execute.return_value.get_output.return_value = enm_output
        excepted_output = {
            u'netsim_LTE02ERBS00008': {'scannerMasterState': u'ENABLED', 'fileCollectionState': u'true',
                                       'pmEnabled': u'ENABLED'},
            u'netsim_LTE02ERBS00007': {'scannerMasterState': u'ENABLED', 'fileCollectionState': u'true',
                                       'pmEnabled': u'ENABLED'}}
        response = enm_deployment.get_mo_attributes_from_enm(enm_user=enm_user, mo_type="PmFunction",
                                                             mo_attributes=["scannerMasterState", "fileCollectionState",
                                                                            "pmEnabled"])
        self.assertTrue(mock_debug_log.called)
        self.assertEqual(response, excepted_output)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_mo_attributes_from_enm__getting_single_node_mo_attributes_values(self, mock_debug_log):
        enm_user = Mock()
        enm_output = [u'NetworkElement,PmFunction',
                      u'NodeId\tPmFunctionId\tfileCollectionState\tpmEnabled\tscannerMasterState',
                      u'netsim_LTE02ERBS00007\t1\tENABLED\ttrue\tENABLED', u'', u'1 instance(s)']
        enm_user.enm_execute.return_value.get_output.return_value = enm_output
        excepted_output = {
            u'netsim_LTE02ERBS00007': {'scannerMasterState': u'ENABLED', 'fileCollectionState': u'true',
                                       'pmEnabled': u'ENABLED'}}
        response = enm_deployment.get_mo_attributes_from_enm(enm_user=enm_user, mo_type="PmFunction",
                                                             mo_attributes=["scannerMasterState", "fileCollectionState",
                                                                            "pmEnabled"],
                                                             scope=["netsim_LTE02ERBS00007"])
        self.assertTrue(mock_debug_log.called)
        self.assertEqual(response, excepted_output)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_mo_attributes_from_enm__getting_multiple_nodes_mo_attributes_values(self, mock_debug_log):
        enm_user = Mock()
        enm_output = [u'NetworkElement,PmFunction',
                      u'NodeId\tPmFunctionId\tfileCollectionState\tpmEnabled\tscannerMasterState',
                      u'netsim_LTE02ERBS00007\t1\tENABLED\ttrue\tENABLED',
                      u'LTE01dg2ERBS00003\t1\tENABLED\ttrue\tENABLED',
                      u'LTE01dg2ERBS00028\t1\tENABLED\ttrue\tENABLED', u'', u'3 instance(s)']
        enm_user.enm_execute.return_value.get_output.return_value = enm_output
        excepted_output = {
            u'LTE01dg2ERBS00028': {'scannerMasterState': u'ENABLED', 'fileCollectionState': u'true',
                                   'pmEnabled': u'ENABLED'},
            u'netsim_LTE02ERBS00007': {'scannerMasterState': u'ENABLED', 'fileCollectionState': u'true',
                                       'pmEnabled': u'ENABLED'},
            u'LTE01dg2ERBS00003': {'scannerMasterState': u'ENABLED', 'fileCollectionState': u'true',
                                   'pmEnabled': u'ENABLED'}}
        response = enm_deployment.get_mo_attributes_from_enm(enm_user=enm_user, mo_type="PmFunction",
                                                             mo_attributes=["scannerMasterState", "fileCollectionState",
                                                                            "pmEnabled"],
                                                             scope=["netsim_LTE02ERBS00007", "LTE01dg2ERBS00003",
                                                                    "LTE01dg2ERBS00028"])
        self.assertTrue(mock_debug_log.called)
        self.assertEqual(response, excepted_output)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_mo_attributes_from_enm__getting_multiple_nodes_single_mo_attribute_value(self, mock_debug_log):
        enm_user = Mock()
        enm_output = [u'NetworkElement,PmFunction', u'NodeId\tPmFunctionId\tpmEnabled',
                      u'netsim_LTE02ERBS00007\t1\ttrue', u'netsim_LTE02ERBS00008\t1\ttrue',
                      u'netsim_LTE02ERBS00040\t1\ttrue', u'netsim_LTE02ERBS00025\t1\tfalse', u'', u'4 instance(s)']
        enm_user.enm_execute.return_value.get_output.return_value = enm_output
        excepted_output = {u'netsim_LTE02ERBS00008': {'pmEnabled': u'true'},
                           u'netsim_LTE02ERBS00025': {'pmEnabled': u'false'},
                           u'netsim_LTE02ERBS00040': {'pmEnabled': u'true'},
                           u'netsim_LTE02ERBS00007': {'pmEnabled': u'true'}}
        response = enm_deployment.get_mo_attributes_from_enm(enm_user=enm_user, mo_type="PmFunction",
                                                             mo_attributes=["pmEnabled"],
                                                             scope=["netsim_LTE02ERBS00008", "netsim_LTE02ERBS00025",
                                                                    "netsim_LTE02ERBS00040", "netsim_LTE02ERBS00007"])
        self.assertTrue(mock_debug_log.called)
        self.assertEqual(response, excepted_output)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_mo_attributes_from_enm__raises_enm_application_error_if_cmd_execution_failed(self, mock_debug_log):
        enm_user = Mock()
        enm_user.enm_execute.side_effect = EnmApplicationError("Error occurred while getting NE PmFunction "
                                                               "status from ENM")
        self.assertRaises(EnmApplicationError, enm_deployment.get_mo_attributes_from_enm, enm_user=enm_user,
                          mo_type="PmFunction", mo_attributes="pmEnabled")
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    def test_get_mo_attributes_from_enm__raises_enmapplicationerror_if_enm_returns_error(self, mock_debug_log):
        enm_user = Mock()
        enm_output = [u'Error\t1\ttrue', u'', u'0 instance(s)']
        enm_user.enm_execute.return_value.get_output.return_value = enm_output
        self.assertRaises(EnmApplicationError, enm_deployment.get_mo_attributes_from_enm, enm_user=enm_user,
                          mo_type="PmFunction", mo_attributes="pmEnabled")
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    @patch('enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms')
    def test_get_list_of_db_vms_host_names__is_successful(self, mock_run_cmd_on_emp_or_ms, mock_debug_log):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=0, stdout='db-1-vm1\ndb-1-vm2')
        enm_deployment.get_list_of_db_vms_host_names()
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    @patch('enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms')
    def test_get_list_of_db_vms_host_names__is_successful_if_db_host_name_existed(self, mock_run_cmd_on_emp_or_ms,
                                                                                  mock_debug_log):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=0, stdout='db-1-vm1')
        enm_deployment.get_list_of_db_vms_host_names(db_vm_host_name="db-1")
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.enm_deployment.log.logger.debug')
    @patch('enmutils_int.lib.enm_deployment.shell.run_cmd_on_emp_or_ms')
    def test_get_list_of_db_vms_host_names__if_db_vms_are_not_existed(self, mock_run_cmd_on_emp_or_ms, mock_debug_log):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=1, stdout='')
        enm_deployment.get_list_of_db_vms_host_names()
        self.assertEqual(1, mock_debug_log.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
