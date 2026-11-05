# AI Visibility Intelligence API

Flask API and three-agent pipeline. Full details are in the [root README](../README.md).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app wsgi db upgrade
flask --app wsgi run --port 5000
```

Run the tests with `pytest`.
