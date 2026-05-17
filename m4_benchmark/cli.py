from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifacts import build_m4_artifact_folder
from .runner import run_single_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M4 steering benchmark")
    parser.add_argument("--true-path-seed", type=int, required=True)
    parser.add_argument("--attacker-path-seed", type=int, required=True)
    parser.add_argument("--stimulus-dim", type=int, choices=[1, 2, 4], required=True)
    parser.add_argument("--path-kind", choices=["polyline", "sine_mix"], default="polyline")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--policy-json", type=str, default="{}")
    parser.add_argument("--build-m4-artifacts", action="store_true")
    args = parser.parse_args()

    policy_params = json.loads(args.policy_json)
    run_single_benchmark(
        policy_params=policy_params,
        true_path_seed=args.true_path_seed,
        attacker_path_seed=args.attacker_path_seed,
        stimulus_dim=args.stimulus_dim,
        output_dir=args.output_dir,
        path_kind=args.path_kind,
    )
    if args.build_m4_artifacts:
        build_m4_artifact_folder(args.output_dir, best_attack_policy=policy_params)


if __name__ == "__main__":
    main()
