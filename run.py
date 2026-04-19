#!/usr/bin/env python
"""
Context-Aware Tourism Recommendation System
Main entry point for the application
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import TourismRecommendationSystem

def main():
    DATASET_PATH = "dataset/Gowalla_totalCheckins.txt"
    
    if not os.path.exists(DATASET_PATH):
        print(f"\n❌ ERROR: Dataset not found at '{DATASET_PATH}'")
        sys.exit(1)
    
    try:
        system = TourismRecommendationSystem(DATASET_PATH)
        system.run_interactive()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()