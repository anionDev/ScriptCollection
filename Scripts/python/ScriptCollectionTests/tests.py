import pytest
from ScriptCollection.core import get_scriptcollection_version


def test_version():
    assert "1.0.2" == get_scriptcollection_version()