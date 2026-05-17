from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class PathData:
    x: np.ndarray
    y: np.ndarray
    heading: np.ndarray
    curvature: np.ndarray
    seed: int
    kind: str


def _resample_polyline(points: np.ndarray, sample_count: int) -> np.ndarray:
    deltas = np.diff(points, axis=0)
    lengths = np.linalg.norm(deltas, axis=1)
    cumulative = np.concatenate([[0.0], np.cumsum(lengths)])
    total_length = cumulative[-1]
    if total_length <= 1e-9:
        return np.repeat(points[:1], sample_count, axis=0)
    targets = np.linspace(0.0, total_length, sample_count)
    x = np.interp(targets, cumulative, points[:, 0])
    y = np.interp(targets, cumulative, points[:, 1])
    return np.column_stack((x, y))


def _smooth_heading(heading: np.ndarray) -> np.ndarray:
    return np.unwrap(heading)


def _compute_heading_and_curvature(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dx = np.gradient(x)
    dy = np.gradient(y)
    heading = _smooth_heading(np.arctan2(dy, dx))
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    denom = np.power(dx * dx + dy * dy, 1.5)
    curvature = np.divide(dx * ddy - dy * ddx, denom, out=np.zeros_like(dx), where=denom > 1e-9)
    return heading, curvature


def _polyline_path(rng: np.random.Generator, sample_count: int) -> np.ndarray:
    anchors = 9
    xs = np.linspace(0.0, 6.0, anchors)
    ys = rng.uniform(-1.0, 1.0, size=anchors)
    ys[0] = 0.0
    ys[-1] = rng.uniform(-0.25, 0.25)
    points = np.column_stack((xs, ys))
    return _resample_polyline(points, sample_count)


def _sine_mix_path(rng: np.random.Generator, sample_count: int) -> np.ndarray:
    x = np.linspace(0.0, 6.0, sample_count)
    amp1 = rng.uniform(0.25, 0.55)
    amp2 = rng.uniform(0.08, 0.22)
    freq1 = rng.uniform(0.8, 1.4)
    freq2 = rng.uniform(1.6, 2.8)
    phase1 = rng.uniform(-math.pi, math.pi)
    phase2 = rng.uniform(-math.pi, math.pi)
    y = amp1 * np.sin(freq1 * x + phase1) + amp2 * np.sin(freq2 * x + phase2)
    y -= y[0]
    return np.column_stack((x, y))


def _make_path(seed: int, kind: str, sample_count: int) -> PathData:
    rng = np.random.default_rng(seed)
    if kind == "polyline":
        points = _polyline_path(rng, sample_count)
    elif kind == "sine_mix":
        points = _sine_mix_path(rng, sample_count)
    else:
        raise ValueError(f"Unsupported path kind: {kind}")
    x = points[:, 0]
    y = points[:, 1]
    heading, curvature = _compute_heading_and_curvature(x, y)
    return PathData(x=x, y=y, heading=heading, curvature=curvature, seed=seed, kind=kind)


def _laterally_offset_path(path: PathData, offset_m: float, seed: int) -> PathData:
    normal_x = -np.sin(path.heading)
    normal_y = np.cos(path.heading)
    x = path.x + offset_m * normal_x
    y = path.y + offset_m * normal_y
    heading, curvature = _compute_heading_and_curvature(x, y)
    return PathData(x=x, y=y, heading=heading, curvature=curvature, seed=seed, kind=f"{path.kind}_offset")


def generate_random_duckiebot_path(seed: int, kind: str = "polyline", sample_count: int = 240) -> dict[str, np.ndarray]:
    path = _make_path(seed=seed, kind=kind, sample_count=sample_count)
    return {
        "x": path.x.copy(),
        "y": path.y.copy(),
        "heading": path.heading.copy(),
        "curvature": path.curvature.copy(),
    }


def generate_true_and_attacker_paths(
    true_path_seed: int,
    attacker_path_seed: int,
    kind: str = "polyline",
    sample_count: int = 240,
) -> tuple[PathData, PathData]:
    true_path = _make_path(seed=true_path_seed, kind=kind, sample_count=sample_count)
    offset_rng = np.random.default_rng(attacker_path_seed)
    offset_sign = -1.0 if offset_rng.random() < 0.5 else 1.0
    offset_magnitude = offset_rng.uniform(0.35, 0.65)
    attacker_path = _laterally_offset_path(true_path, offset_sign * offset_magnitude, attacker_path_seed)
    return true_path, attacker_path
