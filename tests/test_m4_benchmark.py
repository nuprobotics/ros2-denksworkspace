from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from m4_benchmark import evaluate_attack_policy, generate_random_duckiebot_path


class M4BenchmarkTests(unittest.TestCase):
    def test_generate_random_duckiebot_path_outputs_expected_fields(self) -> None:
        path = generate_random_duckiebot_path(seed=0, kind="polyline")
        self.assertEqual(set(path.keys()), {"x", "y", "heading", "curvature"})
        self.assertEqual(len(path["x"]), len(path["y"]))
        self.assertEqual(len(path["x"]), len(path["heading"]))
        self.assertEqual(len(path["x"]), len(path["curvature"]))

    def test_evaluate_attack_policy_writes_4d_stimulus_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            score = evaluate_attack_policy(
                policy_params={"bias": [0.1, -0.1, 0.2, 0.0]},
                true_path_seed=2,
                attacker_path_seed=102,
                stimulus_dim=4,
                output_dir=tmp_dir,
            )
            self.assertIsInstance(score, float)
            stimulus_path = Path(tmp_dir) / "stimulus.csv"
            self.assertTrue(stimulus_path.exists())
            with stimulus_path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                first_row = next(reader)
            for key in ("u0", "u1", "u2", "u3"):
                self.assertIn(key, first_row)


if __name__ == "__main__":
    unittest.main()
