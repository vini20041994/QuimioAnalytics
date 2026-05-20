#!/usr/bin/env python3
"""Legacy wrapper.

This entrypoint is kept only for compatibility and delegates to
scripts.run.run_etl_candidates_external.
"""

from scripts.run.run_etl_candidates_external import main


if __name__ == "__main__":
    main()