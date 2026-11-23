from pathlib import Path
import shutil
import nbformat
import pandas as pd
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "gdp_out"
OUT.mkdir(exist_ok=True)

source = ROOT / "Lucy_temperature_and_handover.ipynb"
assert source.exists(), "Lucy notebook not found"

print("Loading Lucy's pair-generation notebook...", flush=True)

nb = nbformat.read(source, as_version=4)

# Verified cells that generate the original seven-day pairs.
selected = [5, 9, 12, 21]
cells = []

for i in selected:
    cells.append(nb.cells[i - 1])

    if i == 5:
        cells.append(
            nbformat.v4.new_code_cell(
                f"OUT = {str(OUT)!r}"
            )
        )

run_nb = nbformat.v4.new_notebook(cells=cells)

print("Generating seven-day pairs from NOAA...", flush=True)

client = NotebookClient(
    run_nb,
    timeout=None,
    kernel_name="python3",
    resources={"metadata": {"path": str(ROOT)}},
)

client.execute()

generated = OUT / "pairs7.csv"
target = ROOT / "pairs7.csv"

assert generated.exists(), "Pair generation did not produce pairs7.csv"

pairs = pd.read_csv(generated)
assert len(pairs) == 154139, (
    f"Expected 154139 pairs, got {len(pairs)}"
)

if target.exists():
    existing = pd.read_csv(target)
    pd.testing.assert_frame_equal(existing, pairs, check_exact=True)
    print("PASS: Generated pairs match existing pairs7.csv exactly.")
else:
    shutil.copyfile(generated, target)
    print("PASS: Generated pairs7.csv in repository root.")

print(f"PASS: {len(pairs):,} seven-day pairs generated.")
