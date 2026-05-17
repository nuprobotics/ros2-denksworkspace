from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path

import numpy as np

from .metrics import compute_path_metrics
from .paths import PathData, generate_true_and_attacker_paths
from .policy import parse_policy_params, stimulus_at_time, stimulus_vector_to_attack_features
from .render import save_trajectory_overlay_png


@dataclass(frozen=True)
class InitialPose:
    x: float
    y: float
    heading: float


def _nearest_path_index(path: PathData, x: float, y: float, start_idx: int) -> int:
    search_end = min(len(path.x), start_idx + 25)
    points = np.column_stack((path.x[start_idx:search_end], path.y[start_idx:search_end]))
    dists = np.linalg.norm(points - np.array([[x, y]]), axis=1)
    return int(start_idx + np.argmin(dists))


def _controller_step(path: PathData, x: float, y: float, heading: float, base_speed: float, attack_features: dict[str, float], path_idx: int) -> tuple[float, float, int]:
    idx = _nearest_path_index(path, x, y, path_idx)
    lookahead_idx = min(len(path.x) - 1, idx + 8)
    target_x = path.x[lookahead_idx]
    target_y = path.y[lookahead_idx]
    dx = target_x - x
    dy = target_y - y

    tangent = np.array([math.cos(path.heading[idx]), math.sin(path.heading[idx])])
    normal = np.array([-tangent[1], tangent[0]])
    lateral_error = float(np.dot(np.array([x - path.x[idx], y - path.y[idx]]), normal))

    desired_heading = math.atan2(dy, dx)
    heading_error = math.atan2(math.sin(desired_heading - heading), math.cos(desired_heading - heading))
    attacked_lateral_error = lateral_error - attack_features["line_offset_m"]
    attacked_heading_error = heading_error + attack_features["heading_bias_rad"]

    steering = 1.35 * attacked_heading_error - 1.10 * attacked_lateral_error + attack_features["steering_bias_rad"]
    steering = float(np.clip(steering, -0.9, 0.9))

    speed = base_speed * (1.0 + attack_features["speed_scale_delta"])
    speed = float(np.clip(speed, 0.05, 0.45))
    return speed, steering, idx


def _simulate(
    true_path: PathData,
    attacker_path: PathData,
    policy_params: dict | None,
    stimulus_dim: int,
    initial_pose: InitialPose,
    steps: int = 220,
    dt: float = 0.1,
) -> dict[str, object]:
    if stimulus_dim not in (1, 2, 4):
        raise ValueError("stimulus_dim must be one of 1, 2, or 4")

    policy = parse_policy_params(policy_params, stimulus_dim)
    wheelbase = 0.12
    base_speed = 0.26
    x = initial_pose.x
    y = initial_pose.y
    heading = initial_pose.heading
    path_idx = 0

    trajectory_rows = []
    stimulus_rows = []
    motor_rows = []

    for step in range(steps):
        time_s = step * dt
        stimulus = stimulus_at_time(policy, time_s)
        attack_features = stimulus_vector_to_attack_features(stimulus)
        speed, steering, path_idx = _controller_step(true_path, x, y, heading, base_speed, attack_features, path_idx)

        heading += (speed / wheelbase) * math.tan(steering) * dt
        x += speed * math.cos(heading) * dt
        y += speed * math.sin(heading) * dt

        left_motor = float(np.clip(speed - 0.5 * steering * wheelbase, -1.0, 1.0))
        right_motor = float(np.clip(speed + 0.5 * steering * wheelbase, -1.0, 1.0))

        trajectory_rows.append(
            {
                "step": step,
                "time_s": time_s,
                "x": x,
                "y": y,
                "heading": heading,
                "true_path_index": path_idx,
            }
        )
        stimulus_row = {"step": step, "time_s": time_s}
        for idx, value in enumerate(stimulus):
            stimulus_row[f"u{idx}"] = float(value)
        stimulus_rows.append(stimulus_row)
        motor_rows.append(
            {
                "step": step,
                "time_s": time_s,
                "speed_command": speed,
                "steering_command": steering,
                "left_motor": left_motor,
                "right_motor": right_motor,
            }
        )

    trajectory_xy = np.array([[row["x"], row["y"]] for row in trajectory_rows], dtype=float)
    metrics = compute_path_metrics(trajectory_xy=trajectory_xy, true_path=true_path, attacker_path=attacker_path)
    metrics.update(
        {
            "primary_metric": "hijack_score",
            "backup_metric": "mean_abs_true_path_error",
            "stimulus_dim": stimulus_dim,
            "true_path_seed": true_path.seed,
            "attacker_path_seed": attacker_path.seed,
            "initial_pose": asdict(initial_pose),
            "attack_adapter": "experiment_local_vector_to_line_heading_speed_steering",
        }
    )
    return {
        "trajectory_rows": trajectory_rows,
        "stimulus_rows": stimulus_rows,
        "motor_rows": motor_rows,
        "metrics": metrics,
        "trajectory_xy": trajectory_xy,
    }


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _path_rows(path: PathData) -> list[dict[str, float]]:
    rows = []
    for idx in range(len(path.x)):
        rows.append(
            {
                "index": idx,
                "x": float(path.x[idx]),
                "y": float(path.y[idx]),
                "heading": float(path.heading[idx]),
                "curvature": float(path.curvature[idx]),
            }
        )
    return rows


def run_single_benchmark(
    policy_params: dict | None,
    true_path_seed: int,
    attacker_path_seed: int,
    stimulus_dim: int,
    output_dir: str | Path | None = None,
    path_kind: str = "polyline",
) -> dict[str, object]:
    true_path, attacker_path = generate_true_and_attacker_paths(
        true_path_seed=true_path_seed,
        attacker_path_seed=attacker_path_seed,
        kind=path_kind,
    )
    initial_pose = InitialPose(
        x=float(true_path.x[0]),
        y=float(true_path.y[0]),
        heading=float(true_path.heading[0]),
    )
    results = _simulate(
        true_path=true_path,
        attacker_path=attacker_path,
        policy_params=policy_params,
        stimulus_dim=stimulus_dim,
        initial_pose=initial_pose,
    )

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        _write_csv(output_path / "true_path.csv", _path_rows(true_path), ["index", "x", "y", "heading", "curvature"])
        _write_csv(output_path / "attacker_path.csv", _path_rows(attacker_path), ["index", "x", "y", "heading", "curvature"])
        _write_csv(output_path / "trajectory.csv", results["trajectory_rows"], ["step", "time_s", "x", "y", "heading", "true_path_index"])
        stimulus_fields = ["step", "time_s"] + [f"u{idx}" for idx in range(stimulus_dim)]
        _write_csv(output_path / "stimulus.csv", results["stimulus_rows"], stimulus_fields)
        _write_csv(
            output_path / "motor_commands.csv",
            results["motor_rows"],
            ["step", "time_s", "speed_command", "steering_command", "left_motor", "right_motor"],
        )
        with (output_path / "metrics.json").open("w", encoding="utf-8") as handle:
            json.dump(results["metrics"], handle, indent=2)
        save_trajectory_overlay_png(
            output_path / "trajectory_overlay.png",
            true_path=true_path,
            attacker_path=attacker_path,
            trajectory_xy=results["trajectory_xy"],
        )

    return {
        "true_path": true_path,
        "attacker_path": attacker_path,
        **results,
    }


def evaluate_attack_policy(
    policy_params: dict | None,
    true_path_seed: int,
    attacker_path_seed: int,
    stimulus_dim: int,
    output_dir: str | Path | None = None,
    path_kind: str = "polyline",
) -> float:
    results = run_single_benchmark(
        policy_params=policy_params,
        true_path_seed=true_path_seed,
        attacker_path_seed=attacker_path_seed,
        stimulus_dim=stimulus_dim,
        output_dir=output_dir,
        path_kind=path_kind,
    )
    return float(results["metrics"]["hijack_score"])
