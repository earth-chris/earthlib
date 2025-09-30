import random

import pytest

from earthlib import utils
from earthlib.errors import SensorError

sensor = "Sentinel2"
band = "B8"
band_description = "near infrared"
dtype = "vegetation"
random_str = "{num:06d}.xyz".format(num=random.randint(1e6, 1e7 - 1))


def test_listSensors():
    sensors = utils.listSensors()
    assert sensor in sensors
    assert random_str not in sensors


def test_validateSensor():
    with pytest.raises(SensorError):
        utils.validateSensor(random_str)


def test_getCollectionName():
    assert "COPERNICUS" in utils.getCollectionName(sensor)


def test_getScaler():
    assert utils.getScaler(sensor) == 0.0001


def test_getBands():
    assert band in utils.getBands(sensor)


def test_getBandIndices():
    assert 6 in utils.getBandIndices([band], sensor)
    assert 6 in utils.getBandIndices(band, sensor)


def test_getBandDescriptions():
    descriptions = utils.getBandDescriptions(sensor)
    print(descriptions)
    assert band_description in descriptions
