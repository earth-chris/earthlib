from importlib.metadata import version as _version

from earthlib import metadata, read, sensors
from earthlib.endmembers import Spectra, library
from earthlib.sensors import Sensor, supported_sensors

try:
    from earthlib.geelib import (
        BRDFCorrect,
        BrightMask,
        BurnPVSoil,
        CloudMask,
        NIRv,
        Scale,
        ShadeMask,
        SoilPVNPV,
        Unmix,
        VegImperviousSoil,
    )
    from earthlib.geelib.utils import getCollection
except ImportError:
    pass

__version__ = _version("earthlib")
