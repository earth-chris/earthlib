"""A global spectral library with tools for satellite land cover mapping."""

from importlib.metadata import version as _version

from earthlib import endmembers, metadata, read, sensors
from earthlib.endmembers import (
    Spectra,
    full_library,
    get_type_level,
    library,
    list_types,
)
from earthlib.sensors import Sensor, list_sensors, supported_sensors

__version__ = _version("earthlib")

__all__ = [
    "Sensor",
    "Spectra",
    "endmembers",
    "full_library",
    "get_type_level",
    "library",
    "list_sensors",
    "list_types",
    "metadata",
    "read",
    "sensors",
    "supported_sensors",
]
