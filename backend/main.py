"""
Entry point for the backend server.
Run with: uvicorn backend.main:app --reload
"""
import uvicorn
from .api.server import create_app

app = create_app()

if __name__ == "__main__":
    from .core import get_settings
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_config=None,
    )
