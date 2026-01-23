"""Retry utilities with exponential backoff."""
import logging
import time
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry(
    func: Callable,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
):
    """Execute a function with retries and exponential backoff."""
    attempt = 1
    delay = initial_delay
    while True:
        try:
            return func()
        except exceptions as exc:
            if attempt >= max_attempts:
                logger.error("Retry failed after %s attempts: %s", attempt, exc)
                raise
            logger.warning("Retry %s/%s after error: %s", attempt, max_attempts, exc)
            time.sleep(delay)
            attempt += 1
            delay *= backoff_factor
