"""ACQ580 VFD Application Package.

This package provides full monitoring and control of ABB ACQ580 variable
frequency drives via Modbus TCP communication.
"""

from pydoover.docker import run_app

from .application import Acq580Application
from .app_config import Acq580Config


def main():
    """Run the ACQ580 application."""
    run_app(Acq580Application(config=Acq580Config()))
