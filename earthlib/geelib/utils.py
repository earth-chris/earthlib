"""Utility functions for working with earth engine."""

import ee

from earthlib.utils import getCollectionName


def getCollection(sensor: str) -> ee.ImageCollection:
    """Returns the default image collection for a satellite sensor.

    Args:
        sensor: the name of the sensor (from earthlib.listSensors()).

    Returns:
        that sensor's ee image collection.
    """
    return ee.ImageCollection(getCollectionName(sensor))
