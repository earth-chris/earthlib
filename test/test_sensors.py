from earthlib import sensors


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
