import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipeline import SpeeKeyPipeline

async def test_pipeline_initialization():
    """测试管线初始化"""
    try:
        pipeline = SpeeKeyPipeline()
        print("Pipeline initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing pipeline: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pipeline_initialization())
