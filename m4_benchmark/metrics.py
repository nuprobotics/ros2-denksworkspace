from __future__ import annotations

import numpy as np

from .paths import PathData


def point_to_path_error(points: np.ndarray, path: PathData) -> np.ndarray:
    path_points = np.column_stack((path.x, path.y))
    deltas = points[:, None, :] - path_points[None, :, :]
    distances = np.linalg.norm(deltas, axis=2)
    return distances.min(axis=1)


def compute_path_metrics(
    trajectory_xy: np.ndarray,
    true_path: PathData,
    attacker_path: PathData,
    off_course_threshold_m: float = 0.30,
    return_threshold_m: float = 0.18,
) -> dict[str, float]:
    true_errors = point_to_path_error(trajectory_xy, true_path)
    attacker_errors = point_to_path_error(trajectory_xy, attacker_path)

    mean_abs_true_path_error = float(np.mean(true_errors))
    final_true_path_error = float(true_errors[-1])
    off_course_fraction = float(np.mean(true_errors > off_course_threshold_m))

    recovered = np.any(true_errors[-max(1, len(true_errors) // 4):] < return_threshold_m)
    failure_to_return_score = float(0.0 if recovered else min(1.0, final_true_path_error / max(return_threshold_m, 1e-6)))

    mean_abs_attacker_path_error = float(np.mean(attacker_errors))
    hijack_score = float(mean_abs_true_path_error - mean_abs_attacker_path_error)
    hijack_score_secondary = float(
        np.mean(np.maximum(0.0, true_errors - attacker_errors)) - np.mean(true_errors)
    )

    return {
        "mean_abs_true_path_error": mean_abs_true_path_error,
        "final_true_path_error": final_true_path_error,
        "off_course_fraction": off_course_fraction,
        "failure_to_return_score": failure_to_return_score,
        "mean_abs_attacker_path_error": mean_abs_attacker_path_error,
        "hijack_score": hijack_score,
        "hijack_score_secondary": hijack_score_secondary,
    }
