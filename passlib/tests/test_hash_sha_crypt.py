"""tests for passlib.pwhash -- (c) Assurance Technologies 2003-2009"""
#=========================================================
#imports
#=========================================================
from __future__ import with_statement
#core
import hashlib
from logging import getLogger
import re
try:
    from warnings import catch_warnings
except ImportError: #wasn't added until py26
    catch_warnings = None
import warnings
#site
#pkg
from passlib.tests.utils import TestCase, enable_option
from passlib.tests.handler_utils import _HandlerTestCase
import passlib.hash.sha256_crypt as mod2
import passlib.hash.sha512_crypt as mod5
#module
log = getLogger(__name__)

#=========================================================
#test sha256-crypt
#=========================================================
class Sha256CryptTest(_HandlerTestCase):
    handler = mod2
    known_correct = (
        ('', '$5$rounds=10428$uy/jIAhCetNCTtb0$YWvUOXbkqlqhyoPMpN8BMe.ZGsGx2aBvxTvDFI613c3'),
        (' ', '$5$rounds=10376$I5lNtXtRmf.OoMd8$Ko3AI1VvTANdyKhBPavaRjJzNpSatKU6QVN9uwS9MH.'),
        ('test', '$5$rounds=11858$WH1ABM5sKhxbkgCK$aTQsjPkz0rBsH3lQlJxw9HDTDXPKBxC0LlVeV69P.t1'),
        ('Compl3X AlphaNu3meric', '$5$rounds=10350$o.pwkySLCzwTdmQX$nCMVsnF3TXWcBPOympBUUSQi6LGGloZoOsVJMGJ09UB'),
        ('4lpHa N|_|M3r1K W/ Cur5Es: #$%(*)(*%#', '$5$rounds=11944$9dhlu07dQMRWvTId$LyUI5VWkGFwASlzntk1RLurxX54LUhgAcJZIt0pYGT7'),
        (u'with unic\u00D6de', '$5$rounds=1000$IbG0EuGQXw5EkMdP$LQ5AfPf13KufFsKtmazqnzSGZ4pxtUNw3woQ.ELRDF4'),
        )
    known_invalid = (
        #bad char in otherwise correct hash
        '$5$rounds=10428$uy/:jIAhCetNCTtb0$YWvUOXbkqlqhyoPMpN8BMeZGsGx2aBvxTvDFI613c3'

        #zero-padded rounds
       '$5$rounds=010428$uy/jIAhCetNCTtb0$YWvUOXbkqlqhyoPMpN8BMe.ZGsGx2aBvxTvDFI613c3',
    )

if mod2.backend != "builtin" and enable_option("all-backends"):

    #monkeypatch sha256-crypt mod so it uses builtin backend

    class BuiltinSha256CryptTest(Sha256CryptTest):
        case_prefix = "sha256-crypt (builtin backend)"

        def setUp(self):
            self.tmp = mod2.crypt
            mod2.crypt = None

        def cleanUp(self):
            mod2.crypt = self.tmp

#=========================================================
#test sha512-crypt
#=========================================================
class Sha512CryptTest(_HandlerTestCase):
    handler = mod5
    known_correct = (
        ('', '$6$rounds=11021$KsvQipYPWpr93wWP$v7xjI4X6vyVptJjB1Y02vZC5SaSijBkGmq1uJhPr3cvqvvkd42Xvo48yLVPFt8dvhCsnlUgpX.//Cxn91H4qy1'),
        (' ', '$6$rounds=11104$ED9SA4qGmd57Fq2m$q/.PqACDM/JpAHKmr86nkPzzuR5.YpYa8ZJJvI8Zd89ZPUYTJExsFEIuTYbM7gAGcQtTkCEhBKmp1S1QZwaXx0'),
        ('test', '$6$rounds=11531$G/gkPn17kHYo0gTF$Kq.uZBHlSBXyzsOJXtxJruOOH4yc0Is13uY7yK0PvAvXxbvc1w8DO1RzREMhKsc82K/Jh8OquV8FZUlreYPJk1'),
        ('Compl3X AlphaNu3meric', '$6$rounds=10787$wakX8nGKEzgJ4Scy$X78uqaX1wYXcSCtS4BVYw2trWkvpa8p7lkAtS9O/6045fK4UB2/Jia0Uy/KzCpODlfVxVNZzCCoV9s2hoLfDs/'),
        ('4lpHa N|_|M3r1K W/ Cur5Es: #$%(*)(*%#', '$6$rounds=11065$5KXQoE1bztkY5IZr$Jf6krQSUKKOlKca4hSW07MSerFFzVIZt/N3rOTsUgKqp7cUdHrwV8MoIVNCk9q9WL3ZRMsdbwNXpVk0gVxKtz1'),
        )
    known_invalid = (
        #bad char in otherwise correct hash
        '$6$rounds=11021$KsvQipYPWpr9:wWP$v7xjI4X6vyVptJjB1Y02vZC5SaSijBkGmq1uJhPr3cvqvvkd42Xvo48yLVPFt8dvhCsnlUgpX.//Cxn91H4qy1',

        #zero-padded rounds
        '$6$rounds=011021$KsvQipYPWpr93wWP$v7xjI4X6vyVptJjB1Y02vZC5SaSijBkGmq1uJhPr3cvqvvkd42Xvo48yLVPFt8dvhCsnlUgpX.//Cxn91H4qy1',
    )

    #NOTE: these test cases taken from spec definition at http://www.akkadia.org/drepper/SHA-crypt.txt
    cases512 = [
        #salt-hash, secret, result
        ("$6$saltstring", "Hello world!",
        "$6$saltstring$svn8UoSVapNtMuq1ukKS4tPQd8iKwSMHWjl/O817G3uBnIFNjnQJu"
        "esI68u4OTLiBFdcbYEdFCoEOfaS35inz1" ),

      ( "$6$rounds=10000$saltstringsaltstring", "Hello world!",
        "$6$rounds=10000$saltstringsaltst$OW1/O6BYHV6BcXZu8QVeXbDWra3Oeqh0sb"
        "HbbMCVNSnCM/UrjmM0Dp8vOuZeHBy/YTBmSK6H9qs/y3RnOaw5v." ),

      ( "$6$rounds=5000$toolongsaltstring", "This is just a test",
        "$6$rounds=5000$toolongsaltstrin$lQ8jolhgVRVhY4b5pZKaysCLi0QBxGoNeKQ"
        "zQ3glMhwllF7oGDZxUhx1yxdYcz/e1JSbq3y6JMxxl8audkUEm0" ),

      ( "$6$rounds=1400$anotherlongsaltstring",
        "a very much longer text to encrypt.  This one even stretches over more"
        "than one line.",
        "$6$rounds=1400$anotherlongsalts$POfYwTEok97VWcjxIiSOjiykti.o/pQs.wP"
        "vMxQ6Fm7I6IoYN3CmLs66x9t0oSwbtEW7o7UmJEiDwGqd8p4ur1" ),

      ( "$6$rounds=77777$short",
        "we have a short salt string but not a short password",
        "$6$rounds=77777$short$WuQyW2YR.hBNpjjRhpYD/ifIw05xdfeEyQoMxIXbkvr0g"
        "ge1a1x3yRULJ5CCaUeOxFmtlcGZelFl5CxtgfiAc0" ),

      ( "$6$rounds=123456$asaltof16chars..", "a short string",
        "$6$rounds=123456$asaltof16chars..$BtCwjqMJGx5hrJhZywWvt0RLE8uZ4oPwc"
        "elCjmw2kSYu.Ec6ycULevoBK25fs2xXgMNrCzIMVcgEJAstJeonj1" ),

      ( "$6$rounds=10$roundstoolow", "the minimum number is still observed",
        "$6$rounds=1000$roundstoolow$kUMsbe306n21p9R.FRkW3IGn.S9NPN0x50YhH1x"
        "hLsPuWGsUSklZt58jaTfF4ZEQpyUNGc0dqbpBYYBaHHrsX." ),
    ]

    def test_spec_vectors(self):
        "verify sha512-crypt passes specification test vectors"
        handler = mod5

        #NOTE: the 'roundstoolow' vector is known to raise a warning, which we silence here
        if catch_warnings:
            ctx = catch_warnings()
            ctx.__enter__()
        warnings.filterwarnings("ignore", "sha512-crypt algorithm does not allow less than 1000 rounds: 10")

        for config, secret, hash in self.cases512:

            result = handler.genhash(secret, config)

            #parse config
            settings = handler.parse(config)

            #make sure we got expected result back
            self.assertEqual(result, hash, "hash=%r secret=%r:" % (hash, secret))

            #parse result and check that salt was truncated to max 16 chars
            info = handler.parse(result)
            if len(settings['salt']) > 16:
                #spec sez we can truncate salt
                self.assertEqual(info['salt'], settings['salt'][:16], "hash=%r secret=%r:" % (hash, secret))
            else:
                self.assertEqual(info['salt'], settings['salt'], "hash=%r secret=%r:" % (hash, secret))

        if catch_warnings:
            ctx.__exit__(None,None,None)

if mod5.backend != "builtin" and enable_option("all-backends"):

    #monkeypatch sha512-crypt mod so it uses builtin backend

    class BuiltinSha512CryptTest(Sha512CryptTest):
        case_prefix = "sha512-crypt (builtin backend)"

        def setUp(self):
            self.tmp = mod5.crypt
            mod5.crypt = None

        def cleanUp(self):
            mod5.crypt = self.tmp
#=========================================================
#EOF
#=========================================================
