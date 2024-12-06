import os
import shutil
from fastapi import HTTPException, UploadFile
from pathlib import Path
from utils import get_kb_root


async def upload_file(
    file: UploadFile, root_path: str, kb_root: str = get_kb_root()
) -> bool:
    """
    上传文件到指定的input目录
    Args:
        file: FastAPI的UploadFile对象
        root_path: 目标根目录路径
    Returns:
        bool: 上传是否成功
    """
    try:
        # 检查文件格式是否为txt
        if not file.filename.lower().endswith(".txt"):
            return False
        # 确保目标input目录存在
        input_dir = os.path.join(kb_root, root_path, "input")
        if not os.path.exists(input_dir):
            raise HTTPException(status_code=400, detail="input目录不存在")
        # 构建目标文件路径
        target_path = os.path.join(input_dir, file.filename)
        # 保存上传的文件
        content = await file.read()
        with open(target_path, "wb") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"上传文件时发生错误: {str(e)}")
        return False
