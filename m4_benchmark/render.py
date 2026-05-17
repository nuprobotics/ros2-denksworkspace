from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw
import numpy as np

from .paths import PathData


def save_trajectory_overlay_png(
    output_path: str | Path,
    true_path: PathData,
    attacker_path: PathData,
    trajectory_xy: np.ndarray,
    width: int = 1280,
    height: int = 720,
) -> None:
    output_path = Path(output_path)
    img = Image.new("RGB", (width, height), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)

    all_points = np.vstack(
        [
            np.column_stack((true_path.x, true_path.y)),
            np.column_stack((attacker_path.x, attacker_path.y)),
            trajectory_xy,
        ]
    )
    min_xy = all_points.min(axis=0)
    max_xy = all_points.max(axis=0)
    span = np.maximum(max_xy - min_xy, 1e-6)
    padding = np.array([0.6, 0.6])
    min_xy -= padding
    max_xy += padding
    span = max_xy - min_xy

    def project(points: np.ndarray) -> list[tuple[int, int]]:
        norm = (points - min_xy) / span
        px = norm[:, 0] * (width - 80) + 40
        py = (1.0 - norm[:, 1]) * (height - 80) + 40
        return [(int(x), int(y)) for x, y in np.column_stack((px, py))]

    true_pts = project(np.column_stack((true_path.x, true_path.y)))
    attacker_pts = project(np.column_stack((attacker_path.x, attacker_path.y)))
    traj_pts = project(trajectory_xy)

    draw.line(true_pts, fill=(44, 110, 216), width=5)
    draw.line(attacker_pts, fill=(214, 76, 76), width=5)
    draw.line(traj_pts, fill=(31, 31, 31), width=4)

    for label, color, pos in [
        ("true", (44, 110, 216), (40, 20)),
        ("attacker", (214, 76, 76), (140, 20)),
        ("trajectory", (31, 31, 31), (290, 20)),
    ]:
        x, y = pos
        draw.rectangle((x, y + 8, x + 28, y + 18), fill=color)
        draw.text((x + 36, y), label, fill=(20, 20, 20))

    img.save(output_path)
