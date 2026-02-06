import asyncio
import logging
import time
from .stage_registry import get_pipeline_stages

logger = logging.getLogger("PipelineEngine")
logging.basicConfig(level=logging.INFO)

class PipelineEngine:
    def __init__(self):
        self.stages = get_pipeline_stages()
        # Create an event flag for every stage
        # This allows tasks to wait for specific stages to finish without knowing about the Task object itself
        self.completion_events = {name: asyncio.Event() for name in self.stages}

    async def _execute_stage(self, stage_name: str):
        """
        Worker function for a single stage.
        Waits for dependencies -> Runs Logic -> Signals Completion.
        """
        stage = self.stages[stage_name]

        # 1. Wait for Dependencies
        if stage.depends_on:
            logger.info(f"⏳ {stage_name} waiting for dependencies: {stage.depends_on}")
            for dep in stage.depends_on:
                # Wait until the dependency's event flag is set to True
                await self.completion_events[dep].wait()

        # 2. Execute Action
        logger.info(f"🚀 Starting Stage: {stage_name}")
        start_time = time.time()
        status = "FAILED"
        
        try:
            # Run the synchronous action in a separate thread to keep the event loop moving
            await asyncio.to_thread(stage.action)
            status = "SUCCESS"
        except Exception as e:
            logger.error(f"❌ Stage {stage_name} Failed: {e}")
            # In a production system, you might want to stop the whole pipeline here
            # For now, we allow it to proceed so we can see what else works
        
        duration = round(time.time() - start_time, 2)
        logger.info(f"✅ Finished Stage: {stage_name} ({duration}s) [{status}]")

        # 3. Signal Completion
        # This wakes up any other tasks waiting on this stage
        self.completion_events[stage_name].set()
        return status

    async def run(self):
        """
        Main entry point to run the whole graph.
        """
        logger.info("🎬 Starting OSINT Pipeline...")
        start_global = time.time()

        # Create a TaskGroup to manage all stages concurrently
        async with asyncio.TaskGroup() as tg:
            for name in self.stages:
                # Schedule every stage immediately.
                # The _execute_stage logic handles the waiting.
                tg.create_task(self._execute_stage(name))

        duration = round(time.time() - start_global, 2)
        logger.info(f"🏁 Pipeline Execution Completed in {duration}s")
