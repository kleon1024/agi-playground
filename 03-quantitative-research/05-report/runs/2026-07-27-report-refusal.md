# Report verdict branches

- Command: `uv run python 03-quantitative-research/05-report/core/report.py`; then the same command with `--artifact 03-quantitative-research/05-report/core/fixtures/complete_met.json` and `--artifact 03-quantitative-research/05-report/core/fixtures/complete_breached.json`.
- Hardware: local macOS lane
- Software: Python via uv; standard library
- Wall-clock: under one second total
- Cost: \$0 (local lane)
- Metrics: the actual mission-state path returned `CANNOT DETERMINE` and named 18 missing inputs. The hand-authored, explicitly synthetic fixtures exercised `MET` and `NOT MET`; the breached fixture failed the deflated-Sharpe veto.
- Notes: fixture figures are test data, not mission outcomes. The only real current-state conclusion is cannot determine.
