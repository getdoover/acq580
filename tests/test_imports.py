"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from acq580.application import Acq580Application
    assert Acq580Application

def test_config():
    from acq580.app_config import Acq580Config

    config = Acq580Config()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from acq580.app_ui import Acq580UI
    assert Acq580UI

def test_state():
    from acq580.app_state import Acq580State
    assert Acq580State