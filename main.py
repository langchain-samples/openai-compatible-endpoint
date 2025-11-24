"""Main entry point for the OpenAI-compatible server."""

import sys
import uvicorn

from config import load_settings
from server import app


def main():
    """Main function - starts the server."""
    print("=" * 70)
    print("OpenAI-Compatible Server with Chart Generation")
    print("=" * 70)
    print()
    
    # Load settings (this will load from .env file and validate)
    try:
        settings = load_settings()
        # Settings loaded successfully, API key is present
    except SystemExit:
        # load_settings already printed error and exited
        raise
    
    print("✓ Chart hook registered")
    print("✓ Server configured")
    print()
    
    # Start the server
    print("Starting server on http://localhost:8000...")
    print("Press Ctrl+C to stop the server")
    print()
    print("Example usage:")
    print("  curl -X POST http://localhost:8000/v1/chat/completions \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"model\": \"gpt-3.5-turbo\", \"messages\": [{\"role\": \"user\", \"content\": \"hello\"}], \"stream\": false}'")
    print()
    print("=" * 70)
    print()
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()

