import asyncio
import os
from fastapi import Depends, HTTPException
from utils import get_kb_root
from models import InitRequest


async def run_init(request: InitRequest, kb_root: str = get_kb_root()):
    try:
        target_path = os.path.join(kb_root, request.root)
        inputpath = os.path.join(target_path, "input")
        os.makedirs(inputpath, mode=0o777, exist_ok=False)
        cmd = ["graphrag", "init"]
        cmd.extend(["--root", f"{target_path}"])
        process = await asyncio.create_subprocess_exec(*cmd)
        await process.wait()
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail="Failed to initialize")
        return {"status": "success"}
    except FileExistsError:
        raise HTTPException(
            status_code=409,
            detail=f"Knowledgebase '{request.root}' already exists. Please choose a different name.",
        )
