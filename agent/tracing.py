import os
import logging

logger = logging.getLogger("agent")

def get_traceable():
    """
    Returns the @traceable decorator from langsmith if enabled and installed,
    otherwise returns a dummy decorator to prevent crashes.
    """
    from agent.config import settings
    
    if not settings.langsmith_tracing:
        return _dummy_traceable
        
    try:
        from langsmith import traceable
        return traceable
    except ImportError:
        logger.warning("LANGSMITH_TRACING is enabled but 'langsmith' package is not installed.")
        return _dummy_traceable

def _dummy_traceable(*args, **kwargs):
    def decorator(func):
        return func
    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator

traceable = get_traceable()
