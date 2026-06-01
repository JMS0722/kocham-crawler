"""EuroCham 디렉토리 크롤러 실행 진입점"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.eurocham_main import main

if __name__ == "__main__":
    main()
