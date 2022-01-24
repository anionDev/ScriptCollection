import unittest
from ..Utilities import GeneralUtilities
from ..Core import ScriptCollectionCore

class CertificateUpdaterTests(unittest.TestCase):

    def test_dummy(self)->None:
        sc=ScriptCollectionCore()
        sc.register_mock_program_call("test","","",0,"","",0,0)
        GeneralUtilities.string_is_none_or_whitespace("")
        assert True is True
