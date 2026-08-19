"""Functions for reading specifically formatted data, mostly spectral libraries."""

import os
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import spectral.io.envi as envi

from earthlib.sensors import ASD, Sensor

if TYPE_CHECKING:
    from earthlib.endmembers import Spectra


def check_file(path: str) -> bool:
    """Verifies whether a file exists and can be read.

    Args:
        path: the file path to check.

    Returns:
        file status.
    """
    return os.path.isfile(path) and os.access(path, os.R_OK)


def find_envi_header(path: str) -> str:
    """Locates the ENVI header file that accompanies a spectral library.

    Handles both header naming conventions: a sidecar that replaces the data
    file's extension (`spectra.hdr`) and one that appends to it
    (`spectra.sli.hdr`).

    Args:
        path: path to the spectral library, or to the header itself.

    Returns:
        path to the header file.

    Raises:
        FileNotFoundError: when no readable header accompanies the library.

    Example:
        ```python
        hdr = find_envi_header("spectra.sli")
        ```
    """
    base, ext = os.path.splitext(path)

    if ext.lower() == ".hdr":
        if not check_file(path):
            raise FileNotFoundError(f"No header file found for {path}")
        return path

    for candidate in (base + ".hdr", path + ".hdr"):
        if check_file(candidate):
            return candidate

    raise FileNotFoundError(f"No header file found for {path}")


def envi_output_paths(path: str) -> tuple[str, str]:
    """Formats the pair of output paths used to write an ENVI spectral library.

    Handles both header naming conventions, so a path produced by
    `find_envi_header` round-trips back to the library it came from.

    Args:
        path: the base file path, with or without an extension.

    Returns:
        the spectral library path and the header path.

    Example:
        ```python
        sli, hdr = envi_output_paths("spectra")
        ```
    """
    base, ext = os.path.splitext(path)

    if ext.lower() == ".sli":
        return path, f"{base}.hdr"

    if ext.lower() == ".hdr":
        # a `spectra.sli.hdr` sidecar already carries the library name in its base
        if base.lower().endswith(".sli"):
            return base, path
        return f"{base}.sli", path

    return f"{base}.sli", f"{base}.hdr"


def envi_library(
    path: str, sensor: Sensor | None = None
) -> tuple[np.ndarray, list[str], Sensor]:
    """Reads the raw contents of an ENVI spectral library.

    This is the low-level reader shared by `earthlib.read.spectral_library` and
    `earthlib.endmembers.Spectra.from_sli`.

    Args:
        path: path to the spectral library file. Searches for a .hdr sidecar.
        sensor: sensor information not recorded in the .hdr file. Derived from
            the header when None.

    Returns:
        the spectra array, the spectrum names, and the sensor.

    Raises:
        FileNotFoundError: when no readable header accompanies the library.
    """
    hdr = find_envi_header(path)
    data_path = _envi_data_path(hdr, path)
    sli = envi.open(hdr, data_path) if data_path else envi.open(hdr)

    if sensor is None:
        sensor = Sensor(
            name=os.path.basename(path),
            band_centers=sli.bands.centers,
            wavelength_unit=sli.bands.band_unit.lower(),
        )

    return sli.spectra, sli.names, sensor


def _envi_data_path(hdr: str, path: str) -> str | None:
    """Locates the data file paired with an ENVI header, or None to let spectral infer it."""
    base, _ = os.path.splitext(hdr)
    for candidate in (base, path, f"{base}.sli"):
        if check_file(candidate):
            return candidate

    return None


def spectral_library(
    path: str,
    sensor: Sensor | None = None,
    metadata: pd.DataFrame | None = None,
) -> "Spectra":
    """Reads an ENVI-format spectral library into memory.

    Args:
        path: path to the spectral library file. Searches for a .hdr sidecar.
        sensor: sensor information not recorded in the .hdr file.
        metadata: dataframe of per-spectrum metadata.

    Returns:
        endmembers from the spectral library.

    Raises:
        FileNotFoundError: when no readable header accompanies the library.

    Example:
        ```python
        spectra = spectral_library("spectra.sli")
        ```
    """
    from earthlib.endmembers import Spectra

    return Spectra.from_sli(path, sensor=sensor, metadata=metadata)


def jfsp(path: str) -> "Spectra":
    """Reads JFSP-formatted ASCII files.

    Reads the ASCII format spectral data from the Joint Fire Science Program and
    returns an object with the mean and +/- standard deviation reflectance.

    https://www.frames.gov/assessing-burn-severity/spectral-library/overview

    Args:
        path: file path to the JFSP spectra text file.

    Returns:
        an earthlib Spectra with the JFSP reflectance data.

    Example:
        ```python
        spectra = jfsp("jfsp_graysoil.txt")
        ```
    """
    from earthlib.endmembers import Spectra

    spectra = Spectra(data=None, sensor=ASD)
    spectra.spectra_stdevm = np.zeros(spectra.data.shape)
    spectra.spectra_stdevp = np.zeros(spectra.data.shape)

    with open(path, "r") as f:
        f.readline()
        for i, line in enumerate(f):
            values = line.strip().split()
            spectra.data[0, i] = values[1]
            spectra.spectra_stdevp[0, i] = values[2]
            spectra.spectra_stdevm[0, i] = values[3]

    return spectra
