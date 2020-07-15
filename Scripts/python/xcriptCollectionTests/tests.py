import pytest
from ScriptCollection.core import get_scriptcollection_version


def test_version():
    assert get_scriptcollection_version().startswith("1.0.")#TODO
