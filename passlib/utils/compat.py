"""passlib.utils.compat - python 2/3 compatibility helpers"""
#=============================================================================
# figure out what version we're running
#=============================================================================
import sys
PY2 = sys.version_info < (3,0)
PY3 = sys.version_info >= (3,0)
PY_MAX_25 = sys.version_info < (2,6) # py 2.5 or earlier
PY27 = sys.version_info[:2] == (2,7) # supports last 2.x release
PY_MIN_32 = sys.version_info >= (3,2) # py 3.2 or later

#=============================================================================
# common imports
#=============================================================================
import logging; log = logging.getLogger(__name__)
if PY3:
    import builtins
else:
    import __builtin__ as builtins


def _add_doc(obj, doc):
    """add docstring to an object"""
    obj.__doc__ = doc

#=============================================================================
# the default exported vars
#=============================================================================
__all__ = [
    # python versions
    'PY2', 'PY3', 'PY_MAX_25', 'PY27', 'PY_MIN_32',

    # io
    'BytesIO', 'StringIO', 'SafeConfigParser',
    'print_',

    # type detection
    'is_mapping',
    'callable',
    'int_types',
    'num_types',

    # unicode/bytes types & helpers
    'u', 'b',
    'unicode', 'bytes', 'sb_types',
    'uascii_to_str', 'bascii_to_str',
    'str_to_uascii', 'str_to_bascii',
    'ujoin', 'bjoin', 'bjoin_ints', 'bjoin_elems', 'belem_ord',

    # iteration helpers
    'irange', 'trange', #'lrange',
    'imap', 'lmap',
    'iteritems', 'itervalues',

    # introspection
    'exc_err', 'get_method_function', '_add_doc',
]

#=============================================================================
# lazy-loaded aliases (see LazyOverlayModule at bottom)
#=============================================================================
if PY3:
    _lazy_attrs = dict(
        BytesIO="io.BytesIO",
        StringIO="io.StringIO",
        SafeConfigParser="configparser.SafeConfigParser",
    )
    if PY_MIN_32:
        # py32 renamed this, removing old ConfigParser
        _lazy_attrs["SafeConfigParser"] = "configparser.ConfigParser"
else:
    _lazy_attrs = dict(
        BytesIO="cStringIO.StringIO",
        StringIO="StringIO.StringIO",
        SafeConfigParser="ConfigParser.SafeConfigParser",
    )

#=============================================================================
# typing
#=============================================================================
def is_mapping(obj):
    # non-exhaustive check, enough to distinguish from lists, etc
    return hasattr(obj, "items")

if (3,0) <= sys.version_info < (3,2):
    # callable isn't dead, it's just resting
    from collections import Callable
    def callable(obj):
        return isinstance(obj, Callable)
else:
    callable = builtins.callable

if PY3:
    int_types = (int,)
    num_types = (int, float)
else:
    int_types = (int, long)
    num_types = (int, long, float)

#=============================================================================
# unicode & bytes types
#=============================================================================
if PY3:
    unicode = str
    bytes = builtins.bytes
#    string_types = (unicode,)

    def u(s):
        assert isinstance(s, str)
        return s

    def b(s):
        assert isinstance(s, str)
        return s.encode("latin-1")

else:
    unicode = builtins.unicode
    bytes = str if PY_MAX_25 else builtins.bytes
#    string_types = (unicode, bytes)

    def u(s):
        assert isinstance(s, str)
        return s.decode("unicode_escape")

    def b(s):
        assert isinstance(s, str)
        return s

sb_types = (unicode, bytes)

#=============================================================================
# unicode & bytes helpers
#=============================================================================
# function to join list of unicode strings
ujoin = u('').join

# function to join list of byte strings
bjoin = b('').join

if PY3:
    def uascii_to_str(s):
        assert isinstance(s, unicode)
        return s

    def bascii_to_str(s):
        assert isinstance(s, bytes)
        return s.decode("ascii")

    def str_to_uascii(s):
        assert isinstance(s, str)
        return s

    def str_to_bascii(s):
        assert isinstance(s, str)
        return s.encode("ascii")

    bjoin_ints = bjoin_elems = bytes

    def belem_ord(elem):
        return elem

    def biter_ints(s):
        assert isinstance(s, bytes)
        return s

else:
    def uascii_to_str(s):
        assert isinstance(s, unicode)
        return s.encode("ascii")

    def bascii_to_str(s):
        assert isinstance(s, bytes)
        return s

    def str_to_uascii(s):
        assert isinstance(s, str)
        return s.decode("ascii")

    def str_to_bascii(s):
        assert isinstance(s, str)
        return s

    def bjoin_ints(values):
        return bjoin(chr(v) for v in values)

    bjoin_elems = bjoin

    belem_ord = ord

    def biter_ints(s):
        assert isinstance(s, bytes)
        return (ord(c) for c in s)

_add_doc(uascii_to_str, "helper to convert ascii unicode -> native str")
_add_doc(bascii_to_str, "helper to convert ascii bytes -> native str")
_add_doc(str_to_uascii, "helper to convert ascii native str -> unicode")
_add_doc(str_to_bascii, "helper to convert ascii native str -> bytes")

# bjoin_ints -- function to convert list of ordinal integers to byte string.

# bjoin_elems --  function to convert list of byte elements to byte string;
#                 i.e. what's returned by ``b('a')[0]``...
#                 this is b('a') under PY2, but 97 under PY3.

# belem_ord -- function to convert byte element to integer -- a noop under PY3

_add_doc(biter_ints, "helper to iterate over byte values in byte string")

#=============================================================================
# iteration helpers
#
# irange - range iterator
# trange - immutable range sequence (list under py2, range object under py3)
# lrange - range list
#
# lmap - map to list
#=============================================================================
if PY3:
    irange = trange = range
    ##def lrange(*a,**k):
    ##    return list(range(*a,**k))

    def lmap(*a, **k):
        return list(map(*a,**k))
    imap = map

else:
    irange = xrange
    trange = range
    ##lrange = range

    lmap = map
    from itertools import imap

if PY3:
    def iteritems(d):
        return d.items()
    def itervalues(d):
        return d.values()
else:
    def iteritems(d):
        return d.iteritems()
    def itervalues(d):
        return d.itervalues()

if PY_MAX_25:
    def next(itr):
        "compat wrapper for next()"
        # NOTE: omits support for 'default' arg
        return itr.next()
else:
    next = builtins.next

#=============================================================================
# introspection
#=============================================================================
def exc_err():
    "return current error object (to avoid try/except syntax change)"
    return sys.exc_info()[1]

if PY3:
    def get_method_function(method):
        return method.__func__
else:
    def get_method_function(method):
        return method.im_func

#=============================================================================
# input/output
#=============================================================================
if PY3:
    print_ = getattr(builtins, "print")
else:
    def print_(*args, **kwds):
        """The new-style print function."""
        # extract kwd args
        fp = kwds.pop("file", sys.stdout)
        sep = kwds.pop("sep", None)
        end = kwds.pop("end", None)
        if kwds:
            raise TypeError("invalid keyword arguments")

        # short-circuit if no target
        if fp is None:
            return

        # use unicode or bytes ?
        want_unicode = isinstance(sep, unicode) or isinstance(end, unicode) or \
                       any(isinstance(arg, unicode) for arg in args)

        # pick default end sequence
        if end is None:
            end = u("\n") if want_unicode else "\n"
        elif not isinstance(end, sb_types):
            raise TypeError("end must be None or a string")

        # pick default separator
        if sep is None:
            sep = u(" ") if want_unicode else " "
        elif not isinstance(sep, sb_types):
            raise TypeError("sep must be None or a string")

        # write to buffer
        first = True
        write = fp.write
        for arg in args:
            if first:
                first = False
            else:
                write(sep)
            if not isinstance(arg, basestring):
                arg = str(arg)
            write(arg)
        write(end)

#=============================================================================
# lazy overlay module
#=============================================================================
from types import ModuleType

def import_object(source):
    "helper to import object from module; accept format `path.to.object`"
    modname, modattr = source.rsplit(".",1)
    mod = __import__(modname, fromlist=[modattr], level=0)
    return getattr(mod, modattr)

class LazyOverlayModule(ModuleType):
    """proxy module which overlays original module,
    and lazily imports specified attributes.

    this is mainly used to prevent importing of resources
    that are only needed by certain password hashes,
    yet allow them to be imported from a single location.

    used by :mod:`passlib.utils`, :mod:`passlib.utils.crypto`,
    and :mod:`passlib.utils.compat`.
    """

    @classmethod
    def replace_module(cls, name, attrmap):
        orig = sys.modules[name]
        self = cls(name, attrmap, orig)
        sys.modules[name] = self
        return self

    def __init__(self, name, attrmap, proxy=None):
        ModuleType.__init__(self, name)
        self.__attrmap = attrmap
        self.__proxy = proxy
        self.__log = logging.getLogger(name)

    def __getattr__(self, attr):
        proxy = self.__proxy
        if proxy and hasattr(proxy, attr):
            return getattr(proxy, attr)
        attrmap = self.__attrmap
        if attr in attrmap:
            source = attrmap[attr]
            if callable(source):
                value = source()
            else:
                value = import_object(source)
            setattr(self, attr, value)
            self.__log.debug("loaded lazy attr %r: %r", attr, value)
            return value
        raise AttributeError("'module' object has no attribute '%s'" % (attr,))

    def __repr__(self):
        proxy = self.__proxy
        if proxy:
            return repr(proxy)
        else:
            return ModuleType.__repr__(self)

    def __dir__(self):
        attrs = set(dir(self.__class__))
        attrs.update(self.__dict__)
        attrs.update(self.__attrmap)
        proxy = self.__proxy
        if proxy:
            attrs.update(dir(proxy))
        return list(attrs)

# replace this module with overlay that will lazily import attributes.
LazyOverlayModule.replace_module(__name__, _lazy_attrs)

#=============================================================================
# eof
#=============================================================================
