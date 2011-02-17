"""passlib.drivers.postgres_md5 - MD5-based algorithm used by Postgres for pg_shadow table"""
#=========================================================
#imports
#=========================================================
#core
from hashlib import md5
import re
import logging; log = logging.getLogger(__name__)
from warnings import warn
#site
#libs
#pkg
from passlib.utils import autodocument
#local
__all__ = [
    "postgres_md5",
]

#=========================================================
#
#=========================================================
class postgres_plaintext(object):
    "fake password hash which recognizes ALL hashes, and assumes they encode the password in plain-text"
    name = "postgres_plaintext"

    setting_kwds = ()
    context_kwds = ("user",)

    @classmethod
    def genconfig(cls):
        return None

    @classmethod
    def genhash(cls, secret, config, user):
        return secret

    @classmethod
    def identify(cls, hash):
        return bool(hash)

    @classmethod
    def encrypt(cls, secret, config, user):
        return secret

    @classmethod
    def verify(cls, secret, hash, user):
        return secret == hash

#=========================================================
#handler
#=========================================================
class postgres_md5(object):
    #=========================================================
    #algorithm information
    #=========================================================
    name = "postgres_md5"
    setting_kwds = ()
    context_kwds = ("user",)

    #=========================================================
    #formatting
    #=========================================================
    _pat = re.compile(r"^md5[0-9a-f]{32}$")

    @classmethod
    def identify(cls, hash):
        return bool(hash and cls._pat.match(hash))

    #=========================================================
    #primary interface
    #=========================================================
    @classmethod
    def genconfig(cls):
        return None

    @classmethod
    def genhash(cls, secret, config, user):
        if config and not cls.identify(config):
            raise ValueError, "not a postgres-md5 hash"
        return cls.encrypt(secret, user)

    #=========================================================
    #secondary interface
    #=========================================================
    @classmethod
    def encrypt(cls, secret, user):
        #FIXME: not sure what postgres' policy is for unicode
        if not user:
            raise ValueError, "user keyword must be specified for this algorithm"
        if isinstance(secret, unicode):
            secret = secret.encode("utf-8")
        if isinstance(user, unicode):
            user = user.encode("utf-8")
        return "md5" + md5(secret + user).hexdigest().lower()

    @classmethod
    def verify(cls, secret, hash, user):
        if not hash:
            raise ValueError, "no hash specified"
        return hash == cls.genhash(secret, hash, user)

    #=========================================================
    #eoc
    #=========================================================

autodocument(postgres_md5, context_doc="""\
:param user: string containing name of postgres user account this password is associated with.
""")
#=========================================================
#eof
#=========================================================
