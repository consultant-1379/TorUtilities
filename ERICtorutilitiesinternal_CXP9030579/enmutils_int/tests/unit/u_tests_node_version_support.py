#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils_int.lib.node_version_support import NodeVersionSupport, EnmApplicationError
from testslib import unit_test_utils

SUPPORTED_MODEL_DATA = [
    {u'reliable': True,
     u'productVersions': [
         [{u'identity': u'CXP9024418/698', u'revision': u'RI548'}],
         [{u'identity': u'CXP9024418/6', u'revision': u'R57A153'}]
     ],
     u'neType': u'RadioNode',
     u'functionalMims': {u'Lrat': u'3.70.0', u'Wrat': u'7.64.0', u'Grat': u'5.1.2'},
     u'nodes': [
         {u'nodeId': u'LTE02dg2ERBS00030',
          u'productVersion': [{u'identity': u'CXP9024418/698', u'revision': u'RI548'}]},
         {u'nodeId': u'LTE02dg2ERBS00009',
          u'productVersion': [{u'identity': u'CXP9024418/698', u'revision': u'RI548'}]}],
     u'modelIdentity': u'2168-544-861'},
    {u'reliable': True,
     u'productVersions': [
         [{u'identity': u'CXP9024418/698', u'revision': u'RI548'}],
         [{u'identity': u'CXP9024418/6', u'revision': u'R57A153'}]
     ],
     u'neType': u'RNC',
     u'functionalMims': {u'Lrat': u'3.70.0', u'Wrat': u'7.64.0', u'Grat': u'5.1.2'},
     u'nodes': [
         {u'nodeId': u'LTE02dg2ERBS00030',
          u'productVersion': [{u'identity': u'CXP9024418/698', u'revision': u'RI548'}]},
         {u'nodeId': u'LTE02dg2ERBS00009',
          u'productVersion': [{u'identity': u'CXP9024418/698', u'revision': u'RI548'}]}],
     u'modelIdentity': u'2169-544-861'},
    {u'reliable': True,
     u'productVersions': [
         [{u'identity': u'CXP9024418/698', u'revision': u'RI548'}],
         [{u'identity': u'CXP9024418/6', u'revision': u'R57A153'}]
     ],
     u'neType': u'MTAS',
     u'functionalMims': {u'Lrat': u'3.70.0', u'Wrat': u'7.64.0', u'Grat': u'5.1.2'},
     u'nodes': [
         {u'nodeId': u'LTE02dg2ERBS00030',
          u'productVersion': [{u'identity': u'CXP9024418/698', u'revision': u'RI548'}]},
         {u'nodeId': u'LTE02dg2ERBS00009',
          u'productVersion': [{u'identity': u'CXP9024418/698', u'revision': u'RI548'}]}],
     u'modelIdentity': u'2170-544-861'}
]
UNSUPPORTED_MODEL_DATA = [
    {u'statusMsg': u'Success',
     u'reliable': True,
     u'neType': u'MTAS', u'versionId': u'MTAS-341466369983_948664785237_991363377730',
     u'productVersion': [
         {u'identity': u'AVA90129/9', u'revision': u'R6A'}
     ],
     u'modelStatus': u'DOWNLOAD_OK',
     u'functionalMims': {u'MtasFunction': u'5.110.0'},
     u'nodes': [{u'nodeId': u'CORE01MTAS009', u'ossModelIdentity': u'MTAS-1.5'}],
     u'modelIdentity': u'4054-714-323'},
    {u'statusMsg': u'Success',
     u'reliable': True,
     u'neType': u'ERBS', u'versionId': u'ERBS-341466369983_948664785237_991363377730',
     u'productVersion': [
         {u'identity': u'12345', u'revision': u'18.Q1'}
     ],
     u'modelStatus': u'DOWNLOAD_OK',
     u'functionalMims': {u'ERBSFunction': u'5.110.0'},
     u'nodes': [{u'nodeId': u'LTE01ERBS00001', u'ossModelIdentity': u'ERBS-1.5'}],
     u'modelIdentity': u'4054-714-323'},
    {u'statusMsg': u'Success',
     u'reliable': True,
     u'neType': u'RadioNode', u'versionId': u'RadioNode-341466369983_948664785237_991363377730',
     u'productVersion': [
         {u'identity': u'12345', u'revision': u'18.Q1'}
     ],
     u'modelStatus': u'DOWNLOAD_OK',
     u'functionalMims': {u'RadionodeFunction': u'5.110.0'},
     u'nodes': [{u'nodeId': u'LTE01DG200001', u'ossModelIdentity': u'DG2-1.5'}],
     u'modelIdentity': u'4054-714-323'}
]


class NodeVersionSupportUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nvs = NodeVersionSupport(user=self.user, supported_ne_types=["ERBS", "RadioNode", "RNC"])

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_all_unsupported_version_ids__retrieves_all_matching_unsupported_models(self):
        response = Mock(status_code=200)
        response.json.return_value = UNSUPPORTED_MODEL_DATA
        self.user.get.return_value = response
        result = self.nvs.get_all_unsupported_version_ids()
        expected = [u'ERBS-341466369983_948664785237_991363377730', u'RadioNode-341466369983_948664785237_991363377730']
        self.assertListEqual(expected, result)

    def test_get_all_supported_version_ids__retrieves_all_matching_supported_models(self):
        response = Mock(status_code=200)
        response.json.return_value = SUPPORTED_MODEL_DATA
        self.user.get.return_value = response
        result = self.nvs.get_all_supported_version_ids()
        expected = {u'2169-544-861': u'RNC', u'2168-544-861': u'RadioNode'}
        self.assertDictEqual(expected, result)

    @patch('enmutils_int.lib.node_version_support.NodeVersionSupport.get_all_unsupported_version_ids',
           return_value=[])
    @patch('enmutils_int.lib.node_version_support.log.logger.debug')
    def test_deploy_unsupported_models__no_models(self, mock_debug, _):
        self.nvs.deploy_unsupported_models()
        mock_debug.assert_called_with("No unsupported models available to deploy.")

    @patch('enmutils_int.lib.node_version_support.NodeVersionSupport.get_all_unsupported_version_ids',
           return_value=["ERBS-1234"])
    @patch('enmutils_int.lib.node_version_support.log.logger.debug')
    def test_deploy_unsupported_models__success(self, mock_debug, _):
        response = Mock(status_code=200)
        self.user.post.return_value = response
        self.nvs.deploy_unsupported_models()
        mock_debug.assert_called_with("Completed deploy model(s) request to ENM for list of unsupported models.")

    @patch('enmutils_int.lib.node_version_support.NodeVersionSupport.get_all_supported_version_ids', return_value={})
    @patch('enmutils_int.lib.node_version_support.log.logger.debug')
    def test_remove_supported_models__no_models(self, mock_debug, _):
        self.nvs.remove_supported_models()
        mock_debug.assert_called_with("No supported models available to delete.")

    @patch('enmutils_int.lib.node_version_support.NodeVersionSupport.get_all_supported_version_ids',
           return_value={"1234": "ERBS"})
    def test_remove_supported_models__raises_enm_application_error(self, _):
        response = Mock(status_code=500)
        response.raise_for_status.side_effect = Exception("Error")
        self.user.delete_request.return_value = response
        self.assertRaises(EnmApplicationError, self.nvs.remove_supported_models)

    @patch('enmutils_int.lib.node_version_support.NodeVersionSupport.get_all_supported_version_ids',
           return_value={"1234": "ERBS"})
    @patch('enmutils_int.lib.node_version_support.log.logger.debug')
    def test_remove_supported_models__success(self, mock_debug, _):
        response = Mock(status_code=200)
        self.user.delete_request.return_value = response
        self.nvs.remove_supported_models()
        mock_debug.assert_called_with("Completed delete model request(s) to ENM, of supported models.")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
