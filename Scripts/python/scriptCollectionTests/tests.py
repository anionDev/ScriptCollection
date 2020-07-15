import pytest
from scriptCollection.core import get_scriptCollection_version


def test_version():
    assert get_scriptCollection_version().startswith("1.0.")#TODO
