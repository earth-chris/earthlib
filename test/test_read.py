import os

from earthlib import read
from earthlib.config import endmember_path

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir, "data")
jfsp_path = os.path.join(data_dir, "jfsp_graysoil.txt")


def test_check_file():
    random_str = "537451794.xyz"
    assert read.check_file(__file__)
    assert not read.check_file(random_str)


def test_read_sli():
    s = read.spectral_library(endmember_path)
    assert s is not None
    assert s.data.shape[0] == 1
    assert s.data.shape[1] == 2151
    assert s.band_centers.shape[0] == 2151
    assert (s.data >= 0).all()
    assert (s.data <= 1).all()


def test_jfsp():
    s = read.jfsp(jfsp_path)
    assert s.data.shape[0] == 1
    assert s.data.shape[1] == 2151
    assert s.band_centers.shape[0] == 2151
    assert (s.data >= 0).all()
    assert (s.data <= 1).all()
