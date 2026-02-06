import asyncio
import logging
import time
from .stage_registry import get_pipeline_stages

logger = logging.getLogger("PipelineEngine")
logging.basicConfig(level=logging.INFO)

class PipelineEngine:
    def __init__(self):
        self.stages = get_pipeline_stages()
        self.results = {}      # Track completion status
        self.tasks = {}        # Track asyncio tasks
        self._lock = asyncio.Lock()

    async def run_stage(self, stage_name: str):
        """
        Recursive function to run a stage and its dependencies.
        """
        # If already running/done, return the existing task/result
        if stage_name in self.tasks:
            return await self.tasks[stage_name]

        stage = self.stages[stage_name]

        # 1. Wait for Dependencies
        if stage.depends_on:
            logger.info(f"⏳ {stage_name} waiting for dependencies: {stage.depends_on}")
            await asyncio.gather(*(self.run_stage(dep) for dep in stage.depends_on))

        # 2. Execute Action (in thread pool to avoid blocking async loop)
        logger.info(f"🚀 Starting Stage: {stage_name}")
        start_time = time.time()
        
        try:
            # Most of our tools are synchronous (requests), so we offload them to a thread
            await asyncio.to_thread(stage.action)
            status = "SUCCESS"
        except Exception as e:
            logger.error(f"❌ Stage {stage_name} Failed: {e}")
            status = "FAILED"
            # In a strict pipeline, we might raise e here to stop dependents

        duration = round(time.time() - start_time, 2)
        logger.info(f"✅ Finished Stage: {stage_name} ({duration}s) [{status}]")
        
        return status

    async def run(self):
        """
        Main entry point to run the whole graph.
        """
        logger.info("🎬 Starting OSINT Pipeline...")
        start_global = time.time()

        # Identify all leaf nodes (stages) and run them.
        # The recursive `run_stage` will handle the order automatically.
        
        async with asyncio.TaskGroup() as tg:
            for name in self.stages:
                # We start a task for every stage. 
                # The dependency logic ensures they wait for each other.
                self.tasks[name] = tg.create_task(self.run_stage(name))

        duration = round(time.time() - start_global, 2)
        logger.info(f"🏁 Pipeline Execution Completed in {duration}s")
