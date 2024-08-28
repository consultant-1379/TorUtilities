#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from base64 import standard_b64encode

import unittest2
from mock import patch
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib import security
from testslib import unit_test_utils


class SecurityUnitTests(ParameterizedTestCase):

    test_strong_password = r"ArvIz_Tur0_Tuk0r%Fur0-G3p!$2342"
    test_password_data = r"L0ng_L0ng_PlAin_T3xt_Password!%^&*$#!"
    test_salt = r"__salt__"
    test_b64_key = r"cQlaIVya1SEhuUigzHrMbszvhQpeMe4Gp7Ia46Z/KGk="
    test_b64_encrypted_password_block = r"Ju350m7A+OE0N9XR3xc3I5SJGM4PtYkS9BbRrwgf2UlaHbV9YQ=="

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("Crypto.Random.random.StrongRandom.choice")
    def test_encrypt_with_base64_output(self, mock_rand_choice):
        # Mocking pseudo-random generator output
        mock_rand_choice.side_effect = [letter for letter in self.test_salt]

        self.assertEqual(security.encrypt(self.test_password_data,
                                          self.test_strong_password, True),
                         (self.test_b64_encrypted_password_block,
                          self.test_salt))

    def test_derive_keys_with_no_salt(self):
        salt, key = security._derive_keys(self.test_strong_password)
        self.assertEqual(len(salt), 8)
        self.assertEqual(len(key), 32)

    def test_derive_keys_with_fixed_salt(self):
        salt, key = security._derive_keys(self.test_strong_password,
                                          self.test_salt)
        self.assertEqual(len(salt), 8)
        self.assertEqual(len(key), 32)
        self.assertEqual(standard_b64encode(key), self.test_b64_key)

    def test_encrypt_with_base64_equals_false(self):
        actual_result = security.encrypt(self.test_password_data, self.test_strong_password, False)
        self.assertIsNotNone(actual_result)
        self.assertNotEqual("", actual_result)
        self.assertNotEqual(self.test_password_data, actual_result)


if __name__ == "__main__":
    suite = unittest2.TestLoader().loadTestsFromTestCase(SecurityUnitTests)
    result = unittest2.TextTestRunner(verbosity=2).run(suite)

    if not result.wasSuccessful():
        sys.exit(1)
