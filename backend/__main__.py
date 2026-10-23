"""Development entry point for the FastAPI server: ``python -m backend``."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    """Run the diligence server with the same host/port resolution as the app."""
    host = (os.environ.get("HOST") or "0.0.0.0").strip().strip("\"'") or "0.0.0.0"
    port = int((os.environ.get("PORT") or "8000").strip().strip("\"'") or "8000")
    uvicorn.run("backend.app:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
