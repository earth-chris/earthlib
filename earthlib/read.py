"""Functions for reading specifically formatted data, mostly spectral libraries."""

import os

import numpy as np
import pandas as pd
import spectral.io.envi as envi

from earthlib.endmembers import Spectra
from earthlib.sensors import Sensor


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
    if check_file(path[:-4] + ".hdr"):
        hdr = path[:-4] + ".hdr"
    else:
        if check_file(path + ".hdr"):
            hdr = path + ".hdr"
        else:
            return None

    sli = envi.open(hdr, path)

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
    s = Spectra(n_spectra=1, instrument="asd")
    s.spectra_stdevm = np.zeros(s.spectra.shape)
    s.spectra_stdevp = np.zeros(s.spectra.shape)

    # open the file and read the data
    with open(path, "r") as f:
        f.readline()
        for i, line in enumerate(f):
            line = line.strip().split()
            s.spectra[0, i] = line[1]
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
