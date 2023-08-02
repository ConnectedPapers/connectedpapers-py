python -m poetry run black connectedpapers tests
python -m poetry run isort .
python -m poetry run mypy --strict connectedpapers tests
python -m poetry run flake8 connectedpapers tests
python -m poetry run pytest tests
