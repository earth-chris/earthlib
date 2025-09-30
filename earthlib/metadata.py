"""Metadata specification for VIPER tools tables."""

from dataclasses import asdict, dataclass
from typing import Literal


@dataclass
class Schema:
    """Base class for defining EO sensor specifications."""

    # unique ID for the measured spectrum
    NAME: str

    # the following are hierarchical land cover classification levels
    LEVEL_1: Literal["pervious", "impervious"]
    LEVEL_2: Literal["bare", "burn", "npv", "urban", "vegetation"]
    LEVEL_3: Literal["measured", "simulated"] = "measured"
    LEVEL_4: str | None = None

    # geographic location data
    LAT: float | None = None
    LON: float | None = None

    # data source
    SOURCE: str | None = None

    # additional notes about the sample
    NOTES: str | None = None

    def copy(self) -> "Schema":
        """Returns a copy of the schema object."""
        return Schema(**asdict(self))
