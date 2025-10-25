#!/usr/bin/env python3
"""Entry point for executing the drug overlap pipeline from the CLI."""

import sys
import os

# Add current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drug_overlap_pipeline import main

if __name__ == "__main__":
    main()