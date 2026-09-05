import time
from functools import wraps
from typing import Callable, Any

def track_performance(metric_key: str):
    """
    Decorator to track execution time of a graph node or function
    and store it in the state's `metrics` dictionary.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(state: dict, *args, **kwargs) -> dict:
            start_time = time.time()
            result = func(state, *args, **kwargs)
            
            # Record the duration
            duration_ms = (time.time() - start_time) * 1000
            
            # If the function returns a state dict update, inject metrics
            if isinstance(result, dict):
                metrics = state.get("metrics") or {}
                metrics = dict(metrics) # Create a copy
                
                # If metric already exists, add to it (e.g. multiple LLM calls)
                current = metrics.get(metric_key, 0.0)
                metrics[metric_key] = current + duration_ms
                
                # Keep track of counts (e.g. llm_calls)
                if metric_key.endswith("_time"):
                    count_key = metric_key.replace("_time", "_calls")
                    metrics[count_key] = metrics.get(count_key, 0) + 1
                    
                result["metrics"] = metrics
            
            return result
        return wrapper
    return decorator
