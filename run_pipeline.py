#!/usr/bin/env python3
"""
Convenience script to run the drug overlap analysis pipeline.

Usage:
    python run_pipeline.py [--threshold XX | --XX | XX]

Examples:
    python run_pipeline.py                 # Default 85% threshold
    python run_pipeline.py --threshold 90  # Explicit 90% threshold
    python run_pipeline.py --90            # Shorthand 90% threshold
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Build command and forward any CLI args to the pipeline runner
    cmd = [sys.executable, os.path.join("pipeline", "run_analysis.py"), *sys.argv[1:]]
    
    # Run the pipeline
    subprocess.run(cmd)