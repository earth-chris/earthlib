"""Default configuration paths and parameters"""

import os

import pandas as pd

# file paths for the package data
package_path = os.path.realpath(__file__)
package_dir = os.path.dirname(package_path)
metadata_path = os.path.join(package_dir, "data", "spectra.csv")
endmember_path = os.path.join(package_dir, "data", "spectra.sli")

# read critical data into memory
metadata = pd.read_csv(metadata_path)
