import asyncio
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize logging FIRST, before any pipeline imports
from core.logging_config import setup_logging
setup_logging()

from core.pipeline.pipeline_engine import PipelineEngine

if __name__ == "__main__":
    engine = PipelineEngine()
    try:
        asyncio.run(engine.run())
    except KeyboardInterrupt:
        print("\n🛑 Pipeline stopped by user.")
