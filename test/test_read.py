import os

import pytest
import spectral.io.envi as envi

from earthlib import read
from earthlib.config import endmember_path, header_path

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir, "data")
jfsp_path = os.path.join(data_dir, "jfsp_graysoil.txt")


def test_check_file():
    random_str = "537451794.xyz"
    assert read.check_file(__file__)
    assert not read.check_file(random_str)


def test_find_envi_header():
    # should find header with .sli extension
    hdr = read.find_envi_header(endmember_path)
    assert hdr == header_path

    # should find header with .hdr extension
    hdr = read.find_envi_header(header_path)
    assert hdr == header_path

    # should fail on nonexistent file
    with pytest.raises(FileNotFoundError):
        read.find_envi_header("nonexistent_file.sli")


def test_find_envi_header_missing_hdr_path():
    with pytest.raises(FileNotFoundError):
        read.find_envi_header("nonexistent_file.hdr")


@pytest.mark.parametrize(
    "path,expected_sli,expected_hdr",
    [
        ("tmp.sli", "tmp.sli", "tmp.hdr"),
        ("tmp", "tmp.sli", "tmp.hdr"),
        ("tmp.hdr", "tmp.sli", "tmp.hdr"),
    ],
)
def test_envi_output_paths(path, expected_sli, expected_hdr):
    sli, hdr = read.envi_output_paths(path)
    assert sli == expected_sli
    assert hdr == expected_hdr


def test_envi_library():
    data, names, sensor = read.envi_library(endmember_path)
    hdr = envi.open(header_path)
    assert (data == hdr.spectra).all()
    assert len(names) == data.shape[0]
    assert sensor.band_count == hdr.params.ncols


def test_spectral_library_and_from_sli_agree():
    """read.spectral_library and Spectra.from_sli must not diverge."""
    from earthlib.endmembers import Spectra

    a = read.spectral_library(endmember_path)
    b = Spectra.from_sli(endmember_path)
    assert (a.data == b.data).all()
    assert a.names == b.names
    assert (a.sensor.band_centers == b.sensor.band_centers).all()


def test_read_sli():
    s = read.spectral_library(endmember_path)
    hdr = envi.open(header_path)
    assert s.sensor.band_count == hdr.params.ncols
    assert (s.data == hdr.spectra).all()


def test_jfsp():
    s = read.jfsp(jfsp_path)
    assert s.data.shape[0] == 1
    assert s.data.shape[1] == 2151
    assert s.sensor.band_centers.shape[0] == 2151
    assert (s.data >= 0).all()
    assert (s.data <= 1).all()
    assert s.spectra_stdevp is not None
    assert s.spectra_stdevm is not None
