import random

import numpy as np
import pytest

from earthlib import sensors
from earthlib.errors import SensorError

sensor = "Sentinel2"
band = "B8"
band_description = "near infrared"
dtype = "vegetation"
random_str = "{num:06d}.xyz".format(num=random.randint(int(1e6), int(1e7) - 1))


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


def test_get_band_indices_preserves_requested_order():
    ordered = sensors.get_band_indices(["SR_B7", "SR_B2"], "Landsat8")
    assert ordered == [5, 0]


def test_get_band_indices_rejects_unknown_band():
    with pytest.raises(SensorError):
        sensors.get_band_indices([band, random_str], sensor)

    with pytest.raises(SensorError):
        sensors.get_band_indices(random_str, sensor)


def test_get_band_indices_rejects_sensor_without_named_bands():
    unnamed = sensors.Sensor(name="Unnamed", band_centers=[450, 550])
    sensors.supported_sensors["Unnamed"] = unnamed
    try:
        with pytest.raises(SensorError):
            sensors.get_band_indices(["B1"], "Unnamed")
    finally:
        del sensors.supported_sensors["Unnamed"]


def test_get_sensor_returns_a_copy():
    """Mutating a returned sensor must not poison the module-level singleton."""
    s = sensors.get_sensor("Landsat8")
    s.band_centers = s.band_centers * 1000.0
    assert not np.allclose(s.band_centers, sensors.Landsat8.band_centers)


def test_all_defined_sensors_are_registered():
    """Every module-level Sensor must be reachable through supported_sensors."""
    defined = {
        name
        for name, value in vars(sensors).items()
        if isinstance(value, sensors.Sensor)
    }
    missing = defined - set(sensors.supported_sensors)
    assert not missing, f"Sensors defined but not registered: {sorted(missing)}"


def test_registered_sensors_match_their_keys():
    for key, instance in sensors.supported_sensors.items():
        assert key == instance.name


@pytest.mark.parametrize("name", sorted(sensors.supported_sensors))
def test_sensor_band_lengths_are_consistent(name):
    s = sensors.supported_sensors[name]
    assert s.band_count == len(s.band_centers)

    for attribute in ("band_widths", "band_names", "band_descriptions"):
        values = getattr(s, attribute)
        if values is not None:
            assert len(values) == s.band_count, f"{name}.{attribute} length mismatch"


@pytest.mark.parametrize("name", ["Pelican", "Pelican2"])
def test_pelican_sensors_are_registered(name):
    assert name in sensors.list_sensors()
    assert sensors.get_sensor(name).name == name


def test_get_band_descriptions():
    descriptions = sensors.get_band_descriptions(sensor)
    assert band_description in descriptions
