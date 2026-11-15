import numpy as np
import pandas as pd
from clouddrift.datasets import gdp1h

# STEP 1: Load NOAA drifter dataset
print("Loading NOAA GDP data...")
ds = gdp1h()

# STEP 2: Get drogue-loss dates
lost = ds["drogue_lost_date"].values

# Lucy's timestamp conversion
def as_time(x):
    x = np.asarray(x)
    if np.issubdtype(x.dtype, np.datetime64):
        return x
    return pd.to_datetime(x, unit="s").to_numpy()

lost_dates = as_time(lost)

# STEP 3: Create a table linking drifter indices to drogue-loss dates
drogue_data = pd.DataFrame({
    "traj": np.arange(len(lost_dates)),
    "drogue_lost_date": lost_dates
})

# STEP 4: Save as CSV
drogue_data.to_csv("drogue_info.csv", index=False)

print("\nDrogue information exported!")
print(drogue_data.head())
print("Total drifters:", len(drogue_data))
print("Missing drogue-loss dates:",
      drogue_data["drogue_lost_date"].isna().sum())


# Check which drifters from the pair dataset are represented
pairs_check = pd.read_csv("pairs7.csv")

print("\nDRIFTER ID CHECK")
print("Maximum pair traj index:", pairs_check["traj"].max())
print("Number of NOAA drifters:", len(drogue_data))

print(
    "All pair indices within NOAA dataset:",
    pairs_check["traj"].between(0, len(drogue_data) - 1).all()
)

# ==================================================
# VERIFY LUCY'S PAIRS AGAINST ORIGINAL NOAA DATA
# ==================================================

pairs_check = pd.read_csv("pairs7.csv")
pairs_check["time"] = pd.to_datetime(
    pairs_check["time"], utc=True
)

# Randomly sample 100 pairs for verification
sample = pairs_check.sample(n=100, random_state=42)

# Original NOAA observation timestamps
noaa_times = pd.to_datetime(
    as_time(ds["time"].values),
    utc=True
)

# Compare timestamps at Lucy's obs_row indices
original_times = noaa_times[
    sample["obs_row"].to_numpy(dtype=int)
]

matches = (
    original_times.to_numpy()
    == sample["time"].to_numpy()
)

print("\nOBSERVATION TIMESTAMP VERIFICATION")
print("Pairs checked:", len(sample))
print("Matching timestamps:", matches.sum())
print("All timestamps match:", matches.all())

# ==================================================
# VERIFY ALL TRAJECTORY IDS
# ==================================================

rowsize = ds["rowsize"].values
trajectory_ends = np.cumsum(rowsize)

pairs_check = pd.read_csv("pairs7.csv")

calculated_traj = np.searchsorted(
    trajectory_ends,
    pairs_check["obs_row"].to_numpy(dtype=int),
    side="right"
)

matches = (
    calculated_traj
    == pairs_check["traj"].to_numpy(dtype=int)
)

print("\nTRAJECTORY ID VERIFICATION")
print("Pairs checked:", len(matches))
print("Matching trajectory IDs:", matches.sum())
print("All trajectory IDs match:", matches.all())