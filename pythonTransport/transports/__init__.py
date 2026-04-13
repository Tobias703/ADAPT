"""
transports package

Import all bundled transports so their @register decorators execute.
This populates the global transport registry at startup.
"""

# Import each transport module here
from . import foobar  # noqa: F401