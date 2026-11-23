from pathlib import Path
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "gdp_out"
OUT.mkdir(exist_ok=True)

source = ROOT / "drifter_split.csv"
assert source.exists(), "Missing tracked drifter_split.csv"

split = pd.read_csv(source)

required = {
    "traj", "gdp_id", "n_pairs", "n_exits",
    "n_origin_cells", "first_origin",
    "last_origin", "split"
}
assert required <= set(split.columns)

assert split["traj"].is_unique
assert set(split["split"]) == {"train", "val", "test"}

# Preserve the original, frozen split.
shutil.copyfile(source, OUT / "drifter_split.csv")

# Reconstruct the drifter metadata.
ids = split.drop(columns=["split"])
ids.to_csv(OUT / "drifter_ids.csv", index=False)

print("PASS: Frozen drifter split copied unchanged.")
print(f"PASS: Reconstructed metadata for {len(ids):,} drifters.")

# If the pair table has been generated, verify its compatibility.
pairs_path = ROOT / "pairs7.csv"

if pairs_path.exists():
    pairs = pd.read_csv(pairs_path)

    counts = pairs.groupby("traj").size()
    expected = split.set_index("traj")["n_pairs"]

    assert counts.index.equals(expected.sort_index().index)
    assert counts.equals(expected.sort_index()), (
        "Pair counts do not match the frozen split."
    )

    print(f"PASS: {len(pairs):,} pairs match frozen split.")
else:
    print(
        "NOTE: pairs7.csv is not present. "
        "Generate it using Lucy's notebook first."
    )
