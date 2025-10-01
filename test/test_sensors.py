import random

import pytest

from earthlib import sensors
from earthlib.errors import SensorError

sensor = "Sentinel2"
band = "B8"
band_description = "near infrared"
dtype = "vegetation"
random_str = "{num:06d}.xyz".format(num=random.randint(1e6, 1e7 - 1))


def test_Sensor():
    s = sensors.Sensor(
        name="TestSensor",
        collection="TestCollection",
        band_names=["B1", "B2", "B3"],
        band_centers=[450, 550, 650],
        band_widths=[20, 20, 20],
        wavelength_unit="nanometers",
        measurement_unit="reflectance",
    )
    assert s.name == "TestSensor"
    assert s.collection == "TestCollection"
    assert len(s.band_names) == 3
    assert s.band_centers[0] == 450
    assert s.band_widths[1] == 20
    assert s.wavelength_unit == "nanometers"
    assert s.measurement_unit == "reflectance"


def test_list_sensors():
    sensor_list = sensors.list_sensors()
    assert sensor in sensor_list
    assert random_str not in sensor_list


def test_validate_sensor():
    with pytest.raises(SensorError):
        sensors.validate_sensor(random_str)


def test_get_collection_name():
    assert "COPERNICUS" in sensors.get_collection_name(sensor)


def test_get_scaler():
    assert sensors.get_scaler(sensor) == 0.0001


def test_get_bands():
    assert band in sensors.get_bands(sensor)


def test_get_band_indices():
    assert 6 in sensors.get_band_indices([band], sensor)
    assert 6 in sensors.get_band_indices(band, sensor)


def test_get_band_descriptions():
    descriptions = sensors.get_band_descriptions(sensor)
    print(descriptions)
    assert band_description in descriptions
