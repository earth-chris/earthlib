import os
import random
from tempfile import NamedTemporaryFile

import numpy as np
import pytest

from earthlib import endmembers, sensors
from earthlib.errors import EndmemberError

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir, "data")

dtype = "vegetation"
random_str = "{num:06d}.xyz".format(num=random.randint(int(1e6), int(1e7) - 1))


def find_nearest(band_centers, wavelength, spectrum):
    idx = (np.abs(band_centers - wavelength)).argmin()
    return spectrum[idx]


def asd_spectra(n_spectra=5):
    sensor = sensors.ASD
    data = np.ones((n_spectra, sensor.band_count))
    return endmembers.Spectra(data=data, sensor=sensor)


def test_init():
    n_spectra = 5
    s = asd_spectra(n_spectra)
    assert len(s) == n_spectra
    assert (s.sensor.band_centers <= 2500).all()
    assert (s.sensor.band_centers >= 350).all()
    assert len(s.names) == n_spectra


def test_init_defaults_to_zeros():
    s = endmembers.Spectra(data=None, sensor=sensors.ASD)
    assert s.data.shape == (1, sensors.ASD.band_count)
    assert (s.data == 0).all()


def test_remove_water_bands_zero():
    s = asd_spectra()
    s.remove_water_bands(set_nan=False)

    # 1400 nm should be masked, 1000 nm is ok
    spectrum = s.data[0]
    assert find_nearest(s.sensor.band_centers, 1400, spectrum) == 0
    assert find_nearest(s.sensor.band_centers, 1000, spectrum) != 0


def test_remove_water_bands_nan():
    s = asd_spectra()
    s.remove_water_bands(set_nan=True)
    assert np.isnan(s.data).any()


def test_remove_water_bands_in_micrometers():
    s = asd_spectra()
    s.to_micrometers()
    s.remove_water_bands(set_nan=False)

    spectrum = s.data[0]
    assert find_nearest(s.sensor.band_centers, 1.4, spectrum) == 0
    assert find_nearest(s.sensor.band_centers, 1.0, spectrum) != 0


def test_unit_conversion_round_trip():
    s = asd_spectra()
    centers = s.sensor.band_centers.copy()

    s.to_micrometers()
    assert s.sensor.wavelength_unit == "micrometers"
    assert (s.sensor.band_centers <= 2.5).all()

    s.to_nanometers()
    assert s.sensor.wavelength_unit == "nanometers"
    assert np.allclose(s.sensor.band_centers, centers)


def test_unit_conversion_scales_band_widths():
    sensor = sensors.get_sensor("Earthlib")
    s = endmembers.Spectra(data=None, sensor=sensor)
    widths = s.sensor.band_widths.copy()

    s.to_nanometers()
    assert np.allclose(s.sensor.band_widths, widths * 1000.0)


def test_unit_conversion_is_noop_when_already_converted():
    s = asd_spectra()
    centers = s.sensor.band_centers.copy()

    s.to_nanometers()
    assert np.allclose(s.sensor.band_centers, centers)


def test_shortwave_band_idxs():
    s = asd_spectra()
    shortwave_bands = s.shortwave_band_idxs()
    assert min(s.sensor.band_centers[shortwave_bands]) >= 350
    assert max(s.sensor.band_centers[shortwave_bands]) <= 2500


def test_brightness_normalize():
    s = asd_spectra()
    s.brightness_normalize()
    assert s.data.shape[1] == sensors.ASD.band_count


def test_brightness_normalize_band_subset():
    s = asd_spectra()
    s.brightness_normalize(inds=np.arange(10))
    assert s.data.shape[1] == 10
    assert len(s.sensor.band_centers) == 10


def test_brightness_normalize_rejects_out_of_range_indices():
    s = asd_spectra()
    band_count = s.data.shape[-1]

    # the highest valid index is band_count - 1, so band_count itself is invalid
    s.brightness_normalize(inds=[band_count])
    assert s.data.shape[1] == band_count


def test_brightness_normalize_rejects_negative_indices():
    s = asd_spectra()
    band_count = s.data.shape[-1]

    s.brightness_normalize(inds=[-1, 0])
    assert s.data.shape[1] == band_count


def test_to_sensor():
    for target_sensor in sensors.supported_sensors.values():
        s = asd_spectra()
        t = s.to_sensor(target_sensor)
        assert t.data.shape[1] == target_sensor.band_count


def test_to_sensor_leaves_source_unchanged():
    s = asd_spectra()
    band_count = s.sensor.band_count
    s.to_sensor(sensors.Landsat8)
    assert s.sensor.band_count == band_count


def test_getitem_int():
    s = endmembers.library[3]
    assert len(s) == 1
    assert len(s.names) == 1


def test_getitem_slice():
    s = endmembers.library[0:5]
    assert len(s) == 5
    assert s.names == endmembers.library.names[0:5]


def test_getitem_open_ended_slice():
    s = endmembers.library[:10]
    assert len(s) == 10


def test_getitem_integer_list():
    idxs = [100, 200, 300]
    s = endmembers.library[idxs]
    assert len(s) == 3
    assert s.names == [endmembers.library.names[i] for i in idxs]


def test_getitem_boolean_mask():
    mask = endmembers.library.metadata["LEVEL_2"] == "npv"
    s = endmembers.library[mask]
    assert len(s) == int(mask.sum())
    assert (s.metadata["LEVEL_2"] == "npv").all()


def test_getitem_boolean_mask_as_numpy_array():
    mask = (endmembers.library.metadata["LEVEL_2"] == "npv").to_numpy()
    s = endmembers.library[mask]
    assert len(s) == int(mask.sum())


def test_getitem_boolean_mask_as_plain_list():
    mask = [i < 4 for i in range(len(endmembers.library))]
    s = endmembers.library[mask]
    assert len(s) == 4
    assert s.names == endmembers.library.names[:4]


def test_getitem_integer_list_matching_length_is_not_a_mask():
    """An integer list as long as the library must not be read as a boolean mask."""
    n = len(endmembers.library)
    idxs = list(range(n))
    s = endmembers.library[idxs]
    assert len(s) == n


def test_getitem_rejects_mismatched_boolean_mask():
    mask = np.ones(len(endmembers.library) - 1, dtype=bool)
    with pytest.raises(IndexError):
        endmembers.library[mask]


def test_subsample():
    n_samples = 3
    s_sub = endmembers.library.subsample(n_samples)
    assert len(s_sub) == n_samples


def test_subsample_by_type():
    n_samples = 3
    for t in endmembers.list_types(level=2):
        s_sub = endmembers.library.subsample(n_samples, by_type=t)
        assert len(s_sub) == n_samples
        assert (s_sub.metadata["LEVEL_2"] == t).all()


def test_subsample_invalid_type():
    with pytest.raises(EndmemberError):
        endmembers.library.subsample(3, by_type="InvalidType")


def test_subsample_without_metadata():
    s = asd_spectra()
    with pytest.raises(ValueError):
        s.subsample(3, by_type=dtype)


@pytest.mark.parametrize("path", ["tmp.sli", "tmp", "tmp.hdr"])
def test_format_output_paths(path):
    s = asd_spectra()
    sli, hdr = s.format_output_paths(path)
    assert sli.endswith(".sli")
    assert hdr.endswith(".hdr")


def test_write_read_sli():
    n_spectra = 5
    sensor = sensors.Earthlib
    data = np.ones((n_spectra, sensor.band_count))
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


def test_from_sli_missing_header():
    with pytest.raises(FileNotFoundError):
        endmembers.Spectra.from_sli("/tmp/earthlib_does_not_exist.sli")


def test_list_types():
    types = endmembers.list_types()
    assert dtype in types
    assert random_str not in types


def test_get_type_level():
    assert endmembers.get_type_level(dtype) == 2
    assert endmembers.get_type_level(random_str) == 0


def test_list_types_deprecated_alias():
    with pytest.deprecated_call():
        assert endmembers.listTypes() == endmembers.list_types()


def test_get_type_level_deprecated_alias():
    with pytest.deprecated_call():
        assert endmembers.getTypeLevel(dtype) == endmembers.get_type_level(dtype)
