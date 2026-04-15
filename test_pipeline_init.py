import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    print("Testing pipeline import...")
    from src.pipeline import SpeeKeyPipeline
    print("Import successful")
    
    print("Testing pipeline initialization...")
    pipeline = SpeeKeyPipeline()
    print("Initialization successful")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
