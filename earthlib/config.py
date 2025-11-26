"""Default configuration paths and parameters"""

import os

import pandas as pd

# file paths for the package data
package_path = os.path.realpath(__file__)
package_dir = os.path.dirname(package_path)

# paths for the optimized spectra
metadata_path = os.path.join(package_dir, "data", "optimized.csv")
endmember_path = os.path.join(package_dir, "data", "optimized.sli")
header_path = endmember_path + ".hdr"
metadata = pd.read_csv(metadata_path)

# paths for the original library
full_metadata_path = os.path.join(package_dir, "data", "spectra.csv")
full_endmember_path = os.path.join(package_dir, "data", "spectra.sli")
header_path_full = full_endmember_path + ".hdr"
full_metadata = pd.read_csv(full_metadata_path)
