#!/usr/bin/env python
from datetime import datetime, timedelta
import json
import unittest2
from mock import patch, Mock, PropertyMock, call
from parameterizedtestcase import ParameterizedTestCase
from requests.exceptions import HTTPError
from testslib import unit_test_utils
from enmutils_int.lib.fmx_mgr import FmxMgr
from enmutils_int.lib.workload.fmx_01 import FMX_01
from enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow import (FMX01, EnvironError, NotLoadedFmxModuleError,
                                                                  NotActivatedFmxModuleError, EnmApplicationError)
from enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow import FMX05, SSHException
from enmutils.lib.exceptions import (ShellCommandReturnedNonZero, ValidationError, FileNotUpdatedError)

URL = 'http://locahost'
export_dir_json = ('{"name":"export","absolutePath":"/var/opt/ericsson/fmx/export","freeSpace":"19 GB",'
                   '"freeSpaceInBytes":20654850048,"canRead":true,"canWrite":true,"isDirectory":true,'
                   '"lastModified":"2018-12-03T10:46:09.000","localFiles":[{"name":"CN_External_Alarm-18.1.fmx",'
                   '"absolutePath":"/var/opt/ericsson/fmx/export/CN_External_Alarm-18.1.fmx","size":"25 KB",'
                   '"sizeInBytes":26291,"canRead":true,"canWrite":false,"isFile":true,'
                   '"lastModified":"2018-11-26T11:02:46.000","lastModifiedInEpoch":1543230166000},'
                   '{"name":"NSX_Configuration-16.16.fmx",'
                   '"absolutePath":"/var/opt/ericsson/fmx/export/NSX_Configuration-16.16.fmx",'
                   '"size":"88 KB","sizeInBytes":91052,"canRead":true,"canWrite":false,"isFile":true,'
                   '"lastModified":"2018-11-26T11:02:46.000","lastModifiedInEpoch":1543230166000}]}')

already_imported_error_json = ('{"httpStatusCode":500,"internalErrorCode":119,"internalErrorCodeAsString":'
                               '"MODULE_IMPORT_UNKNOWN_ERROR","userMessage":"The version of the module has already '
                               'been created!","time":"2018-12-04T01:43:12.103","timeInEpoch":1543930992103,'
                               '"exceptionRootCauseMessage":"Exception: The version of the module has already been '
                               'created!"}')

list_loaded_body_json = ('{"messageOrigin":{"user":{"userName":"nmxadm","email":"nmxadm@dummydomain.com"},"start":1544518198998,'
                         '"ipAdress":"svc-3-fmx","processName":"Git server list listener","id":"dbe63c75-42b3-452c-b63c-5e2840b4e456",'
                         '"actionType":"LIST"},"exception":null,"finishTime":1544518198998,"messageFlow":[{"user":{"userName":"nmxadm",'
                         '"email":"nmxadm@dummydomain.com"},"start":1544518198991,"ipAdress":"localhost","processName":"fmxadminws"}],'
                         '"modules":[{"activationInformation":{"module":{"@type":"UTILITYMODULE",'
                         '"moduleInformation":{"versionInformation":{"moduleName":"enm-blocks-module",'
                         '"version":{"numberOfAllowedVersionParts":2,"version":"17.28"}},"requiredModules":[],"writeState":"READONLY",'
                         '"type":"UTILITYMODULE","description":"ENM Event Blocks","productNumber":"","lastModified":1542734478067,'
                         '"userName":"root","releaseNote":"-","files":null,"archivedTime":null,"moduleName":"enm-blocks-module"},'
                         '"partial":false,"moduleName":"enm-blocks-module","files":null},"version":{"numberOfAllowedVersionParts":2,'
                         '"version":"17.28"},"activeState":"INACTIVE","includedTopology":[],"excludedTopology":[]},"module":{"@type":"UTILITYMODULE",'
                         '"moduleInformation":{"versionInformation":{"moduleName":"enm-blocks-module","version":{"numberOfAllowedVersionParts":2,'
                         '"version":"17.28"}},"requiredModules":[],"writeState":"READONLY","type":"UTILITYMODULE","description":"ENM Event Blocks",'
                         '"productNumber":"","lastModified":1542734478067,"userName":"root","releaseNote":"-","files":null,"archivedTime":null,'
                         '"moduleName":"enm-blocks-module"},"partial":false,"moduleName":"enm-blocks-module","files":null},"moduleParameters":[],'
                         '"engineStatus":{"svc-4-fmx":"true","svc-3-fmx":"true"},"engineFault":{},"simulation":false},'
                         '{"activationInformation":{"module":{"@type":"RULEMODULE","moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                         '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"requiredModules":[{"moduleName":"BASEBLOCKS-MODULE",'
                         '"version":{"numberOfAllowedVersionParts":2,"version":"0.1"}},{"moduleName":"ENM-BLOCKS-MODULE",'
                         '"version":{"numberOfAllowedVersionParts":2,"version":"0.1"}},{"moduleName":"EXCLUSIVE-REGION-MODULE",'
                         '"version":{"numberOfAllowedVersionParts":2,"version":"0.1"}}],"writeState":"READONLY","type":"RULEMODULE",'
                         '"description":"GRX - GSM Surveillance eXpert rules package","productNumber":"","lastModified":1525252680000,'
                         '"userName":"FMXteam","releaseNote":"-","files":null,"archivedTime":null,"moduleName":"CN_External_Alarm"},'
                         '"partial":false,"moduleName":"CN_External_Alarm","files":null},"version":{"numberOfAllowedVersionParts":2,'
                         '"version":"18.1"},"activeState":"ACTIVE","includedTopology":[],"excludedTopology":[]},'
                         '"module":{"@type":"RULEMODULE","moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                         '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"requiredModules":[{"moduleName":"BASEBLOCKS-MODULE",'
                         '"version":{"numberOfAllowedVersionParts":2,"version":"0.1"}},{"moduleName":"ENM-BLOCKS-MODULE",'
                         '"version":{"numberOfAllowedVersionParts":2,"version":"0.1"}},{"moduleName":"EXCLUSIVE-REGION-MODULE",'
                         '"version":{"numberOfAllowedVersionParts":2,"version":"0.1"}}],"writeState":"READONLY","type":"RULEMODULE",'
                         '"productNumber":"","lastModified":1525252680000,"userName":"FMXteam","releaseNote":"-","files":null,"archivedTime":null,'
                         '"moduleName":"CN_External_Alarm"},"partial":false,"moduleName":"CN_External_Alarm","files":null},'
                         '"engineStatus":{"svc-4-fmx":"true","svc-3-fmx":"true"},"engineFault":{},"simulation":false}]}')

already_active_error_json = ('{"httpStatusCode":400,"userMessage":"Module is already active","time":"2016-09-21T04:01:32.029",'
                             '"timeInEpoch":1474470092029,"exceptionRootCauseMessage":"BadRequestException:'
                             'HTTP 400 Bad Request","exceptionMessage":"BadRequestException: HTTP 400 Bad Request"}')
archive_modules_json = ('{"modules":['
                        '{"moduleName":"enm-blocks-module","version":{"numberOfAllowedVersionParts":2,"version":"16.16"}},'
                        '{"moduleName":"enm-blocks-module","version":{"numberOfAllowedVersionParts":2,"version":"14.18"}},'
                        '{"moduleName":"NSX_Configuration","version":{"numberOfAllowedVersionParts":2,"version":"16.16"}},'
                        '{"moduleName":"enmcli-blocks-module","version":{"numberOfAllowedVersionParts":2,"version":"16.8"}},'
                        '{"moduleName":"baseblocks-module","version":{"numberOfAllowedVersionParts":2,"version":"15.74"}}'
                        ']}')
modules = ['NSX_Configuration', 'baseblocks-module', 'enm-blocks-module', 'enmcli-blocks-module']
application_json = 'application/json'
application_url_encoded_utf8 = 'application/x-www-form-urlencoded; charset=UTF-8'
vm_addresses = ["svc-3-fmx", "svc-4-fmx"]
message = "If there is a failing test-case you are about to push a change that will break the automated " \
          "performance testing framework (APT). \n Actions: \n1) Please let team APT know ASAP \n3) Skip the " \
          "failing test-case and continue with your push.\nIMPORTANT: Do not modify a test-case to get it passing " \
          "without notifying team APT"


class FmxUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.fmx_mgr = FmxMgr(user=self.user, all_modules=modules, vm_addresses=vm_addresses)
        self.fmx_mgr2 = None
        self.error_response = [Exception("Some Exception")]

        self.FMX_01 = FMX_01()
        self.FMX_01_flow = FMX01()
        self.FMX_01_flow.USER_ROLES = ["FMX_Administrator"]
        self.FMX_01.SCHEDULE_SLEEP = 0
        self.FMX_01.ALL_MODULES = []
        self.FMX_01.FMX_RULEMODULES = []
        self.FMX_01_flow.FMX_RULEMODULES = []
        self.FMX_01_flow.FMX_UTILITYMODULES = []
        self.fmx_05_flow = FMX05()
        self.fmx_05_flow.FETCH_NODES_FROM = ["FM_01"]
        self.fmx_05_flow.SCHEDULE_SLEEP = 0
        self.fmx_05_flow.USER_ROLES = ["ADMINISTRATOR"]
        self.fmx_05_flow.NUM_NODES = Mock()
        self.fmx_05_flow.NUM_USERS = 1
        self.fmx_05_flow.MAINTENANCE_MODES = ['MARK', 'NMS', 'NMSandOSS']
        self.fmx_05_flow.NODE_TYPES = ['ERBS', 'RadioNode']
        self.fmx_05_flow.NODE_COUNT = 2

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_export_dir_modules__raises_http_error(self):
        response = Mock()
        response.ok = False
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.fmx_mgr.get_export_dir_modules)

    def test_import_module__raises_validation_error(self):
        fmx_module = "CN_Signalling_Disturbances"
        response_get = Mock()
        response_get.ok = True
        response_get.json.return_value = json.loads(export_dir_json)
        self.user.get.return_value = response_get
        response_put = Mock()
        response_put.ok = True
        self.user.put.return_value = response_put
        self.assertRaises(ValidationError, self.fmx_mgr.import_module, fmx_module)

    def test_import_module__does_not_raise_error_for_already_imported_module(self):
        fmx_module = "CN_External_Alarm"
        response_get = Mock()
        response_get.ok = True
        response_get.json.return_value = json.loads(export_dir_json)
        self.user.get.return_value = response_get
        response_put = Mock()
        response_put.ok = False
        response_put.json.return_value = json.loads(already_imported_error_json)
        self.user.put.return_value = response_put
        self.fmx_mgr.import_module(fmx_module)
        self.assertTrue(self.user.get.called)
        self.assertTrue(self.user.put.called)

    def test_import_module__raises_http_error(self):
        fmx_module = "CN_External_Alarm"
        resp = '{"  userMessage":"Internal Error!"}'
        response_get = Mock()
        response_get.ok = True
        response_get.json.return_value = json.loads(export_dir_json)
        self.user.get.return_value = response_get
        response_put = Mock()
        response_put.ok = False
        response_put.json.return_value = json.loads(resp)
        self.user.put.return_value = response_put
        self.assertRaises(HTTPError, self.fmx_mgr.import_module, fmx_module)

    @patch('enmutils_int.lib.fmx_mgr.enm_deployment.get_pod_hostnames_in_cloud_native', return_value='fmxengine')
    @patch('enmutils_int.lib.fmx_mgr.is_enm_on_cloud_native', return_value=True)
    def test_init__cloud_native(self, *_):
        self.fmx_mgr.CLOUD_NATIVE = True
        self.fmx_mgr.__init__("user", all_modules=None, vm_addresses=None)

    @patch('enmutils_int.lib.fmx_mgr.enm_deployment.get_pod_hostnames_in_cloud_native', return_value='fmxengine')
    @patch('enmutils_int.lib.fmx_mgr.is_enm_on_cloud_native', return_value=False)
    def test_init__not_cloud_native(self, *_):
        self.fmx_mgr.__init__("user", all_modules=None, vm_addresses=None)

    def test_import_load__is_successful(self):
        self.fmx_mgr.all_modules = ['NSX_Configuration']
        archived_response = ('{"modules":['
                             '{"moduleName":"enm-blocks-module","version":{"numberOfAllowedVersionParts":2,"version":"16.16"}},'
                             '{"moduleName":"enm-blocks-module","version":{"numberOfAllowedVersionParts":2,"version":"14.18"}},'
                             '{"moduleName":"enmcli-blocks-module","version":{"numberOfAllowedVersionParts":2,"version":"16.8"}},'
                             '{"moduleName":"baseblocks-module","version":{"numberOfAllowedVersionParts":2,"version":"15.74"}}'
                             ']}')
        response_get = Mock()
        response_get.ok = True
        response_get.json.side_effect = [json.loads(list_loaded_body_json), json.loads(archived_response),
                                         json.loads(export_dir_json), json.loads(archive_modules_json)]
        self.user.get.return_value = response_get
        response_put = Mock()
        response_put.ok = True
        self.user.put.return_value = response_put
        response_post = Mock()
        response_post.ok = True
        self.user.post.return_value = response_post
        self.fmx_mgr.import_load()
        self.assertTrue(self.user.get.called)
        self.assertTrue(self.user.post.called)
        self.assertTrue(self.user.put.called)

    def test_import_load__does_not_load_already_loaded_modules(self):
        self.fmx_mgr.all_modules = ['CN_External_Alarm']
        response_get = Mock()
        response_get.ok = True
        response_get.json.side_effect = [json.loads(list_loaded_body_json), json.loads(archive_modules_json)]
        self.user.get.return_value = response_get
        self.fmx_mgr.import_load()
        self.assertTrue(self.user.get.called)

    def test_import_load__does_not_import_already_imported_modules(self):
        self.fmx_mgr.all_modules = ['NSX_Configuration']
        list_loaded_body = ('{"modules":[{"activationInformation":{"module":{"@type":"RULEMODULE",'
                            '"moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                            '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                            '"type":"RULEMODULE","moduleName":"CN_External_Alarm"},"partial":false,'
                            '"moduleName":"CN_External_Alarm","files":null},"version":{"numberOfAllowedVersionParts":2,'
                            '"version":"18.1"},"activeState":"INACTIVE","includedTopology":[],"excludedTopology":[]},'
                            '"module":{"@type":"RULEMODULE","moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                            '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                            '"type":"RULEMODULE","productNumber":"","lastModified":1525252680000,"userName":"FMXteam",'
                            '"releaseNote":"-","files":null,"archivedTime":null,"moduleName":"CN_External_Alarm"},'
                            '"partial":false,"moduleName":"CN_External_Alarm","files":null},'
                            '"engineStatus":{"svc-4-fmx":"true","svc-3-fmx":"true"},"engineFault":{},"simulation":false}]}')
        response_get = Mock()
        response_get.ok = True
        response_get.json.side_effect = [json.loads(list_loaded_body), json.loads(archive_modules_json),
                                         json.loads(archive_modules_json)]
        self.user.get.return_value = response_get
        response_post = Mock()
        response_post.ok = True
        self.user.post.return_value = response_post
        self.fmx_mgr.import_load()
        self.assertTrue(self.user.get.called)

    def test_get_loaded_modules__raises_http_error(self):
        response_get = Mock()
        response_get.ok = False
        self.user.get.return_value = response_get
        self.assertRaises(HTTPError, self.fmx_mgr.get_loaded_modules)

    def test_load_module__raises_http_error(self):
        response_post = Mock()
        response_post.ok = False
        self.user.post.return_value = response_post
        self.assertRaises(HTTPError, self.fmx_mgr.load_module, "NSX_Configuration", "16.16")

    def test_get_archive_modules__raises_http_error(self):
        response_get = Mock()
        response_get.ok = False
        self.user.get.return_value = response_get
        self.assertRaises(HTTPError, self.fmx_mgr._get_archive_modules)

    def test_activate_fmx_modules__is_successful(self):
        self.fmx_mgr.all_modules = ['CN_External_Alarm']
        list_loaded_body = ('{"modules":[{"activationInformation":{"module":{"@type":"RULEMODULE",'
                            '"moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                            '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                            '"type":"RULEMODULE","moduleName":"CN_External_Alarm"},"partial":false,'
                            '"moduleName":"CN_External_Alarm","files":null},"version":{"numberOfAllowedVersionParts":2,'
                            '"version":"18.1"},"activeState":"INACTIVE","includedTopology":[],"excludedTopology":[]},'
                            '"module":{"@type":"RULEMODULE","moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                            '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                            '"type":"RULEMODULE","productNumber":"","lastModified":1525252680000,"userName":"FMXteam",'
                            '"releaseNote":"-","files":null,"archivedTime":null,"moduleName":"CN_External_Alarm"},'
                            '"partial":false,"moduleName":"CN_External_Alarm","files":null},'
                            '"engineStatus":{"svc-4-fmx":"true","svc-3-fmx":"true"},"engineFault":{},"simulation":false}]}')
        response_get = Mock()
        response_get.ok = True
        response_get.json.return_value = json.loads(list_loaded_body)
        self.user.get.return_value = response_get
        self.fmx_mgr.activate_fmx_modules()
        self.assertTrue(self.user.get.called)

    def test_activate_fmx_module__activates_module_on_given_set_of_nodes(self):
        self.fmx_mgr.all_modules = ['CN_External_Alarm']
        list_loaded_body = ('{"modules":[{"activationInformation":{"module":{"@type":"RULEMODULE",'
                            '"moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                            '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                            '"type":"RULEMODULE","moduleName":"CN_External_Alarm"},"partial":false,'
                            '"moduleName":"CN_External_Alarm","files":null},"version":{"numberOfAllowedVersionParts":2,'
                            '"version":"18.1"},"activeState":"INACTIVE","includedTopology":[],"excludedTopology":[]},'
                            '"module":{"@type":"RULEMODULE","moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                            '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                            '"type":"RULEMODULE","productNumber":"","lastModified":1525252680000,"userName":"FMXteam",'
                            '"releaseNote":"-","files":null,"archivedTime":null,"moduleName":"CN_External_Alarm"},'
                            '"partial":false,"moduleName":"CN_External_Alarm","files":null},'
                            '"engineStatus":{"svc-4-fmx":"true","svc-3-fmx":"true"},"engineFault":{},"simulation":false}]}')
        response_get = Mock()
        response_get.ok = True
        response_get.json.return_value = json.loads(list_loaded_body)
        self.user.get.return_value = response_get
        response_post = Mock()
        response_post.ok = True
        self.user.post.return_value = response_post
        self.fmx_mgr.activate_fmx_modules(nodes=[Mock(node_id='LTE01ERBS0001')], entire_network=False)
        self.assertEqual(self.user.get.call_count, 1)

    def test_activate_fmx_module_does_not_activated_already_activated_modules(self, ):
        self.fmx_mgr.all_modules = ['CN_External_Alarm']
        list_loaded_body = ('{"modules":[{"activationInformation":{"module":{"@type":"RULEMODULE",'
                            '"moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                            '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                            '"type":"RULEMODULE","moduleName":"CN_External_Alarm"},"partial":false,'
                            '"moduleName":"CN_External_Alarm","files":null},"version":{"numberOfAllowedVersionParts":2,'
                            '"version":"18.1"},"activeState":"ACTIVE","includedTopology":[],"excludedTopology":[]},'
                            '"module":{"@type":"RULEMODULE","moduleInformation":{"versionInformation":{"moduleName":"CN_External_Alarm",'
                            '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                            '"type":"RULEMODULE","productNumber":"","lastModified":1525252680000,"userName":"FMXteam",'
                            '"releaseNote":"-","files":null,"archivedTime":null,"moduleName":"CN_External_Alarm"},'
                            '"partial":false,"moduleName":"CN_External_Alarm","files":null},'
                            '"engineStatus":{"svc-4-fmx":"true","svc-3-fmx":"true"},"engineFault":{},"simulation":false}]}')
        response_get = Mock()
        response_get.ok = True
        response_get.json.return_value = json.loads(list_loaded_body)
        self.user.get.return_value = response_get
        self.fmx_mgr.activate_fmx_modules()
        self.assertEqual(self.user.get.call_count, 1)

    @ParameterizedTestCase.parameterize(
        ('nodes', 'mode', 'start', 'end'),
        [
            ([], '', datetime.now(), datetime.now() + timedelta(seconds=3600)),
            (['test_node'], 'MARK', datetime.now() + timedelta(seconds=3600), datetime.now()),
            (['test_node'], 'MARK', '2016-03-03 12:40:59.710553', '2016-03-03 12:40:59.710553'),
            (['test_node'], '', datetime.now(), datetime.now() + timedelta(seconds=3600)),
        ]
    )
    def test_value_error_raised_from_set_maintenance_mode_for_nodes_when_wrong_args(self, nodes, mode, start, end):
        self.assertRaises(ValidationError, self.fmx_mgr.set_maintenance_mode_for_nodes, nodes, mode, start, end)

    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    def test_set_maintenance_mode_for_nodes__raises(self, mock_execute):
        nodes = [Mock(node_id="LTE01ERBS0001", subnetwork="LTE01")]
        response = Mock()
        response.rc = 1
        response.subnetwork = "SUBNET"
        response.node_id = "LTE07"
        mock_execute.return_value = response
        self.fmx_mgr.set_maintenance_mode_for_nodes(nodes, "MARK", "8", "9")

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.execute_maintenance_cmd')
    def test_set_maintenance_mode_for_nodes__is_successful(self, mock_execute):
        nodes = [Mock(node_id="LTE01ERBS0001", subnetwork="LTE01")]
        self.fmx_mgr.set_maintenance_mode_for_nodes(nodes, "MARK", "8", "9")
        self.assertTrue(mock_execute.called)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    def test_execute_maintenance_cmd__successful(self, mock_execute, mock_log):
        response = Mock()
        response.rc = 0
        mock_execute.return_value = response
        self.fmx_mgr.execute_maintenance_cmd(Mock(), Mock())
        self.assertEqual(mock_log.call_count, 13)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    def test_execute_maintenance_cmd__successful_not_cn(self, mock_execute, mock_log):
        response = Mock()
        self.fmx_mgr.CLOUD_NATIVE = False
        response.rc = 0
        mock_execute.return_value = response
        self.fmx_mgr.execute_maintenance_cmd(Mock(), Mock())
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_cloud_native_pod')
    def test_execute_maintenance_cmd__successful_cn(self, mock_execute, mock_log):
        response = Mock()
        self.fmx_mgr.CLOUD_NATIVE = True
        response.rc = 0
        mock_execute.return_value = response
        self.fmx_mgr.execute_maintenance_cmd(Mock(), Mock())
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    def test_execute_maintenance_cmd__exception(self, mock_execute, mock_log):
        mock_execute.side_effect = SSHException
        self.fmx_mgr.execute_maintenance_cmd(Mock(), Mock())
        self.assertEqual(mock_log.call_count, 13)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    def test_execute_maintenance_cmd__ShellCommandReturnedNonZero_exception(self, mock_execute, _):
        self.fmx_mgr.CLOUD_NATIVE = False
        response = Mock()
        response.rc = 1
        self.assertRaises(ShellCommandReturnedNonZero, self.fmx_mgr.execute_maintenance_cmd, Mock(), Mock())

    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    def test_execute_maintenance_cmd__when_run_time_error_raised(self, mock_execute, mock_log):
        mock_execute.side_effect = RuntimeError
        self.fmx_mgr.execute_maintenance_cmd(Mock(), Mock())
        self.assertEqual(mock_log.call_count, 13)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    def test_execute_maintenance_cmd__when_one_vm_down(self, mock_execute, mock_log):
        response = Mock()
        response.rc = 0
        mock_execute.side_effect = [SSHException, response]
        self.fmx_mgr.execute_maintenance_cmd(Mock(), Mock())
        self.assertEqual(mock_log.call_count, 13)

    @patch('enmutils_int.lib.fmx_mgr.node_pool_mgr')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.remove_expired_node_entries_from_maintenance')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._remove_from_maintenance')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._deactivate_unload_modules')
    def test_teardown__if_maintenance_is_successful(self, mock_deactivate_unload, mock_remove_from_maintenance, *_):
        self.fmx_mgr.maintenance = True
        self.fmx_mgr._teardown()
        self.assertEqual(mock_deactivate_unload.call_count, 1)
        self.assertEqual(mock_remove_from_maintenance.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    @patch('enmutils_int.lib.fmx_mgr.enm_deployment.get_pod_hostnames_in_cloud_native', return_value='fmxengine')
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_cloud_native_pod')
    def test_remove_expired_node__entries_from_maintenance__is_successful(self, mock_run, *_):
        self.fmx_mgr.maintenance = True
        self.fmx_mgr.CLOUD_NATIVE = True
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        response = Mock()
        response.rc = 0
        mock_run.return_value = response
        self.fmx_mgr.remove_expired_node_entries_from_maintenance()
        self.assertEqual(mock_run.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    @patch('enmutils_int.lib.fmx_mgr.enm_deployment.get_pod_hostnames_in_cloud_native', return_value=[])
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_cloud_native_pod')
    def test_remove_expired_node__entries_from_maintenance__is_failed_no_vmaddress_cn(self, *_):
        self.fmx_mgr.maintenance = True
        self.fmx_mgr.CLOUD_NATIVE = True
        self.assertRaises(EnvironError, self.fmx_mgr.remove_expired_node_entries_from_maintenance)

    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    def test_remove_expired_node__entries_from_maintenance__is_failed_no_vmaddress(self, *_):
        self.fmx_mgr.maintenance = True
        self.fmx_mgr.CLOUD_NATIVE = False
        self.fmx_mgr.vm_addresses = ''
        self.assertRaises(EnvironError, self.fmx_mgr.remove_expired_node_entries_from_maintenance)

    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    @patch('enmutils_int.lib.fmx_mgr.enm_deployment.get_pod_hostnames_in_cloud_native', return_value='fmxengine')
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_cloud_native_pod')
    def test_remove_expired_node__entries_from_maintenance__in_error(self, mock_run, *_):
        self.fmx_mgr.maintenance = True
        self.fmx_mgr.CLOUD_NATIVE = False
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        response = Mock()
        response.rc = 1
        mock_run.return_value = response
        self.assertRaises(ShellCommandReturnedNonZero, self.fmx_mgr.remove_expired_node_entries_from_maintenance)

    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._get_nodes_in_maintenance')
    def test_remove_from_maintenance__raises_ShellCommandReturnedNonZero_error(self, mock_get_nodes_in_maintenance, _):
        self.fmx_mgr.maintenance = True
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        mock_get_nodes_in_maintenance.return_value = ['LTE01']
        response = Mock()
        response.rc = 1
        self.assertRaises(ShellCommandReturnedNonZero, self.fmx_mgr._remove_from_maintenance)
        self.assertEqual(mock_get_nodes_in_maintenance.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.node_pool_mgr')
    @patch('enmutils_int.lib.fmx_mgr.time.sleep')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._get_loaded_rule_active_modules')
    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    def test_teardown__if_not_maintenance_is_successful(self, mock_log_info, mock_get_loaded_rule_active_modules, *_):
        self.fmx_mgr.maintenance = False
        modules_list = ['CN_External_Alarm']
        self.fmx_mgr.all_modules = modules_list
        mock_get_loaded_rule_active_modules.return_value = [modules_list + ["CN_Signalling_Disturbances"],
                                                            modules_list,
                                                            modules_list]
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        self.fmx_mgr.user = Mock()
        response = Mock()
        response.ok = True
        response.json.return_value = list_loaded_body_json
        self.fmx_mgr.user.get.side_effect = [response, Mock()]

        self.fmx_mgr._teardown()
        self.assertTrue(mock_log_info.called)

    @patch('enmutils_int.lib.fmx_mgr.node_pool_mgr')
    @patch('enmutils_int.lib.fmx_mgr.time.sleep')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._get_loaded_rule_active_modules')
    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    def test_teardown__if_not_maintenance_is_successful_response_not_ok_loaded_is_different(self, mock_log_debug,
                                                                                            mock_get_loaded_rule_active_modules, *_):
        self.fmx_mgr.maintenance = False
        modules_list = ['CN_External_Alarm']
        self.fmx_mgr.all_modules = modules_list
        mock_get_loaded_rule_active_modules.return_value = [["CN_Signalling_Disturbances"],
                                                            modules_list,
                                                            modules_list]
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        self.fmx_mgr.user = Mock()
        response = Mock()
        response.ok = False
        response.json.return_value = list_loaded_body_json

        self.fmx_mgr.user.get.side_effect = response
        self.fmx_mgr.user.post.return_value = response

        self.fmx_mgr._teardown()
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.fmx_mgr.node_pool_mgr')
    @patch('enmutils_int.lib.fmx_mgr.time.sleep')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._get_loaded_rule_active_modules')
    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    def test_teardown__if_not_maintenance_is_successful_response_not_ok_loaded_is_same(self, mock_log_debug,
                                                                                       mock_get_loaded_rule_active_modules, *_):
        self.fmx_mgr.maintenance = False
        modules_list = ['CN_External_Alarm']
        self.fmx_mgr.all_modules = modules_list
        mock_get_loaded_rule_active_modules.return_value = [modules_list,
                                                            modules_list,
                                                            modules_list]
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        self.fmx_mgr.user = Mock()
        response = Mock()
        response.ok = False
        response.json.return_value = list_loaded_body_json

        self.fmx_mgr.user.get.side_effect = response
        self.fmx_mgr.user.post.return_value = response

        self.fmx_mgr._teardown()
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.fmx_mgr.time.sleep', side_effect=[1])
    def test_deactivate_unload_modules__does_not_deactivae_and_unload_if_there_are_no_modules(self, _):
        self.fmx_mgr.all_modules = []
        self.fmx_mgr._deactivate_unload_modules()

    @patch('enmutils_int.lib.fmx_mgr.node_pool_mgr')
    @patch('enmutils_int.lib.fmx_mgr.time.sleep')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._deactivate_unload_modules', side_effect=Exception)
    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    def test_teardown__if_not_maintenance_logs_exception_and_all_modules_is_empty(self, mock_log_info, *_):
        self.fmx_mgr2 = FmxMgr(user=self.user, all_modules=[], vm_addresses=vm_addresses)
        self.fmx_mgr2.maintenance = False
        self.fmx_mgr2.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        self.fmx_mgr2.user = Mock()
        response = Mock()
        response.ok = True
        response.json.return_value = list_loaded_body_json
        self.fmx_mgr2.user.get.side_effect = [response, Mock()]

        self.fmx_mgr2._teardown()
        self.assertTrue(mock_log_info.called)

    @patch('enmutils_int.lib.fmx_mgr.node_pool_mgr')
    @patch('enmutils_int.lib.fmx_mgr.shell')
    def test_teardown__if_maintenance_logs_exception(self, mock_shell, *_):
        self.fmx_mgr.maintenance = True
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        response = Mock()
        response.rc = 1
        mock_shell.run_cmd_on_vm.return_value = response
        self.fmx_mgr._teardown()
        self.assertEqual(mock_shell.run_cmd_on_vm.call_count, 0)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.__init__', return_value=None)
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._disable_simulation_module')
    @patch('enmutils_int.lib.fmx_mgr.nodemanager_adaptor.deallocate_nodes')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._deactivate_unload_modules')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr._remove_from_maintenance')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.remove_expired_node_entries_from_maintenance')
    def test_teardown__successful_if_service_used(
            self, mock_remove_expired_node_entries_from_maintenance, mock_remove_from_maintenance,
            mock_deactivate_unload_modules, mock_deallocate_nodes, mock_disable_simulation, *_):
        fmx_mgr = FmxMgr(user=Mock(), all_modules=Mock(), vm_addresses=Mock())
        fmx_mgr.maintenance = True
        profile = Mock(nodemanager_service_can_be_used=True)
        options = {"profile": profile}
        fmx_mgr._teardown(**options)
        self.assertTrue(mock_remove_expired_node_entries_from_maintenance.called)
        self.assertTrue(mock_remove_from_maintenance.called)
        self.assertTrue(mock_deactivate_unload_modules.called)
        self.assertTrue(mock_disable_simulation.called)
        mock_deallocate_nodes.assert_called_with(profile)

    @patch('enmutils_int.lib.fmx_mgr.re')
    @patch('enmutils_int.lib.fmx_mgr.shell')
    def test_remove_from_maintenance__if_maintenance(self, mock_shell, mock_re):
        response1 = Mock()
        response1.rc = 0
        response1.stdout = ("Listing all entries:"
                            "-node=SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv010-01_LTE03ERBS00040 "
                            "-Start=20190514063700 -End=20190514073700 -mode=MARK")
        response2 = Mock()
        response2.rc = 0
        mock_re.compile.return_value.findall.return_value = ["SubNetwork=ERBS-SUBNW-1,"
                                                             "MeContext=ieatnetsimv010-01_LTE03ERBS00040"]
        self.fmx_mgr.maintenance = True
        mock_shell.run_cmd_on_vm.side_effect = [response1, response2]
        self.fmx_mgr._remove_from_maintenance()
        self.assertEqual(mock_shell.run_cmd_on_vm.call_count, 2)

    @patch('enmutils_int.lib.fmx_mgr.shell')
    def test_remove_from_maintenance__if_not_maintenance(self, mock_shell):
        self.fmx_mgr.maintenance = False
        self.fmx_mgr._remove_from_maintenance()
        self.assertFalse(mock_shell.run_cmd_on_vm.called)

    @patch('enmutils_int.lib.fmx_mgr.shell')
    def test_remove_expired_node_entries_from_maintenance__if_not_maintenance(self, mock_shell):
        self.fmx_mgr.maintenance = False
        self.fmx_mgr.remove_expired_node_entries_from_maintenance()
        self.assertFalse(mock_shell.run_cmd_on_vm.called)

    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_vm')
    @patch('enmutils_int.lib.fmx_mgr.shell')
    def test_remove_expired_node_entries_from_maintenance__if_maintenance_cloud_native(self, mock_shell, mock_run):
        self.fmx_mgr.maintenance = True
        self.fmx_mgr.CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run.return_value = response
        self.fmx_mgr.remove_expired_node_entries_from_maintenance()
        self.assertTrue(mock_shell.run_cmd_on_vm.called)

    @patch('enmutils_int.lib.fmx_mgr.re')
    @patch('enmutils_int.lib.fmx_mgr.shell')
    def test_get_nodes_in_maintenance__raises_ShellCommandReturnedNonZero(self, mock_shell, *_):
        response = Mock()
        response.rc = 1
        mock_shell.run_cmd_on_vm.return_value = response
        self.assertRaises(ShellCommandReturnedNonZero, self.fmx_mgr._get_nodes_in_maintenance,
                          unit_test_utils.generate_configurable_ip())

    def test_activate_module__raises_HTTP_error(self):
        response = Mock()
        response.ok = False
        response.json.return_value = {}
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.fmx_mgr._activate_module, 'NSX_Configuration')

    def test_activate_module__returns_if_module_already_active(self):
        response = Mock()
        response.ok = False
        response.json.return_value = {'userMessage': 'already active'}
        self.user.get.return_value = response
        self.fmx_mgr._activate_module('NSX_Configuration')
        self.assertTrue(self.user.get.called)

    def test_enable_simulation_module__raises_HTTP_error(self):
        response_post = Mock()
        response_post.ok = False
        self.user.post.return_value = response_post
        self.assertRaises(HTTPError, self.fmx_mgr.enable_simulation_module, 'CN_Signalling_Disturbances')

    def test_enable_simulation_module__Sucess(self):
        response_post = Mock()
        response_post.ok = True
        self.user.post.return_value = response_post
        self.fmx_mgr.enable_simulation_module('CN_Signalling_Disturbances')

    @patch('enmutils_int.lib.fmx_mgr.log.logger.debug')
    def test_deactivate_module__logs_if_response_is_not_ok(self, mock_log_debug):
        response = Mock()
        response.ok = False
        response.json.return_value = {}
        self.user.get.return_value = response
        self.fmx_mgr._deactivate_module('NSX_Configuration')
        self.assertEqual(mock_log_debug.call_count, 2)

    def test_activate_module_on_set_of_nodes__raises_HTTP_error(self):
        response = Mock()
        response.ok = False
        response.json.return_value = {}
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.fmx_mgr._activate_module_on_set_of_nodes, 'NSX_Configuration',
                          [Mock(node_id='LTE01ERBS0001')])

    def test_activate_module_on_set_of_nodes__returns_if_module_already_active(self):
        response = Mock()
        response.ok = False
        response.json.return_value = {'userMessage': 'already active'}
        self.user.post.return_value = response
        self.fmx_mgr._activate_module_on_set_of_nodes('NSX_Configuration', [Mock(node_id='LTE01ERBS0001')])
        self.assertTrue(self.user.post.called)

    @patch('enmutils_int.lib.fmx_mgr.is_host_physical_deployment', return_value=True)
    def test_check_deployment_type__physical_deployment(self, _):
        self.fmx_mgr.check_deployment_type()

    @patch('enmutils_int.lib.fmx_mgr.is_emp', return_value=True)
    def test_check_deployment_type__cloud(self, _):
        self.fmx_mgr.check_deployment_type()

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_user_to_root_on_fmx_vm')
    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_switch_to_ms__exception(self, mock_pexpect_spawn, mock_logger, *_):
        self.fmx_mgr.PHYSICAL = True
        mock_pexpect_spawn.return_value = Mock()
        mock_pexpect_spawn.return_value.expect.side_effect = Exception
        self.assertRaises(EnvironError, self.fmx_mgr.switch_to_ms)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_user_to_root_on_fmx_vm')
    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_switch_to_ms__is_successful_for_physical(self, mock_pexpect_spawn, mock_logger, *_):
        self.fmx_mgr.PHYSICAL = True
        mock_pexpect_spawn.return_value = Mock()
        mock_pexpect_spawn.return_value.expect.return_value = 0
        self.fmx_mgr.switch_to_ms()
        self.assertTrue(mock_logger.called)
        self.assertTrue(mock_pexpect_spawn.called)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_user_to_root_on_fmx_vm')
    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_switch_to_ms__is_successful_for_cloud(self, mock_pexpect_spawn, mock_logger, *_):
        self.fmx_mgr.CLOUD = True
        mock_pexpect_spawn.return_value = Mock()
        mock_pexpect_spawn.return_value.expect.return_value = 0
        self.fmx_mgr.switch_to_ms()
        self.assertTrue(mock_logger.called)
        self.assertTrue(mock_pexpect_spawn.called)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_switch_user_to_root_on_fmx_vm(self, mock_spawn, mock_logger):
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        mock_spawn.return_value.expect.return_value = ["\\[root@svc-3-fmx ~\\]# "]
        self.fmx_mgr.switch_user_to_root_on_fmx_vm(mock_spawn)
        self.assertTrue(mock_logger.called)
        self.assertTrue(mock_spawn.expect.called)
        self.assertTrue(mock_spawn.sendline.called)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_switch_user_to_root_on_fmx_vm__cloud(self, mock_spawn, mock_logger):
        self.fmx_mgr.CLOUD = True
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        mock_spawn.return_value.expect.return_value = ["\\[root@svc-3-fmx ~\\]# "]
        self.fmx_mgr.switch_user_to_root_on_fmx_vm(mock_spawn)
        self.assertTrue(mock_logger.called)
        self.assertTrue(mock_spawn.expect.called)
        self.assertTrue(mock_spawn.sendline.called)

    @patch('enmutils_int.lib.fmx_mgr.time.sleep')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_switch_user_to_root_on_fmx_vm__on_cloud_raises_exception(self, mock_spawn, *_):
        self.fmx_mgr.CLOUD = True
        mock_spawn.sendline.side_effect = EnvironError
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        self.fmx_mgr.execute_on_transport = True
        self.assertRaises(EnvironError, self.fmx_mgr.switch_user_to_root_on_fmx_vm, mock_spawn)

    @patch('enmutils_int.lib.fmx_mgr.time.sleep')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_switch_user_to_root_on_fmx_vm__raises_exception(self, mock_spawn, *_):
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        self.fmx_mgr.execute_on_transport = False
        mock_spawn.expect = Mock()
        mock_spawn.sendline = Mock()
        mock_spawn.expect.side_effect = EnvironError
        self.assertRaises(EnvironError, self.fmx_mgr.switch_user_to_root_on_fmx_vm, mock_spawn)

    @patch('enmutils_int.lib.fmx_mgr.time.sleep')
    @patch('enmutils_int.lib.fmx_mgr.log')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_switch_user_to_root_on_fmx_vm__retries_with_another_IP_if_exception_encountered(self, mock_spawn,
                                                                                             mock_log, *_):
        self.fmx_mgr.vm_addresses = [unit_test_utils.generate_configurable_ip(), unit_test_utils.generate_configurable_ip()]
        self.fmx_mgr.execute_on_transport = False
        mock_spawn.expect.side_effect = [Mock(), Mock()]
        mock_spawn.sendline.side_effect = [Mock(), Mock()]
        mock_spawn.expect.side_effect = [EnvironError, Mock()]
        self.fmx_mgr.switch_user_to_root_on_fmx_vm(mock_spawn)
        self.assertEqual(mock_log.logger.info.call_count, 3)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.update_hardfilter')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.update_externalalarmsfilter')
    def test_execute_filter_file_updates(self, mock_update_external_filter, mock_update_hardfilter):
        self.fmx_mgr.execute_on_transport = False
        self.fmx_mgr.execute_filter_file_updates(execute_on_transport=False)
        self.assertTrue(mock_update_external_filter.called)
        self.assertTrue(mock_update_hardfilter.called)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.update_hardfilter')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.update_externalalarmsfilter')
    def test_execute_filter_file_updates__soem(self, mock_update_external_filter, mock_update_hardfilter):
        self.fmx_mgr.execute_on_transport = True
        self.fmx_mgr.CLOUD = True
        self.fmx_mgr.execute_filter_file_updates(execute_on_transport=True, cloud=True)
        self.assertTrue(mock_update_external_filter.called)
        self.assertTrue(mock_update_hardfilter.called)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.update_hardfilter')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.update_externalalarmsfilter')
    def test_execute_filter_file_updates__transport_physical(self, mock_update_external_filter, mock_update_hardfilter):
        self.fmx_mgr.execute_on_transport = True
        self.fmx_mgr.CLOUD = False
        self.fmx_mgr.execute_filter_file_updates(execute_on_transport=True, cloud=False)
        self.assertTrue(mock_update_external_filter.called)
        self.assertTrue(mock_update_hardfilter.called)

    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_check_externalalarmfilter(self, mock_spawn, mock_logger, mock_shell):
        self.fmx_mgr.execute_on_transport = True
        self.fmx_mgr.CLOUD_NATIVE = True
        mock_spawn.before = '0'
        mock_shell.return_value = "fmxip"
        self.fmx_mgr.check_externalalarmfilter(mock_spawn)

    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_check_externalalarmfilter__on_transport(self, mock_spawn, mock_logger, mock_shell):
        self.fmx_mgr.execute_on_transport = False
        self.fmx_mgr.CLOUD_NATIVE = False
        mock_spawn.before = '0'
        mock_shell.return_value = "fmxip"
        self.fmx_mgr.check_externalalarmfilter(mock_spawn)
        self.assertTrue(mock_spawn.sendline.called)
        self.assertTrue(mock_spawn.expect.called)
        self.assertTrue(mock_logger.called)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_check_externalalarmfilter__not_on_transport(self, mock_spawn, mock_logger):
        self.fmx_mgr.execute_on_transport = True
        self.fmx_mgr.CLOUD_NATIVE = False
        mock_spawn.before = '0'
        self.fmx_mgr.check_externalalarmfilter(mock_spawn)
        self.assertTrue(mock_logger.called)

    @patch('enmutils_int.lib.fmx_mgr.time.sleep', side_effect=[1])
    @patch('enmutils_int.lib.fmx_mgr.shell.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_check_hardfilter__is_successful(self, mock_spawn, *_):
        self.fmx_mgr.execute_on_transport = True
        self.fmx_mgr.CLOUD_NATIVE = True
        mock_spawn.expect.return_value = 0
        self.fmx_mgr.update_hf_transport = ["test", "test"]
        self.fmx_mgr.check_hardfilter(mock_spawn)

    @patch('enmutils_int.lib.fmx_mgr.log.logger.info')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_check_externalalarmfilter__logs_exception(self, mock_spawn, mock_log_info):
        self.fmx_mgr.execute_on_transport = False
        self.fmx_mgr.CLOUD_NATIVE = False
        mock_spawn.before = "1"
        self.fmx_mgr.check_externalalarmfilter(mock_spawn)
        self.assertTrue(mock_log_info.called)

    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_check_hardfilter__raises_exception(self, mock_spawn):
        self.fmx_mgr.execute_on_transport = True
        self.fmx_mgr.CLOUD_NATIVE = False
        mock_spawn.expect.side_effect = self.error_response
        self.assertRaises(FileNotUpdatedError, self.fmx_mgr.check_hardfilter, mock_spawn)

    @patch('enmutils_int.lib.fmx_mgr.time.sleep', side_effect=[1])
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    def test_check_hardfilter__success(self, mock_spawn, _):
        self.fmx_mgr.execute_on_transport = True
        self.fmx_mgr.update_hf = ["fmx"]
        self.fmx_mgr.CLOUD_NATIVE = False
        mock_spawn.expect.return_value = "fmx"
        self.fmx_mgr.check_hardfilter(mock_spawn)

    @patch("enmutils_int.lib.fmx_mgr.enm_deployment")
    def test_fmx_mgr_init_success(self, mock_enm_deployment):
        mock_enm_deployment.get_service_hosts.return_value = "mock_ip_address"
        FmxMgr(user=self.user, all_modules=modules, vm_addresses=None)
        self.assertFalse(mock_enm_deployment.get_values_from_global_properties.called)

    @patch('enmutils_int.lib.fmx_mgr.log')
    @patch("enmutils_int.lib.fmx_mgr.enm_deployment")
    def test_fmx_mgr_init_get_values_from_global_properties_exception(self, mock_enm_deployment, mock_log):
        mock_enm_deployment.get_values_from_global_properties.side_effect = Exception()
        FmxMgr(user=self.user, all_modules=modules, vm_addresses=None)

        self.assertRaises(Exception, FmxMgr(user=self.user, all_modules=modules, vm_addresses=None))
        self.assertTrue(mock_log.logger.error.called)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.check_hardfilter')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_to_ms')
    def test_update_hardfilter__is_successful(self, mock_switch_to_ms, mock_check_hardfilter):
        self.fmx_mgr.CLOUD_NATIVE = False
        self.fmx_mgr.update_hardfilter()
        self.assertEqual(mock_check_hardfilter.call_count, 1)
        self.assertEqual(mock_switch_to_ms.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.check_hardfilter')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_to_ms')
    def test_update_hardfilter__is_successful_on_cloud_native(self, mock_switch_to_ms, mock_check_hardfilter):
        self.fmx_mgr.CLOUD_NATIVE = True
        self.fmx_mgr.update_hardfilter()
        self.assertEqual(mock_check_hardfilter.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.check_externalalarmfilter')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_to_ms')
    def test_update_externalalarmsfilter__is_succe_teardownssful(self, mock_switch_to_ms, mock_check_externalalarmfilter):
        self.fmx_mgr.CLOUD_NATIVE = True
        self.fmx_mgr.update_externalalarmsfilter()
        self.assertEqual(mock_check_externalalarmfilter.call_count, 1)
        self.assertEqual(mock_switch_to_ms.call_count, 0)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.check_externalalarmfilter')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_to_ms')
    def test_update_externalalarmsfilter__is_cloud_native_succe_teardownssful(self, mock_switch_to_ms,
                                                                              mock_check_externalalarmfilter):
        self.fmx_mgr.CLOUD_NATIVE = False
        self.fmx_mgr.update_externalalarmsfilter()
        self.assertEqual(mock_check_externalalarmfilter.call_count, 1)
        self.assertEqual(mock_switch_to_ms.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_to_ms')
    def test_execute_post_fmxenmcli_creation_steps__is_successful_if_credentials_file_exists(self, mock_switch_to_ms):
        mock_switch_to_ms.return_value.expect.side_effect = [0, 0, 0, 0, 0, 0, 0]
        self.fmx_mgr.execute_post_fmxenmcli_creation_steps('test', 'testpassword')
        self.assertEqual(mock_switch_to_ms.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_to_ms')
    def test_execute_post_fmxenmcli_creation_steps__is_successful_if_credentials_file_does_not_exist(self,
                                                                                                     mock_switch_to_ms):
        mock_switch_to_ms.return_value.expect.side_effect = [0, 0, 0, 1, 0, 0, 0]
        self.fmx_mgr.execute_post_fmxenmcli_creation_steps('test', 'testpassword')
        self.assertEqual(mock_switch_to_ms.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.switch_to_ms')
    def test_execute_post_fmxenmcli_creation_steps__is_successful_if_credentials_file_does_not_exist_exception(self, mock_switch_to_ms):
        mock_switch_to_ms.return_value.expect.side_effect = [0, 0, 0, 2, 0, 0, 0]
        self.fmx_mgr.execute_post_fmxenmcli_creation_steps('test', 'testpassword')
        self.assertEqual(mock_switch_to_ms.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    @patch('enmutils_int.lib.fmx_mgr.enm_deployment.get_pod_hostnames_in_cloud_native')
    def test_execute_post_fmxenmcli_creation_steps_cloudnative__is_successful_if_credentials_file_exists_success(self,
                                                                                                                 mock_get_pod_hostnames_in_cloud_native,
                                                                                                                 mock_pexpect_spawn, *_):
        mock_pexpect_spawn.return_value = Mock()
        mock_pexpect_spawn.return_value.expect.return_value = 0
        mock_get_pod_hostnames_in_cloud_native.return_value.expect.side_effect = [0, 0, 0, 0, 0, 0, 0]
        self.fmx_mgr.execute_post_fmxenmcli_creation_steps_cloudnative('test', 'testpassword')
        self.assertEqual(mock_get_pod_hostnames_in_cloud_native.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    @patch('enmutils_int.lib.fmx_mgr.enm_deployment.get_pod_hostnames_in_cloud_native')
    def test_execute_post_fmxenmcli_creation_steps_cloudnative__is_successful_if_credentials_file_exists(self, mock_get_pod_hostnames_in_cloud_native, mock_pexpect_spawn, *_):
        mock_pexpect_spawn.return_value = Mock()
        mock_pexpect_spawn.return_value.expect.side_effect = [1, 1, 1, 1, 1, 1, 1, 1]
        self.fmx_mgr.execute_post_fmxenmcli_creation_steps_cloudnative('test', 'testpassword')
        self.assertEqual(mock_get_pod_hostnames_in_cloud_native.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    @patch('enmutils_int.lib.fmx_mgr.enm_deployment.get_pod_hostnames_in_cloud_native')
    def test_execute_post_fmxenmcli_creation_steps_cloudnative__is_successful_if_credentials_file_exists_exception(self,
                                                                                                                   mock_get_pod_hostnames_in_cloud_native,
                                                                                                                   mock_pexpect_spawn, *_):
        mock_pexpect_spawn.return_value = Mock()
        mock_pexpect_spawn.return_value.expect.side_effect = [0, 0, 0, 0, 2, 0, 0, 0]
        self.fmx_mgr.execute_post_fmxenmcli_creation_steps_cloudnative('test', 'testpassword')
        self.assertEqual(mock_get_pod_hostnames_in_cloud_native.call_count, 1)

    @patch('enmutils_int.lib.fmx_mgr.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.fmx_mgr.pexpect.spawn')
    @patch('enmutils_int.lib.fmx_mgr.enm_deployment.get_pod_hostnames_in_cloud_native', return_value=[])
    def test_execute_post_fmxenmcli_creation_steps_cloudnative__is_successful_if_credentials_file_exists_cenm_exception(self, *_):
        self.assertRaises(EnvironError, self.fmx_mgr.execute_post_fmxenmcli_creation_steps_cloudnative, "'test'", "'testpassword'")

    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FmxMgr')
    def test_execute_filter_updates__adds_exception_if_no_vm_addresses_are_present(self, mock_fmxmgr, mock_add_exception):
        mock_fmxmgr.vm_addresses = None
        self.FMX_01_flow.execute_filter_updates(mock_fmxmgr)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.cloud', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FmxMgr')
    def test_execute_filter_updates__adds_error_as_exception_during_filter_update(self, mock_fmxmgr, mock_add_exception,
                                                                                  *_):
        mock_fmxmgr.return_value.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        self.FMX_01_flow.execute_on_transport = True
        mock_fmxmgr.execute_filter_file_updates.side_effect = Exception
        self.FMX_01_flow.execute_filter_updates(mock_fmxmgr)
        self.assertTrue(mock_add_exception.called)

    @patch("enmutils_int.lib.profile.is_emp", return_value=True)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FmxMgr')
    def test_execute_filter_updates__returns_without_updating_filters_if_cloud(self, mock_fmxmgr, *_):
        self.FMX_01_flow.execute_on_transport = False
        mock_fmxmgr.return_value.vm_addresses = [unit_test_utils.generate_configurable_ip()]
        self.FMX_01_flow.execute_on_transport = False
        self.FMX_01_flow.execute_filter_updates(mock_fmxmgr)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.execute_filter_updates')
    def test_load_activate_fmx_modules__is_successful_for_initial_run(self, mock_filter_updates):
        fmx_mgr = Mock()
        fmx_mgr.get_loaded_modules.return_value = Mock()
        fmx_mgr._get_loaded_rule_active_modules.return_value = [], Mock(), Mock()
        self.FMX_01_flow.load_activate_fmx_modules(fmx_mgr)
        self.assertEqual(mock_filter_updates.call_count, 1)
        self.assertEqual(fmx_mgr.get_loaded_modules.call_count, 1)
        self.assertEqual(fmx_mgr._get_loaded_rule_active_modules.call_count, 1)
        self.assertEqual(fmx_mgr.import_load.call_count, 1)
        self.assertEqual(fmx_mgr.activate_fmx_modules.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.execute_filter_updates')
    def test_load_activate_fmx_modules__continues_evn_if_modules_are_loaded_for_initial_run(self, mock_filter_updates):
        fmx_mgr = Mock()
        fmx_mgr.get_loaded_modules.return_value = Mock()
        fmx_mgr._get_loaded_rule_active_modules.return_value = ['NSX_Configuration'], Mock(), Mock()
        self.FMX_01_flow.load_activate_fmx_modules(fmx_mgr)
        self.assertEqual(mock_filter_updates.call_count, 1)
        self.assertEqual(fmx_mgr.get_loaded_modules.call_count, 1)
        self.assertEqual(fmx_mgr._get_loaded_rule_active_modules.call_count, 1)
        self.assertEqual(fmx_mgr.import_load.call_count, 1)
        self.assertEqual(fmx_mgr.activate_fmx_modules.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.execute_filter_updates')
    def test_load_activate_fmx_modules__is_successful_if_not_initial_run(self, mock_filter_updates):
        self.FMX_01.ALL_MODULES = ['NSX_Configuration']
        self.FMX_01_flow.INITIAL_RUN = False
        fmx_mgr = Mock()
        fmx_mgr.get_loaded_modules.return_value = Mock()
        fmx_mgr._get_loaded_rule_active_modules.return_value = ['NSX_Configuration'], Mock(), ['NSX_Configuration']
        self.FMX_01_flow.load_activate_fmx_modules(fmx_mgr)
        self.assertEqual(fmx_mgr.get_loaded_modules.call_count, 1)
        self.assertEqual(fmx_mgr._get_loaded_rule_active_modules.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.execute_filter_updates')
    def test_load_activate_fmx_modules__raises_NotLoadedFmxModuleError(self, mock_filter_updates):
        self.FMX_01_flow.ALL_MODULES = ['NSX_Configuration', 'NSX_Hard_Filter']
        self.FMX_01_flow.INITIAL_RUN = False
        fmx_mgr = Mock()
        fmx_mgr.get_loaded_modules.return_value = Mock()
        fmx_mgr._get_loaded_rule_active_modules.return_value = ['NSX_Configuration'], Mock(), Mock()
        self.assertRaises(NotLoadedFmxModuleError, self.FMX_01_flow.load_activate_fmx_modules, fmx_mgr)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.execute_filter_updates')
    def test_load_activate_fmx_modules__raises_NotActivatedFmxModuleError(self, mock_filter_updates):
        self.FMX_01_flow.ALL_MODULES = ['NSX_Configuration', 'NSX_Hard_Filter']
        self.FMX_01_flow.FMX_RULEMODULES = ['NSX_Configuration', 'NSX_Hard_Filter']
        self.FMX_01_flow.INITIAL_RUN = False
        fmx_mgr = Mock()
        fmx_mgr.get_loaded_modules.return_value = Mock()
        fmx_mgr._get_loaded_rule_active_modules.return_value = (['NSX_Configuration', 'NSX_Hard_Filter'], Mock(),
                                                                ['NSX_Configuration'])
        self.assertRaises(NotActivatedFmxModuleError, self.FMX_01_flow.load_activate_fmx_modules, fmx_mgr)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.Target')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.EnmRole')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.CustomUser')
    def test_create_fmxenmcli_user__creates_user_successfully(self, mock_custom_user, *_):
        self.FMX_01_flow.create_fmxenmcli_user()
        self.assertEqual(mock_custom_user.return_value.create.call_count, 1)
        self.assertEqual(mock_custom_user.return_value.is_session_established.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.Target')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.EnmRole')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.CustomUser')
    def test_create_fmxenmcli_user__retires_if_user_creation_fails(self, mock_custom_user, mock_log, *_):
        mock_custom_user.return_value.create.side_effect = [Exception, Exception, Exception, Mock()]
        self.FMX_01_flow.create_fmxenmcli_user()
        self.assertEqual(mock_custom_user.return_value.create.call_count, 3)
        self.assertEqual(mock_custom_user.return_value.is_session_established.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 6)
        self.assertFalse(mock_log.logger.info.called)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.Target')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.EnmRole')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.CustomUser')
    def test_create_fmxenmcli_user__raises_exception_if_session_is_not_established(self, mock_custom_user, mock_log, *_):
        mock_custom_user.return_value.is_session_established.return_value = False
        self.assertRaises(EnmApplicationError, self.FMX_01_flow.create_fmxenmcli_user)
        self.assertEqual(mock_custom_user.return_value.create.call_count, 1)
        self.assertEqual(mock_custom_user.return_value.is_session_established.call_count, 1)
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.Target')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.EnmRole')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.CustomUser')
    def test_create_fmxenmmml_user__creates_user_successfully(self, mock_custom_user, *_):
        self.FMX_01_flow.create_fmxenmmml_user()
        self.assertEqual(mock_custom_user.return_value.create.call_count, 1)
        self.assertEqual(mock_custom_user.return_value.is_session_established.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.Target')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.EnmRole')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.CustomUser')
    def test_create_fmxenmmml_user__retires_if_user_creation_fails(self, mock_custom_user, mock_log, *_):
        mock_custom_user.return_value.create.side_effect = [Exception, Exception, Exception, Mock()]
        self.FMX_01_flow.create_fmxenmmml_user()
        self.assertEqual(mock_custom_user.return_value.create.call_count, 3)
        self.assertEqual(mock_custom_user.return_value.is_session_established.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 6)
        self.assertFalse(mock_log.logger.info.called)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.Target')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.EnmRole')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.CustomUser')
    def test_create_fmxenmmml_user__raises_exception_if_session_is_not_established(self, mock_custom_user, mock_log,
                                                                                   *_):
        mock_custom_user.return_value.is_session_established.return_value = False
        self.assertRaises(EnmApplicationError, self.FMX_01_flow.create_fmxenmmml_user)
        self.assertEqual(mock_custom_user.return_value.create.call_count, 1)
        self.assertEqual(mock_custom_user.return_value.is_session_established.call_count, 1)
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.user_exists')
    def test_check_for_fmxenmcli_user__returns_if_user_already_exists_in_enm(self, mock_user_exists,
                                                                             mock_create_user, mock_log, *_):
        mock_user_exists.return_value = True
        self.FMX_01_flow.check_for_fmxenmcli_user()
        self.assertFalse(mock_create_user.called)
        self.assertEqual(mock_log.logger.info.call_count, 1)
        self.assertEqual(mock_user_exists.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.user_exists')
    def test_check_for_fmxenmcli_user__creates_user_if_not_already_existsing_in_enm(self, mock_user_exists,
                                                                                    mock_create_user, mock_log, *_):
        response = Mock(status_code=404)
        response.reason = "User Not Found"
        mock_user_exists.side_effect = HTTPError(response=response)
        self.FMX_01_flow.check_for_fmxenmcli_user()
        self.assertEqual(mock_create_user.call_count, 1)
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.user_exists')
    def test_check_for_fmxenmcli_user__logs_exception_while_checking_if_user_exists(self, mock_user_exists,
                                                                                    mock_create_user, mock_log, *_):
        response = Mock(status_code=504)
        response.reason = "Gateway Time-out"
        mock_user_exists.side_effect = HTTPError(response=response)
        self.FMX_01_flow.check_for_fmxenmcli_user()
        self.assertFalse(mock_create_user.called)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.user_exists')
    def test_check_for_fmxenmmml__returns_if_user_already_exists_in_enm(self, mock_user_exists, mock_create_user,
                                                                        mock_log, *_):
        mock_user_exists.return_value = True
        self.FMX_01_flow.check_for_fmxenmmml_user()
        self.assertFalse(mock_create_user.called)
        self.assertEqual(mock_log.logger.info.call_count, 1)
        self.assertEqual(mock_user_exists.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.user_exists')
    def test_check_for_fmxenmmml_user__creates_user_if_not_already_existsing_in_enm(self, mock_user_exists,
                                                                                    mock_create_user, mock_log, *_):
        response = Mock(status_code=404)
        response.reason = "User Not Found"
        mock_user_exists.side_effect = HTTPError(response=response)
        self.FMX_01_flow.check_for_fmxenmmml_user()
        self.assertEqual(mock_create_user.call_count, 1)
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.user_exists')
    def test_check_for_fmxenmmml_user__logs_exception_while_checking_if_user_exists(self, mock_user_exists,
                                                                                    mock_create_user, mock_log, *_):
        response = Mock(status_code=504)
        response.reason = "Gateway Time-out"
        mock_user_exists.side_effect = HTTPError(response=response)
        self.FMX_01_flow.check_for_fmxenmmml_user()
        self.assertFalse(mock_create_user.called)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_post_user_creation')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.load_activate_fmx_modules')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils.lib.cache.is_emp', return_value=True)
    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.sleep')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, True, True, False])
    @patch('enmutils_int.lib.profile.Profile.create_users', side_effect=[[Mock()]])
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmcli_user', return_value=False)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FmxMgr')
    def test_execute_fmx_01_flow__is_successful_for_multiple_iterations(self, mock_fmxmgr, *_):
        mock_fmxmgr.return_value.execute_post_fmxenmcli_creation_steps.return_value = Mock()
        self.FMX_01_flow.execute_fmx_01_flow()

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.execute_post_fmxenmcli_creation_steps_cloudnative')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.is_enm_on_cloud_native')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log.logger.info')
    def test_check_post_user_creation__is_cloud_native(self, mock_logger, *_):
        self.FMX_01_flow.check_post_user_creation(self.fmx_mgr)
        self.assertTrue(mock_logger.called)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.fmx_mgr.FmxMgr.execute_post_fmxenmcli_creation_steps')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log.logger.info')
    def test_check_post_user_creation__is_not_cloud_native(self, mock_logger, *_):
        self.FMX_01_flow.check_post_user_creation(self.fmx_mgr)
        self.assertEqual(mock_logger.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.load_activate_fmx_modules')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.keep_running', side_effect=[True, True, True, False])
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_users', return_value=[None])
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmcli_user', return_value=False)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FmxMgr')
    def test_execute_fmx_01_flow__is_successful_for_multiple_iterations_no_user(self, mock_fmxmgr, *_):
        self.FMX_01_flow.execute_fmx_01_flow()
        self.assertEqual(mock_fmxmgr.return_value.execute_post_fmxenmcli_creation_steps.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_post_user_creation')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.load_activate_fmx_modules')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils.lib.cache.is_emp', return_value=True)
    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.keep_running', side_effect=[True, True, True, False])
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_users', side_effect=[[None], [Mock()]])
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmcli_user', return_value=False)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FmxMgr')
    def test_execute_fmx_01_flow__is_successful_for_multiple_iterations_cloudnative(self, mock_fmxmgr, *_):
        mock_fmxmgr.return_value.execute_post_fmxenmcli_creation_steps.return_value = Mock()
        self.FMX_01_flow.execute_fmx_01_flow()

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.load_activate_fmx_modules')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmcli_user', return_value=True)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FmxMgr')
    def test_execute_fmx_01_flow__does_not_execute_post_steps_if_fmxenmcli_exists(self, mock_fmxmgr,
                                                                                  mock_load_activate_modules, *_):
        self.FMX_01_flow.execute_fmx_01_flow()
        self.assertFalse(mock_fmxmgr.return_value.execute_post_fmxenmcli_creation_steps.called)
        self.assertEqual(mock_load_activate_modules.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_fmxenmcli_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.load_activate_fmx_modules', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.sleep')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.create_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmmml_user')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FMX01.check_for_fmxenmcli_user', return_value=True)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow.FmxMgr')
    def test_execute_fmx_01_flow__adds_error_as_exception(self, mock_fmxmgr, mock_add_error, *_):
        self.FMX_01_flow.execute_fmx_01_flow()
        self.assertFalse(mock_fmxmgr.return_value.execute_post_fmxenmcli_creation_steps.called)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.partial")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.nodemanager_service_can_be_used",
           new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.node_pool_mgr.deallocate_nodes")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.datetime")
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FmxMgr')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.keep_running', side_effect=[True, True, False])
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.create_profile_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.sleep")
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.fetch_nodes_for_the_profile',
           side_effect=[["node1", "node2", "node3"], ["node4", "node5", "node6"]])
    @patch("enmutils_int.lib.fmx_mgr.FmxMgr.remove_expired_node_entries_from_maintenance")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.set_available_nodes_into_maintenance_modes")
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.remove_expired_old_entries')
    @patch(
        "enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.node_allocation_and_different_operations_on_nodes")
    def test_execute_fmx_05_flow__is_successful(self, mock_node_allocation, mock_remove_expired_entries,
                                                mock_set_maintenance, *_):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_05_flow.execute_fmx_05_flow()
        self.assertEqual(mock_remove_expired_entries.call_count, 2)
        calls = [call(["node1", "node2", "node3"], "NSX_Maintenance_filter", True),
                 call(["node4", "node5", "node6"], "NSX_Maintenance_filter", False)]
        mock_node_allocation.assert_has_calls(calls)
        self.assertEqual(mock_node_allocation.call_count, 2)
        self.assertEqual(mock_set_maintenance.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.partial")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.allocate_specific_nodes_to_profile")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.nodemanager_service_can_be_used",
           new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.node_pool_mgr.deallocate_nodes")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.datetime")
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FmxMgr')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.keep_running', side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.create_profile_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.sleep")
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.fetch_nodes_for_the_profile',
           side_effect=[[Mock()]])
    @patch("enmutils_int.lib.fmx_mgr.FmxMgr.remove_expired_node_entries_from_maintenance")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.set_available_nodes_into_maintenance_modes")
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.remove_expired_old_entries')
    @patch(
        "enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.node_allocation_and_different_operations_on_nodes")
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.log.logger.debug')
    def test_execute_fmx_05_flow__less_than_3_available_nodes(self, mock_log, mock_node_allocation,
                                                              mock_remove_expired_entries,
                                                              mock_set_maintenance, *_):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_05_flow.execute_fmx_05_flow()
        self.assertEqual(mock_remove_expired_entries.call_count, 1)
        self.assertEqual(mock_node_allocation.call_count, 0)
        self.assertEqual(mock_set_maintenance.call_count, 0)
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FmxMgr.set_maintenance_mode_for_nodes")
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.log.logger.debug')
    def test_set_available_nodes_into_maintenance_modes__successful(self, *_):
        nodes = ["node1", "node2", "node3"]
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_05_flow.set_available_nodes_into_maintenance_modes(nodes, 1, "8", "9")
        self.assertEqual(len(nodes), 0)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FmxMgr.set_maintenance_mode_for_nodes")
    def test_set_available_nodes_into_maintenance_modes__add_exception(self, mock_set_maintenance_mode, mock_add_error, _):
        self.fmx_05_flow.fmx_mgr = Exception
        nodes = [Mock(), Mock(), Mock()]
        self.assertRaises(Exception, self.fmx_05_flow.set_available_nodes_into_maintenance_modes(nodes, 1, "8", "9"))
        self.assertEqual(mock_set_maintenance_mode.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.persist")
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.log.logger.info')
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.allocate_specific_nodes_to_profile")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.load_and_activate_nsx_maintenance_filter")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.deactivate_and_activate_maintenance_filter_on_given_nodes")
    def test_node_allocation_and_different_operations_on_nodes__initial_run(self, mock_deactivate_and_activate,
                                                                            mock_load_and_activate, *_):
        available_nodes = [[Mock(), Mock(), Mock()],
                           [Mock(), Mock(), Mock()]]
        self.fmx_05_flow.node_allocation_and_different_operations_on_nodes(available_nodes, "filter", initial_run=True)
        self.assertEqual(mock_load_and_activate.call_count, 1)
        self.assertEqual(mock_deactivate_and_activate.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.allocate_specific_nodes_to_profile")
    @patch("enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.load_and_activate_nsx_maintenance_filter")
    @patch(
        "enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05"
        ".deactivate_and_activate_maintenance_filter_on_given_nodes")
    def test_node_allocation_and_different_operations_on_nodes__next_iterations(self, mock_deactivate_and_activate,
                                                                                mock_load_and_activate, *_):
        available_nodes = [[Mock(), Mock(), Mock()],
                           [Mock(), Mock(), Mock()]]
        self.fmx_05_flow.node_allocation_and_different_operations_on_nodes(available_nodes, "filter", initial_run=False)
        self.assertEqual(mock_load_and_activate.call_count, 0)
        self.assertEqual(mock_deactivate_and_activate.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.get_allocated_nodes')
    def test_fetch_nodes_for_the_profile__is_successful_correct_required_nodes(self, mock_get_allocated_nodes,
                                                                               mock_log_info):
        mock_get_allocated_nodes.return_value = [Mock(primary_type='ERBS'), Mock(primary_type='SGSN'),
                                                 Mock(primary_type='RadioNode', managed_element_type='ENodeB'),
                                                 Mock(primary_type='RadioNode', managed_element_type='ENodeB'),
                                                 Mock(primary_type='RadioNode', managed_element_type='NodeB'),
                                                 Mock(primary_type='RNC')]
        nodes = self.fmx_05_flow.fetch_nodes_for_the_profile()
        self.assertEqual(len(nodes), 2)
        self.assertEqual(mock_log_info.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.get_allocated_nodes')
    def test_fetch_nodes_for_the_profile__is_successful_less_required_nodes(self, mock_get_allocated_nodes,
                                                                            mock_log_info):
        mock_get_allocated_nodes.return_value = [Mock(primary_type='RadioNode', managed_element_type='ENodeB'),
                                                 Mock(primary_type='RadioNode', managed_element_type='NodeB'),
                                                 Mock(primary_type='RNC')]
        nodes = self.fmx_05_flow.fetch_nodes_for_the_profile()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(mock_log_info.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.get_allocated_nodes')
    def test_fetch_nodes_for_the_profile__is_unsuccessful(self, mock_get_allocated_nodes, mock_log_info):
        mock_get_allocated_nodes.return_value = []
        self.fmx_05_flow.fetch_nodes_for_the_profile()
        self.assertTrue(mock_log_info.called)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.get_allocated_nodes')
    def test_fetch_nodes_for_the_profile__adds_error_as_exception(self, mock_get_allocated_nodes, mock_add_exception):
        mock_get_allocated_nodes.side_effect = Exception
        self.fmx_05_flow.fetch_nodes_for_the_profile()
        self.assertEqual(mock_add_exception.call_count, 1)

    def test_remove_expired_old_entries__is_successful(self):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_mgr.CLOUD_NATIVE = False
        self.fmx_05_flow.remove_expired_old_entries()
        self.assertTrue(self.fmx_05_flow.fmx_mgr.remove_expired_node_entries_from_maintenance.called)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.add_error_as_exception')
    def test_remove_expired_old_entries__adds_SSHException_as_exception(self, mock_add_error_as_exception):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_mgr.CLOUD_NATIVE = False
        self.fmx_05_flow.fmx_mgr.remove_expired_node_entries_from_maintenance.side_effect = SSHException
        self.fmx_05_flow.remove_expired_old_entries()
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.add_error_as_exception')
    def test_remove_expired_old_entries__adds_RuntimeError_as_exception(self, mock_add_error_as_exception):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_mgr.CLOUD_NATIVE = False
        self.fmx_05_flow.fmx_mgr.remove_expired_node_entries_from_maintenance.side_effect = RuntimeError
        self.fmx_05_flow.remove_expired_old_entries()
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.add_error_as_exception')
    def test_remove_expired_old_entries__adds_errors_as_exception(self, mock_add_error_as_exception):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_mgr.CLOUD_NATIVE = False
        self.fmx_05_flow.fmx_mgr.remove_expired_node_entries_from_maintenance.side_effect = ValidationError
        self.fmx_05_flow.remove_expired_old_entries()
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_load_and_activate_nsx_maintenance_filter__is_successful(self):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_05_flow.load_and_activate_nsx_maintenance_filter([Mock()])
        self.assertTrue(self.fmx_05_flow.fmx_mgr.import_load.called)
        self.assertTrue(self.fmx_05_flow.fmx_mgr.activate_fmx_modules.called)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.add_error_as_exception')
    def test_load_and_activate_nsx_maintenance_filter__adds_exception(self, mock_add_error_as_exception):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_05_flow.fmx_mgr.import_load.side_effect = Exception
        self.fmx_05_flow.load_and_activate_nsx_maintenance_filter([Mock()])
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.sleep')
    def test_deactivate_and_activate_maintenance_filter_on_given_nodes_is_successful(self, *_):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_05_flow.deactivate_and_activate_maintenance_filter_on_given_nodes([Mock()], 'NSX_Maintenance_Filter')
        self.assertTrue(self.fmx_05_flow.fmx_mgr._deactivate_module.called)
        self.assertTrue(self.fmx_05_flow.fmx_mgr.activate_fmx_modules.called)

    @patch('enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow.FMX05.add_error_as_exception')
    def test_deactivate_and_activate_maintenance_filter_on_given_nodes__adds_exception(self,
                                                                                       mock_add_error_as_exception):
        self.fmx_05_flow.fmx_mgr = Mock()
        self.fmx_05_flow.fmx_mgr._deactivate_module.side_effect = Exception
        self.fmx_05_flow.deactivate_and_activate_maintenance_filter_on_given_nodes([Mock()], 'NSX_Maintenance_Filter')
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_get_loaded_rule_active_modules_returns_three_modules_list(self):
        response = Mock(ok=True)
        response.json.return_value = json.loads(list_loaded_body_json)
        self.user.get.return_value = response
        data = ('{"modules":[{"activationInformation":{"module":{"@type":"RULEMODULE",'
                '"moduleInformation":{"versionInformation":{"moduleName":"CN_Signalling_Disturbances",'
                '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                '"type":"RULEMODULE","moduleName":"CN_External_Alarm"},"partial":false,'
                '"moduleName":"CN_Signalling_Disturbances","files":null},"version":{"numberOfAllowedVersionParts":2,'
                '"version":"18.1"},"activeState":"INACTIVE","includedTopology":[],"excludedTopology":[]},'
                '"module":{"@type":"RULEMODULE","moduleInformation":{"versionInformation":{"moduleName":'
                '"CN_External_Alarm",'
                '"version":{"numberOfAllowedVersionParts":2,"version":"18.1"}},"writeState":"READONLY",'
                '"type":"RULEMODULE","productNumber":"","lastModified":1525252680000,"userName":"FMXteam",'
                '"releaseNote":"-","files":null,"archivedTime":null,"moduleName":"CN_Signalling_Disturbances"},'
                '"partial":false,"moduleName":"CN_Signalling_Disturbances","files":null},'
                '"engineStatus":{"svc-4-fmx":"true","svc-3-fmx":"true"},"engineFault":{},"simulation":true}]}')
        response2 = Mock(ok=True)
        response2.json.return_value = json.loads(data)
        fmx_modules_list = len(self.fmx_mgr._get_loaded_rule_active_modules(response2))
        self.assertEqual(fmx_modules_list, 3, message)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
