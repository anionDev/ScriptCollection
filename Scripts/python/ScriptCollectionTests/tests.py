import pytest
from ScriptCollectionUtilities.main import get_scriptcollection_version


def test_version():
    assert "0.2.0" == get_scriptcollection_version()
