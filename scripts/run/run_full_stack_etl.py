#!/usr/bin/env python3
"""Wrapper de compatibilidade para o orquestrador unificado."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run.run_pipeline_frontend import main


if __name__ == "__main__":
    extra_args = sys.argv[1:]
    if "--full-stack" not in extra_args:
        extra_args = ["--full-stack", *extra_args]
    sys.argv = [sys.argv[0], *extra_args]
    main()
