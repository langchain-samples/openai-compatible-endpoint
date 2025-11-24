"""Pydantic models for API requests and responses."""

from typing import List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message model."""
    role: str
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """Chat completion request model."""
    model: str
    messages: List[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None
    stream: Optional[bool] = False
    user: Optional[str] = None

