import os
from tempfile import NamedTemporaryFile

import numpy as np

from earthlib import read

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir, "data")
jfsp_path = os.path.join(data_dir, "jfsp_graysoil.txt")


def find_nearest(band_centers, wavelength, spectrum):
    idx = (np.abs(band_centers - wavelength)).argmin()
    return spectrum[idx]


def test_Spectra():
    n_spectra = 5
    instrument = "asd"
    s = read.Spectra(n_spectra=n_spectra, instrument=instrument)
    assert len(s.spectra) == n_spectra
    assert max(s.band_centers <= 2500)
    assert min(s.band_centers >= 350)

    # test water band removal
    s.spectra[:] = 1  # set all to 1
    s.remove_water_bands(set_nan=False)

    # 1400 nm should be masked, 1300 nm is ok
    spectrum = s.spectra[0]
    val_1400 = find_nearest(s.band_centers, 1400, spectrum)
    val_1000 = find_nearest(s.band_centers, 1000, spectrum)
    assert val_1400 == 0
    assert val_1000 != 0

    # nan test for water band removal
    s = read.Spectra(n_spectra=n_spectra, instrument=instrument)
    s.remove_water_bands(set_nan=True)
    assert np.isnan(s.spectra).any()

    # test shortwave band range retrieval
    shortwave_bands = s.get_shortwave_bands()
    assert min(s.band_centers[shortwave_bands]) >= 350
    assert max(s.band_centers[shortwave_bands]) <= 2500

    # test brightness normlization
    s.bn()

    # test on a subset of bands
    s = read.Spectra(n_spectra=n_spectra)
    s.bn(inds=np.arange(10))


def test_check_file():
    random_str = "537451794.xyz"
    assert read.check_file(__file__)
    assert not read.check_file(random_str)


def test_write_read_sli():
    n_spectra = 5
    all_values = 2
    instrument = "asd"
    s = read.Spectra(n_spectra=n_spectra, instrument=instrument)
    s.spectra[:] = all_values  # set all to a uniform value

    # write the output file
    with NamedTemporaryFile(suffix=".sli", delete=True) as tmp:
        out_file = tmp.name
        s.write_sli(out_file)

        # read it back in
        s2 = read.spectralLibrary(out_file)

        # check that the values are the same
        assert np.array_equal(s.band_centers, s2.band_centers)
        assert np.array_equal(s.spectra, s2.spectra)
        assert np.array_equal(s.names, s2.names)
        assert s.spectra.shape == s2.spectra.shape
        assert s.spectra.shape[0] == n_spectra
        assert (s.spectra == all_values).all()
        assert (s2.spectra == all_values).all()


def test_jfsp():
    s = read.jfsp(jfsp_path)
    assert s.spectra.shape[0] == 1
    assert s.spectra.shape[1] == 2151
    assert s.band_centers.shape[0] == 2151
    assert (s.spectra >= 0).all()
    assert (s.spectra <= 1).all()
