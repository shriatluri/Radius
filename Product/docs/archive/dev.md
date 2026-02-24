# Local Development

## Prereqs

- Python 3.11+

## Run API

```bash
python -m venv .venv
./.venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Interactive docs: `http://127.0.0.1:8000/docs`
