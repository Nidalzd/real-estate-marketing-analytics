"""run_cleaning.py — Execute the data cleaning pipeline."""

import sys
from pathlib import Path

# Ensure project root is on the path when run directly
sys.path.insert(0, str(Path(__file__).parent))

from src.cleaning import clean_dataset

if __name__ == "__main__":
    clean_dataset()
