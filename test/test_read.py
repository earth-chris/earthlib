import os

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


# TODO: verify properties match the header file
def test_read_sli():
    s = read.spectral_library(endmember_path)
    # hdr = envi.open(header_path)
    assert s.data is not None


def test_jfsp():
    s = read.jfsp(jfsp_path)
    assert s.data.shape[0] == 1
    assert s.data.shape[1] == 2151
    assert s.sensor.band_centers.shape[0] == 2151
    assert (s.data >= 0).all()
    assert (s.data <= 1).all()
