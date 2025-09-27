from earthlib import read
from earthlib.config import collections, metadata
from earthlib.utils import getBands, getScaler, listSensors, listTypes, selectSpectra

try:
    from earthlib.geelib import (
        BRDFCorrect,
        BrightMask,
        BurnPVSoil,
        CloudMask,
        NIRv,
        Scale,
        ShadeMask,
        SoilPVNPV,
        Unmix,
        VegImperviousSoil,
    )
    from earthlib.geelib.utils import getCollection
except ImportError:
    pass

# expose the full spectral library
library = read.endmembers()
