import asyncio
from asyncio.subprocess import PIPE
import json
import os
import time
import uuid
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from utils import get_kb_root
from models import ChatCompletionRequest
from logger import get_logger

logger = get_logger(__name__)


async def run_graphrag_query(
    request: ChatCompletionRequest, kb_root: str = get_kb_root()
) -> StreamingResponse:
    """
    Execute a GraphRAG query and return results as a streaming response.
    Args:
        request (ChatCompletionRequest): The request object containing query options and messages.
    Returns:
        StreamingResponse: A streaming response containing query results in SSE format.
    Raises:
        HTTPException: If the query execution fails or encounters an error.
    """
    try:
        # Extract query options and the latest message content
        query_options = request.query_options
        # query = request.messages[-1].content
        query = request.query
        # Build the GraphRAG CLI command with required arguments
        cmd = ["graphrag", "query"]
        target_path = os.path.join(kb_root, query_options.selected_folder)
        cmd.extend(["--root", target_path])
        cmd.extend(["--query", f"{query}"])
        cmd.extend(["--data", f"{target_path}/output"])
        cmd.extend(["--method", query_options.query_type])  # 'global' or 'local'
        # Add streaming flag if specified
        if request.stream:
            cmd.append("--streaming")
        # Add optional command arguments if specified
        if query_options.community_level:
            cmd.extend(["--community-level", str(query_options.community_level)])
        # if query_options.response_type:
        #     cmd.extend(["--response-type", query_options.response_type])
        # if query_options.custom_cli_args:
        #     cmd.extend(query_options.custom_cli_args.split())
        logger.info(f"Executing GraphRAG query: {' '.join(cmd)}")

        async def generate_response():
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=PIPE, stderr=PIPE
            )

            async def read_stream(stream):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    yield line.decode().strip()

            if request.stream:
                # 流式处理模式
                async for line in read_stream(process.stdout):
                    response_chunk = {
                        "id": f"chatcmpl-{uuid.uuid4().hex}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": line},
                                "finish_reason": None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(response_chunk)}\n\n"
            else:
                # 非流式处理模式，收集所有输出后一次性返回
                full_response = []
                async for line in read_stream(process.stdout):
                    full_response.append(line)
                response = {
                    "id": f"chatcmpl-{uuid.uuid4().hex}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"content": "\n".join(full_response)},
                            "finish_reason": "stop",
                        }
                    ],
                }
                yield f"data: {json.dumps(response)}\n\n"
            await process.wait()
            if process.returncode != 0:
                error_message = await process.stderr.read()
                logger.error(f"GraphRAG query failed: {error_message.decode()}")
                raise HTTPException(
                    status_code=500,
                    detail=f"GraphRAG query failed: {error_message.decode()}",
                )
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_response(), media_type="text/event-stream; charset=utf-8"
        )
    except Exception as e:
        # Log and re-raise any unexpected errors
        logger.error(f"Error in GraphRAG query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during the GraphRAG query: {str(e)}",
        )
