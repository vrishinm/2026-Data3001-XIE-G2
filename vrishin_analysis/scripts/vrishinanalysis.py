import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load Lucy's seven-day pairs
pairs = pd.read_csv("pairs7.csv")

# Basic checks
print("Total 7-day pairs:", len(pairs))
print("Unique drifters:", pairs["traj"].nunique())
print("Missing values:")
print(pairs.isnull().sum())

# Check for duplicate starting observations
duplicates = pairs.duplicated(subset=["traj", "time"]).sum()
print("Duplicate starting observations:", duplicates)

# Check first-exit outcomes
print("\nDestination counts:")
print("Inside region:", (pairs["dest"] < 234).sum())
print("West exits:", (pairs["dest"] == 234).sum())
print("East exits:", (pairs["dest"] == 235).sum())
print("South exits:", (pairs["dest"] == 236).sum())
print("North exits:", (pairs["dest"] == 237).sum())

# TASK 2: Build a reusable transition matrix

def build_transition_matrix(pairs):
    n_cells = 234
    n_states = 238  # 234 interior cells + 4 exit states

    # Count transitions from each starting cell to each destination
    counts = np.zeros((n_states, n_states), dtype=int)

    for origin, dest in zip(pairs["origin_cell"], pairs["dest"]):
        counts[int(origin), int(dest)] += 1

    # Convert counts into probabilities
    P = np.zeros((n_states, n_states), dtype=float)

    row_totals = counts.sum(axis=1)
    supported = row_totals > 0

    P[supported] = (
        counts[supported] / row_totals[supported, None]
    )

    # Make the four exit states absorbing
    for state in range(234, 238):
        P[state, state] = 1.0

    return P, counts, row_totals


# Test the function
P, counts, row_totals = build_transition_matrix(pairs)

print("\nTRANSITION MATRIX CHECK")
print("Matrix shape:", P.shape)
print("Supported starting cells:", (row_totals[:234] > 0).sum())
print("Unsupported starting cells:", (row_totals[:234] == 0).sum())

# Check that all supported rows sum to 1
supported_rows = row_totals[:234] > 0
print(
    "Supported rows sum to 1:",
    np.allclose(P[:234][supported_rows].sum(axis=1), 1)
)

# Check absorbing exit states
print(
    "Exit states absorbing:",
    np.allclose(P[234:238, 234:238], np.eye(4))
)

# TASK 3: Whole-drifter bootstrap confidence intervals

def bootstrap_exit_probability(
    pairs,
    starting_cell,
    exit_state=234,
    n_bootstrap=500,
    seed=42
):
    rng = np.random.default_rng(seed)

    # Select pairs starting in the chosen cell
    cell_pairs = pairs[pairs["origin_cell"] == starting_cell].copy()

    # Identify distinct drifters contributing to that cell
    drifter_ids = cell_pairs["traj"].unique()

    if len(drifter_ids) < 2:
        raise ValueError("Not enough distinct drifters for bootstrapping.")

    # Store all destination outcomes for each drifter
    outcomes_by_drifter = {
        drifter: group["dest"].to_numpy()
        for drifter, group in cell_pairs.groupby("traj")
    }

    bootstrap_probs = []

    for _ in range(n_bootstrap):

        # Sample whole drifters WITH replacement
        sampled_ids = rng.choice(
            drifter_ids,
            size=len(drifter_ids),
            replace=True
        )

        total_pairs = 0
        exit_pairs = 0

        # Retain all pairs from each sampled drifter
        for drifter in sampled_ids:
            outcomes = outcomes_by_drifter[drifter]

            total_pairs += len(outcomes)
            exit_pairs += np.sum(outcomes == exit_state)

        bootstrap_probs.append(exit_pairs / total_pairs)

    bootstrap_probs = np.array(bootstrap_probs)

    # Original estimate using all supplied pairs
    original_prob = (
        (cell_pairs["dest"] == exit_state).sum()
        / len(cell_pairs)
    )

    # Percentile confidence interval
    lower, upper = np.percentile(
        bootstrap_probs, [2.5, 97.5]
    )

    return original_prob, lower, upper, bootstrap_probs


# Example: Starting cell 126, west exit (234)
estimate, lower, upper, bootstrap_samples = (
    bootstrap_exit_probability(
        pairs,
        starting_cell=126,
        exit_state=234,
        n_bootstrap=500
    )
)

print("\nBOOTSTRAP RESULTS")
print(f"Estimated west-exit probability: {estimate:.2%}")
print(f"95% bootstrap CI: [{lower:.2%}, {upper:.2%}]")


plt.hist(bootstrap_samples * 100, bins=25, edgecolor="black")

plt.axvline(estimate * 100, color="red", linestyle="--",
            label="Original estimate")

plt.axvline(lower * 100, color="green", linestyle=":",
            label="95% CI")

plt.axvline(upper * 100, color="green", linestyle=":")

plt.xlabel("Seven-day west-exit probability (%)")
plt.ylabel("Bootstrap frequency")
plt.title("Whole-drifter bootstrap: Starting Cell 126")
plt.legend()
plt.tight_layout()
plt.show()