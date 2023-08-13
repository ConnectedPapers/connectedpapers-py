python -m poetry run black connectedpapers tests usage_samples
python -m poetry run isort .
python -m poetry run mypy --strict connectedpapers tests usage_samples
python -m poetry run flake8 connectedpapers tests usage_samples
python -m poetry run pytest tests usage_samples
