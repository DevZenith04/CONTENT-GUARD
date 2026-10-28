# ContentGuard 🛡️

ContentGuard is an automated and human-in-the-loop content moderation system powered by rule-based heuristic engines and HuggingFace Transformer models (`unitary/toxic-bert`), backed by FastAPI and SQLite.

## ✨ Features

- **Hybrid Moderation Pipeline**:
  - **Rule-based**: Fast regex / heuristic pattern matching for immediate filtering.
  - **Transformer LLM**: Deep contextual classification using toxic-bert for toxicity, threats, insults, and hate speech.
  - **Decision Engine**: Combines rule and model signals with configurable severity thresholds.
- **Human-in-the-Loop Review Queue**: Flagged content can be queued for manual reviewer override and decision logging.
- **Audit & Event Tracking**: Async SQLite-backed audit trails for all moderation queries and resolution outcomes.
- **Evaluation Workbench**: Test prompts, run benchmark evaluations, and calibrate model/rule sensitivity.
- **Interactive UI**: Clean, responsive frontend workbench, review dashboard, and evaluation tool.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- `pip` / `venv`

### Installation & Run

1. Clone the repository:
   ```bash
   git clone https://github.com/DevZenith04/CONTENT-GUARD.git
   cd CONTENT-GUARD
   ```

2. Make the startup script executable and run:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

The script will automatically activate or set up the virtual environment, install requirements if needed, and start the Uvicorn server on port `8001`.

### Endpoints & Web UI

Once started, access the application in your browser:
- **Workbench**: [http://localhost:8001/](http://localhost:8001/)
- **Review Queue**: [http://localhost:8001/review.html](http://localhost:8001/review.html)
- **Event Audit**: [http://localhost:8001/event.html](http://localhost:8001/event.html)
- **Evaluation**: [http://localhost:8001/evaluation.html](http://localhost:8001/evaluation.html)
- **API Docs (Swagger)**: [http://localhost:8001/docs](http://localhost:8001/docs)

## 📁 Project Structure

```
├── assets/          # CSS stylesheets and UI styling
├── backend/
│   ├── config/      # Policy and rule configurations (rules.yaml)
│   ├── engine/      # Pipeline, decision logic, rule matching & LLM inference
│   ├── evaluation/  # Evaluation datasets and batch benchmark runner
│   ├── models/      # Pydantic schemas and enums
│   ├── routes/      # FastAPI route definitions (/v1/moderate, /v1/reviews, etc.)
│   ├── storage/     # Async SQLite storage layer
│   ├── config.py    # Environment settings
│   ├── main.py      # FastAPI application entry point
│   └── requirements.txt
├── js/              # Frontend client scripts (API client, UI rendering)
├── pages/           # HTML templates for workbench, review, audit, & evaluation
└── start.sh         # Application launcher script
```

## 📄 License

MIT
