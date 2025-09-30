import os
import random
from tempfile import NamedTemporaryFile

import numpy as np
import pytest

from earthlib import endmembers, sensors
from earthlib.errors import EndmemberError

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir, "data")
jfsp_path = os.path.join(data_dir, "jfsp_graysoil.txt")

dtype = "vegetation"
random_str = "{num:06d}.xyz".format(num=random.randint(1e6, 1e7 - 1))


def find_nearest(band_centers, wavelength, spectrum):
    idx = (np.abs(band_centers - wavelength)).argmin()
    return spectrum[idx]


def test_Spectra():
    n_spectra = 5
    sensor = sensors.ASD
    band_count = sensor.band_count
    data = np.ones((n_spectra, band_count))
    s = endmembers.Spectra(data=data, sensor=sensor)
    assert len(s) == n_spectra
    assert max(s.sensor.band_centers <= 2500)
    assert min(s.sensor.band_centers >= 350)

    # test water band removal
    s.remove_water_bands(set_nan=False)

    # 1400 nm should be masked, 1300 nm is ok
    spectrum = s.data[0]
    val_1400 = find_nearest(s.sensor.band_centers, 1400, spectrum)
    val_1000 = find_nearest(s.sensor.band_centers, 1000, spectrum)
    assert val_1400 == 0
    assert val_1000 != 0

    # test it works in micrometers
    s.data[:] = 1
    s.to_micrometers()
    s.remove_water_bands(set_nan=False)
    spectrum = s.data[0]
    val_1400 = find_nearest(s.sensor.band_centers, 1.4, spectrum)
    val_1000 = find_nearest(s.sensor.band_centers, 1.0, spectrum)
    assert val_1400 == 0
    assert val_1000 != 0

    # convert back to nanometers
    s.to_nanometers()
    assert s.sensor.wavelength_unit == "nanometers"
    assert max(s.sensor.band_centers <= 2500)
    assert min(s.sensor.band_centers >= 350)

    # nan test for water band removal
    s = endmembers.Spectra(data=data, sensor=sensor)
    s.remove_water_bands(set_nan=True)
    assert np.isnan(s.data).any()

    # test shortwave band range retrieval
    shortwave_bands = s.shortwave_band_idxs()
    assert min(s.sensor.band_centers[shortwave_bands]) >= 350
    assert max(s.sensor.band_centers[shortwave_bands]) <= 2500

    # test brightness normlization
    s.brightness_normalize()

    # test on a subset of bands
    s = endmembers.Spectra(data=data, sensor=sensor)
    s.brightness_normalize(inds=np.arange(10))

    # test band resampling
    for target_sensor in sensors.supported_sensors.values():
        s = endmembers.Spectra(data=data, sensor=sensor)
        t = s.to_sensor(target_sensor)
        assert t.data.shape[1] == target_sensor.band_count

    # test subsampling
    # s = endmembers.Spectra(data=data, sensor=sensor)
    n_samples = 3
    s_sub = endmembers.library.subsample(n_samples)
    assert len(s_sub) == n_samples

    # subsample by type
    types = endmembers.listTypes(level=2)
    for t in types:
        s_sub = endmembers.library.subsample(n_samples, by_type=t)
        assert len(s_sub) == n_samples
        assert (s_sub.metadata["LEVEL_2"] == t).all()

    # test subsampling with invalid type
    with pytest.raises(EndmemberError):
        endmembers.library.subsample(n_samples, by_type="InvalidType")

    # test output path formatting
    sli, hdr = s.format_output_paths("tmp.sli")
    assert sli.endswith(".sli")
    assert hdr.endswith(".hdr")

    sli, hdr = s.format_output_paths("tmp")
    assert sli.endswith(".sli")
    assert hdr.endswith(".hdr")

    sli, hdr = s.format_output_paths("tmp.hdr")
    assert sli.endswith(".sli")
    assert hdr.endswith(".hdr")


def test_write_read_sli():
    n_spectra = 5
    sensor = sensors.Earthlib
    band_count = sensor.band_count
    data = np.ones((n_spectra, band_count))
    s = endmembers.Spectra(data=data, sensor=sensor)

    # set all to a uniform value
    all_values = 2
    s.data[:] = all_values

    # write the output file
    with NamedTemporaryFile(suffix=".sli", delete=True) as tmp:
        out_file = tmp.name
        s.to_sli(out_file)

        # read it back in
        s2 = endmembers.Spectra.from_sli(out_file)

        # check that the values are the same
        assert np.array_equal(s.sensor.band_centers, s2.sensor.band_centers)
        assert np.array_equal(s.data, s2.data)
        assert np.array_equal(s.names, s2.names)
        assert s.data.shape == s2.data.shape
        assert s.data.shape[0] == n_spectra
        assert (s.data == all_values).all()
        assert (s2.data == all_values).all()


def test_listTypes():
    types = endmembers.listTypes()
    assert dtype in types
    assert random_str not in types


def test_getTypeLevel():
    valid_level = endmembers.getTypeLevel(dtype)
    assert valid_level == 2

    invalid_level = endmembers.getTypeLevel(random_str)
    assert invalid_level == 0
