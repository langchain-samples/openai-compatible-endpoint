"""FastAPI server with OpenAI-compatible chat completion endpoint."""

import json
import time
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from config import load_settings
from models import ChatCompletionRequest
from hooks import register_post_hook, apply_post_hooks
from hooks.chart import chart_hook

# Load settings
settings = load_settings()

# Create FastAPI app
app = FastAPI(title="OpenAI Compatible Chat Completion Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)

# Register hooks
register_post_hook(chart_hook)


def create_streaming_response(content, model: str, response_id: str):
    """Create OpenAI-compatible streaming response"""
    created = int(time.time())
    
    # First chunk - role establishment
    first_chunk = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"role": "assistant", "content": ""},
                "finish_reason": None,
            }
        ],
    }
    yield f"data: {json.dumps(first_chunk)}\n\n"
    
    # Handle content - can be string or array (multimodal)
    if isinstance(content, list):
        # For array content (multimodal), stream the text parts
        text_items = [item for item in content if isinstance(item, dict) and item.get("type") == "text"]
        image_items = [item for item in content if isinstance(item, dict) and item.get("type") == "image_url"]
        
        # Stream text content first
        if text_items:
            text_content = text_items[0].get("text", "")
            if text_content:
                chunk_size = 10
                for i in range(0, len(text_content), chunk_size):
                    chunk_content = text_content[i:i + chunk_size]
                    content_chunk = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": chunk_content},
                                "finish_reason": None
                            }
                        ],
                    }
                    yield f"data: {json.dumps(content_chunk)}\n\n"
        
        # After streaming text, send the full content array (text + images)
        if image_items:
            full_content_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": content},
                        "finish_reason": None
                    }
                ],
            }
            yield f"data: {json.dumps(full_content_chunk)}\n\n"
    else:
        # For string content, stream normally
        chunk_size = 10
        for i in range(0, len(content), chunk_size):
            chunk_content = content[i:i + chunk_size]
            content_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk_content},
                        "finish_reason": None
                    }
                ],
            }
            yield f"data: {json.dumps(content_chunk)}\n\n"
    
    # Final chunk - completion marker
    final_chunk = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }
        ],
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    
    # End of stream marker
    yield "data: [DONE]\n\n"


@app.options("/v1/chat/completions")
async def chat_completions_options():
    """Handle CORS preflight requests."""
    return JSONResponse(content={})


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completion endpoint with post-hook support."""
    try:
        # Prepare request parameters
        request_params = {
            "model": request.model,
            "messages": [msg.model_dump() for msg in request.messages],
        }
        
        # Add optional parameters
        if request.temperature is not None:
            request_params["temperature"] = request.temperature
        if request.max_tokens is not None:
            request_params["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            request_params["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            request_params["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            request_params["presence_penalty"] = request.presence_penalty
        if request.stop is not None:
            request_params["stop"] = request.stop
        if request.user is not None:
            request_params["user"] = request.user
        
        # Handle streaming
        is_streaming = request.stream or False
        
        # Call OpenAI API
        response = client.chat.completions.create(**request_params)
        
        # Convert response to dict format
        response_dict = response.model_dump()
        
        # Apply post-hooks
        modified_response = apply_post_hooks(response_dict)
        
        # Ensure the response has all required fields for LangSmith compatibility
        if "choices" in modified_response and len(modified_response["choices"]) > 0:
            choice = modified_response["choices"][0]
            
            # Ensure all required fields are present
            if "finish_reason" not in choice:
                choice["finish_reason"] = "stop"
            if "index" not in choice:
                choice["index"] = 0
            if "logprobs" not in choice:
                choice["logprobs"] = None
            
            # Ensure message has all required fields
            if "message" in choice:
                message = choice["message"]
                if "role" not in message:
                    message["role"] = "assistant"
                if "refusal" not in message:
                    message["refusal"] = None
                
                # Handle content format for LangSmith compatibility
                content = message.get("content")
                if isinstance(content, list):
                    # Ensure text items come first in the array
                    text_items = [item for item in content if isinstance(item, dict) and item.get("type") == "text"]
                    other_items = [item for item in content if isinstance(item, dict) and item.get("type") != "text"]
                    
                    if text_items:
                        message["content"] = text_items + other_items
                    else:
                        message["content"] = content
                elif content is None:
                    message["content"] = ""
        
        # Ensure usage is present
        if "usage" not in modified_response:
            modified_response["usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        
        # Ensure other required fields
        if "id" not in modified_response:
            modified_response["id"] = f"chatcmpl-{int(time.time())}"
        if "object" not in modified_response:
            modified_response["object"] = "chat.completion"
        if "created" not in modified_response:
            modified_response["created"] = int(time.time())
        
        # Handle streaming response
        if is_streaming:
            content = modified_response["choices"][0]["message"]["content"]
            return StreamingResponse(
                create_streaming_response(
                    content,
                    modified_response["model"],
                    modified_response["id"]
                ),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            return JSONResponse(content=modified_response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OpenAI Compatible Chat Completion Server",
        "version": "1.0.0",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "health": "/health"
        }
    }
