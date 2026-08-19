"""Endmember spectra management tools"""

import warnings

import numpy as np
import pandas as pd
import spectral
from loguru import logger

from earthlib import read
from earthlib.config import endmember_path, full_endmember_path, full_metadata, metadata
from earthlib.errors import EndmemberError
from earthlib.sensors import Earthlib, Sensor

# every index form Spectra.__getitem__ accepts
SpectraIndex = int | slice | list[int] | list[bool] | np.ndarray | pd.Index | pd.Series


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

        self.data: np.ndarray
        if data is None:
            self.data = np.zeros((1, self.sensor.band_count), dtype=np.float32)
        else:
            self.data = data.copy()

        self.names: list[str]
        if names is None:
            self.names = ["spectrum_{}".format(i + 1) for i in range(len(self.data))]
        else:
            self.names = names.copy()

        # populated by earthlib.read.jfsp, which carries +/- stdev spectra
        self.spectra_stdevp: np.ndarray | None = None
        self.spectra_stdevm: np.ndarray | None = None

    def __len__(self) -> int:
        """Returns the number of spectra stored."""
        return len(self.data)

    def __getitem__(self, idx: SpectraIndex) -> "Spectra":
        """Index the spectra to return a subset.

        Supports integer, slice, integer-sequence and boolean-mask indexing.

        Args:
            idx: the index, slice, integer sequence or boolean mask to select.

        Returns:
            a new Spectra holding the selected subset.

        Example:
            ```python
            first_ten = library[:10]
            vegetation = library[library.metadata["LEVEL_2"] == "vegetation"]
            ```
        """
        positions = self._resolve_index(idx)
        data = self.data[positions]

        if self.metadata is not None:
            metadata = self.metadata.iloc[positions].reset_index(drop=True)
        else:
            metadata = None

        if self.names is not None:
            names = [self.names[i] for i in positions]
        else:
            names = None

        return Spectra(data=data, sensor=self.sensor, metadata=metadata, names=names)

    def _resolve_index(self, idx: SpectraIndex) -> np.ndarray:
        """Normalizes any supported index into an array of integer positions.

        Boolean masks are distinguished from integer sequences by dtype, so an
        integer sequence whose length happens to equal the number of spectra is
        no longer misread as a mask.
        """
        if isinstance(idx, slice):
            return np.arange(len(self.data))[idx]

        if isinstance(idx, (int, np.integer)):
            return np.array([idx], dtype=int)

        values = np.asarray(idx.values if isinstance(idx, pd.Series) else idx)

        if values.dtype == bool:
            if len(values) != len(self.data):
                raise IndexError(
                    f"Boolean mask of length {len(values)} does not match "
                    f"{len(self.data)} spectra."
                )
            return np.flatnonzero(values)

        return values.astype(int)

    def remove_water_bands(self, set_nan: bool = True) -> None:
        """Masks reflectance data from water vapor absorption bands.

        Wavelengths in the ranges of (1.35-1.46 um and 1.79-1.96 um) will be masked.
            Updates self.data in-place.

        Args:
            set_nan: set the water bands to NaN. False sets values to 0.
        """
        update_val = np.nan if set_nan else 0
        centers = np.asarray(self.sensor.band_centers)

        if self.sensor.wavelength_unit.lower() == "micrometers":
            water_vapor_bands = [[1.35, 1.46], [1.79, 1.96]]
        else:
            water_vapor_bands = [[1350.0, 1460.0], [1790.0, 1960.0]]

        # start with nir-swir1 transition
        gt = np.where(centers > water_vapor_bands[0][0])
        lt = np.where(centers < water_vapor_bands[0][1])
        nd = np.intersect1d(gt[0], lt[0])
        self.data[:, nd] = update_val

        # then swir1-swir2 transition
        gt = np.where(centers > water_vapor_bands[1][0])
        lt = np.where(centers < water_vapor_bands[1][1])
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
        centers = np.asarray(self.sensor.band_centers)

        # normalize if wavelength units are different
        if self.sensor.wavelength_unit.lower() == "micrometers":
            shortwave_range /= 1000.0

        # find overlapping range
        gt = np.where(centers > shortwave_range[0])
        lt = np.where(centers < shortwave_range[1])
        overlap = np.intersect1d(gt[0], lt[0])

        # return output
        return overlap

    def brightness_normalize(self, inds: list[int] | None = None) -> None:
        """Brightness normalizes the spectra.

        Updates self.data, and subsets the sensor band centers and widths to the
        selected indices, in-place.

        Args:
            inds: the band indices to use for normalization. Uses all bands when
                None, or when the indices fall outside the available bands.

        Example:
            ```python
            library.brightness_normalize()
            ```
        """
        band_count = self.data.shape[-1]
        selected = list(range(band_count)) if inds is None else list(inds)

        if selected and (max(selected) >= band_count or min(selected) < 0):
            logger.warning("Invalid range set. using all spectra")
            selected = list(range(band_count))

        # normalize
        self.data = self.data[:, selected] / np.expand_dims(
            np.sqrt((self.data[:, selected] ** 2).sum(1)), 1
        )

        # subset band centers to the indices selected
        centers = np.asarray(self.sensor.band_centers)
        self.sensor.band_centers = centers[selected]

        # and fwhms, too
        if self.sensor.band_widths is not None:
            widths = np.asarray(self.sensor.band_widths)
            self.sensor.band_widths = widths[selected]

    def to_nanometers(self) -> None:
        """Converts the sensor band centers and widths to nanometers.

        Updates self.sensor.band_centers, self.sensor.band_widths and
        self.sensor.wavelength_unit in-place. Does nothing if already in
        nanometers.
        """
        if self.sensor.wavelength_unit.lower() != "micrometers":
            logger.warning(
                "Wavelength unit already in nanometers. No conversion applied."
            )
            return

        self.sensor.band_centers = np.asarray(self.sensor.band_centers) * 1000.0
        if self.sensor.band_widths is not None:
            self.sensor.band_widths = np.asarray(self.sensor.band_widths) * 1000.0
        self.sensor.wavelength_unit = "nanometers"

    def to_micrometers(self) -> None:
        """Converts the sensor band centers and widths to micrometers.

        Updates self.sensor.band_centers, self.sensor.band_widths and
        self.sensor.wavelength_unit in-place. Does nothing if already in
        micrometers.
        """
        if self.sensor.wavelength_unit.lower() != "nanometers":
            logger.warning(
                "Wavelength unit already in micrometers. No conversion applied."
            )
            return

        self.sensor.band_centers = np.asarray(self.sensor.band_centers) / 1000.0
        if self.sensor.band_widths is not None:
            self.sensor.band_widths = np.asarray(self.sensor.band_widths) / 1000.0
        self.sensor.wavelength_unit = "micrometers"

    def to_sensor(self, sensor: Sensor) -> "Spectra":
        """Resamples the spectra to a different sensor's band centers.

        Args:
            sensor: the sensor object defining the instrument
                to resample the spectra to.

        Returns:
            a new Spectra object with the resampled spectra and new sensor info.

        Example:
            ```python
            landsat_spectra = library.to_sensor(earthlib.sensors.Landsat8)
            ```
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
        """Subsamples n random spectra, with replacement.

        Args:
            n: the number of random spectra to select.
            by_type: if set, subsamples n spectra from this land cover type only.
                Uses the metadata DataFrame to filter by type.
                Get the valid type list using earthlib.list_types().

        Returns:
            subsampled Spectra data.

        Raises:
            ValueError: when by_type is set but no metadata is available.
            EndmemberError: when by_type is not a valid land cover type.

        Example:
            ```python
            vegetation = library.subsample(10, by_type="vegetation")
            ```
        """
        # pre-filter to just the spectra of the selected type
        if by_type is None:
            spectra = self.data
            names = self.names
            metadata = self.metadata

        else:
            if self.metadata is None:
                raise ValueError("Metadata is not set.")

            level = get_type_level(by_type)
            if level == 0:
                raise EndmemberError(
                    f"Invalid land cover type: {by_type}. Get valid values from earthlib.list_types()."
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
            rows: the row-wise indices of the array to write.
            bands: indices for which spectral to write

        Example:
            ```python
            library.subsample(10).to_sli("subsample.sli")
            ```
        """
        sli, hdr = read.envi_output_paths(path)

        # subset the data if specific indices are set
        spectra = self.data.copy()
        names = np.array(self.names)
        band_centers = np.asarray(self.sensor.band_centers).copy()

        if rows is not None:
            spectra = spectra[rows, :]
            names = names[rows]

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
        with open(sli, "wb") as f:
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

        Raises:
            FileNotFoundError: when no readable header accompanies the library.

        Example:
            ```python
            spectra = Spectra.from_sli("spectra.sli")
            ```
        """
        data, names, sensor = read.envi_library(path, sensor=sensor)

        return cls(data=data, sensor=sensor, names=names, metadata=metadata)

    def format_output_paths(self, path: str) -> tuple[str, str]:
        """Formats the output paths for the spectral library and header.

        Args:
            path: the base file path (with or without extension).

        Returns:
            A tuple containing the paths for the spectral library and header.
        """
        return read.envi_output_paths(path)


def list_types(level: int = 2) -> list:
    """Returns a list of the spectral classification types.

    Args:
        level: the level of spectral classification specificity to return. Supports integers 1-4.

    Returns:
        classes: a list of spectral data types referenced throughout this package.

    Example:
        ```python
        cover_types = list_types(level=2)
        ```
    """
    key = f"LEVEL_{level}"
    types = list(metadata[key].unique())
    return types


def get_type_level(type_name: str) -> int:
    """Checks whether a spectral data type is available in the endmember library.

    Args:
        type_name: the type of spectra to select.

    Returns:
        level: the metadata "level" of the group for subsetting. returns 0 if not found.

    Example:
        ```python
        level = get_type_level("vegetation")
        ```
    """
    for i in range(4):
        level = i + 1
        available_types = list_types(level=level)
        if type_name in available_types:
            return level

    return 0


def listTypes(level: int = 2) -> list:
    """Deprecated alias for `list_types`."""
    warnings.warn(
        "listTypes() is deprecated and will be removed in v2.0.0. Use list_types().",
        DeprecationWarning,
        stacklevel=2,
    )
    return list_types(level=level)


def getTypeLevel(Type: str) -> int:
    """Deprecated alias for `get_type_level`."""
    warnings.warn(
        "getTypeLevel() is deprecated and will be removed in v2.0.0. Use get_type_level().",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_type_level(Type)


library = Spectra.from_sli(endmember_path, sensor=Earthlib, metadata=metadata)

full_library = Spectra.from_sli(
    full_endmember_path, sensor=Earthlib, metadata=full_metadata
)
