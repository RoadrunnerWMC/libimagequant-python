import libimagequant as liq
import pytest

import utils


def test_version_info():
    """
    Test that the library version constants exist and seem sane
    """
    assert isinstance(liq.LIQ_VERSION, int)
    assert isinstance(liq.LIQ_VERSION_STRING, str)
    assert isinstance(liq.BINDINGS_VERSION, int)
    assert isinstance(liq.BINDINGS_VERSION_STRING, str)

    # Check that the version strings match the version ints

    def version_int_to_string(value):
        parts = []
        while value:
            parts.insert(0, str(value % 100))
            value //= 100
        return '.'.join(parts)

    assert liq.LIQ_VERSION_STRING == version_int_to_string(liq.LIQ_VERSION)
    assert liq.BINDINGS_VERSION_STRING == version_int_to_string(liq.BINDINGS_VERSION)
