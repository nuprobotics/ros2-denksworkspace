# M4 Benchmark

Experiment-local pure-Python steering benchmark for random true paths, attacker paths, and bounded vector stimuli.

Exposed API:

- `generate_random_duckiebot_path(seed, kind="polyline" | "sine_mix")`
- `evaluate_attack_policy(policy_params, true_path_seed, attacker_path_seed, stimulus_dim, output_dir=None)`
- `run_seed_sweep(seeds=[0,1,2], attacker_seed_offset=100, stimulus_dim=4, output_root=...)`

Example:

```bash
python3 -m m4_benchmark.cli \
  --true-path-seed 0 \
  --attacker-path-seed 100 \
  --stimulus-dim 4 \
  --output-dir /tmp/m4_run \
  --policy-json '{"bias":[0.2,-0.1,0.0,0.1],"amplitude":[0.1,0.2,0.0,0.1]}'
```

Saved artifacts per run:

- `true_path.csv`
- `attacker_path.csv`
- `trajectory.csv`
- `stimulus.csv`
- `motor_commands.csv`
- `metrics.json`
- `trajectory_overlay.png`
