#!/usr/bin/env python3
"""
Convenience script to run the drug overlap analysis pipeline.

Usage:
    python run_pipeline.py [threshold]

Examples:
    python run_pipeline.py         # Default 85% threshold
    python run_pipeline.py 90      # 90% threshold
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Build command
    cmd = [sys.executable, os.path.join("pipeline", "run_analysis.py")]
    
    # Add threshold argument if provided
    if len(sys.argv) > 1:
        cmd.append(sys.argv[1])
    
    # Run the pipeline
    subprocess.run(cmd)