import pytest
from scriptcollection.main import get_scriptcollection_version


def test_version():
    scriptcollection_version = get_scriptcollection_version()
    assert "0.1.1" == scriptcollection_version
