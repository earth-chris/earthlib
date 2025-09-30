"""Functions for reading specifically formatted data, mostly spectral libraries."""

import os

import numpy as np
import pandas as pd
import spectral.io.envi as envi

from earthlib.endmembers import Spectra
from earthlib.sensors import ASD, Sensor


def find_envi_header(path: str) -> tuple[str, str]:
    """Generates the file paths for an ENVI spectral library and its header file."""
    base, ext = os.path.splitext(path)

    if ext == ".hdr":
        hdr = path

    else:
        if check_file(base + ".hdr"):
            hdr = base + ".hdr"

        else:
            if check_file(path + ".hdr"):
                hdr = path + ".hdr"

            else:
                raise FileNotFoundError(f"No header file found for {path}")

    return hdr


def spectral_library(
    path: str,
    sensor: Sensor | None = None,
    metadata: pd.DataFrame | None = None,
) -> Spectra:
    """Reads an ENVI-format spectral library into memory.

    Args:
        path: path to the spectral library file.
            Searches for a .hdr sidecar file.
        sensor: an earthlib.sensors.Sensor object specifying
            sensor information not included in the .hdr file.

    Returns:
        endmembers from the spectral library
    """
    # get the header file path
    hdr = find_envi_header(path)

    sli = envi.open(hdr)

    if sensor is None:
        sensor = Sensor(
            name=os.path.basename(path),
            band_centers=sli.bands.centers,
            wavelength_unit=sli.bands.band_unit,
        )

    endmembers = Spectra(
        data=sli.spectra,
        sensor=sensor,
        names=sli.names,
        metadata=metadata,
    )

    return endmembers


def jfsp(path: str) -> Spectra:
    """Reads JFSP-formatted ASCII files.

    Reads the ASCII format spectral data from the Joint Fire Science Program and returns an object with the mean and +/- standard deviation reflectance.

    https://www.frames.gov/assessing-burn-severity/spectral-library/overview

    Args:
        path: file path to the JFSP spectra text file.

    Returns:
        an earthlib Spectra with the JFSP reflectance data.
    """

    # create the spectral object
    s = Spectra(data=None, sensor=ASD)
    print(s.data)
    s.spectra_stdevm = np.zeros(s.data.shape)
    s.spectra_stdevp = np.zeros(s.data.shape)

    print(s.data.shape)
    print(ASD.band_count)
    # print(s.sensor)

    # open the file and read the data
    with open(path, "r") as f:
        f.readline()
        for i, line in enumerate(f):
            line = line.strip().split()
            s.data[0, i] = line[1]
            s.spectra_stdevp[0, i] = line[2]
            s.spectra_stdevm[0, i] = line[3]

        return s


def check_file(path: str) -> bool:
    """Verifies whether a file exists and can be read.

    Args:
        path: the file path to check.

    Returns:
        file status.
    """
    return os.path.isfile(path) and os.access(path, os.R_OK)
