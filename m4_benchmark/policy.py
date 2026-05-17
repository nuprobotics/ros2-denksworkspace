from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


def _clip_unit(value: float) -> float:
    return float(np.clip(value, -1.0, 1.0))


@dataclass(frozen=True)
class PolicySpec:
    bias: np.ndarray
    amplitude: np.ndarray
    frequency: np.ndarray
    phase: np.ndarray


def parse_policy_params(policy_params: dict | None, stimulus_dim: int) -> PolicySpec:
    policy_params = policy_params or {}

    def _vector(name: str, default: float) -> np.ndarray:
        value = policy_params.get(name, default)
        if np.isscalar(value):
            arr = np.full(stimulus_dim, float(value), dtype=float)
        else:
            arr = np.asarray(value, dtype=float)
            if arr.shape != (stimulus_dim,):
                raise ValueError(f"policy_params['{name}'] must have shape ({stimulus_dim},)")
        return np.clip(arr, -1.0, 1.0)

    bias = _vector("bias", 0.0)
    amplitude = np.clip(np.abs(_vector("amplitude", 0.0)), 0.0, 1.0)
    frequency = np.asarray(policy_params.get("frequency", np.linspace(0.2, 0.7, stimulus_dim)), dtype=float)
    if frequency.shape == ():
        frequency = np.full(stimulus_dim, float(frequency), dtype=float)
    if frequency.shape != (stimulus_dim,):
        raise ValueError(f"policy_params['frequency'] must have shape ({stimulus_dim},)")
    phase = np.asarray(policy_params.get("phase", np.zeros(stimulus_dim)), dtype=float)
    if phase.shape == ():
        phase = np.full(stimulus_dim, float(phase), dtype=float)
    if phase.shape != (stimulus_dim,):
        raise ValueError(f"policy_params['phase'] must have shape ({stimulus_dim},)")
    return PolicySpec(bias=bias, amplitude=amplitude, frequency=frequency, phase=phase)


def stimulus_at_time(policy: PolicySpec, time_s: float) -> np.ndarray:
    signal = policy.bias + policy.amplitude * np.sin(2.0 * math.pi * policy.frequency * time_s + policy.phase)
    return np.clip(signal, -1.0, 1.0)


def stimulus_vector_to_attack_features(stimulus: np.ndarray) -> dict[str, float]:
    if stimulus.shape == (1,):
        values = np.array([stimulus[0], 0.0, 0.0, 0.0], dtype=float)
    elif stimulus.shape == (2,):
        values = np.array([stimulus[0], stimulus[1], 0.0, 0.0], dtype=float)
    elif stimulus.shape == (4,):
        values = stimulus
    else:
        raise ValueError(f"Unsupported stimulus shape {stimulus.shape}; expected 1, 2, or 4")

    return {
        "line_offset_m": _clip_unit(values[0]) * 0.18,
        "heading_bias_rad": _clip_unit(values[1]) * 0.28,
        "speed_scale_delta": _clip_unit(values[2]) * 0.20,
        "steering_bias_rad": _clip_unit(values[3]) * 0.22,
    }
