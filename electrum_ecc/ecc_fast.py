# Copyright (c) 2013-2018 Richard Kiss
# Copyright (c) 2018-2024 The Electrum developers
# Distributed under the MIT software license, see the accompanying
# file LICENCE or http://www.opensource.org/licenses/mit-license.php
#
# Originally based on pycoin:
# https://github.com/richardkiss/pycoin/blob/01b1787ed902df23f99a55deb00d8cd076a906fe/pycoin/ecdsa/native/secp256k1.py

import logging
import os
import sys
import ctypes
from ctypes import (
    c_int, c_uint, c_char, c_size_t, c_void_p,
    CFUNCTYPE, POINTER,
)
from bisq.common.setup.log_setup import get_base_logger

_logger = get_base_logger(__name__)
_logger.setLevel(logging.DEBUG)



SECP256K1_FLAGS_TYPE_MASK = ((1 << 8) - 1)
SECP256K1_FLAGS_TYPE_CONTEXT = (1 << 0)
SECP256K1_FLAGS_TYPE_COMPRESSION = (1 << 1)
# /** The higher bits contain the actual data. Do not use directly. */
SECP256K1_FLAGS_BIT_CONTEXT_VERIFY = (1 << 8)
SECP256K1_FLAGS_BIT_CONTEXT_SIGN = (1 << 9)
SECP256K1_FLAGS_BIT_COMPRESSION = (1 << 8)

# /** Flags to pass to secp256k1_context_create. */
SECP256K1_CONTEXT_VERIFY = (SECP256K1_FLAGS_TYPE_CONTEXT | SECP256K1_FLAGS_BIT_CONTEXT_VERIFY)
SECP256K1_CONTEXT_SIGN = (SECP256K1_FLAGS_TYPE_CONTEXT | SECP256K1_FLAGS_BIT_CONTEXT_SIGN)
SECP256K1_CONTEXT_NONE = (SECP256K1_FLAGS_TYPE_CONTEXT)

SECP256K1_EC_COMPRESSED = (SECP256K1_FLAGS_TYPE_COMPRESSION | SECP256K1_FLAGS_BIT_COMPRESSION)
SECP256K1_EC_UNCOMPRESSED = (SECP256K1_FLAGS_TYPE_COMPRESSION)


class LibModuleMissing(Exception): pass


# note: new releases of bitcoin-core/secp256k1 sometimes bump the ABI version. When that happens,
#       the new version should be tested and added to this list.
# note: for a mapping between bitcoin-core/secp256k1 git tags and .so.V libtool version numbers,
#       see https://github.com/bitcoin-core/secp256k1/pull/1055#issuecomment-1227505189
KNOWN_COMPATIBLE_ABI_VERSIONS = [5, 2, 1, 0, ]  # try latest version first


def load_library():
    global HAS_SCHNORR

    libnames_local = []
    libnames_anywhere = []
    if sys.platform == 'darwin':
        for v in KNOWN_COMPATIBLE_ABI_VERSIONS:
            libname = f"libsecp256k1.{v}.dylib"
            libnames_local.append(libname)
            libnames_anywhere.append(libname)
    elif sys.platform in ('windows', 'win32'):
        for v in KNOWN_COMPATIBLE_ABI_VERSIONS:
            libname = f"libsecp256k1-{v}.dll"
            libnames_local.append(libname)
            libnames_anywhere.append(libname)
    elif 'ANDROID_DATA' in os.environ:
        # don't care about version number. we built w/e is available.
        libname = "libsecp256k1.so"
        libnames_local.append(libname)
        libnames_anywhere.append(libname)
    else:  # desktop Linux and similar
        for v in KNOWN_COMPATIBLE_ABI_VERSIONS:
            libname = f"libsecp256k1.so.{v}"
            libnames_local.append(libname)
            libnames_anywhere.append(libname)
        libnames_local.append("libsecp256k1.so")
        # maybe we could fall back to trying "any" version? maybe guarded with an env var?
        #libnames_anywhere.append(f"libsecp256k1.so")
    library_paths = []
    for libname in libnames_local:  # try local files in repo dir first (for security, but also compat)
        library_paths.append(os.path.join(os.path.dirname(__file__), libname))
    for libname in libnames_anywhere:
        library_paths.append(libname)

    exceptions = []
    secp256k1 = None
    for libpath in library_paths:
        try:
            secp256k1 = ctypes.cdll.LoadLibrary(libpath)
        except BaseException as e:
            exceptions.append(e)
        else:
            break
    if not secp256k1:
        _logger.error(f'libsecp256k1 library failed to load. exceptions: {repr(exceptions)}')
        return None

    try:
        secp256k1.secp256k1_context_create.argtypes = [c_uint]
        secp256k1.secp256k1_context_create.restype = c_void_p

        secp256k1.secp256k1_context_randomize.argtypes = [c_void_p, POINTER(c_char)]
        secp256k1.secp256k1_context_randomize.restype = c_int

        secp256k1.secp256k1_ec_pubkey_create.argtypes = [c_void_p, c_void_p, POINTER(c_char)]
        secp256k1.secp256k1_ec_pubkey_create.restype = c_int

        secp256k1.secp256k1_ecdsa_sign.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), POINTER(c_char), c_void_p, c_void_p]
        secp256k1.secp256k1_ecdsa_sign.restype = c_int

        #secp256k1.secp256k1_ecdh.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), POINTER(c_char), HASHFN, c_void_p]
        #secp256k1.secp256k1_ecdh.restype = c_int

        secp256k1.secp256k1_ecdsa_verify.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), POINTER(c_char)]
        secp256k1.secp256k1_ecdsa_verify.restype = c_int

        secp256k1.secp256k1_ec_pubkey_parse.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), c_size_t]
        secp256k1.secp256k1_ec_pubkey_parse.restype = c_int

        secp256k1.secp256k1_ec_pubkey_serialize.argtypes = [c_void_p, POINTER(c_char), c_void_p, POINTER(c_char), c_uint]
        secp256k1.secp256k1_ec_pubkey_serialize.restype = c_int

        secp256k1.secp256k1_ecdsa_signature_parse_compact.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char)]
        secp256k1.secp256k1_ecdsa_signature_parse_compact.restype = c_int

        secp256k1.secp256k1_ecdsa_signature_normalize.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char)]
        secp256k1.secp256k1_ecdsa_signature_normalize.restype = c_int

        secp256k1.secp256k1_ecdsa_signature_serialize_compact.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char)]
        secp256k1.secp256k1_ecdsa_signature_serialize_compact.restype = c_int

        secp256k1.secp256k1_ecdsa_signature_parse_der.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), c_size_t]
        secp256k1.secp256k1_ecdsa_signature_parse_der.restype = c_int
    
        try:
            secp256k1.ecdsa_signature_parse_der_lax.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), c_size_t]
            secp256k1.ecdsa_signature_parse_der_lax.restype = c_int
        except:
            pass

        secp256k1.secp256k1_ecdsa_signature_serialize_der.argtypes = [c_void_p, POINTER(c_char), c_void_p, POINTER(c_char)]
        secp256k1.secp256k1_ecdsa_signature_serialize_der.restype = c_int

        secp256k1.secp256k1_ec_pubkey_tweak_mul.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char)]
        secp256k1.secp256k1_ec_pubkey_tweak_mul.restype = c_int

        secp256k1.secp256k1_ec_pubkey_combine.argtypes = [c_void_p, POINTER(c_char), c_void_p, c_size_t]
        secp256k1.secp256k1_ec_pubkey_combine.restype = c_int

        # --enable-module-recovery
        try:
            secp256k1.secp256k1_ecdsa_recover.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), POINTER(c_char)]
            secp256k1.secp256k1_ecdsa_recover.restype = c_int

            secp256k1.secp256k1_ecdsa_recoverable_signature_parse_compact.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), c_int]
            secp256k1.secp256k1_ecdsa_recoverable_signature_parse_compact.restype = c_int
        except (OSError, AttributeError):
            raise LibModuleMissing('libsecp256k1 library found but it was built '
                                   'without required module (--enable-module-recovery)')

        # --enable-module-schnorrsig
        try:
            secp256k1.secp256k1_schnorrsig_sign32.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), POINTER(c_char), POINTER(c_char)]
            secp256k1.secp256k1_schnorrsig_sign32.restype = c_int

            secp256k1.secp256k1_schnorrsig_verify.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char), c_size_t, POINTER(c_char)]
            secp256k1.secp256k1_schnorrsig_verify.restype = c_int
        except (OSError, AttributeError):
            _logger.warning(f"libsecp256k1 library found but it was built without desired module (--enable-module-schnorrsig)")
            HAS_SCHNORR = False
            # raise LibModuleMissing('libsecp256k1 library found but it was built '
            #                        'without required module (--enable-module-schnorrsig)')

        # --enable-module-extrakeys
        try:
            secp256k1.secp256k1_xonly_pubkey_parse.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char)]
            secp256k1.secp256k1_xonly_pubkey_parse.restype = c_int

            secp256k1.secp256k1_xonly_pubkey_serialize.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char)]
            secp256k1.secp256k1_xonly_pubkey_serialize.restype = c_int

            secp256k1.secp256k1_keypair_create.argtypes = [c_void_p, POINTER(c_char), POINTER(c_char)]
            secp256k1.secp256k1_keypair_create.restype = c_int
        except (OSError, AttributeError):
            _logger.warning(f"libsecp256k1 library found but it was built without desired module (--enable-module-extrakeys)")
            HAS_SCHNORR = False
            # raise LibModuleMissing('libsecp256k1 library found but it was built '
            #                        'without required module (--enable-module-extrakeys)')

        secp256k1.ctx = secp256k1.secp256k1_context_create(SECP256K1_CONTEXT_SIGN | SECP256K1_CONTEXT_VERIFY)
        ret = secp256k1.secp256k1_context_randomize(secp256k1.ctx, os.urandom(32))
        if not ret:
            _logger.error('secp256k1_context_randomize failed')
            return None

        return secp256k1
    except (OSError, AttributeError) as e:
        _logger.error(f'libsecp256k1 library was found and loaded but there was an error when using it: {repr(e)}')
        return None


_libsecp256k1 = None
HAS_SCHNORR = True
try:
    _libsecp256k1 = load_library()
except BaseException as e:
    _logger.error(f'failed to load libsecp256k1: {repr(e)}')


if _libsecp256k1 is None:
    # hard fail:
    raise ImportError("Failed to load libsecp256k1")


def version_info() -> dict:
    return {
        "libsecp256k1.path": _libsecp256k1._name if _libsecp256k1 else None,
    }
