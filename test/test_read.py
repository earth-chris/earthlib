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
