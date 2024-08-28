#!/usr/bin/env python
# -*- coding: utf-8 -*-
# *************************************************************************
# Ericsson LMI                 Utility Script
# *************************************************************************
#
# (c) Ericsson LMI 2015 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property of
# Ericsson LMI. The programs may be used and/or copied only with the
# written permission from Ericsson LMI or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
#
# *************************************************************************
# Name    : Security
# Purpose : Provides functionality to encrypt passwords.
# *************************************************************************


import re
import string

from base64 import standard_b64encode

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import random
from Crypto.Util import Counter


ENM_USERNAME_PATTERN = re.compile(r"^[\w\.\-]{1,255}$", re.UNICODE)
ENM_NAME_PATTERN = re.compile(
    r"^[\w\'\-ÁüąĄćĆœŒÂęĘÐÛ¡ÚøÜ¿âŁÀÃłÅÄÇÆÉÈËÊÍÌÏÎÑùÓÒÕÔÖÙØśŚÝûßÞáàãúåäçæéèëêíìïîñðóòõôöŹŸŻźýżþ\s]{1,255}$", re.UNICODE)


def encrypt(data_to_encrypt, password, base_64_encoding=True):
    """
    B{It encrypts the specified data based on the given passphrase}.

    :type data_to_encrypt: str
    :param data_to_encrypt: String that is to be encrypted
    :type password: str
    :param password: Password to derive cipher encryption key
    :type base_64_encoding: bool
    :param base_64_encoding: Base64 encode the resulting encrypted text
    :rtype: str
    :return: Encrypted data
    """
    ctr = Counter.new(128)
    salt, key = _derive_keys(password)
    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
    encrypted_data = cipher.encrypt(data_to_encrypt)

    if base_64_encoding:
        return standard_b64encode(encrypted_data), salt
    else:
        return encrypted_data, salt


def _derive_keys(password, salt=None):
    """
    B{It derives encryption key and salt for cipher based on the given password}

    :type password: str
    :param password: Passphrase that is used to derive encryption keys
    :type salt: str
    :param salt: Salt that should be used to digest the password
    :rtype: list[string]
    :return: The salt and cipher key generated
    """

    if salt is None:
        random_generator = random.StrongRandom()
        salt = "".join(random_generator.choice(string.printable[:94]) for _ in range(8))

    sha256_hash_func = SHA256.new(salt)
    sha256_hash_func.update(password)
    key = sha256_hash_func.digest()

    return salt, key
