from pydoover.docker import run_app

from .application import Acq580Application
from .app_config import Acq580Config

def main():
    """
    Run the application.
    """
    run_app(Acq580Application(config=Acq580Config()))
