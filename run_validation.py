from pathlib import Path
import tempfile
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent

required = [
    ROOT / "Validation_code.ipynb",
    ROOT / "pairs7.csv",
    ROOT / "gdp_out/drifter_ids.csv",
    ROOT / "gdp_out/drifter_split.csv",
]

for path in required:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path.name}. Run generate_pairs.py "
            "and prepare_inputs.py first."
        )

# Store reproduced outputs outside the repository.
audit = Path(tempfile.mkdtemp(prefix="data3001_validation_"))
output = audit / "outputs"
output.mkdir()

nb = nbformat.read(
    ROOT / "Validation_code.ipynb",
    as_version=4
)

# Validated notebook cells, in their original order.
# Excludes Colab-specific setup and final test-set cell 25.
selected = [8, 10, 12, 14, 16, 18, 19, 21, 23]

cells = []

for i in selected:
    cells.append(nb.cells[i - 1])

    if i == 8:
        cells.append(nbformat.v4.new_code_cell(
            f"OUT = {str(output)!r}\n"
            f"PAIRS_PATH = {str(ROOT / 'pairs7.csv')!r}\n"
            f"ID_TABLE_PATH = {str(ROOT / 'gdp_out/drifter_ids.csv')!r}\n"
            f"SPLIT_PATH = {str(ROOT / 'gdp_out/drifter_split.csv')!r}\n"
            "TEST_UNLOCKED = False\n"
        ))

run_nb = nbformat.v4.new_notebook(cells=cells)

print("Running DATA3001 validation...", flush=True)
print("Final test set remains locked.", flush=True)

client = NotebookClient(
    run_nb,
    timeout=None,
    kernel_name="python3",
    resources={"metadata": {"path": str(ROOT)}},
)

try:
    client.execute()
    print("\nPASS: Validation completed.", flush=True)
finally:
    nbformat.write(run_nb, audit / "executed_validation.ipynb")
    print("\nResults saved to:", output, flush=True)

    for path in sorted(output.glob("*.csv")):
        print(" -", path.name, flush=True)
