"""
Micro-Batching for ML Inference
================================
Groups concurrent inference requests into batches for efficient processing.

This reduces model call overhead by processing multiple requests together,
typically achieving 2-4x throughput improvement.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Any, Callable, TypeVar, Generic, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Input type
R = TypeVar('R')  # Output type


@dataclass
class BatchedItem(Generic[T, R]):
    """Represents a single item in a batch."""
    input: T
    future: asyncio.Future[R]
    timestamp: datetime


class MicroBatcher(Generic[T, R]):
    """
    Async micro-batcher that groups requests within a time window.
    
    Example:
        batcher = MicroBatcher(
            runner=lambda batch: [model.predict(x) for x in batch],
            max_wait_ms=5,
            max_batch_size=64
        )
        result = await batcher.infer(single_input)
    """
    
    def __init__(
        self,
        runner: Callable[[List[T]], List[R]],
        max_wait_ms: float = 5.0,
        max_batch_size: int = 64,
        name: str = "batcher"
    ):
        """
        Initialize micro-batcher.
        
        Args:
            runner: Function that processes a batch of inputs
            max_wait_ms: Maximum wait time (ms) before processing batch
            max_batch_size: Maximum items per batch
            name: Name for logging
        """
        self.runner = runner
        self.max_wait = max_wait_ms / 1000.0  # Convert to seconds
        self.max_batch_size = max_batch_size
        self.name = name
        
        self.queue: List[BatchedItem[T, R]] = []
        self.lock = asyncio.Lock()
        self._drain_task: Optional[asyncio.Task] = None
    
    async def infer(self, item: T) -> R:
        """
        Submit item for batched inference.
        
        Args:
            item: Input to process
            
        Returns:
            Inference result
        """
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        
        batched_item = BatchedItem(
            input=item,
            future=future,
            timestamp=datetime.now()
        )
        
        async with self.lock:
            self.queue.append(batched_item)
            
            # Start drain task if this is the first item
            if len(self.queue) == 1:
                self._drain_task = asyncio.create_task(self._drain())
        
        return await future
    
    async def _drain(self) -> None:
        """Process the current batch."""
        # Wait for batching window
        await asyncio.sleep(self.max_wait)
        
        # Extract batch under lock
        async with self.lock:
            batch_items = self.queue[:self.max_batch_size]
            self.queue = self.queue[self.max_batch_size:]
        
        if not batch_items:
            return
        
        inputs = [item.input for item in batch_items]
        futures = [item.future for item in batch_items]
        
        # Run inference (synchronously for now - can be made async if needed)
        try:
            # Run in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            outputs = await loop.run_in_executor(None, self.runner, inputs)
            
            # Set results
            for output, future in zip(outputs, futures):
                if not future.done():
                    future.set_result(output)
            
            logger.debug(
                f"{self.name}: Processed batch of {len(batch_items)} items"
            )
        except Exception as e:
            logger.error(f"{self.name}: Batch processing failed: {e}")
            # Set exception on all futures
            for future in futures:
                if not future.done():
                    future.set_exception(e)
        
        # Process remaining items if any
        async with self.lock:
            if self.queue:
                asyncio.create_task(self._drain())

