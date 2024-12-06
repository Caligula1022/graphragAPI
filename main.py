import argparse
import os
from dotenv import load_dotenv
from logger import get_logger
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from handler import router
from settings import init_kbs

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # global settings
    try:
        logger.info("Initializing KBs...")
        load_dotenv(".env")
        init_kbs(os.getenv("KB_ROOT"))
        logger.info("Initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing: {str(e)}")
        raise
    yield
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch the GraphRAG API server")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", type=int, default=8012, help="Port to bind the server to"
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload mode")
    args = parser.parse_args()
    import uvicorn

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)
