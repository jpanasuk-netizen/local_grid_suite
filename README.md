# Local Grid Suite

**Local LLM telemetry, routing, and operator tooling for a single-node GPU lab.**

Built during an independent engineering year (Aug 2024 – present) to turn a personal NVIDIA box into a measurable local AI platform — not a toy demo folder.

[![Python](https://img.shields.io/badge/Python-3.10+-blue)]()
[![Ollama](https://img.shields.io/badge/Backend-Ollama-green)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]()

---

## Why this exists

Enterprise data platforms taught me to measure before claiming. This suite applies that habit to local LLMs:

1. **Discover** available models on a local Ollama host  
2. **Benchmark** decode / prefill / wall-clock throughput  
3. **Persist** runs to SQLite  
4. **Report** operator-readable summaries (CLI + optional PDF)  
5. **Stress / mesh** helpers for VRAM and multi-process experiments  

Companion stack: the full Dockerized app layer lives in [`tabby-tavern-stack`](https://github.com/jpanasuk-netizen/tabby-tavern-stack) and on [Hugging Face](https://huggingface.co/jpanasuk/tabby-tavern-stack).

---

## Headline result (measured)

From checked-in sample telemetry (`benchmarks/sample_hardware_runs.json`):

| Stage | Model | Decode tok/s |
|------:|-------|-------------:|
| Baseline | `qwen3:8b` | **1.39** |
| GPU-routed | `qwen-gpu:latest` | **29.7 – 39.3** |
| Stabilized | `qwen-gpu:latest` | **37.47** |

→ **~27× decode uplift** on that run series after GPU routing/tuning.

Warm stream suite on `qwen3:8b`: **~76 tok/s** (400-token runs).  
Full methodology: [`benchmarks/METHODOLOGY.md`](benchmarks/METHODOLOGY.md).

---

## Quick start

```bash
git clone https://github.com/jpanasuk-netizen/local_grid_suite.git
cd local_grid_suite
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Ollama must be running locally
export OLLAMA_HOST=http://localhost:11434

python3 grid_cli.py --list-models
python3 grid_cli.py -m qwen -t 150
python3 grid_reporter.py -l 10
```

Optional PDF export (needs `reportlab`):

```bash
python3 grid_reporter.py -l 20 -o ./logs/grid_performance_report.pdf
```

---

## Tool map

| Script | Role |
|--------|------|
| `grid_cli.py` | Primary portable runner — model discovery, timed generate, SQLite insert |
| `grid_benchmark.py` | Multi-iteration stream benchmark + JSON history |
| `grid_manager.py` | Parameter sweep (temp / top_p / max tokens) with monitor agent |
| `grid_reporter.py` | Query/filter telemetry DB; optional PDF + email dispatch |
| `grid_full_telemetry_suite.py` | Broader multi-probe suite |
| `grid_live_meter.py` | Live throughput meter |
| `grid_vram_stress.py` | VRAM pressure helper |
| `grid_mesh_daemon.py` / `mesh_router.py` | Lightweight mesh / routing experiments |
| `core_engine.py` | Local code-gen loop against Ollama (self-heal retries) |

Defaults write under `./logs` relative to the repo (no hardcoded home paths in the published tree).

---

## Architecture

```text
                  ┌─────────────────────┐
                  │   Operator (CLI)    │
                  └──────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   grid_cli.py        grid_benchmark.py   grid_manager.py
   (discover+run)     (stream suite)      (param sweep)
          │                  │                  │
          └────────────┬─────┴────────┬─────────┘
                       ▼              ▼
                 Ollama HTTP API   SQLite / JSON logs
                       │
                       ▼
                 Local GPU model
```

---

## Repository layout

```text
local_grid_suite/
├── README.md
├── requirements.txt
├── benchmarks/
│   ├── METHODOLOGY.md
│   ├── sample_hardware_runs.json
│   └── sample_stream_runs.json
├── grid_cli.py
├── grid_benchmark.py
├── grid_manager.py
├── grid_reporter.py
└── ... supporting probes
```

---

## What this is / is not

**Is:** a practical operator toolkit from a real local lab year.  
**Is not:** a multi-cloud inference product, a training framework, or a claim of SOTA tokens/sec.

If you are evaluating the independent-work year on a resume, start here + the Tabby Tavern stack.

---

## Author

**Jeremy Panasuk** — enterprise data/Informatica background; 2024–present independent local AI systems work.  
GitHub: [@jpanasuk-netizen](https://github.com/jpanasuk-netizen) · HF: [jpanasuk](https://huggingface.co/jpanasuk)

## License

MIT
