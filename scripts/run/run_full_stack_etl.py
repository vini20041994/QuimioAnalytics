#!/usr/bin/env python3
"""Wrapper de compatibilidade para o orquestrador unificado com integrações externas."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run.run_pipeline_frontend import main


if __name__ == "__main__":
    extra_args = sys.argv[1:]
    
    # Adiciona --full-stack se não estiver presente
    if "--full-stack" not in extra_args:
        extra_args = ["--full-stack", *extra_args]
    
    # Adiciona --run-external e --sources por padrão se não estiverem presentes
    if "--no-external" not in extra_args and "--run-external" not in extra_args:
        # Inserir após --full-stack ou no início
        idx = extra_args.index("--full-stack") + 1 if "--full-stack" in extra_args else 1
        extra_args.insert(idx, "--run-external")
        extra_args.insert(idx + 1, "--sources")
        extra_args.insert(idx + 2, "pubchem")
        extra_args.insert(idx + 3, "chebi")
        extra_args.insert(idx + 4, "chemspider")
        extra_args.insert(idx + 5, "classyfire")
    
    sys.argv = [sys.argv[0], *extra_args]
    main()
