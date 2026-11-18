#!/usr/bin/env bash
export PYTHONPATH=backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
