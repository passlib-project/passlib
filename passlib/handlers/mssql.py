"""passlib.handlers.mssql - MS-SQL Password Hash

Notes
=====
MS-SQL has used a number of hash algs over the years,
most of which were exposed through the undocumented
'pwdencrypt' and 'pwdcompare' sql functions.

Known formats
-------------
6.5
    snefru hash, ascii encoded password
    no examples found

7.0
    snefru hash, unicode (what encoding?)
    saw ref that these blobs were 16 bytes in size
    no examples found

2000
    byte string using displayed as 0x hex, using 0x0100 prefix.
    contains hashes of password and upper-case password.

2007
    same as 2000, but without the upper-case hash.

refs
----------
https://blogs.msdn.com/b/lcris/archive/2007/04/30/sql-server-2005-about-login-password-hashes.aspx?Redirected=true
http://us.generation-nt.com/securing-passwords-hash-help-35429432.html
http://forum.md5decrypter.co.uk/topic230-mysql-and-mssql-get-password-hashes.aspx
http://www.theregister.co.uk/2002/07/08/cracking_ms_sql_server_passwords/
"""
#=============================================================================
# imports
#=============================================================================
# core
from binascii import hexlify, unhexlify
from hashlib import sha1
import re
import logging; log = logging.getLogger(__name__)
from warnings import warn
# site
# pkg
from passlib.utils import consteq
from passlib.utils.compat import bascii_to_str, unicode, u
import passlib.utils.handlers as uh
# local
__all__ = [
    "mssql2000",
    "mssql2005",
]

#=============================================================================
# mssql 2000
#=============================================================================
def _raw_mssql(secret, salt):
    assert isinstance(secret, unicode)
    assert isinstance(salt, bytes)
    return sha1(secret.encode("utf-16-le") + salt).digest()

BIDENT = b"0x0100"
##BIDENT2 = b("\x01\x00")
UIDENT = u("0x0100")

def _ident_mssql(hash, csize, bsize):
    """common identify for mssql 2000/2005"""
    if isinstance(hash, unicode):
        if len(hash) == csize and hash.startswith(UIDENT):
            return True
    elif isinstance(hash, bytes):
        if len(hash) == csize and hash.startswith(BIDENT):
            return True
        ##elif len(hash) == bsize and hash.startswith(BIDENT2): # raw bytes
        ##    return True
    else:
        raise uh.exc.ExpectedStringError(hash, "hash")
    return False

def _parse_mssql(hash, csize, bsize, handler):
    """common parser for mssql 2000/2005; returns 4 byte salt + checksum"""
    if isinstance(hash, unicode):
        if len(hash) == csize and hash.startswith(UIDENT):
            try:
                return unhexlify(hash[6:].encode("utf-8"))
            except TypeError: # throw when bad char found
                pass
    elif isinstance(hash, bytes):
        # assumes ascii-compat encoding
        assert isinstance(hash, bytes)
        if len(hash) == csize and hash.startswith(BIDENT):
            try:
                return unhexlify(hash[6:])
            except TypeError: # throw when bad char found
                pass
        ##elif len(hash) == bsize and hash.startswith(BIDENT2): # raw bytes
        ##    return hash[2:]
    else:
        raise uh.exc.ExpectedStringError(hash, "hash")
    raise uh.exc.InvalidHashError(handler)

class mssql2000(uh.HasRawSalt, uh.HasRawChecksum, uh.GenericHandler):
    """This class implements the password hash used by MS-SQL 2000, and follows the :ref:`password-hash-api`.

    It supports a fixed-length salt.

    The :meth:`~passlib.ifc.PasswordHash.hash` and :meth:`~passlib.ifc.PasswordHash.genconfig` methods accept the following optional keywords:

    :type salt: bytes
    :param salt:
        Optional salt string.
        If not specified, one will be autogenerated (this is recommended).
        If specified, it must be 4 bytes in length.

    :type relaxed: bool
    :param relaxed:
        By default, providing an invalid value for one of the other
        keywords will result in a :exc:`ValueError`. If ``relaxed=True``,
        and the error can be corrected, a :exc:`~passlib.exc.PasslibHashWarning`
        will be issued instead. Correctable errors include
        ``salt`` strings that are too long.
    """
    #===================================================================
    # algorithm information
    #===================================================================
    name = "mssql2000"
    setting_kwds = ("salt",)
    checksum_size = 40
    min_salt_size = max_salt_size = 4

    #===================================================================
    # formatting
    #===================================================================

    # 0100 - 2 byte identifier
    # 4 byte salt
    # 20 byte checksum
    # 20 byte checksum
    # = 46 bytes
    # encoded '0x' + 92 chars = 94

    @classmethod
    def identify(cls, hash):
        return _ident_mssql(hash, 94, 46)

    @classmethod
    def from_string(cls, hash):
        data = _parse_mssql(hash, 94, 46, cls)
        return cls(salt=data[:4], checksum=data[4:])

    def to_string(self):
        raw = self.salt + self.checksum
        # raw bytes format - BIDENT2 + raw
        return "0x0100" + bascii_to_str(hexlify(raw).upper())

    def _calc_checksum(self, secret):
        if isinstance(secret, bytes):
            secret = secret.decode("utf-8")
        salt = self.salt
        return _raw_mssql(secret, salt) + _raw_mssql(secret.upper(), salt)

    @classmethod
    def verify(cls, secret, hash):
        # NOTE: we only compare against the upper-case hash
        # XXX: add 'full' just to verify both checksums?
        uh.validate_secret(secret)
        self = cls.from_string(hash)
        chk = self.checksum
        if chk is None:
            raise uh.exc.MissingDigestError(cls)
        if isinstance(secret, bytes):
            secret = secret.decode("utf-8")
        result = _raw_mssql(secret.upper(), self.salt)
        return consteq(result, chk[20:])

#=============================================================================
# handler
#=============================================================================
class mssql2005(uh.HasRawSalt, uh.HasRawChecksum, uh.GenericHandler):
    """This class implements the password hash used by MS-SQL 2005, and follows the :ref:`password-hash-api`.

    It supports a fixed-length salt.

    The :meth:`~passlib.ifc.PasswordHash.hash` and :meth:`~passlib.ifc.PasswordHash.genconfig` methods accept the following optional keywords:

    :type salt: bytes
    :param salt:
        Optional salt string.
        If not specified, one will be autogenerated (this is recommended).
        If specified, it must be 4 bytes in length.

    :type relaxed: bool
    :param relaxed:
        By default, providing an invalid value for one of the other
        keywords will result in a :exc:`ValueError`. If ``relaxed=True``,
        and the error can be corrected, a :exc:`~passlib.exc.PasslibHashWarning`
        will be issued instead. Correctable errors include
        ``salt`` strings that are too long.
    """
    #===================================================================
    # algorithm information
    #===================================================================
    name = "mssql2005"
    setting_kwds = ("salt",)

    checksum_size = 20
    min_salt_size = max_salt_size = 4

    #===================================================================
    # formatting
    #===================================================================

    # 0x0100 - 2 byte identifier
    # 4 byte salt
    # 20 byte checksum
    # = 26 bytes
    # encoded '0x' + 52 chars = 54

    @classmethod
    def identify(cls, hash):
        return _ident_mssql(hash, 54, 26)

    @classmethod
    def from_string(cls, hash):
        data = _parse_mssql(hash, 54, 26, cls)
        return cls(salt=data[:4], checksum=data[4:])

    def to_string(self):
        raw = self.salt + self.checksum
        # raw bytes format - BIDENT2 + raw
        return "0x0100" + bascii_to_str(hexlify(raw)).upper()

    def _calc_checksum(self, secret):
        if isinstance(secret, bytes):
            secret = secret.decode("utf-8")
        return _raw_mssql(secret, self.salt)

    #===================================================================
    # eoc
    #===================================================================

#=============================================================================
# eof
#=============================================================================
