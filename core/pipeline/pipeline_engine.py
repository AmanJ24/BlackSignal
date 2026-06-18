import asyncio
import logging
import time
from .stage_registry import get_pipeline_stages

logger = logging.getLogger("PipelineEngine")

# Critical categories — failure here aborts the pipeline
CRITICAL_CATEGORIES = {"collection", "scoring"}

class PipelineEngine:
    def __init__(self, fail_fast: bool = True):
        self.stages = get_pipeline_stages()
        self.fail_fast = fail_fast
        # Note: completion_events are created in run() to ensure
        # they are bound to the active event loop.
        self.completion_events: dict = {}
        # Track failed stages for downstream decision-making
        self.failed_stages: set = set()
        self.stage_results: dict = {}

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

        # 2. Check if any upstream dependency failed (skip if so)
        if stage.depends_on:
            failed_deps = [dep for dep in stage.depends_on if dep in self.failed_stages]
            if failed_deps:
                logger.warning(f"⏭️  Skipping {stage_name} — upstream failed: {failed_deps}")
                self.failed_stages.add(stage_name)
                self.stage_results[stage_name] = "SKIPPED"
                self.completion_events[stage_name].set()
                return "SKIPPED"

        # 3. Execute Action
        logger.info(f"🚀 Starting Stage: {stage_name}")
        start_time = time.time()
        status = "FAILED"
        
        try:
            await asyncio.to_thread(stage.action)
            status = "SUCCESS"
        except Exception as e:
            logger.error(f"❌ Stage {stage_name} Failed: {e}", exc_info=True)
            self.failed_stages.add(stage_name)
            
            # If a critical stage fails and fail_fast is on, abort the pipeline
            if self.fail_fast and stage.category in CRITICAL_CATEGORIES:
                logger.critical(f"🛑 Critical stage {stage_name} failed. Aborting pipeline.")
                raise RuntimeError(f"Critical stage '{stage_name}' failed: {e}") from e
        
        duration = round(time.time() - start_time, 2)
        self.stage_results[stage_name] = status
        logger.info(f"{'✅' if status == 'SUCCESS' else '❌'} Finished Stage: {stage_name} ({duration}s) [{status}]")

        # 4. Signal Completion
        self.completion_events[stage_name].set()
        return status

    async def run(self):
        """
        Main entry point to run the whole graph.
        """
        # Create event flags inside the running event loop
        self.completion_events = {name: asyncio.Event() for name in self.stages}
        self.failed_stages.clear()
        self.stage_results.clear()

        logger.info("🎬 Starting OSINT Pipeline...")
        start_global = time.time()

        try:
            async with asyncio.TaskGroup() as tg:
                for name in self.stages:
                    tg.create_task(self._execute_stage(name))
        except* RuntimeError as eg:
            # Collect critical failure messages
            for exc in eg.exceptions:
                logger.critical(f"Pipeline aborted: {exc}")
        except* Exception as eg:
            # Catch any other unexpected errors from stages
            for exc in eg.exceptions:
                logger.error(f"Unexpected pipeline error: {exc}", exc_info=exc)

        duration = round(time.time() - start_global, 2)
        
        # Print summary
        succeeded = sum(1 for s in self.stage_results.values() if s == "SUCCESS")
        failed = sum(1 for s in self.stage_results.values() if s == "FAILED")
        skipped = sum(1 for s in self.stage_results.values() if s == "SKIPPED")
        
        logger.info(f"🏁 Pipeline Completed in {duration}s — ✅ {succeeded} succeeded, ❌ {failed} failed, ⏭️ {skipped} skipped")
