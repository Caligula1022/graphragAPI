import os
from typing import Dict
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from logger import get_logger

# from fastapi.responses import JSONResponse
from models import ChatCompletionRequest, IndexingRequest, InitRequest
from query import run_graphrag_query
from index import run_indexing, indexing_logs, run_indexing_with_status
from init import run_init
from upload import upload_file
from utils import get_kb_root

# from settings import load_settings
# from utils import fetch_available_models

router = APIRouter()
logger = get_logger(__name__)


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        logger.info(f"Received request for model: {request.model}")
        if request.model.startswith("graphrag-"):
            logger.info("Routing to GraphRAG query")
            if not request.query_options or not request.query_options.selected_folder:
                raise HTTPException(
                    status_code=400,
                    detail="Selected folder is required for GraphRAG queries",
                )
            return await run_graphrag_query(request)
        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid model specified: {request.model}"
            )
    except HTTPException as he:
        logger.error(f"HTTP Exception: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/health")
async def health_check():
    return {"status": "ok"}


task_status: Dict[str, str] = {}


@router.post("/v1/index")
async def start_indexing(request: IndexingRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())  # 生成唯一任务ID
    task_status[task_id] = "running"  # 初始化任务状态为运行中
    background_tasks.add_task(run_indexing_with_status, request, task_id, task_status)
    return {
        "status": "started",
        "task_id": task_id,
        "message": "Indexing process has been started in the background",
    }


@router.get("/v1/index_status/{task_id}")
async def get_indexing_status(task_id: str):
    status = task_status.get(task_id, "unknown")
    return {
        "task_id": task_id,
        "status": "failed" if status.startswith("failed:") else status,
        "error": status[7:] if status.startswith("failed:") else None,
    }


@router.post("/v1/init")
async def init(request: InitRequest):
    logger.info(f"Received init request: {request}")
    if not request.root:
        raise HTTPException(status_code=400, detail="Root is required")
    return await run_init(request)


@router.post("/v1/upload/")
async def handle_upload(file: UploadFile, root_path: str) -> Dict[str, str]:
    """
    处理文件上传的API接口
    """
    if not file:
        raise HTTPException(status_code=400, detail="没有文件被上传")
    success = await upload_file(file, root_path)
    if success:
        return {"message": f"文件 {file.filename} 上传成功"}
    else:
        raise HTTPException(
            status_code=400, detail="文件上传失败，请确保上传的是txt格式文件"
        )


@router.get("/v1/list_knowledge_bases")
async def list_knowledge_bases():
    # check all files in kb_root and return a list of available knowledge bases
    kb_root = get_kb_root()
    files = os.listdir(kb_root)
    return [f for f in files if os.path.isdir(os.path.join(kb_root, f))]


@router.get("/v1/show_uploaded_files/{kb_name}")
async def show_uploaded_files(kb_name: str):
    kb_root = get_kb_root()
    kb_path = os.path.join(kb_root, kb_name, "input")
    files = os.listdir(kb_path)
    return [f for f in files if os.path.isfile(os.path.join(kb_path, f))]
