#!/bin/bash
set -euo pipefail

poetry run black --check connectedpapers tests usage_samples
poetry run isort --check-only connectedpapers tests usage_samples
poetry run mypy --strict connectedpapers tests usage_samples
poetry run flake8 connectedpapers tests usage_samples
poetry run pytest tests usage_samples "$@"
