from __future__ import annotations

import csv
import json
from pathlib import Path

from .runner import run_single_benchmark


def run_seed_sweep(
    seeds: list[int],
    attacker_seed_offset: int,
    stimulus_dim: int,
    output_root: str | Path,
    path_kind: str = "polyline",
    policy_params: dict | None = None,
) -> Path:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    for seed in seeds:
        run_dir = output_root / f"seed_{seed}"
        results = run_single_benchmark(
            policy_params=policy_params,
            true_path_seed=seed,
            attacker_path_seed=seed + attacker_seed_offset,
            stimulus_dim=stimulus_dim,
            output_dir=run_dir,
            path_kind=path_kind,
        )
        summary_rows.append(results["metrics"])

    summary_path = output_root / "results_summary.csv"
    fieldnames = sorted(summary_rows[0].keys()) if summary_rows else []
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    (output_root / "policy.json").write_text(json.dumps(policy_params or {}, indent=2) + "\n", encoding="utf-8")
    return summary_path
