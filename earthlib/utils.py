"""Utility functions for working with spectral libraries."""

import numpy as np
import spectral

from earthlib.config import endmember_path, metadata
from earthlib.errors import EndmemberError, SensorError
from earthlib.read import spectral_library
from earthlib.sensors import supported_sensors


def listSensors() -> list:
    """Returns a list of the supported sensor image collections.

    Returns:
        sensors: a list of supported sensors using the names referenced by this package.
    """
    sensors = list(supported_sensors.keys())
    return sensors


def validateSensor(sensor: str) -> None:
    """Verify a string sensor ID is valid, raise an error otherwise.

    Args:
        sensor: the name of the sensor (from earthlib.listSensors()).

    Raises:
        SensorError: when an invalid sensor name is passed
    """
    supported = listSensors()
    if sensor not in supported:
        raise SensorError(
            f"Invalid sensor: {sensor}. Supported: {', '.join(supported)}"
        )


def getCollectionName(sensor: str) -> str:
    """Returns the earth engine collection name for a specific satellite sensor.

    Args:
        sensor: the name of the sensor (from earthlib.listSensors()).

    Returns:
        collection: a string with the earth engine collection.
    """
    validateSensor(sensor)
    collection = supported_sensors[sensor].collection
    return collection


def getScaler(sensor: str) -> str:
    """Returns the scaling factor to convert sensor data to percent reflectance (0-1).

    Args:
        sensor: the name of the sensor (from earthlib.listSensors()).

    Returns:
        scaler: the scale factor to multiply.
    """
    validateSensor(sensor)
    scaler = supported_sensors[sensor].scale
    return scaler


def getBands(sensor: str) -> list:
    """Returns a list of available band names by sensor.

    Args:
        sensor: the name of the sensor (from earthlib.listSensors()).

    Returns:
        bands: a list of sensor-specific band names.
    """
    validateSensor(sensor)
    bands = supported_sensors[sensor].band_names
    return bands


def getBandDescriptions(sensor: str) -> list:
    """Returns a list band name descriptions by sensor.

    Args:
        sensor: the name of the sensor (from earthlib.listSensors()).

    Returns:
        bands: a list of sensor-specific band names.
    """
    validateSensor(sensor)
    bands = supported_sensors[sensor].band_descriptions
    return bands


def getBandIndices(custom_bands: list, sensor: str) -> list:
    """Cross-references a list of bands passed as strings to the 0-based integer indices

    Args:
        custom_bands: a list of band names.
        sensor: a string sensor type for indexing the supported collections.

    Returns:
        indices: list of integer band indices.
    """
    validateSensor(sensor)
    sensor_bands = supported_sensors[sensor].band_names
    indices = list()

    if type(custom_bands) in (list, tuple):
        for band in custom_bands:
            if band in sensor_bands:
                indices.append(sensor_bands.index(band))

    elif isinstance(custom_bands, str):
        indices.append(sensor_bands.index(custom_bands))

    indices.sort()
    return indices
