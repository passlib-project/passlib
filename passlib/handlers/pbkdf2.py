"""passlib.handlers.pbkdf - PBKDF2 based hashes"""
#=========================================================
#imports
#=========================================================
#core
from binascii import hexlify, unhexlify
from base64 import b64encode, b64decode
import re
import logging; log = logging.getLogger(__name__)
from warnings import warn
#site
#libs
from passlib.utils import adapted_b64_encode, adapted_b64_decode, ALL_BYTE_VALUES, handlers as uh
from passlib.utils.pbkdf2 import pbkdf2
#pkg
#local
__all__ = [
    "pbkdf2_sha1",
    "pbkdf2_sha256",
    "pbkdf2_sha512",
    "dlitz_pbkdf2_sha1",
    "grub_pbkdf2_sha512",
]

#=========================================================
#
#=========================================================
class Pbkdf2DigestHandler(uh.HasRounds, uh.HasRawSalt, uh.HasRawChecksum, uh.GenericHandler):
    "base class for various pbkdf2_{digest} algorithms"
    #=========================================================
    #class attrs
    #=========================================================

    #--GenericHandler--
    setting_kwds = ("salt", "rounds")

    #--HasSalt--
    default_salt_chars = 16
    min_salt_chars = 0
    max_salt_chars = 1024

    #--HasRounds--
    default_rounds = 6400
    min_rounds = 1
    max_rounds = 2**32-1
    rounds_cost = "linear"

    #--this class--
    _prf = None #subclass specified prf identifier

    #NOTE: max_salt_chars and max_rounds are arbitrarily chosen to provide sanity check.
    #      the underlying pbkdf2 specifies no bounds for either.

    #NOTE: defaults chosen to be at least as large as pbkdf2 rfc recommends...
    #      >8 bytes of entropy in salt, >1000 rounds
    #      increased due to time since rfc established

    #=========================================================
    #methods
    #=========================================================

    @classmethod
    def from_string(cls, hash):
        if not hash:
            raise ValueError("no hash specified")
        rounds, salt, chk = uh.parse_mc3(hash, cls.ident, cls.name)
        int_rounds = int(rounds)
        if rounds != str(int_rounds): #forbid zero padding, etc.
            raise ValueError("invalid %s hash" % (cls.name,))
        raw_salt = adapted_b64_decode(salt)
        raw_chk = adapted_b64_decode(chk) if chk else None
        return cls(
            rounds=int_rounds,
            salt=raw_salt,
            checksum=raw_chk,
            strict=bool(raw_chk),
        )

    def to_string(self, withchk=True):
        salt = adapted_b64_encode(self.salt)
        if withchk and self.checksum:
            return '%s%d$%s$%s' % (self.ident, self.rounds, salt, adapted_b64_encode(self.checksum))
        else:
            return '%s%d$%s' % (self.ident, self.rounds, salt)

    def calc_checksum(self, secret):
        if isinstance(secret, unicode):
            secret = secret.encode("utf-8")
        return pbkdf2(secret, self.salt, self.rounds, self.checksum_chars, self._prf)

def create_pbkdf2_hash(hash_name, digest_size):
    "create new Pbkdf2DigestHandler subclass for a specific hash"
    name = 'pbkdf2_' + hash_name
    ident = "$pbkdf2-%s$" % (hash_name,)
    prf = "hmac-%s" % (hash_name,)
    base = Pbkdf2DigestHandler
    return type(name, (base,), dict(
        name=name,
        ident=ident,
        _prf = prf,
        checksum_chars=digest_size,
        encoded_checksum_chars=(digest_size*4+2)//3,
        __doc__="""This class implements passlib's pbkdf2-%(prf)s hash, and follows the :ref:`password-hash-api`.

    It supports a variable-length salt, and a variable number of rounds.

    The :meth:`encrypt()` and :meth:`genconfig` methods accept the following optional keywords:

    :param salt:
        Optional salt bytes.
        If specified, the length must be between 0-1024 bytes.
        If not specified, a %(dsc)d byte salt will be autogenerated (this is recommended).

    :param rounds:
        Optional number of rounds to use.
        Defaults to %(dr)d, but must be within ``range(1,1<<32)``.
    """ % dict(prf=prf, dsc=base.default_salt_chars, dr=base.default_rounds)
    ))

#---------------------------------------------------------
#derived handlers
#---------------------------------------------------------
pbkdf2_sha1 = create_pbkdf2_hash("sha1", 20)
pbkdf2_sha256 = create_pbkdf2_hash("sha256", 32)
pbkdf2_sha512 = create_pbkdf2_hash("sha512", 64)

#=========================================================
#dlitz's pbkdf2 hash
#=========================================================
class dlitz_pbkdf2_sha1(uh.HasRounds, uh.HasSalt, uh.GenericHandler):
    """This class implements Dwayne Litzenberger's PBKDF2-based crypt algorithm, and follows the :ref:`password-hash-api`.

    It supports a variable-length salt, and a variable number of rounds.

    The :meth:`encrypt()` and :meth:`genconfig` methods accept the following optional keywords:

    :param salt:
        Optional salt string.
        If specified, it may be any length, but must use the characters in the regexp range ``[./0-9A-Za-z]``.
        If not specified, a 16 character salt will be autogenerated (this is recommended).

    :param rounds:
        Optional number of rounds to use.
        Defaults to 10000, must be within ``range(1,1<<32)``.
    """

    #=========================================================
    #class attrs
    #=========================================================
    #--GenericHandler--
    name = "dlitz_pbkdf2_sha1"
    setting_kwds = ("salt", "rounds")
    ident = "$p5k2$"

    #NOTE: max_salt_chars and max_rounds are arbitrarily chosen to provide sanity check.
    #   underlying algorithm (and reference implementation) allow effectively unbounded values for both of these.

    #--HasSalt--
    default_salt_chars = 16
    min_salt_chars = 0
    max_salt_chars = 1024

    #--HasROunds--
    default_rounds = 10000
    min_rounds = 0
    max_rounds = 2**32-1
    rounds_cost = "linear"

    #=========================================================
    #formatting
    #=========================================================

    #hash       $p5k2$c$u9HvcT4d$Sd1gwSVCLZYAuqZ25piRnbBEoAesaa/g
    #ident      $p5k2$
    #rounds     c
    #salt       u9HvcT4d
    #chk        Sd1gwSVCLZYAuqZ25piRnbBEoAesaa/g
    #rounds in lowercase hex, no zero padding

    @classmethod
    def from_string(cls, hash):
        if not hash:
            raise ValueError("no hash specified")
        rounds, salt, chk = uh.parse_mc3(hash, cls.ident, cls.name)
        if rounds.startswith("0"): #zero not allowed, nor left-padded with zeroes
            raise ValueError("invalid dlitz_pbkdf2_crypt hash")
        rounds = int(rounds, 16) if rounds else 400
        return cls(
            rounds=rounds,
            salt=salt,
            checksum=chk,
            strict=bool(chk),
        )

    def to_string(self, withchk=True):
        if self.rounds == 400:
            out = '$p5k2$$%s' % (self.salt,)
        else:
            out = '$p5k2$%x$%s' % (self.rounds, self.salt)
        if withchk and self.checksum:
            out = "%s$%s" % (out,self.checksum)
        return out

    #=========================================================
    #backend
    #=========================================================
    def calc_checksum(self, secret):
        if isinstance(secret, unicode):
            secret = secret.encode("utf-8")
        salt = self.to_string(withchk=False)
        result = pbkdf2(secret, salt, self.rounds, 24, "hmac-sha1")
        return adapted_b64_encode(result)

    #=========================================================
    #eoc
    #=========================================================

#=========================================================
#crowd
#=========================================================
class atlassian_pbkdf2_sha1(uh.HasRawSalt, uh.HasRawChecksum, uh.GenericHandler):
    """This class implements the PBKDF2 hash used by Atlassian.

    It supports a fixed-length salt, and a fixed number of rounds.

    The :meth:`encrypt()` and :meth:`genconfig` methods accept the following optional keyword:

    :param salt:
        Optional salt bytes.
        If specified, the length must be exactly 16 bytes.
        If not specified, a salt will be autogenerated (this is recommended).
    """
    #--GenericHandler--
    name = "atlassian_pbkdf2_sha1"
    setting_kwds =("salt",)
    ident = "{PKCS5S2}"
    checksum_chars = 32

    _stub_checksum = "\x00" * 32

    #--HasRawSalt--
    min_salt_chars = max_salt_chars = 16

    @classmethod
    def from_string(cls, hash):
        if not hash:
            raise ValueError("no hash specified")
        if isinstance(hash, unicode):
            hash = hash.encode("ascii")
        ident = cls.ident
        if not hash.startswith(ident):
            raise ValueError("invalid %s hash" % (cls.name,))
        data = b64decode(hash[len(ident):])
        salt, chk = data[:16], data[16:]
        return cls(salt=salt, checksum=chk, strict=True)

    def to_string(self):
        data = self.salt + (self.checksum or self._stub_checksum)
        return self.ident + b64encode(data)

    def calc_checksum(self, secret):
        #TODO: find out what crowd's policy is re: unicode
        if isinstance(secret, unicode):
            secret = secret.encode("utf-8")
        #crowd seems to use a fixed number of rounds.
        return pbkdf2(secret, self.salt, 10000, 32, "hmac-sha1")

#=========================================================
#grub
#=========================================================
class grub_pbkdf2_sha512(uh.HasRounds, uh.HasRawSalt, uh.HasRawChecksum, uh.GenericHandler):
    """This class implements Grub's pbkdf2-hmac-sha512 hash, and follows the :ref:`password-hash-api`.

    It supports a variable-length salt, and a variable number of rounds.

    The :meth:`encrypt()` and :meth:`genconfig` methods accept the following optional keywords:

    :param salt:
        Optional salt bytes.
        If specified, the length must be between 0-1024 bytes.
        If not specified, a 64 byte salt will be autogenerated (this is recommended).

    :param rounds:
        Optional number of rounds to use.
        Defaults to 10000, but must be within ``range(1,1<<32)``.
    """
    name = "grub_pbkdf2_sha512"
    setting_kwds = ("salt", "rounds")

    ident = "grub.pbkdf2.sha512."

    #NOTE: max_salt_chars and max_rounds are arbitrarily chosen to provide sanity check.
    #      the underlying pbkdf2 specifies no bounds for either,
    #      and it's not clear what grub specifies.

    default_salt_chars = 64
    min_salt_chars = 0
    max_salt_chars = 1024

    default_rounds = 10000
    min_rounds = 1
    max_rounds = 2**32-1
    rounds_cost = "linear"

    @classmethod
    def from_string(cls, hash):
        if not hash:
            raise ValueError("no hash specified")
        rounds, salt, chk = uh.parse_mc3(hash, cls.ident, cls.name, sep=".")
        int_rounds = int(rounds)
        if rounds != str(int_rounds): #forbid zero padding, etc.
            raise ValueError("invalid %s hash" % (cls.name,))
        raw_salt = unhexlify(salt)
        raw_chk = unhexlify(chk) if chk else None
        return cls(
            rounds=int_rounds,
            salt=raw_salt,
            checksum=raw_chk,
            strict=bool(raw_chk),
        )

    def to_string(self, withchk=True):
        salt = hexlify(self.salt).upper()
        if withchk and self.checksum:
            return '%s%d.%s.%s' % (self.ident, self.rounds, salt, hexlify(self.checksum).upper())
        else:
            return '%s%d.%s' % (self.ident, self.rounds, salt)

    def calc_checksum(self, secret):
        #TODO: find out what grub's policy is re: unicode
        if isinstance(secret, unicode):
            secret = secret.encode("utf-8")
        return pbkdf2(secret, self.salt, self.rounds, 64, "hmac-sha512")

#=========================================================
#eof
#=========================================================
