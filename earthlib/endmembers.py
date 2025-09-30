"""Endmember spectra management tools"""

import os
from warnings import warn

import numpy as np
import pandas as pd
import spectral
import spectral.io.envi as envi

from earthlib.config import endmember_path, metadata
from earthlib.errors import EndmemberError
from earthlib.sensors import Earthlib, Sensor


class Spectra:
    """Base class for endmember spectra management."""

    def __init__(
        self,
        data: np.ndarray | None,
        sensor: Sensor,
        metadata: pd.DataFrame | None = None,
        names: list[str] | None = None,
    ) -> None:
        """Endmember spectra initialization.

        Args:
            data: an array of spectral responses
                should be of shape (n_spectra, n_wavelengths).
                initiaalizes to zeros if None.
            sensor: the sensor object defining the instrument
                used for measurement
            names: list of names to assign to each spectrum
            metadata: dataframe containing metadata for each spectrum.
                Should have n_spectra rows.
                See earthlib.metadata.Schema for expected columns.
        """
        self.sensor = sensor.copy()
        self.metadata = metadata.copy() if metadata is not None else None

        if data is None:
            self.data = np.zeros((1, self.sensor.band_count), dtype=np.float32)
        else:
            self.data = data.copy()

        if names is None:
            self.names = ["spectrum_{}".format(i + 1) for i in range(len(self.data))]
        else:
            self.names = names.copy() if names is not None else None

    def __len__(self) -> int:
        """Returns the number of spectra stored."""
        return len(self.data)

    def remove_water_bands(self, set_nan: bool = True) -> None:
        """Masks reflectance data from water vapor absorption bands.

        Wavelengths in the ranges of (1.35-1.46 um and 1.79-1.96 um) will be masked.
            Updates self.data in-place.

        Args:
            set_nan: set the water bands to NaN. False sets values to 0.
        """
        update_val = np.nan if set_nan else 0

        if self.sensor.wavelength_unit.lower() == "micrometers":
            water_vapor_bands = [[1.35, 1.46], [1.79, 1.96]]
        else:
            water_vapor_bands = [[1350.0, 1460.0], [1790.0, 1960.0]]

        # start with nir-swir1 transition
        gt = np.where(self.sensor.band_centers > water_vapor_bands[0][0])
        lt = np.where(self.sensor.band_centers < water_vapor_bands[0][1])
        nd = np.intersect1d(gt[0], lt[0])
        self.data[:, nd] = update_val

        # then swir1-swir2 transition
        gt = np.where(self.sensor.band_centers > water_vapor_bands[1][0])
        lt = np.where(self.sensor.band_centers < water_vapor_bands[1][1])
        nd = np.intersect1d(gt[0], lt[0])
        self.data[:, nd] = update_val

    def shortwave_band_idxs(self) -> np.ndarray:
        """Returns indices of the bands that encompass the shortwave range.

        This refers to the range (350 - 2500 nm).

        Returns:
            an index of bands to subset to the shortwave range.
        """
        # set range to return in nanometers
        shortwave_range = np.array([350.0, 2500.0])

        # normalize if wavelength units are different
        if self.sensor.wavelength_unit.lower() == "micrometers":
            shortwave_range /= 1000.0

        # find overlapping range
        gt = np.where(self.sensor.band_centers > shortwave_range[0])
        lt = np.where(self.sensor.band_centers < shortwave_range[1])
        overlap = np.intersect1d(gt[0], lt[0])

        # return output
        return overlap

    def brightness_normalize(self, inds: list = None) -> None:
        """Brightness normalizes the spectra.

        Updates the self.spectra array in-place.

        Args:
            inds: the band indices to use for normalization.
        """
        # check if indices were set and valid. if not, use all bands
        if inds is not None:
            if max(inds) > self.data.shape[-1]:
                inds = range(0, self.data.shape[-1])
                warn("Invalid range set. using all spectra")

            if min(inds) < 0:
                inds = range(0, self.data.shape[-1])
                warn("Invalid range set. using all spectra")

        else:
            inds = range(0, self.data.shape[-1])

        # normalize
        self.data = self.data[:, inds] / np.expand_dims(
            np.sqrt((self.data[:, inds] ** 2).sum(1)), 1
        )

        # subset band centers to the indices selected
        self.sensor.band_centers = self.sensor.band_centers[inds]

        # and fwhms, too
        if self.sensor.band_widths is not None:
            self.sensor.band_widths = self.sensor.band_widths[inds]

    def to_nanometers(self) -> None:
        """Converts the sensor band centers to nanometers.

        Updates self.sensor.band_centers and self.sensor.wavelength_unit in-place.
        """
        if self.sensor.wavelength_unit.lower() == "micrometers":
            self.sensor.band_centers *= 1000.0
            self.sensor.wavelength_unit = "nanometers"
        else:
            warn("Wavelength unit already in nanometers. No conversion applied.")

    def to_micrometers(self) -> None:
        """Converts the sensor band centers to micrometers.

        Updates self.sensor.band_centers and self.sensor.wavelength_unit in-place.
        """
        if self.sensor.wavelength_unit.lower() == "nanometers":
            self.sensor.band_centers /= 1000.0
            self.sensor.wavelength_unit = "micrometers"
        else:
            warn("Wavelength unit already in micrometers. No conversion applied.")

    def to_sensor(self, sensor: Sensor) -> "Spectra":
        """Resamples the spectra to a different sensor's band centers.

        Updates self.data and self.sensor in-place.

        Args:
            sensor: the sensor object defining the instrument
                to resample the spectra to.

        Returns:
            a new Spectra object with the resampled spectra and new sensor info.
        """
        # create a band resampler for this collection
        resampler = spectral.BandResampler(
            self.sensor.band_centers,
            sensor.band_centers,
            fwhm1=self.sensor.band_widths,
            fwhm2=sensor.band_widths,
        )

        # loop through each spectrum and resample to the sensor wavelengths
        resampled = list()
        for i in range(self.data.shape[0]):
            spectrum = resampler(self.data[i, :])
            resampled.append(spectrum)

        # update the data and sensor info in place
        new_spectra = Spectra(
            data=np.array(resampled, dtype=np.float32),
            sensor=sensor.copy(),
            names=self.names.copy(),
            metadata=self.metadata.copy() if self.metadata is not None else None,
        )
        return new_spectra

    def subsample(self, n: int, by_type: str | None = None) -> "Spectra":
        """Subsamples n random spectra.

        Args:
            n: the number of random spectra to select.
            by_type: if set, subsamples n spectra from this land cover type only.
                Uses the metadata DataFrame to filter by type.
                If the metadata is not set, raises a ValueError.
                Get the valid type list using earthlib.utils.listTypes().

        Returns:
            subsampled Spectra data.
        """
        # pre-filter to just the spectra of the selected type
        if by_type is None:
            spectra = self.data
            names = self.names
            metadata = self.metadata

        else:
            if self.metadata is None:
                raise ValueError("Metadata is not set.")

            level = getTypeLevel(by_type)
            if level == 0:
                raise EndmemberError(
                    f"Invalid land cover type: {by_type}. Get valid values from earthlib.listTypes()."
                )

            key = f"LEVEL_{level}"
            indices = self.metadata[key] == by_type
            spectra = self.data[indices, :]
            names = [self.names[idx] for idx in range(len(self.names)) if indices[idx]]
            metadata = self.metadata[indices].reset_index(drop=True)

        random_indices = np.random.randint(0, len(spectra), size=n)
        subsampled_spectra = spectra[random_indices, :]
        subsampled_names = [names[i] for i in random_indices]
        subsampled_metadata = (
            metadata.iloc[random_indices].reset_index(drop=True)
            if metadata is not None
            else None
        )

        endmembers = Spectra(
            data=subsampled_spectra,
            sensor=self.sensor.copy(),
            names=subsampled_names,
            metadata=subsampled_metadata,
        )

        return endmembers

    def to_sli(
        self,
        path: str,
        rows: list[int] | np.ndarray | None = None,
        bands: list[int] | np.ndarray | None = None,
    ) -> None:
        """Write the endmember spectra to an ENVI spectral library.

        Args:
            path: the output file path.
            row_inds: the row-wise indices of the array to write.
            spectral_inds: indices for which spectral to write
        """
        sli, hdr = self.format_output_paths(path)

        # subset the data if specific indices are set
        spectra = self.data.copy()
        names = self.names.copy()
        band_centers = self.sensor.band_centers.copy()

        if rows is not None:
            spectra = spectra[rows, :]
            names = np.array(names)[rows]

        if bands is not None:
            spectra = spectra[:, bands]
            band_centers = band_centers[bands]

        # set up the metadata for the ENVI header file
        envi_metadata = {
            "samples": len(band_centers),
            "lines": len(names),
            "bands": 1,
            "data type": 4,
            "header offset": 0,
            "interleave": "bsq",
            "byte order": 0,
            "sensor type": self.sensor.name,
            "spectra names": names,
            "wavelength units": self.sensor.wavelength_unit,
            "wavelength": band_centers,
        }
        spectral.envi.write_envi_header(hdr, envi_metadata, is_library=True)

        # then write the spectral library
        with open(sli, "w") as f:
            spectra.astype(np.float32).tofile(f)

    @classmethod
    def from_sli(
        cls,
        path: str,
        sensor: Sensor | None = None,
        metadata: pd.DataFrame | None = None,
    ) -> "Spectra":
        """Reads an ENVI spectral library file.

        Args:
            path: path to the spectral library file.
                Searches for a .hdr sidecar file.
            sensor: an earthlib.sensors.Sensor object specifying
                sensor information not included in the .hdr file.
            metadata: DataFrame containing metadata for each spectrum.

        Returns:
            Spectra containing the spectral data, sensor information, and metadata.
        """
        hdr = cls.get_hdr_path(path)
        sli = envi.open(hdr, path)

        if sensor is None:
            sensor = Sensor(
                name=os.path.basename(path),
                band_centers=sli.bands.centers,
                wavelength_unit=sli.bands.band_unit,
            )

        return cls(
            data=sli.spectra,
            sensor=sensor,
            names=sli.names,
            metadata=metadata,
        )

    def format_output_paths(self, path: str) -> tuple[str, str]:
        """Formats the output paths for the spectral library and header.

        Args:
            path: the base file path (with or without extension).

        Returns:
            A tuple containing the paths for the spectral library and header.
        """

        # set up the output file names for the library and the header
        base, ext = os.path.splitext(path)
        if ext.lower() == ".sli":
            sli = path
            hdr = f"{base}.hdr"
        elif ext.lower() == ".hdr":
            sli = path.replace(".hdr", ".sli")
            hdr = path
        else:
            sli = f"{base}.sli"
            hdr = f"{base}.hdr"

        return sli, hdr

    @classmethod
    def get_hdr_path(cls, path: str) -> str:
        """Gets the header file path from a given spectral library path.

        Args:
            path: The path to the spectral library file.

        Returns:
            The path to the corresponding header file.
        """
        if os.path.isfile(path[:-4] + ".hdr"):
            hdr = path[:-4] + ".hdr"
        else:
            if os.path.isfile(path + ".hdr"):
                hdr = path + ".hdr"

        return hdr


def listTypes(level: int = 2) -> list:
    """Returns a list of the spectral classification types.

    Args:
        level: the level of spectral classification specificity to return. Supports integers 1-4.

    Returns:
        classes: a list of spectral data types referenced throughout this package.
    """
    key = f"LEVEL_{level}"
    types = list(metadata[key].unique())
    return types


def getTypeLevel(Type: str) -> int:
    """Checks whether a spectral data type is available in the endmember library.

    Args:
        Type: the type of spectra to select.

    Returns:
        level: the metadata "level" of the group for subsetting. returns 0 if not found.
    """
    for i in range(4):
        level = i + 1
        available_types = listTypes(level=level)
        if Type in available_types:
            return level

    return 0


library = Spectra.from_sli(endmember_path, sensor=Earthlib, metadata=metadata)
