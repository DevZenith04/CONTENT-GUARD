# ContentGuard 🛡️

[![CI](https://github.com/DevZenith04/CONTENT-GUARD/actions/workflows/ci.yml/badge.svg)](https://github.com/DevZenith04/CONTENT-GUARD/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/Coverage-92%25-brightgreen.svg)](Makefile)

ContentGuard is a production-grade, human-in-the-loop content moderation system combining high-throughput rule engines and HuggingFace Transformers (`unitary/toxic-bert`), powered by FastAPI and asynchronous SQLite storage.

---

## 📊 Measured Benchmark Results

Evaluated on an independent, stratified dataset (50 annotated items covering benign idioms, lethal threats, targeted harassment, dehumanizing hate speech, and crisis self-harm expressions):

| Moderation Mode | Review Rate | Median Latency | Threat F1 | Harassment F1 | Hate F1 | Self-Harm F1 |
|-----------------|-------------|----------------|-----------|---------------|---------|--------------|
| **Rule-Only**   | 40.0%       | < 1 ms         | 0.706     | 0.519         | 0.857   | 0.909        |
| **LLM-Only**    | 32.0%       | 24 ms          | 0.762     | 0.708         | 0.667   | 0.833        |
| **Hybrid**      | **36.0%**   | **26 ms**      | **0.762** | **0.708**     | **0.857**| **0.833**   |

> Full evaluation methodology, category/outcome scoring equations, and ablation benchmarks are documented in [docs/EVALUATION.md](docs/EVALUATION.md).

---

## 🔍 Category Capabilities & Limits

| Category | What it Detects | What it Misses / Excludes |
|---|---|---|
| **Threat** | Direct first-person lethal threats, conditional extortion, weapons violence | Idioms ("kill it at interview"), gaming references ("destroy final boss") |
| **Harassment** | Targeted derogatory abuse, severe expletives directed at individuals | Literal household usage ("take out the trash"), untargeted profanity |
| **Hate Speech** | Group dehumanization, animalistic slurs, exclusion incitement | Discussion of historical discrimination, self-affirming identity statements |
| **Self-Harm** | Direct suicidal intent and self-injury ideation (*Routed to review; never auto-blocked*) | Colloquial expressions ("feet are killing me", "dying of laughter") |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- `pip` / `venv`

### Installation & Run

1. **Clone the repository**:
   ```bash
   git clone https://github.com/DevZenith04/CONTENT-GUARD.git
   cd CONTENT-GUARD
   ```

2. **Start the application**:
   ```bash
   ./start.sh
   # Or using Make:
   make run
   ```

The script configures the virtual environment, verifies dependencies, and boots the Uvicorn server on port `8001`.

### Web Interfaces & Endpoints

- **Workbench**: [http://localhost:8001/](http://localhost:8001/)
- **Review Queue**: [http://localhost:8001/review.html](http://localhost:8001/review.html)
- **Event Audit**: [http://localhost:8001/event.html](http://localhost:8001/event.html)
- **Evaluation Dashboard**: [http://localhost:8001/evaluation.html](http://localhost:8001/evaluation.html)
- **API Swagger Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 🧪 Testing & Evaluation

```bash
# Run pytest test suite with 92% coverage:
make test

# Run offline benchmark evaluation runner:
make eval

# Run linter:
make lint
```

---

## 📚 Documentation & Architecture Decision Records (ADRs)

- [docs/EVALUATION.md](docs/EVALUATION.md): Formal evaluation framework, scoring formulas, and ablation studies.
- [docs/LABELLING.md](docs/LABELLING.md): Data annotation guide, edge-case disambiguation, and agreement protocols.
- **Architecture Decision Records**:
  - [ADR 0001: Hybrid Rules Plus Transformer Architecture](docs/adr/0001-hybrid-rules-plus-model.md)
  - [ADR 0002: SQLite for Event & Review Persistence](docs/adr/0002-sqlite-for-storage.md)
  - [ADR 0003: YAML Policy Specification as Configuration](docs/adr/0003-yaml-policy-as-data.md)
  - [ADR 0004: Routing Self-Harm Content to Review Instead of Auto-Block](docs/adr/0004-do-not-autoblock-self-harm.md)
  - [ADR 0005: Choice of unitary/toxic-bert for Local Inference](docs/adr/0005-choice-of-toxic-bert.md)
  - [ADR 0006: Outcome-Level & Category-Level Evaluation Metrics](docs/adr/0006-outcome-level-scoring-definitions.md)

---

## 📁 Repository Structure

```
├── .github/workflows/ci.yml # GitHub Actions CI workflow
├── assets/                  # CSS stylesheets and theme
├── backend/
│   ├── config/              # YAML rules and policy configuration
│   ├── engine/              # Rule engine, transformer LLM analyzer, decision cascade
│   ├── evaluation/          # Evaluation runner & stratified evaluation datasets
│   ├── models/              # Pydantic data schemas and enums
│   ├── results/             # Reproducible evaluation JSON artifacts
│   ├── routes/              # FastAPI endpoints (/moderate, /reviews, /evaluation)
│   ├── storage/             # Async SQLite persistence layer
│   ├── tests/               # Comprehensive pytest suite
│   ├── config.py            # Environment settings
│   ├── main.py              # Application factory and lifecycle
│   ├── requirements.txt     # Base dependencies
│   ├── requirements.lock    # Pinned dependencies
│   └── requirements-dev.txt # Test and lint dependencies
├── docs/                    # Annotation guides, evaluation protocol, and ADRs
├── js/                      # Frontend application scripts
├── pages/                   # HTML workbench, review, audit, & eval interfaces
├── Makefile                 # Automation shortcuts (run, test, eval, lint)
├── start.sh                 # Application startup script
└── LICENSE                  # MIT License
```

## 📄 License

MIT
