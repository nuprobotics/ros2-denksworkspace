from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from PIL import Image


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copy2(src, dst)


def _stack_images_horizontally(left: Path, right: Path, output: Path) -> None:
    if not left.exists() or not right.exists():
        return
    left_img = Image.open(left)
    right_img = Image.open(right)
    canvas = Image.new("RGB", (left_img.width + right_img.width, max(left_img.height, right_img.height)), (255, 255, 255))
    canvas.paste(left_img, (0, 0))
    canvas.paste(right_img, (left_img.width, 0))
    canvas.save(output)


def build_m4_artifact_folder(
    benchmark_run_dir: str | Path,
    best_attack_policy: dict,
    baseline_run_dir: str | Path | None = None,
    output_dir: str | Path = "artifacts/milestones/m4_blackbox_search",
) -> Path:
    benchmark_run_dir = Path(benchmark_run_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = benchmark_run_dir / "metrics.json"
    metrics = {}
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    with (output_dir / "results.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = sorted(metrics.keys()) if metrics else ["status"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(metrics if metrics else {"status": "missing_metrics"})

    with (output_dir / "best_attack_policy.json").open("w", encoding="utf-8") as handle:
        json.dump(best_attack_policy, handle, indent=2)

    _copy_if_exists(benchmark_run_dir / "trajectory_overlay.png", output_dir / "trajectory_overlay.png")
    comparison_left = Path(baseline_run_dir) / "trajectory_overlay.png" if baseline_run_dir else benchmark_run_dir / "trajectory_overlay.png"
    comparison_right = benchmark_run_dir / "trajectory_overlay.png"
    _stack_images_horizontally(comparison_left, comparison_right, output_dir / "comparison.png")

    readme = [
        "# M4 Blackbox Search",
        "",
        "This artifact folder was generated from the experiment-local pure-Python steering benchmark.",
        "",
        "Included files:",
        "- `results.csv`: single-run metric summary",
        "- `comparison.png`: side-by-side baseline/attack overlay when a baseline run is provided",
        "- `trajectory_overlay.png`: true path, attacker path, and realized trajectory",
        "- `best_attack_policy.json`: policy parameters used for the run",
    ]
    (output_dir / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    return output_dir
