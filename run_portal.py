"""Lotte Rental Directory Crawler Portal"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.portal import main

if __name__ == "__main__":
    main()
