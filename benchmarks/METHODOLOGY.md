# Benchmark Methodology

## Hardware baseline
- **GPU:** NVIDIA GeForce RTX 4070 (laptop/desktop local node)
- **Host:** Linux (WSL2-capable environment)
- **Runtime:** Ollama local OpenAI-compatible API (`localhost:11434`)

## What is measured
`grid_cli.py` records Ollama generation telemetry into SQLite:

| Field | Meaning |
|-------|---------|
| `decode_tps` | Pure decode tokens/sec from Ollama `eval_count / eval_duration` |
| `prefill_tps` | Prompt eval tokens/sec |
| `load_ms` | Model weight load duration |
| `wall_time_sec` | End-to-end wall clock including stream overhead |

## Representative results (checked into `sample_*.json`)

### Decode-path improvement (same prompt length, 150 predict tokens)

| Run | Model | Decode tok/s | Wall sec | Notes |
|-----|-------|-------------:|---------:|-------|
| 1 | `qwen3:8b` | **1.39** | 106.65 | early baseline |
| 2 | `qwen-gpu:latest` | **29.68** | 11.23 | GPU-routed |
| 5 | `qwen-gpu:latest` | **37.47** | 5.03 | stabilized |

**Observed decode uplift:** 1.39 → 37.47 tok/s ≈ **27×** on the decode metric for this series.

### Stream wall-clock suite (`grid_benchmark.py`)
Three consecutive 400-token runs on `qwen3:8b` landed at **75.8–77.3 tok/s** wall-eval throughput once the stack was warm.

## How to reproduce
```bash
# requires a running Ollama with at least one model
python3 grid_cli.py --list-models
python3 grid_cli.py -m qwen -t 150 --db ./logs/grid_telemetry.db
python3 grid_benchmark.py
python3 grid_reporter.py -l 10 --db ./logs/grid_telemetry.db -o ./logs/report.pdf
```

## Honesty notes
- Numbers are **local single-node** results, not multi-node cluster claims.
- Throughput depends on model, quantization, context, GPU load, and Ollama version.
- Sample JSON is a redacted export of real local runs from 2026-07-27, not synthetic marketing data.
