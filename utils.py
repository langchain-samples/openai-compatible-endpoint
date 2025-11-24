"""Utility functions for working with API responses."""

from typing import Dict, Any, List, Optional
import requests


def extract_chart_from_response(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract the chart image from the API response."""
    try:
        choice = response["choices"][0]
        message = choice["message"]
        content = message.get("content", [])
        
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "image_url":
                    return {
                        "type": "image_url",
                        "image_url": item.get("image_url", {})
                    }
    except (KeyError, IndexError, TypeError):
        pass
    
    return None


def extract_text_from_response(response: Dict[str, Any]) -> str:
    """Extract the text content from the API response."""
    try:
        choice = response["choices"][0]
        message = choice["message"]
        content = message.get("content", "")
        
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    return item.get("text", "")
        elif isinstance(content, str):
            return content
    except (KeyError, IndexError, TypeError):
        pass
    
    return ""


def append_ai_message_with_chart(
    conversation: List[Dict[str, Any]],
    response: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Append the AI's response (with chart) to the conversation.
    
    This demonstrates how to properly format the message for OpenAI-compatible
    clients that support multimodal content.
    """
    choice = response["choices"][0]
    message = choice["message"]
    
    # The message already contains the content array with text and image
    ai_message = {
        "role": message.get("role", "assistant"),
        "content": message.get("content", [])
    }
    
    conversation.append(ai_message)
    return conversation


def make_chat_request(
    base_url: str,
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    stream: bool = False
) -> Dict[str, Any]:
    """Make a chat completion request to the server."""
    url = f"{base_url}/v1/chat/completions"
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "max_tokens": 100
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

