#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from requests.exceptions import HTTPError

from enmutils.lib import headers
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.pkiadm import (PKIAdm, Entity, EntityProfile, CertificateProfile, get_all_certificate_profiles,
                                     get_all_entity_profiles)
from testslib import unit_test_utils

NAME = "U_test"
ENITITY_LIST = [
    {u'entityProfile': {u'name': u'Test', u'id': 89}, u'entityType': u'entity',
     u'entityInfo': {u'otpcount': 0, u'status': u'ACTIVE', u'name': u'Secui_Six_NOJdBB', u'subjectAltName': None,
                     u'certificateAssigned': 1, u'otp': u'',
                     u'subject': {u'subjectFields': [{u'type': u'COMMON_NAME', u'value': u'Secui_Six_NOJdBB'}]}},
     u'publishCertificatetoTDPS': False, u'keyGenerationAlgorithm': {u'supported': True, u'name': u'RSA',
                                                                     u'oid': u'1.2', u'keySize': 0, u'type': u'A',
                                                                     u'id': 22, u'categories': []}, u'type': u'ENTITY'},
    {u'entityProfile': {u'name': u'Test', u'id': 89}, u'entityType': u'entity',
     u'entityInfo': {u'otpcount': 0, u'status': u'ACTIVE', u'name': u'Secui_Six_NOJdBB', u'subjectAltName': None,
                     u'id': 1, u'certificateAssigned': 1, u'otp': u'',
                     u'subject': {u'subjectFields': [{u'type': u'COMMON_NAME', u'value': u'Secui_Six_NOJdBB'}]}},
     u'publishCertificatetoTDPS': False, u'keyGenerationAlgorithm': {u'supported': True, u'name': u'RSA',
                                                                     u'oid': u'1.2', u'keySize': 0, u'type': u'A',
                                                                     u'id': 22, u'categories': []}, u'type': u'ENTITY'},
    {u'entityProfile': {u'name': u'Test', u'id': 89}, u'entityType': u'entity',
     u'entityInfo': {u'otpcount': 0, u'status': u'DELETED', u'name': u'Secui_Seven', u'subjectAltName': None, u'id': 1,
                     u'certificateAssigned': 1, u'otp': u'',
                     u'subject': {u'subjectFields': [{u'type': u'COMMON_NAME', u'value': u'Secui_Seven'}]}},
     u'publishCertificatetoTDPS': False, u'keyGenerationAlgorithm': {u'supported': True, u'name': u'RSA',
                                                                     u'oid': u'1.2', u'keySize': 0, u'type': u'A',
                                                                     u'id': 22, u'categories': []}, u'type': u'ENTITY'}
]


class PKIAdmUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

        self.pki = PKIAdm(user=self.user, name=NAME)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    def test_delete__is_successful(self, mock_debug):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {u'Success': u'True'}
        self.user.delete_request.return_value = response
        self.pki.delete()
        self.assertTrue(mock_debug.called)

    def test_get_all_entities__success(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {u'Success': u'True'}
        self.user.post.return_value = response
        self.pki.get_all_entities()
        self.user.post.assert_called_with(self.pki.GET_ALL_ENTITIES_URL, json={"offset": 0, "limit": 60000},
                                          headers=headers.SECURITY_REQUEST_HEADERS)

    def test_repr__is_over_written(self):
        self.assertEqual(self.pki.__repr__(), "<PKIAdm U_test>")

    def test_pkiadm__body_is_empty(self):
        self.assertEqual({}, self.pki.body)

    @patch('enmutils_int.lib.pkiadm.raise_for_status')
    @patch('enmutils_int.lib.pkiadm.log.logger.debug')
    def test_get_all_certificate_profiles__is_success(self, mock_debug, mock_raise_for_status):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = [{'name': "Secui_six_sdfdgdfhg", 'id': 3, 'type': 'CERTIFICATE_PROFILE'}]
        self.user.post.return_value = response
        get_all_certificate_profiles(self.user)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_raise_for_status.called)

    @patch('enmutils_int.lib.pkiadm.raise_for_status', side_effect=HTTPError)
    @patch('enmutils_int.lib.pkiadm.log.logger.debug')
    def test_get_all_certificate_profiles__raises_http_error(self, mock_debug, mock_raise_for_status):
        response = Mock(status_code=500, ok=False)
        response.json.return_value = "Something is wrong"
        self.user.post.return_value = response
        self.assertRaises(HTTPError, get_all_certificate_profiles, self.user)
        self.assertFalse(mock_debug.called)
        self.assertTrue(mock_raise_for_status.called)

    @patch('enmutils_int.lib.pkiadm.raise_for_status')
    @patch('enmutils_int.lib.pkiadm.log.logger.debug')
    def test_get_all_entity_profiles__is_success(self, mock_debug, mock_raise_for_status):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = [{'name': "Secui_six_sdfdgdfhg", 'id': 3, 'type': 'ENTITY_PROFILE'}]
        self.user.post.return_value = response
        get_all_entity_profiles(self.user)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_raise_for_status.called)

    @patch('enmutils_int.lib.pkiadm.raise_for_status', side_effect=HTTPError)
    @patch('enmutils_int.lib.pkiadm.log.logger.debug')
    def test_get_all_entity_profiles__raises_http_error(self, mock_debug, mock_raise_for_status):
        response = Mock(status_code=500, ok=False)
        response.json.return_value = "Something is wrong"
        self.user.post.return_value = response
        self.assertRaises(HTTPError, get_all_entity_profiles, self.user)
        self.assertFalse(mock_debug.called)
        self.assertTrue(mock_raise_for_status.called)


class CertificateProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.certificate_profiles = [{'name': "Other", 'id': 1, 'type': 'CERTIFICATE_PROFILE'},
                                     {'name': "Secui_six_sdfdgdfhg", 'id': 3, 'type': 'CERTIFICATE_PROFILE'}]
        self.cert = CertificateProfile(name=NAME, user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_certificate_profiles_body__is_not_none(self):
        self.assertIsNotNone(self.cert.body)

    def test_certificate_profile_create__raises_enm_application_error(self):
        response = Mock(status_code=200, ok=True, text=None)
        self.user.post.return_value = response
        self.assertRaises(EnmApplicationError, self.cert.create)

    def test_certificate_profile__create_sets_id(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"id": 41}
        self.user.post.return_value = response
        self.cert.create()
        self.assertEqual(41, self.cert.id)

    @patch("enmutils_int.lib.pkiadm.get_all_certificate_profiles")
    @patch("enmutils_int.lib.pkiadm.CertificateProfile.delete")
    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    def test_remove_old_certificate_profiles__is_success(self, mock_debug_log, mock_cert_delete,
                                                         mock_get_all_certificate_profiles):
        mock_get_all_certificate_profiles.return_value = self.certificate_profiles
        self.cert.name = "Secui_six_1d3f4g4f"
        self.cert.remove_old_certificate_profiles(self.user)
        self.assertEqual(mock_get_all_certificate_profiles.call_count, 1)
        self.assertEqual(mock_cert_delete.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.pkiadm.get_all_certificate_profiles")
    @patch("enmutils_int.lib.pkiadm.CertificateProfile.delete")
    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    def test_remove_old_certificate_profiles__no_cert_profiles_retrieved(self, mock_debug_log, mock_cert_delete,
                                                                         mock_get_all_certificate_profiles):
        mock_get_all_certificate_profiles.return_value = []
        self.cert.name = "Secui_six_1d3f4g4f"
        self.cert.remove_old_certificate_profiles(self.user)
        self.assertEqual(mock_get_all_certificate_profiles.call_count, 1)
        self.assertEqual(mock_cert_delete.call_count, 0)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.pkiadm.get_all_certificate_profiles")
    @patch("enmutils_int.lib.pkiadm.CertificateProfile.delete")
    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    def test_remove_old_certificate_profiles__if_get_cert_profiles_raises_exception(self, mock_debug_log,
                                                                                    mock_cert_delete,
                                                                                    mock_get_all_certificate_profiles):
        mock_get_all_certificate_profiles.side_effect = Exception("error")
        self.cert.name = "Secui_six_1d3f4g4f"
        self.cert.remove_old_certificate_profiles(self.user)
        self.assertEqual(mock_get_all_certificate_profiles.call_count, 1)
        self.assertEqual(mock_cert_delete.call_count, 0)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.pkiadm.get_all_certificate_profiles")
    @patch("enmutils_int.lib.pkiadm.CertificateProfile.delete")
    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    def test_remove_old_certificate_profiles__if_cert_delete_raises_error(self, mock_debug_log, mock_cert_delete,
                                                                          mock_get_all_certificate_profiles):
        mock_get_all_certificate_profiles.return_value = self.certificate_profiles
        mock_cert_delete.side_effect = Exception("error")
        self.cert.name = "Secui_six_1d3f4g4f"
        self.cert.remove_old_certificate_profiles(self.user)
        self.assertEqual(mock_get_all_certificate_profiles.call_count, 1)
        self.assertEqual(mock_cert_delete.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)


class EntityProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

        self.entity_profile = EntityProfile(name=NAME, user=self.user)
        self.json = [{"name": NAME, "id": 111, "type": "CERTIFICATE_PROFILE"}]

        self.entity_profiles = [{'name': "Other", 'id': 1, 'type': 'ENTITY_PROFILE'},
                                {'name': "Secui_six_1s3df4f7", 'id': 1, 'type': 'ENTITY_PROFILE'}]
        self.entity_profile.ENTITY_PROFILE_ID = 76
        self.entity_profile.ENTITY_PROFILE_NAME = "test"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.pkiadm.get_all_certificate_profiles")
    def test_entity_profiles_body__is_not_none(self, mock_get_all_certificate_profiles):
        mock_get_all_certificate_profiles.return_value = self.json
        self.assertIsNotNone(self.entity_profile.body)

    @patch("enmutils_int.lib.pkiadm.get_all_certificate_profiles")
    def test_entity_profile_create__sets_id(self, _):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"id": 41}
        self.user.post.return_value = response
        self.entity_profile.create()
        self.assertEqual(41, self.entity_profile.id)

    @patch("enmutils_int.lib.pkiadm.EntityProfile.delete")
    def test_teardown__calls_delete(self, mock_delete):
        self.entity_profile._teardown()
        self.assertEqual(1, mock_delete.call_count)

    @patch("enmutils_int.lib.pkiadm.get_all_certificate_profiles", return_value=[{'name': "Other", 'id': 1,
                                                                                  'type': 'CERTIFICATE_PROFILE'}])
    def test_certificate_profile_id__no_match(self, *_):
        self.assertEqual(self.entity_profile.certificate_profile_id, None)

    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    @patch("enmutils_int.lib.pkiadm.EntityProfile.delete")
    @patch("enmutils_int.lib.pkiadm.get_all_entity_profiles")
    def test_remove_old_entity_profiles__is_success(self, mock_get_all_entity_profiles, mock_entity_profile_delete,
                                                    mock_debug_log):
        self.entity_profile.name = "Secui_six_1d3f4g4f"
        mock_get_all_entity_profiles.return_value = self.entity_profiles
        self.entity_profile.remove_old_entity_profiles()
        self.assertEqual(mock_get_all_entity_profiles.call_count, 1)
        self.assertEqual(mock_entity_profile_delete.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    @patch("enmutils_int.lib.pkiadm.EntityProfile.delete")
    @patch("enmutils_int.lib.pkiadm.get_all_entity_profiles")
    def test_remove_old_entity_profiles__no_entity_profiles_found(self, mock_get_all_entity_profiles,
                                                                  mock_entity_profile_delete, mock_debug_log):
        self.entity_profile.name = "Secui_six_1d3f4g4f"
        mock_get_all_entity_profiles.return_value = []
        self.entity_profile.remove_old_entity_profiles()
        self.assertEqual(mock_get_all_entity_profiles.call_count, 1)
        self.assertEqual(mock_entity_profile_delete.call_count, 0)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    @patch("enmutils_int.lib.pkiadm.EntityProfile.delete")
    @patch("enmutils_int.lib.pkiadm.get_all_entity_profiles")
    def test_remove_old_entity_profiles__if_get_all_entity_profiles_raises_error(self, mock_get_all_entity_profiles,
                                                                                 mock_entity_profile_delete,
                                                                                 mock_debug_log):
        self.entity_profile.name = "Secui_six_1d3f4g4f"
        mock_get_all_entity_profiles.side_effect = Exception("error")
        self.entity_profile.remove_old_entity_profiles()
        self.assertEqual(mock_get_all_entity_profiles.call_count, 1)
        self.assertEqual(mock_entity_profile_delete.call_count, 0)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    @patch("enmutils_int.lib.pkiadm.EntityProfile.delete")
    @patch("enmutils_int.lib.pkiadm.get_all_entity_profiles")
    def test_remove_old_entity_profiles__if_delete_entity_profile_raises_error(self, mock_get_all_entity_profiles,
                                                                               mock_entity_profile_delete,
                                                                               mock_debug_log):
        self.entity_profile.name = "Secui_six_1d3f4g4f"
        mock_get_all_entity_profiles.return_value = self.entity_profiles
        mock_entity_profile_delete.side_effect = Exception("error")
        self.entity_profile.remove_old_entity_profiles()
        self.assertEqual(mock_get_all_entity_profiles.call_count, 1)
        self.assertEqual(mock_entity_profile_delete.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)


class EntityUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

        self.entity = Entity(name=NAME, user=self.user)
        self.json = [{"name": "Random", "id": 111, "type": "ENTITY_PROFILE"}]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.pkiadm.get_all_entity_profiles")
    def test_entity_body__is_not_none(self, mock_get_all_entity_profiles):
        mock_get_all_entity_profiles.return_value = self.json
        self.assertIsNotNone(self.entity.body)

    @patch("enmutils_int.lib.pkiadm.get_all_entity_profiles")
    def test_entity_create_sets_id(self, *_):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"entityInfo": {"id": 41}}
        self.user.post.return_value = response
        self.entity.create()
        self.assertEqual(41, self.entity.id)

    @patch('enmutils_int.lib.pkiadm.log.logger.debug')
    def test_entity_issue__success_calls_logger(self, mock_debug):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {u"Success": u"true"}
        self.user.post.return_value = response
        self.entity.issue()
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.pkiadm.log.logger.debug')
    def test_entity_revoke__success_calls_logger(self, mock_debug):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {u"Success": u"true"}
        self.user.post.return_value = response
        self.entity.revoke()
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.log.logger.debug')
    @patch("enmutils_int.lib.pkiadm.get_all_entity_profiles")
    def test_entity_body__with_amos_user(self, mock_get_all_entity_profiles, mock_debug):
        mock_get_all_entity_profiles.return_value = self.json
        self.entity.ENTITY_PROFILE_NAME = "AMOS_EM_USER_EP"
        self.assertIsNotNone(self.entity.body)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.pkiadm.log.logger.debug')
    @patch("enmutils_int.lib.pkiadm.get_all_entity_profiles")
    def test_entity_body__without_amos_user(self, mock_get_all_entity_profiles, mock_debug):
        mock_get_all_entity_profiles.return_value = self.json
        self.assertIsNotNone(self.entity.body)
        self.assertFalse(mock_debug.called)

    @patch('enmutils_int.lib.pkiadm.get_all_entity_profiles')
    def test_set_all_profiles__calls_fetch_all_profiles(self, mock_get_all_entity_profiles):
        mock_get_all_entity_profiles.return_value = [{"name": NAME, "id": 111, "type": "ENTITY_PROFILE"},
                                                     {"name": "Random", "id": 123, "type": "ENTITY_PROFILE"}]
        self.entity.set_all_profiles()
        mock_get_all_entity_profiles.assert_called_with(self.user, limit=6000)

    @patch('enmutils_int.lib.pkiadm.get_all_entity_profiles')
    def test_set_all_profiles__if_all_enm_profiles_is_not_none(self, mock_get_all_entity_profiles):
        self.entity.all_enm_profiles = [{"name": NAME, "id": 111, "type": "ENTITY_PROFILE"},
                                        {"name": "Random", "id": 122, "type": "ENTITY_PROFILE"}]
        self.entity.set_all_profiles()
        self.assertFalse(mock_get_all_entity_profiles.called)

    def test_set_entity_profile_name_and_id__is_successful(self):
        self.entity.all_enm_profiles = [{"name": NAME, "id": 111, "type": "CERTIFICATE_PROFILE"},
                                        {"name": "Random", "id": 121, "type": "ENTITY_PROFILE"},
                                        {"name": NAME, "id": 131, "type": "ENTITY_PROFILE"}]
        self.entity.set_entity_profile_name_and_id()
        self.assertEqual("Random", self.entity.ENTITY_PROFILE_NAME)
        self.assertEqual(121, self.entity.ENTITY_PROFILE_ID)

    def test_set_entity_profile_name_and_id__if_all_enm_profiles_is_empty(self):
        self.entity.all_enm_profiles = []
        self.entity.set_entity_profile_name_and_id()
        self.assertEqual('None', self.entity.ENTITY_PROFILE_NAME)
        self.assertEqual(0, self.entity.ENTITY_PROFILE_ID)

    @patch("enmutils_int.lib.pkiadm.Entity.get_all_entities", return_value=ENITITY_LIST)
    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    @patch("enmutils_int.lib.pkiadm.Entity.delete")
    @patch("enmutils_int.lib.pkiadm.Entity.revoke")
    def test_remove_old_entities__is_success(self, mock_revoke, mock_delete, mock_debug_log, _):
        self.entity.remove_old_entities()
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_revoke.call_count)
        self.assertEqual(1, mock_delete.call_count)

    @patch("enmutils_int.lib.pkiadm.Entity.get_all_entities")
    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    @patch("enmutils_int.lib.pkiadm.Entity.delete")
    @patch("enmutils_int.lib.pkiadm.Entity.revoke")
    def test_remove_old_entities__if_get_all_entities_raises_error(self, mock_revoke, mock_delete, mock_debug_log,
                                                                   mock_get_all_entities):
        mock_get_all_entities.side_effect = Exception("something is wrong")
        self.entity.remove_old_entities()
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(0, mock_revoke.call_count)
        self.assertEqual(0, mock_delete.call_count)

    @patch("enmutils_int.lib.pkiadm.Entity.get_all_entities", return_value=ENITITY_LIST)
    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    @patch("enmutils_int.lib.pkiadm.Entity.delete")
    @patch("enmutils_int.lib.pkiadm.Entity.revoke")
    def test_remove_old_entities__if_entity_revoke_raises_error(self, mock_revoke, mock_delete, mock_debug_log, _):
        mock_revoke.side_effect = Exception("something is wrong")
        self.entity.remove_old_entities()
        self.assertEqual(3, mock_debug_log.call_count)
        self.assertEqual(1, mock_revoke.call_count)
        self.assertEqual(0, mock_delete.call_count)

    @patch("enmutils_int.lib.pkiadm.Entity.get_all_entities", return_value=ENITITY_LIST)
    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    @patch("enmutils_int.lib.pkiadm.Entity.delete")
    @patch("enmutils_int.lib.pkiadm.Entity.revoke")
    def test_remove_old_entities__if_entity_delete_raises_error(self, mock_revoke, mock_delete, mock_debug_log, _):
        mock_delete.side_effect = Exception("something is wrong")
        self.entity.remove_old_entities()
        self.assertEqual(3, mock_debug_log.call_count)
        self.assertEqual(1, mock_revoke.call_count)
        self.assertEqual(1, mock_delete.call_count)

    @patch("enmutils_int.lib.pkiadm.Entity.get_all_entities", return_value=[])
    @patch("enmutils_int.lib.pkiadm.log.logger.debug")
    @patch("enmutils_int.lib.pkiadm.Entity.delete")
    @patch("enmutils_int.lib.pkiadm.Entity.revoke")
    def test_remove_old_entities__no_entities_retrieved(self, mock_revoke, mock_delete, mock_debug_log, _):
        self.entity.remove_old_entities()
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_revoke.call_count)
        self.assertEqual(0, mock_delete.call_count)

    @patch("enmutils_int.lib.pkiadm.Entity.delete")
    @patch("enmutils_int.lib.pkiadm.Entity.revoke")
    def test_teardown__calls_revoke_and_delete(self, mock_revoke, mock_delete):
        self.entity._teardown()
        self.assertEqual(1, mock_revoke.call_count)
        self.assertEqual(1, mock_delete.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
