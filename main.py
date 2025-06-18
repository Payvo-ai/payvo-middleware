#!/usr/bin/env python3
"""
Railway Entry Point for Payvo Middleware
"""

import sys
import os
from pathlib import Path

# Add middleware-system to Python path
middleware_path = Path(__file__).parent / "middleware-system"
sys.path.insert(0, str(middleware_path))

# Change to middleware-system directory
os.chdir(str(middleware_path))

# Import and run the main application
if __name__ == "__main__":
    from run import main
    main() 