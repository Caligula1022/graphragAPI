# Global variable to store the latest indexing logs
import asyncio
from collections import deque
import os
from typing import Any, Dict
from fastapi import HTTPException
from settings import update_env_file, update_yaml_config
from utils import get_kb_root
from logger import get_logger
from models import IndexingRequest

indexing_logs = deque(maxlen=100)
logger = get_logger(__name__)
indexing_status = {"status": "idle", "logs": []}


async def run_indexing(request: IndexingRequest, kb_root: str = get_kb_root()):
    cmd = ["graphrag", "index"]
    target_path = os.path.join(kb_root, request.root)
    input_path = os.path.join(target_path, "input")
    if not os.path.exists(input_path):
        raise HTTPException(status_code=400, detail="Input path does not exist")
    # if there is no file in the input path, raise an error
    if not os.listdir(input_path):
        raise HTTPException(status_code=400, detail="Input path is empty")
    cmd.extend(["--root", target_path])
    if request.verbose:
        cmd.append("--verbose")
    if request.nocache:
        cmd.append("--nocache")
    if request.resume:
        cmd.extend(["--resume", request.resume])
    cmd.extend(["--reporter", request.reporter])
    cmd.extend(["--emit", ",".join(request.emit)])
    # Set environment variables for LLM and embedding models
    env_path = os.path.join(target_path, ".env")
    settings_path = os.path.join(target_path, "settings.yaml")
    updates = [
        ("llm.model", request.llm_model),
        ("llm.api_base", request.llm_api_base),
        ("embeddings.llm.model", request.embed_model),
        ("embeddings.llm.api_base", request.embed_api_base),
    ]
    update_env_file("GRAPHRAG_API_KEY", request.api_key, env_path)
    if not update_yaml_config(updates, settings_path):
        raise HTTPException(status_code=500, detail="Failed to update settings.yaml")
    env: Dict[str, Any] = os.environ.copy()
    # update .env file with the new api key
    # env["GRAPHRAG_API_KEY"] = request.api_key
    # env["GRAPHRAG_LLM_MODEL"] = request.llm_model
    # env["GRAPHRAG_EMBED_MODEL"] = request.embed_model
    # env["GRAPHRAG_LLM_API_BASE"] = request.llm_api_base
    # # env["GRAPHRAG_LLM_API_BASE"] = LLM_API_BASE
    # env["GRAPHRAG_EMBED_API_BASE"] = request.embed_api_base
    # env["GRAPHRAG_EMBED_API_BASE"] = EMBEDDINGS_API_BASE
    # Set environment variables for LLM parameters
    # for key, value in request.llm_params.items():
    #     env[f"GRAPHRAG_LLM_{key.upper()}"] = str(value)
    # # Set environment variables for embedding parameters
    # for key, value in request.embed_params.items():
    #     env[f"GRAPHRAG_EMBED_{key.upper()}"] = str(value)
    # # Add custom CLI arguments
    # if request.custom_args:
    #     cmd.extend(request.custom_args.split())
    logger.info(f"Executing indexing command: {' '.join(cmd)}")
    logger.info(f"Environment variables: {env}")
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        async def read_stream(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                line = line.decode().strip()
                indexing_logs.append(line)
                logger.info(line)

        await asyncio.gather(read_stream(process.stdout), read_stream(process.stderr))
        await process.wait()
        if process.returncode == 0:
            logger.info("Indexing completed successfully")
            return {"status": "success", "message": "Indexing completed successfully"}
        else:
            logger.error("Indexing failed")
            return {
                "status": "error",
                "message": "Indexing failed. Check logs for details.",
            }
    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        return {"status": "error", "message": f"Indexing failed: {str(e)}"}


async def run_indexing_with_status(
    request: IndexingRequest, task_id: str, task_status: Dict[str, str]
):
    try:
        result = await run_indexing(request)
        if result["status"] == "error":
            task_status[task_id] = f"failed: {result['message']}"
        else:
            task_status[task_id] = "success"
    except Exception as e:
        task_status[task_id] = f"failed: {str(e)}"
