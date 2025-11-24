"""Hook system for modifying API responses."""

from typing import Dict, Any, List, Callable

# Global list to store post-hooks
post_hooks: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []


def register_post_hook(hook_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
    """
    Register a post-hook function that will modify responses.
    
    Args:
        hook_func: Function that takes a response dict and returns a modified response dict
    """
    post_hooks.append(hook_func)
    return hook_func


def apply_post_hooks(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply all registered post-hooks to the response.
    
    Args:
        response: The OpenAI API response dictionary
        
    Returns:
        Modified response dictionary
    """
    modified_response = response
    for hook in post_hooks:
        modified_response = hook(modified_response)
    return modified_response

