#!/bin/bash

# Check if -v flag is passed
PYTEST_FLAGS=""
if [[ "$1" == "-v" ]]; then
    PYTEST_FLAGS="-v -s"
fi

python -m poetry run black .
python -m poetry run isort . --profile black
python -m poetry run mypy --strict connectedpapers tests usage_samples
python -m poetry run flake8 connectedpapers tests usage_samples
python -m poetry run pytest tests usage_samples $PYTEST_FLAGS
