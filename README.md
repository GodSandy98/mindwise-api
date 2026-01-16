# mindwise-api

FastAPI backend for MindWise student psychological assessment system.

## Quick Start

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate on Windows

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000